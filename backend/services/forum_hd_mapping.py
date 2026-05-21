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
        "theme": "resources, stewardship, responsibility, and the will to provide",
        "relational": "resources and responsibility",
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
    "21-45": {
        # The Money Line — gates 21 (control of resources) + 45 (gatherer of
        # resources).  Founders/operators feel this one in the material world:
        # provision, capability, ambition, who carries what.
        "headline": "Resources, direction, and responsibility quickly become shared territory",
        "description": (
            "Together, you naturally start organizing resources, direction, "
            "and responsibility — this connection tends to move toward "
            "building something tangible. Provision and stewardship become "
            "a live thread between you, and the question of who carries what "
            "surfaces early."
        ),
        "what_works": (
            "Naming what each of you brings — capital, capability, time, "
            "follow-through — before the imbalance gets quiet. Visible "
            "agreements about who provides, who decides, who executes."
        ),
        "what_to_watch": (
            "Unspoken contracts about who provides and who directs. Surface "
            "them while they're still small — by the time it's resentment, "
            "the conversation is much harder."
        ),
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


def _resolve_pronouns(pronouns_b: Dict[str, str] = None) -> tuple:
    """Resolve he/him/his pronouns from pronouns_b dict. Defaults to they/them."""
    if pronouns_b:
        return pronouns_b.get("he", "they"), pronouns_b.get("him", "them"), pronouns_b.get("his", "their")
    return "they", "them", "their"


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
    pronouns_b: Dict[str, str] = None,
) -> Optional[Dict[str, List[str]]]:
    """Compute HIGH-CONVICTION astrology synastry signals. Only uses Sun-Moon, Venus-Mars,
    Venus-Venus, Mars-Mars, Saturn-personal, Mercury-Mercury. Each signal must describe
    observable interaction behavior, not abstract traits."""
    astro_a = chart_a.get("astrology", {}) if chart_a else {}
    astro_b = chart_b.get("astrology", {}) if chart_b else {}
    
    planets_a = astro_a.get("planets", {})
    planets_b = astro_b.get("planets", {})
    
    if not planets_a or not planets_b:
        return None
    
    attraction = []
    tension = []
    growth = []
    
    def get_planet(planets, name):
        for key in [name, name.capitalize(), name.lower()]:
            if key in planets:
                return planets[key]
        return None
    
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
    saturn_a = get_planet(planets_a, "Saturn")
    saturn_b = get_planet(planets_b, "Saturn")
    
    def sign_of(p):
        return p.get("sign", "") if p else ""
    def degree_of(p):
        return float(p.get("degree", 0)) if p else 0
    
    SIGN_ORDER = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                   "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    
    def abs_degree(planet):
        if not planet: return 0
        sign = sign_of(planet)
        idx = SIGN_ORDER.index(sign) if sign in SIGN_ORDER else 0
        return idx * 30 + degree_of(planet)
    
    def check_aspect(deg_a, deg_b):
        diff = abs(deg_a - deg_b)
        if diff > 180: diff = 360 - diff
        for asp_name, asp_def in SYNASTRY_ASPECTS.items():
            if abs(diff - asp_def["angle"]) <= asp_def["orb"]:
                return asp_name
        return None
    
    # ===== SUN-MOON CROSS (strongest synastry indicator) =====
    if sun_a and moon_b:
        asp = check_aspect(abs_degree(sun_a), abs_degree(moon_b))
        if asp == "conjunction":
            attraction.append(f"You tend to understand {name_b}'s emotional reactions before she explains them — which creates closeness but can blur boundaries")
        elif asp == "trine":
            attraction.append(f"When {name_b} is upset, you instinctively know how to meet it — there's an ease in emotional repair between you")
        elif asp == "opposition":
            attraction.append(f"You and {name_b} are drawn to each other's differences — the pull is magnetic, but keeping balance requires awareness")
        elif asp == "square":
            tension.append(f"What you express and what {name_b} needs emotionally don't always line up — the mismatch creates friction that feels personal even when it isn't")
    
    if sun_b and moon_a:
        asp = check_aspect(abs_degree(sun_b), abs_degree(moon_a))
        if asp in ("conjunction", "trine"):
            attraction.append(f"{name_b}'s presence settles something in you — you feel less reactive and more grounded when she's steady")
        elif asp == "square":
            tension.append(f"{name_b} can trigger emotional reactions in you that feel disproportionate — it's not about what was said, it's about what was activated")
    
    # ===== VENUS-VENUS (shared values / love language) =====
    if venus_a and venus_b:
        asp = check_aspect(abs_degree(venus_a), abs_degree(venus_b))
        if asp == "conjunction":
            attraction.append(f"You value the same things in a relationship — comfort, beauty, ease tend to look the same to both of you")
        elif asp == "trine" or asp == "sextile":
            attraction.append(f"How you each show love is naturally received by the other — gestures land without needing translation")
        elif asp == "square":
            tension.append(f"You show care differently — one of you may feel unloved while the other feels unappreciated, even when both are trying")
    
    # ===== VENUS-MARS CROSS (desire / attraction) =====
    if venus_a and mars_b:
        asp = check_aspect(abs_degree(venus_a), abs_degree(mars_b))
        if asp in ("conjunction", "trine", "opposition"):
            attraction.append(f"There's a pull where {name_b}'s initiative meets your receptivity — one pursues while the other draws in, and that dance sustains itself")
    
    if venus_b and mars_a:
        asp = check_aspect(abs_degree(venus_b), abs_degree(mars_a))
        if asp in ("conjunction", "trine", "opposition"):
            attraction.append(f"Your drive activates something soft in {name_b} — she opens up in response to your directness, not despite it")
    
    # ===== MOON-MOON (emotional resonance) =====
    if moon_a and moon_b:
        asp = check_aspect(abs_degree(moon_a), abs_degree(moon_b))
        if asp == "conjunction":
            attraction.append(f"Your emotional instincts are wired the same way — you react to things at the same speed and in the same register, which creates a wordless understanding")
        elif asp == "trine":
            attraction.append(f"You process emotions in compatible ways — what soothes one tends to soothe the other, which makes emotional repair easier")
        elif asp == "opposition":
            tension.append(f"Your emotional needs pull in opposite directions — what settles you can unsettle {name_b}, and vice versa")
        elif asp == "square":
            tension.append(f"Your emotional rhythms clash — one needs space when the other needs closeness, creating a mismatch that feels personal")
    
    # ===== MARS-MARS (conflict style) =====
    if mars_a and mars_b:
        asp = check_aspect(abs_degree(mars_a), abs_degree(mars_b))
        if asp == "conjunction":
            tension.append(f"You fight the same way — when conflict happens, you escalate in sync rather than balancing each other out")
        elif asp == "square":
            tension.append(f"Your action styles clash — one pushes while the other resists, and the timing mismatch creates real frustration")
        elif asp == "trine":
            attraction.append(f"When you need to act together — decide, move, handle something — your energy aligns without negotiation")
        elif asp == "opposition":
            growth.append(f"You approach problems from opposite directions, which means together you cover angles neither would alone — if you stop competing")
    
    # ===== MERCURY-MERCURY (communication) =====
    if mercury_a and mercury_b:
        asp = check_aspect(abs_degree(mercury_a), abs_degree(mercury_b))
        if asp == "conjunction" or asp == "trine":
            attraction.append(f"Conversations between you flow — you finish each other's thoughts or arrive at the same conclusion from different starting points")
        elif asp == "square":
            tension.append(f"You process information differently enough that the same conversation can feel productive to one and circular to the other")
    
    # ===== SATURN CROSS (growth / structure) =====
    if saturn_a and sun_b:
        asp = check_aspect(abs_degree(saturn_a), abs_degree(sun_b))
        if asp in ("conjunction", "square", "opposition"):
            growth.append(f"You hold {name_b} to a higher standard than most people do — she grows because of it, but may resist in the moment")
    
    if saturn_b and sun_a:
        asp = check_aspect(abs_degree(saturn_b), abs_degree(sun_a))
        if asp in ("conjunction", "square", "opposition"):
            growth.append(f"{name_b} grounds your ambition in reality — what she reflects back isn't what you want to hear, but it's usually what you need")
    
    # ===== QUALITY GATE: require at least 1 real signal =====
    total = len(attraction) + len(tension) + len(growth)
    if total < 1:
        return None
    
    result = {}
    if attraction: result["attraction"] = attraction[:2]
    if tension: result["tension"] = tension[:2]
    if growth: result["growth"] = growth[:2]
    
    return result if result else None


