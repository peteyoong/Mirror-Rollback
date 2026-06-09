"""
Mirror Chat v2 — Intent-Aware Context Routing  ·  Slice A regression suite
==========================================================================

Covers:
  1. question_intent_router  →  deterministic domain classification.
  2. astrology_domain_context →  relationship-domain proof block content
                                  and ordering.
  3. Pete-marriage prompt-assembly regression — proves the relationship
     proof block lands BEFORE the generic Sun/HD/Numerology context.
  4. P0 regression — build_chart_entity_index must NOT crash when
     `formatted_cusps` is a list of strings (legacy schema).

These tests run without the FastAPI app — they exercise the pure helpers
that the route relies on, plus a small "system prompt assembly" mimic
that uses the exact same ordering rule as the route handler.

Run:
    cd /app/backend && python -m pytest tests/test_intent_aware_chat.py -v
"""
from __future__ import annotations

import re

import pytest

from services.question_intent_router import classify_question_intent
from services.astrology_domain_context import (
    build_domain_proof_block,
    build_relationship_context,
)
from services.astrology_conversation import build_chart_entity_index


# ---------------------------------------------------------------------------
# Pete-like chart fixture
# ---------------------------------------------------------------------------
# A trimmed-but-realistic chart payload.  Mirrors the shape produced by
# calculations.astrology.get_full_natal_chart: planets keyed by canonical
# name, houses.formatted_cusps as list-of-dicts, angles for asc/mc/ic/dc.

PETE_CHART = {
    "astrology": {
        "planets": {
            "Sun":     {"sign": "Gemini",      "degree": 12.0, "house": 11, "formatted": "12°Gemini"},
            "Moon":    {"sign": "Pisces",      "degree":  4.5, "house":  8, "formatted":  "4°Pisces"},
            "Mercury": {"sign": "Gemini",      "degree": 22.1, "house": 11, "formatted": "22°Gemini"},
            "Venus":   {"sign": "Taurus",      "degree":  9.8, "house": 10, "formatted":  "9°Taurus"},
            "Mars":    {"sign": "Leo",         "degree": 18.2, "house":  1, "formatted": "18°Leo"},
            "Jupiter": {"sign": "Cancer",      "degree":  3.0, "house": 12, "formatted":  "3°Cancer"},
            "Saturn":  {"sign": "Capricorn",   "degree": 11.4, "house":  6, "formatted": "11°Capricorn"},
            "Juno":    {"sign": "Sagittarius", "degree":  6.0, "house":  5, "formatted":  "6°Sagittarius"},
        },
        "houses": {
            "system": "Equal",
            "formatted_cusps": [
                {"house":  1, "sign": "Leo",         "degree": 28.0, "formatted": "28°Leo"},
                {"house":  2, "sign": "Virgo",       "degree": 28.0, "formatted": "28°Virgo"},
                {"house":  3, "sign": "Libra",       "degree": 28.0, "formatted": "28°Libra"},
                {"house":  4, "sign": "Scorpio",     "degree": 28.0, "formatted": "28°Scorpio"},
                {"house":  5, "sign": "Sagittarius", "degree": 28.0, "formatted": "28°Sagittarius"},
                {"house":  6, "sign": "Capricorn",   "degree": 28.0, "formatted": "28°Capricorn"},
                {"house":  7, "sign": "Aquarius",    "degree": 28.0, "formatted": "28°Aquarius"},
                {"house":  8, "sign": "Pisces",      "degree": 28.0, "formatted": "28°Pisces"},
                {"house":  9, "sign": "Aries",       "degree": 28.0, "formatted": "28°Aries"},
                {"house": 10, "sign": "Taurus",      "degree": 28.0, "formatted": "28°Taurus"},
                {"house": 11, "sign": "Gemini",      "degree": 28.0, "formatted": "28°Gemini"},
                {"house": 12, "sign": "Cancer",      "degree": 28.0, "formatted": "28°Cancer"},
            ],
        },
        "angles": {
            "asc": {"sign": "Leo",      "degree": 28.0, "formatted": "28°Leo"},
            "dc":  {"sign": "Aquarius", "degree": 28.0, "formatted": "28°Aquarius"},
            "mc":  {"sign": "Taurus",   "degree": 28.0, "formatted": "28°Taurus"},
            "ic":  {"sign": "Scorpio",  "degree": 28.0, "formatted": "28°Scorpio"},
        },
    },
    "human_design": {"type": "Manifestor", "profile": "5/1"},
    "numerology":   {"life_path": 7},
}


