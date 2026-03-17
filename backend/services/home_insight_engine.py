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
        "what_happening": "You took action—sent the message, made the move, started the thing—but nothing came back yet. No response, no confirmation, no signal that it landed.",
        "why_feels": "You're ready for the next step, but the world hasn't caught up. That gap between 'I did my part' and 'where's the result' creates pressure that makes you want to do more.",
        "watch_for": "Sending a follow-up before it's needed. Changing your approach because silence feels like rejection. Doing more when the original move hasn't had time to land.",
        "better_move": "Let the current move finish playing out. Give it 24-48 more hours before deciding if something is wrong.",
        "interrupt": "If you're about to check your inbox again, or send another message, or pivot your strategy—stop. Ask yourself: did anything actually break, or has it just not landed yet?"
    },
    "high_drive_low_signal": {
        "title": "High Drive, Low Signal",
        "what_happening": "You have energy and you want to use it, but you don't have a clear target. So you're scanning—opening tabs, starting conversations, looking for something to put the energy into.",
        "why_feels": "The drive is real but directionless. It's like having a full tank of gas but no destination. That mismatch creates restlessness that disguises itself as productivity.",
        "watch_for": "Starting three things instead of finishing one. Filling time with tasks that feel useful but don't actually move anything forward. Confusing movement with progress.",
        "better_move": "Before you start anything new, write down the one thing that would actually matter if it got done today. Do that first.",
        "interrupt": "If you've opened a new browser tab or switched tasks in the last 10 minutes without finishing something—that's the pattern. Close everything and pick one thing."
    },
    "emotional_noise_low_clarity": {
        "title": "Emotional Noise, Low Clarity",
        "what_happening": "You're feeling something strongly, but you can't name it cleanly. Someone asked 'what's wrong' and you couldn't give a straight answer—not because nothing's wrong, but because it's not one thing.",
        "why_feels": "Multiple signals are hitting at once—frustration, disappointment, maybe some old stuff getting stirred up. The noise makes it hard to think straight, and that creates more frustration.",
        "watch_for": "Making a decision to get relief from the discomfort. Picking a fight because the tension needs somewhere to go. Saying something you'll need to walk back later.",
        "better_move": "Don't try to solve it right now. Write down what you're feeling without trying to fix it. Let the wave move through before you act on any of it.",
        "interrupt": "If someone asks what's wrong and you feel the urge to snap or give a sharp answer—that's the signal. Say 'I don't know yet' and give yourself more time."
    },
    "strong_urge_wrong_timing": {
        "title": "Strong Urge, Wrong Timing",
        "what_happening": "You know what you want to do. You've been ready. But the situation isn't there yet—the other person isn't ready, the opportunity hasn't opened, the pieces aren't in place.",
        "why_feels": "Your internal clock says 'now' but the external clock says 'not yet.' That mismatch creates pressure to force something that would work better if you waited.",
        "watch_for": "Trying to manufacture the opening instead of waiting for it. Pushing someone to be ready before they are. Making the move anyway and hoping it works out.",
        "better_move": "Stay ready without acting. Use this time to get more prepared so when the window opens, you can move cleanly.",
        "interrupt": "If you're about to push through resistance because you're tired of waiting—pause. Ask yourself: will forcing this now create a bigger problem than waiting?"
    },
    "pattern_returning_control": {
        "title": "Pattern Returning: Control Under Pressure",
        "what_happening": "Something uncertain showed up—a conversation that didn't go as planned, a result you can't predict, a situation you can't fully manage. And your response is to tighten your grip on everything you can control.",
        "why_feels": "When you can't control the big thing, controlling the small things feels like safety. It's not—it's just a way to manage anxiety. But it feels productive in the moment.",
        "watch_for": "Over-preparing for things that don't need it. Checking details you've already checked. Asking for updates on things that are already in motion. Managing other people's work too closely.",
        "better_move": "Name the thing you're actually worried about—the real thing, not the surface one. Then ask: is controlling these details actually helping that, or just keeping you busy?",
        "interrupt": "If you're reviewing something for the third time or asking someone for a status update you don't need—that's the pattern. Step back and let it breathe."
    },
    "waiting_for_permission": {
        "title": "Waiting for Permission",
        "what_happening": "You know what you want to do. You've known for a while. But you haven't done it yet because part of you is waiting for someone to say it's the right call—a sign, a green light, an external yes.",
        "why_feels": "The decision is already made inside you, but you don't fully trust it. So you keep gathering input, asking questions, running scenarios—not to decide, but to delay committing.",
        "watch_for": "Asking for opinions you don't actually need. Framing a statement as a question. Waiting for someone to give you permission you could give yourself.",
        "better_move": "Notice what you would do if you knew no one would judge the choice. That's probably the answer.",
        "interrupt": "If you're about to ask someone 'what do you think I should do'—stop. Check if you already know what you'd do if they weren't there."
    },
    "momentum_building": {
        "title": "Momentum Building",
        "what_happening": "Something is working. You got traction—a response, a result, a sign that the thing you're doing is landing. It's not finished, but it's moving.",
        "why_feels": "Early wins create urgency to do more, faster. The excitement is real, but so is the temptation to overcommit before you know what's actually sustainable.",
        "watch_for": "Adding complexity before the current approach stabilizes. Making promises based on early results. Scaling before you understand what's actually working.",
        "better_move": "Keep doing exactly what's working. Don't optimize yet. Don't expand yet. Let the current move finish playing out before you add anything new.",
        "interrupt": "If you're thinking about a bigger version of this before the current one is stable—slow down. Finish this phase first."
    },
    "holding_back_expression": {
        "title": "Something Unsaid",
        "what_happening": "There's something you want to say—to a specific person, about a specific thing—and you haven't said it yet. You've thought about how to phrase it. You've played out scenarios. But you haven't pulled the trigger.",
        "why_feels": "The thing is real, but the moment hasn't felt right. Or you're worried how it will land. Or you're not sure if saying it will actually help. So it stays stuck.",
        "watch_for": "Waiting for a perfect moment that doesn't come. Hinting at the thing instead of saying it directly. Letting resentment build because the other person should have figured it out by now.",
        "better_move": "Say the smaller, simpler version. You don't have to say all of it—just the first honest piece. See how that lands before deciding on the rest.",
        "interrupt": "If you've mentally rehearsed this conversation more than twice—it's ready. The next time you see that person, say the first sentence."
    },
    "decision_avoidance": {
        "title": "Decision in the Room",
        "what_happening": "There's a choice you've been sitting with for days or weeks. You've thought about it, analyzed it, maybe talked to people about it. But you haven't decided—because both options have real costs and neither feels safe.",
        "why_feels": "Deciding means closing a door. That loss is real, even if the gain is too. So you stay in analysis mode, where the decision stays theoretical and the consequences stay hypothetical.",
        "watch_for": "Gathering more information when you already have enough. Running the same mental loop without new inputs. Treating 'I'm still deciding' as an answer when it's actually avoidance.",
        "better_move": "Name what you're actually afraid of getting wrong. Not the practical risk—the emotional one. That's the real thing stopping you.",
        "interrupt": "If you've been 'thinking about' this decision for more than a week without new information—it's time. Decide by end of day, or decide to drop it entirely."
    },
    "energy_recovery": {
        "title": "Recovery Phase",
        "what_happening": "You pushed hard recently—maybe a deadline, maybe an emotional stretch, maybe just an extended period of output. Now you're running on less, and it's showing up in your capacity.",
        "why_feels": "You're comparing today's energy to a version of yourself that didn't just spend a lot. That comparison makes normal recovery feel like failure. It's not—it's the cost of what you did.",
        "watch_for": "Forcing productivity when your body is asking for rest. Saying yes to things because you feel guilty about slowing down. Judging yourself for not being at full capacity.",
        "better_move": "Protect the recovery window. Don't fill the empty space with new commitments. Let yourself move slower today so you can move faster later.",
        "interrupt": "If you feel guilty about doing less—that's the signal you need the rest more, not less. Stay down one more day."
    },
    "quiet_signal_day": {
        "title": "A Quiet Signal Day",
        "what_happening": "No urgent pull today. No strong emotion. No crisis. No breakthrough. Just a regular Tuesday. And weirdly, that might feel uncomfortable.",
        "why_feels": "You're used to having something to respond to. When there's no fire, you might be tempted to start one—create urgency, find a problem, manufacture intensity.",
        "watch_for": "Looking for something to fix when nothing is broken. Starting a conversation that doesn't need to happen. Making a neutral day feel significant because quiet feels wrong.",
        "better_move": "Use the space for maintenance—small tasks, loose ends, things that don't need urgency but do need attention. Don't fill it with new drama.",
        "interrupt": "If you're scanning for something to worry about or react to—stop. Maybe today is just a day. Let it be that."
    },
    "default": {
        "title": "Something Present",
        "what_happening": "There's something here today that's asking for your attention. Not an emergency—more like a pull. You might not have words for it yet, but you're noticing it.",
        "why_feels": "Your system is picking up a signal that your conscious mind hasn't fully processed. That's not a problem—it's information. The work is to stay with it long enough to hear what it's saying.",
        "watch_for": "Dismissing the feeling because you can't explain it. Moving too fast past something that needed another minute. Letting noise drown out something quieter but real.",
        "better_move": "Don't rush to label it. Sit with what you're noticing before you try to solve it. Let it become clearer before you act.",
        "interrupt": "If you're about to switch tasks or move on and something in you hesitates—listen to that. The hesitation is the signal."
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
    
    # Get recent journal entries (last 7 days)
    try:
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        journal_cursor = db.journal.find({
            "user_id": user_id,
            "timestamp": {"$gte": seven_days_ago.isoformat()}
        }).sort("timestamp", -1).limit(10)
        
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
    # STEP 2: Extract signal flags
    # =================================================================
    signal_flags = extract_signal_flags(texts_to_analyze)
    active_flags = {k: v for k, v in signal_flags.items() if v}
    logger.info(f"[HomeInsight] Active signal flags: {list(active_flags.keys())}")
    
    # =================================================================
    # STEP 3: Select pattern based on signals
    # =================================================================
    chart_data = None
    try:
        chart_data = await db.charts.find_one({"user_id": user_id})
    except Exception as e:
        logger.debug(f"[HomeInsight] Could not load chart: {e}")
    
    pattern_key, selection_reason = select_pattern_for_user(user_id, signal_flags, chart_data)
    template = PATTERN_TEMPLATES.get(pattern_key, PATTERN_TEMPLATES["default"])
    
    # =================================================================
    # STEP 4: Build response with debug info
    # =================================================================
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Determine confidence based on signal strength
    confidence = "low"
    if len(active_flags) >= 3:
        confidence = "high"
    elif len(active_flags) >= 1:
        confidence = "medium"
    
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
        "confidence": confidence,
        "debug": {
            "pattern_key": pattern_key,
            "selection_reason": selection_reason,
            "signal_flags": active_flags,
            "signal_sources": list(set(signal_sources)),
            "texts_analyzed": len(texts_to_analyze),
            "source": "signal_v2" if active_flags else "fallback_rotation",
            "computed_at": datetime.now(timezone.utc).isoformat()
        }
    }
