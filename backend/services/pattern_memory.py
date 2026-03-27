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

# Copy variants for each pattern family × exposure state
PATTERN_COPY_VARIANTS = {
    "stall": {
        ExposureState.FIRST_EXPOSURE: {
            "headline": "The Pause",
            "opening": "Something is holding you back before you move.",
            "explanation": "There is real force here—initiating energy that wants to move. But it's meeting something that isn't ready.",
            "reflection_prompt": "Does this feel true right now?",
        },
        ExposureState.REPEATED_EXPOSURE: {
            "headline": "The Pause",
            "opening": "You've seen this before. The pause isn't random.",
            "explanation": "This is still active. The same holding pattern is showing up again—which means something hasn't shifted yet.",
            "reflection_prompt": "What's still not ready?",
            "time_words": ["still", "again"],
        },
        ExposureState.PERSISTENT_PATTERN: {
            "headline": "The Pause (Persistent)",
            "opening": "This pattern is staying. Something is not ready—or not being faced.",
            "explanation": "You've encountered this multiple times now. When a pause keeps returning, it's no longer about timing—it's about what you're avoiding or what genuinely needs to develop.",
            "reflection_prompt": "What would shift if you stopped waiting?",
            "time_words": ["keeps returning", "won't let go"],
        },
        ExposureState.ENGAGED_PATTERN: {
            "headline": "The Pause",
            "opening": "You've already noticed this. Now it's about what you do with it.",
            "explanation": "You've engaged with this pattern before. The insight exists—the question is whether action has followed, or whether the knowing is enough for now.",
            "reflection_prompt": "What's changed since you first noticed this?",
            "time_words": ["already", "since then"],
        },
    },
    "push_pull": {
        ExposureState.FIRST_EXPOSURE: {
            "headline": "The Crossroads",
            "opening": "You're standing between two valid directions.",
            "explanation": "Both pulls are real. The tension isn't confusion—it's competing truths that haven't resolved.",
            "reflection_prompt": "Which direction has more weight right now?",
        },
        ExposureState.REPEATED_EXPOSURE: {
            "headline": "The Crossroads",
            "opening": "Still at the crossroads. The tension hasn't resolved.",
            "explanation": "This same fork is appearing again. Something is keeping you from choosing—and that something may be worth understanding.",
            "reflection_prompt": "What would you lose by choosing?",
            "time_words": ["still", "hasn't resolved"],
        },
        ExposureState.PERSISTENT_PATTERN: {
            "headline": "The Crossroads (Recurring)",
            "opening": "You keep coming back here. The crossroads isn't going away.",
            "explanation": "This isn't a moment—it's becoming a pattern. The inability to choose may itself be the message.",
            "reflection_prompt": "Is the staying at the crossroads serving something?",
            "time_words": ["keeps appearing", "coming back"],
        },
        ExposureState.ENGAGED_PATTERN: {
            "headline": "The Crossroads",
            "opening": "You know this tension. What's shifted since you first saw it?",
            "explanation": "You've engaged with this before. The crossroads is familiar now—the question is whether that familiarity has brought clarity or just comfort.",
            "reflection_prompt": "What's different this time?",
            "time_words": ["familiar now", "since then"],
        },
    },
    "expression": {
        ExposureState.FIRST_EXPOSURE: {
            "headline": "The Held Voice",
            "opening": "Something wants to be said but isn't being said.",
            "explanation": "The silence isn't empty. There's truth in there—held back by timing, fear, or protection.",
            "reflection_prompt": "What would happen if you said it?",
        },
        ExposureState.REPEATED_EXPOSURE: {
            "headline": "The Held Voice",
            "opening": "That unsaid thing is still there. It's not going away.",
            "explanation": "You've noticed this before—the thing you're not expressing. Its persistence means it matters.",
            "reflection_prompt": "What's the cost of continuing to hold it?",
            "time_words": ["still", "not going away"],
        },
        ExposureState.PERSISTENT_PATTERN: {
            "headline": "The Held Voice (Building)",
            "opening": "The pressure to express is building. Something will eventually come out.",
            "explanation": "When the same truth keeps pressing against the silence, it finds a way out—often sideways. The question is whether you choose how it emerges.",
            "reflection_prompt": "What if you chose the moment?",
            "time_words": ["building", "pressing"],
        },
        ExposureState.ENGAGED_PATTERN: {
            "headline": "The Held Voice",
            "opening": "You're aware of what you're holding. Has any of it been released?",
            "explanation": "You've sat with this. The awareness is there. Now the question is action—or the decision that silence is right for now.",
            "reflection_prompt": "Is the holding still wise?",
            "time_words": ["aware", "sat with this"],
        },
    },
    "clarity": {
        ExposureState.FIRST_EXPOSURE: {
            "headline": "The Fog",
            "opening": "Understanding hasn't landed yet.",
            "explanation": "The fog isn't confusion—it's protection against premature certainty. Sometimes not-knowing is wisdom.",
            "reflection_prompt": "What are you trying to figure out?",
        },
        ExposureState.REPEATED_EXPOSURE: {
            "headline": "The Fog",
            "opening": "Still in the fog. That's information too.",
            "explanation": "If clarity hasn't come despite your attention, the fog itself may be the message. Something isn't ready to be seen yet.",
            "reflection_prompt": "What if the fog is protecting you from something?",
            "time_words": ["still", "hasn't come"],
        },
        ExposureState.PERSISTENT_PATTERN: {
            "headline": "The Fog (Extended)",
            "opening": "The fog is staying longer than expected. Pay attention to that.",
            "explanation": "Extended uncertainty often means the question isn't ripe yet—or the question itself is wrong. What you're trying to understand may not be the real issue.",
            "reflection_prompt": "Are you asking the right question?",
            "time_words": ["staying", "extended"],
        },
        ExposureState.ENGAGED_PATTERN: {
            "headline": "The Fog",
            "opening": "You've been sitting with this uncertainty. Has anything shifted underneath?",
            "explanation": "Sometimes clarity comes not through thinking but through living. The answer may already be forming—just not in words yet.",
            "reflection_prompt": "What do you sense but can't say?",
            "time_words": ["sitting with", "forming"],
        },
    },
    "control": {
        ExposureState.FIRST_EXPOSURE: {
            "headline": "The Grip",
            "opening": "You're holding something tightly—maybe too tightly.",
            "explanation": "The control isn't wrong—it's responding to real instability. But the grip may be creating more tension than it solves.",
            "reflection_prompt": "What are you afraid will happen if you let go?",
        },
        ExposureState.REPEATED_EXPOSURE: {
            "headline": "The Grip",
            "opening": "Still holding. The grip hasn't loosened.",
            "explanation": "You noticed this before—and it's still here. The thing you're trying to control is still slipping, or the fear hasn't eased.",
            "reflection_prompt": "What would loosen the grip?",
            "time_words": ["still", "hasn't loosened"],
        },
        ExposureState.PERSISTENT_PATTERN: {
            "headline": "The Grip (Exhausting)",
            "opening": "The holding is becoming exhausting. Something has to give.",
            "explanation": "Persistent control is a signal that the underlying issue isn't being addressed. You can't grip your way to stability.",
            "reflection_prompt": "What would stability actually look like?",
            "time_words": ["exhausting", "persistent"],
        },
        ExposureState.ENGAGED_PATTERN: {
            "headline": "The Grip",
            "opening": "You know you're holding tight. Has the fear underneath changed?",
            "explanation": "Awareness of the grip is the first step. The second is understanding what's really at risk. Sometimes the grip protects nothing.",
            "reflection_prompt": "What's actually at risk?",
            "time_words": ["know", "underneath"],
        },
    },
    "movement": {
        ExposureState.FIRST_EXPOSURE: {
            "headline": "The Push",
            "opening": "There's momentum here—energy wanting to move forward.",
            "explanation": "Forward motion is present. The question isn't whether to move—it's whether the timing is aligned or ahead of itself.",
            "reflection_prompt": "Is the push coming from readiness or impatience?",
        },
        ExposureState.REPEATED_EXPOSURE: {
            "headline": "The Push",
            "opening": "The forward energy is still here. Something wants to happen.",
            "explanation": "You felt this before—and it's returned. The persistence of the push suggests it's real, not just a passing impulse.",
            "reflection_prompt": "What's blocking the movement?",
            "time_words": ["still", "returned"],
        },
        ExposureState.PERSISTENT_PATTERN: {
            "headline": "The Push (Urgent)",
            "opening": "The push keeps coming. Something is ready—or thinks it is.",
            "explanation": "When momentum is this persistent, either the timing is truly right or you're ahead of the field. Only action will reveal which.",
            "reflection_prompt": "What would you regret more—moving or waiting?",
            "time_words": ["keeps coming", "persistent"],
        },
        ExposureState.ENGAGED_PATTERN: {
            "headline": "The Push",
            "opening": "You've felt this momentum before. Did you act on it?",
            "explanation": "You've engaged with this forward energy. The question now is whether the last action created movement—or whether it's still incomplete.",
            "reflection_prompt": "What happened last time?",
            "time_words": ["before", "last time"],
        },
    },
    "release": {
        ExposureState.FIRST_EXPOSURE: {
            "headline": "The Release",
            "opening": "Something is ready to be let go.",
            "explanation": "The letting go is already in motion. The question is whether you're fighting it or allowing it.",
            "reflection_prompt": "What's leaving?",
        },
        ExposureState.REPEATED_EXPOSURE: {
            "headline": "The Release",
            "opening": "Still releasing. The process isn't complete.",
            "explanation": "You're in the middle of letting go—and that middle can feel unstable. Trust that release has its own timing.",
            "reflection_prompt": "What's still holding?",
            "time_words": ["still", "middle of"],
        },
        ExposureState.PERSISTENT_PATTERN: {
            "headline": "The Release (Ongoing)",
            "opening": "The release is taking longer than expected. There's more to let go.",
            "explanation": "When release is this extended, there are layers. What you thought you were letting go of may be connected to something deeper.",
            "reflection_prompt": "What's underneath what you're releasing?",
            "time_words": ["ongoing", "layers"],
        },
        ExposureState.ENGAGED_PATTERN: {
            "headline": "The Release",
            "opening": "You've been consciously letting go. How does it feel now?",
            "explanation": "Active release creates space. The question is what's filling it—or whether the space itself is the point.",
            "reflection_prompt": "What's emerging in the space?",
            "time_words": ["consciously", "now"],
        },
    },
}


def get_state_aware_copy(
    pattern_family: str,
    exposure_state: ExposureState,
    base_pattern_title: str = None,
) -> Dict[str, str]:
    """
    Get copy variants based on pattern family and exposure state.
    Returns opening, explanation, and reflection prompt that evolve with exposure.
    """
    
    # Get variants for this pattern family
    family_variants = PATTERN_COPY_VARIANTS.get(pattern_family, PATTERN_COPY_VARIANTS.get("stall"))
    
    # Get state-specific copy
    state_copy = family_variants.get(exposure_state, family_variants.get(ExposureState.FIRST_EXPOSURE))
    
    return {
        "headline": state_copy.get("headline", base_pattern_title or "Pattern Active"),
        "opening": state_copy.get("opening", "Something is surfacing."),
        "explanation": state_copy.get("explanation", "A pattern is asking for attention."),
        "reflection_prompt": state_copy.get("reflection_prompt", "Does this feel true?"),
        "time_words": state_copy.get("time_words", []),
        "exposure_state": exposure_state.value,
    }


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
