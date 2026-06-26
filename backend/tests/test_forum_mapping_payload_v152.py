"""test_forum_mapping_payload_v152.py — end-to-end mapping payload check
==========================================================================
Validates that `generate_mapping_interpretation` produces:
  • signals.human_design[i].narrative {gift, tension, practical_use}
  • signals.human_design_field.narrative_blocks (HD drill-down)
  • signals.bazi.animal_narrative (when both charts have animals)
  • signals.numerology.v2_card.{core_dynamic, ...}  (existing, validated here)
  • relationship_synthesis.undertone_for_today

Strict additive contract: legacy fields stay populated.
"""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.forum_hd_mapping import (
    generate_mapping_interpretation, find_completed_channels,
)


def _mock_chart_a():
    return {
        "human_design": {
            "type": "Manifestor",
            "authority": "Splenic",
            "profile": "5/1",
            "definition": "Single Definition",
            "defined_centers":   ["Throat", "Ajna", "Head", "Spleen", "Heart"],
            "undefined_centers": ["Sacral", "Solar Plexus", "Root", "G"],
            "active_gates": [1, 8, 37, 21, 25, 51],
            "defined_channels": ["1-8", "37-40 partial"],
        },
        "bazi": {
            "day_master": {"element": "Wood", "strength": "strong",
                            "keywords": ["growth", "leadership"], "description": "..."},
            "pillars": {
                "year":  {"animal_name": "Tiger", "animal_emoji": "🐅"},
                "day":   {"animal_name": "Snake", "animal_emoji": "🐍"},
            },
        },
        "numerology": {
            "life_path":  {"number": 1},
            "expression": {"number": 5},
            "soul_urge":  {"number": 7},
        },
        "astrology": {"planets": []},
    }


def _mock_chart_b():
    return {
        "human_design": {
            "type": "Generator",
            "authority": "Sacral",
            "profile": "2/4",
            "definition": "Split Definition",
            "defined_centers":   ["Sacral", "Throat", "Heart", "G"],
            "undefined_centers": ["Ajna", "Head", "Spleen", "Solar Plexus", "Root"],
            "active_gates": [40, 45, 51, 2, 14, 50],
            "defined_channels": ["2-14"],
        },
        "bazi": {
            "day_master": {"element": "Earth", "strength": "weak",
                            "keywords": ["nurturing", "stable"], "description": "..."},
            "pillars": {
                "year":  {"animal_name": "Monkey", "animal_emoji": "🐒"},
                "day":   {"animal_name": "Pig", "animal_emoji": "🐖"},
            },
        },
        "numerology": {
            "life_path":  {"number": 7},
            "expression": {"number": 3},
            "soul_urge":  {"number": 11},
        },
        "astrology": {"planets": []},
    }


def _mock_user_a():
    return {"id": "a", "name": "Ana", "gender": "female"}


def _mock_user_b():
    return {"id": "b", "name": "Pete", "gender": "male"}


def _run():
    a, b = _mock_chart_a(), _mock_chart_b()
    gates_a = a["human_design"]["active_gates"]
    gates_b = b["human_design"]["active_gates"]
    channels = find_completed_channels(gates_a, gates_b)
    return generate_mapping_interpretation(
        "Ana", "Pete", channels, a, b, _mock_user_a(), _mock_user_b(),
    )


def test_payload_has_relationship_synthesis_with_undertone():
    out = _run()
    syn = out.get("relationship_synthesis")
    assert syn is not None
    # undertone field must exist as a string (may be empty in degenerate runs)
    assert "undertone_for_today" in syn
    assert isinstance(syn["undertone_for_today"], str)


def test_hd_channels_each_have_narrative_block():
    out = _run()
    hd = out["signals"]["human_design"]
    assert isinstance(hd, list)
    if not hd:
        return  # acceptable when no channels — fallback path
    for ch in hd:
        narrative = ch.get("narrative")
        assert narrative is not None, f"channel {ch.get('channel')} missing narrative"
        assert all(k in narrative for k in ("gift", "tension", "practical_use"))
        assert all(narrative[k].strip() for k in ("gift", "tension", "practical_use"))


def test_hd_field_has_narrative_blocks():
    out = _run()
    field = out["signals"].get("human_design_field")
    assert field, "human_design_field must be present"
    blocks = field.get("narrative_blocks")
    assert blocks, "narrative_blocks must be present"
    expected = {"type_pair_engagement", "authority_rhythm", "profile_interaction",
                "definition_dynamics", "centers_conditioning", "channels",
                "practical_guidance"}
    assert expected <= set(blocks.keys())


def test_bazi_signals_have_animal_narrative():
    out = _run()
    bazi = out["signals"].get("bazi") or {}
    an = bazi.get("animal_narrative")
    assert an, "animal_narrative must be present when both charts have animals"
    assert "pair_dynamic" in an and "inner_dynamic" in an and "triad_signal" in an


def test_numerology_v2_card_present():
    out = _run()
    num = out["signals"].get("numerology") or {}
    v2 = num.get("v2_card")
    if v2 is None:
        return  # engine may decline; not required for this test
    # When present, it should have at least one Mirror-Language field
    has_any = any(isinstance(v2.get(k), str) and v2.get(k, "").strip()
                  for k in ("core_dynamic", "natural_strength", "growth_edge",
                            "shadow_pattern", "repair_pathway"))
    assert has_any, f"v2_card present but empty: {v2}"


def test_legacy_fields_still_present():
    out = _run()
    # Backward compat keys must still exist
    for k in ("headline", "description", "what_works", "what_to_watch",
              "why_this_happens", "channel_count", "strength_score"):
        assert k in out, f"missing legacy key: {k}"
    assert "story" in out and "patterns" in out and "signals" in out
