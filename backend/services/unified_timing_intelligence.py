"""
Unified Timing Intelligence Layer
=================================

Creates ONE coherent timing profile that:
1. Homepage, Astrology Today, HD Today, BaZi all consume
2. NEVER contradicts what lens tabs show
3. Uses real transit data, not simplification

TransitProfile:
- intensity: low | moderate | high
- types: expansion | constraint | disruption | stabilization | closure | awakening
- domains: decision | growth | direction | identity | relationships | action
- is_forcing: bool
- evidence: List of actual transits

BaziDayProfile:
- day_element: Metal | Wood | Water | Fire | Earth
- interactions: clash | combine | pressure | support
- ten_gods_active: officer | wealth | output | resource | companion
- strength_shift: stronger | weaker | balanced
- implication: behavioral meaning

NumerologyDayProfile:
- universal_day: 1-9
- personal_day: 1-9
- energy_type: initiation | patience | communication | stability | change | harmony | reflection | power | completion
- implication: what the day supports

This feeds into cross_lens_diagnostician as the SINGLE source of truth.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# TRANSIT PROFILE - Astrology Timing
# =============================================================================

class TransitIntensity(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


@dataclass
class TransitProfile:
    """
    The unified transit profile consumed by all layers.
    NEVER simplified to just "quiet" vs "forcing".
    """
    intensity: TransitIntensity
    types: List[str]  # expansion, constraint, disruption, stabilization, closure, awakening
    domains: List[str]  # decision, growth, direction, identity, relationships, action
    is_forcing: bool
    evidence: List[Dict[str, Any]]  # Actual transit data
    summary: str  # Human-readable summary
    pattern_link: str  # How this relates to the current pattern
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "intensity": self.intensity.value,
            "types": self.types,
            "domains": self.domains,
            "is_forcing": self.is_forcing,
            "evidence": self.evidence,
            "summary": self.summary,
            "pattern_link": self.pattern_link,
        }


# Transit type mappings
ASPECT_TYPE_MAPPINGS = {
    "conjunction": {
        "Jupiter": ["expansion", "opportunity"],
        "Saturn": ["constraint", "responsibility"],
        "Uranus": ["disruption", "awakening"],
        "Neptune": ["dissolution", "spirituality"],
        "Pluto": ["transformation", "intensity"],
        "Mars": ["action", "drive"],
        "Venus": ["relationships", "values"],
        "Mercury": ["communication", "decision"],
        "Sun": ["identity", "purpose"],
        "Moon": ["emotion", "instinct"],
    },
    "square": {
        "Jupiter": ["expansion blocked", "overreach risk"],
        "Saturn": ["constraint", "pressure"],
        "Uranus": ["disruption", "unexpected change"],
        "Neptune": ["confusion", "illusion"],
        "Pluto": ["power struggle", "transformation pressure"],
        "Mars": ["frustration", "conflict"],
        "default": ["tension", "friction"],
    },
    "opposition": {
        "Jupiter": ["expansion vs contraction"],
        "Saturn": ["freedom vs responsibility"],
        "Uranus": ["stability vs change"],
        "default": ["polarity", "awareness"],
    },
    "trine": {
        "Jupiter": ["natural growth", "ease"],
        "Saturn": ["earned stability"],
        "Uranus": ["natural evolution", "awakening"],
        "default": ["flow", "support"],
    },
    "sextile": {
        "default": ["opportunity", "potential"],
    },
}

DOMAIN_MAPPINGS = {
    "Jupiter": ["growth", "opportunity", "expansion"],
    "Saturn": ["structure", "decision", "responsibility"],
    "Uranus": ["direction", "change", "awakening"],
    "Neptune": ["intuition", "spirituality", "confusion"],
    "Pluto": ["transformation", "power", "depth"],
    "Mars": ["action", "drive", "assertion"],
    "Venus": ["relationships", "values", "desire"],
    "Mercury": ["communication", "thought", "decision"],
    "Sun": ["identity", "purpose", "will"],
    "Moon": ["emotion", "needs", "instinct"],
    "North Node": ["destiny", "growth direction"],
    "Chiron": ["healing", "wound", "wisdom"],
}

# House to Life Domain mapping
HOUSE_DOMAINS = {
    1: {"name": "identity", "keywords": ["self", "appearance", "beginnings", "personal direction"]},
    2: {"name": "money", "keywords": ["value", "resources", "possessions", "self-worth"]},
    3: {"name": "communication", "keywords": ["siblings", "local environment", "learning", "daily movement"]},
    4: {"name": "home", "keywords": ["family", "roots", "private life", "emotional foundation"]},
    5: {"name": "creativity", "keywords": ["romance", "self-expression", "children", "pleasure"]},
    6: {"name": "work", "keywords": ["health", "routine", "service", "daily habits"]},
    7: {"name": "relationships", "keywords": ["partnership", "contracts", "one-on-one bonds", "open enemies"]},
    8: {"name": "intimacy", "keywords": ["shared resources", "transformation", "deeper bonds", "death/rebirth"]},
    9: {"name": "beliefs", "keywords": ["philosophy", "higher learning", "travel", "worldview"]},
    10: {"name": "career", "keywords": ["public life", "reputation", "responsibility", "achievement"]},
    11: {"name": "community", "keywords": ["friends", "groups", "future vision", "hopes"]},
    12: {"name": "retreat", "keywords": ["inner life", "endings", "spirituality", "hidden patterns"]},
}


def build_transit_profile(
    transit_aspects: List[Dict[str, Any]],
    pattern_family: str = "general",
    pattern_title: str = "Today's Pattern",
    natal_planets: Optional[Dict[str, Any]] = None,  # For house lookup
) -> TransitProfile:
    """
    Build a unified transit profile from actual transit data.
    
    CRITICAL: Never collapse to "quiet" if outer planet aspects exist.
    Now includes house/domain activation for specificity.
    """
    
    if not transit_aspects:
        return TransitProfile(
            intensity=TransitIntensity.LOW,
            types=["stillness"],
            domains=["internal"],
            is_forcing=False,
            evidence=[],
            summary="No major transits are activating your chart today. The signal is internal.",
            pattern_link="With no external transit pressure, what you're experiencing is arising from within."
        )
    
    types = []
    domains = []
    evidence = []
    activated_houses = []
    activated_life_domains = []
    outer_planet_count = 0
    hard_aspect_count = 0
    total_strength = 0
    
    OUTER_PLANETS = ["Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]
    HARD_ASPECTS = ["square", "opposition", "conjunction"]
    
    for transit in transit_aspects:
        transit_planet = transit.get("transit_point", "")
        aspect_type = transit.get("aspect_type", "")
        natal_planet = transit.get("natal_point", "")
        strength = transit.get("strength_score", 0.5)
        orb = transit.get("orb", 5)
        natal_house = transit.get("natal_house")  # House of natal planet
        
        total_strength += strength
        
        # Track outer planet involvement
        if transit_planet in OUTER_PLANETS:
            outer_planet_count += 1
        
        # Track hard aspects
        if aspect_type in HARD_ASPECTS:
            hard_aspect_count += 1
        
        # Get transit types
        aspect_mappings = ASPECT_TYPE_MAPPINGS.get(aspect_type, ASPECT_TYPE_MAPPINGS.get("sextile", {}))
        planet_types = aspect_mappings.get(transit_planet, aspect_mappings.get("default", ["activation"]))
        types.extend(planet_types)
        
        # Get domains
        planet_domains = DOMAIN_MAPPINGS.get(transit_planet, ["general"])
        domains.extend(planet_domains)
        
        # Get house/life domain if available
        if natal_house and natal_house in HOUSE_DOMAINS:
            house_info = HOUSE_DOMAINS[natal_house]
            if natal_house not in activated_houses:
                activated_houses.append(natal_house)
                activated_life_domains.append(house_info["name"])
        
        # Also try to look up house from natal_planets data
        if natal_planets and natal_planet:
            # Normalize planet name for lookup
            planet_key = natal_planet.lower().replace(" ", "_")
            for key in [planet_key, natal_planet, natal_planet.capitalize()]:
                if key in natal_planets:
                    planet_data = natal_planets.get(key, {})
                    if isinstance(planet_data, dict):
                        house = planet_data.get("house")
                        if house and house in HOUSE_DOMAINS and house not in activated_houses:
                            house_info = HOUSE_DOMAINS[house]
                            activated_houses.append(house)
                            activated_life_domains.append(house_info["name"])
                    break
        
        # Build evidence entry with house info
        evidence_entry = {
            "transit": f"{transit_planet} {aspect_type} {natal_planet}",
            "strength": round(strength, 2),
            "orb": round(orb, 2),
            "types": planet_types,
            "meaning": get_transit_meaning(transit_planet, aspect_type, natal_planet),
        }
        
        if natal_house and natal_house in HOUSE_DOMAINS:
            evidence_entry["house"] = natal_house
            evidence_entry["life_domain"] = HOUSE_DOMAINS[natal_house]["name"]
        
        evidence.append(evidence_entry)
    
    # Deduplicate
    types = list(dict.fromkeys(types))[:5]  # Top 5 unique
    domains = list(dict.fromkeys(domains))[:5]
    activated_life_domains = list(dict.fromkeys(activated_life_domains))[:5]
    
    # Calculate intensity - NEVER "quiet" with outer planet hard aspects
    avg_strength = total_strength / len(transit_aspects) if transit_aspects else 0
    
    if outer_planet_count >= 2 and hard_aspect_count >= 1:
        intensity = TransitIntensity.HIGH
    elif outer_planet_count >= 1 and hard_aspect_count >= 1:
        intensity = TransitIntensity.MODERATE
    elif avg_strength >= 0.7:
        intensity = TransitIntensity.MODERATE
    elif len(transit_aspects) >= 3:
        intensity = TransitIntensity.MODERATE
    else:
        intensity = TransitIntensity.LOW
    
    # Determine if forcing
    is_forcing = (
        hard_aspect_count >= 2 and 
        any("Mars" in t.get("transit_point", "") or "Pluto" in t.get("transit_point", "") for t in transit_aspects)
    )
    
    # Build summary with house/domain context
    summary = build_transit_summary_with_domains(types, domains, evidence, intensity, is_forcing, activated_life_domains)
    
    # Build pattern link with house context
    pattern_link = build_pattern_link_with_domains(types, domains, pattern_family, pattern_title, intensity, activated_life_domains)
    
    return TransitProfile(
        intensity=intensity,
        types=types,
        domains=domains,
        is_forcing=is_forcing,
        evidence=evidence,
        summary=summary,
        pattern_link=pattern_link
    )


def get_transit_meaning(transit_planet: str, aspect: str, natal_planet: str) -> str:
    """Get human-readable meaning for a transit."""
    
    MEANINGS = {
        ("Jupiter", "square", "Saturn"): "growth pushing against structure—expansion wants to happen but something resists",
        ("Uranus", "square", "Jupiter"): "disruption meeting opportunity—sudden changes to growth direction",
        ("Uranus", "trine", "Uranus"): "natural evolution—life direction aligning with awakening",
        ("Pluto", "square"): "transformation pressure—deep change demanding attention",
        ("Saturn", "square"): "responsibility weight—structure requiring decision",
        ("Mars", "conjunction"): "action activation—drive is intensified",
        ("Mars", "square"): "frustration building—action meeting resistance",
        ("Neptune", "square"): "confusion or dissolution—clarity harder to find",
    }
    
    # Try specific match
    key = (transit_planet, aspect, natal_planet)
    if key in MEANINGS:
        return MEANINGS[key]
    
    # Try planet + aspect
    for k, v in MEANINGS.items():
        if len(k) == 2 and k[0] == transit_planet and k[1] == aspect:
            return v
    
    # Default
    return f"{transit_planet} is activating {natal_planet} through {aspect}"


def build_transit_summary(
    types: List[str], 
    domains: List[str], 
    evidence: List[Dict], 
    intensity: TransitIntensity,
    is_forcing: bool
) -> str:
    """Build human-readable transit summary. NEVER say 'quiet' if there's real activation."""
    
    if not evidence:
        return "No major transits are activating your chart today."
    
    # Lead with intensity
    if intensity == TransitIntensity.HIGH:
        lead = "Multiple major transits are active today."
    elif intensity == TransitIntensity.MODERATE:
        lead = "There is real activation in the timing today."
    else:
        lead = "Mild transit activity is present."
    
    # Add type description
    type_descriptions = []
    if "expansion" in types and "constraint" in types:
        type_descriptions.append("Growth is pushing forward, but something is resisting it.")
    if "disruption" in types:
        type_descriptions.append("Change energy is active, though not fully formed.")
    if "transformation" in types:
        type_descriptions.append("Deep transformation pressure is present.")
    if "awakening" in types:
        type_descriptions.append("A natural evolution is underway.")
    
    # Add specific evidence
    if evidence:
        top_transit = evidence[0]
        type_descriptions.append(f"{top_transit['transit']}: {top_transit['meaning']}.")
    
    # Combine
    if type_descriptions:
        return f"{lead} {' '.join(type_descriptions[:2])}"
    
    return lead


