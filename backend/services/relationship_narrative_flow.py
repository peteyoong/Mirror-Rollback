"""
Relationship Narrative Flow Engine V1.0

Adapted from Forum Live Field for 1:1 RELATIONSHIP dynamics.

5-PART STRUCTURE:
1. FIELD STATE - What's happening between you two right now
2. YOUR POSITION - Where you stand in this dynamic
3. TRAJECTORY - What happens if nothing changes
4. STORY - What this connection tends to become
5. THE MOVE - Subtle action opening

LANGUAGE RULES (Different from Forum):
- Use: "between you", "this connection", "this dynamic", "the two of you"
- Avoid: "the room", "the space", "the circle", "the group"
- More intimate, immediate, emotionally charged
- Still calm, reflective, Mirror-toned

TONE:
- Not a psychological diagnosis
- Not advice
- Observational, present-tense
- One unfolding moment between two people
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import hashlib

logger = logging.getLogger(__name__)


# =============================================================================
# SECTION 1: FIELD STATE (What's happening between you two)
# =============================================================================

RELATIONSHIP_FIELD_STATES = {
    # Based on escalation level and dynamic type
    "level_0": {  # Dormant
        "neutral": [
            "Right now, the connection is quiet.",
            "There's stillness between you.",
            "This dynamic hasn't been activated recently.",
        ],
    },
    "level_1": {  # Present
        "tension": [
            "Something is present between you.",
            "There's a familiar shape forming in this dynamic.",
            "The connection is active, holding something unnamed.",
        ],
        "forward": [
            "There's movement between you right now.",
            "Something is shifting in this connection.",
            "The dynamic is in motion.",
        ],
    },
    "level_2": {  # Recurring
        "tension": [
            "This keeps surfacing between you.",
            "The pattern is back. You've felt this with them before.",
            "Something familiar is circling again in this dynamic.",
        ],
        "forward": [
            "You're both in this now. There's momentum.",
            "The connection is pulling you both somewhere.",
            "Something wants to complete between you.",
        ],
    },
    "level_3": {  # Escalating
        "tension": [
            "This is building between you. It's asking for attention.",
            "The tension is growing. It won't stay quiet much longer.",
            "Something between you is reaching a point.",
        ],
        "forward": [
            "This dynamic is accelerating. You're both in it.",
            "There's heat here. Something is about to shift.",
            "The connection is charged. Something wants to move.",
        ],
    },
}

def generate_relationship_field_state(
    escalation_level: int,
    emotional_tone: str,  # "tension" or "forward"
    seed_hash: int,
) -> str:
    """Generate field state for a relationship dynamic."""
    level_key = f"level_{min(escalation_level, 3)}"
    states = RELATIONSHIP_FIELD_STATES.get(level_key, {})
    
    if emotional_tone not in states:
        emotional_tone = list(states.keys())[0] if states else "neutral"
    
    options = states.get(emotional_tone, RELATIONSHIP_FIELD_STATES["level_0"]["neutral"])
    return options[seed_hash % len(options)]


# =============================================================================
# SECTION 2: YOUR POSITION (Where you stand in this dynamic)
# =============================================================================

RELATIONSHIP_POSITIONS = {
    "initiating": [
        "You're the one moving toward them.",
        "You've been reaching. They may not have met you yet.",
        "You're carrying more of the forward energy here.",
    ],
    "receiving": [
        "You're the one being approached.",
        "They're moving toward you. You're deciding how to respond.",
        "The next step is in your hands.",
    ],
    "holding_back": [
        "You're holding something back from them.",
        "There's a part of this you haven't brought forward yet.",
        "You're present, but not fully in.",
    ],
    "withdrawing": [
        "You've stepped back from this connection.",
        "Something has pulled you away. They may have noticed.",
        "The distance between you grew recently.",
    ],
    "mirroring": [
        "You're reflecting each other right now.",
        "The dynamic is even. Neither is leading.",
        "You're both in the same uncertain place.",
    ],
    "protecting": [
        "You're guarding something in this connection.",
        "There's a boundary you're holding, maybe without naming it.",
        "You're keeping part of yourself back, for a reason.",
    ],
}

def generate_relationship_position(
    user_type: str,
    other_type: str,
    escalation_level: int,
    seed_hash: int,
) -> tuple[str, str]:
    """
    Generate user's position in the relationship dynamic.
    
    Returns: (position_type, position_text)
    """
    # Determine position based on types
    initiating_types = ["initiator", "action_taker", "momentum_carrier", "expresser"]
    receiving_types = ["reflector", "atmospheric_reader", "attunement_holder", "absorber"]
    
    if user_type in initiating_types and other_type in receiving_types:
        position = "initiating"
    elif user_type in receiving_types and other_type in initiating_types:
        position = "receiving"
    elif escalation_level >= 2:
        position = "holding_back" if seed_hash % 2 == 0 else "protecting"
    else:
        position = "mirroring"
    
    options = RELATIONSHIP_POSITIONS.get(position, RELATIONSHIP_POSITIONS["mirroring"])
    return position, options[seed_hash % len(options)]


# =============================================================================
# SECTION 3: TRAJECTORY (What happens if nothing changes)
# =============================================================================

RELATIONSHIP_TRAJECTORIES = {
    "distance_growing": {
        "low": "If this stays unspoken, the gap may widen.",
        "moderate": "The distance between you is growing. It doesn't fix itself.",
        "high": "Without a move, you may drift further apart than either of you want.",
    },
    "tension_building": {
        "low": "Something is building that hasn't been named yet.",
        "moderate": "If this stays unaddressed, it compounds. The tension doesn't fade on its own.",
        "high": "This is reaching a point. What's unsaid is becoming louder.",
    },
    "pattern_repeating": {
        "low": "This dynamic may loop again.",
        "moderate": "The pattern has shown up before. Without something different, it will likely return.",
        "high": "The pattern is entrenched. It will repeat until one of you breaks it.",
    },
    "connection_deepening": {
        "positive": "Something is settling between you. The connection is finding its ground.",
    },
    "stagnation": {
        "low": "Without movement, this may go quiet.",
        "moderate": "The connection could fade if neither of you tends to it.",
    },
}

def generate_relationship_trajectory(
    escalation_level: int,
    is_breakthrough: bool,
    emotional_tone: str,
    seed_hash: int,
) -> tuple[str, str, str]:
    """
    Generate trajectory for relationship.
    
    Returns: (trajectory_type, severity, trajectory_text)
    """
    if is_breakthrough:
        return "connection_deepening", "positive", RELATIONSHIP_TRAJECTORIES["connection_deepening"]["positive"]
    
    if escalation_level >= 3:
        trajectory_type = "tension_building"
        severity = "high"
    elif escalation_level >= 2:
        trajectory_type = "pattern_repeating" if seed_hash % 2 == 0 else "tension_building"
        severity = "moderate"
    elif escalation_level >= 1:
        trajectory_type = "distance_growing" if emotional_tone == "tension" else "stagnation"
        severity = "low"
    else:
        return "stagnation", "low", RELATIONSHIP_TRAJECTORIES["stagnation"]["low"]
    
    trajectories = RELATIONSHIP_TRAJECTORIES.get(trajectory_type, {})
    text = trajectories.get(severity, trajectories.get("low", ""))
    
    return trajectory_type, severity, text


# =============================================================================
# SECTION 4: STORY (What this connection tends to become)
# =============================================================================

RELATIONSHIP_STORIES = {
    ("initiator", "reflector"): [
        "Connections like this often find a rhythm over time. One moves, one catches. When it works, there's a dance. When it doesn't, one feels pushed and the other unseen.",
        "This kind of dynamic can deepen into real trust—or wear itself out in mismatched timing. It depends on whether you learn each other's rhythm.",
    ],
    ("reflector", "initiator"): [
        "In relationships like this, one often waits while the other moves. The question is whether the waiting feels like presence or absence.",
        "This dynamic can become a source of grounding—or frustration. It depends on whether the pace difference becomes a feature, not a flaw.",
    ],
    ("initiator", "initiator"): [
        "When two people both move forward, the connection can catch fire—or burn out. There's energy here, but it needs somewhere to go.",
        "Connections between two movers can be exciting and exhausting. The key is learning when to lead and when to follow.",
    ],
    ("reflector", "reflector"): [
        "When two people both wait, the silence can become intimacy—or distance. Someone eventually has to break the stillness.",
        "This kind of connection often needs a catalyst. Without one, it may remain potential without becoming real.",
    ],
    "default": [
        "Every connection has its own shape. This one is still finding itself. What it becomes depends on what you both bring.",
        "Relationships like this don't arrive finished. They're made, moment by moment, in the choices you each make toward the other.",
    ],
}

def generate_relationship_story(
    user_type: str,
    other_type: str,
    seed_hash: int,
) -> str:
    """Generate the story of what this connection tends to become."""
    # Simplify to initiator/reflector
    initiating_types = ["initiator", "action_taker", "momentum_carrier", "expresser"]
    
    user_archetype = "initiator" if user_type in initiating_types else "reflector"
    other_archetype = "initiator" if other_type in initiating_types else "reflector"
    
    pair = (user_archetype, other_archetype)
    stories = RELATIONSHIP_STORIES.get(pair, RELATIONSHIP_STORIES["default"])
    
    return stories[seed_hash % len(stories)]


# =============================================================================
# SECTION 5: THE MOVE (Subtle action opening)
# =============================================================================

RELATIONSHIP_MOVES = {
    "initiating": [
        "There's space to slow your approach without pulling away.",
        "You could name what you're reaching for. Not to demand, just to make it visible.",
    ],
    "receiving": [
        "There's room to respond without committing to everything.",
        "A small signal might be enough. You don't have to decide it all now.",
    ],
    "holding_back": [
        "What you're holding back could be shared. Not all of it—just enough to be seen.",
        "You could let them in without letting go of your ground.",
    ],
    "withdrawing": [
        "Returning doesn't mean forgetting why you stepped back.",
        "A small move toward them doesn't undo the space you needed.",
    ],
    "tension_building": [
        "Something could be named between you. Not solved—just named.",
        "The tension doesn't need to be resolved. It just needs acknowledgment.",
    ],
    "distance_growing": [
        "One of you could close the gap. It doesn't have to be a big move.",
        "Reaching out doesn't mean pretending nothing happened.",
    ],
    "pattern_repeating": [
        "One different choice could interrupt the loop.",
        "You don't have to break the whole pattern. Just this one moment.",
    ],
    "default": [
        "There's a move available here. It doesn't have to be the right one.",
        "Something small could shift this. You don't have to solve it.",
    ],
}

def generate_relationship_move(
    position_type: str,
    trajectory_type: str,
    seed_hash: int,
    confidence: str = "high",
) -> Optional[str]:
    """
    Generate THE MOVE for a relationship.
    
    Only returns when confidence is high.
    """
    if confidence != "high":
        return None
    
    # Prioritize trajectory-based moves for tension/pattern situations
    if trajectory_type in ["tension_building", "distance_growing", "pattern_repeating"]:
        moves = RELATIONSHIP_MOVES.get(trajectory_type, RELATIONSHIP_MOVES["default"])
    else:
        moves = RELATIONSHIP_MOVES.get(position_type, RELATIONSHIP_MOVES["default"])
    
    return moves[seed_hash % len(moves)]


# =============================================================================
# MAIN GENERATOR
# =============================================================================

def generate_relationship_narrative_flow(
    user_id: str,
    other_name: str,
    user_type: str,
    other_type: str,
    escalation_level: int,
    is_breakthrough: bool,
    breakthrough_confidence: int,
    seed_hash: int,
) -> Dict[str, Any]:
    """
    Generate complete 5-part Relationship Narrative Flow.
    
    Returns a dictionary suitable for the frontend narrative flow component.
    """
    logger.info(f"[RelationshipNarrative] Generating for user {user_id}, other={other_name}")
    
    # Determine emotional tone based on escalation and breakthrough
    emotional_tone = "forward" if is_breakthrough else ("tension" if escalation_level >= 2 else "neutral")
    if escalation_level == 0:
        emotional_tone = "neutral"
    
    # 1. FIELD STATE
    field_state = generate_relationship_field_state(
        escalation_level=escalation_level,
        emotional_tone=emotional_tone if emotional_tone != "neutral" else "tension",
        seed_hash=seed_hash,
    )
    
    # 2. YOUR POSITION
    position_type, position_text = generate_relationship_position(
        user_type=user_type,
        other_type=other_type,
        escalation_level=escalation_level,
        seed_hash=seed_hash,
    )
    
    # 3. TRAJECTORY
    trajectory_type, trajectory_severity, trajectory_text = generate_relationship_trajectory(
        escalation_level=escalation_level,
        is_breakthrough=is_breakthrough,
        emotional_tone=emotional_tone,
        seed_hash=seed_hash,
    )
    
    # 4. STORY
    story = generate_relationship_story(
        user_type=user_type,
        other_type=other_type,
        seed_hash=seed_hash,
    )
    
    # 5. THE MOVE
    # Only show when we have high confidence (enough signal)
    signal_confidence = "high" if escalation_level >= 1 or is_breakthrough else "medium"
    the_move = generate_relationship_move(
        position_type=position_type,
        trajectory_type=trajectory_type,
        seed_hash=seed_hash,
        confidence=signal_confidence,
    )
    
    # Determine field temperature
    if is_breakthrough:
        field_temperature = "warm"
    elif escalation_level >= 3:
        field_temperature = "charged"
    elif escalation_level >= 1:
        field_temperature = "present"
    else:
        field_temperature = "quiet"
    
    return {
        "success": True,
        "other_name": other_name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        
        # Narrative flow sections
        "field_state": field_state,
        "your_position": position_text,
        "your_position_type": position_type,
        "trajectory": trajectory_text,
        "trajectory_type": trajectory_type,
        "trajectory_severity": trajectory_severity,
        "story": story,
        "the_move": the_move,
        
        # Metadata
        "field_temperature": field_temperature,
        "escalation_level": escalation_level,
        "is_breakthrough": is_breakthrough,
        "signal_confidence": signal_confidence,
        
        # For debugging
        "debug": {
            "user_type": user_type,
            "other_type": other_type,
            "emotional_tone": emotional_tone,
        }
    }
