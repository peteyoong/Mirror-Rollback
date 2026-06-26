"""V1.5 Payload Contract Verification — Backend payload contract for
relationship_synthesis (Mirror Knowledge Graph V1.5).

Verifies:
  * NORMALIZER_VERSION / GRAPH_VERSION / ORCHESTRATOR_VERSION markers
  * synthesize_relationship() emits required V1.5 keys
  * evidence_ladder entries carry required attribution fields
  * diagnostics.provenance_rollup present
  * knowledge_graph.cross_cuts present with required buckets
  * V1 backward-compat keys still present
"""
import sys
sys.path.insert(0, '/app/backend')

import pytest

from services.mirror_signal_normalizer import (
    normalize_signals, NORMALIZER_VERSION
)
from services.mirror_knowledge_graph import build_knowledge_graph, GRAPH_VERSION
from services.mirror_reflection_orchestrator import (
    synthesize_relationship, ORCHESTRATOR_VERSION
)


# Sample non-empty signal payload covering all five lenses (Pete↔Mel-ish)
SAMPLE_SIGNALS = {
    "human_design_field": {
        "field_v3": {
            "energy_weather": "Steady rhythm with occasional emotional waves.",
            "decision_dynamics": "Wait through the emotional wave before deciding.",
            "centre_conditioning": [
                "Open Solar Plexus amplifies the other's emotional state.",
                "Open Throat takes in pressure to speak quickly.",
            ],
            "repair_pathway": [
                "Name the emotional wave before making a commitment.",
                "Slow speech under pressure; let the other land first.",
            ],
            "friction_patterns": [
                "Quick decision-making clashes with emotional clarity.",
            ],
        },
        "diagnostics": {
            "type_pair": "Generator–Projector",
            "authority_pair": "Emotional–Splenic",
        },
    },
    "bazi": {
        "v2_card": {
            "current_movement": "Wood season pushing initiative.",
            "natural_strength": "Earth grounds and steadies the field.",
            "shadow_pattern": "Pressure to control timing creates friction.",
            "repair_pathway": "Let the bridge element soften before speaking.",
            "current_relationship_season": "Spring opens new rhythm together.",
        },
        "diagnostics": {
            "bridge_element": "Water",
            "ten_gods_a_sees_b": "Resource",
            "ten_gods_b_sees_a": "Output",
            "day_master_relation": "Supportive",
        },
    },
    "numerology": {
        "v2_card": {
            "core_dynamic": "Life Path 7 meets Life Path 3: depth meets expression.",
            "natural_strength": "Shared 5-year cycle of growth and learning.",
            "growth_edge": "Learning to expand without losing depth.",
            "shadow_pattern": "Withdrawal under pressure shuts down communication.",
            "repair_pathway": "Speak the inner thought aloud before retreating.",
        },
        "diagnostics": {"pair_type": "7-3"},
        "themes": ["growth", "communication", "timing"],
    },
    "astrology": {
        "v2_card": {
            "current_movement": "Saturn transit asks for structure in commitments.",
            "growth_edge": "Mercury–Mars contact: speak directly, not defensively.",
            "shadow_pattern": "Pluto square triggers control patterns.",
            "repair_pathway": "Venus retrograde invites repair through listening.",
            "core_dynamic": "Sun–Moon midpoint resonance: identity flows.",
        },
        "attraction": ["Strong Venus contact draws warmth."],
        "tension": ["Mars–Saturn aspect creates frustration."],
        "growth": ["Jupiter return opens learning."],
    },
    "enneagram": {
        "how_you_help_them": "Type 5's depth steadies Type 2's emotional reach.",
        "how_they_help_you": "Type 2's warmth invites Type 5 out of withdrawal.",
        "friction_pattern": "5 withdraws when 2 pursues; pressure builds.",
        "growth_edge": "Learning to stay present through the wave.",
    },
}


