"""
Tests for Phase-2 Mirror Object Interpretation Layer.

Build marker: mirror-interpretation-layer-v1
"""
from __future__ import annotations

import pytest

from services.mirror_object_interpreter import (
    BUILD_MARKER,
    has_mirror_interpretation,
    build_mirror_object_proof_block,
)
from services.natal_object_engine import build_natal_object_proof_block


# ----------------------------------------------------------------------
# Coverage of Mirror-interpreted objects
# ----------------------------------------------------------------------
@pytest.mark.parametrize("name,expected", [
    ("Vertex", True),
    ("Anti-Vertex", True),
    ("Juno", True),
    ("Chiron", True),
    ("Black Moon Lilith", True),
    ("True Black Moon Lilith", True),       # alias → Black Moon Lilith
    ("Lot of Fortune", True),
    ("Lot of Spirit", True),
    ("Pholus", True),
    # T2 additions — mirror-interpretation-layer-v1.1
    ("Ceres", True),
    ("Pallas", True),
    ("Vesta", True),
    ("North Node", True),
    ("South Node", True),
    # T2 corroboration bodies — mirror-interpretation-layer-v1.2-t2
    ("Eros", True),
    ("Psyche", True),
    ("Astraea", True),
    ("Hygiea", True),
    # Not Mirror-wrapped — fall back to generic block
    ("Sun", False),
    ("", False),
])
def test_has_mirror_interpretation(name, expected):
    assert has_mirror_interpretation(name) is expected


# ----------------------------------------------------------------------
# Block-shape contract
# ----------------------------------------------------------------------
def _make_envelope(object_name, sign="Virgo", house=9, lon=142.12):
    return {
        "success": True,
        "object": object_name,
        "build_marker": "test",
        "placement": {
            "sign": sign,
            "degree": 0.5,
            "formatted": f"0°{sign}",
            "longitude": lon,
            "house": house,
            "body_type": "angle",
            "source": "test",
        },
    }


@pytest.mark.parametrize("object_name", [
    "Vertex", "Anti-Vertex", "Juno", "Chiron",
    "Black Moon Lilith", "Lot of Fortune", "Lot of Spirit", "Pholus",
    # T2 corroboration bodies — must obey the same block-shape contract
    "Eros", "Psyche", "Astraea", "Hygiea",
])
def test_mirror_block_contains_placement_and_voice_floor(object_name):
    env = _make_envelope(object_name)
    block = build_mirror_object_proof_block(env)
    assert block, f"Mirror block empty for {object_name}"
    assert "MIRROR INTERPRETATION" in block
    assert object_name in block or "Black Moon Lilith" in block
    assert "Mirror question" in block
    assert "VOICE FLOOR" in block
    # Placement must surface inside the block
    assert "0°Virgo" in block
    # Each block must publish its build marker for trace
    assert BUILD_MARKER in block


# ----------------------------------------------------------------------
# Object-specific ban lists
# ----------------------------------------------------------------------
def test_chiron_block_bans_victim_language():
    block = build_mirror_object_proof_block(_make_envelope("Chiron"))
    # Bans must surface in the prompt so the LLM sees them
    for forbidden in ("deep wound", "core wound", "trauma response"):
        assert forbidden in block.lower(), (
            f"Chiron block missing victim-ban for {forbidden!r}"
        )


def test_lilith_block_bans_fear_language():
    block = build_mirror_object_proof_block(_make_envelope("Black Moon Lilith"))
    for forbidden in ("shadow work", "scary", "be careful"):
        assert forbidden in block.lower()


def test_juno_block_bans_soulmate_language():
    block = build_mirror_object_proof_block(_make_envelope("Juno"))
    for forbidden in ("soulmate", "twin flame", "fated to marry"):
        assert forbidden in block.lower()


def test_vertex_block_bans_destiny_language():
    block = build_mirror_object_proof_block(_make_envelope("Vertex"))
    for forbidden in ("fated meeting", "destined to meet", "karmic appointment"):
        assert forbidden in block.lower()


