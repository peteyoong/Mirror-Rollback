"""Human Design Centers Interpretation Service

Provides reflective, template-based interpretations for the 9 Human Design centers.
Uses the same Mirror tone as Gene Keys - practical, warm, non-deterministic.

This service does NOT compute anything - it only provides interpretation.
The deterministic center computation is done in /calculations/human_design.py.
"""

from typing import List, Dict, Any, TypedDict


# =============================================================================
# GATE-TO-CENTER MAPPING
# =============================================================================
# Maps each of the 64 gates to their corresponding center

GATE_TO_CENTER = {
    # HEAD CENTER - Gates of inspiration and pressure to think
    64: "Head", 61: "Head", 63: "Head",
    
    # AJNA CENTER - Gates of mental processing and conceptualization
    47: "Ajna", 24: "Ajna", 4: "Ajna", 17: "Ajna", 43: "Ajna", 11: "Ajna",
    
    # THROAT CENTER - Gates of expression and manifestation
    62: "Throat", 23: "Throat", 56: "Throat", 35: "Throat", 12: "Throat",
    45: "Throat", 33: "Throat", 8: "Throat", 31: "Throat", 20: "Throat", 16: "Throat",
    
    # G CENTER (Identity) - Gates of identity, direction, and love
    7: "G Center", 1: "G Center", 13: "G Center", 25: "G Center", 46: "G Center",
    2: "G Center", 15: "G Center", 10: "G Center",
    
    # EGO / HEART CENTER - Gates of willpower and material resources
    21: "Ego", 51: "Ego", 26: "Ego", 40: "Ego",
    
    # SOLAR PLEXUS CENTER - Gates of emotional awareness
    36: "Solar Plexus", 22: "Solar Plexus", 37: "Solar Plexus", 6: "Solar Plexus",
    49: "Solar Plexus", 55: "Solar Plexus", 30: "Solar Plexus",
    
    # SACRAL CENTER - Gates of life force and work capacity
    5: "Sacral", 14: "Sacral", 29: "Sacral", 59: "Sacral", 9: "Sacral",
    3: "Sacral", 42: "Sacral", 27: "Sacral", 34: "Sacral",
    
    # SPLEEN CENTER - Gates of instinct and survival awareness
    48: "Spleen", 57: "Spleen", 44: "Spleen", 50: "Spleen", 32: "Spleen", 28: "Spleen", 18: "Spleen",
    
    # ROOT CENTER - Gates of pressure and adrenaline
    58: "Root", 38: "Root", 54: "Root", 53: "Root", 60: "Root", 52: "Root",
    19: "Root", 39: "Root", 41: "Root",
}

# Center display names for UI
CENTER_DISPLAY_NAMES = {
    "Head": "Head",
    "Ajna": "Ajna (Mind)",
    "Throat": "Throat",
    "G Center": "G / Identity",
    "Ego": "Heart / Ego",
    "Solar Plexus": "Solar Plexus",
    "Sacral": "Sacral",
    "Spleen": "Spleen",
    "Root": "Root"
}

# Center themes - plain language description
CENTER_THEMES = {
    "Head": ["inspiration", "mental pressure", "questions"],
    "Ajna": ["thinking patterns", "conceptualization", "opinions"],
    "Throat": ["expression", "communication", "action"],
    "G Center": ["identity", "direction", "sense of self"],
    "Ego": ["willpower", "commitment", "material resources"],
    "Solar Plexus": ["emotions", "feelings", "emotional waves"],
    "Sacral": ["life force", "work energy", "vitality"],
    "Spleen": ["instinct", "intuition", "survival awareness"],
    "Root": ["pressure", "drive", "adrenaline"]
}


class CenterInterpretation(TypedDict):
    """Full interpretation for a single center - Mirror Content System V1."""
    center_name: str
    display_name: str
    defined: bool
    gates_present: List[int]
    themes: List[str]
    # Mirror Content System V1 fields
    recognition: str
    what_this_is: str
    when_it_trips_you_up: str
    when_it_works: str
    at_your_highest: str
    where_youll_notice_today: List[str]
    try_this: List[str]
    why_this_is_happening: str
    system_label: str


