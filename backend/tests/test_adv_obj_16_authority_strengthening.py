"""ADV-OBJ-16 — Proof-block authority strengthening.

Locks in:
  (A) Placeholder pre-substitution:
        `{SIGN_PLACEMENT}` → e.g. "29°Virgo"
        `{N}`              → e.g. "3"
      The LLM never sees template variables.

  (B) Authoritative-placement footer that explicitly tells the LLM
      not to substitute a different sign / degree / house from upstream
      context blocks (FKR member tables, planet listings, etc.).

Both are critical for the Forum-tab target-only path
("Tell me about Mel's Juno") which was hallucinating "15° Cancer"
because Mel's chart contains several Cancer placements that bled
through the FKR block.
"""
from __future__ import annotations

from services.mirror_object_interpreter import build_mirror_object_proof_block
from services.natal_object_engine import build_natal_object_proof_block


def _juno_env():
    return {
        "object": "Juno",
        "success": True,
        "placement": {"sign": "Virgo", "house": 3, "degree": 29.5},
        "source": "swisseph_on_demand",
    }


def _vertex_env():
    return {
        "object": "Vertex",
        "success": True,
        "placement": {"sign": "Pisces", "house": 9, "degree": 15.2},
        "source": "swisseph_on_demand",
    }


def _nn_env():
    return {
        "object": "North Node",
        "success": True,
        "placement": {"sign": "Leo", "house": 5, "degree": 11.0},
        "source": "swisseph_on_demand",
    }


def _anti_vertex_env():
    return {
        "object": "Anti-Vertex",
        "success": True,
        "placement": {"sign": "Virgo", "house": 3, "degree": 15.2},
        "source": "swisseph_on_demand",
    }


# ---------------------------------------------------------------------
# (A) Placeholder substitution
# ---------------------------------------------------------------------
def test_sign_placement_placeholder_substituted_juno():
    block = build_mirror_object_proof_block(_juno_env())
    assert "{SIGN_PLACEMENT}" not in block
    assert "{N}" not in block
    # the literal interpolated values must be present
    assert "29°Virgo" in block
    assert "in the 3th house" in block or "in the 3rd house" in block or "in the 3 " in block  # any of the literal substitutions


def test_sign_placement_placeholder_substituted_vertex():
    block = build_mirror_object_proof_block(_vertex_env())
    assert "{SIGN_PLACEMENT}" not in block
    assert "{N}" not in block
    assert "15°Pisces" in block
    # The instruction template now embeds the placement instead of `{SIGN_PLACEMENT}`
    assert "Your Vertex sits at 15°Pisces in the 9" in block


def test_sign_placement_placeholder_substituted_north_node():
    block = build_mirror_object_proof_block(_nn_env())
    assert "{SIGN_PLACEMENT}" not in block
    assert "{N}" not in block
    assert "11°Leo" in block
    assert "Your North Node sits at 11°Leo in the 5" in block


def test_target_name_and_placeholder_substitution_combine():
    """ADV-OBJ-15 (pronoun) + ADV-OBJ-16 (placeholder) must both apply."""
    block = build_mirror_object_proof_block(
        _juno_env(), chart_owner_name="Mel"
    )
    assert "Mel's Juno sits at 29°Virgo in the 3" in block
    assert "Your Juno sits at" not in block
    assert "{SIGN_PLACEMENT}" not in block


def test_anti_vertex_placeholder_substitution():
    block = build_mirror_object_proof_block(
        _anti_vertex_env(), chart_owner_name="Mel"
    )
    assert "Mel's Anti-Vertex sits at 15°Virgo in the 3" in block
    assert "{SIGN_PLACEMENT}" not in block
    # Bleed check
    assert block.count("Vertex") == block.count("Anti-Vertex")


# ---------------------------------------------------------------------
# (B) Authority footer
# ---------------------------------------------------------------------
def test_authority_footer_present_in_mirror_block_self():
    block = build_mirror_object_proof_block(_juno_env())
    assert "AUTHORITATIVE PLACEMENT" in block
    assert "Juno: 29°Virgo, house 3" in block
    assert "do not contradict" in block
    assert "do not substitute" in block


def test_authority_footer_present_in_mirror_block_target():
    block = build_mirror_object_proof_block(
        _juno_env(), chart_owner_name="Mel"
    )
    assert "AUTHORITATIVE PLACEMENT" in block
    assert "Juno: 29°Virgo, house 3" in block
    # The footer should name the specific object so the LLM cannot
    # generalise.
    assert "If you discuss Juno" in block


def test_authority_footer_mentions_fkr_explicitly():
    """The footer must explicitly tell the LLM to ignore FKR/member tables."""
    block = build_mirror_object_proof_block(_juno_env())
    assert "FKR" in block
    assert "member tables" in block or "planet listings" in block


def test_authority_footer_in_natal_engine_block():
    """The generic-fallback path also gets an authority footer."""
    # Use an envelope that does NOT have a Mirror block — but
    # has_mirror_interpretation returns True for known objects, so we
    # synthesise an unknown object name to force the fallback.
    env = {
        "object": "Eros",
        "success": True,
        "placement": {"sign": "Aries", "house": 7, "degree": 4.1},
        "source": "swisseph_on_demand",
    }
    block = build_natal_object_proof_block(env)
    assert "AUTHORITATIVE PLACEMENT" in block
    assert "Eros: 4°Aries, house 7" in block


def test_self_case_no_target_pronoun_change_but_authority_present():
    """Self case: no name swap, but the authority footer is still
    present so the LLM doesn't hallucinate on multi-context prompts."""
    block = build_mirror_object_proof_block(_juno_env())
    assert "Your Juno sits at 29°Virgo in the 3" in block
    assert "AUTHORITATIVE PLACEMENT" in block


# ---------------------------------------------------------------------
# Defensive — empty/failure cases must not crash
# ---------------------------------------------------------------------
def test_empty_envelope_returns_empty_block():
    assert build_mirror_object_proof_block({}) == ""


def test_failure_envelope_returns_empty_block():
    env = {"object": "Juno", "success": False, "reason": "missing_birth_time"}
    assert build_mirror_object_proof_block(env) == ""


def test_no_house_placement_does_not_crash():
    env = {
        "object": "Juno",
        "success": True,
        "placement": {"sign": "Virgo", "house": None, "degree": 29.5},
        "source": "swisseph_on_demand",
    }
    block = build_mirror_object_proof_block(env, chart_owner_name="Mel")
    # Substitution still runs; "{N}" is replaced with "?"
    assert "{N}" not in block
    assert "Mel's Juno sits at" in block
