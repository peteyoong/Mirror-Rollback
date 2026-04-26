"""
Tests for detect_identity_pattern_recurrence() — covers:
  1. cold_start (no journals + no pattern_memory)
  2. first_appearance (pattern_memory match_count=1)
  3. returning pattern (match_count=2 OR strong journal signal alone)
  4. recurring pattern (match_count>=3)
  5. malformed pattern_memory docs (corrupt fields, wrong types)
  6. pattern_memory state field takes priority over count
  7. cold start + strong journal signal = returning_pattern
  8. human_label generation matches state
  9. recurrence metadata is forwarded by generate_relationship_pattern
 10. exposed payload has no raw IDs/scores

Run with:
    cd /app/backend && python -m pytest tests/test_identity_pattern_recurrence.py -v
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

import pytest

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.relationship_insight_engine import (  # noqa: E402
    detect_identity_pattern_recurrence,
    generate_relationship_pattern,
)


# ---------------------------------------------------------------------------
# Fake DB doubles — async-compatible MongoDB-ish
# ---------------------------------------------------------------------------

class _FakeCursor:
    def __init__(self, items: List[Dict[str, Any]]):
        self._items = items

    def sort(self, *args, **kwargs):
        return self

    def limit(self, n: int):
        self._items = self._items[:n]
        return self

    async def to_list(self, length: Optional[int] = None):
        if length is None:
            return list(self._items)
        return list(self._items[:length])


class _FakeCollection:
    def __init__(self, docs: List[Dict[str, Any]]):
        self._docs = docs

    async def find_one(self, query: Dict[str, Any]):
        for d in self._docs:
            if all(d.get(k) == v for k, v in query.items()):
                return dict(d)
        return None

    def find(self, query: Dict[str, Any]):
        matches = [
            dict(d) for d in self._docs
            if all(d.get(k) == v for k, v in query.items())
        ]
        return _FakeCursor(matches)


class _FakeDB:
    def __init__(
        self,
        pattern_memory_docs: Optional[List[Dict[str, Any]]] = None,
        journals_docs: Optional[List[Dict[str, Any]]] = None,
    ):
        self.pattern_memory = _FakeCollection(pattern_memory_docs or [])
        self.journals = _FakeCollection(journals_docs or [])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

USER_ID = "test_user_001"
USER_TYPE = "initiator"


def _journal(content: str) -> Dict[str, Any]:
    return {"user_id": USER_ID, "content": content, "created_at": "2026-04-26"}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cold_start_no_history():
    """No journals + no pattern_memory → memory_state='no_history'."""
    db = _FakeDB()
    out = await detect_identity_pattern_recurrence(db, USER_ID, USER_TYPE)
    assert out["memory_state"] == "no_history"
    assert out["match_count"] == 0
    assert out["dominant_tension"] is None
    assert out["recent_tensions"] == []
    assert out["recurrence_confidence"] == "low"
    assert out["human_label"] is None
    assert out["recurrence_detected"] is False
    assert out["sources"]["pattern_memory_used"] is False
    assert out["sources"]["journal_signal"] == "none"


@pytest.mark.asyncio
async def test_first_appearance():
    """match_count=1 → first_appearance, no human label, no recurrence_detected."""
    db = _FakeDB(
        pattern_memory_docs=[{
            "user_id": USER_ID,
            "memory_state": "first_appearance",
            "match_count": 1,
            "dominant_tension": "You reach before they're ready",
        }],
    )
    out = await detect_identity_pattern_recurrence(db, USER_ID, USER_TYPE)
    assert out["memory_state"] == "first_appearance"
    assert out["match_count"] == 1
    assert out["dominant_tension"] == "You reach before they're ready"
    assert out["human_label"] is None
    assert out["recurrence_detected"] is False
    assert out["recurrence_confidence"] == "low"


@pytest.mark.asyncio
async def test_returning_pattern_via_match_count():
    """match_count=2 → returning_pattern with proper human label."""
    db = _FakeDB(
        pattern_memory_docs=[{
            "user_id": USER_ID,
            "memory_state": "returning_pattern",
            "match_count": 2,
            "dominant_tension": "You over-translate the room",
            "recent_tensions": ["over-translate", "absorb tension early"],
        }],
    )
    out = await detect_identity_pattern_recurrence(db, USER_ID, USER_TYPE)
    assert out["memory_state"] == "returning_pattern"
    assert out["match_count"] == 2
    assert out["human_label"] == "This is becoming familiar."
    assert out["recurrence_detected"] is True
    assert out["recurrence_confidence"] in ("medium", "low")
    assert out["recent_tensions"] == ["over-translate", "absorb tension early"]


@pytest.mark.asyncio
async def test_recurring_pattern_match_count_gte_3():
    """match_count>=3 → recurring_pattern with 'You've been here before.' label."""
    db = _FakeDB(
        pattern_memory_docs=[{
            "user_id": USER_ID,
            "memory_state": "recurring_pattern",
            "match_count": 5,
            "dominant_tension": "You absorb pressure before naming your own boundary",
            "recent_tensions": ["absorb pressure", "translate first", "name boundary last"],
        }],
    )
    out = await detect_identity_pattern_recurrence(db, USER_ID, USER_TYPE)
    assert out["memory_state"] == "recurring_pattern"
    assert out["match_count"] == 5
    assert out["human_label"] == "You've been here before."
    assert out["recurrence_detected"] is True
    assert out["recurrence_confidence"] == "high"


