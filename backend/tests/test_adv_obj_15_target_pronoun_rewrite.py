"""ADV-OBJ-15 — Target-only proof-block pronoun rewrite.

Locks in the behaviour that when `chart_owner_name=<name>` is passed
to either builder, the instruction templates that previously said
`'Your <Object> sits at …'` become `'<name>'s <Object> sits at …'`.

This is what fixes the LLM hallucination on Forum-tab target-only
queries like "Tell me about Mel's Juno" — the instruction template
now unambiguously refers to Mel, so the LLM has nothing to resolve.

We only test the proof-block-level rewrite; the routing decision
that decides WHEN to pass `chart_owner_name` is covered by
tests/test_adv_obj_13_pairwise_bridge.py.
"""
from __future__ import annotations

import re

from services.mirror_object_interpreter import build_mirror_object_proof_block
from services.natal_object_engine import build_natal_object_proof_block


# Helper used everywhere — must match the shape compute_natal_object
# returns for a successful Juno computation.
def _juno_envelope():
    return {
        "object": "Juno",
        "success": True,
        "placement": {
            "sign":   "Virgo",
            "house":  3,
            "degree": 29.5,
        },
        "source": "swisseph_on_demand",
    }


def _vertex_envelope():
    return {
        "object": "Vertex",
        "success": True,
        "placement": {
            "sign":   "Pisces",
            "house":  9,
            "degree": 15.2,
        },
        "source": "swisseph_on_demand",
    }


def _north_node_envelope():
    return {
        "object": "North Node",
        "success": True,
        "placement": {
            "sign":   "Leo",
            "house":  5,
            "degree": 11.0,
        },
        "source": "swisseph_on_demand",
    }


# ---------------------------------------------------------------------
# 1. Self case (chart_owner_name=None) — unchanged behaviour
# ---------------------------------------------------------------------
def test_mirror_block_self_case_uses_your():
    block = build_mirror_object_proof_block(_juno_envelope())
    assert "Your Juno sits at" in block
    assert "'s Juno sits at" not in block


def test_natal_block_self_case_uses_your():
    block = build_natal_object_proof_block(_juno_envelope())
    # mirror block routing kicks in for Juno (has_mirror_interpretation),
    # so we still get the mirror-style "Your Juno sits at" text
    assert "Your Juno sits at" in block
    assert "'s Juno sits at" not in block


# ---------------------------------------------------------------------
# 2. Target case (chart_owner_name="Mel") — rewrite kicks in
# ---------------------------------------------------------------------
def test_mirror_block_target_case_uses_mels():
    block = build_mirror_object_proof_block(
        _juno_envelope(), chart_owner_name="Mel"
    )
    assert "Mel's Juno sits at" in block
    assert "Your Juno sits at" not in block


def test_natal_block_target_case_uses_mels():
    block = build_natal_object_proof_block(
        _juno_envelope(), chart_owner_name="Mel"
    )
    assert "Mel's Juno sits at" in block
    assert "Your Juno sits at" not in block


def test_vertex_target_case_uses_mels():
    block = build_mirror_object_proof_block(
        _vertex_envelope(), chart_owner_name="Mel"
    )
    assert "Mel's Vertex sits at" in block
    assert "Your Vertex sits at" not in block


def test_north_node_multiword_object_target_case():
    block = build_mirror_object_proof_block(
        _north_node_envelope(), chart_owner_name="Mel"
    )
    assert "Mel's North Node sits at" in block
    assert "Your North Node sits at" not in block


# ---------------------------------------------------------------------
# 3. Universal voice floor is NOT touched
# ---------------------------------------------------------------------
def test_universal_voice_floor_pronouns_unchanged():
    block_self  = build_mirror_object_proof_block(_juno_envelope())
    block_mel   = build_mirror_object_proof_block(
        _juno_envelope(), chart_owner_name="Mel"
    )
    # The universal voice floor uses they/them/their/this person —
    # those tokens must appear in BOTH variants verbatim.  We pick
    # phrases from _UNIVERSAL_VOICE_FLOOR that are highly unique.
    for marker in (
        "WHAT HAPPENS",
        "OBSERVABLE SIGNAL",
        "2nd person",
    ):
        assert marker in block_self
        assert marker in block_mel


# ---------------------------------------------------------------------
# 4. Empty / falsy chart_owner_name is a no-op
# ---------------------------------------------------------------------
def test_empty_chart_owner_name_is_no_op():
    a = build_mirror_object_proof_block(_juno_envelope(), chart_owner_name="")
    b = build_mirror_object_proof_block(_juno_envelope(), chart_owner_name=None)
    c = build_mirror_object_proof_block(_juno_envelope())
    assert a == b == c
    assert "Your Juno sits at" in a


# ---------------------------------------------------------------------
# 5. Apostrophe handling — name itself contains an apostrophe
# ---------------------------------------------------------------------
def test_chart_owner_name_with_apostrophe():
    block = build_mirror_object_proof_block(
        _juno_envelope(), chart_owner_name="D'Angelo"
    )
    assert "D'Angelo's Juno sits at" in block


# ---------------------------------------------------------------------
# 6. Anti-Vertex (hyphenated) survives the rewrite
# ---------------------------------------------------------------------
def test_anti_vertex_hyphenated_object_target_case():
    av_env = {
        "object": "Anti-Vertex",
        "success": True,
        "placement": {"sign": "Pisces", "house": 3, "degree": 3.0},
        "source": "swisseph_on_demand",
    }
    block = build_mirror_object_proof_block(av_env, chart_owner_name="Mel")
    assert "Mel's Anti-Vertex sits at" in block
    # Crucially must NOT bleed into a bare 'Vertex sits at'
    bare_vertex = re.search(r"\bMel's Vertex sits at\b", block)
    assert bare_vertex is None


# ---------------------------------------------------------------------
# 7. Failure envelope still returns a usable block (no crash, no rewrite)
# ---------------------------------------------------------------------
def test_failure_envelope_unaffected():
    fail = {
        "object": "Juno",
        "success": False,
        "reason": "missing_birth_time",
        "message": "Juno requires a birth time.",
    }
    block_self = build_natal_object_proof_block(fail)
    block_mel  = build_natal_object_proof_block(fail, chart_owner_name="Mel")
    # build_mirror_object_proof_block returns "" for failure envelopes,
    # so build_natal_object_proof_block falls through to its own
    # failure block — which never contains "Your X sits at" anyway.
    assert "engine_message" in block_self
    assert "engine_message" in block_mel
