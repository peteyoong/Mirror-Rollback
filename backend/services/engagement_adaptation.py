"""
Engagement Adaptation Layer for Mirror Home - V1
=================================================

PROBLEM: Mirror doesn't adapt based on whether user actually engaged.
SOLUTION: Track engagement, derive state, adapt next Home output.

ENGAGEMENT STATES:
- captured: User interacted OR spent > threshold time
- skimmed: Time > threshold but no interaction
- bounced: Time < threshold AND no interaction

ADAPTATION RULES:
- IF bounced: Sharper hook, more concrete, less abstraction
- IF skimmed: More tension, call out avoidance, less softness
- IF captured: Continue thread, deepen, reference continuity

NEVER explicitly reference engagement. Adjust implicitly.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# ENGAGEMENT STATES
# =============================================================================

class EngagementState(Enum):
    """Derived engagement state from user behavior."""
    CAPTURED = "captured"    # User engaged meaningfully
    SKIMMED = "skimmed"      # User saw it but didn't interact
    BOUNCED = "bounced"      # User left quickly
    UNKNOWN = "unknown"      # No prior data


class AdaptationMode(Enum):
    """How to adapt Home output based on engagement."""
    SHARPEN = "sharpen"      # For bounced - sharper, more concrete
    INTENSIFY = "intensify"  # For skimmed - more tension, less soft
    DEEPEN = "deepen"        # For captured - continue thread
    NEUTRAL = "neutral"      # No adaptation needed


# =============================================================================
# THRESHOLDS
# =============================================================================

# Time thresholds in seconds
BOUNCE_THRESHOLD = 5        # < 5 seconds = bounced
SKIM_THRESHOLD = 15         # 5-15 seconds without interaction = skimmed
CAPTURE_THRESHOLD = 15      # > 15 seconds OR any interaction = captured


# =============================================================================
# SESSION DATA MODEL
# =============================================================================

@dataclass
class HomeEngagementSession:
    """Data captured per home session."""
    user_id: str
    session_id: str
    opened_home: datetime
    
    # Time tracking
    time_on_home: float = 0.0  # seconds
    
    # Interaction flags
    interacted: bool = False
    entered_lens: bool = False
    entered_chat: bool = False
    closed_from_home: bool = False
    
    # Derived state
    engagement_state: EngagementState = EngagementState.UNKNOWN
    
    # Pattern context
    pattern_shown: Optional[str] = None
    behavior_snap_shown: Optional[str] = None
    life_arena_shown: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "opened_home": self.opened_home.isoformat() if self.opened_home else None,
            "time_on_home": self.time_on_home,
            "interacted": self.interacted,
            "entered_lens": self.entered_lens,
            "entered_chat": self.entered_chat,
            "closed_from_home": self.closed_from_home,
            "engagement_state": self.engagement_state.value,
            "pattern_shown": self.pattern_shown,
            "behavior_snap_shown": self.behavior_snap_shown,
            "life_arena_shown": self.life_arena_shown,
        }


# =============================================================================
# DERIVE ENGAGEMENT STATE
# =============================================================================

def derive_engagement_state(
    time_on_home: float,
    interacted: bool = False,
    entered_lens: bool = False,
    entered_chat: bool = False,
) -> EngagementState:
    """
    Derive engagement state from session data.
    
    Rules:
    - captured: any interaction OR > CAPTURE_THRESHOLD time
    - skimmed: time > BOUNCE_THRESHOLD but no interaction
    - bounced: time < BOUNCE_THRESHOLD AND no interaction
    """
    # Any meaningful interaction = captured
    if interacted or entered_lens or entered_chat:
        return EngagementState.CAPTURED
    
    # Long enough time = captured
    if time_on_home >= CAPTURE_THRESHOLD:
        return EngagementState.CAPTURED
    
    # Short time without interaction = bounced
    if time_on_home < BOUNCE_THRESHOLD:
        return EngagementState.BOUNCED
    
    # Medium time without interaction = skimmed
    return EngagementState.SKIMMED


# =============================================================================
# ADAPTATION RULES
# =============================================================================

def get_adaptation_mode(
    last_engagement: EngagementState,
    consecutive_bounces: int = 0,
    consecutive_skims: int = 0,
) -> AdaptationMode:
    """
    Determine how to adapt Home output based on last engagement.
    
    Returns adaptation mode that drives content generation.
    """
    if last_engagement == EngagementState.BOUNCED:
        return AdaptationMode.SHARPEN
    
    if last_engagement == EngagementState.SKIMMED:
        return AdaptationMode.INTENSIFY
    
    if last_engagement == EngagementState.CAPTURED:
        return AdaptationMode.DEEPEN
    
    return AdaptationMode.NEUTRAL


# =============================================================================
# ADAPTATION MODIFIERS
# =============================================================================

@dataclass
class AdaptationModifiers:
    """Modifiers to apply to Home generation based on engagement."""
    
    # Hook strength (0-1, higher = sharper)
    hook_strength: float = 0.5
    
    # Tension level (0-1, higher = more confronting)
    tension_level: float = 0.5
    
    # Abstraction level (0-1, higher = more abstract)
    abstraction_level: float = 0.5
    
    # Continuity weight (0-1, higher = more thread continuation)
    continuity_weight: float = 0.0
    
    # Softness level (0-1, higher = softer tone)
    softness_level: float = 0.5
    
    # Avoidance callout strength (0-1)
    avoidance_callout: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "hook_strength": round(self.hook_strength, 2),
            "tension_level": round(self.tension_level, 2),
            "abstraction_level": round(self.abstraction_level, 2),
            "continuity_weight": round(self.continuity_weight, 2),
            "softness_level": round(self.softness_level, 2),
            "avoidance_callout": round(self.avoidance_callout, 2),
        }


def compute_adaptation_modifiers(
    adaptation_mode: AdaptationMode,
    consecutive_bounces: int = 0,
    consecutive_skims: int = 0,
) -> AdaptationModifiers:
    """
    Compute modifiers based on adaptation mode.
    
    Escalates with consecutive bounces/skims.
    """
    mods = AdaptationModifiers()
    
    if adaptation_mode == AdaptationMode.SHARPEN:
        # For bounced: sharper hook, less abstraction, more concrete
        mods.hook_strength = min(0.8 + (consecutive_bounces * 0.1), 1.0)
        mods.abstraction_level = max(0.2 - (consecutive_bounces * 0.05), 0.0)
        mods.tension_level = min(0.6 + (consecutive_bounces * 0.1), 0.9)
        mods.softness_level = max(0.3 - (consecutive_bounces * 0.1), 0.1)
        mods.continuity_weight = 0.0  # Fresh start
        mods.avoidance_callout = 0.0  # Don't call out, just sharpen
        
    elif adaptation_mode == AdaptationMode.INTENSIFY:
        # For skimmed: more tension, call out avoidance, less soft
        mods.hook_strength = 0.7
        mods.tension_level = min(0.7 + (consecutive_skims * 0.1), 0.95)
        mods.abstraction_level = 0.3
        mods.softness_level = max(0.2 - (consecutive_skims * 0.05), 0.05)
        mods.continuity_weight = 0.2  # Some continuity
        mods.avoidance_callout = min(0.3 + (consecutive_skims * 0.15), 0.7)
        
    elif adaptation_mode == AdaptationMode.DEEPEN:
        # For captured: continue thread, deepen, reference continuity
        mods.hook_strength = 0.5
        mods.tension_level = 0.5
        mods.abstraction_level = 0.4  # Can be slightly more abstract
        mods.softness_level = 0.5
        mods.continuity_weight = 0.8  # Strong continuity
        mods.avoidance_callout = 0.0
        
    return mods


# =============================================================================
# BEHAVIOR SNAP SHARPENERS
# =============================================================================

# Sharper behavior snaps for bounced users
SHARPENED_BEHAVIOR_SNAPS = {
    "decision": [
        "You avoided the decision again.",
        "Still not locked in.",
        "You looked away.",
        "The choice is still there.",
    ],
    "message": [
        "You didn't send it.",
        "Still unsent.",
        "You closed the draft.",
        "The message is waiting.",
    ],
    "follow_up": [
        "You checked. Nothing.",
        "Still waiting.",
        "No response yet.",
        "You refreshed again.",
    ],
    "commitment": [
        "You didn't commit.",
        "Still open.",
        "You hesitated again.",
        "The yes didn't come.",
    ],
    "internal_doubt": [
        "You second-guessed yourself.",
        "The doubt won.",
        "You backed off.",
        "You questioned it again.",
    ],
    "relationship": [
        "You didn't say it.",
        "Still unsaid.",
        "They don't know.",
        "You held it back.",
    ],
    "timing": [
        "The moment passed.",
        "You waited too long.",
        "It's still not time.",
        "You missed it.",
    ],
    "execution": [
        "You didn't do it.",
        "Still not done.",
        "You stopped.",
        "It's still pending.",
    ],
}

# Intensified behavior snaps for skimmed users
INTENSIFIED_BEHAVIOR_SNAPS = {
    "decision": [
        "The decision isn't going away.",
        "Avoiding it doesn't make it smaller.",
        "It's still sitting there.",
        "You know you can't skip this.",
    ],
    "message": [
        "The thing you need to say won't say itself.",
        "Waiting isn't sending.",
        "The silence is getting louder.",
        "They can't read your mind.",
    ],
    "follow_up": [
        "Checking won't change the answer.",
        "The response isn't coming faster.",
        "The wait is the work.",
        "Nothing to do but sit with it.",
    ],
    "commitment": [
        "Circling isn't committing.",
        "The commitment is still pending.",
        "You're delaying the lock-in.",
        "Hesitation has a cost.",
    ],
    "internal_doubt": [
        "The doubt is getting louder.",
        "You keep questioning instead of moving.",
        "Overthinking isn't clarity.",
        "The answer was there — you dismissed it.",
    ],
    "relationship": [
        "The tension isn't resolving itself.",
        "Silence isn't fixing it.",
        "They're still waiting.",
        "The distance is growing.",
    ],
    "timing": [
        "The window is still open — but narrowing.",
        "Waiting for perfect isn't working.",
        "The right time doesn't announce itself.",
        "You're running out of runway.",
    ],
    "execution": [
        "Planning isn't doing.",
        "The task is still there.",
        "Motion isn't progress.",
        "You haven't started the real work.",
    ],
}

# Deepening behavior snaps for captured users (continuity)
DEEPENING_BEHAVIOR_SNAPS = {
    "decision": [
        "You're still weighing this.",
        "The decision is clearer now.",
        "You're closer than yesterday.",
        "The path is narrowing — that's good.",
    ],
    "message": [
        "You know what you need to say.",
        "The words are forming.",
        "You're almost ready to send it.",
        "The conversation is coming.",
    ],
    "follow_up": [
        "Still in the waiting.",
        "The patience is working something.",
        "You're learning to sit with uncertainty.",
        "The answer will come when it comes.",
    ],
    "commitment": [
        "You're circling closer.",
        "The commitment is clarifying.",
        "You're testing the yes.",
        "Almost ready to lock in.",
    ],
    "internal_doubt": [
        "The doubt is softer today.",
        "You're finding ground.",
        "The questioning is slowing.",
        "You're learning to trust yourself.",
    ],
    "relationship": [
        "The dynamic is shifting.",
        "Something is moving between you.",
        "The tension has a direction now.",
        "You're understanding them better.",
    ],
    "timing": [
        "The timing is aligning.",
        "You're reading the moment better.",
        "Patience is doing its work.",
        "The window is clearer.",
    ],
    "execution": [
        "Progress is happening.",
        "You're in motion now.",
        "The work is building.",
        "Momentum is forming.",
    ],
}


def get_adapted_behavior_snap(
    base_snap: str,
    life_arena: str,
    adaptation_mode: AdaptationMode,
    pattern_id: str = None,
) -> str:
    """
    Get behavior snap adapted to engagement state.
    
    - SHARPEN: Use sharpened snaps (concrete, immediate)
    - INTENSIFY: Use intensified snaps (more tension, call out avoidance)
    - DEEPEN: Use deepening snaps (continuity, progress)
    - NEUTRAL: Return base snap
    """
    day_of_year = datetime.now().timetuple().tm_yday
    hash_seed = hash(pattern_id or "") if pattern_id else 0
    
    arena_key = life_arena.lower() if life_arena else "internal_doubt"
    
    if adaptation_mode == AdaptationMode.SHARPEN:
        snaps = SHARPENED_BEHAVIOR_SNAPS.get(arena_key, SHARPENED_BEHAVIOR_SNAPS["internal_doubt"])
        return snaps[(day_of_year + hash_seed) % len(snaps)]
    
    elif adaptation_mode == AdaptationMode.INTENSIFY:
        snaps = INTENSIFIED_BEHAVIOR_SNAPS.get(arena_key, INTENSIFIED_BEHAVIOR_SNAPS["internal_doubt"])
        return snaps[(day_of_year + hash_seed) % len(snaps)]
    
    elif adaptation_mode == AdaptationMode.DEEPEN:
        snaps = DEEPENING_BEHAVIOR_SNAPS.get(arena_key, DEEPENING_BEHAVIOR_SNAPS["internal_doubt"])
        return snaps[(day_of_year + hash_seed) % len(snaps)]
    
    # NEUTRAL - return base snap
    return base_snap


# =============================================================================
# BODY TEXT ADAPTATION
# =============================================================================

def adapt_body_text(
    body: str,
    modifiers: AdaptationModifiers,
    adaptation_mode: AdaptationMode,
) -> str:
    """
    Adapt body text based on engagement modifiers.
    
    This is a light-touch adaptation that adjusts tone without rewriting.
    """
    if not body:
        return body
    
    lines = body.split("\n")
    
    # For SHARPEN: trim to essentials, remove soft language
    if adaptation_mode == AdaptationMode.SHARPEN:
        # Remove soft openers
        soft_openers = ["maybe", "perhaps", "it might be", "you might", "consider", "think about"]
        cleaned_lines = []
        for line in lines:
            line_lower = line.lower()
            # Skip lines that start with soft language
            starts_soft = any(line_lower.strip().startswith(s) for s in soft_openers)
            if not starts_soft:
                cleaned_lines.append(line)
        
        # Limit to first 4-5 meaningful lines
        meaningful_lines = [ln for ln in cleaned_lines if ln.strip()]
        if len(meaningful_lines) > 5:
            meaningful_lines = meaningful_lines[:5]
        
        return "\n\n".join(meaningful_lines)
    
    # For INTENSIFY: keep structure, language handles itself via snap
    elif adaptation_mode == AdaptationMode.INTENSIFY:
        return body  # Snap already intensified
    
    # For DEEPEN: add subtle continuity marker
    elif adaptation_mode == AdaptationMode.DEEPEN:
        # Could add continuity phrase but keeping implicit per requirements
        return body
    
    return body


# =============================================================================
# MONGODB PERSISTENCE
# =============================================================================

async def save_engagement_session(
    db,
    session: HomeEngagementSession,
) -> bool:
    """
    Save engagement session to MongoDB.
    """
    try:
        collection = db["home_engagement_sessions"]
        
        doc = session.to_dict()
        doc["created_at"] = datetime.now(timezone.utc)
        
        await collection.insert_one(doc)
        
        logger.info(f"[Engagement] Saved session for user {session.user_id[:8]}: {session.engagement_state.value}")
        return True
    except Exception as e:
        logger.error(f"[Engagement] Failed to save session: {e}")
        return False


async def update_last_engagement(
    db,
    user_id: str,
    engagement_state: EngagementState,
    pattern_shown: str = None,
    behavior_snap_shown: str = None,
    life_arena_shown: str = None,
) -> bool:
    """
    Update user's last engagement state (for quick lookup).
    """
    try:
        collection = db["user_engagement_state"]
        
        doc = {
            "user_id": user_id,
            "last_engagement_state": engagement_state.value,
            "last_engagement_at": datetime.now(timezone.utc),
            "last_pattern_shown": pattern_shown,
            "last_behavior_snap": behavior_snap_shown,
            "last_life_arena": life_arena_shown,
        }
        
        await collection.update_one(
            {"user_id": user_id},
            {"$set": doc},
            upsert=True
        )
        
        # Update consecutive counts
        if engagement_state == EngagementState.BOUNCED:
            await collection.update_one(
                {"user_id": user_id},
                {"$inc": {"consecutive_bounces": 1}, "$set": {"consecutive_skims": 0}}
            )
        elif engagement_state == EngagementState.SKIMMED:
            await collection.update_one(
                {"user_id": user_id},
                {"$inc": {"consecutive_skims": 1}, "$set": {"consecutive_bounces": 0}}
            )
        else:
            await collection.update_one(
                {"user_id": user_id},
                {"$set": {"consecutive_bounces": 0, "consecutive_skims": 0}}
            )
        
        logger.info(f"[Engagement] Updated state for user {user_id[:8]}: {engagement_state.value}")
        return True
    except Exception as e:
        logger.error(f"[Engagement] Failed to update state: {e}")
        return False


async def get_last_engagement(
    db,
    user_id: str,
) -> Dict[str, Any]:
    """
    Get user's last engagement state.
    """
    try:
        collection = db["user_engagement_state"]
        
        doc = await collection.find_one({"user_id": user_id})
        
        if not doc:
            return {
                "engagement_state": EngagementState.UNKNOWN,
                "consecutive_bounces": 0,
                "consecutive_skims": 0,
                "last_engagement_at": None,
                "last_pattern_shown": None,
                "last_behavior_snap": None,
                "last_life_arena": None,
            }
        
        return {
            "engagement_state": EngagementState(doc.get("last_engagement_state", "unknown")),
            "consecutive_bounces": doc.get("consecutive_bounces", 0),
            "consecutive_skims": doc.get("consecutive_skims", 0),
            "last_engagement_at": doc.get("last_engagement_at"),
            "last_pattern_shown": doc.get("last_pattern_shown"),
            "last_behavior_snap": doc.get("last_behavior_snap"),
            "last_life_arena": doc.get("last_life_arena"),
        }
    except Exception as e:
        logger.error(f"[Engagement] Failed to get state: {e}")
        return {
            "engagement_state": EngagementState.UNKNOWN,
            "consecutive_bounces": 0,
            "consecutive_skims": 0,
            "last_engagement_at": None,
            "last_pattern_shown": None,
            "last_behavior_snap": None,
            "last_life_arena": None,
        }


async def get_engagement_history(
    db,
    user_id: str,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Get user's recent engagement history.
    """
    try:
        collection = db["home_engagement_sessions"]
        
        cursor = collection.find(
            {"user_id": user_id}
        ).sort("opened_home", -1).limit(limit)
        
        sessions = []
        async for doc in cursor:
            sessions.append({
                "session_id": doc.get("session_id"),
                "opened_home": doc.get("opened_home"),
                "time_on_home": doc.get("time_on_home"),
                "engagement_state": doc.get("engagement_state"),
                "interacted": doc.get("interacted"),
                "entered_lens": doc.get("entered_lens"),
                "entered_chat": doc.get("entered_chat"),
            })
        
        return sessions
    except Exception as e:
        logger.error(f"[Engagement] Failed to get history: {e}")
        return []


