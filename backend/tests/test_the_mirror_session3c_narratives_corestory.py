"""test_the_mirror_session3c_narratives_corestory.py
========================================================================
Session-3c Phases 4 + 5 test gate.

- Phase 4: component narratives (centres / channels / activations /
           profile / definition / incarnation cross) are evidence-
           grounded and reference the ACTUAL chart, not generic
           boilerplate.
- Phase 5: hierarchical evidence-ranked Core Story ranks Type +
           Authority above single-channel / single-line signals.
- Governance detectors: identical-narrative + deterministic-advice-
                        without-evidence + theme-hierarchy-not-flat.

Uses the live backend at http://localhost:8001.
"""
from __future__ import annotations

import os
import re
import sys
import pytest
import requests

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8001")
PETE_ID = "697f0c6abf35c0528ff06954"


@pytest.fixture(scope="module")
def pete_mechanics():
    r = requests.get(f"{BASE_URL}/api/human-design/mechanics/{PETE_ID}", timeout=15)
    assert r.status_code == 200, r.text
    return r.json()


# =======================================================================
# Phase 4 — Component narratives
# =======================================================================
def test_component_narratives_present(pete_mechanics):
    narr = pete_mechanics.get("component_narratives")
    assert isinstance(narr, dict), narr
    assert narr.get("content_provenance") == "session3c_verified"
    for k in ("centers", "channels", "activations", "profile", "definition", "incarnation_cross"):
        assert k in narr, k


def test_centre_narratives_cover_all_nine(pete_mechanics):
    narr = pete_mechanics["component_narratives"]
    centres = {c["centre"] for c in narr["centers"]}
    assert len(centres) == 9, centres


def test_defined_centre_cites_channel_evidence(pete_mechanics):
    """A defined centre's narrative must cite the channel(s) defining it."""
    narr = pete_mechanics["component_narratives"]
    head = next(c for c in narr["centers"] if c["centre"] == "Head")
    assert head["is_defined"] is True
    text = head["text"] or ""
    assert "4-63" in text or "Logic" in text, text
    # And its evidence contains a channel entry
    ev_fields = [e.get("field") for e in head["evidence"]]
    assert "defined_channels" in ev_fields, head["evidence"]


def test_undefined_centre_has_openness_framing(pete_mechanics):
    narr = pete_mechanics["component_narratives"]
    sacral = next(c for c in narr["centers"] if c["centre"] == "Sacral")
    assert sacral["is_defined"] is False
    txt = (sacral["text"] or "").lower()
    assert "undefined" in txt or "openness" in txt or "open" in txt, sacral


def test_channel_narrative_specific_for_pete_defined_channels(pete_mechanics):
    """The three specific channels 4-63, 35-36, 37-40 must have
    Session-3c authored narratives (not the structural fallback)."""
    narr = pete_mechanics["component_narratives"]
    by_id = {ch["channel_id"]: ch for ch in narr["channels"]}
    for cid in ("4-63", "35-36", "37-40"):
        assert cid in by_id, f"missing narrative for {cid}"
        assert by_id[cid]["variant"] == "authored", by_id[cid]
        assert by_id[cid]["text"], by_id[cid]


def test_channel_narratives_are_not_identical(pete_mechanics):
    """Governance: two different channels must not share identical text."""
    narr = pete_mechanics["component_narratives"]
    texts = [ch["text"] for ch in narr["channels"] if ch.get("text")]
    assert len(texts) == len(set(texts)), "channel narratives collided"


def test_centre_narratives_defined_vs_undefined_use_different_framings(pete_mechanics):
    """A defined and undefined centre must not have identical text."""
    narr = pete_mechanics["component_narratives"]
    defined = [c["text"] for c in narr["centers"] if c["is_defined"]]
    undefined = [c["text"] for c in narr["centers"] if not c["is_defined"]]
    assert defined and undefined
    for d in defined:
        for u in undefined:
            assert d != u, f"defined and undefined share text: {d}"


def test_activations_include_p_sun_and_d_sun(pete_mechanics):
    """Pete: P.Sun gate 37 line 5, D.Sun gate 5 line 1."""
    narr = pete_mechanics["component_narratives"]
    by_key = {(a["side"], a["planet"]): a for a in narr["activations"]}
    p_sun = by_key.get(("personality", "Sun"))
    d_sun = by_key.get(("design", "Sun"))
    assert p_sun and p_sun["gate"] == 37 and p_sun["line"] == 5, p_sun
    assert d_sun and d_sun["gate"] == 5 and d_sun["line"] == 1, d_sun


def test_activations_carry_line_tone_and_evidence(pete_mechanics):
    narr = pete_mechanics["component_narratives"]
    for a in narr["activations"]:
        assert a.get("line_tone"), a
        assert a.get("evidence"), a


def test_profile_narrative_specific_for_5_1(pete_mechanics):
    narr = pete_mechanics["component_narratives"]
    prof = narr.get("profile", {})
    assert prof.get("profile") == "5/1", prof
    assert prof.get("variant") == "authored", prof
    text = (prof.get("text") or "").lower()
    assert "5" in text and "1" in text and ("line" in text or "foundation" in text), prof