def build_transit_summary_with_domains(
    types: List[str], 
    domains: List[str], 
    evidence: List[Dict], 
    intensity: TransitIntensity,
    is_forcing: bool,
    activated_life_domains: List[str]
) -> str:
    """Build human-readable transit summary WITH house/domain specificity."""
    
    if not evidence:
        return "No major transits are activating your chart today."
    
    # Lead with intensity
    if intensity == TransitIntensity.HIGH:
        lead = "Multiple major transits are active today"
    elif intensity == TransitIntensity.MODERATE:
        lead = "There is real activation in the timing today"
    else:
        lead = "Mild transit activity is present"
    
    # Add life domain context if available
    if activated_life_domains:
        domain_str = ", ".join(activated_life_domains[:4])
        lead += f", especially around {domain_str}."
    else:
        lead += "."
    
    # Add type description
    type_descriptions = []
    if "expansion" in types and "constraint" in types:
        if activated_life_domains:
            type_descriptions.append(f"Growth is meeting resistance around your {activated_life_domains[0] if activated_life_domains else 'direction'}.")
        else:
            type_descriptions.append("Growth is pushing forward, but something is resisting it.")
    if "disruption" in types:
        type_descriptions.append("Change energy is active, though not fully formed.")
    if "transformation" in types:
        type_descriptions.append("Deep transformation pressure is present.")
    if "awakening" in types:
        type_descriptions.append("A natural evolution is underway.")
    
    # Add specific evidence with house
    if evidence:
        top_transit = evidence[0]
        transit_str = f"{top_transit['transit']}: {top_transit['meaning']}"
        if top_transit.get("life_domain"):
            transit_str += f" (activating {top_transit['life_domain']})"
        type_descriptions.append(transit_str + ".")
    
    # Combine
    if type_descriptions:
        return f"{lead} {' '.join(type_descriptions[:2])}"
    
    return lead


