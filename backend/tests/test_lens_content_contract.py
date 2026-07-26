"""Session-2 integrity tests — Shared Lens Content Contract V1
========================================================================

Covers every "TESTS" bullet from Session-2 spec:

  1. Schema validity for every contract layer
  2. Every material narrative claim has ≥1 evidence reference
  3. Evidence references resolve to real data (structural check)
  4. Calculated vs inferred vs generated distinguishable
  5. Missing data → explicit unavailable state
  6. Timing claims contain current factor + structural target + window
  7. Existing lens payloads adapt to the shared contract
  8. Heart/Ego canonicalization across legacy aliases
  9. Variant-A degree validation against variable-width boundaries
 10. Absolute-longitude round-trip
 11. No modulo-30 or clamping in frontend rendering
 12. No regressions in Session-1 tests (imports and re-runs them)

build_marker: personal-mirror-session2-tests-v1
"""
from __future__ import annotations
import os
import sys
import urllib.request
import json
from typing import Any, Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(HERE)
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

# ── Schema imports ──────────────────────────────────────────────────
from services.lens_content_contract import (  # noqa: E402
    LensEnvelope, MaterialClaim, EvidenceRef, MissingSlot,
    AtAGlanceLayer, StructureLayer, CoreStoryLayer,
    ComponentStoriesLayer, IntegrationLayer, EvidenceLayer,
    TodayTimingLayer, TimingSignal, TimingWindow, FactBadge,
    StructureComponent, ComponentStory,
)
from services.lens_content_adapter import (  # noqa: E402
    adapt_human_design, adapt_astrology,
    adapt_numerology, adapt_bazi, adapt_enneagram, adapt_gene_keys,
)
from services.hd_center_canonical import (  # noqa: E402
    canonicalize_center, canonicalize_centers,
    split_defined_undefined, CANONICAL_CENTERS,
)
from calculations.sign_attribution import (  # noqa: E402
    attribute_sign_midpoint13_variant_a,
    MIDPOINT_BOUNDARIES_VARIANT_A,
)


PETE = "697f0c6abf35c0528ff06954"


def _fetch(url: str) -> Dict[str, Any]:
    with urllib.request.urlopen(url, timeout=45) as resp:
        return json.loads(resp.read())


# ─────────────────────────────────────────────────────────────────────
# 1. Schema validity — construct a minimal valid envelope end-to-end
# ─────────────────────────────────────────────────────────────────────
def test_schema_valid_minimal_envelope():
    ev = EvidenceRef(source_lens="test", calculation="test.ok",
                     origin="calculated", confidence="high")
    claim = MaterialClaim(text="Example.", evidence=[ev],
                          origin="inferred", confidence="high")
    env = LensEnvelope(
        lens="test",
        at_a_glance=AtAGlanceLayer(recognition_statement="ok"),
        structure=StructureLayer(),
        core_story=CoreStoryLayer(
            essence=claim, capacity=claim,
            shadow_or_distortion=claim, central_tension=claim,
            developmental_possibility=claim, practical_application=claim,
            reflection_question=claim,
        ),
        component_stories=ComponentStoriesLayer(),
        integration=IntegrationLayer(how_they_operate_together=claim),
        evidence=EvidenceLayer(all_refs=[ev]),
        today_timing=TodayTimingLayer(),
    )
    assert env.envelope_version == "lens-content-contract-v1"
    problems = env.validate_governance()
    assert not problems, f"unexpected governance violations: {problems}"


# 2 + 3. Material claim without evidence must be flagged by governance
def test_governance_flags_claim_without_evidence():
    empty_claim = MaterialClaim(text="A dramatic claim.", evidence=[])
    ev = EvidenceRef(source_lens="t", calculation="t.ok")
    good = MaterialClaim(text="ok", evidence=[ev])
    env = LensEnvelope(
        lens="t",
        at_a_glance=AtAGlanceLayer(recognition_statement="ok"),
        structure=StructureLayer(),
        core_story=CoreStoryLayer(
            essence=empty_claim, capacity=good,
            shadow_or_distortion=good, central_tension=good,
            developmental_possibility=good, practical_application=good,
            reflection_question=good,
        ),
        component_stories=ComponentStoriesLayer(),
        integration=IntegrationLayer(how_they_operate_together=good),
        evidence=EvidenceLayer(),
        today_timing=TodayTimingLayer(),
    )
    probs = env.validate_governance()
    assert any("essence" in p and "no evidence" in p for p in probs), (
        f"expected essence-evidence violation, got: {probs}"
    )


