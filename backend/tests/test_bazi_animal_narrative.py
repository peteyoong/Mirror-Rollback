"""test_bazi_animal_narrative.py — animal narrative tests
=========================================================
"""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.bazi_animal_narrative import compute_animal_narrative, NARRATIVE_VERSION


def test_clash_pair_explains_dynamic():
    out = compute_animal_narrative("Tiger", "Monkey", "Tiger", "Monkey", "A", "B")
    assert out is not None
    pair = out["pair_dynamic"]
    assert pair["tone"] == "clash"
    # Must EXPLAIN, not just name them
    assert len(pair["summary"]) > 60
    assert any(word in pair["summary"].lower() for word in ("instinct", "strategy", "leaps", "calculates"))


def test_harmony_pair_explains_dynamic():
    out = compute_animal_narrative("Snake", "Monkey", None, None, "A", "B")
    pair = out["pair_dynamic"]
    assert pair["tone"] == "harmony"
    assert "strategic" in pair["summary"].lower() or "resonance" in pair["summary"].lower()


def test_same_sign_pair():
    out = compute_animal_narrative("Rat", "Rat", "Rat", "Rat", "A", "B")
    assert out["pair_dynamic"]["tone"] == "same-sign"
    assert "blind spot" in out["pair_dynamic"]["summary"].lower()


def test_neutral_pair_explained():
    out = compute_animal_narrative("Rat", "Tiger", None, None, "A", "B")
    pair = out["pair_dynamic"]
    assert pair["tone"] == "neutral"
    assert "Rat meets Tiger" in pair["summary"]


def test_triad_block_same_triad():
    out = compute_animal_narrative("Rat", "Monkey", None, None)  # both in Water triad
    triad = out["triad_signal"]
    assert triad.get("element") == "Water"
    assert "Water" in triad["summary"]


def test_triad_block_cross_triad():
    out = compute_animal_narrative("Rat", "Rabbit", None, None)  # Water vs Wood
    triad = out["triad_signal"]
    assert "Water" in triad["summary"] and "Wood" in triad["summary"]


def test_inner_clash_uses_day_animals():
    out = compute_animal_narrative("Rat", "Tiger", "Tiger", "Monkey", "A", "B")
    inner = out["inner_dynamic"]
    assert inner["summary"]
    assert "private" in inner["summary"].lower()
    assert "Tiger" in inner["summary"] and "Monkey" in inner["summary"]


def test_returns_none_when_animals_missing():
    assert compute_animal_narrative("", "Rat") is None
    assert compute_animal_narrative("Rat", "") is None


def test_no_mystical_fatalism():
    forbidden = ("destined", "soulmate", "karmic", "fate", "destiny")
    out = compute_animal_narrative("Tiger", "Monkey", "Snake", "Pig", "A", "B")
    flat = str(out).lower()
    for term in forbidden:
        assert term not in flat, f"leaked '{term}': {flat}"


def test_version_marker_exposed():
    assert NARRATIVE_VERSION.startswith("bazi-animal-narrative")
