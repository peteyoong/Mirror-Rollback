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
# HOW THIS SHOWS UP - Real-life behaviors
# =============================================================================

HOW_THIS_SHOWS_UP_TEMPLATES = {
    ("Wood", "Yang"): [
        "You start conversations before others finish thinking",
        "You've already moved on to the next thing before this one lands",
        "You push through obstacles that others stop at",
        "You say 'let's go' when others are still planning",
        "You get frustrated with slow processes",
    ],
    ("Wood", "Yin"): [
        "You find alternative routes when direct paths close",
        "You build connections without forcing them",
        "You persist quietly while others give up loudly",
        "You adapt to what's in front of you rather than fighting it",
        "You grow sideways when you can't grow up",
    ],
    ("Fire", "Yang"): [
        "You end up leading even when you didn't plan to",
        "Your presence fills the room before you speak",
        "You clarify situations by just being there",
        "You attract attention without seeking it",
        "You inspire action in others just by starting",
    ],
    ("Fire", "Yin"): [
        "You provide consistent warmth that others rely on",
        "You nurture through steady presence, not grand gestures",
        "You stay lit when others burn out",
        "You support without needing to be seen doing it",
        "You maintain connection even through silence",
    ],
    ("Earth", "Yang"): [
        "You hold space that others can't",
        "People come to you when everything else feels unstable",
        "You stay solid when chaos hits",
        "You carry more than people realize",
        "You provide structure that others lean on without noticing",
    ],
    ("Earth", "Yin"): [
        "You create conditions for others to grow",
        "You absorb more than you realize you're taking on",
        "You nurture without being asked",
        "You make fertile ground out of difficult situations",
        "Others flourish around you, sometimes at your expense",
    ],
    ("Metal", "Yang"): [
        "You see what matters and what doesn't — quickly",
        "You decide when others are still deliberating",
        "You hold standards that others avoid naming",
        "You cut through emotional noise to find the point",
        "You end conversations that need ending",
    ],
    ("Metal", "Yin"): [
        "You notice details others miss",
        "You prefer less but better",
        "You refine what you touch",
        "You set internal standards higher than anyone else's expectations",
        "You catch mistakes before they become problems",
    ],
    ("Water", "Yang"): [
        "You navigate uncertainty that freezes others",
        "You find paths through chaos",
        "You're comfortable not knowing what comes next",
        "You adapt faster than you realize",
        "You keep moving when others stop to plan",
    ],
    ("Water", "Yin"): [
        "You perceive undercurrents others miss",
        "You know things before you can explain how",
        "Stillness reveals what movement hides for you",
        "You understand people before they speak",
        "You sense shifts before they happen",
    ],
}


# =============================================================================
# WHEN THIS BACKFIRES - Sharp, specific
# =============================================================================

WHEN_THIS_BACKFIRES_TEMPLATES = {
    ("Wood", "Yang"): [
        "You bulldoze through situations that needed finesse",
        "You start things before the last thing is finished",
        "You dismiss input because it feels like delay",
        "You push harder when pulling back would work better",
    ],
    ("Wood", "Yin"): [
        "You bend so much you lose your direction",
        "You adapt to everyone else's needs and forget your own",
        "Flexibility becomes indecision",
        "You avoid conflict by never taking a position",
    ],
    ("Fire", "Yang"): [
        "You burn hot and fast until nothing's left",
        "You need visibility even when it costs you",
        "You react dramatically when quiet would serve better",
        "You exhaust yourself sustaining high energy",
    ],
    ("Fire", "Yin"): [
        "You dim yourself to make others comfortable",
        "You flicker erratically when your fuel runs low",
        "You disappear when you need to be seen",
        "You give warmth until you have none left",
    ],
    ("Earth", "Yang"): [
        "You become immovable when adaptation is needed",
        "You carry so much you can't move",
        "Stability becomes stubbornness",
        "You hold on to things that need releasing",
    ],
    ("Earth", "Yin"): [
        "You over-give until you're empty",
        "You lose yourself in others' needs",
        "You absorb problems that aren't yours to carry",
        "You nurture at the expense of your own growth",
    ],
    ("Metal", "Yang"): [
        "You cut things that needed more time",
        "You become harsh when precision isn't welcome",
        "Clarity becomes coldness",
        "You're right in a way that makes you alone",
    ],
    ("Metal", "Yin"): [
        "You become overly critical — of yourself first, then others",
        "Precision becomes perfectionism that freezes action",
        "You notice every flaw, including ones that don't matter",
        "You refine past the point of usefulness",
    ],
    ("Water", "Yang"): [
        "You keep moving when you need to stop",
        "You become scattered, always going but never arriving",
        "You flow past things that needed your attention",
        "You avoid by moving instead of facing",
    ],
    ("Water", "Yin"): [
        "You withdraw so deep others can't reach you",
        "You lose yourself in reflection without action",
        "You understand but never share what you know",
        "You sense everything and process nothing",
    ],
}


# =============================================================================
# WHAT THIS COSTS YOU - Energy, Relationships, Opportunities
# =============================================================================

WHAT_THIS_COSTS_TEMPLATES = {
    ("Wood", "Yang"): {
        "energy": "Starting over repeatedly instead of building on what exists",
        "relationships": "People stop offering input because you'll move anyway",
        "opportunities": "Missed refinements that would have made the win bigger",
    },
    ("Wood", "Yin"): {
        "energy": "Processing everyone else's direction before choosing your own",
        "relationships": "People don't know what you actually want",
        "opportunities": "Paths not taken because you adapted instead of chose",
    },
    ("Fire", "Yang"): {
        "energy": "Burning out before the finish line",
        "relationships": "Being seen but not known",
        "opportunities": "Projects abandoned when the spotlight moved",
    },
    ("Fire", "Yin"): {
        "energy": "Maintaining warmth when you have none left",
        "relationships": "Being relied on but not supported",
        "opportunities": "Not being seen when it mattered",
    },
    ("Earth", "Yang"): {
        "energy": "Carrying weight that was never yours",
        "relationships": "Being leaned on but not met",
        "opportunities": "Stuck positions that missed the moment",
    },
    ("Earth", "Yin"): {
        "energy": "Giving until nothing remains for yourself",
        "relationships": "Known for what you give, not who you are",
        "opportunities": "Your own growth delayed by tending others",
    },
    ("Metal", "Yang"): {
        "energy": "Fighting battles that didn't need winning",
        "relationships": "Being right and being alone",
        "opportunities": "Cut options that had more to offer",
    },
    ("Metal", "Yin"): {
        "energy": "Perfecting past the point of return",
        "relationships": "People feel judged before they start",
        "opportunities": "Good enough shipped, perfect never did",
    },
    ("Water", "Yang"): {
        "energy": "Moving without arriving",
        "relationships": "Hard to find when people need you",
        "opportunities": "Flowed past moments that needed your presence",
    },
    ("Water", "Yin"): {
        "energy": "Processing depth that never surfaces",
        "relationships": "Understood others, never was understood",
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
