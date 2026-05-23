"""Seed a synthetic demo user whose chart triggers the Achievement-as-Stabilization atom.

Used to visually verify the Echo Across Systems card on the Lifeline tab.
Idempotent: re-running this script will wipe and re-seed cleanly.

Login email:  achievement.demo@test.com

Signature triggered:
  - Channel 21-45 (Authority)
  - Defined Heart (Ego) — supporting amplifier
  - Mars Square Saturn 2.0° — strongest astro marker
  - Life Path 8 — supporting numerology
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

EMAIL = "achievement.demo@test.com"


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
        "name":       "Achievement Demo",
        "birth_date": "1980-11-26",
        "birth_time": "09:00",
        "city":       "Singapore",
        "country":    "Singapore",
        "gender":     "male",
        "created_at": datetime.now(timezone.utc),
    }
    res = await db.users.insert_one(user_doc)
    uid = str(res.inserted_id)
    print(f"[seed] created user {uid}")

    chart_doc = {
        "user_id":       uid,
        "calculated_at": datetime.now(timezone.utc),
        # Migration shield.
        "debug_stamp": {
            "sidereal_settings_used": {
                "svp_degrees":      31.2836,
                "reference_year":   2000,
                "yearly_increment": 0.0,
            },
            "computed_at_iso": datetime.utcnow().isoformat(),
            "migration":       "synthetic_achievement_seed",
        },
        "bazi": {
            "pillars": {
                "year": {
                    "stem":         "Geng",
                    "branch":       "Shen",
                    "animal_name":  "Monkey",
                    "animal_emoji": "🐒",
                },
            },
        },
        "human_design": {
            "type":              "Manifesting Generator",
            "strategy":          "To Respond",
            "authority":         "Sacral",
            "profile":           "3/5",
            "definition":        "Single",
            "incarnation_cross": {"name": "Right Angle Cross of Maya"},
            "defined_centers":   ["Throat", "Ego", "G Center", "Sacral", "Spleen"],
            "undefined_centers": ["Head", "Ajna", "Solar Plexus", "Root"],
            "defined_channels": [
                {"gate1": 21, "gate2": 45, "centers": ["Ego", "Throat"]},
            ],
            "active_gates": [21, 45, 5, 14, 47, 64],
            "all_gates":    [21, 45, 5, 14, 47, 64],
        },
        "astrology": {
            "planets": {
                "Sun":     {"sign": "Sagittarius", "degree":  3.0, "longitude": 243.0, "house":  9, "retrograde": False},
                "Moon":    {"sign": "Aries",       "degree": 24.0, "longitude":  24.0, "house":  1, "retrograde": False},
                "Mercury": {"sign": "Scorpio",     "degree": 12.0, "longitude": 222.0, "house":  8, "retrograde": False},
                "Venus":   {"sign": "Capricorn",   "degree":  2.0, "longitude": 272.0, "house": 10, "retrograde": False},
                "Mars":    {"sign": "Leo",         "degree": 18.0, "longitude": 138.0, "house":  5, "retrograde": False},
                "Jupiter": {"sign": "Virgo",       "degree":  6.0, "longitude": 156.0, "house":  6, "retrograde": False},
                "Saturn":  {"sign": "Libra",       "degree": 16.0, "longitude": 196.0, "house": 10, "retrograde": False},
                "Uranus":  {"sign": "Scorpio",     "degree": 26.0, "longitude": 236.0, "house":  8, "retrograde": True},
                "Neptune": {"sign": "Sagittarius", "degree": 22.0, "longitude": 262.0, "house":  9, "retrograde": True},
                "Pluto":   {"sign": "Libra",       "degree": 22.0, "longitude": 202.0, "house":  9, "retrograde": True},
            },
            "aspects": [
                # Primary signal — Mars square Saturn 2.0°
                {"body1": "Mars",   "body2": "Saturn",  "type": "square",      "orb": 2.0, "exact_angle":  92.0, "applying": False},
                # Ambient
                {"body1": "Sun",    "body2": "Mercury", "type": "conjunction", "orb": 3.0, "exact_angle":   3.0, "applying": True},
                {"body1": "Saturn", "body2": "Sun",     "type": "square",      "orb": 7.0, "exact_angle":  97.0, "applying": True},  # Over the 5° tight cap, won't qualify
            ],
            "houses": {
                "system":     "Equal",
                "cusps":      [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330],
                "ascendant":  20.0,
                "mc":         290.0,
            },
            "chart_type": "True Sidereal User-Defined (SVP 31.2836°, Equal Houses)",
        },
        "numerology": {
            "core": {
                "life_path": {
                    "number":      8,
                    "description": "Mastery, material outcomes, building.",
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
        print(f"        - {a['atom_id']} (conf={a.get('confidence')}): {a['recognition']}")
        for sig in a["signals"]:
            print(f"            · {sig['lens']} · {sig['label']}")

    print()
    print(f">>> Login email : {EMAIL}")
    print(f">>> user_id     : {uid}")


if __name__ == "__main__":
    asyncio.run(main())
