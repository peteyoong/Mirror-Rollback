"""Member Summary — Ascendant 5-fallback resolution + chart-version stamp.

Regression suite for the **P0 Mel Ascendant Regression** fix.

Build marker:    mel-rising-fix-member-summary-v1
Sister fix:      `services/forum_lens_helpers` astrology-lens-summary-rising-fix-v1

These tests lock in three guarantees for `services.member_summary`:

1.  A Mel-style chart with `astro.angles.asc.sign = "Cancer"` MUST surface
    as `"Cancer Rising"` in the member-summary string (this is the user-
    facing assertion: `"Gemini Sun · Scorpio Moon · Cancer Rising"`).

2.  A chart that has a correct `astro.angles.asc.longitude` (~89.10°) but
    a MISSING / STALE `astro.angles.asc.sign` MUST still derive
    `"Cancer Rising"` via `calculations.astrology.longitude_to_sign_degree`.
    Before this fix, that surface dropped the Rising row silently.

3.  `_compute_chart_version` produces a stable token that CHANGES whenever
    the underlying chart is recomputed/rewritten (engine version bump,
    timestamp bump, or chart `_id` change). The frontend uses this token
    as a cache-bust key so a stale payload can never survive a chart
    correction.

Run from /app/backend:
    pytest -xvs tests/test_member_summary_rising_resolution.py
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

# Make `services.*` importable when running from /app/backend.
BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from services.member_summary import (  # noqa: E402
    _compute_chart_version,
    _format_astrology,
)


# ---------------------------------------------------------------------------
# Canonical Mel chart fixture — matches the persisted shape we verified in
# local Mongo for `697ec826ad4b18f75bf42616` and `69c90702497688b97a8e67a1`.
# Cancer Ascendant 3.06°, sidereal longitude 89.103°.
# ---------------------------------------------------------------------------

MEL_CANCER_ASC_DEG = 3.062223
MEL_CANCER_ASC_LON = 89.10342319395835
MEL_CANCER_ASC_TROP_LON = 120.39  # informational only


def _mel_chart_full() -> dict:
    """Mel-style chart with the canonical engine output fully populated."""
    return {
        "_id": "fake-chart-id-aaaa",
        "user_id": "697ec826ad4b18f75bf42616",
        "chart_updated_at": datetime(2026, 6, 11, 17, 28, 30, tzinfo=timezone.utc),
        "astrology": {
            "metadata": {
                "computation_version": "mirror-deterministic-v1",
                "astrology_engine_version": "midpoint13_variant_a_v1",
                "sidereal_mode": "true_sidereal_user_defined",
                "house_system": "Equal",
                "svp_degrees": 31.2836,
                "input_datetime_utc": "1981-07-12T23:55:00+00:00",
                "coordinates": {"lat": 2.1896, "lon": 102.2501},
            },
            "planets": {
                "Sun":  {"sign": "Gemini",  "longitude": 79.489, "degree": 22.9},
                "Moon": {"sign": "Scorpio", "longitude": 212.126, "degree": 1.9},
            },
            "angles": {
                "asc": {
                    "sign": "Cancer",
                    "degree": MEL_CANCER_ASC_DEG,
                    "longitude": MEL_CANCER_ASC_LON,
                    "formatted": "3°Cancer",
                },
            },
            "houses": {
                "ascendant": MEL_CANCER_ASC_LON,
                "ascendant_sign": None,
            },
        },
    }


def _mel_chart_missing_asc_sign() -> dict:
    """Same chart but with the `asc.sign` token stripped — only the
    longitude remains. Exercises fallback step #4 (longitude derivation)."""
    chart = _mel_chart_full()
    chart["astrology"]["angles"]["asc"].pop("sign", None)
    return chart


def _mel_chart_legacy_houses_only() -> dict:
    """Legacy chart where only `houses.ascendant_sign` and `houses.ascendant`
    are populated; `angles.asc` is empty. Exercises fallback steps #3/#5."""
    chart = _mel_chart_full()
    chart["astrology"]["angles"] = {"asc": {}}
    chart["astrology"]["houses"] = {
        "ascendant": MEL_CANCER_ASC_LON,
        "ascendant_sign": "Cancer",
    }
    return chart


def _mel_chart_only_legacy_float() -> dict:
    """Legacy chart with ONLY `houses.ascendant` (float) — no signs anywhere.
    Exercises fallback step #5 chained into the longitude derivation."""
    chart = _mel_chart_full()
    chart["astrology"]["angles"] = {}
    chart["astrology"]["houses"] = {
        "ascendant": MEL_CANCER_ASC_LON,
        "ascendant_sign": None,
    }
    return chart


