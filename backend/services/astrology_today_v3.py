"""
Astrology Today V3 - Real-World Clarity Engine
===============================================

CORE PRINCIPLE:
Transform abstract astro-speak into instantly understandable, grounded insights.

MANDATORY OUTPUT FORMAT:
1. HEADLINE: One clear sentence
2. WHAT'S ACTUALLY HAPPENING: 2-3 real-world dynamics
3. HOW THIS SHOWS UP FOR YOU: 2-3 observable behaviors
4. WHAT THIS MAY FEEL LIKE: 2-3 physical/emotional signals
5. THE MOVE: Small behavioral shift (not advice)

SUCCESS CRITERIA:
A non-astrology user should:
- Immediately understand it
- Recognize where it applies in their day
- NOT ask "What does this mean?"
"""

import logging
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# V3 TENSION TYPES - Mapped to Real-World Behaviors
# =============================================================================

class TodayTensionV3(str, Enum):
    HESITATION_WHEN_READY = "hesitation_when_ready"
    RUSHING_BEFORE_CLEAR = "rushing_before_clear"
    EMOTIONAL_BEFORE_MENTAL = "emotional_before_mental"
    PAST_RESURFACING = "past_resurfacing"
    CHANGE_WITHOUT_DIRECTION = "change_without_direction"
    MISMATCHED_TIMING = "mismatched_timing"
    HOLDING_PAST_DONE = "holding_past_done"


# =============================================================================
# V3 STRUCTURED TEMPLATES - All Grounded in Real Life
# =============================================================================

