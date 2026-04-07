"""
BaZi Insight Layer - "Insight First + Proof Expand" Architecture

Transforms BaZi technical output into recognition-first insights.
System proof is still available but hidden behind collapsible sections.

Structure:
1. CORE TRUTH (always visible, no BaZi language)
2. HOW THIS SHOWS UP (real-life behaviors)
3. WHEN THIS BACKFIRES (sharper, specific)
4. WHAT THIS COSTS YOU (energy, relationships, opportunities)
5. ONE SHIFT (doable today)
6. WHY THIS IS SHOWING UP (collapsible - light explanation)
7. SEE YOUR CHART DETAILS (collapsible - raw BaZi data)
"""

from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# CORE TRUTH - Recognition-first, no system language
# =============================================================================

CORE_TRUTH_TEMPLATES = {
    ("Wood", "Yang"): {
        "line1": "You don't wait for permission — you move first.",
        "line2": "And you notice when others hesitate.",
    },
    ("Wood", "Yin"): {
        "line1": "You grow around obstacles that stop others cold.",
        "line2": "Persistence is your superpower, not force.",
    },
    ("Fire", "Yang"): {
        "line1": "You light up rooms without trying.",
        "line2": "And you notice when others dim.",
    },
    ("Fire", "Yin"): {
        "line1": "You're the candle that stays lit when the bonfire burns out.",
        "line2": "Steady warmth, not dramatic heat.",
    },
    ("Earth", "Yang"): {
        "line1": "You're the mountain people lean on when everything shakes.",
        "line2": "Solid when others crumble.",
    },
    ("Earth", "Yin"): {
        "line1": "You grow what you touch — sometimes at the cost of yourself.",
        "line2": "Others flourish in your presence.",
    },
    ("Metal", "Yang"): {
        "line1": "You cut through confusion that paralyzes others.",
        "line2": "Sometimes too quickly.",
    },
    ("Metal", "Yin"): {
        "line1": "You don't move fast — you move right.",
        "line2": "And you notice when others don't.",
    },
    ("Water", "Yang"): {
        "line1": "You flow around obstacles that stop others.",
        "line2": "Sometimes you can't stop yourself.",
    },
    ("Water", "Yin"): {
        "line1": "You understand things before you can explain them.",
        "line2": "And sometimes before you should.",
    },
}


# =============================================================================
# HOW THIS SHOWS UP - Real-life behaviors (SHARPENED)
# =============================================================================

HOW_THIS_SHOWS_UP_TEMPLATES = {
    ("Wood", "Yang"): [
        "You start before others finish thinking",
        "You've moved on before this thing lands",
        "You push through walls others walk around",
        "You say 'let's go' while others are still deciding",
        "Slow feels like stuck to you",
    ],
    ("Wood", "Yin"): [
        "You find ways around when the door closes",
        "You outlast people who started louder",
        "You adapt instead of fight",
        "You grow sideways when up isn't available",
        "You bend without breaking — mostly",
    ],
    ("Fire", "Yang"): [
        "You lead without meaning to",
        "You fill the room before you speak",
        "People watch you even when you're not performing",
        "You start things others only talk about",
        "Your presence is felt before your words land",
    ],
    ("Fire", "Yin"): [
        "You're still warm when everyone else burns out",
        "You support without being asked",
        "You stay connected even through silence",
        "You nurture through presence, not performance",
        "You're the one people forget to thank",
    ],
    ("Earth", "Yang"): [
        "People come to you when nothing else is stable",
        "You hold what others drop",
        "You stay solid when everything shakes",
        "You carry more than anyone knows",
        "You're the floor they don't notice until it's gone",
    ],
    ("Earth", "Yin"): [
        "Things grow around you",
        "You give before you're asked",
        "You absorb more than you track",
        "Others flourish — sometimes at your expense",
        "You make hard ground fertile",
    ],
    ("Metal", "Yang"): [
        "You see what matters — fast",
        "You decide while others debate",
        "You name standards others avoid",
        "You cut through noise to the point",
        "You end conversations that need ending",
    ],
    ("Metal", "Yin"): [
        "You notice what others miss",
        "You want less, but better",
        "You refine everything you touch",
        "Your standards are higher than anyone else's",
        "You catch problems before they land",
    ],
    ("Water", "Yang"): [
        "You move when others freeze",
        "You find paths through chaos",
        "Uncertainty doesn't slow you down",
        "You adapt before you realize you're adapting",
        "You keep going when others stop to think",
    ],
    ("Water", "Yin"): [
        "You know things before you can explain them",
        "You sense what's underneath the surface",
        "Stillness shows you what movement hides",
        "You understand people before they speak",
        "You feel shifts before they happen",
    ],
}


