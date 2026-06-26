"""Tests for the Phase 2-lite Numerology Relationship Engine
================================================================

Build marker: relationship-numerology-lite-v1

Eight required test groups:
  1. minimum life-path-only input returns all 5 v2_card fields
  2. hand-authored cell is used when available
  3. fallback cell works for unspecified pair
  4. themes remains backward-compatible
  5. diagnostics emits life paths, pair_type, shared_numbers,
     master_number_flags
  6. forbidden language guard
  7. 200-pair sweep produces non-empty v2_card for all valid life-
     path pairs
  8. existing Phase 1 hit-rate remains ~100%

Snapshot pairs locked: Pete↔Mel, Pete↔Isaac, Pete↔Thaddeus.
"""
from __future__ import annotations

import asyncio
import os
import sys
from itertools import combinations
from typing import Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(HERE)
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

from services.relationship_numerology_engine_lite import (
    ARCHETYPES,
    FORBIDDEN_TOKENS,
    HAND_AUTHORED,
    compute_numerology_relationship,
    find_forbidden_language,
)
from services.forum_hd_mapping import compute_numerology_signals


# ── Fixtures ─────────────────────────────────────────────────────────
def _num(life_path=None, expression=None, soul_urge=None,
         personality=None, birthday=None) -> Dict:
    """Build a minimal numerology dict in the chart shape."""
    out: Dict = {}
    if life_path   is not None: out["life_path"]   = {"number": life_path}
    if expression  is not None: out["expression"]  = {"number": expression}
    if soul_urge   is not None: out["soul_urge"]   = {"number": soul_urge}
    if personality is not None: out["personality"] = {"number": personality}
    if birthday    is not None: out["birthday"]    = {"number": birthday}
    return out


def _chart(num_dict) -> Dict:
    """Wrap a numerology dict in a chart-style envelope."""
    return {"numerology": num_dict}


PETE_NUM     = _num(life_path=11, expression=1)
MEL_NUM      = _num(life_path=3,  birthday=4)
ISAAC_NUM    = _num(life_path=5,  birthday=5)
THADDEUS_NUM = _num(life_path=9,  birthday=5)


# ─────────────────────────────────────────────────────────────────────
# 1. Minimum life-path-only input → all 5 v2_card fields present
# ─────────────────────────────────────────────────────────────────────
def test_minimum_life_path_only_returns_complete_v2_card():
    result = compute_numerology_relationship(
        _num(life_path=4), _num(life_path=7),
        "Alpha", "Bravo",
    )
    assert result is not None, "engine should not return None when both LP present"
    card = result["v2_card"]
    expected_keys = {"core_dynamic", "natural_strength", "growth_edge",
                     "shadow_pattern", "repair_pathway"}
    assert set(card.keys()) == expected_keys, f"missing keys: {expected_keys - card.keys()}"
    for k, v in card.items():
        assert isinstance(v, str) and len(v) > 10, f"{k} is empty/too short"


def test_returns_none_when_life_path_missing():
    assert compute_numerology_relationship(_num(), _num(life_path=5), "A", "B") is None
    assert compute_numerology_relationship(_num(life_path=5), _num(), "A", "B") is None
    assert compute_numerology_relationship({}, {}, "A", "B") is None


# ─────────────────────────────────────────────────────────────────────
# 2. Hand-authored cell used when pair is in table
# ─────────────────────────────────────────────────────────────────────
def test_hand_authored_cell_used_for_11x3_pair():
    # Pete (LP=11) ↔ Mel (LP=3) — must use hand-authored 11↔3 cell.
    result = compute_numerology_relationship(PETE_NUM, MEL_NUM, "Pete", "Mel")
    assert result is not None
    card = result["v2_card"]
    # Hand-authored cell signature phrases (Mirror-tone, distinct from fallback):
    assert "Inner Knower" in card["core_dynamic"]
    assert "Voice"        in card["core_dynamic"]
    assert "Pause"        in card["repair_pathway"]
    assert result["diagnostics"]["used_hand_authored"] is True


def test_hand_authored_cells_exist_for_required_pairs():
    """Spec requires at minimum: 11↔3, 11↔5, 11↔9, 3↔5, 4↔8, 2↔7."""
    required = [
        frozenset({11, 3}), frozenset({11, 5}), frozenset({11, 9}),
        frozenset({3, 5}),  frozenset({4, 8}),  frozenset({2, 7}),
    ]
    for pair in required:
        assert pair in HAND_AUTHORED, f"required hand-authored cell missing: {sorted(pair)}"


# ─────────────────────────────────────────────────────────────────────
# 3. Fallback cell works for unspecified pair
# ─────────────────────────────────────────────────────────────────────
def test_fallback_used_for_unspecified_pair():
    # LP=6 ↔ LP=8 is NOT hand-authored — must compose via fallback.
    assert frozenset({6, 8}) not in HAND_AUTHORED  # guard
    result = compute_numerology_relationship(
        _num(life_path=6), _num(life_path=8),
        "Cara", "Diane",
    )
    assert result is not None
    assert result["diagnostics"]["used_hand_authored"] is False
    card = result["v2_card"]
    # Fallback uses archetype labels from both sides:
    assert "Caretaker" in card["core_dynamic"]  # LP=6 archetype
    assert "Steward"   in card["core_dynamic"]  # LP=8 archetype


