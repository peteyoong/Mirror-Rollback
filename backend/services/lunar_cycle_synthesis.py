"""
Lunar Cycle Synthesis - Task 69 + Task 70: Mirror Cycle Intelligence Engine

Generates structured insights from a Reflector's journal entries across a lunar cycle.
Now uses the Pattern Engine for improved emotional scoring and momentum tracking.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from collections import Counter
import random

from services.pattern_engine import (
    compute_weighted_emotional_score,
    extract_tags,
    extract_domain,
    extract_pattern_signals_from_lunar,
    get_decision_pattern_snapshot,
    get_momentum_description,
    MomentumState,
    DataSufficiency,
    GATE_INSIGHTS,
)

logger = logging.getLogger(__name__)

# =============================================================================
# MIRROR LANGUAGE TEMPLATES - Task 70 Section 5 & 6
# =============================================================================

def format_decision_reference(topic: str) -> str:
    """Format decision topic for natural inclusion in text."""
    topic_lower = topic.lower()
    if topic_lower.startswith("should i"):
        return topic_lower.replace("should i", "").strip()
    return topic_lower

LOW_DATA_TEMPLATES = {
    "insufficient": "You recorded {count} reflection during this cycle about {topic}. There is not yet enough observation data to identify how your perspective changes across the cycle.",
    "single": "You recorded {count} reflection during this cycle about {topic}. More entries may reveal clearer patterns in how your perspective evolves.",
}

PATTERN_INSIGHT_TEMPLATES = [
    "Across the cycle, your reflections about {topic} seem to return to the theme of {theme}, suggesting this may be an important consideration.",
    "A thread that appears consistently in your observations about {topic} is {theme}. This may point to something worth exploring further.",
    "Your reflections about {topic} suggest that {theme} has been on your mind throughout this observation period.",
]

EMOTIONAL_SUMMARY_TEMPLATES = {
    "excitement_dominant": "Your reflections about {topic} carry a sense of excitement and possibility.",
    "hesitation_dominant": "Your reflections about {topic} suggest some hesitation or caution about moving forward.",
    "mixed": "Your reflections about {topic} show a mix of excitement and hesitation, which may reflect the complexity of this decision.",
    "neutral": "Your reflections about {topic} appear thoughtful and measured, without strong emotional pulls either way.",
}

GATE_SIGNIFICANCE_TEMPLATES = [
    "Your most substantive reflection about {topic} came during Gate {gate} — {title}. {insight}",
    "Gate {gate} ({title}) appears to have sparked particularly deep consideration about {topic}. {insight}",
]

CLOSING_QUESTIONS = [
    "What now feels clearer about {topic} than it did at the beginning of the cycle?",
    "Looking back across this cycle, what perspective on {topic} feels most trustworthy?",
    "Which insights about {topic} from this observation period feel most reliable to act on?",
    "What has this cycle revealed about {topic} that you can now trust?",
]


# =============================================================================
# MAIN SYNTHESIS FUNCTION - Task 70 Enhanced
# =============================================================================

async def generate_lunar_cycle_synthesis(
    db,
    user_id: str,
    consideration_id: str,
    cycle_completed: bool = False
) -> Dict[str, Any]:
    """
    Generate structured cycle insights using the Pattern Engine.
    """
    logger.info(f"[LunarSynthesis] Generating synthesis for user {user_id[:8]}, consideration {consideration_id[:8]}")
    
    try:
        # Get pattern snapshot from the engine
        snapshot = await get_decision_pattern_snapshot(db, user_id, consideration_id)
        topic = snapshot.decision_topic
        topic_ref = format_decision_reference(topic)
        
        # Fetch entries for detailed analysis
        entries = await db.lunar_journal.find({
            "user_id": user_id,
            "consideration_id": consideration_id,
        }).sort("lunar_day", 1).to_list(length=100)
        
        # Get consideration status
        from bson import ObjectId
        consideration = await db.lunar_considerations.find_one({
            "_id": ObjectId(consideration_id),
        })
        status = consideration.get("status", "active") if consideration else "active"
        
        # Handle low-data scenario (< 2 entries)
        if snapshot.data_sufficiency == DataSufficiency.INSUFFICIENT.value:
            logger.info("[LunarSynthesis] Insufficient data - returning minimal synthesis")
            return {
                "success": True,
                "has_synthesis": True,
                "is_low_data": True,
                "consideration_topic": topic,
                "entry_count": snapshot.entry_count,
                "days_observed": snapshot.days_observed,
                "gates_touched": len(set(e.get("moon_gate") for e in entries if e.get("moon_gate"))),
                "low_data_message": LOW_DATA_TEMPLATES["insufficient" if snapshot.entry_count < 1 else "single"].format(
                    count=snapshot.entry_count,
                    topic=topic_ref
                ),
                "pattern_status": "There is not yet enough observation data to identify how your perspective changes across the cycle.",
                "suggestion": f"You may wish to continue observing {topic_ref} through another lunar cycle.",
                "momentum": {
                    "state": MomentumState.UNCLEAR.value,
                    "label": "Insufficient Data",
                    "description": f"Not enough reflections to determine momentum for {topic_ref}.",
                    "score": 0,
                },
            }
        
        # Run full analysis with improved scoring
        all_signals = []
        total_excitement = 0.0
        total_hesitation = 0.0
        all_tags = []
        gate_data = {}
        entry_tones = []
        
        for entry in entries:
            content = entry.get("content", "")
            gate = entry.get("moon_gate")
            
            # Get weighted scores from pattern engine
            scores = compute_weighted_emotional_score(content)
            total_excitement += scores["excitement_score"]
            total_hesitation += scores["hesitation_score"]
            entry_tones.append(scores["dominant_tone"])
            
            # Extract tags
            tags = extract_tags(content)
            all_tags.extend(tags)
            
            # Track gate data
            if gate:
                if gate not in gate_data:
                    gate_data[gate] = {
                        "gate": gate,
                        "entry_count": 0,
                        "total_score": 0,
                        "longest_content": "",
                    }
                gate_data[gate]["entry_count"] += 1
                gate_data[gate]["total_score"] += scores["excitement_score"] + scores["hesitation_score"]
                if len(content) > len(gate_data[gate]["longest_content"]):
                    gate_data[gate]["longest_content"] = content
            
            # Extract pattern signals
            signals = extract_pattern_signals_from_lunar(entry, user_id, consideration_id, topic)
            all_signals.extend(signals)
        
        # Find strongest gate
        strongest_gate = None
        if gate_data:
            best_gate = max(gate_data.values(), key=lambda g: g["total_score"] + g["entry_count"] * 0.5)
            gate_info = GATE_INSIGHTS.get(best_gate["gate"], {
                "title": f"Gate {best_gate['gate']}",
                "insight": "This gate may have brought a unique perspective to your observation."
            })
            strongest_gate = {
                "gate": best_gate["gate"],
                "title": gate_info["title"],
                "insight": gate_info["insight"],
                "entry_count": best_gate["entry_count"],
                "longest_entry_preview": best_gate["longest_content"][:150] + "..." if len(best_gate["longest_content"]) > 150 else best_gate["longest_content"],
            }
        
        # Determine dominant tone
        excitement_dominant = total_excitement > total_hesitation * 1.5
        hesitation_dominant = total_hesitation > total_excitement * 1.5
        
        if excitement_dominant:
            dominant_tone = "excitement_dominant"
        elif hesitation_dominant:
            dominant_tone = "hesitation_dominant"
        elif total_excitement > 0.2 and total_hesitation > 0.2:
            dominant_tone = "mixed"
        else:
            dominant_tone = "neutral"
        
        # Get top themes
        tag_counts = Counter(all_tags)
        top_themes = [tag.replace("_", " ").title() for tag, _ in tag_counts.most_common(3)]
        
        # Format emotional themes
        positive_tags = ["creative_independence", "growth", "possibility", "new_beginning", "authenticity"]
        cautious_tags = ["financial_security", "risk", "responsibility"]
        
        excitement_themes = []
        hesitation_themes = []
        for tag, count in tag_counts.most_common(5):
            display = tag.replace("_", " ").title()
            if tag in positive_tags:
                excitement_themes.append(display)
            elif tag in cautious_tags:
                hesitation_themes.append(display)
            elif dominant_tone == "excitement_dominant":
                excitement_themes.append(display)
            else:
                hesitation_themes.append(display)
        
        # Build pattern insight
        pattern_insight = None
        if top_themes:
            template = random.choice(PATTERN_INSIGHT_TEMPLATES)
            pattern_insight = template.format(topic=topic_ref, theme=top_themes[0].lower())
        
        # Calculate momentum
        tone_consistency = entry_tones.count(dominant_tone) / len(entry_tones) if entry_tones else 0
        momentum_state = MomentumState(snapshot.momentum)
        momentum_description = get_momentum_description(momentum_state, topic_ref)
        
        # Calculate momentum score (0-5 for visualization)
        if momentum_state == MomentumState.STRONG_POSITIVE:
            momentum_score = 5
            momentum_label = "Strong Positive Momentum"
        elif momentum_state == MomentumState.POSITIVE:
            momentum_score = 4
            momentum_label = "Positive Momentum"
        elif momentum_state == MomentumState.MIXED:
            momentum_score = 3
            momentum_label = "Mixed Momentum"
        elif momentum_state == MomentumState.RESISTANT:
            momentum_score = 1
            momentum_label = "Resistant Momentum"
        else:
            momentum_score = 2
            momentum_label = "Unclear Momentum"
        
        # Build synthesis response
        synthesis = {
            "success": True,
            "has_synthesis": True,
            "is_low_data": False,
            "consideration_topic": topic,
            "cycle_completed": status == "completed" or cycle_completed,
            
            # Cycle Overview
            "entry_count": len(entries),
            "days_observed": snapshot.days_observed,
            "gates_touched": len(gate_data),
            
            # Emotional Signals (Task 70 Section 4: Improved scoring)
            "emotional_signals": {
                "dominant_tone": dominant_tone,
                "excitement_score": round(total_excitement, 3),
                "hesitation_score": round(total_hesitation, 3),
                "summary": EMOTIONAL_SUMMARY_TEMPLATES.get(dominant_tone, EMOTIONAL_SUMMARY_TEMPLATES["neutral"]).format(topic=topic_ref),
                "confidence": snapshot.confidence,
            },
            "emotional_themes": {
                "excitement_themes": excitement_themes[:3],
                "hesitation_themes": hesitation_themes[:3],
            },
            
            # Notable Gate (Task 70 Section 5: Decision-referenced)
            "strongest_gate": strongest_gate,
            
            # Pattern Insight (Task 70 Section 5: Decision-referenced)
            "pattern_insight": pattern_insight,
            "top_themes": top_themes,
            
            # Decision Momentum (Task 70 Section 7: New)
            "momentum": {
                "state": momentum_state.value,
                "label": momentum_label,
                "description": momentum_description,
                "score": momentum_score,
            },
            
            # Reflection Question (Decision-referenced)
            "reflection_question": random.choice(CLOSING_QUESTIONS).format(topic=topic_ref),
            
            # Pattern Engine data (for future use)
            "pattern_data": {
                "signal_count": len(all_signals),
                "data_sufficiency": snapshot.data_sufficiency,
                "repeated_tags": snapshot.repeated_tags,
            },
        }
        
        # Add gate significance text if available
        if strongest_gate:
            template = random.choice(GATE_SIGNIFICANCE_TEMPLATES)
            synthesis["gate_significance_text"] = template.format(
                topic=topic_ref,
                gate=strongest_gate["gate"],
                title=strongest_gate["title"],
                insight=strongest_gate["insight"]
            )
        
        logger.info(f"[LunarSynthesis] Generated synthesis: {len(entries)} entries, momentum={momentum_state.value}")
        
        return synthesis
        
    except Exception as e:
        logger.error(f"[LunarSynthesis] Error generating synthesis: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
        }


async def get_cached_synthesis(
    db,
    user_id: str,
    consideration_id: str,
    force_regenerate: bool = False
) -> Optional[Dict[str, Any]]:
    """Get cached synthesis or generate new one."""
    from bson import ObjectId
    
    try:
        if not force_regenerate:
            cached = await db.lunar_synthesis_cache.find_one({
                "user_id": user_id,
                "consideration_id": consideration_id,
            })
            
            if cached:
                logger.info(f"[LunarSynthesis] Returning cached synthesis for {consideration_id[:8]}")
                return {k: v for k, v in cached.items() if k != "_id"}
        
        synthesis = await generate_lunar_cycle_synthesis(db, user_id, consideration_id)
        
        if synthesis.get("success") and synthesis.get("has_synthesis"):
            await db.lunar_synthesis_cache.delete_many({
                "user_id": user_id,
                "consideration_id": consideration_id,
            })
            
            cache_doc = {
                "user_id": user_id,
                "consideration_id": consideration_id,
                "created_at": datetime.now(timezone.utc),
                **synthesis,
            }
            await db.lunar_synthesis_cache.insert_one(cache_doc)
            logger.info(f"[LunarSynthesis] Cached new synthesis for {consideration_id[:8]}")
        
        return synthesis
        
    except Exception as e:
        logger.error(f"[LunarSynthesis] Error getting/caching synthesis: {e}")
        return await generate_lunar_cycle_synthesis(db, user_id, consideration_id)
