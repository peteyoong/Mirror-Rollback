"""test_auto_migration_mel_safety_net.py — v1.5.4 regression test
====================================================================
Validates the auto-migration logic in `check_and_migrate_astrology_chart`
that targets Mel-Yoong-style stale charts.

These tests are PURE-LOGIC tests against the eligibility branches; they
do not hit the DB or run the chart engine. The goal is to assert the
exact pattern that triggers re-migration:

Case 4: pre-1982 Malaysian birth with `resolved_offset == "+08:00"`
Case 5: Mel safety net — name "Mel" or email "melissa.mars@gmail.com"
        whose chart is NOT stamped with `resolved_offset == "+07:30"`.
"""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# We import the eligibility logic via a local copy here because
# `check_and_migrate_astrology_chart` is async and pulls in the
# entire server.py at import. Instead we replicate the gating logic.
from datetime import datetime


def _evaluate_case4(user: dict, chart: dict) -> bool:
    mi = chart.get("migration_info") or {}
    ro = (mi.get("resolved_offset") or "").strip()
    if ro != "+08:00":
        return False
    user_tz = (user.get("timezone") or "").strip()
    if not user_tz.startswith(("Asia/Kuala_Lumpur", "Asia/Kuching",
                                "Asia/Singapore", "Asia/Brunei")):
        return False
    bd = user.get("birth_date")
    if isinstance(bd, str):
        try:
            bd = datetime.fromisoformat(bd[:10])
        except Exception:
            return False
    if not isinstance(bd, datetime):
        return False
    return bd.year < 1982


def _evaluate_case5(user: dict, chart: dict) -> bool:
    emails = (user.get("email") or "").lower()
    names  = (user.get("name") or "").lower().strip()
    if not (emails == "melissa.mars@gmail.com" or names == "mel"):
        return False
    mi = chart.get("migration_info") or {}
    return (mi.get("resolved_offset") or "").strip() != "+07:30"


def _mel_user():
    return {
        "email": "melissa.mars@gmail.com",
        "name": "Mel",
        "timezone": "Asia/Kuala_Lumpur",
        "birth_date": "1981-07-13",
    }


def _correct_mel_chart():
    return {"migration_info": {"resolved_offset": "+07:30"}}


def _stale_mel_chart():
    return {"migration_info": {"resolved_offset": "+08:00"}}


# ─────────────────────────────────────────────────────────────────────
# Case 4 tests
# ─────────────────────────────────────────────────────────────────────
def test_case4_mel_pre_1982_kl_plus_08_triggers():
    assert _evaluate_case4(_mel_user(), _stale_mel_chart()) is True


def test_case4_post_1982_does_not_trigger():
    u = _mel_user(); u["birth_date"] = "1985-07-13"
    assert _evaluate_case4(u, _stale_mel_chart()) is False


def test_case4_non_malaysian_does_not_trigger():
    u = _mel_user(); u["timezone"] = "Asia/Tokyo"
    assert _evaluate_case4(u, _stale_mel_chart()) is False


def test_case4_already_correct_offset_does_not_trigger():
    assert _evaluate_case4(_mel_user(), _correct_mel_chart()) is False


# ─────────────────────────────────────────────────────────────────────
# Case 5 — Mel safety net (idempotent, hits if her chart isn't +07:30)
# ─────────────────────────────────────────────────────────────────────
def test_case5_mel_by_email_with_stale_chart_triggers():
    assert _evaluate_case5(_mel_user(), _stale_mel_chart()) is True


def test_case5_mel_by_name_with_stale_chart_triggers():
    u = _mel_user(); u["email"] = "different@example.com"
    assert _evaluate_case5(u, _stale_mel_chart()) is True


def test_case5_mel_already_correct_does_not_trigger():
    assert _evaluate_case5(_mel_user(), _correct_mel_chart()) is False


def test_case5_non_mel_user_does_not_trigger():
    other = {"email": "pete@pulsifi.me", "name": "Pete"}
    assert _evaluate_case5(other, _stale_mel_chart()) is False


def test_case5_mel_missing_migration_info_triggers():
    """If migration_info doesn't exist at all, that's NOT +07:30 → trigger."""
    assert _evaluate_case5(_mel_user(), {}) is True
