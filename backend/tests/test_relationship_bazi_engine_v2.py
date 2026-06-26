"""Tests for the Phase 3 BaZi Relationship Engine V2
====================================================

Build marker: relationship-bazi-engine-v2

Covers the lens-parity contract:
  1. v2_card carries all 6 new keys (natural_strength, repair_pathway,
     current_movement, how_they_help_each_other,
     how_they_challenge_each_other, current_relationship_season)
  2. Existing wisdom-v3 keys (core_dynamic, what_strengthens,
     growth_edge, shadow_pattern, why_matters, what_bazi_sees) remain
  3. diagnostics carries all new dimensional fields
  4. Bridge element correctly computed for every control cycle
  5. Ten-Gods role-casting deterministic for all 5×5 element pairs
  6. Animal relations cover same / clash / harmony / triad / harm /
     punishment / neutral
  7. Forbidden-language guard catches all listed tokens
  8. Backward compatibility — existing v2_card keys + diagnostics
     fields are NOT removed when v2 layer is merged in
  9. Pete↔Mel, Pete↔Isaac, Pete↔Thaddeus snapshot
"""
from __future__ import annotations

import asyncio
import datetime as _dt
import os
import sys
from typing import Any, Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(HERE)
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

from services.relationship_bazi_engine_v2 import (
    ANIMAL_CLASHES, ANIMAL_HARMONIES, ANIMAL_TRIADS,
    ANIMAL_HARMS, ANIMAL_PUNISHMENTS,
    BRIDGE_ELEMENT, BRIDGE_BEHAVIOUR,
    CONTROLS, PRODUCES,
    ENGINE_VERSION, FORBIDDEN_TOKENS,
    _animal_relation, _cycle, _bridge, _polarity_relation,
    _ten_gods_a_sees_b, _current_annual_pillar,
    enrich_bazi_relationship, find_forbidden_language,
)


# ── Fixtures: real Pete / Mel / Isaac / Thaddeus shapes ──────────────
PETE_CHART = {
    "bazi": {
        "day_master": {"element": "Metal", "polarity": "Yin"},
        "pillars": {
            "year": {"animal_name": "Ox"},
            "day":  {"animal_name": "Ox", "hidden_stems": ["己", "癸", "辛"]},
        },
    },
}

MEL_CHART = {
    "bazi": {
        "day_master": {"element": "Water", "polarity": "Yang"},
        "pillars": {
            "year": {"animal_name": "Rooster"},
            "day":  {"animal_name": "Pig", "hidden_stems": ["甲", "壬"]},
        },
    },
}

ISAAC_CHART = {
    "bazi": {
        "day_master": {"element": "Fire", "polarity": "Yang"},
        "pillars": {
            "year": {"animal_name": "Rabbit"},
            "day":  {"animal_name": "Tiger", "hidden_stems": ["甲", "丙", "戊"]},
        },
    },
}

THADDEUS_CHART = {
    "bazi": {
        "day_master": {"element": "Wood", "polarity": "Yang"},
        "pillars": {
            "year": {"animal_name": "Goat"},
            "day":  {"animal_name": "Goat", "hidden_stems": ["己", "丁", "乙"]},
        },
    },
}


# ─────────────────────────────────────────────────────────────────────
# 1. v2_card carries all 6 new keys
# ─────────────────────────────────────────────────────────────────────
def test_v2_card_emits_all_six_new_keys():
    r = enrich_bazi_relationship(PETE_CHART, MEL_CHART, "Pete", "Mel")
    assert r is not None
    expected = {
        "natural_strength", "repair_pathway", "current_movement",
        "how_they_help_each_other", "how_they_challenge_each_other",
        "current_relationship_season",
    }
    assert set(r["v2_card"].keys()) == expected
    for k, v in r["v2_card"].items():
        assert isinstance(v, str) and len(v) > 10, f"{k} empty/short: {v!r}"


def test_returns_none_when_element_missing():
    assert enrich_bazi_relationship({}, MEL_CHART, "A", "B") is None
    assert enrich_bazi_relationship(PETE_CHART, {}, "A", "B") is None
    assert enrich_bazi_relationship({"bazi":{"day_master":{}}},
                                    MEL_CHART, "A", "B") is None


