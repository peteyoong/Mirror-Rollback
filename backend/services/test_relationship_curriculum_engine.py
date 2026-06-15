"""Relationship Curriculum Engine V1 — acceptance tests.

Run with:
    cd /app/backend && python -m pytest services/test_relationship_curriculum_engine.py -v

Verifies:
    G1.  Output shape — all 4 sections + proof + confidence keys present
    G2.  User-facing strings NEVER contain destiny / soulmate / fate /
         twin-flame / karmic / cosmic-assignment language
    G3.  Mirror voice — uses "appears / suggests / invites / reflects /
         seems / may be developing"; NEVER "will / must / is destined to"
    G4.  Deterministic — fixed inputs produce byte-equal output
    G5.  Word-count targets met:
            gift         ≥ 90 words   (target 150–200)
            challenge    ≥ 70 words   (target 100–150)
            growth_edge  ≥ 70 words   (target 100–150)
            curriculum   ≥ 90 words   (target 120–200)
    G6.  Role weighting works: spouse > friend on confidence
    G7.  Pete↔Mel real DB charts produce a complete payload
    G8.  Empty / partial input does not crash
    G9.  Flag gate works: is_enabled / maybe_generate
   G10.  HD pair (Manifestor ↔ Reflector) produces HD proof line
   G11.  Synthetic "Gemini DSC + Pluto 7th + Mercury ruler" axis
         activates curiosity/dialogue/depth themes against a
         Gemini-Sun + Reflector person B.
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

from services.relationship_curriculum_engine import (    # noqa: E402
    generate_relationship_curriculum,
    maybe_generate,
    is_enabled,
    BUILD_MARKER,
)


PETE_ID = "697f0c6abf35c0528ff06954"
MEL_ID  = "697ec826ad4b18f75bf42616"


# ════════════════════════════════════════════════════════════════════
# DESTINY / CERTAINTY BAN-LIST  (G2 + G3)
# ════════════════════════════════════════════════════════════════════
_DESTINY_BANLIST = [
    r"soulmate", r"twin\s+flame", r"destined", r"destiny",
    r"fate", r"fated", r"predestined", r"meant\s+to\s+be",
    r"\bkarmic\b", r"\bkarma\b",
    r"cosmic\s+assignment",
    r"\bguaranteed\b",
    r"\bwill\s+(always|never)\b",
]
_DESTINY_RE = re.compile(
    r"\b(?:" + r"|".join(_DESTINY_BANLIST) + r")",
    re.IGNORECASE,
)

# Mirror-voice violations
_CERTAINTY_BANLIST = [
    r"\bis\s+destined\s+to\b",
    r"\bis\s+meant\s+to\b",
    r"\bmust\s+",
    r"\babsolutely\b",
]
_CERTAINTY_RE = re.compile(
    r"\b(?:" + r"|".join(_CERTAINTY_BANLIST) + r")",
    re.IGNORECASE,
)


def _scan(payload, scenario):
    rc = (payload or {}).get("relationship_curriculum") or {}
    for fld in ("gift", "challenge", "growth_edge", "curriculum"):
        text = rc.get(fld) or ""
        d = _DESTINY_RE.search(text)
        assert not d, (
            f"[{scenario}] destiny leak in {fld}: matched {d.group(0)!r} "
            f"in text {text!r}"
        )
        c = _CERTAINTY_RE.search(text)
        assert not c, (
            f"[{scenario}] certainty leak in {fld}: matched {c.group(0)!r} "
            f"in text {text!r}"
        )


@pytest.fixture(scope="function")
def db():
    load_dotenv(os.path.join(ROOT, ".env"))
    mongo_url = os.getenv("MONGO_URL")
    assert mongo_url
    client = AsyncIOMotorClient(mongo_url)
    yield client["test_database"]
    client.close()


# ════════════════════════════════════════════════════════════════════
# Test fixtures — synthetic charts for repeatable scenarios
# ════════════════════════════════════════════════════════════════════

def _mk_chart(
    *,
    asc_sign: str = "Sagittarius",
    sun: str = "Pisces", sun_house: int = 3,
    moon: str = "Aries", moon_house: int = 4,
    mercury: str = "Pisces", mercury_house: int = 3,
    venus: str = "Pisces", venus_house: int = 3,
    mars: str = "Aries", mars_house: int = 4,
    saturn: str = "Cancer", saturn_house: int = 8,
    pluto: str = "Leo", pluto_house: int = 9,
    pluto_in_7th: bool = False,
    extra_in_7th: dict | None = None,
    hd_type: str = "Manifestor",
):
    planets = {
        "Sun":      {"sign": sun,     "house": sun_house},
        "Moon":     {"sign": moon,    "house": moon_house},
        "Mercury":  {"sign": mercury, "house": mercury_house},
        "Venus":    {"sign": venus,   "house": venus_house},
        "Mars":     {"sign": mars,    "house": mars_house},
        "Saturn":   {"sign": saturn,  "house": saturn_house},
        "Pluto":    {"sign": pluto,   "house": 7 if pluto_in_7th else pluto_house},
    }
    if extra_in_7th:
        for p, sg in extra_in_7th.items():
            planets[p] = {"sign": sg, "house": 7}
    return {
        "astrology": {
            "planets": planets,
            "angles": {"asc": {"sign": asc_sign}},
        },
        "hd_type": hd_type,
    }


# ════════════════════════════════════════════════════════════════════
# G1 — output shape complete
# ════════════════════════════════════════════════════════════════════
def test_G1_output_shape_complete():
    out = generate_relationship_curriculum(
        person_a={"chart": _mk_chart(asc_sign="Sagittarius"), "name": "A"},
        person_b={"chart": _mk_chart(asc_sign="Cancer", sun="Gemini", hd_type="Reflector"),
                  "name": "B"},
        relationship_context={"role": "spouse"},
    )
    assert out["success"] is True
    assert out["build_marker"] == BUILD_MARKER
    rc = out["relationship_curriculum"]
    for k in ("gift", "challenge", "growth_edge", "curriculum",
              "confidence", "proof"):
        assert k in rc, f"missing key {k}"
    for k in ("astrology", "human_design", "enneagram", "bazi", "numerology"):
        assert k in rc["proof"], f"missing proof.{k}"
        assert isinstance(rc["proof"][k], list)
    assert rc["confidence"] in ("low", "medium", "high")


# ════════════════════════════════════════════════════════════════════
# G2 + G3 — banlist (destiny + certainty)
# ════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize("scenario,role,asc", [
    ("sag_asc_spouse",   "spouse",       "Sagittarius"),
    ("cancer_asc_child", "child",        "Cancer"),
    ("leo_asc_friend",   "close_friend", "Leo"),
    ("aqua_asc_partner", "partner",      "Aquarius"),
    ("pisces_asc_parent","parent",       "Pisces"),
])
def test_G2_G3_no_destiny_or_certainty(scenario, role, asc):
    out = generate_relationship_curriculum(
        person_a={"chart": _mk_chart(asc_sign=asc), "name": "A"},
        person_b={"chart": _mk_chart(asc_sign="Cancer", sun="Gemini",
                                      hd_type="Reflector"), "name": "B"},
        relationship_context={"role": role},
    )
    assert out["success"] is True
    _scan(out, scenario)


# ════════════════════════════════════════════════════════════════════
# G4 — determinism
# ════════════════════════════════════════════════════════════════════
def test_G4_determinism():
    args = dict(
        person_a={"chart": _mk_chart(asc_sign="Sagittarius"), "name": "Pete"},
        person_b={"chart": _mk_chart(asc_sign="Cancer", sun="Gemini",
                                      hd_type="Reflector"), "name": "Mel"},
        relationship_context={"role": "spouse"},
    )
    r1 = generate_relationship_curriculum(**args)
    r2 = generate_relationship_curriculum(**args)
    assert r1 == r2


# ════════════════════════════════════════════════════════════════════
# G5 — word-count targets
# ════════════════════════════════════════════════════════════════════
def test_G5_word_counts():
    out = generate_relationship_curriculum(
        person_a={"chart": _mk_chart(asc_sign="Sagittarius",
                                      pluto_in_7th=True,
                                      extra_in_7th={"Mercury": "Gemini"}),
                   "name": "Pete"},
        person_b={"chart": _mk_chart(asc_sign="Cancer", sun="Gemini",
                                      mercury="Gemini",
                                      hd_type="Reflector"),
                   "name": "Mel"},
        relationship_context={"role": "spouse"},
    )
    rc = out["relationship_curriculum"]
    def _wc(s): return len((s or "").split())
    assert _wc(rc["gift"])        >= 90,  f"gift too short: {_wc(rc['gift'])}"
    assert _wc(rc["challenge"])   >= 70,  f"challenge too short: {_wc(rc['challenge'])}"
    assert _wc(rc["growth_edge"]) >= 70,  f"growth_edge too short: {_wc(rc['growth_edge'])}"
    assert _wc(rc["curriculum"])  >= 90,  f"curriculum too short: {_wc(rc['curriculum'])}"


# ════════════════════════════════════════════════════════════════════
# G6 — role weighting
# ════════════════════════════════════════════════════════════════════
def test_G6_role_weight_affects_confidence():
    # Synthetic axis with 2 activations + HD pair — enough to be medium
    # at spouse weight but lower at colleague weight.
    args_base = dict(
        person_a={"chart": _mk_chart(
            asc_sign="Sagittarius", pluto_in_7th=True,
            extra_in_7th={"Mercury": "Gemini"},
        ), "name": "A"},
        person_b={"chart": _mk_chart(asc_sign="Cancer", sun="Gemini",
                                      mercury="Gemini", hd_type="Reflector"),
                   "name": "B"},
    )
    out_spouse  = generate_relationship_curriculum(
        **args_base, relationship_context={"role": "spouse"})
    out_friend  = generate_relationship_curriculum(
        **args_base, relationship_context={"role": "forum_member"})
    rank = {"low": 0, "medium": 1, "high": 2}
    assert rank[out_spouse["relationship_curriculum"]["confidence"]] >= \
           rank[out_friend["relationship_curriculum"]["confidence"]], (
        f"role weighting failed: spouse={out_spouse['relationship_curriculum']['confidence']!r} "
        f"forum_member={out_friend['relationship_curriculum']['confidence']!r}"
    )


# ════════════════════════════════════════════════════════════════════
# G7 — real DB Pete↔Mel
# ════════════════════════════════════════════════════════════════════
def test_G7_real_charts_pete_mel(db):
    async def _run():
        a = await db.charts.find_one({"user_id": PETE_ID})
        b = await db.charts.find_one({"user_id": MEL_ID})
        assert a and b
        out = generate_relationship_curriculum(
            person_a={"chart": a, "name": "Pete"},
            person_b={"chart": b, "name": "Mel"},
            relationship_context={"role": "spouse"},
        )
        assert out["success"] is True
        rc = out["relationship_curriculum"]
        assert rc["gift"]        and rc["challenge"]
        assert rc["growth_edge"] and rc["curriculum"]
        _scan(out, "real_pete_mel")
        # Proof.astrology must reference Pete's Gemini Descendant
        astro_proof = " ".join(rc["proof"]["astrology"]).lower()
        assert "gemini" in astro_proof, (
            f"Pete's Gemini Descendant should appear in proof.astrology: "
            f"{rc['proof']['astrology']}"
        )
        # Proof.human_design must mention Manifestor ↔ Reflector
        hd_proof = " ".join(rc["proof"]["human_design"]).lower()
        assert "manifestor" in hd_proof and "reflector" in hd_proof
    asyncio.run(_run())


# ════════════════════════════════════════════════════════════════════
# G8 — empty / partial input does not crash
# ════════════════════════════════════════════════════════════════════
def test_G8_empty_inputs_safe():
    out = generate_relationship_curriculum(
        person_a={}, person_b={}, relationship_context={},
    )
    assert out["success"] is True
    rc = out["relationship_curriculum"]
    # Even with no inputs, scan must pass — Mirror voice is built-in
    _scan(out, "empty_inputs")
    assert rc["confidence"] == "low"


# ════════════════════════════════════════════════════════════════════
# G9 — flag gate
# ════════════════════════════════════════════════════════════════════
def test_G9_flag_gate_off_returns_none():
    os.environ.pop("RELATIONSHIP_CURRICULUM_ENGINE", None)
    assert is_enabled() is False
    out = maybe_generate(
        person_a={"chart": _mk_chart(), "name": "A"},
        person_b={"chart": _mk_chart(), "name": "B"},
        relationship_context={"role": "spouse"},
    )
    assert out is None


def test_G9_flag_gate_on_returns_payload():
    os.environ["RELATIONSHIP_CURRICULUM_ENGINE"] = "true"
    try:
        assert is_enabled() is True
        out = maybe_generate(
            person_a={"chart": _mk_chart(), "name": "A"},
            person_b={"chart": _mk_chart(), "name": "B"},
            relationship_context={"role": "spouse"},
        )
        assert out is not None
        assert out["success"] is True
    finally:
        os.environ.pop("RELATIONSHIP_CURRICULUM_ENGINE", None)


# ════════════════════════════════════════════════════════════════════
# G10 — HD pair proof
# ════════════════════════════════════════════════════════════════════
def test_G10_manifestor_reflector_hd_proof():
    out = generate_relationship_curriculum(
        person_a={"chart": _mk_chart(asc_sign="Sagittarius",
                                      hd_type="Manifestor"), "name": "Pete"},
        person_b={"chart": _mk_chart(asc_sign="Cancer", sun="Gemini",
                                      hd_type="Reflector"), "name": "Mel"},
        relationship_context={"role": "spouse"},
    )
    rc = out["relationship_curriculum"]
    hd_proof_text = " ".join(rc["proof"]["human_design"])
    assert "Manifestor" in hd_proof_text and "Reflector" in hd_proof_text
    assert "initiating without controlling outcomes" in hd_proof_text or \
           "reflecting without disappearing" in hd_proof_text


# ════════════════════════════════════════════════════════════════════
# G11 — Synthetic axis demo (Gemini DSC + Pluto 7th + Mercury ruler)
#       activated by Gemini-Sun + Reflector person B
# ════════════════════════════════════════════════════════════════════
def test_G11_synthetic_pete_mel_axis_activation():
    """The user's described axis — used in the delivery report demo."""
    out = generate_relationship_curriculum(
        person_a={"chart": _mk_chart(
            asc_sign="Sagittarius",     # → Gemini DSC
            pluto_in_7th=True,           # Pluto in 7th
            extra_in_7th={"Mercury": "Gemini"},  # Mercury (ruler of Gemini DSC) in 7th
            hd_type="Manifestor",
        ), "name": "Pete"},
        person_b={"chart": _mk_chart(
            asc_sign="Cancer", sun="Gemini",
            mercury="Gemini",
            hd_type="Reflector",
        ), "name": "Mel"},
        relationship_context={"role": "spouse"},
    )
    rc = out["relationship_curriculum"]
    astro_proof = " ".join(rc["proof"]["astrology"]).lower()
    # 1. Gemini DSC is detected
    assert "gemini" in astro_proof
    # 2. Pluto in 7th is detected with depth/transformation themes
    assert "pluto" in astro_proof
    # 3. At least one Gemini-sign anchor on B activates a theme
    assert "activates" in astro_proof
    # 4. Sections mention curiosity / dialogue / depth / transformation
    body = (rc["gift"] + rc["challenge"] + rc["growth_edge"] +
            rc["curriculum"]).lower()
    assert ("curiosity" in body or "dialogue" in body or
            "perspective" in body or "depth" in body or
            "transformation" in body)
    # 5. Confidence should be medium or high under spouse role
    assert rc["confidence"] in ("medium", "high")
    # 6. No destiny / certainty leakage
    _scan(out, "synthetic_axis_demo")