# =============================================================================
# ENNEAGRAM RELATIONSHIP SIGNALS
# =============================================================================

ENNEAGRAM_RELATIONAL = {
    1: {
        "unlocks_in_other": "a clearer sense of what actually matters — your standards cut through their noise",
        "needs_from_other": "permission to let go of getting it right, without feeling like they've failed you",
        "core_fear": "being wrong or morally flawed",
    },
    2: {
        "unlocks_in_other": "a feeling of being genuinely cared for — you attune to what they need before they ask",
        "needs_from_other": "to be seen for who they are, not just what they give",
        "core_fear": "being unwanted or unworthy of love",
    },
    3: {
        "unlocks_in_other": "forward motion and a belief that things can actually get done",
        "needs_from_other": "to be valued for who they are when they stop performing — not just for what they produce",
        "core_fear": "being worthless or without inherent value",
    },
    4: {
        "unlocks_in_other": "emotional depth and honesty — you name what others skirt around",
        "needs_from_other": "to be received without being fixed — their pain is not a problem to solve",
        "core_fear": "having no identity or personal significance",
    },
    5: {
        "unlocks_in_other": "a quieter, more observant perspective — you see what others miss because you're not in the fray",
        "needs_from_other": "space that isn't interpreted as pulling away — their withdrawal is how they refuel",
        "core_fear": "being useless, incapable, or overwhelmed",
    },
    6: {
        "unlocks_in_other": "a steadiness in uncertainty — you show up when others leave",
        "needs_from_other": "consistency that proves itself over time — their trust is earned, not given",
        "core_fear": "being without support or guidance",
    },
    7: {
        "unlocks_in_other": "possibilities they wouldn't consider alone — you expand what feels available",
        "needs_from_other": "to be met in their depth, not just their energy — the lightness hides something real",
        "core_fear": "being trapped in pain or deprivation",
    },
    8: {
        "unlocks_in_other": "a sense that someone has their back — you clear the path and don't flinch",
        "needs_from_other": "for their vulnerability to be held, not used — the softness under the strength is the real person",
        "core_fear": "being controlled or harmed by others",
    },
    9: {
        "unlocks_in_other": "a calm that isn't performance — you genuinely accept what's here",
        "needs_from_other": "to be asked what they want, and for that answer to actually matter",
        "core_fear": "loss, separation, or conflict that fragments connection",
    },
}