@pytest.mark.asyncio
async def test_recurring_pattern_with_low_match_count_uses_state():
    """If memory_state='recurring_pattern' but match_count is missing, still recurring."""
    db = _FakeDB(
        pattern_memory_docs=[{
            "user_id": USER_ID,
            "memory_state": "recurring_pattern",
            # no match_count present
        }],
    )
    out = await detect_identity_pattern_recurrence(db, USER_ID, USER_TYPE)
    assert out["memory_state"] == "recurring_pattern"
    # Engine should normalize match_count up to >=3 when state is recurring
    assert out["match_count"] >= 3
    assert out["human_label"] == "You've been here before."


@pytest.mark.asyncio
async def test_cold_start_with_strong_journal_signal_promotes_to_returning():
    """No pattern_memory but strong journal keyword signal → returning_pattern."""
    # 'initiator' keywords are: reach, start, wait, silence, respond, ignored
    # We need >= 4 unique keywords across >= 3 journals
    journals = [
        _journal("I keep wanting to reach out first and then I just wait"),
        _journal("the silence after sending a message is too loud, no respond"),
        _journal("I started to start the conversation but felt ignored again"),
    ]
    db = _FakeDB(pattern_memory_docs=[], journals_docs=journals)
    out = await detect_identity_pattern_recurrence(db, USER_ID, "initiator")
    assert out["sources"]["journal_signal"] == "strong"
    assert out["memory_state"] == "returning_pattern"
    assert out["recurrence_detected"] is True
    assert out["human_label"] == "This is becoming familiar."


@pytest.mark.asyncio
async def test_malformed_pattern_memory_docs():
    """Corrupt fields (wrong types, missing keys) must NOT raise — degrade gracefully."""
    db = _FakeDB(
        pattern_memory_docs=[{
            "user_id": USER_ID,
            "memory_state": 42,                # wrong type (int)
            "match_count": "not-a-number",     # wrong type (str)
            "dominant_tension": None,          # null
            "recent_tensions": "single|piped|string|with|extras",  # str instead of list (supported)
        }],
    )
    out = await detect_identity_pattern_recurrence(db, USER_ID, USER_TYPE)
    # State falls back because '42' is not a recognised state string
    assert out["memory_state"] == "no_history"
    assert out["match_count"] == 0
    assert out["dominant_tension"] is None
    # Piped string should be split into list, capped at 3
    assert out["recent_tensions"] == ["single", "piped", "string"]
    assert out["recurrence_detected"] is False