# ─────────────────────────────────────────────────────────────────────
# 2. diagnostics carries all dimensional fields
# ─────────────────────────────────────────────────────────────────────
def test_diagnostics_emits_all_required_fields():
    r = enrich_bazi_relationship(PETE_CHART, MEL_CHART, "Pete", "Mel")
    d = r["diagnostics"]
    required = [
        "day_master_relation", "ten_gods_a_sees_b", "ten_gods_b_sees_a",
        "animal_relation_year", "animal_relation_day",
        "hidden_stem_relation", "yin_yang_relation", "bridge_element",
        "luck_pillar_relation", "current_annual_pillar", "engine_version",
    ]
    for k in required:
        assert k in d, f"diagnostics missing key: {k}"
    assert d["engine_version"] == ENGINE_VERSION


# ─────────────────────────────────────────────────────────────────────
# 3. Bridge element correctness for every control cycle
# ─────────────────────────────────────────────────────────────────────
def test_bridge_element_for_every_control_cycle():
    # Every (controller, controlled) pair produces a deterministic bridge
    # which is the element controller PRODUCES that ALSO PRODUCES controlled.
    for (a, b), bridge in BRIDGE_ELEMENT.items():
        assert PRODUCES[a] == bridge, f"{a}→{bridge} broken"
        assert PRODUCES[bridge] == b, f"{bridge}→{b} broken"


def test_bridge_returned_only_for_control_cycles():
    # Wood controls Earth → bridge Fire
    assert _bridge("Wood", "Earth", "a_controls_b") == "Fire"
    # Earth controlled by Wood → from B side
    assert _bridge("Earth", "Wood", "b_controls_a") == "Fire"
    # Production cycle → no bridge
    assert _bridge("Wood", "Fire",  "a_produces_b") is None
    # Same element → no bridge
    assert _bridge("Metal", "Metal", "same") is None


def test_bridge_behaviour_table_complete():
    for el in ("Wood", "Fire", "Earth", "Metal", "Water"):
        assert el in BRIDGE_BEHAVIOUR


# ─────────────────────────────────────────────────────────────────────
# 4. Ten Gods role-casting for all 5×5 element pairs
# ─────────────────────────────────────────────────────────────────────
def test_ten_gods_role_casting_complete_for_25_pairs():
    elements = ("Wood", "Fire", "Earth", "Metal", "Water")
    valid_roles = {"Resource", "Wealth", "Officer", "Companion", "Output"}
    for ea in elements:
        for eb in elements:
            role = _ten_gods_a_sees_b(ea, eb)
            assert role in valid_roles, f"{ea}↔{eb} produced bad role: {role!r}"


def test_ten_gods_resource_and_output_are_inverse():
    # If B produces A (B is A's Resource), then A produces B is Output
    # from B's perspective.  Same axis, opposite direction.
    assert _ten_gods_a_sees_b("Metal", "Earth") == "Resource"  # Earth → Metal
    assert _ten_gods_a_sees_b("Earth", "Metal") == "Output"
    assert _ten_gods_a_sees_b("Metal", "Wood")  == "Wealth"    # Metal controls Wood
    assert _ten_gods_a_sees_b("Wood",  "Metal") == "Officer"   # Wood is controlled by Metal


# ─────────────────────────────────────────────────────────────────────
# 5. Animal relations cover all 7 categories
# ─────────────────────────────────────────────────────────────────────
def test_animal_relations_all_categories():
    assert _animal_relation("Rat", "Rat")      == "same"
    assert _animal_relation("Rat", "Horse")    == "clash"
    assert _animal_relation("Rat", "Ox")       == "harmony"
    assert _animal_relation("Rat", "Dragon")   == "triad"      # Rat-Dragon-Monkey
    assert _animal_relation("Rat", "Goat")     == "harm"
    assert _animal_relation("Rat", "Rabbit")   == "punishment"
    assert _animal_relation("Rat", "Tiger")    == "neutral"
    assert _animal_relation("", "Tiger")       == "unknown"


def test_animal_tables_are_well_formed():
    assert len(ANIMAL_CLASHES)   == 6
    assert len(ANIMAL_HARMONIES) == 6
    assert len(ANIMAL_TRIADS)    == 4
    assert len(ANIMAL_HARMS)     == 6


# ─────────────────────────────────────────────────────────────────────
# 6. Forbidden-language guard
# ─────────────────────────────────────────────────────────────────────
def test_forbidden_language_detection():
    for tok in FORBIDDEN_TOKENS:
        assert find_forbidden_language(f"sentence with {tok} inside") == [tok]


