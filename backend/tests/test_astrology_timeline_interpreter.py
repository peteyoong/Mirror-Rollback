"""
Audit tests for services/astrology_timeline_interpreter.py
==========================================================

Covers the 8 audit items from the task brief:
  1. Q1 → current_phase Recognition
  2. Q2 → current_phase Confrontation
  3. Q3 → current_phase Crossroads
  4. Q4 → current_phase Integration
  5. Turning points parsed correctly
  6. Domain relevance maps intimacy/shared resources to relationships/money
  7. Ask contradiction question uses timeline_context (life_interpreter)
  8. Ask timing question falls back cleanly if timeline_context unavailable
"""

import sys
from pathlib import Path

# Ensure the backend dir is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

from services import astrology_timeline_interpreter as ati  # noqa: E402
from services import life_interpreter as li  # noqa: E402


# ---------------------------------------------------------------------------
# 1–4. Quarter → phase scaffold
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "current_date, expected_phase, expected_next",
    [
        ("2026-02-15", "Recognition",   "Confrontation"),
        ("2026-05-15", "Confrontation", "Crossroads"),
        ("2026-08-15", "Crossroads",    "Integration"),
        ("2026-11-15", "Integration",   "Recognition"),
    ],
)
def test_scaffold_phases_by_quarter(current_date, expected_phase, expected_next):
    r = ati.build_timeline_context(
        user_id="u1",
        astrology_timeline_payload=None,
        current_date=current_date,
    )
    assert r["current_phase"]["name"] == expected_phase, (
        f"For {current_date}, expected current={expected_phase}, "
        f"got {r['current_phase']['name']}"
    )
    assert r["next_phase"]["name"] == expected_next
    # Pressure types must match the scaffold's canonical labels
    assert r["current_phase"]["pressure_type"] in {
        "clarity emerging", "avoidance becoming costly",
        "choice point", "settling into form",
    }


# ---------------------------------------------------------------------------
# 5. Turning points parsed correctly
# ---------------------------------------------------------------------------

def test_turning_points_parsed_with_classification():
    payload = {
        "year_theme": "A year of refining how you engage.",
        "arc": "What you've been avoiding stops being optional.",
        "phases": [
            {
                "name": "Confrontation",
                "period": "April–June 2026",
                "description": "What you've been avoiding starts to cost.",
            },
        ],
        "turning_points": [
            {
                "timing": "Late April",
                "why_this_matters": "An old avoidance becomes impossible to keep.",
                "what_becomes_clear": "You see what was costing you.",
                "what_happens_if_avoided": "It goes underground and surfaces louder.",
            },
            {
                "timing": "Mid-August",
                "why_this_matters": "A genuine fork in the road opens. You must choose.",
                "what_becomes_clear": "Both paths are real; neither is free.",
                "what_happens_if_avoided": "The choice gets made for you.",
            },
            {
                "timing": "Early November",
                "why_this_matters": "You name what the year has been about.",
                "what_becomes_clear": "Integration starts to land in the body.",
            },
        ],
    }
    r = ati.build_timeline_context(
        user_id="u2",
        astrology_timeline_payload=payload,
        current_date="2026-05-15",
    )
    tps = r["key_turning_points"]
    assert len(tps) == 3
    # Late April → confrontation
    assert tps[0]["type"] == "confrontation", tps[0]
    assert "April" in (tps[0]["timing"] or "")
    # Mid-August → decision (choice/fork)
    assert tps[1]["type"] == "decision", tps[1]
    # Early November → integration
    assert tps[2]["type"] == "integration", tps[2]
    # if_avoided fields should be preserved
    assert tps[0]["if_avoided"] is not None
    assert tps[1]["if_avoided"] is not None


# ---------------------------------------------------------------------------
# 6. Domain relevance — intimacy/shared resources → relationships + money
# ---------------------------------------------------------------------------

def test_domain_relevance_intimacy_and_shared_resources():
    payload = {
        "year_theme": "Intimacy and shared resources are being reweighed.",
        "phases": [
            {
                "name": "Confrontation",
                "description": "What you offer in your closest connections "
                               "is no longer matched by what you receive.",
            },
        ],
        "turning_points": [
            {
                "timing": "Mid-July",
                "what_activates": "A shared-resources conversation that has "
                                  "been delayed comes due.",
                "what_becomes_clear": "What feels like generosity in this "
                                      "relationship has become unsustainable.",
            },
        ],
    }
    r = ati.build_timeline_context(
        user_id="u3",
        astrology_timeline_payload=payload,
        current_date="2026-05-15",
        domain="relationships",
    )
    dr = r["domain_relevance"]
    assert "relationships" in dr, f"expected 'relationships' in {list(dr)}"
    assert "money" in dr, f"expected 'money' in {list(dr)}"
    # Notes are short human-readable strings, not jargon
    for v in dr.values():
        assert isinstance(v, str) and 10 < len(v) < 200
        for jargon in ("planet", "house", "transit", "decan", "pluto"):
            assert jargon not in v.lower(), v


