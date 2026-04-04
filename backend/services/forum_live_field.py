"""
Forum Live Field Engine V1.0

ARCHITECTURE: FIELD-FIRST, NOT IDENTITY-FIRST

This engine reads the live field dynamics of a forum based on actual activity signals,
NOT on personality composition summaries.

LAYERS:
1. SIGNAL LAYER - Raw activity detection
   - Who is posting, who is silent
   - Timing gaps between activity
   - Message frequency patterns
   - Emotional tone markers

2. FIELD PATTERN LAYER - Dynamic detection (NO personality references)
   - Pacing mismatch: some ready to move, others still processing
   - Unspoken tension: activity patterns that suggest something unsaid
   - Emotional saturation: when the field feels heavy or charged
   - Over-initiation vs under-response: output/input imbalance
   - Holding back vs pushing forward: collective movement patterns

3. LANGUAGE LAYER - Mirror voice (present-tense, situational)
   - "Right now, the space feels..."
   - "Something hasn't landed yet..."
   - "Part of the room is ready, part is still processing..."

4. OPTIONAL IDENTITY LAYER - Light touch ONLY after field is described
   - "Some move fast, others take time to sense"
   - NEVER lead with "Manifestors are..." or "Type 5s tend to..."

SUCCESS CRITERIA:
- Feels like reading the room in real time
- Not a static report
- Not personality analysis
- Helps user sense what is happening NOW
- Supports: "What do I need to shift?"
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


# =============================================================================
# LAYER 1: SIGNAL EXTRACTION
# =============================================================================

async def extract_activity_signals(db, forum_id: str, lookback_days: int = 14) -> Dict[str, Any]:
    """
    Extract raw activity signals from forum data.
    
    Signals:
    - member_activity: who posted, when, how much
    - silence_map: who hasn't engaged
    - timing_gaps: gaps between forum activity
    - frequency_pattern: burst vs steady vs sparse
    - emotional_markers: detected tone signals
    """
    
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=lookback_days)
    recent_cutoff = now - timedelta(days=3)
    
    def ensure_tz_aware(dt):
        """Ensure datetime is timezone-aware."""
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt
    
    def is_after_cutoff(dt, cutoff_dt):
        """Safely compare datetime to cutoff."""
        dt = ensure_tz_aware(dt)
        if dt is None:
            return False
        return dt >= cutoff_dt
    
    # Get all members
    members = []
    members_cursor = db.forum_members.find({
        "forum_id": forum_id,
        "status": "active"
    })
    async for m in members_cursor:
        members.append({
            "user_id": m["user_id"],
            "joined_at": m.get("joined_at"),
        })
    
    member_ids = [m["user_id"] for m in members]
    member_count = len(members)
    
    # Track per-member activity
    member_activity = defaultdict(lambda: {
        "updates": 0,
        "reflections": 0,
        "chat_messages": 0,
        "last_activity": None,
        "activity_timestamps": [],
    })
    
    all_timestamps = []
    emotional_markers = []
    
    # === FORUM UPDATES ===
    updates_cursor = db.forum_updates.find({
        "forum_id": forum_id,
    }).sort("created_at", -1)
    
    async for u in updates_cursor:
        uid = u.get("user_id")
        ts = ensure_tz_aware(u.get("created_at"))
        
        # Skip if outside lookback window
        if not is_after_cutoff(ts, cutoff):
            continue
        
        if uid and ts:
            member_activity[uid]["updates"] += 1
            member_activity[uid]["activity_timestamps"].append(ts)
            all_timestamps.append(ts)
            
            last_act = ensure_tz_aware(member_activity[uid]["last_activity"])
            if last_act is None or ts > last_act:
                member_activity[uid]["last_activity"] = ts
            
            # Extract emotional markers from update content
            content = u.get("updates", {})
            for area, data in content.items():
                if isinstance(data, dict):
                    emotions = data.get("emotions", [])
                    text = data.get("update_text", "")
                    if emotions:
                        emotional_markers.extend(emotions)
                    if text:
                        emotional_markers.extend(_extract_tone_markers(text))
    
    # === FORUM REFLECTIONS ===
    reflections_cursor = db.forum_reflections.find({
        "forum_id": forum_id,
    }).sort("created_at", -1)
    
    async for r in reflections_cursor:
        uid = r.get("user_id")
        ts = ensure_tz_aware(r.get("created_at"))
        
        # Skip if outside lookback window
        if not is_after_cutoff(ts, cutoff):
            continue
        
        if uid and ts:
            member_activity[uid]["reflections"] += 1
            member_activity[uid]["activity_timestamps"].append(ts)
            all_timestamps.append(ts)
            
            last_act = ensure_tz_aware(member_activity[uid]["last_activity"])
            if last_act is None or ts > last_act:
                member_activity[uid]["last_activity"] = ts
            
            # Extract emotional markers from reflection
            content = r.get("content", "")
            if content:
                emotional_markers.extend(_extract_tone_markers(content))
    
    # === FORUM CHAT MESSAGES ===
    chat_cursor = db.forum_chat_messages.find({
        "forum_id": forum_id,
    }).sort("created_at", -1)
    
    async for c in chat_cursor:
        uid = c.get("user_id")
        ts = ensure_tz_aware(c.get("created_at"))
        
        # Skip if outside lookback window
        if not is_after_cutoff(ts, cutoff):
            continue
        
        if uid and ts:
            member_activity[uid]["chat_messages"] += 1
            member_activity[uid]["activity_timestamps"].append(ts)
            all_timestamps.append(ts)
            
            last_act = ensure_tz_aware(member_activity[uid]["last_activity"])
            if last_act is None or ts > last_act:
                member_activity[uid]["last_activity"] = ts
            
            # Extract emotional markers from chat
            content = c.get("content", "")
            if content:
                emotional_markers.extend(_extract_tone_markers(content))
    
    # === COMPUTE SILENCE MAP ===
    active_members = set(member_activity.keys())
    silent_members = [uid for uid in member_ids if uid not in active_members]
    
    # Members who were active but went quiet recently
    recently_quiet = []
    for uid, data in member_activity.items():
        last_act = ensure_tz_aware(data["last_activity"])
        if last_act and last_act < recent_cutoff:
            recently_quiet.append(uid)
    
    # === COMPUTE TIMING GAPS ===
    timing_gaps = []
    if len(all_timestamps) > 1:
        sorted_ts = sorted(all_timestamps, reverse=True)
        for i in range(min(10, len(sorted_ts) - 1)):
            gap = (sorted_ts[i] - sorted_ts[i + 1]).total_seconds() / 3600  # hours
            timing_gaps.append(gap)
    
    # === COMPUTE FREQUENCY PATTERN ===
    total_activity = len(all_timestamps)
    recent_activity = sum(1 for ts in all_timestamps if ts >= recent_cutoff)
    
    if total_activity == 0:
        frequency_pattern = "dormant"
    elif recent_activity > 5:
        frequency_pattern = "active"
    elif recent_activity > 0:
        frequency_pattern = "sporadic"
    else:
        frequency_pattern = "fading"
    
    # === COMPUTE ACTIVITY DISTRIBUTION ===
    activity_counts = []
    for uid in member_ids:
        data = member_activity.get(uid, {})
        total = data.get("updates", 0) + data.get("reflections", 0) + data.get("chat_messages", 0)
        activity_counts.append(total)
    
    # Detect imbalance
    max_activity = max(activity_counts) if activity_counts else 0
    min_activity = min(activity_counts) if activity_counts else 0
    avg_activity = sum(activity_counts) / len(activity_counts) if activity_counts else 0
    
    return {
        "member_count": member_count,
        "member_activity": dict(member_activity),
        "silent_members": silent_members,
        "recently_quiet": recently_quiet,
        "timing_gaps": timing_gaps,
        "frequency_pattern": frequency_pattern,
        "total_activity": total_activity,
        "recent_activity": recent_activity,
        "activity_distribution": {
            "max": max_activity,
            "min": min_activity,
            "avg": round(avg_activity, 1),
            "spread": max_activity - min_activity,
        },
        "emotional_markers": emotional_markers,
        "lookback_days": lookback_days,
    }


def _extract_tone_markers(text: str) -> List[str]:
    """Extract emotional tone markers from text."""
    markers = []
    text_lower = text.lower()
    
    # Tension/heaviness markers
    tension_words = ["stuck", "frustrated", "overwhelmed", "anxious", "worried", "confused", "uncertain"]
    for word in tension_words:
        if word in text_lower:
            markers.append(f"tension:{word}")
    
    # Movement/energy markers
    energy_words = ["excited", "ready", "motivated", "clear", "moving", "decided", "committed"]
    for word in energy_words:
        if word in text_lower:
            markers.append(f"energy:{word}")
    
    # Processing/pause markers
    pause_words = ["thinking", "processing", "sitting with", "not sure", "wondering", "maybe", "might"]
    for word in pause_words:
        if word in text_lower:
            markers.append(f"pause:{word}")
    
    # Relational markers
    relational_words = ["between us", "with them", "relationship", "connection", "together", "apart"]
    for word in relational_words:
        if word in text_lower:
            markers.append(f"relational:{word}")
    
    return markers


# =============================================================================
# LAYER 2: FIELD PATTERN DETECTION
# =============================================================================

def detect_field_patterns(signals: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect field dynamics from signals.
    
    NO PERSONALITY REFERENCES - pure field dynamics.
    
    Patterns detected:
    - pacing_mismatch: some ready to move, others still processing
    - unspoken_tension: patterns suggesting something unsaid
    - emotional_saturation: field feels heavy or charged
    - initiation_response_imbalance: output/input imbalance
    - collective_movement: holding back vs pushing forward
    - silence_weight: what the silence might mean
    """
    
    patterns = {
        "pacing_mismatch": None,
        "unspoken_tension": None,
        "emotional_saturation": None,
        "initiation_response_imbalance": None,
        "collective_movement": None,
        "silence_weight": None,
        "field_temperature": None,  # warm, cool, charged, still
        "detected_patterns": [],
    }
    
    member_count = signals.get("member_count", 0)
    silent_count = len(signals.get("silent_members", []))
    recently_quiet_count = len(signals.get("recently_quiet", []))
    total_activity = signals.get("total_activity", 0)
    frequency = signals.get("frequency_pattern", "dormant")
    distribution = signals.get("activity_distribution", {})
    emotional_markers = signals.get("emotional_markers", [])
    timing_gaps = signals.get("timing_gaps", [])
    
    # === PACING MISMATCH ===
    # High spread in activity = some moving fast, others not
    spread = distribution.get("spread", 0)
    avg = distribution.get("avg", 0)
    
    if member_count >= 3 and spread > 3 and avg > 0:
        patterns["pacing_mismatch"] = {
            "detected": True,
            "severity": "moderate" if spread < 6 else "high",
            "signal": "Some members are engaging frequently while others are still finding their pace.",
        }
        patterns["detected_patterns"].append("pacing_mismatch")
    
    # === SILENCE WEIGHT ===
    # What does the silence mean?
    silence_ratio = silent_count / member_count if member_count > 0 else 0
    
    if silence_ratio > 0.5:
        patterns["silence_weight"] = {
            "detected": True,
            "type": "majority_silent",
            "signal": "More than half the room hasn't entered the space yet.",
        }
        patterns["detected_patterns"].append("heavy_silence")
    elif recently_quiet_count > 0:
        patterns["silence_weight"] = {
            "detected": True,
            "type": "recent_withdrawal",
            "signal": "Some voices that were present have gone quiet.",
        }
        patterns["detected_patterns"].append("recent_silence")
    elif silent_count > 0 and total_activity > 5:
        patterns["silence_weight"] = {
            "detected": True,
            "type": "observer_presence",
            "signal": "Some are watching, not yet speaking.",
        }
        patterns["detected_patterns"].append("observer_silence")
    
    # === EMOTIONAL SATURATION ===
    tension_count = sum(1 for m in emotional_markers if m.startswith("tension:"))
    energy_count = sum(1 for m in emotional_markers if m.startswith("energy:"))
    pause_count = sum(1 for m in emotional_markers if m.startswith("pause:"))
    
    total_emotional = tension_count + energy_count + pause_count
    
    if total_emotional > 0:
        tension_ratio = tension_count / total_emotional
        energy_ratio = energy_count / total_emotional
        pause_ratio = pause_count / total_emotional
        
        if tension_ratio > 0.5:
            patterns["emotional_saturation"] = {
                "detected": True,
                "type": "heavy",
                "signal": "There's weight in what's being shared. The field feels loaded.",
            }
            patterns["field_temperature"] = "charged"
            patterns["detected_patterns"].append("emotional_weight")
        elif energy_ratio > 0.5:
            patterns["emotional_saturation"] = {
                "detected": True,
                "type": "activated",
                "signal": "There's forward energy in the room. Something wants to move.",
            }
            patterns["field_temperature"] = "warm"
            patterns["detected_patterns"].append("forward_energy")
        elif pause_ratio > 0.5:
            patterns["emotional_saturation"] = {
                "detected": True,
                "type": "processing",
                "signal": "The room is in a processing state. Things are landing.",
            }
            patterns["field_temperature"] = "still"
            patterns["detected_patterns"].append("collective_pause")
    
    # === UNSPOKEN TENSION ===
    # Detect from: large timing gaps after activity burst, or high activity but low sharing
    avg_gap = sum(timing_gaps) / len(timing_gaps) if timing_gaps else 0
    
    if avg_gap > 48 and total_activity > 3:  # Long gaps after some activity
        patterns["unspoken_tension"] = {
            "detected": True,
            "type": "gaps_after_activity",
            "signal": "Something may have landed that hasn't been named. Long pauses after engagement.",
        }
        patterns["detected_patterns"].append("unspoken_tension")
    
    # === COLLECTIVE MOVEMENT ===
    if frequency == "active":
        patterns["collective_movement"] = {
            "state": "moving",
            "signal": "The space is in motion. Things are happening.",
        }
    elif frequency == "sporadic":
        patterns["collective_movement"] = {
            "state": "intermittent",
            "signal": "Movement comes in waves. Bursts followed by stillness.",
        }
    elif frequency == "fading":
        patterns["collective_movement"] = {
            "state": "slowing",
            "signal": "The space was active but has gone quieter recently.",
        }
    elif frequency == "dormant":
        patterns["collective_movement"] = {
            "state": "still",
            "signal": "The space is quiet. Nothing has moved recently.",
        }
    
    # === FIELD TEMPERATURE (overall) ===
    if patterns["field_temperature"] is None:
        if frequency == "dormant":
            patterns["field_temperature"] = "cool"
        elif frequency == "active" and tension_count > energy_count:
            patterns["field_temperature"] = "charged"
        elif frequency == "active":
            patterns["field_temperature"] = "warm"
        else:
            patterns["field_temperature"] = "still"
    
    return patterns


