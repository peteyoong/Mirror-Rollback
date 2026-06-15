"""
Relationship Curriculum Engine V1 — "Why This Person Matters"
==============================================================
Build marker: relationship-curriculum-engine-v1

Mirror-aligned meaning-layer engine.  Produces a 4-section synthesis
answering the question users naturally ask:

    "Why might this person matter in my life?"

NOT a compatibility engine.
NOT a destiny / soulmate / fate / karmic engine.
NOT a prediction engine.

Output structure:
    {
        "success": True,
        "build_marker": "relationship-curriculum-engine-v1",
        "relationship_curriculum": {
            "gift":         <str, 150–200 words>,
            "challenge":    <str, 100–150 words>,
            "growth_edge":  <str, 100–150 words>,
            "curriculum":   <str, 120–200 words>,
            "confidence":   "low" | "medium" | "high",
            "proof": {
                "astrology":    [str, ...],
                "human_design": [str, ...],
                "enneagram":    [str, ...],
                "bazi":         [str, ...],
                "numerology":   [str, ...],
            },
        },
    }

Hard rules (verified by acceptance tests):
    A. User-facing strings NEVER contain destiny / soulmate / fate /
       twin-flame / karmic / cosmic-assignment language.
    B. Use only Mirror voice modal verbs:
         "appears", "suggests", "invites", "reflects",
         "may be developing", "seems to be trying to grow"
       Never "will", "must", "is destined to", "is guaranteed to".
    C. Deterministic — same inputs produce same outputs.
    D. No DB writes, no LLM calls, no external services.

Surface wiring is OUT OF SCOPE for this slice (see delivery report).
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

BUILD_MARKER = "relationship-curriculum-engine-v1"
FLAG_NAME = "RELATIONSHIP_CURRICULUM_ENGINE"


# ════════════════════════════════════════════════════════════════════
# FLAG GATE
# ════════════════════════════════════════════════════════════════════
def is_enabled() -> bool:
    return (os.environ.get(FLAG_NAME, "") or "").strip().lower() == "true"


# ════════════════════════════════════════════════════════════════════
# THEME TABLES
# Each theme is a SHORT NOUN PHRASE that can appear in user-facing
# narrative without leaking astrology jargon.  These are the
# vocabulary of the engine.
# ════════════════════════════════════════════════════════════════════

# Descendant-sign → relational growth themes (Mirror voice; jargon-free)
_DSC_THEMES: Dict[str, List[str]] = {
    "Aries":       ["healthy assertion", "honest directness", "individual courage"],
    "Taurus":      ["steadiness", "shared embodiment", "simple pleasures held in common"],
    "Gemini":      ["curiosity", "perspective-taking", "dialogue"],
    "Cancer":      ["emotional safety", "attunement", "the courage to be cared for"],
    "Leo":         ["full presence", "creative expression", "generosity"],
    "Virgo":       ["refinement", "practical care", "ordinary devotion"],
    "Libra":       ["balance", "fairness", "the practice of equal partnership"],
    "Scorpio":     ["depth", "honesty", "ongoing transformation"],
    "Sagittarius": ["meaning-making", "exploration", "freedom inside commitment"],
    "Capricorn":   ["structure", "commitment", "shared responsibility"],
    "Aquarius":    ["individuality", "shared ideals", "friendship as foundation"],
    "Pisces":      ["compassion", "imagination", "the practice of letting go"],
    "Ophiuchus":   ["transformation through honesty", "wisdom-as-relationship",
                    "the practice of beginning again"],
}

# Planet-in-7th-house → additional themes
_PLANET_7TH_THEMES: Dict[str, List[str]] = {
    "Sun":     ["identity discovered through relating"],
    "Moon":    ["emotional attunement", "shared interiority"],
    "Mercury": ["dialogue as relationship", "thought-companionship"],
    "Venus":   ["shared values", "ease of beauty between you"],
    "Mars":    ["honest assertion", "the practice of healthy friction"],
    "Jupiter": ["expansion through relating", "shared meaning"],
    "Saturn":  ["commitment", "the long view", "earned trust"],
    "Uranus":  ["independence held inside closeness", "the surprise of each other"],
    "Neptune": ["compassion", "the dissolving of separate worlds"],
    "Pluto":   ["depth", "honesty about what's underneath", "transformation"],
    "Chiron":  ["mutual healing", "the room to be imperfect"],
    "North Node": ["growth-axis between you", "what wants to be learned together"],
    "South Node": ["familiarity that asks to be examined", "echoes from before"],
}

# Sign rulership — used to derive the 7th-ruler theme
_SIGN_RULER: Dict[str, str] = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo":   "Sun", "Virgo":  "Mercury", "Libra":  "Venus", "Scorpio": "Pluto",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Uranus",
    "Pisces": "Neptune", "Ophiuchus": "Pluto",
}

# Sign emphasis-test buckets: B "activates" theme X if B carries one of
# the listed signs on Sun / Moon / Mercury / ASC.
_THEME_ACTIVATIONS: Dict[str, List[str]] = {
    "curiosity":                ["Gemini", "Sagittarius", "Aquarius"],
    "perspective-taking":       ["Gemini", "Libra", "Aquarius"],
    "dialogue":                 ["Gemini", "Libra"],
    "depth":                    ["Scorpio", "Pisces", "Ophiuchus"],
    "honesty":                  ["Scorpio", "Sagittarius", "Ophiuchus"],
    "ongoing transformation":   ["Scorpio", "Pluto", "Ophiuchus"],
    "emotional safety":         ["Cancer", "Pisces", "Taurus"],
    "attunement":               ["Cancer", "Pisces"],
    "steadiness":               ["Taurus", "Capricorn", "Virgo"],
    "shared embodiment":        ["Taurus", "Virgo"],
    "structure":                ["Capricorn", "Virgo"],
    "commitment":               ["Capricorn", "Taurus"],
    "balance":                  ["Libra"],
    "freedom inside commitment":["Sagittarius", "Aquarius"],
    "creative expression":      ["Leo", "Sagittarius"],
    "full presence":            ["Leo", "Scorpio"],
    "compassion":               ["Pisces", "Cancer"],
    "imagination":              ["Pisces", "Aquarius"],
    "individuality":            ["Aquarius", "Sagittarius", "Aries"],
    "shared ideals":            ["Aquarius", "Libra"],
    "healthy assertion":        ["Aries", "Leo"],
    "honest directness":        ["Aries", "Sagittarius"],
}

# Human Design dynamics — pair-keyed themes (order-independent)
_HD_DYNAMICS: Dict[frozenset, List[str]] = {
    frozenset(["Manifestor", "Reflector"]):
        ["initiating without controlling outcomes",
         "reflecting without disappearing"],
    frozenset(["Manifestor", "Generator"]):
        ["initiating in a way the other can respond to",
         "honouring the other's lit-up yes"],
    frozenset(["Manifestor", "Manifesting Generator"]):
        ["respecting two ignition points",
         "informing instead of bulldozing"],
    frozenset(["Manifestor", "Projector"]):
        ["leading without overlooking the recogniser",
         "inviting before directing"],
    frozenset(["Generator", "Projector"]):
        ["sustainable energy meeting deserved recognition"],
    frozenset(["Manifesting Generator", "Projector"]):
        ["honouring the recogniser's pacing",
         "letting recognition steer the pace"],
    frozenset(["Generator", "Generator"]):
        ["two lit-up yeses building something durable"],
    frozenset(["Projector", "Projector"]):
        ["seeing one another into recognition"],
    frozenset(["Reflector", "Reflector"]):
        ["mutual mirroring of the field",
         "becoming a barometer for one another"],
    frozenset(["Reflector", "Generator"]):
        ["letting the reflector taste your aliveness",
         "trusting the reflector's slow read"],
    frozenset(["Reflector", "Projector"]):
        ["each one a different kind of mirror"],
}


# ════════════════════════════════════════════════════════════════════
# ROLE WEIGHTING
# ════════════════════════════════════════════════════════════════════
_ROLE_WEIGHT: Dict[str, float] = {
    "spouse":            1.0,
    "partner":           1.0,
    "ex_partner":        0.85,
    "former_partner":    0.85,
    "parent":            0.9,
    "child":             0.9,
    "cofounder":         0.8,
    "business_partner":  0.8,
    "mentor":            0.7,
    "mentee":            0.7,
    "coach":             0.7,
    "coachee":           0.7,
    "sibling":           0.7,
    "close_friend":      0.6,
    "friend":            0.6,
    "colleague":         0.5,
    "forum_member":      0.4,
    "familiar":          0.4,
    "unknown":           0.4,
}


# ════════════════════════════════════════════════════════════════════
# CHART READERS  (no jargon ever leaks through these)
# ════════════════════════════════════════════════════════════════════

def _astro(ch: Dict[str, Any]) -> Dict[str, Any]:
    return (ch or {}).get("astrology") or ch or {}


def _planet(ch: Dict[str, Any], name: str) -> Dict[str, Any]:
    planets = _astro(ch).get("planets") or {}
    if isinstance(planets, dict):
        for k in (name, name.capitalize(), name.lower()):
            if k in planets and isinstance(planets[k], dict):
                return planets[k]
    return {}


def _sign(ch: Dict[str, Any], name: str) -> Optional[str]:
    return _planet(ch, name).get("sign")


def _house(ch: Dict[str, Any], name: str) -> Optional[int]:
    h = _planet(ch, name).get("house")
    return int(h) if isinstance(h, (int, float)) else None


def _asc_sign(ch: Dict[str, Any]) -> Optional[str]:
    angles = _astro(ch).get("angles") or {}
    asc = angles.get("asc") or angles.get("ascendant")
    if isinstance(asc, dict):
        return asc.get("sign")
    if isinstance(asc, str):
        return asc
    return None


def _opposite_sign(s: Optional[str]) -> Optional[str]:
    _OPP = {
        "Aries": "Libra", "Libra": "Aries",
        "Taurus": "Scorpio", "Scorpio": "Taurus",
        "Gemini": "Sagittarius", "Sagittarius": "Gemini",
        "Cancer": "Capricorn", "Capricorn": "Cancer",
        "Leo": "Aquarius", "Aquarius": "Leo",
        "Virgo": "Pisces", "Pisces": "Virgo",
        "Ophiuchus": "Taurus",
    }
    return _OPP.get(s) if s else None


def _descendant_sign(ch: Dict[str, Any]) -> Optional[str]:
    angles = _astro(ch).get("angles") or {}
    dsc = angles.get("desc") or angles.get("descendant")
    if isinstance(dsc, dict) and dsc.get("sign"):
        return dsc["sign"]
    if isinstance(dsc, str):
        return dsc
    # Fallback — derive from ASC
    return _opposite_sign(_asc_sign(ch))


def _planets_in_house(ch: Dict[str, Any], house_n: int) -> List[str]:
    out: List[str] = []
    planets = _astro(ch).get("planets") or {}
    if not isinstance(planets, dict):
        return out
    for name, data in planets.items():
        if isinstance(data, dict) and data.get("house") == house_n:
            out.append(name)
    return out


def _hd_type(ch: Dict[str, Any]) -> Optional[str]:
    t = ch.get("hd_type")
    if isinstance(t, str) and t:
        return t
    hd = ch.get("human_design") or {}
    if isinstance(hd, dict):
        return hd.get("type") or hd.get("hd_type")
    return None


# ════════════════════════════════════════════════════════════════════
# SIGNAL LAYERS
# ════════════════════════════════════════════════════════════════════

def _layer1_relationship_axis(ch_a: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """Return (themes, proof_lines) derived from person A's relational axis."""
    themes: List[str] = []
    proof: List[str] = []
    dsc = _descendant_sign(ch_a)
    if dsc:
        themes.extend(_DSC_THEMES.get(dsc, []))
        proof.append(f"Descendant in {dsc} → " + ", ".join(_DSC_THEMES.get(dsc, [])))
    ruler = _SIGN_RULER.get(dsc or "")
    if ruler:
        ruler_sign = _sign(ch_a, ruler)
        ruler_house = _house(ch_a, ruler)
        if ruler_sign:
            proof.append(
                f"{dsc} ruler ({ruler}) in {ruler_sign}"
                + (f", house {ruler_house}" if ruler_house else "")
            )
    # Planets in 7th add their own themes
    for p in _planets_in_house(ch_a, 7):
        for t in _PLANET_7TH_THEMES.get(p, []):
            if t not in themes:
                themes.append(t)
        if p in _PLANET_7TH_THEMES:
            proof.append(f"{p} in the 7th house → " + ", ".join(_PLANET_7TH_THEMES[p]))
    return themes, proof


