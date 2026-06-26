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
#
# Layered Convergence v1.3 — Phase 4 Batch 1 voice.
# Each entry answers the 5 channel questions:
#   1. What activates?  (headline)
#   2. What forms between them?  (description, opening)
#   3. What becomes easier together?  (what_works)
#   4. What tension emerges?  (what_to_watch)
#   5. What shows up in real life?  (translation — lives in TRANSLATION_MAP)
# Channel names + gate numbers stay visible as proof in the card chrome.
CHANNEL_INTERPRETATIONS = {
    # ── Batch 1 — most-active / currently-curated channels ──────────────
    "37-40": {
        # The Bargain — community / loyalty / agreements
        "headline": "Loyalty and unspoken agreements form fast — and feel binding",
        "description": (
            "An invisible contract starts the moment you meet. You both feel "
            "a sense of 'we're in this' before anything is said. What forms "
            "between you is the architecture of a tribe — promises, "
            "expectations, mutual backing — even if neither of you used "
            "those words."
        ),
        "what_works": (
            "Saying out loud what you've already agreed to silently. The "
            "contract is real either way — making it visible just makes it "
            "cleaner."
        ),
        "what_to_watch": (
            "What feels 'agreed' may not actually be shared. When loyalty "
            "meets a different definition of loyalty, the pressure builds "
            "quietly."
        ),
    },
    "6-59": {
        # Mating — intimacy / emotional permeability
        "headline": "Emotional barriers come down faster than either of you expects",
        "description": (
            "When you're around each other, the door to intimacy opens "
            "without much prompting — old defenses get quiet. You both feel "
            "the temperature of the room before words land. What forms "
            "between you is a kind of emotional permeability most people "
            "rarely experience."
        ),
        "what_works": (
            "Letting closeness arrive without forcing it. Naming the "
            "temperature out loud when one of you needs a breath."
        ),
        "what_to_watch": (
            "The same permeability that opens you can overwhelm. When it "
            "gets close, one of you tends to pull back to recover — that's "
            "recovery, not rejection."
        ),
    },
    "10-20": {
        # Awakening — authenticity / present-moment honesty
        "headline": "You both become more openly yourselves when together",
        "description": (
            "Filters drop. The version of you that performs for most people "
            "doesn't survive long around each other — you skip past the "
            "polite layer and land in something more real, faster. What "
            "forms between you is relief from performing."
        ),
        "what_works": (
            "Honest expression in the moment. Both of you saying what's "
            "actually true rather than what's strategic."
        ),
        "what_to_watch": (
            "Authenticity can land as bluntness when timing is off. "
            "Different truths can coexist — don't confuse honesty with "
            "always agreeing."
        ),
    },
    "13-33": {
        # The Prodigal — witness / story / reflection
        "headline": "One speaks, the other deeply hears — and stories matter here",
        "description": (
            "There's a witnessing dynamic at play: experiences and memories "
            "surface between you that don't surface elsewhere. The listener "
            "often sees more than the speaker realizes. What forms between "
            "you is a kind of archive — your stories acquire meaning by "
            "being told here."
        ),
        "what_works": (
            "Taking turns. The speaker speaking fully, the listener "
            "listening fully, before the role flips."
        ),
        "what_to_watch": (
            "If only one of you ever speaks, the dynamic ossifies. Both "
            "roles need air."
        ),
    },
    "27-50": {
        # Preservation — care / nourishment / protection of values
        "headline": "You naturally look out for what matters to each other",
        "description": (
            "Care moves between you before being asked — a small "
            "adjustment, a noticed need, a quiet protection. What forms is "
            "mutual stewardship of the things and people each of you "
            "values. This connection naturally moves toward care, "
            "protection, and sustaining what matters."
        ),
        "what_works": (
            "Letting yourselves receive, not just give. Checking that care "
            "flows both directions."
        ),
        "what_to_watch": (
            "One of you can over-give until the giving becomes invisible — "
            "and then resentment finds the gap. Surface the score before it "
            "gets uneven."
        ),
    },
    "5-15": {
        # Rhythm — natural pacing / timing / flow
        "headline": "Your natural pace and timing line up",
        "description": (
            "When you're aligned, things move between you without "
            "negotiation — you fall into the same rhythm of meeting, "
            "doing, resting. What forms is a container of ease that other "
            "connections in your life don't have. This one runs on flow, "
            "not friction."
        ),
        "what_works": (
            "Trusting the rhythm when it's there. Letting timing do the "
            "work."
        ),
        "what_to_watch": (
            "When the rhythms diverge — different sleep, different "
            "seasons, different speeds — the whole connection can feel off "
            "even when nothing's wrong."
        ),
    },
    "34-57": {
        # Power / Intuition — instinctive read / wordless trust
        "headline": "An unusually fast instinctive read of each other forms here",
        "description": (
            "There's an instinctive read of each other that doesn't need "
            "data. You can tell when the other is off, before the words. "
            "What forms between you is an unusually fast instinctive read "
            "of each other — trust tends to form before explanation does."
        ),
        "what_works": (
            "Trusting the read. When you feel something's off, name it — "
            "that's the channel doing its job."
        ),
        "what_to_watch": (
            "Fast read can become unchecked read. Don't let instinct "
            "replace the small adjustments that keep a connection current."
        ),
    },
    "35-36": {
        # Transitoriness — experience / novelty / movement
        "headline": "You pull each other into new experiences — sometimes before either of you is ready",
        "description": (
            "Together you generate momentum into the new — places, "
            "projects, emotional terrain neither of you would enter alone. "
            "What forms between you is appetite. The connection wants "
            "experience, not stability."
        ),
        "what_works": (
            "Saying yes to the experiment, but checking in with whether "
            "you both actually want it after."
        ),
        "what_to_watch": (
            "The hunger for novelty can destabilize what's already "
            "working. Some of what was built quietly needs protection."
        ),
    },
    "21-45": {
        # The Money Line — gates 21 (control of resources) + 45 (gatherer of
        # resources).  Founders/operators feel this one in the material
        # world: provision, capability, ambition, who carries what.
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
    # ─────────────────────────────────────────────────────────────────────
    # V1.3 — BATCH 2 channel rewrites (32-54, 28-38, 39-55, 18-58, 12-22,
    # 1-8, 4-63, 11-56). Voice calibrated to "what activates / what forms
    # between two people in lived reality" — recognisable, behavioural,
    # not melodramatic. Especially careful with 39-55, 28-38, 18-58 which
    # are easy to over-intensify into suffering archetypes.
    # ─────────────────────────────────────────────────────────────────────
    "32-54": {
        # Transformation — ambition / ascent. Founder/operator energy.
        "headline": "Together you start treating ambition as something to engineer, not just talk about",
        "description": (
            "There's a steady ladder-climbing energy here. You stop asking "
            "whether something is possible and start asking what it would "
            "actually take. What forms between you is a working version of "
            "ambition — the kind that survives weeks four through twelve, "
            "not just the first conversation."
        ),
        "what_works": (
            "Naming the bigger thing you're moving toward, then resourcing "
            "it properly — money, time, the right people."
        ),
        "what_to_watch": (
            "Ambition can become the only language you speak together. "
            "Notice when the connection has quietly become a project plan."
        ),
    },
    "28-38": {
        # Struggle — purpose / stake-holding. Not melodrama; lived stakes.
        "headline": "What each of you refuses to give up on becomes visible here",
        "description": (
            "Between you, the question of what's worth standing behind "
            "stops being abstract. You catch each other testing whether "
            "something is real enough to defend. What forms is a kind of "
            "mutual stake-holding — not drama, but accuracy about what each "
            "of you is unwilling to abandon."
        ),
        "what_works": (
            "Letting each of you name your stake without negotiating it "
            "down. The honesty matters more than the agreement."
        ),
        "what_to_watch": (
            "When both of you have something to defend, the same "
            "conversation can keep happening at the wrong angle. The real "
            "stake is usually one layer beneath the surface argument."
        ),
    },
    "39-55": {
        # Emoting — provocation + emotional abundance. Avoid melodrama.
        "headline": "Moods carry more information between you than either of you expected",
        "description": (
            "Emotional tone matters here in a way it doesn't in most "
            "connections. You catch the shift in each other's mood faster "
            "than the other has named it. What forms is a sensitivity to "
            "atmosphere — when the spirit is high between you, the "
            "connection feels rich; when it's flat, both of you feel that too."
        ),
        "what_works": (
            "Naming the mood out loud rather than pretending it isn't in "
            "the room. The connection regulates faster once it's said."
        ),
        "what_to_watch": (
            "Small jabs can leak in — provocations testing for a reaction. "
            "Catch them early; the channel is asking for honesty, not a fight."
        ),
    },
    "18-58": {
        # Judgment — correction / improvement. Not critical; quietly improving.
        "headline": "You catch what's off and want to fix it — and most of the time, you're right",
        "description": (
            "Between you, there's a sharp eye for what could be better. "
            "You notice the broken thing first, the unsaid imbalance, the "
            "place a system isn't working yet. What forms is a quietly "
            "improving connection — care expressed as the willingness to "
            "point at the thing that needs adjusting."
        ),
        "what_works": (
            "Letting the correction land on the thing, not the person. The "
            "accuracy is the love; the tone is the test."
        ),
        "what_to_watch": (
            "The same eye that sees what could improve can become the eye "
            "that never lets up. Some things between you don't need to be "
            "optimised."
        ),
    },
    "12-22": {
        # Openness — social grace / mood-driven expression. Behavioural.
        "headline": "How easily this connection moves depends on the mood it walks in with",
        "description": (
            "When the spirit is open between you, everything flows — "
            "conversation, affection, plans. When it isn't, no amount of "
            "pushing fixes it. What forms is a connection that runs on "
            "receptivity rather than effort: the moment determines what's "
            "possible, and you've both learnt to read that."
        ),
        "what_works": (
            "Letting the door open when it's open, and not trying to pry it "
            "open when it isn't."
        ),
        "what_to_watch": (
            "When the mood goes flat, one of you may push for expression "
            "the moment can't carry. Wait it out."
        ),
    },
    "1-8": {
        # Inspiration — creative direction + contribution.
        "headline": "You become more creatively bold around each other than you are alone",
        "description": (
            "Between you, individual expression gets a witness — and the "
            "witness is part of what gives it shape. One of you brings the "
            "original spark; the other helps direct it into something other "
            "people can actually see. What forms is a creative pairing "
            "where ambition for the work matters as much as the work itself."
        ),
        "what_works": (
            "Honouring whose vision it actually is, and putting structure "
            "under it instead of around it."
        ),
        "what_to_watch": (
            "If one of you keeps shaping the other's expression without "
            "contributing your own, the dynamic flattens. Both creators "
            "have to be visible."
        ),
    },
    "4-63": {
        # Logic — doubt → answers / testing ideas in pairs.
        "headline": "You think things through together — answers arrive faster than they would alone",
        "description": (
            "There's a back-and-forth structure to your thinking here. One "
            "of you raises a doubt; the other finds the formulation that "
            "resolves it. What forms is a working pair of minds — better at "
            "testing ideas together than either of you is on your own."
        ),
        "what_works": (
            "Letting the doubt be a real question, not a rhetorical one. "
            "The friction is the engine."
        ),
        "what_to_watch": (
            "Premature answers close the loop before it's actually finished "
            "forming. Let some questions stay open longer than feels "
            "comfortable."
        ),
    },
    "11-56": {
        # Curiosity — ideas + storytelling.
        "headline": "Ideas and stories travel back and forth here — and the best ones come out of motion",
        "description": (
            "You exchange ideas, framings, and stories with unusual ease. "
            "Something one of you says triggers something in the other, "
            "which triggers something back — and over time you accumulate a "
            "private library of useful frames other people don't have "
            "access to. What forms is a connection that thinks in stories."
        ),
        "what_works": (
            "Letting the back-and-forth play out without rushing to a "
            "conclusion. The metabolising is the value."
        ),
        "what_to_watch": (
            "Curiosity without grounding can stay theoretical forever. "
            "Land at least some of what you've talked about in something real."
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

# Variant A canonical: ensure Ophiuchus has an element + modality entry.
from services.ophiuchus_metadata import patch_element_map as _patch_e, patch_modality_map as _patch_m
_patch_e(ELEMENT_MAP)
_patch_m(MODALITY_MAP)

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

    # Additive: grounded animal narrative blocks for the BaZi drill-down.
    # Strict templates, no mystical fatalism. See bazi_animal_narrative.py.
    try:
        from services.bazi_animal_narrative import compute_animal_narrative
        _animal_narr = compute_animal_narrative(
            animal_a=animal_a or "",
            animal_b=animal_b or "",
            day_animal_a=day_animal_a or "",
            day_animal_b=day_animal_b or "",
            name_a=name_a,
            name_b=name_b,
        )
        if _animal_narr:
            result["animal_narrative"] = _animal_narr
    except Exception as _ban_err:
        logger.warning(f"[BaziAnimalNarrative] skipped: {_ban_err}")

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

    # Short single-word descriptors used for the "different operating
    # systems" fallback so it stays a single readable sentence.
    NUM_SHORT = {
        1: "initiative",        2: "partnership",     3: "expression",
        4: "structure",         5: "freedom",         6: "responsibility",
        7: "depth",             8: "authority",       9: "release",
        11: "intuitive insight", 22: "master-builder vision", 33: "selfless service",
    }

    # Canonical numerology complement pairs — the classical "natural
    # counterweight" pairings drawn from Pythagorean tradition.  Order-
    # insensitive; covers both single-digit and master-amplified pairings.
    COMPLEMENT_PAIRS = {
        frozenset({1, 2}): "Your initiating energy gives shape to {name_b}'s relational instincts; their listening softens your forward push.",
        frozenset({3, 6}): "Your expression flows into {name_b}'s caregiving form — words become commitments, talk becomes shelter.",
        frozenset({4, 8}): "Your steadiness anchors {name_b}'s ambition; their drive scales the structures you build.",
        frozenset({5, 7}): "Your appetite for change keeps {name_b}'s inward depth from becoming isolation; their reflection slows your motion just enough.",
        frozenset({6, 9}): "Your devotion to specific people meets {name_b}'s wider compassion — the personal and the universal balance each other.",
        frozenset({1, 7}): "Your action sharpens against {name_b}'s introspection — together you learn when to move and when to wait.",
        frozenset({2, 8}): "Your sensitivity tempers {name_b}'s authority; their decisiveness covers the ground your care alone can't.",
        frozenset({3, 9}): "Your expression becomes their release — speaking what was held, finishing what was started.",
        frozenset({4, 5}): "Your stability gives {name_b}'s freedom somewhere to return to; their disruption keeps your structure alive.",
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
        themes.append(
            f"Both of you carry master numbers ({', '.join(str(n) for n in master_a)} and "
            f"{', '.join(str(n) for n in master_b)}) — this connection operates at an "
            f"intensity most relationships don't reach"
        )

    # ── PARITY V1 FALLBACK (relationship-parity-numerology-v1) ────────
    # If the shared/master detectors didn't find anything, fall back to
    # a Life-Path-based baseline so the lens is never silently dropped.
    # This mirrors the BaZi engine's `el_a / el_b` fallback at L#1120.
    if not themes:
        # 1. Canonical complementary Life-Path pair?
        pair_key = frozenset({lp_a, lp_b})
        complement = COMPLEMENT_PAIRS.get(pair_key)
        if complement and lp_a != lp_b:
            themes.append(
                complement.format(name_a=name_a, name_b=name_b)
            )
        else:
            # 2. Baseline: "different operating systems" narrative —
            #    always produces a readable line whenever both have a
            #    usable life-path number.
            short_a = NUM_SHORT.get(lp_a, f"a {lp_a}-path")
            short_b = NUM_SHORT.get(lp_b, f"a {lp_b}-path")
            if lp_a == lp_b:
                themes.append(
                    f"You both move through life on the same {lp_a}-path — {NUM_LIVED.get(lp_a, short_a)} — "
                    f"which can feel like deep recognition or like looking in a mirror you can't always escape"
                )
            else:
                themes.append(
                    f"You operate from {short_a}; {name_b} operates from {short_b}. "
                    f"Different rhythms reaching for the same destination — translation between the two is the work"
                )

    # Cap output to keep the lens scannable.  Forum FE renders all
    # entries verbatim; >3 reads as noise.
    out: Dict[str, Any] = {"themes": themes[:3]}

    # ── Phase 2-lite enrichment (additive; backward compatible) ──────
    # Attach v2_card + diagnostics from the deterministic engine.
    # Frontend may ignore these fields; existing `themes` consumers
    # see identical shape.  Engine returns None only when life_path
    # missing on either side — already guarded above.
    try:
        from services.relationship_numerology_engine_lite import (
            compute_numerology_relationship,
        )
        enriched = compute_numerology_relationship(
            num_a, num_b, name_a, name_b,
        )
        if isinstance(enriched, dict):
            if "v2_card" in enriched:
                out["v2_card"] = enriched["v2_card"]
            if "diagnostics" in enriched:
                out["diagnostics"] = enriched["diagnostics"]
    except Exception as e:  # pragma: no cover — defensive
        logger.warning(
            "[NumerologyLite] v2_card attachment failed: %s", e,
        )

    return out



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

        # Additive: attach the curated CHANNEL_INTERPRETATIONS entry under
        # `interpretation` so the frontend can render richer card accordions
        # ("What this opens" / "What works" / "What to watch") later.  When
        # no curated entry exists for this channel id we fall back to the
        # "default" interpretation — never None — so the contract is
        # idempotent and additive.
        interp = (
            CHANNEL_INTERPRETATIONS.get(cid)
            or CHANNEL_INTERPRETATIONS.get("default", {})
        )

        # Per-channel narrative (gift / tension / practical_use) — additive
        # for the relationship-page HD drill-down. See hd_channel_narrative.py.
        channel_narrative = None
        try:
            from services.hd_channel_narrative import compute_channel_narrative
            channel_narrative = compute_channel_narrative(
                channel_id=cid,
                channel_name=c.get("name", ""),
                theme=c.get("theme", ""),
                relational=c.get("relational", ""),
                name_a=current_user_name,
                name_b=member_name,
            )
        except Exception as _ch_n_err:
            logger.warning(f"[HDChannelNarrative] skipped for {cid}: {_ch_n_err}")
            channel_narrative = None

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
            # Additive: curated interpretation card (headline / description /
            # what_works / what_to_watch).  Safe even on legacy clients that
            # ignore unknown keys.
            "interpretation": {
                "headline":      interp.get("headline"),
                "description":   interp.get("description"),
                "what_works":    interp.get("what_works"),
                "what_to_watch": interp.get("what_to_watch"),
                "is_curated":    cid in CHANNEL_INTERPRETATIONS,
            },
            # NEW — per-channel narrative {gift, tension, practical_use}.
            # Frontend renders this directly under each channel box.
            "narrative": channel_narrative,
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
    # HD FIELD ENGINE V3 — relationship-hd-field-v3 (Phase 3 lens parity).
    # ---------------------------------------------------------------------
    # Computes a deterministic energy-field interpretation between the two
    # charts and exposes it as a NEW sibling key on the mapping:
    #     mapping["signals"]["human_design_field"] = {field_v3, diagnostics}
    # The existing `signals.human_design` array (channel cards) remains
    # byte-identical — frontend consumers of the list are unaffected.
    # =========================================================================
    hd_field_v3 = None
    try:
        from services.relationship_hd_field_engine import (
            compute_hd_relationship_field as _compute_hd_field,
        )
        hd_field_v3 = _compute_hd_field(
            chart_a, chart_b, current_user_name, member_name,
        )
        if hd_field_v3:
            logger.info(
                f"[HDFieldV3] pair={current_user_name}<->{member_name} "
                f"sig={hd_field_v3['field_v3']['energy_signature']!r} "
                f"em={hd_field_v3['diagnostics']['electromagnetic_count']} "
                f"dom={hd_field_v3['diagnostics']['dominance_count']}"
            )
            # Additive: build human-readable HD relationship narrative blocks
            # (type_pair, authority, profile, definition, centers, channels,
            # practical_guidance). See hd_relationship_narrative.py.
            try:
                from services.hd_relationship_narrative import (
                    compute_hd_narrative_blocks,
                )
                _nblocks = compute_hd_narrative_blocks(
                    field_v3=hd_field_v3.get("field_v3"),
                    diagnostics=hd_field_v3.get("diagnostics"),
                    name_a=current_user_name,
                    name_b=member_name,
                )
                if _nblocks:
                    hd_field_v3["narrative_blocks"] = _nblocks
            except Exception as _nb_err:
                logger.warning(
                    f"[HDRelationshipNarrative] skipped: {_nb_err}"
                )
    except Exception as _hd_v3_err:
        logger.warning(f"[HDFieldV3] error: {_hd_v3_err}")

    # =========================================================================
    # MIRROR KG OVERLAY V1 — relationship_synthesis (additive only).
    # Normalises lens signals → ephemeral knowledge graph → progressive
    # synthesis.  Wrapped in try/except so it cannot break the mapping.
    # Adds ONE new key: mapping["relationship_synthesis"]
    # =========================================================================
    relationship_synthesis = None
    try:
        from services.mirror_signal_normalizer import normalize_signals
        from services.mirror_knowledge_graph import build_knowledge_graph
        from services.mirror_reflection_orchestrator import synthesize_relationship
        _kg_signals_input = {
            "human_design_field": hd_field_v3,
            "bazi":       bazi_signals,
            "numerology": numerology_signals,
            "astrology":  astrology_signals,
            "enneagram":  enneagram_signals,
        }
        _norm_signals = normalize_signals(_kg_signals_input)
        _graph = build_knowledge_graph(_norm_signals)
        relationship_synthesis = synthesize_relationship(
            _norm_signals, _graph, current_user_name, member_name,
        )
        logger.info(
            f"[MirrorKG] pair={current_user_name}<->{member_name} "
            f"signals={len(_norm_signals)} "
            f"clusters={(_graph.get('diagnostics') or {}).get('cluster_count')} "
            f"conf={relationship_synthesis['confidence']['level']}"
        )
    except Exception as _kg_err:
        logger.warning(f"[MirrorKG] overlay error: {_kg_err}")

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
            "human_design_field": hd_field_v3,
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
        # MIRROR KG OVERLAY V1 — additive, may be None on failure.
        "relationship_synthesis": relationship_synthesis,
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

            # ──────────────────────────────────────────────────────────
            # V2: relationship-mapping-deep-astrology-v2
            # Inject role-aware deep astrology synthesis + dedupe across
            # signal cards. Strictly additive — legacy fields preserved.
            # ──────────────────────────────────────────────────────────
            try:
                from services.relationship_resolver import resolve_relationship
                from services.relationship_astrology_engine import (
                    build_relationship_astrology,
                    dedupe_mapping_sections,
                    BUILD_MARKER as _RAE_MARKER,
                )
                _rel_ctx = await resolve_relationship(
                    db=db,
                    asker_user_id=current_user_id,
                    target_user_id=str(member_id),
                    target_name=member_name,
                    forum_id=forum_id,
                )
                _role = _rel_ctx.get("relationship_role") or "forum_member"
                _spouse_aware = _role in ("spouse", "partner", "ex_partner")
                logger.info(
                    f"[RelationshipMappingV2] pair={current_user_name}<->{member_name} "
                    f"role={_role} source={_rel_ctx.get('relationship_source')}"
                )
                if current_chart and member_chart:
                    _deep = build_relationship_astrology(
                        chart_a=current_chart,
                        chart_b=member_chart,
                        name_a=current_user_name,
                        name_b=member_name,
                        relationship_role=_role,
                        closeness=_rel_ctx.get("closeness", "medium"),
                        emotional_weight=_rel_ctx.get("emotional_weight", "medium"),
                    )
                    # ── relationship-astrology-instrumentation-v2 ───────
                    # Engine now emits its own canonical log line (see
                    # services/relationship_astrology_engine.py).  No
                    # additional logging needed here — keeping the
                    # dispatch site quiet to avoid contradictory output.
                    # ── Surface wiring v1: Astrology Relationship Re-Story V1 ──
                    # Strictly additive.  Returns None when the
                    # `ASTROLOGY_RELATIONSHIP_RESTORY_V1` flag is unset, or
                    # either chart is missing.  Otherwise emits the 5-section
                    # payload (see services/astrology_relationship_restory_v1).
                    try:
                        from services.astrology_relationship_restory_v1 import (
                            maybe_compute_restory as _maybe_restory_v1,
                        )
                        _restory_v1 = _maybe_restory_v1(
                            chart_a=current_chart,
                            chart_b=member_chart,
                            relationship_role=_role,
                            name_a=current_user_name,
                            name_b=member_name,
                        )
                    except Exception as _rsv1_err:    # pragma: no cover
                        logger.debug(
                            f"[RelMappingV2][ReStoryV1] compute skipped: "
                            f"{type(_rsv1_err).__name__}: {_rsv1_err!r}"
                        )
                        _restory_v1 = None

                    # ── Surface wiring v1: Relationship Curriculum Engine ──
                    # Meaning-layer synthesis ("Why This Person Matters").
                    # Returns None when `RELATIONSHIP_CURRICULUM_ENGINE` is
                    # unset (default) — legacy payload preserved.
                    try:
                        from services.relationship_curriculum_engine import (
                            maybe_generate as _maybe_curriculum,
                        )
                        _curriculum = _maybe_curriculum(
                            person_a={"chart": current_chart, "name": current_user_name},
                            person_b={"chart": member_chart,  "name": member_name},
                            relationship_context={
                                "role":             _role,
                                "closeness":        _rel_ctx.get("closeness"),
                                "emotional_weight": _rel_ctx.get("emotional_weight"),
                            },
                        )
                    except Exception as _curr_err:    # pragma: no cover
                        logger.debug(
                            f"[RelMappingV2][Curriculum] compute skipped: "
                            f"{type(_curr_err).__name__}: {_curr_err!r}"
                        )
                        _curriculum = None

                    if _deep.get("success"):
                        # Promote the deep astrology card into the
                        # signals.astrology surface so the UI picks it up.
                        signals = mapping.get("signals") or {}
                        astro_existing = signals.get("astrology") or {}
                        # Preserve the legacy attraction/tension/growth
                        # arrays but PREPEND the V2 card so the headline
                        # leads with the spouse-aware synthesis.
                        if isinstance(astro_existing, dict):
                            astro_existing["v2_card"] = _deep["astrology_card"]
                            astro_existing["core_relational_pattern"] = _deep["core_relational_pattern"]
                            astro_existing["emotional_safety_loop"] = _deep["emotional_safety_loop"]
                            astro_existing["communication_loop"] = _deep["communication_loop"]
                            astro_existing["conflict_signature"] = _deep["conflict_signature"]
                            astro_existing["repair_condition"] = _deep["repair_condition"]
                            astro_existing["spouse_specific_translation"] = _deep.get("spouse_specific_translation")
                            astro_existing["ic_emotional_foundation"] = _deep.get("ic_emotional_foundation")
                            astro_existing["what_a_triggers_in_b"] = _deep.get("what_a_triggers_in_b")
                            astro_existing["what_b_triggers_in_a"] = _deep.get("what_b_triggers_in_a")
                            astro_existing["supporting_signals"] = _deep["supporting_signals"]
                            astro_existing["build_marker"] = _RAE_MARKER
                            # Surface wiring v1 — only present when the
                            # flag is on AND both charts are available.
                            if _restory_v1 is not None:
                                astro_existing["restory_v1"] = _restory_v1
                            # ── Relationship Curriculum Engine V1 surface wiring ──
                            # Top-level `signals.relationship_curriculum` (NOT
                            # nested under astrology) because the engine
                            # spans astrology + HD + enneagram + bazi.
                            if _curriculum is not None:
                                signals["relationship_curriculum"] = _curriculum
                            # relationship-v2-final-cleanup: suppress
                            # legacy bullets (attraction/tension/growth)
                            # when V2 deep card is present so the
                            # frontend never has to choose between two
                            # conflicting astrology payloads.
                            astro_existing["legacy_hidden_due_to_v2"] = True
                            astro_existing["attraction"] = []
                            astro_existing["tension"] = []
                            astro_existing["growth"] = []
                            signals["astrology"] = astro_existing
                        else:
                            signals["astrology"] = {
                                "v2_card": _deep["astrology_card"],
                                "build_marker": _RAE_MARKER,
                                "core_relational_pattern": _deep["core_relational_pattern"],
                                "supporting_signals": _deep["supporting_signals"],
                            }
                        mapping["signals"] = signals
                        # Surface a top-level astrology_dynamics card so
                        # the UI can render it as the dedicated section.
                        mapping["astrology_dynamics"] = _deep["astrology_card"]

                # ── BaZi Dynamics narrative card (v2.2) ────────────────────
                # relationship-mapping-bazi-narrative-v1
                # Adds a 5-section deterministic interpretation layer above
                # the existing Elemental Dynamics (which remains as evidence).
                # No calculator changes; pure synthesis from compute_bazi_signals
                # output + already-computed chart.bazi fields.
                try:
                    from services.relationship_bazi_engine import (
                        build_relationship_bazi as _build_bazi,
                        BUILD_MARKER as _BAZI_MARKER,
                    )
                    _sigs_now = mapping.get("signals") or {}
                    _bsigs = _sigs_now.get("bazi") or {}
                    _bazi_out = _build_bazi(
                        chart_a=current_chart,
                        chart_b=member_chart,
                        name_a=current_user_name,
                        name_b=member_name,
                        relationship_role=_role,
                        support_signals=_bsigs.get("support") or [],
                        tension_signals=_bsigs.get("tension") or [],
                        growth_signals=_bsigs.get("growth") or [],
                    )
                    if _bazi_out.get("success"):
                        # Surface at top level (parallel to astrology_dynamics)
                        mapping["bazi_dynamics"] = _bazi_out["bazi_card"]
                        mapping["bazi_dynamics"]["build_marker"] = _BAZI_MARKER
                        # Also nest under signals.bazi so consumers can find
                        # the card alongside the evidence arrays.
                        if isinstance(_bsigs, dict):
                            _bsigs["v2_card"] = _bazi_out["bazi_card"]
                            _bsigs["build_marker"] = _BAZI_MARKER
                            _bsigs["diagnostics"] = _bazi_out.get("diagnostics") or {}
                            # ── Phase 3 V2 enrichment (additive) ─────────
                            # relationship-bazi-engine-v2 — lens-parity
                            # dimensions: natural_strength, repair_pathway,
                            # current_movement, how_they_help_each_other,
                            # how_they_challenge_each_other,
                            # current_relationship_season.  Merged INTO
                            # the existing v2_card without removing any
                            # wisdom-v3 keys.
                            try:
                                from services.relationship_bazi_engine_v2 import (
                                    enrich_bazi_relationship as _enrich_bazi,
                                    ENGINE_VERSION as _BAZI_V2_VERSION,
                                )
                                _v2_enriched = _enrich_bazi(
                                    chart_a=current_chart,
                                    chart_b=member_chart,
                                    name_a=current_user_name,
                                    name_b=member_name,
                                )
                                if isinstance(_v2_enriched, dict):
                                    # Merge new v2_card keys (don't overwrite v3 keys)
                                    for _k, _v in (_v2_enriched.get("v2_card") or {}).items():
                                        if _k not in _bsigs["v2_card"]:
                                            _bsigs["v2_card"][_k] = _v
                                    # Merge diagnostics
                                    for _k, _v in (_v2_enriched.get("diagnostics") or {}).items():
                                        _bsigs["diagnostics"][_k] = _v
                                    _bsigs["v2_engine_version"] = _BAZI_V2_VERSION
                            except Exception as _v2_err:  # pragma: no cover
                                logger.warning(
                                    f"[BaziV2Enrich] error for {member_name}: {_v2_err}"
                                )
                            _sigs_now["bazi"] = _bsigs
                            mapping["signals"] = _sigs_now
                        logger.info(
                            f"[BaziNarrative] pair={current_user_name}<->{member_name} "
                            f"role={_role} cycle={_bazi_out['diagnostics'].get('cycle')} "
                            f"el={_bazi_out['diagnostics'].get('element_a')}-"
                            f"{_bazi_out['diagnostics'].get('element_b')}"
                        )
                    else:
                        logger.info(
                            f"[BaziNarrative] skipped pair={current_user_name}<->{member_name}: "
                            f"{_bazi_out.get('reason')}"
                        )
                except Exception as _bz_err:
                    logger.warning(
                        f"[BaziNarrative] error for {member_name}: "
                        f"{type(_bz_err).__name__}: {_bz_err}"
                    )

                # Attach relationship_context debug
                mapping.setdefault("debug", {})["relationship_context"] = {
                    "target_name":          member_name,
                    "relationship_role":    _role,
                    "role_source":          _rel_ctx.get("relationship_source"),
                    "closeness":            _rel_ctx.get("closeness"),
                    "emotional_weight":     _rel_ctx.get("emotional_weight"),
                    "spouse_context_used":  _spouse_aware,
                    "forum_name":           _rel_ctx.get("forum_name"),
                    "build_marker":         _RAE_MARKER,
                }

                # Dedupe pass — removes overlapping shallow phrases.
                mapping = dedupe_mapping_sections(mapping)
            except Exception as _v2_err:
                logger.warning(
                    f"[RelationshipMappingV2] skipped for {member_name}: {_v2_err}"
                )

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
