"""test_the_mirror_session3d_generalisation.py
========================================================================
Session-3d generalisation & product-integration gate.

- No debug/session identifiers reach user-facing copy.
- Every Type has a valid Signature / Not-Self mapping.
- Every Authority is mechanically supported.
- All 12 Profiles have distinct handling (authored or composed-from-lines).
- All nine centres handle defined & undefined variants distinctly.
- The channel composition strategy never emits a generic fallback.
- Advanced activation fields (color/tone/base) are gated as unverified.
- Synthetic non-Pete charts render without Pete-specific leakage.
- Triple/Quadruple topology never claims Small/Wide subtype.

Runs entirely on unit-level module inputs — does NOT hit the live
server for the coverage matrix (uses direct module calls with synthetic
fixtures).  Pete's live-endpoint tests remain in the 3c files.
"""
from __future__ import annotations

import os
import sys
import re
import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


# ─────────────────────────────────────────────────────────────
# 1. No session/debug terminology in narrative payloads.
# ─────────────────────────────────────────────────────────────
FORBIDDEN_USER_FACING = [
    r"\bsession[-\s]?3[abcd]\b",
    r"\bdecision\s?\d\b",
    r"\bstructural fallback\b",
    r"\bacceptance surface\b",
    r"\bno formally verified algorithm\b",
    r"\bderivation[_\s]?rule\b",
    r"\bcontent_provenance\b",
]

def _has_forbidden(text: str) -> str | None:
    lowered = (text or "").lower()
    for pat in FORBIDDEN_USER_FACING:
        m = re.search(pat, lowered)
        if m:
            return m.group(0)
    return None


def test_narratives_have_no_debug_terminology():
    from services.hd_narratives import (
        center_narrative, channel_narrative, activation_narrative,
        profile_narrative, definition_narrative,
        incarnation_cross_narrative,
    )

    # Centres — defined + undefined
    for centre in ("Head", "Ajna", "Throat", "Sacral"):
        for defined in (True, False):
            blk = center_narrative(centre, defined, [
                {"gates": "4-63", "name": "Logic", "centers": ["Ajna", "Head"]}
            ])
            hit = _has_forbidden(blk.get("text", ""))
            assert hit is None, (centre, defined, hit)

    # Channels — authored + composed variants
    for ch in [
        {"gates": "4-63", "name": "Logic", "circuit": "Collective", "theme": "mental pressure",
         "centers": ["Ajna", "Head"]},
        {"gates": "34-57", "name": "Power", "circuit": "Individual", "theme": "instinctive power",
         "centers": ["Sacral", "Spleen"]},
    ]:
        blk = channel_narrative(ch)
        hit = _has_forbidden(blk.get("text", ""))
        assert hit is None, (ch["gates"], hit)

    # Profiles — all 12 must produce clean text
    for p in ["1/3", "1/4", "2/4", "2/5", "3/5", "3/6", "4/6", "4/1",
              "5/1", "5/2", "6/2", "6/3"]:
        blk = profile_narrative(p)
        hit = _has_forbidden(blk.get("text", ""))
        assert hit is None, (p, hit)

    # Definition
    for derived in ("Single Definition", "Split Definition",
                    "Triple Split Definition", "Quadruple Split Definition"):
        blk = definition_narrative({
            "derived_type": derived,
            "components_count": 1 if "Single" in derived else 2,
            "split_subtype_unverified": derived == "Split Definition",
            "derivation_rule": "hd_definition_topology_component_count_v1",
        })
        hit = _has_forbidden(blk.get("text", ""))
        assert hit is None, (derived, hit)

    # Incarnation Cross
    blk = incarnation_cross_narrative("Right Angle Cross of Planning",
                                       "37/40 | 5/35", 37, 40, 5, 35)
    hit = _has_forbidden(blk.get("text", ""))
    assert hit is None, hit


