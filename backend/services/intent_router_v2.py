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