ENNEAGRAM_FRICTION_MAP = {
    (7, 3): "You open doors she wants to walk through — but you struggle to stay in one room long enough for her to finish what she started. She builds toward outcomes; you chase the next spark. The friction is between commitment to a path and freedom to explore.",
    (7, 4): "You reframe what she insists on feeling. She needs to sit in it; you need to move past it. The friction: emotional honesty vs emotional escape.",
    (7, 1): "You want options; she wants correctness. Your spontaneity feels irresponsible to her. Her standards feel limiting to you.",
    (7, 2): "You run toward experience; she runs toward people. The gap: you may not circle back when she needs closeness.",
    (7, 5): "You overflow; she conserves. Your energy can feel intrusive to her retreat. Her silence can feel like rejection of your world.",
    (7, 6): "You leap; she prepares. Your optimism feels reckless to her. Her caution feels like a cage to you.",
    (7, 7): "Double expansion, double avoidance. Everything is exciting until something real needs to be faced.",
    (7, 8): "Two big energies — you seek freedom, she seeks control. Who sets the direction becomes the recurring argument.",
    (7, 9): "You push for action; she pushes back by going still. Your energy overwhelms her pace. Her passivity frustrates yours.",
    (3, 1): "She holds standards; you hold results. The gap: you cut corners she can't accept.",
    (3, 2): "She gives to be needed; you perform to be valued. Both strategies avoid the same question: 'Am I enough without this?'",
    (3, 4): "She wants depth; you want progress. Your efficiency dismisses her process. Her intensity slows your momentum.",
    (3, 5): "She observes; you perform. She needs space you read as disengagement. You need audience she reads as surface.",
    (3, 7): "Both forward-movers. The friction: one seeks achievement, the other seeks experience. Alignment requires slowing down.",
    (3, 8): "Both powerful. The tension is about who leads — and neither backs down easily.",
    (3, 9): "You push forward; she accommodates until she doesn't. Then the resentment surfaces all at once.",
    (8, 1): "Power meets principle — you lead with force, she leads with correctness. Collision happens when both feel right.",
    (8, 2): "Your intensity meets her warmth. The challenge: vulnerability without control.",
    (8, 9): "You push; she absorbs. Eventually what she absorbed comes back, and neither of you is ready for it.",
    (1, 9): "She accepts; you correct. Your standards feel like criticism of her nature. Her peace feels like complacency to you.",
    (4, 9): "She goes still; you go deep. Your intensity can feel like an assault on her calm.",
}


def compute_enneagram_signals(
    user_data_a: Dict[str, Any],
    user_data_b: Dict[str, Any],
    name_a: str = "You",
    name_b: str = "them",
    pronouns_b: Dict[str, str] = None,
) -> Optional[Dict[str, List[str]]]:
    """Compute DIRECTIONAL enneagram relationship signals. Requires both types."""
    # CANONICAL RESOLUTION — use the shared helper so this function honours
    # the same fallback chain (enneagram_type → enneagram.inferred_core →
    # enneagram.core → legacy enneagram) as Forum Dynamics + Member Lens.
    try:
        from services.enneagram_source import get_user_enneagram
    except Exception:
        from enneagram_source import get_user_enneagram  # type: ignore

    core_a = get_user_enneagram(user_data_a)
    core_b = get_user_enneagram(user_data_b)

    if not core_a or not core_b:
        logger.debug(f"[Enneagram] Missing: A={core_a}, B={core_b}")
        return None

    # Wing (for metadata only) still lives under enneagram.inferred_wing.
    enn_a = (user_data_a.get("enneagram") or {}) if isinstance(user_data_a, dict) else {}
    enn_b = (user_data_b.get("enneagram") or {}) if isinstance(user_data_b, dict) else {}
    wing_a = enn_a.get("inferred_wing") if isinstance(enn_a, dict) else None
    wing_b = enn_b.get("inferred_wing") if isinstance(enn_b, dict) else None

    rel_a = ENNEAGRAM_RELATIONAL.get(core_a, {})
    rel_b = ENNEAGRAM_RELATIONAL.get(core_b, {})
    
    how_you_help_them = []
    how_they_help_you = []
    friction_pattern = []
    
    # Directional gifts — what each unlocks in the other.  Written as
    # natural Mirror prose so the legacy signals layer renders cleanly
    # without raw "You → {name}:" arrow notation.
    if rel_a.get("unlocks_in_other"):
        how_you_help_them.append(f"With you, {name_b} finds {rel_a['unlocks_in_other']}.")
    if rel_b.get("unlocks_in_other"):
        how_they_help_you.append(f"With {name_b}, you find {rel_b['unlocks_in_other']}.")

    # Directional needs — what each person most reaches toward the other for.
    # `needs_from_other` catalogue values sometimes begin with an infinitive
    # ("to be valued for…"), in which case we drop the "for " bridge to keep
    # the prose grammatical ("Mel most reaches toward you to be valued…").
    def _needs_join(prefix: str, value: str) -> str:
        v = str(value or "").strip()
        if not v:
            return ""
        if v.lower().startswith("to "):
            return f"{prefix} {v}."
        return f"{prefix} for {v}."

    if rel_b.get("needs_from_other"):
        line = _needs_join(f"{name_b} most reaches toward you", rel_b["needs_from_other"])
        if line:
            how_you_help_them.append(line)
    if rel_a.get("needs_from_other"):
        line = _needs_join(f"You most reach toward {name_b}", rel_a["needs_from_other"])
        if line:
            how_they_help_you.append(line)
    
    # Friction — rooted in core fear/desire interaction
    pair = (core_a, core_b)
    reverse_pair = (core_b, core_a)
    
    if pair in ENNEAGRAM_FRICTION_MAP:
        friction_pattern.append(ENNEAGRAM_FRICTION_MAP[pair])
    elif reverse_pair in ENNEAGRAM_FRICTION_MAP:
        friction_pattern.append(ENNEAGRAM_FRICTION_MAP[reverse_pair])
    elif core_a == core_b:
        fear = rel_a.get("core_fear", "the same thing")
        friction_pattern.append(f"Two {core_a}s share the same blind spot. You both fear {fear} — so neither of you catches it when the pattern activates.")
    
    # FALLBACK: If relational data is sparse, generate from core type descriptions
    if not how_you_help_them and not how_they_help_you:
        # Use center-based interaction
        center_a = enn_a.get("enneagram_computed_details", {}).get("center", "")
        center_b = enn_b.get("enneagram_computed_details", {}).get("center", "")
        
        center_gifts = {
            ("head", "heart"): (f"Your thinking helps {name_b} step back from emotional reactivity", f"{name_b}'s emotional awareness shows you what logic misses"),
            ("head", "gut"): (f"Your analysis gives {name_b}'s instincts a framework", f"{name_b}'s decisiveness cuts through your overthinking"),
            ("heart", "gut"): (f"Your emotional intelligence softens {name_b}'s directness", f"{name_b}'s groundedness helps you stop performing"),
            ("heart", "head"): (f"Your warmth makes {name_b} feel safe enough to think out loud", f"{name_b}'s clarity helps you see past emotion"),
            ("gut", "head"): (f"Your decisiveness helps {name_b} stop analyzing and start moving", f"{name_b}'s perspective shows you options you'd skip"),
            ("gut", "heart"): (f"Your strength gives {name_b} permission to be vulnerable", f"{name_b}'s empathy reveals what you're actually feeling"),
        }
        
        pair_key = (center_a, center_b)
        if pair_key in center_gifts:
            how_you_help_them.append(center_gifts[pair_key][0])
            how_they_help_you.append(center_gifts[pair_key][1])
        elif center_a and center_b:
            how_you_help_them.append(f"As a Type {core_a}, you bring {rel_a.get('core_desire', 'a different perspective')} into this dynamic")
            how_they_help_you.append(f"As a Type {core_b}, {name_b} brings {rel_b.get('core_desire', 'a complementary lens')} into this dynamic")
    
    # Always return something if we have core types
    result = {}
    if how_you_help_them: result["how_you_help_them"] = how_you_help_them[:2]
    if how_they_help_you: result["how_they_help_you"] = how_they_help_you[:2]
    if friction_pattern: result["friction_pattern"] = friction_pattern[:1]
    
    # If result is totally empty but we have types, add a baseline
    if not result:
        result["how_you_help_them"] = [f"Type {core_a} and Type {core_b} see the world from different centers — this creates a natural complementarity"]
        result["how_they_help_you"] = [f"{name_b}'s Type {core_b} perspective balances what your Type {core_a} tends to overlook"]
    
    return result


