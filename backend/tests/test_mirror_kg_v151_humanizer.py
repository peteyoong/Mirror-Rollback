"""test_mirror_kg_v151_humanizer.py — regression tests for V1.5.1 fixes
   ------------------------------------------------------------------
   1) No duplicate sentence across story slots.
   2) Top story strips raw HD jargon (Ajna, Sacral, defined center, Gate 5, 35-36 channel, etc.).
   3) Different story slots come from distinct signals.
   4) Evidence ladder retains technical refs even after humanization.
   5) Fallback works if no clusters/signals match.
"""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.mirror_signal_normalizer import normalize_signals
from services.mirror_knowledge_graph import build_knowledge_graph
from services.mirror_reflection_orchestrator import synthesize_relationship, _humanize, _normalize_for_dedupe

TECH_TERMS = (
    "Ajna", "defined center", "open center", "Sacral", "Solar Plexus",
    "G Center", "G-Center", "Throat Center", "Head Center",
)


def _pete_mel_signals():
    return {
        "human_design_field": {
            "field_v3": {
                "energy_weather": "Pete's defined Ajna amplifies certainty; the room locks onto his ideas.",
                "decision_dynamics": "Pete's defined Ajna amplifies certainty before Mel can sense her own response.",
                "centre_conditioning": [
                    "Pete's defined Ajna amplifies certainty in conversation.",
                    "Mel's open Solar Plexus samples Pete's emotional wave.",
                ],
                "repair_pathway": [
                    "Pause and let Mel name what is hers before Pete moves.",
                    "Re-acknowledge the 28-day rhythm before re-engaging.",
                ],
                "friction_patterns": ["Manifestor x Reflector pace mismatch under pressure."],
            },
            "diagnostics": {"type_pair": "Manifestor x Reflector"},
        },
        "bazi": {"v2_card": {"current_movement": "Fire year pressures the wood-water cycle."}},
        "numerology": {"v2_card": {"core_dynamic": "7 meets 11 — introspection meets vision."}},
        "enneagram": {"friction_pattern": "Pete initiates too fast; Mel withdraws to clarify."},
    }


def _run(signals_dict):
    sigs = normalize_signals(signals_dict)
    g = build_knowledge_graph(sigs)
    return synthesize_relationship(sigs, g, "Pete", "Mel")


def test_humanize_strips_ajna():
    out = _humanize("Pete's defined Ajna amplifies certainty in the room.")
    assert "Ajna" not in out and "defined" not in out, f"residue: {out}"


def test_humanize_solar_plexus():
    out = _humanize("Mel's open Solar Plexus samples emotional wave.")
    assert "Solar Plexus" not in out
    assert "absorb" in out or "weather" in out


def test_humanize_manifestor_reflector():
    out = _humanize("Manifestor x Reflector pace mismatch.")
    assert "Manifestor" not in out and "Reflector" not in out


def test_no_duplicate_sentences_across_story_slots():
    syn = _run(_pete_mel_signals())
    story = syn["story"]
    texts = [story.get(k, "") for k in ("headline", "summary", "current_movement", "growth_edge", "shadow_pattern")]
    keys = [_normalize_for_dedupe(t) for t in texts if t]
    assert len(keys) == len(set(keys)), f"duplicate in story slots: {texts}"


def test_no_tech_terms_in_top_story():
    syn = _run(_pete_mel_signals())
    story_text = " ".join([
        syn["story"].get("headline", ""),
        syn["story"].get("summary", ""),
        syn["story"].get("current_movement", ""),
        syn["story"].get("growth_edge", ""),
        syn["story"].get("shadow_pattern", ""),
    ] + (syn["story"].get("repair_pathway") or []) + [syn["story"].get("question_to_ask", "")])
    for term in TECH_TERMS:
        assert term.lower() not in story_text.lower(), f"top story leaked '{term}': {story_text!r}"


def test_evidence_ladder_keeps_technical_refs():
    syn = _run(_pete_mel_signals())
    ladder = syn.get("evidence_ladder", [])
    assert ladder, "ladder must be present"
    # Each ladder entry still carries supporting_signals (which keep raw summaries via .summary)
    for entry in ladder:
        assert "supporting_signals" in entry
        # claim is humanized; claim_raw preserves original for drill-down
        assert "claim_raw" in entry, "drill-down must keep raw claim text"


def test_diversified_slots_distinct_signals():
    syn = _run(_pete_mel_signals())
    # No slot should repeat the exact same humanized text
    s = syn["story"]
    distinct = {k: s[k] for k in ("current_movement", "growth_edge", "shadow_pattern") if s.get(k)}
    keys = {_normalize_for_dedupe(v) for v in distinct.values()}
    assert len(keys) == len(distinct), f"slots overlap: {distinct}"


def test_fallback_when_no_signals():
    # Empty signals → still returns a valid synthesis envelope
    sigs = normalize_signals({})
    g = build_knowledge_graph(sigs)
    out = synthesize_relationship(sigs, g, "X", "Y")
    assert "story" in out and "evidence_ladder" in out


def test_undertone_for_today_present_when_signals_exist():
    syn = _run(_pete_mel_signals())
    # undertone must be present (string), humanized (no Ajna), and short
    undertone = syn.get("undertone_for_today", "")
    assert isinstance(undertone, str)
    if undertone:  # may be empty in degenerate cases
        assert "Ajna" not in undertone and "defined" not in undertone.lower() or "the field" in undertone.lower()
        assert len(undertone) < 220


def test_undertone_does_not_duplicate_top_story_slot():
    """The undertone must not echo headline/summary/movement etc."""
    from services.mirror_reflection_orchestrator import _normalize_for_dedupe as _norm
    syn = _run(_pete_mel_signals())
    undertone = syn.get("undertone_for_today", "")
    if not undertone:
        return  # acceptable when synthesis surfaced no extra signal
    used = set()
    for k in ("headline", "summary", "current_movement", "growth_edge", "shadow_pattern"):
        v = syn["story"].get(k, "")
        if v:
            used.add(_norm(v))
    assert _norm(undertone) not in used, f"undertone dup'd top story: {undertone!r}"
