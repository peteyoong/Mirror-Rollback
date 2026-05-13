"""Human Design calculations using True Sidereal positions

===============================================================================
DETERMINISTIC COMPUTATION CORE - FROZEN
===============================================================================
This file is part of Project Mirror's deterministic computation core.
Outputs must remain stable across versions.
Do NOT modify without updating regression tests and bumping computation_version.

Current version: hd_sidereal_v1
Astronomy version: true_sidereal_m_swe_v1
Computation version: mirror_compute_v1

FROZEN: 2025-03-07 - All benchmarks passed (Jay, Melissa, Pete)
===============================================================================

SYMBOLIC COMPUTE CONTRACT:
This module implements the SymbolicComputeContract interface for Human Design.
All payloads must include compute_integrity validation.
===============================================================================
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple, Optional
from .astrology import get_full_natal_chart, normalize_degrees
from .symbolic_compute_contract import (
    ComputeIntegrityError,
    ComputeIntegrityResult,
    HUMAN_DESIGN_REQUIRED_KEYS
)
import swisseph as swe
import math


# All centers in Human Design
ALL_CENTERS = ['Head', 'Ajna', 'Throat', 'G Center', 'Ego', 'Sacral', 'Solar Plexus', 'Spleen', 'Root']

# =============================================================================
# HUMAN DESIGN RAVE MANDALA GATE WHEEL
# =============================================================================
# The HD gates are NOT evenly distributed around the zodiac.
# They follow the I-Ching sequence mapped to specific zodiac positions.
# Format: (gate_number, start_degree, end_degree) in absolute zodiac degrees
# where Aries 0° = 0, Taurus 0° = 30, etc.

HD_GATE_WHEEL = [
    # Gate, Start Degree, End Degree (absolute zodiac 0-360)
    
    # Aries (0-30°)
    (25, 358.25, 363.867),  # 28°15′ Pisces to 3°52′ Aries (wraps around)
    (17, 3.867, 9.5),       # 3°52′ to 9°30′ Aries
    (21, 9.5, 15.117),      # 9°30′ to 15°07′ Aries
    (51, 15.117, 20.75),    # 15°07′ to 20°45′ Aries
    (42, 20.75, 26.367),    # 20°45′ to 26°22′ Aries
    (3, 26.367, 32.0),      # 26°22′ Aries to 2°00′ Taurus
    
    # Taurus (30-60°)
    (27, 32.0, 37.617),     # 2°00′ to 7°37′ Taurus
    (24, 37.617, 43.25),    # 7°37′ to 13°15′ Taurus
    (2, 43.25, 48.867),     # 13°15′ to 18°52′ Taurus
    (23, 48.867, 54.5),     # 18°52′ to 24°30′ Taurus
    (8, 54.5, 60.117),      # 24°30′ Taurus to 0°07′ Gemini
    
    # Gemini (60-90°)
    (20, 60.117, 65.75),    # 0°07′ to 5°45′ Gemini
    (16, 65.75, 71.367),    # 5°45′ to 11°22′ Gemini
    (35, 71.367, 77.0),     # 11°22′ to 17°00′ Gemini
    (45, 77.0, 82.617),     # 17°00′ to 22°37′ Gemini
    (12, 82.617, 88.25),    # 22°37′ to 28°15′ Gemini
    (15, 88.25, 93.867),    # 28°15′ Gemini to 3°52′ Cancer
    
    # Cancer (90-120°)
    (52, 93.867, 99.5),     # 3°52′ to 9°30′ Cancer
    (39, 99.5, 105.117),    # 9°30′ to 15°07′ Cancer
    (53, 105.117, 110.75),  # 15°07′ to 20°45′ Cancer
    (62, 110.75, 116.367),  # 20°45′ to 26°22′ Cancer
    (56, 116.367, 122.0),   # 26°22′ Cancer to 2°00′ Leo
    
    # Leo (120-150°)
    (31, 122.0, 127.617),   # 2°00′ to 7°37′ Leo
    (33, 127.617, 133.25),  # 7°37′ to 13°15′ Leo
    (7, 133.25, 138.867),   # 13°15′ to 18°52′ Leo
    (4, 138.867, 144.5),    # 18°52′ to 24°30′ Leo
    (29, 144.5, 150.117),   # 24°30′ Leo to 0°07′ Virgo
    
    # Virgo (150-180°)
    (59, 150.117, 155.75),  # 0°07′ to 5°45′ Virgo
    (40, 155.75, 161.367),  # 5°45′ to 11°22′ Virgo
    (64, 161.367, 167.0),   # 11°22′ to 17°00′ Virgo
    (47, 167.0, 172.617),   # 17°00′ to 22°37′ Virgo
    (6, 172.617, 178.25),   # 22°37′ to 28°15′ Virgo
    (46, 178.25, 183.867),  # 28°15′ Virgo to 3°52′ Libra
    
    # Libra (180-210°)
    (18, 183.867, 189.5),   # 3°52′ to 9°30′ Libra
    (48, 189.5, 195.117),   # 9°30′ to 15°07′ Libra
    (57, 195.117, 200.75),  # 15°07′ to 20°45′ Libra
    (32, 200.75, 206.367),  # 20°45′ to 26°22′ Libra
    (50, 206.367, 212.0),   # 26°22′ Libra to 2°00′ Scorpio
    
    # Scorpio (210-240°)
    (28, 212.0, 217.617),   # 2°00′ to 7°37′ Scorpio
    (44, 217.617, 223.25),  # 7°37′ to 13°15′ Scorpio
    (1, 223.25, 228.867),   # 13°15′ to 18°52′ Scorpio
    (43, 228.867, 234.5),   # 18°52′ to 24°30′ Scorpio
    (14, 234.5, 240.117),   # 24°30′ Scorpio to 0°07′ Sagittarius
    
    # Sagittarius (240-270°)
    (34, 240.117, 245.75),  # 0°07′ to 5°45′ Sagittarius
    (9, 245.75, 251.367),   # 5°45′ to 11°22′ Sagittarius
    (5, 251.367, 257.0),    # 11°22′ to 17°00′ Sagittarius
    (26, 257.0, 262.617),   # 17°00′ to 22°37′ Sagittarius
    (11, 262.617, 268.25),  # 22°37′ to 28°15′ Sagittarius
    (10, 268.25, 273.867),  # 28°15′ Sagittarius to 3°52′ Capricorn
    
    # Capricorn (270-300°)
    (58, 273.867, 279.5),   # 3°52′ to 9°30′ Capricorn
    (38, 279.5, 285.117),   # 9°30′ to 15°07′ Capricorn
    (54, 285.117, 290.75),  # 15°07′ to 20°45′ Capricorn
    (61, 290.75, 296.367),  # 20°45′ to 26°22′ Capricorn
    (60, 296.367, 302.0),   # 26°22′ Capricorn to 2°00′ Aquarius
    
    # Aquarius (300-330°)
    (41, 302.0, 307.617),   # 2°00′ to 7°37′ Aquarius
    (19, 307.617, 313.25),  # 7°37′ to 13°15′ Aquarius
    (13, 313.25, 318.867),  # 13°15′ to 18°52′ Aquarius
    (49, 318.867, 324.5),   # 18°52′ to 24°30′ Aquarius
    (30, 324.5, 330.117),   # 24°30′ Aquarius to 0°07′ Pisces
    
    # Pisces (330-360°)
    (55, 330.117, 335.75),  # 0°07′ to 5°45′ Pisces
    (37, 335.75, 341.367),  # 5°45′ to 11°22′ Pisces
    (63, 341.367, 347.0),   # 11°22′ to 17°00′ Pisces
    (22, 347.0, 352.617),   # 17°00′ to 22°37′ Pisces
    (36, 352.617, 358.25),  # 22°37′ to 28°15′ Pisces
    # Gate 25 wraps from Pisces to Aries (handled specially)
]

# =============================================================================
# INCARNATION CROSS NAMES
# =============================================================================
# Maps personality Sun gate to the cross name. The cross is determined by
# the Sun gate in the Personality (conscious) calculation.
# Format: gate_number -> cross_name

INCARNATION_CROSS_NAMES = {
    1: "Sphinx",
    2: "Driver",
    3: "Laws",
    4: "Explanation",
    5: "Consciousness",
    6: "Eden",
    7: "Sphinx",
    8: "Contagion",
    9: "Planning",
    10: "Vessel of Love",
    11: "Education",
    12: "Eden",
    13: "Sphinx",
    14: "Contagion",
    15: "Vessel of Love",
    16: "Planning",
    17: "Service",
    18: "Service",
    19: "Four Ways",
    20: "Sleeping Phoenix",
    21: "Tension",
    22: "Rulership",
    23: "Assimilation",
    24: "Incarnation",
    25: "Vessel of Love",
    26: "Rulership",
    27: "Unexpected",
    28: "Game Player",
    29: "Contagion",
    30: "Contagion",
    31: "Unexpected",
    32: "Maya",
    33: "Four Ways",
    34: "Sleeping Phoenix",
    35: "Consciousness",
    36: "Eden",
    37: "Migration",
    38: "Tension",
    39: "Tension",
    40: "Migration",
    41: "Unexpected",
    42: "Maya",
    43: "Explanation",
    44: "Four Ways",
    45: "Rulership",
    46: "Vessel of Love",
    47: "Rulership",
    48: "Tension",
    49: "Explanation",
    50: "Laws",
    51: "Penetration",
    52: "Service",
    53: "Penetration",
    54: "Penetration",
    55: "Sleeping Phoenix",
    56: "Laws",
    57: "Penetration",
    58: "Service",
    59: "Sleeping Phoenix",
    60: "Laws",
    61: "Maya",
    62: "Maya",
    63: "Consciousness",
    64: "Consciousness",
}

# ============================================================================
# INCARNATION CROSS STRUCTURED INTERPRETATIONS
# Deterministic theme layer separate from LLM prose
# ============================================================================
INCARNATION_CROSS_THEMES = {
    # Cross name -> structured interpretation with theme bullets
    "Migration": {
        "themes": [
            "Movement and transition as life themes",
            "Finding belonging through shared agreements",
            "The courage to leave what's familiar",
            "Building community wherever you go"
        ],
        "orientation_flavor": {
            "RAX": "Your personal journey involves cycles of leaving and arriving. Growth comes through movement.",
            "LAX": "You carry something that helps others navigate transitions. Your moves often serve a larger purpose.",
            "JXP": "Your path of movement is fixed - you are meant to be a bridge between worlds."
        }
    },
    "Sphinx": {
        "themes": [
            "The mystery of self-identity",
            "Direction through self-love",
            "Being a riddle others want to solve",
            "Leadership through knowing yourself"
        ],
        "orientation_flavor": {
            "RAX": "Your personal journey is about discovering who you truly are beneath roles and expectations.",
            "LAX": "Your self-knowledge becomes a compass that guides others toward their own direction.",
            "JXP": "You embody the mystery - your very presence raises questions about identity and direction."
        }
    },
    "Tension": {
        "themes": [
            "Holding opposing forces in creative tension",
            "Depth that comes from struggle",
            "The value of meaningful challenge",
            "Purpose found through perseverance"
        ],
        "orientation_flavor": {
            "RAX": "Your personal growth comes through engaging with what's difficult, not avoiding it.",
            "LAX": "You help others see that their struggles have meaning. Your tension serves the collective.",
            "JXP": "You are meant to hold tension - it's your fixed role to embody this dynamic."
        }
    },
    "Vessel of Love": {
        "themes": [
            "Love as a guiding principle",
            "The body as a vehicle for spirit",
            "Being present in physical experience",
            "Love expressed through action"
        ],
        "orientation_flavor": {
            "RAX": "Your personal path is about embodying love in tangible, physical ways.",
            "LAX": "You transmit love that serves something larger than yourself. Your presence heals.",
            "JXP": "You are a fixed vessel - love flows through you in a consistent, destined pattern."
        }
    },
    "Consciousness": {
        "themes": [
            "The drive to understand and know",
            "Mental clarity as a life theme",
            "Sharing what makes sense",
            "Logic as a contribution"
        ],
        "orientation_flavor": {
            "RAX": "Your personal journey involves developing clarity through doubt and questioning.",
            "LAX": "Your understanding serves the collective. You help others make sense of confusion.",
            "JXP": "You are meant to embody a particular kind of knowing - your clarity is fixed."
        }
    },
    "Contagion": {
        "themes": [
            "Spreading something valuable",
            "The power of committed energy",
            "Influence through demonstration",
            "Success that others can catch"
        ],
        "orientation_flavor": {
            "RAX": "Your personal success spreads to those around you. Your energy is contagious.",
            "LAX": "You carry something meant to spread widely. Your contagion serves the whole.",
            "JXP": "You are a fixed carrier of contagious energy - spreading is your destiny."
        }
    },
    "Eden": {
        "themes": [
            "The search for paradise",
            "Emotional depth and experience",
            "Crisis as transformation",
            "Learning through feeling"
        ],
        "orientation_flavor": {
            "RAX": "Your personal journey involves emotional experiences that deepen understanding.",
            "LAX": "Your emotional journey serves others - you help people process their own feelings.",
            "JXP": "You are fixed in the emotional realm - eden and its losses are your domain."
        }
    },
    "Explanation": {
        "themes": [
            "Making the complex understandable",
            "Breaking through mental barriers",
            "Insight that wants to be shared",
            "Individual knowing that benefits all"
        ],
        "orientation_flavor": {
            "RAX": "Your personal breakthroughs in understanding are meant to be expressed.",
            "LAX": "Your explanations serve the collective - you simplify for others.",
            "JXP": "You are meant to explain - your insights have a fixed, destined quality."
        }
    },
    "Laws": {
        "themes": [
            "Structure and natural order",
            "The value of limitation",
            "Principles that guide behavior",
            "Conservation of what matters"
        ],
        "orientation_flavor": {
            "RAX": "Your personal growth involves accepting the laws and limits that shape your life.",
            "LAX": "You help others understand the value of structure and limitation.",
            "JXP": "You embody natural law - your principles are fixed and meant to be demonstrated."
        }
    },
    "Service": {
        "themes": [
            "Contributing through correction",
            "The joy of vitality",
            "Making things better",
            "Service that energizes"
        ],
        "orientation_flavor": {
            "RAX": "Your personal fulfillment comes through acts of service and improvement.",
            "LAX": "Your service is meant for the collective - you correct what needs correcting for all.",
            "JXP": "You are a fixed servant - service is your destined mode of being."
        }
    },
    "Rulership": {
        "themes": [
            "Natural authority",
            "Leading through emotional intelligence",
            "Influence through presence",
            "The responsibility of power"
        ],
        "orientation_flavor": {
            "RAX": "Your personal path involves developing authentic authority.",
            "LAX": "Your leadership serves something larger - you rule for the benefit of others.",
            "JXP": "You are meant to rule in some domain - your authority is fixed."
        }
    },
    "Planning": {
        "themes": [
            "Organizing collective resources",
            "The power of practical vision",
            "Making things work",
            "Contributing through logistics"
        ],
        "orientation_flavor": {
            "RAX": "Your personal growth involves learning to plan and organize effectively.",
            "LAX": "Your planning abilities serve the collective - you organize for others.",
            "JXP": "You are a fixed planner - organizing is your destined role."
        }
    },
    "Unexpected": {
        "themes": [
            "The value of surprise",
            "New experiences as growth",
            "Leading others into the unknown",
            "Completion through surprise"
        ],
        "orientation_flavor": {
            "RAX": "Your personal path involves embracing the unexpected as growth.",
            "LAX": "You bring unexpected experiences to others - your surprises serve the collective.",
            "JXP": "You are fixed in the unexpected - surprise is your destined mode."
        }
    },
    "Four Ways": {
        "themes": [
            "Multiple paths and perspectives",
            "Alertness to timing and opportunity",
            "The value of instinct",
            "Resources found through intuition"
        ],
        "orientation_flavor": {
            "RAX": "Your personal journey involves navigating multiple possible paths.",
            "LAX": "You help others see the different ways forward. Your instincts serve the collective.",
            "JXP": "You are meant to embody the four ways - your alertness is fixed."
        }
    },
    "Maya": {
        "themes": [
            "The illusion and reality of experience",
            "Finding truth in confusion",
            "Cycles of growth and decay",
            "Wisdom through limitation"
        ],
        "orientation_flavor": {
            "RAX": "Your personal journey involves seeing through illusion to reality.",
            "LAX": "You help others navigate the maya - your clarity serves the collective.",
            "JXP": "You are fixed in the maya - embodying the dance of illusion and reality."
        }
    },
    "Sleeping Phoenix": {
        "themes": [
            "Rebirth and renewal",
            "Power waiting to emerge",
            "The value of intimacy",
            "Transformation through connection"
        ],
        "orientation_flavor": {
            "RAX": "Your personal path involves cycles of death and rebirth in various forms.",
            "LAX": "Your transformations serve others - your rebirths model possibility.",
            "JXP": "You are a fixed phoenix - transformation and renewal is your destiny."
        }
    },
    "Penetration": {
        "themes": [
            "Breaking through barriers",
            "Shock as initiation",
            "Depth and focus",
            "Getting to the core"
        ],
        "orientation_flavor": {
            "RAX": "Your personal growth comes through penetrating experiences.",
            "LAX": "You help others break through - your penetrating quality serves the collective.",
            "JXP": "You are a fixed penetrator - breaking through is your destined mode."
        }
    },
    "Education": {
        "themes": [
            "Gathering and sharing ideas",
            "The value of harmony",
            "Peace through understanding",
            "Teaching and learning"
        ],
        "orientation_flavor": {
            "RAX": "Your personal path involves continuous learning and sharing.",
            "LAX": "You educate for the benefit of all - your teaching serves the collective.",
            "JXP": "You are a fixed educator - teaching is your destined role."
        }
    },
    "Game Player": {
        "themes": [
            "Meaning found through risk",
            "The value of struggle",
            "Playing for something worthwhile",
            "Purpose through challenge"
        ],
        "orientation_flavor": {
            "RAX": "Your personal growth comes through engaging with worthy struggles.",
            "LAX": "You play games that serve the collective - your struggles have larger meaning.",
            "JXP": "You are a fixed game player - meaningful struggle is your destiny."
        }
    },
    "Incarnation": {
        "themes": [
            "The return and renewal",
            "Spirit meeting form",
            "Rationalizing experience",
            "Making sense of cycles"
        ],
        "orientation_flavor": {
            "RAX": "Your personal path involves finding meaning in cycles of return.",
            "LAX": "You help others understand the purpose of incarnation itself.",
            "JXP": "You embody the incarnation theme - return and renewal is fixed in you."
        }
    },
    "Driver": {
        "themes": [
            "Direction and purpose",
            "The will to go higher",
            "Receptive knowing",
            "Being called forward"
        ],
        "orientation_flavor": {
            "RAX": "Your personal journey involves finding and following your true direction.",
            "LAX": "You help others find their direction - your knowing serves the collective.",
            "JXP": "You are a fixed driver - direction and calling is your destiny."
        }
    },
    "Assimilation": {
        "themes": [
            "Making the complex simple",
            "Breaking down what's complicated",
            "Individual insight for collective benefit",
            "The value of simplicity"
        ],
        "orientation_flavor": {
            "RAX": "Your personal journey involves distilling complex ideas into clear understanding.",
            "LAX": "You simplify for others - your insights make the complex accessible to all.",
            "JXP": "You are meant to assimilate - breaking things down is your fixed destiny."
        }
    },
}

def get_incarnation_cross_interpretation(cross_name: str, orientation: str) -> dict:
    """
    Get the structured interpretation for an incarnation cross.
    
    Args:
        cross_name: The cross name (e.g., "Migration")
        orientation: The angle (RAX, LAX, or JXP)
    
    Returns:
        Dict with themes and orientation-specific flavor
    """
    # Extract just the cross name if it includes orientation prefix
    name_only = cross_name
    for prefix in ["RAX ", "LAX ", "JXP "]:
        if cross_name.startswith(prefix):
            name_only = cross_name[len(prefix):]
            break
    
    theme_data = INCARNATION_CROSS_THEMES.get(name_only, {
        "themes": [
            "Your unique life direction",
            "The purpose encoded in your design",
            "Your contribution to the whole"
        ],
        "orientation_flavor": {
            "RAX": "Your personal journey follows this theme.",
            "LAX": "This theme serves a transpersonal purpose through you.",
            "JXP": "This theme is fixed in your destiny."
        }
    })
    
    return {
        "cross_name": cross_name,
        "name_only": name_only,
        "orientation": orientation,
        "themes": theme_data["themes"],
        "orientation_flavor": theme_data["orientation_flavor"].get(orientation, ""),
        "full_label": f"{orientation} {name_only}"
    }

def get_incarnation_cross_name(p_sun_gate: int, profile_line1: int) -> str:
    """
    DEPRECATED: Use get_incarnation_cross_full() instead.
    This function is kept for backward compatibility.
    """
    result = get_incarnation_cross_full(p_sun_gate, profile_line1)
    return result['cross_name']


def get_incarnation_cross_full(p_sun_gate: int, p_sun_line: int) -> dict:
    """
    Get the full incarnation cross data based on personality Sun gate and LINE.
    
    IMPORTANT: The cross angle (RAX/JXP/LAX) is determined by the Personality Sun LINE,
    NOT the profile.
    
    Personality Sun Line → Cross Angle:
    - Lines 1, 2, 3 → Right Angle Cross (RAX) - Personal destiny
    - Line 4 → Juxtaposition Cross (JXP) - Fixed fate  
    - Lines 5, 6 → Left Angle Cross (LAX) - Transpersonal karma
    
    Args:
        p_sun_gate: Personality Sun gate number (1-64)
        p_sun_line: Personality Sun line number (1-6)
    
    Returns:
        Dict with full cross information:
        {
            "cross_name": "Left Angle Cross of Migration 1",
            "cross_family": "Migration",
            "angle": "LAX",
            "angle_full": "Left Angle Cross",
            "variant": 1,
            "display_quartet": None  # To be filled by caller with gate data
        }
    """
    cross_family = INCARNATION_CROSS_NAMES.get(p_sun_gate, f"Gate {p_sun_gate}")
    
    # Determine cross angle from PERSONALITY SUN LINE (not profile!)
    if p_sun_line in [1, 2, 3]:
        angle = "RAX"
        angle_full = "Right Angle Cross"
        # Variant: lines 1,2,3 map to variants 1,2,3 within RAX
        variant = p_sun_line
    elif p_sun_line == 4:
        angle = "JXP"
        angle_full = "Juxtaposition Cross"
        # Juxtaposition has only 1 variant per gate
        variant = 1
    elif p_sun_line in [5, 6]:
        angle = "LAX"
        angle_full = "Left Angle Cross"
        # Variant: line 5 = variant 1, line 6 = variant 2
        variant = p_sun_line - 4
    else:
        # Fallback for invalid line
        angle = "RAX"
        angle_full = "Right Angle Cross"
        variant = 1
    
    # Build full cross name: e.g., "Left Angle Cross of Migration 1"
    # NOTE: This retains the variant for backward compatibility with any
    # internal code that needs to disambiguate cross variants. The
    # USER-FACING display name (`cross_name_display`) drops the variant
    # number — see /app/backend/calculations/human_design.py where the
    # gate quartet is filled in for the final payload.
    cross_name = f"{angle_full} of {cross_family} {variant}"

    # User-facing name — NEVER show the variant index to end users.
    # "Left Angle Cross of Explanation 1" → "Left Angle Cross of Explanation"
    cross_name_display = f"{angle_full} of {cross_family}"

    return {
        "cross_name": cross_name,
        "cross_name_display": cross_name_display,
        "cross_family": cross_family,
        "angle": angle,
        "angle_full": angle_full,
        "variant": variant,
        "display_quartet": None  # To be filled by caller
    }


def longitude_to_gate(longitude: float) -> Dict:
    """Convert sidereal longitude to I-Ching gate using HD Rave Mandala wheel
    
    The HD gate wheel is NOT a simple 360/64 division.
    Each gate has specific zodiac degree boundaries following I-Ching order.
    
    Args:
        longitude: Sidereal longitude (0-360)
    
    Returns:
        Dict with gate number, line (1-6), and formatted string
    """
    # Normalize to 0-360
    longitude = longitude % 360
    
    # Special handling for Gate 25 which wraps around 0°
    if longitude >= 358.25 or longitude < 3.867:
        gate = 25
        if longitude >= 358.25:
            pos_in_gate = longitude - 358.25
        else:
            pos_in_gate = (360 - 358.25) + longitude
        gate_size = (360 - 358.25) + 3.867  # ~5.617°
    else:
        # Search through gate wheel
        gate = None
        pos_in_gate = 0
        gate_size = 5.625  # Default
        
        for g, start, end in HD_GATE_WHEEL:
            if g == 25:  # Skip, handled above
                continue
            if start <= longitude < end:
                gate = g
                pos_in_gate = longitude - start
                gate_size = end - start
                break
        
        # Fallback if not found (shouldn't happen)
        if gate is None:
            gate = 1
            pos_in_gate = 0
            gate_size = 5.625
    
    # Calculate line (1-6) within gate
    # Each gate has 6 lines, evenly distributed
    line = int((pos_in_gate / gate_size) * 6) + 1
    if line > 6:
        line = 6
    if line < 1:
        line = 1
    
    # Calculate color (1-6) within line
    # Each line is divided into 6 colors
    line_size = gate_size / 6
    pos_in_line = pos_in_gate % line_size
    color = int((pos_in_line / line_size) * 6) + 1
    if color > 6:
        color = 6
    if color < 1:
        color = 1
    
    # Calculate tone (1-6) within color
    # Each color is divided into 6 tones
    color_size = line_size / 6
    pos_in_color = pos_in_line % color_size
    tone = int((pos_in_color / color_size) * 6) + 1
    if tone > 6:
        tone = 6
    if tone < 1:
        tone = 1
    
    # Calculate base (1-5) within tone
    # Each tone is divided into 5 bases
    tone_size = color_size / 5
    pos_in_tone = pos_in_color % tone_size
    base = int((pos_in_tone / tone_size) * 5) + 1
    if base > 5:
        base = 5
    if base < 1:
        base = 1
    
    return {
        'gate': gate,
        'line': line,
        'color': color,
        'tone': tone,
        'base': base,
        'formatted': f"{gate}.{line}",
        'full_formatted': f"{gate}.{line}.{color}.{tone}.{base}"
    }


# ============================================================================
# VARIABLES (PHS) COMPUTATION
# Variables are the "arrows" in HD - they come from Sun positions
# ============================================================================

# Environment types based on Design Sun tone
ENVIRONMENT_TYPES = {
    1: {'type': 'caves', 'description': 'Selective, enclosed spaces'},
    2: {'type': 'markets', 'description': 'Active, busy environments'},
    3: {'type': 'kitchens', 'description': 'Warm, nourishing spaces'},
    4: {'type': 'mountains', 'description': 'Elevated, overview perspectives'},
    5: {'type': 'valleys', 'description': 'Acoustic, sound-sensitive spaces'},
    6: {'type': 'shores', 'description': 'Transitional, edge spaces'}
}

# Determination (Digestion) based on Design Sun color
DETERMINATION_TYPES = {
    1: {'type': 'appetite', 'arrow': 'left', 'description': 'Eating when hungry, following appetite'},
    2: {'type': 'taste', 'arrow': 'left', 'description': 'Specific taste preferences guide nutrition'},
    3: {'type': 'thirst', 'arrow': 'left', 'description': 'Hydration and liquid-based nourishment'},
    4: {'type': 'touch', 'arrow': 'right', 'description': 'Texture and temperature awareness in food'},
    5: {'type': 'sound', 'arrow': 'right', 'description': 'Acoustic environment affects digestion'},
    6: {'type': 'light', 'arrow': 'right', 'description': 'Light conditions affect nourishment'}
}

# Cognition (Perspective) based on Personality Sun color
COGNITION_TYPES = {
    1: {'type': 'smell', 'arrow': 'left', 'description': 'Sensing through atmosphere and mood'},
    2: {'type': 'taste', 'arrow': 'left', 'description': 'Discriminating through experience'},
    3: {'type': 'outer_vision', 'arrow': 'left', 'description': 'Peripheral, wide-angle awareness'},
    4: {'type': 'inner_vision', 'arrow': 'right', 'description': 'Focused, concentrated perception'},
    5: {'type': 'feeling', 'arrow': 'right', 'description': 'Sensing through touch and proximity'},
    6: {'type': 'touch', 'arrow': 'right', 'description': 'Direct contact awareness'}
}

# Motivation based on Personality Sun tone
MOTIVATION_TYPES = {
    1: {'type': 'fear', 'description': 'Motivated by survival and security'},
    2: {'type': 'hope', 'description': 'Motivated by possibility and optimism'},
    3: {'type': 'desire', 'description': 'Motivated by attraction and want'},
    4: {'type': 'need', 'description': 'Motivated by necessity and requirement'},
    5: {'type': 'guilt', 'description': 'Motivated by responsibility and duty'},
    6: {'type': 'innocence', 'description': 'Motivated by purity and fresh perspective'}
}

# Arrow direction mapping (for the 4 arrows in HD chart)
def get_arrow_direction(color: int) -> str:
    """Determine arrow direction based on color
    Colors 1-3 = Left arrow (passive/receptive)
    Colors 4-6 = Right arrow (active/focused)
    """
    return 'left' if color <= 3 else 'right'


# REMOVED: estimate_color_tone_from_line()
# Variables must ONLY be computed from exact longitude data.
# Estimation/heuristics are not acceptable for deterministic output.


def calculate_variables(personality_sun_data: dict, design_sun_data: dict) -> dict:
    """Calculate Human Design Variables (the 4 arrows) from Sun positions
    
    The Variables are:
    - Top Left Arrow: Digestion/Determination (Design Sun color) - how you take in nourishment
    - Bottom Left Arrow: Environment (Design Sun tone) - where you thrive
    - Top Right Arrow: Perspective/Cognition (Personality Sun color) - how you see
    - Bottom Right Arrow: Motivation (Personality Sun tone) - why you act
    
    Args:
        personality_sun_data: Dict with gate, line, color, tone, base for Personality Sun
        design_sun_data: Dict with gate, line, color, tone, base for Design Sun
        
    Returns:
        Dict with complete Variables data
    """
    # Extract values
    p_color = personality_sun_data.get('color', 1)
    p_tone = personality_sun_data.get('tone', 1)
    d_color = design_sun_data.get('color', 1)
    d_tone = design_sun_data.get('tone', 1)
    
    # Calculate each Variable
    determination = DETERMINATION_TYPES.get(d_color, DETERMINATION_TYPES[1])
    environment = ENVIRONMENT_TYPES.get(d_tone, ENVIRONMENT_TYPES[1])
    cognition = COGNITION_TYPES.get(p_color, COGNITION_TYPES[1])
    motivation = MOTIVATION_TYPES.get(p_tone, MOTIVATION_TYPES[1])
    
    # Calculate arrow directions
    digestion_arrow = get_arrow_direction(d_color)  # Top left
    environment_arrow = 'left' if d_tone <= 3 else 'right'  # Bottom left
    perspective_arrow = get_arrow_direction(p_color)  # Top right
    awareness_arrow = 'left' if p_tone <= 3 else 'right'  # Bottom right
    
    # Build the canonical Variables payload
    return {
        # Environment - where you function best
        'environment': {
            'type': environment['type'],
            'tone': d_tone,
            'description': environment['description'],
            'arrow': environment_arrow
        },
        # Determination - how you take in nourishment
        'determination': {
            'type': determination['type'],
            'color': d_color,
            'description': determination['description'],
            'arrow': digestion_arrow
        },
        # Cognition - how you perceive
        'cognition': {
            'type': cognition['type'],
            'color': p_color,
            'description': cognition['description'],
            'arrow': perspective_arrow
        },
        # Motivation - what drives you
        'motivation': {
            'type': motivation['type'],
            'tone': p_tone,
            'description': motivation['description'],
            'arrow': awareness_arrow
        },
        # Raw values for reference
        'raw': {
            'personality_sun_color': p_color,
            'personality_sun_tone': p_tone,
            'design_sun_color': d_color,
            'design_sun_tone': d_tone
        },
        # Arrow summary (for visual representation)
        'arrows': {
            'top_left': digestion_arrow,      # Digestion
            'bottom_left': environment_arrow,  # Environment
            'top_right': perspective_arrow,    # Perspective
            'bottom_right': awareness_arrow    # Awareness
        }
    }


def calculate_design_date(birth_datetime: datetime, lat: float = 0, lon: float = 0, 
                          svp_degrees: float = 31.2836) -> Tuple[datetime, float, Dict]:
    """Calculate Design date using numerical solver
    
    The Design date is NOT simply 88 days before birth.
    It's the precise moment when the sidereal Sun was 88 degrees
    BEFORE its position at birth.
    
    Algorithm:
    1. Get birth Sun sidereal longitude
    2. Calculate target: birth_sun - 88 degrees (normalized to 0-360)
    3. Binary search in window of 70-110 days before birth
    4. Find timestamp where Sun is within 0.01° of target
    
    Args:
        birth_datetime: UTC birth datetime
        lat: Latitude (for consistency, not used in Sun calc)
        lon: Longitude (for consistency, not used in Sun calc)
        svp_degrees: Sidereal Vernal Point offset
    
    Returns:
        Tuple of (design_datetime, offset_degrees, debug_info)
    """
    # Ensure we're working with UTC
    if birth_datetime.tzinfo is None:
        birth_datetime = birth_datetime.replace(tzinfo=timezone.utc)
    
    # Get birth Sun sidereal position
    birth_sun_sidereal = _get_sun_sidereal(birth_datetime, svp_degrees)
    
    # Target: 88 degrees before birth Sun
    target_sun = normalize_degrees(birth_sun_sidereal - 88.0)
    
    # Search window: 70-110 days before birth
    early_bound = birth_datetime - timedelta(days=110)
    late_bound = birth_datetime - timedelta(days=70)
    
    # Binary search parameters
    # Tolerance matches canonical_astronomy._solve_design_datetime so both solvers
    # converge to the same design timestamp — keeping HD and Astrology in sync.
    tolerance = 0.001  # degrees (~3.6 arcseconds; ~0.1 minutes of time)
    max_iterations = 60
    
    low = early_bound
    high = late_bound
    best_datetime = None
    best_delta = 999
    
    for iteration in range(max_iterations):
        # Calculate midpoint
        mid_timestamp = low + (high - low) / 2
        mid_sun = _get_sun_sidereal(mid_timestamp, svp_degrees)
        
        # Calculate angular delta
        delta = _angular_difference(mid_sun, target_sun)
        
        # Track best result
        if delta < best_delta:
            best_delta = delta
            best_datetime = mid_timestamp
        
        # Check convergence
        if delta < tolerance:
            break
        
        # Determine search direction
        # Sun moves ~1° per day forward through zodiac
        # Signed difference: positive means mid_sun is ahead of target
        signed_diff = (mid_sun - target_sun + 180) % 360 - 180
        
        if signed_diff > 0:
            # mid_sun is ahead of target, need earlier time
            high = mid_timestamp
        else:
            # mid_sun is behind target, need later time
            low = mid_timestamp
    
    # Build debug info
    debug_info = {
        "birth_sun_sidereal": birth_sun_sidereal,
        "target_sun_sidereal": target_sun,
        "design_sun_sidereal": _get_sun_sidereal(best_datetime, svp_degrees),
        "search_iterations": iteration + 1,
        "converged": best_delta < tolerance
    }
    
    return best_datetime, best_delta, debug_info


def _get_sun_sidereal(dt: datetime, svp_degrees: float = 31.2836) -> float:
    """Get sidereal Sun longitude at a given datetime.

    CANONICAL PATH: Uses Swiss Ephemeris SIDM_USER mode via the canonical
    sidereal_config initialization — the same path Astrology uses. Does NOT
    do manual tropical-minus-SVP subtraction (which bypasses sidereal mode
    precision and can silently fall back to Moshier when FLG_SWIEPH is unset).

    Args:
        dt: UTC datetime
        svp_degrees: Kept for API compatibility; ignored. Canonical SVP is enforced.

    Returns:
        Sidereal Sun longitude (0-360), identical to what Astrology would read.
    """
    # Route through the canonical sidereal config so HD and Astrology can
    # never drift: same FLG_SWIEPH | FLG_SIDEREAL flag combination, same
    # SIDM_USER mode, same SVP, same ephemeris path.
    from calculations.sidereal_config import (
        _ensure_ephemeris_initialized as _canon_init,
        CALC_FLAGS_SIDEREAL as _CANON_FLAGS,
        normalize_degrees as _canon_norm,
    )

    _canon_init()

    if dt.tzinfo is not None:
        utc_dt = dt.astimezone(timezone.utc)
    else:
        utc_dt = dt

    decimal_hour = utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
    jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, decimal_hour)

    # CANONICAL sidereal Sun (same flags Astrology uses)
    result = swe.calc_ut(jd, swe.SUN, _CANON_FLAGS)
    return _canon_norm(result[0][0])


def _angular_difference(a: float, b: float) -> float:
    """Calculate shortest angular distance between two angles
    
    Args:
        a, b: Angles in degrees (0-360)
    
    Returns:
        Absolute shortest distance (0-180)
    """
    diff = abs(a - b) % 360
    if diff > 180:
        diff = 360 - diff
    return diff


# =============================================================================
# HUMAN DESIGN CHANNEL, CENTER, TYPE, AUTHORITY, PROFILE LOGIC
# =============================================================================

# Complete list of 36 Human Design channels
# Format: (gate1, gate2, center1, center2)
HD_CHANNELS = [
    # Head to Ajna
    (64, 47, 'Head', 'Ajna'),
    (61, 24, 'Head', 'Ajna'),
    (63, 4, 'Head', 'Ajna'),
    # Ajna to Throat
    (17, 62, 'Ajna', 'Throat'),
    (43, 23, 'Ajna', 'Throat'),
    (11, 56, 'Ajna', 'Throat'),
    # Throat to G Center
    (31, 7, 'Throat', 'G Center'),
    (8, 1, 'Throat', 'G Center'),
    (33, 13, 'Throat', 'G Center'),
    # Throat to Sacral (Motor to Throat)
    (20, 34, 'Throat', 'Sacral'),
    # Throat to Solar Plexus (Motor to Throat)
    (35, 36, 'Throat', 'Solar Plexus'),
    (12, 22, 'Throat', 'Solar Plexus'),
    # Throat to Ego/Heart (Motor to Throat)
    (45, 21, 'Throat', 'Ego'),
    # Throat to Spleen
    (16, 48, 'Throat', 'Spleen'),
    (20, 57, 'Throat', 'Spleen'),
    # G Center to Sacral
    (15, 5, 'G Center', 'Sacral'),
    (2, 14, 'G Center', 'Sacral'),
    (46, 29, 'G Center', 'Sacral'),
    # G Center to Spleen
    (10, 57, 'G Center', 'Spleen'),
    # G Center to Ego
    (25, 51, 'G Center', 'Ego'),
    # Sacral to Spleen
    (27, 50, 'Sacral', 'Spleen'),
    (59, 6, 'Sacral', 'Solar Plexus'),
    (3, 60, 'Sacral', 'Root'),
    (9, 52, 'Sacral', 'Root'),
    (42, 53, 'Sacral', 'Root'),
    (34, 57, 'Sacral', 'Spleen'),
    # Solar Plexus to Root
    (49, 19, 'Solar Plexus', 'Root'),
    (55, 39, 'Solar Plexus', 'Root'),
    (30, 41, 'Solar Plexus', 'Root'),
    (36, 35, 'Solar Plexus', 'Throat'),  # Already listed above
    (37, 40, 'Solar Plexus', 'Ego'),
    # Spleen to Root
    (44, 26, 'Spleen', 'Ego'),
    (28, 38, 'Spleen', 'Root'),
    (18, 58, 'Spleen', 'Root'),
    (32, 54, 'Spleen', 'Root'),
    # Ego to Sacral
    (26, 44, 'Ego', 'Spleen'),  # duplicate, already listed
]

# Clean channel list (remove duplicates, ensure consistent ordering)
HD_CHANNELS_CLEAN = [
    # Head to Ajna (3 channels)
    (64, 47, 'Head', 'Ajna'),
    (61, 24, 'Head', 'Ajna'),
    (63, 4, 'Head', 'Ajna'),
    # Ajna to Throat (3 channels)
    (17, 62, 'Ajna', 'Throat'),
    (43, 23, 'Ajna', 'Throat'),
    (11, 56, 'Ajna', 'Throat'),
    # Throat to G Center (3 channels)
    (31, 7, 'Throat', 'G Center'),
    (8, 1, 'Throat', 'G Center'),
    (33, 13, 'Throat', 'G Center'),
    # G Center to Sacral (3 channels)
    (15, 5, 'G Center', 'Sacral'),
    (2, 14, 'G Center', 'Sacral'),
    (46, 29, 'G Center', 'Sacral'),
    # G Center to Spleen (1 channel)
    (10, 57, 'G Center', 'Spleen'),
    # G Center to Ego (1 channel)
    (25, 51, 'G Center', 'Ego'),
    # Sacral to Throat (1 channel - Motor to Throat)
    (20, 34, 'Sacral', 'Throat'),
    # Sacral to Spleen (2 channels)
    (27, 50, 'Sacral', 'Spleen'),
    (34, 57, 'Sacral', 'Spleen'),
    # Sacral to Solar Plexus (1 channel)
    (59, 6, 'Sacral', 'Solar Plexus'),
    # Sacral to Root (3 channels)
    (3, 60, 'Sacral', 'Root'),
    (9, 52, 'Sacral', 'Root'),
    (42, 53, 'Sacral', 'Root'),
    # Throat to Solar Plexus (2 channels - Motor to Throat)
    (35, 36, 'Throat', 'Solar Plexus'),
    (12, 22, 'Throat', 'Solar Plexus'),
    # Throat to Ego (1 channel - Motor to Throat)
    (45, 21, 'Throat', 'Ego'),
    # Throat to Spleen (2 channels)
    (16, 48, 'Throat', 'Spleen'),
    (57, 20, 'Throat', 'Spleen'),  # 20-57 channel
    # Solar Plexus to Ego (1 channel)
    (37, 40, 'Solar Plexus', 'Ego'),
    # Solar Plexus to Root (3 channels)
    (49, 19, 'Solar Plexus', 'Root'),
    (55, 39, 'Solar Plexus', 'Root'),
    (30, 41, 'Solar Plexus', 'Root'),
    # Spleen to Ego (1 channel)
    (44, 26, 'Spleen', 'Ego'),
    # Spleen to Root (3 channels)
    (28, 38, 'Spleen', 'Root'),
    (18, 58, 'Spleen', 'Root'),
    (32, 54, 'Spleen', 'Root'),
]

# Motors are: Sacral, Solar Plexus, Ego (Heart), Root
MOTOR_CENTERS = {'Sacral', 'Solar Plexus', 'Ego', 'Root'}


def get_defined_channels(all_gates: set) -> List[Tuple]:
    """Find all defined channels based on activated gates
    
    A channel is defined ONLY if BOTH gates are present.
    
    Args:
        all_gates: Set of all activated gate numbers (personality + design)
    
    Returns:
        List of tuples: (gate1, gate2, center1, center2) for each defined channel
    """
    defined_channels = []
    
    for gate1, gate2, center1, center2 in HD_CHANNELS_CLEAN:
        if gate1 in all_gates and gate2 in all_gates:
            defined_channels.append((gate1, gate2, center1, center2))
    
    return defined_channels


def get_defined_centers(defined_channels: List[Tuple]) -> List[str]:
    """Get list of defined centers based on defined channels
    
    A center is defined ONLY if it has at least one FULL channel connected.
    
    Args:
        defined_channels: List of defined channel tuples
    
    Returns:
        List of defined center names
    """
    defined_centers = set()
    
    for gate1, gate2, center1, center2 in defined_channels:
        defined_centers.add(center1)
        defined_centers.add(center2)
    
    return list(defined_centers)


def has_motor_to_throat(defined_channels: List[Tuple]) -> bool:
    """Check if any motor center reaches the Throat through defined channels.

    Motor centers: Sacral, Solar Plexus, Ego (Heart), Root.

    Per canonical Ra Uru Hu HD, the Throat is "defined by a motor" whenever
    there exists a *path* of defined channels from any motor center to the
    Throat — not only direct motor↔Throat channels.  Example (Michelle Chai,
    May 2026 fix): Sacral —(2-14)→ G Center —(1-8)→ Throat is a valid
    motor-to-throat path through the G Center bridge, which classifies the
    chart as Manifesting Generator (not Generator).

    Args:
        defined_channels: List of defined channel tuples
            (gate1, gate2, center1, center2).

    Returns:
        True if ANY motor center is reachable from the Throat (or vice
        versa) through the graph of defined channels.
    """
    # Build adjacency map: center -> set(neighbor centers)
    adjacency: Dict[str, set] = {}
    for ch in defined_channels:
        # Channels are either (g1, g2, c1, c2) tuples or dicts; support both.
        if isinstance(ch, dict):
            c1, c2 = ch.get('center1'), ch.get('center2')
            centers = ch.get('centers') or []
            if (not c1 or not c2) and len(centers) >= 2:
                c1, c2 = centers[0], centers[1]
        else:
            try:
                _, _, c1, c2 = ch
            except (ValueError, TypeError):
                continue
        if not c1 or not c2 or c1 == c2:
            continue
        adjacency.setdefault(c1, set()).add(c2)
        adjacency.setdefault(c2, set()).add(c1)

    if 'Throat' not in adjacency:
        return False

    # BFS from Throat through the channel graph; if we encounter any motor
    # center, the Throat is motor-defined.
    visited = {'Throat'}
    queue = ['Throat']
    while queue:
        cur = queue.pop(0)
        for nb in adjacency.get(cur, ()):
            if nb in visited:
                continue
            if nb in MOTOR_CENTERS:
                return True
            visited.add(nb)
            queue.append(nb)
    return False


def determine_type(defined_centers: List[str], defined_channels: List[Tuple]) -> str:
    """Determine Human Design Type based on defined centers and channels
    
    Order matters:
    1. Reflector: NO defined centers
    2. Generator: Sacral defined AND no motor-to-throat
    3. Manifesting Generator: Sacral defined AND motor-to-throat
    4. Manifestor: motor-to-throat AND Sacral undefined
    5. Projector: Sacral undefined AND not Reflector or Manifestor
    
    Args:
        defined_centers: List of defined center names
        defined_channels: List of defined channel tuples
    
    Returns:
        HD Type string
    """
    # Convert to set for efficient lookup
    centers_set = set(defined_centers)
    
    # 1. Reflector: NO defined centers
    if len(defined_centers) == 0:
        return 'Reflector'
    
    sacral_defined = 'Sacral' in centers_set
    motor_to_throat = has_motor_to_throat(defined_channels)
    
    # 2. Generator: Sacral defined AND no motor-to-throat
    if sacral_defined and not motor_to_throat:
        return 'Generator'
    
    # 3. Manifesting Generator: Sacral defined AND motor-to-throat
    if sacral_defined and motor_to_throat:
        return 'Manifesting Generator'
    
    # 4. Manifestor: motor-to-throat AND Sacral undefined
    if motor_to_throat and not sacral_defined:
        return 'Manifestor'
    
    # 5. Projector: everything else (Sacral undefined, not Reflector/Manifestor)
    return 'Projector'


def determine_definition(defined_channels: List[Tuple], defined_centers: List[str]) -> str:
    """Determine Definition type based on how centers are connected
    
    Args:
        defined_channels: List of defined channel tuples
        defined_centers: List of defined center names
    
    Returns:
        Definition type: "No Definition", "Single", "Split", "Triple Split", "Quadruple Split"
    """
    if len(defined_centers) == 0:
        return "No Definition"
    
    if len(defined_channels) == 0:
        return "No Definition"
    
    # Build adjacency graph
    graph = {center: set() for center in defined_centers}
    for gate1, gate2, center1, center2 in defined_channels:
        if center1 in graph and center2 in graph:
            graph[center1].add(center2)
            graph[center2].add(center1)
    
    # Count connected components using BFS
    visited = set()
    components = 0
    
    for center in defined_centers:
        if center not in visited:
            components += 1
            # BFS from this center
            queue = [center]
            while queue:
                current = queue.pop(0)
                if current not in visited:
                    visited.add(current)
                    for neighbor in graph.get(current, []):
                        if neighbor not in visited:
                            queue.append(neighbor)
    
    if components == 1:
        return "Single"
    elif components == 2:
        return "Split"
    elif components == 3:
        return "Triple Split"
    else:
        return "Quadruple Split"


def determine_authority(hd_type: str, defined_centers: List[str]) -> str:
    """Determine Inner Authority based on type and defined centers
    
    CANONICAL LABELS (frozen):
    - Lunar (Reflector only)
    - Emotional
    - Sacral
    - Splenic
    - Ego
    - Self
    - None (Mental/Environment Projector)
    
    Args:
        hd_type: Human Design type
        defined_centers: List of defined center names
    
    Returns:
        Authority string (canonical label)
    """
    # Reflector special case
    if hd_type == 'Reflector':
        return 'Lunar'
    
    centers_set = set(defined_centers)
    
    # Standard HD authority hierarchy with canonical labels
    if 'Solar Plexus' in centers_set:
        return 'Emotional'
    if 'Sacral' in centers_set:
        return 'Sacral'
    if 'Spleen' in centers_set:
        return 'Splenic'
    if 'Ego' in centers_set:
        return 'Ego'
    if 'G Center' in centers_set:
        return 'Self'
    
    # Mental/Environment authority (Projector with only Head/Ajna defined)
    return 'None'


def calculate_profile(personality_sun_line: int, design_sun_line: int) -> str:
    """Calculate Human Design Profile
    
    Profile = personality Sun line / design Sun line
    No inversion, no fallback.
    
    Args:
        personality_sun_line: Line number (1-6) from personality Sun gate
        design_sun_line: Line number (1-6) from design Sun gate
    
    Returns:
        Profile string (e.g., "3/5")
    """
    return f"{personality_sun_line}/{design_sun_line}"


def calculate_centers_old(personality_gates: List[int], design_gates: List[int]) -> Dict:
    """DEPRECATED: Old center calculation (incorrect)
    Kept for reference only - DO NOT USE
    """
    pass

def get_human_design_chart(birth_datetime: datetime, lat: float, lon: float,
                           sidereal_settings: Dict = None) -> Dict:
    """Calculate complete Human Design bodygraph with compute integrity contract.
    
    HUMAN DESIGN COMPUTE INTEGRITY CONTRACT:
    This function MUST return a complete, validated canonical payload or raise
    ComputeIntegrityError. Partial charts are NEVER returned.
    
    REQUIRED COMPUTED OBJECTS:
    - type (Generator, Projector, Manifestor, Manifesting Generator, Reflector)
    - strategy (To Respond, To Inform, etc.)
    - authority (Emotional, Sacral, Splenic, etc.)
    - profile (e.g., "3/5")
    - definition (None, Single, Split, Triple Split, Quadruple Split)
    - incarnation_cross (dict with name + gates)
    - defined_centers (list)
    - undefined_centers (list)
    - defined_channels (list)
    - active_gates (list)
    
    Args:
        birth_datetime: UTC birth datetime
        lat: Geographic latitude
        lon: Geographic longitude  
        sidereal_settings: Optional sidereal settings override
    
    Returns:
        Dict with canonical HD payload
    
    Raises:
        ComputeIntegrityError: If any required data is missing or invalid
    """
    # Default sidereal settings
    if sidereal_settings is None:
        sidereal_settings = {
            "mode": "true_sidereal_user_defined",
            "svp_degrees": 31.2836,
            "reference_year": 2000,
            "yearly_increment": 0.0
        }
    
    svp_degrees = sidereal_settings.get("svp_degrees", 31.2836)
    
    # Get Personality (Conscious) chart at birth
    try:
        personality_chart = get_full_natal_chart(birth_datetime, lat, lon, sidereal_settings)
    except ComputeIntegrityError as e:
        # Re-raise with HD context
        raise ComputeIntegrityError(
            [f"HD Personality Chart: {err}" for err in e.errors],
            e.partial_data
        )
    
    # Calculate Design date using numerical solver
    design_datetime, design_offset_degrees, design_debug = calculate_design_date(
        birth_datetime, lat, lon, svp_degrees
    )
    
    # Get Design (Unconscious) chart at solved design date
    try:
        design_chart = get_full_natal_chart(design_datetime, lat, lon, sidereal_settings)
    except ComputeIntegrityError as e:
        # Re-raise with HD context
        raise ComputeIntegrityError(
            [f"HD Design Chart: {err}" for err in e.errors],
            e.partial_data
        )
    
    # Extract key planets for Human Design
    # Human Design uses 13 celestial bodies for gate activation
    hd_planets = [
        'Sun', 'Earth', 'Moon',
        'Mercury', 'Venus', 'Mars',
        'Jupiter', 'Saturn',
        'Uranus', 'Neptune', 'Pluto',
        'North Node', 'South Node'
    ]
    
    personality_data = {}
    design_data = {}
    
    for planet in hd_planets:
        # Personality
        p_pos = personality_chart['planets'].get(planet)
        if not p_pos:
            raise ComputeIntegrityError([f"HD Personality: {planet} missing"])
        p_longitude = p_pos['longitude']
        personality_data[planet] = {
            'position': p_pos,
            'longitude': p_longitude,  # Store longitude directly for Variables computation
            'gate': longitude_to_gate(p_longitude)
        }
        
        # Design
        d_pos = design_chart['planets'].get(planet)
        if not d_pos:
            raise ComputeIntegrityError([f"HD Design: {planet} missing"])
        d_longitude = d_pos['longitude']
        design_data[planet] = {
            'position': d_pos,
            'longitude': d_longitude,  # Store longitude directly for Variables computation
            'gate': longitude_to_gate(d_longitude)
        }
    
    # Get all gates (gate numbers only)
    personality_gates = [personality_data[p]['gate']['gate'] for p in hd_planets]
    design_gates = [design_data[p]['gate']['gate'] for p in hd_planets]
    all_gates = set(personality_gates + design_gates)
    
    # NEW CORRECT LOGIC: Calculate channels first, then centers
    # A channel is defined ONLY if BOTH gates are present
    defined_channels = get_defined_channels(all_gates)
    
    # A center is defined ONLY if it has at least one FULL channel
    defined_centers = get_defined_centers(defined_channels)
    
    # Calculate undefined centers
    undefined_centers = [c for c in ALL_CENTERS if c not in defined_centers]
    
    # Determine type based on defined centers and channels
    hd_type = determine_type(defined_centers, defined_channels)
    
    # Determine definition (None, Single, Split, etc.)
    definition = determine_definition(defined_channels, defined_centers)
    
    # Determine authority based on type and defined centers
    authority = determine_authority(hd_type, defined_centers)
    
    # Calculate Profile: personality Sun line / design Sun line
    personality_sun_line = personality_data['Sun']['gate']['line']
    design_sun_line = design_data['Sun']['gate']['line']
    profile = calculate_profile(personality_sun_line, design_sun_line)
    
    # Calculate Variables (PHS/Environment) from Sun positions
    # Variables come from color and tone of Personality Sun and Design Sun
    variables = calculate_variables(
        personality_sun_data=personality_data['Sun']['gate'],
        design_sun_data=design_data['Sun']['gate']
    )
    
    # Calculate Incarnation Cross with proper naming
    p_sun_gate = personality_data['Sun']['gate']['gate']
    p_earth_gate = personality_data['Earth']['gate']['gate']
    d_sun_gate = design_data['Sun']['gate']['gate']
    d_earth_gate = design_data['Earth']['gate']['gate']
    
    # Get FULL cross data using Personality Sun LINE (not profile!)
    cross_data = get_incarnation_cross_full(p_sun_gate, personality_sun_line)
    incarnation_cross_gates = f"{p_sun_gate}/{p_earth_gate} | {d_sun_gate}/{d_earth_gate}"

    # User-facing display strings — these are what the UI should render.
    # We expose them explicitly so callers don't have to massage the
    # internal `cross_name` (which still carries the variant for
    # backward-compat).
    gates_display = (
        f"Gates: {p_sun_gate} \u00b7 {p_earth_gate} \u00b7 "
        f"{d_sun_gate} \u00b7 {d_earth_gate}"
    )

    # Update cross_data with gate quartet
    cross_data['display_quartet'] = incarnation_cross_gates
    cross_data['gates_display'] = gates_display
    cross_data['personality_sun'] = p_sun_gate
    cross_data['personality_earth'] = p_earth_gate
    cross_data['design_sun'] = d_sun_gate
    cross_data['design_earth'] = d_earth_gate
    cross_data['personality_sun_line'] = personality_sun_line
    
    # Legacy field for backward compatibility
    incarnation_cross_name = cross_data['cross_name']
    
    # Format channels for output
    defined_channels_formatted = [
        {"gate1": g1, "gate2": g2, "centers": [c1, c2]} 
        for g1, g2, c1, c2 in defined_channels
    ]
    
    # Strategy for type
    strategy = get_strategy_for_type(hd_type)
    
    # =========================================================================
    # COMPUTE INTEGRITY ASSERTIONS (FAIL FAST)
    # =========================================================================
    compute_errors = []
    
    # 1. Assert type is valid
    valid_types = ['Generator', 'Manifesting Generator', 'Projector', 'Manifestor', 'Reflector']
    if hd_type not in valid_types:
        compute_errors.append(f"Type: invalid value '{hd_type}'")
    
    # 2. Assert strategy exists
    if not strategy:
        compute_errors.append("Strategy: missing")
    
    # 3. Assert authority exists
    if not authority:
        compute_errors.append("Authority: missing")
    
    # 4. Assert profile format is valid (X/Y where X,Y are 1-6)
    if not profile or '/' not in profile:
        compute_errors.append(f"Profile: invalid format '{profile}'")
    else:
        try:
            p1, p2 = profile.split('/')
            if not (1 <= int(p1) <= 6 and 1 <= int(p2) <= 6):
                compute_errors.append(f"Profile: lines out of range '{profile}'")
        except ValueError:
            compute_errors.append(f"Profile: invalid format '{profile}'")
    
    # 5. Assert definition is valid
    valid_definitions = ['No Definition', 'Single', 'Split', 'Triple Split', 'Quadruple Split']
    if definition not in valid_definitions:
        compute_errors.append(f"Definition: invalid value '{definition}'")
    
    # 6. Assert incarnation cross exists
    if not incarnation_cross_name:
        compute_errors.append("Incarnation Cross: name missing")
    if not incarnation_cross_gates:
        compute_errors.append("Incarnation Cross: gates missing")
    
    # 7. Assert centers are computed (either defined or undefined)
    total_centers = len(defined_centers) + len(undefined_centers)
    if total_centers != 9:
        compute_errors.append(f"Centers: expected 9 total, got {total_centers}")
    
    # 8. Assert active_gates is populated
    if len(all_gates) == 0:
        compute_errors.append("Active Gates: none computed")
    
    # =========================================================================
    # FAIL FAST - DO NOT RETURN PARTIAL DATA
    # =========================================================================
    if compute_errors:
        partial_data = {
            'type': hd_type,
            'authority': authority,
            'profile': profile,
            'defined_centers_count': len(defined_centers),
            'gates_count': len(all_gates)
        }
        raise ComputeIntegrityError(compute_errors, partial_data)
    
    # =========================================================================
    # INTERPRETATION BOUNDARY - DO NOT CROSS
    # =========================================================================
    # This payload contains DETERMINISTIC FACTS only.
    # - Type, Profile, Authority (classifications)
    # - Gates, Channels, Centers (structural data)
    # - Design date calculations
    #
    # This layer must NEVER include:
    # - Personality descriptions ("you are...")
    # - Life advice or strategies explained
    # - Predictions about relationships or career
    # - Value judgments about types
    #
    # Interpretation and narrative generation must occur DOWNSTREAM
    # in a separate layer (e.g., AI prompt assembly, UI copy).
    # =========================================================================
    
    # =========================================================================
    # BUILD CANONICAL PAYLOAD
    # =========================================================================
    return {
        # CANONICAL REQUIRED FIELDS (normalized structure)
        'type': hd_type,
        'strategy': strategy,
        'authority': authority,
        'profile': profile,
        'definition': definition,
        'incarnation_cross': {
            'name': incarnation_cross_name,
            'gates': incarnation_cross_gates,
            'personality_sun': p_sun_gate,
            'personality_earth': p_earth_gate,
            'design_sun': d_sun_gate,
            'design_earth': d_earth_gate,
            # NEW: Full cross data from get_incarnation_cross_full()
            'cross_name': cross_data['cross_name'],
            'cross_family': cross_data['cross_family'],
            'angle': cross_data['angle'],
            'angle_full': cross_data['angle_full'],
            'variant': cross_data['variant'],
            'personality_sun_line': cross_data['personality_sun_line']
        },
        'defined_centers': defined_centers,
        'undefined_centers': undefined_centers,
        'defined_channels': defined_channels_formatted,
        'active_gates': list(all_gates),
        'variables': variables,  # Computed from Sun positions (PHS/Environment)
        
        # Planetary longitudes for Variables computation (deterministic data)
        'planetary_longitudes': {
            'personality': {
                'sun': personality_data['Sun']['longitude'],
                'earth': personality_data['Earth']['longitude'],
                'moon': personality_data['Moon']['longitude'],
                'mercury': personality_data['Mercury']['longitude'],
                'venus': personality_data['Venus']['longitude'],
                'mars': personality_data['Mars']['longitude'],
                'jupiter': personality_data['Jupiter']['longitude'],
                'saturn': personality_data['Saturn']['longitude'],
                'uranus': personality_data['Uranus']['longitude'],
                'neptune': personality_data['Neptune']['longitude'],
                'pluto': personality_data['Pluto']['longitude'],
                'north_node': personality_data['North Node']['longitude'],
                'south_node': personality_data['South Node']['longitude'],
            },
            'design': {
                'sun': design_data['Sun']['longitude'],
                'earth': design_data['Earth']['longitude'],
                'moon': design_data['Moon']['longitude'],
                'mercury': design_data['Mercury']['longitude'],
                'venus': design_data['Venus']['longitude'],
                'mars': design_data['Mars']['longitude'],
                'jupiter': design_data['Jupiter']['longitude'],
                'saturn': design_data['Saturn']['longitude'],
                'uranus': design_data['Uranus']['longitude'],
                'neptune': design_data['Neptune']['longitude'],
                'pluto': design_data['Pluto']['longitude'],
                'north_node': design_data['North Node']['longitude'],
                'south_node': design_data['South Node']['longitude'],
            }
        },
        
        # Extended data
        'personality': personality_data,
        'design': design_data,
        'personality_gates': personality_gates,
        'design_gates': design_gates,
        
        # Legacy fields for backward compatibility
        'incarnation_cross_legacy': incarnation_cross_name,  # Old flat format
        'all_gates': list(all_gates),  # Alias
        
        # Metadata
        'chart_type': 'True Sidereal Human Design',
        'computation_version': 'mirror_compute_v1',
        'astronomy_version': 'true_sidereal_m_swe_v1',
        'human_design_version': 'hd_sidereal_v1',
        'design_datetime_utc_iso': design_datetime.isoformat() if hasattr(design_datetime, 'isoformat') else str(design_datetime),
        'design_offset_degrees': design_offset_degrees,
        'design_solver_debug': design_debug,
        
        # Compute integrity confirmation
        'compute_integrity': {
            'valid': True,
            'type_valid': hd_type in valid_types,
            'authority_valid': bool(authority),
            'profile_valid': bool(profile),
            'definition_valid': definition in valid_definitions,
            'centers_count': total_centers,
            'gates_count': len(all_gates),
            'channels_count': len(defined_channels)
        }
    }

def get_strategy_for_type(hd_type: str) -> str:
    """Get strategy description for each type"""
    strategies = {
        'Generator': 'To Respond',
        'Manifesting Generator': 'To Respond and Inform',
        'Manifestor': 'To Inform',
        'Projector': 'To Wait for Invitation',
        'Reflector': 'To Wait a Lunar Cycle'
    }
    return strategies.get(hd_type, 'Unknown')
# Deployment: 20260204_080831 - Incarnation cross naming fix
