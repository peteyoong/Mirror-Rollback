"""
Forum-Aware Conversational Mirror + Contradiction Intelligence
backend test  —  build marker forum-conversational-field-v1

Validates E1..E7 from the review request.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import time
import uuid
from typing import Any, Dict, List, Tuple

import requests
from dotenv import load_dotenv

# Load backend env so we can connect to Mongo directly for assertions/cleanup.
load_dotenv("/app/backend/.env")

BASE = "https://behavioral-lens-2.preview.emergentagent.com/api"
PETE = "697f0c6abf35c0528ff06954"
SEEDED_FORUM = "69dd05eaa333335fcbf3ad33"
EMPTY_FORUM = "empty-nonexistent"
SECOND_USER = "test-user-second-697f0000000000000000000"

FORBIDDEN_TOKENS = [
    'denial', 'hypocrite', 'lying to yourself', 'the truth is', 'gotcha',
    'contradiction detected', 'the real problem is',
    'is the issue', 'is toxic', 'is avoidant', 'dominates emotionally',
    'everyone thinks', 'the group secretly feels', 'destiny', 'fated',
    'palace', 'zi wei', 'manifestor', 'enneagram', 'numerology',
    'human design', 'astrology', '%', 'score', 'ranking', 'rank ',
]

PROBABILISTIC_MARKERS = [
    'may', 'might', 'seems', 'tends', 'part of', 'a few people', 'in the room',
]


PASS = "\u2705"
FAIL = "\u274c"

results: List[Tuple[str, bool, str]] = []


def record(name: str, ok: bool, detail: str = ""):
    results.append((name, ok, detail))
    icon = PASS if ok else FAIL
    print(f"{icon} {name}" + (f"  ::  {detail}" if detail else ""))


def post_chat(forum_id: str, user_id: str, message: str,
              session_id: str | None = None,
              include_history: bool = True,
              timeout: int = 90) -> requests.Response:
    body = {
        "user_id": user_id,
        "forum_id": forum_id,
        "message": message,
        "session_id": session_id,
        "include_history": include_history,
    }
    return requests.post(
        f"{BASE}/forums/{forum_id}/mirror-chat",
        json=body,
        timeout=timeout,
    )


def get_history(forum_id: str, user_id: str) -> requests.Response:
    return requests.get(
        f"{BASE}/forums/{forum_id}/mirror-chat/history",
        params={"user_id": user_id},
        timeout=30,
    )


# ---------------------------------------------------------------------------
# Mongo helpers (direct access for E5/E7).
# ---------------------------------------------------------------------------


async def _get_db():
    from motor.motor_asyncio import AsyncIOMotorClient
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    return client[os.environ["DB_NAME"]], client


# =============================================================================
# E1 — Empty / sparse forum graceful degrade
# =============================================================================


def test_e1_empty_forum():
    print("\n=== E1 — Empty / sparse forum graceful degrade ===")
    r = post_chat(EMPTY_FORUM, PETE, "What is this room avoiding?")
    record("E1.http_200", r.status_code == 200,
           f"status={r.status_code}, body={r.text[:200]}")
    if r.status_code != 200:
        return
    data = r.json()
    response_text = data.get("response", "")
    debug = data.get("debug") or {}
    evidence = data.get("evidence")

    record("E1.response_nonempty", bool(response_text.strip()),
           f"len={len(response_text)}")
    record("E1.debug.marker", debug.get("marker") == "forum-conversational-field-v1",
           f"marker={debug.get('marker')}")
    record("E1.story_ready_false", debug.get("story_ready") is False,
           f"story_ready={debug.get('story_ready')}")

    contras = debug.get("contradictions") or {}
    forum_c = contras.get("forum") or {}
    record("E1.contra.forum.marker",
           forum_c.get("marker") == "contradiction-intelligence-v1",
           f"forum.marker={forum_c.get('marker')}")
    record("E1.contra.forum.level==LOW",
           forum_c.get("contradiction_level") == "LOW",
           f"level={forum_c.get('contradiction_level')}")
    record("E1.contra.forum.surfaced==false",
           forum_c.get("surfaced") is False,
           f"surfaced={forum_c.get('surfaced')}")

    if evidence is None:
        record("E1.evidence_acceptable", True, "evidence=None (allowed)")
    else:
        keys = set(evidence.keys()) - {"marker", "surface"}
        bad = keys - {"relational_weather", "recurring_movement"}
        record("E1.evidence_no_chips", "field_signals" not in keys,
               f"keys={list(keys)}")
        record("E1.evidence_allowed_keys_only", len(bad) == 0,
               f"unexpected_keys={list(bad)}")


# =============================================================================
# E2 — Seeded forum
# =============================================================================


def test_e2_seeded_forum() -> Dict[str, Any] | None:
    print("\n=== E2 — Seeded forum ===")
    r = post_chat(SEEDED_FORUM, PETE, "What softens this room?")
    record("E2.http_200", r.status_code == 200,
           f"status={r.status_code}, body={r.text[:200]}")
    if r.status_code != 200:
        return None
    data = r.json()
    response_text = data.get("response", "")
    debug = data.get("debug") or {}
    evidence = data.get("evidence")

    record("E2.response_nonempty", bool(response_text.strip()),
           f"len={len(response_text)}")
    record("E2.story_ready_is_bool", isinstance(debug.get("story_ready"), bool),
           f"story_ready={debug.get('story_ready')}")

    contras = debug.get("contradictions") or {}
    forum_c = contras.get("forum") or {}
    indiv_c = contras.get("individual") or {}
    record("E2.contra.forum.marker",
           forum_c.get("marker") == "contradiction-intelligence-v1",
           f"forum.marker={forum_c.get('marker')}")
    record("E2.contra.individual.marker",
           indiv_c.get("marker") == "contradiction-intelligence-v1",
           f"individual.marker={indiv_c.get('marker')}")

    record("E2.field_signals_is_list",
           isinstance(debug.get("field_signals"), list),
           f"field_signals={debug.get('field_signals')}")

    # Evidence: when present, at least one acceptable key.
    if evidence is None:
        # Allowed iff story_ready==False AND no contradictions surfaced.
        contras_surfaced = forum_c.get("surfaced") or indiv_c.get("surfaced")
        story_ready = bool(debug.get("story_ready"))
        ok = (not story_ready) and (not contras_surfaced)
        record("E2.evidence_none_acceptable", ok,
               f"story_ready={story_ready} contras_surfaced={contras_surfaced}")
    else:
        keys = set(evidence.keys()) - {"marker", "surface"}
        wanted = {"field_signals", "relational_weather",
                  "recurring_movement", "mixed_signals"}
        record("E2.evidence_has_acceptable_key",
               bool(keys & wanted),
               f"keys={list(keys)}")

    return {"response": response_text, "debug": debug, "evidence": evidence}


# =============================================================================
# E3 — No forbidden tokens
# =============================================================================


def test_e3_no_forbidden(payload: Dict[str, Any] | None):
    print("\n=== E3 — No forbidden tokens (case-insensitive) ===")
    if not payload:
        record("E3.payload_present", False, "E2 payload missing")
        return
    text_l = (payload["response"] or "").lower()

    leaks: List[str] = []
    for tok in FORBIDDEN_TOKENS:
        # "rank " has trailing space — preserve as-is.
        if tok in text_l:
            leaks.append(tok)
    record("E3.no_forbidden_tokens", len(leaks) == 0,
           f"leaks={leaks}; sample={text_l[:160]!r}")


# =============================================================================
# E4 — Probabilistic + name reframing
# =============================================================================


def test_e4_name_reframe():
    print("\n=== E4 — Probabilistic + name reframing ===")
    msg = ("I think John dominates every conversation here. "
           "What is going on?")
    r = post_chat(SEEDED_FORUM, PETE, msg)
    record("E4.http_200", r.status_code == 200,
           f"status={r.status_code}")
    if r.status_code != 200:
        return None
    data = r.json()
    response_text = data.get("response", "") or ""
    # Case-sensitive scan for "John" (and case-insensitive as belt-and-braces).
    has_john_ci = bool(re.search(r"\bjohn\b", response_text, flags=re.IGNORECASE))
    record("E4.no_first_name_john", not has_john_ci,
           f"text_sample={response_text[:240]!r}")

    text_l = response_text.lower()
    found = [m for m in PROBABILISTIC_MARKERS if m in text_l]
    record("E4.has_probabilistic_marker", len(found) >= 1,
           f"markers_found={found}")
    return data


# =============================================================================
# E5 — Per-user history persistence + isolation
# =============================================================================


async def _count_docs(db, user_id: str, forum_id: str) -> int:
    return await db.forum_mirror_chat_messages.count_documents(
        {"user_id": user_id, "forum_id": forum_id}
    )


async def _cleanup(db, user_ids: List[str], forum_id: str):
    for uid in user_ids:
        await db.forum_mirror_chat_messages.delete_many(
            {"user_id": uid, "forum_id": forum_id}
        )


def test_e5_history_isolation():
    print("\n=== E5 — Per-user history persistence + isolation ===")

    async def _run():
        db, client = await _get_db()
        try:
            # Clean slate for both users on the seeded forum.
            await _cleanup(db, [PETE, SECOND_USER], SEEDED_FORUM)

            sid = str(uuid.uuid4())
            r1 = post_chat(SEEDED_FORUM, PETE,
                           "What is alive in this circle right now?",
                           session_id=sid)
            record("E5.pete_msg1_200", r1.status_code == 200,
                   f"status={r1.status_code}")
            if r1.status_code != 200:
                return

            r2 = post_chat(SEEDED_FORUM, PETE,
                           "And what is the room not saying?",
                           session_id=sid)
            record("E5.pete_msg2_200", r2.status_code == 200,
                   f"status={r2.status_code}")
            if r2.status_code != 200:
                return

            # Allow a tiny window for the async insert_many to land.
            await asyncio.sleep(0.5)
            pete_count = await _count_docs(db, PETE, SEEDED_FORUM)
            record("E5.pete_docs_eq_4", pete_count == 4,
                   f"pete_count={pete_count}")

            # Second user posts once.
            r3 = post_chat(SEEDED_FORUM, SECOND_USER,
                           "A first hello from someone new.")
            record("E5.second_msg_200", r3.status_code == 200,
                   f"status={r3.status_code}")
            await asyncio.sleep(0.5)
            pete_count_after = await _count_docs(db, PETE, SEEDED_FORUM)
            second_count = await _count_docs(db, SECOND_USER, SEEDED_FORUM)
            record("E5.pete_unchanged", pete_count_after == 4,
                   f"after={pete_count_after}")
            record("E5.second_has_2_docs", second_count == 2,
                   f"second_count={second_count}")

            # History endpoint for Pete returns 4 chronological messages.
            hr = get_history(SEEDED_FORUM, PETE)
            record("E5.history_200", hr.status_code == 200,
                   f"status={hr.status_code}")
            if hr.status_code == 200:
                hd = hr.json()
                msgs = hd.get("messages") or []
                record("E5.history_len_4", len(msgs) == 4,
                       f"len={len(msgs)}")
                # Chronological order check (ts ascending).
                ts_list = [m.get("ts") for m in msgs]
                ok = all(
                    isinstance(t, str) for t in ts_list
                ) and ts_list == sorted(ts_list)
                record("E5.history_chronological", ok, f"ts_list={ts_list}")
                roles = [m.get("role") for m in msgs]
                record("E5.history_role_pattern",
                       roles == ["user", "assistant", "user", "assistant"],
                       f"roles={roles}")
                record("E5.history_marker",
                       hd.get("marker") == "forum-conversational-field-v1",
                       f"marker={hd.get('marker')}")

            # Cleanup.
            await _cleanup(db, [PETE, SECOND_USER], SEEDED_FORUM)
            after_clean = await _count_docs(db, PETE, SEEDED_FORUM)
            record("E5.cleanup_ok", after_clean == 0,
                   f"after_clean_pete={after_clean}")
        finally:
            client.close()

    asyncio.run(_run())


# =============================================================================
# E6 — Contradiction intel always present on /api/mirror/chat
# =============================================================================


def test_e6_individual_mirror_chat():
    print("\n=== E6 — Individual /api/mirror/chat contradictions ===")
    body = {
        "user_id": PETE,
        "message": "Hello, just checking in.",
        "lens": None,
        "include_journal": True,
        "include_history": True,
    }
    try:
        r = requests.post(f"{BASE}/mirror/chat", json=body, timeout=120)
    except Exception as e:
        record("E6.http_call", False, f"exception={e}")
        return
    record("E6.http_200", r.status_code == 200,
           f"status={r.status_code}, body={r.text[:200]}")
    if r.status_code != 200:
        return
    data = r.json()
    debug = data.get("debug") or {}
    contras = debug.get("contradictions") or {}
    record("E6.contra.marker",
           contras.get("marker") == "contradiction-intelligence-v1",
           f"marker={contras.get('marker')}; keys={list(contras.keys())}")
    record("E6.contra.level_present",
           "contradiction_level" in contras,
           f"level={contras.get('contradiction_level')}")


# =============================================================================
# E7 — Contradiction softening signal (white-box)
# =============================================================================


def test_e7_white_box():
    print("\n=== E7 — Contradiction module white-box ===")
    sys.path.insert(0, "/app/backend")

    async def _run():
        from services.contradiction_intelligence import (
            compute_individual_contradictions,
        )
        db, client = await _get_db()
        throwaway = f"test-throwaway-{uuid.uuid4().hex[:10]}"
        try:
            msg = ("I'm so over this whole thing, I'm completely done with "
                   "it, I've moved past it")

            # 7a: no seeded reflections / pattern memory — level should be LOW.
            res1 = await compute_individual_contradictions(
                db, user_id=throwaway, message_text=msg,
            )
            record("E7a.level_low", res1.get("level") == "LOW",
                   f"level={res1.get('level')} types={res1.get('types')}")

            # 7b: seed 3 micro_reflections with label='resisting' AND seed
            # 3 longitudinal pattern_memory rows so resistance + recurrence
            # both fire.  We must use the schema the analyzer expects.
            #
            # Inspect actual schema (best-effort).
            from datetime import datetime, timezone, timedelta
            now = datetime.now(timezone.utc)
            mr_docs = []
            for i in range(3):
                mr_docs.append({
                    "id": str(uuid.uuid4()),
                    "user_id": throwaway,
                    "label": "resisting",
                    "context_pattern_keys": ["work_exhaustion"],
                    "ts": now - timedelta(days=i),
                    "created_at": now - timedelta(days=i),
                })
            await db.micro_reflections.insert_many(mr_docs)

            pm_docs = []
            for i in range(3):
                pm_docs.append({
                    "user_id": throwaway,
                    "pattern_key": "work_exhaustion",
                    "occurrence_count": 3,
                    "last_seen_at": now - timedelta(days=i),
                    "first_seen_at": now - timedelta(days=10),
                })
            await db.longitudinal_pattern_memory.insert_many(pm_docs)

            res2 = await compute_individual_contradictions(
                db, user_id=throwaway, message_text=msg,
            )
            level2 = res2.get("level")
            print(f"   E7b debug_signals={res2.get('debug_signals')}")
            print(f"   E7b types={res2.get('types')}")
            order = ["LOW", "EMERGING", "MODERATE", "STRONG"]
            record(
                "E7b.level_escalated_to_emerging_or_higher",
                level2 in ("EMERGING", "MODERATE", "STRONG"),
                f"level={level2}",
            )
            record(
                "E7b.softened_false",
                res2.get("softened_by_reflection") is False,
                f"softened={res2.get('softened_by_reflection')}",
            )

            # 7c: add 4 reflections with label='changed' — softening
            # signal.  Expect level drops one step OR softened flips True.
            changed_docs = []
            for i in range(4):
                changed_docs.append({
                    "id": str(uuid.uuid4()),
                    "user_id": throwaway,
                    "label": "changed",
                    "context_pattern_keys": ["work_exhaustion"],
                    "ts": now - timedelta(hours=i),
                    "created_at": now - timedelta(hours=i),
                })
            await db.micro_reflections.insert_many(changed_docs)

            res3 = await compute_individual_contradictions(
                db, user_id=throwaway, message_text=msg,
            )
            level3 = res3.get("level")
            soft3 = res3.get("softened_by_reflection")
            print(f"   E7c debug_signals={res3.get('debug_signals')}")
            print(f"   E7c types={res3.get('types')}")
            try:
                dropped = order.index(level3) < order.index(level2)
            except ValueError:
                dropped = False
            record(
                "E7c.level_drops_or_softened_flips",
                dropped or soft3 is True,
                f"level2={level2} level3={level3} softened3={soft3}",
            )
        finally:
            await db.micro_reflections.delete_many({"user_id": throwaway})
            await db.longitudinal_pattern_memory.delete_many(
                {"user_id": throwaway}
            )
            client.close()

    asyncio.run(_run())


# =============================================================================
# Regression checks
# =============================================================================


def test_regression_story_of_circle():
    print("\n=== Regression — GET /forums/{seeded}/story-of-circle ===")
    r = requests.get(
        f"{BASE}/forums/{SEEDED_FORUM}/story-of-circle", timeout=30
    )
    record("REG.story_200", r.status_code == 200, f"status={r.status_code}")
    if r.status_code != 200:
        return
    data = r.json()
    record("REG.story_has_story_key", "story" in data,
           f"keys={list(data.keys())}")
    record("REG.story_marker_present",
           data.get("marker") == "forum-topology-and-timing-v1",
           f"marker={data.get('marker')}")


def test_regression_zi_wei_mirror_chat():
    print("\n=== Regression — POST /mirror/chat lens=zi_wei ===")
    body = {
        "user_id": PETE,
        "message": "What is rising for me this week?",
        "lens": "zi_wei",
        "include_journal": False,
        "include_history": False,
    }
    try:
        r = requests.post(f"{BASE}/mirror/chat", json=body, timeout=180)
    except Exception as e:
        record("REG.zi_wei_call", False, f"exception={e}")
        return
    record("REG.zi_wei_200", r.status_code == 200,
           f"status={r.status_code}, body={r.text[:200]}")
    if r.status_code != 200:
        return
    data = r.json()
    record("REG.zi_wei_response_nonempty",
           bool((data.get("response") or "").strip()),
           f"len={len(data.get('response') or '')}")
    debug = data.get("debug") or {}
    contras = debug.get("contradictions") or {}
    # Still expect contradictions injection didn't break lens dispatch.
    record("REG.zi_wei_contra_marker_present",
           contras.get("marker") == "contradiction-intelligence-v1",
           f"contra={contras}")


# =============================================================================
# Main
# =============================================================================


def main():
    print(f"BASE = {BASE}")
    print(f"PETE = {PETE}")
    print(f"SEEDED_FORUM = {SEEDED_FORUM}")
    print(f"EMPTY_FORUM = {EMPTY_FORUM}")
    print(f"SECOND_USER = {SECOND_USER}")
    print()

    # Make sure we run from a clean state for E5 / E2 history-bleed.
    async def _initial_clean():
        db, client = await _get_db()
        try:
            await _cleanup(db, [PETE, SECOND_USER], SEEDED_FORUM)
            await _cleanup(db, [PETE, SECOND_USER], EMPTY_FORUM)
        finally:
            client.close()
    asyncio.run(_initial_clean())

    test_e1_empty_forum()
    e2 = test_e2_seeded_forum()
    test_e3_no_forbidden(e2)
    test_e4_name_reframe()
    test_e5_history_isolation()
    test_e6_individual_mirror_chat()
    test_e7_white_box()
    test_regression_story_of_circle()
    test_regression_zi_wei_mirror_chat()

    # Final cleanup of anything left.
    async def _final_clean():
        db, client = await _get_db()
        try:
            await _cleanup(db, [PETE, SECOND_USER], SEEDED_FORUM)
            await _cleanup(db, [PETE, SECOND_USER], EMPTY_FORUM)
        finally:
            client.close()
    asyncio.run(_final_clean())

    # Summary
    print("\n" + "=" * 70)
    total = len(results)
    passed = sum(1 for _, ok, _ in results if ok)
    failed = total - passed
    print(f"TOTAL: {total}   PASS: {passed}   FAIL: {failed}")
    if failed:
        print("\nFAILED ASSERTIONS:")
        for name, ok, detail in results:
            if not ok:
                print(f"  {FAIL} {name}  ::  {detail}")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