# ---------------------------------------------------------------------------
# 1.  Intent classifier
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("msg, expected_domain", [
    # Relationship triggers
    ("What does astrology tell me about marriage?",      "relationship"),
    ("Will I ever meet my soulmate?",                    "relationship"),
    ("What kind of spouse should I look for?",           "relationship"),
    ("Tell me about my current relationship.",           "relationship"),
    ("Why is dating so hard for me?",                    "relationship"),

    # Career triggers
    ("What's my best career path?",                      "career"),
    ("How should I lead at work?",                       "career"),
    ("Am I meant to start my own business?",             "career"),

    # Family / home triggers
    ("How do I show up better as a parent?",             "home"),
    ("What does my chart say about family?",             "home"),
    ("Tell me about my home life.",                      "home"),

    # Spiritual triggers
    ("What is my soul's destiny?",                       "spiritual"),
    ("Tell me about my spiritual awakening.",            "spiritual"),

    # Should remain general
    ("What is my Saturn sign?",                          "general"),
    ("Where is Mercury today?",                          "general"),
    ("Hello there.",                                     "general"),
])
def test_intent_classifier_assigns_correct_domain(msg, expected_domain):
    result = classify_question_intent(msg)
    assert result["domain"] == expected_domain, (
        f"expected {expected_domain} for {msg!r} but got {result['domain']}"
    )


def test_intent_classifier_extracts_self_target():
    result = classify_question_intent("What does astrology tell me about my marriage?")
    assert result["domain"] == "relationship"
    assert result["target"] == "self"


def test_intent_classifier_extracts_named_target():
    result = classify_question_intent("Tell me about Mel's marriage chart.")
    assert result["domain"] == "relationship"
    # Mel may resolve as the named target — at minimum it must not be 'self'.
    assert result["target"] in {"Mel", None}  # 'Mel' preferred; None acceptable
    # And the classifier must NOT mark this as self.
    assert result["target"] != "self"


def test_intent_classifier_lens_priority_for_relationship():
    result = classify_question_intent("What does astrology tell me about marriage?")
    assert result["lens_priority"], "relationship domain must populate lens_priority"
    # Relationship layer must lead the priority order.
    assert "astrology_relationship_layer" == result["lens_priority"][0]


# ---------------------------------------------------------------------------
# 2.  Relationship domain context — content
# ---------------------------------------------------------------------------

def test_relationship_context_pulls_partnership_architecture():
    ctx = build_relationship_context(PETE_CHART)
    assert ctx["house_7_sign"] == "Aquarius"
    assert ctx["descendant_sign"] == "Aquarius"
    # 7th-house ruler of Aquarius is Saturn (traditional)
    assert ctx["house_7_ruler"] == "Saturn"
    assert "Capricorn" in (ctx["house_7_ruler_placement"] or "")
    # Venus placement is captured
    assert ctx["venus"] is not None and "Taurus" in ctx["venus"]
    # Juno is captured
    assert ctx["juno"] is not None and "Sagittarius" in ctx["juno"]
    # Moon is supporting color
    assert ctx["moon"] is not None and "Pisces" in ctx["moon"]


def test_relationship_proof_block_has_correct_voice():
    block = build_domain_proof_block(
        domain="relationship", chart=PETE_CHART, target_name="Pete",
    )
    assert block, "relationship proof block must be emitted"

    # Headline architecture is present
    assert "DESCENDANT" in block.upper() or "Descendant" in block
    assert "7th House" in block or "7th house" in block.lower()
    assert "Venus" in block
    assert "Juno" in block

    # Absolute rule must include the ban
    assert "NEVER" in block.upper()
    # Sun / Human Design / Numerology must be named in the ban clause
    # (the LLM is told NOT to lead with them — but the WORDS themselves
    # must appear so the rule is unambiguous).
    assert "Sun sign" in block
    assert "Human Design" in block
    assert "Numerology" in block

    # Mirror voice rule (interpret-first, then explain why)
    assert "Why this" in block or "why this" in block


