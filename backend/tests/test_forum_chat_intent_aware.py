"""
Forum Chat (Ask Mirror) — Slice A intent-aware routing regression
==================================================================

Covers:
  1. Layered relationship block builder — asker-only + asker+spouse.
  2. Spouse auto-promotion when life-domain == relationship and the
     asker has a stored spouse mapping, even if the message never
     names the spouse or uses the word "spouse".
  3. Pete + Mel marriage prompt-assembly regression — the orchestrator
     addendum must lead with Pete's relationship architecture (Gemini
     Descendant) and include Mel's architecture before any Sun / HD /
     Numerology mention.

Run:
    cd /app/backend && python -m pytest tests/test_forum_chat_intent_aware.py -v
"""
from __future__ import annotations

import asyncio
import pytest

from services.astrology_domain_context import (
    build_layered_relationship_block,
    build_relationship_context,
)


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------
# `asyncio.run` closes the default event loop, which contaminates other
# test modules in the same session (e.g. test_lifecycle_engine.py).  Use
# an isolated loop and restore the previous one on exit.

def _run_iso(coro):
    try:
        prev_loop = asyncio.get_event_loop_policy().get_event_loop()
    except Exception:
        prev_loop = None
    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)
    try:
        return new_loop.run_until_complete(coro)
    finally:
        new_loop.close()
        if prev_loop is not None and not prev_loop.is_closed():
            asyncio.set_event_loop(prev_loop)
        else:
            # Re-create a fresh default loop so downstream tests can use it.
            asyncio.set_event_loop(asyncio.new_event_loop())


# ---------------------------------------------------------------------------
# Fixtures — Pete and Mel chart shells (real placements pulled from prod)
# ---------------------------------------------------------------------------

PETE_CHART = {
    "astrology": {
        "planets": {
            "Sun":     {"sign": "Pisces",     "degree": 16.2, "house": 3},
            "Moon":    {"sign": "Aries",      "degree": 16.5, "house": 4},
            "Mercury": {"sign": "Aquarius",   "degree": 22.9, "house": 2},
            "Venus":   {"sign": "Aquarius",   "degree": 23.2, "house": 2},
            "Mars":    {"sign": "Aries",      "degree":  7.2, "house": 4},
            "Jupiter": {"sign": "Leo",        "degree":  4.4, "house": 8},
            "Saturn":  {"sign": "Pisces",     "degree": 19.9, "house": 3},
            "Pluto":   {"sign": "Leo",        "degree":  4.0, "house": 8},
        },
        "houses": {
            "system": "Equal",
            "formatted_cusps": [
                "25°Sagittarius", "25°Capricorn", "27°Aquarius", "29°Pisces",
                "28°Aries", "27°Taurus", "25°Gemini", "1°Leo",
                "31°Leo", "28°Virgo", "21°Libra", "22°Scorpio",
            ],
        },
        "angles": {
            "asc": {"sign": "Sagittarius", "degree": 25.5},
            "dc":  {"sign": "Gemini",      "degree": 25.8},
            "mc":  {"sign": "Virgo",       "degree": 33.2},
            "ic":  {"sign": "Aries",       "degree":  3.5},
        },
    },
    "human_design": {"type": "Manifestor", "profile": "5/1"},
    "numerology":   {"life_path": 7},
}

# Mel placeholder — exact placements not needed for this regression; we just
# need a chart where Descendant != Pete's and Venus is locatable.
MEL_CHART = {
    "astrology": {
        "planets": {
            "Sun":   {"sign": "Aries",   "degree": 10.0, "house": 9},
            "Moon":  {"sign": "Leo",     "degree": 12.0, "house": 1},
            "Venus": {"sign": "Pisces",  "degree":  4.0, "house": 8},
            "Mars":  {"sign": "Aries",   "degree": 22.0, "house": 9},
        },
        "houses": {
            "system": "Equal",
            "formatted_cusps": [
                {"house":  1, "sign": "Leo",         "degree": 12.0},
                {"house":  2, "sign": "Virgo",       "degree": 12.0},
                {"house":  3, "sign": "Libra",       "degree": 12.0},
                {"house":  4, "sign": "Scorpio",     "degree": 12.0},
                {"house":  5, "sign": "Sagittarius", "degree": 12.0},
                {"house":  6, "sign": "Capricorn",   "degree": 12.0},
                {"house":  7, "sign": "Aquarius",    "degree": 12.0},
                {"house":  8, "sign": "Pisces",      "degree": 12.0},
                {"house":  9, "sign": "Aries",       "degree": 12.0},
                {"house": 10, "sign": "Taurus",      "degree": 12.0},
                {"house": 11, "sign": "Gemini",      "degree": 12.0},
                {"house": 12, "sign": "Cancer",      "degree": 12.0},
            ],
        },
        "angles": {
            "asc": {"sign": "Leo",      "degree": 12.0},
            "dc":  {"sign": "Aquarius", "degree": 12.0},
        },
    },
}


