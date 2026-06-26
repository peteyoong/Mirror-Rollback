"""mirror_knowledge_graph.py — Ephemeral per-request Knowledge Graph V1
========================================================================

Build marker:  mirror-knowledge-graph-v1

Clusters normalized evidence signals by theme; computes cross-lens
convergence + agreement + confidence.  Pure in-memory, no DB, no
persistence.
"""
from __future__ import annotations
from collections import defaultdict
from typing import Any, Dict, List

GRAPH_VERSION = "mirror-knowledge-graph-v1.5"


def _confidence_label(score: float) -> str:
    if score >= 0.70: return "high"
    if score >= 0.45: return "medium"
    return "emerging"


def _provenance_summary(sigs):
    """Aggregate provenance status across a cluster's signals.
    Returns (rollup_status, penalty_h) where penalty_h is in [0, 1].
    Rollup logic:
      * all verified → 'verified', penalty 0.0
      * any stale/missing → 'mixed' if some verified, else 'suspect'
      * any repaired present → keeps verified rollup but logs
      * all unknown → 'unknown', penalty 0.05
    """
    statuses = [(s.get("provenance") or {}).get("status") or "unknown" for s in sigs]
    if not statuses:
        return "unknown", 0.05
    s_set = set(statuses)
    if s_set == {"verified"}:
        return "verified", 0.0
    if s_set == {"unknown"}:
        return "unknown", 0.05
    has_bad = any(x in s_set for x in ("stale", "missing", "suspect"))
    has_good = "verified" in s_set
    if has_bad and has_good:
        return "mixed", 0.10
    if has_bad and not has_good:
        return "suspect", 0.20
    if "repaired" in s_set and has_good:
        return "verified", 0.0
    return "mixed", 0.05


def build_knowledge_graph(signals):
    """Cluster signals by `theme`; compute supporting lenses, agreement
    score, and confidence label per cluster."""
    by_theme: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for s in signals:
        if not isinstance(s, dict): continue
        theme = s.get("theme") or "growth"
        by_theme[theme].append(s)

    clusters: List[Dict[str, Any]] = []
    all_lenses_used = set()
    for theme, sigs in by_theme.items():
        lenses = sorted({s.get("lens") for s in sigs if s.get("lens")})
        all_lenses_used.update(lenses)
        # Agreement: weighted by signal strength, normalized by lens count.
        avg_strength = sum(float(s.get("strength", 0.5)) for s in sigs) / max(len(sigs), 1)
        avg_conf     = sum(float(s.get("confidence", 0.5)) for s in sigs) / max(len(sigs), 1)
        # Convergence multiplier: +0.15 per additional lens beyond 1, capped
        lens_bonus = min(0.30, max(0, len(lenses) - 1) * 0.15)
        agreement = round(min(1.0, avg_strength + lens_bonus), 3)
        # Combined confidence numeric
        conf_score = round(min(1.0, avg_conf * 0.7 + lens_bonus * 1.5), 3)
        # Polarity tally helps the orchestrator pick the right narrative slot.
        polarity_counts: Dict[str, int] = defaultdict(int)
        for s in sigs:
            polarity_counts[s.get("polarity", "evidence")] += 1
        # ── V1.5 provenance-aware confidence ──
        prov_status, prov_pen = _provenance_summary(sigs)
        conf_score_v15 = round(max(0.0, conf_score - prov_pen), 3)
        clusters.append({
            "theme":              theme,
            "signals":            sigs,
            "supporting_lenses":  lenses,
            "lens_count":         len(lenses),
            "signal_count":       len(sigs),
            "agreement_score":    agreement,
            "confidence_score":   conf_score_v15,
            "confidence":         _confidence_label(conf_score_v15 if len(lenses) >= 2 else conf_score_v15 * 0.7),
            "polarity_tally":     dict(polarity_counts),
            # ── V1.5 fields ──
            "provenance_status":  prov_status,
            "provenance_penalty": prov_pen,
            "layers":             sorted({s.get("layer") for s in sigs if s.get("layer")}),
            "mechanics":          sorted({s.get("mechanic") for s in sigs if s.get("mechanic")}),
            "evidence_types":     sorted({s.get("evidence_type") for s in sigs if s.get("evidence_type")}),
            "time_scopes":        sorted({s.get("time_scope") for s in sigs if s.get("time_scope")}),
            "domains":            sorted({s.get("domain") for s in sigs if s.get("domain")}),
        })

    # Sort clusters by agreement DESC then lens_count DESC for deterministic
    # ordering.
    clusters.sort(key=lambda c: (-c["agreement_score"], -c["lens_count"], c["theme"]))

    nodes = [{"id": s["id"], "lens": s.get("lens"), "theme": s.get("theme"),
              "polarity": s.get("polarity"), "source_path": s.get("source_path"),
              # V1.5 — additive node attributes
              "layer": s.get("layer"), "mechanic": s.get("mechanic"),
              "evidence_type": s.get("evidence_type"),
              "provenance_status": (s.get("provenance") or {}).get("status")}
             for s in signals if isinstance(s, dict) and s.get("id")]

    # ── V1.5 cross-cuts: cluster by axes other than theme.
    def _bucket(key):
        b = defaultdict(list)
        for s in signals:
            if not isinstance(s, dict): continue
            v = s.get(key) or ((s.get("provenance") or {}).get("status") if key == "provenance_status" else None)
            if v is None: continue
            b[v].append({"id": s.get("id"), "lens": s.get("lens"), "theme": s.get("theme")})
        return {k: vs for k, vs in b.items()}

    cross_cuts = {
        "by_domain":            _bucket("domain"),
        "by_layer":             _bucket("layer"),
        "by_mechanic":          _bucket("mechanic"),
        "by_time_scope":        _bucket("time_scope"),
        "by_provenance_status": _bucket("provenance_status"),
        "by_evidence_type":     _bucket("evidence_type"),
    }

    return {
        "nodes":      nodes,
        "clusters":   clusters,
        "cross_cuts": cross_cuts,
        "diagnostics": {
            "signal_count":   len(signals),
            "lens_count":     len(all_lenses_used),
            "lenses_present": sorted(all_lenses_used),
            "cluster_count":  len(clusters),
            "engine_version": GRAPH_VERSION,
        },
    }
