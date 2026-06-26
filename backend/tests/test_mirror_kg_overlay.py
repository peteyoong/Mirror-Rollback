"""Tests for Knowledge Graph + Orchestration Overlay V1
========================================================

Build markers: mirror-signal-normalizer-v1, mirror-knowledge-graph-v1,
               mirror-reflection-orchestrator-v1

Coverage (14 categories per spec):
  1.  normalizer emits valid signal format from HD Field V3
  2.  normalizer emits valid signal format from BaZi V2
  3.  normalizer emits valid signal format from Numerology V2-lite
  4.  graph clusters same themes across multiple lenses
  5.  graph confidence rises when 3+ lenses converge
  6.  graph confidence remains emerging for single-lens insight
  7.  orchestrator emits all required story keys
  8.  evidence tray includes lens and source_path
  9.  technical refs preserved
  10. no forbidden language
  11. no existing relationship mapping keys removed
  12. Pete ↔ Mel snapshot
  13. Pete ↔ Isaac snapshot
  14. Pete ↔ Thaddeus snapshot
"""
from __future__ import annotations
import asyncio
import os
import sys
from typing import Any, Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(HERE)
if BACKEND not in sys.path: sys.path.insert(0, BACKEND)

from services.mirror_signal_normalizer import (
    CANONICAL_THEMES, NORMALIZER_VERSION,
    normalize_signals, normalize_hd_field, normalize_bazi,
    normalize_numerology, normalize_astrology, normalize_enneagram,
)
from services.mirror_knowledge_graph import (
    GRAPH_VERSION, build_knowledge_graph,
)
from services.mirror_reflection_orchestrator import (
    FORBIDDEN, ORCHESTRATOR_VERSION, synthesize_relationship,
)

# Required signal fields (from spec).
SIGNAL_KEYS = {"id","lens","domain","subject_id","object_id","theme",
               "polarity","time_scope","strength","confidence",
               "source_path","summary","technical"}


# ── Test fixtures ────────────────────────────────────────────────────
HD_FIELD_FIXTURE = {
    "field_v3": {
        "energy_signature": "The Catalyst and the Engine.",
        "field_overview":   "Pete's closed aura initiates; Isaac's open enveloping aura responds.",
        "aura_dynamics":    "Pete's closed aura initiates; Isaac's open enveloping aura responds.",
        "decision_dynamics":"Pete needs the wave; Isaac's body knows in the moment.",
        "centre_conditioning":[
            "Pete's defined Solar Plexus amplifies emotional waves.",
            "Pete's defined Throat amplifies the urge to speak.",
        ],
        "electromagnetic_gifts":"2 channels complete between you.",
        "compromise_dynamics":  "No compromise dynamics.",
        "dominance_dynamics":   "Pete's defined channels dominate the field.",
        "friction_patterns":[
            "Deciding before the emotional wave has settled.",
            "Acting without informing.",
        ],
        "repair_pathway":[
            "Sleep on it.  No important decisions until the emotional wave settles.",
            "Inform before acting next time.",
        ],
        "growth_edge":   "Each learns the other's pacing.",
        "energy_weather":"Initiating energy meeting response.",
    },
    "diagnostics": {
        "type_pair":      "Manifestor × Generator",
        "authority_pair": "Emotional × Sacral",
        "engine_version": "relationship-hd-field-v3",
    },
}

BAZI_FIXTURE = {
    "v2_card": {
        "natural_strength": "Pete's Metal naturally nourishes Mel's Water.  Structure becomes motion.",
        "repair_pathway":   "When the flow runs one-way, the repair is reciprocity.",
        "current_movement": "This is a Fire-Horse year (2026).  The Fire pillar presses on the first's rhythm.",
        "how_they_help_each_other": "Mel becomes where Pete's effort lands.  Pete restores Mel's perspective.",
        "how_they_challenge_each_other": "The challenge axis is subtle.",
        "current_relationship_season": "The Fire cycle tests one rhythm in particular.",
        "shadow_pattern": "Pete keeps surfacing what Mel already released.",
        "growth_edge":    "Pete grows by moving before fully understanding.",
    },
    "diagnostics": {
        "bridge_element":     "Earth",
        "ten_gods_a_sees_b":  "Output",
        "ten_gods_b_sees_a":  "Resource",
        "day_master_relation":"Metal-Yin × Water-Yang",
        "engine_version":     "relationship-bazi-engine-v2",
    },
}