def test_fallback_same_life_path():
    """LP_a == LP_b uses the same-rhythm fallback branch."""
    result = compute_numerology_relationship(
        _num(life_path=7), _num(life_path=7),
        "Eve", "Finn",
    )
    assert result is not None
    card = result["v2_card"]
    # Same-rhythm branch always emits "same rhythm" or "recognise each other"
    text = " ".join(card.values()).lower()
    assert "same rhythm" in text or "recognise each other" in text


# ─────────────────────────────────────────────────────────────────────
# 4. themes remains backward-compatible
# ─────────────────────────────────────────────────────────────────────
def test_themes_field_preserved_after_v2_card_attached():
    result = compute_numerology_signals(
        _chart(PETE_NUM), _chart(MEL_NUM), "Pete", "Mel",
    )
    assert result is not None
    assert "themes" in result
    assert isinstance(result["themes"], list)
    assert len(result["themes"]) >= 1
    # Phase 2-lite additions are present:
    assert "v2_card" in result
    assert "diagnostics" in result


# ─────────────────────────────────────────────────────────────────────
# 5. diagnostics emits life paths, pair_type, shared_numbers, master flags
# ─────────────────────────────────────────────────────────────────────
def test_diagnostics_complete_for_pete_mel():
    result = compute_numerology_relationship(PETE_NUM, MEL_NUM, "Pete", "Mel")
    diag = result["diagnostics"]
    assert diag["life_path_a"] == 11
    assert diag["life_path_b"] == 3
    assert diag["pair_type"].startswith("3x11-") or diag["pair_type"].startswith("11x3-")
    # Pete's LP=11 is a master number — must be flagged
    assert any("life_path=11" in f for f in diag["master_number_flags"])
    assert isinstance(diag["shared_numbers"], list)


def test_shared_numbers_correctly_intersected():
    # Both have life_path=5 — shared_numbers must contain 5
    result = compute_numerology_relationship(
        _num(life_path=5, expression=2),
        _num(life_path=5, birthday=7),
        "A", "B",
    )
    assert 5 in result["diagnostics"]["shared_numbers"]
    # 2 and 7 each only on one side — must NOT be shared
    assert 2 not in result["diagnostics"]["shared_numbers"]
    assert 7 not in result["diagnostics"]["shared_numbers"]


def test_master_number_flags_for_both_sides():
    result = compute_numerology_relationship(
        _num(life_path=11, expression=22),
        _num(life_path=33),
        "A", "B",
    )
    flags = result["diagnostics"]["master_number_flags"]
    # a:life_path=11, a:expression=22, b:life_path=33 — all 3 expected
    assert any("a:life_path=11"  in f for f in flags)
    assert any("a:expression=22" in f for f in flags)
    assert any("b:life_path=33"  in f for f in flags)


# ─────────────────────────────────────────────────────────────────────
# 6. Forbidden language guard
# ─────────────────────────────────────────────────────────────────────
def test_find_forbidden_language_detects_each_token():
    for tok in FORBIDDEN_TOKENS:
        assert find_forbidden_language(f"this is {tok} for real") == [tok]


def test_find_forbidden_language_clean_on_mirror_phrases():
    clean = "Rhythm meets pacing; translation handles friction; repair pathway"
    assert find_forbidden_language(clean) == []


def test_no_forbidden_language_in_any_hand_authored_cell():
    for pair, cell in HAND_AUTHORED.items():
        for field, text in cell.items():
            bad = find_forbidden_language(text)
            assert not bad, f"forbidden token in {sorted(pair)}/{field}: {bad}"


def test_no_forbidden_language_in_compositional_fallback_sweep():
    """Compose every (a, b) combo of 1..9 + masters; scan all 5 fields."""
    keys = [1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 22, 33]
    for a in keys:
        for b in keys:
            result = compute_numerology_relationship(
                _num(life_path=a), _num(life_path=b),
                "Alpha", "Bravo",
            )
            assert result is not None
            for field, text in result["v2_card"].items():
                bad = find_forbidden_language(text)
                assert not bad, f"forbidden token at LP {a}x{b}/{field}: {bad}"