def build_pattern_link_with_domains(
    types: List[str],
    domains: List[str],
    pattern_family: str,
    pattern_title: str,
    intensity: TransitIntensity,
    activated_life_domains: List[str]
) -> str:
    """Link transit profile to the current pattern WITH domain context."""
    
    # Pattern-specific links with domain awareness
    PATTERN_LINKS = {
        "stall": {
            "expansion+constraint": lambda d: f"This expansion-meets-resistance energy matches the stop-start momentum of your pause{', especially around ' + d[0] if d else ''}.",
            "disruption": lambda d: f"Change is active but unformed—this explains why forward motion keeps stalling{', particularly in ' + d[0] if d else ''}.",
            "transformation": lambda d: "Deep transformation is demanding attention before you move forward.",
            "default": lambda d: f"The transit pressure creates conditions where pausing makes sense{', especially in ' + ', '.join(d[:2]) if d else ''}.",
        },
        "push_pull": {
            "expansion+constraint": lambda d: f"Growth pushing against resistance creates the exact back-and-forth you're feeling{', around ' + ' and '.join(d[:2]) if d else ''}.",
            "disruption": lambda d: "Disruption energy is pulling you toward change while something else holds you back.",
            "default": lambda d: "Multiple forces are creating the push-pull you're experiencing.",
        },
        "expression": {
            "constraint": lambda d: "Constraint pressure is suppressing expression—the silence has external reinforcement.",
            "transformation": lambda d: "What wants to be said is connected to deeper transformation work.",
            "default": lambda d: f"The timing is influencing what can and cannot be expressed{', in ' + d[0] if d else ''}.",
        },
    }
    
    family_links = PATTERN_LINKS.get(pattern_family, PATTERN_LINKS.get("stall", {}))
    
    # Check for expansion + constraint combo
    if "expansion" in types and "constraint" in types:
        link_func = family_links.get("expansion+constraint", family_links.get("default", lambda d: "The timing is relevant to your pattern."))
        return link_func(activated_life_domains)
    
    # Check for specific types
    for type_name in ["disruption", "transformation", "constraint", "confusion"]:
        if type_name in types:
            if type_name in family_links:
                return family_links[type_name](activated_life_domains)
    
    # Default
    default_func = family_links.get("default", lambda d: f"The timing is connected to '{pattern_title}'.")
    return default_func(activated_life_domains)


