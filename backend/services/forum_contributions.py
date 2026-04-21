"""
What Each Person Brings — Multi-Lens Superpower Synthesis (Mirror Engine v3).

For each forum member:
    - ONE named superpower (1-2 words) chosen by multi-lens scoring
    - TWO lines of description — line 1 = what happens in the room,
      line 2 = how they uniquely express it (varies by secondary signals)

Input lenses (consulted, never surfaced to the user):
    - Human Design    → FUNCTION (how energy moves)
    - Enneagram       → MOTIVATION (why it moves)
    - BaZi            → BEHAVIOR UNDER PRESSURE (element + strength)
    - Numerology      → RHYTHM (life-path, expression)
    - Astrology/Decan → EXPRESSION STYLE (sun sign + decan, moon, asc)
    - Pattern Memory  → INTENSITY (NEW / RETURNING / RECURRING)

Design:
    Each superpower carries weighted affinities across every lens. For a
    given member we compute:

        score(sp) = Σ affinity_for(sp, lens_signal)

    and pick the highest-scoring superpower that's not yet used in the
    forum. Same HD type + similar enneagram can still yield different
    superpowers when numerology / astro / bazi diverge — that's the point.

    Line 1 is the stable "what the room gets" core per superpower.
    Line 2 has up to 5 style variants per superpower ("default", "fire",
    "water", "earth", "air") keyed to the BaZi-element + sun-sign blend,
    so two members who happen to share a superpower can still read
    differently. Pattern memory RECURRING picks an intensified variant
    where available.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Set, Tuple

from bson import ObjectId

logger = logging.getLogger(__name__)


# ===========================================================================
# 24-ENTRY SUPERPOWER POOL (stable line 1 + style-variant line 2)
# ===========================================================================
# Line 2 variants: "default" is required; "fire"/"water"/"earth"/"air"
# optional. "recurring" optional — used when pattern memory says RECURRING.

_POOL: Dict[str, Dict[str, Any]] = {
    "Expansion": {
        "l1": "You open space before others feel ready — the room stretches around your movement.",
        "l2": {
            "default":   "What looks like confidence is often you moving ahead of your own certainty.",
            "fire":      "You move hot — you'd rather create the moment than wait for permission.",
            "water":     "You expand by sensing the opening before you can name it.",
            "earth":     "You stretch the ground steadily — not fast, but always further than last time.",
            "air":       "You expand through the idea first; the room catches up.",
            "recurring": "You've done this enough times that the reach no longer scares you — it's the staying wide that does.",
        },
    },
    "Amplification": {
        "l1": "You reflect what's really happening in the room.",
        "l2": {
            "default": "What others feel vaguely becomes clear through you, often without you needing to push.",
            "water":   "You feel the undertone first — by the time you speak, the room already half-knew.",
            "air":     "You translate the room into language nobody else had located yet.",
            "earth":   "You hold the signal steady enough that others can finally see it themselves.",
            "fire":    "You amplify by moving first — people watch what you notice and match it.",
        },
    },
    "Momentum": {
        "l1": "When you're in, the work moves.",
        "l2": {
            "default":   "You convert half-formed ideas into forward motion faster than most can track.",
            "fire":      "You pull the group into the next step before they've finished debating the last one.",
            "earth":     "You don't rush — you just never stop, and that turns out to be faster.",
            "water":     "You read when the wave is ready, then commit everyone to it.",
            "recurring": "You've built this muscle in rooms that stalled — now momentum follows you in.",
        },
    },
    "Clarity": {
        "l1": "After you speak, the fog lifts.",
        "l2": {
            "default": "You cut through what others are trying to say but haven't yet named.",
            "air":     "You think in outlines — and hand the rest of us the outline.",
            "fire":    "You'd rather be specific and wrong than vague and safe.",
            "water":   "You name the quiet thing underneath, and the confusion releases.",
            "earth":   "You make the abstract concrete — a list, a name, a next step.",
        },
    },
    "Disruption": {
        "l1": "You break the pattern the room was quietly agreeing to.",
        "l2": {
            "default":   "You say what needs saying before it's comfortable to hear.",
            "fire":      "You'd rather disturb the surface than let a lie set.",
            "air":       "You reframe what nobody wanted reframed — and it changes the whole room.",
            "recurring": "You're the one who's been here before — so the break doesn't scare you anymore.",
        },
    },
    "Anchoring": {
        "l1": "The group settles when you enter.",
        "l2": {
            "default": "You hold steady ground so others can stop bracing.",
            "earth":   "Your steadiness is physical — people relax in their bodies around you.",
            "water":   "You anchor through tone — not volume, not words, just presence that doesn't flinch.",
            "metal":   "You anchor through clean standards — the room trusts what you won't drop.",
        },
    },
    "Catalysis": {
        "l1": "Things start changing the moment you're in the mix.",
        "l2": {
            "default": "You don't push — your presence alone makes the next move obvious.",
            "fire":    "You carry a heat that rearranges what people were willing to try.",
            "water":   "You shift emotional temperature and the logic follows.",
            "air":     "You plant an idea once, casually, and it grows without you.",
        },
    },
    "Revelation": {
        "l1": "Truths that were hiding come into view because you're here.",
        "l2": {
            "default": "You name the thing underneath the conversation, gently.",
            "water":   "You track what's actually felt, not what's said — and bring it up.",
            "air":     "You expose the assumption no one noticed they were standing on.",
            "fire":    "You'd rather surface the hard thing than protect the comfortable thing.",
        },
    },
    "Acceleration": {
        "l1": "Time moves faster in your presence.",
        "l2": {
            "default":   "Things that usually take weeks come together inside one session with you.",
            "fire":      "You compress whole arcs into moments — the rest of us catch up later.",
            "air":       "You skip three steps because you can see step four from here.",
            "recurring": "You've moved at this speed long enough that you've learned to leave a clean trail.",
        },
    },
    "Attunement": {
        "l1": "You feel the room before it speaks.",
        "l2": {
            "default": "You adjust your tone to what the moment is actually asking for.",
            "water":   "You absorb the emotional weather, then hand it back a degree cooler.",
            "earth":   "You tune slow — but once you're locked in, you don't miss.",
            "air":     "You clock the shift in tone and name it faster than the rest of the room.",
        },
    },
    "Insistence": {
        "l1": "You don't let the bar drop when others would.",
        "l2": {
            "default": "You hold the line on what matters until everyone else matches it.",
            "fire":    "You'd rather be the one people resent for a day than the one who stayed quiet.",
            "earth":   "Your standard is physical — you won't let the work sit in a form you don't believe in.",
            "metal":   "You refuse sloppy like some people refuse food they don't like.",
        },
    },
    "Witnessing": {
        "l1": "You see people as they actually are, not who they perform to be.",
        "l2": {
            "default": "Your attention alone invites them to drop the act.",
            "water":   "You feel the layer beneath the behaviour — and that's where you meet them.",
            "air":     "You name what you see, cleanly, and it lands as a gift instead of a judgement.",
        },
    },
    "Resonance": {
        "l1": "The emotional truth of the room lives through you.",
        "l2": {
            "default":   "You amplify what's real and let what's performative fall away.",
            "water":     "Feelings travel through you with almost no translation loss.",
            "recurring": "You've been the emotional channel often enough to know it's not always yours to hold — and you're learning the difference.",
        },
    },
    "Steadiness": {
        "l1": "When things get loud, you don't escalate.",
        "l2": {
            "default": "You lower the temperature of the room just by being in it.",
            "earth":   "Your rhythm is unhurried, and that's the leadership.",
            "water":   "You absorb the charge without passing it on.",
        },
    },
    "Direction": {
        "l1": "You see who should do what, and you say it.",
        "l2": {
            "default": "Your instinct for where people belong is usually right before the rest of us catch up.",
            "air":     "You think in roles, not tasks — and that's why the work clicks when you assign it.",
            "fire":    "You'd rather make the call and be corrected than leave people drifting.",
        },
    },
    "Refinement": {
        "l1": "What you touch gets noticeably better.",
        "l2": {
            "default": "You improve things others would have called done.",
            "metal":   "You have an almost physical reaction to slop — so the work around you quietly lifts.",
            "earth":   "You finish with a steadiness that makes it feel inevitable.",
        },
    },
    "Reliability": {
        "l1": "When you commit, it happens.",
        "l2": {
            "default": "The work quietly gets carried by what you follow through on.",
            "earth":   "You don't over-promise — which is why people trust what you do promise.",
        },
    },
    "Vitality": {
        "l1": "Your energy re-charges the room.",
        "l2": {
            "default": "Things that were drooping start standing up again when you're in.",
            "fire":    "You run warmer than the average person — the room borrows heat from you.",
        },
    },
    "Recognition": {
        "l1": "You name the gift others don't know they have.",
        "l2": {
            "default": "People leave conversations with you feeling more clearly seen.",
            "air":     "You articulate someone's edge so precisely they can finally work with it.",
            "water":   "You see the tender place where someone's gift lives — and you protect it.",
        },
    },
    "Endurance": {
        "l1": "You stay with what others have already given up on.",
        "l2": {
            "default":   "Your patience is the thing that finishes the work.",
            "earth":     "You don't tire at the speed most people do — that's the edge.",
            "recurring": "You've walked long roads before. The stamina isn't willpower for you — it's who you are.",
        },
    },
    "Invitation": {
        "l1": "People lean in when you're the one asking.",
        "l2": {
            "default": "You draw out contribution others weren't sure they had.",
            "water":   "You make space that feels safe enough to risk being honest in.",
            "air":     "You ask the question that reframes the whole situation.",
        },
    },
    "Precision": {
        "l1": "You catch what others miss.",
        "l2": {
            "default": "Small errors stop compounding because you surface them early.",
            "metal":   "You move more slowly on purpose — so what you deliver lands clean.",
            "air":     "Your attention is narrow and sharp — that's the gift.",
        },
    },
    "Depth": {
        "l1": "Conversations go to a truer layer when you're in them.",
        "l2": {
            "default": "You don't skim — you go where the real thing is happening.",
            "water":   "You follow the feeling to its source, and bring others with you.",
        },
    },
    "Presence": {
        "l1": "You're fully here, and that changes what's possible.",
        "l2": {
            "default": "You make it easier for others to stop multitasking and land.",
            "earth":   "Your body arrives before your words — and the room settles around that.",
        },
    },
}


# ===========================================================================
# SIGNAL HELPERS
# ===========================================================================

_ZODIAC_ELEMENT: Dict[str, str] = {
    "aries": "fire", "leo": "fire", "sagittarius": "fire",
    "taurus": "earth", "virgo": "earth", "capricorn": "earth",
    "gemini": "air", "libra": "air", "aquarius": "air",
    "cancer": "water", "scorpio": "water", "pisces": "water",
}

_ZODIAC_MODALITY: Dict[str, str] = {
    "aries": "cardinal", "cancer": "cardinal", "libra": "cardinal", "capricorn": "cardinal",
    "taurus": "fixed", "leo": "fixed", "scorpio": "fixed", "aquarius": "fixed",
    "gemini": "mutable", "virgo": "mutable", "sagittarius": "mutable", "pisces": "mutable",
}


def _norm_hd_type(raw: Any) -> Optional[str]:
    if not isinstance(raw, str): return None
    t = raw.strip().lower()
    if "manifesting" in t and "generator" in t: return "Manifesting Generator"
    if t.startswith("manifestor"): return "Manifestor"
    if t.startswith("projector"):  return "Projector"
    if t.startswith("reflector"):  return "Reflector"
    if "generator" in t:           return "Generator"
    return None


def _enneagram(user: Dict[str, Any]) -> Optional[int]:
    raw = (
        user.get("enneagram_type")
        or user.get("primary_enneagram_type")
        or (user.get("enneagram") or {}).get("primary_type")
        or (user.get("enneagram_result") or {}).get("primary_type")
    )
    try:
        n = int(raw)
        return n if 1 <= n <= 9 else None
    except (TypeError, ValueError):
        return None


def _collect_signals(user: Dict[str, Any], chart: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten every available lens into a single signal bag for scoring."""
    hd = chart.get("human_design") or {}
    bazi = chart.get("bazi") or {}
    num = chart.get("numerology") or {}
    astro = chart.get("astrology") or {}
    planets = astro.get("planets") or {}
    angles = astro.get("angles") or {}

    sun = (planets.get("Sun") or planets.get("sun") or {})
    moon = (planets.get("Moon") or planets.get("moon") or {})
    asc = (angles.get("asc") or {})

    sun_sign = (sun.get("sign") or "").strip().lower() or None
    moon_sign = (moon.get("sign") or "").strip().lower() or None
    asc_sign = (asc.get("sign") or "").strip().lower() or None
    sun_deg = sun.get("degree") or sun.get("longitude")
    try:
        sun_decan = int(float(sun_deg) // 10) + 1 if sun_deg is not None else None
        if sun_decan not in (1, 2, 3):
            sun_decan = None
    except Exception:
        sun_decan = None

    bazi_dom = bazi.get("day_master", {}).get("element")
    bazi_dom = bazi_dom.strip().lower() if isinstance(bazi_dom, str) else None
    bazi_str = bazi.get("day_master", {}).get("strength")
    bazi_str = bazi_str.strip().lower() if isinstance(bazi_str, str) else None
    bazi_dominant_list = [
        e.strip().lower() for e in (bazi.get("elements") or {}).get("dominant", []) if isinstance(e, str)
    ]

    def _num(block):
        v = None
        if isinstance(block, dict):
            v = block.get("number")
        elif isinstance(block, int):
            v = block
        try:
            return int(v) if v is not None else None
        except Exception:
            return None

    life_path = _num(num.get("life_path")) or _num(num.get("life_path_number"))
    expression = _num(num.get("expression")) or _num(num.get("expression_number"))
    soul_urge = _num(num.get("soul_urge")) or _num(num.get("soul_urge_number"))

    return {
        "hd_type":          _norm_hd_type(hd.get("type")),
        "hd_profile":       (hd.get("profile") or None),
        "enneagram":        _enneagram(user),
        "bazi_element":     bazi_dom,
        "bazi_strength":    bazi_str,
        "bazi_dominant":    bazi_dominant_list,
        "life_path":        life_path,
        "expression":       expression,
        "soul_urge":        soul_urge,
        "sun_sign":         sun_sign,
        "sun_decan":        sun_decan,
        "sun_element":      _ZODIAC_ELEMENT.get(sun_sign or "") if sun_sign else None,
        "sun_modality":     _ZODIAC_MODALITY.get(sun_sign or "") if sun_sign else None,
        "moon_sign":        moon_sign,
        "moon_element":     _ZODIAC_ELEMENT.get(moon_sign or "") if moon_sign else None,
        "asc_sign":         asc_sign,
        "asc_element":      _ZODIAC_ELEMENT.get(asc_sign or "") if asc_sign else None,
    }


# ===========================================================================
# MULTI-LENS AFFINITY TABLE
# ===========================================================================
# For every superpower, how strongly does each signal push us toward it?
# Weights are small integers; scoring sums them up. We keep the weights
# loose so a single lens dominates only when all others are missing.

_AFFINITY: Dict[str, Dict[str, Dict[Any, int]]] = {
    "Expansion": {
        "hd_type": {"Manifestor": 3, "Manifesting Generator": 2},
        "enneagram": {7: 3, 3: 2, 8: 1, 4: 1},
        "bazi_element": {"fire": 3, "wood": 2},
        "sun_element": {"fire": 2, "air": 1},
        "sun_modality": {"mutable": 1},
        "life_path": {1: 2, 3: 2, 5: 3, 11: 2},
    },
    "Momentum": {
        "hd_type": {"Manifesting Generator": 3, "Generator": 2, "Manifestor": 2},
        "enneagram": {3: 3, 8: 2, 7: 2},
        "bazi_element": {"fire": 2, "wood": 1},
        "bazi_strength": {"strong": 1},
        "sun_element": {"fire": 2},
        "sun_modality": {"cardinal": 2},
        "life_path": {1: 2, 8: 2, 22: 2},
    },
    "Acceleration": {
        "hd_type": {"Manifesting Generator": 3, "Manifestor": 2},
        "enneagram": {7: 3, 3: 2},
        "bazi_element": {"fire": 2},
        "sun_element": {"fire": 2, "air": 1},
        "sun_modality": {"cardinal": 1, "mutable": 1},
        "life_path": {5: 3, 1: 1},
    },
    "Catalysis": {
        "hd_type": {"Manifestor": 3, "Manifesting Generator": 1, "Projector": 1},
        "enneagram": {8: 3, 7: 2, 3: 1},
        "bazi_element": {"fire": 2, "wood": 1},
        "sun_element": {"fire": 2},
        "sun_modality": {"cardinal": 2},
    },
    "Disruption": {
        "hd_type": {"Manifestor": 3},
        "enneagram": {8: 3, 4: 2, 7: 1},
        "bazi_element": {"fire": 2, "metal": 1},
        "bazi_strength": {"strong": 2},
        "sun_element": {"fire": 2},
        "sun_modality": {"fixed": 1},
    },
    "Insistence": {
        "hd_type": {"Manifestor": 2, "Generator": 2, "Projector": 1},
        "enneagram": {1: 3, 8: 3, 6: 1},
        "bazi_element": {"metal": 3, "earth": 1},
        "bazi_strength": {"strong": 2},
        "sun_element": {"earth": 1, "fire": 1},
        "sun_modality": {"fixed": 2},
    },
    "Revelation": {
        "hd_type": {"Projector": 2, "Manifestor": 1, "Reflector": 1},
        "enneagram": {5: 3, 4: 2, 1: 1},
        "bazi_element": {"water": 2, "metal": 1},
        "sun_element": {"water": 2, "air": 1},
        "sun_modality": {"mutable": 1},
        "life_path": {7: 3, 11: 3, 22: 2},
    },
    "Amplification": {
        "hd_type": {"Reflector": 3, "Projector": 1, "Manifestor": 1},
        "enneagram": {4: 2, 2: 2, 3: 2},
        "bazi_element": {"water": 2, "fire": 1},
        "sun_element": {"water": 2, "fire": 1},
        "sun_modality": {"mutable": 1},
    },
    "Witnessing": {
        "hd_type": {"Reflector": 3, "Projector": 3},
        "enneagram": {5: 2, 9: 2, 4: 2},
        "bazi_element": {"water": 2, "earth": 1},
        "sun_element": {"water": 2},
        "sun_modality": {"mutable": 1, "fixed": 1},
        "life_path": {2: 2, 9: 2, 7: 1},
    },
    "Resonance": {
        "hd_type": {"Reflector": 3, "Generator": 1},
        "enneagram": {4: 3, 2: 2, 9: 1},
        "bazi_element": {"water": 3},
        "sun_element": {"water": 3},
        "sun_modality": {"fixed": 1},
        "life_path": {2: 2, 11: 2},
    },
    "Attunement": {
        "hd_type": {"Reflector": 2, "Projector": 2, "Generator": 1},
        "enneagram": {9: 3, 2: 2, 6: 1},
        "bazi_element": {"water": 2, "earth": 1},
        "sun_element": {"water": 1, "earth": 1},
        "sun_modality": {"mutable": 1},
    },
    "Anchoring": {
        "hd_type": {"Generator": 2, "Projector": 2, "Reflector": 1},
        "enneagram": {6: 3, 9: 2, 1: 2},
        "bazi_element": {"earth": 3, "metal": 1},
        "bazi_strength": {"strong": 1},
        "sun_element": {"earth": 3},
        "sun_modality": {"fixed": 2},
        "life_path": {4: 3, 22: 2},
    },
    "Steadiness": {
        "hd_type": {"Generator": 2, "Reflector": 2, "Projector": 1},
        "enneagram": {9: 3, 1: 2, 6: 1},
        "bazi_element": {"earth": 2, "water": 1},
        "sun_element": {"earth": 2, "water": 1},
        "sun_modality": {"fixed": 2},
        "life_path": {4: 2, 6: 2},
    },
    "Endurance": {
        "hd_type": {"Generator": 3, "Manifesting Generator": 1},
        "enneagram": {1: 2, 8: 2, 6: 2},
        "bazi_element": {"earth": 2, "metal": 2},
        "bazi_strength": {"strong": 2},
        "sun_element": {"earth": 2},
        "sun_modality": {"fixed": 2},
    },
    "Reliability": {
        "hd_type": {"Generator": 3, "Projector": 1},
        "enneagram": {1: 2, 6: 3, 2: 1},
        "bazi_element": {"earth": 3, "metal": 1},
        "sun_element": {"earth": 2},
        "sun_modality": {"fixed": 1},
        "life_path": {4: 3, 6: 2, 22: 2},
    },
    "Refinement": {
        "hd_type": {"Generator": 2, "Manifesting Generator": 2, "Projector": 1},
        "enneagram": {1: 3, 5: 2},
        "bazi_element": {"metal": 3, "earth": 1},
        "sun_element": {"earth": 2, "air": 1},
        "sun_modality": {"mutable": 1},
        "life_path": {4: 2, 7: 1},
    },
    "Precision": {
        "hd_type": {"Generator": 2, "Projector": 2, "Reflector": 1},
        "enneagram": {1: 3, 5: 3, 6: 1},
        "bazi_element": {"metal": 3},
        "sun_element": {"earth": 2, "air": 2},
        "sun_modality": {"mutable": 1},
        "life_path": {7: 2, 4: 1},
    },
    "Clarity": {
        "hd_type": {"Projector": 3, "Manifestor": 1},
        "enneagram": {5: 3, 1: 2, 3: 1},
        "bazi_element": {"metal": 2, "wood": 1},
        "sun_element": {"air": 3, "fire": 1},
        "sun_modality": {"cardinal": 1, "mutable": 1},
        "life_path": {7: 2, 1: 1},
    },
    "Direction": {
        "hd_type": {"Projector": 3, "Manifestor": 1},
        "enneagram": {3: 2, 8: 2, 1: 1},
        "bazi_element": {"metal": 1, "fire": 1},
        "sun_element": {"air": 2, "fire": 2},
        "sun_modality": {"cardinal": 2},
        "life_path": {1: 2, 8: 2},
    },
    "Recognition": {
        "hd_type": {"Projector": 3, "Reflector": 1},
        "enneagram": {2: 3, 4: 2, 9: 1},
        "bazi_element": {"water": 1, "wood": 1},
        "sun_element": {"air": 1, "water": 1},
        "sun_modality": {"mutable": 1},
        "life_path": {2: 2, 9: 2, 6: 2},
    },
    "Invitation": {
        "hd_type": {"Generator": 2, "Projector": 2, "Reflector": 1},
        "enneagram": {2: 3, 9: 2, 4: 1},
        "bazi_element": {"water": 1, "wood": 2},
        "sun_element": {"water": 1, "air": 1},
        "sun_modality": {"cardinal": 1},
    },
    "Vitality": {
        "hd_type": {"Generator": 3, "Manifesting Generator": 2},
        "enneagram": {7: 3, 3: 2, 8: 1},
        "bazi_element": {"fire": 3, "wood": 1},
        "bazi_strength": {"strong": 2},
        "sun_element": {"fire": 2},
        "sun_modality": {"fixed": 1},
        "life_path": {5: 2, 3: 2},
    },
    "Depth": {
        "hd_type": {"Projector": 2, "Reflector": 2, "Generator": 1},
        "enneagram": {4: 3, 5: 2, 8: 1},
        "bazi_element": {"water": 3},
        "sun_element": {"water": 3},
        "sun_modality": {"fixed": 1},
        "life_path": {7: 2, 11: 2},
    },
    "Presence": {
        "hd_type": {"Reflector": 3, "Projector": 2, "Generator": 1},
        "enneagram": {9: 3, 6: 2, 2: 1},
        "bazi_element": {"earth": 2, "water": 1},
        "sun_element": {"earth": 2, "water": 1},
        "sun_modality": {"fixed": 2},
    },
}


# ===========================================================================
# STYLE KEY FOR LINE 2 VARIANT SELECTION
# ===========================================================================

def _style_key(signals: Dict[str, Any]) -> str:
    """
    Return one of: "fire"/"water"/"earth"/"air"/"metal" — used to pick a
    style variant for line 2. We score each candidate using bazi_element +
    sun_element + enneagram so the key is actually blended (not just bazi).
    """
    tally: Dict[str, int] = {"fire": 0, "water": 0, "earth": 0, "air": 0, "metal": 0}

    be = signals.get("bazi_element")
    if isinstance(be, str) and be in tally:
        tally[be] += 3

    se = signals.get("sun_element")
    # sun "fire/water/earth/air" map directly; Chinese-element "metal/wood" don't,
    # so we collapse wood → fire/air-adjacent in the sun signal.
    if isinstance(se, str) and se in tally:
        tally[se] += 2

    # enneagram nudge
    enn = signals.get("enneagram")
    if enn is not None:
        enn_style = {
            1: "metal", 2: "water", 3: "fire", 4: "water", 5: "air",
            6: "earth", 7: "fire", 8: "fire", 9: "earth",
        }.get(enn)
        if enn_style in tally:
            tally[enn_style] += 1

    # moon / ascendant as tiebreakers
    for key in ("moon_element", "asc_element"):
        v = signals.get(key)
        if isinstance(v, str) and v in tally:
            tally[v] += 1

    # pick the winner; ties broken by a stable order
    winner = max(tally.items(), key=lambda kv: (kv[1], -["fire","water","earth","air","metal"].index(kv[0])))
    return winner[0] if winner[1] > 0 else "default"


# ===========================================================================
# SCORING + PICK
# ===========================================================================

def _score_superpowers(signals: Dict[str, Any]) -> Dict[str, int]:
    scores: Dict[str, int] = {}
    for sp, table in _AFFINITY.items():
        s = 0
        for lens_key, weights in table.items():
            val = signals.get(lens_key)
            if val is None:
                continue
            if isinstance(val, list):
                for v in val:
                    s += weights.get(v, 0)
            else:
                s += weights.get(val, 0)
        scores[sp] = s
    return scores


def _pick_superpower(signals: Dict[str, Any], used: Set[str]) -> Tuple[str, int, int]:
    """
    Return (superpower, score, num_lenses_contributing). Never returns a
    used superpower unless the pool is exhausted.
    """
    scores = _score_superpowers(signals)

    # count lenses contributing signal (for confidence)
    lenses_present = sum(
        1 for k in ("hd_type", "enneagram", "bazi_element",
                    "sun_element", "life_path") if signals.get(k) is not None
    )

    # prefer unused; break ties by stable alphabetical order
    candidates = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    for sp, sc in candidates:
        if sp not in used and sp in _POOL:
            return sp, sc, lenses_present

    # pool exhausted — allow reuse
    for sp, sc in candidates:
        if sp in _POOL:
            return sp, sc, lenses_present

    return "Presence", 0, lenses_present


# ===========================================================================
# LINE PICKING
# ===========================================================================

def _pick_lines(sp: str, signals: Dict[str, Any], pattern_state: Optional[str]) -> Tuple[str, str]:
    entry = _POOL[sp]
    l1 = entry["l1"]
    variants: Dict[str, str] = entry["l2"]

    # RECURRING wins if available for this superpower
    if pattern_state == "RECURRING" and "recurring" in variants:
        return l1, variants["recurring"]

    style = _style_key(signals)
    if style in variants:
        return l1, variants[style]
    return l1, variants["default"]


# ===========================================================================
# PATTERN MEMORY
# ===========================================================================

async def _pattern_state(db, user_id: str) -> Optional[str]:
    try:
        count = await db.forum_reflections.count_documents({"user_id": user_id})
    except Exception:
        return None
    if count >= 3: return "RECURRING"
    if count >= 1: return "RETURNING"
    return None


# ===========================================================================
# PUBLIC API
# ===========================================================================

async def get_forum_contributions(db, forum_id: str) -> List[Dict[str, Any]]:
    if not ObjectId.is_valid(forum_id):
        return []
    forum = await db.forums.find_one({"_id": ObjectId(forum_id)})
    if not forum:
        return []
    creator_id = forum.get("created_by")

    memberships = await db.forum_members.find({
        "forum_id": forum_id, "status": "active",
    }).to_list(500)

    def sort_key(m):
        return (0 if m.get("user_id") == creator_id else 1, m.get("joined_at") or 0)
    memberships.sort(key=sort_key)

    used: Set[str] = set()
    out: List[Dict[str, Any]] = []

    for m in memberships:
        uid = m.get("user_id")
        if not uid or not ObjectId.is_valid(uid):
            continue
        user = await db.users.find_one({"_id": ObjectId(uid)})
        if not user:
            continue

        name = (user.get("name") or "").strip() or "Member"
        chart = await db.charts.find_one({"user_id": uid}) or {}

        signals = _collect_signals(user, chart)
        superpower, score, lenses_present = _pick_superpower(signals, used)
        used.add(superpower)

        pattern_state = await _pattern_state(db, uid)
        l1, l2 = _pick_lines(superpower, signals, pattern_state)

        # Confidence signal — fewer lenses means softer framing. For now we
        # keep the lines as-is; the signal is just exposed in the payload
        # so future clients can visualise confidence if they want.
        confidence = (
            "high" if lenses_present >= 4 else
            "medium" if lenses_present >= 2 else
            "low"
        )

        out.append({
            "member_id": uid,
            "name": name,
            "is_host": uid == creator_id,
            # v3 preferred fields
            "superpower": superpower,
            "lines": [l1, l2],
            "synthesis": {
                "score": score,
                "lenses_present": lenses_present,
                "confidence": confidence,
                "pattern_state": pattern_state,
            },
            # legacy compat
            "items": [{"title": superpower, "description": f"{l1} {l2}"}],
            "attributes": [superpower.upper()],
            "primary_label": l1,
        })

    return out
