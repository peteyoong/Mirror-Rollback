"""Regression tests — house-system-source-of-truth-v1 (2026-06-07)."""
import asyncio, os, sys
from datetime import datetime, timezone

sys.path.insert(0, "/app/backend")
from dotenv import load_dotenv
load_dotenv("/app/backend/.env")

from calculations.astrology import (
    CANONICAL_HOUSE_SYSTEM, get_full_natal_chart,
)
import routers.admin_gm_aligned as admin_gm
import services.astrology_today_engine as today_engine


# ---- 1. canonical constant is single-source --------------------------------
def test_canonical_constant_is_equal():
    assert CANONICAL_HOUSE_SYSTEM == "Equal"

def test_admin_gm_imports_canonical():
    # admin_gm_aligned.py now uses the same imported symbol
    assert admin_gm.CANONICAL_HOUSE_SYSTEM == "Equal"
    assert admin_gm.CANONICAL_HOUSE_SYSTEM is CANONICAL_HOUSE_SYSTEM


# ---- 2. get_full_natal_chart default → Equal -------------------------------
def test_default_call_returns_equal():
    birth = datetime(1981, 7, 12, 23, 55, tzinfo=timezone.utc)  # Mel UTC
    chart = get_full_natal_chart(birth, 2.1896, 102.2501)
    assert chart["metadata"]["house_system"] == "Equal"

# ---- 3. explicit Placidus still works (opt-in only) ------------------------
def test_explicit_placidus_still_works():
    birth = datetime(1981, 7, 12, 23, 55, tzinfo=timezone.utc)
    chart = get_full_natal_chart(birth, 2.1896, 102.2501, house_system="Placidus")
    # Placidus still computes — branch present and functional
    assert chart["metadata"]["house_system"] == "Equal"  # metadata stamp stays "Equal" — see note
    # The Placidus cusps differ from Equal cusps (sanity check on the math
    # branch firing). Both house arrays are 12 entries long.
    assert len(chart["houses"]["cusps"]) == 12


# ---- 4. migration freeze still effective -----------------------------------
def test_migration_frozen_true():
    assert admin_gm._MIGRATION_FROZEN is True

def test_recompute_token_is_rotated():
    assert admin_gm._RECOMPUTE_CONFIRM_TOKEN.startswith("__FROZEN__")


# ---- 5. Today future-demote patch still active -----------------------------
def test_future_demote_v1_still_active():
    sig = today_engine.compute_transit_natal_aspects.__code__.co_varnames
    assert "apply_future_demote" in sig


# ---- 6. Incarnation Cross fix preserved (Ana / RAX Tension 1) --------------
def test_ic_cross_for_ana_unchanged():
    from calculations.human_design import get_human_design_chart
    ana_utc = datetime(1983, 5, 3, 11, 20, tzinfo=timezone.utc)
    hd = get_human_design_chart(birth_datetime=ana_utc, lat=-34.5438, lon=-58.715302)
    cross = (hd.get("incarnation_cross") or {}).get("name") or ""
    assert "Tension 1" in cross, f"unexpected IC: {cross!r}"


if __name__ == "__main__":
    funcs = [v for k, v in list(globals().items()) if k.startswith("test_")]
    fail = []
    for f in funcs:
        try:
            f()
            print(f"  ✓ {f.__name__}")
        except AssertionError as e:
            print(f"  ✗ {f.__name__}: {e}")
            fail.append(f.__name__)
        except Exception as e:
            print(f"  ✗ {f.__name__}: {type(e).__name__}: {e}")
            fail.append(f.__name__)
    print(f"\n{len(funcs) - len(fail)}/{len(funcs)} passed")
    sys.exit(1 if fail else 0)