# =============================================================================
# WHEN THIS BACKFIRES - Sharp, specific (SHARPENED - "shit, that's me")
# =============================================================================

WHEN_THIS_BACKFIRES_TEMPLATES = {
    ("Wood", "Yang"): [
        "You bulldoze through things that needed finesse",
        "You start the next thing before finishing this one",
        "You dismiss good input because it feels like delay",
        "You push harder when pulling back would actually work",
    ],
    ("Wood", "Yin"): [
        "You bend so much you forget where you were going",
        "You adapt to everyone's needs — except your own",
        "Your flexibility starts looking like indecision",
        "You avoid conflict by never actually taking a side",
    ],
    ("Fire", "Yang"): [
        "You burn hot and fast — then there's nothing left",
        "You chase visibility even when it costs you",
        "You go dramatic when quiet would serve you better",
        "You exhaust yourself keeping the energy up",
    ],
    ("Fire", "Yin"): [
        "You dim yourself so others feel comfortable",
        "You flicker when you run out of fuel",
        "You disappear exactly when you need to be seen",
        "You keep giving warmth when you have none left",
    ],
    ("Earth", "Yang"): [
        "You won't move — even when movement is exactly what's needed",
        "You carry so much you can't actually go anywhere",
        "Your stability becomes stubbornness",
        "You hold onto things that needed to be released",
    ],
    ("Earth", "Yin"): [
        "You give until you're empty",
        "You lose yourself inside other people's needs",
        "You absorb problems that were never yours",
        "You nurture everyone else while you starve",
    ],
    ("Metal", "Yang"): [
        "You cut things that needed more time to grow",
        "You get harsh when precision isn't wanted",
        "Your clarity becomes coldness",
        "You end up right — and alone",
    ],
    ("Metal", "Yin"): [
        "You criticize yourself first, then everyone else",
        "Your precision freezes you into perfectionism",
        "You notice every flaw — including ones that don't matter",
        "You refine past the point where it helps",
    ],
    ("Water", "Yang"): [
        "You don't stop — even when stopping is the answer",
        "You're always moving, but nothing actually lands",
        "You move past things that actually needed your attention",
        "You keep moving to avoid actually facing it",
    ],
    ("Water", "Yin"): [
        "You withdraw so deep no one can reach you",
        "You get lost in reflection without acting on it",
        "You understand — but never share what you know",
        "You sense everything and process none of it",
    ],
}


# =============================================================================
# GENIUS - Pure identity recognition (NOT explanation)
# =============================================================================

GENIUS_TEMPLATES = {
    ("Wood", "Yang"): {
        "line1": "You get things moving when everyone else is still deciding.",
        "line2": "Momentum follows you. It always has.",
    },
    ("Wood", "Yin"): {
        "line1": "You survive things that break other people.",
        "line2": "You find a way through. Always have.",
    },
    ("Fire", "Yang"): {
        "line1": "People follow you without being asked.",
        "line2": "You walk into a room and something shifts.",
    },
    ("Fire", "Yin"): {
        "line1": "People trust you when everything else feels uncertain.",
        "line2": "You stay warm when everyone else burns out or goes cold.",
    },
    ("Earth", "Yang"): {
        "line1": "People come to you when nothing else is stable.",
        "line2": "You hold ground that others can't.",
    },
    ("Earth", "Yin"): {
        "line1": "Things grow around you.",
        "line2": "People flourish in your presence — and that's rare.",
    },
    ("Metal", "Yang"): {
        "line1": "You cut through confusion that paralyzes other people.",
        "line2": "You see what matters. And you name it.",
    },
    ("Metal", "Yin"): {
        "line1": "Things get better when you touch them.",
        "line2": "You notice what others miss. You refine what others accept.",
    },
    ("Water", "Yang"): {
        "line1": "You move through uncertainty faster than most people.",
        "line2": "You don't freeze. You figure it out while others are still stuck.",
    },
    ("Water", "Yin"): {
        "line1": "You understand people before they explain themselves.",
        "line2": "You sense what's underneath — and you're usually right.",
    },
}


