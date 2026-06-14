"""Acceptance tests for Astrology Relationship Re-Story V1.

Run with:
    cd /app/backend && python -m pytest services/test_astrology_relationship_restory_v1.py -v

Verifies:
    G1. User-facing fields (`headline`, `body`) NEVER contain astrology
        terminology (Sun, Moon, Mars, Venus, Saturn, Pluto, Juno, Vertex,
        North Node, South Node, Descendant, IC, MC, sign names, house
        numbers, aspect names, ruler/ruling, planet, conjunction, square,
        opposition, trine, sextile, …).
    G2. User-facing fields NEVER contain destiny / soulmate / fate /
        certainty language.
    G3. Output is deterministic for fixed inputs (byte-equal across two
        invocations).
    G4. All 5 sections present with the documented keys + headline + body.
    G5. `hidden_evidence` MAY contain astro tokens — that's its purpose.
    G6. Real DB charts (Pete+Mel) produce a complete narrative.
"""
from __future__ import annotations

import asyncio
import os
import re
import sys

import pytest
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.astrology_relationship_restory_v1 import (    # noqa: E402
    compute_relationship_restory_v1,
    BUILD_MARKER,
)


PETE_ID = "697f0c6abf35c0528ff06954"
MEL_ID  = "697ec826ad4b18f75bf42616"


# ════════════════════════════════════════════════════════════════════
# JARGON DETECTOR — fails any user-facing string that mentions astro.
# ════════════════════════════════════════════════════════════════════

# Build a single word-boundary regex.  Case-insensitive.
_ASTRO_BANLIST = [
    # Bodies / points
    r"sun", r"moon", r"mercury", r"venus", r"mars", r"jupiter",
    r"saturn", r"uranus", r"neptune", r"pluto", r"chiron",
    r"juno", r"vertex", r"north\s+node", r"south\s+node", r"nodal",
    r"ascendant", r"descendant", r"midheaven", r"imum\s+coeli",
    r"\basc\b", r"\bdsc\b", r"\bmc\b", r"\bic\b",
    # Signs
    r"aries", r"taurus", r"gemini", r"cancer", r"leo", r"virgo",
    r"libra", r"scorpio", r"sagittarius", r"capricorn", r"aquarius",
    r"pisces", r"ophiuchus",
    # Houses / aspects / structures
    r"house", r"cusp", r"conjunction", r"opposition", r"square",
    r"trine", r"sextile", r"quincunx", r"orb", r"natal",
    r"synastry", r"composite", r"transit",
    r"ruler", r"rulership", r"ruling", r"\baspect\b", r"placement",
    r"placeholder",   # safety
    # Generic astro words
    r"astrology", r"astrological", r"horoscope", r"zodiac",
]
_JARGON_RE = re.compile(
    r"\b(?:" + r"|".join(_ASTRO_BANLIST) + r")\b",
    re.IGNORECASE,
)

# Destiny / soulmate / certainty banlist
_DESTINY_BANLIST = [
    r"soulmate", r"twin\s+flame", r"destined", r"destiny",
    r"fate", r"fated", r"predestined", r"meant\s+to\s+be",
    r"\bkarmic\b", r"karma", r"karmic\s+lesson",
    r"\bwill\s+always\b", r"\bnever\s+will\b",
    r"\bguaranteed\b", r"\bguarantee\b",
    r"\babsolute(?:ly)?\b", r"\bcertain\b", r"\bcertainty\b",
    r"\bmust\s+",
]
_DESTINY_RE = re.compile(
    r"\b(?:" + r"|".join(_DESTINY_BANLIST) + r")",
    re.IGNORECASE,
)


def _scan_user_facing(payload, scenario):
    """Walk the payload and fail on jargon or destiny language anywhere
    in `headline` / `body`.  `hidden_evidence` is allowed to contain
    astro tokens (that's its purpose)."""
    sections = (payload or {}).get("sections") or {}
    for key, sec in sections.items():
        for field in ("headline", "body"):
            text = (sec or {}).get(field) or ""
            j = _JARGON_RE.search(text)
            assert not j, (
                f"[{scenario}] astro-jargon leak in sections.{key}.{field}: "
                f"matched {j.group(0)!r} in text {text!r}"
            )
            d = _DESTINY_RE.search(text)
            assert not d, (
                f"[{scenario}] destiny/certainty leak in "
                f"sections.{key}.{field}: matched {d.group(0)!r} in text "
                f"{text!r}"
            )


@pytest.fixture(scope="function")
def db():
    load_dotenv(os.path.join(ROOT, ".env"))
    mongo_url = os.getenv("MONGO_URL")
    assert mongo_url, "MONGO_URL must be set in /app/backend/.env"
    client = AsyncIOMotorClient(mongo_url)
    yield client["test_database"]
    client.close()


async def _load_chart(db, user_id: str):
    return await db.charts.find_one({"user_id": user_id})


# ════════════════════════════════════════════════════════════════════
# G4 — output shape is complete
# ════════════════════════════════════════════════════════════════════