V3_TEMPLATES = {
    TodayTensionV3.HESITATION_WHEN_READY: {
        "headlines": [
            "You may hesitate in a moment where you're actually ready to step forward.",
            "There's a conversation or decision today where you might pause — even though you know what to do.",
            "You could find yourself holding back when it's actually time to speak or act.",
            "A moment may come today where you're expected to step up, and you hesitate because you're not fully sure yet.",
        ],
        "whats_happening": [
            "A moment is coming where you'll be expected to decide, speak, or commit to something.",
            "Part of you knows you're ready — another part is looking for more certainty first.",
            "The opening is there, but you might let it pass while checking if you're 'really' ready.",
            "External timing is saying 'now' while internal timing is saying 'wait'.",
        ],
        "how_it_shows_up": [
            "You start to say something in a conversation, then edit it or pull back.",
            "You draft a message, then delete it. Draft again. Pause.",
            "You're about to make a decision, then think 'maybe I should wait' — even though waiting won't add anything new.",
            "You defer to someone else when you actually had the answer.",
            "You over-explain or qualify something that could have been a simple statement.",
        ],
        "what_it_feels_like": [
            "A slight hesitation in your chest right before speaking.",
            "The urge to 'check one more thing' before committing.",
            "A sense that you almost did something, then didn't.",
            "Mild restlessness after a moment passes where you could have stepped forward.",
            "Second-guessing yourself right after you finally say something.",
        ],
        "the_move": [
            "You don't need to force it. Just let your first answer stand — before the edit kicks in.",
            "Just take the opening when it appears. The certainty comes after, not before.",
            "Just say 10% more than you normally would.",
            "Just notice when you're about to defer — and don't.",
        ],
    },
    
    TodayTensionV3.RUSHING_BEFORE_CLEAR: {
        "headlines": [
            "You might feel pressure to act on something before you fully understand it.",
            "There's an urge today to make a decision before all the pieces are visible.",
            "You may want to move forward on something that isn't quite ready yet.",
            "Something is asking for a response before you've had time to process it.",
        ],
        "whats_happening": [
            "Something is asking for a response, but the full picture isn't available yet.",
            "There's external pressure — or internal impatience — pushing for action.",
            "The timing feels urgent, but the clarity hasn't arrived.",
            "You want to be done thinking about this. But you're not done yet.",
        ],
        "how_it_shows_up": [
            "You reply to a message quickly, then wish you'd waited.",
            "You make a decision just to stop thinking about it — not because you're ready.",
            "You commit to something before checking in with yourself.",
            "You say yes or no before you've actually processed the question.",
            "You send the email, then immediately think of what you should have said.",
        ],
        "what_it_feels_like": [
            "A restless need to 'just decide already.'",
            "Tension that feels like it would go away if you could just act.",
            "A buzzy, forward-leaning energy that doesn't want to pause.",
            "Slight regret after acting — the sense you moved too fast.",
            "Relief when you finally act, followed by 'wait, did I think that through?'",
        ],
        "the_move": [
            "You don't need to slow everything down. Just pause for three breaths before responding to the next thing that asks for a decision.",
            "Just say 'let me think about it' once today — even if you think you know the answer.",
            "Just let one thing stay undecided until tomorrow.",
            "Just notice when you're acting to end discomfort rather than because you're ready.",
        ],
    },
    
    TodayTensionV3.EMOTIONAL_BEFORE_MENTAL: {
        "headlines": [
            "You might react to something today before you've fully understood what triggered it.",
            "There's a moment coming where your feelings may arrive faster than your thoughts.",
            "You could find yourself responding emotionally before you've processed what happened.",
            "Something may hit a nerve today — and your reaction might surprise you.",
        ],
        "whats_happening": [
            "Something will touch a nerve — and your body will respond before your mind catches up.",
            "A conversation or moment may trigger a feeling that's bigger than the situation calls for.",
            "There's old material underneath that might hijack a present-moment response.",
            "Your nervous system is more activated than usual — smaller things feel bigger.",
        ],
        "how_it_shows_up": [
            "You snap at someone, then realize it wasn't really about them.",
            "You tear up or get heated, then notice the reaction was disproportionate.",
            "You defend yourself before you've even been accused of anything.",
            "You shut down or pull back in a conversation, then wonder why.",
            "You say something with more edge than you intended.",
        ],
        "what_it_feels_like": [
            "Heat rising before you've identified the thought behind it.",
            "An urge to speak or react that feels automatic.",
            "A sense of being hijacked by a feeling you didn't invite.",
            "Surprise at your own reaction — 'where did that come from?'",
            "Physical tension (jaw, shoulders, chest) before conscious awareness.",
        ],
        "the_move": [
            "You don't need to suppress it. Just name it to yourself before you act on it: 'I'm having a reaction.'",
            "Just take one breath between feeling it and saying it.",
            "Just notice if the size of your reaction matches the size of the moment.",
            "Just wait three seconds before responding when you feel the heat rise.",
        ],
    },
    
    TodayTensionV3.PAST_RESURFACING: {
        "headlines": [
            "Something from the past may show up uninvited today — a memory, a feeling, a person.",
            "You might find yourself thinking about something you thought was resolved.",
            "An old feeling or situation could resurface when you weren't expecting it.",
            "The past might tap you on the shoulder today.",
        ],
        "whats_happening": [
            "The past is asking for attention — even though you didn't invite it.",
            "Something triggered a memory or feeling that still has weight.",
            "There's unfinished business underneath that's looking for closure.",
            "An old pattern or feeling is moving through — not to derail you, but to be seen.",
        ],
        "how_it_shows_up": [
            "You think about someone you haven't thought about in a while — and notice it still affects you.",
            "A song, photo, or mention brings you right back to a moment you thought was closed.",
            "You catch yourself replaying an old conversation in your head.",
            "You feel a familiar ache — one you recognize from before.",
            "You compare your current situation to something from the past without meaning to.",
        ],
        "what_it_feels_like": [
            "A heaviness that doesn't match today but feels familiar.",
            "Nostalgia mixed with something unresolved.",
            "The sense that you're 'back there' even though you're physically here.",
            "A pull toward something you decided to leave behind.",
            "Surprise that this still has power over you.",
        ],
        "the_move": [
            "You don't need to resolve it today. Just notice that it's visiting — and let it pass without following it.",
            "Just acknowledge it: 'This is still alive in me.' That's enough.",
            "Just let it surface without making it mean you haven't moved on.",
            "Just notice it without getting on the train.",
        ],
    },
    
    TodayTensionV3.CHANGE_WITHOUT_DIRECTION: {
        "headlines": [
            "Something may feel like it's shifting today, but you can't name what it's shifting toward.",
            "You might sense that things are changing — without knowing what the change means yet.",
            "There's movement happening, but the destination isn't visible.",
            "The ground is moving, but you can't see where it's settling.",
        ],
        "whats_happening": [
            "The ground is shifting, but the new shape hasn't formed.",
            "You're in a transition — but you don't know what you're transitioning into.",
            "Old certainties are loosening, but new ones haven't arrived.",
            "Something is ending or changing, and the next thing hasn't become clear.",
        ],
        "how_it_shows_up": [
            "You make a decision, then unmake it. Then make a different one. Nothing sticks.",
            "You start something with energy, then lose the thread halfway through.",
            "You can't quite commit to plans because you don't know what you'll want later.",
            "You feel restless but can't identify what you're restless for.",
            "You have trouble concentrating because everything feels temporary.",
        ],
        "what_it_feels_like": [
            "A vague sense of 'something's different' that you can't pin down.",
            "Groundlessness that isn't quite anxiety but isn't peace either.",
            "Difficulty focusing because everything feels in-between.",
            "The sense that you're waiting for something to become clear.",
            "Mild vertigo — the familiar feels slightly unfamiliar.",
        ],
        "the_move": [
            "You don't need to find direction today. Just stay present to what's here — and trust the shape will form.",
            "Just do the next small thing without needing to know where it leads.",
            "Just let the uncertainty exist without trying to resolve it.",
            "Just hold the 'I don't know' without rushing to fill it.",
        ],
    },
    
    TodayTensionV3.MISMATCHED_TIMING: {
        "headlines": [
            "Your inner pace and the world's pace might not match today.",
            "You may feel pressure to move at a speed that doesn't feel right.",
            "What you need to do and what you're ready to do might be at odds.",
            "There's friction between your rhythm and what's being asked of you.",
        ],
        "whats_happening": [
            "External demands are asking for more than your system wants to give.",
            "Or: you're ready to move, but circumstances are asking you to wait.",
            "There's a mismatch between your rhythm and what's being asked of you.",
            "The world is running at a different speed than you are.",
        ],
        "how_it_shows_up": [
            "You feel rushed even when the deadline isn't that tight.",
            "You feel bored or stuck even when there's plenty to do.",
            "You push through fatigue because stopping doesn't seem like an option.",
            "You wait when every part of you wants to move.",
            "You feel out of sync with the people around you.",
        ],
        "what_it_feels_like": [
            "Friction between what you want to do and what you have to do.",
            "The sense that you're swimming against the current.",
            "Tiredness that doesn't match your actual effort.",
            "Impatience that doesn't match the actual situation.",
            "The sense of being slightly out of phase with everyone else.",
        ],
        "the_move": [
            "You don't need to force the timing. Just acknowledge the mismatch — and work with it instead of against it.",
            "Just do one thing at your own pace today. Even if it's small.",
            "Just give yourself permission to be out of sync.",
            "Just notice when you're fighting the current, and stop for a moment.",
        ],
    },
    
    TodayTensionV3.HOLDING_PAST_DONE: {
        "headlines": [
            "You might be holding onto something that's actually ready to be released.",
            "There's something that's finished, but you're not letting it go yet.",
            "You could be keeping something alive that's asking to close.",
            "Something has ended, but you haven't fully let it end.",
        ],
        "whats_happening": [
            "A chapter is ending — but you're keeping it open.",
            "Something completed its purpose, but you're still carrying it.",
            "Letting go is available, but you haven't taken it.",
            "You're maintaining something that doesn't need maintaining anymore.",
        ],
        "how_it_shows_up": [
            "You revisit a decision you already made — and re-open the debate.",
            "You stay in contact with something (or someone) past the natural end point.",
            "You keep a project or task 'in progress' even though it's essentially done.",
            "You rehearse conversations that already happened.",
            "You keep checking on something that doesn't need checking.",
        ],
        "what_it_feels_like": [
            "Holding something that's heavier than it needs to be.",
            "The sense that you 'should' have let go by now.",
            "Relief when you imagine putting it down — but not actually doing it.",
            "Fatigue from carrying something that's asking to be set down.",
            "A lingering sense of 'not quite done' with something that is done.",
        ],
        "the_move": [
            "You don't need to release everything. Just name one thing that's done — and let it be done.",
            "Just stop checking on something that doesn't need checking.",
            "Just close one loop that's been sitting open.",
            "Just let something be finished without one more look.",
        ],
    },
}


