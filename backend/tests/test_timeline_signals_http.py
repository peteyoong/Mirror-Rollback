"""HTTP tests for the Phase-4 GET /api/timeline/signals/current endpoint.

Covers the contract items from the review request:
  • 200 + shape (engines_run, timing_signals.annual_profection.*)
  • date=YYYY-MM-DD variant returns a historical profection year
  • invalid user_id → 400
  • unknown 24-hex user_id → 404
  • Phase-1+2 profection endpoints still function (regression)
"""
from __future__ import annotations
import os
import requests
import pytest

BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL",
                          "https://hd-incarnation-fix.preview.emergentagent.com").rstrip("/")
PETE = "697f0c6abf35c0528ff06954"


@pytest.fixture(scope="module")
def s():
    sess = requests.Session()
    sess.headers.update({"Content-Type": "application/json"})
    return sess


# --- Phase 4: signals/current -------------------------------------------------
def test_signals_current_today_shape(s):
    r = s.get(f"{BASE_URL}/api/timeline/signals/current",
              params={"user_id": PETE}, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["ok"] is True
    assert "annual_profection" in d["protocol"]["engines_run"]
    sig = d["timing_signals"]["annual_profection"]
    assert sig["engine_id"] == "annual_profection"
    assert sig["name"]
    assert sig["meaning"]
    assert sig["confidence"] == "moderate"
    assert isinstance(sig["supporting_signals"], list)
    assert len(sig["supporting_signals"]) > 0
    house = sig["details"]["activated_house"]
    assert 1 <= house <= 12
    tone = sig["details"]["interpretation"]["tone_contract"]
    assert tone["observational_not_predictive"] is True
    assert tone["no_fatalism"] is True
    assert tone["no_certainty_claim"] is True
    assert tone["identity_first"] is True


def test_signals_current_historical_date(s):
    r = s.get(f"{BASE_URL}/api/timeline/signals/current",
              params={"user_id": PETE, "date": "1993-08-01"}, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["computed_for"]["date"] == "1993-08-01"
    sig = d["timing_signals"]["annual_profection"]
    assert 1 <= sig["details"]["activated_house"] <= 12


def test_signals_current_invalid_user_id(s):
    r = s.get(f"{BASE_URL}/api/timeline/signals/current",
              params={"user_id": "not-a-hex"}, timeout=30)
    assert r.status_code == 400


def test_signals_current_unknown_user_id_404(s):
    r = s.get(f"{BASE_URL}/api/timeline/signals/current",
              params={"user_id": "000000000000000000000000"}, timeout=30)
    assert r.status_code == 404


def test_signals_current_bad_date_format(s):
    r = s.get(f"{BASE_URL}/api/timeline/signals/current",
              params={"user_id": PETE, "date": "bogus"}, timeout=30)
    assert r.status_code == 400


# --- Phase 1+2 regression ------------------------------------------------------
def test_profection_current_still_works(s):
    r = s.get(f"{BASE_URL}/api/timeline/profection/current",
              params={"user_id": PETE}, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["ok"] is True
    assert 1 <= d["profection"]["activated_house"] <= 12


def test_profection_series_still_works(s):
    r = s.get(f"{BASE_URL}/api/timeline/profection/series",
              params={"user_id": PETE, "from_age": 0, "to_age": 5}, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["ok"] is True
    assert len(d["years"]) == 6
