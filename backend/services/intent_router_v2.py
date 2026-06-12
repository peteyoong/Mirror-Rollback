"""intent_router_v2 — Mirror Chat V2 Slice B1 (SHADOW MODE).

B1.1 + B1.2 calibration pass.

Key changes vs initial draft:
  * Replaced 13-way softmax confidence with a two-signal model:
        signal_strength = raw top score (clamped 0–1)
        margin          = (top - second) / (top + second)
        confidence      = signal_strength * (0.5 + 0.5 * margin)
  * Low-confidence fallback now uses raw signal_strength (not post-softmax
    probability) so a single phrase hit (w=0.85) is no longer collapsed to
    “general”.
  * Frame bias for `member` now boosts career/work (was empty).
  * Frame bias for `forum` boosts relationship harder + adds family/parenting.
  * Role bias values increased (was 0.10–0.20, now 0.30–0.50).
  * New target_active_bonus: when current_target_id is set, add a base bonus
    to the role-relevant domain so the router knows the user is in a
    relational context.

Non-breaking by design.  Shadow only until B2.
"""
from __future__ import annotations

import os, re, math, logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone as dt_tz
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml
except ImportError:
    yaml = None

log = logging.getLogger("intent_router_v2")
ROUTER_VERSION = "intent_router_v2.1.0"
_LEXICON_PATH = Path(__file__).parent / "lens_registries" / "domain_lexicons.yaml"
_LEXICON_CACHE: Optional[Dict[str, List[Dict[str, Any]]]] = None

DOMAINS = [
    "identity", "relationship", "family", "parenting", "career", "work",
    "leadership", "money", "purpose", "spirituality", "health",
    "growth", "life_direction",
]

LENS_WEIGHTS_PER_DOMAIN: Dict[str, Dict[str, float]] = {
    "identity":       {"astrology": 0.9, "human_design": 1.0, "enneagram": 1.0, "numerology": 0.6, "relationship": 0.0, "timeline": 0.2},
    "relationship":   {"astrology": 0.9, "human_design": 0.8, "enneagram": 0.6, "numerology": 0.3, "relationship": 1.0, "timeline": 0.6},
    "family":         {"astrology": 0.7, "human_design": 0.7, "enneagram": 0.7, "numerology": 0.5, "relationship": 0.9, "timeline": 0.5},
    "parenting":      {"astrology": 0.6, "human_design": 0.8, "enneagram": 0.8, "numerology": 0.4, "relationship": 0.7, "timeline": 0.7},
    "career":         {"astrology": 0.9, "human_design": 0.7, "enneagram": 0.6, "numerology": 0.5, "relationship": 0.2, "timeline": 0.9},
    "work":           {"astrology": 0.8, "human_design": 0.7, "enneagram": 0.6, "numerology": 0.4, "relationship": 0.4, "timeline": 0.7},
    "leadership":     {"astrology": 0.7, "human_design": 1.0, "enneagram": 0.7, "numerology": 0.4, "relationship": 0.4, "timeline": 0.6},
    "money":          {"astrology": 0.9, "human_design": 0.6, "enneagram": 0.5, "numerology": 0.8, "relationship": 0.3, "timeline": 0.7},
    "purpose":        {"astrology": 0.9, "human_design": 0.9, "enneagram": 0.7, "numerology": 0.5, "relationship": 0.2, "timeline": 0.5},
    "spirituality":   {"astrology": 0.8, "human_design": 0.6, "enneagram": 0.6, "numerology": 0.5, "relationship": 0.1, "timeline": 0.5},
    "health":         {"astrology": 0.7, "human_design": 1.0, "enneagram": 0.4, "numerology": 0.3, "relationship": 0.2, "timeline": 0.7},
    "growth":         {"astrology": 0.7, "human_design": 0.8, "enneagram": 1.0, "numerology": 0.4, "relationship": 0.3, "timeline": 0.9},
    "life_direction": {"astrology": 0.9, "human_design": 0.8, "enneagram": 0.7, "numerology": 0.5, "relationship": 0.2, "timeline": 1.0},
}