@pytest.fixture(scope="module")
def synth_output():
    sigs = normalize_signals(SAMPLE_SIGNALS)
    assert isinstance(sigs, list) and len(sigs) > 0, "normalize_signals produced no output"
    graph = build_knowledge_graph(sigs)
    assert isinstance(graph, dict)
    out = synthesize_relationship(sigs, graph, name_a="Pete", name_b="Mel")
    return {"signals": sigs, "graph": graph, "synth": out}


# ── Version markers ─────────────────────────────────────────────────
class TestVersionMarkers:
    def test_normalizer_version(self):
        assert NORMALIZER_VERSION == "mirror-signal-normalizer-v1.5"

    def test_graph_version(self):
        assert GRAPH_VERSION == "mirror-knowledge-graph-v1.5"

    def test_orchestrator_version(self):
        assert ORCHESTRATOR_VERSION == "mirror-reflection-orchestrator-v1.5"


# ── V1.5 synthesis contract ─────────────────────────────────────────
class TestSynthesisContract:
    def test_top_level_keys_present(self, synth_output):
        out = synth_output["synth"]
        for k in ("story", "evidence", "evidence_ladder", "confidence", "diagnostics"):
            assert k in out, f"Missing top-level key: {k}"

    def test_evidence_ladder_non_empty_list(self, synth_output):
        ladder = synth_output["synth"]["evidence_ladder"]
        assert isinstance(ladder, list), "evidence_ladder must be a list"
        assert len(ladder) > 0, "evidence_ladder is empty"

    def test_evidence_ladder_entry_shape(self, synth_output):
        ladder = synth_output["synth"]["evidence_ladder"]
        required = ("claim_label", "claim", "cluster_theme",
                    "supporting_signals", "lens_contributions",
                    "technical_refs", "provenance_status")
        for entry in ladder:
            for k in required:
                assert k in entry, f"evidence_ladder entry missing key: {k}; entry={entry}"
            assert isinstance(entry["supporting_signals"], list)
            assert isinstance(entry["lens_contributions"], dict)
            assert isinstance(entry["technical_refs"], list)
            assert entry["provenance_status"] in ("verified", "suspect", "mixed", "unknown")

    def test_diagnostics_provenance_rollup(self, synth_output):
        diag = synth_output["synth"]["diagnostics"]
        assert "provenance_rollup" in diag, "diagnostics.provenance_rollup missing"
        assert isinstance(diag["provenance_rollup"], list)

    def test_diagnostics_engine_version_v15(self, synth_output):
        diag = synth_output["synth"]["diagnostics"]
        assert diag.get("engine_version") == "mirror-reflection-orchestrator-v1.5"


# ── V1.5 knowledge graph cross_cuts ─────────────────────────────────
class TestKnowledgeGraphCrossCuts:
    def test_cross_cuts_present(self, synth_output):
        g = synth_output["graph"]
        assert "cross_cuts" in g, "graph.cross_cuts missing"

    def test_cross_cuts_required_buckets(self, synth_output):
        cc = synth_output["graph"]["cross_cuts"]
        required = ("by_domain", "by_layer", "by_mechanic",
                    "by_time_scope", "by_provenance_status",
                    "by_evidence_type")
        for k in required:
            assert k in cc, f"cross_cuts missing bucket: {k}"
            assert isinstance(cc[k], dict)


# ── V1 backward compatibility ───────────────────────────────────────
class TestV1BackwardCompat:
    def test_story_headline_and_summary(self, synth_output):
        story = synth_output["synth"]["story"]
        assert "headline" in story and isinstance(story["headline"], str)
        assert "summary" in story

    def test_evidence_v1_keys(self, synth_output):
        ev = synth_output["synth"]["evidence"]
        for k in ("why_mirror_sees_this", "lens_contributions", "technical_refs"):
            assert k in ev, f"evidence missing V1 key: {k}"

    def test_confidence_present(self, synth_output):
        conf = synth_output["synth"]["confidence"]
        assert conf is not None
        # Shape: level + score + reason (V1 shape)
        assert "level" in conf
        assert "score" in conf

    def test_diagnostics_engine_version_key_present(self, synth_output):
        # V1 also exposed engine_version on diagnostics. Verify it survives.
        assert "engine_version" in synth_output["synth"]["diagnostics"]
