"""HD channel-detector regression for the Gate-10 omission fix
================================================================

Build marker:  hd-channel-1020-1034-fix
Root cause:    HD_CHANNELS_CLEAN was missing the two Gate-10 connection
               pairs (10-20 Awakening, 10-34 Exploration).  Other Gate-10
               channel (10-57 Perfected Form) was present.

This test asserts the detector now emits all three Gate-10 channels when
the corresponding co-gates are active, using Jaan's chart as the canonical
fixture, and that pre-existing users' channel sets are unchanged.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

# Ensure /app/backend is importable when running via pytest from repo root.
HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(HERE)
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

from calculations.human_design import (
    HD_CHANNELS_CLEAN,
    get_defined_channels,
    get_human_design_chart,
)


# ----------------------------------------------------------------------
# 1. Table-level assertion — the canonical 36-channel list must include
#    every Gate-10 connection pair.
# ----------------------------------------------------------------------
def _pair_set():
    return {tuple(sorted((g1, g2))) for g1, g2, *_ in HD_CHANNELS_CLEAN}


def test_table_contains_all_gate_10_channels():
    pairs = _pair_set()
    assert (10, 20) in pairs, "Channel of Awakening (10-20) missing"
    assert (10, 34) in pairs, "Channel of Exploration (10-34) missing"
    assert (10, 57) in pairs, "Channel of Perfected Form (10-57) regressed"


# ----------------------------------------------------------------------
# 2. Synthetic detector probe — does NOT depend on ephemeris or DB.
# ----------------------------------------------------------------------
def _channel_keys(channels):
    """Return {'10-20', '20-34', …} style set for assertion ergonomics."""
    out = set()
    for g1, g2, *_ in channels:
        a, b = sorted((g1, g2))
        out.add(f"{a}-{b}")
    return out


def test_detector_emits_1020_when_gates_10_and_20_active():
    chans = get_defined_channels({10, 20})
    assert "10-20" in _channel_keys(chans)


def test_detector_emits_1034_when_gates_10_and_34_active():
    chans = get_defined_channels({10, 34})
    assert "10-34" in _channel_keys(chans)


def test_detector_emits_2034_when_gates_20_and_34_active():
    """Pre-existing 20-34 Charisma must remain untouched."""
    chans = get_defined_channels({20, 34})
    assert "20-34" in _channel_keys(chans)


def test_jaan_synthetic_all_three_channels():
    """Jaan's active gates include 10, 20, 34 — all three pairs must fire."""
    jaan_gates = {1, 2, 6, 7, 8, 10, 13, 14, 17, 20, 24, 28, 29,
                  34, 36, 47, 50, 58, 59}
    keys = _channel_keys(get_defined_channels(jaan_gates))
    # New (the bug fix):
    assert "10-20" in keys, f"10-20 still missing — keys={sorted(keys)}"
    assert "10-34" in keys, f"10-34 still missing — keys={sorted(keys)}"
    # Pre-existing, must remain:
    assert "20-34" in keys, "20-34 regressed"
    assert "1-8"   in keys, "1-8 (Inspiration) regressed"
    assert "2-14"  in keys, "2-14 (Beat) regressed"
    assert "6-59"  in keys, "6-59 (Intimacy) regressed"


def test_no_phantom_channels_from_random_gates():
    """A gate set with no valid pairs must return zero channels."""
    # Pick gates that don't form ANY canonical channel together.
    isolated = {1, 14, 39}  # 1↔8 partner missing, 14↔2 partner missing, 39↔55 partner missing
    chans = get_defined_channels(isolated)
    assert chans == []


# ----------------------------------------------------------------------
# 3. End-to-end ephemeris fixture — Jaan's actual birth data.
# ----------------------------------------------------------------------
JAAN_BIRTH_UTC = datetime(1973, 12, 9, 13, 50, tzinfo=timezone.utc)  # 21:50 +08:00
JAAN_LAT = 3.1702996
JAAN_LON = 101.699563


def test_jaan_ephemeris_emits_1020_and_1034():
    chart = get_human_design_chart(JAAN_BIRTH_UTC, JAAN_LAT, JAAN_LON)
    channels = chart.get("defined_channels") or []
    keys = {
        f"{min(c['gate1'], c['gate2'])}-{max(c['gate1'], c['gate2'])}"
        for c in channels
    }
    assert "10-20" in keys, f"Jaan: 10-20 missing.  keys={sorted(keys)}"
    assert "10-34" in keys, f"Jaan: 10-34 missing.  keys={sorted(keys)}"
    assert "20-34" in keys, "Jaan: 20-34 regressed"
    # Pre-existing channels (zero-padded forms 0108/0214/0659):
    assert "1-8"   in keys, "Jaan: 1-8 regressed"
    assert "2-14"  in keys, "Jaan: 2-14 regressed"
    assert "6-59"  in keys, "Jaan: 6-59 regressed"
    # Profile + type must NOT have shifted as a result of the channel fix.
    assert chart.get("profile") == "4/6"
    assert chart.get("type") == "Manifesting Generator"


if __name__ == "__main__":
    # Make this runnable as a script for quick iteration.
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  PASS  {name}")
            except AssertionError as e:
                print(f"  FAIL  {name}: {e}")
                raise
    print("\nALL TESTS PASSED")