# B1.2 — tuned frame biases.
# Member/forum frames *strongly* shift the prior toward the inter-personal
# or operational stack, because the user has already declared they're
# discussing someone else.  These are added *raw* to the lexicon score.
FRAME_BIAS: Dict[str, Dict[str, float]] = {
    "forum":   {"relationship": 0.45, "family": 0.10, "growth": 0.05},
    "member":  {"career": 0.40, "work": 0.20, "relationship": 0.15, "identity": 0.10},
    "reflect": {"identity": 0.20, "growth": 0.15, "purpose": 0.10},
    "self":    {},
}

# B1.2 — role biases significantly boosted.  These are tightly tied to
# real saved-people roles and should outweigh stray phrase hits.
ROLE_BIAS: Dict[str, Dict[str, float]] = {
    "parent":    {"family": 0.50, "growth": 0.05},
    "child":     {"parenting": 0.55, "family": 0.15},
    "sibling":   {"family": 0.45},
    "partner":   {"relationship": 0.55, "family": 0.10},
    "spouse":    {"relationship": 0.55, "family": 0.10},
    "friend":    {"relationship": 0.35},
    "colleague": {"work": 0.40, "career": 0.15},
    "boss":      {"career": 0.40, "work": 0.20, "leadership": 0.10},
    "mentor":    {"growth": 0.30, "career": 0.10, "purpose": 0.10},
    "ex":        {"relationship": 0.50, "growth": 0.10},
}

# When current_target_id is set we know the user is in a relational
# context.  Boost the role-implied domain.  Falls back to relationship if
# role is unknown.
TARGET_ACTIVE_BONUS = 0.20

# ---------------------------------------------------------------------------
# B3.1 — Educational-mode disambiguation
# ---------------------------------------------------------------------------
# When a message contains a lens term (astrology body/house/transit, HD
# component, enneagram type token, …) AND no contextual cue (relational,
# career, financial, temporal, conflict, named person) → prefer the
# contextually neutral `identity` synthesis lane instead of collapsing on
# the lens-term's natural domain.
#
# The bonus is intentionally smaller than the strongest natural-domain
# signals (e.g. `between us` w=0.95) so a contextual relational query
# still routes to relationship.  The bonus is applied AFTER lexicon,
# frame, role, and target-active scoring so it doesn't cascade.

_EDU_LENS_TERM_RE = re.compile(
    r"\b("
    r"saturn|venus|mars|jupiter|pluto|mercury|sun|moon|uranus|neptune|"
    r"chiron|north\s+node|south\s+node|nodes?|"
    r"\d+(st|nd|rd|th)\s+house|"
    r"natal|transit|return|ascendant|midheaven|descendant|ic\b|"
    r"manifestor|generator|projector|reflector|sacral|splenic|"
    r"emotional\s+authority|gate\s+\d+|channel\s+\d+|profile\s+\d|"
    r"\d/\d\s*profile|defined\s+\w+\s+center|undefined\s+\w+\s+center|"
    r"my\s+(sun|moon|rising|ascendant|mercury|venus|mars|jupiter|"
    r"saturn|uranus|neptune|pluto|chiron|midheaven|big\s+three|"
    r"chart|natal\s+chart|birth\s+chart|astrology|human\s+design|"
    r"hd\s+type|type|profile|authority|strategy|incarnation\s+cross|"
    r"enneagram|tritype|wing|life\s+path|expression|destiny\s+number|"
    r"soul\s+urge|bazi|day\s+master|gene\s+keys)"
    r")\b",
    re.I)

_EDU_CONTEXTUAL_CUE_RE = re.compile(
    r"\b("
    # relational
    r"mel|wife|husband|partner|spouse|girlfriend|boyfriend|"
    r"with\s+(my|her|his|them)|between\s+(us|me|mel|him|her|them)|"
    r"my\s+(mum|mom|mother|dad|father|sister|brother|sibling|child|"
    r"son|daughter|kid|kids|teen|parents?|in[- ]laws)|"
    r"marriage|divorce|breakup|"
    # career / leadership
    r"founder|cofounder|co-founder|ceo|cto|coo|executive|exec|"
    r"manager|management|board|investor|"
    r"team|company|startup|firm|department|"
    r"fundrais|runway|hiring|layoff|downsiz|fire|fired|promotion|"
    r"role|career|job|workplace|deadline|deliverable|"
    # financial cue
    r"money|salary|wealth|finances?|invest|debt|budget|income|"
    # temporal
    r"today|right\s+now|this\s+(week|month|year)|currently|"
    r"happening|tension|conflict|fight|struggling|stuck\s+with|"
    r"crisis|breakdown|"
    # health
    r"burn(ed|t|out)|exhausted|tired|sick"
    r")\b",
    re.I)

