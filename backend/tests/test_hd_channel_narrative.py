"""test_hd_channel_narrative.py — per-channel narrative tests
================================================================
Asserts that EVERY HD channel produces a {gift, tension, practical_use}
triplet, that curated overrides win, that template fallback never
produces empty strings, and that name placeholders never leak.
"""
from __future__ import annotations
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.hd_channel_narrative import (
    compute_channel_narrative, CURATED, NARRATIVE_VERSION,
)
from services.forum_hd_mapping import HD_CHANNELS


def test_returns_required_keys_for_curated():
    out = compute_channel_narrative(
        channel_id="6-59", channel_name="Intimacy",
        theme="emotional bonding", relational="closeness",
        name_a="Pete", name_b="Mel",
    )
    assert {"gift", "tension", "practical_use"} <= set(out.keys())
    assert all(isinstance(v, str) and len(v.strip()) > 0 for v in out.values())


def test_curated_inlines_names():
    out = compute_channel_narrative(
        channel_id="1-8", channel_name="Inspiration",
        theme="creative direction", relational="creative momentum",
        name_a="Ana", name_b="Pete",
    )
    full = " ".join(out.values())
    assert "Ana" in full and "Pete" in full
    assert "{a}" not in full and "{b}" not in full
    assert "{name_a}" not in full and "{name_b}" not in full


def test_template_fallback_for_uncurated():
    out = compute_channel_narrative(
        channel_id="59-99-unknown", channel_name="Some Channel",
        theme="hypothetical theme", relational="hypothetical relation",
        name_a="Ana", name_b="Pete",
    )
    assert {"gift", "tension", "practical_use"} <= set(out.keys())
    assert all(len(v) > 10 for v in out.values()), out


def test_every_hd_channel_yields_narrative():
    """Smoke test: every channel id in HD_CHANNELS produces a non-empty triplet."""
    missing = []
    for cid, data in HD_CHANNELS.items():
        n = compute_channel_narrative(
            channel_id=cid, channel_name=data["name"],
            theme=data["theme"], relational=data["relational"],
            name_a="A", name_b="B",
        )
        if not n or not all(n.get(k, "").strip() for k in ("gift", "tension", "practical_use")):
            missing.append(cid)
    assert not missing, f"channels missing narrative: {missing}"


def test_no_mystical_fatalism_terms():
    forbidden = ("destined", "soulmate", "karmic", "fate", "destiny")
    for cid in CURATED.keys():
        out = compute_channel_narrative(
            channel_id=cid, channel_name="", theme="", relational="",
            name_a="A", name_b="B",
        )
        joined = " ".join(out.values()).lower()
        for term in forbidden:
            assert term not in joined, f"channel {cid} leaked forbidden term '{term}': {joined}"


def test_version_marker_exposed():
    assert NARRATIVE_VERSION.startswith("hd-channel-narrative")
