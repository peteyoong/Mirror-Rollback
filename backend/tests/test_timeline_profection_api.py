"""HTTP tests for /api/timeline/profection endpoints (Timeline Intelligence V2).

Uses the public backend URL from frontend/.env and MongoDB user Pete Yoong
(697f0c6abf35c0528ff06954, born 1968-04-01 01:25 Asia/Kuala_Lumpur).
"""
from __future__ import annotations

import os
import re
import pytest
import requests

# --- Resolve BASE_URL ---------------------------------------------------------
def _load_env(path: str) -> dict:
    out = {}
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip('"')
    except FileNotFoundError:
        pass
    return out

_FE_ENV = _load_env("/app/frontend/.env")
BASE_URL = (
    os.environ.get("EXPO_BACKEND_URL")
    or _FE_ENV.get("EXPO_PUBLIC_BACKEND_URL")
    or _FE_ENV.get("EXPO_PACKAGER_PROXY_URL")
    or ""
).rstrip("/")

if not BASE_URL:
    raise RuntimeError("No backend URL available (check frontend/.env)")

PETE_ID = "697f0c6abf35c0528ff06954"
TIMEOUT = 60


@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# =============================================================================
# /api/timeline/profection/current
# =============================================================================
class TestProfectionCurrent:
    def test_current_no_date(self, api):
        r = api.get(f"{BASE_URL}/api/timeline/profection/current",
                    params={"user_id": PETE_ID}, timeout=TIMEOUT)
        assert r.status_code == 200, r.text
        j = r.json()
        assert j.get("ok") is True
        p = j["profection"]
        assert 1 <= p["activated_house"] <= 12
        assert isinstance(p["profected_sign"], str) and p["profected_sign"]
        # lord may be None ONLY if Ophiuchus year
        if p["profected_sign"] != "Ophiuchus":
            assert p["lord_of_the_year"], f"lord missing for {p['profected_sign']}"
        assert p["profection_source"] == "mirror_canonical_variant_a_equal"
        # Should NOT contain mongo _id
        assert "_id" not in j and "_id" not in p

    def test_current_historical_2000_01_01(self, api):
        """Pete born 1968-04-01. On 2000-01-01 he's age 31 (birthday-year 31
        window = 1999-04-01..2000-03-31)."""
        r = api.get(f"{BASE_URL}/api/timeline/profection/current",
                    params={"user_id": PETE_ID, "date": "2000-01-01"},
                    timeout=TIMEOUT)
        assert r.status_code == 200, r.text
        j = r.json()
        assert j["computed_for"]["age"] == 31
        # Because target date falls INSIDE that year's window
        assert j["profection"]["is_current"] is True
        # 31 % 12 = 7 → 8th house
        assert j["profection"]["activated_house"] == 8

    def test_current_future_2050(self, api):
        r = api.get(f"{BASE_URL}/api/timeline/profection/current",
                    params={"user_id": PETE_ID, "date": "2050-06-01"},
                    timeout=TIMEOUT)
        assert r.status_code == 200, r.text
        j = r.json()
        # Pete age on 2050-06-01 = 82
        assert j["computed_for"]["age"] == 82
        assert 1 <= j["profection"]["activated_house"] <= 12

    def test_current_invalid_user_id_returns_400(self, api):
        r = api.get(f"{BASE_URL}/api/timeline/profection/current",
                    params={"user_id": "not-hex"}, timeout=TIMEOUT)
        assert r.status_code == 400, r.text

    def test_current_missing_user_returns_404(self, api):
        # Valid 24-hex that doesn't exist
        r = api.get(f"{BASE_URL}/api/timeline/profection/current",
                    params={"user_id": "0" * 24}, timeout=TIMEOUT)
        assert r.status_code == 404, r.text

    def test_current_invalid_date_returns_400(self, api):
        r = api.get(f"{BASE_URL}/api/timeline/profection/current",
                    params={"user_id": PETE_ID, "date": "2020-13-40"},
                    timeout=TIMEOUT)
        assert r.status_code == 400, r.text

    def test_interpretation_has_six_mirror_v2_answers(self, api):
        r = api.get(f"{BASE_URL}/api/timeline/profection/current",
                    params={"user_id": PETE_ID}, timeout=TIMEOUT)
        assert r.status_code == 200
        interp = r.json()["interpretation"]
        required = [
            "what_area_is_asking_attention",
            "experiences_that_tend_to_emerge",
            "active_developmental_question",
            "strengths_easier_this_year",
            "blind_spots_more_visible",
            "identity_synthesis_interaction",
        ]
        for k in required:
            v = interp.get(k)
            assert v and isinstance(v, str) and v.strip(), f"missing/empty {k}"

    def test_tone_contract_all_true(self, api):
        r = api.get(f"{BASE_URL}/api/timeline/profection/current",
                    params={"user_id": PETE_ID}, timeout=TIMEOUT)
        tc = r.json()["interpretation"]["tone_contract"]
        for k in ("observational_not_predictive", "no_fatalism",
                  "no_certainty_claim", "identity_first"):
            assert tc[k] is True, f"tone contract {k} != True"

    def test_timing_signals_annual_profection_wrapper(self, api):
        r = api.get(f"{BASE_URL}/api/timeline/profection/current",
                    params={"user_id": PETE_ID}, timeout=TIMEOUT)
        w = r.json()["timing_signals"]["annual_profection"]
        assert w["name"] and re.match(r"^\d+(st|nd|rd|th) House Year$", w["name"])
        assert isinstance(w["house"], int) and 1 <= w["house"] <= 12
        assert w["meaning"]
        assert w["confidence"] == "moderate"
        assert isinstance(w["supporting_signals"], list) and w["supporting_signals"]