# =============================================================================
# LAYER 3: LANGUAGE GENERATION (Mirror Voice)
# =============================================================================

def generate_field_language(
    signals: Dict[str, Any],
    patterns: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Generate present-tense, situational language about the field.
    
    NO PERSONALITY REFERENCES in the core language.
    
    Structure:
    - field_reading: The main present-tense observation
    - what_hasnt_landed: What might be unresolved
    - what_the_room_needs: What might help
    - your_shift_prompt: Invitation for the user
    """
    
    member_count = signals.get("member_count", 0)
    silent_count = len(signals.get("silent_members", []))
    frequency = signals.get("frequency_pattern", "dormant")
    temperature = patterns.get("field_temperature", "still")
    detected = patterns.get("detected_patterns", [])
    
    # === BUILD FIELD READING ===
    field_lines = []
    
    # Opening based on temperature
    if temperature == "charged":
        field_lines.append("Right now, the space feels charged.")
    elif temperature == "warm":
        field_lines.append("Right now, there's energy in the room.")
    elif temperature == "still":
        field_lines.append("Right now, the space is still.")
    elif temperature == "cool":
        field_lines.append("Right now, the room is quiet.")
    
    # Add pattern-specific observations
    if "pacing_mismatch" in detected:
        field_lines.append("Part of the room is ready to move. Part is still processing.")
    
    if "heavy_silence" in detected:
        field_lines.append("Most voices haven't entered yet. The space is mostly waiting.")
    elif "recent_silence" in detected:
        field_lines.append("Some voices that were here have gone quiet.")
    elif "observer_silence" in detected:
        field_lines.append("Some are present but not speaking. Watching, sensing.")
    
    if "emotional_weight" in detected:
        field_lines.append("There's weight in what's being shared.")
    elif "forward_energy" in detected:
        field_lines.append("Something wants to move forward.")
    elif "collective_pause" in detected:
        field_lines.append("The room is in a processing state.")
    
    if "unspoken_tension" in detected:
        field_lines.append("Something hasn't been named yet.")
    
    # === WHAT HASN'T LANDED ===
    what_hasnt_landed = None
    
    if "unspoken_tension" in detected:
        what_hasnt_landed = "There may be something that was touched but not resolved. A thought that landed without response."
    elif "recent_silence" in detected:
        what_hasnt_landed = "Someone stepped back. It might be processing, or it might be retreat."
    elif "heavy_silence" in detected:
        what_hasnt_landed = "The invitation to enter hasn't been taken up by most. Something about the space may not feel safe or ready."
    elif "pacing_mismatch" in detected:
        what_hasnt_landed = "The different tempos haven't found sync yet. Some are ahead, others behind."
    
    # === WHAT THE ROOM NEEDS ===
    what_room_needs = None
    
    if temperature == "charged":
        what_room_needs = "The room might need acknowledgment before action. Something wants to be seen."
    elif temperature == "cool" or frequency == "dormant":
        what_room_needs = "The room might need a first move. Someone to open."
    elif "pacing_mismatch" in detected:
        what_room_needs = "The room might need those moving fast to pause, or those processing to signal they're still here."
    elif "collective_pause" in detected:
        what_room_needs = "The room might need more time. Let things land before the next thing."
    else:
        what_room_needs = "The room might just need presence. People showing up without forcing."
    
    # === YOUR SHIFT PROMPT ===
    your_shift = None
    
    if "heavy_silence" in detected:
        your_shift = "You might ask: What would make it safe for me to enter here?"
    elif "recent_silence" in detected:
        your_shift = "You might notice: Who went quiet, and does that change how I show up?"
    elif "pacing_mismatch" in detected:
        your_shift = "You might check: Am I moving at my pace, or the room's pace?"
    elif "unspoken_tension" in detected:
        your_shift = "You might ask: What am I not saying that might help?"
    elif temperature == "charged":
        your_shift = "You might pause before adding to the charge. What would help the field settle?"
    elif temperature == "cool":
        your_shift = "You might be the one who opens. What would you want to share first?"
    else:
        your_shift = "You might just notice: What is this space asking of me right now?"
    
    return {
        "field_reading": "\n".join(field_lines),
        "what_hasnt_landed": what_hasnt_landed,
        "what_room_needs": what_room_needs,
        "your_shift": your_shift,
        "field_temperature": temperature,
        "detected_dynamics": detected,
    }


# =============================================================================
# LAYER 4: OPTIONAL IDENTITY LAYER (Light Touch)
# =============================================================================

def add_identity_context(
    language: Dict[str, Any],
    signals: Dict[str, Any],
    member_tendencies: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Optionally add light identity context AFTER the field is described.
    
    NEVER leads with "Manifestors are..." or "Type 5s tend to..."
    
    Only uses tendency language:
    - "Some move fast, others take time to sense"
    - "Different tempos are natural here"
    """
    
    # Only add if we have real data and there's pacing mismatch
    if "pacing_mismatch" not in language.get("detected_dynamics", []):
        return language
    
    # Add a light touch observation (NO TYPES NAMED)
    identity_note = "This group has different natural tempos. Some move when they feel it, others need time to land first. Neither is wrong."
    
    language["identity_note"] = identity_note
    
    return language


# =============================================================================
# LAYER 5: YOUR POSITION IN THE FIELD
# =============================================================================

def detect_user_position(
    signals: Dict[str, Any],
    patterns: Dict[str, Any],
    user_id: str,
) -> Dict[str, Any]:
    """
    Determine the user's role in current field dynamics.
    
    Positions:
    - initiating: User is one of the active voices moving things forward
    - holding_back: User has been quieter than their usual or than others
    - bridging: User's activity sits between extremes
    - observing: User is present but hasn't engaged recently
    
    NO PERSONALITY REFERENCES. Pure behavioral observation.
    """
    
    member_activity = signals.get("member_activity", {})
    user_data = member_activity.get(user_id, {})
    
    user_total = (
        user_data.get("updates", 0) + 
        user_data.get("reflections", 0) + 
        user_data.get("chat_messages", 0)
    )
    
    # Calculate group average
    all_totals = []
    for uid, data in member_activity.items():
        total = data.get("updates", 0) + data.get("reflections", 0) + data.get("chat_messages", 0)
        all_totals.append(total)
    
    avg_activity = sum(all_totals) / len(all_totals) if all_totals else 0
    max_activity = max(all_totals) if all_totals else 0
    
    # Determine position
    position = "observing"  # default
    
    if user_total == 0:
        position = "observing"
    elif max_activity > 0 and user_total >= max_activity * 0.7:
        position = "initiating"
    elif avg_activity > 0 and user_total < avg_activity * 0.5:
        position = "holding_back"
    elif avg_activity > 0:
        position = "bridging"
    
    # Check if user recently went quiet (was active but stopped)
    recently_quiet = signals.get("recently_quiet", [])
    if user_id in recently_quiet:
        position = "withdrawing"
    
    return {
        "position": position,
        "user_activity": user_total,
        "avg_activity": round(avg_activity, 1),
        "is_most_active": user_total == max_activity and max_activity > 0,
    }


def generate_position_language(
    position_data: Dict[str, Any],
    patterns: Dict[str, Any],
) -> str:
    """
    Generate 1-2 lines describing user's position in the field.
    
    Mirror voice: observational, present-tense, no advice.
    """
    
    position = position_data.get("position", "observing")
    is_most_active = position_data.get("is_most_active", False)
    detected = patterns.get("detected_patterns", [])
    
    # Position-specific language
    if position == "initiating":
        if is_most_active:
            return "You're one of the ones moving this forward. The space has felt your presence."
        else:
            return "You've been active here. Your voice is part of what's shaping this."
    
    elif position == "holding_back":
        if "forward_energy" in detected:
            return "You're quieter than usual here. The room is moving, but you're not in step with it yet."
        else:
            return "You've been holding back. Something may be keeping you from entering fully."
    
    elif position == "withdrawing":
        return "You were here, and then you went quiet. That shift is part of what the room is feeling."
    
    elif position == "bridging":
        if "pacing_mismatch" in detected:
            return "You're somewhere in the middle. Not pushing, not withdrawing. Watching the tempo."
        else:
            return "You're present, pacing with the room. Neither leading nor trailing."
    
    elif position == "observing":
        if "heavy_silence" in detected:
            return "You haven't entered yet. You're one of the many waiting."
        else:
            return "You're watching from the edge. Present, but not yet in the conversation."
    
    return "Your position in this field is still forming."


# =============================================================================
# LAYER 6: TRAJECTORY (IF NOTHING CHANGES)
# =============================================================================

def detect_trajectory(
    signals: Dict[str, Any],
    patterns: Dict[str, Any],
    position_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Predict near-term relational direction based on current signals.
    
    Trajectories:
    - disengagement: People are pulling away
    - misalignment: Pacing/energy differences growing
    - tension_building: Unspoken things accumulating
    - stagnation: Nothing moving, energy draining
    - fragmentation: Group splitting into subgroups
    - stabilizing: Things finding a rhythm (positive)
    
    NO DETERMINISTIC LANGUAGE. Observational, possibility-based.
    """
    
    detected = patterns.get("detected_patterns", [])
    frequency = signals.get("frequency_pattern", "dormant")
    temperature = patterns.get("field_temperature", "still")
    timing_gaps = signals.get("timing_gaps", [])
    recently_quiet = signals.get("recently_quiet", [])
    silent_count = len(signals.get("silent_members", []))
    member_count = signals.get("member_count", 0)
    total_activity = signals.get("total_activity", 0)
    distribution = signals.get("activity_distribution", {})
    
    trajectory = "unclear"
    severity = "low"
    
    # Disengagement signals - be more sensitive
    if len(recently_quiet) >= 1 or frequency == "fading":
        trajectory = "disengagement"
        severity = "moderate" if len(recently_quiet) >= 2 else "low"
    
    # Tension building - check emotional markers
    elif "unspoken_tension" in detected:
        trajectory = "tension_building"
        severity = "moderate" if "emotional_weight" in detected else "low"
    
    # Misalignment - pacing issues
    elif "pacing_mismatch" in detected:
        trajectory = "misalignment"
        severity = "moderate" if temperature == "charged" else "low"
    
    # Stagnation - dormant or minimal activity with multiple members
    elif frequency == "dormant" and member_count >= 3:
        trajectory = "stagnation"
        severity = "low"
    elif frequency == "sporadic" and silent_count > member_count / 2:
        trajectory = "stagnation"
        severity = "low"
    
    # Fragmentation - high spread in activity
    elif distribution.get("spread", 0) >= 3 and total_activity > 2:
        trajectory = "fragmentation"
        severity = "low"
    
    # Recent silence pattern - someone withdrew
    elif "recent_silence" in detected:
        trajectory = "disengagement"
        severity = "low"
    
    # Stabilizing (positive) - active without tension
    elif frequency == "active" and "pacing_mismatch" not in detected and "unspoken_tension" not in detected:
        trajectory = "stabilizing"
        severity = "positive"
    
    return {
        "trajectory": trajectory,
        "severity": severity,
    }


def generate_trajectory_language(
    trajectory_data: Dict[str, Any],
    position_data: Dict[str, Any],
) -> str:
    """
    Generate 1-2 lines about what happens if nothing changes.
    
    Creates gentle urgency without pressure.
    Mirror voice: observational, possibility-based.
    """
    
    trajectory = trajectory_data.get("trajectory", "unclear")
    severity = trajectory_data.get("severity", "low")
    user_position = position_data.get("position", "observing")
    
    # Trajectory-specific language
    if trajectory == "disengagement":
        if severity == "moderate":
            return "If this continues, some may disengage quietly. Presence fades before it's noticed."
        else:
            return "The pull away has started. It's subtle, but it's there."
    
    elif trajectory == "tension_building":
        if severity == "moderate":
            return "If this stays unspoken, it doesn't go away. It waits. It compounds."
        else:
            return "Something is building. It hasn't surfaced, but it's accumulating."
    
    elif trajectory == "misalignment":
        if user_position == "initiating":
            return "The gap between movers and processors may widen. Some may feel left behind."
        elif user_position == "holding_back":
            return "The room may move without you. Not intentionally, but because momentum doesn't wait."
        else:
            return "If the tempo differences stay unnamed, people may stop trying to sync."
    
    elif trajectory == "stagnation":
        return "Without movement, energy drains quietly. Waiting becomes the default."
    
    elif trajectory == "fragmentation":
        return "The group may split into pockets. Those connecting may stop trying to include those who aren't."
    
    elif trajectory == "stabilizing":
        return "Something is finding its rhythm here. The field is settling into itself."
    
    return None  # No trajectory language if unclear


# =============================================================================
# LAYER 7: THE MOVE (subtle action opening)
# =============================================================================

def calculate_signal_confidence(
    signals: Dict[str, Any],
    patterns: Dict[str, Any],
    trajectory_data: Dict[str, Any],
) -> str:
    """
    Calculate confidence level in field signals.
    
    Returns: 'high', 'medium', or 'low'
    
    High confidence required for THE MOVE to appear.
    """
    total_activity = signals.get("total_activity", 0)
    member_count = signals.get("member_count", 0)
    detected_patterns = patterns.get("detected_patterns", [])
    trajectory = trajectory_data.get("trajectory", "unclear")
    
    # High confidence: multiple signals aligning
    if total_activity >= 3 and len(detected_patterns) >= 2 and trajectory != "unclear":
        return "high"
    
    # Medium confidence: some signals present
    if total_activity >= 2 and len(detected_patterns) >= 1:
        return "medium"
    
    # Low confidence: minimal data
    return "low"


def generate_the_move(
    signals: Dict[str, Any],
    patterns: Dict[str, Any],
    position_data: Dict[str, Any],
    trajectory_data: Dict[str, Any],
    confidence: str,
) -> Optional[str]:
    """
    Generate THE MOVE - a subtle action opening.
    
    NOT advice. NOT instruction. NOT prescriptive.
    
    A felt sense of what is available next.
    
    Only appears when confidence is HIGH.
    """
    
    # Only show when confidence is high
    if confidence != "high":
        return None
    
    trajectory = trajectory_data.get("trajectory", "unclear")
    user_position = position_data.get("position", "observing")
    detected = patterns.get("detected_patterns", [])
    temperature = patterns.get("field_temperature", "still")
    
    # === THE MOVE based on trajectory + position ===
    
    # Disengagement trajectory
    if trajectory == "disengagement":
        if user_position == "initiating":
            return "There's space here to reach back without pulling."
        elif user_position == "observing":
            return "Something small could be enough to stay connected."
        else:
            return "Presence alone might be the move. Not fixing, just staying."
    
    # Tension building trajectory
    elif trajectory == "tension_building":
        if "emotional_weight" in detected:
            return "Something here could be named. Not solved, just named."
        else:
            return "There's something waiting to be said. It doesn't have to be everything."
    
    # Misalignment trajectory
    elif trajectory == "misalignment":
        if user_position == "initiating":
            return "There's space here to slow this down without stopping it."
        elif user_position == "holding_back":
            return "A signal that you're still here might be enough."
        else:
            return "The gap doesn't have to be bridged all at once."
    
    # Stagnation trajectory
    elif trajectory == "stagnation":
        if user_position in ["observing", "holding_back"]:
            return "One small thing could shift the stillness."
        else:
            return "Movement doesn't have to be big to matter."
    
    # Fragmentation trajectory
    elif trajectory == "fragmentation":
        return "You don't have to carry this forward alone."
    
    # Stabilizing trajectory (positive)
    elif trajectory == "stabilizing":
        return "What's working here could be named. Not to fix it, but to honor it."
    
    # Field-specific moves based on temperature
    if temperature == "charged":
        return "There's space to let this settle before the next thing."
    elif temperature == "cool":
        return "Something could open this. It doesn't have to be the right thing."
    
    return None


# =============================================================================
# MAIN API FUNCTION
# =============================================================================

async def generate_forum_live_field(
    db,
    forum_id: str,
    user_id: str,
) -> Dict[str, Any]:
    """
    Generate a live field reading for a forum.
    
    Returns present-tense, situational language about what's happening NOW.
    
    Layers:
    1. Signal Extraction - Raw activity data
    2. Field Pattern Detection - Dynamics without personality
    3. Field Language - Present-tense room reading
    4. Optional Identity Context - Light touch
    5. YOUR POSITION - Where user sits in the field
    6. TRAJECTORY - What happens if nothing changes
    7. THE MOVE - Subtle action opening (only when confidence is high)
    """
    logger.info(f"[ForumLiveField] Generating for forum {forum_id}")
    
    try:
        # Layer 1: Extract signals
        signals = await extract_activity_signals(db, forum_id, lookback_days=14)
        
        # Layer 2: Detect field patterns
        patterns = detect_field_patterns(signals)
        
        # Layer 3: Generate language
        language = generate_field_language(signals, patterns)
        
        # Layer 4: Optional identity context (light touch)
        language = add_identity_context(language, signals)
        
        # Layer 5: YOUR POSITION IN THE FIELD
        position_data = detect_user_position(signals, patterns, user_id)
        position_language = generate_position_language(position_data, patterns)
        
        # Layer 6: TRAJECTORY (IF NOTHING CHANGES)
        trajectory_data = detect_trajectory(signals, patterns, position_data)
        trajectory_language = generate_trajectory_language(trajectory_data, position_data)
        
        # Layer 7: THE MOVE (subtle action opening)
        signal_confidence = calculate_signal_confidence(signals, patterns, trajectory_data)
        the_move = generate_the_move(signals, patterns, position_data, trajectory_data, signal_confidence)
        
        logger.info(f"[ForumLiveField] Generated: temp={language['field_temperature']}, position={position_data['position']}, trajectory={trajectory_data['trajectory']}, confidence={signal_confidence}, has_move={the_move is not None}")
        
        return {
            "success": True,
            "forum_id": forum_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            
            # Core field reading
            "field_reading": language["field_reading"],
            "what_hasnt_landed": language.get("what_hasnt_landed"),
            "what_room_needs": language.get("what_room_needs"),
            "your_shift": language.get("your_shift"),
            
            # Your position in the field
            "your_position": position_language,
            "your_position_type": position_data["position"],
            
            # Trajectory (if nothing changes)
            "trajectory": trajectory_language,
            "trajectory_type": trajectory_data["trajectory"],
            "trajectory_severity": trajectory_data["severity"],
            
            # THE MOVE (subtle action opening) - only when confidence is high
            "the_move": the_move,
            "signal_confidence": signal_confidence,
            
            # Metadata
            "field_temperature": language["field_temperature"],
            "detected_dynamics": language["detected_dynamics"],
            "identity_note": language.get("identity_note"),
            
            # Debug data (for development)
            "debug": {
                "member_count": signals["member_count"],
                "total_activity": signals["total_activity"],
                "silent_count": len(signals["silent_members"]),
                "frequency_pattern": signals["frequency_pattern"],
                "user_activity": position_data["user_activity"],
                "avg_activity": position_data["avg_activity"],
            }
        }
        
    except Exception as e:
        logger.error(f"[ForumLiveField] Error: {e}")
        raise
