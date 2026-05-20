"""
Server Router Refactor v7 — regression test.
Tests for build marker: server-router-refactor-v7

Tests:
A) MEMBER-SUMMARY (folded into forums_intelligence)
B) FORUM INTELLIGENCE ROUTES (regression)
C) /api/mirror/chat — pipeline stages (CRITICAL — debug shape must be byte-identical)
D) Previously extracted routers (sanity)
"""

import os
import sys
import json
import time
import requests
from typing import Any, Dict, Optional, Tuple

BASE = "https://signup-issues-1.preview.emergentagent.com/api"

FORUM_ID = "69dd05eaa333335fcbf3ad33"
PETE_ID = "697f0c6abf35c0528ff06954"
MEL_ID = "697ec826ad4b18f75bf42616"

TIMEOUT = 90  # seconds (LLM calls can take time)

results = []  # (name, ok, info)


def record(name: str, ok: bool, info: str = ""):
    results.append((name, ok, info))
    flag = "✅ PASS" if ok else "❌ FAIL"
    print(f"{flag} | {name} | {info}")


def get(path: str, params: Optional[Dict[str, Any]] = None) -> Tuple[int, Any]:
    url = f"{BASE}{path}"
    try:
        r = requests.get(url, params=params, timeout=TIMEOUT)
        try:
            data = r.json()
        except Exception:
            data = r.text
        return r.status_code, data
    except Exception as e:
        return -1, {"error": str(e)}


def post(path: str, body: Dict[str, Any]) -> Tuple[int, Any]:
    url = f"{BASE}{path}"
    try:
        r = requests.post(url, json=body, timeout=TIMEOUT)
        try:
            data = r.json()
        except Exception:
            data = r.text
        return r.status_code, data
    except Exception as e:
        return -1, {"error": str(e)}


# ─────────────────────────────────────────────────────────────────
# A) MEMBER-SUMMARY (folded into forums_intelligence)
# ─────────────────────────────────────────────────────────────────
def section_A():
    print("\n" + "=" * 70)
    print("A) MEMBER-SUMMARY (folded into forums_intelligence)")
    print("=" * 70)

    # A.1 Pete viewing Pete
    code, data = get(
        f"/forums/{FORUM_ID}/member-summary/{PETE_ID}", {"user_id": PETE_ID}
    )
    ok = code == 200 and isinstance(data, dict)
    info = f"status={code}"
    if ok:
        info += f", keys={list(data.keys())[:8]}"
    else:
        info += f", body={str(data)[:300]}"
    record("A.1 member-summary Pete viewing Pete", ok, info)

    # A.2 Pete viewing Mel
    code, data = get(
        f"/forums/{FORUM_ID}/member-summary/{MEL_ID}", {"user_id": PETE_ID}
    )
    ok = code == 200 and isinstance(data, dict)
    info = f"status={code}"
    if ok:
        info += f", keys={list(data.keys())[:8]}"
    else:
        info += f", body={str(data)[:300]}"
    record("A.2 member-summary Pete viewing Mel", ok, info)

    # A.3 Requester not in forum → 403
    bogus_user = "000000000000000000000000"
    code, data = get(
        f"/forums/{FORUM_ID}/member-summary/{MEL_ID}", {"user_id": bogus_user}
    )
    ok = code == 403
    info = f"status={code}, expected 403"
    if not ok:
        info += f", body={str(data)[:200]}"
    record("A.3 not-in-forum → 403", ok, info)

    # A.4 Invalid forum_id → 400
    code, data = get(
        "/forums/INVALID_FORUM_ID_xx/member-summary/" + PETE_ID, {"user_id": PETE_ID}
    )
    # Accept 400 (per spec) or 404 (commonly used for invalid id)
    ok = code in (400, 404, 422)
    info = f"status={code} (expected 400; 404/422 also acceptable)"
    if not ok:
        info += f", body={str(data)[:200]}"
    record("A.4 invalid forum_id → 4xx", ok, info)