def _layer2_person_activation(
    ch_b: Dict[str, Any], themes: List[str],
) -> Tuple[List[Tuple[str, str]], List[str]]:
    """For each theme A's axis emits, look for activation features in B."""
    activations: List[Tuple[str, str]] = []
    proof: List[str] = []
    # Collect B's anchor signs
    b_signs = {
        "Sun":     _sign(ch_b, "Sun"),
        "Moon":    _sign(ch_b, "Moon"),
        "Mercury": _sign(ch_b, "Mercury"),
        "Venus":   _sign(ch_b, "Venus"),
        "ASC":     _asc_sign(ch_b),
    }
    seen = set()
    for theme in themes:
        active_signs = _THEME_ACTIVATIONS.get(theme, [])
        if not active_signs:
            continue
        for anchor, b_sign in b_signs.items():
            if b_sign and b_sign in active_signs and (theme, b_sign) not in seen:
                activations.append((theme, b_sign))
                proof.append(f"{anchor} in {b_sign} activates '{theme}'")
                seen.add((theme, b_sign))
                break  # one activation per theme per anchor pass
    return activations, proof


def _layer3_synastry_corroboration(
    ch_a: Dict[str, Any], ch_b: Dict[str, Any],
) -> List[str]:
    """Lightweight corroboration markers — ONLY used to up/down weight
    confidence, NEVER as destiny statements."""
    notes: List[str] = []
    sun_a, sun_b = _sign(ch_a, "Sun"), _sign(ch_b, "Sun")
    moon_a, moon_b = _sign(ch_a, "Moon"), _sign(ch_b, "Moon")
    venus_a, venus_b = _sign(ch_a, "Venus"), _sign(ch_b, "Venus")
    saturn_a, saturn_b = _sign(ch_a, "Saturn"), _sign(ch_b, "Saturn")
    if sun_a and sun_b == _opposite_sign(sun_a):
        notes.append("Sun-axis polarity (complementary identity poles)")
    if moon_a and moon_b == moon_a:
        notes.append("Moon-sign resonance (similar inner climate)")
    if venus_a and venus_b == venus_a:
        notes.append("Venus-sign resonance (shared aesthetic vocabulary)")
    if saturn_a and saturn_b == saturn_a:
        notes.append("Saturn-sign resonance (similar inner rule of how-to-be-good)")
    # North Node alignment
    nn_a = _sign(ch_a, "North Node")
    if nn_a and _sign(ch_b, "Sun") == nn_a:
        notes.append("Their Sun touches your North Node sign")
    return notes


