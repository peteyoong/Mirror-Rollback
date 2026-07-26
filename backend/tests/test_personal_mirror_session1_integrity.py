"""Phase-11 integrity tests — Personal Mirror Session-1 scaffold
=================================================================

Only tests for concrete Session-1 fixes ship here. The broader Phase-11
test suite (degree bounds under Variant-A, no-boilerplate similarity,
prompt/token integrity) is Session-2+ scope pending the design decisions
listed in the audit doc.

build_marker: personal-mirror-session1-tests-v1
"""
from __future__ import annotations
import os
import sys
import asyncio
from typing import Any, Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(HERE)
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

# ── FE lens count consistency ────────────────────────────────────────
def test_lens_library_count_is_dynamic_not_hardcoded():
    """The Lenses tab header must NOT hardcode 'Four perspectives' —
    once we ship the dynamic-count fix (audit §3a) the string is
    computed at render time from the actual lens list.
    """
    fe_path = os.path.join(
        BACKEND, "..", "frontend", "app", "(tabs)", "lenses.tsx",
    )
    fe_path = os.path.normpath(fe_path)
    with open(fe_path, encoding="utf-8") as fh:
        src = fh.read()
    # The literal 'Four perspectives' string must not appear anymore.
    assert "Four perspectives" not in src, (
        "lens library header must not hardcode 'Four perspectives'"
    )
    # And the dynamic build marker must be present.
    assert "lens-library-dynamic-count-v1" in src, (
        "expected dynamic-count fix build_marker in lenses.tsx"
    )


# ── HD center-name canonicalization on today-diagnosis ──────────────
def test_hd_today_diagnosis_no_center_in_both_lists():
    """Live pull from `/api/human-design/today-diagnosis/{Pete}` — the
    same centre must not appear in defined_centers AND undefined_centers
    under any name variant (Ego / Heart/Ego, G Center / G/Identity, etc.).
    audit §3c
    """
    import urllib.request
    import json
    PETE = "697f0c6abf35c0528ff06954"
    url = f"http://localhost:8001/api/human-design/today-diagnosis/{PETE}"
    with urllib.request.urlopen(url, timeout=45) as resp:
        data = json.loads(resp.read())
    sig = data.get("signals") or {}
    defined = sig.get("defined_centers") or []
    undefined = sig.get("undefined_centers") or []

    # Canonicalize both lists to a common vocabulary and diff.
    _CANON = {
        "ego": "Heart/Ego", "heart": "Heart/Ego", "heart/ego": "Heart/Ego",
        "heart / ego": "Heart/Ego",
        "g center": "G/Identity", "g": "G/Identity", "g/identity": "G/Identity",
        "g / identity": "G/Identity", "identity": "G/Identity",
    }
    def _canon(name: str) -> str:
        return _CANON.get((name or "").lower().strip(), name)

    canon_defined = {_canon(c) for c in defined}
    canon_undefined = {_canon(c) for c in undefined}
    overlap = canon_defined & canon_undefined
    assert not overlap, (
        f"centres appear in BOTH lists after canonicalization: {overlap} "
        f"(defined={defined} undefined={undefined})"
    )

    # And there should be exactly 9 centres total in the union.
    assert len(canon_defined | canon_undefined) == 9, (
        f"expected 9 canonical centres total; got "
        f"{len(canon_defined | canon_undefined)}: "
        f"{sorted(canon_defined | canon_undefined)}"
    )


# ── HD centre display name never renders "X Center Center" ─────────
def test_hd_center_titles_never_duplicate_suffix():
    """Regression guard against `HumanDesignLensView.tsx` bug where
    `${centerName} Center` produced "G Center Center" (audit §3b)."""
    import re
    fe = os.path.join(
        BACKEND, "..", "frontend", "components", "HumanDesignLensView.tsx",
    )
    fe = os.path.normpath(fe)
    with open(fe, encoding="utf-8") as fh:
        src = fh.read()

    # ANY line that literally builds a title as "${x} Center" without
    # stripping a trailing " Center" from `x` is suspicious.  Session-1
    # inlined a `_stripTrailingCenter` / `_titleFor` helper — the source
    # must reference one of them near every `Center` interpolation.
    # We codify this via a specific string check:
    assert "_stripTrailingCenter" in src or "_titleFor" in src, (
        "HumanDesignLensView.tsx must strip trailing 'Center' before "
        "appending 'Center' to a display title. Missing helper."
    )
    # And no raw ${centerName} Center pattern should remain untouched.
    bad = re.findall(r"`\$\{centerName\}\s+Center`", src)
    assert not bad, (
        f"HumanDesignLensView.tsx still contains {len(bad)} raw "
        f"`${{centerName}} Center` interpolation(s) without dedup guard"
    )


# ── Astrology angle consistency (universal — regardless of policy) ──
def test_astrology_angles_mc_ic_and_asc_dsc_opposite():
    """MC/IC and Asc/Dsc absolute longitudes must be exactly 180° apart
    (mod 360, within 0.001°).  This test is safe under BOTH tropical
    30°-per-sign AND Variant-A variable-width sidereal — because it
    only touches absolute longitudes.
    audit §3d (Phase 11 test-only; policy A/B/C not required)
    """
    import urllib.request
    import json
    PETE = "697f0c6abf35c0528ff06954"
    url = f"http://localhost:8001/api/astrology/chart/{PETE}"
    with urllib.request.urlopen(url, timeout=45) as resp:
        data = json.loads(resp.read())
    natal = data.get("natal") or {}
    angles = natal.get("angles") or {}

    def _lon(k: str) -> float:
        v = angles.get(k) or {}
        return float(v.get("longitude", 0.0))

    def _opposite(a: float, b: float) -> float:
        return abs(((a - b) % 360.0) - 180.0)

    mc_ic = _opposite(_lon("mc"), _lon("ic"))
    asc_dc = _opposite(_lon("asc"), _lon("dc"))
    assert mc_ic < 0.001, (
        f"MC/IC not opposite: |Δ − 180°| = {mc_ic}° "
        f"(mc={_lon('mc')} ic={_lon('ic')})"
    )
    assert asc_dc < 0.001, (
        f"Asc/Dc not opposite: |Δ − 180°| = {asc_dc}° "
        f"(asc={_lon('asc')} dc={_lon('dc')})"
    )


# ── Astrology degree — Option A (constellation-relative, Variant-A) ─
def test_astrology_deg_bounds_under_tropical():
    """Session-2 update: Option A is now the ratified policy — degrees
    are constellation-relative under Variant-A and may exceed 30°.

    The rigorous Variant-A degree validation lives in
    `test_lens_content_contract.py::test_variant_a_degrees_within_constellation_width`.
    This wrapper delegates so Session-1 stays green under the new policy.
    """
    from tests import test_lens_content_contract as t2  # noqa: E402
    t2.test_variant_a_degrees_within_constellation_width()


# ── Runner ──
if __name__ == "__main__":
    import traceback
    passed = failed = 0
    names = [n for n in sorted(globals()) if n.startswith("test_")]
    for name in names:
        fn = globals()[name]
        try:
            fn()
            print(f"  PASS  {name}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {name}")
            print(f"        {e}")
            failed += 1
        except Exception:
            print(f"  FAIL  {name} (unexpected exception)")
            traceback.print_exc()
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    raise SystemExit(0 if failed == 0 else 1)