EDUCATIONAL_MODE_BONUS = 0.50

# When educational-mode fires, we also subtract from the lens-collapse
# natural domains (relationship/career/family/money) so a bare
# `my 7th house` style query routes to `identity` instead of collapsing.
# Strictly capped to avoid ever flipping a true positive (e.g. when a
# contextual cue is also present, educational-mode never fires).
EDUCATIONAL_MODE_NATURAL_PENALTY = 1.2
EDUCATIONAL_MODE_NATURAL_DOMAINS = ("relationship", "career", "family", "money")

# If a compound-lane domain (life_direction / growth) has a strong
# signal (>= this floor) the educational-mode override is SKIPPED so the
# compound lane wins — e.g. "Tell me about my Saturn return" → life_direction
# beats "identity" because `saturn return` is a deliberate compound entry.
EDUCATIONAL_MODE_COMPOUND_SUPPRESS_FLOOR = 0.85
EDUCATIONAL_MODE_COMPOUND_DOMAINS = ("life_direction", "growth")

# ---------------------------------------------------------------------------
# B3.2 — Team-relationship anti-collapse
# ---------------------------------------------------------------------------
# Generic team / business-unit phrasing on the `self` frame must NOT
# collapse to `relationship`.  Subtract a fixed penalty from
# `relationship` raw score when:
#   * frame is `self`,
#   * the message contains a generic team / business-unit token,
#   * no real proper-name candidate is present,
#   * no role noun (partner, wife, husband, …) is present.

_TEAM_BIZ_RE = re.compile(
    r"\b("
    r"my\s+(team|management\s+team|leadership\s+team|exec(utive)?\s+team|"
    r"engineering\s+team|product\s+team|cofounders?)|"
    r"the\s+(team|management\s+team|leadership\s+team|exec(utive)?\s+team|"
    r"company|business|board|management|executives?)|"
    r"the\s+org(anisation|anization)?|"
    r"management\s+team|leadership\s+team"
    r")\b",
    re.I)

_ROLE_NOUN_RE = re.compile(
    r"\b("
    r"partner|spouse|wife|husband|girlfriend|boyfriend|"
    r"mum|mom|mother|dad|father|sister|brother|sibling|"
    r"child|children|kid|kids|son|daughter|teen|"
    r"friend|mentor|colleague|coworker|client|boss|ex"
    r")\b",
    re.I)

# Reuse the proper-name candidate regex from relationship_router_v2.
_PROPER_NAME_RE = re.compile(r"\b([A-Z][a-z]{1,30})\b")
_PROPER_NAME_FILTER_LC = {
    "how", "what", "why", "when", "where", "who", "tell", "show", "can",
    "should", "would", "am", "is", "are", "do", "does", "has", "have", "had",
    "i", "me", "my", "we", "us", "our", "you", "your", "they",
    "this", "that", "these", "those", "there", "here", "the", "a", "an",
    "but", "and", "or", "so", "if", "yet",
    "yes", "no", "ok", "okay", "hi", "hey", "hello",
    # imperatives commonly capitalised mid-sentence
    "explain", "describe", "define", "tell", "show", "give", "list", "name",
    "outline", "summarize", "summarise",
    "saturn", "venus", "mars", "jupiter", "pluto", "mercury", "sun",
    "moon", "uranus", "neptune", "chiron", "lilith", "node", "nodes",
    "midheaven", "ascendant", "descendant",
    "aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra",
    "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
    "human", "design", "enneagram", "astrology", "numerology", "bazi",
    "mirror", "chat", "cross", "lens", "lenses", "forum", "reflection",
    "rl", "probe", "test", "today", "monday", "tuesday", "wednesday",
    "thursday", "friday", "saturday", "sunday",
    "ceo", "cto", "coo", "vp", "vpe",
}