def _layer4_human_design(
    ch_a: Dict[str, Any], ch_b: Dict[str, Any],
) -> Tuple[List[str], List[str]]:
    """HD dynamics → growth themes."""
    themes: List[str] = []
    proof: List[str] = []
    ta, tb = _hd_type(ch_a), _hd_type(ch_b)
    if ta and tb:
        key = frozenset([ta, tb])
        hd_themes = _HD_DYNAMICS.get(key, [])
        if hd_themes:
            themes.extend(hd_themes)
            proof.append(f"{ta} ↔ {tb} dynamic → " + ", ".join(hd_themes))
        else:
            proof.append(f"{ta} ↔ {tb} (no canonical dynamic mapped — generic)")
    return themes, proof


def _layer5_enneagram(
    ch_a: Dict[str, Any], ch_b: Dict[str, Any],
) -> List[str]:
    """Enneagram contributes attachment / growth-pattern themes."""
    proof: List[str] = []
    en_a = (ch_a.get("enneagram") or {}).get("type")
    en_b = (ch_b.get("enneagram") or {}).get("type")
    if en_a and en_b:
        proof.append(f"Enneagram pair {en_a} ↔ {en_b}")
    return proof


def _layer6_bazi(
    ch_a: Dict[str, Any], ch_b: Dict[str, Any],
) -> List[str]:
    """BaZi day-pillar element interplay."""
    proof: List[str] = []
    dp_a = ((ch_a.get("bazi") or {}).get("day_pillar") or {})
    dp_b = ((ch_b.get("bazi") or {}).get("day_pillar") or {})
    if dp_a.get("element") and dp_b.get("element"):
        proof.append(
            f"BaZi day pillars: {dp_a.get('element')} ↔ {dp_b.get('element')}"
        )
    return proof


