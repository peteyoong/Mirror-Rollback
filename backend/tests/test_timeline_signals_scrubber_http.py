"""HTTP-level regression tests for WP0XX Timeline V2 · Phase 4
signals aggregator + Phase 1+2 profection endpoints against the
public preview backend.

Focus:
  - /api/timeline/signals/current returns 3 engines (profection, transits, ZR)
  - Date scrubbing (past + future) alters engine outputs coherently
  - Profection routes remain stable (Phase 1+2 regression)
"""
from __future__ import annotations

import os
from datetime import date

import pytest
import requests

BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # /app/frontend/.env uses EXPO_PUBLIC_BACKEND_URL
    raise RuntimeError("EXPO_PUBLIC_BACKEND_URL not set in env")

PETE_USER_ID = "697f0c6abf35c0528ff06954"
VALID_SIGNS_12 = {
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
}
VALID_RULERS = {"Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"}
VALID_CONFIDENCE = {"high", "moderate", "conditional", "low"}


# ─── shared session ─────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


def _get_signals(api, *, date_str: str | None = None):
    params = {"user_id": PETE_USER_ID}
    if date_str:
        params["date"] = date_str
    r = api.get(f"{BASE_URL}/api/timeline/signals/current", params=params, timeout=60)
    assert r.status_code == 200, r.text[:400]
    return r.json()


# ─── Aggregator shape (Test 1) ───────────────────────────────────────────────
class TestSignalsAggregatorShape:
    def test_engines_run_lists_three_plugins(self, api):
        body = _get_signals(api)
        engines_run = body["protocol"]["engines_run"]
        assert engines_run == [
            "annual_profection", "transits", "zodiacal_releasing"
        ], f"engines_run mismatch: {engines_run}"

    def test_all_three_signals_present(self, api):
        body = _get_signals(api)
        keys = set(body["timing_signals"].keys())
        assert {"annual_profection", "transits", "zodiacal_releasing"}.issubset(keys)

    def test_confidence_vocabulary(self, api):
        body = _get_signals(api)
        for sid, sig in body["timing_signals"].items():
            assert sig["confidence"] in VALID_CONFIDENCE, (
                f"{sid} bad confidence {sig['confidence']}")


# ─── Transits signal schema (Test 2) ─────────────────────────────────────────
class TestTransitsSignal:
    def test_shape_and_loci(self, api):
        body = _get_signals(api)
        tr = body["timing_signals"]["transits"]["details"]
        assert isinstance(tr.get("aspects_top"), list)
        loci = tr.get("loci_measured") or []
        # 4 angles must appear (Lord of the Year optional)
        assert {"Ascendant", "MC", "IC", "Descendant"}.issubset(set(loci)), \
            f"loci missing angles: {loci}"
        assert tr["target_date"] == date.today().isoformat()
        assert body["timing_signals"]["transits"]["confidence"] in {
            "high", "moderate", "low"}


# ─── ZR signal schema (Test 3) ───────────────────────────────────────────────
class TestZRSignal:
    def test_spirit_fortune_blocks_valid(self, api):
        body = _get_signals(api)
        zr = body["timing_signals"]["zodiacal_releasing"]["details"]
        for lot in ("spirit", "fortune"):
            b = zr.get(lot)
            assert b is not None, f"{lot} block missing"
            assert b["current_L1_sign"] in VALID_SIGNS_12, \
                f"{lot} L1 sign not 12-sign: {b['current_L1_sign']}"
            assert b["current_L1_ruler"] in VALID_RULERS, \
                f"{lot} ruler invalid: {b['current_L1_ruler']}"
            assert b["period_years"] > 0
            assert 0 <= b["years_remaining"] <= b["period_years"]
            assert b["period_start_date"] < b["period_end_date"]


# ─── Historical scrubbing (Test 4) ───────────────────────────────────────────
class TestHistoricalScrub:
    def test_year_2000(self, api):
        body = _get_signals(api, date_str="2000-06-01")
        ap = body["timing_signals"]["annual_profection"]["details"]
        # Pete: 1968-03-31 -> in 2000-06-01 he had just turned 32
        assert ap["age"] == 32, f"expected age 32, got {ap['age']}"

        tr = body["timing_signals"]["transits"]["details"]
        assert tr["target_date"] == "2000-06-01"

        zr = body["timing_signals"]["zodiacal_releasing"]["details"]
        # ZR should have valid period blocks in 2000 too
        for lot in ("spirit", "fortune"):
            b = zr.get(lot)
            assert b is not None
            assert b["period_start_date"] <= "2000-06-01" <= b["period_end_date"], \
                f"{lot} period {b['period_start_date']}..{b['period_end_date']} does not contain 2000-06-01"


# ─── Future scrubbing (Test 5) ───────────────────────────────────────────────
class TestFutureScrub:
    def test_2030_shifts_house_vs_now(self, api):
        now_body = _get_signals(api)
        fut_body = _get_signals(api, date_str="2030-06-01")

        now_house = now_body["timing_signals"]["annual_profection"]["details"]["activated_house"]
        fut_house = fut_body["timing_signals"]["annual_profection"]["details"]["activated_house"]
        assert now_house != fut_house, (
            f"2030 house should differ from now; got now={now_house} fut={fut_house}"
        )
        # 4 years advance = 4 houses forward (mod 12)
        expected = ((now_house - 1 + 4) % 12) + 1
        assert fut_house == expected, (
            f"expected +4 shift from house {now_house} -> {expected}, got {fut_house}"
        )


# ─── Regression on Phase 1+2 (Test 6) ────────────────────────────────────────
class TestProfectionRegression:
    def test_current_endpoint_200(self, api):
        r = api.get(
            f"{BASE_URL}/api/timeline/profection/current",
            params={"user_id": PETE_USER_ID}, timeout=45)
        assert r.status_code == 200, r.text[:400]
        j = r.json()
        assert j["ok"] is True
        assert "profection" in j and "activated_house" in j["profection"]

    def test_series_endpoint_200(self, api):
        r = api.get(
            f"{BASE_URL}/api/timeline/profection/series",
            params={"user_id": PETE_USER_ID, "from_age": 0, "to_age": 48},
            timeout=45)
        assert r.status_code == 200, r.text[:400]
        j = r.json()
        assert j["ok"] is True
        assert isinstance(j.get("years"), list) and len(j["years"]) >= 40
