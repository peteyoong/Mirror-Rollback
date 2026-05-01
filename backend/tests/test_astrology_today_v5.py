"""
Tests for the Astrology Today v5 Mirror-Language refinement
===========================================================

Covers:
  1. signal_conflict flag on classify_signals (multi-category vs single-category)
  2. Core message template selection:
       - single-dominance → uses _SINGLE_CORE template
       - conflict         → uses _CONFLICT_CORE template ("You feel pushed to
                            act — but your read of the situation isn't fully
                            clean")
  3. Guardrail post-filter catches banned vocabulary + numeric timing +
     "should"/"must".
  4. Overlap detector catches a section that copies the core message.
  5. Deterministic fallback produces a valid `sections` payload with the
     non-prescriptive move shape (action, reflect) — no numbers.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.astrology_today_v5 import (  # noqa: E402
    _CONFLICT_CORE,
    _SINGLE_CORE,
    _core_message,
    _fallback_sections,
    _guardrail_violations,
    _overlap_ratio,
)
from services.transit_dominance_engine import classify_signals  # noqa: E402


def _sky(bodies_signs):
    return {"bodies": {k: {"sign": v, "longitude": 0, "degree": 0} for k, v in bodies_signs.items()}}


def _phase(full_h=None, new_h=None):
    return {
        "sun_moon_angle_deg": 0,
        "phase_key": "new_moon",
        "phase_human": "New Moon",
        "nearest_full_moon": (
            {"at_utc": "", "hours_offset": full_h,
             "within_48h": abs(full_h) <= 48, "within_7d": abs(full_h) <= 168}
            if full_h is not None else None
        ),
        "nearest_new_moon": (
            {"at_utc": "", "hours_offset": new_h,
             "within_48h": abs(new_h) <= 48, "within_7d": abs(new_h) <= 168}
            if new_h is not None else None
        ),
    }


# ---------------------------------------------------------------------------
# 1. signal_conflict detection
# ---------------------------------------------------------------------------

def test_signal_conflict_true_when_multiple_categories_live():
    # Full Moon (lunation) + tight aspect (aspect) + sign cluster (cluster)
    tight = {
        "id": "x", "transit": "Saturn", "aspect": "square", "natal": "Sun",
        "orb": 0.3, "applying": True, "is_tight": True,
        "exact_angle": 90, "natal_house": 10,
        "transit_sign": "Taurus", "natal_sign": "Aquarius",
    }
    c = classify_signals(
        moon_phase=_phase(full_h=24),
        ingresses=[],
        aspects=[tight],
        house_activations={"clusters": []},
        sky=_sky({"Sun": "Libra", "Mercury": "Libra", "Venus": "Libra"}),
    )
    assert c["signal_conflict"] is True
    assert set(c["active_categories"]) == {"lunation", "aspect", "cluster"}


def test_signal_conflict_false_when_only_one_category():
    c = classify_signals(
        moon_phase=_phase(full_h=24),
        ingresses=[],
        aspects=[],
        house_activations={"clusters": []},
        sky=_sky({"Moon": "Libra", "Sun": "Aries"}),
    )
    # Only lunation present → no conflict
    assert c["signal_conflict"] is False
    assert c["active_categories"] == ["lunation"]


# ---------------------------------------------------------------------------
# 2. Core message template selection
# ---------------------------------------------------------------------------

def test_core_message_uses_conflict_template_when_flag_true():
    out = _core_message(
        dominant_type="full_moon", signal_conflict=True, is_continuity=False,
    )
    assert out == _CONFLICT_CORE
    assert "pushed to act" in out
    assert "read of the situation isn't fully clean" in out


def test_core_message_uses_single_template_when_flag_false():
    out = _core_message(
        dominant_type="full_moon", signal_conflict=False, is_continuity=False,
    )
    assert out == _SINGLE_CORE["full_moon"]
    # Verify it does NOT bleed the conflict wording
    assert "pushed to act" not in out


def test_core_message_continuity_wrapper_prepended():
    out = _core_message(
        dominant_type="full_moon", signal_conflict=False, is_continuity=True,
    )
    assert "one day deeper" in out
    assert _SINGLE_CORE["full_moon"] in out


# ---------------------------------------------------------------------------
# 3. Guardrail post-filter
# ---------------------------------------------------------------------------

def test_guardrails_catch_vague_vocab():
    hits = _guardrail_violations("Today the energy is shifting — lean into the flow.")
    assert "energy" in hits
    assert "flow" in hits


def test_guardrails_catch_astrology_jargon():
    hits = _guardrail_violations("The full moon makes Mercury retrograde feel bigger.")
    assert any(h in hits for h in ("full moon", "mercury", "retrograde"))


def test_guardrails_catch_prescriptive_tokens():
    hits = _guardrail_violations("You should wait 30 minutes before replying.")
    assert "should" in hits
    assert "numeric-timing" in hits


def test_guardrails_pass_clean_text():
    clean = (
        "agreeing to something just to move the conversation forward. "
        "catching yourself rephrasing a reply three different ways."
    )
    # "three" is not numeric-timing (no unit), no banned vocab
    assert _guardrail_violations(clean) == []


# ---------------------------------------------------------------------------
# 4. Overlap detector
# ---------------------------------------------------------------------------

def test_overlap_high_when_sections_copy_core_message():
    core = _SINGLE_CORE["full_moon"]
    leaky = core[:160]  # first half of the core message
    assert _overlap_ratio(core, leaky) > 0.60


def test_overlap_low_when_sections_introduce_new_info():
    core = _SINGLE_CORE["full_moon"]
    new = (
        "replying to something before you have finished reading it. "
        "agreeing just to close a thread. "
        "filling a gap you haven't actually measured."
    )
    assert _overlap_ratio(core, new) < 0.35


# ---------------------------------------------------------------------------
# 5. Fallback sections shape
# ---------------------------------------------------------------------------

def test_fallback_sections_shape_and_nonprescriptive_move():
    dominance = {
        "dominant_signal": {"type": "full_moon"},
        "signal_conflict": False,
    }
    s = _fallback_sections(dominance)
    assert isinstance(s["how_it_shows_up"], list) and len(s["how_it_shows_up"]) >= 3
    assert isinstance(s["the_risk"], str) and s["the_risk"].strip()
    assert isinstance(s["the_move"], dict)
    assert "action" in s["the_move"] and "reflect" in s["the_move"]
    # The move must not contain numeric timing or prescriptive tokens
    all_move = s["the_move"]["action"] + " " + s["the_move"]["reflect"]
    hits = _guardrail_violations(all_move)
    assert hits == [], f"fallback move violated guardrails: {hits}"


def test_fallback_conflict_bullets_are_behavioural():
    dominance = {
        "dominant_signal": {"type": "full_moon"},
        "signal_conflict": True,
    }
    s = _fallback_sections(dominance)
    bullets = s["how_it_shows_up"]
    assert len(bullets) >= 3
    # Concrete action verbs only — no abstractions or feelings-as-nouns
    for b in bullets:
        assert _guardrail_violations(b) == [], f"bullet '{b}' violated guardrails"
        assert len(b.split()) >= 6, f"bullet '{b}' too abstract / too short"
