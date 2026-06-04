"""Regression tests for the lifecycle engine — astrology-lifecycle-v1.

Pete is the canonical fixture: born 1968-04-01 01:25 UTC+07:00, age ~58.
He should be DURING his 2nd Saturn Return (peak ~2027-03), with 1st
Saturn Return in 1997 (after) and 3rd in 2056 (before).
"""
import asyncio
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, "/app/backend")

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

from services.lifecycle_engine import (
    compute_lifecycle,
    build_lifecycle_proof_block,
)
from services.astrology_chat_router import classify_astrology_intent

load_dotenv("/app/backend/.env")


def _load_pete_sync():
    """Load Pete's chart + birth_utc synchronously for pytest-style use."""
    async def _go():
        cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
        db = cli[os.environ.get("DB_NAME", "test_database")]
        u = await db.users.find_one({"email": "pete@pulsifi.me"})
        c = await db.charts.find_one({"user_id": str(u["_id"])})
        return c["astrology"]
    return asyncio.get_event_loop().run_until_complete(_go())


# Regression set per user spec --------------------------------------------------
def test_pete_saturn_return_active_is_second():
    chart = _load_pete_sync()
    md    = chart["metadata"]
    birth = datetime.fromisoformat(md["input_datetime_utc"]).replace(tzinfo=timezone.utc)
    env = compute_lifecycle(chart, birth, event_keys=["saturn_return"])
    assert env["success"]
    active = env["active_by_key"]["saturn_return"]
    assert active["instance"] == 2,    f"expected 2nd return, got {active['instance']}"
    assert active["phase"]    == "during", f"expected during, got {active['phase']}"

def test_pete_saturn_return_first_is_after():
    chart = _load_pete_sync()
    md    = chart["metadata"]
    birth = datetime.fromisoformat(md["input_datetime_utc"]).replace(tzinfo=timezone.utc)
    env = compute_lifecycle(chart, birth, event_keys=["saturn_return"])
    first = next(e for e in env["events"] if e["instance"] == 1)
    assert first["phase"] == "after"
    assert first["exact_passes"][0].startswith("199")     # 1997 returns

def test_pete_saturn_return_third_is_before():
    chart = _load_pete_sync()
    md    = chart["metadata"]
    birth = datetime.fromisoformat(md["input_datetime_utc"]).replace(tzinfo=timezone.utc)
    env = compute_lifecycle(chart, birth, event_keys=["saturn_return"])
    third = next(e for e in env["events"] if e["instance"] == 3)
    assert third["phase"] == "before"
    assert third["exact_passes"][0].startswith("205")     # 2056

def test_proof_block_distinguishes_second_return_meaning():
    chart = _load_pete_sync()
    md    = chart["metadata"]
    birth = datetime.fromisoformat(md["input_datetime_utc"]).replace(tzinfo=timezone.utc)
    env = compute_lifecycle(chart, birth, event_keys=["saturn_return"])
    block = build_lifecycle_proof_block(env, user_phrasing_mode="personal")
    assert "2nd Saturn Return" in block
    assert "legacy" in block.lower()
    assert "young-adult maturation" in block          # exclusion clause present
    assert "ANSWER THE PERSON BEFORE THE CONCEPT" in block

def test_classifier_personal():
    r = classify_astrology_intent("Tell me about my Saturn return")
    assert r and r["data_mode"] == "lifecycle"
    assert r["event_keys"] == ["saturn_return"]
    assert r["phrasing"]   == "personal"

def test_classifier_concept_no_anchor():
    r = classify_astrology_intent("What is a Saturn return?")
    assert r and r["phrasing"] == "concept_no_anchor"

def test_classifier_hybrid_concept():
    r = classify_astrology_intent("What is a Saturn return in my chart?")
    assert r and r["phrasing"] == "concept"

def test_classifier_followup_uses_history():
    hist = [
        {"role": "user",      "content": "Tell me about my Saturn return"},
        {"role": "assistant", "content": "You're in your 2nd Saturn Return."},
    ]
    r = classify_astrology_intent("And when does that happen in my chart?", history=hist)
    assert r and r["data_mode"] == "lifecycle"
    assert "saturn_return" in r["event_keys"]
    assert r["followup"] is True


if __name__ == "__main__":
    # quick manual run
    funcs = [v for k, v in list(globals().items()) if k.startswith("test_")]
    passed = 0
    failed = []
    for f in funcs:
        try:
            f()
            print(f"  ✓ {f.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  ✗ {f.__name__}: {e}")
            failed.append(f.__name__)
        except Exception as e:
            print(f"  ✗ {f.__name__}: {type(e).__name__}: {e}")
            failed.append(f.__name__)
    print(f"\n{passed}/{len(funcs)} passed")
    if failed:
        sys.exit(1)