# =============================================================================
# HOUSE CONTEXT - WHERE THIS SHOWS UP IN LIFE
# =============================================================================

HOUSE_CONTEXT_V3 = {
    1: "how you show up and present yourself",
    2: "money, resources, and what you value",
    3: "conversations, messages, and daily decisions",
    4: "home, family, and your private life",
    5: "creativity, self-expression, and things you create",
    6: "work, daily routines, and health habits",
    7: "relationships, partnerships, and one-on-one dynamics",
    8: "shared resources, intimacy, and what you share with others",
    9: "beliefs, learning, and long-term direction",
    10: "career, public life, and how you're seen professionally",
    11: "friendships, community, and group dynamics",
    12: "rest, reflection, and what you process privately",
}


# =============================================================================
# MAPPING FROM OLD TENSION TYPES
# =============================================================================

TENSION_MAPPING = {
    "forcing_clarity": TodayTensionV3.RUSHING_BEFORE_CLEAR,
    "movement_before_alignment": TodayTensionV3.HESITATION_WHEN_READY,
    "reacting_before_understanding": TodayTensionV3.EMOTIONAL_BEFORE_MENTAL,
    "reopening_unresolved": TodayTensionV3.PAST_RESURFACING,
    "shift_before_direction": TodayTensionV3.CHANGE_WITHOUT_DIRECTION,
    "inner_pace_outer_timing": TodayTensionV3.MISMATCHED_TIMING,
    "completion_resistance": TodayTensionV3.HOLDING_PAST_DONE,
}


