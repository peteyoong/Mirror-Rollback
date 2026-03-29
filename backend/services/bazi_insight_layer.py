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
        "You're always moving, but nothing lands",
        "You flow past things that needed your attention",
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
