"""
Relationship Field Architecture v1
==================================

Activation-first synthesizer for "How They Map To You".

Reads the per-lens signals that services.forum_hd_mapping already computes
(HD channels + astrology + bazi + enneagram + numerology) plus three NEW
astrology amplifier inputs (Juno / North Node / Vertex synastry), and
produces a SINGLE relationship-field envelope that answers the user's
question:

    "What happens between us?"

…BEFORE any technical evidence is shown.

KEY PRODUCT RULES
-----------------
1. Activation-first, not friction-first.  The opening sentence MUST
   describe what activates in this pair — not what conflicts.
2. Synthesize the field BEFORE evidence.  We name the feel of the pair
   before naming HD channels, aspects, or animal pairs.
3. Cluster signals into 2-4 human themes (label + what_lives_here +
   friction_inside_it).  Friction is contextualised inside a theme,
   never broken out as a separate list at the top.
4. Always include a "Gift of this connection" line.
5. Move technical channel / aspect / animal labels into the evidence
   drawer (frontend handles this by reading mapping.signals.* like
   today — we do not touch those keys).
6. This is NOT compatibility scoring.  We never emit "good fit / bad
   fit / 7/10 / strong / weak compatibility / they're your match" etc.
7. Juno / North Node / Vertex are SIGNIFICANCE AMPLIFIERS ONLY.
   They raise the stakes of a theme that already exists in the field.
   They are NEVER soulmate / fate / destiny / karmic indicators.
8. Strict prose sanitizer rejects forbidden vocabulary and re-asks the
   caller to drop the line (silently — we simply suppress).

ENVELOPE SHAPE
--------------
The synthesizer returns a dict that the route attaches under
``mapping["field"]``::

    {
        "version": "relationship-field-v1",
        "field_paragraph": str,           # 1 short paragraph, activation-first
        "activation": str,                # one-line "what activates here"
        "themes": [                       # 2-4 themed clusters
            {
                "label": str,             # human, no jargon (e.g. "Quiet trust")
                "what_lives_here": str,   # 1-2 sentences, behavioural
                "friction_inside_it": Optional[str],  # contextualised friction
            },
            ...
        ],
        "gift_of_this_connection": str,   # 1 line
        "amplifiers": {                   # significance amplifiers only
            "juno":        Optional[str],
            "north_node":  Optional[str],
            "vertex":      Optional[str],
        },
    }

If absolutely nothing surfaces (extremely rare — the synthesizer
guarantees a field_paragraph from whatever signals exist), the
function returns ``None`` and the caller skips the ``field`` key
entirely.  Old keys (story / patterns / signals) remain byte-identical
on the mapping object — additive, never destructive.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Prose guardrail / sanitizer
# ---------------------------------------------------------------------------

# Forbidden vocabulary — any line containing one of these (case-insensitive,
# whole-word) is rejected by the sanitizer.  Amplifier lines are the most
# likely to drift into this register; the sanitizer is a backstop.
_FORBIDDEN_TERMS = [
    r"\bsoulmate[s]?\b",
    r"\btwin\s+flame[s]?\b",
    r"\bdestin(?:y|ed|ied)\b",
    r"\bfated?\b",
    r"\bfate[s]?\b",
    r"\bkarmic\b",
    r"\bkarma\b",
    r"\bpast[-\s]?life\b",
    r"\bpast[-\s]?lives\b",
    r"\bcosmic\s+pull\b",
    r"\bwritten\s+in\s+the\s+stars\b",
    r"\bmeant\s+to\s+be\b",
    r"\bdivinely?\b",
    r"\b(?:perfect|ideal)\s+match\b",
    r"\bcompatibilit(?:y|ies)\b",
    r"\bcompatible\b",
    r"\bincompatible\b",
]
_FORBIDDEN_RE = re.compile("|".join(_FORBIDDEN_TERMS), re.IGNORECASE)


# Shadow-heavy / framework-jargon vocabulary — substituted (not suppressed)
# with neutral relational language.  This keeps the descriptive text on the
# channel/signal cards readable instead of removing whole lines.  Ordering
# matters: longer/more-specific phrases are matched first so we don't end
# up double-substituting (e.g. "materialism" replaced before "material").
#
# Banned terms come from the product copy spec:
#   materialism, control, manipulation, domination, lack, selfishness,
#   weakness, failure.
# Replacements lean into the neutral palette:
#   responsibility, rhythm, pressure, trust, direction, resources,
#   protection, intimacy, timing, agreements, repair, expression,
#   steadiness, movement.
_SHADOW_SUBSTITUTIONS: List[tuple] = [
    # Multi-word phrases first (so "willpower for resources" isn't left
    # alone after we strip "control"):
    (re.compile(r"\bwillpower\s+for\s+resources\b", re.IGNORECASE),
     "the will to provide"),
    (re.compile(r"\bcontrol\s+dynamics?\b", re.IGNORECASE),
     "responsibility and direction"),
    (re.compile(r"\bcontrol\s+become[sn]?\b", re.IGNORECASE),
     "responsibility becomes"),
    (re.compile(r"\bpower\s+imbalance\b", re.IGNORECASE),
     "uneven sense of responsibility"),
    (re.compile(r"\bemotional\s+manipulation\b", re.IGNORECASE),
     "emotional influence"),
    # Single words — only stripped where they read user-facing.  We keep the
    # substitution conservative so prose stays grammatical.
    (re.compile(r"\bmaterialism\b", re.IGNORECASE),                "resources"),
    (re.compile(r"\bmaterialistic\b", re.IGNORECASE),              "resource-focused"),
    (re.compile(r"\bmanipulation\b", re.IGNORECASE),               "influence"),
    (re.compile(r"\bmanipulative\b", re.IGNORECASE),               "influencing"),
    (re.compile(r"\bdomination\b", re.IGNORECASE),                 "leading"),
    (re.compile(r"\bdominating\b", re.IGNORECASE),                 "leading"),
    (re.compile(r"\bselfishness\b", re.IGNORECASE),                "self-focus"),
    (re.compile(r"\bselfish\b", re.IGNORECASE),                    "self-focused"),
    (re.compile(r"\bweakness\b", re.IGNORECASE),                   "tender spot"),
    (re.compile(r"\bfailure\b", re.IGNORECASE),                    "setback"),
    # "control" alone is broad — only substitute when it appears in the
    # noun sense ("of control", "for control", "and control", ", control,").
    # We avoid touching verbs like "to control" so callers can still
    # describe behaviours.  Keep it tight to nominal usage to preserve
    # grammar.
    (re.compile(r"\b(of|for|and|over|about|in)\s+control\b", re.IGNORECASE),
     r"\1 direction"),
    # Comma-list context: "..., control, ..." → "..., direction, ..."
    # Common in keyword strings like "materialism, control, willpower".
    (re.compile(r",\s*control\s*,", re.IGNORECASE),
     ", direction,"),
    (re.compile(r",\s*control\s*$", re.IGNORECASE),
     ", direction"),
    # "lack" used as a noun in shadow framing ("a lack of trust") rewrites
    # cleanly to "a gap in trust"; verb usage ("you lack X") is rarer in
    # the channel templates so we accept the rare false positive.
    (re.compile(r"\ba\s+lack\s+of\b", re.IGNORECASE),              "a gap in"),
    (re.compile(r"\black\s+of\b", re.IGNORECASE),                  "gap in"),
]


# Article-grammar fix-up — substitutions can leave "a uneven" / "a influence"
# in place where it ought to be "an".  Cheap two-pass regex repair.
_AN_FIXUPS = [
    (re.compile(r"\ba\s+(uneven|influence|influencing|influencer)\b", re.IGNORECASE),
     r"an \1"),
    (re.compile(r"\bA\s+(uneven|influence|influencing|influencer)\b"),
     r"An \1"),
]


def _sanitize_shadow_words(line: Optional[str]) -> Optional[str]:
    """
    Replace shadow-heavy framework words with neutral relational terms.
    Returns the rewritten line (does NOT suppress).  Intended to run on
    every user-visible channel theme / signal subtitle before the strict
    suppression sanitizer.
    """
    if not isinstance(line, str) or not line:
        return line
    out = line
    for rx, repl in _SHADOW_SUBSTITUTIONS:
        out = rx.sub(repl, out)
    for rx, repl in _AN_FIXUPS:
        out = rx.sub(repl, out)
    # Collapse any double-spaces introduced by substitutions.
    out = re.sub(r"\s{2,}", " ", out).strip()
    return out or None


def _sanitize_line(line: Optional[str]) -> Optional[str]:
    """
    Return the line unchanged if it passes the guardrail, else None.

    Pipeline:
      1. Shadow-word substitution (soft pass — rewrites banned framework
         vocabulary like "materialism", "control dynamics", "weakness"
         into neutral relational language).
      2. Strict forbidden-vocab suppression (rejects soulmate / fate /
         compatibility framing entirely).

    The sanitizer is intentionally STRICT on step 2: we'd rather emit no
    amplifier line than emit one with forbidden vocabulary.  Logs the
    rejection at info level so we can monitor it.
    """
    if not line or not isinstance(line, str):
        return None
    # Step 1: soft shadow-word substitution.
    rewritten = _sanitize_shadow_words(line) or ""
    if not rewritten:
        return None
    # Step 2: hard suppression for soulmate / fate / compatibility framing.
    if _FORBIDDEN_RE.search(rewritten):
        logger.info(
            f"[RelationshipField] Sanitizer suppressed line containing forbidden "
            f"vocabulary: {rewritten[:80]!r}"
        )
        return None
    return rewritten.strip() or None


# ---------------------------------------------------------------------------
# Astrology amplifier helpers
# ---------------------------------------------------------------------------

_SIGN_ORDER = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

# Tight orbs — amplifiers must be specific, not loose.
_AMP_ASPECTS = {
    "conjunction": {"angle": 0,   "orb": 6},
    "opposition":  {"angle": 180, "orb": 6},
    "trine":       {"angle": 120, "orb": 5},
    "square":      {"angle": 90,  "orb": 5},
}


def _abs_degree(planet: Optional[Dict[str, Any]]) -> Optional[float]:
    if not planet:
        return None
    sign = planet.get("sign", "")
    deg = planet.get("degree")
    if sign not in _SIGN_ORDER or deg is None:
        # Fall back to longitude if explicitly provided
        lon = planet.get("longitude")
        if isinstance(lon, (int, float)):
            return float(lon)
        return None
    return _SIGN_ORDER.index(sign) * 30 + float(deg)


def _aspect_between(a: Optional[Dict[str, Any]], b: Optional[Dict[str, Any]]) -> Optional[str]:
    deg_a = _abs_degree(a)
    deg_b = _abs_degree(b)
    if deg_a is None or deg_b is None:
        return None
    diff = abs(deg_a - deg_b)
    if diff > 180:
        diff = 360 - diff
    for name, defn in _AMP_ASPECTS.items():
        if abs(diff - defn["angle"]) <= defn["orb"]:
            return name
    return None


def _planet(planets: Dict[str, Any], name: str) -> Optional[Dict[str, Any]]:
    if not planets:
        return None
    for key in (name, name.capitalize(), name.lower()):
        if key in planets:
            return planets[key]
    return None


def _get_north_node(astro: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Resolve North Node across all storage variants used in the codebase."""
    if not astro:
        return None
    nodes = astro.get("nodes") or {}
    nn = nodes.get("north") or nodes.get("north_node")
    if nn and nn.get("sign"):
        return nn
    planets = astro.get("planets") or {}
    for key in ("North Node", "True Node", "Mean Node", "GC"):
        if key in planets and planets[key].get("sign"):
            return planets[key]
    return None


