"""
Reflector Lunar Decision Journal - Task 51

Enables Reflector users to track a major decision across an entire lunar cycle,
observing how their perspective changes as the Moon activates different gates.

Key features:
- Lunar consideration tracking (one per cycle)
- Journal entries with lunar metadata
- Cycle timeline view
- Cycle completion and archiving
- History of past cycles
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from bson import ObjectId

from services.lunar_cycle import (
    calculate_lunar_cycle_info,
    get_current_moon_gate,
    SYNODIC_MONTH
)

logger = logging.getLogger(__name__)

# =============================================================================
# DAILY JOURNAL PROMPTS FOR REFLECTORS
# =============================================================================

REFLECTOR_JOURNAL_PROMPTS = [
    "What seems different about this consideration today?",
    "What appears clearer or more confusing compared with earlier in the cycle?",
    "What may belong to you, and what may belong to your environment?",
    "How does this decision feel in your body right now?",
    "What perspective is the current gate offering you?",
    "What have you noticed that surprised you today?",
    "Where do you feel resistance, and where do you feel openness?",
    "What would you tell yourself from the beginning of this cycle?",
]

# End-of-cycle reflection prompts
CYCLE_COMPLETION_PROMPTS = [
    "What perspective stayed consistent across the entire cycle?",
    "What changed as the Moon moved through different gates?",
    "What now feels reliable enough to act on?",
    "What might need another cycle of observation?",
    "What have you learned about yourself through this process?",
]


# =============================================================================
# LUNAR CYCLE HELPERS
# =============================================================================

def get_current_cycle_boundaries() -> Dict[str, Any]:
    """
    Calculate the current lunar cycle start and end dates.
    Returns approximate dates based on lunar day.
    """
    lunar_info = calculate_lunar_cycle_info()
    lunar_day = lunar_info.get("lunar_day", 0)
    
    now = datetime.now(timezone.utc)
    
    # Calculate cycle start (last new moon)
    days_since_new = lunar_day
    cycle_start = now - timedelta(days=days_since_new)
    
    # Calculate cycle end (next new moon)
    days_until_new = SYNODIC_MONTH - lunar_day
    cycle_end = now + timedelta(days=days_until_new)
    
    return {
        "cycle_start": cycle_start.strftime("%Y-%m-%d"),
        "cycle_end": cycle_end.strftime("%Y-%m-%d"),
        "lunar_day": lunar_day,
        "is_near_new_moon": lunar_day > 27 or lunar_day < 2,
        "days_until_new_moon": round(days_until_new, 1),
    }


def get_daily_prompt(lunar_day: int, gate_number: Optional[int] = None) -> str:
    """
    Get a daily journal prompt based on lunar day.
    Varies throughout the cycle for freshness.
    """
    import random
    # Use lunar day as seed for consistency within the day
    random.seed(int(lunar_day * 100))
    prompt = random.choice(REFLECTOR_JOURNAL_PROMPTS)
    random.seed()  # Reset seed
    return prompt


# =============================================================================
# LUNAR CONSIDERATION MANAGEMENT
# =============================================================================

async def get_active_consideration(db, user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the user's most recent active lunar consideration.
    For backward compatibility, returns only one consideration.
    Use get_all_active_considerations() for full list.
    """
    try:
        consideration = await db.lunar_considerations.find_one(
            {"user_id": user_id, "status": "active"},
            sort=[("created_at", -1)]  # Most recent first
        )
        
        if consideration:
            return {
                "id": str(consideration["_id"]),
                "topic": consideration.get("topic", ""),
                "created_at": consideration.get("created_at").isoformat() if consideration.get("created_at") else None,
                "cycle_start": consideration.get("cycle_start"),
                "status": consideration.get("status"),
            }
        
        return None
        
    except Exception as e:
        logger.error(f"[LunarJournal] Error getting active consideration: {e}")
        return None


# Task 64: Support multiple active considerations
async def get_all_active_considerations(db, user_id: str) -> List[Dict[str, Any]]:
    """
    Get ALL active lunar considerations for a user.
    Users can track multiple decisions simultaneously.
    """
    try:
        cursor = db.lunar_considerations.find(
            {"user_id": user_id, "status": "active"}
        ).sort("created_at", -1)  # Most recent first
        
        considerations = []
        async for consideration in cursor:
            # Get entry count for this consideration
            entry_count = await db.lunar_journal_entries.count_documents({
                "user_id": user_id,
                "consideration_id": str(consideration["_id"])
            })
            
            # Calculate days in cycle
            created_at = consideration.get("created_at")
            if created_at:
                days_in_cycle = (datetime.now(timezone.utc) - created_at).days + 1
            else:
                days_in_cycle = 1
            
            considerations.append({
                "id": str(consideration["_id"]),
                "topic": consideration.get("topic", ""),
                "created_at": created_at.isoformat() if created_at else None,
                "cycle_start": consideration.get("cycle_start"),
                "status": consideration.get("status"),
                "entry_count": entry_count,
                "days_in_cycle": min(days_in_cycle, 29),
            })
        
        return considerations
        
    except Exception as e:
        logger.error(f"[LunarJournal] Error getting all active considerations: {e}")
        return []