# ---------------------------------------------------------------------------
# 7. Life Interpreter consumes the structured timeline_context
# ---------------------------------------------------------------------------

def test_life_interpreter_compresses_richer_timeline_context():
    """
    Ensure the interpreter's _compress_context preserves the new
    structured fields and that _format_context_for_llm renders them
    without error and includes phase + turning point hints.
    """
    timeline = ati.build_timeline_context(
        user_id="u4",
        astrology_timeline_payload={
            "year_theme": "A year of refining how you engage in relationships, not expansion.",
            "phases": [
                {
                    "name": "Confrontation",
                    "period": "April–June 2026",
                    "description": "What you've been avoiding in your closest "
                                   "connections stops being optional.",
                },
                {
                    "name": "Crossroads",
                    "period": "July–September 2026",
                    "description": "Choose which boundary you can actually hold "
                                   "in this relationship.",
                },
            ],
            "turning_points": [
                {
                    "timing": "Mid-August",
                    "why_this_matters": "A real fork in the road opens about "
                                        "shared resources and intimacy.",
                    "what_becomes_clear": "Both paths are real; neither is free.",
                    "what_happens_if_avoided": "The choice gets made for you.",
                },
            ],
        },
        current_date="2026-05-15",
        domain="relationships",
    )

    ctx = li.build_context_payload(
        chip_domain="relationships",
        question="What's my outlook for relationships this year? "
                 "I feel it is getting better but my astrology timeline seems "
                 "to say otherwise.",
        role_card=None,
        domain_synthesis=None,
        phase_current=None,
        domain_weights=None,
        pattern_memory=None,
        today_state=None,
        evidence_signals=None,
        chart=None,
        lifeline_summary=None,
        cross_domain_pattern=None,
        recurrence_data=None,
        activation_now_data=None,
        phase_context=None,
        timeline_context=timeline,
    )
    tl_block = ctx["timeline_context"]
    assert tl_block["year_theme"], "year_theme must propagate"
    assert tl_block["current_phase"], "current_phase must propagate"
    assert tl_block["current_phase"]["name"] == "Confrontation"
    assert tl_block["next_phase"]["name"] == "Crossroads"
    assert tl_block["key_turning_points"], "turning points must propagate"
    assert tl_block["domain_relevance"], "domain_relevance must propagate"

    # Now render to LLM-facing string and ensure key signals appear
    rendered = li._format_context_for_llm(ctx)
    assert "TIMELINE CONTEXT" in rendered
    assert "Confrontation" in rendered
    assert "Crossroads" in rendered
    assert "Mid-August" in rendered
    # The instruction line negatively references "transit / decan" by
    # name (those are *forbidden* tokens in the answer); that's fine.
    # We just want to confirm the user-supplied phase content itself
    # doesn't carry astrology jargon.
    cur_block_idx = rendered.find("current period")
    next_block_end = rendered.find("Use this for", cur_block_idx)
    phase_section = rendered[cur_block_idx:next_block_end].lower()
    for jargon in ("planet", "house ", "ayanamsa", "natal chart"):
        assert jargon not in phase_section, (
            f"jargon '{jargon}' leaked into phase content section"
        )


# ---------------------------------------------------------------------------
# 8. Empty / missing payload — clean fallback
# ---------------------------------------------------------------------------

def test_fallback_when_timeline_unavailable():
    """When no payload is provided, the interpreter must still return a
    well-formed structured context (deterministic 4-phase scaffold) so
    Ask never sees a None / malformed timeline_context."""
    r = ati.build_timeline_context(
        user_id="u5",
        astrology_timeline_payload=None,
        current_date="2026-05-15",
    )
    # Top-level keys per spec
    expected_keys = {
        "year_theme", "current_phase", "next_phase",
        "key_turning_points", "domain_relevance",
        "failure_mode", "confidence",
    }
    assert expected_keys.issubset(r.keys()), set(r) ^ expected_keys
    # Without a payload, there are no turning points and confidence is low
    assert r["key_turning_points"] == []
    assert r["confidence"] == "low"
    # Current phase is still well-formed
    cp = r["current_phase"]
    assert cp["name"] in {
        "Recognition", "Confrontation", "Crossroads", "Integration",
    }
    assert cp["pressure_type"] in {
        "clarity emerging", "avoidance becoming costly",
        "choice point", "settling into form",
    }


def test_intent_detection_for_contradiction_and_outlook():
    """The intent detector picks up contradiction + outlook_timing for the
    canonical user question, which is what triggers timeline_context
    computation in /api/life/ask."""
    intent = li.detect_question_intent(
        "What's my outlook for relationships this year? I feel it is "
        "getting better but my astrology timeline seems to say otherwise."
    )
    assert intent.get("is_contradiction") is True
    assert intent.get("is_outlook_timing") is True
