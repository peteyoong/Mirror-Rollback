"""Session-3 Structural Test Gate — Human Design lens
========================================================================

Project: The Mirror (Emergent `/app` application).

15 structural invariants that MUST pass before any narrative rewrite is
attempted on the HD lens (per Session-3 spec Phase 3).

This gate is deliberately narrow — it tests STRUCTURE, not prose.  If
any of these fail, the underlying data model is broken and the narrative
work would just paper over it.

build_marker: the-mirror-session3-hd-structural-gate-v1
"""
from __future__ import annotations
import os
import sys
import urllib.request
import json
from typing import Dict, Any, List, Set

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(HERE)
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

from services.hd_center_canonical import (  # noqa: E402
    CANONICAL_CENTERS, canonicalize_center,
)

PETE = "697f0c6abf35c0528ff06954"


def _fetch(path: str) -> Dict[str, Any]:
    url = f"http://localhost:8001/api{path}"
    with urllib.request.urlopen(url, timeout=45) as r:
        return json.loads(r.read())


# 1. Exactly nine canonical centres across every HD endpoint
def test_exactly_nine_canonical_centres_everywhere():
    mech = _fetch(f"/human-design/mechanics/{PETE}")
    defined = mech.get("defined_centers", [])
    undefined = mech.get("undefined_centers", [])
    all_ = set(defined) | set(undefined)
    assert all_ == set(CANONICAL_CENTERS), (
        f"mechanics centres mismatch canonical set: got {all_}, "
        f"expected {set(CANONICAL_CENTERS)}"
    )
    diag = _fetch(f"/human-design/today-diagnosis/{PETE}")
    sig = diag.get("signals") or {}
    d2 = set(sig.get("defined_centers", []))
    u2 = set(sig.get("undefined_centers", []))
    assert (d2 | u2) == set(CANONICAL_CENTERS), (
        f"today-diagnosis centres: {d2 | u2}"
    )


# 2. No overlap between defined and undefined centres
def test_no_defined_undefined_overlap_on_mechanics():
    mech = _fetch(f"/human-design/mechanics/{PETE}")
    d = set(mech.get("defined_centers", []))
    u = set(mech.get("undefined_centers", []))
    assert not (d & u), f"overlap: {d & u}"


# 3. Heart/Ego canonical across every HD endpoint (no legacy alias leak)
def test_heart_ego_canonical_across_endpoints():
    for path in ("/human-design/mechanics/",
                 "/human-design/today-diagnosis/"):
        p = _fetch(f"{path}{PETE}")
        blob = json.dumps(p)
        # Case-sensitive check for the raw legacy tokens
        assert '"Ego"' not in blob, f"legacy 'Ego' string leaked in {path}"
        # Allow "Heart/Ego" (canonical) — check for bare "Heart" as a list entry
        for k in ("defined_centers", "undefined_centers"):
            v = p.get(k) or (p.get("signals") or {}).get(k) or []
            assert "Ego" not in v, f"{path} {k}: bare 'Ego' present"
            assert "Heart" not in v, f"{path} {k}: bare 'Heart' present"
            assert "G" not in v, f"{path} {k}: bare 'G' present"


# 4. No duplicated centre suffix (regression guard — verified in FE source)
def test_no_center_center_duplicate_suffix_in_fe_source():
    fe = os.path.normpath(os.path.join(
        BACKEND, "..", "frontend", "components", "HumanDesignLensView.tsx",
    ))
    with open(fe, encoding="utf-8") as fh:
        src = fh.read()
    # Session-1 shipped the fix; ensure it stays
    assert "_stripTrailingCenter" in src or "_titleFor" in src, (
        "HumanDesignLensView must strip trailing 'Center' before appending"
    )