# =============================================================================
# MAIN ADAPTATION FUNCTION
# =============================================================================

async def compute_engagement_adaptation(
    db,
    user_id: str,
    current_behavior_snap: str,
    current_life_arena: str,
    current_body: str,
    pattern_id: str = None,
) -> Dict[str, Any]:
    """
    Main function to compute engagement-based adaptation.
    
    Returns adapted content and debug info.
    """
    # Get last engagement
    last_eng = await get_last_engagement(db, user_id)
    
    engagement_state = last_eng["engagement_state"]
    consecutive_bounces = last_eng["consecutive_bounces"]
    consecutive_skims = last_eng["consecutive_skims"]
    
    # Get adaptation mode
    adaptation_mode = get_adaptation_mode(
        engagement_state,
        consecutive_bounces,
        consecutive_skims,
    )
    
    # Compute modifiers
    modifiers = compute_adaptation_modifiers(
        adaptation_mode,
        consecutive_bounces,
        consecutive_skims,
    )
    
    # Adapt behavior snap
    adapted_snap = get_adapted_behavior_snap(
        current_behavior_snap,
        current_life_arena,
        adaptation_mode,
        pattern_id,
    )
    
    # Adapt body text
    adapted_body = adapt_body_text(
        current_body,
        modifiers,
        adaptation_mode,
    )
    
    # Replace behavior snap in body if it was at the start
    if current_behavior_snap and adapted_body.startswith(current_behavior_snap):
        adapted_body = adapted_body.replace(current_behavior_snap, adapted_snap, 1)
    elif adapted_snap:
        # Prepend adapted snap if not already there
        lines = adapted_body.split("\n")
        if lines and lines[0].strip() != adapted_snap.strip():
            adapted_body = adapted_snap + "\n\n" + adapted_body
    
    # Build result
    result = {
        "behavior_snap": adapted_snap,
        "body": adapted_body,
        "engagement_state": engagement_state.value,
        "adaptation_mode": adaptation_mode.value,
        "modifiers": modifiers.to_dict(),
        "debug": {
            "previous_engagement": engagement_state.value,
            "consecutive_bounces": consecutive_bounces,
            "consecutive_skims": consecutive_skims,
            "last_engagement_at": last_eng["last_engagement_at"].isoformat() if last_eng["last_engagement_at"] else None,
            "last_pattern_shown": last_eng["last_pattern_shown"],
            "adaptation_applied": adaptation_mode != AdaptationMode.NEUTRAL,
        }
    }
    
    logger.info(f"[Engagement] Adaptation for user {user_id[:8]}: mode={adaptation_mode.value}, bounces={consecutive_bounces}, skims={consecutive_skims}")
    
    return result


# =============================================================================
# API PAYLOAD MODELS
# =============================================================================

@dataclass
class EngagementEventPayload:
    """Payload for engagement tracking endpoint."""
    user_id: str
    session_id: str
    event_type: str  # "open", "interact", "enter_lens", "enter_chat", "close"
    timestamp: Optional[datetime] = None
    time_on_home: Optional[float] = None
    pattern_shown: Optional[str] = None
    behavior_snap_shown: Optional[str] = None
    life_arena_shown: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EngagementEventPayload":
        return cls(
            user_id=data.get("user_id", ""),
            session_id=data.get("session_id", ""),
            event_type=data.get("event_type", ""),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.now(timezone.utc),
            time_on_home=data.get("time_on_home"),
            pattern_shown=data.get("pattern_shown"),
            behavior_snap_shown=data.get("behavior_snap_shown"),
            life_arena_shown=data.get("life_arena_shown"),
        )