# =============================================================================
# WHAT THIS COSTS YOU - Energy, Relationships, Opportunities (SHARPENED)
# =============================================================================

WHAT_THIS_COSTS_TEMPLATES = {
    ("Wood", "Yang"): {
        "energy": "You start over constantly instead of building on what's there",
        "relationships": "People stop offering input — you'll move anyway",
        "opportunities": "The refinements that would've made it great",
    },
    ("Wood", "Yin"): {
        "energy": "You process everyone's direction before choosing your own",
        "relationships": "No one knows what you actually want",
        "opportunities": "Paths you never took because you adapted instead",
    },
    ("Fire", "Yang"): {
        "energy": "You burn out before the finish line",
        "relationships": "People see you but don't actually know you",
        "opportunities": "Projects abandoned when the spotlight moved",
    },
    ("Fire", "Yin"): {
        "energy": "You keep giving warmth when you're running on empty",
        "relationships": "People rely on you — but don't support you back",
        "opportunities": "Moments when you needed to be seen and weren't",
    },
    ("Earth", "Yang"): {
        "energy": "You carry weight that was never yours to lift",
        "relationships": "People lean on you — but don't meet you",
        "opportunities": "Stuck positions that missed the right moment",
    },
    ("Earth", "Yin"): {
        "energy": "You give until there's nothing left for yourself",
        "relationships": "People know what you give, not who you are",
        "opportunities": "Your own growth — delayed by tending everyone else",
    },
    ("Metal", "Yang"): {
        "energy": "Battles you fought that didn't need winning",
        "relationships": "Being right — and being alone",
        "opportunities": "Options you cut that had more to offer",
    },
    ("Metal", "Yin"): {
        "energy": "You perfect past the point where it matters",
        "relationships": "People feel judged before they even start",
        "opportunities": "Good enough shipped. Perfect never did.",
    },
    ("Water", "Yang"): {
        "energy": "You're always moving — but nothing actually lands",
        "relationships": "People can't count on you when it matters",
        "opportunities": "Moments that needed your presence, not your motion",
    },
    ("Water", "Yin"): {
        "energy": "You go so deep nothing ever surfaces",
        "relationships": "You understood everyone — no one understood you",
        "opportunities": "Insights that stayed insights",
    },
}


# =============================================================================
# ONE SHIFT - Doable today
# =============================================================================

ONE_SHIFT_TEMPLATES = {
    ("Wood", "Yang"): "Before you move on the next thing, ask one person for input — and wait for their full answer.",
    ("Wood", "Yin"): "Name one thing you want today — out loud — without adapting it to what others might prefer.",
    ("Fire", "Yang"): "Do one thing today without an audience. Notice how it feels.",
    ("Fire", "Yin"): "Let yourself be seen for something you did today, even briefly.",
    ("Earth", "Yang"): "Put one thing down today that you've been carrying. Actually let it go.",
    ("Earth", "Yin"): "Receive something today without immediately giving back.",
    ("Metal", "Yang"): "Let one thing be less than perfect today. Don't mention it.",
    ("Metal", "Yin"): "Ship one thing at 80%. Notice what happens.",
    ("Water", "Yang"): "Stay in one place 10% longer than feels comfortable. See what arrives.",
    ("Water", "Yin"): "Surface one thing you know but haven't said. Say it to someone.",
}


# =============================================================================
# WHY THIS IS SHOWING UP - Light BaZi explanation (collapsible)
# =============================================================================