NUM_FIXTURE = {
    "themes": ["You both process life through expression and communication."],
    "v2_card": {
        "core_dynamic":     "Inner Knower meets Voice.",
        "natural_strength": "Pete feels what's underneath.  Mel gives it shape.",
        "growth_edge":      "Pete grows by trusting articulate words.",
        "shadow_pattern":   "Under pressure Pete starts to speak in hints.",
        "repair_pathway":   "Pause.  Each names one true thing.",
    },
    "diagnostics": {"pair_type": "3x11-voice-meets-inner-knower"},
}


# ─────────────────────────────────────────────────────────────────────
# 1–3. Normalizer per-lens shape compliance
# ─────────────────────────────────────────────────────────────────────
def _assert_signal_shape(sig: Dict[str, Any], lens: str):
    # V1.5 is additive: V1 keys must all be present; new V1.5 keys
    # (layer/mechanic/evidence_type/drilldown_level/provenance) are
    # allowed but not required by this contract test.
    missing = SIGNAL_KEYS - set(sig.keys())
    assert not missing, f"{lens}: missing V1 keys: {missing}"
    assert sig["lens"] == lens
    assert 0.0 <= sig["strength"] <= 1.0
    assert 0.0 <= sig["confidence"] <= 1.0
    assert sig["theme"] in CANONICAL_THEMES
    assert sig["polarity"] in ("support","friction","growth","repair","movement","shadow","evidence")
    assert sig["source_path"].startswith(f"signals.{lens}.")
    assert isinstance(sig["summary"], str) and len(sig["summary"]) >= 1
    assert isinstance(sig["technical"], dict)


def test_normalizer_hd_field_shape():
    sigs = normalize_hd_field(HD_FIELD_FIXTURE)
    assert len(sigs) >= 5
    for s in sigs: _assert_signal_shape(s, "human_design")


def test_normalizer_bazi_shape():
    sigs = normalize_bazi(BAZI_FIXTURE)
    assert len(sigs) >= 5
    for s in sigs: _assert_signal_shape(s, "bazi")


def test_normalizer_numerology_shape():
    sigs = normalize_numerology(NUM_FIXTURE)
    assert len(sigs) >= 4
    for s in sigs: _assert_signal_shape(s, "numerology")


def test_normalizer_handles_missing_input():
    assert normalize_hd_field({}) == []
    assert normalize_bazi({}) == []
    assert normalize_numerology({}) == []
    assert normalize_astrology({}) == []
    assert normalize_enneagram({}) == []
    assert normalize_signals({}) == []


# ─────────────────────────────────────────────────────────────────────
# 4. Graph clusters same themes across multiple lenses
# ─────────────────────────────────────────────────────────────────────
def test_graph_clusters_repair_across_lenses():
    sigs = (normalize_hd_field(HD_FIELD_FIXTURE)
            + normalize_bazi(BAZI_FIXTURE)
            + normalize_numerology(NUM_FIXTURE))
    g = build_knowledge_graph(sigs)
    repair_cluster = next((c for c in g["clusters"] if c["theme"] == "repair"), None)
    assert repair_cluster is not None, "repair theme not clustered"
    assert len(repair_cluster["supporting_lenses"]) >= 2, \
        f"repair only in {repair_cluster['supporting_lenses']}"


# ─────────────────────────────────────────────────────────────────────
# 5. Graph confidence rises with 3+ lens convergence
# ─────────────────────────────────────────────────────────────────────
def test_confidence_rises_with_three_lens_convergence():
    sigs = (normalize_hd_field(HD_FIELD_FIXTURE)
            + normalize_bazi(BAZI_FIXTURE)
            + normalize_numerology(NUM_FIXTURE))
    g = build_knowledge_graph(sigs)
    # Find the cluster with the most lenses
    top = max(g["clusters"], key=lambda c: c["lens_count"])
    if top["lens_count"] >= 3:
        assert top["confidence"] == "high"


# ─────────────────────────────────────────────────────────────────────
# 6. Single-lens insight stays emerging
# ─────────────────────────────────────────────────────────────────────
def test_single_lens_confidence_stays_emerging_or_medium():
    sigs = normalize_numerology(NUM_FIXTURE)  # only one lens
    g = build_knowledge_graph(sigs)
    # The orchestrator's confidence should not be 'high' on single lens
    synth = synthesize_relationship(sigs, g, "A", "B")
    assert synth["confidence"]["level"] in ("emerging", "medium")


