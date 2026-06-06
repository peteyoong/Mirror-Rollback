"""Audit Mirror Today's ranked candidate list for Mel on the current date.

Read-only. Calls the same scoring functions Today uses.
"""
import asyncio, os, sys, json
from datetime import datetime, timezone, timedelta
sys.path.insert(0, "/app/backend")
from dotenv import load_dotenv
load_dotenv("/app/backend/.env")
from motor.motor_asyncio import AsyncIOMotorClient
import swisseph as swe

from services.astrology_today_engine import (
    ASPECT_TYPES as ASPECT_TABLE, compute_transit_natal_aspects,
    get_current_transits, PLANET_WEIGHT as PLANET_WEIGHTS,
)

async def main():
    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = cli[os.environ.get("DB_NAME","test_database")]
    u = await db.users.find_one({"email":"melissa.mars@gmail.com"})
    c = await db.charts.find_one({"user_id": str(u["_id"])})
    chart = c["astrology"]
    planets = chart.get("planets") or {}
    angles  = chart.get("angles") or {}
    natal: dict = {}
    for name,p in planets.items():
        if "longitude" in p:    # <-- SIDEREAL field (same one engine reads)
            natal[name] = {
                "longitude": p["longitude"],
                "tropical_longitude": p.get("tropical_longitude"),
                "sign":      p.get("sign"),
                "retrograde": p.get("retrograde", False),
            }
    for ang_key, src in (("Ascendant","asc"),("Midheaven","mc")):
        a = angles.get(src) or {}
        if "longitude" in a:
            natal[ang_key] = {"longitude": a["longitude"], "sign": a.get("sign")}

    print("== Today's candidate transit-to-natal aspects for Mel ==")
    now = datetime.now(timezone.utc)
    print(f"Today UTC: {now.isoformat()}")
    print()
    transits = get_current_transits(now)
    print("Transit positions (tropical):")
    for name, info in transits.items():
        print(f"  {name:12} {info.get('longitude'):8.3f}° {info.get('sign'):14} {'R' if info.get('retrograde') else ''}")
    print()

    aspects = compute_transit_natal_aspects(transits, natal)
    if not aspects:
        print("  (no aspects within orb)")
        return
    print(f"Aspects within orb ({len(aspects)} total) — POST RANKING PATCH:")
    print(f"{'#':>2}  {'transit':10} {'aspect':12} {'natal':14} {'orb°':>6} {'days_to_exact':>13}  {'score':>6}  {'demoted':>8}  nature")
    for i, a in enumerate(aspects, 1):
        body = a['transit_planet']
        asp_name = a['aspect']
        dte = a.get('days_to_exact')
        dte_s = f"{dte:+8.1f}" if dte is not None else "    n/a "
        dem = "Y" if a.get('future_demoted') else "-"
        print(f"{i:2}  {a['transit_planet']:10} {asp_name:12} {a['natal_planet']:14} {a['orb']:6.2f} {dte_s}      {a['score']:6.3f}  {dem:>8}  {a['nature']}")

asyncio.run(main())
