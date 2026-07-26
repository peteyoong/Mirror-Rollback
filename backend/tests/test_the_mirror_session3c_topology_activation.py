"""test_the_mirror_session3c_topology_activation.py
========================================================================
Session-3c Decisions 3 + 4 test gate.

- Decision 3: 13-planet Personality/Design activation table is present
              and structurally sound.
- Decision 4: Definition topology is derived from the defined-centre
              graph via connected-component count. Split-subtype
              (Small/Wide) is NOT emitted; unverified flag is on.

Runs against the live backend on http://localhost:8001.
Test user: pete@pulsifi.me → 697f0c6abf35c0528ff06954.
"""
from __future__ import annotations

import os
import sys
import pytest
import requests

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8001")
PETE_ID = "697f0c6abf35c0528ff06954"

# -----------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------
@pytest.fixture(scope="module")
def pete_mechanics():
    r = requests.get(f"{BASE_URL}/api/human-design/mechanics/{PETE_ID}", timeout=15)
    assert r.status_code == 200, r.text
    return r.json()


# =======================================================================
# Decision 3 — 13-planet activation table
# =======================================================================
def test_activation_table_present(pete_mechanics):
    assert "activation_table" in pete_mechanics
    at = pete_mechanics["activation_table"]
    assert isinstance(at, dict)
    assert "personality" in at and "design" in at
    assert isinstance(at["personality"], list)
    assert isinstance(at["design"], list)


def test_activation_table_thirteen_planets_per_side(pete_mechanics):
    at = pete_mechanics["activation_table"]
    assert len(at["personality"]) == 13, "Personality side must have 13 planet rows"
    assert len(at["design"]) == 13, "Design side must have 13 planet rows"


def test_activation_table_pete_has_all_present(pete_mechanics):
    at = pete_mechanics["activation_table"]
    counts = at.get("counts") or {}
    assert counts.get("personality_present") == 13, counts
    assert counts.get("design_present") == 13, counts


def test_activation_table_p_sun_matches_incarnation_cross(pete_mechanics):
    """P.Sun in activation table == personality_sun on core."""
    at = pete_mechanics["activation_table"]
    p_sun = next(r for r in at["personality"] if r["planet"] == "Sun")
    assert p_sun["gate"] == 37, p_sun
    assert p_sun["line"] == 5, p_sun
    # sanity — full formatted has color.tone.base
    assert p_sun["full_formatted"] == "37.5.5.5.5"


def test_activation_table_d_sun_matches_incarnation_cross(pete_mechanics):
    at = pete_mechanics["activation_table"]
    d_sun = next(r for r in at["design"] if r["planet"] == "Sun")
    assert d_sun["gate"] == 5, d_sun


def test_activation_table_row_has_derivation_lineage(pete_mechanics):
    at = pete_mechanics["activation_table"]
    for row in at["personality"] + at["design"]:
        assert row.get("derivation_rule"), row
        assert row.get("source"), row
        # Missing rows must state a reason
        if row.get("missing"):
            assert row.get("missing_reason"), row


# =======================================================================
# Decision 4 — Definition topology (verified) + Small/Wide subtype UNVERIFIED
# =======================================================================
def test_definition_topology_present(pete_mechanics):
    top = pete_mechanics.get("core_mechanics", {}).get("definition_topology")
    assert isinstance(top, dict)
    assert top.get("derivation_rule"), top
    assert top.get("provenance"), top


def test_definition_topology_pete_is_split(pete_mechanics):
    top = pete_mechanics["core_mechanics"]["definition_topology"]
    assert top.get("derived_type") == "Split Definition", top


def test_definition_topology_two_components_for_pete(pete_mechanics):
    top = pete_mechanics["core_mechanics"]["definition_topology"]
    assert top.get("components_count") == 2, top
    comps = top.get("components") or []
    assert len(comps) == 2
    # Head + Ajna form one component via 4-63 (Logic)
    assert {"Head", "Ajna"} <= set(c for comp in comps for c in comp)