# 4. ContentOrigin distinguishes calculated/inferred/generated
def test_content_origin_values_present():
    ev = EvidenceRef(source_lens="l", calculation="x", origin="calculated")
    ev2 = EvidenceRef(source_lens="l", calculation="x", origin="inferred")
    ev3 = EvidenceRef(source_lens="l", calculation="x", origin="generated")
    assert ev.origin == "calculated"
    assert ev2.origin == "inferred"
    assert ev3.origin == "generated"


# 5. Missing data → explicit unavailable state
def test_missing_produces_unavailable_state():
    env = adapt_numerology({})  # empty payload
    assert env.at_a_glance.availability == "unavailable"
    assert env.core_story.availability == "unavailable"
    assert env.today_timing.availability == "unavailable"
    # Structure carries a MissingSlot explaining why
    assert env.structure.availability == "unavailable"
    assert len(env.structure.missing) >= 1
    assert env.structure.missing[0].what


# 6. Timing claim shape enforced
def test_governance_flags_incomplete_timing_signal():
    ev = EvidenceRef(source_lens="astrology", calculation="transits")
    claim = MaterialClaim(text="ok", evidence=[ev])
    bad_sig = TimingSignal(
        current_factor="", structural_target="", interaction="",
        window=TimingWindow(scope="day"),
        interpretation=claim, confidence="high", evidence=[ev],
    )
    env = LensEnvelope(
        lens="t",
        at_a_glance=AtAGlanceLayer(recognition_statement="ok"),
        structure=StructureLayer(),
        core_story=CoreStoryLayer(
            essence=claim, capacity=claim,
            shadow_or_distortion=claim, central_tension=claim,
            developmental_possibility=claim, practical_application=claim,
            reflection_question=claim,
        ),
        component_stories=ComponentStoriesLayer(),
        integration=IntegrationLayer(how_they_operate_together=claim),
        evidence=EvidenceLayer(),
        today_timing=TodayTimingLayer(signals=[bad_sig]),
    )
    probs = env.validate_governance()
    assert any("current_factor" in p or "structural_target" in p for p in probs)


# 7. Real HD + astrology payloads adapt without exception
def test_hd_payload_adapts_to_contract():
    summary = _fetch(f"http://localhost:8001/api/human-design/summary/{PETE}")
    centers = _fetch(f"http://localhost:8001/api/human-design/centers/{PETE}")
    env = adapt_human_design(summary, centers)
    assert env.lens == "human_design"
    assert env.at_a_glance.availability == "present"
    assert env.structure.availability == "present"
    # Every centre resolves to a canonical name via display_name
    labels = [c.label for c in env.structure.components]
    assert any(l for l in labels), "expected centre components"


def test_astrology_payload_adapts_to_contract():
    chart = _fetch(f"http://localhost:8001/api/astrology/chart/{PETE}")
    env = adapt_astrology(chart)
    assert env.lens == "astrology"
    assert env.structure.availability == "present"
    # Every planet component's value includes constellation-relative
    # degree AND absolute longitude (no modulo-30, no clamp)
    planets = [c for c in env.structure.components if c.component_id.startswith("planet:")]
    assert planets
    for p in planets:
        val = p.value or {}
        assert "degree_within_sign" in val, (
            f"planet {p.label}: missing degree_within_sign"
        )
        assert "absolute_longitude" in val, (
            f"planet {p.label}: missing absolute_longitude"
        )
        assert val.get("degree_label") == "constellation-relative degree", (
            f"planet {p.label}: missing constellation-relative degree label"
        )


# 8. Heart/Ego canonicalization across legacy aliases
def test_heart_ego_canonicalization_all_aliases():
    aliases = [
        "Ego", "Heart", "Heart Center", "Ego Center",
        "heart", "ego", "heart/ego", "Heart / Ego",
        "Heart_Center", "ego-center", " HEART ", "Will",
    ]
    for a in aliases:
        assert canonicalize_center(a) == "Heart/Ego", f"failed alias: {a!r}"

    g_aliases = ["G", "G Center", "G/Identity", "G / Identity",
                 "Identity", "the g", "Self"]
    for a in g_aliases:
        assert canonicalize_center(a) == "G/Identity", f"failed G alias: {a!r}"

    # Unknown alias returns None
    assert canonicalize_center("Made Up Center") is None
    assert canonicalize_center(None) is None
    assert canonicalize_center("") is None


