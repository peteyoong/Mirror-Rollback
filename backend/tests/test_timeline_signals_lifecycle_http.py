"""Live HTTP integration tests for Timeline V2 Phase-4 signals with
LifeCycleTimingEngine + LifeMilestoneTimingEngine plug-ins for Pete.
"""
from __future__ import annotations

import os
import pytest
import requests

# Public URL used by the mobile app
BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL") \
           or "https://hd-incarnation-fix.preview.emergentagent.com"
BASE_URL = BASE_URL.rstrip("/")

PETE_ID = "697f0c6abf35c0528ff06954"


@pytest.fixture
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ---------- signals/current ----------

def test_signals_current_engines_run_has_five(api):
    r = api.get(f"{BASE_URL}/api/timeline/signals/current",
                params={"user_id": PETE_ID}, timeout=60)
    assert r.status_code == 200, r.text
    body = r.json()
    engines = body["protocol"]["engines_run"]
    assert engines == [
        "annual_profection", "transits", "zodiacal_releasing",
        "life_cycle", "life_milestones",
    ], f"engines_run mismatch: {engines}"


def test_signals_current_lifecycle_active_saturn_return(api):
    r = api.get(f"{BASE_URL}/api/timeline/signals/current",
                params={"user_id": PETE_ID}, timeout=60)
    assert r.status_code == 200, r.text
    sig = r.json()["timing_signals"]
    assert "life_cycle" in sig, "life_cycle signal missing"
    lc = sig["life_cycle"]

    # Confidence should be high when actively in a window
    assert lc["confidence"] == "high", f"confidence={lc['confidence']}"

    d = lc["details"]
    assert d["active_windows"], "active_windows should be non-empty (Saturn Return)"
    # active anchor should include saturn_return
    anchor_ids = [w["anchor_id"] for w in d["active_windows"]]
    assert "saturn_return" in anchor_ids, f"anchors={anchor_ids}"

    # verify window band is 2025-08-30 → 2028-08-29 (the 2nd Saturn Return)
    sr = next(w for w in d["active_windows"] if w["anchor_id"] == "saturn_return")
    assert sr["window_start"] == "2025-08-30", sr
    assert sr["window_end"]   == "2028-08-29", sr

    # age ~ 58
    assert 57.0 < d["age_years"] < 59.0, f"age_years={d['age_years']}"
    # next_hit populated
    assert d["next_hit"] is not None


def test_signals_current_lifecycle_scrubbed_quiet_stretch(api):
    # Scrub back to 1978-06-01 → age ~10, no anchor active but next_hit present
    r = api.get(f"{BASE_URL}/api/timeline/signals/current",
                params={"user_id": PETE_ID, "date": "1978-06-01",
                        "include_inactive": "true"}, timeout=60)
    assert r.status_code == 200, r.text
    sig = r.json()["timing_signals"]
    assert "life_cycle" in sig
    lc = sig["life_cycle"]
    # engine returns active=True always in code path, but active_windows empty
    d = lc["details"]
    assert d["active_windows"] == [], f"expected empty, got {d['active_windows']}"
    assert d["next_hit"] is not None
    assert d["next_hit"]["years_from_now"] > 0
    assert 9.0 < d["age_years"] < 11.0


def test_signals_current_life_milestones_inactive_for_pete(api):
    # Pete has no life_events recorded → engine should return inactive
    r = api.get(f"{BASE_URL}/api/timeline/signals/current",
                params={"user_id": PETE_ID, "include_inactive": "true"},
                timeout=60)
    assert r.status_code == 200, r.text
    sig = r.json()["timing_signals"]
    assert "life_milestones" in sig, "life_milestones missing (with include_inactive)"
    lm = sig["life_milestones"]
    assert lm["active"] is False, lm
    assert lm["confidence"] == "conditional"
    assert "Record" in lm["meaning"] or "record" in lm["meaning"]


def test_signals_current_backcompat_shape(api):
    r = api.get(f"{BASE_URL}/api/timeline/signals/current",
                params={"user_id": PETE_ID}, timeout=60)
    assert r.status_code == 200
    sig = r.json()["timing_signals"]
    # Three original engines still fire
    for k in ("annual_profection", "transits", "zodiacal_releasing"):
        assert k in sig, f"{k} missing"
        assert "name" in sig[k]
        assert "meaning" in sig[k]
        assert "confidence" in sig[k]
        assert "supporting_signals" in sig[k]


# ---------- profection regressions ----------

def test_profection_current_still_200(api):
    r = api.get(f"{BASE_URL}/api/timeline/profection/current",
                params={"user_id": PETE_ID}, timeout=60)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert "profection" in body
    assert 1 <= body["profection"]["activated_house"] <= 12


def test_profection_series_still_200(api):
    r = api.get(f"{BASE_URL}/api/timeline/profection/series",
                params={"user_id": PETE_ID, "from_age": 0, "to_age": 12},
                timeout=60)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert len(body["years"]) == 13