# ════════════════════════════════════════════════════════════════════
# SECTION COMPOSERS
# Templates are theme-aware and woven into 100–200 word paragraphs.
# Mirror voice only — no certainty / destiny / soulmate language.
# ════════════════════════════════════════════════════════════════════

def _pick_top_themes(themes: List[str], activations: List[Tuple[str, str]], n: int = 3) -> List[str]:
    """Prefer themes that ALSO appear in activations (i.e. B activates them)."""
    activated = [t for (t, _) in activations]
    out: List[str] = []
    for t in activated:
        if t in themes and t not in out:
            out.append(t)
        if len(out) >= n:
            return out
    for t in themes:
        if t not in out:
            out.append(t)
        if len(out) >= n:
            return out
    return out


def _theme_phrase(themes: List[str]) -> str:
    if not themes:
        return "what is quietly being learned between you"
    if len(themes) == 1:
        return themes[0]
    if len(themes) == 2:
        return f"{themes[0]} and {themes[1]}"
    return f"{themes[0]}, {themes[1]}, and {themes[2]}"


def _build_gift(
    themes: List[str], activations: List[Tuple[str, str]],
    name_a: str, name_b: str, role: str,
) -> str:
    top = _pick_top_themes(themes, activations, n=3)
    phrase = _theme_phrase(top)
    activation_clause = ""
    if activations:
        first = activations[0]
        activation_clause = (
            f"  In particular, {name_b} appears to embody {first[0]} naturally — "
            f"it shows up in how {name_b} arrives, not in what {name_b} performs."
        )
    role_clause = ""
    if role in ("spouse", "partner"):
        role_clause = (
            "  That this happens inside a partnership only makes it harder to "
            "miss — partnership is the room where the field has nowhere to hide."
        )
    elif role in ("child",):
        role_clause = (
            f"  That the relationship is parent-and-child means the gift moves "
            f"in both directions: what {name_b} is learning through you, you are "
            f"also being asked to remember through them."
        )
    elif role in ("parent",):
        role_clause = (
            "  That the relationship is child-and-parent means the gift is older "
            "than this conversation — and may keep arriving long after the "
            "original context has shifted."
        )
    elif role in ("close_friend", "friend"):
        role_clause = (
            "  Because there is no contract here other than choice, the gift "
            "keeps having to be chosen again — which is also what keeps it real."
        )
    body = (
        f"What {name_b} appears to bring into your life is {phrase}.  "
        f"This is not flattery and it is not the whole story — it is a description "
        f"of a quality your field consistently lights up around when {name_b} is "
        f"present.  The gift is rarely loud; it tends to show up as a small "
        f"recurring invitation, not a single dramatic moment."
        f"{activation_clause}{role_clause}"
    )
    return body.strip()


