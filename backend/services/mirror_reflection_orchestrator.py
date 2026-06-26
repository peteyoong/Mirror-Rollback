"""mirror_reflection_orchestrator.py — Progressive-revelation synthesizer V1
=============================================================================

Build marker:  mirror-reflection-orchestrator-v1

Turns Knowledge Graph clusters into a single relationship-synthesis
story.  Every emitted line is traceable to one or more clusters; every
cluster is traceable to its source signals (and through them, back to
the lens engine output).
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional

ORCHESTRATOR_VERSION = "mirror-reflection-orchestrator-v1"

FORBIDDEN = ("destiny", "destined", "soulmate", "meant to be",
             "karmic partner", "guaranteed compatibility",
             "prediction", "fortune telling", "fortune-telling")


def _find_forbidden(text: str) -> List[str]:
    if not isinstance(text, str) or not text: return []
    lower = text.lower()
    return [t for t in FORBIDDEN if t in lower]


def _pick_cluster_by_polarity(clusters: List[Dict[str, Any]],
                              polarity: str) -> Optional[Dict[str, Any]]:
    """Return the highest-agreement cluster where the requested polarity
    is the dominant tally."""
    best = None
    best_score = -1
    for c in clusters:
        tally = c.get("polarity_tally") or {}
        if not tally.get(polarity): continue
        score = c["agreement_score"] + 0.05 * c["lens_count"] + 0.02 * tally[polarity]
        if score > best_score:
            best_score = score; best = c
    return best


def _first_summary(cluster: Dict[str, Any]) -> str:
    if not cluster: return ""
    # Pick the signal in the cluster with the highest strength × confidence.
    sigs = sorted(cluster["signals"],
                  key=lambda s: -(s.get("strength", 0.5) * s.get("confidence", 0.5)))
    return (sigs[0]["summary"] if sigs else "").strip()


def _collect_repair_lines(clusters: List[Dict[str, Any]],
                          max_lines: int = 3) -> List[str]:
    seen: set = set()
    out: List[str] = []
    for c in clusters:
        if c["theme"] != "repair" and "repair" not in (c.get("polarity_tally") or {}):
            continue
        for s in sorted(c["signals"],
                        key=lambda x: -(x.get("strength", 0.5) * x.get("confidence", 0.5))):
            if s.get("polarity") != "repair": continue
            line = s.get("summary", "").strip()
            if line and line not in seen:
                seen.add(line); out.append(line)
                if len(out) >= max_lines: return out
    return out


def _confidence_score(clusters: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not clusters:
        return {"level": "emerging", "score": 0, "reason": "No clusters produced."}
    top = clusters[0]
    high_conv = sum(1 for c in clusters if c["lens_count"] >= 3)
    mid_conv  = sum(1 for c in clusters if c["lens_count"] == 2)
    base = int(round(top["agreement_score"] * 60 + high_conv * 10 + mid_conv * 5))
    score = max(5, min(100, base))
    if high_conv >= 1 or top["lens_count"] >= 3:
        level = "high"
        reason = f"{high_conv or 1} theme(s) supported by 3+ lenses."
    elif mid_conv >= 1 or top["lens_count"] == 2:
        level = "medium"
        reason = f"{mid_conv} theme(s) supported by 2 lenses."
    else:
        level = "emerging"
        reason = "Single-lens insight; awaiting cross-lens confirmation."
    return {"level": level, "score": score, "reason": reason}


def _headline(clusters: List[Dict[str, Any]], name_a: str, name_b: str) -> str:
    if not clusters:
        return f"{name_a} and {name_b}: insufficient evidence to synthesize."
    top = clusters[0]
    theme = top["theme"].replace("_", " ").title()
    lc = top["lens_count"]
    lens_str = " + ".join(top["supporting_lenses"])
    if lc >= 3:
        return f"{theme} is the strongest signal between {name_a} and {name_b} ({lens_str} converge)."
    if lc == 2:
        return f"{theme} is the leading theme between {name_a} and {name_b} ({lens_str})."
    return f"{theme} is an emerging theme for {name_a} and {name_b} ({lens_str} only)."


def _question(top_cluster: Optional[Dict[str, Any]]) -> str:
    if not top_cluster: return ""
    theme = top_cluster.get("theme", "growth")
    Q = {
        "communication":     "Where are you each translating instead of speaking directly?",
        "pressure":          "Where does pressure get held silently instead of named?",
        "repair":            "When repair happens, who moves first — and is that sustainable?",
        "commitment":        "What have you committed to that no longer has the heart behind it?",
        "growth":            "What does this relationship ask each of you to grow into?",
        "identity":          "Whose sense of self is leading the room right now?",
        "timing":            "Whose rhythm is setting the pace — and is that intentional?",
        "emotional_clarity": "What decisions are being made before the emotional wave has settled?",
        "responsibility":    "What responsibility is being carried unevenly?",
        "belonging":         "Where do each of you feel most seen by the other?",
        "movement":          "What's moving between you that wasn't moving before?",
        "grounding":         "What needs to slow down before it can land?",
    }
    return Q.get(theme, "What does this connection make possible that nothing else does?")


def synthesize_relationship(
    signals: List[Dict[str, Any]],
    graph:   Dict[str, Any],
    name_a:  str = "You",
    name_b:  str = "them",
) -> Dict[str, Any]:
    clusters = graph.get("clusters") or []

    # Story slots — each derived from a polarity-targeted cluster pick.
    top                 = clusters[0] if clusters else None
    movement_cluster    = _pick_cluster_by_polarity(clusters, "movement") or top
    growth_cluster      = _pick_cluster_by_polarity(clusters, "growth") or top
    shadow_cluster      = _pick_cluster_by_polarity(clusters, "shadow")
    if not shadow_cluster:
        shadow_cluster = _pick_cluster_by_polarity(clusters, "friction")

    headline  = _headline(clusters, name_a, name_b)
    summary   = _first_summary(top) if top else ""

    story = {
        "headline":          headline,
        "summary":           summary,
        "current_movement":  _first_summary(movement_cluster),
        "growth_edge":       _first_summary(growth_cluster),
        "shadow_pattern":    _first_summary(shadow_cluster) if shadow_cluster else "",
        "repair_pathway":    _collect_repair_lines(clusters, 3),
        "question_to_ask":   _question(top),
    }

    # Evidence tray
    evidence_lines: List[str] = []
    lens_contributions: Dict[str, int] = {}
    technical_refs:  List[Dict[str, Any]] = []
    for c in clusters[:5]:
        for s in sorted(c["signals"],
                        key=lambda x: -(x.get("strength", 0.5) * x.get("confidence", 0.5)))[:2]:
            evidence_lines.append({
                "line":        s.get("summary"),
                "lens":        s.get("lens"),
                "source_path": s.get("source_path"),
                "signal_id":   s.get("id"),
                "theme":       s.get("theme"),
                "polarity":    s.get("polarity"),
                "strength":    s.get("strength"),
                "confidence":  s.get("confidence"),
            })
            lens_contributions[s.get("lens", "unknown")] = (
                lens_contributions.get(s.get("lens", "unknown"), 0) + 1
            )
            if s.get("technical"):
                technical_refs.append({
                    "signal_id": s.get("id"),
                    "lens":      s.get("lens"),
                    "data":      s.get("technical"),
                })

    # Forbidden language guard — defensive, since all upstream prose
    # already passes this check.  If anything slips through, surface it.
    flagged: List[str] = []
    for v in story.values():
        if isinstance(v, str):
            flagged.extend(_find_forbidden(v))
        elif isinstance(v, list):
            for item in v: flagged.extend(_find_forbidden(item))

    confidence = _confidence_score(clusters)

    return {
        "story":      story,
        "evidence": {
            "why_mirror_sees_this": evidence_lines,
            "lens_contributions":   lens_contributions,
            "technical_refs":       technical_refs,
        },
        "confidence": confidence,
        "diagnostics": {
            "strongest_cluster": (top or {}).get("theme"),
            "clusters_used":     [c["theme"] for c in clusters[:5]],
            "signal_count":      len(signals),
            "lenses_present":    (graph.get("diagnostics") or {}).get("lenses_present", []),
            "forbidden_flagged": flagged,
            "engine_version":    ORCHESTRATOR_VERSION,
        },
    }
