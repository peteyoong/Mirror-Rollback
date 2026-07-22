"""Tests for the Phase 2-lite Enneagram Relationship Engine
================================================================

Build marker: relationship-enneagram-lite-v1

Test groups (parity with numerology-lite):
  1. minimum core-type-only input returns all 5 v2_card fields
  2. hand-authored cell is used when available
  3. fallback cell works for unspecified pair
  4. directional-signal shape remains backward-compatible
  5. diagnostics emits cores, wings, centers, line_relationship
  6. forbidden language guard
  7. full sweep of 1..9 × 1..9 produces non-empty v2_card
  8. existing directional-signal hit rate remains ~100%

Snapshot pairs locked: 3↔7, 8↔5, 3↔6, 5↔5 (same-type), 8↔4 (fallback).
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

from services.relationship_enneagram_engine_lite import (
    ENGINE_VERSION,
    FORBIDDEN_TOKENS,
    HAND_AUTHORED,
    STRESS_LINE,
    SECURITY_LINE,
    TYPE_CENTER,
    compute_enneagram_relationship,
    find_forbidden_language,
)
from services.forum_hd_mapping import compute_enneagram_signals


# ── Fixtures ─────────────────────────────────────────────────────────
def _user(core=None, wing=None, instinct=None) -> Dict:
    """Build a minimal user dict with an enneagram_type field."""
    out: Dict = {}
    if core is not None:
        out["enneagram_type"] = core
    if wing is not None or instinct is not None:
        enn: Dict = {}
        if wing is not None:
            enn["inferred_wing"] = wing
        if instinct is not None:
            enn["enneagram_computed_details"] = {"instinctual_stack": instinct}
        out["enneagram"] = enn
    return out


# ─────────────────────────────────────────────────────────────────────
# 1. Minimum core-type-only input → all 5 v2_card fields present
# ─────────────────────────────────────────────────────────────────────
def test_minimum_core_only_returns_complete_v2_card():
    result = compute_enneagram_relationship(
        _user(core=4), _user(core=8),
        "Alpha", "Bravo",
    )
    assert result is not None
    card = result["v2_card"]
    expected = {"core_dynamic", "natural_strength", "growth_edge",
                "shadow_pattern", "repair_pathway"}
    assert set(card.keys()) == expected
    for k, v in card.items():
        assert isinstance(v, str) and len(v) > 10, f"{k} too short"


def test_returns_none_when_core_missing():
    assert compute_enneagram_relationship(_user(), _user(core=5), "A", "B") is None
    assert compute_enneagram_relationship(_user(core=5), _user(), "A", "B") is None
    assert compute_enneagram_relationship({}, {}, "A", "B") is None


def test_returns_none_when_core_invalid():
    # Out-of-range values should NOT produce a bogus card
    assert compute_enneagram_relationship(
        {"enneagram_type": 10}, {"enneagram_type": 4}, "A", "B"
    ) is None
    assert compute_enneagram_relationship(
        {"enneagram_type": 0}, {"enneagram_type": 4}, "A", "B"
    ) is None


# ─────────────────────────────────────────────────────────────────────
# 2. Hand-authored cells used when available
# ─────────────────────────────────────────────────────────────────────
def test_hand_authored_used_for_3x7_pair():
    result = compute_enneagram_relationship(
        _user(core=3), _user(core=7), "Alex", "Sam",
    )
    assert result is not None
    assert result["diagnostics"]["used_hand_authored"] is True
    text = " ".join(result["v2_card"].values()).lower()
    assert "achiever" in text
    assert "enthusiast" in text


def test_required_hand_authored_pairs_exist():
    """Ship-required coverage: all 9 same-type + key line-connected pairs."""
    required = [
        # Same-type coverage
        frozenset({1}), frozenset({2}), frozenset({3}), frozenset({4}),
        frozenset({5}), frozenset({6}), frozenset({7}), frozenset({8}),
        frozenset({9}),
        # High-signal line-connected + common cross-center pairs
        frozenset({3, 6}), frozenset({1, 7}), frozenset({5, 7}),
        frozenset({2, 8}), frozenset({4, 2}), frozenset({3, 9}),
        frozenset({8, 5}), frozenset({3, 7}), frozenset({4, 9}),
        frozenset({1, 9}), frozenset({6, 9}), frozenset({8, 9}),
        frozenset({5, 4}),
    ]
    for pair in required:
        assert pair in HAND_AUTHORED, f"missing hand-authored cell: {sorted(pair)}"


def test_hand_authored_same_type_pair():
    """Same-type hand-authored cell exists and reads like a double-lens."""
    result = compute_enneagram_relationship(
        _user(core=5), _user(core=5), "Eve", "Finn",
    )
    assert result is not None
    assert result["diagnostics"]["used_hand_authored"] is True
    card = result["v2_card"]
    assert "Two Investigators" in card["core_dynamic"]


# ─────────────────────────────────────────────────────────────────────
# 3. Fallback cell works for unspecified pair
# ─────────────────────────────────────────────────────────────────────
def test_fallback_used_for_unspecified_pair():
    # 8↔4 is NOT hand-authored — must compose via fallback.
    assert frozenset({8, 4}) not in HAND_AUTHORED
    result = compute_enneagram_relationship(
        _user(core=8), _user(core=4), "Cara", "Diane",
    )
    assert result is not None
    assert result["diagnostics"]["used_hand_authored"] is False
    card = result["v2_card"]
    assert "Challenger" in card["core_dynamic"]
    assert "Individualist" in card["core_dynamic"]
    # Fallback anchors in center-pair phrasing
    text = " ".join(card.values()).lower()
    assert "body" in text or "heart" in text


def test_fallback_uses_line_awareness_when_relevant():
    """5↔8 is hand-authored, so we use 4↔1 which sits on 1's stress line
    AND 4's security line — both directions."""
    assert frozenset({4, 1}) not in HAND_AUTHORED  # guard
    result = compute_enneagram_relationship(
        _user(core=4), _user(core=1), "Kate", "Liam",
    )
    assert result is not None
    diag = result["diagnostics"]
    assert diag["line_relationship"] is not None
    # Line-aware fallback references the line explicitly in repair
    assert "line" in result["v2_card"]["repair_pathway"].lower()