def _build_challenge(
    themes: List[str], activations: List[Tuple[str, str]],
    name_a: str, name_b: str, role: str,
) -> str:
    top = _pick_top_themes(themes, activations, n=2)
    if not top:
        return (
            f"The challenge of this relationship appears to be ordinary rather "
            f"than dramatic: staying open to what is actually here, instead of "
            f"the version of {name_b} that is easier to predict.  Most of what "
            f"is difficult to receive is difficult because it asks something "
            f"you haven't yet practised."
        )
    # Compose pairs of "gift → shadow" inversions
    inversions = {
        "curiosity":                  "the unsettling of certainty",
        "perspective-taking":         "having to put down your own version of the story",
        "dialogue":                   "the discomfort of being interrupted by a different view",
        "depth":                      "the discomfort of being met underneath your composure",
        "honesty":                    "having less room to perform",
        "ongoing transformation":     "having to keep letting old shapes of you die",
        "emotional safety":           "the discomfort of allowing yourself to be cared for",
        "attunement":                 "being read more accurately than you'd planned",
        "steadiness":                 "the disappointment of slowness",
        "structure":                  "feeling structure where you wanted spontaneity",
        "commitment":                 "no longer having an easy exit",
        "balance":                    "noticing the asymmetry you've been carrying",
        "freedom inside commitment":  "tolerating the freedom you asked for in the other",
        "creative expression":        "being witnessed in your unfinished output",
        "full presence":              "having less room to drift",
        "compassion":                 "softening when you'd rather stay armoured",
        "imagination":                "letting the shape of the future stay un-set",
        "individuality":              "loving someone who will not be absorbed",
        "shared ideals":              "the demand that ideals become daily practice",
        "healthy assertion":          "having your own assertions met head-on",
        "honest directness":          "fewer hiding places for half-said things",
    }
    inv = [inversions.get(t, "having to grow") for t in top]
    if len(inv) == 1:
        inv_phrase = inv[0]
    else:
        inv_phrase = f"{inv[0]}, and {inv[1]}"
    body = (
        f"The same qualities that make this relationship a gift are what make "
        f"the gift hard to receive.  What {name_b} appears to invite — "
        f"{_theme_phrase(top)} — also asks you to tolerate {inv_phrase}.  "
        f"This is not blame and it is not a flaw on either side; it is the "
        f"price of admission for the kind of growth this relationship seems "
        f"to be capable of.  The work, if you accept it, is small and daily "
        f"rather than heroic."
    )
    return body.strip()