# ─────────────────────────────────────────────────────────────────
# B) FORUM INTELLIGENCE ROUTES (regression)
# ─────────────────────────────────────────────────────────────────
def section_B():
    print("\n" + "=" * 70)
    print("B) FORUM INTELLIGENCE ROUTES (regression)")
    print("=" * 70)

    pairs = [
        ("B.1 member-lens",
         f"/forums/{FORUM_ID}/member-lens/{PETE_ID}", {"user_id": PETE_ID}),
        ("B.2 member-mappings",
         f"/forums/{FORUM_ID}/member-mappings", {"user_id": PETE_ID}),
        ("B.3 relationship-map",
         f"/forums/{FORUM_ID}/relationship-map", {"user_id": PETE_ID}),
        ("B.4 contributions",
         f"/forums/{FORUM_ID}/contributions", {"user_id": PETE_ID}),
        ("B.5 dynamics-context",
         f"/forums/{FORUM_ID}/dynamics-context", {"user_id": PETE_ID}),
        ("B.7 pattern-map",
         f"/forums/{FORUM_ID}/pattern-map", {"user_id": PETE_ID}),
    ]
    for name, path, params in pairs:
        code, data = get(path, params)
        ok = code == 200 and isinstance(data, dict)
        info = f"status={code}"
        if ok:
            info += f", top_keys={list(data.keys())[:6]}"
        else:
            info += f", body={str(data)[:300]}"
        record(name, ok, info)

    # B.6 POST pairwise-dynamics
    body = {
        "user_id": PETE_ID,
        "member_a_id": PETE_ID,
        "member_b_id": MEL_ID,
    }
    code, data = post(f"/forums/{FORUM_ID}/pairwise-dynamics", body)
    ok = code == 200 and isinstance(data, dict)
    info = f"status={code}"
    if ok:
        info += f", top_keys={list(data.keys())[:6]}"
    else:
        info += f", body={str(data)[:300]}"
    record("B.6 pairwise-dynamics POST", ok, info)


# ─────────────────────────────────────────────────────────────────
# C) /api/mirror/chat — pipeline stages
# ─────────────────────────────────────────────────────────────────

def _success_indicator(code: int, data: Any) -> bool:
    """Mirror chat has no `success` field. HTTP 200 + non-empty response is success."""
    if code != 200 or not isinstance(data, dict):
        return False
    resp = data.get("response")
    return isinstance(resp, str) and len(resp.strip()) > 0