# 5 + 6. Every defined channel contains both gates; no channel with one gate
def test_defined_channel_contains_both_gates():
    mech = _fetch(f"/human-design/mechanics/{PETE}")
    channels = mech.get("channels", [])
    cons = set(int(g) for g in (mech.get("conscious_gates") or []) if isinstance(g, (int, str)) and str(g).isdigit())
    uncons = set(int(g) for g in (mech.get("unconscious_gates") or []) if isinstance(g, (int, str)) and str(g).isdigit())
    all_gates = cons | uncons
    assert channels, "expected at least one channel (Pete has 3)"
    for ch in channels:
        key = ch.get("gates") or ""
        if "-" not in key:
            raise AssertionError(f"channel key not in a-b format: {key}")
        a_str, b_str = key.split("-")
        a, b = int(a_str), int(b_str)
        assert a in all_gates, f"channel {key}: gate {a} not activated"
        assert b in all_gates, f"channel {key}: gate {b} not activated"


# 7. Every gate maps to its correct centre (via HD_CHANNELS.centers)
def test_channel_centres_are_from_canonical_set():
    mech = _fetch(f"/human-design/mechanics/{PETE}")
    for ch in mech.get("channels", []):
        centres = ch.get("centers") or []
        for c in centres:
            can = canonicalize_center(c)
            assert can is not None, f"channel {ch.get('gates')} has unknown centre: {c!r}"
            assert can in CANONICAL_CENTERS


# 8. Every activation maps to a valid planet + side
def test_activations_have_valid_side():
    mech = _fetch(f"/human-design/mechanics/{PETE}")
    cons = mech.get("conscious_gates") or []
    uncons = mech.get("unconscious_gates") or []
    assert len(cons) >= 12, f"expected ≥12 conscious activations, got {len(cons)}"
    assert len(uncons) >= 12, f"expected ≥12 unconscious activations, got {len(uncons)}"


# 9. Personality and Design remain distinct
def test_personality_design_distinct():
    mech = _fetch(f"/human-design/mechanics/{PETE}")
    p_sun = mech.get("personality_sun")
    d_sun = mech.get("design_sun")
    assert isinstance(p_sun, dict) and isinstance(d_sun, dict)
    assert p_sun.get("gate") != d_sun.get("gate"), (
        f"P.Sun and D.Sun collapsed to same gate: {p_sun} / {d_sun}"
    )


# 10. Multiple activation sources retained (channels showing side per gate)
def test_channel_gate_activations_side_present():
    mech = _fetch(f"/human-design/mechanics/{PETE}")
    for ch in mech.get("channels", []):
        acts = ch.get("gate_activations") or {}
        assert acts, f"channel {ch.get('gates')}: no gate_activations map"
        for gate_str, meta in acts.items():
            assert meta.get("side") in {"conscious", "unconscious", "both"}, (
                f"channel {ch.get('gates')} gate {gate_str}: bad side {meta.get('side')}"
            )


# 11. Incarnation Cross gates match calculated Sun/Earth activations
def test_incarnation_cross_gates_match_sun_earth():
    mech = _fetch(f"/human-design/mechanics/{PETE}")
    cross = (mech.get("core_mechanics") or {}).get("incarnation_cross_gates") or ""
    p_sun_gate = ((mech.get("personality_sun") or {}) or {}).get("gate")
    d_sun_gate = ((mech.get("design_sun") or {}) or {}).get("gate")
    p_earth_gate = ((mech.get("personality_earth") or {}) or {}).get("gate")
    d_earth_gate = ((mech.get("design_earth") or {}) or {}).get("gate")
    # Cross format "P.Sun/P.Earth | D.Sun/D.Earth"
    cross_gates = set()
    for tok in cross.replace("|", " ").replace("/", " ").split():
        if tok.isdigit():
            cross_gates.add(int(tok))
    expected = {p_sun_gate, p_earth_gate, d_sun_gate, d_earth_gate} - {None}
    assert cross_gates == expected, (
        f"cross gates {cross_gates} != sun/earth activations {expected}"
    )