def test_fortune_block_bans_luck_language():
    block = build_mirror_object_proof_block(_make_envelope("Lot of Fortune"))
    for forbidden in ("luck", "destiny", "manifestation"):
        assert forbidden in block.lower()


def test_spirit_block_bans_purpose_cliches():
    block = build_mirror_object_proof_block(_make_envelope("Lot of Spirit"))
    for forbidden in ("soul purpose", "ascension", "destiny"):
        assert forbidden in block.lower()


# ----------------------------------------------------------------------
# True Lilith aliases to Black Moon Lilith block
# ----------------------------------------------------------------------
def test_true_lilith_aliases_to_lilith_block():
    block_bml = build_mirror_object_proof_block(_make_envelope("Black Moon Lilith"))
    block_tru = build_mirror_object_proof_block(_make_envelope("True Black Moon Lilith"))
    # Same instruction set (just the object label differs in the header).
    # Stable Lilith-block markers (voice-floor-v3): Mirror question +
    # "stop apologising" closing seed.
    for marker in ("refuses domestication",):
        assert marker.lower() in block_bml.lower()
        assert marker.lower() in block_tru.lower()
    # And both must contain the per-object ban list signature (Lilith-specific).
    assert "shadow work" in block_bml.lower()
    assert "shadow work" in block_tru.lower()


# ----------------------------------------------------------------------
# Integration: natal_object_engine routes Phase-2 objects to Mirror block
# ----------------------------------------------------------------------
def test_natal_object_engine_uses_mirror_block_for_vertex():
    env = _make_envelope("Vertex")
    block = build_natal_object_proof_block(env)
    assert "MIRROR INTERPRETATION" in block
    assert "Which encounters carry unusual weight" in block


def test_natal_object_engine_uses_mirror_block_for_juno():
    env = _make_envelope("Juno")
    block = build_natal_object_proof_block(env)
    assert "MIRROR INTERPRETATION" in block
    assert "What does commitment actually look like" in block


def test_natal_object_engine_falls_back_to_generic_for_non_mirror_object():
    # T2 bodies (Eros / Psyche / Astraea / Hygiea) are NOW Mirror-wrapped,
    # so they no longer demonstrate the generic-fallback path.  We use the
    # Sun as the stand-in: the Sun is a valid envelope object but is NOT
    # in the Mirror interpretation catalogue, so it must still route
    # through the generic ENGINE OUTPUT block.
    env = _make_envelope("Sun")
    block = build_natal_object_proof_block(env)
    # Not Mirror-wrapped → generic block (no MIRROR INTERPRETATION header)
    assert "ENGINE OUTPUT" in block
    assert "MIRROR INTERPRETATION" not in block


# ----------------------------------------------------------------------
# T2 corroboration bodies — object-specific ban lists & framings
# mirror-interpretation-layer-v1.2-t2
# ----------------------------------------------------------------------
def test_eros_block_bans_lust_and_seducer_language():
    block = build_mirror_object_proof_block(_make_envelope("Eros"))
    for forbidden in (
        "your sexual nature", "seducer", "twin flame", "soulmate",
        "lust", "sex magic",
    ):
        assert forbidden in block.lower(), (
            f"Eros block missing T2 ban for {forbidden!r}"
        )
    # Eros Mirror question must surface (shape of desire, not conquest)
    assert "kindles desire" in block.lower()


def test_psyche_block_bans_soul_love_language():
    block = build_mirror_object_proof_block(_make_envelope("Psyche"))
    for forbidden in (
        "soul love", "soulmate", "twin flame", "destined love",
        "past life connection", "completes you",
    ):
        assert forbidden in block.lower(), (
            f"Psyche block missing T2 ban for {forbidden!r}"
        )
    # Psyche Mirror question must surface (intimacy → transformation)
    assert "intimacy deepen" in block.lower()


def test_astraea_block_bans_justice_warrior_language():
    block = build_mirror_object_proof_block(_make_envelope("Astraea"))
    for forbidden in (
        "justice warrior", "righteous", "karmic vengeance",
        "moral crusade", "they'll get what's coming",
    ):
        assert forbidden in block.lower(), (
            f"Astraea block missing T2 ban for {forbidden!r}"
        )
    # Astraea Mirror question must surface (fairness as reflex)
    assert "fairness" in block.lower()