# =============================================================================
# TEMPLATE-BASED INTERPRETATIONS (Real-Life Language)
# =============================================================================
# Structure:
# 1. WHAT YOU TEND TO DO - "You tend to...", "You often..."
# 2. HOW THIS SHOWS UP TODAY - 2-3 real behaviors
# 3. WHAT TO WATCH - 1 clear risk
# 4. WHAT TO DO - 1 concrete action
# 5. SYSTEM LABEL - "(Ajna · defined)" - optional, last line

DEFINED_TEMPLATES = {
    "Head": {
        "what_you_tend_to_do": "You tend to get caught by questions that won't let go. Ideas arrive uninvited and stay until you've turned them over. When something sparks your curiosity, you can't easily set it down.",
        "how_this_shows_up_today": [
            "A question or idea keeps circling back even when you're busy with other things",
            "You find yourself researching or thinking about something you didn't plan to",
            "You feel a subtle pressure to figure something out before moving on"
        ],
        "what_to_watch": "Watch for chasing every interesting question as if they're all urgent. Not every thought needs to become a project.",
        "what_to_do": "Try this: Write the question down. If it's still important in 3 days, it's worth pursuing.",
        "system_label": "Head center · defined"
    },
    "Ajna": {
        "what_you_tend_to_do": "You tend to lock into a way of seeing things—and once something makes sense to you, you stick with it. Changing your mind takes real evidence, not just pressure from others.",
        "how_this_shows_up_today": [
            "You hold a clear opinion and find yourself defending it, even internally",
            "You process new information through your existing framework first",
            "You may feel certain about something before others are ready to commit"
        ],
        "what_to_watch": "Watch for rigidity. Confidence can become stubbornness when you stop considering new information.",
        "what_to_do": "Try this: When someone disagrees, ask 'What would it take for me to change my mind?' before responding.",
        "system_label": "Ajna · defined"
    },
    "Throat": {
        "what_you_tend_to_do": "You tend to speak or act in recognizable patterns. Your voice has a consistent style. When something needs to be said, it often comes out—sometimes before you've planned it.",
        "how_this_shows_up_today": [
            "You find yourself naturally taking the lead in conversations",
            "Others may wait for you to speak or act first",
            "You feel a pull to fill silence or move things forward"
        ],
        "what_to_watch": "Watch for speaking just to be heard. Not every silence needs filling, and not every moment needs your voice.",
        "what_to_do": "Try this: Before speaking in a meeting or conversation, count to three. Notice if the moment actually needs you.",
        "system_label": "Throat · defined"
    },
    "G Center": {
        "what_you_tend_to_do": "You tend to have a steady sense of who you are and where you're going. Even when life is uncertain, something in you holds direction. Others may look to you for steadiness.",
        "how_this_shows_up_today": [
            "You know what you want, even if you can't explain why",
            "People may ask for your guidance or follow your lead without you asking",
            "You feel pulled toward certain places, people, or paths"
        ],
        "what_to_watch": "Watch for staying on a path just because it's familiar. Steadiness can become stubbornness about direction.",
        "what_to_do": "Try this: Ask yourself 'Is this direction still true for me, or am I just used to it?'",
        "system_label": "G center · defined"
    },
    "Ego": {
        "what_you_tend_to_do": "You tend to push through when you've committed to something. Willpower is available when you decide to use it. When you say you'll do something, you usually can.",
        "how_this_shows_up_today": [
            "You feel capable of making promises and keeping them",
            "You may push through resistance when something matters to you",
            "You have opinions about what's valuable and what's worth effort"
        ],
        "what_to_watch": "Watch for proving yourself when you don't need to. Willpower is available, but not every situation requires it.",
        "what_to_do": "Try this: Before committing to something hard, ask 'Does this actually need my effort, or am I just proving I can?'",
        "system_label": "Heart/Ego · defined"
    },
    "Solar Plexus": {
        "what_you_tend_to_do": "You tend to feel things in waves. Your emotional state rises and falls—sometimes dramatically, sometimes subtly. Clarity about decisions comes after time, not in the first moment.",
        "how_this_shows_up_today": [
            "Your mood may shift without clear external cause",
            "You might feel very certain in one moment, then less certain hours later",
            "Big decisions feel better when you've slept on them"
        ],
        "what_to_watch": "Watch for making commitments at emotional peaks or lows. The wave will pass, and your perspective will shift.",
        "what_to_do": "Try this: For any decision that matters, wait at least one full day. Notice if your feeling about it changes.",
        "system_label": "Solar Plexus · defined"
    },
    "Sacral": {
        "what_you_tend_to_do": "You tend to have consistent energy for work that engages you. When something is right, you can go and go. When it's wrong, even simple tasks feel draining.",
        "how_this_shows_up_today": [
            "You feel energy rising when you think about certain tasks—and dropping for others",
            "Your gut responds quickly to requests: a subtle 'yes' or 'no' before you think",
            "You may keep working long after others would stop, if you're engaged"
        ],
        "what_to_watch": "Watch for overriding your gut response with logic. That 'ugh' feeling is data, not laziness.",
        "what_to_do": "Try this: When asked to do something, notice your body's first response before your mind forms an opinion.",
        "system_label": "Sacral · defined"
    },
    "Spleen": {
        "what_you_tend_to_do": "You tend to get quiet, instant signals about what's safe or healthy. A knowing arrives in the moment and doesn't repeat. It's subtle—easy to miss if you're not listening.",
        "how_this_shows_up_today": [
            "You may get a 'hit' about something—a sense of yes or no—that you can't explain",
            "Your body reacts to environments or people before your mind catches up",
            "You might know something is 'off' without being able to say why"
        ],
        "what_to_watch": "Watch for overriding these signals with logic or politeness. The first hit is often more accurate than the second thought.",
        "what_to_do": "Try this: When you get a quiet 'no,' honor it—even before you have a reason.",
        "system_label": "Spleen · defined"
    },
    "Root": {
        "what_you_tend_to_do": "You tend to handle pressure without being destabilized. Stress arrives, but it doesn't overwhelm you. You may even work better under deadline or urgency.",
        "how_this_shows_up_today": [
            "You feel steady even when there's a lot happening",
            "You may create pressure or deadlines to get yourself moving",
            "Others might notice that stress doesn't seem to affect you as much"
        ],
        "what_to_watch": "Watch for creating unnecessary urgency. Not everything needs to be a deadline to get done.",
        "what_to_do": "Try this: Try finishing something without a deadline. Notice if you can stay motivated without the pressure.",
        "system_label": "Root · defined"
    }
}