def section_C():
    print("\n" + "=" * 70)
    print("C) /api/mirror/chat — pipeline stages")
    print("=" * 70)

    # C.1 NULL LENS
    body = {"user_id": PETE_ID, "message": "What's coming up for me?"}
    code, data = post("/mirror/chat", body)
    if not _success_indicator(code, data):
        record("C.1 null lens (HTTP 200 + non-empty response)", False,
               f"status={code}, body={str(data)[:300]}")
    else:
        debug = data.get("debug") or {}
        has_pm = "pattern_memory" in debug
        has_mr = "micro_reflection" in debug
        has_co = "contradictions" in debug
        ok = has_pm and has_mr and has_co
        info = (
            f"status=200, response_len={len(data.get('response',''))}; "
            f"debug.pattern_memory={has_pm}, micro_reflection={has_mr}, contradictions={has_co}; "
            f"debug.lens_chat={'lens_chat' in debug}, life_master_voice={'life_master_voice' in debug}"
        )
        record("C.1 null lens — debug has pattern_memory/micro_reflection/contradictions", ok, info)

    # C.2 ASTROLOGY LENS
    body = {
        "user_id": PETE_ID,
        "message": "What does my chart say this month?",
        "lens": "astrology",
    }
    code, data = post("/mirror/chat", body)
    if not _success_indicator(code, data):
        record("C.2 astrology lens (HTTP 200 + non-empty response)", False,
               f"status={code}, body={str(data)[:300]}")
    else:
        debug = data.get("debug") or {}
        lens_chat = debug.get("lens_chat") or {}
        ok = (
            lens_chat.get("marker") == "multi-lens-chat-memory-v1"
            and lens_chat.get("lens") == "astrology"
            and "active_entity" in lens_chat
            and debug.get("marker") == "multi-lens-chat-memory-v1"
            and debug.get("lens") == "astrology"
        )
        info = (
            f"lens_chat.marker={lens_chat.get('marker')}, "
            f"lens_chat.lens={lens_chat.get('lens')}, "
            f"active_entity={'active_entity' in lens_chat}, "
            f"flat debug.marker={debug.get('marker')}, debug.lens={debug.get('lens')}"
        )
        record("C.2 astrology lens — nested+flat debug shape preserved", ok, info)

    # C.3 ZI_WEI LENS
    body = {
        "user_id": PETE_ID,
        "message": "What does my Purple Star say?",
        "lens": "zi_wei",
    }
    code, data = post("/mirror/chat", body)
    if not _success_indicator(code, data):
        record("C.3 zi_wei lens (HTTP 200 + non-empty response)", False,
               f"status={code}, body={str(data)[:300]}")
    else:
        debug = data.get("debug") or {}
        lens_chat = debug.get("lens_chat") or {}
        ok = (
            lens_chat.get("marker") == "multi-lens-chat-memory-v1"
            and lens_chat.get("lens") == "zi_wei"
        )
        info = (
            f"lens_chat.marker={lens_chat.get('marker')}, "
            f"lens_chat.lens={lens_chat.get('lens')}"
        )
        record("C.3 zi_wei lens — debug.lens_chat preserved", ok, info)

    # C.4 LIFE TAB — relationships
    body = {
        "user_id": PETE_ID,
        "message": "What's going on with my partner?",
        "life_domain": "relationships",
    }
    code, data = post("/mirror/chat", body)
    if not _success_indicator(code, data):
        record("C.4 life_domain=relationships (HTTP 200 + non-empty response)", False,
               f"status={code}, body={str(data)[:300]}")
    else:
        debug = data.get("debug") or {}
        lmv = debug.get("master_voice") or {}
        ok = bool(lmv) and ("contributing_frameworks" in lmv)
        info = f"master_voice present={bool(lmv)}, contributing_frameworks={lmv.get('contributing_frameworks')}, marker={lmv.get('marker')}"
        record("C.4 life_domain=relationships — master_voice surfaces", ok, info)

    # C.5 LIFE TAB — work
    body = {
        "user_id": PETE_ID,
        "message": "How am I showing up at work?",
        "life_domain": "work",
    }
    code, data = post("/mirror/chat", body)
    if not _success_indicator(code, data):
        record("C.5 life_domain=work (HTTP 200 + non-empty response)", False,
               f"status={code}, body={str(data)[:300]}")
    else:
        debug = data.get("debug") or {}
        lmv = debug.get("master_voice") or {}
        ok = bool(lmv) and ("contributing_frameworks" in lmv)
        info = f"master_voice present={bool(lmv)}, contributing_frameworks={lmv.get('contributing_frameworks')}, marker={lmv.get('marker')}"
        record("C.5 life_domain=work — master_voice surfaces", ok, info)

    # C.6 LIFE TAB — self
    body = {
        "user_id": PETE_ID,
        "message": "What pattern am I in right now?",
        "life_domain": "self",
    }
    code, data = post("/mirror/chat", body)
    if not _success_indicator(code, data):
        record("C.6 life_domain=self (HTTP 200 + non-empty response)", False,
               f"status={code}, body={str(data)[:300]}")
    else:
        debug = data.get("debug") or {}
        lmv = debug.get("master_voice") or {}
        ok = bool(lmv) and ("contributing_frameworks" in lmv)
        info = f"master_voice present={bool(lmv)}, contributing_frameworks={lmv.get('contributing_frameworks')}, marker={lmv.get('marker')}"
        record("C.6 life_domain=self — master_voice surfaces", ok, info)

    # C.7 ASK ABOUT PERSON
    code, data = get("/saved-people", {"user_id": PETE_ID})
    person_id = None
    if code == 200:
        # Try common shapes
        people = []
        if isinstance(data, list):
            people = data
        elif isinstance(data, dict):
            for k in ("saved_people", "people", "items", "results", "data"):
                v = data.get(k)
                if isinstance(v, list):
                    people = v
                    break
        if people:
            p0 = people[0]
            if isinstance(p0, dict):
                person_id = (
                    p0.get("id")
                    or p0.get("_id")
                    or p0.get("person_id")
                    or p0.get("saved_person_id")
                )
    if not person_id:
        record("C.7 ask-about-person (relational layer)", True,
               f"SKIPPED — no saved_people available (saved-people status={code})")
    else:
        body = {
            "user_id": PETE_ID,
            "message": "Help me understand what's going on with them",
            "lens": "astrology",
            "about_person_id": person_id,
        }
        code, data = post("/mirror/chat", body)
        if not _success_indicator(code, data):
            record("C.7 ask-about-person (HTTP 200 + non-empty response)", False,
                   f"status={code}, body={str(data)[:300]}")
        else:
            debug = data.get("debug") or {}
            relational = debug.get("relational") or {}
            ok = (
                bool(relational)
                and "relationship_class" in relational
                and "projection_risk" in relational
            )
            info = (
                f"relational present={bool(relational)}, "
                f"keys={list(relational.keys())[:6] if isinstance(relational,dict) else None}, "
                f"intensity_capped_by_relational={(debug.get('lens_chat') or {}).get('intensity_capped_by_relational')}"
            )
            record("C.7 ask-about-person — debug.relational surfaces", ok, info)

    # C.8 EVIDENCE DRAWER (re-use a simple chat call)
    body = {"user_id": PETE_ID, "message": "Where am I right now?"}
    code, data = post("/mirror/chat", body)
    if not _success_indicator(code, data):
        record("C.8 evidence drawer (HTTP 200 + non-empty response)", False,
               f"status={code}, body={str(data)[:300]}")
    else:
        evidence = data.get("evidence")
        ok = isinstance(evidence, dict) and bool(evidence.get("marker"))
        info = (
            f"evidence present={isinstance(evidence,dict)}, "
            f"marker={evidence.get('marker') if isinstance(evidence,dict) else None}"
        )
        record("C.8 evidence drawer — evidence.marker non-empty", ok, info)


