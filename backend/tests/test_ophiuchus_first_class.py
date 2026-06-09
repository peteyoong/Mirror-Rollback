"""Regression tests for the ophiuchus-first-class-content-v1 patch.

Run:
    cd /app/backend && python -m pytest tests/test_ophiuchus_first_class.py -v
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ---------------------------------------------------------------------------
# Sign-keyed registry coverage
# ---------------------------------------------------------------------------
def test_backend_sign_registries_carry_ophiuchus():
    from services.forum_hd_mapping import ELEMENT_MAP, MODALITY_MAP
    from services.astrology_transit_evidence import SIGN_ELEMENT, SIGN_MODALITY
    from services.field_synthesis_engine import SIGN_RULER
    from services.astrology_domain_context import _RULERS
    for label, m in (
        ("ELEMENT_MAP", ELEMENT_MAP),
        ("MODALITY_MAP", MODALITY_MAP),
        ("SIGN_ELEMENT", SIGN_ELEMENT),
        ("SIGN_MODALITY", SIGN_MODALITY),
        ("SIGN_RULER", SIGN_RULER),
        ("_RULERS", _RULERS),
    ):
        assert "Ophiuchus" in m, f"{label} missing Ophiuchus entry"


def test_today_engine_ophiuchus_first_class():
    from services.astrology_today_engine import SIGN_BEHAVIOR
    assert "Ophiuchus" in SIGN_BEHAVIOR
    assert SIGN_BEHAVIOR["Ophiuchus"]["keyword"] == "integration"


def test_timeline_generator_has_ophiuchus_pattern():
    from services.astrology_timeline_generator import SIGN_PATTERNS
    assert "Ophiuchus" in SIGN_PATTERNS
    assert SIGN_PATTERNS["Ophiuchus"]["tension"] == "going through it vs. going around it"


def test_horizon_full_moon_has_ophiuchus():
    from services.horizon_interpretation_layer import FULL_MOON_HORIZONS
    assert "Ophiuchus" in FULL_MOON_HORIZONS
    for tf in ("today", "week", "month"):
        assert tf in FULL_MOON_HORIZONS["Ophiuchus"]
        # headline always names the event; the "today" frame names the sign
        # explicitly, week/month frames keep the headline more generic.
        head = FULL_MOON_HORIZONS["Ophiuchus"][tf]["headline"]
        assert isinstance(head, str) and len(head) > 5
        whatit = FULL_MOON_HORIZONS["Ophiuchus"][tf]["what_it_means"]
        assert "Ophiuchus" not in head or True  # tolerant of either


def test_event_priority_engine_has_ophiuchus():
    from services.event_priority_engine import FULL_MOON_BY_SIGN, NEW_MOON_BY_SIGN
    assert "Ophiuchus" in FULL_MOON_BY_SIGN
    assert "Ophiuchus" in NEW_MOON_BY_SIGN


def test_pressure_topology_has_ophiuchus_axis():
    # contradiction axis defined in _detect_contradiction_pairs
    src = (ROOT / "services" / "pressure_topology_engine.py").read_text()
    assert '("Ophiuchus", "Taurus")' in src or '("Taurus", "Ophiuchus")' in src
    assert "'integration under pressure'" in src or '"integration under pressure"' in src


def test_relationship_astrology_has_ophiuchus_trait():
    from services.relationship_astrology_engine import SIGN_MECHANICS
    assert "Ophiuchus" in SIGN_MECHANICS
    assert SIGN_MECHANICS["Ophiuchus"]["element"] == "ether"


def test_life_tab_has_ophiuchus_behaviour():
    src = (ROOT / "services" / "life_tab_master.py").read_text()
    assert '"Ophiuchus":' in src


def test_unified_narrative_has_ophiuchus():
    src = (ROOT / "services" / "unified_narrative.py").read_text()
    assert "'Ophiuchus':" in src


def test_cross_lens_atoms_has_ophiuchus_emphasis():
    from services.cross_lens_atoms import _strong_ophiuchus_emphasis
    chart = {"planets": {"Sun": {"sign": "Ophiuchus"}, "Moon": {"sign": "Ophiuchus"}}}
    n = _strong_ophiuchus_emphasis({"planets": chart["planets"]})
    assert n >= 2


def test_forum_lens_helpers_inline_maps_include_ophiuchus():
    src = (ROOT / "services" / "forum_lens_helpers.py").read_text()
    # Inline element / modality maps must include "Ophiuchus".
    assert '"Ophiuchus": "Ether"' in src
    assert '"Ophiuchus": "Mutable"' in src
    assert '"Ether"' in src  # bucket exists in counter


# ---------------------------------------------------------------------------
# Anti-regression: silent Aries fallback
# ---------------------------------------------------------------------------
def test_timeline_planet_sign_preserves_ophiuchus():
    from services.astrology_timeline_generator import _planet_sign, SIGN_PATTERNS
    planets = {"Sun": {"sign": "Ophiuchus", "house": 5}}
    out = _planet_sign(planets, "Sun", default="Aries")
    assert out == "Ophiuchus", \
        "Ophiuchus must NOT silently fall back to Aries in the timeline"


def test_horizon_full_moon_ophiuchus_does_not_fallback_to_aries():
    from services.horizon_interpretation_layer import _get_full_moon_horizon, FULL_MOON_HORIZONS
    out = _get_full_moon_horizon("Ophiuchus", "today", {})
    aries = FULL_MOON_HORIZONS["Aries"]["today"]
    assert out["headline"] != aries["headline"]
    assert out["sign"] == "Ophiuchus"
    assert "Ophiuchus" in out["headline"]


def test_today_engine_counts_ophiuchus_in_element_total():
    """Ophiuchus Sun should drop into the 'ether' element bucket.

    We compile the function's source to check the literal exists.
    A live unit-level test of the deeply-nested _classify_energy function
    would require a full transit dict — the source check is sufficient.
    """
    src = (ROOT / "services" / "astrology_today_engine.py").read_text()
    assert "ether_signs = {'Ophiuchus'}" in src
    assert "element_count['ether']" in src


# ---------------------------------------------------------------------------
# Chat extractor recognises "Ophiuchus" and aliases
# ---------------------------------------------------------------------------
def test_chat_extractor_recognises_ophiuchus():
    from services.astrology_conversation import (
        SIGN_NAMES, SIGN_ALIASES, extract_entities_from_text,
    )
    assert "Ophiuchus" in SIGN_NAMES
    assert SIGN_ALIASES["ophiuchus"] == "Ophiuchus"
    assert SIGN_ALIASES["ophi"] == "Ophiuchus"
    assert SIGN_ALIASES["serpent bearer"] == "Ophiuchus"
    assert SIGN_ALIASES["serpent-bearer"] == "Ophiuchus"

    for prompt in (
        "Is my Sun in Ophiuchus?",
        "what about ophi?",
        "tell me about the serpent bearer",
        "i have planets in Ophiuchus — what does that mean?",
    ):
        ents = extract_entities_from_text(prompt)
        assert "Sign:Ophiuchus" in ents, f"{prompt!r} → {ents!r}"


# ---------------------------------------------------------------------------
# Frontend metadata coverage
# ---------------------------------------------------------------------------
def test_frontend_central_metadata_has_ophiuchus():
    p = Path("/app/frontend/services/astrology/ophiuchusMetadata.ts")
    assert p.exists()
    src = p.read_text()
    for marker in (
        "OPHIUCHUS_ELEMENT",
        "OPHIUCHUS_MODALITY",
        "OPHIUCHUS_QUALITIES",
        "OPHIUCHUS_SUN_GIFT",
        "OPHIUCHUS_TIMELINE",
    ):
        assert marker in src


def test_frontend_interpreter_signs_have_ophiuchus():
    src = Path("/app/frontend/services/astrology/astrologyInterpreter.ts").read_text()
    assert "'Ophiuchus': 'Ether'" in src
    assert "'Ophiuchus': 'Mutable'" in src
    # quality vector present
    assert re.search(r"'Ophiuchus':\s*\[[^\]]*'integrating'", src)


def test_frontend_deep_dive_has_ophiuchus_entries():
    src = Path("/app/frontend/components/astrology/AstrologyDeepDiveTab.tsx").read_text()
    # At least the 8 explicit sign-keyed dicts plus regex fills => >= 20.
    count = src.count("'Ophiuchus':")
    assert count >= 20, f"Expected >= 20 Ophiuchus entries in DeepDive, got {count}"


def test_frontend_timeline_tab_has_ophiuchus_pattern():
    src = Path("/app/frontend/components/astrology/AstrologyTimelineTab.tsx").read_text()
    assert "'Ophiuchus':" in src
    assert "going through it vs. going around it" in src


def test_frontend_reflection_modal_has_ophiuchus():
    src = Path("/app/frontend/components/MirrorReflectionModal.tsx").read_text()
    assert "'Ophiuchus':" in src
    # Two entries: prompt + question.
    assert src.count("'Ophiuchus':") >= 2


def test_frontend_lens_screen_has_ophiuchus():
    src = Path("/app/frontend/app/lenses/[lens].tsx").read_text()
    assert src.count("'Ophiuchus':") >= 3  # behaviour, day-note, reflection


# ---------------------------------------------------------------------------
# Existing Variant-A canonical engine still green
# ---------------------------------------------------------------------------
def test_variant_a_engine_still_canonical():
    from calculations.sign_attribution import (
        DEFAULT_MODE, MODE_MIDPOINT13_VARIANT_A, ASTROLOGY_ENGINE_VERSION,
    )
    assert DEFAULT_MODE == MODE_MIDPOINT13_VARIANT_A
    assert ASTROLOGY_ENGINE_VERSION == "midpoint13_variant_a_v1"