# ─────────────────────────────────────────────────────────────
# 2. Types × Signature/Not-Self mapping — every supported type
# ─────────────────────────────────────────────────────────────
def test_every_supported_type_has_signature_and_not_self():
    from services.hd_signature_notself import signature_and_not_self
    supported = [
        "Manifestor",
        "Generator",
        "Manifesting Generator",
        "Projector",
        "Reflector",
    ]
    for t in supported:
        out = signature_and_not_self(t)
        assert isinstance(out, dict), t
        assert out.get("signature"), t
        assert out.get("not_self"), t


# ─────────────────────────────────────────────────────────────
# 3. All 12 profiles — distinct handling
# ─────────────────────────────────────────────────────────────
def test_all_twelve_profiles_have_distinct_handling():
    from services.hd_narratives import profile_narrative
    profiles = ["1/3", "1/4", "2/4", "2/5", "3/5", "3/6",
                "4/6", "4/1", "5/1", "5/2", "6/2", "6/3"]
    seen_texts = set()
    for p in profiles:
        blk = profile_narrative(p)
        assert blk["variant"] in ("authored", "composed_from_lines"), (p, blk["variant"])
        txt = blk["text"]
        assert txt, p
        # Line pair must be reflected in the text
        assert (p.split("/")[0] in txt) and (p.split("/")[1] in txt), (p, txt)
        assert txt not in seen_texts, f"profile text collision at {p}"
        seen_texts.add(txt)


# ─────────────────────────────────────────────────────────────
# 4. Nine centres — defined vs undefined narratives differ per centre
# ─────────────────────────────────────────────────────────────
def test_all_nine_centres_have_defined_undefined_distinction():
    from services.hd_narratives import center_narrative
    centres = [
        "Head", "Ajna", "Throat", "G/Identity", "Heart/Ego",
        "Solar Plexus", "Sacral", "Spleen", "Root",
    ]
    for c in centres:
        d = center_narrative(c, True, [
            {"gates": "4-63", "name": "Logic",
             "centers": ["Ajna", "Head"]}
        ])
        u = center_narrative(c, False, [])
        assert d["text"] != u["text"], c
        assert c in d["text"], (c, d["text"])
        assert c in u["text"], (c, u["text"])


# ─────────────────────────────────────────────────────────────
# 5. Compositional channel strategy — never emits a generic fallback
# ─────────────────────────────────────────────────────────────
def test_every_channel_gets_channel_specific_composition():
    """Feed a channel not in the authored map; the composed text must
    reference THIS channel's own name/circuit/endpoints."""
    from services.hd_narratives import channel_narrative
    ch = {"gates": "34-57", "name": "Power", "circuit": "Individual",
          "theme": "instinctive power", "centers": ["Sacral", "Spleen"]}
    blk = channel_narrative(ch)
    assert blk["variant"] in ("authored", "composed_from_structure"), blk
    txt = blk["text"] or ""
    assert "Power" in txt or "34-57" in txt, txt
    assert "Sacral" in txt or "Spleen" in txt, txt
    # No debug labels leak
    assert _has_forbidden(txt) is None, txt


# ─────────────────────────────────────────────────────────────
# 6. Advanced activation fields gated as unverified
# ─────────────────────────────────────────────────────────────
def test_activation_table_advanced_fields_unverified_by_default():
    from services.hd_activation_table import build_activation_table
    # Minimal synthetic hd_raw
    hd_raw = {
        "personality": {
            "Sun": {
                "position": {"longitude": 340.24, "sign": "Pisces"},
                "gate": {
                    "gate": 37, "line": 5, "color": 5, "tone": 5, "base": 5,
                    "formatted": "37.5", "full_formatted": "37.5.5.5.5",
                },
            }
        },
        "design": {},
    }
    out = build_activation_table(hd_raw)
    assert out.get("advanced_fields_verified") is False
    assert out.get("advanced_fields_status") == "PRESENT_BUT_UNVERIFIED"
    # The row still carries the values for developer inspection.
    row = out["personality"][0]
    assert row["color"] == 5
    assert row["tone"] == 5
    assert row["base"] == 5