def test_hygiea_block_bans_purity_culture_language():
    block = build_mirror_object_proof_block(_make_envelope("Hygiea"))
    for forbidden in (
        "germaphobe", "purity culture", "hypochondriac",
        "obsessive cleanliness", "perfectionism as virtue",
    ):
        assert forbidden in block.lower(), (
            f"Hygiea block missing T2 ban for {forbidden!r}"
        )
    # Hygiea Mirror question must surface (pruning / system upkeep)
    assert "prune" in block.lower() or "tend" in block.lower()


def test_t2_bodies_route_through_engine_to_mirror_block():
    """The natal_object_engine must route each T2 corroboration body to
    its Mirror block (not the generic ENGINE OUTPUT block) when the
    envelope is a success envelope.  Failed envelopes still fall through
    to ENGINE STATUS — see test_failed_envelope_does_not_invoke_mirror_block
    for that contract."""
    for name in ("Eros", "Psyche", "Astraea", "Hygiea"):
        env = _make_envelope(name)
        block = build_natal_object_proof_block(env)
        assert "MIRROR INTERPRETATION" in block, (
            f"T2 body {name} did not route through Mirror block"
        )
        assert name in block


def test_t2_bodies_publish_v3_framework():
    """T2 blocks must surface the BEHAVIOR-FIRST V3 framework markers and
    the V3 voice-floor bans — exact same contract as the rest of the
    catalogue."""
    for name in ("Eros", "Psyche", "Astraea", "Hygiea"):
        block = build_mirror_object_proof_block(_make_envelope(name))
        # V3 framework primer
        for marker in (
            "BEHAVIOR-FIRST",
            "SUCCESS TEST",
            "THE PATTERN",
            "THE TENSION",
            "THE GIFT",
            "OBSERVABLE SIGNAL",
        ):
            assert marker.lower() in block.lower(), (
                f"T2 body {name} missing V3 framework marker {marker!r}"
            )
        # V3 voice-floor escalated bans (catalogue-wide)
        for forbidden in (
            "this placement suggests",
            "often manifests as",
            "speaks to how",
            "represents",
            "the archetype of",
        ):
            assert forbidden in block.lower(), (
                f"T2 body {name} missing v3 voice-floor ban {forbidden!r}"
            )


def test_t2_bodies_can_combine_pairwise_with_existing_catalogue():
    """T2 bodies must compose with the existing pairwise builder so a
    query like 'Eros + Psyche' produces a single intersection read
    rather than two stacked single-object reads."""
    eros = _make_envelope("Eros", sign="Scorpio", house=8)
    psyche = _make_envelope("Psyche", sign="Cancer", house=4)
    block = build_pairwise_mirror_block([eros, psyche])
    assert "Eros" in block
    assert "Psyche" in block
    assert "Scorpio" in block
    assert "Cancer" in block
    for marker in (
        "SHARED PATTERN",
        "SHARED TENSION",
        "SHARED GIFT",
        "HOW THEY INTERACT",
        "OBSERVABLE SIGNAL",
    ):
        assert marker in block, f"T2 pairwise missing {marker}"
    # Merged ban list must include both bodies' specific bans
    assert "seducer" in block.lower() or "lust" in block.lower()
    assert "soul love" in block.lower() or "completes you" in block.lower()


# ----------------------------------------------------------------------
# Safety: unsuccessful envelopes still go through the not-wired path
# ----------------------------------------------------------------------
def test_failed_envelope_does_not_invoke_mirror_block():
    env = {
        "success": False,
        "object": "Vertex",
        "reason": "vertex_inputs_missing",
        "message": "Vertex couldn't be computed — birth coordinates or "
                   "Julian Day are missing from this chart.",
    }
    block = build_natal_object_proof_block(env)
    assert "MIRROR INTERPRETATION" not in block
    assert "ENGINE STATUS" in block
    assert "couldn't be computed" in block


