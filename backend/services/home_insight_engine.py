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
        "title": "Fast Start, Delayed Feedback",
        "what_happening": "You moved quickly and executed, but you're not seeing results yet.",
        "why_feels": "There is a gap between your action speed and when outcomes become visible.",
        "watch_for": "Switching direction too early or pushing harder out of frustration.",
        "better_move": "Hold your current direction and give it one more cycle to land.",
        "interrupt": "If you feel urgency to change, pause and check if it's impatience."
    },
    "high_drive_low_signal": {
        "title": "High Drive, Low Signal",
        "what_happening": "You're ready to move, but the direction isn't clear yet.",
        "why_feels": "The energy is there. The clarity isn't keeping pace.",
        "watch_for": "Starting things to escape the discomfort of not knowing.",
        "better_move": "Name what you're waiting to understand before acting.",
        "interrupt": "If you catch yourself doing busy work—pause and ask what you're avoiding."
    },
    "emotional_noise_low_clarity": {
        "title": "Emotional Noise, Low Clarity",
        "what_happening": "Feelings are running high. Thinking isn't keeping pace.",
        "why_feels": "You're processing something that doesn't have words yet.",
        "watch_for": "Making decisions while the wave is still moving.",
        "better_move": "Let feelings pass before deciding anything permanent.",
        "interrupt": "If someone asks 'what's wrong' and you snap—that's the signal to pause."
    },
    "strong_urge_wrong_timing": {
        "title": "Strong Urge, Wrong Timing",
        "what_happening": "Something feels urgent, but the conditions aren't aligned yet.",
        "why_feels": "Your internal readiness is ahead of external circumstances.",
        "watch_for": "Forcing outcomes that need more time to mature.",
        "better_move": "Prepare fully so you're ready when the opening appears.",
        "interrupt": "If you're about to push through resistance—check if waiting costs anything real."
    },
    "pattern_returning_control": {
        "title": "Pattern Returning: Control Under Pressure",
        "what_happening": "A familiar response is showing up again. You've been here before.",
        "why_feels": "When things feel uncertain, control feels like the only option.",
        "watch_for": "Tightening your grip on things you can't actually control.",
        "better_move": "Name what you're actually afraid of losing.",
        "interrupt": "If you catch yourself micromanaging—that's the pattern talking."
    },
    "waiting_for_permission": {
        "title": "Waiting for Permission",
        "what_happening": "You know what you want to do, but you're waiting for someone to say it's okay.",
        "why_feels": "There's a gap between your own knowing and trusting it.",
        "watch_for": "Asking for opinions when you already have your answer.",
        "better_move": "Notice what you'd do if no one was watching.",
        "interrupt": "If you're about to ask 'what do you think'—check if you already know."
    },
    "momentum_building": {
        "title": "Momentum Building",
        "what_happening": "Things are starting to move. Not finished, but in motion.",
        "why_feels": "Early traction creates a mix of excitement and impatience.",
        "watch_for": "Overcommitting before you see what's actually working.",
        "better_move": "Keep doing what's working. Don't add complexity yet.",
        "interrupt": "If you're tempted to scale before stabilizing—slow down."
    },
    "holding_back_expression": {
        "title": "Something Unsaid",
        "what_happening": "There's something you want to express but haven't yet.",
        "why_feels": "The words are forming, but the moment doesn't feel right.",
        "watch_for": "Waiting so long that the moment passes entirely.",
        "better_move": "Say the smaller version first. See how it lands.",
        "interrupt": "If you've rehearsed it in your head more than twice—it's time."
    },
    "decision_avoidance": {
        "title": "Decision in the Room",
        "what_happening": "A choice is present that you're circling but not making.",
        "why_feels": "Both options have real costs, so neither feels safe.",
        "watch_for": "Gathering more information as a way to delay.",
        "better_move": "Name what you're actually afraid of getting wrong.",
        "interrupt": "If you've been 'thinking about it' for more than a week—decide or drop it."
    },
    "energy_recovery": {
        "title": "Recovery Phase",
        "what_happening": "You're coming off a period of output. Energy is rebuilding.",
        "why_feels": "Lower capacity right now isn't failure—it's recalibration.",
        "watch_for": "Judging yourself for not being as productive as before.",
        "better_move": "Protect your recovery. Don't fill the space with new commitments.",
        "interrupt": "If you feel guilty for resting—that's the signal you need more rest."
    },
    "quiet_signal_day": {
        "title": "A Quiet Signal Day",
        "what_happening": "Nothing strong is pulling today. That can be information too.",
        "why_feels": "Not every day has a clear pattern. Some days are just days.",
        "watch_for": "Creating urgency where none exists.",
        "better_move": "Use the space for maintenance, not new projects.",
        "interrupt": "If you're looking for something to fix—maybe nothing needs fixing today."
    },
    "default": {
        "title": "Noticing Today",
        "what_happening": "Something is present that's worth paying attention to.",
        "why_feels": "Your attention is being drawn somewhere specific.",
        "watch_for": "Dismissing what you're noticing as unimportant.",
        "better_move": "Stay with what's here before moving to what's next.",
        "interrupt": "If you're rushing past this moment—pause and ask why."
    }
}


def select_pattern_for_user(user_id: str, chart_data: Optional[dict] = None) -> str:
    """
    Select appropriate pattern template based on available data.
    Phase 1: Simple selection logic.
    """
    import hashlib
    from datetime import datetime, timezone
    
    # Create daily seed for variety
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    seed = hashlib.sha256(f"{user_id}:{today}".encode()).hexdigest()
    
    # Get list of pattern keys (excluding default)
    pattern_keys = [k for k in PATTERN_TEMPLATES.keys() if k != "default"]
    
    # Select based on seed
    index = int(seed[:8], 16) % len(pattern_keys)
    selected = pattern_keys[index]
    
    logger.info(f"[HomeInsight] Selected pattern '{selected}' for user {user_id[:8]}...")
    return selected


async def generate_daily_insight(db, user_id: str) -> Dict[str, Any]:
    """
    Generate structured daily insight for Home Screen.
    
    Phase 1: Simple template selection with deterministic daily variety.
    Returns the new structured format.
    """
    from datetime import datetime, timezone
    from bson import ObjectId
    
    logger.info(f"[HomeInsight] Generating insight for user {user_id[:8]}...")
    
    # Fetch user chart for future use
    chart_data = None
    try:
        chart_data = await db.charts.find_one({"user_id": user_id})
    except Exception as e:
        logger.debug(f"[HomeInsight] Could not load chart: {e}")
    
    # Select pattern
    pattern_key = select_pattern_for_user(user_id, chart_data)
    template = PATTERN_TEMPLATES.get(pattern_key, PATTERN_TEMPLATES["default"])
    
    # Build response
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    return {
        "success": True,
        "date": today,
        "pattern_id": f"{pattern_key}_{today.replace('-', '')}",
        "title": template["title"],
        "what_happening": template["what_happening"],
        "why_feels": template["why_feels"],
        "watch_for": template["watch_for"],
        "better_move": template["better_move"],
        "interrupt": template["interrupt"],
        "confidence": "medium",
        "debug": {
            "pattern_key": pattern_key,
            "source": "template_v1",
            "computed_at": datetime.now(timezone.utc).isoformat()
        }
    }