def test_no_forbidden_language_in_any_engine_output():
    # Sweep every element pair × every polarity combo.
    elements = ("Wood", "Fire", "Earth", "Metal", "Water")
    polarities = ("Yang", "Yin")
    for ea in elements:
        for eb in elements:
            for pa in polarities:
                for pb in polarities:
                    chart_a = {"bazi":{"day_master":{"element":ea, "polarity":pa},
                                       "pillars":{"year":{"animal_name":"Rat"},
                                                  "day":{"animal_name":"Ox",
                                                         "hidden_stems":["甲"]}}}}
                    chart_b = {"bazi":{"day_master":{"element":eb, "polarity":pb},
                                       "pillars":{"year":{"animal_name":"Horse"},
                                                  "day":{"animal_name":"Goat",
                                                         "hidden_stems":["乙"]}}}}
                    r = enrich_bazi_relationship(chart_a, chart_b, "Alpha", "Bravo")
                    assert r is not None
                    for field, text in r["v2_card"].items():
                        bad = find_forbidden_language(text)
                        assert not bad, f"forbidden token at {ea}/{pa}↔{eb}/{pb}/{field}: {bad}"


# ─────────────────────────────────────────────────────────────────────
# 7. Backward compatibility — orchestrator merge preserves v3 keys
# ─────────────────────────────────────────────────────────────────────
def test_orchestrator_merge_preserves_legacy_keys():
    """Simulate the orchestrator merge: existing v2_card has v3 keys,
    v2 enrichment adds new keys without overwriting any existing."""
    # Existing v3 card
    legacy_card = {
        "core_dynamic":     "v3 core",
        "what_strengthens": "v3 strengths",
        "growth_edge":      "v3 growth",
        "shadow_pattern":   "v3 shadow",
        "why_matters":      "v3 meaning",
        "what_bazi_sees":   "v3 integrated",
    }
    v2 = enrich_bazi_relationship(PETE_CHART, MEL_CHART, "Pete", "Mel")
    merged = dict(legacy_card)
    for k, v in v2["v2_card"].items():
        if k not in merged:
            merged[k] = v
    # All 12 keys must coexist (6 legacy + 6 new — but
    # `growth_edge` and `shadow_pattern` already in v3, so v2 prose
    # for those is the v3 version preserved; v2-only keys add 4 more)
    expected_keys = (
        {"core_dynamic","what_strengthens","growth_edge","shadow_pattern","why_matters","what_bazi_sees"}
        | {"natural_strength","repair_pathway","current_movement",
           "how_they_help_each_other","how_they_challenge_each_other",
           "current_relationship_season"}
    )
    assert set(merged.keys()) == expected_keys
    # Legacy prose preserved verbatim
    for k, v in legacy_card.items():
        assert merged[k] == v


# ─────────────────────────────────────────────────────────────────────
# 8. DB sweep — v2_card complete on every valid chart pair
# ─────────────────────────────────────────────────────────────────────
def test_db_sweep_v2_card_always_complete():
    from itertools import combinations
    from motor.motor_asyncio import AsyncIOMotorClient
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BACKEND, ".env"))

    async def _run():
        client = AsyncIOMotorClient(os.getenv("MONGO_URL"))
        db = client[os.getenv("DB_NAME","test_database")]
        users = await db.users.find({}).to_list(length=None)
        charts = {}
        for u in users:
            c = await db.charts.find_one({"user_id": str(u["_id"])})
            if not c: continue
            bazi = c.get("bazi") or {}
            if (bazi.get("day_master") or {}).get("element"):
                charts[str(u["_id"])] = c
        usable = list(charts.values())[:30]
        pairs = list(combinations(usable, 2))[:200]
        ok = 0; bad: List[str] = []
        for a, b in pairs:
            r = enrich_bazi_relationship(a, b, "A", "B")
            if not r: bad.append("None"); continue
            if set(r["v2_card"].keys()) != {
                "natural_strength","repair_pathway","current_movement",
                "how_they_help_each_other","how_they_challenge_each_other",
                "current_relationship_season"}:
                bad.append(f"missing keys: {set(r['v2_card'].keys())}")
                continue
            ok += 1
        client.close()
        return ok, len(pairs), bad

    ok, total, bad = asyncio.run(_run())
    assert not bad, f"v2_card incomplete: {bad[:3]}"
    assert ok == total, f"only {ok}/{total} pairs ok"


