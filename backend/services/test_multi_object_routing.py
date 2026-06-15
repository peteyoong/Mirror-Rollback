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


# ----------------------------------------------------------------------
# ADV-OBJ-12 — Anti-Vertex must not also resolve the bare "Vertex" token
# that sits inside the hyphenated word.
# ----------------------------------------------------------------------
def test_anti_vertex_does_not_dual_resolve_vertex():
    """'Tell me about my Anti-Vertex' must NOT produce two proof blocks.
    The shorter, embedded `\\bvertex\\b` match must be suppressed when
    it falls inside the Anti-Vertex span."""
    for q in (
        "Tell me about my Anti-Vertex",
        "Tell me about my anti-vertex",
        "what does my anti vertex mean",
        "my AntiVertex",   # no hyphen variant
    ):
        intent = classify_astrology_intent(q)
        assert intent and intent["data_mode"] == "natal_object", q
        objs = intent.get("objects") or []
        assert objs == ["Anti-Vertex"], (
            f"ADV-OBJ-12 regression: query {q!r} returned {objs!r} — "
            "must contain ONLY 'Anti-Vertex', not also 'Vertex'."
        )
        assert intent.get("multi") is False, q


def test_anti_vertex_plus_vertex_explicit_still_returns_both():
    """If the user EXPLICITLY says both, both must surface (no over-suppression)."""
    intent = classify_astrology_intent(
        "Tell me about my Anti-Vertex and my Vertex."
    )
    assert intent and intent["data_mode"] == "natal_object"
    objs = intent.get("objects") or []
    # Both ends present; user wrote them as distinct tokens.
    assert "Anti-Vertex" in objs
    assert "Vertex" in objs
    assert intent.get("multi") is True


def test_bare_vertex_still_resolves():
    """Bare Vertex queries continue to work (no false suppression)."""
    intent = classify_astrology_intent("Tell me about my Vertex")
    assert intent and intent["data_mode"] == "natal_object"
    assert intent.get("objects") == ["Vertex"]
    assert intent.get("multi") is False