# =============================================================================
# 1.  HAPPY PATH — canonical Mel chart MUST render Cancer Rising
# =============================================================================

def test_mel_canonical_chart_renders_cancer_rising():
    """User-facing assertion: the member-summary card MUST surface
    `'Gemini Sun · Scorpio Moon · Cancer Rising'` for Mel's canonical
    chart. This is the headline acceptance criterion of the P0 fix."""
    out = _format_astrology(_mel_chart_full())
    assert out == "Gemini Sun · Scorpio Moon · Cancer Rising", (
        f"Mel's canonical chart must render Cancer Rising. Got: {out!r}"
    )


def test_planet_sign_lookup_is_case_insensitive():
    """Lowercase planet keys ('sun', 'moon') must work — covers legacy
    chart documents where the engine wrote lowercase names."""
    chart = _mel_chart_full()
    chart["astrology"]["planets"] = {
        "sun":  {"sign": "Gemini"},
        "moon": {"sign": "Scorpio"},
    }
    out = _format_astrology(chart)
    assert "Gemini Sun" in out
    assert "Scorpio Moon" in out


# =============================================================================
# 2.  FALLBACK — missing asc.sign but longitude present → derive Cancer
# =============================================================================

def test_missing_asc_sign_derives_cancer_from_longitude():
    """If `astro.angles.asc.sign` is missing/stale but the longitude is
    correct (~89.10° sidereal), the resolver MUST derive Cancer Rising
    rather than silently dropping the row. This is the exact failure
    mode that masked the Mel chart pre-fix."""
    out = _format_astrology(_mel_chart_missing_asc_sign())
    assert out is not None and "Cancer Rising" in out, (
        f"Longitude-derived fallback must yield 'Cancer Rising'. Got: {out!r}"
    )


def test_legacy_houses_ascendant_sign_is_honoured():
    """If only the legacy `houses.ascendant_sign` is set (no
    `angles.asc.sign`), the resolver MUST pick that up at fallback #3."""
    out = _format_astrology(_mel_chart_legacy_houses_only())
    assert out is not None and "Cancer Rising" in out


def test_legacy_houses_ascendant_float_derives_via_longitude():
    """Pre-Variant-A charts that only have `houses.ascendant` as a float
    (no sign string anywhere) MUST still resolve to Cancer Rising via
    fallback step #5 + longitude derivation."""
    out = _format_astrology(_mel_chart_only_legacy_float())
    assert out is not None and "Cancer Rising" in out


# =============================================================================
# 3.  NEGATIVE / GRACEFUL — bad inputs MUST NOT crash and MUST NOT lie
# =============================================================================

def test_empty_chart_returns_none():
    assert _format_astrology({}) is None
    assert _format_astrology({"astrology": {}}) is None
    assert _format_astrology({"astrology": {"planets": {}, "angles": {}}}) is None


def test_no_rising_data_omits_rising_token():
    """If absolutely no Rising signal can be resolved, the row MUST be
    rendered without a Rising token — never with a wrong one."""
    chart = _mel_chart_full()
    chart["astrology"]["angles"] = {}
    chart["astrology"]["houses"] = {}
    out = _format_astrology(chart)
    assert out == "Gemini Sun · Scorpio Moon"


def test_rising_is_never_substituted_with_sun_sign():
    """Defence in depth: even if every Rising field is empty, the
    resolver MUST NOT fall back to the Sun sign as 'Rising'. This is the
    exact substitution the live regression presented (Sun=Gemini being
    shown as 'Gemini Rising')."""
    chart = _mel_chart_full()
    chart["astrology"]["angles"] = {}
    chart["astrology"]["houses"] = {}
    out = _format_astrology(chart) or ""
    assert "Rising" not in out, (
        "Resolver leaked a Rising token without a real source. "
        "This is exactly the failure mode the fix exists to prevent."
    )


# =============================================================================
# 4.  CHART VERSION — the cache-bust token MUST change on any chart change
# =============================================================================

def test_chart_version_is_stable_for_identical_input():
    chart = _mel_chart_full()
    v1 = _compute_chart_version(chart)
    v2 = _compute_chart_version(chart)
    assert v1 == v2
    assert v1.startswith("v:mirror-deterministic-v1"), (
        f"Token must surface the engine version in its prefix; got {v1!r}"
    )


