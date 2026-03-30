"""
Engagement Adaptation Layer for Mirror Home - V1.1 PERCEIVED ADAPTATION
========================================================================

PROBLEM: System adapts internally, but UI feels static.
SOLUTION: Make adaptation FELT through first-line changes.

V1.0: Track engagement, derive state, adapt output
V1.1: PERCEIVED ADAPTATION - Users FEEL the system adapted

ENGAGEMENT STATES:
- captured: User interacted OR spent > threshold time
- skimmed: Time > threshold but no interaction
- bounced: Time < threshold AND no interaction

PERCEIVED ADAPTATION RULES:
- First line must ALWAYS change based on engagement
- IF bounced: Sharper, more immediate, more concrete
- IF skimmed: Call out avoidance clearly
- IF captured: Continuity + deepening
- NEVER explain adaptation explicitly

BANNED GENERIC OPENERS (V1.1):
- "You're avoiding something you already know"
- "You already know what's off here"
- "This keeps coming back"
- "There's something you're not facing"
- "Something is off"

FIRST LINE RULES (V1.1):
- Must describe something user likely just did
- Must be <= 12 words
- Must use present or immediate past tense
- Must be behavior-based, time-bound, specific
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# BANNED GENERIC OPENERS (V1.1)
# =============================================================================

BANNED_OPENERS = [
    "you're avoiding something you already know",
    "you already know what's off here",
    "this keeps coming back",
    "there's something you're not facing",
    "something is off",
    "you know what you need to do",
    "the answer is already there",
    "you've been here before",
    "this pattern is familiar",
    "something feels unresolved",
    "there's a tension",
    "you're holding something back",
    "you know what's true",
]


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
# V1.1: PERCEIVED ADAPTATION BEHAVIOR SNAPS
# =============================================================================
# Rules:
# - Must describe something user likely just did
# - Must be <= 12 words
# - Must use present or immediate past tense
# - Must be behavior-based, time-bound, specific

# BOUNCED: Sharper, more immediate, more concrete
# User barely looked - hit them with what they JUST did
BOUNCED_BEHAVIOR_SNAPS = {
    "decision": [
        "You paused — then moved past it again.",
        "You almost decided — then didn't.",
        "You saw the choice — and left.",
        "You looked away from it.",
    ],
    "message": [
        "You almost sent it — then closed it.",
        "You opened the draft — and left.",
        "You typed something — then deleted.",
        "You thought about saying it — didn't.",
    ],
    "follow_up": [
        "You checked — nothing changed.",
        "You refreshed — same result.",
        "You looked for the answer — not there.",
        "You waited — then gave up.",
    ],
    "commitment": [
        "You were about to lock in — then stopped.",
        "You got close — then backed off.",
        "You almost said yes — but didn't.",
        "You hesitated — again.",
    ],
    "internal_doubt": [
        "You paused — then moved past it.",
        "You felt it — then ignored it.",
        "You almost trusted yourself — then didn't.",
        "You had the answer — then questioned it.",
    ],
    "relationship": [
        "You almost said something — then didn't.",
        "You thought about them — then let it go.",
        "You started to reach out — then stopped.",
        "You had the words — held them back.",
    ],
    "timing": [
        "The moment came — you let it pass.",
        "You felt the window — didn't move.",
        "You sensed it was time — ignored it.",
        "The opening was there — you waited.",
    ],
    "execution": [
        "You were about to start — then didn't.",
        "You opened it — then closed it.",
        "You got ready — then stopped.",
        "You almost did it — then paused.",
    ],
}

# SKIMMED: Call out avoidance clearly
# User saw it but kept scrolling - acknowledge they saw it
SKIMMED_BEHAVIOR_SNAPS = {
    "decision": [
        "You saw it — and kept going anyway.",
        "You noticed the choice — pushed past it.",
        "You recognized it — then moved on.",
        "You knew what needed deciding — skipped it.",
    ],
    "message": [
        "You knew what to say — stayed quiet.",
        "You saw the message — didn't respond.",
        "You thought about sending it — scrolled past.",
        "You noticed the silence — left it.",
    ],
    "follow_up": [
        "You checked — saw nothing — moved on.",
        "You noticed the wait — didn't sit with it.",
        "You saw the empty inbox — kept going.",
        "You felt the limbo — pushed past.",
    ],
    "commitment": [
        "You saw the commitment — walked past it.",
        "You noticed the open loop — left it open.",
        "You recognized the hesitation — continued.",
        "You felt the pull to decide — resisted.",
    ],
    "internal_doubt": [
        "You noticed the doubt — pushed through anyway.",
        "You felt the uncertainty — ignored it.",
        "You saw the question — didn't answer it.",
        "You recognized the hesitation — kept moving.",
    ],
    "relationship": [
        "You thought about them — kept scrolling.",
        "You noticed the tension — didn't address it.",
        "You felt the distance — left it alone.",
        "You saw what needed saying — stayed silent.",
    ],
    "timing": [
        "You felt the moment — let it slide.",
        "You noticed the window — didn't go through.",
        "You sensed the timing — kept waiting.",
        "You saw the opportunity — passed on it.",
    ],
    "execution": [
        "You saw the task — scrolled past.",
        "You noticed what needed doing — didn't do it.",
        "You recognized the work — moved on.",
        "You felt the push to act — resisted.",
    ],
}

# CAPTURED: Continuity + deepening
# User engaged yesterday - acknowledge they're back
CAPTURED_BEHAVIOR_SNAPS = {
    "decision": [
        "You stayed with this.",
        "You're still here — thinking.",
        "The decision is clearer now.",
        "You're closer than before.",
    ],
    "message": [
        "You're still thinking about what to say.",
        "The words are forming.",
        "You're getting ready to send it.",
        "It's almost time.",
    ],
    "follow_up": [
        "You're still waiting — that's okay.",
        "The patience is doing something.",
        "You're learning to sit with this.",
        "Still no answer — but you're here.",
    ],
    "commitment": [
        "You're circling closer.",
        "The yes is getting clearer.",
        "You're almost ready to lock in.",
        "The commitment is forming.",
    ],
    "internal_doubt": [
        "The doubt is quieter today.",
        "You're finding ground.",
        "The questioning is slowing.",
        "You're starting to trust it.",
    ],
    "relationship": [
        "You're still thinking about them.",
        "Something is shifting between you.",
        "The words are getting clearer.",
        "You're getting ready to say it.",
    ],
    "timing": [
        "The timing is aligning.",
        "You're reading the moment better.",
        "Patience is doing its work.",
        "The window is getting clearer.",
    ],
    "execution": [
        "You're in motion now.",
        "Progress is happening — slowly.",
        "The work is building.",
        "You're closer than yesterday.",
    ],
}


def is_generic_opener(text: str) -> bool:
    """Check if text starts with a banned generic opener."""
    if not text:
        return False
    text_lower = text.lower().strip()
    return any(text_lower.startswith(banned) for banned in BANNED_OPENERS)


def get_adapted_behavior_snap(
    base_snap: str,
    life_arena: str,
    adaptation_mode: AdaptationMode,
    pattern_id: str = None,
) -> str:
    """
    V1.1: Get behavior snap adapted to engagement state with perceived adaptation.
    
    Rules:
    - Must describe something user likely just did
    - Must be <= 12 words
    - Must use present or immediate past tense
    - Must be behavior-based, time-bound, specific
    - Must NOT be a banned generic opener
    
    SHARPEN (bounced): More immediate, more concrete
    INTENSIFY (skimmed): Call out avoidance clearly
    DEEPEN (captured): Continuity + deepening
    NEUTRAL: Return base snap (if not generic)
    """
    day_of_year = datetime.now().timetuple().tm_yday
    hash_seed = hash(pattern_id or "") if pattern_id else 0
    
    arena_key = life_arena.lower() if life_arena else "internal_doubt"
    
    # Select appropriate snap dictionary based on mode
    if adaptation_mode == AdaptationMode.SHARPEN:
        snaps = BOUNCED_BEHAVIOR_SNAPS.get(arena_key, BOUNCED_BEHAVIOR_SNAPS["internal_doubt"])
        snap = snaps[(day_of_year + hash_seed) % len(snaps)]
    
    elif adaptation_mode == AdaptationMode.INTENSIFY:
        snaps = SKIMMED_BEHAVIOR_SNAPS.get(arena_key, SKIMMED_BEHAVIOR_SNAPS["internal_doubt"])
        snap = snaps[(day_of_year + hash_seed) % len(snaps)]
    
    elif adaptation_mode == AdaptationMode.DEEPEN:
        snaps = CAPTURED_BEHAVIOR_SNAPS.get(arena_key, CAPTURED_BEHAVIOR_SNAPS["internal_doubt"])
        snap = snaps[(day_of_year + hash_seed) % len(snaps)]
    
    else:
        # NEUTRAL - check if base snap is generic
        if is_generic_opener(base_snap):
            # Replace with a neutral but specific snap
            neutral_snaps = CAPTURED_BEHAVIOR_SNAPS.get(arena_key, CAPTURED_BEHAVIOR_SNAPS["internal_doubt"])
            snap = neutral_snaps[(day_of_year + hash_seed) % len(neutral_snaps)]
        else:
            snap = base_snap
    
    # Final check - ensure it's not generic
    if is_generic_opener(snap):
        # Fallback to bounced snaps (always specific)
        fallback = BOUNCED_BEHAVIOR_SNAPS.get(arena_key, BOUNCED_BEHAVIOR_SNAPS["internal_doubt"])
        snap = fallback[(day_of_year + hash_seed) % len(fallback)]
    
    logger.debug(f"[PerceivedAdapt] mode={adaptation_mode.value}, arena={arena_key}, snap='{snap}'")
    
    return snap


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