# ─────────────────────────────────────────────────────────────────────
# 4. Directional signals remain backward-compatible
# ─────────────────────────────────────────────────────────────────────
def test_directional_signals_preserved_after_v2_card_attached():
    result = compute_enneagram_signals(
        _user(core=3), _user(core=7), "Pete", "Sam",
    )
    assert result is not None
    # Legacy directional keys still emitted (at least one)
    has_directional = any(
        k in result for k in
        ("how_you_help_them", "how_they_help_you", "friction_pattern")
    )
    assert has_directional
    # Phase 2-lite additions are present:
    assert "v2_card" in result
    assert "diagnostics" in result
    # Existing consumer contract: legacy keys are lists of strings
    for k in ("how_you_help_them", "how_they_help_you", "friction_pattern"):
        if k in result:
            assert isinstance(result[k], list)
            for item in result[k]:
                assert isinstance(item, str)


# ─────────────────────────────────────────────────────────────────────
# 5. Diagnostics — cores, wings, centers, line_relationship, pair_type
# ─────────────────────────────────────────────────────────────────────
def test_diagnostics_complete_for_3x7():
    r = compute_enneagram_relationship(
        _user(core=3, wing=2), _user(core=7, wing=6), "Alex", "Sam",
    )
    d = r["diagnostics"]
    assert d["core_a"] == 3
    assert d["core_b"] == 7
    assert d["wing_a"] == 2
    assert d["wing_b"] == 6
    assert d["center_a"] == "Heart"
    assert d["center_b"] == "Head"
    assert d["center_pair"] == "heart-head"
    assert d["shared_center"] is False
    assert d["pair_type"].startswith("3x7-") or d["pair_type"].startswith("7x3-")
    assert d["engine_version"] == ENGINE_VERSION
    assert d["used_hand_authored"] is True


def test_diagnostics_line_relationship_stress():
    """8's stress line lands on 5.  Diagnostic must capture it."""
    r = compute_enneagram_relationship(
        _user(core=8), _user(core=5), "A", "B",
    )
    d = r["diagnostics"]
    assert d["line_relationship"] is not None
    assert "8_stress_to_5" in d["line_relationship"]


