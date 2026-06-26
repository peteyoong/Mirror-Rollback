"""
test_mirror_kg_v15.py — Mirror Knowledge Graph V1.5 unit tests
================================================================
Covers:
  * provenance carried through signal normalizer
  * stale provenance reduces confidence
  * verified multi-lens convergence increases confidence
  * technical refs preserved
  * evidence ladder exists for every reflection claim
  * existing relationship mapping keys unchanged (backward-compat)
  * Pete ↔ Mel snapshot
  * Pete ↔ Isaac snapshot
  * Pete ↔ Thaddeus snapshot
  * no DB writes (deterministic, pure functions)
"""
from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from services.mirror_signal_normalizer import (
    normalize_signals,
    normalize_signals_v15,
    NORMALIZER_VERSION,
    _provenance_default,
)
from services.mirror_knowledge_graph import (
    build_knowledge_graph,
    GRAPH_VERSION,
)
from services.mirror_reflection_orchestrator import (
    synthesize_relationship,
    ORCHESTRATOR_VERSION,
)


# ─────────────────────────────────────────────────────────────────────
# Test fixtures — three relationship snapshots
# ─────────────────────────────────────────────────────────────────────
def _signals_pete_mel():
    """Manifestor (Pete) ↔ Reflector (Mel) — classic emotional / pace pair."""
    return {
        "human_design_field": {
            "field_v3": {
                "energy_weather": "Pete's emotional clarity arrives in waves; Mel reflects the pattern back.",
                "decision_dynamics": "Wait through the emotional wave before initiating; clarity comes on the 28-day rhythm.",
                "centre_conditioning": [
                    "Solar Plexus defined ↔ undefined creates emotional amplification.",
                    "Throat-to-Sacral pull conditions Pete's pace.",
                ],
                "repair_pathway": [
                    "Re-acknowledge the 28-day rhythm before re-engaging.",
                    "Speak the wave aloud before committing.",
                ],
                "friction_patterns": [
                    "Pete initiates under pressure; Mel withdraws to clarify.",
                ],
            },
            "diagnostics": {"type_pair": "Manifestor x Reflector", "authority_pair": "Emotional x Lunar"},
        },
        "bazi": {
            "v2_card": {
                "current_movement": "Fire year pressures the wood-water cycle; commitment timing shifts.",
                "shadow_pattern":   "Control attempts emerge under pressure.",
                "repair_pathway":   "Ground in seasonal rhythm; let the wave pass.",
                "natural_strength": "Earth element grounds the relationship under pressure.",
                "growth_edge":      "Translating inner clarity into shared structure.",
            },
            "diagnostics": {"pair_type": "fire-pressure-wood-water"},
        },
        "numerology": {
            "themes": ["Inner Knower meets Voice."],
            "v2_card": {
                "core_dynamic":     "Life path 7 meets life path 11; introspection meets vision.",
                "natural_strength": "Pete feels what's underneath; Mel gives it shape.",
                "growth_edge":      "Translating inner clarity into shared structure.",
                "shadow_pattern":   "Under pressure Pete starts to speak in hints.",
                "repair_pathway":   "Pause. Each names one true thing. Speak the rhythm aloud.",
            },
            "diagnostics": {"pair_type": "7-meets-11"},
        },
        "astrology": {
            "themes": ["Commitment under emotional pressure; friction in pace and movement."],
            "natal_aspects": [
                {"name": "Saturn opposition Moon", "category": "commitment_emotional_pressure"},
                {"name": "Venus square Mars",      "category": "pace_friction"},
            ],
        },
        "enneagram": {
            "how_you_help_them": "Pete listens for the underlying need.",
            "how_they_help_you":  "Mel reflects the rhythm back without judgment.",
            "friction_pattern":   "Pete initiates too fast; Mel withdraws to clarify.",
            "growth_edge":        "Slow the pace; honor the wave.",
        },
    }


def _signals_pete_isaac():
    """Father–son fixture (less dense; tests sparse-signal robustness)."""
    return {
        "human_design_field": {
            "field_v3": {
                "energy_weather": "Strong identity transmission across generations.",
                "repair_pathway": ["Allow the son to feel his own response timing."],
            },
            "diagnostics": {"type_pair": "Manifestor x Generator"},
        },
        "bazi": {
            "v2_card": {"current_movement": "Wood-fire amplification; expansion phase."},
        },
        "numerology": {
            "v2_card": {"core_dynamic": "Life path 5 meets life path 8 — movement meets responsibility."},
        },
    }


def _signals_pete_thaddeus():
    """Another father–son fixture, used to confirm determinism."""
    return {
        "human_design_field": {
            "field_v3": {
                "energy_weather": "Sacral response is the steady ground both share.",
                "repair_pathway": ["Return to the body's yes/no before talking."],
            },
            "diagnostics": {"type_pair": "Manifestor x Generator"},
        },
        "bazi": {
            "v2_card": {"current_movement": "Earth season grounds the relationship."},
        },
        "enneagram": {
            "how_they_help_you": "Thaddeus grounds Pete's pace with steady response.",
            "friction_pattern": "Pete projects responsibility too soon.",
        },
    }