# ---------------------------------------------------------------------------
# 1.  build_layered_relationship_block — asker-only path
# ---------------------------------------------------------------------------

def test_layered_block_pete_solo_no_spouse():
    block = build_layered_relationship_block(
        asker_chart=PETE_CHART, asker_name="Pete",
    )
    assert "LAYERED RELATIONSHIP PROOF BLOCK" in block
    # Layer 1 names Pete's actual Descendant (Gemini), not the fixture's Aquarius
    assert "Gemini" in block
    assert "Mercury" in block      # 7th-house ruler of Gemini
    assert "Venus: Aquarius" in block
    # Layer 2 must explicitly say no spouse stored
    assert "no stored spouse mapping" in block.lower()
    # Bans
    assert "NEVER open" in block
    assert "Sun sign" in block
    assert "Human Design" in block
    assert "Numerology" in block


# ---------------------------------------------------------------------------
# 2.  build_layered_relationship_block — asker + spouse path
# ---------------------------------------------------------------------------

def test_layered_block_pete_plus_mel_spouse():
    block = build_layered_relationship_block(
        asker_chart=PETE_CHART, asker_name="Pete",
        spouse_chart=MEL_CHART, spouse_name="Mel",
        relationship_role="spouse",
    )
    # Header carries both names
    assert "PETE + MEL" in block
    # Layer 1 — Pete architecture
    layer1_idx = block.find("LAYER 1 — Pete")
    assert layer1_idx > 0
    # Layer 2 — Mel architecture (must be present and ordered after Layer 1)
    layer2_idx = block.find("LAYER 2 — Mel")
    assert layer2_idx > layer1_idx
    # Layer 3 — Relationship field (Pete ↔ Mel)
    layer3_idx = block.find("LAYER 3 — RELATIONSHIP FIELD")
    assert layer3_idx > layer2_idx
    # Both 7th-house signs named
    assert "Gemini" in block   # Pete's DC / 7th
    assert "Aquarius" in block # Mel's DC / 7th
    # The relationship-field rule names BOTH 7th-house signs as the meeting point
    assert "Gemini meeting Aquarius" in block or "Aquarius meeting Gemini" in block


def test_layered_block_bans_solo_lens_lead_when_spouse_present():
    block = build_layered_relationship_block(
        asker_chart=PETE_CHART, asker_name="Pete",
        spouse_chart=MEL_CHART, spouse_name="Mel",
        relationship_role="spouse",
    )
    # Sun-sign ban appears in absolute-rules section
    ban_idx = block.find("ABSOLUTE RULES")
    sun_ban_idx = block.find("NEVER open with the Sun sign", ban_idx)
    assert sun_ban_idx > 0
    # And the ban comes AFTER the partnership-architecture instructions
    open_rule_idx = block.find("OPEN the response with the partnership architecture", ban_idx)
    assert open_rule_idx > 0
    assert open_rule_idx < sun_ban_idx


# ---------------------------------------------------------------------------
# 3.  Forum-orchestrator level: spouse auto-promotion + addendum ordering
# ---------------------------------------------------------------------------
# We simulate the orchestrator's addendum assembly with a mock DB.  The
# spouse auto-promoter MUST find Mel via relationship_mappings even when
# the message never says "Mel" / "spouse" / "wife".

class _MockCursor:
    def __init__(self, docs): self._docs = docs
    async def to_list(self, length=None): return self._docs
    def sort(self, *a, **kw): return self
    def limit(self, n): return self

class _MockCollection:
    def __init__(self, docs): self._docs = docs
    def find(self, query=None):
        return _MockCursor(self._filter(query or {}))
    async def find_one(self, query):
        for d in self._docs:
            if all(d.get(k) == v for k, v in query.items()):
                return d
        return None
    def _filter(self, q):
        return [d for d in self._docs if all(d.get(k) == v for k, v in q.items() if not isinstance(v, dict))]

class _MockDB:
    def __init__(self):
        self.relationship_mappings = _MockCollection([{
            "asker_user_id":     "pete",
            "target_user_id":    "mel",
            "relationship_type": "spouse",
            "target_name":       "Mel",
        }])
        # Charts collection — find_one by user_id
        self.charts = _MockCollection([
            {"user_id": "pete", **PETE_CHART},
            {"user_id": "mel",  **MEL_CHART},
        ])
        # Users — find_one by _id; our mock matches by id field
        self.users = _MockCollection([
            {"_id": "pete", "name": "Pete"},
            {"_id": "mel",  "name": "Mel"},
        ])
        self.forum_members = _MockCollection([])

