"""intent_router_v2 — Mirror Chat V2 Slice B1 (SHADOW MODE).

Non-breaking by design. Runs in parallel with legacy routers when
INTENT_ROUTER_V2_SHADOW=true; output is logged to the receipts collection
but MUST NOT influence the user-visible response.

The production cutover happens in Slice B2 by flipping a separate flag.
"""
from __future__ import annotations

import os, re, math, logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone as dt_tz
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    yaml = None

log = logging.getLogger("intent_router_v2")
ROUTER_VERSION = "intent_router_v2.0.0"
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

FRAME_BIAS: Dict[str, Dict[str, float]] = {
    "forum":   {"relationship": 0.10, "growth": 0.05},
    "reflect": {"identity": 0.10, "growth": 0.10},
    "member":  {"relationship": 0.15},
    "self":    {},
}

ROLE_BIAS: Dict[str, Dict[str, float]] = {
    "parent":  {"family": 0.20},
    "child":   {"parenting": 0.20, "family": 0.10},
    "sibling": {"family": 0.15},
    "partner": {"relationship": 0.20},
    "friend":  {"relationship": 0.10},
    "colleague": {"work": 0.15},
}

TIMELINE_TRIGGERS_PER_DOMAIN = {
    "career", "work", "life_direction", "growth", "parenting",
    "money", "health",
}


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


@dataclass
class IntentEnvelope:
    primary_domain: str
    secondary_domains: List[str]
    confidence: float
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


def _phrase_score(text: str, phrases: List[Dict[str, Any]]) -> tuple[float, List[str]]:
    text_low = " " + text.lower() + " "
    score = 0.0
    matched: List[str] = []
    for entry in phrases:
        p = entry["p"]
        if p in text_low:
            score += entry["w"]
            matched.append(p)
    return score, matched


def _softmax(scores: Dict[str, float]) -> Dict[str, float]:
    if not scores:
        return {}
    mx = max(scores.values())
    exps = {k: math.exp(v - mx) for k, v in scores.items()}
    s = sum(exps.values()) or 1.0
    return {k: v / s for k, v in exps.items()}


def _lens_priority_for(domain: str) -> List[str]:
    weights = LENS_WEIGHTS_PER_DOMAIN.get(domain, {})
    return [k for k, _ in sorted(weights.items(), key=lambda kv: -kv[1])]


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

    # 2. History bias (light Laplace smoothing on last 3 user turns)
    hist_bias: Dict[str, float] = {d: 0.0 for d in DOMAINS}
    for turn in (history or [])[-3:]:
        prev = turn.get("domain")
        if prev in hist_bias:
            hist_bias[prev] += 0.15
    for d in DOMAINS:
        raw_scores[d] += hist_bias[d]

    # 3. Frame bias
    for d, bonus in (FRAME_BIAS.get(active_frame) or {}).items():
        raw_scores[d] = raw_scores.get(d, 0.0) + bonus

    # 4. Role bias (target relationship)
    if relationship_role:
        for d, bonus in (ROLE_BIAS.get(relationship_role.lower()) or {}).items():
            raw_scores[d] = raw_scores.get(d, 0.0) + bonus

    # 5. Aggregate
    probs = _softmax(raw_scores)
    ranked = sorted(probs.items(), key=lambda kv: -kv[1])
    top, top_p = ranked[0]
    second, second_p = ranked[1] if len(ranked) > 1 else ("general", 0.0)
    confidence = round(top_p - second_p, 4)

    # If everything is zero (no phrase match, no bias) → fall back to general
    if max(raw_scores.values()) <= 0.0:
        return IntentEnvelope(
            primary_domain="general",
            secondary_domains=[],
            confidence=0.0,
            relationship_relevant=bool(current_target_id),
            timeline_relevant=False,
            lens_priority=["cross_lens_atoms"],
            frame_resolved=active_frame,
            target_resolved=current_target_id,
            evidence={
                "matched_phrases": [],
                "raw_scores": raw_scores,
                "fallback_reason": "no_signal",
            },
        )

    # Confidence buckets
    if confidence >= 0.10:
        secondary = [second] if (top_p - second_p) < 0.20 and second_p > 0.05 else []
    else:
        secondary = [second] if second_p > 0.05 else []

    # Low confidence → bias to general for the primary, keep evidence
    fallback_reason = None
    if top_p < 0.30 and confidence < 0.05:
        primary = "general"
        fallback_reason = "low_confidence"
        lens_priority = ["cross_lens_atoms"]
    else:
        primary = top
        lens_priority = _lens_priority_for(primary)

    relationship_relevant = (
        primary in ("relationship", "family", "parenting")
        or bool(current_target_id)
        or active_frame in ("forum", "member")
    )
    timeline_relevant = primary in TIMELINE_TRIGGERS_PER_DOMAIN

    env = IntentEnvelope(
        primary_domain=primary,
        secondary_domains=secondary,
        confidence=confidence,
        relationship_relevant=relationship_relevant,
        timeline_relevant=timeline_relevant,
        lens_priority=lens_priority,
        frame_resolved=active_frame,
        target_resolved=current_target_id,
        evidence={
            "matched_phrases":  phrase_evidence,
            "raw_scores":       {k: round(v, 4) for k, v in raw_scores.items()},
            "probabilities":    {k: round(v, 4) for k, v in probs.items()},
            "history_bias":     {k: round(v, 4) for k, v in hist_bias.items() if v},
            "frame_bias_applied":  FRAME_BIAS.get(active_frame, {}),
            "role_bias_applied":   ROLE_BIAS.get((relationship_role or "").lower(), {}),
            "fallback_reason":  fallback_reason,
        },
    )
    return env


def shadow_mode_enabled() -> bool:
    return os.environ.get("INTENT_ROUTER_V2_SHADOW", "true").lower() in ("1", "true", "yes")