def test_diagnostics_line_relationship_security():
    """1's security line lands on 7.  Diagnostic must capture it."""
    r = compute_enneagram_relationship(
        _user(core=1), _user(core=7), "A", "B",
    )
    d = r["diagnostics"]
    assert d["line_relationship"] is not None
    assert "1_security_to_7" in d["line_relationship"]


def test_diagnostics_shared_center():
    """Both types in Body center → shared_center = True."""
    r = compute_enneagram_relationship(
        _user(core=8), _user(core=9), "A", "B",
    )
    d = r["diagnostics"]
    assert d["shared_center"] is True
    assert d["center_pair"] == "body-body"


def test_wing_extraction_from_string_style():
    """Accept '5w4' style wing strings."""
    r = compute_enneagram_relationship(
        {"enneagram_type": 5, "enneagram": {"inferred_wing": "5w4"}},
        _user(core=8),
        "A", "B",
    )
    assert r["diagnostics"]["wing_a"] == 4


def test_wing_returns_none_when_invalid():
    r = compute_enneagram_relationship(
        {"enneagram_type": 5, "enneagram": {"inferred_wing": "invalid"}},
        _user(core=8),
        "A", "B",
    )
    assert r["diagnostics"]["wing_a"] is None


# ─────────────────────────────────────────────────────────────────────
# 6. Forbidden language guard
# ─────────────────────────────────────────────────────────────────────
def test_find_forbidden_language_detects_each_token():
    for tok in FORBIDDEN_TOKENS:
        assert find_forbidden_language(f"this is {tok} for real") == [tok]


def test_find_forbidden_language_clean_on_mirror_phrases():
    clean = "Pattern meets pattern; translation handles friction; small repair"
    assert find_forbidden_language(clean) == []


def test_no_forbidden_language_in_any_hand_authored_cell():
    for pair, cell in HAND_AUTHORED.items():
        for field, text in cell.items():
            bad = find_forbidden_language(text)
            assert not bad, f"forbidden token in {sorted(pair)}/{field}: {bad}"


def test_no_forbidden_language_in_full_1_through_9_sweep():
    """Compose every core-a × core-b pair; scan every field."""
    for a in range(1, 10):
        for b in range(1, 10):
            r = compute_enneagram_relationship(
                _user(core=a), _user(core=b), "Alpha", "Bravo",
            )
            assert r is not None, f"None for {a}↔{b}"
            for field, text in r["v2_card"].items():
                bad = find_forbidden_language(text)
                assert not bad, f"forbidden token at {a}x{b}/{field}: {bad}"


# ─────────────────────────────────────────────────────────────────────
# 7. Full 9x9 sweep — v2_card always complete for valid cores
# ─────────────────────────────────────────────────────────────────────
def test_full_9x9_sweep_v2_card_complete():
    expected = {"core_dynamic", "natural_strength", "growth_edge",
                "shadow_pattern", "repair_pathway"}
    for a in range(1, 10):
        for b in range(1, 10):
            r = compute_enneagram_relationship(
                _user(core=a), _user(core=b), "A", "B",
            )
            assert r is not None
            assert set(r["v2_card"].keys()) == expected, (
                f"missing keys for {a}↔{b}: {expected - r['v2_card'].keys()}"
            )
            for field, text in r["v2_card"].items():
                assert isinstance(text, str) and len(text) > 20, (
                    f"{a}↔{b}/{field} too short"
                )


# ─────────────────────────────────────────────────────────────────────
# 8. Enneagram_source canonical resolver honoured
# ─────────────────────────────────────────────────────────────────────
def test_resolves_from_nested_inferred_core():
    """User doc with only enneagram.inferred_core should resolve."""
    r = compute_enneagram_relationship(
        {"enneagram": {"inferred_core": 3}},
        {"enneagram_type": 7},
        "Pete", "Sam",
    )
    assert r is not None
    assert r["diagnostics"]["core_a"] == 3
    assert r["diagnostics"]["core_b"] == 7