def build_pattern_link(
    types: List[str],
    domains: List[str],
    pattern_family: str,
    pattern_title: str,
    intensity: TransitIntensity
) -> str:
    """Link transit profile to the current pattern. Make it feel like evidence."""
    
    # Pattern-specific links
    PATTERN_LINKS = {
        "stall": {
            "expansion+constraint": "This expansion-meets-resistance energy matches the stop-start momentum of your pause.",
            "disruption": "Change is active but unformed—this explains why forward motion keeps stalling.",
            "transformation": "Deep transformation is demanding attention before you move forward.",
            "default": "The transit pressure creates conditions where pausing makes sense.",
        },
        "push_pull": {
            "expansion+constraint": "Growth pushing against resistance creates the exact back-and-forth you're feeling.",
            "disruption": "Disruption energy is pulling you toward change while something else holds you back.",
            "default": "Multiple forces are creating the push-pull you're experiencing.",
        },
        "expression": {
            "constraint": "Constraint pressure is suppressing expression—the silence has external reinforcement.",
            "transformation": "What wants to be said is connected to deeper transformation work.",
            "default": "The timing is influencing what can and cannot be expressed.",
        },
        "clarity": {
            "confusion": "Neptune-style confusion is active—the fog has astrological support.",
            "disruption": "Disruption makes clarity harder because the ground keeps shifting.",
            "default": "The timing isn't supporting clear conclusions yet.",
        },
        "control": {
            "constraint": "Constraint pressure explains the need to grip—something really is unstable.",
            "transformation": "Transformation demands letting go, but the grip resists.",
            "default": "The timing is creating conditions that trigger control instincts.",
        },
    }
    
    family_links = PATTERN_LINKS.get(pattern_family, PATTERN_LINKS.get("stall", {}))
    
    # Check for expansion + constraint combo
    if "expansion" in types and "constraint" in types:
        return family_links.get("expansion+constraint", family_links.get("default", "The timing is relevant to your pattern."))
    
    # Check for specific types
    for type_name in ["disruption", "transformation", "constraint", "confusion"]:
        if type_name in types:
            if type_name in family_links:
                return family_links[type_name]
    
    # Default
    return family_links.get("default", f"The timing is connected to '{pattern_title}'.")


# =============================================================================
# BAZI DAY PROFILE
# =============================================================================

class BaziElement(str, Enum):
    WOOD = "Wood"
    FIRE = "Fire"
    EARTH = "Earth"
    METAL = "Metal"
    WATER = "Water"