# ─────────────────────────────────────────────────────────────────────
# 9. Snapshot — Pete↔Mel / Pete↔Isaac / Pete↔Thaddeus
# ─────────────────────────────────────────────────────────────────────
def test_snapshot_pete_mel_signatures():
    r = enrich_bazi_relationship(PETE_CHART, MEL_CHART, "Pete", "Mel")
    c, d = r["v2_card"], r["diagnostics"]
    # Pete=Metal, Mel=Water: Metal produces Water → a_produces_b
    assert d["ten_gods_a_sees_b"] == "Output"   # Metal produces Water → Mel is Pete's Output
    assert d["ten_gods_b_sees_a"] == "Resource" # Water produced by Metal → Pete is Mel's Resource
    assert d["bridge_element"] is None          # No control cycle, no bridge
    assert "Metal naturally nourishes" in c["natural_strength"]
    assert "Mel" in c["how_they_help_each_other"]
    assert "Pete" in c["how_they_help_each_other"]


def test_snapshot_pete_isaac_signatures():
    r = enrich_bazi_relationship(PETE_CHART, ISAAC_CHART, "Pete", "Isaac")
    c, d = r["v2_card"], r["diagnostics"]
    # Pete=Metal, Isaac=Fire: Fire controls Metal → b_controls_a
    assert d["ten_gods_a_sees_b"] == "Officer"  # Fire controls Metal → Isaac is Pete's Officer
    assert d["ten_gods_b_sees_a"] == "Wealth"   # Metal controlled by Fire → Pete is Isaac's Wealth
    assert d["bridge_element"] == "Earth"       # Fire→Earth→Metal
    assert "Earth behaviour" in c["repair_pathway"]
    assert "control axis" in c["natural_strength"].lower() or "honesty under pressure" in c["natural_strength"].lower()


def test_snapshot_pete_thaddeus_signatures():
    r = enrich_bazi_relationship(PETE_CHART, THADDEUS_CHART, "Pete", "Thaddeus")
    c, d = r["v2_card"], r["diagnostics"]
    # Pete=Metal, Thaddeus=Wood: Metal controls Wood → a_controls_b
    assert d["ten_gods_a_sees_b"] == "Wealth"   # Metal controls Wood → Thaddeus is Pete's Wealth
    assert d["ten_gods_b_sees_a"] == "Officer"  # Wood controlled by Metal → Pete is Thaddeus's Officer
    assert d["bridge_element"] == "Water"       # Metal→Water→Wood
    assert "Water behaviour" in c["repair_pathway"]
    assert "listening" in c["repair_pathway"].lower()


# ─────────────────────────────────────────────────────────────────────
# 10. Annual pillar deterministic
# ─────────────────────────────────────────────────────────────────────
def test_current_annual_pillar_deterministic_2026():
    # 2026 - 4 = 2022; 2022 % 10 = 2 → 丙 (Fire-Yang); 2022 % 12 = 6 → 午 (Horse-Fire)
    p = _current_annual_pillar(today=_dt.date(2026, 6, 26))
    assert p["year"]     == 2026
    assert p["stem"]     == "丙"
    assert p["branch"]   == "午"
    assert p["animal"]   == "Horse"
    assert p["stem_element"]   == "Fire"
    assert p["stem_polarity"]  == "Yang"


def test_lichun_boundary_pre_feb_4():
    # Jan 2026 should still resolve to 2025-year pillar
    p = _current_annual_pillar(today=_dt.date(2026, 1, 15))
    assert p["year"] == 2025


# ─────────────────────────────────────────────────────────────────────
# 11. Cycle classification deterministic
# ─────────────────────────────────────────────────────────────────────
def test_cycle_classification_table():
    assert _cycle("Wood",  "Fire")  == "a_produces_b"
    assert _cycle("Fire",  "Wood")  == "b_produces_a"
    assert _cycle("Metal", "Wood")  == "a_controls_b"
    assert _cycle("Wood",  "Metal") == "b_controls_a"
    assert _cycle("Earth", "Earth") == "same"
    assert _cycle("",      "Fire")  == "neutral"


# ─────────────────────────────────────────────────────────────────────
# Script runner
# ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import traceback
    passed = failed = 0
    for name in sorted(globals()):
        if not name.startswith("test_"): continue
        fn = globals()[name]
        try:
            fn()
            print(f"  PASS  {name}")
            passed += 1
        except Exception:
            print(f"  FAIL  {name}")
            traceback.print_exc()
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    raise SystemExit(0 if not failed else 1)