UNDEFINED_TEMPLATES = {
    "Head": {
        "what_you_tend_to_do": "You tend to take in other people's mental pressure—their questions become yours, even when they're not. Ideas arrive from outside you, and sometimes you mistake them for your own thoughts.",
        "how_this_shows_up_today": [
            "You may find yourself thinking intensely about something that doesn't actually concern you",
            "Your mental activity changes depending on who you're around",
            "You might feel pressure to answer questions that aren't really yours to solve"
        ],
        "what_to_watch": "Watch for chasing ideas that disappear when you're alone. If it doesn't stay with you, it probably wasn't yours.",
        "what_to_do": "Try this: When inspired by an idea, wait until you're alone. If it's still alive, it might be yours.",
        "system_label": "Head center · open"
    },
    "Ajna": {
        "what_you_tend_to_do": "You tend to think differently depending on who you're around. Your mind is flexible—you can see multiple perspectives, but you may struggle to land on one view.",
        "how_this_shows_up_today": [
            "Your opinions might shift based on who you're talking to",
            "You can argue either side of a debate convincingly",
            "You may feel uncertain about what you 'really' think about something"
        ],
        "what_to_watch": "Watch for pretending to have certainty you don't have. It's okay to not have a fixed opinion.",
        "what_to_do": "Try this: Say 'I see it differently depending on context' and notice if that feels more honest.",
        "system_label": "Ajna · open"
    },
    "Throat": {
        "what_you_tend_to_do": "You tend to communicate differently depending on the situation. Your voice adapts. Sometimes you speak up easily; other times, words don't come.",
        "how_this_shows_up_today": [
            "You may find it easier to speak in some settings than others",
            "You might feel pressure to fill silence, or alternately, go very quiet",
            "Your communication style shifts based on who you're with"
        ],
        "what_to_watch": "Watch for forcing yourself to speak when you don't have anything to say. Silence is allowed.",
        "what_to_do": "Try this: Wait to be asked before offering your perspective. Notice if the timing feels better.",
        "system_label": "Throat · open"
    },
    "G Center": {
        "what_you_tend_to_do": "You tend to feel different in different places and with different people. Your sense of direction and identity shifts. This isn't instability—it's openness.",
        "how_this_shows_up_today": [
            "You may not be sure 'who you are' or where you're headed",
            "Certain places or people make you feel more like yourself",
            "You might feel lost, then suddenly clear, depending on context"
        ],
        "what_to_watch": "Watch for attaching to someone else's direction as if it's your own. Environment matters more for you than for most.",
        "what_to_do": "Try this: Notice which places make you feel most yourself. Go there when you need clarity.",
        "system_label": "G center · open"
    },
    "Ego": {
        "what_you_tend_to_do": "You tend to have variable willpower—sometimes you can push through, other times you can't. This isn't weakness; it's a different relationship with effort.",
        "how_this_shows_up_today": [
            "You may feel capable of effort in some moments and depleted in others",
            "You might over-promise to prove your worth, then struggle to follow through",
            "You may compare yourself to people who seem to push harder"
        ],
        "what_to_watch": "Watch for proving yourself when no proof is required. Your worth isn't measured by willpower.",
        "what_to_do": "Try this: Before committing, ask 'Am I saying yes because I genuinely can, or because I want to prove something?'",
        "system_label": "Heart/Ego · open"
    },
    "Solar Plexus": {
        "what_you_tend_to_do": "You tend to absorb emotions from others—feeling what they feel, sometimes more intensely than they do. Your own baseline is more neutral.",
        "how_this_shows_up_today": [
            "You may pick up tension in a room before others notice it",
            "Your mood might shift based on who you're around",
            "Conflict nearby can feel like your own conflict"
        ],
        "what_to_watch": "Watch for mistaking someone else's emotion for your own. If it arrived suddenly, ask who brought it.",
        "what_to_do": "Try this: After leaving an emotional situation, check in: is this feeling still with me, or was it theirs?",
        "system_label": "Solar Plexus · open"
    },
    "Sacral": {
        "what_you_tend_to_do": "You tend to have inconsistent work energy. Some days you can go and go; other days you're depleted. Learning when to stop matters more for you.",
        "how_this_shows_up_today": [
            "Your energy for work may not match what's expected of you",
            "You might borrow energy from others and not realize you're running on fumes",
            "You may need to rest before you feel tired"
        ],
        "what_to_watch": "Watch for pushing through exhaustion because you technically can. Just because you can keep going doesn't mean you should.",
        "what_to_do": "Try this: Stop working before you're exhausted. Build in rest before you need it.",
        "system_label": "Sacral · open"
    },
    "Spleen": {
        "what_you_tend_to_do": "You tend to hold onto things longer than you should—jobs, relationships, habits. Letting go feels risky because security isn't consistent for you.",
        "how_this_shows_up_today": [
            "You might stay in something past its expiration because change feels unsafe",
            "Fear may feel more amplified for you than for others",
            "You could ignore health signals or dismiss intuitive hits"
        ],
        "what_to_watch": "Watch for holding on just because letting go feels scary. The grip isn't keeping you safe—it's keeping you stuck.",
        "what_to_do": "Try this: Name one thing you're holding onto that might be ready to release. See how it feels to consider letting it go.",
        "system_label": "Spleen · open"
    },
    "Root": {
        "what_you_tend_to_do": "You tend to absorb pressure from outside—other people's urgency becomes yours. You may rush to finish things just to get them off your plate.",
        "how_this_shows_up_today": [
            "You may feel stressed by other people's deadlines",
            "Calm environments feel like relief; busy environments feel overwhelming",
            "You might rush even when there's no actual rush"
        ],
        "what_to_watch": "Watch for manufacturing urgency that isn't real. Not everything needs to be done now.",
        "what_to_do": "Try this: When you feel pressure to rush, pause and ask: 'Is this deadline real, or am I absorbing someone else's stress?'",
        "system_label": "Root · open"
    }
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_gates_for_center(center_name: str, active_gates: List[int]) -> List[int]:
    """Get which gates from active_gates belong to a specific center."""
    return [gate for gate in active_gates if GATE_TO_CENTER.get(gate) == center_name]


def get_center_interpretation(
    center_name: str,
    defined: bool,
    active_gates: List[int]
) -> Dict[str, Any]:
    """Generate interpretation for a single center using Mirror Content System V1.
    
    Structure:
    - Recognition (top, always visible)
    - WHAT THIS IS (2-3 lines)
    - WHEN IT TRIPS YOU UP (2-3 lines)
    - WHEN IT WORKS (2-3 lines)
    - AT YOUR HIGHEST (1-2 lines)
    - WHERE YOU'LL NOTICE THIS TODAY (3 bullets)
    - TRY THIS (3 bullets)
    - WHY THIS IS HAPPENING (collapsible)
    - System label (bottom, metadata)
    
    Args:
        center_name: Internal center name (e.g., "G Center")
        defined: Whether the center is defined
        active_gates: List of all user's active gates
    
    Returns:
        Dict with Mirror Content System structure
    """
    from services.mirror_content_system import get_hd_center_content
    
    # Get gates present in this center
    gates_present = get_gates_for_center(center_name, active_gates)
    
    # Get display name and themes
    display_name = CENTER_DISPLAY_NAMES.get(center_name, center_name)
    themes = CENTER_THEMES.get(center_name, [])
    
    # Get Mirror Content System content
    mirror_content = get_hd_center_content(center_name, defined)
    
    # Build system label with gates
    gate_str = f" · Gates {', '.join(str(g) for g in gates_present)}" if gates_present else ""
    system_label = f"{mirror_content['system_label']}{gate_str}"
    
    return {
        "center_name": center_name,
        "display_name": display_name,
        "defined": defined,
        "gates_present": gates_present,
        "themes": themes,
        
        # MIRROR CONTENT SYSTEM V1 STRUCTURE
        "recognition": mirror_content["recognition"],
        "what_this_is": mirror_content["what_this_is"],
        "when_it_trips_you_up": mirror_content["when_it_trips_you_up"],
        "when_it_works": mirror_content["when_it_works"],
        "at_your_highest": mirror_content["at_your_highest"],
        "where_youll_notice_today": mirror_content["where_youll_notice_today"],
        "try_this": mirror_content["try_this"],
        "why_this_is_happening": mirror_content["why_this_is_happening"],
        "system_label": system_label,
    }


def build_centers_profile(
    defined_centers: List[str],
    undefined_centers: List[str],
    active_gates: List[int]
) -> List[CenterInterpretation]:
    """Build complete centers profile with interpretations for all 9 centers.
    
    Args:
        defined_centers: List of defined center names from HD computation
        undefined_centers: List of undefined center names from HD computation
        active_gates: List of all active gates from HD computation
    
    Returns:
        List of CenterInterpretation for all 9 centers in standard order
    """
    # Standard center order for display
    center_order = [
        "Head", "Ajna", "Throat", "G Center", "Ego",
        "Solar Plexus", "Sacral", "Spleen", "Root"
    ]
    
    defined_set = set(defined_centers)
    
    centers = []
    for center_name in center_order:
        is_defined = center_name in defined_set
        interpretation = get_center_interpretation(
            center_name=center_name,
            defined=is_defined,
            active_gates=active_gates
        )
        centers.append(interpretation)
    
    return centers