@pytest.mark.asyncio
async def test_malformed_recent_tensions_list_with_invalid_items():
    """List with invalid items (None, dicts) should be filtered."""
    db = _FakeDB(
        pattern_memory_docs=[{
            "user_id": USER_ID,
            "memory_state": "returning_pattern",
            "match_count": 2,
            "recent_tensions": ["valid one", None, {"bad": "dict"}, "another valid", 42, ""],
        }],
    )
    out = await detect_identity_pattern_recurrence(db, USER_ID, USER_TYPE)
    # Strings and stringifiable scalars kept; dicts and None and empty filtered
    assert "valid one" in out["recent_tensions"]
    assert "another valid" in out["recent_tensions"]
    assert "42" in out["recent_tensions"]
    assert None not in out["recent_tensions"]
    assert {} not in out["recent_tensions"]
    assert len(out["recent_tensions"]) <= 3


@pytest.mark.asyncio
async def test_human_label_omitted_for_first_appearance():
    """first_appearance must NOT surface 'You've been here before' — too premature."""
    db = _FakeDB(
        pattern_memory_docs=[{"user_id": USER_ID, "memory_state": "first_appearance",
                              "match_count": 1}],
    )
    out = await detect_identity_pattern_recurrence(db, USER_ID, USER_TYPE)
    assert out["human_label"] is None


@pytest.mark.asyncio
async def test_no_raw_ids_or_scores_exposed():
    """Output schema must not contain raw signature IDs, hashes, or numeric scores."""
    db = _FakeDB(
        pattern_memory_docs=[{
            "user_id": USER_ID,
            "memory_state": "recurring_pattern",
            "match_count": 4,
            "dominant_tension": "test",
            "_id": "internal_objectid_12345",            # internal — must NOT leak
            "signature_hash": "abc123deadbeef",          # internal — must NOT leak
            "score": 0.87,                               # internal — must NOT leak
        }],
    )
    out = await detect_identity_pattern_recurrence(db, USER_ID, USER_TYPE)
    forbidden = {"_id", "signature_hash", "score", "raw_signature", "internal_id"}
    for k in out.keys():
        assert k not in forbidden, f"{k} leaked into recurrence payload"
    # Sources block is allowed but must only carry safe metadata
    assert set(out["sources"].keys()) == {"pattern_memory_used", "journal_signal"}


def test_generate_relationship_pattern_forwards_recurrence():
    """generate_relationship_pattern surfaces recurrence block when given data."""
    user_profile = {"user_id": "u1", "enneagram": {}, "astrology": {}}
    rec_data = {
        "memory_state": "recurring_pattern",
        "match_count": 5,
        "dominant_tension": "You over-translate",
        "recent_tensions": ["a", "b", "c"],
        "recurrence_confidence": "high",
        "human_label": "You've been here before.",
        "recurrence_detected": True,
    }
    out = generate_relationship_pattern(user_profile=user_profile, recurrence_data=rec_data)
    assert out["success"] is True
    assert "recurrence" in out
    rec = out["recurrence"]
    assert rec["memory_state"] == "recurring_pattern"
    assert rec["match_count"] == 5
    assert rec["dominant_tension"] == "You over-translate"
    assert rec["recurrence_confidence"] == "high"
    assert rec["human_label"] == "You've been here before."
    # Same loop language is added to what_teaching when recurrence_detected=True
    assert "Same loop. Different face." in out["what_teaching"]


def test_generate_relationship_pattern_no_recurrence_block_on_cold_start():
    """If recurrence_data is None, no `recurrence` key is exposed."""
    user_profile = {"user_id": "u1", "enneagram": {}, "astrology": {}}
    out = generate_relationship_pattern(user_profile=user_profile, recurrence_data=None)
    assert out["success"] is True
    assert "recurrence" not in out
    # Stable copy (no "Same loop" line)
    assert "Same loop. Different face." not in out["what_teaching"]


# ---------------------------------------------------------------------------
# Allow running standalone without pytest
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import inspect

    async def _run():
        cases = [(n, fn) for n, fn in globals().items()
                 if n.startswith("test_") and callable(fn)]
        passed = 0
        failed: List[str] = []
        for name, fn in cases:
            try:
                if inspect.iscoroutinefunction(fn):
                    await fn()
                else:
                    fn()
                print(f"  ✓ {name}")
                passed += 1
            except Exception as e:  # noqa: BLE001
                print(f"  ✗ {name} — {e}")
                failed.append(name)
        print(f"\n{passed}/{len(cases)} passed")
        if failed:
            print("Failures:", failed)
            raise SystemExit(1)

    asyncio.run(_run())
