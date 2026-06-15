"""Multi-object natal-object routing — astrology-chat-multi-object-v1.

Verifies the dispatcher returns a list of canonical objects (not just
the first match) when the user references more than one body, and tags
the NN/SN pair as an axis.
"""
from __future__ import annotations

from services.astrology_chat_router import classify_astrology_intent


def test_single_object_returns_legacy_shape():
    intent = classify_astrology_intent("Tell me about my Ceres.")
    assert intent and intent["data_mode"] == "natal_object"
    assert intent["object"] == "Ceres"
    assert intent.get("objects") == ["Ceres"]
    assert intent.get("multi") is False
    assert intent.get("axis") is None


def test_ceres_vesta_pairwise():
    intent = classify_astrology_intent(
        "What do Ceres and Vesta reveal about my work and relationships?"
    )
    assert intent and intent["data_mode"] == "natal_object"
    objs = intent.get("objects") or []
    assert "Ceres" in objs and "Vesta" in objs
    assert intent.get("multi") is True
    assert intent.get("axis") is None
    # Legacy `object` field is the FIRST canonical name encountered
    assert intent["object"] == objs[0]


def test_north_south_node_axis():
    intent = classify_astrology_intent(
        "How do my North Node and South Node interact?"
    )
    assert intent and intent["data_mode"] == "natal_object"
    objs = intent.get("objects") or []
    assert "North Node" in objs and "South Node" in objs
    assert intent.get("multi") is True
    assert intent.get("axis") == "nodal"


def test_north_south_node_axis_explicit_together():
    intent = classify_astrology_intent(
        "What do my North Node and South Node mean together?"
    )
    assert intent and intent["data_mode"] == "natal_object"
    assert intent.get("axis") == "nodal"
    assert "North Node" in intent["objects"]
    assert "South Node" in intent["objects"]


def test_nodes_plural_expands_to_both_ends():
    """Bare 'my nodes' should expand to both NN + SN as an axis query."""
    intent = classify_astrology_intent("Tell me about my nodes.")
    assert intent and intent["data_mode"] == "natal_object"
    objs = intent.get("objects") or []
    assert "North Node" in objs
    assert "South Node" in objs
    assert intent.get("axis") == "nodal"


def test_three_object_query():
    """Three bodies in one query → all three returned, pairwise (no axis)."""
    intent = classify_astrology_intent(
        "Tell me about my Ceres, Pallas, and Vesta."
    )
    assert intent and intent["data_mode"] == "natal_object"
    objs = intent.get("objects") or []
    for nm in ("Ceres", "Pallas", "Vesta"):
        assert nm in objs
    assert intent.get("multi") is True
    assert intent.get("axis") is None


def test_rahu_ketu_aliases_to_nodal_axis():
    """Vedic node names (Rahu/Ketu) also resolve into the nodal axis."""
    intent = classify_astrology_intent("How do my Rahu and Ketu interact?")
    assert intent and intent["data_mode"] == "natal_object"
    objs = intent.get("objects") or []
    assert "North Node" in objs and "South Node" in objs
    assert intent.get("axis") == "nodal"