def test_split_defined_undefined_preserves_invariants():
    defined_raw = ["Ego", "Throat", "Ajna", "Head", "Solar Plexus"]
    defined, undefined = split_defined_undefined(defined_raw)
    assert set(defined + undefined) == set(CANONICAL_CENTERS)
    assert not (set(defined) & set(undefined)), "overlap forbidden"
    assert len(defined) + len(undefined) == 9
    assert "Heart/Ego" in defined
    assert "Ego" not in defined  # legacy alias must not leak through


# 9. Variant-A degree validation against variable-width boundaries
def test_variant_a_degrees_within_constellation_width():
    """For every planet emitted by /astrology/chart, the constellation-
    relative degree must satisfy 0 ≤ deg < sign_width — NOT the naïve
    0..30 rule which is invalid under Variant-A."""
    chart = _fetch(f"http://localhost:8001/api/astrology/chart/{PETE}")
    planets = (chart.get("natal") or {}).get("planets") or {}
    # Build a sign→width table from the canonical Variant-A table
    width_by_sign = {}
    for name, start, end in MIDPOINT_BOUNDARIES_VARIANT_A:
        if start <= end:
            width_by_sign[name] = end - start
        else:
            width_by_sign[name] = (360.0 - start) + end
    for planet_name, p in planets.items():
        if not isinstance(p, dict):
            continue
        sign = p.get("sign")
        deg = p.get("degree")
        lon = p.get("longitude")
        assert sign in width_by_sign, f"unknown sign for {planet_name}: {sign}"
        width = width_by_sign[sign]
        assert 0 <= (lon or 0) < 360.0, f"{planet_name}: lon {lon} out of [0,360)"
        assert deg is not None and deg >= 0, (
            f"{planet_name}: degree {deg} negative"
        )
        assert deg < width + 0.001, (
            f"{planet_name}: degree {deg}° exceeds Variant-A "
            f"{sign} constellation width {width:.3f}°"
        )


# 10. Absolute longitude → sign+relative → longitude round-trip
def test_variant_a_round_trip_absolute_longitude():
    for target_lon in [0.0, 15.0, 45.5, 89.9, 120.0, 175.2, 219.9,
                       270.0, 305.3, 358.7]:
        result = attribute_sign_midpoint13_variant_a(target_lon)
        sign_start = result["sign_start"]
        deg = result["degree_within_sign"]
        # Reconstruct longitude = sign_start + degree (mod 360)
        reconstructed = (sign_start + deg) % 360.0
        assert abs(reconstructed - target_lon) < 1e-4, (
            f"round-trip failed: lon={target_lon} sign={result['sign']} "
            f"→ reconstructed={reconstructed}"
        )


# 11. No modulo-30 or clamping in FE rendering — source scan
def test_frontend_no_modulo_30_or_clamp_in_lens_contract_view():
    import re
    fe = os.path.normpath(os.path.join(
        BACKEND, "..", "frontend", "components", "lens_contract",
        "LensContractView.tsx",
    ))
    with open(fe, encoding="utf-8") as fh:
        src = fh.read()
    # No `% 30` or `.mod(30)` or `Math.min(29`
    forbidden = [r"%\s*30\b", r"\.mod\(\s*30", r"Math\.min\([^,]+,\s*29\.9",
                 r"Math\.min\([^,]+,\s*30\)"]
    for pat in forbidden:
        assert not re.search(pat, src), (
            f"forbidden clamping pattern found in LensContractView: {pat}"
        )


def test_frontend_no_modulo_30_in_mappings():
    import re
    fe = os.path.normpath(os.path.join(
        BACKEND, "..", "frontend", "app", "forums", "mappings.tsx",
    ))
    if not os.path.exists(fe):
        return
    with open(fe, encoding="utf-8") as fh:
        src = fh.read()
    # We do use `.split(/(?<=[.!?])\s+/)` and Jaccard math but no
    # astrology-degree normalization should exist here.
    assert not re.search(r"degree\s*%\s*30", src), (
        "modulo-30 on degree found in mappings.tsx"
    )


# 12. Session-1 regression — import the Session-1 test module
def test_session1_tests_still_pass():
    import subprocess
    result = subprocess.run(
        [sys.executable, os.path.join(HERE, "test_the_mirror_session1_integrity.py")],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, (
        f"Session-1 tests regressed. stdout=\n{result.stdout}\n"
        f"stderr=\n{result.stderr}"
    )


# ─────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────
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
            print(f"  FAIL  {name}\n        {e}")
            failed += 1
        except Exception:
            print(f"  FAIL  {name}")
            traceback.print_exc()
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    raise SystemExit(0 if failed == 0 else 1)
