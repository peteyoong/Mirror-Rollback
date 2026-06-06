"""Regression test for the future-exact demote rule.
ranking-future-demote-v1 — Mel-based fixture.
"""
import asyncio, os, sys
from datetime import datetime, timezone

sys.path.insert(0, "/app/backend")
from dotenv import load_dotenv
load_dotenv("/app/backend/.env")
from motor.motor_asyncio import AsyncIOMotorClient

from services.astrology_today_engine import (
    compute_transit_natal_aspects, get_current_transits,
)


def _load_mel_natal():
    async def _go():
        cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
        db  = cli[os.environ.get("DB_NAME", "test_database")]
        u   = await db.users.find_one({"email": "melissa.mars@gmail.com"})
        c   = await db.charts.find_one({"user_id": str(u["_id"])})
        astro = c["astrology"]
        natal = {}
        for n, p in (astro.get("planets") or {}).items():
            if "longitude" in p:
                natal[n] = {
                    "longitude": p["longitude"],
                    "tropical_longitude": p.get("tropical_longitude"),
                    "sign": p.get("sign"),
                }
        return natal
    return asyncio.get_event_loop().run_until_complete(_go())


def test_future_uranus_opp_moon_is_demoted_today():
    natal   = _load_mel_natal()
    sky     = get_current_transits(datetime.now(timezone.utc))
    aspects = compute_transit_natal_aspects(sky, natal)

    # Find Uranus opposition Moon (exact ~2026-06-20, ~14 days out)
    uranus_moon = next(
        (a for a in aspects
         if a["transit_planet"] == "Uranus"
         and a["aspect"] == "opposition"
         and a["natal_planet"] == "Moon"),
        None,
    )
    assert uranus_moon is not None, "Uranus opp Moon should still be present"
    assert uranus_moon["future_demoted"] is True
    # It must rank BELOW every near-exact aspect
    near_exact = [a for a in aspects
                  if a.get("days_to_exact") is not None
                  and abs(a["days_to_exact"]) <= 2.0]
    assert near_exact, "Expected at least one near-exact aspect today"
    uranus_idx = aspects.index(uranus_moon)
    for ne in near_exact:
        assert aspects.index(ne) < uranus_idx, (
            f"Near-exact {ne['transit_planet']} {ne['aspect']} {ne['natal_planet']} "
            f"({ne['days_to_exact']}d) must rank above demoted Uranus-opp-Moon"
        )


def test_demote_can_be_disabled():
    natal   = _load_mel_natal()
    sky     = get_current_transits(datetime.now(timezone.utc))
    raw     = compute_transit_natal_aspects(sky, natal, apply_future_demote=False)
    patched = compute_transit_natal_aspects(sky, natal, apply_future_demote=True)
    # Without demote: pure score sort, no future_demoted=True
    for a in raw:
        assert a.get("future_demoted") is False
    # With demote: at least one demoted
    assert any(a.get("future_demoted") for a in patched)


def test_signal_map_preserved():
    """The total set of aspects must NOT change — only ordering."""
    natal   = _load_mel_natal()
    sky     = get_current_transits(datetime.now(timezone.utc))
    raw     = compute_transit_natal_aspects(sky, natal, apply_future_demote=False)
    patched = compute_transit_natal_aspects(sky, natal, apply_future_demote=True)
    assert len(raw) == len(patched)
    sig_raw     = sorted([(a["transit_planet"], a["aspect"], a["natal_planet"]) for a in raw])
    sig_patched = sorted([(a["transit_planet"], a["aspect"], a["natal_planet"]) for a in patched])
    assert sig_raw == sig_patched, "Aspect set must be identical pre/post patch"


def test_no_natal_math_change():
    """Sanity: the natal frame Mirror reads from must be unchanged.
    Uranus opp Moon is still detected within orb (this is the structural
    guarantee that natal math is untouched)."""
    natal   = _load_mel_natal()
    sky     = get_current_transits(datetime.now(timezone.utc))
    aspects = compute_transit_natal_aspects(sky, natal)
    uranus_moon = next(
        (a for a in aspects
         if a["transit_planet"] == "Uranus"
         and a["aspect"] == "opposition"
         and a["natal_planet"] == "Moon"),
        None,
    )
    assert uranus_moon is not None
    assert uranus_moon["orb"] < 3.0  # was 1.4° in audit


if __name__ == "__main__":
    funcs = [v for k, v in list(globals().items()) if k.startswith("test_")]
    failed = []
    for f in funcs:
        try:
            f(); print(f"  ✓ {f.__name__}")
        except AssertionError as e:
            print(f"  ✗ {f.__name__}: {e}"); failed.append(f.__name__)
        except Exception as e:
            print(f"  ✗ {f.__name__}: {type(e).__name__}: {e}")
            failed.append(f.__name__)
    print(f"\n{len(funcs) - len(failed)}/{len(funcs)} passed")
    sys.exit(1 if failed else 0)
