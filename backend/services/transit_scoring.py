"""
Transit Signal Scoring + Pair Archetypes (V6)
==============================================
Build marker: astrology-today-v6-scoring

Forensic finding (May 2026 audit):
The V5 dominance engine had no numeric scoring — `dominant = tier1[0]`
picked by append order. Combined with a blanket `signal_conflict`
override that routed ~100% of Pete's days to a single `_CONFLICT_CORE`
string, this collapsed astrologically distinct skies into the same
"slow down / don't react" lesson.

V6 fix (this module, called by astrology_today_v5.py):
  1. Numeric scoring of every classified signal.
  2. Role assignment: dominant / destabilizer / amplifier — driven by
     score and role-fit, not by tier-append order.
  3. Transit-pair archetype detection: Saturn-Sun, Pluto-Mars,
     Mercury-Uranus, etc., each with its own theme + lesson + risk +
     move strings.
  4. Optional interpretive register (operator_founder, relationship,
     creative, inner) that re-flavours the same transit through a
     specific life-domain lens.

This file does NOT touch astronomy (positions, orbs, houses are still
computed by transit_dominance_engine.py and the underlying ephemeris).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── Planet & natal-point weights ───────────────────────────────────────────

_TRANSIT_PLANET_WEIGHT = {
    "Pluto":   30, "Neptune": 28, "Uranus": 28, "Saturn": 28,
    "Jupiter": 18, "Chiron":  16,
    "Mars":    14, "Sun":     14, "Venus":   12,
    "Mercury": 11, "Moon":     8,
}
_NATAL_POINT_WEIGHT = {
    "Sun":     16, "Moon":    16, "ASC":     16, "MC":     14,
    "Mars":    11, "Venus":   11, "Mercury": 10,
    "Saturn":   9, "Jupiter":  9, "Uranus":  9, "Neptune": 9, "Pluto": 9,
    "Earth":    6, "Chiron":   7, "North Node": 7, "South Node": 6,
    "Juno":     5, "Pallas":   4, "Ceres":    4, "Vesta":    4,
}

# How tight does a 0° orb add to score? Linear taper to 0 at 6°.
def _orb_bonus(orb: float, max_orb: float = 6.0) -> float:
    if orb is None or orb >= max_orb:
        return 0.0
    return round(40.0 * (1.0 - (orb / max_orb)), 1)


_HARD_ASPECTS = {"conjunction", "opposition", "square"}
_SOFT_ASPECTS = {"trine", "sextile"}


# ── Scoring ────────────────────────────────────────────────────────────────

def _score_transit_to_natal(asp: Dict[str, Any]) -> Dict[str, Any]:
    t = asp.get("transit") or ""
    n = asp.get("natal") or ""
    orb = float(asp.get("orb") or 99)
    applying = bool(asp.get("applying"))
    aspect = (asp.get("aspect") or "").lower()
    house = asp.get("natal_house")

    pw = _TRANSIT_PLANET_WEIGHT.get(t, 8)
    nw = _NATAL_POINT_WEIGHT.get(n, 4)
    base = pw + nw                      # planet-pair gravity
    orb_b = _orb_bonus(orb)             # tightness bonus
    hard = 8 if aspect in _HARD_ASPECTS else (4 if aspect in _SOFT_ASPECTS else 0)
    apply_b = 6 if applying else 0      # applying carries forward
    house_b = 3 if isinstance(house, int) and house in (1, 4, 7, 10) else 0  # angular houses
    # Slow planet to luminary/angle is the headline of all astrology
    slow_to_core = 0
    if t in ("Pluto", "Neptune", "Uranus", "Saturn") and n in ("Sun", "Moon", "ASC", "MC"):
        slow_to_core = 15

    score = base + orb_b + hard + apply_b + house_b + slow_to_core
    reason = (
        f"{t} {aspect} {n}; orb {orb}° "
        f"{'applying' if applying else 'separating'}; "
        f"house {house}; planet_wt={pw} natal_wt={nw} orb_b={orb_b} "
        f"hard={hard} apply_b={apply_b} angular_b={house_b} slow_to_core={slow_to_core}"
    )
    return {
        "label":  f"{t} {aspect} natal {n}",
        "type":   "transit_to_natal",
        "subtype": "tight" if orb <= 0.5 else "strong" if orb <= 1.5 else "wide",
        "transit_planet": t,
        "natal_point":    n,
        "aspect":         aspect,
        "orb":            orb,
        "applying":       applying,
        "house":          house,
        "score":          round(score, 1),
        "reason":         reason,
        "_raw":           asp,
    }


def _score_lunation(phase: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for key, friendly in [("nearest_full_moon", "Full Moon"),
                          ("nearest_new_moon", "New Moon")]:
        node = phase.get(key) or {}
        if not node.get("within_48h"):
            continue
        hours = abs(float(node.get("hours_offset") or 99))
        # Up to +35 base for a lunation; tighter window scores higher.
        base = 35 - min(35, hours * 0.7)   # 0h → 35, 48h → ~1
        out.append({
            "label":  friendly,
            "type":   "lunation",
            "subtype": "full_moon" if key == "nearest_full_moon" else "new_moon",
            "exact_in_hours": round(node.get("hours_offset") or 0, 2),
            "score":  round(base, 1),
            "reason": f"{friendly} within 48h (exact in {node.get('hours_offset'):+.1f}h)",
        })
    return out


def _score_ingress(ing: Dict[str, Any]) -> Dict[str, Any]:
    planet = ing.get("planet") or ""
    days = abs(float(ing.get("days_offset") or 99))
    is_outer = ing.get("is_outer")
    is_heavy = ing.get("is_heavy")
    is_personal = ing.get("is_personal")
    if is_outer:
        base = 30 - min(20, days * 1.5)
        category = "outer_ingress"
    elif is_heavy:
        base = 22 - min(18, days * 2.0)
        category = "heavy_ingress"
    elif is_personal:
        base = 12 - min(10, days * 3.0)
        category = "personal_ingress"
    else:
        base = 5 - min(4, days)
        category = "ingress"
    return {
        "label":  f"{planet} → {ing.get('to_sign')}",
        "type":   "ingress",
        "subtype": category,
        "planet":  planet,
        "to_sign": ing.get("to_sign"),
        "days":   ing.get("days_offset"),
        "score":  round(max(0.0, base), 1),
        "reason": f"{planet} ingress to {ing.get('to_sign')} ({days:.1f}d away, {category})",
    }


def _score_cluster(c: Dict[str, Any], kind: str) -> Dict[str, Any]:
    n = len(c.get("bodies") or [])
    base = 6 + 3 * max(0, n - 3)  # 3 bodies = 6, 4 = 9, 5 = 12 …
    if kind == "house_cluster":
        return {
            "label": f"{n} bodies in house {c.get('house')}",
            "type":  "cluster",
            "subtype": "house_cluster",
            "house": c.get("house"),
            "bodies": c.get("bodies"),
            "score": round(base, 1),
            "reason": f"{n} active bodies in house {c.get('house')}",
        }
    return {
        "label": f"{n} bodies in {c.get('sign')}",
        "type":  "cluster",
        "subtype": "sign_cluster",
        "sign":  c.get("sign"),
        "bodies": c.get("bodies"),
        "score": round(base, 1),
        "reason": f"{n} bodies in {c.get('sign')}",
    }


# ── Role assignment ────────────────────────────────────────────────────────

def _is_friction(cand: Dict[str, Any]) -> bool:
    """Is this candidate a destabilizer (tension/friction signal)?"""
    if cand["type"] == "transit_to_natal":
        return cand.get("aspect", "").lower() in _HARD_ASPECTS
    if cand["type"] == "lunation" and cand.get("subtype") == "full_moon":
        return True
    return False


def _is_amplifier(cand: Dict[str, Any]) -> bool:
    """Is this a systemic backdrop (lunation, ingress) that amplifies?"""
    return cand["type"] in ("lunation", "ingress", "cluster")


def rank_candidates(
    *,
    aspects: List[Dict[str, Any]],
    moon_phase: Dict[str, Any],
    ingresses: List[Dict[str, Any]],
    house_activations: Dict[str, Any],
    sky: Dict[str, Any],
) -> Dict[str, Any]:
    """Score and rank every candidate signal in today's sky.

    Returns:
      {
        "ranked_candidates": [{"label","type","score","reason",...}, ...],
        "dominant":      <top candidate>,
        "destabilizer":  <top friction candidate that isn't dominant>,
        "amplifier":     <top amplifier candidate that isn't dominant>,
      }
    """
    candidates: List[Dict[str, Any]] = []

    # Transit-to-natal aspects
    for asp in aspects or []:
        scored = _score_transit_to_natal(asp)
        candidates.append(scored)

    # Lunations
    candidates.extend(_score_lunation(moon_phase or {}))

    # Ingresses (filter to the immediate window — engine already filters)
    for ing in ingresses or []:
        scored = _score_ingress(ing)
        if scored["score"] > 0:
            candidates.append(scored)

    # Sign + house clusters
    sign_counts: Dict[str, List[str]] = {}
    for name, body in (sky or {}).get("bodies", {}).items():
        sign_counts.setdefault(body["sign"], []).append(name)
    for sign, bodies in sign_counts.items():
        if len(bodies) >= 3:
            candidates.append(_score_cluster({"sign": sign, "bodies": bodies}, "sign_cluster"))
    for cluster in (house_activations or {}).get("clusters", []):
        candidates.append(_score_cluster(cluster, "house_cluster"))

    # Rank
    candidates.sort(key=lambda c: c["score"], reverse=True)

    dominant = candidates[0] if candidates else None
    destabilizer = next(
        (c for c in candidates[1:] if _is_friction(c)), None
    )
    amplifier = next(
        (c for c in candidates[1:] if _is_amplifier(c) and c is not destabilizer), None
    )

    return {
        "ranked_candidates": candidates,
        "dominant":          dominant,
        "destabilizer":      destabilizer,
        "amplifier":         amplifier,
    }


# ── Transit-pair archetypes (Phase 3) ──────────────────────────────────────
#
# Each archetype carries its OWN headline + lesson, not the generic
# "don't move too fast". The archetype lookup falls back to the V5 type
# archetype only if no transit-pair match is found.

# Archetypes keyed by (transit_planet, natal_point). Aspect is included
# only when the meaning differs between hard and soft contacts; in most
# cases hard aspects share a body (conj/opp/square).

ARCHETYPES: Dict[str, Dict[str, str]] = {
    "saturn_sun": {
        "theme": "responsibility, self-definition, authority, visibility, consequence, endurance",
        "core": (
            "Saturn is pressing on your Sun. Responsibility, identity, "
            "and the weight of being seen are heavier than usual. This "
            "isn't a mood — it's a compression point. What you carry, "
            "what people expect of you, what your words cost, and what "
            "you cannot delegate are all pulling into focus. The work "
            "is to meet the pressure as structure, not as injury."
        ),
        "risk": (
            "Treating the weight as a personal failure, or rushing to "
            "discharge it through over-delivery."
        ),
        "move": "Name what's actually yours to hold today, and what isn't.",
    },
    "saturn_moon": {
        "theme": "emotional containment, duty, heaviness, family pressure, maturity around need",
        "core": (
            "Saturn is on your Moon. The feeling tone today is heavier "
            "and more contained. Old emotional duties or family-shaped "
            "obligations are closer to the surface. Comfort is in short "
            "supply, and your usual ways of being soothed feel a step "
            "too far away. This is a day for honest emotional maturity, "
            "not performance of resilience."
        ),
        "risk": (
            "Mistaking the weight for proof you're failing, or muscling "
            "through what actually needs to be acknowledged."
        ),
        "move": "Acknowledge the heaviness without making it your identity.",
    },
    "saturn_venus": {
        "theme": "relational reality, value, commitment, cost of attachment",
        "core": (
            "Saturn is touching your Venus. Relationships, value, and "
            "what something is actually worth are being tested for "
            "structural truth today. The day pulls toward clarity about "
            "who and what is real, durable, and reciprocal — and where "
            "you've been over-spending on something that doesn't return."
        ),
        "risk": (
            "Treating clarity as coldness, or making permanent decisions "
            "from a single compressed moment."
        ),
        "move": "Notice what would still be standing here in six months.",
    },
    "saturn_mars": {
        "theme": "blocked action, disciplined force, frustration, pacing",
        "core": (
            "Saturn is on your Mars. Your forward drive is meeting a "
            "wall — not because the drive is wrong, but because the "
            "shape of it has to change. Force won't move what's in the "
            "way. The day asks for disciplined, narrow, well-aimed "
            "action, not for more push."
        ),
        "risk": "Doubling down on the same shove, or going passive in protest.",
        "move": "Halve your action surface; keep the intent.",
    },
    "uranus_sun_moon_asc": {
        "theme": "disruption, individuation, nervous system change, freedom pressure",
        "core": (
            "Uranus is on a personal point. Something in how you've "
            "been organising your life is asking to be unstuck. The "
            "nervous system runs fast and bright today. New information, "
            "a sudden read, or an unexpected ask can reframe a whole "
            "pattern — but the body's job today is to absorb without "
            "throwing the steering wheel."
        ),
        "risk": "Confusing the spark of insight with a binding decision.",
        "move": "Capture the new read; act on it after one full sleep.",
    },
    "mercury_uranus_hard": {
        "theme": "mental speed, assumptions, sudden speech, disruptive insight",
        "core": (
            "Mercury is in hard contact with Uranus. The mind is running "
            "faster than your read of the situation can settle. You'll "
            "have sharp insights and you'll also have sharp misreads — "
            "and from the inside they feel the same. Words and messages "
            "carry more current than usual today."
        ),
        "risk": "Saying or sending the take while it's still moving.",
        "move": "Let the sharpest thing wait one sleep before it leaves your mouth.",
    },
    "pluto_mars": {
        "theme": "power, force, survival drive, anger, control",
        "core": (
            "Pluto is on your Mars. The drive that's coming up is older "
            "and deeper than today's situation — it's a survival-level "
            "force. Power dynamics are loud. Anger arrives wearing a "
            "different face than it usually does, and so does the urge "
            "to control. This is a high-leverage day; nothing here is "
            "small."
        ),
        "risk": "Burning a bridge you'll need, or freezing a fight you'll keep paying for.",
        "move": "Use the force, but pick what it's pointed at deliberately.",
    },
    "pluto_moon": {
        "theme": "emotional exposure, depth, compulsion, attachment pressure",
        "core": (
            "Pluto is on your Moon. The emotional floor is lower than "
            "usual today; what surfaces is older than the situation "
            "that triggered it. Attachment, control, and the way you "
            "needed to be held a long time ago are all closer to the "
            "skin."
        ),
        "risk": "Acting from the old wound while calling it the present.",
        "move": "Let the old material be old. The present can stay the present.",
    },
    "neptune_sun_moon": {
        "theme": "diffusion, sensitivity, dream-state, dissolved boundary",
        "core": (
            "Neptune is on a luminary. The edges of self are softer "
            "today — porous, dreamy, suggestible. Intuition is louder "
            "but so is the pull to merge with whatever's around you. "
            "You'll feel more than you can name; some of what you feel "
            "isn't yours."
        ),
        "risk": "Mistaking absorbed feeling for your own conviction.",
        "move": "Name what's yours and what came in from the room.",
    },
    "jupiter_personal": {
        "theme": "expansion, opportunity, scope, optimism",
        "core": (
            "Jupiter is in contact with a personal point. The day "
            "carries opening — scope, possibility, a sense that more "
            "is available. The pull is to take the opening as proof "
            "you should expand everywhere; that's how Jupiter overplays. "
            "The signal is: meet the bigger thing as bigger, but with "
            "the same standards."
        ),
        "risk": "Mistaking expansion for direction.",
        "move": "Choose the one expansion that costs you nothing later.",
    },
    "full_moon": {
        "theme": "visibility, culmination, peak awareness, emotional exposure",
        "core": (
            "A Full Moon is exact. Something that's been building "
            "underneath has reached the place where it can actually be "
            "seen. The temptation is to make a decision about it "
            "immediately — to match the brightness with action — but "
            "seeing isn't deciding."
        ),
        "risk": "Closing the window before you've finished looking through it.",
        "move": "Look at it from at least two angles before you respond.",
    },
    "new_moon": {
        "theme": "seed, reset, intention, emerging beginning",
        "core": (
            "A New Moon is exact. The ground is quieter than it's been. "
            "Something is seeding, not starting. The pull is to name "
            "it, mark it, decide what it is — but naming a seed too "
            "early closes its shape."
        ),
        "risk": "Forcing a verdict on a beginning that isn't ready to declare.",
        "move": "Let the beginning be a beginning. Note it without sealing it.",
    },
}


def match_archetype(dominant: Optional[Dict[str, Any]]) -> Optional[str]:
    """Return the ARCHETYPES key that best matches the dominant signal.
    Falls back to None if no transit-pair match exists; caller should
    then use the V5 type-archetype as fallback.
    """
    if not dominant:
        return None
    if dominant["type"] == "lunation":
        return dominant.get("subtype")  # "full_moon" or "new_moon"
    if dominant["type"] != "transit_to_natal":
        return None
    t = dominant.get("transit_planet") or ""
    n = dominant.get("natal_point") or ""
    asp = (dominant.get("aspect") or "").lower()

    # Saturn pairs
    if t == "Saturn":
        if n == "Sun":    return "saturn_sun"
        if n == "Moon":   return "saturn_moon"
        if n == "Venus":  return "saturn_venus"
        if n == "Mars":   return "saturn_mars"
    # Uranus to personal points
    if t == "Uranus" and n in ("Sun", "Moon", "ASC", "MC"):
        return "uranus_sun_moon_asc"
    # Mercury-Uranus hard
    if t == "Mercury" and n == "Uranus" and asp in _HARD_ASPECTS:
        return "mercury_uranus_hard"
    if t == "Uranus" and n == "Mercury" and asp in _HARD_ASPECTS:
        return "mercury_uranus_hard"
    # Pluto pairs
    if t == "Pluto":
        if n == "Mars":   return "pluto_mars"
        if n == "Moon":   return "pluto_moon"
    if t == "Mars" and n == "Pluto":
        return "pluto_mars"
    # Neptune to luminaries
    if t == "Neptune" and n in ("Sun", "Moon"):
        return "neptune_sun_moon"
    # Jupiter to personal
    if t == "Jupiter" and n in ("Sun", "Moon", "Venus", "Mars", "ASC", "MC"):
        return "jupiter_personal"

    return None


# ── Operator / Founder register (Phase 4) ──────────────────────────────────

_OPERATOR_OVERLAYS: Dict[str, Dict[str, str]] = {
    "saturn_sun": {
        "core_overlay": (
            "For someone running something, this lands as authority "
            "under compression: what people are projecting onto you, "
            "what your words now cost, what visibility you can't dodge, "
            "and where the org or the relationship is asking you to "
            "stand for a longer beat. The pressure is not personal "
            "failure — it's the shape of the role."
        ),
        "risk_overlay": (
            "Confusing the role pressure with self-worth, and burning "
            "a credibility move just to discharge the tension."
        ),
        "move_overlay": "Name the call that only you can make, and make it once.",
    },
    "saturn_moon": {
        "core_overlay": (
            "For an operator, this is the part of leadership that "
            "isn't on any deck: holding the affective weight of the "
            "people around you while still moving the work. Today the "
            "carry is heavier than usual."
        ),
        "risk_overlay": "Performing fine instead of acknowledging the load.",
        "move_overlay": "Tell one person the truth of where you are.",
    },
    "saturn_mars": {
        "core_overlay": (
            "The push is meeting the wall because the move you're "
            "trying to make is no longer a one-person move. The day "
            "is asking for narrowed force, not more shove."
        ),
        "risk_overlay": "Trying to outrun a structural problem with personal hustle.",
        "move_overlay": "Pick the one decision that unlocks the next ten.",
    },
    "saturn_venus": {
        "core_overlay": (
            "Relationships in the operation — partners, team, "
            "investors, close collaborators — are being clarified for "
            "what they actually return."
        ),
        "risk_overlay": "Confusing comfort with alignment.",
        "move_overlay": "Notice which relationship would still be here in six months without effort.",
    },
    "uranus_sun_moon_asc": {
        "core_overlay": (
            "The org or the role is on its way to looking different "
            "than it did. Today's job is to capture the new read, not "
            "to restructure on impulse."
        ),
        "risk_overlay": "Calling a re-org from a 24-hour sense of clarity.",
        "move_overlay": "Write the new read down. Don't send it yet.",
    },
    "mercury_uranus_hard": {
        "core_overlay": (
            "Communication today carries unusual current. Messages, "
            "decisions made in chat, public statements — all heavier "
            "than they look from the inside."
        ),
        "risk_overlay": "Sending the sharp thing while it's still moving.",
        "move_overlay": "Slow the channel that carries the most weight.",
    },
    "pluto_mars": {
        "core_overlay": (
            "Power moves are loud today. What you decide to do with "
            "force — push, hold, confront, withdraw — carries more "
            "downstream than usual."
        ),
        "risk_overlay": "Spending a relationship you'll need.",
        "move_overlay": "Pick what the force is pointed at on purpose.",
    },
    "pluto_moon": {
        "core_overlay": (
            "The older emotional material driving this is not the "
            "operator's job to resolve mid-day. The work is to not let "
            "it ride a current decision."
        ),
        "risk_overlay": "Making the org or the partner pay the old bill.",
        "move_overlay": "Notice when a present moment is asking you to repay an old one.",
    },
    "neptune_sun_moon": {
        "core_overlay": (
            "Conviction is soft today. Plans that need clarity should "
            "wait one beat. Plans that need imagination should run."
        ),
        "risk_overlay": "Mistaking absorbed mood for the read of the room.",
        "move_overlay": "Sort which calls need facts and which need feel.",
    },
    "jupiter_personal": {
        "core_overlay": (
            "An opening shows up. The job is to choose the one you'd "
            "still pick a year from now, not the one that makes today "
            "feel big."
        ),
        "risk_overlay": "Mistaking optionality for direction.",
        "move_overlay": "Take the one expansion that doesn't cost you focus later.",
    },
    "full_moon": {
        "core_overlay": (
            "Things that have been building under the surface in the "
            "operation become visible to people who weren't watching "
            "the same way you were."
        ),
        "risk_overlay": "Treating new visibility as new information.",
        "move_overlay": "Let the brightness settle for a sleep before you respond to it.",
    },
    "new_moon": {
        "core_overlay": (
            "Something is seeding in the work. Don't draft the press "
            "release."
        ),
        "risk_overlay": "Naming the seed publicly before it has roots.",
        "move_overlay": "Note it privately. Plant. Don't announce.",
    },
}


def apply_register(
    archetype_key: Optional[str],
    archetype_payload: Optional[Dict[str, Any]],
    register: Optional[str],
) -> Optional[Dict[str, Any]]:
    """If register is set (e.g. 'operator_founder'), splice a domain-
    specific overlay on top of the base archetype."""
    if not archetype_payload or not archetype_key:
        return archetype_payload
    if register != "operator_founder":
        return archetype_payload
    overlay = _OPERATOR_OVERLAYS.get(archetype_key)
    if not overlay:
        return archetype_payload
    base = dict(archetype_payload)
    base["core"] = (base.get("core", "") + " " + overlay.get("core_overlay", "")).strip()
    if overlay.get("risk_overlay"):
        base["risk"] = (base.get("risk", "") + " " + overlay["risk_overlay"]).strip()
    if overlay.get("move_overlay"):
        base["move"] = overlay["move_overlay"]
    base["_register"] = register
    return base


__all__ = [
    "rank_candidates",
    "ARCHETYPES",
    "match_archetype",
    "apply_register",
]