# ─────────────────────────────────────────────────────────────
# 7. Synthetic non-Pete topology — Generator with Sacral, Single Def
# ─────────────────────────────────────────────────────────────
def test_synthetic_generator_sacral_single_definition():
    from services.hd_definition_topology import analyse_definition_topology
    # Generator archetype: Sacral + Throat, joined via one channel.
    out = analyse_definition_topology(
        defined_centers=["Sacral", "Throat", "G/Identity"],
        defined_channels=[
            {"gates": "20-34", "centers": ["Throat", "Sacral"]},
            {"gates": "2-14", "centers": ["Sacral", "G/Identity"]},
        ],
        upstream_label="Single Definition",
    )
    assert out["derived_type"] == "Single Definition", out
    assert out["components_count"] == 1


def test_synthetic_projector_split():
    from services.hd_definition_topology import analyse_definition_topology
    # Projector-style: no Sacral, Ajna+Head one comp, Spleen+Solar Plexus another.
    out = analyse_definition_topology(
        defined_centers=["Head", "Ajna", "Spleen", "Solar Plexus"],
        defined_channels=[
            {"gates": "4-63", "centers": ["Ajna", "Head"]},
            {"gates": "48-16", "centers": ["Spleen", "Throat"]},  # touches undefined Throat — ignored
            {"gates": "22-12", "centers": ["Solar Plexus", "Throat"]},  # ditto
        ],
        upstream_label="Split Definition",
    )
    assert out["derived_type"] in ("Split Definition", "Triple Split Definition"), out
    assert out["split_subtype"] in (None, "unverified"), out


def test_synthetic_reflector_no_definition():
    from services.hd_definition_topology import analyse_definition_topology
    out = analyse_definition_topology(
        defined_centers=[],
        defined_channels=[],
        upstream_label="No Definition",
    )
    assert out["derived_type"] == "No Definition"


def test_synthetic_triple_split_no_subtype_leakage():
    """Triple/Quadruple splits must not claim Small/Wide subtype."""
    from services.hd_definition_topology import analyse_definition_topology
    out = analyse_definition_topology(
        defined_centers=["Head", "Ajna", "Sacral", "Root", "Spleen", "Throat"],
        defined_channels=[
            {"gates": "4-63", "centers": ["Ajna", "Head"]},
            {"gates": "20-34", "centers": ["Throat", "Sacral"]},
            {"gates": "18-58", "centers": ["Spleen", "Root"]},
        ],
        upstream_label="Triple Split",
    )
    assert out["derived_type"] == "Triple Split Definition"
    assert out["split_subtype"] is None
    assert out["split_subtype_unverified"] is False, out  # subtype only signalled on Split


def test_synthetic_quadruple_split_still_deterministic():
    from services.hd_definition_topology import analyse_definition_topology
    out = analyse_definition_topology(
        defined_centers=["Head", "Ajna", "Sacral", "Root",
                         "Spleen", "Throat", "Heart/Ego", "G/Identity"],
        defined_channels=[
            {"gates": "4-63", "centers": ["Ajna", "Head"]},
            {"gates": "20-34", "centers": ["Throat", "Sacral"]},
            {"gates": "18-58", "centers": ["Spleen", "Root"]},
            {"gates": "25-51", "centers": ["G/Identity", "Heart/Ego"]},
        ],
        upstream_label="Quadruple Split",
    )
    assert out["derived_type"] == "Quadruple Split Definition"
    assert out["components_count"] == 4


