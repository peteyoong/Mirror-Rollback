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

GRAPH_VERSION = "mirror-knowledge-graph-v1"


def _confidence_label(score: float) -> str:
    if score >= 0.70: return "high"
    if score >= 0.45: return "medium"
    return "emerging"


def build_knowledge_graph(signals: List[Dict[str, Any]]) -> Dict[str, Any]:
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
        clusters.append({
            "theme":              theme,
            "signals":            sigs,
            "supporting_lenses":  lenses,
            "lens_count":         len(lenses),
            "signal_count":       len(sigs),
            "agreement_score":    agreement,
            "confidence_score":   conf_score,
            "confidence":         _confidence_label(conf_score if len(lenses) >= 2 else conf_score * 0.7),
            "polarity_tally":     dict(polarity_counts),
        })

    # Sort clusters by agreement DESC then lens_count DESC for deterministic
    # ordering.
    clusters.sort(key=lambda c: (-c["agreement_score"], -c["lens_count"], c["theme"]))

    nodes = [{"id": s["id"], "lens": s.get("lens"), "theme": s.get("theme"),
              "polarity": s.get("polarity"), "source_path": s.get("source_path")}
             for s in signals if isinstance(s, dict) and s.get("id")]

    return {
        "nodes":    nodes,
        "clusters": clusters,
        "diagnostics": {
            "signal_count":   len(signals),
            "lens_count":     len(all_lenses_used),
            "lenses_present": sorted(all_lenses_used),
            "cluster_count":  len(clusters),
            "engine_version": GRAPH_VERSION,
        },
    }
