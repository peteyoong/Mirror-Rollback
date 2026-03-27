"""
Pattern Memory Service
======================

Tracks user exposure to patterns over time to evolve messaging.
Prevents the same pattern from showing identical text across days.

SCHEMA:
pattern_exposures collection:
{
    user_id: str,
    pattern_id: str,           # e.g., "pause_stall", "premature_initiation"
    pattern_title: str,        # e.g., "The Pause"
    pattern_family: str,       # e.g., "stall"
    first_seen_at: datetime,
    last_seen_at: datetime,
    times_seen_total: int,
    times_seen_7d: int,        # Rolling 7-day count
    last_interaction: str,     # "none", "yes", "no", "reflect", "chat"
    interaction_count: int,
    exposure_dates: [str],     # List of dates (YYYY-MM-DD)
}

EXPOSURE STATES:
- first_exposure: Never seen this pattern
- repeated_exposure: Same pattern within 24-72h
- persistent_pattern: Same pattern 3+ times in rolling window
- engaged_pattern: User has interacted deeply (reflect/chat)
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# HOUSE → LIFE DOMAIN MAPPING
# =============================================================================
# Maps astrological houses to concrete life domains for contextual messaging.
# Used to make pattern messages feel situational and specific.
# =============================================================================

HOUSE_DOMAINS = {
    1: {"domain": "self", "phrases": ["in how you see yourself", "in your sense of who you are", "about your identity"]},
    2: {"domain": "security", "phrases": ["around money", "about security", "with what you value"]},
    3: {"domain": "communication", "phrases": ["in how you communicate", "in a conversation", "with something you need to say"]},
    4: {"domain": "home", "phrases": ["at home", "with family", "about where you belong"]},
    5: {"domain": "creativity", "phrases": ["creatively", "in something you're making", "about expressing yourself"]},
    6: {"domain": "work", "phrases": ["at work", "in your daily routines", "with something practical"]},
    7: {"domain": "relationship", "phrases": ["with someone", "in a relationship", "between you and another person"]},
    8: {"domain": "intensity", "phrases": ["emotionally", "in something deep", "about power or control"]},
    9: {"domain": "expansion", "phrases": ["about what's next", "with a bigger vision", "around meaning"]},
    10: {"domain": "direction", "phrases": ["in your direction", "about your path", "with where you're heading"]},
    11: {"domain": "network", "phrases": ["with a group", "in your network", "about influence"]},
    12: {"domain": "internal", "phrases": ["internally", "in what you're avoiding", "beneath the surface"]},
}

# Fallback phrases when no house context is available
DEFAULT_CONTEXT_PHRASES = ["in your life", "with something", "about what's ahead"]


def get_house_context(house_number: int) -> Dict[str, Any]:
    """Get life domain context for a house number (1-12)."""
    if house_number < 1 or house_number > 12:
        return {"domain": "general", "phrases": DEFAULT_CONTEXT_PHRASES}
    return HOUSE_DOMAINS.get(house_number, {"domain": "general", "phrases": DEFAULT_CONTEXT_PHRASES})


def select_primary_house(transit_aspects: List[Dict], chart_data: Dict = None) -> Optional[int]:
    """
    Select the primary activated house based on transit data.
    
    Priority:
    1. House of natal planet receiving strongest outer planet transit
    2. House of Moon if Moon is transiting
    3. House of Sun
    4. Default to 10 (direction/career) as fallback
    """
    if not transit_aspects:
        return 10  # Default to direction
    
    # Find the strongest transit to a natal planet
    for aspect in transit_aspects:
        natal_point = aspect.get("natal_point", "").lower()
        
        # Try to get house from chart data
        if chart_data:
            planets = chart_data.get("astrology", {}).get("planets", {})
            natal_key = natal_point.replace(" ", "_").lower()
            
            planet_data = planets.get(natal_key, {})
            if isinstance(planet_data, dict):
                house = planet_data.get("house")
                if house:
                    try:
                        return int(house)
                    except:
                        pass
        
        # Use transit point to infer domain if no house data
        transit_point = aspect.get("transit_point", "").lower()
        
        # Map outer planet transits to likely domains
        if transit_point == "saturn":
            return 10  # Career/direction
        elif transit_point == "jupiter":
            return 9   # Expansion/vision
        elif transit_point == "mars":
            return 6   # Work/action
        elif transit_point == "venus":
            return 7   # Relationships
        elif transit_point == "mercury":
            return 3   # Communication
        elif transit_point == "moon":
            return 4   # Home/emotions
        elif transit_point in ["uranus", "neptune", "pluto"]:
            return 8   # Deep transformation
    
    return 10  # Default to direction


class ExposureState(Enum):
    FIRST_EXPOSURE = "first_exposure"
    REPEATED_EXPOSURE = "repeated_exposure"
    PERSISTENT_PATTERN = "persistent_pattern"
    ENGAGED_PATTERN = "engaged_pattern"


async def get_pattern_exposure(
    db,
    user_id: str,
    pattern_id: str,
    pattern_title: str,
    pattern_family: str
) -> Dict[str, Any]:
    """
    Get or create pattern exposure record for a user.
    Returns exposure state and relevant metadata.
    """
    try:
        today = datetime.now(timezone.utc)
        today_str = today.strftime("%Y-%m-%d")
        seven_days_ago = today - timedelta(days=7)
        
        logger.info(f"[PatternMemory] Looking up: user={user_id[:8]}, pattern={pattern_id}")
        
        # Find existing exposure record
        exposure = await db.pattern_exposures.find_one({
            "user_id": user_id,
            "pattern_id": pattern_id
        })
        
        logger.info(f"[PatternMemory] Found exposure: {exposure is not None}")
        
        if exposure:
            logger.info(f"[PatternMemory] Exposure dates: {exposure.get('exposure_dates', [])}")
        
        if not exposure:
            # First time seeing this pattern
            new_exposure = {
                "user_id": user_id,
                "pattern_id": pattern_id,
                "pattern_title": pattern_title,
                "pattern_family": pattern_family,
                "first_seen_at": today,
                "last_seen_at": today,
                "times_seen_total": 1,
                "times_seen_7d": 1,
                "last_interaction": "none",
                "interaction_count": 0,
                "exposure_dates": [today_str],
            }
            await db.pattern_exposures.insert_one(new_exposure)
            
            logger.info(f"[PatternMemory] First exposure for {user_id[:8]}: {pattern_id}")
            
            return {
                "state": ExposureState.FIRST_EXPOSURE,
                "times_seen": 1,
                "times_seen_7d": 1,
                "days_since_last": 0,
                "last_interaction": "none",
                "is_new_day": True,
            }
        
        # Calculate time-based metrics
        last_seen = exposure.get("last_seen_at", today)
        if isinstance(last_seen, str):
            last_seen = datetime.fromisoformat(last_seen.replace("Z", "+00:00"))
        # Handle naive datetime from MongoDB
        if last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)
        
        days_since_last = (today - last_seen).days
        
        # Count exposures in last 7 days
        exposure_dates = exposure.get("exposure_dates", [])
        recent_dates = [d for d in exposure_dates if d >= seven_days_ago.strftime("%Y-%m-%d")]
        times_seen_7d = len(recent_dates)
        
        # Check if this is a new day view
        is_new_day = today_str not in exposure_dates
        
        # Update exposure record if new day
        if is_new_day:
            exposure_dates.append(today_str)
            # Keep only last 30 days of exposure dates
            cutoff = (today - timedelta(days=30)).strftime("%Y-%m-%d")
            exposure_dates = [d for d in exposure_dates if d >= cutoff]
            
            await db.pattern_exposures.update_one(
                {"user_id": user_id, "pattern_id": pattern_id},
                {
                    "$set": {
                        "last_seen_at": today,
                        "exposure_dates": exposure_dates,
                    },
                    "$inc": {
                        "times_seen_total": 1,
                        "times_seen_7d": 1,
                    }
                }
            )
            times_seen_7d += 1
        
        times_seen_total = exposure.get("times_seen_total", 1) + (1 if is_new_day else 0)
        last_interaction = exposure.get("last_interaction", "none")
        interaction_count = exposure.get("interaction_count", 0)
        
        # Determine exposure state
        state = _determine_exposure_state(
            times_seen_7d=times_seen_7d,
            days_since_last=days_since_last,
            last_interaction=last_interaction,
            interaction_count=interaction_count,
        )
        
        logger.info(f"[PatternMemory] {user_id[:8]} viewing {pattern_id}: state={state.value}, seen_7d={times_seen_7d}")
        
        return {
            "state": state,
            "times_seen": times_seen_total,
            "times_seen_7d": times_seen_7d,
            "days_since_last": days_since_last,
            "last_interaction": last_interaction,
            "interaction_count": interaction_count,
            "is_new_day": is_new_day,
        }
        
    except Exception as e:
        logger.error(f"[PatternMemory] Error getting exposure: {e}")
        return {
            "state": ExposureState.FIRST_EXPOSURE,
            "times_seen": 1,
            "times_seen_7d": 1,
            "days_since_last": 0,
            "last_interaction": "none",
            "is_new_day": True,
        }


def _determine_exposure_state(
    times_seen_7d: int,
    days_since_last: int,
    last_interaction: str,
    interaction_count: int,
) -> ExposureState:
    """Determine the exposure state based on metrics."""
    
    # Engaged pattern: User has interacted deeply
    if interaction_count >= 2 or last_interaction in ["reflect", "chat", "explore"]:
        return ExposureState.ENGAGED_PATTERN
    
    # Persistent pattern: Seen 3+ times in 7 days
    if times_seen_7d >= 3:
        return ExposureState.PERSISTENT_PATTERN
    
    # Repeated exposure: Same pattern within 3 days
    if days_since_last <= 3 and times_seen_7d >= 2:
        return ExposureState.REPEATED_EXPOSURE
    
    # First exposure (or long gap)
    return ExposureState.FIRST_EXPOSURE


async def record_pattern_interaction(
    db,
    user_id: str,
    pattern_id: str,
    interaction_type: str,  # "yes", "no", "reflect", "chat", "explore"
) -> None:
    """Record that user interacted with a pattern."""
    try:
        await db.pattern_exposures.update_one(
            {"user_id": user_id, "pattern_id": pattern_id},
            {
                "$set": {"last_interaction": interaction_type},
                "$inc": {"interaction_count": 1}
            }
        )
        logger.info(f"[PatternMemory] Recorded {interaction_type} for {user_id[:8]} on {pattern_id}")
    except Exception as e:
        logger.error(f"[PatternMemory] Error recording interaction: {e}")


# =============================================================================
# STATE-AWARE COPY GENERATION
# =============================================================================
# 
# NEW MESSAGE STRUCTURE (V2):
# 1. BEHAVIOR OR STATE (what the user is doing or feeling)
# 2. INTERNAL SPLIT (tension or contradiction)  
# 3. GROUNDING LINE (why it matters now)
#
# RULES:
# - Use "you", not "this"
# - No "may", "might", "suggests"
# - No abstract terms like "energy", "alignment", "activation"
# - One concrete behavior, one clear tension, short sharp phrasing
# =============================================================================

# Copy variants for each pattern family × exposure state
PATTERN_COPY_VARIANTS = {
    "stall": {
        ExposureState.FIRST_EXPOSURE: {
            "headline": "The Pause",
            # V2: Behavior → Split → Grounding
            "opening": "You're ready to act — but something in you knows it's not clean yet.\nThe push is there. The ground isn't.",
            "explanation": "You're already in motion, but the timing isn't holding. Part of you knows this won't land the way you expect.",
            "reflection_prompt": "What's the part that isn't ready?",
        },
        ExposureState.REPEATED_EXPOSURE: {
            "headline": "The Pause",
            "opening": "You've been here before — the same stall, the same tension.\nSomething still isn't settled.",
            "explanation": "The drive keeps returning, and so does the resistance. That's not random. Something hasn't shifted underneath.",
            "reflection_prompt": "What's still unresolved?",
            "time_words": ["still", "again"],
        },
        ExposureState.PERSISTENT_PATTERN: {
            "headline": "The Pause",
            "opening": "You keep pushing into this — and it keeps not moving.\nThis isn't about timing anymore. It's about what you're avoiding.",
            "explanation": "When the same pause keeps returning, it's asking to be faced, not waited out. The block isn't external.",
            "reflection_prompt": "What would you have to face to actually move?",
            "time_words": ["keeps returning", "won't shift"],
        },
        ExposureState.ENGAGED_PATTERN: {
            "headline": "The Pause",
            "opening": "You've already seen this. The question isn't what — it's what now.\nKnowing hasn't changed the pattern yet.",
            "explanation": "Awareness is here. The gap is between knowing and acting. Something is still holding.",
            "reflection_prompt": "What would actually change this?",
            "time_words": ["already", "now"],
        },
    },
    "push_pull": {
        ExposureState.FIRST_EXPOSURE: {
            "headline": "The Crossroads",
            "opening": "You're pulled in two directions — and both feel real.\nThe tension isn't confusion. It's two truths competing.",
            "explanation": "Neither option is wrong. That's why it's hard. Something has to give, and you're not ready to decide what.",
            "reflection_prompt": "Which pull has more weight right now?",
        },
        ExposureState.REPEATED_EXPOSURE: {
            "headline": "The Crossroads",
            "opening": "You're still standing here. The fork hasn't closed.\nSomething keeps you from choosing.",
            "explanation": "This same tension is returning — which means the answer isn't clear yet, or you're avoiding what choosing would cost.",
            "reflection_prompt": "What are you protecting by not choosing?",
            "time_words": ["still", "keeps returning"],
        },
        ExposureState.PERSISTENT_PATTERN: {
            "headline": "The Crossroads",
            "opening": "You keep coming back here. Same fork, same hesitation.\nThe crossroads isn't going anywhere — and neither are you.",
            "explanation": "At some point, staying at the fork becomes its own choice. The indecision may be serving something.",
            "reflection_prompt": "What's the cost of staying here longer?",
            "time_words": ["keeps appearing", "won't resolve"],
        },
        ExposureState.ENGAGED_PATTERN: {
            "headline": "The Crossroads",
            "opening": "You've looked at this before. The tension is familiar now.\nBut familiarity isn't resolution.",
            "explanation": "You understand the pull. The question is whether understanding has moved anything, or just become comfortable.",
            "reflection_prompt": "What would it take to actually choose?",
            "time_words": ["familiar", "before"],
        },
    },
    "expression": {
        ExposureState.FIRST_EXPOSURE: {
            "headline": "The Held Voice",
            "opening": "There's something you're not saying — and it's sitting in you.\nThe silence isn't peace. It's pressure.",
            "explanation": "The words exist. The permission doesn't. Something is keeping the truth from being spoken.",
            "reflection_prompt": "What would happen if you said it?",
        },
        ExposureState.REPEATED_EXPOSURE: {
            "headline": "The Held Voice",
            "opening": "That unsaid thing is still there. It hasn't gone away.\nHolding it is starting to cost something.",
            "explanation": "You've noticed this before. The silence continues. At some point, what's held becomes heavier than what's said.",
            "reflection_prompt": "What's the cost of holding this longer?",
            "time_words": ["still", "hasn't gone"],
        },
        ExposureState.PERSISTENT_PATTERN: {
            "headline": "The Held Voice",
            "opening": "You keep holding this in. The pressure is building.\nSomething will come out — the question is how.",
            "explanation": "Persistent silence doesn't stay silent. It leaks sideways. The question is whether you choose how it emerges.",
            "reflection_prompt": "What if you chose the moment?",
            "time_words": ["building", "keeps holding"],
        },
        ExposureState.ENGAGED_PATTERN: {
            "headline": "The Held Voice",
            "opening": "You know what you're holding back. Has any of it been released?\nAwareness without action becomes another form of holding.",
            "explanation": "You've engaged with this. The question is whether the holding is still wise, or just familiar.",
            "reflection_prompt": "Is the silence still serving you?",
            "time_words": ["still", "know"],
        },
    },
    "clarity": {
        ExposureState.FIRST_EXPOSURE: {
            "headline": "The Fog",
            "opening": "You're trying to see something that isn't showing itself yet.\nThe uncertainty isn't failure — it's protection.",
            "explanation": "Not everything is meant to be clear right now. Sometimes the fog keeps you from moving too early.",
            "reflection_prompt": "What are you trying to figure out?",
        },
        ExposureState.REPEATED_EXPOSURE: {
            "headline": "The Fog",
            "opening": "Still unclear. The answer hasn't come.\nThat's information too.",
            "explanation": "If clarity hasn't arrived despite your attention, the fog may be the message. Something isn't ready to be seen.",
            "reflection_prompt": "What if the fog is protecting you?",
            "time_words": ["still", "hasn't come"],
        },
        ExposureState.PERSISTENT_PATTERN: {
            "headline": "The Fog",
            "opening": "The fog is lasting longer than expected.\nAt some point, waiting for clarity becomes its own avoidance.",
            "explanation": "Extended uncertainty often means the question is wrong. What you're trying to understand may not be the real issue.",
            "reflection_prompt": "Are you asking the right question?",
            "time_words": ["lasting", "longer"],
        },
        ExposureState.ENGAGED_PATTERN: {
            "headline": "The Fog",
            "opening": "You've sat with this uncertainty. Has anything shifted underneath?\nSometimes clarity comes through living, not thinking.",
            "explanation": "You've engaged with the not-knowing. The answer may already be forming — just not in words yet.",
            "reflection_prompt": "What do you sense but can't say?",
            "time_words": ["underneath", "already"],
        },
    },
    "control": {
        ExposureState.FIRST_EXPOSURE: {
            "headline": "The Grip",
            "opening": "You're holding something tight — tighter than you need to.\nThe grip isn't wrong, but it's exhausting.",
            "explanation": "Control is responding to real instability. But the holding may be creating more tension than it solves.",
            "reflection_prompt": "What are you afraid will happen if you let go?",
        },
        ExposureState.REPEATED_EXPOSURE: {
            "headline": "The Grip",
            "opening": "Still holding. The grip hasn't loosened.\nWhatever you're trying to control is still slipping.",
            "explanation": "The same tension is back. The grip continues. Something isn't being addressed underneath.",
            "reflection_prompt": "What would it take to loosen this?",
            "time_words": ["still", "hasn't loosened"],
        },
        ExposureState.PERSISTENT_PATTERN: {
            "headline": "The Grip",
            "opening": "The holding is becoming exhausting. Something has to give.\nYou can't grip your way to stability.",
            "explanation": "Persistent control is a signal that the underlying issue isn't being faced. The grip is a symptom, not the solution.",
            "reflection_prompt": "What would stability actually look like?",
            "time_words": ["exhausting", "has to give"],
        },
        ExposureState.ENGAGED_PATTERN: {
            "headline": "The Grip",
            "opening": "You know you're holding tight. Has the fear underneath changed?\nSometimes the grip protects nothing.",
            "explanation": "Awareness of the grip is the first step. The second is understanding what's actually at risk.",
            "reflection_prompt": "What's actually at risk?",
            "time_words": ["know", "underneath"],
        },
    },
    "movement": {
        ExposureState.FIRST_EXPOSURE: {
            "headline": "The Push",
            "opening": "There's momentum here — something wants to move forward.\nThe question is whether the timing is right or you're ahead of yourself.",
            "explanation": "Forward motion is real. But moving too early can waste the opening. The push needs to match the ground.",
            "reflection_prompt": "Is this readiness or impatience?",
        },
        ExposureState.REPEATED_EXPOSURE: {
            "headline": "The Push",
            "opening": "The forward pull is still here. Something wants to happen.\nThe persistence suggests it's real, not just impulse.",
            "explanation": "This momentum keeps returning — which means there's something behind it. The question is what's blocking it.",
            "reflection_prompt": "What's blocking the movement?",
            "time_words": ["still", "keeps returning"],
        },
        ExposureState.PERSISTENT_PATTERN: {
            "headline": "The Push",
            "opening": "The push keeps coming. Something is ready — or thinks it is.\nAt some point, waiting becomes its own risk.",
            "explanation": "Persistent momentum often means the timing is closer than you think. Or you're pushing against something immovable.",
            "reflection_prompt": "What would you regret more — moving or waiting?",
            "time_words": ["keeps coming", "ready"],
        },
        ExposureState.ENGAGED_PATTERN: {
            "headline": "The Push",
            "opening": "You've felt this momentum before. Did you act on it?\nThe question now is whether the last movement created change — or incompletion.",
            "explanation": "You've engaged with this forward energy. The pattern reveals whether action followed insight.",
            "reflection_prompt": "What happened last time?",
            "time_words": ["before", "last time"],
        },
    },
    "release": {
        ExposureState.FIRST_EXPOSURE: {
            "headline": "The Release",
            "opening": "Something is ready to be let go — and part of you knows it.\nThe releasing has already started. The question is whether you're fighting it.",
            "explanation": "Letting go doesn't mean it wasn't real. It means its time is complete.",
            "reflection_prompt": "What's leaving?",
        },
        ExposureState.REPEATED_EXPOSURE: {
            "headline": "The Release",
            "opening": "Still releasing. The process isn't complete.\nYou're in the middle of letting go — and that middle is uncomfortable.",
            "explanation": "Release has its own timing. Trust that the process knows where it's going.",
            "reflection_prompt": "What's still holding?",
            "time_words": ["still", "incomplete"],
        },
        ExposureState.PERSISTENT_PATTERN: {
            "headline": "The Release",
            "opening": "The letting go is taking longer than expected. There's more than you thought.\nWhat you're releasing may be connected to something deeper.",
            "explanation": "Extended release means layers. What looked like one thing may be several.",
            "reflection_prompt": "What's underneath what you're releasing?",
            "time_words": ["longer", "deeper"],
        },
        ExposureState.ENGAGED_PATTERN: {
            "headline": "The Release",
            "opening": "You've been consciously letting go. How does it feel now?\nRelease creates space. The question is what's filling it.",
            "explanation": "Active release changes things. The question is whether the space is welcomed or feared.",
            "reflection_prompt": "What's emerging in the space?",
            "time_words": ["consciously", "now"],
        },
    },
}


def get_state_aware_copy(
    pattern_family: str,
    exposure_state: ExposureState,
    base_pattern_title: str = None,
    house_number: int = None,
) -> Dict[str, str]:
    """
    Get copy variants based on pattern family and exposure state.
    Returns opening, explanation, and reflection prompt that evolve with exposure.
    
    If house_number is provided, injects life domain context into the opening.
    """
    
    # Get variants for this pattern family
    family_variants = PATTERN_COPY_VARIANTS.get(pattern_family, PATTERN_COPY_VARIANTS.get("stall"))
    
    # Get state-specific copy
    state_copy = family_variants.get(exposure_state, family_variants.get(ExposureState.FIRST_EXPOSURE))
    
    opening = state_copy.get("opening", "Something is surfacing.")
    
    # Inject house context if available
    if house_number:
        house_context = get_house_context(house_number)
        domain = house_context.get("domain", "general")
        phrases = house_context.get("phrases", DEFAULT_CONTEXT_PHRASES)
        
        # Select a context phrase
        import random
        context_phrase = random.choice(phrases)
        
        # Inject context into the opening based on pattern family
        opening = inject_house_context(opening, pattern_family, context_phrase, domain)
    
    return {
        "headline": state_copy.get("headline", base_pattern_title or "Pattern Active"),
        "opening": opening,
        "explanation": state_copy.get("explanation", "A pattern is asking for attention."),
        "reflection_prompt": state_copy.get("reflection_prompt", "Does this feel true?"),
        "time_words": state_copy.get("time_words", []),
        "exposure_state": exposure_state.value,
        "house_context": house_number if house_number else None,
    }


def inject_house_context(opening: str, pattern_family: str, context_phrase: str, domain: str) -> str:
    """
    Inject house context into the opening line to make it feel situational.
    
    Structure: CONTEXT (where) → BEHAVIOR (what) → SPLIT (tension)
    """
    # Pattern-specific context injection
    if pattern_family == "stall":
        if "ready to act" in opening.lower():
            return f"You're trying to push something forward {context_phrase} — but it's not landing.\nPart of you is already moving. Part of you doesn't trust it yet."
        elif "keep pushing" in opening.lower():
            return f"You keep pushing into this {context_phrase} — and it keeps not moving.\nThis isn't about timing anymore. It's about what you're avoiding."
        elif "been here before" in opening.lower():
            return f"You've been here before — the same stall {context_phrase}, the same tension.\nSomething still isn't settled."
        elif "already seen" in opening.lower():
            return f"You've already seen this {context_phrase}. The question isn't what — it's what now.\nKnowing hasn't changed the pattern yet."
    
    elif pattern_family == "push_pull":
        if "pulled in two" in opening.lower():
            return f"You're pulled in two directions {context_phrase} — and both feel real.\nThe tension isn't confusion. It's two truths competing."
        elif "still standing" in opening.lower():
            return f"You're still standing at the fork {context_phrase}. The tension hasn't closed.\nSomething keeps you from choosing."
        elif "keep coming back" in opening.lower():
            return f"You keep coming back to this crossroads {context_phrase}. Same fork, same hesitation.\nThe crossroads isn't going anywhere — and neither are you."
    
    elif pattern_family == "expression":
        if "not saying" in opening.lower():
            return f"There's something you're not saying {context_phrase} — and it's sitting in you.\nThe silence isn't peace. It's pressure."
        elif "unsaid thing" in opening.lower():
            return f"That unsaid thing {context_phrase} is still there. It hasn't gone away.\nHolding it is starting to cost something."
    
    elif pattern_family == "clarity":
        if "trying to see" in opening.lower():
            return f"You're trying to see something {context_phrase} that isn't showing itself yet.\nThe uncertainty isn't failure — it's protection."
        elif "still unclear" in opening.lower():
            return f"Still unclear {context_phrase}. The answer hasn't come.\nThat's information too."
    
    elif pattern_family == "control":
        if "holding something tight" in opening.lower():
            return f"You're holding something tight {context_phrase} — tighter than you need to.\nThe grip isn't wrong, but it's exhausting."
    
    elif pattern_family == "movement":
        if "momentum here" in opening.lower():
            return f"There's momentum here {context_phrase} — something wants to move forward.\nThe question is whether the timing is right or you're ahead of yourself."
    
    elif pattern_family == "release":
        if "ready to be let go" in opening.lower():
            return f"Something {context_phrase} is ready to be let go — and part of you knows it.\nThe releasing has already started. The question is whether you're fighting it."
    
    # Default: prepend context
    return opening


def apply_time_context_to_copy(
    copy: Dict[str, str],
    exposure_data: Dict[str, Any],
) -> Dict[str, str]:
    """
    Add micro-time context words to make messaging feel continuous.
    Adds words like "still", "again", "coming back" based on exposure history.
    """
    times_seen = exposure_data.get("times_seen_7d", 1)
    days_since_last = exposure_data.get("days_since_last", 0)
    
    # Add continuity markers
    continuity_marker = ""
    if times_seen >= 4:
        continuity_marker = "This keeps showing up. "
    elif times_seen >= 2 and days_since_last <= 2:
        continuity_marker = "Still here. "
    elif times_seen >= 2 and days_since_last <= 5:
        continuity_marker = "Coming back. "
    
    if continuity_marker and copy.get("opening"):
        # Don't double-add if already present
        if not any(word in copy["opening"].lower() for word in ["still", "again", "keep", "coming back"]):
            copy["opening"] = continuity_marker + copy["opening"]
    
    return copy