# ─────────────────────────────────────────────────────────────────────
# 7. 200-pair DB sweep — v2_card always populated when LP valid
# ─────────────────────────────────────────────────────────────────────
def test_db_sweep_v2_card_always_complete():
    """Pull real charts, run 200 pairs, assert every v2_card has 5 keys."""
    from motor.motor_asyncio import AsyncIOMotorClient
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BACKEND, ".env"))

    async def _run():
        client = AsyncIOMotorClient(os.getenv("MONGO_URL"))
        db = client[os.getenv("DB_NAME", "test_database")]
        users = await db.users.find({}).to_list(length=None)
        charts = {}
        for u in users:
            c = await db.charts.find_one({"user_id": str(u["_id"])})
            if c: charts[str(u["_id"])] = c
        valid = [
            u for u in users
            if str(u["_id"]) in charts
            and (charts[str(u["_id"])].get("numerology", {}) or {})
                  .get("life_path", {}).get("number")
        ][:50]
        pairs = list(combinations(valid, 2))[:200]
        all_complete = True
        sample_failures: List[str] = []
        for a, b in pairs:
            r = compute_numerology_relationship(
                charts[str(a["_id"])].get("numerology", {}),
                charts[str(b["_id"])].get("numerology", {}),
                a.get("name", "A"), b.get("name", "B"),
            )
            if not r: all_complete = False; sample_failures.append(f"None for {a.get('name')}↔{b.get('name')}"); continue
            card = r["v2_card"]
            if set(card.keys()) != {"core_dynamic", "natural_strength",
                                     "growth_edge", "shadow_pattern",
                                     "repair_pathway"}:
                all_complete = False
                sample_failures.append(f"{a.get('name')}↔{b.get('name')}: keys={list(card.keys())}")
        client.close()
        return all_complete, len(pairs), sample_failures

    ok, n, failures = asyncio.run(_run())
    assert ok, f"v2_card incomplete in {len(failures)}/{n} pairs.  First: {failures[:3]}"
    assert n >= 100, f"only {n} pairs sampled; expected 200"


# ─────────────────────────────────────────────────────────────────────
# 8. Phase 1 hit rate remains ~100% with Phase 2-lite stacked on top
# ─────────────────────────────────────────────────────────────────────
def test_phase1_hit_rate_unchanged_with_v2_card_enrichment():
    """compute_numerology_signals must still return non-None themes
    for ≥99% of pairs with usable life_path."""
    from motor.motor_asyncio import AsyncIOMotorClient
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BACKEND, ".env"))

    async def _run():
        client = AsyncIOMotorClient(os.getenv("MONGO_URL"))
        db = client[os.getenv("DB_NAME", "test_database")]
        users = await db.users.find({}).to_list(length=None)
        charts = {}
        for u in users:
            c = await db.charts.find_one({"user_id": str(u["_id"])})
            if c: charts[str(u["_id"])] = c
        valid = [
            u for u in users
            if str(u["_id"]) in charts
            and (charts[str(u["_id"])].get("numerology", {}) or {})
                  .get("life_path", {}).get("number")
        ][:50]
        pairs = list(combinations(valid, 2))[:200]
        hits = 0
        for a, b in pairs:
            r = compute_numerology_signals(
                charts[str(a["_id"])], charts[str(b["_id"])],
                a.get("name", "A"), b.get("name", "B"),
            )
            if r and r.get("themes"):
                hits += 1
        client.close()
        return hits, len(pairs)

    hits, total = asyncio.run(_run())
    assert hits / total >= 0.99, f"hit rate dropped to {hits}/{total}"


# ─────────────────────────────────────────────────────────────────────
# Snapshot tests (locked but semantic — not byte-exact)
# ─────────────────────────────────────────────────────────────────────
def test_snapshot_pete_mel_signature_phrases():
    r = compute_numerology_relationship(PETE_NUM, MEL_NUM, "Pete", "Mel")
    card = r["v2_card"]
    # Signature phrases that LOCK the 11↔3 hand-authored prose:
    assert "Inner Knower" in card["core_dynamic"]
    assert "Voice"        in card["core_dynamic"]
    assert "translate"    in card["natural_strength"].lower()
    assert "silence"      in card["growth_edge"].lower()
    assert "Pause"        in card["repair_pathway"]


def test_snapshot_pete_isaac_signature_phrases():
    r = compute_numerology_relationship(PETE_NUM, ISAAC_NUM, "Pete", "Isaac")
    card = r["v2_card"]
    assert "Inner Knower" in card["core_dynamic"]
    assert "Disrupter"    in card["core_dynamic"]
    assert "motion"       in card["natural_strength"].lower()
    assert "still"        in card["growth_edge"].lower()
    assert "one direction" in card["repair_pathway"]


def test_snapshot_pete_thaddeus_signature_phrases():
    r = compute_numerology_relationship(PETE_NUM, THADDEUS_NUM, "Pete", "Thaddeus")
    card = r["v2_card"]
    assert "Inner Knower" in card["core_dynamic"]
    assert "Releaser"     in card["core_dynamic"]
    assert "released"     in card["shadow_pattern"].lower() or "release" in card["shadow_pattern"].lower()
    assert "closed"       in card["repair_pathway"].lower()


# ─────────────────────────────────────────────────────────────────────
# Script-mode runner — pytest-free quick check
# ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import traceback
    passed = failed = 0
    names = [n for n in sorted(globals()) if n.startswith("test_")]
    for name in names:
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