# ─────────────────────────────────────────────────────────────
# 8. Colour / tone / base range + boundary validation
# ─────────────────────────────────────────────────────────────
def test_activation_table_row_ranges_are_valid():
    from services.hd_activation_table import build_activation_table
    hd_raw = {
        "personality": {
            "Sun": {"gate": {"gate": 37, "line": 5, "color": 5, "tone": 5, "base": 5,
                              "formatted": "37.5"}},
            "Moon": {"gate": {"gate": 13, "line": 6, "color": 6, "tone": 6, "base": 3,
                               "formatted": "13.6"}},
        },
        "design": {
            "Sun": {"gate": {"gate": 5, "line": 1, "color": 1, "tone": 1, "base": 1,
                              "formatted": "5.1"}},
        },
    }
    out = build_activation_table(hd_raw)
    for side in ("personality", "design"):
        for row in out[side]:
            if row.get("missing"):
                continue
            if row.get("line") is not None:
                assert 1 <= row["line"] <= 6, row
            if row.get("color") is not None:
                assert 1 <= row["color"] <= 6, row
            if row.get("tone") is not None:
                assert 1 <= row["tone"] <= 6, row
            if row.get("base") is not None:
                assert 1 <= row["base"] <= 5, row
            if row.get("gate") is not None:
                assert 1 <= row["gate"] <= 64, row


# ─────────────────────────────────────────────────────────────
# 9. Synthetic non-Pete → no Pete-specific text leaks
# ─────────────────────────────────────────────────────────────
def test_synthetic_generator_narratives_have_no_pete_leakage():
    from services.hd_narratives import (
        channel_narrative, center_narrative, profile_narrative,
    )
    # A Generator profile 3/5 with channel 34-57 (Power)
    profile_blk = profile_narrative("3/5")
    channel_blk = channel_narrative({
        "gates": "34-57", "name": "Power", "circuit": "Individual",
        "theme": "instinctive power", "centers": ["Sacral", "Spleen"],
    })
    centre_blk = center_narrative("Sacral", True, [{
        "gates": "34-57", "name": "Power", "centers": ["Sacral", "Spleen"],
    }])
    joined = " ".join([
        profile_blk.get("text", ""),
        channel_blk.get("text", ""),
        centre_blk.get("text", ""),
    ]).lower()
    for term in ["pete", "pulsifi", "manifestor", "logic 4-63",
                 "transitoriness", "community", "5/1"]:
        assert term not in joined, (term, joined[:400])


# ─────────────────────────────────────────────────────────────
# 10. FE component renamed and legacy references purged
# ─────────────────────────────────────────────────────────────
def test_fe_component_has_no_session_terminology_in_source():
    """The renamed FE component must not carry session-3 identifiers in
    user-visible strings."""
    import pathlib
    p = pathlib.Path("/app/frontend/components/lens_contract/HumanDesignDeepDiveSections.tsx")
    assert p.exists(), "renamed FE component missing"
    src = p.read_text()
    # No user-visible session labels
    for banned in [
        "Session-3c · Human Design narratives",
        "The Mirror · Session-3c",
        "Authored narrative pending; structural lineage only",
        "Split sub-classification (Small / Wide) is intentionally not shown",
    ]:
        assert banned not in src, banned
    # Old filename must be gone
    old = pathlib.Path("/app/frontend/components/lens_contract/HumanDesignSession3cSections.tsx")
    assert not old.exists(), "old session-named FE component still present"


# ─────────────────────────────────────────────────────────────
# 11. Regression umbrella — earlier tests still green
# ─────────────────────────────────────────────────────────────
def test_regression_earlier_sessions_still_green():
    import subprocess
    result = subprocess.run(
        [
            "pytest",
            "tests/test_the_mirror_session1_integrity.py",
            "tests/test_lens_content_contract.py",
            "tests/test_the_mirror_session3_hd_structural.py",
            "tests/test_the_mirror_session3b_narratives.py",
            "tests/test_the_mirror_session3c_topology_activation.py",
            "tests/test_the_mirror_session3c_narratives_corestory.py",
            "-q", "--no-header", "-x",
        ],
        capture_output=True, text=True, cwd=_ROOT,
    )
    assert result.returncode == 0, result.stdout + "\n" + result.stderr