@dataclass
class BaziDayProfile:
    """
    BaZi daily timing layer - what element energy is active today.
    """
    day_element: BaziElement
    day_stem: str  # 甲乙丙丁戊己庚辛壬癸
    day_branch: str  # 子丑寅卯辰巳午未申酉戌亥
    interactions: List[str]  # clash, combine, pressure, support, harm
    ten_gods_active: List[str]  # officer, wealth, output, resource, companion
    strength_shift: str  # stronger, weaker, balanced
    element_balance: Dict[str, str]  # how each element is affected today
    implication: str  # behavioral meaning
    pattern_link: str  # how it connects to current pattern
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "day_element": self.day_element.value,
            "day_stem": self.day_stem,
            "day_branch": self.day_branch,
            "interactions": self.interactions,
            "ten_gods_active": self.ten_gods_active,
            "strength_shift": self.strength_shift,
            "element_balance": self.element_balance,
            "implication": self.implication,
            "pattern_link": self.pattern_link,
        }


# BaZi Heavenly Stems cycle (10-day)
HEAVENLY_STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
STEM_ELEMENTS = {
    "甲": BaziElement.WOOD, "乙": BaziElement.WOOD,
    "丙": BaziElement.FIRE, "丁": BaziElement.FIRE,
    "戊": BaziElement.EARTH, "己": BaziElement.EARTH,
    "庚": BaziElement.METAL, "辛": BaziElement.METAL,
    "壬": BaziElement.WATER, "癸": BaziElement.WATER,
}

# Earthly Branches cycle (12-day)
EARTHLY_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
BRANCH_ELEMENTS = {
    "子": BaziElement.WATER, "丑": BaziElement.EARTH,
    "寅": BaziElement.WOOD, "卯": BaziElement.WOOD,
    "辰": BaziElement.EARTH, "巳": BaziElement.FIRE,
    "午": BaziElement.FIRE, "未": BaziElement.EARTH,
    "申": BaziElement.METAL, "酉": BaziElement.METAL,
    "戌": BaziElement.EARTH, "亥": BaziElement.WATER,
}

# Element cycle
ELEMENT_CYCLE = [BaziElement.WOOD, BaziElement.FIRE, BaziElement.EARTH, BaziElement.METAL, BaziElement.WATER]

# Element relationships
ELEMENT_PRODUCES = {
    BaziElement.WOOD: BaziElement.FIRE,
    BaziElement.FIRE: BaziElement.EARTH,
    BaziElement.EARTH: BaziElement.METAL,
    BaziElement.METAL: BaziElement.WATER,
    BaziElement.WATER: BaziElement.WOOD,
}

ELEMENT_CONTROLS = {
    BaziElement.WOOD: BaziElement.EARTH,
    BaziElement.FIRE: BaziElement.METAL,
    BaziElement.EARTH: BaziElement.WATER,
    BaziElement.METAL: BaziElement.WOOD,
    BaziElement.WATER: BaziElement.FIRE,
}