def test_definition_topology_matches_upstream_label(pete_mechanics):
    top = pete_mechanics["core_mechanics"]["definition_topology"]
    assert top.get("matches_upstream") is True, top


def test_split_subtype_never_shown_without_verified_algorithm(pete_mechanics):
    """Small/Wide split subtype must NOT be emitted until a formally
    verified algorithm ships with tests."""
    top = pete_mechanics["core_mechanics"]["definition_topology"]
    assert top.get("split_subtype") in (None, "unverified"), top
    if top.get("derived_type") == "Split Definition":
        assert top.get("split_subtype_unverified") is True, top
        assert top.get("split_subtype_reason") == "no_formal_algorithm_verified", top


def test_definition_narrative_never_says_small_or_wide(pete_mechanics):
    """The rendered definition narrative must never emit 'Small Split'
    or 'Wide Split' while the subtype is unverified."""
    narr = pete_mechanics.get("component_narratives", {})
    definition_block = narr.get("definition", {}) if isinstance(narr, dict) else {}
    text = (definition_block.get("text") or "") + " " + (definition_block.get("headline") or "")
    lowered = text.lower()
    assert "small split" not in lowered, definition_block
    assert "wide split" not in lowered, definition_block


# =======================================================================
# Unit tests on the topology module directly (edge cases)
# =======================================================================
def _analyse(**kw):
    from services.hd_definition_topology import analyse_definition_topology
    return analyse_definition_topology(**kw)


def test_topology_module_single_definition():
    out = _analyse(
        defined_centers=["Head", "Ajna", "Throat"],
        defined_channels=[
            {"gates": "4-63", "centers": ["Ajna", "Head"]},
            {"gates": "17-62", "centers": ["Ajna", "Throat"]},
        ],
        upstream_label="Single",
    )
    assert out["derived_type"] == "Single Definition"
    assert out["components_count"] == 1
    assert out["split_subtype_unverified"] is False


def test_topology_module_triple_split():
    out = _analyse(
        defined_centers=["Head", "Ajna", "Throat", "Sacral", "Root", "Spleen"],
        defined_channels=[
            {"gates": "4-63", "centers": ["Ajna", "Head"]},
            # Throat, Sacral, Root, Spleen all isolated OR each pair
            {"gates": "20-34", "centers": ["Throat", "Sacral"]},
            {"gates": "18-58", "centers": ["Spleen", "Root"]},
        ],
        upstream_label="Triple",
    )
    assert out["derived_type"] == "Triple Split Definition", out
    assert out["components_count"] == 3


def test_topology_module_no_definition():
    out = _analyse(
        defined_centers=[],
        defined_channels=[],
        upstream_label="No Definition",
    )
    assert out["derived_type"] == "No Definition"
    assert out["components_count"] == 0


def test_topology_module_handles_center_aliases():
    """Centres arriving as legacy aliases 'Ego' or 'G' must canonicalise."""
    out = _analyse(
        defined_centers=["Ego", "G"],
        defined_channels=[{"gates": "25-51", "centers": ["G", "Heart"]}],
        upstream_label="Single",
    )
    assert "Heart/Ego" in [c for comp in out["components"] for c in comp]
    assert "G/Identity" in [c for comp in out["components"] for c in comp]


def test_topology_module_ignores_edges_with_undefined_endpoint():
    """A channel touching an undefined centre cannot glue components."""
    out = _analyse(
        defined_centers=["Head", "Ajna"],
        defined_channels=[
            {"gates": "4-63", "centers": ["Ajna", "Head"]},
            # Bogus channel touching an undefined centre
            {"gates": "17-62", "centers": ["Ajna", "Throat"]},
        ],
        upstream_label="Single",
    )
    # Should be single — the throat edge is ignored
    assert out["derived_type"] == "Single Definition"
    assert out["components_count"] == 1