# The orchestrator calls ObjectId(user_id) — patch with a passthrough.

@pytest.fixture
def patched_objectid(monkeypatch):
    import services.forum_mirror_orchestrator as fmo
    monkeypatch.setattr(fmo, "ObjectId", lambda x: x)
    yield


def test_spouse_auto_promote_marriage_question(patched_objectid, monkeypatch):
    """When Pete asks a marriage question with no name mentioned, the
    orchestrator must auto-promote Mel as the resolved target via the
    relationship_mappings spouse entry."""
    from services.forum_mirror_orchestrator import (
        build_relational_orchestrator_payload,
    )
    # Patch the relationship_resolver dependency to avoid Mongo work
    import services.forum_mirror_orchestrator as fmo

    async def _fake_resolver(**kw):
        return {
            "relationship_detected": True,
            "relationship_role":     "spouse",
            "relationship_source":   "explicit_map",
            "closeness":             "close",
            "emotional_weight":      "high",
        }
    # Inject into the dynamic import path
    import services.relationship_resolver as rr
    monkeypatch.setattr(rr, "resolve_relationship", _fake_resolver)

    db = _MockDB()
    payload = _run_iso(build_relational_orchestrator_payload(
        db=db,
        forum_id="forum1",
        asker_user_id="pete",
        message="Tell me about what my chart says about marriage",
        mode="self",
        target_member_id=None,
    ))

    # Life domain detected
    assert payload["life_domain"] == "relationship"
    # Spouse was auto-promoted
    assert payload["spouse_auto_promoted"] is True
    assert (payload["resolved_target"] or {}).get("target_name") == "Mel"
    assert (payload["resolved_target"] or {}).get("source") == "spouse_auto_promote"
    # Layered block was emitted
    assert payload["layered_block_emitted"] is True

    # Addendum content + ordering checks
    add = payload["system_prompt_addendum"]
    assert "LAYERED RELATIONSHIP PROOF BLOCK" in add
    assert "PETE + MEL" in add

    # The layered block must appear BEFORE the resolved-target identity
    # assertion line ("RESOLVED TARGET: Mel ...") to lead the prompt.
    layered_idx = add.find("LAYERED RELATIONSHIP PROOF BLOCK")
    resolved_idx = add.find("RESOLVED TARGET: Mel")
    assert layered_idx > 0 and resolved_idx > 0
    assert layered_idx < resolved_idx


def test_non_relationship_question_no_layered_block(patched_objectid, monkeypatch):
    """A career question must NOT trigger spouse auto-promotion or
    the layered relationship block."""
    from services.forum_mirror_orchestrator import (
        build_relational_orchestrator_payload,
    )
    db = _MockDB()
    payload = _run_iso(build_relational_orchestrator_payload(
        db=db,
        forum_id="forum1",
        asker_user_id="pete",
        message="What does my chart say about my career?",
        mode="self",
        target_member_id=None,
    ))
    assert payload["life_domain"] == "career"
    assert payload["spouse_auto_promoted"] is False
    assert payload["layered_block_emitted"] is False
    assert "LAYERED RELATIONSHIP PROOF BLOCK" not in payload["system_prompt_addendum"]


# ---------------------------------------------------------------------------
# 4.  Prompt-assembly regression — relationship architecture leads
# ---------------------------------------------------------------------------

def test_pete_marriage_layered_block_orders_before_sun_sign():
    """Stand-in for the full Forum Chat prompt assembly.  The layered
    relationship block goes ABOVE the generic FORUM CONTEXT in the
    real route; the test confirms the orchestrator addendum itself
    keeps relationship architecture above any Sun/HD/Numerology
    references it might internally include (in the ABSOLUTE RULES
    ban clause)."""
    block = build_layered_relationship_block(
        asker_chart=PETE_CHART, asker_name="Pete",
        spouse_chart=MEL_CHART, spouse_name="Mel",
        relationship_role="spouse",
    )
    # Architecture leads
    arch_idx = min(i for i in (
        block.find("Gemini"),
        block.find("Descendant"),
        block.find("7th House"),
    ) if i >= 0)
    sun_idx = block.find("Sun sign")
    hd_idx = block.find("Human Design")
    np_idx = block.find("Numerology")
    assert arch_idx >= 0
    # All bans appear AFTER architecture
    assert sun_idx > arch_idx
    assert hd_idx > arch_idx
    assert np_idx > arch_idx