def test_resolves_from_legacy_scalar():
    """User doc with only legacy enneagram scalar should resolve."""
    r = compute_enneagram_relationship(
        {"enneagram": 5},
        {"enneagram_type": 8},
        "Pete", "Sam",
    )
    assert r is not None
    assert r["diagnostics"]["core_a"] == 5


# ─────────────────────────────────────────────────────────────────────
# Line-map integrity checks (guardrails on the Enneagram data)
# ─────────────────────────────────────────────────────────────────────
def test_stress_and_security_lines_symmetry_property():
    """Every type's stress line target is another type's security-line
    inverse (Enneagram symbol property).  This catches typos."""
    for t in range(1, 10):
        stress_target = STRESS_LINE[t]
        # Stress from t lands on security target of some type; the pair
        # (t, stress_target) must have SECURITY_LINE[stress_target] == t
        # This is the canonical Enneagram inversion property.
        assert SECURITY_LINE[stress_target] == t, (
            f"line inversion broken for type {t}: stress→{stress_target}, "
            f"security({stress_target}) = {SECURITY_LINE[stress_target]}, expected {t}"
        )


def test_type_center_covers_all_nine():
    for t in range(1, 10):
        assert TYPE_CENTER[t] in {"Body", "Heart", "Head"}


# ─────────────────────────────────────────────────────────────────────
# 9. DB sweep — v2_card always populated on real user pairs
# ─────────────────────────────────────────────────────────────────────
def test_db_sweep_v2_card_when_both_types_present():
    from motor.motor_asyncio import AsyncIOMotorClient
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BACKEND, ".env"))

    async def _run():
        client = AsyncIOMotorClient(os.getenv("MONGO_URL"))
        db = client[os.getenv("DB_NAME", "test_database")]
        users = await db.users.find({}).to_list(length=None)
        try:
            from services.enneagram_source import get_user_enneagram
        except Exception:
            from enneagram_source import get_user_enneagram  # type: ignore
        typed = [u for u in users if get_user_enneagram(u)][:40]
        pairs = list(combinations(typed, 2))[:200]
        failures: List[str] = []
        for a, b in pairs:
            r = compute_enneagram_relationship(
                a, b,
                a.get("name", "A"), b.get("name", "B"),
            )
            if not r:
                failures.append(f"None for {a.get('name')}↔{b.get('name')}")
                continue
            keys = set(r["v2_card"].keys())
            need = {"core_dynamic", "natural_strength", "growth_edge",
                    "shadow_pattern", "repair_pathway"}
            missing = need - keys
            if missing:
                failures.append(
                    f"{a.get('name')}↔{b.get('name')}: missing {missing}"
                )
        client.close()
        return len(pairs), failures

    total, failures = asyncio.run(_run())
    if total == 0:
        # DB has no Enneagram-typed users; skip gracefully rather than fail
        return
    assert not failures, (
        f"v2_card incomplete in {len(failures)}/{total} pairs. "
        f"First: {failures[:3]}"
    )


# ─────────────────────────────────────────────────────────────────────
# Snapshot tests — signature phrases locked
# ─────────────────────────────────────────────────────────────────────
def test_snapshot_3x7_signature_phrases():
    r = compute_enneagram_relationship(
        _user(core=3), _user(core=7), "Pete", "Sam",
    )
    card = r["v2_card"]
    assert "Achiever" in card["core_dynamic"]
    assert "Enthusiast" in card["core_dynamic"]
    assert "finish" in card["repair_pathway"].lower()


def test_snapshot_8x5_signature_phrases():
    r = compute_enneagram_relationship(
        _user(core=8), _user(core=5), "Pete", "Rae",
    )
    card = r["v2_card"]
    assert "Challenger" in card["core_dynamic"]
    assert "Investigator" in card["core_dynamic"]
    assert "stress line" in card["core_dynamic"].lower()


def test_snapshot_3x6_signature_phrases():
    r = compute_enneagram_relationship(
        _user(core=3), _user(core=6), "Pete", "Kim",
    )
    card = r["v2_card"]
    assert "Achiever" in card["core_dynamic"]
    assert "Loyalist" in card["core_dynamic"]
    # 3 and 6 sit on each other's stress/security line — signature reference
    assert "line" in card["core_dynamic"].lower()


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