# ---------------------------------------------------------------------------
# 3.  Pete-marriage prompt-assembly regression
# ---------------------------------------------------------------------------
# The route handler assembles the system prompt in a strict order:
#   1) MIRROR_SYSTEM_PROMPT
#   2) preference inserts
#   3) lens prompts
#   4) DOMAIN PROOF BLOCK     ← Slice A injects HERE
#   5) "--- USER CONTEXT ---" with Sun/HD/Numerology
#   6) … lens memory / signals / etc.
# This test mimics the same ordering and asserts the relationship
# architecture lands BEFORE the generic Sun/HD/numerology block.

def _assemble_prompt_like_route(chart: dict, user_msg: str) -> str:
    """Minimal stand-in for the route handler's prompt assembly."""
    intent = classify_question_intent(user_msg)
    domain = intent["domain"]

    prompt = "MIRROR_SYSTEM_PROMPT (base)\n"
    if domain != "general":
        prompt += "\n" + build_domain_proof_block(
            domain=domain, chart=chart, target_name="Pete",
        )
    # Generic user context (matches the route's "--- USER CONTEXT ---" block)
    planets = chart["astrology"]["planets"]
    prompt += "\n\n--- USER CONTEXT ---\n"
    prompt += f"Sun: {planets['Sun']['formatted']} ({planets['Sun']['sign']})\n"
    prompt += f"Moon: {planets['Moon']['formatted']} ({planets['Moon']['sign']})\n"
    prompt += f"\n--- HUMAN DESIGN ---\nType: {chart['human_design']['type']}\n"
    prompt += f"\n--- NUMEROLOGY ---\nLife Path: {chart['numerology']['life_path']}\n"
    return prompt


def test_pete_marriage_relationship_leads_prompt():
    """
    Pete asks 'What does astrology tell me about marriage?'.
    The relationship architecture (Descendant / 7th house / Venus / Juno)
    MUST appear in the assembled system prompt BEFORE any Sun/HD/Numerology
    context.
    """
    prompt = _assemble_prompt_like_route(
        chart=PETE_CHART,
        user_msg="What does astrology tell me about marriage?",
    )

    # 1. Domain proof block is present
    assert "DOMAIN PROOF BLOCK" in prompt
    assert "RELATIONSHIP" in prompt.upper()

    # 2. The 7th-house / Descendant terms appear BEFORE the Sun line
    sun_idx = prompt.find("Sun:")
    assert sun_idx > 0, "Sun line must be present in USER CONTEXT"

    desc_idx_a = prompt.find("Descendant")
    desc_idx_b = prompt.find("7th House")
    desc_idx = min(i for i in (desc_idx_a, desc_idx_b) if i >= 0)
    assert desc_idx >= 0 and desc_idx < sun_idx, (
        f"Descendant/7th House (idx={desc_idx}) must appear before Sun (idx={sun_idx})"
    )

    # 3. Venus or Juno appear BEFORE the Human Design line
    hd_idx = prompt.find("--- HUMAN DESIGN ---")
    venus_idx = prompt.find("Venus")
    juno_idx = prompt.find("Juno")
    earliest_rel = min(i for i in (venus_idx, juno_idx) if i >= 0)
    assert earliest_rel >= 0 and earliest_rel < hd_idx, (
        f"Venus/Juno (idx={earliest_rel}) must appear before Human Design (idx={hd_idx})"
    )

    # 4. The block must NOT precede with Sun-sign-as-headline content
    # i.e. the FIRST domain-level mention must be partnership architecture,
    # NOT a Sun-sign reference inside the proof block.
    block_start = prompt.find("DOMAIN PROOF BLOCK")
    block_end = prompt.find("--- USER CONTEXT ---")
    proof_segment = prompt[block_start:block_end]
    # The proof block intentionally NAMES Sun sign in its ban clause, but
    # it must not OPEN with it.  Cheap proxy: the substring "Sun sign"
    # appears later in the proof segment than "Descendant" / "7th House".
    if "Sun sign" in proof_segment:
        sun_sign_idx = proof_segment.find("Sun sign")
        first_arch_idx = min(
            i for i in (
                proof_segment.find("Descendant"),
                proof_segment.find("7th House"),
            ) if i >= 0
        )
        assert first_arch_idx < sun_sign_idx, (
            "Within the proof block, partnership architecture must be "
            "named before the Sun-sign ban clause"
        )