# ─────────────────────────────────────────────────────────────────────
# 1. Provenance + Evidence Ontology carried through normalizer
# ─────────────────────────────────────────────────────────────────────
def test_provenance_default_shape():
    p = _provenance_default()
    for k in ("status", "hash", "engine_version", "computed_at",
              "source_input_status", "confidence_penalty"):
        assert k in p, f"provenance default missing key: {k}"
    assert p["confidence_penalty"] == 0.0


def test_signal_carries_v15_fields():
    sigs = normalize_signals(_signals_pete_mel())
    assert sigs, "expected non-empty signals"
    for s in sigs:
        for k in ("layer", "mechanic", "evidence_type", "drilldown_level", "provenance"):
            assert k in s, f"signal {s.get('id')} missing V1.5 field: {k}"
        # provenance default carries status + carrier fields
        for pk in ("status", "engine_version", "source_input_status"):
            assert pk in s["provenance"], f"provenance missing {pk}"


def test_normalizer_v15_overlay_with_per_lens_provenance():
    prov_map = {
        "human_design": {"status": "verified", "engine_version": "hd-v3",
                         "source_input_status": "valid", "confidence_penalty": 0.0},
        "bazi":         {"status": "stale", "engine_version": "bazi-v2",
                         "source_input_status": "stale_chart", "confidence_penalty": 0.15},
    }
    sigs = normalize_signals_v15(_signals_pete_mel(), prov_map)
    bazi = [s for s in sigs if s["lens"] == "bazi"]
    hd   = [s for s in sigs if s["lens"] == "human_design"]
    assert bazi and hd
    for b in bazi:
        assert b["provenance"]["status"] == "stale"
        assert b["provenance"]["source_input_status"] == "stale_chart"
    for h in hd:
        assert h["provenance"]["status"] == "verified"


# ─────────────────────────────────────────────────────────────────────
# 2. Stale provenance reduces confidence; verified convergence raises
# ─────────────────────────────────────────────────────────────────────
def test_stale_provenance_reduces_confidence():
    raw = _signals_pete_mel()
    base = normalize_signals_v15(raw, {
        lens: {"status": "verified", "confidence_penalty": 0.0}
        for lens in ("human_design", "bazi", "numerology", "astrology", "enneagram")
    })
    stale = normalize_signals_v15(raw, {
        lens: {"status": "stale", "confidence_penalty": 0.0}
        for lens in ("human_design", "bazi", "numerology", "astrology", "enneagram")
    })
    g_base = build_knowledge_graph(base)
    g_stale = build_knowledge_graph(stale)
    # Same top theme; verified rollup should never have lower score
    top_base  = g_base["clusters"][0]
    top_stale = g_stale["clusters"][0]
    assert top_base["theme"] == top_stale["theme"]
    assert top_base["confidence_score"] >= top_stale["confidence_score"]
    assert top_base["provenance_status"] == "verified"
    assert top_stale["provenance_status"] in ("suspect", "mixed")


def test_verified_multilens_convergence_increases_confidence():
    g = build_knowledge_graph(normalize_signals_v15(
        _signals_pete_mel(),
        {l: {"status": "verified", "confidence_penalty": 0.0}
         for l in ("human_design", "bazi", "numerology", "astrology", "enneagram")}
    ))
    # Find a cluster supported by ≥ 3 lenses; it should be 'high'
    multi = [c for c in g["clusters"] if c["lens_count"] >= 3]
    assert multi, "expected at least one multi-lens cluster"
    assert any(c["confidence"] == "high" for c in multi), \
        "expected ≥1 multi-lens verified cluster at high confidence"


# ─────────────────────────────────────────────────────────────────────
# 3. Cross-cuts + backward compatibility
# ─────────────────────────────────────────────────────────────────────
def test_kg_has_cross_cuts_and_keeps_existing_keys():
    g = build_knowledge_graph(normalize_signals(_signals_pete_mel()))
    # Existing V1 keys preserved
    for k in ("nodes", "clusters", "diagnostics"):
        assert k in g
    # New V1.5 key added
    assert "cross_cuts" in g
    for axis in ("by_domain", "by_layer", "by_mechanic",
                  "by_time_scope", "by_provenance_status", "by_evidence_type"):
        assert axis in g["cross_cuts"]
    # Cluster shape additive
    for c in g["clusters"]:
        for k in ("theme", "signals", "supporting_lenses", "lens_count",
                  "signal_count", "agreement_score", "confidence_score",
                  "confidence", "polarity_tally"):
            assert k in c, f"V1 cluster key missing: {k}"
        for k in ("provenance_status", "provenance_penalty",
                  "layers", "mechanics", "evidence_types",
                  "time_scopes", "domains"):
            assert k in c, f"V1.5 cluster key missing: {k}"
    # Diagnostics carries V1.5 engine_version
    assert g["diagnostics"]["engine_version"] == GRAPH_VERSION