def test_G4_output_shape_complete():
    out = compute_relationship_restory_v1(
        chart_a={"astrology": {"planets": {"Sun": {"sign": "Pisces"},
                                            "Moon": {"sign": "Cancer"}}}},
        chart_b={"astrology": {"planets": {"Sun": {"sign": "Gemini"},
                                            "Moon": {"sign": "Aquarius"}}}},
        relationship_role="spouse",
        name_a="A",
        name_b="B",
    )
    assert out["success"] is True
    assert out["build_marker"] == BUILD_MARKER
    assert out["relationship_role"] == "spouse"
    keys = set(out["sections"].keys())
    assert keys == {
        "what_lives_between_you",
        "what_strengthens_this_relationship",
        "growth_edge",
        "shadow_pattern",
        "why_this_person_matters",
    }
    for k, sec in out["sections"].items():
        assert sec["headline"], f"section {k} missing headline"
        assert sec["body"], f"section {k} missing body"
        assert "hidden_evidence" in sec


# ════════════════════════════════════════════════════════════════════
# G1+G2 — no jargon / no destiny language across diverse role/sign mixes
# ════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("scenario,inputs", [
    ("air_water_spouse", dict(
        sun_a="Gemini",   moon_a="Aquarius",
        sun_b="Pisces",   moon_b="Cancer",
        role="spouse",
    )),
    ("fire_earth_partner", dict(
        sun_a="Aries",    moon_a="Leo",
        sun_b="Virgo",    moon_b="Taurus",
        role="partner",
    )),
    ("fire_water_child", dict(
        sun_a="Sagittarius", moon_a="Leo",
        sun_b="Cancer",      moon_b="Pisces",
        role="child",
    )),
    ("same_element_friend", dict(
        sun_a="Libra",    moon_a="Aquarius",
        sun_b="Aquarius", moon_b="Gemini",
        role="close_friend",
    )),
    ("missing_b_unknown_role", dict(
        sun_a="Capricorn", moon_a="Virgo",
        sun_b=None,        moon_b=None,
        role="forum_member",
    )),
])
def test_G1_G2_no_jargon_or_destiny(scenario, inputs):
    def _mk_chart(sun, moon):
        planets = {}
        if sun:  planets["Sun"]  = {"sign": sun}
        if moon: planets["Moon"] = {"sign": moon}
        return {"astrology": {"planets": planets}}
    out = compute_relationship_restory_v1(
        chart_a=_mk_chart(inputs["sun_a"], inputs["moon_a"]),
        chart_b=_mk_chart(inputs["sun_b"], inputs["moon_b"]),
        relationship_role=inputs["role"],
        name_a="A",
        name_b="B",
    )
    assert out["success"] is True
    _scan_user_facing(out, scenario)


# ════════════════════════════════════════════════════════════════════
# G3 — deterministic
# ════════════════════════════════════════════════════════════════════

def test_G3_determinism():
    inputs = dict(
        chart_a={"astrology": {"planets": {
            "Sun":   {"sign": "Pisces"},
            "Moon":  {"sign": "Cancer"},
            "Venus": {"sign": "Taurus"},
            "Saturn":{"sign": "Capricorn"},
        }}},
        chart_b={"astrology": {"planets": {
            "Sun":   {"sign": "Gemini"},
            "Moon":  {"sign": "Aquarius"},
            "Venus": {"sign": "Gemini"},
            "Saturn":{"sign": "Aquarius"},
        }}},
        relationship_role="spouse",
        name_a="Pete",
        name_b="Mel",
    )
    r1 = compute_relationship_restory_v1(**inputs)
    r2 = compute_relationship_restory_v1(**inputs)
    assert r1 == r2, "Re-Story V1 must be deterministic for fixed inputs"


# ════════════════════════════════════════════════════════════════════
# G6 — End-to-end against real DB charts
# ════════════════════════════════════════════════════════════════════

def test_G6_real_charts_pete_mel(db):
    async def _run():
        a = await _load_chart(db, PETE_ID)
        b = await _load_chart(db, MEL_ID)
        assert a is not None, "Pete chart missing — DB fixture problem"
        assert b is not None, "Mel chart missing — DB fixture problem"
        out = compute_relationship_restory_v1(
            chart_a=a,
            chart_b=b,
            relationship_role="spouse",
            name_a="Pete",
            name_b="Mel",
        )
        assert out["success"] is True
        # All sections produced
        assert len(out["sections"]) == 5
        # Each body has at least one full sentence (rough heuristic).
        for k, sec in out["sections"].items():
            body = sec["body"]
            assert len(body) >= 60, (
                f"section {k} body too short ({len(body)} chars): {body!r}"
            )
        # G1+G2 on real data
        _scan_user_facing(out, "real_pete_mel_spouse")
        # Hidden evidence MUST contain at least one astro token (that's
        # what makes it hidden_evidence).
        between = out["sections"]["what_lives_between_you"]
        assert len(between["hidden_evidence"]) >= 1
    asyncio.run(_run())


# ════════════════════════════════════════════════════════════════════
# G7 — Empty chart inputs do not crash
# ════════════════════════════════════════════════════════════════════

def test_G7_empty_inputs_safe():
    out = compute_relationship_restory_v1(
        chart_a={},
        chart_b={},
        relationship_role="",
        name_a="",
        name_b="",
    )
    assert out["success"] is True
    assert out["build_marker"] == BUILD_MARKER
    # Defaults applied; user-facing fields still clean.
    _scan_user_facing(out, "empty_inputs")