# ----------------------------------------------------------------------
# voice-floor-v2 — escalated bans baked into every Mirror block
# ----------------------------------------------------------------------
def test_voice_floor_v2_escalated_bans_present():
    """Every Mirror block must surface the escalated voice-floor bans
    so the LLM cannot silently drift back into textbook phrasing."""
    block = build_mirror_object_proof_block(_make_envelope("Ceres"))
    for forbidden in (
        "this placement suggests",
        "this placement indicates",
        "this placement invites",
        "often manifests as",
        "speaks to how",
        "Remember, this",
        "as per our agreement",
        "grounded in one area at a time",
    ):
        assert forbidden.lower() in block.lower(), (
            f"voice-floor-v2: missing ban on {forbidden!r}"
        )


# ----------------------------------------------------------------------
# Multi-object — pairwise builder + nodal axis builder
# astrology-chat-multi-object-v1
# ----------------------------------------------------------------------
from services.mirror_object_interpreter import (  # noqa: E402
    build_axis_mirror_block,
    build_pairwise_mirror_block,
    is_nodal_axis,
)


def test_is_nodal_axis_detection():
    assert is_nodal_axis(["North Node", "South Node"]) is True
    assert is_nodal_axis(["South Node", "North Node"]) is True
    assert is_nodal_axis(["Ceres", "Vesta"]) is False
    assert is_nodal_axis(["North Node"]) is False
    assert is_nodal_axis([]) is False


def test_nodal_axis_block_unifies_both_nodes():
    nn = _make_envelope("North Node", sign="Pisces", house=4)
    sn = _make_envelope("South Node", sign="Virgo", house=10)
    block = build_axis_mirror_block(nn, sn)
    assert "Nodal Axis" in block
    assert "North Node" in block
    assert "South Node" in block
    # Both placements must surface in the unified block
    assert "Pisces" in block
    assert "Virgo" in block
    # Polarity framing markers
    assert "overused" in block.lower()
    assert "stretch" in block.lower()
    # Axis-specific ban list must still ban past-life / soul-debt language
    assert "past life" in block.lower()
    assert "soul debt" in block.lower()


def test_pairwise_block_concatenates_two_bodies():
    ceres = _make_envelope("Ceres", sign="Virgo", house=10)
    vesta = _make_envelope("Vesta", sign="Aquarius", house=2)
    block = build_pairwise_mirror_block([ceres, vesta])
    assert "pairwise" in block.lower() or "INTERSECTION" in block.upper() or "intersection" in block.lower()
    # Both objects surface in the block
    assert "Ceres" in block
    assert "Vesta" in block
    # Both placements surface
    assert "Virgo" in block
    assert "Aquarius" in block
    # Per-object Mirror questions are surfaced
    assert "nourish" in block.lower()           # Ceres question
    assert "quiet, ongoing attention" in block.lower()  # Vesta question
    # The intersection instruction must explicitly forbid refusing the
    # second body (so the LLM can't bail with "let's stay on one topic").
    assert "do not refuse" in block.lower()
    assert "do not invent a prior agreement" in block.lower()


def test_pairwise_with_single_envelope_returns_single_block():
    """Pairwise builder gracefully delegates to single-block when only
    one envelope is passed."""
    env = _make_envelope("Ceres", sign="Virgo", house=10)
    block = build_pairwise_mirror_block([env])
    assert "MIRROR INTERPRETATION: Ceres" in block
    assert "pairwise" not in block.lower()


def test_pairwise_with_one_failed_envelope_still_renders():
    """If one body in a pair fails to compute, the block still emits
    rather than silently dropping the multi-object query."""
    ok = _make_envelope("Ceres", sign="Virgo", house=10)
    fail = {
        "success": False,
        "object": "Eros",
        "reason": "ephemeris_file_missing",
        "message": "Eros isn't wired into this build (its .se1 file is "
                   "missing).",
    }
    block = build_pairwise_mirror_block([ok, fail])
    assert "Ceres" in block
    assert "Eros" in block
    assert "not computed" in block.lower()