# =============================================================================
# BAZI RELATIONSHIP SIGNALS — Element interaction dynamics
# =============================================================================

BAZI_ELEMENT_CYCLE = {
    # Productive: element produces the next
    "Wood": "Fire", "Fire": "Earth", "Earth": "Metal", "Metal": "Water", "Water": "Wood",
}
BAZI_CONTROL_CYCLE = {
    # Controlling: element controls/restrains
    "Wood": "Earth", "Fire": "Metal", "Earth": "Water", "Metal": "Wood", "Water": "Fire",
}


def compute_bazi_signals(
    chart_a: Dict[str, Any],
    chart_b: Dict[str, Any],
    name_a: str = "You",
    name_b: str = "them",
    pronouns_b: Dict[str, str] = None,
) -> Optional[Dict[str, List[str]]]:
    bazi_a = chart_a.get("bazi", {}) if chart_a else {}
    bazi_b = chart_b.get("bazi", {}) if chart_b else {}
    
    if not bazi_a or not bazi_b:
        return None
    
    dm_a = bazi_a.get("day_master", {})
    dm_b = bazi_b.get("day_master", {})
    
    el_a = dm_a.get("element", "")
    el_b = dm_b.get("element", "")
    str_a = dm_a.get("strength", "")
    str_b = dm_b.get("strength", "")
    
    if not el_a or not el_b:
        return None
    
    support = []
    tension_list = []
    growth = []
    
    # === DAY MASTER NATURE INTERACTION ===
    kw_a = dm_a.get("keywords", [])
    kw_b = dm_b.get("keywords", [])
    desc_a = dm_a.get("description", "")
    desc_b = dm_b.get("description", "")
    
    if kw_a and kw_b:
        support.append(f"Your core nature is {', '.join(kw_a[:2])} ({el_a}) — {name_b}'s is {', '.join(kw_b[:2])} ({el_b})")
    
    # === ELEMENT CYCLE DYNAMICS ===
    # A produces B
    if BAZI_ELEMENT_CYCLE.get(el_a) == el_b:
        support.append(f"Your {el_a} energy naturally nourishes {name_b}'s {el_b} — you feed what they need to grow")
        growth.append(f"This works best when acknowledged — otherwise you may feel like you're giving more than you're receiving")
    
    # B produces A
    if BAZI_ELEMENT_CYCLE.get(el_b) == el_a:
        support.append(f"{name_b}'s {el_b} energy stabilizes your {el_a} — their presence gives your energy somewhere to land")
    
    # A controls B
    if BAZI_CONTROL_CYCLE.get(el_a) == el_b:
        tension_list.append(f"Your {el_a} naturally restrains {name_b}'s {el_b} — what you see as helpful, they may feel as limiting")
        growth.append(f"This pushes {name_b} to build resilience — but only works when the pressure is conscious")
    
    # B controls A
    if BAZI_CONTROL_CYCLE.get(el_b) == el_a:
        tension_list.append(f"{name_b}'s {el_b} energy checks your {el_a} — they hold you to a standard you wouldn't choose for yourself")
    
    # Same element
    if el_a == el_b:
        support.append(f"You process energy the same way — there's an ease in how you both approach decisions and conflict")
        if str_a != str_b:
            growth.append(f"One carries this more strongly — the quieter one learns to assert, the louder one learns to listen")
    
    # Strength dynamics
    if str_a == "strong" and str_b == "weak" and el_a != el_b:
        support.append(f"You anchor things when {name_b} feels ungrounded — your steadiness is something they lean on")
    elif str_a == "weak" and str_b == "strong" and el_a != el_b:
        support.append(f"{name_b}'s solidity gives you something to push against without breaking")
    
    # === ANIMAL SIGN INTERACTION ===
    pillars_a = bazi_a.get("pillars", {})
    pillars_b = bazi_b.get("pillars", {})
    
    year_a = pillars_a.get("year", {})
    year_b = pillars_b.get("year", {})
    day_a = pillars_a.get("day", {})
    day_b = pillars_b.get("day", {})
    
    animal_a = year_a.get("animal_name", "")
    animal_b = year_b.get("animal_name", "")
    animal_emoji_a = year_a.get("animal_emoji", "")
    animal_emoji_b = year_b.get("animal_emoji", "")
    
    day_animal_a = day_a.get("animal_name", "")
    day_animal_b = day_b.get("animal_name", "")
    
    # Chinese zodiac compatibility
    ZODIAC_CLASHES = {
        ("Rat", "Horse"), ("Ox", "Goat"), ("Tiger", "Monkey"),
        ("Rabbit", "Rooster"), ("Dragon", "Dog"), ("Snake", "Pig"),
    }
    ZODIAC_HARMONY = {
        ("Rat", "Dragon"), ("Rat", "Monkey"),
        ("Ox", "Snake"), ("Ox", "Rooster"),
        ("Tiger", "Horse"), ("Tiger", "Dog"),
        ("Rabbit", "Goat"), ("Rabbit", "Pig"),
        ("Dragon", "Monkey"), ("Dragon", "Rat"),
        ("Snake", "Rooster"), ("Snake", "Ox"),
        ("Horse", "Dog"), ("Horse", "Tiger"),
        ("Goat", "Pig"), ("Goat", "Rabbit"),
        ("Monkey", "Rat"), ("Monkey", "Dragon"),
        ("Rooster", "Ox"), ("Rooster", "Snake"),
        ("Dog", "Tiger"), ("Dog", "Horse"),
        ("Pig", "Rabbit"), ("Pig", "Goat"),
    }
    
    if animal_a and animal_b:
        pair = (animal_a, animal_b)
        pair_rev = (animal_b, animal_a)
        
        if pair in ZODIAC_CLASHES or pair_rev in ZODIAC_CLASHES:
            tension_list.append(f"{animal_emoji_a} {animal_a} and {animal_emoji_b} {animal_b} clash in Chinese astrology — your social instincts and generational patterns pull in opposing directions")
        elif pair in ZODIAC_HARMONY or pair_rev in ZODIAC_HARMONY:
            support.append(f"{animal_emoji_a} {animal_a} and {animal_emoji_b} {animal_b} are natural allies — your generational rhythms harmonize and you intuitively understand each other's timing")
        elif animal_a == animal_b:
            support.append(f"Both {animal_emoji_a} {animal_a} — you share the same generational instinct, which creates deep familiarity but also shared blind spots")
        elif animal_a and animal_b:
            growth.append(f"{animal_emoji_a} {animal_a} meets {animal_emoji_b} {animal_b} — different generational energies that expand each other's perspective")
    
    # Day animal (inner self) interaction
    if day_animal_a and day_animal_b and day_animal_a != day_animal_b:
        day_pair = (day_animal_a, day_animal_b)
        day_pair_rev = (day_animal_b, day_animal_a)
        if day_pair in ZODIAC_CLASHES or day_pair_rev in ZODIAC_CLASHES:
            tension_list.append(f"Your inner natures ({day_animal_a} vs {day_animal_b}) create friction in private — how you are at home may clash")
        elif day_pair in ZODIAC_HARMONY or day_pair_rev in ZODIAC_HARMONY:
            support.append(f"Your inner natures ({day_animal_a} and {day_animal_b}) flow together — at your core, you get each other")
    
    # Always return if we have any data
    result = {}
    if support: result["support"] = support[:3]
    if tension_list: result["tension"] = tension_list[:2]
    if growth: result["growth"] = growth[:2]
    
    # Fallback: if we have elements but no signals generated, create baseline
    if not result and el_a and el_b:
        result["support"] = [f"Your {el_a} nature and {name_b}'s {el_b} nature create a specific energetic dynamic"]
        if animal_a and animal_b:
            result["growth"] = [f"{animal_emoji_a} {animal_a} and {animal_emoji_b} {animal_b} bring different generational perspectives"]
    
    return result if result else None




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
    pronouns_b: Dict[str, str] = None,
) -> Optional[Dict[str, List[str]]]:
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
    
    # Grounded numerology translations
    NUM_LIVED = {
        1: "independence and initiative — things move when someone takes the first step",
        2: "partnership and sensitivity — connection deepens through listening, not leading",
        3: "expression and communication — things tend to move forward when you talk, not when you hold back",
        4: "structure and reliability — trust builds through consistency, not grand gestures",
        5: "freedom and change — growth happens through disruption, not stability",
        6: "responsibility and nurturing — what matters most is who you show up for",
        7: "depth and introspection — understanding comes from going inward, not outward",
        8: "power and authority — dynamics around control and resources are amplified",
        9: "compassion and release — letting go is the path forward, not holding on",
        11: "heightened intuition and sensitivity — you both pick up on things most people miss, which creates depth but also intensity",
        22: "large-scale vision and practical idealism — together you think bigger than most couples allow themselves to",
        33: "deep compassion and selfless service — what you build together serves more than just the two of you",
    }
    
    # Shared core numbers (strongest signal)
    all_a = set(filter(None, [lp_a, exp_a, soul_a]))
    all_b = set(filter(None, [lp_b, exp_b, soul_b]))
    shared = all_a & all_b
    
    for num in shared:
        lived = NUM_LIVED.get(num)
        if lived:
            themes.append(f"You both process life through {lived}")
    
    # Both carry master numbers (11, 22, 33)
    master_a = [n for n in all_a if n in (11, 22, 33)]
    master_b = [n for n in all_b if n in (11, 22, 33)]
    if master_a and master_b:
        themes.append(f"Both of you carry master numbers ({', '.join(str(n) for n in master_a)} and {', '.join(str(n) for n in master_b)}) — this connection operates at an intensity most relationships don't reach")
    
    # STRICT quality gate: need 2+ genuinely strong themes
    if len(themes) < 2:
        return None
    
    return {"themes": themes[:2]}



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
    Uses gender from user records for correct pronouns.
    """
    # Resolve pronouns from gender
    gender_b = (user_b or {}).get("gender", "").lower() if user_b else ""
    if gender_b == "male":
        him = "him"; his = "his"; he = "he"; her_obj = "him"; her_pos = "his"; she = "he"
    elif gender_b == "female":
        him = "her"; his = "her"; he = "she"; her_obj = "her"; her_pos = "her"; she = "she"
    else:
        him = "them"; his = "their"; he = "they"; her_obj = "them"; her_pos = "their"; she = "they"
    """
    Generate 3-LAYER relationship interpretation.
    
    Layer 1: STORY (emotional hook)
    Layer 2: PATTERNS (behavioral recognition)
    Layer 3: SIGNALS (HD proof + placeholders)
    """
    
    if not completed_channels:
        no_channel_mapping = {
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
        # Additive: try to synthesize a field envelope even for no-channel pairs
        # using whatever astro / bazi / ennea / numerology signals exist.  If
        # nothing surfaces (still possible), the function returns None and we
        # simply don't attach the `field` key — legacy payload is unchanged.
        try:
            from services.relationship_field import build_relationship_field
            _astro = compute_astrology_signals(chart_a, chart_b, current_user_name, member_name) if chart_a and chart_b else None
            _bazi = compute_bazi_signals(chart_a, chart_b, current_user_name, member_name) if chart_a and chart_b else None
            _ennea = compute_enneagram_signals(user_a, user_b, current_user_name, member_name) if user_a and user_b else None
            _num = compute_numerology_signals(chart_a, chart_b, current_user_name, member_name) if chart_a and chart_b else None
            _field = build_relationship_field(
                current_user_name=current_user_name,
                member_name=member_name,
                completed_channels=[],
                chart_a=chart_a,
                chart_b=chart_b,
                astro_signals=_astro,
                bazi_signals=_bazi,
                enneagram_signals=_ennea,
                numerology_signals=_num,
                hd_signals=[],
            )
            if _field is not None:
                no_channel_mapping["field"] = _field
        except Exception as _no_ch_field_err:
            logger.error(
                f"[RelationshipField] no-channel synthesis skipped for "
                f"{current_user_name} ↔ {member_name}: "
                f"{type(_no_ch_field_err).__name__}: {_no_ch_field_err}"
            )
        return no_channel_mapping
    
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
    has_rhythm = "5-15" in channel_ids
    has_logic = "4-63" in channel_ids
    has_openness = "12-22" in channel_ids
    has_initiation = "25-51" in channel_ids
    has_transformation = "32-54" in channel_ids
    has_abstraction = "47-64" in channel_ids
    has_emo_wave = "39-55" in channel_ids
    has_struggle = "28-38" in channel_ids
    has_caring = "27-50" in channel_ids
    
    # =========================================================================
    # SIGNATURE-BASED HEADLINE — chooses the DOMINANT vibe, not just count.
    # Generic "deep + wide" is a last resort — we try to pick something that
    # actually differentiates this person from any other multi-channel connection.
    # =========================================================================
    
    if channel_count >= 4:
        # Priority ladder: pick the MOST DISTINCTIVE combo present
        if has_intimacy and has_emo_wave:
            story_headline = "Your emotional worlds don't stay separate for long — feelings move between you."
            story_summary = f"With {channel_count} active channels — including the intimacy channel and the emotional wave — this connection is wired to feel, not just function. You process each other's weather in real time."
        elif has_money and has_intimacy:
            story_headline = "There's both closeness and control alive in this connection — and neither stays quiet for long."
            story_summary = f"You have {channel_count} energetic completions pulling you together. Intimacy opens you, but resource and power dynamics surface right alongside it. Both sit at the same table."
        elif has_rhythm and has_community:
            story_headline = "Your natural tempo syncs with theirs — belonging forms through shared timing, not just shared history."
            story_summary = f"With {channel_count} active channels, this dynamic is less about intensity and more about resonance. When you're aligned, it's effortless. When rhythms diverge, the whole thing feels off."
        elif has_logic and has_transformation:
            story_headline = "You think things through together — and the thinking itself changes both of you."
            story_summary = f"With {channel_count} active channels, this connection runs on mental engagement and real growth. You sharpen each other's reasoning; you also push each other past who you were."
        elif has_adventure and has_initiation:
            story_headline = "You don't just encourage each other — you start things together, often before you've agreed to."
            story_summary = f"With {channel_count} electromagnetic completions, momentum builds fast between you. Ideas become plans; plans become action. Pausing is the harder skill."
        elif has_authenticity and has_listening:
            story_headline = "When you're together, the masks drop fast — and the listening is real."
            story_summary = f"With {channel_count} active channels, this connection rewards honesty over performance. Surface talk dissolves quickly; what's left is what actually matters to both of you."
        elif has_intimacy and has_community:
            # Original "deep + wide" — now ONLY when no more specific combo applies
            story_headline = "This connection reaches both your emotional core and your sense of belonging."
            story_summary = f"With {channel_count} active channels between you, this isn't a surface-level dynamic. You complete each other in ways that create real pull — the kind where silence feels full and distance feels temporary."
        elif has_intimacy:
            story_headline = "There's an intensity here that most connections don't reach."
            story_summary = f"You have {channel_count} energetic completions pulling you together. The intimacy channel means barriers dissolve faster than usual between you. That's powerful — and sometimes overwhelming."
        elif has_caring:
            story_headline = "You watch over each other in small, noticed ways — that's the spine of this connection."
            story_summary = f"With {channel_count} active channels, care runs through this dynamic quietly. You remember what matters to them without being asked. They do the same."
        elif has_struggle:
            story_headline = "There's real friction in this connection — and it's the productive kind."
            story_summary = f"With {channel_count} active channels, this dynamic doesn't smooth things over. You challenge each other's sense of purpose. Handled well, it builds both of you. Handled poorly, it burns."
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
            "21-45": "Within a short time of getting close, you start cooperating on real things — money, plans, structure, who owns what. Resources and direction quickly become a shared conversation.",
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
            "21-45": "When direction goes unspoken, one of you ends up carrying more than was agreed — provision, decisions, or load. Make the contract visible while it's still small.",
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
            "21-45": f"Together you can actually build — this connection has a rare combination of ambition, capability, and follow-through wired in",
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
            "21-45": "Together, you naturally start organizing resources, direction, and responsibility — this connection tends to move toward building something tangible",
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
            # Backend returns the short name only (e.g. "Community"); the UI
            # prepends "Channel of ". Previously this produced
            # "Channel of Channel of Community".
            "name": c['name'],
            "theme": c["theme"],
            "translation": translation,
            "your_gate": c["gate_a"],
            "their_gate": c["gate_b"],
        })
    
    # Compute multi-lens signals (real data, not placeholders)
    # Pass pronouns for gender-correct output
    pronouns_b = {"he": he, "him": him, "his": his, "she": she}
    astrology_signals = compute_astrology_signals(chart_a, chart_b, current_user_name, member_name, pronouns_b) if chart_a and chart_b else None
    enneagram_signals = compute_enneagram_signals(user_a, user_b, current_user_name, member_name, pronouns_b) if user_a and user_b else None
    numerology_signals = compute_numerology_signals(chart_a, chart_b, current_user_name, member_name, pronouns_b) if chart_a and chart_b else None
    # BaZi: compute from chart data
    bazi_signals = compute_bazi_signals(chart_a, chart_b, current_user_name, member_name, pronouns_b) if chart_a and chart_b else None
    
    # Post-process ALL text output to use correct pronouns based on gender
    def _fix_pronouns(text):
        if not text or not isinstance(text, str) or gender_b == "female":
            return text
        text = text.replace(" she ", f" {he} ").replace(" she's ", f" {he}'s ").replace(" she.", f" {he}.")
        text = text.replace("She ", f"{he.capitalize()} ").replace("She's ", f"{he.capitalize()}'s ")
        text = text.replace(" her ", f" {his} ").replace(" her.", f" {his}.")
        text = text.replace("Her ", f"{his.capitalize()} ")
        return text
    
    def _fix_signals(obj):
        if obj is None: return None
        if isinstance(obj, dict): return {k: _fix_signals(v) for k, v in obj.items()}
        if isinstance(obj, list): return [_fix_pronouns(i) if isinstance(i, str) else _fix_signals(i) for i in obj]
        if isinstance(obj, str): return _fix_pronouns(obj)
        return obj

    astrology_signals = _fix_signals(astrology_signals)
    enneagram_signals = _fix_signals(enneagram_signals)
    bazi_signals = _fix_signals(bazi_signals)
    numerology_signals = _fix_signals(numerology_signals)
    story_headline = _fix_pronouns(story_headline)
    story_summary = _fix_pronouns(story_summary)
    what_happens = [_fix_pronouns(x) for x in what_happens]
    tensions = [_fix_pronouns(x) for x in tensions]
    gifts = [_fix_pronouns(x) for x in gifts]

    # -----------------------------------------------------------------
    # Channel-card shadow-word sanitizer.
    # Substitutes shadow-heavy framework vocabulary ("materialism",
    # "control dynamics", "weakness", "manipulation", "lack of", etc.)
    # with neutral relational language across every user-visible signal
    # string — including the legacy proof drawer that renders
    # hd_signals[*].theme / .translation and signals.enneagram lists.
    # This is a no-op for already-clean strings.
    # -----------------------------------------------------------------
    try:
        from services.relationship_field import _sanitize_shadow_words as _ss
        def _clean_text(obj):
            if obj is None: return None
            if isinstance(obj, dict): return {k: _clean_text(v) for k, v in obj.items()}
            if isinstance(obj, list): return [_clean_text(i) for i in obj]
            if isinstance(obj, str): return _ss(obj) or obj
            return obj
        hd_signals = _clean_text(hd_signals)
        enneagram_signals = _clean_text(enneagram_signals)
        astrology_signals = _clean_text(astrology_signals)
        bazi_signals = _clean_text(bazi_signals)
        numerology_signals = _clean_text(numerology_signals)
        what_happens = [_ss(x) or x for x in what_happens]
        tensions = [_ss(x) or x for x in tensions]
        gifts = [_ss(x) or x for x in gifts]
        if isinstance(story_headline, str):
            story_headline = _ss(story_headline) or story_headline
        if isinstance(story_summary, str):
            story_summary = _ss(story_summary) or story_summary
    except Exception as _shadow_err:
        # Never block on the sanitizer — log and continue with raw strings.
        logger.warning(f"[ChannelSanitizer] skipped: {_shadow_err}")

    # =========================================================================
    # RELATIONSHIP FIELD ARCHITECTURE v1 — additive synthesis layer.
    # ---------------------------------------------------------------------
    # Reads all the per-lens outputs already computed above and synthesizes
    # them into a single "what happens between us" envelope BEFORE evidence.
    # Strictly additive: every legacy key on the returned mapping (story /
    # patterns / signals / headline / description / what_works /
    # what_to_watch / why_this_happens / channel_count / strength_score)
    # remains byte-identical.  Failure here never blocks the legacy payload.
    # =========================================================================
    field_envelope = None
    try:
        from services.relationship_field import build_relationship_field
        field_envelope = build_relationship_field(
            current_user_name=current_user_name,
            member_name=member_name,
            completed_channels=completed_channels,
            chart_a=chart_a,
            chart_b=chart_b,
            astro_signals=astrology_signals,
            bazi_signals=bazi_signals,
            enneagram_signals=enneagram_signals,
            numerology_signals=numerology_signals,
            hd_signals=hd_signals,
        )
    except Exception as _rf_err:
        logger.error(
            f"[RelationshipField] synthesis skipped for {current_user_name} ↔ "
            f"{member_name}: {type(_rf_err).__name__}: {_rf_err}"
        )
        field_envelope = None

    result = {
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

    # Attach the new field envelope ONLY when synthesis succeeded.
    if field_envelope is not None:
        result["field"] = field_envelope

    return result


async def _ensure_chart_ready(db, user_id: str, user_doc: Dict[str, Any]) -> None:
    """Trigger the server's migration/auto-compute path so that chart.astrology
    has populated planet signs and chart.bazi is present before we read them
    for signal computation. Safe no-op if already complete.

    We do NOT require the server migration to succeed — failures are logged
    and the downstream signal functions will simply skip that lens.
    """
    try:
        from server import check_and_migrate_astrology_chart  # type: ignore
        await check_and_migrate_astrology_chart(user_id)
    except Exception as _e:  # pragma: no cover — defensive
        logger.warning(f"[ForumMapping] Astrology migration skipped for {user_id[:8]}: {_e}")

    # Auto-compute BaZi if missing
    try:
        existing = await db.charts.find_one({"user_id": user_id}, {"bazi": 1})
        if existing and existing.get("bazi"):
            return
        bd = user_doc.get("birth_date")
        bt = user_doc.get("birth_time")
        bl = user_doc.get("birth_location") or {}
        lat = bl.get("latitude", bl.get("lat"))
        lon = bl.get("longitude", bl.get("lng", bl.get("lon")))
        if not (bd and bt and lat is not None and lon is not None):
            return
        from services.bazi_engine_v2 import compute_bazi_chart_v2
        bazi = compute_bazi_chart_v2(
            birth_date=str(bd),
            birth_time=str(bt),
            birth_place=bl.get("city", "Unknown"),
            latitude=lat,
            longitude=lon,
            timezone_str=user_doc.get("timezone") or bl.get("timezone") or "UTC",
        ) or {}
        if bazi:
            from datetime import datetime, timezone as _tz
            await db.charts.update_one(
                {"user_id": user_id},
                {"$set": {"bazi": bazi, "bazi_updated_at": datetime.now(_tz.utc)}},
                upsert=True,
            )
            logger.info(f"[ForumMapping] BaZi computed on-demand for {user_id[:8]}")
    except Exception as _e:
        logger.warning(f"[ForumMapping] BaZi auto-compute skipped for {user_id[:8]}: {_e}")


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
            # Try string _id (some production records use string instead of ObjectId)
            current_user = await db.users.find_one({"_id": current_user_id})
        if not current_user:
            logger.error(f"[ForumMapping] Current user {current_user_id} not found")
            return []
        
        # Ensure current user's chart is migrated (empty planets + BaZi) before fetch
        await _ensure_chart_ready(db, current_user_id, current_user)

        # Get current user's chart (HD data)
        current_chart = await db.charts.find_one({"user_id": current_user_id})
        if not current_chart:
            current_chart = await db.charts.find_one({"user_id": str(current_user_id)})
        current_user_gates = get_user_gates(current_user, current_chart)
        current_user_name = current_user.get("name", "You")
        
        logger.info(f"[ForumMapping] User {current_user_id[:8]} ({current_user_name}) has {len(current_user_gates)} gates")
        
        # Get all forum members from forum_members collection
        memberships = await db.forum_members.find({
            "forum_id": forum_id,
            "status": "active"
        }).to_list(100)
        
        # Also try without status filter if no members found
        if not memberships:
            memberships = await db.forum_members.find({
                "forum_id": forum_id,
            }).to_list(100)
            logger.info(f"[ForumMapping] Found {len(memberships)} members without status filter")
        
        logger.info(f"[ForumMapping] Found {len(memberships)} memberships for forum {forum_id}")
        
        mappings = []
        
        for membership in memberships:
            member_id = membership.get("user_id")
            if member_id == current_user_id:
                continue  # Skip self
            
            # Get member data - try both ObjectId and string lookups
            member = None
            try:
                member = await db.users.find_one({"_id": ObjectId(str(member_id))})
            except Exception:
                pass
            if not member:
                member = await db.users.find_one({"_id": member_id})
            if not member:
                logger.warning(f"[ForumMapping] Member {member_id} not found in users collection")
                continue
            
            member_name = member.get("name") or membership.get("name") or "Unknown"
            
            # Ensure member's chart is migrated (empty planets + BaZi) before fetch
            await _ensure_chart_ready(db, str(member_id), member)

            # Get member's chart (HD data) - try multiple lookups
            member_chart = await db.charts.find_one({"user_id": str(member_id)})
            if not member_chart:
                member_chart = await db.charts.find_one({"user_id": member_id})
            
            member_gates = get_user_gates(member, member_chart)
            
            logger.info(f"[ForumMapping] Member {member_name} ({member_id[:8] if member_id else '?'}) has {len(member_gates)} gates, chart={'YES' if member_chart else 'NO'}")
            
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

            # -----------------------------------------------------------
            # OPHIUCHUS DISTORTION LAYER — contextual, subtle, 1 bullet,
            # only when at least one person has Ophiuchus AND the pair's
            # patterns.tensions already imply misread / projection /
            # inconsistency. No new section, no Ophiuchus terminology.
            # -----------------------------------------------------------
            try:
                from services.ophiuchus_distortion import check_forum_pair as _ophi_check_pair
                _pair = _ophi_check_pair(
                    (current_chart or {}).get("astrology", {}) if current_chart else None,
                    (member_chart or {}).get("astrology", {}) if member_chart else None,
                    mapping.get("patterns"),
                )
                if _pair.get("inject") and _pair.get("forum_line"):
                    line = _pair["forum_line"]
                    patterns = mapping.get("patterns") or {}
                    tensions = patterns.get("tensions") or []
                    # append into tensions (the "where friction shows up" list)
                    if isinstance(tensions, list):
                        tensions.append(line)
                        patterns["tensions"] = tensions
                        mapping["patterns"] = patterns
                    # and keep backward-compat surface in sync
                    if mapping.get("what_to_watch"):
                        mapping["what_to_watch"] = f"{mapping['what_to_watch']}. {line}"
                    else:
                        mapping["what_to_watch"] = line
                    logger.info(f"[Ophiuchus] Forum injection {current_user_name}<->{member_name}: {_pair.get('reason')}")
            except Exception as _e:
                logger.warning(f"[Ophiuchus] Forum pair injection skipped: {_e}")

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