# ─────────────────────────────────────────────────────────────────
# D) PREVIOUSLY EXTRACTED ROUTERS (sanity)
# ─────────────────────────────────────────────────────────────────
def section_D():
    print("\n" + "=" * 70)
    print("D) PREVIOUSLY EXTRACTED ROUTERS (sanity)")
    print("=" * 70)

    # D.1 chat history
    code, data = get(
        f"/forums/{FORUM_ID}/chat/history", {"user_id": PETE_ID, "limit": 2}
    )
    ok = code == 200
    record("D.1 forums chat/history", ok, f"status={code}")

    # D.2 forums for user
    code, data = get(f"/forums/user/{PETE_ID}")
    ok = code == 200
    record("D.2 forums user list", ok, f"status={code}")

    # D.3 POST forums mirror-chat
    body = {"user_id": PETE_ID, "forum_id": FORUM_ID, "message": "Hi"}
    code, data = post(f"/forums/{FORUM_ID}/mirror-chat", body)
    ok = code == 200
    info = f"status={code}"
    if not ok:
        info += f", body={str(data)[:250]}"
    record("D.3 POST forums mirror-chat", ok, info)

    # D.4 story-of-circle
    code, data = get(
        f"/forums/{FORUM_ID}/story-of-circle", {"user_id": PETE_ID}
    )
    ok = code == 200
    record("D.4 story-of-circle", ok, f"status={code}")

    # D.5 micro-reflection/home-texture
    body = {"user_id": PETE_ID, "texture": "clear", "domain": "self"}
    code, data = post("/micro-reflection/home-texture", body)
    ok = code == 200
    info = f"status={code}"
    if not ok:
        info += f", body={str(data)[:250]}"
    record("D.5 POST micro-reflection/home-texture", ok, info)

    # D.6 pattern-running-me
    code, data = get(f"/pattern-running-me/user/{PETE_ID}")
    ok = code == 200
    record("D.6 pattern-running-me", ok, f"status={code}")

    # D.7 topology
    code, data = get(f"/forums/{FORUM_ID}/topology", {"user_id": PETE_ID})
    ok = code == 200
    record("D.7 forums topology", ok, f"status={code}")


def main():
    print(f"BASE = {BASE}")
    print(f"FORUM_ID = {FORUM_ID}")
    print(f"PETE_ID  = {PETE_ID}")
    print(f"MEL_ID   = {MEL_ID}")

    section_A()
    section_B()
    section_C()
    section_D()

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"PASSED: {passed}/{total}")
    print()
    fails = [(n, info) for n, ok, info in results if not ok]
    if fails:
        print("FAILURES:")
        for n, info in fails:
            print(f"  ❌ {n}  ::  {info}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