TEAM_RELATIONSHIP_PENALTY = 0.35


def _has_proper_name_candidate(text: str) -> bool:
    if not text:
        return False
    for tok in _PROPER_NAME_RE.findall(text):
        if tok.lower() not in _PROPER_NAME_FILTER_LC:
            return True
    return False

TIMELINE_TRIGGERS_PER_DOMAIN = {
    "career", "work", "life_direction", "growth", "parenting",
    "money", "health",
}

# Calibration knobs (B1.1)
SIGNAL_FLOOR_GENERAL = 0.20    # below this raw top score → “general”
SIGNAL_FLOOR_AMBIGUOUS = 0.40  # below this and margin<0.10 → still general
MARGIN_AMBIGUOUS = 0.10        # below this we keep primary but force secondary
MARGIN_STRONG = 0.45           # at/above this we *don't* return a secondary


def _load_lexicon() -> Dict[str, List[Dict[str, Any]]]:
    global _LEXICON_CACHE
    if _LEXICON_CACHE is not None:
        return _LEXICON_CACHE
    if yaml is None or not _LEXICON_PATH.exists():
        _LEXICON_CACHE = {}
        return _LEXICON_CACHE
    with open(_LEXICON_PATH) as f:
        data = yaml.safe_load(f) or {}
    out: Dict[str, List[Dict[str, Any]]] = {}
    for dom, entry in data.items():
        phrases = (entry or {}).get("phrases") or []
        out[dom] = [{"p": str(p["p"]).lower(), "w": float(p["w"])} for p in phrases]
    _LEXICON_CACHE = out
    return out


def reset_lexicon_cache() -> None:
    """Test/dev helper — forces a reload from disk on next classify call."""
    global _LEXICON_CACHE
    _LEXICON_CACHE = None


