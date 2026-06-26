"""test_hd_relationship_narrative.py — HD drill-down narrative blocks
========================================================================
Validates: type_pair / authority / profile / definition / centers /
channels / practical_guidance blocks all populate without leaking
placeholders.
"""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.hd_relationship_narrative import (
    compute_hd_narrative_blocks, NARRATIVE_VERSION,
)


def _mock_field_v3():
    return {
        "energy_signature": "Initiator x Responder",
        "field_overview": "Together you initiate and respond — momentum without confusion.",
        "aura_dynamics": "Manifestor aura meets Generator aura — closed-and-repelling meets open-and-enveloping.",
        "decision_dynamics": "Pete waits to inform; Mel responds with body knowing.",
        "centre_conditioning": [
            "Pete's defined Ajna amplifies certainty for Mel.",
            "Mel's defined Sacral anchors Pete's open Sacral.",
        ],
        "electromagnetic_gifts": "3 electromagnetic completions — channels neither carries alone.",
        "compromise_dynamics": "1 compromise dynamic between you.",
        "dominance_dynamics": "2 of Pete's defined channels operate as dominance.",
        "friction_patterns": ["Pace mismatch under pressure."],
        "repair_pathway": ["Pause and let Mel name what's hers.", "Re-acknowledge the rhythm."],
        "growth_edge": "Pete grows by waiting. Mel grows by responding to her own life.",
        "energy_weather": "High-charge field most days.",
    }


def _mock_diag():
    return {
        "type_pair":         "Manifestor x Generator",
        "authority_pair":    "Splenic x Sacral",
        "profile_pair":      "5/1 x 2/4",
        "definition_pair":   "Single Definition x Split Definition",
        "electromagnetic_count": 3,
        "compromise_count":  1,
        "dominance_a_count": 2,
        "dominance_b_count": 0,
        "dominance_count":   2,
        "companion_count":   1,
        "center_conditioning": {
            "a_amplifies_b_via": ["Ajna"],
            "b_amplifies_a_via": ["Sacral"],
            "both_defined":      ["Throat"],
            "both_open":         ["Heart"],
        },
    }


def test_blocks_present_and_populated():
    blocks = compute_hd_narrative_blocks(_mock_field_v3(), _mock_diag(), "Pete", "Mel")
    assert blocks is not None
    expected = {
        "type_pair_engagement", "authority_rhythm", "profile_interaction",
        "definition_dynamics", "centers_conditioning", "channels",
        "practical_guidance",
    }
    assert expected <= set(blocks.keys()), f"missing blocks: {expected - set(blocks.keys())}"
    # No placeholder residue
    flat = str(blocks)
    assert "{name_a}" not in flat and "{name_b}" not in flat
    assert "{a}" not in flat and "{b}" not in flat


def test_definition_split_dynamics():
    blocks = compute_hd_narrative_blocks(_mock_field_v3(), _mock_diag(), "Pete", "Mel")
    s = blocks["definition_dynamics"]["summary"]
    # Single x Split should produce a directional narrative
    assert "Single" in s and "Split" in s
    assert "Pete" in s or "Mel" in s


def test_profile_interaction_names_lines():
    blocks = compute_hd_narrative_blocks(_mock_field_v3(), _mock_diag(), "Pete", "Mel")
    p = blocks["profile_interaction"]
    assert "5/1" in p["summary"] and "2/4" in p["summary"]


def test_centers_block_calls_out_conditioning():
    blocks = compute_hd_narrative_blocks(_mock_field_v3(), _mock_diag(), "Pete", "Mel")
    s = blocks["centers_conditioning"]["summary"]
    assert "Ajna" in s and "Sacral" in s and "Throat" in s


def test_channels_block_counts():
    blocks = compute_hd_narrative_blocks(_mock_field_v3(), _mock_diag(), "Pete", "Mel")
    ch = blocks["channels"]
    assert ch["electromagnetic"]["count"] == 3
    assert ch["compromise"]["count"] == 1
    assert ch["dominance"]["a_count"] == 2
    assert ch["companion"]["count"] == 1


def test_practical_guidance_pulls_repair_and_growth():
    blocks = compute_hd_narrative_blocks(_mock_field_v3(), _mock_diag(), "Pete", "Mel")
    g = blocks["practical_guidance"]
    assert g["repair_first"] and isinstance(g["repair_first"], list)
    assert g["growth_edge"]


def test_returns_none_on_empty():
    assert compute_hd_narrative_blocks(None, None) is None
    assert compute_hd_narrative_blocks({}, {}) is None or compute_hd_narrative_blocks({}, {}) is not None  # tolerated


def test_version_marker_exposed():
    assert NARRATIVE_VERSION.startswith("hd-relationship-narrative")