WHY_SHOWING_UP_TEMPLATES = {
    ("Wood", "Yang"): {
        "explanation": "Your chart shows strong forward momentum — what classical systems call Yang Wood or Jia. You naturally initiate and push through.",
        "pattern_note": "This creates drive that others rely on, but also impatience with anything that feels like delay.",
    },
    ("Wood", "Yin"): {
        "explanation": "Your chart shows adaptive persistence — what classical systems call Yin Wood or Yi. You grow around obstacles rather than through them.",
        "pattern_note": "This creates flexibility that serves you, but can also mean losing your center while adapting to others.",
    },
    ("Fire", "Yang"): {
        "explanation": "Your chart shows radiant presence — what classical systems call Yang Fire or Bing. You naturally illuminate and attract.",
        "pattern_note": "This creates visibility and inspiration, but also potential for burnout or attention-seeking.",
    },
    ("Fire", "Yin"): {
        "explanation": "Your chart shows steady warmth — what classical systems call Yin Fire or Ding. You sustain rather than blaze.",
        "pattern_note": "This creates reliable support for others, but can mean dimming yourself to make others comfortable.",
    },
    ("Earth", "Yang"): {
        "explanation": "Your chart shows grounded stability — what classical systems call Yang Earth or Wu. You provide solid ground for others.",
        "pattern_note": "This creates reliability others depend on, but also risk of becoming immovable or overburdened.",
    },
    ("Earth", "Yin"): {
        "explanation": "Your chart shows nurturing presence — what classical systems call Yin Earth or Ji. You cultivate growth in what you touch.",
        "pattern_note": "This creates flourishing in others, but can mean giving at the expense of your own needs.",
    },
    ("Metal", "Yang"): {
        "explanation": "Your chart shows decisive clarity — what classical systems call Yang Metal or Geng. You cut through confusion naturally.",
        "pattern_note": "This creates clear direction, but also risk of cutting too quickly or becoming harsh.",
    },
    ("Metal", "Yin"): {
        "explanation": "Your chart shows refined precision — what classical systems call Yin Metal or Xin. You notice and perfect what others miss.",
        "pattern_note": "This creates quality consciousness, but also risk of perfectionism that freezes action.",
    },
    ("Water", "Yang"): {
        "explanation": "Your chart shows flowing adaptability — what classical systems call Yang Water or Ren. You navigate around obstacles naturally.",
        "pattern_note": "This creates ease with uncertainty, but also risk of never stopping or always moving past.",
    },
    ("Water", "Yin"): {
        "explanation": "Your chart shows deep perception — what classical systems call Yin Water or Gui. You sense undercurrents others miss.",
        "pattern_note": "This creates intuitive knowing, but also risk of withdrawing too deep to be reached.",
    },
}


# =============================================================================
# TODAY INSIGHT - Transformed timing content
# =============================================================================

def generate_today_insight(
    today_element: str,
    dm_element: str,
    dm_polarity: str,
    interaction: str,
    ten_god: str
) -> Dict[str, str]:
    """
    Generate today's insight in recognition-first language.
    No element names in the main insight.
    """
    
    # Interaction-based headlines
    if interaction == "supporting":
        headlines = {
            "resource": "Today rewards learning and receiving.",
            "output": "Today rewards expression — if it's grounded.",
            "companion": "Today rewards collaboration over solo work.",
            "wealth": "Today rewards practical action.",
            "default": "Today flows with you, not against you.",
        }
        main_insight = headlines.get(ten_god.lower(), headlines["default"])
        
        behavioral = "You'll feel a pull to move something forward. This works if you anchor it in something real. If not, it becomes noise."
        pressure_note = None
        
    elif interaction == "pressure":
        headlines = {
            "officer": "Today holds you to a higher standard.",
            "seven_killings": "Today tests what you're made of.",
            "controls": "Today pushes back on your natural flow.",
            "default": "Today brings friction worth noticing.",
        }
        main_insight = headlines.get(ten_god.lower(), headlines["default"])
        
        behavioral = "You may feel observed, held accountable, or asked to justify what usually flows easily. This isn't personal — it's clarifying."
        pressure_note = "Don't force outcomes today. Let pressure reveal what's actually solid."
        
    else:  # mixed
        main_insight = "Today brings both support and friction."
        behavioral = "Some things will click into place. Others will push back. Stay flexible with which is which."
        pressure_note = None
    
    return {
        "headline": main_insight,
        "behavioral": behavioral,
        "pressure_note": pressure_note,
    }


# =============================================================================
# MAIN TRANSFORMATION FUNCTION
# =============================================================================