async def create_consideration(db, user_id: str, topic: str) -> Dict[str, Any]:
    """
    Create a new lunar consideration for the current cycle.
    Task 64: Removed restriction - users can track multiple decisions.
    """
    try:
        cycle_info = get_current_cycle_boundaries()
        
        consideration_data = {
            "user_id": user_id,
            "topic": topic,
            "status": "active",
            "cycle_start": cycle_info["cycle_start"],
            "created_at": datetime.now(timezone.utc),
        }
        
        result = await db.lunar_considerations.insert_one(consideration_data)
        
        logger.info(f"[LunarJournal] Created consideration for user {user_id[:8]}: {topic[:30]}...")
        
        return {
            "id": str(result.inserted_id),
            "topic": topic,
            "cycle_start": cycle_info["cycle_start"],
            "status": "active",
        }
        
    except Exception as e:
        logger.error(f"[LunarJournal] Error creating consideration: {e}")
        raise


async def close_consideration(
    db, 
    user_id: str, 
    consideration_id: str,
    final_reflection: Optional[str] = None,
    continue_to_next_cycle: bool = False
) -> Dict[str, Any]:
    """
    Close a lunar consideration at the end of a cycle.
    
    If continue_to_next_cycle is True, creates a new active consideration
    with the same topic for the next cycle.
    """
    try:
        consideration = await db.lunar_considerations.find_one({
            "_id": ObjectId(consideration_id),
            "user_id": user_id,
        })
        
        if not consideration:
            raise ValueError("Consideration not found")
        
        cycle_info = get_current_cycle_boundaries()
        
        # Update the consideration to archived
        await db.lunar_considerations.update_one(
            {"_id": ObjectId(consideration_id)},
            {
                "$set": {
                    "status": "archived",
                    "cycle_end": cycle_info["cycle_start"],  # End at the new cycle's start
                    "final_reflection": final_reflection,
                    "closed_at": datetime.now(timezone.utc),
                }
            }
        )
        
        result = {
            "closed": True,
            "consideration_id": consideration_id,
            "continued": False,
        }
        
        # If continuing to next cycle, create new consideration
        if continue_to_next_cycle:
            new_consideration = await create_consideration(
                db, user_id, consideration["topic"]
            )
            result["continued"] = True
            result["new_consideration_id"] = new_consideration["id"]
        
        logger.info(f"[LunarJournal] Closed consideration {consideration_id}, continued={continue_to_next_cycle}")
        return result
        
    except ValueError as e:
        raise e
    except Exception as e:
        logger.error(f"[LunarJournal] Error closing consideration: {e}")
        raise


async def update_consideration_topic(db, user_id: str, consideration_id: str, new_topic: str) -> Dict[str, Any]:
    """
    Update the topic of an active consideration.
    """
    try:
        result = await db.lunar_considerations.update_one(
            {
                "_id": ObjectId(consideration_id),
                "user_id": user_id,
                "status": "active",
            },
            {"$set": {"topic": new_topic, "updated_at": datetime.now(timezone.utc)}}
        )
        
        if result.modified_count == 0:
            raise ValueError("Consideration not found or not active")
        
        return {"updated": True, "topic": new_topic}
        
    except Exception as e:
        logger.error(f"[LunarJournal] Error updating consideration: {e}")
        raise


# =============================================================================
# LUNAR JOURNAL ENTRIES
# =============================================================================