def calculate_day_pillar(dt: Optional[datetime] = None) -> Tuple[str, str]:
    """
    Calculate the BaZi day pillar (stem + branch).
    Uses the standard Chinese calendar calculation.
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    
    # Reference date: Jan 1, 2000 was 甲子 (Jia Zi) day
    # Actually, let's use a known reference: Feb 4, 2000 was 庚辰 day
    reference = datetime(2000, 2, 4, tzinfo=timezone.utc)
    reference_stem_index = 6  # 庚 (Geng)
    reference_branch_index = 4  # 辰 (Chen)
    
    # Days since reference
    delta = dt - reference
    days = delta.days
    
    # Calculate stem and branch
    stem_index = (reference_stem_index + days) % 10
    branch_index = (reference_branch_index + days) % 12
    
    return HEAVENLY_STEMS[stem_index], EARTHLY_BRANCHES[branch_index]


def build_bazi_day_profile(
    natal_bazi: Optional[Dict] = None,
    pattern_family: str = "general",
    dt: Optional[datetime] = None
) -> BaziDayProfile:
    """
    Build BaZi day profile with behavioral implications.
    """
    day_stem, day_branch = calculate_day_pillar(dt)
    
    day_element = STEM_ELEMENTS[day_stem]
    branch_element = BRANCH_ELEMENTS[day_branch]
    
    # Determine interactions
    interactions = []
    ten_gods = []
    strength_shift = "balanced"
    
    # Check element relationships
    # If day element controls something, it's an "output/control" day
    controlled = ELEMENT_CONTROLS[day_element]
    controlling = [k for k, v in ELEMENT_CONTROLS.items() if v == day_element][0]
    producing = ELEMENT_PRODUCES[day_element]
    produced_by = [k for k, v in ELEMENT_PRODUCES.items() if v == day_element][0]
    
    # Determine ten gods based on element relationships
    if day_element == branch_element:
        ten_gods.append("companion")
        interactions.append("support")
        strength_shift = "stronger"
    elif branch_element == produced_by:
        ten_gods.append("resource")
        interactions.append("support")
        strength_shift = "stronger"
    elif branch_element == producing:
        ten_gods.append("output")
        interactions.append("drain")
        strength_shift = "weaker"
    elif branch_element == controlled:
        ten_gods.append("wealth")
        interactions.append("opportunity")
    elif branch_element == controlling:
        ten_gods.append("officer")
        interactions.append("pressure")
        strength_shift = "weaker"
    
    # Element balance description
    element_balance = {
        "dominant": day_element.value,
        "branch": branch_element.value,
        "relationship": "supporting" if strength_shift == "stronger" else "challenging" if strength_shift == "weaker" else "neutral",
    }
    
    # Generate implication
    implication = generate_bazi_implication(day_element, branch_element, ten_gods, interactions)
    
    # Generate pattern link
    pattern_link = generate_bazi_pattern_link(day_element, ten_gods, interactions, pattern_family)
    
    return BaziDayProfile(
        day_element=day_element,
        day_stem=day_stem,
        day_branch=day_branch,
        interactions=interactions,
        ten_gods_active=ten_gods,
        strength_shift=strength_shift,
        element_balance=element_balance,
        implication=implication,
        pattern_link=pattern_link
    )


def generate_bazi_implication(
    day_element: BaziElement,
    branch_element: BaziElement,
    ten_gods: List[str],
    interactions: List[str]
) -> str:
    """Generate behavioral implication from BaZi day."""
    
    ELEMENT_MEANINGS = {
        BaziElement.WOOD: "growth, initiative, planning",
        BaziElement.FIRE: "expression, passion, visibility",
        BaziElement.EARTH: "stability, responsibility, grounding",
        BaziElement.METAL: "precision, discipline, cutting away",
        BaziElement.WATER: "flow, wisdom, adaptability",
    }
    
    TEN_GOD_MEANINGS = {
        "officer": "responsibility, pressure to perform, authority themes",
        "wealth": "opportunity, resources, what you can gain",
        "output": "expression, creativity, giving out energy",
        "resource": "support, nourishment, receiving",
        "companion": "equality, competition, parallel energy",
    }
    
    parts = [f"Today carries {day_element.value} energy—{ELEMENT_MEANINGS[day_element]}."]
    
    if ten_gods:
        god = ten_gods[0]
        parts.append(f"The {god} influence means {TEN_GOD_MEANINGS.get(god, 'activation')}.")
    
    if "pressure" in interactions:
        parts.append("External pressure is present.")
    elif "support" in interactions:
        parts.append("The day supports your direction.")
    elif "drain" in interactions:
        parts.append("Energy may feel depleted.")
    
    return " ".join(parts)


def generate_bazi_pattern_link(
    day_element: BaziElement,
    ten_gods: List[str],
    interactions: List[str],
    pattern_family: str
) -> str:
    """Link BaZi day to current pattern."""
    
    PATTERN_LINKS = {
        "stall": {
            "officer": "Officer energy adds pressure and responsibility—this reinforces the need to pause before acting.",
            "output": "Output energy wants to express, but the pause blocks it—creative tension.",
            "pressure": "The pressure you feel has elemental backing—it's real, not imagined.",
            "support": "The day supports stability, which aligns with pausing to get centered.",
            "default": "Today's element energy influences the timing of your pause.",
        },
        "push_pull": {
            "officer": "Authority pressure is creating part of the pull.",
            "wealth": "Opportunity is creating the pull forward.",
            "default": "The element balance today feeds the back-and-forth.",
        },
        "expression": {
            "output": "Output energy supports expression—the timing favors speaking.",
            "officer": "Officer energy may suppress what wants to be said.",
            "default": "Today's elements influence what can be expressed.",
        },
    }
    
    family_links = PATTERN_LINKS.get(pattern_family, PATTERN_LINKS["stall"])
    
    for god in ten_gods:
        if god in family_links:
            return family_links[god]
    
    for interaction in interactions:
        if interaction in family_links:
            return family_links[interaction]
    
    return family_links.get("default", "The BaZi day influences your current pattern.")


# =============================================================================
# NUMEROLOGY DAY PROFILE
# =============================================================================

@dataclass
class NumerologyDayProfile:
    """
    Numerology daily timing layer.
    """
    universal_day: int  # 1-9
    personal_day: Optional[int]  # 1-9 (requires birth date)
    energy_type: str  # initiation, patience, communication, etc.
    implication: str
    pattern_link: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "universal_day": self.universal_day,
            "personal_day": self.personal_day,
            "energy_type": self.energy_type,
            "implication": self.implication,
            "pattern_link": self.pattern_link,
        }


NUMEROLOGY_MEANINGS = {
    1: {"energy": "initiation", "meaning": "new beginnings, independence, leadership", "action": "start something new"},
    2: {"energy": "patience", "meaning": "cooperation, balance, waiting", "action": "be patient, collaborate"},
    3: {"energy": "communication", "meaning": "expression, creativity, joy", "action": "express yourself"},
    4: {"energy": "stability", "meaning": "foundation, discipline, hard work", "action": "build structure"},
    5: {"energy": "change", "meaning": "freedom, adventure, versatility", "action": "embrace change"},
    6: {"energy": "harmony", "meaning": "responsibility, nurturing, balance", "action": "focus on relationships"},
    7: {"energy": "reflection", "meaning": "introspection, analysis, spirituality", "action": "go inward"},
    8: {"energy": "power", "meaning": "achievement, authority, manifestation", "action": "take charge"},
    9: {"energy": "completion", "meaning": "endings, wisdom, humanitarianism", "action": "let go, complete"},
}


def calculate_universal_day(dt: Optional[datetime] = None) -> int:
    """Calculate universal day number."""
    if dt is None:
        dt = datetime.now(timezone.utc)
    
    # Add all digits of date
    date_str = dt.strftime("%Y%m%d")
    total = sum(int(d) for d in date_str)
    
    # Reduce to single digit
    while total > 9:
        total = sum(int(d) for d in str(total))
    
    return total


def calculate_personal_day(birth_date: datetime, dt: Optional[datetime] = None) -> int:
    """Calculate personal day number."""
    if dt is None:
        dt = datetime.now(timezone.utc)
    
    # Personal year = birth month + birth day + current year
    birth_sum = birth_date.month + birth_date.day
    year_sum = sum(int(d) for d in str(dt.year))
    personal_year = birth_sum + year_sum
    while personal_year > 9:
        personal_year = sum(int(d) for d in str(personal_year))
    
    # Personal day = personal year + current month + current day
    personal_day = personal_year + dt.month + dt.day
    while personal_day > 9:
        personal_day = sum(int(d) for d in str(personal_day))
    
    return personal_day


def build_numerology_day_profile(
    birth_date: Optional[datetime] = None,
    pattern_family: str = "general",
    dt: Optional[datetime] = None
) -> NumerologyDayProfile:
    """Build numerology day profile."""
    
    universal = calculate_universal_day(dt)
    personal = calculate_personal_day(birth_date, dt) if birth_date else None
    
    meaning = NUMEROLOGY_MEANINGS.get(universal, NUMEROLOGY_MEANINGS[1])
    
    # Generate implication
    implication = f"A {meaning['energy']} day—{meaning['meaning']}. {meaning['action'].capitalize()}."
    
    # Generate pattern link
    PATTERN_LINKS = {
        "stall": {
            2: "Patience energy supports your pause—this is a day for waiting, not pushing.",
            4: "Foundation energy supports pausing to build structure.",
            7: "Reflection energy aligns with the pause—go inward.",
            9: "Completion energy suggests the pause is about finishing something.",
            "default": "The day's energy influences your pause timing.",
        },
        "push_pull": {
            5: "Change energy feeds the back-and-forth—things are in flux.",
            6: "Harmony energy seeks balance between the pulls.",
            "default": "The day's vibration influences the push-pull.",
        },
        "expression": {
            3: "Communication energy strongly supports expression today.",
            7: "Reflection energy suggests inner clarity before speaking.",
            "default": "The day's number influences what can be expressed.",
        },
    }
    
    family_links = PATTERN_LINKS.get(pattern_family, PATTERN_LINKS["stall"])
    pattern_link = family_links.get(universal, family_links.get("default", "Numerology influences the timing."))
    
    return NumerologyDayProfile(
        universal_day=universal,
        personal_day=personal,
        energy_type=meaning["energy"],
        implication=implication,
        pattern_link=pattern_link
    )


# =============================================================================
# UNIFIED TIMING PROFILE
# =============================================================================

@dataclass
class UnifiedTimingProfile:
    """
    The SINGLE source of truth for all timing intelligence.
    Homepage, Astrology, HD, BaZi, Numerology all consume this.
    """
    transit_profile: TransitProfile
    bazi_profile: BaziDayProfile
    numerology_profile: NumerologyDayProfile
    
    # Unified summary
    overall_intensity: str  # low, moderate, high
    overall_type: str  # forcing, holding, threshold, opening, closing
    master_summary: str  # What a master would say
    pattern_synthesis: str  # How ALL timing connects to pattern
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "transit": self.transit_profile.to_dict(),
            "bazi": self.bazi_profile.to_dict(),
            "numerology": self.numerology_profile.to_dict(),
            "overall_intensity": self.overall_intensity,
            "overall_type": self.overall_type,
            "master_summary": self.master_summary,
            "pattern_synthesis": self.pattern_synthesis,
        }


def build_unified_timing_profile(
    transit_aspects: List[Dict[str, Any]],
    natal_bazi: Optional[Dict] = None,
    birth_date: Optional[datetime] = None,
    pattern_family: str = "general",
    pattern_title: str = "Today's Pattern",
    dt: Optional[datetime] = None,
    natal_planets: Optional[Dict[str, Any]] = None,  # For house lookup
) -> UnifiedTimingProfile:
    """
    Build the unified timing profile that ALL lenses consume.
    """
    
    # Build individual profiles
    transit = build_transit_profile(transit_aspects, pattern_family, pattern_title, natal_planets)
    bazi = build_bazi_day_profile(natal_bazi, pattern_family, dt)
    numerology = build_numerology_day_profile(birth_date, pattern_family, dt)
    
    # Determine overall intensity
    if transit.intensity == TransitIntensity.HIGH:
        overall_intensity = "high"
    elif transit.intensity == TransitIntensity.MODERATE or "pressure" in bazi.interactions:
        overall_intensity = "moderate"
    else:
        overall_intensity = "low"
    
    # Determine overall type
    if transit.is_forcing:
        overall_type = "forcing"
    elif "threshold" in transit.types or "decision" in transit.domains:
        overall_type = "threshold"
    elif "closure" in transit.types or numerology.energy_type == "completion":
        overall_type = "closing"
    elif "opening" in transit.types or numerology.energy_type == "initiation":
        overall_type = "opening"
    else:
        overall_type = "holding"
    
    # Build master summary
    master_summary = build_master_summary(transit, bazi, numerology, overall_intensity, overall_type)
    
    # Build pattern synthesis
    pattern_synthesis = build_pattern_synthesis(transit, bazi, numerology, pattern_family, pattern_title)
    
    return UnifiedTimingProfile(
        transit_profile=transit,
        bazi_profile=bazi,
        numerology_profile=numerology,
        overall_intensity=overall_intensity,
        overall_type=overall_type,
        master_summary=master_summary,
        pattern_synthesis=pattern_synthesis
    )


def build_master_summary(
    transit: TransitProfile,
    bazi: BaziDayProfile,
    numerology: NumerologyDayProfile,
    overall_intensity: str,
    overall_type: str
) -> str:
    """Build the master practitioner summary."""
    
    parts = []
    
    # Transit lead
    if transit.intensity != TransitIntensity.LOW:
        parts.append(transit.summary)
    
    # BaZi contribution
    if bazi.ten_gods_active:
        god = bazi.ten_gods_active[0]
        if god == "officer":
            parts.append(f"BaZi adds {bazi.day_element.value} officer energy—responsibility and authority pressure.")
        elif god == "wealth":
            parts.append(f"BaZi adds {bazi.day_element.value} wealth energy—opportunity is present.")
        elif god == "output":
            parts.append(f"BaZi adds {bazi.day_element.value} output energy—expression wants to happen.")
    
    # Numerology contribution
    if numerology.energy_type in ["patience", "reflection", "completion"]:
        parts.append(f"Numerology ({numerology.universal_day}) supports {numerology.energy_type}.")
    elif numerology.energy_type in ["initiation", "change", "power"]:
        parts.append(f"Numerology ({numerology.universal_day}) activates {numerology.energy_type}.")
    
    # Combine
    if not parts:
        return "The timing is relatively neutral across all systems."
    
    return " ".join(parts)


def build_pattern_synthesis(
    transit: TransitProfile,
    bazi: BaziDayProfile,
    numerology: NumerologyDayProfile,
    pattern_family: str,
    pattern_title: str
) -> str:
    """Build the synthesis that ties ALL timing to the pattern."""
    
    # Collect all pattern links
    links = [transit.pattern_link, bazi.pattern_link, numerology.pattern_link]
    
    # Build synthesis
    synthesis_parts = []
    
    # Lead statement
    if transit.intensity == TransitIntensity.HIGH:
        synthesis_parts.append(f"There is significant activation across the timing systems today, all connected to '{pattern_title}'.")
    elif transit.intensity == TransitIntensity.MODERATE:
        synthesis_parts.append(f"Multiple timing systems show activation relevant to '{pattern_title}'.")
    else:
        synthesis_parts.append(f"The timing offers subtle support for understanding '{pattern_title}'.")
    
    # Add best link
    if transit.pattern_link:
        synthesis_parts.append(transit.pattern_link)
    
    # Add supporting evidence
    if bazi.pattern_link and len(synthesis_parts) < 3:
        synthesis_parts.append(bazi.pattern_link)
    
    return " ".join(synthesis_parts)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def get_unified_timing(
    user_id: str,
    transit_aspects: List[Dict[str, Any]],
    pattern_family: str = "general",
    pattern_title: str = "Today's Pattern",
    natal_bazi: Optional[Dict] = None,
    birth_date: Optional[datetime] = None,
    dt: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Main entry point for unified timing intelligence.
    
    Returns a complete timing profile that:
    - Homepage uses for diagnosis
    - Astrology Today uses for detail
    - BaZi Today uses for element energy
    - Numerology uses for day vibration
    
    ALL consuming the SAME data.
    """
    
    profile = build_unified_timing_profile(
        transit_aspects=transit_aspects,
        natal_bazi=natal_bazi,
        birth_date=birth_date,
        pattern_family=pattern_family,
        pattern_title=pattern_title,
        dt=dt
    )
    
    logger.info(f"[UnifiedTiming] Built profile: intensity={profile.overall_intensity}, type={profile.overall_type}, transit_types={profile.transit_profile.types}")
    
    return profile.to_dict()
