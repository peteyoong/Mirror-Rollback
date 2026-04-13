"""
Forum HD Mapping Service
========================

Computes "How they map to me" using Human Design channel-completion logic.
Returns human-readable interpretations, not raw HD data.

For two people:
1. Get their active HD gates (design + personality)
2. Find completed channels between them (electromagnetic connections)
3. Generate relational interpretations

"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


# HD Channel definitions with relational themes
HD_CHANNELS = {
    "1-8": {
        "name": "Inspiration",
        "theme": "creative direction, self-expression, leading through example",
        "relational": "creative momentum",
    },
    "2-14": {
        "name": "The Beat",
        "theme": "being called, higher power direction, natural response",
        "relational": "shared calling",
    },
    "3-60": {
        "name": "Mutation",
        "theme": "innovation, accepting limits, new beginnings",
        "relational": "navigating change together",
    },
    "4-63": {
        "name": "Logic",
        "theme": "mental pressure, doubt leading to answers, problem-solving",
        "relational": "thinking through things together",
    },
    "5-15": {
        "name": "Rhythm",
        "theme": "universal timing, natural flow, accepting life's rhythms",
        "relational": "shared flow and timing",
    },
    "6-59": {
        "name": "Intimacy",
        "theme": "emotional bonding, reproduction, breaking barriers",
        "relational": "deep emotional connection",
    },
    "7-31": {
        "name": "The Alpha",
        "theme": "leadership for the future, democratic influence",
        "relational": "natural leadership dynamic",
    },
    "9-52": {
        "name": "Concentration",
        "theme": "focused attention, stillness, determination",
        "relational": "grounding each other",
    },
    "10-20": {
        "name": "Awakening",
        "theme": "authentic expression, being yourself in the moment",
        "relational": "mutual authenticity",
    },
    "10-34": {
        "name": "Exploration",
        "theme": "following conviction, empowered self-direction",
        "relational": "independent connection",
    },
    "10-57": {
        "name": "Perfected Form",
        "theme": "intuitive self-love, survival through authenticity",
        "relational": "intuitive understanding",
    },
    "11-56": {
        "name": "Curiosity",
        "theme": "seeking and sharing experiences, stimulation",
        "relational": "shared curiosity",
    },
    "12-22": {
        "name": "Openness",
        "theme": "social emotional expression, mood and charm",
        "relational": "emotional expression together",
    },
    "13-33": {
        "name": "The Prodigal",
        "theme": "witnessing and sharing experiences, listener and storyteller",
        "relational": "deep listening",
    },
    "16-48": {
        "name": "The Wavelength",
        "theme": "talent expression, depth mastery, skill development",
        "relational": "appreciating each other's depth",
    },
    "17-62": {
        "name": "Acceptance",
        "theme": "organizational thinking, detail and pattern",
        "relational": "thinking things through",
    },
    "18-58": {
        "name": "Judgment",
        "theme": "correction, perfection drive, improving what exists",
        "relational": "growth through feedback",
    },
    "19-49": {
        "name": "Synthesis",
        "theme": "tribal needs, revolution, sensitivity to belonging",
        "relational": "shared values and boundaries",
    },
    "20-34": {
        "name": "Charisma",
        "theme": "busy-ness, thought into action, immediate response",
        "relational": "active energy together",
    },
    "20-57": {
        "name": "The Brainwave",
        "theme": "intuitive knowing in the now, penetrating awareness",
        "relational": "intuitive understanding",
    },
    "21-45": {
        "name": "The Money Line",
        "theme": "materialism, control, willpower for resources",
        "relational": "resource dynamics",
    },
    "23-43": {
        "name": "Structuring",
        "theme": "genius insight, individual knowing, unique perspective",
        "relational": "unique ideas together",
    },
    "24-61": {
        "name": "Awareness",
        "theme": "mental pressure, knowing through mystery, inspiration",
        "relational": "shared inspiration",
    },
    "25-51": {
        "name": "Initiation",
        "theme": "competitive spirit, initiating others, shock and spirit",
        "relational": "challenging each other",
    },
    "26-44": {
        "name": "Surrender",
        "theme": "transmitter, influence through memory and pattern",
        "relational": "influence dynamics",
    },
    "27-50": {
        "name": "Preservation",
        "theme": "nurturing, values, taking care of what matters",
        "relational": "mutual care",
    },
    "28-38": {
        "name": "Struggle",
        "theme": "stubbornness, individual purpose, fighting for meaning",
        "relational": "purpose alignment",
    },
    "29-46": {
        "name": "Discovery",
        "theme": "commitment, embodiment, saying yes to experience",
        "relational": "shared commitment",
    },
    "30-41": {
        "name": "Recognition",
        "theme": "feeling pressure, desire, new emotional experiences",
        "relational": "emotional exploration",
    },
    "32-54": {
        "name": "Transformation",
        "theme": "ambition, transformation, drive for improvement",
        "relational": "growth together",
    },
    "34-57": {
        "name": "Power",
        "theme": "intuitive power, survival energy, in-the-moment response",
        "relational": "instinctive trust",
    },
    "35-36": {
        "name": "Transitoriness",
        "theme": "emotional adventure, seeking new experiences",
        "relational": "adventure together",
    },
    "37-40": {
        "name": "Community",
        "theme": "bargains, loyalty, agreements and expectations",
        "relational": "trust and agreements",
    },
    "39-55": {
        "name": "Emoting",
        "theme": "emotional spirit, provocation, melancholy and abundance",
        "relational": "emotional depth",
    },
    "42-53": {
        "name": "Maturation",
        "theme": "cyclic growth, beginning and completing",
        "relational": "completing together",
    },
    "47-64": {
        "name": "Abstraction",
        "theme": "mental processing, making sense of confusion",
        "relational": "making sense together",
    },
}


# Interpretation templates for different channel types
CHANNEL_INTERPRETATIONS = {
    # High-connection channels
    "37-40": {
        "headline": "You naturally create strong agreements with each other",
        "description": "There's a real sense of loyalty and mutual backing here. Things may feel solid quickly.",
        "what_works": "Trust, mutual support, shared commitment",
        "what_to_watch": "Make expectations explicit. Don't assume alignment means agreement.",
    },
    "6-59": {
        "headline": "Deep emotional intimacy flows between you",
        "description": "There's potential for profound emotional bonding. Barriers tend to dissolve.",
        "what_works": "Vulnerability, emotional honesty, presence",
        "what_to_watch": "Maintain healthy boundaries. Intensity needs space too.",
    },
    "10-20": {
        "headline": "You encourage each other's authenticity",
        "description": "When together, you both feel more permission to be yourselves in the moment.",
        "what_works": "Honest expression, being present, supporting truth",
        "what_to_watch": "Don't confuse authenticity with always agreeing. Different truths can coexist.",
    },
    "13-33": {
        "headline": "You're natural witnesses for each other",
        "description": "One speaks, the other deeply listens. Stories matter here.",
        "what_works": "Deep listening, sharing experiences, holding space",
        "what_to_watch": "Balance who speaks and who listens. Both roles need time.",
    },
    "27-50": {
        "headline": "You naturally care for what matters to each other",
        "description": "There's mutual nurturing here—a sense of looking after shared values.",
        "what_works": "Nurturing, protecting what matters, shared responsibility",
        "what_to_watch": "Don't over-give. Check that care flows both ways.",
    },
    # Default for channels without specific interpretation
    "default": {
        "headline": "There's a natural energetic completion between you",
        "description": "Something clicks when you're together that neither of you has alone.",
        "what_works": "Presence, allowing the dynamic to unfold naturally",
        "what_to_watch": "Notice what emerges. Some completions bring intensity that needs awareness.",
    },
}


# =============================================================================
# ASTROLOGY SYNASTRY — Real cross-aspect relationship signals
# =============================================================================

ELEMENT_MAP = {
    "Aries": "fire", "Leo": "fire", "Sagittarius": "fire",
    "Taurus": "earth", "Virgo": "earth", "Capricorn": "earth",
    "Gemini": "air", "Libra": "air", "Aquarius": "air",
    "Cancer": "water", "Scorpio": "water", "Pisces": "water",
}

MODALITY_MAP = {
    "Aries": "cardinal", "Cancer": "cardinal", "Libra": "cardinal", "Capricorn": "cardinal",
    "Taurus": "fixed", "Leo": "fixed", "Scorpio": "fixed", "Aquarius": "fixed",
    "Gemini": "mutable", "Virgo": "mutable", "Sagittarius": "mutable", "Pisces": "mutable",
}

# Compatible elements for attraction
ELEMENT_ATTRACTION = {
    ("fire", "air"): True, ("air", "fire"): True,
    ("earth", "water"): True, ("water", "earth"): True,
    ("fire", "fire"): True, ("air", "air"): True,
}

# Tension elements
ELEMENT_TENSION = {
    ("fire", "water"): True, ("water", "fire"): True,
    ("earth", "air"): True, ("air", "earth"): True,
}

# Aspect definitions (orb in degrees for synastry)
SYNASTRY_ASPECTS = {
    "conjunction": {"angle": 0, "orb": 8, "nature": "fusion"},
    "opposition": {"angle": 180, "orb": 8, "nature": "polarity"},
    "trine": {"angle": 120, "orb": 7, "nature": "harmony"},
    "square": {"angle": 90, "orb": 7, "nature": "tension"},
    "sextile": {"angle": 60, "orb": 5, "nature": "opportunity"},
}


def compute_astrology_signals(
    chart_a: Dict[str, Any],
    chart_b: Dict[str, Any],
    name_a: str = "You",
    name_b: str = "them",
) -> Optional[Dict[str, List[str]]]:
    """Compute real astrology synastry signals between two charts."""
    astro_a = chart_a.get("astrology", {}) if chart_a else {}
    astro_b = chart_b.get("astrology", {}) if chart_b else {}
    
    planets_a = astro_a.get("planets", {})
    planets_b = astro_b.get("planets", {})
    
    if not planets_a or not planets_b:
        return None
    
    attraction = []
    tension = []
    growth = []
    
    # Helper to get planet data
    def get_planet(planets, name):
        for key in [name, name.capitalize(), name.lower()]:
            if key in planets:
                return planets[key]
        return None
    
    # Core relationship planets
    sun_a = get_planet(planets_a, "Sun")
    moon_a = get_planet(planets_a, "Moon")
    venus_a = get_planet(planets_a, "Venus")
    mars_a = get_planet(planets_a, "Mars")
    
    sun_b = get_planet(planets_b, "Sun")
    moon_b = get_planet(planets_b, "Moon")
    venus_b = get_planet(planets_b, "Venus")
    mars_b = get_planet(planets_b, "Mars")
    
    mercury_a = get_planet(planets_a, "Mercury")
    mercury_b = get_planet(planets_b, "Mercury")
    jupiter_a = get_planet(planets_a, "Jupiter")
    jupiter_b = get_planet(planets_b, "Jupiter")
    saturn_a = get_planet(planets_a, "Saturn")
    saturn_b = get_planet(planets_b, "Saturn")
    
    def sign_of(p):
        return p.get("sign", "") if p else ""
    
    def degree_of(p):
        return float(p.get("degree", 0)) if p else 0
    
    def element_of(sign):
        return ELEMENT_MAP.get(sign, "")
    
    def check_aspect(deg_a, deg_b):
        """Check if two absolute degrees form a synastry aspect."""
        diff = abs(deg_a - deg_b)
        if diff > 180:
            diff = 360 - diff
        for asp_name, asp_def in SYNASTRY_ASPECTS.items():
            if abs(diff - asp_def["angle"]) <= asp_def["orb"]:
                return asp_name, asp_def["nature"]
        return None, None
    
    # Compute absolute degree (sign position * 30 + degree in sign)
    SIGN_ORDER = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                   "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    
    def abs_degree(planet):
        if not planet:
            return 0
        sign = sign_of(planet)
        deg = degree_of(planet)
        idx = SIGN_ORDER.index(sign) if sign in SIGN_ORDER else 0
        return idx * 30 + deg
    
    # ========= SUN-MOON DYNAMICS (primary) =========
    
    # Sun-Moon cross (strongest synastry indicator)
    if sun_a and moon_b:
        asp, nature = check_aspect(abs_degree(sun_a), abs_degree(moon_b))
        if asp == "conjunction" or asp == "trine":
            attraction.append(f"Your core identity naturally resonates with {name_b}'s emotional world — there's an instinctive sense of being understood")
        elif asp == "opposition":
            attraction.append(f"There's a magnetic pull between your sense of self and {name_b}'s emotional nature — opposites that complete each other")
        elif asp == "square":
            tension.append(f"Your identity and {name_b}'s emotional needs can clash — what you express may not land the way you intend")
    
    if sun_b and moon_a:
        asp, nature = check_aspect(abs_degree(sun_b), abs_degree(moon_a))
        if asp == "conjunction" or asp == "trine":
            attraction.append(f"{name_b}'s presence tends to calm or stabilize your emotional state without effort")
        elif asp == "square":
            tension.append(f"{name_b}'s directness can stir your emotional reactions — not always comfortably")
    
    # ========= VENUS DYNAMICS (love language) =========
    
    if venus_a and venus_b:
        el_a = element_of(sign_of(venus_a))
        el_b = element_of(sign_of(venus_b))
        asp, nature = check_aspect(abs_degree(venus_a), abs_degree(venus_b))
        
        if asp in ["conjunction", "trine", "sextile"]:
            attraction.append(f"Your love languages are naturally compatible — what you each value and enjoy overlaps")
        elif asp == "square":
            tension.append(f"You show care differently — what feels like love to one may not register for the other")
        elif (el_a, el_b) in ELEMENT_ATTRACTION:
            attraction.append(f"There's a natural aesthetic and emotional compatibility in what you each find beautiful or meaningful")
    
    # ========= MARS DYNAMICS (drive/conflict) =========
    
    if mars_a and mars_b:
        asp, nature = check_aspect(abs_degree(mars_a), abs_degree(mars_b))
        if asp == "conjunction":
            tension.append(f"You activate each other's drive and assertiveness — energizing, but can escalate into competition")
        elif asp == "opposition":
            growth.append(f"Your action styles are opposite but complementary — together you cover more ground than alone")
        elif asp == "square":
            tension.append(f"You may trigger each other's frustration patterns — especially around pace, timing, or initiative")
        elif asp == "trine":
            attraction.append(f"Your energy and drive naturally flow together — action feels easier when you're aligned")
    
    # ========= VENUS-MARS CROSS (desire) =========
    
    if venus_a and mars_b:
        asp, nature = check_aspect(abs_degree(venus_a), abs_degree(mars_b))
        if asp in ["conjunction", "trine", "opposition"]:
            attraction.append(f"There's a natural pull between your receptive side and {name_b}'s initiative — a classic attraction dynamic")
    
    if venus_b and mars_a:
        asp, nature = check_aspect(abs_degree(venus_b), abs_degree(mars_a))
        if asp in ["conjunction", "trine", "opposition"]:
            attraction.append(f"{name_b}'s softness meets your drive — this creates a dynamic that feels both activating and grounding")
    
    # ========= MERCURY (communication) =========
    
    if mercury_a and mercury_b:
        el_a = element_of(sign_of(mercury_a))
        el_b = element_of(sign_of(mercury_b))
        asp, nature = check_aspect(abs_degree(mercury_a), abs_degree(mercury_b))
        
        if asp in ["conjunction", "trine", "sextile"]:
            attraction.append(f"Your thinking styles are compatible — conversation flows without excessive translation")
        elif asp == "square":
            tension.append(f"You process and communicate differently — misunderstandings come from different mental frameworks, not bad intent")
        elif el_a == el_b:
            attraction.append(f"You think in similar elements — your mental wavelengths overlap naturally")
    
    # ========= SATURN CROSS (growth/structure) =========
    
    if saturn_a and sun_b:
        asp, nature = check_aspect(abs_degree(saturn_a), abs_degree(sun_b))
        if asp in ["conjunction", "square", "opposition"]:
            growth.append(f"You bring structure and accountability to {name_b}'s expression — this can feel grounding or restrictive depending on timing")
    
    if saturn_b and sun_a:
        asp, nature = check_aspect(abs_degree(saturn_b), abs_degree(sun_a))
        if asp in ["conjunction", "square", "opposition"]:
            growth.append(f"{name_b} brings a reality check to your ambitions — uncomfortable but often exactly what's needed")
    
    # ========= JUPITER CROSS (expansion) =========
    
    if jupiter_a and sun_b:
        asp, nature = check_aspect(abs_degree(jupiter_a), abs_degree(sun_b))
        if asp in ["conjunction", "trine", "sextile"]:
            growth.append(f"You naturally expand {name_b}'s sense of what's possible — your optimism lifts them")
    
    if jupiter_b and sun_a:
        asp, nature = check_aspect(abs_degree(jupiter_b), abs_degree(sun_a))
        if asp in ["conjunction", "trine", "sextile"]:
            growth.append(f"{name_b} broadens your perspective in ways you wouldn't access alone")
    
    # ========= ELEMENT OVERVIEW =========
    
    if sun_a and sun_b:
        el_a = element_of(sign_of(sun_a))
        el_b = element_of(sign_of(sun_b))
        if el_a and el_b and not attraction:
            if (el_a, el_b) in ELEMENT_ATTRACTION:
                attraction.append(f"Your core energies ({el_a} and {el_b}) naturally feed each other")
            elif (el_a, el_b) in ELEMENT_TENSION:
                growth.append(f"Your core energies ({el_a} and {el_b}) challenge each other — tension that creates expansion when held well")
    
    # Only return if we have meaningful content
    total = len(attraction) + len(tension) + len(growth)
    if total == 0:
        return None
    
    # Cap to avoid noise
    return {
        "attraction": attraction[:4],
        "tension": tension[:3],
        "growth": growth[:3],
    }


# =============================================================================
# ENNEAGRAM RELATIONSHIP SIGNALS
# =============================================================================

ENNEAGRAM_GIFTS = {
    1: {"gives": "clarity, integrity, and a push toward doing things right", "needs": "permission to be imperfect"},
    2: {"gives": "warmth, attunement, and emotional availability", "needs": "recognition without having to earn it"},
    3: {"gives": "momentum, ambition, and a model of getting things done", "needs": "to be valued beyond their output"},
    4: {"gives": "depth, emotional honesty, and an invitation to feel fully", "needs": "to be seen without being fixed"},
    5: {"gives": "perspective, insight, and a capacity to see what others miss", "needs": "space that isn't interpreted as disconnection"},
    6: {"gives": "loyalty, preparation, and a steady presence in uncertainty", "needs": "trust that isn't constantly re-tested"},
    7: {"gives": "expansion, lightness, and permission to explore possibility", "needs": "to be met in their depth, not just their energy"},
    8: {"gives": "protection, directness, and a force that clears the path", "needs": "vulnerability to be received, not weaponized"},
    9: {"gives": "peace, acceptance, and the ability to hold space for all sides", "needs": "their own voice to matter as much as others'"},
}

ENNEAGRAM_FRICTION_MAP = {
    (7, 1): "Freedom meets standards — one wants options, the other wants correctness. The tension is between expansion and precision.",
    (7, 2): "Lightness meets attachment — one moves fast, the other needs closeness. The gap is about emotional presence vs freedom.",
    (7, 3): "Two forward-movers, but for different reasons — one seeks experience, the other seeks achievement. Alignment requires slowing down.",
    (7, 4): "Optimism meets emotional depth — one reframes, the other insists on feeling fully. The friction is about emotional honesty vs emotional avoidance.",
    (7, 5): "Expansiveness meets containment — one overflows, the other conserves. The tension is about energy management.",
    (7, 6): "Possibility meets caution — one leaps, the other prepares. The friction is about trust in the unknown.",
    (7, 7): "Double expansion — exciting but can lack grounding. The friction appears when reality interrupts the plan.",
    (7, 8): "Two intense forces — one seeks freedom, the other seeks control. The tension is about who sets the direction.",
    (7, 9): "Momentum meets stillness — one pushes for action, the other resists being pushed. The friction is about pace.",
    (8, 1): "Power meets principle — both strong, but one leads with force and the other with correctness.",
    (8, 2): "Intensity meets warmth — the challenge is vulnerability without control.",
    (8, 4): "Raw force meets deep feeling — both intense, but express it completely differently.",
    (8, 9): "Force meets yielding — one pushes, the other absorbs. The tension is about voice and power.",
    (1, 9): "Standards meet acceptance — one corrects, the other accommodates. The friction is about engagement vs peace.",
    (4, 9): "Depth meets calm — one intensifies, the other smooths. The tension is about emotional presence.",
}


def compute_enneagram_signals(
    user_data_a: Dict[str, Any],
    user_data_b: Dict[str, Any],
    name_a: str = "You",
    name_b: str = "them",
) -> Optional[Dict[str, List[str]]]:
    """Compute enneagram relationship signals between two people."""
    enn_a = user_data_a.get("enneagram", {}) if user_data_a else {}
    enn_b = user_data_b.get("enneagram", {}) if user_data_b else {}
    
    core_a = enn_a.get("inferred_core")
    core_b = enn_b.get("inferred_core")
    
    if not core_a or not core_b:
        return None
    
    try:
        core_a = int(core_a)
        core_b = int(core_b)
    except (ValueError, TypeError):
        return None
    
    gifts_a = ENNEAGRAM_GIFTS.get(core_a, {})
    gifts_b = ENNEAGRAM_GIFTS.get(core_b, {})
    
    how_you_help_them = []
    how_they_help_you = []
    friction_pattern = []
    
    if gifts_a.get("gives"):
        how_you_help_them.append(f"You bring {gifts_a['gives']}")
    if gifts_b.get("gives"):
        how_they_help_you.append(f"{name_b} brings {gifts_b['gives']}")
    
    if gifts_b.get("needs"):
        how_you_help_them.append(f"What {name_b} needs most: {gifts_b['needs']}")
    if gifts_a.get("needs"):
        how_they_help_you.append(f"What you need most: {gifts_a['needs']}")
    
    # Friction pattern
    pair = (core_a, core_b)
    reverse_pair = (core_b, core_a)
    
    if pair in ENNEAGRAM_FRICTION_MAP:
        friction_pattern.append(ENNEAGRAM_FRICTION_MAP[pair])
    elif reverse_pair in ENNEAGRAM_FRICTION_MAP:
        friction_pattern.append(ENNEAGRAM_FRICTION_MAP[reverse_pair])
    else:
        if core_a == core_b:
            friction_pattern.append(f"Two {core_a}s together amplify the same patterns — what works doubles, but so do the blind spots.")
    
    return {
        "how_you_help_them": how_you_help_them,
        "how_they_help_you": how_they_help_you,
        "friction_pattern": friction_pattern,
    }


# =============================================================================
# NUMEROLOGY RELATIONSHIP SIGNALS
# =============================================================================

NUMEROLOGY_MEANINGS = {
    1: "independence, leadership, initiation",
    2: "partnership, sensitivity, cooperation",
    3: "expression, creativity, communication",
    4: "structure, stability, foundation",
    5: "freedom, change, adaptability",
    6: "responsibility, nurturing, harmony",
    7: "introspection, analysis, spiritual depth",
    8: "power, abundance, authority",
    9: "compassion, completion, universal understanding",
    11: "intuition, spiritual insight, heightened sensitivity",
    22: "master builder, large-scale vision, practical idealism",
    33: "master teacher, healing through compassion, selfless service",
}


def compute_numerology_signals(
    chart_a: Dict[str, Any],
    chart_b: Dict[str, Any],
    name_a: str = "You",
    name_b: str = "them",
) -> Optional[Dict[str, List[str]]]:
    """Compute numerology relationship signals. Returns None if not meaningful."""
    num_a = chart_a.get("numerology", {}) if chart_a else {}
    num_b = chart_b.get("numerology", {}) if chart_b else {}
    
    if not num_a or not num_b:
        return None
    
    lp_a = num_a.get("life_path", {}).get("number")
    lp_b = num_b.get("life_path", {}).get("number")
    exp_a = num_a.get("expression", {}).get("number")
    exp_b = num_b.get("expression", {}).get("number")
    soul_a = num_a.get("soul_urge", {}).get("number")
    soul_b = num_b.get("soul_urge", {}).get("number")
    
    if not lp_a or not lp_b:
        return None
    
    themes = []
    
    # Check for shared numbers (strong resonance)
    all_a = set(filter(None, [lp_a, exp_a, soul_a]))
    all_b = set(filter(None, [lp_b, exp_b, soul_b]))
    shared = all_a & all_b
    
    if shared:
        for num in shared:
            meaning = NUMEROLOGY_MEANINGS.get(num, "")
            if meaning:
                themes.append(f"You share the number {num} ({meaning}) — this creates natural resonance in how you approach life")
    
    # Check if one person's Life Path matches another's Expression/Soul
    if lp_a and lp_a in all_b and lp_a not in shared:
        meaning = NUMEROLOGY_MEANINGS.get(lp_a, "")
        themes.append(f"Your Life Path ({lp_a}) aligns with something core in {name_b} — {meaning}")
    
    if lp_b and lp_b in all_a and lp_b not in shared:
        meaning = NUMEROLOGY_MEANINGS.get(lp_b, "")
        themes.append(f"{name_b}'s Life Path ({lp_b}) aligns with something core in you — {meaning}")
    
    # Master numbers
    master_a = [n for n in all_a if n in (11, 22, 33)]
    master_b = [n for n in all_b if n in (11, 22, 33)]
    
    if master_a and master_b:
        themes.append(f"Both of you carry master numbers ({', '.join(str(n) for n in master_a)} and {', '.join(str(n) for n in master_b)}) — this connection operates at a higher frequency than most")
    
    # Complementary numbers (1+2, 3+4, 5+6, 7+8)
    complements = {(1,2), (2,1), (3,4), (4,3), (5,6), (6,5), (7,8), (8,7)}
    if lp_a and lp_b:
        reduced_a = lp_a if lp_a < 10 else (lp_a % 10 or lp_a // 10)
        reduced_b = lp_b if lp_b < 10 else (lp_b % 10 or lp_b // 10)
        if (reduced_a, reduced_b) in complements:
            themes.append(f"Your core numbers are natural complements — one initiates what the other receives")
    
    # Only return if truly meaningful (2+ themes)
    if len(themes) < 2:
        return None
    
    return {"themes": themes[:4]}



def get_user_gates(user_data: Dict[str, Any], chart_data: Dict[str, Any] = None) -> List[int]:
    """
    Extract all active gates from a user's Human Design data.
    Prioritizes chart_data if available (from charts collection).
    """
    gates = set()
    
    # Primary source: charts collection data
    if chart_data:
        hd = chart_data.get("human_design", {})
        
        # Active gates (computed list)
        active_gates = hd.get("active_gates", [])
        for g in active_gates:
            if isinstance(g, int):
                gates.add(g)
            elif isinstance(g, str):
                try:
                    gates.add(int(g))
                except:
                    pass
        
        # Extract from personality/design sections as backup
        for section in ["personality", "design"]:
            section_data = hd.get(section, {})
            if isinstance(section_data, dict):
                for planet_data in section_data.values():
                    if isinstance(planet_data, dict):
                        gate_info = planet_data.get("gate", {})
                        if isinstance(gate_info, dict):
                            gate_num = gate_info.get("gate")
                            if gate_num:
                                gates.add(int(gate_num))
        
        # Also check defined_channels
        channels = hd.get("defined_channels", [])
        for c in channels:
            if isinstance(c, dict):
                g1 = c.get("gate1")
                g2 = c.get("gate2")
                if g1:
                    gates.add(int(g1))
                if g2:
                    gates.add(int(g2))
    
    # Fallback: user data
    if not gates:
        hd_data = user_data.get("human_design", {})
        
        # Try different HD data formats from user
        if "gates" in hd_data:
            gate_list = hd_data.get("gates", [])
            if isinstance(gate_list, list):
                for g in gate_list:
                    if isinstance(g, dict):
                        gate_num = g.get("gate", g.get("number"))
                        if gate_num:
                            gates.add(int(gate_num))
                    elif isinstance(g, (int, str)):
                        try:
                            gates.add(int(g))
                        except:
                            pass
    
    return list(gates)


def find_completed_channels(gates_a: List[int], gates_b: List[int]) -> List[Dict[str, Any]]:
    """
    Find channels completed between two people.
    A channel is completed when one person has one gate and the other has the partner gate.
    """
    completed = []
    
    gates_a_set = set(gates_a)
    gates_b_set = set(gates_b)
    
    for channel_key, channel_data in HD_CHANNELS.items():
        gate_1, gate_2 = [int(g) for g in channel_key.split("-")]
        
        # Check if channel is completed between A and B
        # Case 1: A has gate_1, B has gate_2
        if gate_1 in gates_a_set and gate_2 in gates_b_set:
            completed.append({
                "channel_id": channel_key,
                "name": channel_data["name"],
                "theme": channel_data["theme"],
                "relational": channel_data.get("relational", "connection"),
                "gate_a": gate_1,
                "gate_b": gate_2,
            })
        # Case 2: A has gate_2, B has gate_1
        elif gate_2 in gates_a_set and gate_1 in gates_b_set:
            completed.append({
                "channel_id": channel_key,
                "name": channel_data["name"],
                "theme": channel_data["theme"],
                "relational": channel_data.get("relational", "connection"),
                "gate_a": gate_2,
                "gate_b": gate_1,
            })
    
    return completed


def generate_mapping_interpretation(
    current_user_name: str,
    member_name: str,
    completed_channels: List[Dict[str, Any]],
    chart_a: Dict[str, Any] = None,
    chart_b: Dict[str, Any] = None,
    user_a: Dict[str, Any] = None,
    user_b: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Generate 3-LAYER relationship interpretation.
    
    Layer 1: STORY (emotional hook)
    Layer 2: PATTERNS (behavioral recognition)
    Layer 3: SIGNALS (HD proof + placeholders)
    """
    
    if not completed_channels:
        return {
            "member_name": member_name,
            "story": {
                "headline": "Your connection runs on intention, not automatic pull.",
                "summary": "You don't have energetic completions pulling you together unconsciously. That means what exists between you is built — through choice, presence, and attention. That's not less real. It's just different.",
            },
            "patterns": {
                "what_happens": [
                    "Connection requires more conscious effort — it doesn't just flow automatically",
                    "You may notice periods of natural distance that aren't about disconnection",
                ],
                "tensions": [
                    "One of you may feel like they're doing more work to maintain the connection",
                ],
                "gifts": [
                    "What you build together is fully yours — not driven by unconscious energetic pull",
                ],
            },
            "signals": {
                "human_design": [],
                "astrology": [],
                "bazi": [],
                "enneagram": [],
                "numerology": [],
            },
            "channel_count": 0,
            "strength_score": 0,
        }
    
    channel_count = len(completed_channels)
    
    # =========================================================================
    # LAYER 1: STORY — Emotional, sharp, specific to connection type
    # =========================================================================
    
    # Categorize connection themes
    themes = [c["relational"] for c in completed_channels]
    channel_ids = [c["channel_id"] for c in completed_channels]
    
    # Check for specific powerful combos
    has_intimacy = "6-59" in channel_ids
    has_community = "37-40" in channel_ids
    has_authenticity = "10-20" in channel_ids
    has_power = "34-57" in channel_ids
    has_listening = "13-33" in channel_ids
    has_money = "21-45" in channel_ids
    has_adventure = "35-36" in channel_ids
    
    if channel_count >= 4:
        if has_intimacy and has_community:
            story_headline = "This connection runs deep and wide — it touches both your emotional core and your sense of belonging."
            story_summary = f"With {channel_count} active channels between you, this isn't a surface-level dynamic. You complete each other in ways that create real pull — the kind where silence feels full and distance feels temporary."
        elif has_intimacy:
            story_headline = "There's an intensity here that most connections don't reach."
            story_summary = f"You have {channel_count} energetic completions pulling you together. The intimacy channel means barriers dissolve faster than usual between you. That's powerful — and sometimes overwhelming."
        else:
            story_headline = "You don't just connect — you activate each other."
            story_summary = f"With {channel_count} electromagnetic completions, your presence changes something in each other. This is a connection that runs on energy, not just words."
    elif channel_count == 3:
        story_headline = "There's a triangulation of energy here that creates real depth."
        story_summary = "Three connection points means this dynamic has range — it touches different parts of your life and creates a pull that's hard to ignore."
    elif channel_count == 2:
        story_headline = "Two clear lines of energy run between you."
        story_summary = "This isn't a single-note connection. You complete each other in two distinct ways, which means the dynamic has both depth and texture."
    else:
        # Single channel — use specific interpretation
        primary = completed_channels[0]
        ch_data = CHANNEL_INTERPRETATIONS.get(primary["channel_id"], CHANNEL_INTERPRETATIONS["default"])
        story_headline = ch_data["headline"]
        story_summary = ch_data["description"]
    
    # =========================================================================
    # LAYER 2: PATTERNS — Behavioral, "this is EXACTLY what happens"
    # =========================================================================
    
    what_happens = []
    tensions = []
    gifts = []
    
    # Generate behavioral patterns based on actual channels
    for c in completed_channels:
        cid = c["channel_id"]
        rel = c["relational"]
        
        # What happens — observable behaviors
        WHAT_HAPPENS_MAP = {
            "6-59": "You tend to bypass each other's emotional walls faster than either of you expected",
            "37-40": "There's an unspoken agreement between you — a sense of loyalty that formed before you discussed it",
            "10-20": "When you're together, you both become more openly yourselves — less filtering, more truth",
            "13-33": "One of you speaks while the other deeply absorbs — and the listener often sees more than the speaker realizes",
            "27-50": "You naturally look out for what matters to each other — sometimes before being asked",
            "21-45": "Money, resources, or control dynamics surface between you — not always comfortably",
            "35-36": "You pull each other toward new experiences — sometimes before either of you is ready",
            "5-15": "Your natural rhythms and timing sync up in ways that feel effortless",
            "34-57": "There's an instinctive trust between you that doesn't need explanation",
            "32-54": "You push each other to grow — sometimes gently, sometimes through friction",
            "39-55": "Emotions run deep and unpredictable between you — rich but not always comfortable",
            "28-38": "You challenge each other's sense of purpose — which can feel like pressure or liberation",
        }
        
        if cid in WHAT_HAPPENS_MAP:
            what_happens.append(WHAT_HAPPENS_MAP[cid])
        else:
            what_happens.append(f"There's a natural completion in {rel} that creates pull between you")
        
        # Tensions — where friction shows up
        TENSION_MAP = {
            "6-59": "The emotional depth can feel overwhelming — one of you may pull back when it gets too close",
            "37-40": "Unspoken expectations can build up — what feels 'agreed' may not actually be shared",
            "10-20": "Raw authenticity can accidentally land as bluntness — timing matters",
            "21-45": "Control or resource dynamics may create a power imbalance if not named",
            "35-36": "The drive for novelty can destabilize what's already working",
            "32-54": "Growth-pushing can feel like criticism if the intention isn't clear",
            "39-55": "Emotional provocation — one of you may trigger deep feelings in the other without meaning to",
        }
        
        if cid in TENSION_MAP:
            tensions.append(TENSION_MAP[cid])
        
        # Gifts — how you help each other grow
        GIFT_MAP = {
            "6-59": f"{member_name} helps you access emotional depth you'd normally protect",
            "37-40": f"Together you create a sense of belonging that neither of you has alone",
            "10-20": f"{member_name} gives you permission to be more authentically yourself",
            "13-33": f"One of you holds space that allows the other to process and release",
            "27-50": f"You protect and nurture what matters to each other — without being asked",
            "5-15": f"Your shared rhythm creates a container of ease that other relationships don't have",
            "34-57": f"There's an instinctive safety between you that allows faster trust",
            "35-36": f"{member_name} pulls you toward experiences you'd avoid alone — and that expands you",
        }
        
        if cid in GIFT_MAP:
            gifts.append(GIFT_MAP[cid])
    
    # Ensure minimum content
    if not what_happens:
        what_happens = [f"There's a natural energetic pull between you that activates when you're together"]
    if not tensions:
        tensions = ["The intensity of the connection can create pressure if expectations aren't aligned"]
    if not gifts:
        gifts = [f"Together you access something neither of you has alone — that's the gift of completion"]
    
    # Limit to best items
    what_happens = what_happens[:4]
    tensions = tensions[:3]
    gifts = gifts[:3]
    
    # =========================================================================
    # LAYER 3: SIGNALS — Multi-lens proof layer
    # =========================================================================
    
    # Build HD signals with 1-line plain language translations
    hd_signals = []
    for c in completed_channels:
        cid = c["channel_id"]
        
        # Plain language translation per channel
        TRANSLATION_MAP = {
            "5-15": "Your natural rhythms align — you feel 'in sync' without trying",
            "6-59": "You break through each other's emotional walls naturally",
            "21-45": "Resources, money, or control become a live wire between you",
            "35-36": "You push each other toward adventure and new emotional territory",
            "37-40": "Loyalty and mutual agreements form fast — and feel binding",
            "10-20": "You give each other permission to be more real",
            "13-33": "Deep listening flows naturally — one speaks, the other truly hears",
            "27-50": "You instinctively protect what matters to each other",
            "34-57": "There's a gut-level trust that doesn't need words",
            "32-54": "You drive each other toward growth — sometimes uncomfortably",
            "39-55": "Emotions run deeper and more unpredictably between you",
            "28-38": "You challenge each other's sense of meaning and purpose",
            "18-58": "You push each other toward improvement — through honest feedback",
            "12-22": "Emotional expression between you is amplified — moods are shared",
        }
        
        translation = TRANSLATION_MAP.get(cid, f"Energy flows between your {c['relational']} — this shapes how you interact")
        
        hd_signals.append({
            "channel": cid,
            "name": f"Channel of {c['name']}",
            "theme": c["theme"],
            "translation": translation,
            "your_gate": c["gate_a"],
            "their_gate": c["gate_b"],
        })
    
    # Compute multi-lens signals (real data, not placeholders)
    astrology_signals = compute_astrology_signals(chart_a, chart_b, current_user_name, member_name) if chart_a and chart_b else None
    enneagram_signals = compute_enneagram_signals(user_a, user_b, current_user_name, member_name) if user_a and user_b else None
    numerology_signals = compute_numerology_signals(chart_a, chart_b, current_user_name, member_name) if chart_a and chart_b else None
    # BaZi: only compute if both have bazi data
    bazi_signals = None  # Will be populated when BaZi data is available
    
    return {
        "member_name": member_name,
        # V2 3-LAYER STRUCTURE
        "story": {
            "headline": story_headline,
            "summary": story_summary,
        },
        "patterns": {
            "what_happens": what_happens,
            "tensions": tensions,
            "gifts": gifts,
        },
        "signals": {
            "human_design": hd_signals,
            "astrology": astrology_signals,
            "bazi": bazi_signals,
            "enneagram": enneagram_signals,
            "numerology": numerology_signals,
        },
        # BACKWARD COMPAT (old fields still available)
        "headline": story_headline,
        "description": story_summary,
        "what_works": ", ".join(gifts[:2]) if gifts else "Presence, allowing the dynamic to unfold naturally",
        "what_to_watch": ". ".join(tensions[:2]) if tensions else "Notice what emerges. Some completions bring intensity that needs awareness.",
        "why_this_happens": hd_signals,
        "channel_count": channel_count,
        "strength_score": min(channel_count * 20 + 10, 100),
    }