@dataclass
class IntentEnvelope:
    primary_domain: str
    secondary_domains: List[str]
    confidence: float
    signal_strength: float
    margin: float
    relationship_relevant: bool
    timeline_relevant: bool
    lens_priority: List[str]
    frame_resolved: str
    target_resolved: Optional[str]
    evidence: Dict[str, Any]
    router_version: str = ROUTER_VERSION
    computed_at: str = field(default_factory=lambda: datetime.now(dt_tz.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _phrase_score(text: str, phrases: List[Dict[str, Any]]) -> Tuple[float, List[str]]:
    text_low = " " + text.lower() + " "
    score = 0.0
    matched: List[str] = []
    for entry in phrases:
        p = entry["p"]
        if p in text_low:
            score += entry["w"]
            matched.append(p)
    return score, matched


def _lens_priority_for(domain: str) -> List[str]:
    weights = LENS_WEIGHTS_PER_DOMAIN.get(domain, {})
    return [k for k, _ in sorted(weights.items(), key=lambda kv: -kv[1])]


def _general_envelope(
    *, frame: str, target_id: Optional[str], reason: str,
    raw_scores: Dict[str, float],
    matched: Dict[str, List[str]],
) -> IntentEnvelope:
    return IntentEnvelope(
        primary_domain="general",
        secondary_domains=[],
        confidence=0.0,
        signal_strength=round(max(raw_scores.values()) if raw_scores else 0.0, 4),
        margin=0.0,
        relationship_relevant=bool(target_id) or frame in ("forum", "member"),
        timeline_relevant=False,
        lens_priority=["cross_lens_atoms"],
        frame_resolved=frame,
        target_resolved=target_id,
        evidence={
            "matched_phrases": matched,
            "raw_scores": {k: round(v, 4) for k, v in raw_scores.items()},
            "fallback_reason": reason,
        },
    )


def classify_intent_v2(
    *, message: str,
    history: Optional[List[Dict[str, Any]]] = None,
    active_frame: str = "self",
    current_target_id: Optional[str] = None,
    relationship_role: Optional[str] = None,
    forum_context: Optional[Dict[str, Any]] = None,
) -> IntentEnvelope:
    """Classify a single message into an IntentEnvelope.  Shadow-mode safe."""
    history = history or []
    text = (message or "").strip()
    lexicon = _load_lexicon()

    # 1. Keyword/phrase layer
    raw_scores: Dict[str, float] = {d: 0.0 for d in DOMAINS}
    phrase_evidence: Dict[str, List[str]] = {}
    for dom in DOMAINS:
        sc, matched = _phrase_score(text, lexicon.get(dom, []))
        raw_scores[dom] = sc
        if matched:
            phrase_evidence[dom] = matched

    # 2. History bias (last 3 user turns).  Capped to avoid runaway drift.
    hist_bias: Dict[str, float] = {d: 0.0 for d in DOMAINS}
    for turn in (history or [])[-3:]:
        prev = turn.get("domain")
        if prev in hist_bias:
            hist_bias[prev] += 0.10
    for d in DOMAINS:
        raw_scores[d] += hist_bias[d]

    # 3. Frame bias
    for d, bonus in (FRAME_BIAS.get(active_frame) or {}).items():
        raw_scores[d] = raw_scores.get(d, 0.0) + bonus

    # 4. Role bias
    role_lc = (relationship_role or "").lower()
    for d, bonus in (ROLE_BIAS.get(role_lc) or {}).items():
        raw_scores[d] = raw_scores.get(d, 0.0) + bonus

    # 5. Target-active bonus — when the user is clearly talking about
    #    someone they have saved, push the role-relevant domain.  Falls
    #    back to “relationship” when role is unknown.
    if current_target_id:
        if role_lc and ROLE_BIAS.get(role_lc):
            # boost the top domain in that role's bias map
            primary_dom = max(ROLE_BIAS[role_lc].items(), key=lambda kv: kv[1])[0]
            raw_scores[primary_dom] = raw_scores.get(primary_dom, 0.0) + TARGET_ACTIVE_BONUS
        else:
            raw_scores["relationship"] = raw_scores.get("relationship", 0.0) + TARGET_ACTIVE_BONUS

    # 5b. B3.2 — team-relationship anti-collapse.
    # Generic team / business-unit phrasing in the `self` frame must NOT
    # collapse to `relationship`.  We only apply the penalty when there
    # is no proper name, no role noun, and no explicit target.
    team_penalty_applied = False
    if (active_frame == "self"
            and not current_target_id
            and _TEAM_BIZ_RE.search(text)
            and not _has_proper_name_candidate(text)
            and not _ROLE_NOUN_RE.search(text)):
        raw_scores["relationship"] = (
            raw_scores.get("relationship", 0.0) - TEAM_RELATIONSHIP_PENALTY
        )
        team_penalty_applied = True

    # 5c. B3.1 — educational-mode disambiguation.
    # When a lens term is present without any contextual cue, prefer
    # the contextually neutral `identity` synthesis lane.  Skip when
    # current_target_id is set (the user has explicitly bound a
    # person — that overrides any "educational" framing).
    educational_mode_applied = False
    if (not current_target_id
            and _EDU_LENS_TERM_RE.search(text)
            and not _EDU_CONTEXTUAL_CUE_RE.search(text)
            and not _has_proper_name_candidate(text)):
        # Suppress when a compound-lane domain has a deliberate strong
        # signal (e.g. saturn return → life_direction).  In that case
        # the compound lane is the intended answer; educational mode
        # would incorrectly flatten it to identity.
        compound_active = any(
            raw_scores.get(d, 0.0) >= EDUCATIONAL_MODE_COMPOUND_SUPPRESS_FLOOR
            for d in EDUCATIONAL_MODE_COMPOUND_DOMAINS
        )
        if not compound_active:
            raw_scores["identity"] = (
                raw_scores.get("identity", 0.0) + EDUCATIONAL_MODE_BONUS
            )
            for _dom in EDUCATIONAL_MODE_NATURAL_DOMAINS:
                cur = raw_scores.get(_dom, 0.0)
                if cur > 0:
                    raw_scores[_dom] = max(0.0, cur - EDUCATIONAL_MODE_NATURAL_PENALTY)
            educational_mode_applied = True

    # 6. Rank by raw score (no softmax)
    ranked = sorted(raw_scores.items(), key=lambda kv: -kv[1])
    top, top_score = ranked[0]
    second, second_score = ranked[1] if len(ranked) > 1 else ("general", 0.0)

    # If no signal anywhere → general (no_signal).
    if top_score <= 0.0:
        return _general_envelope(frame=active_frame, target_id=current_target_id,
                                 reason="no_signal",
                                 raw_scores=raw_scores, matched=phrase_evidence)

    # If signal too weak → general (low_signal).  This is the *real*
    # fallback gate, replacing the broken post-softmax one.
    if top_score < SIGNAL_FLOOR_GENERAL:
        return _general_envelope(frame=active_frame, target_id=current_target_id,
                                 reason="low_signal",
                                 raw_scores=raw_scores, matched=phrase_evidence)

    # margin in [0,1] — how decisive is top vs second.
    denom = top_score + second_score
    margin = (top_score - second_score) / denom if denom > 0 else 1.0
    signal_strength = min(top_score, 1.0)
    confidence = round(signal_strength * (0.5 + 0.5 * margin), 4)

    # ambiguous: weak signal AND tight margin → still general
    if top_score < SIGNAL_FLOOR_AMBIGUOUS and margin < MARGIN_AMBIGUOUS:
        env = _general_envelope(frame=active_frame, target_id=current_target_id,
                                reason="weak_ambiguous",
                                raw_scores=raw_scores, matched=phrase_evidence)
        env.signal_strength = round(signal_strength, 4)
        env.margin = round(margin, 4)
        return env

    # secondary domain rules
    if margin < MARGIN_STRONG and second_score > 0:
        secondary = [second]
    else:
        secondary = []

    lens_priority = _lens_priority_for(top)
    relationship_relevant = (
        top in ("relationship", "family", "parenting")
        or bool(current_target_id)
        or active_frame in ("forum", "member")
    )
    timeline_relevant = top in TIMELINE_TRIGGERS_PER_DOMAIN

    return IntentEnvelope(
        primary_domain=top,
        secondary_domains=secondary,
        confidence=confidence,
        signal_strength=round(signal_strength, 4),
        margin=round(margin, 4),
        relationship_relevant=relationship_relevant,
        timeline_relevant=timeline_relevant,
        lens_priority=lens_priority,
        frame_resolved=active_frame,
        target_resolved=current_target_id,
        evidence={
            "matched_phrases":     phrase_evidence,
            "raw_scores":          {k: round(v, 4) for k, v in raw_scores.items()},
            "history_bias":        {k: round(v, 4) for k, v in hist_bias.items() if v},
            "frame_bias_applied":  FRAME_BIAS.get(active_frame, {}),
            "role_bias_applied":   ROLE_BIAS.get(role_lc, {}),
            "target_active_bonus": TARGET_ACTIVE_BONUS if current_target_id else 0.0,
            "team_penalty_applied": team_penalty_applied,
            "educational_mode_applied": educational_mode_applied,
            "top_score":           round(top_score, 4),
            "second":              second,
            "second_score":        round(second_score, 4),
            "fallback_reason":     None,
        },
    )


def shadow_mode_enabled() -> bool:
    return os.environ.get("INTENT_ROUTER_V2_SHADOW", "true").lower() in ("1", "true", "yes")


def cutover_enabled() -> bool:
    """B2 will flip this; B1 keeps it false."""
    return os.environ.get("INTENT_ROUTER_V2_CUTOVER", "false").lower() in ("1", "true", "yes")


# ─────────────────────────────────────────────────────────────────────────────
# Stage 1 rollout — per-user bucketed cutover  (intent-router-v2-stage1-v1)
# ─────────────────────────────────────────────────────────────────────────────
#
# Design intent (per Stage 1 plan, 2026-06-12):
#
#   * Each user is deterministically hashed into a bucket in [0, 99]. The
#     hash is sticky — the same `user_id` always lands in the same bucket
#     across processes, pods, and restarts. This is the *only* source of
#     truth for cutover eligibility during the gradual rollout window.
#
#   * `cutover_enabled_for(user_id)` returns True iff:
#       (a) INTENT_ROUTER_V2_CUTOVER == "true"  → full cutover override
#           (ignores the percent — used for 100% rollout / emergency flips), OR
#       (b) INTENT_ROUTER_V2_ROLLOUT_PERCENT > 0
#           AND _stage1_bucket(user_id) < ROLLOUT_PERCENT
#           → gradual rollout bucket eligibility.
#
#   * Empty / None user_id → False (NEVER routes anonymous traffic through V2
#     during gradual rollout; only flips with the full cutover flag).
#
#   * Default environment state (CUTOVER=false, ROLLOUT_PERCENT=0) means the
#     function always returns False → shadow-only behaviour is preserved.
#
# Activation env vars (DO NOT SET WITHOUT EXPLICIT AUTHORIZATION):
#   INTENT_ROUTER_V2_CUTOVER           "true"|"false"   default "false"
#   INTENT_ROUTER_V2_ROLLOUT_PERCENT   0..100 (int)     default 0
#

_STAGE1_HASH_SALT = "intent_router_v2.stage1.v1"  # changing this re-shuffles buckets


def _stage1_bucket(user_id: Optional[str]) -> int:
    """Deterministic per-user bucket in [0, 99].

    Uses SHA-256 over `salt|user_id` and reads the first 4 bytes as a
    big-endian unsigned int, then mods by 100. Same inputs → same bucket
    everywhere; uniform distribution across [0, 99].

    Returns -1 for empty / None inputs (treated as ineligible for the
    bucketed rollout; the caller MUST check before comparing to a
    percent threshold).
    """
    if not user_id:
        return -1
    import hashlib  # local import → avoid touching top-level imports
    h = hashlib.sha256(
        (_STAGE1_HASH_SALT + "|" + str(user_id)).encode("utf-8")
    ).digest()
    return int.from_bytes(h[:4], "big") % 100


def _rollout_percent() -> int:
    """Read INTENT_ROUTER_V2_ROLLOUT_PERCENT, clamped to [0, 100].

    Invalid / unparseable values fall back to 0 (safe default — no traffic
    routed through V2 from the bucketed path).
    """
    raw = os.environ.get("INTENT_ROUTER_V2_ROLLOUT_PERCENT", "0")
    try:
        n = int(str(raw).strip())
    except Exception:
        return 0
    if n < 0:
        return 0
    if n > 100:
        return 100
    return n


def cutover_decision_for(user_id: Optional[str]) -> Dict[str, Any]:
    """Return the full cutover decision with telemetry fields.

    Used by both `cutover_enabled_for()` and the shadow-receipt builder so
    every dashboarded decision carries the exact reason + thresholds.

    Shape:
      {
        "enabled":         bool,
        "reason":          "cutover_flag_true"
                         | "below_rollout_percent"
                         | "above_rollout_percent"
                         | "no_user_id"
                         | "rollout_percent_zero",
        "stage1_bucket":   int (-1 if no user_id),
        "rollout_percent": int (0..100),
        "cutover_flag":    bool,
        "salt":            str (so re-shuffles can be detected),
      }
    """
    cutover_flag = cutover_enabled()
    percent = _rollout_percent()
    bucket = _stage1_bucket(user_id)

    # Reason ladder — first match wins.
    if cutover_flag:
        reason = "cutover_flag_true"
        enabled = True
    elif bucket < 0:
        reason = "no_user_id"
        enabled = False
    elif percent <= 0:
        reason = "rollout_percent_zero"
        enabled = False
    elif bucket < percent:
        reason = "below_rollout_percent"
        enabled = True
    else:
        reason = "above_rollout_percent"
        enabled = False

    return {
        "enabled":         enabled,
        "reason":          reason,
        "stage1_bucket":   bucket,
        "rollout_percent": percent,
        "cutover_flag":    cutover_flag,
        "salt":            _STAGE1_HASH_SALT,
    }


def cutover_enabled_for(user_id: Optional[str]) -> bool:
    """Boolean form of `cutover_decision_for()` — the single gate the
    runtime should call before routing a request through V2 (post-rollout).

    DURING SHADOW MODE this function's return value is IGNORED by the
    live request handler — it is only consumed by the receipt-building
    code so dashboards can verify the rollout *would* land the expected
    distribution before any flag flip.
    """
    return cutover_decision_for(user_id)["enabled"]