def test_chart_version_changes_when_timestamp_changes():
    """A recompute that touches `chart_updated_at` MUST produce a new
    token — this is what forces the frontend cache to invalidate."""
    base = _mel_chart_full()
    v_old = _compute_chart_version(base)

    bumped = _mel_chart_full()
    bumped["chart_updated_at"] = datetime(2026, 6, 16, 12, 0, 0, tzinfo=timezone.utc)
    v_new = _compute_chart_version(bumped)

    assert v_old != v_new, (
        f"chart_updated_at change MUST produce a different chart_version. "
        f"old={v_old!r} new={v_new!r}"
    )


def test_chart_version_changes_when_engine_version_changes():
    base = _mel_chart_full()
    v_old = _compute_chart_version(base)

    bumped = _mel_chart_full()
    bumped["astrology"]["metadata"]["computation_version"] = (
        "mirror-deterministic-v2"
    )
    v_new = _compute_chart_version(bumped)

    assert v_old != v_new


def test_chart_version_changes_when_chart_id_changes():
    base = _mel_chart_full()
    v_old = _compute_chart_version(base)

    bumped = _mel_chart_full()
    bumped["_id"] = "fake-chart-id-bbbb"
    v_new = _compute_chart_version(bumped)

    assert v_old != v_new


def test_chart_version_changes_when_asc_longitude_changes():
    """mel-rising-fix-content-hash-v1 contract: chart_version MUST change
    when the user-visible astrology content changes — even if no chart
    envelope timestamp was bumped. This is the exact regression seen
    after `/api/admin/fix_mel_live` $set the astrology subtree without
    touching `chart.updated_at`."""
    base = _mel_chart_full()
    v_old = _compute_chart_version(base)

    bumped = _mel_chart_full()
    # Simulate the fix_mel_live $set: only astrology.angles.asc changed,
    # NO timestamp / NO engine version / NO _id change.
    bumped["astrology"]["angles"]["asc"] = {
        "sign": "Gemini",
        "degree": 25.41,
        "longitude": 81.99527,
        "formatted": "25°Gemini",
    }
    v_new = _compute_chart_version(bumped)

    assert v_old != v_new, (
        "chart_version must flip when astrology content changes even if "
        "the chart envelope's updated_at field is untouched. "
        f"old={v_old!r} new={v_new!r}"
    )


def test_chart_version_changes_when_sun_or_moon_longitude_changes():
    """Defence-in-depth — same contract for Sun/Moon longitudes (in case
    of any future planetary-only chart update)."""
    base = _mel_chart_full()
    v_old = _compute_chart_version(base)

    bumped = _mel_chart_full()
    bumped["astrology"]["planets"]["Sun"]["longitude"] = 100.0
    v_new = _compute_chart_version(bumped)
    assert v_old != v_new

    bumped2 = _mel_chart_full()
    bumped2["astrology"]["planets"]["Moon"]["longitude"] = 250.0
    v_new2 = _compute_chart_version(bumped2)
    assert v_old != v_new2


def test_chart_version_is_deterministic_string():
    """The token must be a non-empty string (no None, no objects) so the
    frontend can safely compare with `!==`."""
    v = _compute_chart_version(_mel_chart_full())
    assert isinstance(v, str) and len(v) > 0
    # Must include the integrity hash suffix.
    assert "|h:" in v


def test_chart_version_handles_empty_chart_gracefully():
    """Defensive: a missing chart must still produce a string token (so
    the client cache key generation cannot crash)."""
    assert _compute_chart_version({}) == "v:none"
    assert isinstance(_compute_chart_version(None), str)  # type: ignore[arg-type]


# =============================================================================
# 5.  EXISTING ROWS — non-astrology rows MUST be unaffected by this fix
# =============================================================================

def test_existing_summary_fields_unchanged_for_canonical_chart():
    """Smoke-check that this fix does not perturb HD / BaZi / Enneagram /
    Numerology rendering — those formatters are out of scope and must
    continue returning the same shape."""
    from services.member_summary import (
        _format_hd,
        _format_enneagram,
        _format_numerology,
    )

    chart = _mel_chart_full()
    chart["human_design"] = {
        "type": "Generator",
        "authority": "Sacral",
        "profile": "1/3",
    }
    chart["numerology"] = {"life_path": 11}

    user = {"enneagram_type": 4, "enneagram_wing": 5}

    assert _format_hd(chart) == "Generator · Sacral Authority · 1/3"
    assert _format_enneagram(user) == "4w5"
    assert _format_numerology(chart) == "11/2"