# =============================================================================
# /api/timeline/profection/series
# =============================================================================
class TestProfectionSeries:
    def test_series_shape_and_sequence(self, api):
        r = api.get(f"{BASE_URL}/api/timeline/profection/series",
                    params={"user_id": PETE_ID, "from_age": 0, "to_age": 48},
                    timeout=TIMEOUT)
        assert r.status_code == 200, r.text
        j = r.json()
        years = j["years"]
        assert len(years) == 49
        # Sequence: each next house = (prev % 12) + 1
        for i in range(1, len(years)):
            prev_h = years[i - 1]["activated_house"]
            curr_h = years[i]["activated_house"]
            assert curr_h == (prev_h % 12) + 1, (
                f"non-sequential at index {i}: {prev_h} → {curr_h}"
            )
        # Age 0 -> H1, age 12 -> H1
        assert years[0]["activated_house"] == 1
        assert years[12]["activated_house"] == 1

    def test_series_exactly_one_is_current(self, api):
        r = api.get(f"{BASE_URL}/api/timeline/profection/series",
                    params={"user_id": PETE_ID, "from_age": 0, "to_age": 100},
                    timeout=TIMEOUT)
        assert r.status_code == 200
        years = r.json()["years"]
        current_flags = [y for y in years if y.get("is_current")]
        assert len(current_flags) == 1, (
            f"expected exactly 1 is_current entry, got {len(current_flags)}"
        )


# =============================================================================
# Regression: pre-existing endpoints must still respond
# =============================================================================
class TestRegressionExistingEndpoints:
    def test_admin_build_info(self, api):
        r = api.get(f"{BASE_URL}/api/admin/build-info", timeout=TIMEOUT)
        assert r.status_code == 200, r.text

    def test_admin_dual_house_audit(self, api):
        """Router still registered — a 403 'confirm token required' is the
        expected admin guard, proving the route hasn't been broken."""
        r = api.get(f"{BASE_URL}/api/admin/dual_house_audit",
                    params={"user_id": PETE_ID}, timeout=TIMEOUT)
        assert r.status_code in (200, 400, 403, 422), (
            f"unexpected status {r.status_code}: {r.text[:300]}"
        )
        # If 404 → the route was removed / broken by router registration.
        assert r.status_code != 404

    def test_mirror_endpoint_reachable(self, api):
        """Sanity: an /api/mirror/* endpoint still responds 200 — proves the
        router registration change did not break existing mirror routes."""
        r = api.get(f"{BASE_URL}/api/mirror/home/{PETE_ID}", timeout=TIMEOUT)
        assert r.status_code == 200, (
            f"/api/mirror/home unreachable ({r.status_code}): {r.text[:200]}"
        )