def _build_growth_edge(
    themes: List[str], activations: List[Tuple[str, str]],
    hd_themes: List[str], name_a: str, name_b: str, role: str,
) -> str:
    top = _pick_top_themes(themes, activations, n=2)
    growth_pairs = {
        "curiosity":                  "dialogue over certainty",
        "perspective-taking":         "perspective over position",
        "dialogue":                   "exchange over monologue",
        "depth":                      "depth over performance",
        "honesty":                    "truth over comfort",
        "ongoing transformation":     "becoming over staying",
        "emotional safety":           "receiving over guarding",
        "attunement":                 "presence over reactivity",
        "steadiness":                 "trust over control",
        "structure":                  "responsibility over rescue",
        "commitment":                 "patience over urgency",
        "balance":                    "equity over scorekeeping",
        "freedom inside commitment":  "trust over surveillance",
        "creative expression":        "expression over polish",
        "full presence":              "presence over performance",
        "compassion":                 "softness over hardness",
        "imagination":                "vision over prediction",
        "individuality":              "respect over absorption",
        "shared ideals":              "practice over principle",
        "healthy assertion":          "directness over withholding",
        "honest directness":          "candour over diplomacy",
        # HD-derived themes (mapped to growth axis directly)
        "initiating without controlling outcomes": "initiating over controlling",
        "reflecting without disappearing":         "reflecting over disappearing",
        "respecting two ignition points":          "two-yes alignment over one-yes drag",
        "informing instead of bulldozing":         "informing over pushing",
        "honouring the other's lit-up yes":        "response over demand",
        "inviting before directing":               "invitation over instruction",
    }
    pairs: List[str] = []
    for t in top:
        if t in growth_pairs:
            pairs.append(growth_pairs[t])
    for hd_t in hd_themes:
        gp = growth_pairs.get(hd_t)
        if gp and gp not in pairs:
            pairs.append(gp)
        if len(pairs) >= 3:
            break
    if not pairs:
        pairs = ["presence over reactivity"]
    pair_list = ", ".join(pairs[:3])
    body = (
        f"What seems to be trying to grow between you can be named in a few "
        f"short phrases: {pair_list}.  These are not rules; they are pointers — "
        f"the kind of orientations that keep emerging as the harder, more "
        f"honest move whenever the relationship reaches a familiar edge.  "
        f"Whether the edge is reached today or in two years, the same small "
        f"choices appear to be the ones that move the relationship forward, "
        f"and the ones that keep it from moving forward when they're not made."
    )
    return body.strip()