def _get_vertex(astro: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    angles = (astro or {}).get("angles") or {}
    vx = angles.get("vertex")
    if vx and vx.get("sign"):
        return vx
    return None


def _get_juno(astro: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    planets = (astro or {}).get("planets") or {}
    j = planets.get("Juno") or planets.get("juno")
    if j and j.get("sign"):
        return j
    return None


def compute_juno_amplifier(
    astro_a: Dict[str, Any],
    astro_b: Dict[str, Any],
    name_b: str,
) -> Optional[str]:
    """
    Juno amplifier: surfaces ONLY when Juno-of-A contacts a personal
    point of B (Sun / Moon / Venus / Asc) within tight orb.

    Returns a single short line framed as significance, NEVER as
    soulmate / fate / partnership-promise.  Returns None if no
    amplifier-grade contact is found OR if Juno is not stored on
    either chart.
    """
    juno_a = _get_juno(astro_a)
    juno_b = _get_juno(astro_b)
    if not juno_a and not juno_b:
        return None

    planets_a = (astro_a or {}).get("planets") or {}
    planets_b = (astro_b or {}).get("planets") or {}
    angles_a = (astro_a or {}).get("angles") or {}
    angles_b = (astro_b or {}).get("angles") or {}

    # We look at BOTH directions — Juno of A → personal of B, and vice versa.
    candidates: List[Tuple[str, Optional[str]]] = []

    def _emit(label_a_point: str, label_b_point: str, asp: str, direction: str) -> Optional[str]:
        # direction: "ab" (Juno-of-A → b-point) or "ba"
        if direction == "ab":
            return (
                f"There's added weight in how {name_b}'s presence lands on "
                f"the part of you that takes commitment seriously — a theme "
                f"that's already moving in this connection gets louder, not different."
            )
        else:
            return (
                f"How you show up tends to register on the part of {name_b} "
                f"that holds commitment carefully — it amplifies what's already "
                f"alive here, rather than creating something new."
            )

    if juno_a:
        for pt_name in ("Sun", "Moon", "Venus"):
            asp = _aspect_between(juno_a, _planet(planets_b, pt_name))
            if asp:
                candidates.append((asp, _emit("Juno", pt_name, asp, "ab")))
                break
        if not candidates:
            asp = _aspect_between(juno_a, angles_b.get("asc"))
            if asp:
                candidates.append((asp, _emit("Juno", "Asc", asp, "ab")))

    if not candidates and juno_b:
        for pt_name in ("Sun", "Moon", "Venus"):
            asp = _aspect_between(juno_b, _planet(planets_a, pt_name))
            if asp:
                candidates.append((asp, _emit(pt_name, "Juno", asp, "ba")))
                break

    if not candidates:
        return None

    return _sanitize_line(candidates[0][1])


def compute_north_node_amplifier(
    astro_a: Dict[str, Any],
    astro_b: Dict[str, Any],
    name_b: str,
) -> Optional[str]:
    """
    North Node amplifier: NN-of-A contacts a personal of B (or vice
    versa).  Framed as growth-direction emphasis — never destiny.
    """
    nn_a = _get_north_node(astro_a)
    nn_b = _get_north_node(astro_b)
    if not nn_a and not nn_b:
        return None

    planets_a = (astro_a or {}).get("planets") or {}
    planets_b = (astro_b or {}).get("planets") or {}

    line = None
    if nn_a:
        for pt_name in ("Sun", "Moon", "Venus"):
            asp = _aspect_between(nn_a, _planet(planets_b, pt_name))
            if asp in ("conjunction", "trine"):
                line = (
                    f"The direction you're growing toward keeps showing up in "
                    f"{name_b}'s presence — what's already opening in you finds "
                    f"a clearer edge when you're around them."
                )
                break
            elif asp in ("opposition", "square"):
                line = (
                    f"There's a pull here that tests where you're heading — "
                    f"{name_b} touches the part of you that's stretching, and "
                    f"that stretch becomes more visible in this connection."
                )
                break

    if not line and nn_b:
        for pt_name in ("Sun", "Moon", "Venus"):
            asp = _aspect_between(nn_b, _planet(planets_a, pt_name))
            if asp in ("conjunction", "trine"):
                line = (
                    f"You activate the direction {name_b} is growing toward — "
                    f"not by guiding, but by being a context where their next "
                    f"step feels more obvious."
                )
                break
            elif asp in ("opposition", "square"):
                line = (
                    f"You sit on the edge of where {name_b}'s growth is asking "
                    f"to go — that creates productive friction more than ease."
                )
                break

    return _sanitize_line(line)


def compute_vertex_amplifier(
    astro_a: Dict[str, Any],
    astro_b: Dict[str, Any],
    name_b: str,
) -> Optional[str]:
    """
    Vertex amplifier: Vertex (or anti-Vertex) of A contacts a personal
    of B.  Framed as "this encounter has weight" — never as fated
    meeting / soulmate / destined-to-meet.
    """
    vx_a = _get_vertex(astro_a)
    vx_b = _get_vertex(astro_b)
    if not vx_a and not vx_b:
        return None

    planets_a = (astro_a or {}).get("planets") or {}
    planets_b = (astro_b or {}).get("planets") or {}

    line = None
    if vx_a:
        for pt_name in ("Sun", "Moon", "Venus", "Mars"):
            asp = _aspect_between(vx_a, _planet(planets_b, pt_name))
            if asp in ("conjunction", "opposition"):
                line = (
                    f"This encounter has weight in your chart — {name_b}'s "
                    f"presence lands on a sensitive contact point, so what "
                    f"happens between you tends to feel more vivid than the "
                    f"average interaction."
                )
                break

    if not line and vx_b:
        for pt_name in ("Sun", "Moon", "Venus", "Mars"):
            asp = _aspect_between(vx_b, _planet(planets_a, pt_name))
            if asp in ("conjunction", "opposition"):
                line = (
                    f"For {name_b}, this encounter lands on a sensitive "
                    f"contact point — which means the interactions tend to "
                    f"register for them more than they'd expect."
                )
                break

    return _sanitize_line(line)


# ---------------------------------------------------------------------------
# Core field synthesizer
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Layered Convergence v1.3 — Lens-domain orchestration
# ---------------------------------------------------------------------------
#
# Each lens owns a distinct interpretive responsibility.  When multiple
# lenses converge on the same conceptual dimension, the engine keeps the
# OWNER's contribution and pivots others away — preserving convergence
# visibility without repetition.
#
# Dimensions:
#   ACTIVATION       — energetic chemistry / completion mechanics (HD owns)
#   GROWTH_PRESSURE  — consequence / maturation / mirror (Astrology owns)
#   ATTACHMENT       — unmet needs / pursuit-withdrawal (Enneagram owns)
#   STRUCTURE        — provision / household / practical life (BaZi owns)
#   SYMBOLIC         — recurring themes / archetype (Numerology owns)
#
# Source-lens tags on each theme catalogue entry let us route a theme to
# its native domain at pivot time.  Themes without a dimension tag are
# treated as UNCLAIMED and pass through the pivot filter unmodified.

_LENS_DOMAIN_OWNERSHIP: Dict[str, str] = {
    "ACTIVATION":      "hd",
    "GROWTH_PRESSURE": "astrology",
    "ATTACHMENT":      "enneagram",
    "STRUCTURE":       "bazi",
    "SYMBOLIC":        "numerology",
}

# Keyword buckets used by the dimension classifier.  Moderate detection
# per V1.3 spec: literal keyword + simple phrase patterns.  Avoid
# aggressive semantic suppression so the field doesn't thin out.
_DIMENSION_KEYWORDS: Dict[str, List[str]] = {
    "ACTIVATION": [
        "activate", "activation", "chemistry", "energetic pull",
        "momentum", "rhythm", "completion", "in sync", "wired",
        "live wire", "click", "spark", "fast", "instinctive",
    ],
    "GROWTH_PRESSURE": [
        "harder to avoid", "evolution", "identity", "consequence",
        "mirror", "growth", "maturation", "stakes",
        "pulls both of you toward", "the parts of yourself",
        "what this relationship will ask",
    ],
    "ATTACHMENT": [
        "reaches toward", "most reaches", "most reach",
        "validation", "performance", "valued", "valued for",
        "unmet", "pursuit", "withdrawal",
        "what each person needs", "what each person reaches",
        "emotional hunger", "be seen",
    ],
    "STRUCTURE": [
        "provision", "household", "resources", "capability",
        "capital", "ambition", "follow-through", "follow through",
        "build", "building", "tangible", "responsibility",
        "stewardship", "direction", "who carries what",
        "real-world", "logistics", "structure", "household",
        "shared territory", "provide",
    ],
    "SYMBOLIC": [
        "theme", "archetype", "lesson", "recurring", "motif",
        "journey", "expansion", "reinvention", "path",
        "symbol", "revolves around",
    ],
}

# Pre-compile lowercase keyword sets for fast scan.
_DIMENSION_KEYWORDS_LC: Dict[str, List[str]] = {
    dim: [kw.lower() for kw in kws] for dim, kws in _DIMENSION_KEYWORDS.items()
}


def _classify_dimension(text: Optional[str]) -> Optional[str]:
    """
    Return the dominant dimension claimed by `text`, or None if no
    dimension has a stronger signal than the others.  Ties go to the
    first dimension encountered (deterministic).
    """
    if not isinstance(text, str) or not text.strip():
        return None
    t = text.lower()
    scores: Dict[str, int] = {}
    for dim, kws in _DIMENSION_KEYWORDS_LC.items():
        n = sum(1 for kw in kws if kw in t)
        if n > 0:
            scores[dim] = n
    if not scores:
        return None
    # Return dimension with max hits; ties resolved by ownership order
    best = max(scores.items(), key=lambda kv: (kv[1], -list(_LENS_DOMAIN_OWNERSHIP.keys()).index(kv[0])))
    return best[0]


def _pivot_themes(
    themes: List[Dict[str, Any]],
) -> tuple:
    """
    Layered-convergence pivot filter.

    Input: themes from `_select_themes`, each carrying an optional
    `dimension` tag and `source_lens` tag.  Themes without a dimension
    are classified on the fly from their `what_lives_here` text.

    For each dimension that has 2+ themes claiming it:
      • Keep the theme whose source_lens matches the dimension OWNER.
      • Drop the rest (logged as pivots).
      • Record a convergence note so the field paragraph can surface
        the agreement as a single line (visible convergence, not echoes).

    Returns (kept_themes, convergence_notes).
    """
    if not themes:
        return [], []

    # Annotate each theme with a resolved dimension (explicit > classified).
    annotated: List[Dict[str, Any]] = []
    for t in themes:
        dim = t.get("dimension")
        if not dim:
            dim = _classify_dimension(t.get("what_lives_here")) or _classify_dimension(t.get("label"))
        annotated.append({**t, "_dim": dim or "UNCLAIMED"})

    # Group by dimension.
    by_dim: Dict[str, List[Dict[str, Any]]] = {}
    for t in annotated:
        by_dim.setdefault(t["_dim"], []).append(t)

    kept: List[Dict[str, Any]] = []
    convergences: List[Dict[str, Any]] = []

    # Iterate in input order so deterministic output matches catalogue order.
    seen_dims: set = set()
    for t in annotated:
        dim = t["_dim"]
        if dim in seen_dims:
            continue
        seen_dims.add(dim)
        bucket = by_dim[dim]
        if dim == "UNCLAIMED" or len(bucket) == 1:
            kept.extend(bucket)
            continue
        # Multi-theme convergence on a claimed dimension.
        owner = _LENS_DOMAIN_OWNERSHIP.get(dim)
        primary = next(
            (b for b in bucket if (b.get("source_lens") or "").lower() == owner),
            bucket[0],
        )
        kept.append(primary)
        sources = sorted({(b.get("source_lens") or "lens") for b in bucket})
        for d in bucket:
            if d is primary:
                continue
            logger.info(
                "[LayeredConvergence] Pivoted theme '%s' (source=%s, dim=%s) — "
                "overlaps with owner '%s'",
                d.get("label"), d.get("source_lens"), dim, owner,
            )
        if len(sources) >= 2:
            convergences.append({
                "dimension": dim,
                "sources": sources,
                "primary_label": (primary.get("label") or "").lower(),
            })

    # Strip the transient `_dim` marker before returning.
    cleaned = [{k: v for k, v in t.items() if k != "_dim"} for t in kept]
    return cleaned, convergences


def _build_convergence_note(convergences: List[Dict[str, Any]]) -> Optional[str]:
    """
    Produce a SINGLE short line that makes multi-lens convergence visible
    without repeating it.  Returns None when no convergence detected.

    Per V1.3 editorial spec: convergence is interesting and should be
    SHOWN, but as one line, not paraphrased across the synthesis block.
    """
    if not convergences:
        return None
    # Use only the first / strongest convergence to keep the field tight.
    c = convergences[0]
    sources = c.get("sources") or []
    label = (c.get("primary_label") or "").strip()
    if not label or len(sources) < 2:
        return None
    src_phrase = " and ".join(s.capitalize() for s in sources[:3])
    return (
        f"{src_phrase} converge on the same pattern here — that's how "
        f"clearly {label} sits in this connection."
    )


# Theme-label dictionary: maps signal fingerprints to a human label and a
# short connector that the field paragraph can reuse.  Labels are
# intentionally NEUTRAL — they describe what's alive, not how good it is.
_THEME_CATALOG: List[Dict[str, Any]] = [
    {
        "label": "Emotional reach",
        "match": {"hd_channels": ["6-59", "39-55"], "astro_signals": ["sun-moon", "moon-moon"]},
        "what_lives_here": "Feelings move between you faster than most connections allow — the emotional door opens without much prompting.",
        "friction_inside_it": "When it gets close, one of you tends to pull back to recover space.",
        "dimension": "ACTIVATION",
        "source_lens": "hd",
    },
    {
        "label": "Quiet trust",
        "match": {"hd_channels": ["34-57", "27-50", "13-33"]},
        "what_lives_here": "There's an instinctive sense of safety here — you don't need words to confirm where you stand with each other.",
        "friction_inside_it": "The trust can mute the small adjustments that keep a connection current.",
        "dimension": "ACTIVATION",
        "source_lens": "hd",
    },
    {
        "label": "Shared rhythm",
        "match": {"hd_channels": ["5-15", "9-52"]},
        "what_lives_here": "Your natural pace lines up — when you're in sync, things move without negotiation.",
        "friction_inside_it": "When the rhythms diverge, the whole connection can feel off, even if nothing went wrong.",
        "dimension": "ACTIVATION",
        "source_lens": "hd",
    },
    {
        "label": "Creative momentum",
        "match": {"hd_channels": ["1-8", "11-56", "35-36"]},
        "what_lives_here": "Ideas and direction tend to activate between you — when you're together, things start.",
        "friction_inside_it": "Momentum can outrun the conversation about whether either of you actually wants this.",
        "dimension": "ACTIVATION",
        "source_lens": "hd",
    },
    {
        "label": "Building together",
        "match": {"hd_channels": ["21-45", "7-31", "10-34"]},
        "what_lives_here": "Resources, direction, and responsibility quickly become shared territory — this connection tends to organize toward building something tangible.",
        "friction_inside_it": "When the contract stays unspoken, one of you ends up carrying more than was agreed.",
        "dimension": "STRUCTURE",
        "source_lens": "hd",
    },
    {
        "label": "Mutual sharpening",
        "match": {"hd_channels": ["4-63", "17-62", "32-54", "18-58"]},
        "what_lives_here": "You think things through together — the thinking itself changes both of you.",
        "friction_inside_it": "Sharpening can land as criticism if the intention isn't shared.",
        "dimension": "GROWTH_PRESSURE",
        "source_lens": "hd",
    },
    {
        "label": "Belonging",
        "match": {"hd_channels": ["37-40", "10-20"]},
        "what_lives_here": "A sense of place forms between you — unspoken agreements that feel real even before they're stated.",
        "friction_inside_it": "What feels 'agreed' may not actually be shared — the unsaid can build pressure.",
        "dimension": "ACTIVATION",
        "source_lens": "hd",
    },
    {
        "label": "Reaching toward each other",
        "match": {"ennea_friction": True},
        "what_lives_here": "What each of you reaches for from the other becomes visible quickly — and when the reach isn't met, the patterns repeat.",
        "friction_inside_it": "Type-level needs mean the same hunger can recur in the same place until it's named.",
        "dimension": "ATTACHMENT",
        "source_lens": "enneagram",
    },
    {
        "label": "Elemental fit",
        "match": {"bazi_support": True},
        "what_lives_here": "Your underlying natures feed each other — there's something steady in how you both move through the world.",
        "friction_inside_it": "When the support becomes automatic, it can quietly stop being noticed.",
        "dimension": "STRUCTURE",
        "source_lens": "bazi",
    },
    {
        "label": "Elemental friction",
        "match": {"bazi_tension": True},
        "what_lives_here": "Your underlying natures pull in different directions — neither of you is doing it wrong, but the gap is real.",
        "friction_inside_it": "The friction is the connection — when it disappears, so does the energy.",
        "dimension": "STRUCTURE",
        "source_lens": "bazi",
    },
]


def _extract_hd_channel_ids(hd_signals: Optional[List[Dict[str, Any]]]) -> List[str]:
    if not hd_signals:
        return []
    out = []
    for s in hd_signals:
        cid = s.get("channel") if isinstance(s, dict) else None
        if cid:
            out.append(str(cid))
    return out


def _bazi_has_section(bazi: Optional[Dict[str, Any]], section: str) -> bool:
    if not isinstance(bazi, dict):
        return False
    lst = bazi.get(section)
    return isinstance(lst, list) and len(lst) > 0


def _ennea_has_friction(ennea: Optional[Dict[str, Any]]) -> bool:
    if not isinstance(ennea, dict):
        return False
    lst = ennea.get("friction_pattern")
    return isinstance(lst, list) and len(lst) > 0


def _select_themes(
    channel_ids: List[str],
    bazi_signals: Optional[Dict[str, Any]],
    enneagram_signals: Optional[Dict[str, Any]],
    max_themes: int = 4,
) -> List[Dict[str, Any]]:
    """Walk the theme catalog, return up to `max_themes` matched themes."""
    selected: List[Dict[str, Any]] = []
    used_labels: set = set()

    for entry in _THEME_CATALOG:
        match = entry["match"]
        ok = False

        if "hd_channels" in match:
            if any(cid in match["hd_channels"] for cid in channel_ids):
                ok = True

        if not ok and match.get("bazi_support"):
            if _bazi_has_section(bazi_signals, "support"):
                ok = True

        if not ok and match.get("bazi_tension"):
            if _bazi_has_section(bazi_signals, "tension"):
                ok = True

        if not ok and match.get("ennea_friction"):
            if _ennea_has_friction(enneagram_signals):
                ok = True

        if ok and entry["label"] not in used_labels:
            selected.append({
                "label": entry["label"],
                "what_lives_here": entry["what_lives_here"],
                "friction_inside_it": entry.get("friction_inside_it"),
                "dimension": entry.get("dimension"),
                "source_lens": entry.get("source_lens"),
            })
            used_labels.add(entry["label"])
        if len(selected) >= max_themes:
            break

    return selected


def _build_activation_line(
    channel_ids: List[str],
    astro_signals: Optional[Dict[str, Any]],
    bazi_signals: Optional[Dict[str, Any]],
    name_b: str,
) -> str:
    """
    The single most-alive sentence in this connection.  Activation-first
    — we describe WHAT activates, never what conflicts.

    Layered-Convergence v1.3 hybrid rule: when an emotional channel
    (6-59 / 39-55) co-exists with the money/structure channel (21-45),
    the activation line names BOTH dimensions because that combination
    is the actual relationship signature — it is not an emotional
    connection that happens to have money on the side, or vice versa.
    """
    # Channel-driven activation (strongest signal)
    if channel_ids:
        has_emotional = "6-59" in channel_ids or "39-55" in channel_ids
        has_money = "21-45" in channel_ids
        # Hybrid: emotional + money/structure coexist → name both.
        if has_emotional and has_money:
            return (
                f"What activates between you is both emotional reach and "
                f"real-world coordination — the door opens fast, and so does "
                f"the question of what you are building or carrying together."
            )
        if has_emotional:
            return f"What activates between you is emotional — the door opens faster than usual."
        if "10-20" in channel_ids or "13-33" in channel_ids:
            return f"What activates between you is honesty — surface talk dissolves quickly."
        if "5-15" in channel_ids or "9-52" in channel_ids:
            return f"What activates between you is timing — when you're aligned, things move without effort."
        if "1-8" in channel_ids or "35-36" in channel_ids:
            return f"What activates between you is forward motion — ideas tend to become action."
        if has_money:
            return f"What activates between you is real-world coordination — resources, direction, and who carries what move quickly into shared territory."
        if "34-57" in channel_ids or "27-50" in channel_ids:
            return f"What activates between you is an instinctive sense of safety."
        return f"What activates between you is a specific kind of energetic pull — {len(channel_ids)} active completion(s) connect different parts of your designs."

    # Astrology fallback
    if astro_signals and astro_signals.get("attraction"):
        return f"What activates between you is something subtle — a chemistry that lives in how you respond to {name_b} more than in any single trait."

    # BaZi fallback
    if bazi_signals and bazi_signals.get("support"):
        return f"What activates between you is a quiet elemental fit — your underlying natures feed each other."

    if bazi_signals and bazi_signals.get("tension"):
        return f"What activates between you is the gap between your natures — not absence of connection, but friction that holds the connection together."

    return (
        f"What activates between you is built, not automatic — this connection "
        f"runs on attention rather than pull."
    )


def _build_field_paragraph(
    activation: str,
    themes: List[Dict[str, Any]],
    name_b: str,
    convergence_note: Optional[str] = None,
) -> str:
    """
    One short paragraph that synthesizes the FEEL of this pair.

    Layered Convergence v1.3 architectural rule (Phase 4):
    As the channel cards get richer (curated headline / description /
    what_works / what_to_watch), the top synthesis must get SHORTER and
    more distilled — otherwise the page becomes emotionally exhausting.

    The activation line carries the headline.  The theme labels are
    presented as a compressed signal ("Also alive: X and Y") rather than
    a fully-formed "The dominant themes here are..." sentence.  We never
    paraphrase across the synthesis block — the channel layer carries
    depth, the field layer carries compression.
    """
    if not themes:
        body = activation + (
            f" The shape of this connection emerges through who you both decide "
            f"to be inside it, more than through any energetic completion."
        )
        return f"{body} {convergence_note}".strip() if convergence_note else body

    # relationship-v2-final-cleanup: drop the "Also alive: X and Y" recap
    # entirely — the themes are already exposed as their own distinct cards
    # downstream (what_lives_between_you / activation / today). The top
    # paragraph should be ONE integrated synthesis, not a label recap.
    parts = [activation]
    if convergence_note:
        parts.append(convergence_note)
    return " ".join(parts)


def _rewrap_enneagram_gift(line: Optional[str], name_b: str) -> Optional[str]:
    """
    Rewrap a raw Enneagram directional string out of arrow-notation
    ("You → Mel: X") into Mirror prose ("With you, Mel finds X.") while
    PRESERVING DIRECTION.

    Scope: relationship-field-v1.1 polish — only the gift line uses this.
    The legacy `signals.enneagram.how_you_help_them` list rendered inside
    the technical proof drawer is intentionally NOT touched, so the rest
    of the app continues to render the same strings it always did.

    Recognised prefixes (matched in order):
        "You → {name_b}: <content>"
        "{name_b} → you: <content>"
        "What {name_b} needs most from you: <content>"
        "What you need most from {name_b}: <content>"

    Any string that doesn't match a known prefix is passed through
    unchanged.  This keeps the helper conservative — we only rewrite
    what we can rewrite safely.
    """
    if not isinstance(line, str):
        return line
    s = line.strip()
    if not s:
        return None
    if not name_b:
        return s

    # Direction A: viewer → other (gift FROM viewer TO other)
    pref_a_lower = f"you → {name_b}: ".lower()
    if s.lower().startswith(pref_a_lower):
        content = s[len(pref_a_lower):].strip()
        if content:
            return f"With you, {name_b} finds {content}."
        return s

    # Direction B: other → viewer (gift FROM other TO viewer)
    pref_b_lower = f"{name_b} → you: ".lower()
    if s.lower().startswith(pref_b_lower):
        content = s[len(pref_b_lower):].strip()
        if content:
            return f"With {name_b}, you find {content}."
        return s

    # Needs-pattern (other → viewer phrasing — what the other reaches toward you for)
    pref_c_lower = f"what {name_b} needs most from you: ".lower()
    if s.lower().startswith(pref_c_lower):
        content = s[len(pref_c_lower):].strip()
        if content:
            return f"{name_b} most reaches toward you for {content}."
        return s

    # Needs-pattern (viewer → other phrasing — what you reach toward the other for)
    pref_d_lower = f"what you need most from {name_b}: ".lower()
    if s.lower().startswith(pref_d_lower):
        content = s[len(pref_d_lower):].strip()
        if content:
            return f"You most reach toward {name_b} for {content}."
        return s

    # Unknown shape — leave untouched (e.g. center-based fallback strings
    # like "Your thinking helps Mel step back..." are already clean prose).
    return s


def _build_gift_line(
    channel_ids: List[str],
    bazi_signals: Optional[Dict[str, Any]],
    enneagram_signals: Optional[Dict[str, Any]],
    name_b: str,
) -> str:
    """
    Mandatory 'Gift of this connection' line.  Always positive-framed
    but never inflated.

    Layered-Convergence v1.3 hybrid rule (mirrors `_build_activation_line`):
    when emotional (6-59/39-55) and money/structure (21-45) coexist, name
    BOTH — the combination is the signature, not either dimension alone.
    """
    has_emotional = "6-59" in channel_ids or "39-55" in channel_ids
    has_money = "21-45" in channel_ids

    if has_emotional and has_money:
        return (
            f"The gift here lives in both registers — {name_b} pulls you into "
            f"emotional reach you'd normally protect, AND together you can "
            f"actually build. Most connections give you one of these. This one "
            f"gives you both."
        )
    if has_emotional:
        return (
            f"{name_b} helps you reach emotional depth you'd normally protect — "
            f"and that depth is what makes this connection worth tending."
        )
    if "10-20" in channel_ids:
        return (
            f"With {name_b}, you get to drop a layer of performance — and you "
            f"both get to find out who's underneath."
        )
    if "37-40" in channel_ids:
        return (
            f"Together you build a sense of belonging that neither of you "
            f"would construct alone."
        )
    if "5-15" in channel_ids:
        return (
            f"Your shared rhythm creates a container of ease that other "
            f"connections in your life don't have."
        )
    if "1-8" in channel_ids or "35-36" in channel_ids:
        return (
            f"{name_b} pulls you toward things you wouldn't start alone — "
            f"and that's how parts of you grow."
        )
    if "21-45" in channel_ids:
        return (
            f"Together you can actually build — this connection has a rare "
            f"combination of ambition, capability, and follow-through wired in. "
            f"Most relationships in your life don't carry this much real-world "
            f"weight."
        )

    if enneagram_signals and enneagram_signals.get("how_you_help_them"):
        return _rewrap_enneagram_gift(enneagram_signals["how_you_help_them"][0], name_b)
    if enneagram_signals and enneagram_signals.get("how_they_help_you"):
        return _rewrap_enneagram_gift(enneagram_signals["how_they_help_you"][0], name_b)

    if bazi_signals and bazi_signals.get("support"):
        return (
            f"The gift here is steadiness — your natures meet in a way that "
            f"gives both of you somewhere reliable to stand."
        )

    return (
        f"The gift here is intentional connection — what exists between you "
        f"is built through choice and attention, not driven by unconscious pull."
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_relationship_field(
    *,
    current_user_name: str,
    member_name: str,
    completed_channels: List[Dict[str, Any]],
    chart_a: Optional[Dict[str, Any]],
    chart_b: Optional[Dict[str, Any]],
    astro_signals: Optional[Dict[str, Any]] = None,
    bazi_signals: Optional[Dict[str, Any]] = None,
    enneagram_signals: Optional[Dict[str, Any]] = None,
    numerology_signals: Optional[Dict[str, Any]] = None,
    hd_signals: Optional[List[Dict[str, Any]]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Build the relationship-field-v1 envelope.

    All inputs are already-computed outputs from
    services.forum_hd_mapping — we only synthesize, we never recompute.

    Amplifiers (Juno / NN / Vertex) are computed here BUT are gated on
    a corroboration rule:  an amplifier only surfaces if at least one
    non-amplifier signal (HD channel, astrology contact, bazi support
    or tension, or enneagram friction) already exists in the field.
    Stand-alone amplifier lines are suppressed.
    """
    try:
        # astrology-chat-v5-advanced-object-reconnect — hydrate Juno / Vertex
        # for legacy charts so the amplifier layer doesn't silently drop
        # this person's relationship-significance signals.
        try:
            from services.natal_object_engine import ensure_advanced_objects
            chart_a = ensure_advanced_objects(chart_a)
            chart_b = ensure_advanced_objects(chart_b)
        except Exception:
            pass

        channel_ids = _extract_hd_channel_ids(hd_signals)

        # Build the activation + themes + gift first (from non-amplifier data).
        activation = _build_activation_line(channel_ids, astro_signals, bazi_signals, member_name)
        themes_raw = _select_themes(channel_ids, bazi_signals, enneagram_signals)
        # Phase 2 — Layered Convergence pivot: when 2+ lenses claim the same
        # dimension, keep the owner and surface a single convergence note
        # instead of paraphrasing the same insight across the synthesis block.
        themes, convergences = _pivot_themes(themes_raw)
        convergence_note = _build_convergence_note(convergences)
        field_paragraph = _build_field_paragraph(activation, themes, member_name, convergence_note)
        gift = _build_gift_line(channel_ids, bazi_signals, enneagram_signals, member_name)

        # Corroboration: amplifiers ONLY surface when something else is alive.
        astro_a = (chart_a or {}).get("astrology", {}) if isinstance(chart_a, dict) else {}
        astro_b = (chart_b or {}).get("astrology", {}) if isinstance(chart_b, dict) else {}

        has_corroboration = bool(
            channel_ids
            or (astro_signals and (
                astro_signals.get("attraction") or astro_signals.get("tension") or astro_signals.get("growth")
            ))
            or (bazi_signals and (
                bazi_signals.get("support") or bazi_signals.get("tension") or bazi_signals.get("growth")
            ))
            or (enneagram_signals and enneagram_signals.get("friction_pattern"))
        )

        juno_line = None
        nn_line = None
        vx_line = None

        if has_corroboration and astro_a and astro_b:
            juno_line = compute_juno_amplifier(astro_a, astro_b, member_name)
            nn_line = compute_north_node_amplifier(astro_a, astro_b, member_name)
            vx_line = compute_vertex_amplifier(astro_a, astro_b, member_name)

        # Final sanitizer pass on every user-visible line in the envelope.
        envelope = {
            "version": "relationship-field-v1",
            "field_paragraph": _sanitize_line(field_paragraph) or field_paragraph,
            "activation": _sanitize_line(activation) or activation,
            "themes": [
                {
                    "label": t["label"],
                    "what_lives_here": _sanitize_line(t["what_lives_here"]) or t["what_lives_here"],
                    "friction_inside_it": _sanitize_line(t.get("friction_inside_it")),
                }
                for t in themes
            ],
            "gift_of_this_connection": _sanitize_line(gift) or gift,
            "amplifiers": {
                "juno": juno_line,
                "north_node": nn_line,
                "vertex": vx_line,
            },
        }

        return envelope

    except Exception as exc:
        # Never break the mapping pipeline — log and skip.
        logger.error(
            f"[RelationshipField] build_relationship_field failed for "
            f"{current_user_name} ↔ {member_name}: {type(exc).__name__}: {exc}"
        )
        return None