def test_general_question_does_not_emit_proof_block():
    prompt = _assemble_prompt_like_route(
        chart=PETE_CHART, user_msg="What is my Saturn sign?",
    )
    assert "DOMAIN PROOF BLOCK" not in prompt


# ---------------------------------------------------------------------------
# 4.  P0 regression — formatted_cusps schema mismatch
# ---------------------------------------------------------------------------

def test_build_chart_entity_index_accepts_dict_cusps():
    idx = build_chart_entity_index(PETE_CHART)
    # Cusp sign per house is present
    assert idx["House 7"]["sign_on_cusp"] == "Aquarius"
    # Angles populated from dict cusps
    assert idx["Ascendant"]["sign"] == "Leo"
    assert idx["Descendant"]["sign"] == "Aquarius"


def test_build_chart_entity_index_accepts_string_cusps_no_crash():
    """P0 regression — `formatted_cusps` may be a list of strings.
    Previously this raised AttributeError and the LLM hallucinated."""
    string_chart = {
        "astrology": {
            "planets": {
                "Sun": {"sign": "Gemini", "degree": 12.0, "house": 11},
            },
            "houses": {
                "system": "Equal",
                # Legacy / partial shape — list of strings
                "formatted_cusps": [
                    "28°Leo", "28°Virgo", "28°Libra", "28°Scorpio",
                    "28°Sagittarius", "28°Capricorn", "28°Aquarius",
                    "28°Pisces", "28°Aries", "28°Taurus", "28°Gemini",
                    "28°Cancer",
                ],
            },
        },
    }
    idx = build_chart_entity_index(string_chart)
    # Did not crash.  And the parser pulled the correct sign per house.
    assert idx["House 1"]["sign_on_cusp"] == "Leo"
    assert idx["House 7"]["sign_on_cusp"] == "Aquarius"
    # Angles also work from string cusps
    assert idx["Ascendant"]["sign"] == "Leo"
    assert idx["Descendant"]["sign"] == "Aquarius"


def test_build_chart_entity_index_accepts_string_cusps_with_space():
    """Variant with space + degree symbol  (e.g. '28° Cancer')."""
    string_chart = {
        "astrology": {
            "planets": {},
            "houses": {
                "formatted_cusps": [
                    "28° Leo", "28° Virgo", "28° Libra", "28° Scorpio",
                    "28° Sagittarius", "28° Capricorn", "28° Aquarius",
                    "28° Pisces", "28° Aries", "28° Taurus", "28° Gemini",
                    "28° Cancer",
                ],
            },
        },
    }
    idx = build_chart_entity_index(string_chart)
    assert idx["Ascendant"]["sign"] == "Leo"
    assert idx["House 7"]["sign_on_cusp"] == "Aquarius"


def test_build_chart_entity_index_tolerates_garbage_cusp_entries():
    """A None or unexpected type must not raise; sign_on_cusp falls to None."""
    weird_chart = {
        "astrology": {
            "planets": {},
            "houses": {
                "formatted_cusps": [
                    None, 42, [], {"sign": "Libra"}, "garbage",
                    "", "  ", "Capricorn", "Aquarius",
                    "28°Pisces", "28°Aries", "28°Taurus",
                ],
            },
        },
    }
    # Just don't crash.
    idx = build_chart_entity_index(weird_chart)
    assert "House 4" in idx and idx["House 4"]["sign_on_cusp"] == "Libra"
    assert "House 8" in idx and idx["House 8"]["sign_on_cusp"] == "Capricorn"
    assert idx["House 1"]["sign_on_cusp"] is None  # None entry → no sign