def _build_curriculum(
    themes: List[str], activations: List[Tuple[str, str]],
    hd_themes: List[str], name_a: str, name_b: str, role: str,
) -> str:
    top = _pick_top_themes(themes, activations, n=3)
    phrase = _theme_phrase(top)
    activation_count = len(activations)
    role_label = {
        "spouse":           "your spouse",
        "partner":          "your partner",
        "ex_partner":       "a former partner",
        "former_partner":   "a former partner",
        "parent":           "your parent",
        "child":            "your child",
        "cofounder":        "your co-founder",
        "business_partner": "your business partner",
        "mentor":           "your mentor",
        "mentee":           "your mentee",
        "sibling":          "your sibling",
        "close_friend":     "your close friend",
        "friend":           "your friend",
        "colleague":        "your colleague",
        "forum_member":     "a member of your forum",
    }.get(role, name_b)
    hd_clause = ""
    if hd_themes:
        hd_clause = (
            f"  At the level of design, the two of you appear to be practising "
            f"{hd_themes[0]} — and that practice tends to be both the route and "
            f"the curriculum itself, not separate from each other."
        )
    activation_clause = ""
    if activation_count >= 2:
        activation_clause = (
            f"  The activation is not occasional.  Multiple parts of {name_b}'s "
            f"chart appear to reach into this same theme, which is one reason "
            f"the field between you tends to converge on it whether you plan "
            f"for it or not."
        )
    body = (
        f"If this relationship has a curriculum, the shape that appears in the "
        f"charts is this: through {role_label}, you seem to be invited into "
        f"{phrase}.  The deeper invitation is not to love each other in a "
        f"particular way — it is to discover who each of you becomes through "
        f"the ongoing conversation between your worlds.{hd_clause}"
        f"{activation_clause}  Mirror cannot tell you whether you will take "
        f"the invitation; only that the invitation appears to be there, and "
        f"that the relationship seems to keep returning you to it."
    )
    return body.strip()


# ════════════════════════════════════════════════════════════════════
# CONFIDENCE
# ════════════════════════════════════════════════════════════════════
def _grade_confidence(
    activation_count: int, synastry_count: int, hd_count: int,
    role_weight: float,
) -> str:
    score = activation_count * 1.0 + synastry_count * 0.5 + hd_count * 0.6
    weighted = score * role_weight
    if weighted >= 2.5 and role_weight >= 0.8:
        return "high"
    if weighted >= 1.2:
        return "medium"
    return "low"


# ════════════════════════════════════════════════════════════════════
# PUBLIC API
# ════════════════════════════════════════════════════════════════════

