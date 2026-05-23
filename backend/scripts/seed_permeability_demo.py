"""Seed a synthetic demo user whose chart triggers the Emotional Permeability atom.

Used to visually verify the Echo Across Systems card on the Lifeline tab.
Idempotent: re-running this script will wipe and re-seed cleanly.

Login email:  permeability.demo@test.com
"""
import asyncio
import os
import sys
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, BACKEND)
load_dotenv(os.path.join(BACKEND, ".env"))

from services.cross_lens_atoms import compute_atoms  # noqa: E402

EMAIL = "permeability.demo@test.com"


async def main() -> None:
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ.get("DB_NAME", "test_database")]

    existing = await db.users.find_one({"email": EMAIL})
    if existing:
        await db.charts.delete_many({"user_id": str(existing["_id"])})
        await db.users.delete_one({"_id": existing["_id"]})
        print(f"[seed] cleaned prior {EMAIL}")

    user_doc = {
        "email":      EMAIL,
        "name":       "Permeability Demo",
        "birth_date": "1985-03-08",
        "birth_time": "21:14",
        "city":       "Singapore",
        "country":    "Singapore",
        "gender":     "female",
        "created_at": datetime.now(timezone.utc),
    }
    res = await db.users.insert_one(user_doc)
    uid = str(res.inserted_id)
    print(f"[seed] created user {uid}")

    chart_doc = {
        "user_id":       uid,
        "calculated_at": datetime.now(timezone.utc),
        # Migration shield (see seed_certainty_demo.py for full rationale).
        "debug_stamp": {
            "sidereal_settings_used": {
                "svp_degrees":      31.2836,
                "reference_year":   2000,
                "yearly_increment": 0.0,
            },
            "computed_at_iso": datetime.utcnow().isoformat(),
            "migration":       "synthetic_permeability_seed",
        },
        "bazi": {
            "pillars": {
                "year": {
                    "stem":         "Yi",
                    "branch":       "Chou",
                    "animal_name":  "Ox",
                    "animal_emoji": "🐂",
                },
            },
        },
        "human_design": {
            "type":              "Generator",
            "strategy":          "To Respond",
            "authority":         "Sacral",
            "profile":           "2/4",
            "definition":        "Single",
            "incarnation_cross": {"name": "Right Angle Cross of Eden"},
            # OPEN Solar Plexus — must NOT appear in defined_centers.
            "defined_centers":   ["Throat", "G Center", "Sacral"],
            "undefined_centers": [
                "Head", "Ajna", "Ego", "Solar Plexus", "Spleen", "Root",
            ],
            "defined_channels": [
                {"gate1": 6, "gate2": 59, "centers": ["Solar Plexus", "Sacral"]},
            ],
            "active_gates": [6, 59, 22, 5, 14],
            "all_gates":    [6, 59, 22, 5, 14],
        },
        "astrology": {
            "planets": {
                "Sun":     {"sign": "Pisces",      "degree": 18.0, "longitude": 348.0, "house":  7, "retrograde": False},
                "Moon":    {"sign": "Scorpio",     "degree": 22.0, "longitude": 232.0, "house": 12, "retrograde": False},
                "Mercury": {"sign": "Pisces",      "degree":  2.0, "longitude": 332.0, "house":  6, "retrograde": False},
                "Venus":   {"sign": "Aries",       "degree":  5.0, "longitude":   5.0, "house":  8, "retrograde": False},
                "Mars":    {"sign": "Pisces",      "degree": 14.0, "longitude": 344.0, "house":  7, "retrograde": False},
                "Jupiter": {"sign": "Aquarius",    "degree": 12.0, "longitude": 312.0, "house":  6, "retrograde": False},
                "Saturn":  {"sign": "Scorpio",     "degree": 26.0, "longitude": 236.0, "house": 12, "retrograde": True},
                "Uranus":  {"sign": "Sagittarius", "degree": 18.0, "longitude": 258.0, "house":  1, "retrograde": True},
                "Neptune": {"sign": "Sagittarius", "degree": 26.0, "longitude": 266.0, "house":  1, "retrograde": True},
                "Pluto":   {"sign": "Libra",       "degree":  4.0, "longitude": 184.0, "house": 10, "retrograde": True},
            },
            "aspects": [
                {"body1": "Moon", "body2": "Neptune", "type": "square",      "orb": 1.8, "exact_angle":  91.8, "applying": False},
                {"body1": "Sun",  "body2": "Mercury", "type": "conjunction", "orb": 4.0, "exact_angle":   4.0, "applying": True},
            ],
            "houses": {
                "system":     "Equal",
                "cusps":      [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330],
                "ascendant":  240.0,
                "mc":         150.0,
            },
            "chart_type": "True Sidereal User-Defined (SVP 31.2836°, Equal Houses)",
        },
        "numerology": {
            "core": {
                "life_path": {
                    "number":      2,
                    "description": "Partnership and attunement.",
                },
            },
        },
    }
    await db.charts.insert_one(chart_doc)
    print(f"[seed] created chart for user {uid}")

    chart_back = await db.charts.find_one({"user_id": uid})
    atoms = compute_atoms(chart_back)
    print(f"[seed] atoms detected: {len(atoms)}")
    for a in atoms:
        print(f"        - {a['atom_id']}: {a['recognition']}")
        for sig in a["signals"]:
            print(f"            · {sig['lens']} · {sig['label']}")

    print()
    print(f">>> Login email : {EMAIL}")
    print(f">>> user_id     : {uid}")


if __name__ == "__main__":
    asyncio.run(main())