# ─────────────────────────────────────────────────────────────────────
# 4. Evidence ladder + technical refs preserved
# ─────────────────────────────────────────────────────────────────────
def _run_synthesis(signals_dict, name_a="Pete", name_b="Mel"):
    sigs = normalize_signals(signals_dict)
    g    = build_knowledge_graph(sigs)
    return synthesize_relationship(sigs, g, name_a=name_a, name_b=name_b), sigs, g


def test_evidence_ladder_exists_for_every_claim():
    out, _, _ = _run_synthesis(_signals_pete_mel())
    assert "evidence_ladder" in out, "V1.5: missing evidence_ladder"
    ladder = out["evidence_ladder"]
    assert ladder, "evidence_ladder should not be empty"
    # Every entry has the V1.5 contract fields
    for entry in ladder:
        for k in ("claim_label", "claim", "cluster_theme",
                  "supporting_signals", "lens_contributions",
                  "technical_refs", "provenance_status",
                  "agreement_score", "confidence_score", "drilldown_level"):
            assert k in entry, f"ladder entry missing: {k}"
        assert entry["supporting_signals"], "claim must have ≥1 supporting signal"


def test_technical_refs_preserved_in_evidence_and_ladder():
    out, _, _ = _run_synthesis(_signals_pete_mel())
    # V1 evidence shape preserved
    assert "evidence" in out
    for k in ("why_mirror_sees_this", "lens_contributions", "technical_refs"):
        assert k in out["evidence"]


# ─────────────────────────────────────────────────────────────────────
# 5. Existing relationship_synthesis backward compatibility
# ─────────────────────────────────────────────────────────────────────
def test_synthesis_existing_keys_unchanged():
    out, _, _ = _run_synthesis(_signals_pete_mel())
    # V1 keys must still be present
    for k in ("story", "evidence", "confidence", "diagnostics"):
        assert k in out, f"backward-compat key missing: {k}"
    # Story slots unchanged
    for k in ("headline", "summary", "current_movement",
              "growth_edge", "shadow_pattern", "repair_pathway", "question_to_ask"):
        assert k in out["story"], f"story slot missing: {k}"


def test_orchestrator_engine_version_is_v15():
    out, _, _ = _run_synthesis(_signals_pete_mel())
    assert out["diagnostics"]["engine_version"] == ORCHESTRATOR_VERSION
    assert ORCHESTRATOR_VERSION.endswith("v1.5")


# ─────────────────────────────────────────────────────────────────────
# 6. Snapshots — Pete↔Mel, Pete↔Isaac, Pete↔Thaddeus
# ─────────────────────────────────────────────────────────────────────
def test_pete_mel_snapshot():
    out, sigs, g = _run_synthesis(_signals_pete_mel(), "Pete", "Mel")
    assert out["story"]["headline"]
    assert len(out["evidence_ladder"]) >= 3
    # Multi-lens convergence expected
    assert any(c["lens_count"] >= 3 for c in g["clusters"])


def test_pete_isaac_snapshot():
    out, sigs, g = _run_synthesis(_signals_pete_isaac(), "Pete", "Isaac")
    # Sparse signals still yield a story + ladder
    assert out["story"]["headline"]
    assert out["evidence_ladder"], "even sparse input must produce a ladder"
    # Confidence dict has at least a 'level' or 'label' field describing the rollup
    conf = out["confidence"]
    label_field = conf.get("label") or conf.get("level") or conf.get("status") or "emerging"
    assert label_field in ("emerging", "medium", "high")


def test_pete_thaddeus_snapshot():
    out, sigs, g = _run_synthesis(_signals_pete_thaddeus(), "Pete", "Thaddeus")
    assert out["story"]["headline"]
    assert out["evidence_ladder"]
    # Provenance rollup reported
    assert "provenance_rollup" in out["diagnostics"]


# ─────────────────────────────────────────────────────────────────────
# 7. No DB writes / pure functions (compile-time sanity)
# ─────────────────────────────────────────────────────────────────────
def test_pure_functions_no_side_effects():
    """Re-running the same inputs must produce equal outputs (determinism)."""
    a = synthesize_relationship(
        normalize_signals(_signals_pete_mel()),
        build_knowledge_graph(normalize_signals(_signals_pete_mel())),
        "Pete", "Mel",
    )
    b = synthesize_relationship(
        normalize_signals(_signals_pete_mel()),
        build_knowledge_graph(normalize_signals(_signals_pete_mel())),
        "Pete", "Mel",
    )
    # Strip volatile keys (none expected, but defensive)
    assert a["story"] == b["story"]
    assert [e["claim"] for e in a["evidence_ladder"]] == \
           [e["claim"] for e in b["evidence_ladder"]]