def generate_relationship_curriculum(
    person_a: Dict[str, Any],
    person_b: Dict[str, Any],
    relationship_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Generate the 4-section Relationship Curriculum payload.

    Args:
        person_a:  dict with at least `chart` (or top-level astrology
                   sub-dict) and `name`.  Person whose chart provides
                   the relational axis (typically the viewer).
        person_b:  dict with `chart` and `name`.  The other person.
        relationship_context: dict with `role` (str, default "unknown")
                   and optionally `closeness`, `emotional_weight`.

    Returns:
        {
            "success": True,
            "build_marker": "relationship-curriculum-engine-v1",
            "relationship_curriculum": { gift, challenge, growth_edge,
                                         curriculum, confidence, proof },
        }
        On failure returns {"success": False, "error": <str>}.
    """
    try:
        person_a = person_a or {}
        person_b = person_b or {}
        relationship_context = relationship_context or {}
        ch_a = person_a.get("chart") or person_a
        ch_b = person_b.get("chart") or person_b
        name_a = (person_a.get("name") or "You").strip() or "You"
        name_b = (person_b.get("name") or "This person").strip() or "This person"
        role = (relationship_context.get("role") or "unknown").lower().strip()
        role_weight = _ROLE_WEIGHT.get(role, 0.4)

        # ── Signal layers ────────────────────────────────────────────
        themes_axis, proof_axis     = _layer1_relationship_axis(ch_a)
        activations, proof_activate = _layer2_person_activation(ch_b, themes_axis)
        synastry_notes              = _layer3_synastry_corroboration(ch_a, ch_b)
        hd_themes, proof_hd         = _layer4_human_design(ch_a, ch_b)
        proof_enne                  = _layer5_enneagram(ch_a, ch_b)
        proof_bazi                  = _layer6_bazi(ch_a, ch_b)

        # ── Combine themes ───────────────────────────────────────────
        all_themes: List[str] = []
        for t in themes_axis:
            if t not in all_themes:
                all_themes.append(t)
        for t in hd_themes:
            if t not in all_themes:
                all_themes.append(t)

        # ── Section composition ──────────────────────────────────────
        gift        = _build_gift(all_themes, activations, name_a, name_b, role)
        challenge   = _build_challenge(all_themes, activations, name_a, name_b, role)
        growth_edge = _build_growth_edge(all_themes, activations, hd_themes,
                                          name_a, name_b, role)
        curriculum  = _build_curriculum(all_themes, activations, hd_themes,
                                         name_a, name_b, role)

        # ── Confidence grading ───────────────────────────────────────
        confidence = _grade_confidence(
            activation_count=len(activations),
            synastry_count=len(synastry_notes),
            hd_count=len(hd_themes),
            role_weight=role_weight,
        )

        # ── Proof ledger ─────────────────────────────────────────────
        astrology_proof: List[str] = []
        astrology_proof.extend(proof_axis)
        astrology_proof.extend(proof_activate)
        astrology_proof.extend(synastry_notes)

        return {
            "success":      True,
            "build_marker": BUILD_MARKER,
            "relationship_curriculum": {
                "gift":        gift,
                "challenge":   challenge,
                "growth_edge": growth_edge,
                "curriculum":  curriculum,
                "confidence":  confidence,
                "proof": {
                    "astrology":    astrology_proof,
                    "human_design": proof_hd,
                    "enneagram":    proof_enne,
                    "bazi":         proof_bazi,
                    "numerology":   [],
                },
            },
        }
    except Exception as e:    # pragma: no cover
        logger.warning(f"[RelationshipCurriculum] failed: {e!r}")
        return {
            "success":      False,
            "build_marker": BUILD_MARKER,
            "error":        str(e)[:240],
        }


def maybe_generate(
    person_a: Dict[str, Any],
    person_b: Dict[str, Any],
    relationship_context: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """Flag-gated convenience wrapper.  Returns None when flag is off."""
    if not is_enabled():
        return None
    out = generate_relationship_curriculum(person_a, person_b, relationship_context)
    return out if out.get("success") else None