def transform_bazi_to_insight_first(
    day_master_element: str,
    day_master_polarity: str,
    day_master_strength: str,
    life_pattern: Dict[str, Any],
    ten_gods_detailed: List[Dict],
    timing: Optional[Dict] = None,
    pillars: Optional[Dict] = None,
    favorable_elements: Optional[List[str]] = None,
    unfavorable_elements: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Transform full BaZi output into Insight First + Proof Expand structure.
    
    Returns:
    {
        "core_truth": {"line1": str, "line2": str},
        "how_this_shows_up": [str],
        "when_this_backfires": [str],
        "what_this_costs_you": {energy, relationships, opportunities},
        "one_shift": str,
        "why_showing_up": {explanation, pattern_note},
        "chart_details": {day_master, strength, pillars, ...},
        "today_insight": {...} (if timing provided)
    }
    """
    key = (day_master_element, day_master_polarity)
    
    # Core truth (always visible)
    core_truth = CORE_TRUTH_TEMPLATES.get(key, {
        "line1": "You have a distinct way of moving through the world.",
        "line2": "This lens shows what that looks like.",
    })
    
    # How this shows up (real behaviors)
    how_shows_up = HOW_THIS_SHOWS_UP_TEMPLATES.get(key, [
        "You have consistent patterns that others recognize",
        "Your default mode shows up in how you handle pressure",
    ])[:5]  # Limit to 5
    
    # When this backfires (sharper)
    when_backfires = WHEN_THIS_BACKFIRES_TEMPLATES.get(key, [
        "Your strengths become weaknesses when overused",
        "Under pressure, your pattern intensifies",
    ])[:4]  # Limit to 4
    
    # Genius - the strength inside the pattern (NOT affirmation)
    genius = GENIUS_TEMPLATES.get(key, {
        "line1": "This same pattern is also why you can do things others can't.",
        "line2": "The strength is already there — you just don't always see it.",
    })
    
    # What this costs you
    costs = WHAT_THIS_COSTS_TEMPLATES.get(key, {
        "energy": "Running your pattern without checking if it's serving you",
        "relationships": "Others can't meet you where you are",
        "opportunities": "Missed because the pattern ran on autopilot",
    })
    
    # One shift
    one_shift = ONE_SHIFT_TEMPLATES.get(key, "Notice your pattern running today. Pause before repeating it.")
    
    # Why this is showing up (collapsible)
    why_showing = WHY_SHOWING_UP_TEMPLATES.get(key, {
        "explanation": "Your chart shows a distinct energetic signature that shapes how you move through life.",
        "pattern_note": "This creates tendencies worth noticing — both gifts and blind spots.",
    })
    
    # Chart details (collapsible - raw BaZi)
    chart_details = {
        "day_master": f"{day_master_polarity} {day_master_element}",
        "day_master_chinese": _get_chinese_name(day_master_element, day_master_polarity),
        "strength": day_master_strength,
        "favorable_elements": favorable_elements or [],
        "unfavorable_elements": unfavorable_elements or [],
    }
    
    # Add pillars if provided
    if pillars:
        chart_details["pillars"] = {
            "year": f"{pillars.get('year', {}).get('stem_pinyin', '')} {pillars.get('year', {}).get('branch_pinyin', '')}",
            "month": f"{pillars.get('month', {}).get('stem_pinyin', '')} {pillars.get('month', {}).get('branch_pinyin', '')}",
            "day": f"{pillars.get('day', {}).get('stem_pinyin', '')} {pillars.get('day', {}).get('branch_pinyin', '')}",
            "hour": f"{pillars.get('hour', {}).get('stem_pinyin', '')} {pillars.get('hour', {}).get('branch_pinyin', '')}",
        }
    
    # Add dominant ten gods if available
    if ten_gods_detailed:
        chart_details["dominant_patterns"] = [
            god.get("label", god.get("name", ""))
            for god in ten_gods_detailed[:3]
            if god.get("strength") in ["high", "moderate"]
        ]
    
    result = {
        "core_truth": core_truth,
        "how_this_shows_up": how_shows_up,
        "when_this_backfires": when_backfires,
        "genius": genius,
        "what_this_costs_you": costs,
        "one_shift": one_shift,
        "why_showing_up": why_showing,
        "chart_details": chart_details,
    }
    
    # Today insight (if timing provided)
    if timing and timing.get("today"):
        today = timing["today"]
        result["today_insight"] = generate_today_insight(
            today_element=today.get("element", day_master_element),
            dm_element=day_master_element,
            dm_polarity=day_master_polarity,
            interaction=today.get("interaction", "mixed"),
            ten_god=today.get("ten_god_name", ""),
        )
    
    return result


def _get_chinese_name(element: str, polarity: str) -> str:
    """Get the Chinese/Pinyin name for the Day Master."""
    names = {
        ("Wood", "Yang"): "Jia (甲)",
        ("Wood", "Yin"): "Yi (乙)",
        ("Fire", "Yang"): "Bing (丙)",
        ("Fire", "Yin"): "Ding (丁)",
        ("Earth", "Yang"): "Wu (戊)",
        ("Earth", "Yin"): "Ji (己)",
        ("Metal", "Yang"): "Geng (庚)",
        ("Metal", "Yin"): "Xin (辛)",
        ("Water", "Yang"): "Ren (壬)",
        ("Water", "Yin"): "Gui (癸)",
    }
    return names.get((element, polarity), f"{polarity} {element}")


# =============================================================================
# PILLAR INTERPRETATIONS - Your Chart, Read Simply
# =============================================================================

PILLAR_MEANINGS = {
    "year": {
        "domain": "Roots",
        "represents": "ancestry, early environment, social face",
    },
    "month": {
        "domain": "Work",
        "represents": "career, how others see you professionally, parents",
    },
    "day": {
        "domain": "Self",
        "represents": "core identity, marriage, adult self",
    },
    "hour": {
        "domain": "Inner World",
        "represents": "private self, children, later years, subconscious drives",
    },
}

# Animal-based behavioral tendency descriptions
ANIMAL_BEHAVIORS = {
    "Rat": "seeks advantage, moves in shadows, resourceful to a fault",
    "Ox": "slow to start, impossible to stop, stubborn beyond reason",
    "Tiger": "leads without permission, restless when caged",
    "Rabbit": "diplomatic surface, calculating underneath",
    "Dragon": "believes their own mythology, demands recognition",
    "Snake": "thinks ten moves ahead, trusts no one fully",
    "Horse": "can't stay still, abandons before being abandoned",
    "Goat": "needs belonging more than independence, gives too much",
    "Monkey": "clever enough to trick themselves, restless mind",
    "Rooster": "critical eye that misses nothing—including flaws",
    "Dog": "loyal to a fault, anxious about betrayal",
    "Pig": "generous to the point of naivety, comfort-seeking",
}

# Element dynamics in pillars
ELEMENT_IN_PILLAR = {
    ("Wood", "year"): "Your roots push toward growth, even if the soil isn't ready.",
    ("Wood", "month"): "You expand professionally whether invited or not.",
    ("Wood", "day"): "Your core self is always reaching, always building.",
    ("Wood", "hour"): "Privately, you're never done growing—but who sees it?",
    
    ("Fire", "year"): "You came from heat—drama, visibility, or both.",
    ("Fire", "month"): "Your career demands attention. You give it.",
    ("Fire", "day"): "Your identity burns bright. Sustainable or not.",
    ("Fire", "hour"): "Inside, you're always performing—even alone.",
    
    ("Earth", "year"): "Your foundation is stability. But stability can become stagnation.",
    ("Earth", "month"): "You're the reliable one at work. Do they see you or use you?",
    ("Earth", "day"): "Your core is grounded. Too grounded to move when you should.",
    ("Earth", "hour"): "Your inner world craves security. At what cost?",
    
    ("Metal", "year"): "You inherited precision—or rigidity disguised as it.",
    ("Metal", "month"): "Your work requires standards. You enforce them.",
    ("Metal", "day"): "Your identity is sharp. Others notice the edge.",
    ("Metal", "hour"): "Inside, you're refining constantly. Perfectionism or presence?",
    
    ("Water", "year"): "Your roots flow. Adaptable—or rootless.",
    ("Water", "month"): "Your career shifts shape. Strategic or scattered?",
    ("Water", "day"): "Your core identity is fluid. Freedom or avoidance?",
    ("Water", "hour"): "Your inner world is deep. Wisdom or withdrawal?",
}


def interpret_pillar(pillar_data: Dict, position: str) -> Dict[str, str]:
    """
    Interpret a single pillar in behavioral terms.
    
    Returns:
    {
        "domain": "Roots" / "Work" / "Self" / "Inner World",
        "animal": "Tiger",
        "element_note": "Your roots push toward growth...",
        "behavioral": "You lead without permission...",
    }
    """
    meaning = PILLAR_MEANINGS.get(position, {"domain": position.title(), "represents": ""})
    animal = pillar_data.get("animal_name", pillar_data.get("animal", "Unknown"))
    stem_element = pillar_data.get("stem_element", "")
    
    return {
        "domain": meaning["domain"],
        "animal": animal,
        "element_note": ELEMENT_IN_PILLAR.get((stem_element, position), ""),
        "behavioral": ANIMAL_BEHAVIORS.get(animal, ""),
    }


def synthesize_pillars(pillar_interpretations: Dict[str, Dict]) -> str:
    """
    Create a combined behavioral pattern from all four pillars.
    This is the "one synthesized pattern" requirement.
    """
    year = pillar_interpretations.get("year", {})
    month = pillar_interpretations.get("month", {})
    day = pillar_interpretations.get("day", {})
    hour = pillar_interpretations.get("hour", {})
    
    # Extract animals
    year_animal = year.get("animal", "")
    day_animal = day.get("animal", "")
    hour_animal = hour.get("animal", "")
    
    # Build synthesis based on animal combinations
    if year_animal in ["Tiger", "Dragon", "Horse"] and day_animal in ["Rabbit", "Goat", "Pig"]:
        return "You present as bold externally, but your core craves harmony. The gap creates exhaustion—performing strength while needing softness."
    
    if year_animal in ["Rat", "Monkey"] and hour_animal in ["Dog", "Ox"]:
        return "Your outer cleverness hides inner loyalty anxiety. You strategize in public, worry in private."
    
    if day_animal == hour_animal:
        return f"Your outer and inner selves align—{day_animal} energy runs all the way through. Consistent, but also one-dimensional."
    
    if year_animal in ["Snake", "Rooster"] and day_animal in ["Tiger", "Dragon"]:
        return "Your roots calculate, your core demands. Others experience intensity; you experience internal strategy."
    
    # Default synthesis based on any animal combination
    animals_present = [year_animal, month.get("animal", ""), day_animal, hour_animal]
    animals_present = [a for a in animals_present if a]
    
    if len(set(animals_present)) == 4:
        return "Your four pillars pull in different directions. Versatile—or scattered. The question is whether you're adaptive or avoiding coherence."
    
    return f"Your chart shows {day_animal} at your core, shaped by {year_animal} roots. The tension between inheritance and identity defines your pattern."


# =============================================================================
# THE REAL TENSION - Emotional landing paragraph
# =============================================================================

REAL_TENSION_TEMPLATES = {
    ("Wood", "Yang"): "You've spent your life starting things—projects, relationships, conversations. The tension isn't whether you can begin. It's whether you can stay. Every time you moved on, you told yourself it was strategic. But some of those things deserved more than your momentum. The pattern isn't wrong. It's incomplete.",
    
    ("Wood", "Yin"): "You've survived by bending. And it's worked—you're still here when others broke. But somewhere along the way, bending became automatic. You don't know what shape you'd be if you stopped adapting. The tension isn't whether you're flexible. It's whether you remember what you're flexible toward.",
    
    ("Fire", "Yang"): "People have always watched you. And you've learned to perform—even when you don't mean to. The tension isn't the attention. It's the distance between what they see and who you are when the lights are off. You've been visible so long, you're not sure you know yourself in the dark.",
    
    ("Fire", "Yin"): "You've warmed rooms your whole life. Held space when others couldn't. The tension isn't whether you can sustain. It's whether anyone has ever asked what you need to burn. You've stayed lit for so long, you've forgotten what it feels like to be fed instead of feeding.",
    
    ("Earth", "Yang"): "People have leaned on you since before you were ready. And you held. You always held. The tension isn't the weight—you can carry it. It's that you've been standing so long, you've forgotten how to sit down. What happens when the mountain realizes it's tired?",
    
    ("Earth", "Yin"): "You've grown things. People. Projects. Relationships. They flourished around you, and that felt like enough. But the tension isn't about what you've nurtured. It's about what you've neglected: yourself. You gave until giving became the only way you knew how to exist.",
    
    ("Metal", "Yang"): "You cut through. Always have. When others hesitate, you decide. The tension isn't the clarity—it's the collateral. You've learned to move past the wounds you leave. The question is whether that's strength or avoidance wearing its armor.",
    
    ("Metal", "Yin"): "You notice everything. The flaw in the fabric. The gap in the logic. The thing no one else caught. The tension isn't your precision—it's your exhaustion. You've been refining so long, you've forgotten that some things don't need to be perfect. They just need to be done.",
    
    ("Water", "Yang"): "You've flowed around every obstacle in your path. Adapted. Moved. Found another way when the first one closed. The tension isn't your adaptability—it's the question you've been avoiding: are you flowing toward something, or just away from everything?",
    
    ("Water", "Yin"): "You've understood things before you could explain them. Sensed undercurrents no one else noticed. The tension isn't your depth—it's your silence. You've known so much and shared so little. The isolation isn't happening to you. You've been building it.",
}


def generate_deep_dive_v2(
    day_master_element: str,
    day_master_polarity: str,
    day_master_strength: str,
    pillars: Dict[str, Dict],
    dominant_elements: List[str],
    missing_elements: List[str],
    ten_gods: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """
    Generate the full BaZi Deep Dive in the confrontational Mirror style.
    
    Returns the complete structure:
    {
        "core_pattern": str,
        "the_tension": str,
        "what_this_costs_you": [str],
        "why_this_exists": str,
        "your_chart_read_simply": {
            "year": {...},
            "month": {...},
            "day": {...},
            "hour": {...},
            "synthesis": str,
        },
        "when_this_backfires": [str],
        "the_real_tension": str,
        "one_shift": str,
    }
    """
    key = (day_master_element, day_master_polarity)
    
    # Core Pattern - the sharp opening
    core_truth = CORE_TRUTH_TEMPLATES.get(key, {})
    core_pattern = core_truth.get("line1", "You have a pattern that runs deeper than you admit.")
    
    # The Tension - two forces pulling
    tension_templates = {
        ("Wood", "Yang"): "You want to lead—but you also want to move on before anyone depends on you.",
        ("Wood", "Yin"): "You want to be yourself—but you keep shaping around what others need.",
        ("Fire", "Yang"): "You want to be seen—but you're tired of performing.",
        ("Fire", "Yin"): "You want to be cared for—but you keep being the caretaker.",
        ("Earth", "Yang"): "You want to rest—but you can't stop holding everyone else up.",
        ("Earth", "Yin"): "You want to receive—but giving is the only way you know how to connect.",
        ("Metal", "Yang"): "You want connection—but you keep cutting through instead of staying.",
        ("Metal", "Yin"): "You want it done—but you can't stop perfecting.",
        ("Water", "Yang"): "You want stability—but stillness feels like death.",
        ("Water", "Yin"): "You want to be understood—but you won't let anyone close enough.",
    }
    the_tension = tension_templates.get(key, "Two parts of you are pulling in opposite directions.")
    
    # What This Costs You
    costs_data = WHAT_THIS_COSTS_TEMPLATES.get(key, {})
    what_this_costs = [
        costs_data.get("energy", "Energy spent maintaining the pattern"),
        costs_data.get("relationships", "Relationships that couldn't meet you"),
        costs_data.get("opportunities", "Opportunities that passed while you repeated"),
    ]
    
    # Add element-specific costs
    if "Fire" in missing_elements:
        what_this_costs.append("Visibility you avoided because it felt unsafe")
    if "Water" in missing_elements:
        what_this_costs.append("Depth you skipped because it was inconvenient")
    if "Metal" in missing_elements:
        what_this_costs.append("Decisions delayed because you couldn't cut clean")
    
    # Why This Exists - light BaZi reference
    why_this_exists = f"Your Day Master is {day_master_polarity} {day_master_element}—the part of you that holds the pattern. With {', '.join(dominant_elements) if dominant_elements else 'balanced elements'} dominant and {', '.join(missing_elements) if missing_elements else 'no elements'} less available, your chart amplifies certain tendencies while leaving others underdeveloped."
    
    # Your Chart, Read Simply - pillar interpretations
    pillar_interpretations = {}
    for position in ["year", "month", "day", "hour"]:
        pillar_data = pillars.get(position, {})
        if pillar_data:
            pillar_interpretations[position] = interpret_pillar(pillar_data, position)
    
    synthesis = synthesize_pillars(pillar_interpretations)
    
    # When This Backfires
    when_backfires = WHEN_THIS_BACKFIRES_TEMPLATES.get(key, [])[:4]
    
    # The Real Tension - emotional landing
    the_real_tension = REAL_TENSION_TEMPLATES.get(key, "The pattern isn't the problem. The repetition without awareness is.")
    
    # One Shift
    one_shift = ONE_SHIFT_TEMPLATES.get(key, "Notice the pattern before it runs. That's the only shift that matters.")
    
    return {
        "core_pattern": core_pattern,
        "the_tension": the_tension,
        "what_this_costs_you": what_this_costs[:5],  # Limit to 5
        "why_this_exists": why_this_exists,
        "your_chart_read_simply": {
            **pillar_interpretations,
            "synthesis": synthesis,
        },
        "when_this_backfires": when_backfires,
        "the_real_tension": the_real_tension,
        "one_shift": one_shift,
    }