def map_to_v3_tension(old_tension: str) -> TodayTensionV3:
    """Map old tension string to V3 type."""
    return TENSION_MAPPING.get(old_tension, TodayTensionV3.HESITATION_WHEN_READY)


# =============================================================================
# MAIN GENERATION FUNCTION
# =============================================================================

def generate_today_v3(
    tension_type: TodayTensionV3,
    day_class: str = "normal_flow",
    activated_house: Optional[int] = None,
    sun_sign: Optional[str] = None,
    transit_info: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate V3 Today insight with mandatory structure.
    
    Returns:
    {
        "headline": str,
        "whats_happening": List[str] (2-3 items),
        "how_it_shows_up": List[str] (2-3 items),
        "what_it_feels_like": List[str] (2-3 items),
        "the_move": str,
        "where_context": str or None,
        "technical": {...} (hidden layer)
    }
    """
    # Generate seed for variety
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    seed = int(hashlib.md5(date_str.encode()).hexdigest()[:8], 16)
    
    # Get templates
    templates = V3_TEMPLATES.get(tension_type, V3_TEMPLATES[TodayTensionV3.HESITATION_WHEN_READY])
    
    # Day class affects headline selection
    day_offset = {"phase_shift": 0, "cycle_event": 1, "normal_flow": 2}.get(day_class, 2)
    
    # Select headline
    headline_idx = (seed + day_offset) % len(templates["headlines"])
    headline = templates["headlines"][headline_idx]
    
    # Select 2-3 items for each section with variety
    def select_items(items: List[str], count: int = 3) -> List[str]:
        start = seed % max(1, len(items) - count + 1)
        return items[start:start + count]
    
    whats_happening = select_items(templates["whats_happening"], 3)
    how_it_shows_up = select_items(templates["how_it_shows_up"], 3)
    what_it_feels_like = select_items(templates["what_it_feels_like"], 3)
    
    # Select move
    move_idx = seed % len(templates["the_move"])
    the_move = templates["the_move"][move_idx]
    
    # Build where context if house is available
    where_context = None
    if activated_house and activated_house in HOUSE_CONTEXT_V3:
        where_context = f"This may show up especially around {HOUSE_CONTEXT_V3[activated_house]}."
    
    # Build technical layer (hidden, for expandable)
    technical = None
    if transit_info or activated_house:
        technical = {
            "transit_info": transit_info,
            "activated_house": activated_house,
            "house_meaning": HOUSE_CONTEXT_V3.get(activated_house) if activated_house else None,
        }
    
    return {
        "success": True,
        "version": "v3_clarity",
        "date": date_str,
        # MANDATORY STRUCTURE
        "headline": headline,
        "whats_happening": whats_happening,
        "how_it_shows_up": how_it_shows_up,
        "what_it_feels_like": what_it_feels_like,
        "the_move": the_move,
        "where_context": where_context,
        # HIDDEN TECHNICAL LAYER
        "technical": technical,
        # METADATA
        "tension_type": tension_type.value,
        "day_class": day_class,
    }


# =============================================================================
# HUMAN-READABLE EVENT TYPE MAPPING
# =============================================================================
# Maps raw event type keys to clear, understandable descriptions

EVENT_TYPE_READABLE = {
    "new_moon": "New Moon — A reset cycle is active",
    "full_moon": "Full Moon — Clarity and illumination peaking",
    "waning_crescent": "Waning Crescent — Completion and release phase",
    "waxing_crescent": "Waxing Crescent — New intentions beginning to form",
    "first_quarter": "First Quarter Moon — Tension between old and new",
    "last_quarter": "Last Quarter Moon — Letting go of what's done",
    "eclipse_solar": "Solar Eclipse — Significant reset or turning point",
    "eclipse_lunar": "Lunar Eclipse — Deep emotional recalibration",
    "equinox": "Equinox — Balance point between seasons",
    "solstice": "Solstice — Peak or turning point in the yearly cycle",
    "saturn_sign_change": "Saturn Sign Change — Shifting long-term structures",
    "jupiter_sign_change": "Jupiter Sign Change — New growth direction emerging",
}


def _format_event_type_readable(event_type: str, theme: str = "") -> str:
    """Convert a raw event type key to a human-readable description."""
    if not event_type:
        return ""
    
    # Check direct mapping first
    readable = EVENT_TYPE_READABLE.get(event_type)
    if readable:
        return readable
    
    # Fallback: format the type string nicely
    formatted = event_type.replace("_", " ").title()
    if theme:
        return f"{formatted} — {theme}"
    return formatted


def generate_today_from_transit(
    transit_stack: Dict[str, Any],
    day_class: str = "normal_flow",
    chart_data: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Generate V3 Today insight from transit data.
    
    This is the main integration point with existing transit system.
    """
    # Get dominant tension from transit stack
    dominant_tension = transit_stack.get("dominant_tension", "")
    tension_type = map_to_v3_tension(dominant_tension)
    
    # Get activated house if available
    activated_house = transit_stack.get("activated_house")
    
    # Get sun sign from chart
    sun_sign = chart_data.get("sun_sign") if chart_data else None
    
    # Build transit info for technical layer (human-readable descriptions)
    events = transit_stack.get("events", [])
    transit_info = None
    if events:
        readable_parts = []
        for e in events:
            if isinstance(e, dict):
                event_type = e.get("type", "")
                headline = e.get("headline", "")
                theme = e.get("theme", "")
                # Use headline if available, otherwise map type to readable name
                if headline:
                    readable_parts.append(headline)
                else:
                    readable_name = _format_event_type_readable(event_type, theme)
                    if readable_name:
                        readable_parts.append(readable_name)
            else:
                readable_name = _format_event_type_readable(str(e), "")
                if readable_name:
                    readable_parts.append(readable_name)
        transit_info = " · ".join(readable_parts) if readable_parts else None
    
    return generate_today_v3(
        tension_type=tension_type,
        day_class=day_class,
        activated_house=activated_house,
        sun_sign=sun_sign,
        transit_info=transit_info,
    )


# =============================================================================
# NARRATIVE BUILDER - For Single-String Display
# =============================================================================

def build_narrative_v3(insight: Dict[str, Any]) -> str:
    """
    Build a single narrative string from V3 insight.
    
    For backwards compatibility with systems expecting a single narrative.
    """
    parts = []
    
    # Headline
    parts.append(insight["headline"])
    parts.append("")
    
    # What's happening
    parts.append("**What's actually happening:**")
    for item in insight["whats_happening"]:
        parts.append(f"• {item}")
    parts.append("")
    
    # How it shows up
    parts.append("**How this shows up for you:**")
    for item in insight["how_it_shows_up"]:
        parts.append(f"• {item}")
    parts.append("")
    
    # What it feels like
    parts.append("**What this may feel like:**")
    for item in insight["what_it_feels_like"]:
        parts.append(f"• {item}")
    parts.append("")
    
    # Where context if available
    if insight.get("where_context"):
        parts.append(f"_{insight['where_context']}_")
        parts.append("")
    
    # The move
    parts.append(f"**The move:** {insight['the_move']}")
    
    return "\n".join(parts)