async def create_lunar_journal_entry(
    db,
    user_id: str,
    content: str,
    consideration_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a journal entry with lunar metadata for a Reflector user.
    """
    try:
        # Get current lunar info
        lunar_info = calculate_lunar_cycle_info()
        gate_data = get_current_moon_gate()
        
        entry_data = {
            "user_id": user_id,
            "content": content,
            "created_at": datetime.now(timezone.utc),
            "is_lunar_entry": True,
            # Lunar metadata
            "lunar_day": round(lunar_info.get("lunar_day", 0), 1),
            "moon_phase": lunar_info.get("moon_phase"),
            "moon_gate": gate_data.get("current_moon_gate"),
            "gate_line": gate_data.get("gate_line"),
            "gate_title": gate_data.get("gate_title"),
            "gate_theme": gate_data.get("gate_theme"),
            "center": gate_data.get("center"),
            # Link to consideration if provided
            "consideration_id": consideration_id,
        }
        
        result = await db.lunar_journal.insert_one(entry_data)
        
        # Return clean response (exclude internal _id, serialize properly)
        response_data = {
            "id": str(result.inserted_id),
            "user_id": user_id,
            "content": content,
            "created_at": entry_data["created_at"].isoformat(),
            "is_lunar_entry": True,
            "lunar_day": entry_data["lunar_day"],
            "moon_phase": entry_data["moon_phase"],
            "moon_gate": entry_data["moon_gate"],
            "gate_line": entry_data["gate_line"],
            "gate_title": entry_data["gate_title"],
            "gate_theme": entry_data["gate_theme"],
            "center": entry_data["center"],
            "consideration_id": consideration_id,
        }
        
        logger.info(f"[LunarJournal] Created entry: day={entry_data['lunar_day']}, gate={entry_data['moon_gate']}")
        
        return response_data
        
    except Exception as e:
        logger.error(f"[LunarJournal] Error creating lunar entry: {e}")
        raise


async def get_lunar_journal_entries(
    db,
    user_id: str,
    consideration_id: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Get lunar journal entries for a user.
    If consideration_id is provided, only returns entries for that consideration.
    """
    try:
        query = {"user_id": user_id, "is_lunar_entry": True}
        
        if consideration_id:
            query["consideration_id"] = consideration_id
        
        cursor = db.lunar_journal.find(query).sort("created_at", -1).limit(limit)
        entries = await cursor.to_list(length=limit)
        
        return [
            {
                "id": str(entry["_id"]),
                "content": entry.get("content", ""),
                "created_at": entry.get("created_at").isoformat() if entry.get("created_at") else None,
                "lunar_day": entry.get("lunar_day"),
                "moon_phase": entry.get("moon_phase"),
                "moon_gate": entry.get("moon_gate"),
                "gate_line": entry.get("gate_line"),
                "gate_title": entry.get("gate_title"),
                "gate_theme": entry.get("gate_theme"),
                "center": entry.get("center"),
                "consideration_id": entry.get("consideration_id"),
            }
            for entry in entries
        ]
        
    except Exception as e:
        logger.error(f"[LunarJournal] Error getting entries: {e}")
        return []


async def get_cycle_timeline(db, user_id: str, consideration_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get a timeline view of lunar journal entries for the current cycle.
    Groups entries by lunar day and gate.
    """
    try:
        # Get entries for current consideration or all recent entries
        entries = await get_lunar_journal_entries(db, user_id, consideration_id, limit=100)
        
        # Get current lunar info
        lunar_info = calculate_lunar_cycle_info()
        cycle_info = get_current_cycle_boundaries()
        
        # Group entries by lunar day
        timeline: Dict[int, List[Dict[str, Any]]] = {}
        
        for entry in entries:
            day = int(entry.get("lunar_day", 0))
            if day not in timeline:
                timeline[day] = []
            timeline[day].append(entry)
        
        # Convert to sorted list
        timeline_list = [
            {
                "lunar_day": day,
                "entries": day_entries,
                "entry_count": len(day_entries),
                "gates": list(set(e.get("moon_gate") for e in day_entries if e.get("moon_gate"))),
            }
            for day, day_entries in sorted(timeline.items())
        ]
        
        return {
            "current_lunar_day": round(lunar_info.get("lunar_day", 0), 1),
            "moon_phase": lunar_info.get("moon_phase"),
            "cycle_start": cycle_info["cycle_start"],
            "cycle_end": cycle_info["cycle_end"],
            "is_near_new_moon": cycle_info["is_near_new_moon"],
            "days_until_new_moon": cycle_info["days_until_new_moon"],
            "timeline": timeline_list,
            "total_entries": len(entries),
        }
        
    except Exception as e:
        logger.error(f"[LunarJournal] Error getting cycle timeline: {e}")
        return {
            "timeline": [],
            "total_entries": 0,
            "error": str(e),
        }


# =============================================================================
# LUNAR DECISION HISTORY
# =============================================================================

async def get_consideration_history(db, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get archived lunar considerations for a user.
    Includes summary of entries for each cycle.
    """
    try:
        cursor = db.lunar_considerations.find({
            "user_id": user_id,
            "status": "archived",
        }).sort("closed_at", -1).limit(limit)
        
        considerations = await cursor.to_list(length=limit)
        
        history = []
        for c in considerations:
            consideration_id = str(c["_id"])
            
            # Get entry count for this consideration
            entry_count = await db.lunar_journal.count_documents({
                "consideration_id": consideration_id,
            })
            
            # Get unique gates touched during this cycle
            entries = await db.lunar_journal.find({
                "consideration_id": consideration_id,
            }).to_list(length=100)
            
            gates_touched = list(set(
                e.get("moon_gate") for e in entries if e.get("moon_gate")
            ))
            
            history.append({
                "id": consideration_id,
                "topic": c.get("topic", ""),
                "cycle_start": c.get("cycle_start"),
                "cycle_end": c.get("cycle_end"),
                "created_at": c.get("created_at").isoformat() if c.get("created_at") else None,
                "closed_at": c.get("closed_at").isoformat() if c.get("closed_at") else None,
                "final_reflection": c.get("final_reflection"),
                "entry_count": entry_count,
                "gates_touched": gates_touched,
            })
        
        return history
        
    except Exception as e:
        logger.error(f"[LunarJournal] Error getting history: {e}")
        return []


async def get_consideration_detail(db, user_id: str, consideration_id: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed view of a specific consideration with all its entries.
    """
    try:
        consideration = await db.lunar_considerations.find_one({
            "_id": ObjectId(consideration_id),
            "user_id": user_id,
        })
        
        if not consideration:
            return None
        
        # Get all entries for this consideration
        entries = await get_lunar_journal_entries(db, user_id, consideration_id, limit=100)
        
        # Get unique gates
        gates_touched = list(set(
            e.get("moon_gate") for e in entries if e.get("moon_gate")
        ))
        
        return {
            "id": str(consideration["_id"]),
            "topic": consideration.get("topic", ""),
            "status": consideration.get("status"),
            "cycle_start": consideration.get("cycle_start"),
            "cycle_end": consideration.get("cycle_end"),
            "created_at": consideration.get("created_at").isoformat() if consideration.get("created_at") else None,
            "closed_at": consideration.get("closed_at").isoformat() if consideration.get("closed_at") else None,
            "final_reflection": consideration.get("final_reflection"),
            "entries": entries,
            "entry_count": len(entries),
            "gates_touched": gates_touched,
        }
        
    except Exception as e:
        logger.error(f"[LunarJournal] Error getting consideration detail: {e}")
        return None


# =============================================================================
# MAIN API FUNCTION - GET LUNAR JOURNAL STATUS
# =============================================================================

async def get_lunar_journal_status(db, user_id: str) -> Dict[str, Any]:
    """
    Get complete lunar journal status for a Reflector user.
    Used to initialize the journal UI.
    """
    try:
        # Get current lunar info
        lunar_info = calculate_lunar_cycle_info()
        gate_data = get_current_moon_gate()
        cycle_info = get_current_cycle_boundaries()
        
        # Get active consideration
        active_consideration = await get_active_consideration(db, user_id)
        
        # Get recent entries
        recent_entries = await get_lunar_journal_entries(
            db, user_id, 
            consideration_id=active_consideration["id"] if active_consideration else None,
            limit=10
        )
        
        # Get daily prompt
        daily_prompt = get_daily_prompt(
            lunar_info.get("lunar_day", 0),
            gate_data.get("current_moon_gate")
        )
        
        # Check if cycle completion prompt should show
        show_cycle_completion = cycle_info["is_near_new_moon"] and active_consideration is not None
        
        return {
            "success": True,
            # Current lunar state
            "lunar_day": round(lunar_info.get("lunar_day", 0), 1),
            "moon_phase": lunar_info.get("moon_phase"),
            "moon_icon": lunar_info.get("moon_icon"),
            "cycle_progress": lunar_info.get("cycle_progress"),
            "days_until_new_moon": cycle_info["days_until_new_moon"],
            # Current gate
            "current_gate": gate_data.get("current_moon_gate"),
            "gate_formatted": gate_data.get("gate_formatted"),
            "gate_title": gate_data.get("gate_title"),
            "gate_theme": gate_data.get("gate_theme"),
            "center": gate_data.get("center"),
            "gate_reflection": gate_data.get("gate_reflection_message"),
            # Consideration
            "active_consideration": active_consideration,
            "has_active_consideration": active_consideration is not None,
            # Entries
            "recent_entries": recent_entries,
            "entry_count": len(recent_entries),
            # Prompts
            "daily_prompt": daily_prompt,
            "cycle_completion_prompts": CYCLE_COMPLETION_PROMPTS if show_cycle_completion else None,
            "show_cycle_completion": show_cycle_completion,
            # Cycle info
            "cycle_start": cycle_info["cycle_start"],
            "cycle_end": cycle_info["cycle_end"],
            "is_near_new_moon": cycle_info["is_near_new_moon"],
        }
        
    except Exception as e:
        logger.error(f"[LunarJournal] Error getting status: {e}")
        return {
            "success": False,
            "error": str(e),
        }
