"""cross_lens_synthesis_v2 · receipt-only telemetry.

Phase 2 of the cross-lens synthesis stack. Surfaces *agreement*, *tension*,
and *polarity* signals across the domain space WITHOUT touching the live
response path.

Design properties
-----------------
* Strictly additive. The function is called from the receipt-builder
  hook and writes a single nested dict into the receipt. Existing lens
  outputs (`lens_payloads`, `lens_priority`, `intent_envelope`) are
  preserved verbatim.
* No DB reads. No network. No randomness. Pure function of
  `raw_scores` + matched-phrase evidence.
* Conservative thresholds; surfaces *meaningful* patterns only, never
  invents deterministic conflicts.

Polarity pairs
--------------
We encode a small set of domain pairs where simultaneous strong signals
represent a real-world tension (not a routing bug):

    relationship  ↔  career         — work/relationship pull
    relationship  ↔  leadership     — founder spouse-vs-team tension
    leadership    ↔  health         — burnout-while-leading
    career        ↔  purpose        — "am I in the right thing?"
    money         ↔  purpose        — runway vs mission
    growth        ↔  family         — individuation vs roots
    identity      ↔  relationship   — self vs partnered self
    life_direction ↔ identity       — "who am I becoming?"

A *tension* is surfaced when BOTH sides of a pair exceed `TENSION_FLOOR`
AND their absolute score difference is < `TENSION_PARITY_BAND`. An
*agreement* is surfaced when 2+ semantically-aligned domains (same
pair-cluster) all exceed `AGREEMENT_FLOOR`.

Return shape
------------
```
{
  "version":     "cross_lens_synthesis_v2.1.0",
  "computed":    true,
  "agreements":  [{ "cluster": "founder_op", "domains": ["career","leadership"], "min_score": 0.62 }],
  "tensions":    [{ "pair": ["relationship","career"], "scores": [0.51,0.55], "delta": 0.04 }],
  "polarity":    "founder_op_with_relational_pull"   | <other-label> | null,
  "lens_coverage": ["astrology", "human_design", "enneagram"],
  "lens_outputs_preserved": true
}
```
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

VERSION = "cross_lens_synthesis_v2.2.0"

# Thresholds tuned to surface only meaningful patterns.
TENSION_FLOOR        = 0.45   # both sides must exceed this
TENSION_PARITY_BAND  = 0.25   # max delta to be called a "tension"
AGREEMENT_FLOOR      = 0.40   # all members of a cluster must exceed this

# v2.2 — contradiction surface.
# A "contradiction" is a stronger signal than a tension: ONE side of a
# polarity pair dominates AND the opposing cluster also has measurable
# agreement. Surfaces patterns like "the work cluster is firing and
# you're explicitly talking about your wife" — the dominant frame and
# the counter-cluster are in active opposition, not just parity.
CONTRADICTION_DOMINANT_FLOOR = 0.65   # dominant side must exceed
CONTRADICTION_COUNTER_FLOOR  = 0.35   # counter side must still register

# Polarity pairs — ordered list; first matching pair wins the top-level
# `polarity` label so the dashboard reads a single dominant pattern.
POLARITY_PAIRS: List[Tuple[str, str, str]] = [
    ("relationship",   "leadership",     "founder_with_spouse_pull"),
    ("relationship",   "career",         "work_relationship_pull"),
    ("leadership",     "health",         "leading_through_burnout"),
    ("career",         "purpose",        "role_purpose_misalignment"),
    ("money",          "purpose",        "runway_vs_mission"),
    ("growth",         "family",         "individuation_vs_roots"),
    ("identity",       "relationship",   "self_vs_partnered_self"),
    ("life_direction", "identity",       "becoming_question"),
]

# Agreement clusters — semantically aligned domain groups.
AGREEMENT_CLUSTERS: Dict[str, List[str]] = {
    "founder_op":      ["career", "leadership", "money"],
    "self_inquiry":    ["identity", "growth", "life_direction"],
    "relational_arc":  ["relationship", "family", "parenting"],
    "vocational_arc":  ["career", "purpose", "life_direction"],
    "embodied_arc":    ["health", "growth", "spirituality"],
}

# Which lens types are typically referenced by matched-phrase evidence.
# Used purely to enumerate `lens_coverage` on the receipt.
_LENS_CUES: Dict[str, List[str]] = {
    "astrology":     ["saturn", "venus", "mars", "jupiter", "pluto", "sun",
                      "moon", "ascendant", "midheaven", "house", "transit",
                      "chart", "natal", "return", "node", "chiron",
                      "vertex", "lilith", "synastry", "composite"],
    "human_design": ["human design", "manifestor", "generator", "projector",
                     "reflector", "authority", "profile", "channel",
                     "gate", "hd type", "incarnation cross", "strategy"],
    "enneagram":    ["enneagram", "type", "wing", "tritype"],
    "numerology":   ["life path", "destiny number", "soul urge",
                     "expression", "personality number"],
    "bazi":         ["bazi", "day master", "four pillars"],
    "gene_keys":    ["gene keys", "sphere"],
}


def _lens_coverage_from_evidence(
    matched_phrases: Dict[str, List[str]] | None,
    message: str,
) -> List[str]:
    text = (message or "").lower()
    blob = text + " " + " ".join(
        sum((v or [] for v in (matched_phrases or {}).values()), [])
    ).lower()
    out: List[str] = []
    for lens, cues in _LENS_CUES.items():
        if any(c in blob for c in cues):
            out.append(lens)
    return out


def compute_synthesis_v2(
    *,
    intent_envelope: Dict[str, Any],
    message: str,
) -> Dict[str, Any]:
    """Compute the cross-lens synthesis v2 telemetry block.

    Pure function. Never raises (catches its own errors and falls back
    to a `computed=false` payload so the receipt builder never fails).
    """
    try:
        evidence = intent_envelope.get("evidence") or {}
        raw_scores: Dict[str, float] = {
            k: float(v) for k, v in (evidence.get("raw_scores") or {}).items()
        }
        matched = evidence.get("matched_phrases") or {}

        # Tensions — walk the polarity pairs and pick out any with
        # parity above the floor.
        tensions: List[Dict[str, Any]] = []
        chosen_label: Optional[str] = None
        for a, b, label in POLARITY_PAIRS:
            sa = raw_scores.get(a, 0.0)
            sb = raw_scores.get(b, 0.0)
            if sa >= TENSION_FLOOR and sb >= TENSION_FLOOR:
                delta = abs(sa - sb)
                if delta <= TENSION_PARITY_BAND:
                    tensions.append({
                        "pair":   [a, b],
                        "scores": [round(sa, 4), round(sb, 4)],
                        "delta":  round(delta, 4),
                        "label":  label,
                    })
                    if chosen_label is None:
                        chosen_label = label

        # Agreements — clusters where every member exceeds the floor.
        agreements: List[Dict[str, Any]] = []
        for cluster, members in AGREEMENT_CLUSTERS.items():
            member_scores = [raw_scores.get(m, 0.0) for m in members]
            qualifying = [s for s in member_scores if s >= AGREEMENT_FLOOR]
            if len(qualifying) >= 2:
                agreements.append({
                    "cluster":   cluster,
                    "domains":   members,
                    "min_score": round(min(qualifying), 4),
                    "hit_count": len(qualifying),
                })

        # v2.2 — Contradictions: one side of a polarity pair dominates,
        # the other side still registers above a softer floor. Distinct
        # from tensions (parity); these tag active opposition where the
        # dominant frame is winning but the counter-frame is asserting.
        contradictions: List[Dict[str, Any]] = []
        for a, b, label in POLARITY_PAIRS:
            sa = raw_scores.get(a, 0.0)
            sb = raw_scores.get(b, 0.0)
            dom, counter = (a, b) if sa >= sb else (b, a)
            dom_score, counter_score = (max(sa, sb), min(sa, sb))
            if (dom_score >= CONTRADICTION_DOMINANT_FLOOR
                    and counter_score >= CONTRADICTION_COUNTER_FLOOR
                    and (dom_score - counter_score) > TENSION_PARITY_BAND):
                contradictions.append({
                    "dominant":       dom,
                    "counter":        counter,
                    "dominant_score": round(dom_score, 4),
                    "counter_score":  round(counter_score, 4),
                    "delta":          round(dom_score - counter_score, 4),
                    "label":          f"{label}__{dom}_dominant",
                })

        # Polarity strength: the absolute strength of the chosen
        # polarity signal, scaled 0..1. Tensions contribute more than
        # contradictions (parity is the stronger semantic signal).
        polarity_strength = 0.0
        if tensions:
            top = tensions[0]
            polarity_strength = min(1.0, (top["scores"][0] + top["scores"][1]) / 2.0)
        elif contradictions:
            top = contradictions[0]
            polarity_strength = min(1.0, top["dominant_score"] * 0.6
                                    + top["counter_score"] * 0.4)

        lens_coverage = _lens_coverage_from_evidence(matched, message)

        return {
            "version":                VERSION,
            "computed":               True,
            "agreements":             agreements,
            "tensions":               tensions,
            "contradictions":         contradictions,
            "polarity":               chosen_label,
            "polarity_strength":      round(polarity_strength, 4),
            "lens_coverage":          lens_coverage,
            "lens_outputs_preserved": True,
            "thresholds": {
                "tension_floor":       TENSION_FLOOR,
                "tension_parity_band": TENSION_PARITY_BAND,
                "agreement_floor":     AGREEMENT_FLOOR,
                "contradiction_dominant_floor": CONTRADICTION_DOMINANT_FLOOR,
                "contradiction_counter_floor":  CONTRADICTION_COUNTER_FLOOR,
            },
        }
    except Exception as e:  # never surface to caller
        return {
            "version":   VERSION,
            "computed":  False,
            "error":     f"{type(e).__name__}: {e!s}",
            "lens_outputs_preserved": True,
        }
