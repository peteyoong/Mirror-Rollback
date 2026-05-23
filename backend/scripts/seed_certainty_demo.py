"""Seed a synthetic demo user whose chart triggers the Certainty Pattern atom.

Used to visually verify the Echo Across Systems card on the Lifeline tab.
Idempotent: re-running this script will wipe and re-seed cleanly.

Login email:  certainty.demo@test.com
"""
import asyncio
import os
import sys
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Resolve repo paths so imports work whether script is run from /app/backend
# or anywhere else.
HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, BACKEND)
load_dotenv(os.path.join(BACKEND, ".env"))

from services.cross_lens_atoms import compute_atoms  # noqa: E402

EMAIL = "certainty.demo@test.com"


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
        "name":       "Certainty Demo",
        "birth_date": "1979-04-19",
        "birth_time": "10:00",
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
        # Migration shield — without this the startup data-migration
        # recomputes the chart from birth data and wipes the synthetic
        # signals we explicitly set below. We claim the canonical SVP
        # value and provide a complete-enough bazi block so neither
        # migration check triggers a recompute.
        "debug_stamp": {
            "sidereal_settings_used": {
                "svp_degrees":      31.2836,
                "reference_year":   2000,
                "yearly_increment": 0.0,
            },
            "computed_at_iso": datetime.utcnow().isoformat(),
            "migration":       "synthetic_certainty_seed",
        },
        "bazi": {
            "pillars": {
                "year": {
                    "stem":         "Ji",
                    "branch":       "Wei",
                    "animal_name":  "Goat",
                    "animal_emoji": "🐐",
                },
            },
        },
        "human_design": {
            "type":              "Projector",
            "strategy":          "To Wait for Invitation",
            "authority":         "Splenic",
            "profile":           "5/1",
            "definition":        "Single",
            "incarnation_cross": {"name": "Right Angle Cross of Explanation"},
            "defined_centers":   ["Ajna", "Throat", "Head"],
            "undefined_centers": [
                "G Center", "Ego", "Sacral", "Solar Plexus", "Spleen", "Root",
            ],
            "defined_channels": [
                {"gate1": 4, "gate2": 63, "centers": ["Head", "Ajna"]},
            ],
            "active_gates": [4, 63, 17, 11, 47, 24],
            "all_gates":    [4, 63, 17, 11, 47, 24],
        },
        "astrology": {
            "planets": {
                "Sun":     {"sign": "Aries",       "degree": 29.0, "longitude":  29.0, "house": 10, "retrograde": False},
                "Moon":    {"sign": "Cancer",      "degree": 12.0, "longitude": 102.0, "house":  1, "retrograde": False},
                "Mercury": {"sign": "Aries",       "degree": 15.0, "longitude":  15.0, "house": 10, "retrograde": False},
                "Venus":   {"sign": "Pisces",      "degree":  4.0, "longitude": 334.0, "house":  9, "retrograde": False},
                "Mars":    {"sign": "Pisces",      "degree": 18.0, "longitude": 348.0, "house":  9, "retrograde": False},
                "Jupiter": {"sign": "Leo",         "degree":  2.0, "longitude": 122.0, "house":  2, "retrograde": False},
                "Saturn":  {"sign": "Cancer",      "degree": 13.0, "longitude": 103.0, "house":  1, "retrograde": False},
                "Uranus":  {"sign": "Scorpio",     "degree": 17.0, "longitude": 227.0, "house":  4, "retrograde": True},
                "Neptune": {"sign": "Sagittarius", "degree": 18.0, "longitude": 258.0, "house":  5, "retrograde": True},
                "Pluto":   {"sign": "Libra",       "degree": 15.0, "longitude": 195.0, "house":  3, "retrograde": True},
            },
            "aspects": [
                {"body1": "Mercury", "body2": "Saturn", "type": "square",      "orb": 2.0, "exact_angle":  92.0, "applying": False},
                {"body1": "Sun",     "body2": "Mercury","type": "conjunction", "orb": 3.0, "exact_angle":   3.0, "applying": True},
            ],
            "houses": {
                "system":     "Equal",
                "cusps":      [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330],
                "ascendant":  12.0,
                "mc":         280.0,
            },
            "chart_type": "True Sidereal User-Defined (SVP 31.2836°, Equal Houses)",
        },
        "numerology": {
            "core": {
                "life_path": {
                    "number":      7,
                    "description": "The seeker — analysis, introspection, inner verification.",
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

    print()
    print(f">>> Login email : {EMAIL}")
    print(f">>> user_id     : {uid}")


if __name__ == "__main__":
    asyncio.run(main())