async def get_forum_member_mappings(
    db,
    forum_id: str,
    current_user_id: str,
) -> List[Dict[str, Any]]:
    """
    Get "How they map to me" for all forum members relative to current user.
    Returns sorted list by strength/relevance.
    """
    try:
        # Get forum
        from bson import ObjectId
        forum = await db.forums.find_one({"_id": ObjectId(forum_id)})
        if not forum:
            logger.error(f"[ForumMapping] Forum {forum_id} not found")
            return []
        
        # Get current user data
        current_user = await db.users.find_one({"_id": ObjectId(current_user_id)})
        if not current_user:
            logger.error(f"[ForumMapping] Current user {current_user_id} not found")
            return []
        
        # Get current user's chart (HD data)
        current_chart = await db.charts.find_one({"user_id": current_user_id})
        current_user_gates = get_user_gates(current_user, current_chart)
        current_user_name = current_user.get("name", "You")
        
        logger.info(f"[ForumMapping] User {current_user_id[:8]} has {len(current_user_gates)} gates: {current_user_gates[:5]}...")
        
        # Get all forum members from forum_members collection
        memberships = await db.forum_members.find({
            "forum_id": forum_id,
            "status": "active"
        }).to_list(100)
        
        mappings = []
        
        for membership in memberships:
            member_id = membership.get("user_id")
            if member_id == current_user_id:
                continue  # Skip self
            
            # Get member data
            member = await db.users.find_one({"_id": ObjectId(str(member_id))})
            if not member:
                continue
            
            member_name = member.get("name", "Unknown")
            
            # Get member's chart (HD data)
            member_chart = await db.charts.find_one({"user_id": str(member_id)})
            member_gates = get_user_gates(member, member_chart)
            
            logger.info(f"[ForumMapping] Member {member_name} has {len(member_gates)} gates: {member_gates[:5]}...")
            
            # Find completed channels
            completed_channels = find_completed_channels(current_user_gates, member_gates)
            
            # Generate interpretation with multi-lens signals
            mapping = generate_mapping_interpretation(
                current_user_name=current_user_name,
                member_name=member_name,
                completed_channels=completed_channels,
                chart_a=current_chart,
                chart_b=member_chart,
                user_a=current_user,
                user_b=member,
            )
            mapping["member_id"] = str(member_id)
            
            mappings.append(mapping)
            
            logger.info(f"[ForumMapping] {current_user_name} ↔ {member_name}: {len(completed_channels)} channels")
        
        # Sort by strength score (most connections first)
        mappings.sort(key=lambda x: x["strength_score"], reverse=True)
        
        return mappings
        
    except Exception as e:
        logger.error(f"[ForumMapping] Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []
