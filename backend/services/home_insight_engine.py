"""Home Insight Engine - Phase 1 MVP

Simple structured insight generation for Home Screen.
Phase 1: Transform existing data into new structured format.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# PHASE 1: SIMPLE PATTERN TEMPLATES
# =============================================================================
# Direct, behavioral language. No hedging.

PATTERN_TEMPLATES = {
    "fast_start_delayed_feedback": {
        "title": "You Moved. Nothing Echoed Back.",
        "what_happening": "You took action—sent the message, made the move, started the thing—but nothing came back yet. No response, no confirmation, no signal that it landed.",
        "why_feels": "You did your part. The world hasn't caught up. That gap creates pressure that makes you want to do more.",
        "watch_for": "Sending a follow-up before it's needed. Changing direction because silence feels like rejection.",
        "better_move": "Let the current move finish playing out. Give it 24-48 more hours before deciding if something is wrong.",
        "interrupt": "Right before you check again—stop. Nothing broke. It just hasn't landed."
    },
    "high_drive_low_signal": {
        "title": "Energy Without a Target",
        "what_happening": "You have energy and you want to use it, but you don't have a clear target. So you're scanning—opening tabs, starting conversations, looking for something to put the energy into.",
        "why_feels": "The drive is real but directionless. That mismatch creates restlessness disguised as productivity.",
        "watch_for": "Starting three things instead of finishing one. Confusing movement with progress.",
        "better_move": "Write down the one thing that would actually matter if it got done today. Do that first.",
        "interrupt": "You just switched tasks again. Stop. Pick one. Finish it."
    },
    "emotional_noise_low_clarity": {
        "title": "It's Not One Thing",
        "what_happening": "You're feeling something strongly, but you can't name it cleanly. Someone asked 'what's wrong' and you couldn't give a straight answer—because it's not one thing.",
        "why_feels": "Multiple signals hitting at once. The noise makes it hard to think straight, and that creates more frustration.",
        "watch_for": "Making a decision just to get relief. Picking a fight because the tension needs somewhere to go.",
        "better_move": "Don't solve it right now. Let the wave move through before you act on any of it.",
        "interrupt": "If you feel the snap coming—stop. Say nothing. Walk away for five minutes."
    },
    "strong_urge_wrong_timing": {
        "title": "You're Ready Before It Is",
        "what_happening": "You know what you want to do. You've been ready. But the situation isn't there yet—the other person isn't ready, the opportunity hasn't opened, the pieces aren't in place.",
        "why_feels": "Your internal clock says 'now' but the external clock says 'not yet.' That mismatch creates pressure to force it.",
        "watch_for": "Trying to manufacture the opening. Pushing someone to be ready before they are.",
        "better_move": "Stay ready without acting. Use this time to prepare so when the window opens, you can move cleanly.",
        "interrupt": "You're about to force it. Don't. The cost of waiting is lower than the cost of pushing."
    },
    "pattern_returning_control": {
        "title": "The Grip Is Getting Tighter",
        "what_happening": "Something uncertain showed up. And your response is to tighten your grip on everything you can control—details, plans, other people's work.",
        "why_feels": "When you can't control the big thing, controlling small things feels like safety. It's not. But it feels productive.",
        "watch_for": "Over-preparing. Checking details you've already checked. Asking for updates you don't need.",
        "better_move": "Name what you're actually worried about—the real thing. Is controlling details helping that, or keeping you busy?",
        "interrupt": "You're checking it again. That's the pattern. Step back. Let it breathe."
    },
    "waiting_for_permission": {
        "title": "You Already Know",
        "what_happening": "You know what you want to do. You've known for a while. But you're waiting for someone to say it's the right call—a sign, a green light, an external yes.",
        "why_feels": "The decision is already made inside you, but you don't fully trust it. So you keep gathering input to delay committing.",
        "watch_for": "Asking for opinions you don't need. Framing statements as questions. Waiting for permission you could give yourself.",
        "better_move": "Notice what you would do if no one would judge the choice. That's probably the answer.",
        "interrupt": "You're about to ask what they think. You already know. Say what you know instead."
    },
    "momentum_building": {
        "title": "It's Starting to Work",
        "what_happening": "Something is working. You got traction—a response, a result, a sign that the thing is landing. It's not finished, but it's moving.",
        "why_feels": "Early wins create urgency to do more, faster. The excitement is real, but so is the temptation to overcommit.",
        "watch_for": "Adding complexity before this stabilizes. Making promises based on early results.",
        "better_move": "Keep doing exactly what's working. Don't optimize yet. Don't expand yet.",
        "interrupt": "You're about to add something. Don't. Finish this first."
    },
    "holding_back_expression": {
        "title": "Something Wants to Be Said",
        "what_happening": "There's something you want to say—to a specific person, about a specific thing—and you haven't said it yet. You've rehearsed it. But you haven't pulled the trigger.",
        "why_feels": "The thing is real, but the moment hasn't felt right. Or you're worried how it will land. So it stays stuck.",
        "watch_for": "Waiting for a perfect moment that doesn't come. Letting resentment build because they should have figured it out.",
        "better_move": "Say the smaller version first. You don't have to say all of it—just the first honest piece.",
        "interrupt": "You've rehearsed it twice already. Next time you see them—say the first sentence. Now."
    },
    "decision_avoidance": {
        "title": "The Choice You Keep Circling",
        "what_happening": "There's a decision you've been sitting with. You've thought about it, analyzed it, talked to people about it. But you haven't decided—because both options have real costs.",
        "why_feels": "Deciding means closing a door. That loss is real. So you stay in analysis mode where consequences stay hypothetical.",
        "watch_for": "Gathering more information when you already have enough. Treating 'still deciding' as an answer when it's avoidance.",
        "better_move": "Name what you're actually afraid of getting wrong. Not the practical risk—the emotional one.",
        "interrupt": "You're running the same loop again. Decide now—or drop it entirely. No more thinking."
    },
    "energy_recovery": {
        "title": "You Spent Something Recently",
        "what_happening": "You pushed hard recently—a deadline, an emotional stretch, an extended period of output. Now you're running on less, and it's showing.",
        "why_feels": "You're comparing today's energy to a version of yourself that didn't just spend a lot. That comparison makes recovery feel like failure.",
        "watch_for": "Forcing productivity when your body asks for rest. Saying yes because you feel guilty about slowing down.",
        "better_move": "Protect the recovery window. Don't fill empty space with new commitments.",
        "interrupt": "You feel guilty about resting. That's the signal. Stay down. One more day."
    },
    "quiet_signal_day": {
        "title": "Nothing Urgent Is Pulling",
        "what_happening": "No urgent pull today. No strong emotion. No crisis. No breakthrough. Just a regular day. And that might feel uncomfortable.",
        "why_feels": "You're used to having something to respond to. When there's no fire, you might be tempted to start one.",
        "watch_for": "Looking for something to fix when nothing is broken. Making a neutral day feel significant because quiet feels wrong.",
        "better_move": "Use the space for maintenance—loose ends, small tasks. Don't fill it with new drama.",
        "interrupt": "You're scanning for a problem. Stop. There isn't one. Let the quiet be quiet."
    },
    "default": {
        "title": "Something Present",
        "what_happening": "There's something here today asking for your attention. Not an emergency—more like a pull. You might not have words for it yet.",
        "why_feels": "Your system is picking up a signal that your conscious mind hasn't fully processed. That's not a problem—it's information.",
        "watch_for": "Dismissing the feeling because you can't explain it. Moving too fast past something that needed another minute.",
        "better_move": "Don't rush to label it. Sit with what you're noticing before you try to solve it.",
        "interrupt": "You're about to move on. Something in you hesitated. Listen to that."
    }
}


# =============================================================================
# PHASE 2: SIGNAL-BASED PATTERN SELECTION
# =============================================================================
# Extract signals from journal, mirror chat, reflections
# Map signals to patterns using simple heuristics

# Signal detection keywords
SIGNAL_KEYWORDS = {
    "action_taken": [
        "did", "sent", "made", "started", "launched", "pushed", "submitted",
        "told", "asked", "called", "emailed", "texted", "posted", "shipped",
        "finished", "completed", "delivered", "created", "built", "wrote"
    ],
    "waiting_outcome": [
        "waiting", "wait", "haven't heard", "no response", "nothing yet",
        "still waiting", "haven't gotten", "no reply", "silence", "crickets",
        "not yet", "hasn't landed", "hasn't happened", "no sign", "no word"
    ],
    "frustration": [
        "frustrated", "annoying", "annoyed", "stuck", "blocked", "tired of",
        "sick of", "fed up", "impatient", "why won't", "ugh", "argh",
        "driving me crazy", "can't believe", "so slow", "taking forever"
    ],
    "doubt": [
        "doubt", "not sure", "uncertain", "second guess", "maybe I shouldn't",
        "wrong", "mistake", "regret", "should I have", "was that right",
        "overthinking", "questioning", "wonder if", "what if I"
    ],
    "seeking_validation": [
        "what do you think", "should I", "is this right", "does this make sense",
        "am I crazy", "tell me", "need advice", "opinions", "feedback",
        "asking", "asked everyone", "checking with", "running it by"
    ],
    "high_urgency": [
        "need to", "have to", "must", "urgent", "now", "immediately",
        "can't wait", "right now", "asap", "deadline", "running out of time",
        "pressure", "pushing", "hurry", "rush"
    ],
    "low_clarity": [
        "confused", "unclear", "don't know", "not sure what", "which way",
        "can't decide", "torn", "options", "either", "or", "both",
        "no idea", "lost", "foggy", "muddled"
    ],
    "emotional_intensity": [
        "overwhelmed", "anxious", "stressed", "worried", "scared", "angry",
        "sad", "upset", "crying", "can't stop thinking", "obsessing",
        "spiraling", "triggered", "emotional", "feelings", "heavy"
    ],
    "recovery_needed": [
        "exhausted", "tired", "drained", "burnt out", "burnout", "need rest",
        "low energy", "depleted", "running on empty", "nothing left",
        "can't keep going", "need a break", "worn out"
    ],
    "momentum": [
        "working", "progress", "moving", "traction", "starting to",
        "finally", "breakthrough", "it's happening", "coming together",
        "things are", "getting somewhere", "on track"
    ],
    "something_unsaid": [
        "want to say", "need to tell", "haven't said", "holding back",
        "keeping", "secret", "can't say", "afraid to say", "should tell",
        "been meaning to", "avoiding the conversation"
    ],
    "control_seeking": [
        "need to control", "micromanaging", "checking", "monitoring",
        "can't let go", "have to make sure", "double checking", "triple",
        "keeping tabs", "watching", "obsessing over details"
    ]
}

def extract_signal_flags(texts: list) -> Dict[str, bool]:
    """
    Extract signal flags from a list of text content.
    Simple keyword matching - no NLP needed.
    """
    if not texts:
        return {}
    
    # Combine all text, lowercase
    combined = " ".join(str(t).lower() for t in texts if t)
    
    flags = {}
    for signal_name, keywords in SIGNAL_KEYWORDS.items():
        # Check if any keyword appears in the combined text
        flags[signal_name] = any(kw in combined for kw in keywords)
    
    return flags


# =============================================================================
# PHASE 3: TRAJECTORY / PHASE DETECTION
# =============================================================================
# Detect WHERE user is in pattern cycle: INITIATION → BUILD-UP → FRICTION → RECOVERY

PHASE_DEFINITIONS = {
    "INITIATION": {
        "description": "Starting energy. Movement beginning.",
        "tone": "encourage movement, avoid overthinking"
    },
    "BUILD_UP": {
        "description": "Progress happening. Momentum building.",
        "tone": "reinforce consistency, avoid distraction"
    },
    "FRICTION": {
        "description": "Effort not landing. Tension building.",
        "tone": "normalize frustration, prevent overreaction"
    },
    "RECOVERY": {
        "description": "Slowing down. Integration happening.",
        "tone": "slow down, integrate learning"
    }
}

# Phase-specific content adjustments
PHASE_MODIFIERS = {
    "INITIATION": {
        "title_prefix": "",
        "what_happening_suffix": "",
        "watch_for_emphasis": "Don't second-guess too early.",
        "better_move_emphasis": "Keep moving forward.",
        "interrupt_emphasis": "Hesitation now costs more than mistakes."
    },
    "BUILD_UP": {
        "title_prefix": "",
        "what_happening_suffix": " This is part of the process.",
        "watch_for_emphasis": "Don't get distracted by new shiny things.",
        "better_move_emphasis": "Stay the course a bit longer.",
        "interrupt_emphasis": "Consistency beats intensity here."
    },
    "FRICTION": {
        "title_prefix": "",
        "what_happening_suffix": " The gap between effort and result is creating pressure.",
        "watch_for_emphasis": "Don't blow up what's actually working.",
        "better_move_emphasis": "The frustration is information, not a command.",
        "interrupt_emphasis": "Nothing has failed yet—it just hasn't landed."
    },
    "RECOVERY": {
        "title_prefix": "",
        "what_happening_suffix": " Your system is recalibrating.",
        "watch_for_emphasis": "Don't judge the slowdown as failure.",
        "better_move_emphasis": "Rest is part of the work.",
        "interrupt_emphasis": "Guilt about rest means you need more rest."
    }
}


def extract_signal_flags_per_entry(texts: list) -> list:
    """
    Extract signal flags for EACH text entry separately.
    Used for detecting trajectory across recent entries.
    """
    if not texts:
        return []
    
    entry_flags = []
    for text in texts:
        if not text:
            continue
        text_lower = str(text).lower()
        flags = {}
        for signal_name, keywords in SIGNAL_KEYWORDS.items():
            flags[signal_name] = any(kw in text_lower for kw in keywords)
        entry_flags.append(flags)
    
    return entry_flags


def detect_pattern_phase(signal_flags: Dict[str, bool], entry_history: list) -> tuple:
    """
    Detect where user is in the pattern cycle.
    
    Uses current signals + recent history to determine phase.
    Returns (phase, phase_description, trajectory_summary)
    
    Phases:
    - INITIATION: action_taken, high_urgency, no frustration yet
    - BUILD_UP: action_taken, momentum, some progress
    - FRICTION: frustration/doubt after action, waiting for outcome
    - RECOVERY: recovery signals, lower urgency, reflection mode
    """
    
    # Count signals across recent history
    history_counts = {
        "action_taken": 0,
        "frustration": 0,
        "doubt": 0,
        "momentum": 0,
        "recovery_needed": 0,
        "waiting_outcome": 0,
        "emotional_intensity": 0,
        "high_urgency": 0
    }
    
    for entry_flags in entry_history:
        for key in history_counts.keys():
            if entry_flags.get(key):
                history_counts[key] += 1
    
    # Build trajectory summary
    trajectory_parts = []
    if history_counts["action_taken"] > 0:
        trajectory_parts.append(f"action({history_counts['action_taken']})")
    if history_counts["momentum"] > 0:
        trajectory_parts.append(f"momentum({history_counts['momentum']})")
    if history_counts["frustration"] > 0:
        trajectory_parts.append(f"frustration({history_counts['frustration']})")
    if history_counts["recovery_needed"] > 0:
        trajectory_parts.append(f"recovery({history_counts['recovery_needed']})")
    
    trajectory_summary = " → ".join(trajectory_parts) if trajectory_parts else "no clear trajectory"
    
    # Current state signals
    has_action = signal_flags.get("action_taken", False)
    has_frustration = signal_flags.get("frustration", False)
    has_doubt = signal_flags.get("doubt", False)
    has_momentum = signal_flags.get("momentum", False)
    has_recovery = signal_flags.get("recovery_needed", False)
    has_waiting = signal_flags.get("waiting_outcome", False)
    has_urgency = signal_flags.get("high_urgency", False)
    has_emotional = signal_flags.get("emotional_intensity", False)
    
    # Historical patterns
    had_action_before = history_counts["action_taken"] > 0
    had_frustration_before = history_counts["frustration"] > 0
    had_momentum_before = history_counts["momentum"] > 0
    
    # =================================================================
    # PHASE DETECTION RULES (priority order)
    # =================================================================
    
    # RECOVERY: Clear recovery signals, or coming down from intensity
    if has_recovery:
        return ("RECOVERY", 
                "I think I'm coming out of it.",
                trajectory_summary)
    
    if had_frustration_before and not has_frustration and not has_urgency:
        return ("RECOVERY",
                "Something in me is settling again.",
                trajectory_summary)
    
    # FRICTION: Frustration/doubt after taking action, waiting without result
    if has_frustration or has_doubt:
        if has_waiting or had_action_before:
            return ("FRICTION",
                    "I did my part. Nothing came back yet.",
                    trajectory_summary)
        if has_emotional:
            return ("FRICTION",
                    "There's a lot here, but none of it is clear.",
                    trajectory_summary)
        return ("FRICTION",
                "Something's off, but I can't name it.",
                trajectory_summary)
    
    # BUILD-UP: Momentum happening, action taken, progress visible
    if has_momentum:
        if has_action or had_action_before:
            return ("BUILD_UP",
                    "Things are picking up—I can feel it.",
                    trajectory_summary)
        return ("BUILD_UP",
                "This is already in motion.",
                trajectory_summary)
    
    if had_action_before and had_momentum_before and not has_frustration:
        return ("BUILD_UP",
                "I just need to keep going.",
                trajectory_summary)
    
    # INITIATION: Action starting, urgency present, no friction yet
    if has_action and not has_frustration and not has_doubt:
        return ("INITIATION",
                "Something is starting to move.",
                trajectory_summary)
    
    if has_urgency and not had_frustration_before:
        return ("INITIATION",
                "I'm ready. I just don't know for what yet.",
                trajectory_summary)
    
    # Default: INITIATION with inner voice
    return ("INITIATION",
            "Something is starting… I just don't know what yet.",
            trajectory_summary)


def apply_phase_modifier(template: dict, phase: str, phase_description: str) -> dict:
    """
    Apply phase-specific modifications to template content.
    Returns modified template with phase-aware adjustments.
    """
    modifier = PHASE_MODIFIERS.get(phase, PHASE_MODIFIERS["INITIATION"])
    
    # Create modified copy
    modified = template.copy()
    
    # For FRICTION phase, provide more specific content
    if phase == "FRICTION":
        # Add context about the friction
        if "hasn't landed" not in modified["what_happening"]:
            modified["what_happening"] = modified["what_happening"] + modifier["what_happening_suffix"]
        
        # Emphasize the interrupt for friction
        if "nothing has failed" not in modified["interrupt"].lower():
            modified["interrupt"] = modified["interrupt"] + " " + modifier["interrupt_emphasis"]
    
    elif phase == "RECOVERY":
        # Soften the urgency for recovery
        if "recalibrating" not in modified["what_happening"]:
            modified["what_happening"] = modified["what_happening"] + modifier["what_happening_suffix"]
    
    elif phase == "BUILD_UP":
        # Reinforce consistency
        if "stay" not in modified["better_move"].lower():
            modified["better_move"] = modified["better_move"] + " " + modifier["better_move_emphasis"]
    
    return modified


def select_pattern_from_signals(flags: Dict[str, bool]) -> tuple:
    """
    Select pattern based on signal flags.
    Returns (pattern_key, reason)
    """
    # Priority-ordered pattern matching rules
    
    # Rule 1: Action taken + waiting for outcome + frustration/doubt
    if flags.get("action_taken") and flags.get("waiting_outcome"):
        if flags.get("frustration"):
            return ("fast_start_delayed_feedback", 
                    "Action taken + waiting for outcome + frustration detected")
        if flags.get("doubt"):
            return ("fast_start_delayed_feedback",
                    "Action taken + waiting for outcome + doubt detected")
        return ("fast_start_delayed_feedback",
                "Action taken + waiting for outcome")
    
    # Rule 2: High urgency + low clarity
    if flags.get("high_urgency") and flags.get("low_clarity"):
        return ("strong_urge_wrong_timing",
                "High urgency + low clarity detected")
    
    # Rule 3: High urgency without action
    if flags.get("high_urgency") and not flags.get("action_taken"):
        if flags.get("doubt") or flags.get("low_clarity"):
            return ("strong_urge_wrong_timing",
                    "High urgency without action + doubt/uncertainty")
    
    # Rule 4: Seeking validation + hesitation
    if flags.get("seeking_validation"):
        if not flags.get("action_taken"):
            return ("waiting_for_permission",
                    "Seeking validation without action taken")
        if flags.get("doubt"):
            return ("waiting_for_permission",
                    "Seeking validation + doubt detected")
    
    # Rule 5: Emotional intensity + low clarity
    if flags.get("emotional_intensity") and flags.get("low_clarity"):
        return ("emotional_noise_low_clarity",
                "Emotional intensity + low clarity detected")
    
    # Rule 6: Emotional intensity alone (high)
    if flags.get("emotional_intensity"):
        if flags.get("frustration"):
            return ("emotional_noise_low_clarity",
                    "Emotional intensity + frustration")
    
    # Rule 7: Control seeking behavior
    if flags.get("control_seeking"):
        return ("pattern_returning_control",
                "Control-seeking behavior detected")
    
    # Rule 8: Recovery signals
    if flags.get("recovery_needed"):
        return ("energy_recovery",
                "Recovery/exhaustion signals detected")
    
    # Rule 9: Momentum signals
    if flags.get("momentum") and flags.get("action_taken"):
        return ("momentum_building",
                "Momentum + action signals detected")
    
    # Rule 10: Something unsaid
    if flags.get("something_unsaid"):
        return ("holding_back_expression",
                "Holding back expression signals detected")
    
    # Rule 11: High drive but no clear direction
    if flags.get("high_urgency") and not flags.get("momentum"):
        return ("high_drive_low_signal",
                "High urgency without clear momentum")
    
    # Rule 12: Low clarity / indecision dominant
    if flags.get("low_clarity") and flags.get("doubt"):
        return ("decision_avoidance",
                "Low clarity + doubt = decision avoidance")
    
    # No strong signals - return None to fall back to default logic
    return (None, "No strong lived-state signals detected")


def select_pattern_for_user(user_id: str, signal_flags: Dict[str, bool], chart_data: Optional[dict] = None) -> tuple:
    """
    Select appropriate pattern template based on signal flags.
    Phase 2: Signal-based selection with fallback.
    
    Returns (pattern_key, reason)
    """
    import hashlib
    from datetime import datetime, timezone
    
    # First try signal-based selection
    if signal_flags:
        pattern_key, reason = select_pattern_from_signals(signal_flags)
        if pattern_key:
            logger.info(f"[HomeInsight] Signal-selected pattern '{pattern_key}' for user {user_id[:8]}: {reason}")
            return (pattern_key, reason)
    
    # Fallback: deterministic daily variety (when no strong signals)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    seed = hashlib.sha256(f"{user_id}:{today}".encode()).hexdigest()
    
    # Get list of pattern keys (excluding default)
    pattern_keys = [k for k in PATTERN_TEMPLATES.keys() if k != "default"]
    
    # Select based on seed
    index = int(seed[:8], 16) % len(pattern_keys)
    selected = pattern_keys[index]
    
    logger.info(f"[HomeInsight] Fallback-selected pattern '{selected}' for user {user_id[:8]}")
    return (selected, "No lived-state signals - using daily rotation")


async def generate_daily_insight(db, user_id: str) -> Dict[str, Any]:
    """
    Generate structured daily insight for Home Screen.
    
    Phase 2: Signal-based pattern selection from lived-state data.
    Returns the new structured format with debug info.
    """
    from datetime import datetime, timezone, timedelta
    from bson import ObjectId
    
    logger.info(f"[HomeInsight] Generating insight for user {user_id[:8]}...")
    
    # =================================================================
    # STEP 1: Collect lived-state signals from recent activity
    # =================================================================
    texts_to_analyze = []
    signal_sources = []
    
    # Calculate cutoff date (no timezone for MongoDB comparison with naive datetimes)
    from datetime import datetime, timedelta
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    # Get recent journal entries (last 7 days)
    try:
        journal_cursor = db.journal.find({
            "user_id": user_id,
            "created_at": {"$gte": seven_days_ago}
        }).sort("created_at", -1).limit(10)
        
        async for entry in journal_cursor:
            content = entry.get("content", "")
            if content:
                texts_to_analyze.append(content)
                signal_sources.append("journal")
    except Exception as e:
        logger.debug(f"[HomeInsight] Journal fetch error: {e}")
    
    # Get recent mirror chat insights (last 7 days)
    try:
        chat_cursor = db.mirror_insights.find({
            "user_id": user_id,
            "created_at": {"$gte": seven_days_ago.isoformat()}
        }).sort("created_at", -1).limit(10)
        
        async for insight in chat_cursor:
            content = insight.get("content", "") or insight.get("insight", "")
            if content:
                texts_to_analyze.append(content)
                signal_sources.append("mirror_chat")
    except Exception as e:
        logger.debug(f"[HomeInsight] Mirror chat fetch error: {e}")
    
    # Get recent lunar reflections (last 7 days)
    try:
        lunar_cursor = db.lunar_journal.find({
            "user_id": user_id,
            "created_at": {"$gte": seven_days_ago.isoformat()}
        }).sort("created_at", -1).limit(5)
        
        async for reflection in lunar_cursor:
            content = reflection.get("content", "") or reflection.get("reflection", "")
            if content:
                texts_to_analyze.append(content)
                signal_sources.append("lunar_reflection")
    except Exception as e:
        logger.debug(f"[HomeInsight] Lunar journal fetch error: {e}")
    
    logger.info(f"[HomeInsight] Collected {len(texts_to_analyze)} texts from {len(set(signal_sources))} sources")
    
    # =================================================================
    # STEP 2: Extract signal flags (combined + per-entry for trajectory)
    # =================================================================
    signal_flags = extract_signal_flags(texts_to_analyze)
    active_flags = {k: v for k, v in signal_flags.items() if v}
    logger.info(f"[HomeInsight] Active signal flags: {list(active_flags.keys())}")
    
    # Extract per-entry flags for trajectory detection
    entry_history = extract_signal_flags_per_entry(texts_to_analyze)
    
    # =================================================================
    # STEP 3: Detect pattern phase (trajectory awareness)
    # =================================================================
    phase, phase_description, trajectory_summary = detect_pattern_phase(signal_flags, entry_history)
    logger.info(f"[HomeInsight] Detected phase: {phase} - {phase_description}")
    
    # =================================================================
    # STEP 4: Select pattern based on signals
    # =================================================================
    chart_data = None
    try:
        chart_data = await db.charts.find_one({"user_id": user_id})
    except Exception as e:
        logger.debug(f"[HomeInsight] Could not load chart: {e}")
    
    pattern_key, selection_reason = select_pattern_for_user(user_id, signal_flags, chart_data)
    template = PATTERN_TEMPLATES.get(pattern_key, PATTERN_TEMPLATES["default"])
    
    # =================================================================
    # STEP 5: Apply phase modifier to template
    # =================================================================
    modified_template = apply_phase_modifier(template, phase, phase_description)
    
    # =================================================================
    # STEP 6: Build response with debug info
    # =================================================================
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Determine confidence based on signal strength
    confidence = "low"
    if len(active_flags) >= 3:
        confidence = "high"
    elif len(active_flags) >= 1:
        confidence = "medium"
    
    # Build Mirror-format body from what_happening
    body = modified_template["what_happening"]
    # Clean any system language
    body = body.replace("Looking at your timeline", "").replace("a certain rhythm appears", "").strip()
    if body.startswith(","):
        body = body[1:].strip()
    
    # Use why_feels as bridge if it's personal enough
    bridge = modified_template.get("why_feels", "")
    if "timeline" in bridge.lower() or "rhythm" in bridge.lower() or "pattern suggests" in bridge.lower():
        bridge = ""  # Don't use system-sounding bridges
    
    return {
        "success": True,
        "date": today,
        "pattern_id": f"{pattern_key}_{today.replace('-', '')}",
        "title": modified_template["title"],
        # New Mirror-format fields
        "body": body,
        "bridge": bridge if bridge else None,
        # Legacy fields (for compatibility)
        "what_happening": modified_template["what_happening"],
        "why_feels": modified_template["why_feels"],
        "watch_for": modified_template["watch_for"],
        "better_move": modified_template["better_move"],
        "interrupt": modified_template["interrupt"],
        "phase": phase,
        "phase_description": phase_description,
        "confidence": confidence,
        "card_version": "mirror_v3",  # Version flag for frontend
        "debug": {
            "pattern_key": pattern_key,
            "selection_reason": selection_reason,
            "phase": phase,
            "phase_description": phase_description,
            "trajectory_summary": trajectory_summary,
            "signal_flags": active_flags,
            "signal_sources": list(set(signal_sources)),
            "texts_analyzed": len(texts_to_analyze),
            "entries_in_history": len(entry_history),
            "source": "signal_v3_trajectory" if active_flags else "fallback_rotation",
            "computed_at": datetime.now(timezone.utc).isoformat()
        }
    }