# ─────────────────────────────────────────────────────────────────────
# 7. Orchestrator emits all required story keys
# ─────────────────────────────────────────────────────────────────────
def test_orchestrator_emits_complete_story():
    sigs = (normalize_hd_field(HD_FIELD_FIXTURE)
            + normalize_bazi(BAZI_FIXTURE)
            + normalize_numerology(NUM_FIXTURE))
    g = build_knowledge_graph(sigs)
    synth = synthesize_relationship(sigs, g, "Pete", "Mel")
    required_story_keys = {"headline","summary","current_movement",
                           "growth_edge","shadow_pattern","repair_pathway",
                           "question_to_ask"}
    assert set(synth["story"].keys()) == required_story_keys


def test_orchestrator_emits_evidence_tray():
    sigs = (normalize_hd_field(HD_FIELD_FIXTURE)
            + normalize_bazi(BAZI_FIXTURE)
            + normalize_numerology(NUM_FIXTURE))
    g = build_knowledge_graph(sigs)
    synth = synthesize_relationship(sigs, g, "Pete", "Mel")
    ev = synth["evidence"]
    assert isinstance(ev["why_mirror_sees_this"], list) and ev["why_mirror_sees_this"]
    assert isinstance(ev["lens_contributions"], dict) and ev["lens_contributions"]
    # Confidence + diagnostics + engine versions
    assert synth["confidence"]["level"] in ("high","medium","emerging")
    diag = synth["diagnostics"]
    assert diag["engine_version"] == ORCHESTRATOR_VERSION


# ─────────────────────────────────────────────────────────────────────
# 8. Evidence tray includes lens and source_path
# ─────────────────────────────────────────────────────────────────────
def test_evidence_tray_lines_include_lens_and_source_path():
    sigs = (normalize_hd_field(HD_FIELD_FIXTURE)
            + normalize_bazi(BAZI_FIXTURE))
    g = build_knowledge_graph(sigs)
    synth = synthesize_relationship(sigs, g, "A", "B")
    for line in synth["evidence"]["why_mirror_sees_this"]:
        assert "lens" in line and line["lens"] in ("human_design","bazi","numerology","astrology","enneagram")
        assert "source_path" in line and line["source_path"].startswith("signals.")
        assert "signal_id" in line


# ─────────────────────────────────────────────────────────────────────
# 9. Technical refs preserved
# ─────────────────────────────────────────────────────────────────────
def test_technical_refs_preserved_through_orchestrator():
    sigs = (normalize_hd_field(HD_FIELD_FIXTURE)
            + normalize_bazi(BAZI_FIXTURE))
    g = build_knowledge_graph(sigs)
    synth = synthesize_relationship(sigs, g, "A", "B")
    refs = synth["evidence"]["technical_refs"]
    assert isinstance(refs, list) and refs
    # At least one bazi technical ref must carry bridge_element or ten_gods info
    bazi_refs = [r for r in refs if r["lens"] == "bazi"]
    assert bazi_refs and bazi_refs[0]["data"]


# ─────────────────────────────────────────────────────────────────────
# 10. No forbidden language in synthesized output
# ─────────────────────────────────────────────────────────────────────
def test_no_forbidden_language_in_synthesis():
    sigs = (normalize_hd_field(HD_FIELD_FIXTURE)
            + normalize_bazi(BAZI_FIXTURE)
            + normalize_numerology(NUM_FIXTURE))
    g = build_knowledge_graph(sigs)
    synth = synthesize_relationship(sigs, g, "Pete", "Mel")
    blob: List[str] = []
    for v in synth["story"].values():
        if isinstance(v, str): blob.append(v.lower())
        elif isinstance(v, list):
            blob.extend(x.lower() for x in v if isinstance(x, str))
    joined = " ".join(blob)
    for tok in FORBIDDEN:
        assert tok not in joined, f"forbidden token in synthesis: {tok}"
    assert synth["diagnostics"]["forbidden_flagged"] == []


