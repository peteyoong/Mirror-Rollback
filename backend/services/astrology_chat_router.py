"""
Astrology Chat Intent Router
============================
Build marker: astro-chat-transit-grounding-v1

Tiny pattern-matching layer that runs BEFORE the astrology-lens LLM call.
Classifies the user's question into one of four strict data_modes so the
LLM is constrained to a single answering mode and cannot silently fall
back (e.g., a transit question degrading into a natal answer).

Data modes
----------
  natal_object       — "where is my natal Chiron?", "what sign is my Sun?"
  transit_object     — "where is Chiron now?", "where is Chiron in my transit chart?"
  transit_to_natal   — "is Uranus aspecting my natal Sun?", "is Saturn conjunct my Venus?"
  timeline_summary   — "what's happening this week / this month / year ahead?"

Returns None when the question doesn't match a deterministic-lookup intent
(the regular chat flow handles those).
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, Optional, Tuple

from services.transit_object_engine import resolve_object_name

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Body alias regex — same surface as the engine's resolver but as a
# capturing pattern so we can find a body name inside free-text questions.
# ---------------------------------------------------------------------------
_BODY_PATTERNS = [
    r"\bsun\b", r"\bmoon\b", r"\bluna\b",
    r"\bmercury\b", r"\bvenus\b", r"\bmars\b",
    r"\bjupiter\b", r"\bjove\b", r"\bsaturn\b",
    r"\buranus\b", r"\bneptune\b", r"\bpluto\b",
    r"\bchiron\b",
    r"\bnorth node\b", r"\brahu\b", r"\btrue node\b", r"\bmean node\b",
    r"\bsouth node\b", r"\bketu\b",
    r"\bascendant\b", r"\basc\b", r"\brising( sign)?\b",
    r"\bmc\b", r"\bmidheaven\b",
    # Not-yet-enabled — we still detect so we can return a clean refusal.
    r"\bjuno\b", r"\bvertex\b", r"\blilith\b", r"\bblack moon( lilith)?\b",
    r"\bceres\b", r"\bpallas\b", r"\bvesta\b", r"\beris\b",
]
_BODY_RE = re.compile("|".join(_BODY_PATTERNS), re.IGNORECASE)

# Anything explicitly anchoring to NOW / TODAY / CURRENTLY / TRANSIT.
_TRANSIT_NOW_PATTERNS = [
    r"\bnow\b", r"\btoday\b", r"\bcurrently\b", r"\bright now\b",
    r"\btransit(s|ing)?\b", r"\btransit chart\b",
    r"\bthis week\b", r"\bthis month\b", r"\bthis year\b",
]
_TRANSIT_NOW_RE = re.compile("|".join(_TRANSIT_NOW_PATTERNS), re.IGNORECASE)

# Anything anchoring to NATAL.
_NATAL_PATTERNS = [
    r"\bnatal\b", r"\bmy natal\b",
    r"\bbirth chart\b", r"\bin my chart\b(?!.*transit)",
]
_NATAL_RE = re.compile("|".join(_NATAL_PATTERNS), re.IGNORECASE)

# Aspect query patterns.
_ASPECT_RE = re.compile(
    r"\b(aspect|aspecting|conjunct|conjunction|square|opposition|opposite|trine|sextile|quincunx)\b",
    re.IGNORECASE,
)

# Timeline / week / month broad questions.
_TIMELINE_RE = re.compile(
    r"\b(this week|this month|this year|year ahead|next week|next month|next year|"
    r"what'?s coming|upcoming|timeline|key dates?|important dates?)\b",
    re.IGNORECASE,
)

# Solar return — yearly chart anchored on Sun's tropical return to natal degree.
# astrology-chat-grounding-v2
# House inventory query — "tell me about my 3rd house",
# "what's in my 10th house", "explain my 7th house collectively".
# Must fire BEFORE generic natal_object/positional handlers so a multi-
# body house question goes straight to the synthesis engine.
# astrology-chat-house-hierarchy-v5
_HOUSE_INVENTORY_RE = re.compile(
    r"\b(?:my\s+)?(?P<num>1st|2nd|3rd|4th|5th|6th|7th|8th|9th|10th|11th|12th|"
    r"first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth)\s+house\b",
    re.IGNORECASE,
)
_HOUSE_WORD_TO_NUM = {
    "1st":1,"first":1,"2nd":2,"second":2,"3rd":3,"third":3,
    "4th":4,"fourth":4,"5th":5,"fifth":5,"6th":6,"sixth":6,
    "7th":7,"seventh":7,"8th":8,"eighth":8,"9th":9,"ninth":9,
    "10th":10,"tenth":10,"11th":11,"eleventh":11,"12th":12,"twelfth":12,
}

# Ophiuchus inventory — direct, sign-shaped queries about Ophiuchus.
# Mirror's canonical engine is 13-sign (midpoint13_variant_a_v1) where
# Ophiuchus is a first-class sign. The chat path previously had no
# deterministic engine for these queries and the LLM would fall back
# to a 12-sign denial. Build marker: ophiuchus-inventory-engine-v1
_OPHIUCHUS_INVENTORY_RE = re.compile(
    r"\b("
    r"ophiuchus"
    r"|ophi\b"
    r"|serpent[\s-]?bearer"
    r"|13th\s+sign"
    r"|thirteenth\s+sign"
    r")\b",
    re.IGNORECASE,
)

# Pressure-topology / whole-chart synthesis questions.
# Fires on "tell me about my chart", "what does my chart say",
# "synthesize my chart", "what's the core pattern", "master read", etc.
# Distinct from any specific-body or specific-house lookup; this is the
# fallback synthesis layer (V6). astrology-pressure-topology-v6
_PRESSURE_TOPOLOGY_RE = re.compile(
    r"\b("
    r"(tell\s+me\s+about|what\s+(does|do)|what'?s|whats|read|"
    r"describe|interpret|synthesi[sz]e|give\s+me)\s+"
    r"(a\s+|the\s+)?(my\s+)?"
    r"(whole\s+|entire\s+|overall\s+|full\s+)?chart"
    r"|master\s+(read|reading|astrologer(\s+read(ing)?)?)"
    r"|holistic\s+read(ing)?"
    r"|overall\s+reading"
    r"|core\s+(of\s+my\s+chart|pattern|theme)"
    r"|(dominant|main|primary|core)\s+(theme|pattern|pressure|tension)"
    r"|what.{0,15}keep(s)?\s+(showing\s+up|repeat(ing|s)?|recurring)"
    r"|what'?s\s+the\s+pattern\s+in\s+my\s+chart"
    r"|psychological\s+(pattern|topology|pressure)"
    r"|pressure\s+(pattern|topology)"
    r"|chart\s+synthesis"
    r"|topology\s+(of\s+)?my\s+chart"
    r")\b",
    re.IGNORECASE,
)

_SOLAR_RETURN_RE = re.compile(
    r"\b("
    r"solar\s*return|"          # "solar return", "solar-return", "solarreturn"
    r"sr\s*ascendant|"           # "SR ascendant"
    r"sr\s*chart|"
    r"return\s*chart|"
    r"return\s*ascendant|"
    r"birthday\s*chart|"
    r"yearly\s*return|"
    r"annual\s*chart|"
    r"annual\s*return"
    r")\b",
    re.IGNORECASE,
)

# Natal object query — "tell me about my Lilith", "what does my Chiron mean",
# "what house is my Vertex in". Distinct from positional/aspect queries because
# we want a SPECIFIC named natal placement read.   astrology-chat-master-interpreter-v3
_NATAL_OBJECT_BODIES_RE = re.compile(
    r"\b("
    # Classical 10 (Sun → Pluto)
    # ASTRO-CHAT-PLANET-RESTORE-V1 — paired with _ALIAS restore in
    # natal_object_engine.py so questions like "tell me about my
    # Venus" or "compare my Mercury and Mars" route through the
    # natal_object branch rather than falling out unclassified.
    r"sun|moon|luna|"
    r"mercury|venus|mars|"
    r"jupiter|jove|saturn|"
    r"uranus|neptune|pluto|"
    # Lilith family
    r"lilith|black\s*moon|bml|mean\s*lilith|true\s*lilith|"
    # White Moon family (unsupported but must route here to refuse cleanly)
    r"selena|white\s*moon|"
    r"dark\s*moon|waldemath|"
    # Chiron, angles
    r"chiron|"
    r"vertex|anti.?vertex|"
    # Nodes
    r"north\s*node|south\s*node|rahu|ketu|nodes?|"
    # Lots / Arabic parts
    r"part\s*of\s*fortune|pars\s*fortuna|fortuna|lot\s*of\s*fortune|"
    r"part\s*of\s*spirit|pars\s*spiritus|lot\s*of\s*spirit|"
    r"lot\s*of\s*(eros|necessity|courage|victory|nemesis|basis|marriage)|"
    # Asteroids
    r"juno|ceres|pallas|vesta|eris|eros|psyche|hygi(?:e|ei)a|astraea"
    r")\b",
    re.IGNORECASE,
)


# Canonical-name mapping for multi-object detection inside natal_object
# branch. Pattern → canonical-string-used-by-natal_object_engine.
# Multi-object dispatch resolves through these.
# astrology-chat-multi-object-v1
_NATAL_OBJECT_PATTERN_TO_CANON: list = [
    # ── Classical 10 (Sun → Pluto) ──────────────────────────────────
    # ASTRO-CHAT-PLANET-RESTORE-V1 (2026-06-17): paired with the
    # _ALIAS restore in natal_object_engine.py.  Listed FIRST so a
    # multi-object query like "compare my Mercury and Mars" sees
    # both planets and dispatches through the pairwise builder
    # instead of the single-object branch that takes obj_raw[0].
    # Note: lookahead on "moon" suppresses the bare 'moon' match when
    # it is the head of a Lilith bigram ("Black Moon Lilith",
    # "Mean Lilith Moon", etc.) so the Lilith pattern below still
    # wins via the longest-span tiebreak.
    (re.compile(r"\bsun\b",                     re.IGNORECASE),       "Sun"),
    (re.compile(r"\bmoon\b|\bluna\b",           re.IGNORECASE),       "Moon"),
    (re.compile(r"\bmercury\b",                 re.IGNORECASE),       "Mercury"),
    (re.compile(r"\bvenus\b",                   re.IGNORECASE),       "Venus"),
    (re.compile(r"\bmars\b",                    re.IGNORECASE),       "Mars"),
    (re.compile(r"\bjupiter\b|\bjove\b",        re.IGNORECASE),       "Jupiter"),
    (re.compile(r"\bsaturn\b",                  re.IGNORECASE),       "Saturn"),
    (re.compile(r"\buranus\b",                  re.IGNORECASE),       "Uranus"),
    (re.compile(r"\bneptune\b",                 re.IGNORECASE),       "Neptune"),
    (re.compile(r"\bpluto\b",                   re.IGNORECASE),       "Pluto"),
    # ── Advanced objects ────────────────────────────────────────────
    (re.compile(r"\bnorth\s*node\b|\brahu\b", re.IGNORECASE),           "North Node"),
    (re.compile(r"\bsouth\s*node\b|\bketu\b", re.IGNORECASE),           "South Node"),
    (re.compile(r"\bnodes\b|\bnodal\s+axis\b", re.IGNORECASE),          "_NODES_PAIR_"),
    (re.compile(r"\btrue\s*lilith\b", re.IGNORECASE),                    "True Black Moon Lilith"),
    (re.compile(r"\bblack\s*moon(\s*lilith)?\b|\bbml\b|\blilith\b|\bmean\s*lilith\b", re.IGNORECASE), "Black Moon Lilith"),
    (re.compile(r"\bchiron\b", re.IGNORECASE),                           "Chiron"),
    (re.compile(r"\banti.?vertex\b", re.IGNORECASE),                     "Anti-Vertex"),
    (re.compile(r"\bvertex\b", re.IGNORECASE),                           "Vertex"),
    (re.compile(r"\b(part|pars|lot)\s*of\s*fortune\b|\bfortuna\b", re.IGNORECASE), "Lot of Fortune"),
    (re.compile(r"\b(part|pars|lot)\s*of\s*spirit\b", re.IGNORECASE),    "Lot of Spirit"),
    (re.compile(r"\bpholus\b", re.IGNORECASE),                           "Pholus"),
    (re.compile(r"\bjuno\b", re.IGNORECASE),                             "Juno"),
    (re.compile(r"\bceres\b", re.IGNORECASE),                            "Ceres"),
    (re.compile(r"\bpallas\b", re.IGNORECASE),                           "Pallas"),
    (re.compile(r"\bvesta\b", re.IGNORECASE),                            "Vesta"),
    (re.compile(r"\beros\b", re.IGNORECASE),                             "Eros"),
    (re.compile(r"\bpsyche\b", re.IGNORECASE),                           "Psyche"),
    (re.compile(r"\bhygi(?:e|ei)a\b", re.IGNORECASE),                    "Hygiea"),
    (re.compile(r"\bastraea\b", re.IGNORECASE),                          "Astraea"),
    (re.compile(r"\beris\b", re.IGNORECASE),                             "Eris"),
    (re.compile(r"\b(selena|white\s*moon|dark\s*moon|waldemath)\b", re.IGNORECASE), "Selena/White Moon"),
]


def _extract_natal_objects(text: str) -> list:
    """Return the ordered, de-duplicated list of canonical natal-object
    names referenced in `text`.  Used by the natal_object branch to
    detect multi-object queries like 'Ceres and Vesta' or 'my North Node
    and South Node'.  astrology-chat-multi-object-v1

    ADV-OBJ-12 (regex-bleed fix): when a match consumes a span of the
    input (e.g. "Anti-Vertex" → Anti-Vertex), subsequent shorter
    patterns whose match falls INSIDE that span are suppressed.  This
    prevents "Tell me about my Anti-Vertex" from also resolving the
    bare "Vertex" token inside the hyphenated word.
    """
    found: list = []
    seen: set = set()
    # Find ALL matches (with spans) and sort by position so the order
    # matches the user's phrasing (helps the LLM read SN→NN vs NN→SN
    # as the user wrote it).  Longer / earlier-listed patterns get
    # priority — any later pattern whose span is fully inside an
    # already-consumed span is dropped (regex-bleed suppression).
    hits: list = []
    for pat, canon in _NATAL_OBJECT_PATTERN_TO_CANON:
        # Use finditer so all occurrences of a pattern get their own
        # span (otherwise '...Anti-Vertex and my Vertex' would only
        # see the first match of \bvertex\b and miss the standalone
        # Vertex token entirely).
        for m in pat.finditer(text):
            hits.append((m.start(), m.end(), canon))
    hits.sort(key=lambda h: (h[0], -(h[1] - h[0])))   # earliest first; longest-among-tied first

    consumed_spans: list = []   # list of (start, end) already taken

    def _is_inside_consumed(s: int, e: int) -> bool:
        for cs, ce in consumed_spans:
            if s >= cs and e <= ce:
                return True
        return False

    for s, e, canon in hits:
        if _is_inside_consumed(s, e):
            continue
        # Expand the bare-plural "_NODES_PAIR_" sentinel into both ends.
        if canon == "_NODES_PAIR_":
            for nm in ("North Node", "South Node"):
                if nm not in seen:
                    seen.add(nm)
                    found.append(nm)
            consumed_spans.append((s, e))
            continue
        if canon not in seen:
            seen.add(canon)
            found.append(canon)
            consumed_spans.append((s, e))
    return found
_NATAL_OBJECT_TRIGGER_RE = re.compile(
    r"\b("
    r"tell\s*me\s*about|what\s*does|what's|whats|what\s*is|where\s*is|"
    r"my|read\s*my|interpret|natal|in\s*my\s*chart"
    r")\b",
    re.IGNORECASE,
)

# Positional question shapes — "where is X", "what sign is X", "what house is X".
_POSITIONAL_RE = re.compile(
    r"\b(where(?:'s| is)|what sign (?:is|does)|what house (?:is|does)|in what (?:sign|house))\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Lifecycle queries — "tell me about my Saturn return", "when does my Chiron
# return", "am I in midlife", "nodal opposition"…
# astrology-lifecycle-v1
#
# Each pattern maps to an `event_key` known by services.lifecycle_engine.
# The router collects every matched key, plus detects whether the user is
# asking PERSONALLY ("my", "for me", "in my chart", "when does X happen
# to me") vs CONCEPTUALLY ("what is", "explain", "tell me about saturn
# returns in general"). The downstream proof-block builder uses this to
# pick its instruction set.
# ---------------------------------------------------------------------------
_LIFECYCLE_EVENT_PATTERNS: list[tuple[str, str]] = [
    # (event_key, regex)
    ("saturn_return",          r"saturn\s+return"),
    ("saturn_opposition",      r"saturn\s+opp(osition|osite)\s+saturn|"
                               r"saturn.{0,8}opp(osition|osite)"),
    ("saturn_square_saturn",   r"saturn\s+sq(uare|uares)\s+saturn"),
    ("jupiter_return",         r"jupiter\s+return"),
    ("jupiter_opposition",     r"jupiter\s+opp(osition|osite)"),
    ("uranus_opposition",      r"uranus\s+opp(osition|osite)|midlife\s+(uprising|crisis)"),
    ("uranus_return",          r"uranus\s+return"),
    ("neptune_square_neptune", r"neptune\s+sq(uare|uares)\s+neptune|neptune\s+square"),
    ("pluto_square_pluto",     r"pluto\s+sq(uare|uares)\s+pluto|pluto\s+square"),
    ("chiron_return",          r"chiron\s+return"),
    ("nodal_return",           r"nodal\s+return|north\s+node\s+return"),
    ("nodal_opposition",       r"nodal\s+opp(osition|osite)|north\s+node\s+opp(osition|osite)"),
    ("progressed_lunation",    r"progressed\s+lunation|progressed\s+(new|full)\s+moon|"
                               r"secondary\s+progressed\s+moon|progressed\s+moon\s+return"),
    ("midlife_cluster",        r"\bmidlife\b(?!\s+(uprising|crisis))"),
    # Annual / monthly returns — light support; engine handles them too
    ("mars_return",            r"mars\s+return"),
    ("venus_return",           r"venus\s+return"),
]
_LIFECYCLE_RES = [(k, re.compile(p, re.IGNORECASE)) for k, p in _LIFECYCLE_EVENT_PATTERNS]

# Personal phrasing — implies "answer the person before the concept".
_LIFECYCLE_PERSONAL_RE = re.compile(
    r"\b(my\b|mine\b|for\s+me\b|in\s+my\s+chart|in\s+my\s+life|when\s+(does|did|will|is)\s+(my\s+|this\s+happen)|"
    r"am\s+i\s+(in|during|before|after)|"
    r"where\s+am\s+i\s+in\s+my|what\s+stage\s+of\s+(my\s+)?)\b",
    re.IGNORECASE,
)
# Pure conceptual phrasing — "what is X / explain X in general"
_LIFECYCLE_CONCEPT_ONLY_RE = re.compile(
    r"\b(what\s+is(?:\s+a)?|what(?:'s|s)?\s+a|explain|define|generally|in\s+general)\b",
    re.IGNORECASE,
)

# Follow-up phrasing — "when does that happen", "and when is it", "what about
# for me", "show me the dates". These imply we should reuse the lifecycle
# event from the previous turn.
_LIFECYCLE_FOLLOWUP_RE = re.compile(
    r"\b(and\s+when|when\s+(does|did|will|is)\s+(that|this|it)|"
    r"what\s+about\s+(for\s+me|me|that)|"
    r"show\s+me\s+the\s+dates?|"
    r"give\s+me\s+the\s+dates?|"
    r"in\s+my\s+chart)\b",
    re.IGNORECASE,
)


def _detect_lifecycle(text: str, history: list | None = None) -> Optional[Dict[str, Any]]:
    """Return a lifecycle envelope or None.

    {
        "data_mode":    "lifecycle",
        "event_keys":   ["saturn_return", ...],
        "phrasing":     "personal" | "concept" | "concept_no_anchor",
        "followup":     bool,
        "natural_form": <original text>,
    }

    `history` (optional) is a list of recent {role, content} dicts. When
    the user message has follow-up phrasing ("and when does that happen",
    "when is that", "what about for me") without a specific event keyword,
    the most recently mentioned lifecycle event in the assistant/user
    history is reused.
    """
    keys: list[str] = []
    for k, rgx in _LIFECYCLE_RES:
        if rgx.search(text):
            keys.append(k)

    is_followup = bool(_LIFECYCLE_FOLLOWUP_RE.search(text))

    if not keys and is_followup and history:
        # Scan recent turns (newest first) for any lifecycle event keyword
        for turn in reversed(history[-10:]):
            content = (turn.get("content") if isinstance(turn, dict) else "") or ""
            for k, rgx in _LIFECYCLE_RES:
                if rgx.search(content):
                    keys.append(k)
                    break
            if keys:
                break

    if not keys:
        return None

    is_personal = bool(_LIFECYCLE_PERSONAL_RE.search(text))
    is_concept  = bool(_LIFECYCLE_CONCEPT_ONLY_RE.search(text))
    if is_followup:
        # Follow-up to a prior personal turn always personalizes.
        phrasing = "personal"
    elif is_personal:
        phrasing = "personal"
    elif is_concept and not is_personal:
        phrasing = "concept_no_anchor"
    else:
        phrasing = "personal"
    if is_concept and is_personal:
        phrasing = "concept"

    return {
        "data_mode":    "lifecycle",
        "event_keys":   keys,
        "phrasing":     phrasing,
        "followup":     is_followup,
        "natural_form": text,
    }


def _extract_body(text: str) -> Optional[str]:
    """Return the first canonical body name mentioned in the text."""
    m = _BODY_RE.search(text)
    if not m:
        return None
    return resolve_object_name(m.group(0))


def classify_astrology_intent(
    message: str,
    history: list | None = None,
) -> Optional[Dict[str, Any]]:
    """Classify an incoming astrology-lens message.

    Returns a dict with at minimum:
        { "data_mode": <str>, "object": Optional[str], "natural_form": <str> }
    or None if no deterministic mode matched (caller stays on free-form chat).

    `history` (optional) is a list of recent {role, content} dicts used to
    resolve lifecycle follow-up phrasing such as "and when does that happen?".
    """
    if not message or not isinstance(message, str):
        return None

    text = message.strip()
    body = _extract_body(text)
    has_transit_now = bool(_TRANSIT_NOW_RE.search(text))
    has_natal = bool(_NATAL_RE.search(text))
    has_aspect = bool(_ASPECT_RE.search(text))
    has_positional = bool(_POSITIONAL_RE.search(text))
    has_timeline = bool(_TIMELINE_RE.search(text))
    has_solar_return = bool(_SOLAR_RETURN_RE.search(text))
    has_pressure_topology = bool(_PRESSURE_TOPOLOGY_RE.search(text))
    natal_obj_body_match = _NATAL_OBJECT_BODIES_RE.search(text)
    has_natal_obj_trigger = bool(_NATAL_OBJECT_TRIGGER_RE.search(text))
    house_match = _HOUSE_INVENTORY_RE.search(text)
    has_ophiuchus = bool(_OPHIUCHUS_INVENTORY_RE.search(text))

    # ── ophiuchus_inventory ────────────────────────────────────────────
    # ophiuchus-inventory-engine-v1
    # Fires FIRST when the user mentions Ophiuchus directly. Mirror's
    # canonical zodiac is 13-sign (midpoint13_variant_a_v1) where
    # Ophiuchus is a first-class sign — but a sign-shaped query like
    # "Do I have Ophiuchus in my chart?" has no body / aspect / house
    # anchor, so without this branch the engine returned None and the
    # LLM fell back to its 12-sign RLHF prior and denied Ophiuchus.
    # Must fire BEFORE lifecycle/house/natal_object so "is my Mercury
    # in Ophiuchus?" goes to the inventory builder, not transit_to_natal.
    if has_ophiuchus:
        return {
            "data_mode":    "ophiuchus_inventory",
            "object":       None,
            "natural_form": text,
        }

    # ── lifecycle (Saturn return / Chiron return / Nodal / Uranus opp …) ──
    # astrology-lifecycle-v1
    # P0 trust path. Must run BEFORE solar_return / transit_to_natal /
    # natal_object so a question like "tell me about my Saturn return"
    # cannot be misrouted to the transit-to-natal engine (which would
    # answer "Saturn transiting your Saturn" without the cycle-position
    # framing) or to natal_object (which would just describe natal
    # Saturn in sign and house).
    lifecycle_intent = _detect_lifecycle(text, history=history)
    if lifecycle_intent:
        return lifecycle_intent

    # ── house_inventory ────────────────────────────────────────────────
    # Catches: "tell me about my 3rd house", "what's in my 10th house",
    # "explain my 7th house collectively". Highest priority so multi-body
    # house questions go straight to the synthesis engine and never get
    # mis-routed to natal_object handling.
    # astrology-chat-house-hierarchy-v5
    if house_match:
        ord_word = house_match.group("num").lower()
        h_num = _HOUSE_WORD_TO_NUM.get(ord_word)
        if h_num:
            return {
                "data_mode":    "house_inventory",
                "house_number": h_num,
                "natural_form": text,
            }

    # ── natal_object (specific named body) ─────────────────────────────
    # Catches: "tell me about my Lilith", "what does my Chiron mean",
    # "what house is my Vertex in", "my north node". Must run BEFORE
    # positional/aspect handlers so the LLM doesn't try to free-form it.
    # astrology-chat-master-interpreter-v3
    #
    # Multi-object extension: astrology-chat-multi-object-v1
    # When the user references more than one natal body in one turn
    # (e.g. "Ceres and Vesta", "my North Node and South Node"), the
    # router resolves all of them and tags the envelope so the caller
    # can dispatch through the pairwise / axis builder rather than
    # picking the first match and silently dropping the rest.
    if natal_obj_body_match and (has_natal_obj_trigger or has_positional or has_natal):
        obj_raw = natal_obj_body_match.group(0)
        canonical_list = _extract_natal_objects(text)
        if len(canonical_list) >= 2:
            is_nodal = ("North Node" in canonical_list) and (
                "South Node" in canonical_list
            )
            return {
                "data_mode":    "natal_object",
                "object":       canonical_list[0],   # back-compat
                "objects":      canonical_list,
                "axis":         "nodal" if is_nodal else None,
                "multi":        True,
                "natural_form": text,
            }
        # Single-object fast path — preserve legacy shape.
        return {
            "data_mode":    "natal_object",
            "object":       canonical_list[0] if canonical_list else obj_raw,
            "objects":      canonical_list or [obj_raw],
            "axis":         None,
            "multi":        False,
            "natural_form": text,
        }

    # ── solar_return ──────────────────────────────────────────────────
    # Catches: "what's my solar return ascendant", "SR chart", "yearly
    # return", "birthday chart". Checked FIRST so "solar return ascendant"
    # doesn't get misrouted to positional/natal handling.
    # astrology-chat-grounding-v2
    if has_solar_return:
        return {
            "data_mode":    "solar_return",
            "object":       None,
            "natural_form": text,
        }

    # ── transit_to_natal ───────────────────────────────────────────────
    # Aspect verb + body → transit-to-natal aspect query.
    # NOTE: when the user writes "my natal Sun" the natal flag turns True,
    # but in aspect queries the "natal" anchor refers to the TARGET body
    # (Sun), not the transiting subject (Uranus). So we ignore has_natal
    # in this branch — the aspect verb itself is the strongest intent
    # signal we can get. astro-chat-transit-grounding-v1
    if has_aspect and body:
        return {
            "data_mode":     "transit_to_natal",
            "object":        body,
            "natural_form":  text,
        }

    # ── transit_object ────────────────────────────────────────────────
    # "where is Chiron now" / "where is Chiron in my transit chart" /
    # "what house is Saturn transiting" / "where is Chiron transiting"
    if body and (
        (has_positional and has_transit_now)
        or (has_positional and "transit" in text.lower())
        or ("transit" in text.lower() and has_positional)
    ):
        return {
            "data_mode":    "transit_object",
            "object":       body,
            "natural_form": text,
        }

    # ── natal_object ──────────────────────────────────────────────────
    # "where is my natal Chiron" / "what sign is my Sun" (no transit verb)
    if has_positional and body and has_natal and not has_transit_now:
        canonical_list = _extract_natal_objects(text)
        if len(canonical_list) >= 2:
            is_nodal = ("North Node" in canonical_list) and (
                "South Node" in canonical_list
            )
            return {
                "data_mode":    "natal_object",
                "object":       canonical_list[0],
                "objects":      canonical_list,
                "axis":         "nodal" if is_nodal else None,
                "multi":        True,
                "natural_form": text,
            }
        return {
            "data_mode":    "natal_object",
            "object":       body,
            "objects":      [body],
            "axis":         None,
            "multi":        False,
            "natural_form": text,
        }

    # ── timeline_summary ──────────────────────────────────────────────
    # Broad period questions — no specific body anchor.
    if has_timeline and not body and not has_positional:
        return {
            "data_mode":    "timeline_summary",
            "object":       None,
            "natural_form": text,
        }

    # ── pressure_topology (V6) ────────────────────────────────────────
    # Catches whole-chart synthesis questions: "tell me about my chart",
    # "what does my chart say", "synthesize my chart", "what's the core
    # pattern", "master read". Distinct from any specific-body lookup;
    # this is the deterministic synthesis layer that replaces generic
    # "this placement suggests" LLM hallucination.
    # astrology-pressure-topology-v6
    if has_pressure_topology:
        return {
            "data_mode":    "pressure_topology",
            "object":       None,
            "natural_form": text,
        }

    return None


def build_transit_object_proof_block(envelope: Dict[str, Any]) -> str:
    """Render the deterministic transit envelope into a strict prompt block.

    The LLM consumes this block as ground truth. It is forbidden from
    contradicting or extending the computed numbers.
    """
    if not envelope or not envelope.get("success"):
        reason = (envelope or {}).get("reason", "unknown")
        msg = (envelope or {}).get("message") or ""
        return (
            "=== DETERMINISTIC DATA — data_mode=transit_object ===\n"
            f"COMPUTATION_FAILED · reason={reason}\n"
            f"{msg}\n"
            "ABSOLUTE RULE: Do not answer outside the supplied data_mode. "
            "Do not fall back to natal data. Tell the user the engine could "
            "not compute the requested transit, then stop."
        )

    pos = envelope["transit_position"]
    aspects = envelope.get("aspects_to_natal") or []
    aspect_lines = (
        "\n".join(
            f"  · {a['aspect']} natal {a['natal_body']} · orb {a['orb']}° "
            f"({'applying' if a['applying'] else 'separating'})"
            for a in aspects
        )
        if aspects
        else "  · (no major tight aspects to natal planets right now)"
    )

    return (
        "=== DETERMINISTIC DATA — data_mode=transit_object ===\n"
        f"object:              {envelope['object']}\n"
        f"timestamp:           {envelope['timestamp']}\n"
        f"zodiac_system:       {envelope['zodiac_system']}\n"
        f"ayanamsa:            {envelope['ayanamsa']}\n"
        f"house_system:        {envelope['house_system']}\n"
        f"transit_position:    {pos['formatted']} "
        f"({pos['absolute_longitude']}° abs) "
        f"{'retrograde' if pos['retrograde'] else 'direct'}\n"
        f"natal_house:         {envelope['natal_house']}\n"
        f"aspects_to_natal:\n{aspect_lines}\n"
        "===================================================\n"
        "ABSOLUTE RULES — DO NOT VIOLATE:\n"
        " 1. Do not answer outside the supplied data_mode (transit_object).\n"
        " 2. Do not substitute natal Chiron / natal placement when the user\n"
        "    asked for transit. If you do, you have failed.\n"
        " 3. Lead with the factual placement above, then a short Mirror-style\n"
        "    interpretation grounded ONLY in those numbers.\n"
        " 4. NO therapy-blog phrasing: no 'themes around', 'healing and\n"
        "    vulnerability', 'might be useful to explore', 'what feels tender'.\n"
        " 5. If no aspects are listed, say so calmly — it is not a failure.\n"
    )


def build_transit_object_user_facing_prefix(envelope: Dict[str, Any]) -> Optional[str]:
    """Return a pre-formatted factual prefix the chat layer can prepend.

    Used when we want the answer to be deterministic AT THE PROSE LAYER too
    (e.g., to guarantee the placement string is correct verbatim, even if
    the LLM polish stage misfires).
    """
    if not envelope or not envelope.get("success"):
        return None
    pos = envelope["transit_position"]
    line = (
        f"{envelope['object']} is currently transiting "
        f"{pos['sign']} at {pos['formatted'].replace(pos['sign'], '').strip().lstrip('°').strip() or pos['degree']}°, "
        f"landing in your {_ordinal(envelope['natal_house'])} house."
    )
    aspects = envelope.get("aspects_to_natal") or []
    if aspects:
        line += "\n\nIt is currently making these notable contacts to your natal chart:"
        for a in aspects[:6]:
            line += f"\n• {a['aspect']} natal {a['natal_body']} · orb {a['orb']}°"
    else:
        line += "\n\nNo major tight aspects to your natal planets are active right now."
    return line


def _ordinal(n: int) -> str:
    if not isinstance(n, int):
        return str(n)
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


__all__ = [
    "classify_astrology_intent",
    "build_transit_object_proof_block",
    "build_transit_object_user_facing_prefix",
    "_detect_lifecycle",
]