def test_definition_narrative_uses_derived_topology(pete_mechanics):
    narr = pete_mechanics["component_narratives"]
    df = narr.get("definition", {})
    assert df.get("definition_type") == "Split Definition", df
    assert "components_count" in df, df


def test_incarnation_cross_cites_all_four_gates(pete_mechanics):
    narr = pete_mechanics["component_narratives"]
    cross = narr.get("incarnation_cross", {})
    themes = cross.get("activation_themes") or []
    assert len(themes) == 4, themes
    joined = " ".join(themes)
    for tag in ("P.Sun", "P.Earth", "D.Sun", "D.Earth"):
        assert tag in joined, joined


# =======================================================================
# Phase 5 — Evidence-ranked hierarchical Core Story
# =======================================================================
def test_core_story_present_and_hierarchical(pete_mechanics):
    cs = pete_mechanics.get("core_story", {})
    assert cs.get("primary"), cs
    assert isinstance(cs.get("secondary"), list), cs
    hierarchy = cs.get("hierarchy") or []
    assert len(hierarchy) >= 3, hierarchy


def test_core_story_ranks_type_above_singleton_signals(pete_mechanics):
    """Type + Strategy must rank at least as high as any single-line thread."""
    cs = pete_mechanics["core_story"]
    hierarchy = cs["hierarchy"]
    assert hierarchy[0] == "type_and_strategy", hierarchy


def test_core_story_ranks_authority_before_channels(pete_mechanics):
    cs = pete_mechanics["core_story"]
    hierarchy = cs["hierarchy"]
    if "authority" in hierarchy and "channels" in hierarchy:
        assert hierarchy.index("authority") < hierarchy.index("channels"), hierarchy


def test_core_story_scores_monotonically_decreasing(pete_mechanics):
    cs = pete_mechanics["core_story"]
    scores = [s["score"] for s in cs.get("score_table") or []]
    assert scores == sorted(scores, reverse=True), scores


def test_core_story_hierarchy_matches_score_table(pete_mechanics):
    cs = pete_mechanics["core_story"]
    ordered_ids = [s["thread_id"] for s in cs.get("score_table") or []]
    assert cs["hierarchy"] == ordered_ids, (cs["hierarchy"], ordered_ids)


def test_core_story_every_thread_has_evidence(pete_mechanics):
    cs = pete_mechanics["core_story"]
    for t in [cs.get("primary")] + (cs.get("secondary") or []):
        if t is None:
            continue
        assert t.get("evidence"), t


# =======================================================================
# Phase 6 — Governance detectors (activated)
# =======================================================================
def test_governance_no_deterministic_advice_without_evidence(pete_mechanics):
    """Any narrative block making a hard 'you should' style claim must
    carry at least one EvidenceRef. Enforced across centres + channels
    + activations + profile."""
    narr = pete_mechanics["component_narratives"]
    blocks = (
        list(narr.get("centers", []))
        + list(narr.get("channels", []))
        + list(narr.get("activations", []))
        + [narr.get("profile") or {}, narr.get("definition") or {}]
    )
    for b in blocks:
        txt = (b.get("text") or "").lower()
        if re.search(r"\byou (?:must|should|need to)\b", txt):
            assert b.get("evidence"), f"advice without evidence: {b}"


def test_governance_channel_text_never_reuses_center_text(pete_mechanics):
    narr = pete_mechanics["component_narratives"]
    centre_texts = {c["text"] for c in narr["centers"]}
    for ch in narr["channels"]:
        assert ch["text"] not in centre_texts, ch


def test_governance_no_cross_lens_terms_in_hd_narratives(pete_mechanics):
    """HD narratives must not reference astrology-only terms."""
    narr = pete_mechanics["component_narratives"]
    forbidden = ["mercury retrograde", "pluto transit", "life path", "enneagram",
                 "bazi", "gene keys"]
    joined = " ".join([
        (c.get("text") or "") for c in narr.get("centers", [])
    ] + [
        (c.get("text") or "") for c in narr.get("channels", [])
    ] + [
        (c.get("text") or "") for c in narr.get("activations", [])
    ]).lower()
    for term in forbidden:
        assert term not in joined, term


# =======================================================================
# Regression — accumulated tests from Sessions 1, 2, 3a, 3b
# =======================================================================
def test_regression_earlier_sessions_still_green():
    import subprocess
    result = subprocess.run(
        [
            "pytest",
            "tests/test_the_mirror_session1_integrity.py",
            "tests/test_lens_content_contract.py",
            "tests/test_the_mirror_session3_hd_structural.py",
            "tests/test_the_mirror_session3b_narratives.py",
            "-q", "--no-header", "-x",
        ],
        capture_output=True,
        text=True,
        cwd=_ROOT,
    )
    assert result.returncode == 0, result.stdout + "\n" + result.stderr