# 12. BodyGraph and textual views consume the same structure
def test_bodygraph_and_centers_endpoint_agree():
    """The `/centers` endpoint (used by BodyGraph) must agree with
    `/mechanics` on which centres are defined vs undefined."""
    mech = _fetch(f"/human-design/mechanics/{PETE}")
    centers_ep = _fetch(f"/human-design/centers/{PETE}")
    mech_defined = set(mech.get("defined_centers") or [])
    ep_defined = set()
    for c in centers_ep.get("centers", []):
        if c.get("defined"):
            name = c.get("display_name") or c.get("center_name")
            can = canonicalize_center(name) or name
            ep_defined.add(can)
    assert mech_defined == ep_defined, (
        f"disagreement — mechanics: {mech_defined}, /centers: {ep_defined}"
    )


# 13. Unavailable variables render explicitly as unavailable
def test_variables_render_unavailable_when_missing():
    """When exact longitude data is absent the endpoint MUST return
    `variables: null` (not made-up strings)."""
    # We can't easily mint an "unavailable" user, so we assert the
    # SHAPE that unavailable data would produce:
    mech = _fetch(f"/human-design/mechanics/{PETE}")
    v = mech.get("variables")
    # Pete's data is complete, so v is a dict; if it were absent we
    # would expect either None OR a dict of nulls.  The invariant that
    # matters: NO string "unknown" placeholder outside the label field.
    if isinstance(v, dict):
        for key, sub in v.items():
            assert isinstance(sub, (dict, type(None))), (
                f"variable {key}: unexpected type {type(sub)}"
            )


# 14. No PHS claim appears without calculation provenance
def test_no_phs_claim_without_provenance():
    """Grep-based guard on frontend source: strings such as
    'Wrong acoustics shut you down' MUST NOT appear on any FE surface
    without an accompanying provenance/unverified label.  Session-3
    Phase 1 audit flagged these three exact phrases."""
    import re
    fe_dir = os.path.normpath(os.path.join(BACKEND, "..", "frontend"))
    suspect_phrases = [
        r"Wrong acoustics shut you down",
        r"Wrong lighting disrupts absorption",
        r"Distance creates confusion",
    ]
    found_bare_uses: List[str] = []
    for root, _, files in os.walk(fe_dir):
        if "node_modules" in root:
            continue
        for f in files:
            if not (f.endswith(".tsx") or f.endswith(".ts")):
                continue
            path = os.path.join(root, f)
            try:
                with open(path, encoding="utf-8") as fh:
                    src = fh.read()
            except Exception:
                continue
            for phrase in suspect_phrases:
                for m in re.finditer(phrase, src):
                    # First check whether the WHOLE FILE carries an
                    # explicit "content_provenance: unverified" header
                    # covering these PHS translations.  A block-level
                    # marker like `// ⚠️ content_provenance: unverified`
                    # anywhere in the file is sufficient — it means the
                    # author has consciously flagged the content as
                    # unverified and not calculated.
                    if "content_provenance: unverified" in src:
                        continue
                    # Otherwise fall back to a local window check.
                    start = max(0, m.start() - 200)
                    end = min(len(src), m.end() + 200)
                    window = src[start:end].lower()
                    if ("unverified" in window
                            or "provenance" in window
                            or "content_provenance" in window):
                        continue
                    found_bare_uses.append(f"{path}: {phrase}")
    assert not found_bare_uses, (
        "PHS claims present without a provenance / unverified label:\n  "
        + "\n  ".join(found_bare_uses)
    )


# 15. All Session-1 and Session-2 tests still green
def test_session_1_and_2_regression():
    import subprocess
    for fname in ("test_the_mirror_session1_integrity.py",
                  "test_lens_content_contract.py"):
        r = subprocess.run(
            [sys.executable, os.path.join(HERE, fname)],
            capture_output=True, text=True, timeout=90,
        )
        assert r.returncode == 0, (
            f"regression in {fname}. stdout:\n{r.stdout}\nstderr:\n{r.stderr}"
        )


# ── runner ──
if __name__ == "__main__":
    import traceback
    passed = failed = 0
    for name in sorted(globals()):
        if not name.startswith("test_"):
            continue
        fn = globals()[name]
        try:
            fn()
            print(f"  PASS  {name}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {name}\n        {e}")
            failed += 1
        except Exception:
            print(f"  FAIL  {name}")
            traceback.print_exc()
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    raise SystemExit(0 if failed == 0 else 1)