# ----------------------------------------------------------------------
# Degree-rendering — Variant-A signs can be > 30° wide.
# Per the canonical Variant-A policy (real constellation-width display,
# 2026-06-28), we surface the REAL within-sign offset, including values
# > 30° when astronomically valid. No clamping, no rescaling.
# variant-a-real-width-display-v1
# ----------------------------------------------------------------------
def test_display_degree_shows_real_width_above_29():
    env = _make_envelope("Pallas", sign="Leo", house=9)
    env["placement"]["degree"] = 33.3121   # Variant-A Pallas in wide Leo
    block = build_mirror_object_proof_block(env)
    # Real value 33° MUST appear in the user-visible proof block —
    # Leo's Variant-A band is ~33.82° wide so this is valid.
    assert "33°Leo" in block
    # We must NOT silently cap to 29° anymore.
    assert "29°Leo" not in block


def test_display_degree_normal_range_unchanged():
    env = _make_envelope("Chiron", sign="Aries", house=1)
    env["placement"]["degree"] = 12.4
    block = build_mirror_object_proof_block(env)
    assert "12°Aries" in block


def test_display_degree_missing_degree_falls_back_to_sign_only():
    env = _make_envelope("Chiron", sign="Aries", house=1)
    env["placement"]["degree"] = None
    env["placement"].pop("formatted", None)
    block = build_mirror_object_proof_block(env)
    # No raw '?°' or numeric junk; sign alone is acceptable
    assert "Aries" in block
    assert "?°" not in block


# ----------------------------------------------------------------------
# voice-floor-v3 — BEHAVIOR-FIRST INTERPRETATION FRAMEWORK
# ----------------------------------------------------------------------
def test_voice_floor_v3_framework_primer_present():
    """Every Mirror block surfaces the V3 framework + Pete Test."""
    block = build_mirror_object_proof_block(_make_envelope("Ceres"))
    # Framework primer markers
    for marker in (
        "BEHAVIOR-FIRST",
        "SUCCESS TEST",
        "that is exactly what I do",
        "THE PATTERN",
        "THE TENSION",
        "THE GIFT",
        "OBSERVABLE SIGNAL",
        "MIRROR DESCRIBES WHAT HAPPENS".lower(),  # case-insensitive
    ):
        assert marker.lower() in block.lower(), f"v3 framework missing: {marker}"


def test_voice_floor_v3_extra_bans_present():
    """v3 voice floor adds 'represents', 'symbolises', 'encourages you',
    sign-first / house-first prohibitions, and 'archetype' framings."""
    block = build_mirror_object_proof_block(_make_envelope("Pallas"))
    for forbidden in (
        "represents",
        "symbolises",
        "encourages you to",
        "the archetype of",
        "sign-first or house-first framings",
    ):
        assert forbidden.lower() in block.lower(), (
            f"voice-floor-v3: missing ban on {forbidden!r}"
        )


def test_axis_block_uses_pairwise_v3_framework():
    """Axis builder uses Shared Pattern / Shared Tension / Shared Gift /
    How They Interact framework, NOT two stacked single-body blocks."""
    nn = _make_envelope("North Node", sign="Pisces", house=4)
    sn = _make_envelope("South Node", sign="Virgo", house=10)
    block = build_axis_mirror_block(nn, sn)
    for marker in (
        "SHARED PATTERN",
        "SHARED TENSION",
        "SHARED GIFT",
        "HOW THEY INTERACT",
        "OBSERVABLE SIGNAL",
    ):
        assert marker in block, f"axis-v3 framework missing: {marker}"


def test_pairwise_block_uses_pairwise_v3_framework():
    """Pairwise builder uses the Shared / How They Interact framework."""
    ceres = _make_envelope("Ceres", sign="Virgo", house=10)
    vesta = _make_envelope("Vesta", sign="Aquarius", house=2)
    block = build_pairwise_mirror_block([ceres, vesta])
    for marker in (
        "SHARED PATTERN",
        "SHARED TENSION",
        "SHARED GIFT",
        "HOW THEY INTERACT",
        "OBSERVABLE SIGNAL",
    ):
        assert marker in block, f"pairwise-v3 framework missing: {marker}"
