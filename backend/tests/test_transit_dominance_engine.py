"""
Acceptance tests for the Transit Dominance Engine (P4 in spec)
==============================================================

Scenarios covered:
  1. Full Moon within ±48h → Tier 1 dominant
  2. Uranus sign ingress within ±14d → Tier 1 outer_ingress dominant
  3. Tight transit-to-natal aspect ≤0.5° outranks wider sign concentration
  4. Moon sign change today → Tier 2 surfaces
  5. Same signature as yesterday → signature_changed is False (→ caller
     uses continuity language)
  6. No major signal → low intensity but still emits a dominant signal
     (cluster / aspect / moon_sign_change) — never an empty payload
  7. why_today_is_different sentence explains the dominance reason.

All tests inject synthetic sky / aspect / ingress data via the
classify_signals() public function so they don't depend on the real
ephemeris or today's date.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.transit_dominance_engine import (  # noqa: E402
    classify_signals,
    compute_signature_hash,
)


def _sky(sign_by_body):
    return {"bodies": {k: {"sign": v, "longitude": 0, "degree": 0} for k, v in sign_by_body.items()}}


def _phase(full_in_h=None, new_in_h=None):
    return {
        "sun_moon_angle_deg": 180.0 if full_in_h is not None else 0.0,
        "phase_key": "full_moon" if full_in_h is not None else "new_moon",
        "phase_human": "Full Moon" if full_in_h is not None else "New Moon",
        "nearest_full_moon": (
            {"at_utc": "2026-01-01T00:00:00+00:00", "hours_offset": full_in_h,
             "within_48h": abs(full_in_h) <= 48, "within_7d": abs(full_in_h) <= 168}
            if full_in_h is not None else None
        ),
        "nearest_new_moon": (
            {"at_utc": "2026-01-01T00:00:00+00:00", "hours_offset": new_in_h,
             "within_48h": abs(new_in_h) <= 48, "within_7d": abs(new_in_h) <= 168}
            if new_in_h is not None else None
        ),
    }


# ---------------------------------------------------------------------------
# 1. Full Moon within ±48h → Tier 1 dominant
# ---------------------------------------------------------------------------

def test_full_moon_within_48h_becomes_dominant():
    c = classify_signals(
        moon_phase=_phase(full_in_h=36),
        ingresses=[],
        aspects=[],
        house_activations={"clusters": []},
        sky=_sky({"Moon": "Libra", "Sun": "Aries"}),
    )
    assert c["dominant_signal"]["type"] == "full_moon"
    assert c["intensity"] == "high"
    assert "Full Moon" in c["why_today_is_different"]


# ---------------------------------------------------------------------------
# 2. Uranus ingress within ±14d → Tier 1
# ---------------------------------------------------------------------------

def test_uranus_ingress_within_14d_is_tier1():
    ing = [{
        "planet": "Uranus", "from_sign": "Taurus", "to_sign": "Gemini",
        "at_utc": "2026-01-10T00:00:00+00:00", "hours_offset": 240.0,
        "days_offset": 10.0,
        "is_outer": True, "is_heavy": False, "is_personal": False, "is_luminary": False,
    }]
    c = classify_signals(
        moon_phase=_phase(),
        ingresses=ing,
        aspects=[],
        house_activations={"clusters": []},
        sky=_sky({"Sun": "Aries"}),
    )
    assert c["dominant_signal"]["type"] == "outer_ingress"
    assert c["dominant_signal"]["planet"] == "Uranus"
    assert c["intensity"] == "high"
    assert "Uranus" in c["why_today_is_different"]


# ---------------------------------------------------------------------------
# 3. Tight aspect ≤0.5° outranks sign concentration
# ---------------------------------------------------------------------------

def test_tight_aspect_outranks_sign_cluster():
    # Three bodies in Libra — Tier 2 sign_cluster
    # A tight 0.3° Saturn square natal Sun — Tier 1
    tight = {
        "id": "Saturn-square-Sun", "transit": "Saturn", "aspect": "square",
        "natal": "Sun", "orb": 0.3, "applying": True, "is_tight": True,
        "exact_angle": 90.0, "natal_house": 10,
        "transit_sign": "Taurus", "natal_sign": "Aquarius",
    }
    c = classify_signals(
        moon_phase=_phase(),
        ingresses=[],
        aspects=[tight],
        house_activations={"clusters": []},
        sky=_sky({"Sun": "Libra", "Mercury": "Libra", "Venus": "Libra"}),
    )
    assert c["dominant_signal"]["type"] == "tight_aspect"
    assert c["dominant_signal"]["transit"] == "Saturn"


# ---------------------------------------------------------------------------
# 4. Moon sign change today → Tier 2 surfaces
# ---------------------------------------------------------------------------

def test_moon_sign_change_is_tier2():
    c = classify_signals(
        moon_phase=_phase(),
        ingresses=[],
        aspects=[],
        house_activations={"clusters": []},
        prior_moon_sign="Virgo",
        sky=_sky({"Moon": "Libra", "Sun": "Aries"}),
    )
    # With no Tier 1, Tier 2 takes dominance
    assert c["dominant_signal"]["type"] == "moon_sign_change"
    assert c["intensity"] == "medium"
    assert "Libra" in c["why_today_is_different"]


# ---------------------------------------------------------------------------
# 5. Same signature as yesterday → hash stable (continuity path)
# ---------------------------------------------------------------------------

def test_signature_hash_stable_for_same_dominance():
    c1 = classify_signals(
        moon_phase=_phase(full_in_h=24),
        ingresses=[],
        aspects=[],
        house_activations={"clusters": []},
        sky=_sky({"Sun": "Aries", "Moon": "Libra"}),
    )
    c2 = classify_signals(
        moon_phase=_phase(full_in_h=12),  # different offset, same dominance
        ingresses=[],
        aspects=[],
        house_activations={"clusters": []},
        sky=_sky({"Sun": "Aries", "Moon": "Libra"}),
    )
    h1 = compute_signature_hash(c1)
    h2 = compute_signature_hash(c2)
    assert h1 == h2, "signature should be stable when dominant signal is unchanged"

    # But changing dominance → hash must flip
    c3 = classify_signals(
        moon_phase=_phase(new_in_h=24),
        ingresses=[],
        aspects=[],
        house_activations={"clusters": []},
        sky=_sky({"Sun": "Aries", "Moon": "Libra"}),
    )
    h3 = compute_signature_hash(c3)
    assert h3 != h1


# ---------------------------------------------------------------------------
# 6. No major signal → still produces output
# ---------------------------------------------------------------------------

def test_no_signal_still_emits_low_intensity_output():
    # No Tier 1/2/3 detectable sources
    c = classify_signals(
        moon_phase=_phase(full_in_h=200, new_in_h=-300),  # far away
        ingresses=[],
        aspects=[],
        house_activations={"clusters": []},
        sky=_sky({"Sun": "Aries"}),
    )
    # No dominant, but payload still well-formed
    assert c["intensity"] == "low"
    assert c["dominant_signal"] is None
    assert "quiet day" in c["why_today_is_different"].lower()


def test_wide_aspect_dominates_when_no_better():
    # Only a wide 2.0° aspect
    wide = {
        "id": "Jupiter-trine-Moon", "transit": "Jupiter", "aspect": "trine",
        "natal": "Moon", "orb": 2.0, "applying": False, "is_tight": False,
        "exact_angle": 120.0, "natal_house": 4,
        "transit_sign": "Leo", "natal_sign": "Aries",
    }
    c = classify_signals(
        moon_phase=_phase(full_in_h=200, new_in_h=-200),
        ingresses=[],
        aspects=[wide],
        house_activations={"clusters": []},
        sky=_sky({"Sun": "Aries"}),
    )
    assert c["dominant_signal"]["type"] == "wide_aspect"
    assert c["intensity"] == "low"


# ---------------------------------------------------------------------------
# 7. why_today_is_different explains the dominance choice
# ---------------------------------------------------------------------------

def test_why_line_explains_ingress():
    ing = [{
        "planet": "Pluto", "from_sign": "Capricorn", "to_sign": "Aquarius",
        "at_utc": "2026-01-01T00:00:00+00:00", "hours_offset": 100,
        "days_offset": 4.2, "is_outer": True, "is_heavy": False,
        "is_personal": False, "is_luminary": False,
    }]
    c = classify_signals(
        moon_phase=_phase(),
        ingresses=ing,
        aspects=[],
        house_activations={"clusters": []},
        sky=_sky({"Sun": "Aries"}),
    )
    why = c["why_today_is_different"]
    assert "Pluto" in why
    assert "Capricorn" in why and "Aquarius" in why