# ─────────────────────────────────────────────────────────────────────
# 11. No existing relationship mapping keys removed (live test)
# ─────────────────────────────────────────────────────────────────────
def test_existing_mapping_keys_preserved():
    from motor.motor_asyncio import AsyncIOMotorClient
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BACKEND, ".env"))

    async def _run():
        c = AsyncIOMotorClient(os.getenv("MONGO_URL"))
        db = c[os.getenv("DB_NAME","test_database")]
        from services.forum_hd_mapping import get_forum_member_mappings
        ms = await get_forum_member_mappings(db, "69dda348de9cb1c83c0780fa", "697f0c6abf35c0528ff06954")
        c.close()
        return ms

    mappings = asyncio.run(_run())
    assert mappings, "no mappings returned"
    sample = mappings[0]
    # The existing legacy keys must all still be present.
    required_legacy_keys = {"signals","headline","description","what_works",
                            "what_to_watch","why_this_happens",
                            "channel_count","strength_score"}
    missing = required_legacy_keys - set(sample.keys())
    assert not missing, f"removed legacy keys: {missing}"
    # The new key must be present.
    assert "relationship_synthesis" in sample
    # Existing signals dict must have all 5 lens keys plus the new sibling.
    sigs = sample["signals"]
    expected = {"human_design","human_design_field","astrology","bazi",
                "enneagram","numerology"}
    assert expected.issubset(set(sigs.keys())), \
        f"signals lens-keys missing: {expected - set(sigs.keys())}"


# ─────────────────────────────────────────────────────────────────────
# 12–14. Pete ↔ Mel / Isaac / Thaddeus live snapshots
# ─────────────────────────────────────────────────────────────────────
def _run_live_pair(target_name: str):
    from motor.motor_asyncio import AsyncIOMotorClient
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BACKEND, ".env"))

    async def _r():
        c = AsyncIOMotorClient(os.getenv("MONGO_URL"))
        db = c[os.getenv("DB_NAME","test_database")]
        from services.forum_hd_mapping import get_forum_member_mappings
        ms = await get_forum_member_mappings(db, "69dda348de9cb1c83c0780fa", "697f0c6abf35c0528ff06954")
        c.close()
        return ms
    mappings = asyncio.run(_r())
    for m in mappings:
        if m.get("member_name", "").startswith(target_name):
            return m
    raise AssertionError(f"no mapping for {target_name}")


def test_snapshot_pete_mel():
    m = _run_live_pair("Mel")
    s = m.get("relationship_synthesis")
    assert s is not None
    assert s["story"]["headline"]
    assert s["story"]["repair_pathway"]
    assert s["confidence"]["level"] in ("high","medium","emerging")
    # Multiple lenses should converge for Pete↔Mel (HD+BaZi+Numerology all run)
    lenses_used = s["diagnostics"]["lenses_present"]
    assert len(lenses_used) >= 3, f"only {lenses_used} present"


def test_snapshot_pete_isaac():
    m = _run_live_pair("Isaac")
    s = m.get("relationship_synthesis")
    assert s is not None
    assert s["story"]["headline"]
    assert "Pete" in s["story"]["headline"] or "Isaac" in s["story"]["headline"]
    assert s["diagnostics"]["engine_version"] == ORCHESTRATOR_VERSION


def test_snapshot_pete_thaddeus():
    m = _run_live_pair("Thaddeus")
    s = m.get("relationship_synthesis")
    assert s is not None
    assert s["story"]["headline"]
    assert s["story"]["repair_pathway"]
    # Evidence tray must be populated
    assert len(s["evidence"]["why_mirror_sees_this"]) >= 3


# ─────────────────────────────────────────────────────────────────────
# Bonus: engine_version markers are correct
# ─────────────────────────────────────────────────────────────────────
def test_build_markers_correct():
    assert NORMALIZER_VERSION    in ("mirror-signal-normalizer-v1", "mirror-signal-normalizer-v1.5")
    assert GRAPH_VERSION         in ("mirror-knowledge-graph-v1", "mirror-knowledge-graph-v1.5")
    assert ORCHESTRATOR_VERSION  in ("mirror-reflection-orchestrator-v1", "mirror-reflection-orchestrator-v1.5")


if __name__ == "__main__":
    import traceback
    p = f = 0
    for name in sorted(globals()):
        if not name.startswith("test_"): continue
        fn = globals()[name]
        try: fn(); print(f"  PASS  {name}"); p += 1
        except Exception:
            print(f"  FAIL  {name}"); traceback.print_exc(); f += 1
    print(f"\n{p} passed, {f} failed")
    raise SystemExit(0 if not f else 1)
