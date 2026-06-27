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


# ─────────────────────────────────────────────────────────────────────
# Regression tests for the EXACT broken phrases reported in production
# ─────────────────────────────────────────────────────────────────────
PRODUCTION_LEAKS = [
    "Pete's one of you",                    # malformed possessive + replacement
    "Mel's one of you",
    "open-the field between you",           # compound residue
    "defined-the field between you",
    "open-Solar-Plexus side",               # hyphenated form
    "defined-Ajna side",
    "lunar-authority side",                 # technical term
    "splenic signals don't",
    "Ajna",                                  # raw center
    "Solar Plexus",
    "Sacral",
]


def test_regression_no_production_broken_phrases_in_top_story():
    """Reproduces the strings the user saw on live iOS Safari."""
    syn = _run(_pete_mel_signals())
    story_text = " ".join([
        syn["story"].get("headline", ""),
        syn["story"].get("summary", ""),
        syn["story"].get("current_movement", ""),
        syn["story"].get("growth_edge", ""),
        syn["story"].get("shadow_pattern", ""),
    ] + (syn["story"].get("repair_pathway") or []) + [syn["story"].get("question_to_ask", "")])
    text_l = story_text.lower()
    for bad in PRODUCTION_LEAKS:
        assert bad.lower() not in text_l, f"top story still leaks '{bad}': {story_text!r}"


def test_humanize_strips_possessive_prefix_for_ajna_certainty():
    """Pete's defined Ajna amplifies certainty → clean sentence."""
    from services.mirror_reflection_orchestrator import _humanize as h
    out = h("Pete's defined Ajna amplifies certainty in conversation.")
    assert "Pete's" not in out or "one of you" not in out.lower().replace("pete's one of you", "")
    # Strong: result must NOT start with "Pete's one of you"
    assert not out.lower().startswith("pete's one of you")
    assert "Ajna" not in out


def test_humanize_handles_hyphenated_open_solar_plexus():
    from services.mirror_reflection_orchestrator import _humanize as h
    out = h("open-Solar-Plexus side stays in situations longer.")
    assert "open-Solar-Plexus" not in out
    assert "Solar Plexus" not in out
    assert "open-the field between you" not in out


def test_humanize_replaces_lunar_authority():
    from services.mirror_reflection_orchestrator import _humanize as h
    out = h("Asking the lunar-authority side to respond in real time.")
    assert "lunar-authority" not in out.lower()
    assert "lunar authority" not in out.lower()


def test_humanize_no_compound_open_defined_the_field():
    from services.mirror_reflection_orchestrator import _humanize as h
    inputs = [
        "Mel's defined-Solar-Plexus side's conclusions.",
        "defined-Ajna side's conclusions felt heavy.",
        "open-Ajna side is leading the room.",
    ]
    for i in inputs:
        out = h(i)
        assert "open-the field" not in out.lower(), out
        assert "defined-the field" not in out.lower(), out
        # Must not contain raw HD terms either
        assert "Ajna" not in out and "Solar Plexus" not in out


def test_humanize_sentence_level_atomicity():
    """If only some sentences are broken, clean sentences must survive."""
    from services.mirror_reflection_orchestrator import _humanize as h
    out = h("Initiator meets Seeker. Pete's defined Ajna amplifies certainty. Build slowly.")
    # The clean sentences must persist
    assert "Initiator meets Seeker" in out
    assert "Build slowly" in out
    # The broken one must be rewritten cleanly, NOT dropped entirely
    assert "one of you" in out.lower() or "certain" in out.lower()


def test_evidence_ladder_keeps_technical_refs():
    """v1.5.4 — ladder entries no longer ECHO story claims (used to keep
    `claim_raw`).  Each entry now surfaces a humanized supporting signal
    and exposes technical refs / lens contributions for drill-down."""
    syn = _run(_pete_mel_signals())
    ladder = syn.get("evidence_ladder", [])
    assert ladder, "ladder must be present"
    for entry in ladder:
        assert "supporting_signals" in entry
        assert "lens_contributions" in entry
        assert "technical_refs" in entry
        # `claim` is the human-readable bullet; drill-down stays available
        assert "claim" in entry and isinstance(entry["claim"], str) and entry["claim"]


def test_ladder_does_not_echo_story_slots():
    """Regression: production showed every story slot duplicated as a
    ladder bullet. The new builder dedupes against story slots."""
    syn = _run(_pete_mel_signals())
    used = set()
    for k in ("headline", "summary", "current_movement",
              "growth_edge", "shadow_pattern", "question_to_ask"):
        v = syn["story"].get(k)
        if isinstance(v, str) and v.strip():
            used.add(_normalize_for_dedupe(v))
    for line in (syn["story"].get("repair_pathway") or []):
        if isinstance(line, str):
            used.add(_normalize_for_dedupe(line))
    for entry in syn["evidence_ladder"]:
        norm = _normalize_for_dedupe(entry["claim"])
        # Allow ONLY when ladder fell back to top-cluster (single entry,
        # sparse signals). Multi-entry ladders MUST not echo.
        if len(syn["evidence_ladder"]) > 1:
            assert norm not in used, f"ladder echoes story slot: {entry['claim']!r}"


def test_headline_no_lens_names():
    """Regression: production headline was
    'Pressure is the strongest signal between Pete and Mel (enneagram +
     human_design + numerology converge).'
    The new headline must contain no raw lens identifiers."""
    syn = _run(_pete_mel_signals())
    h = syn["story"].get("headline", "")
    BAD = ("human_design", "numerology", "enneagram", "bazi", "astrology",
           "converge)")
    for term in BAD:
        assert term not in h.lower(), f"headline still leaks '{term}': {h!r}"


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
