"""Read-only A/B comparison — Mirror current vs 13-sign midpoint table.

Run: ``python3 scripts/compare_midpoint13_for_reference_users.py``

Does not modify or persist anything.
Build marker: midpoint13-forensic-module-v1
"""
import asyncio, os, sys
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

sys.path.insert(0, "/app/backend")
load_dotenv("/app/backend/.env")

from calculations.true_sidereal_midpoint_boundaries import (
    compare_current_vs_midpoint13, BUILD_MARKER,
)

REFERENCE_USERS = [
    ("pete@pulsifi.me",        "Pete"),
    ("melissa.mars@gmail.com", "Mel"),
    # Ana — best-effort, by name (no fixed email known here)
]
BODIES = ("Sun", "Moon", "Mercury", "Venus", "Mars")
ANGLES = ("asc", "mc")


async def fetch_chart(db, email):
    u = await db.users.find_one({"email": email})
    if not u:
        return None, None
    c = await db.charts.find_one({"user_id": str(u["_id"])})
    return u, c


async def maybe_fetch_ana(db):
    u = await db.users.find_one({"name": {"$regex": "^Ana", "$options": "i"}})
    if not u:
        return None, None
    c = await db.charts.find_one({"user_id": str(u["_id"])})
    return u, c


async def main():
    print(f"# A/B comparison — Mirror current (Variant B, 12-sign) vs 13-sign midpoint table")
    print(f"# build_marker = {BUILD_MARKER}")
    print(f"# READ-ONLY  ·  no chart math, no DB writes, no migration\n")

    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db  = cli[os.environ.get("DB_NAME", "test_database")]

    fixtures = []
    for email, label in REFERENCE_USERS:
        u, c = await fetch_chart(db, email)
        if c:
            fixtures.append((label, c))
    u_ana, c_ana = await maybe_fetch_ana(db)
    if c_ana:
        fixtures.append(("Ana", c_ana))

    if not fixtures:
        print("(no reference users available)")
        return

    header = f"{'user':6} {'body':6} {'trop_lon':>10}  {'current':14} {'midpoint13':14} {'match':>6} {'oph':>4} {'transition':>10}"
    print(header)
    print("-" * len(header))

    for label, chart in fixtures:
        astro = chart.get("astrology") or {}
        planets = astro.get("planets") or {}
        angles  = astro.get("angles") or {}
        for body in BODIES:
            p = planets.get(body) or {}
            trop = p.get("tropical_longitude")
            if trop is None:
                continue
            r = compare_current_vs_midpoint13(trop)
            flag = "✓" if r["match"] else "✗"
            oph  = "Y" if r["midpoint13_is_ophiuchus"] else "-"
            tz   = "TRANSITION" if r["transition_zone"] else "-"
            print(f"{label:6} {body:6} {r['tropical_longitude']:>10.4f}  "
                  f"{r['current_sign']:14} {r['midpoint13_sign']:14} {flag:>6} {oph:>4} {tz:>10}")
        for ang_key in ANGLES:
            a = angles.get(ang_key) or {}
            trop = a.get("tropical_longitude")
            if trop is None:
                continue
            r = compare_current_vs_midpoint13(trop)
            flag = "✓" if r["match"] else "✗"
            oph  = "Y" if r["midpoint13_is_ophiuchus"] else "-"
            tz   = "TRANSITION" if r["transition_zone"] else "-"
            display = "ASC" if ang_key == "asc" else "MC"
            print(f"{label:6} {display:6} {r['tropical_longitude']:>10.4f}  "
                  f"{r['current_sign']:14} {r['midpoint13_sign']:14} {flag:>6} {oph:>4} {tz:>10}")
        print()

    print("# Notes:")
    print("#   'current' uses Mirror production sign_attribution.attribute_sign(mode=MODE_TRUE_SIDEREAL_MIDPOINT).")
    print("#   'midpoint13' uses TRUE_SIDEREAL_MIDPOINT_BOUNDARIES_13 with ARIES_BOUNDARY_OFFSET=31.2836.")
    print("#   'transition' flag = within 3.00° of any 13-sign boundary.")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
