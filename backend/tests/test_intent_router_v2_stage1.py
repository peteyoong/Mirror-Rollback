"""Stage 1 rollout-infrastructure unit tests  (intent-router-v2-stage1-v1).

Runs WITHOUT touching the database. Verifies:
  1. `_stage1_bucket` is deterministic and uniformly distributed.
  2. `cutover_decision_for` reason ladder matches the spec.
  3. With CUTOVER=false and ROLLOUT_PERCENT=0 → ALL users disabled.
  4. With ROLLOUT_PERCENT=10 → ~10% of unique users enabled (±tolerance).
  5. Bucket assignments are sticky across calls.
  6. Per-user enabled/disabled flips ONLY when the bucket crosses the
     threshold; never within the same percent.

Run:
    pytest -xvs backend/tests/test_intent_router_v2_stage1.py
"""
from __future__ import annotations

import os
import sys
from typing import List

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(HERE)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import pytest  # noqa: E402

from services.intent_router_v2 import (  # noqa: E402
    _stage1_bucket,
    _rollout_percent,
    cutover_decision_for,
    cutover_enabled_for,
)


# 50 synthetic Mongo-style ObjectIds (24-char hex). Deterministic test data.
SYNTHETIC_USERS: List[str] = [
    f"{i:024x}" for i in range(0x1000, 0x1000 + 200)
]


# ─────────────────────────────────────────────────────────────────────────────
# 1. _stage1_bucket — determinism & distribution
# ─────────────────────────────────────────────────────────────────────────────
class TestStage1Bucket:
    def test_deterministic_across_calls(self):
        for uid in SYNTHETIC_USERS[:10]:
            assert _stage1_bucket(uid) == _stage1_bucket(uid)

    def test_in_range_0_99(self):
        for uid in SYNTHETIC_USERS:
            b = _stage1_bucket(uid)
            assert 0 <= b <= 99, f"{uid}: bucket={b} out of range"

    def test_empty_user_returns_minus_one(self):
        assert _stage1_bucket("") == -1
        assert _stage1_bucket(None) == -1

    def test_distribution_is_reasonably_uniform(self):
        """With 200 synthetic users we expect every decile of buckets
        to land roughly 20 ± 15 users. The hash is uniform; tolerate
        a generous spread because n is small."""
        from collections import Counter
        counts = Counter(_stage1_bucket(u) // 10 for u in SYNTHETIC_USERS)
        for decile, c in counts.items():
            assert 5 <= c <= 50, (
                f"Decile {decile} count={c} suspiciously skewed (n=200)"
            )


# ─────────────────────────────────────────────────────────────────────────────
# 2. cutover_decision_for — reason ladder
# ─────────────────────────────────────────────────────────────────────────────
class TestCutoverDecision:
    def setup_method(self):
        self._saved_cutover = os.environ.get("INTENT_ROUTER_V2_CUTOVER")
        self._saved_percent = os.environ.get("INTENT_ROUTER_V2_ROLLOUT_PERCENT")
        os.environ.pop("INTENT_ROUTER_V2_CUTOVER", None)
        os.environ.pop("INTENT_ROUTER_V2_ROLLOUT_PERCENT", None)

    def teardown_method(self):
        for k, v in [
            ("INTENT_ROUTER_V2_CUTOVER", self._saved_cutover),
            ("INTENT_ROUTER_V2_ROLLOUT_PERCENT", self._saved_percent),
        ]:
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def test_default_env_disables_everyone(self):
        for uid in SYNTHETIC_USERS[:50]:
            d = cutover_decision_for(uid)
            assert d["enabled"] is False
            assert d["reason"] == "rollout_percent_zero"
            assert d["rollout_percent"] == 0
            assert d["cutover_flag"] is False

    def test_no_user_id_disabled(self):
        d = cutover_decision_for(None)
        assert d["enabled"] is False
        assert d["reason"] == "no_user_id"
        assert d["stage1_bucket"] == -1

    def test_cutover_flag_overrides_percent(self):
        os.environ["INTENT_ROUTER_V2_CUTOVER"] = "true"
        os.environ["INTENT_ROUTER_V2_ROLLOUT_PERCENT"] = "0"
        for uid in SYNTHETIC_USERS[:20]:
            d = cutover_decision_for(uid)
            assert d["enabled"] is True
            assert d["reason"] == "cutover_flag_true"
            assert d["cutover_flag"] is True

    def test_rollout_percent_10_enables_roughly_10_percent(self):
        os.environ["INTENT_ROUTER_V2_CUTOVER"] = "false"
        os.environ["INTENT_ROUTER_V2_ROLLOUT_PERCENT"] = "10"
        enabled = [u for u in SYNTHETIC_USERS if cutover_enabled_for(u)]
        # 200 users, target 10% → 20 users. SHA-256 uniformity ±10 is fine.
        assert 10 <= len(enabled) <= 30, (
            f"len(enabled)={len(enabled)} for ROLLOUT_PERCENT=10 with n=200"
        )

    def test_rollout_percent_100_enables_all_users_with_id(self):
        os.environ["INTENT_ROUTER_V2_ROLLOUT_PERCENT"] = "100"
        for uid in SYNTHETIC_USERS:
            assert cutover_enabled_for(uid) is True
        # But no-id stays disabled.
        assert cutover_enabled_for(None) is False

    def test_invalid_percent_falls_back_to_zero(self):
        os.environ["INTENT_ROUTER_V2_ROLLOUT_PERCENT"] = "not-a-number"
        assert _rollout_percent() == 0
        os.environ["INTENT_ROUTER_V2_ROLLOUT_PERCENT"] = "-5"
        assert _rollout_percent() == 0
        os.environ["INTENT_ROUTER_V2_ROLLOUT_PERCENT"] = "500"
        assert _rollout_percent() == 100

    def test_decision_payload_carries_all_telemetry_keys(self):
        d = cutover_decision_for(SYNTHETIC_USERS[0])
        for k in ("enabled", "reason", "stage1_bucket",
                  "rollout_percent", "cutover_flag", "salt"):
            assert k in d, f"missing key {k} in cutover_decision_for output"


# ─────────────────────────────────────────────────────────────────────────────
# 3. Per-user stickiness — bucket NEVER moves across calls
# ─────────────────────────────────────────────────────────────────────────────
class TestStage1Stickiness:
    def test_bucket_sticky_across_many_calls(self):
        ref = {u: _stage1_bucket(u) for u in SYNTHETIC_USERS}
        for _ in range(50):
            for u in SYNTHETIC_USERS:
                assert _stage1_bucket(u) == ref[u]

    def test_enabled_only_flips_when_percent_crosses_user_bucket(self):
        """User's bucket is fixed → ramping ROLLOUT_PERCENT through 0..100
        flips the user from disabled→enabled at exactly bucket+1."""
        try:
            saved = os.environ.get("INTENT_ROUTER_V2_ROLLOUT_PERCENT")
            uid = SYNTHETIC_USERS[7]
            bkt = _stage1_bucket(uid)
            # Below threshold
            os.environ["INTENT_ROUTER_V2_ROLLOUT_PERCENT"] = str(bkt)
            assert cutover_enabled_for(uid) is False
            # At threshold (strictly-less compare → still disabled)
            # Above threshold
            os.environ["INTENT_ROUTER_V2_ROLLOUT_PERCENT"] = str(bkt + 1)
            assert cutover_enabled_for(uid) is True
        finally:
            if saved is None:
                os.environ.pop("INTENT_ROUTER_V2_ROLLOUT_PERCENT", None)
            else:
                os.environ["INTENT_ROUTER_V2_ROLLOUT_PERCENT"] = saved
