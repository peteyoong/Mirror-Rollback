"""
v8 Server Router Refactor Regression Test — /api/mirror/chat extracted to routers/mirror_chat.py
Tests the same v7 mirror_chat regression suite to verify zero behavioural drift.

Pete (user_id 697f0c6abf35c0528ff06954) is the test user.
"""
import sys
import uuid
import requests
from pathlib import Path

FRONTEND_ENV = Path("/app/frontend/.env")
BACKEND_URL = None
for line in FRONTEND_ENV.read_text().splitlines():
    if line.startswith("EXPO_PUBLIC_BACKEND_URL="):
        BACKEND_URL = line.split("=", 1)[1].strip().strip('"').strip("'")
        break

API = f"{BACKEND_URL}/api"
PETE = "697f0c6abf35c0528ff06954"

results = []
def record(name, passed, info=""):
    results.append((name, passed, info))
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {name}{('  — ' + info) if info else ''}")


def post(path, body, timeout=120):
    return requests.post(f"{API}{path}", json=body, timeout=timeout)


def get(path, params=None, timeout=60):
    return requests.get(f"{API}{path}", params=params, timeout=timeout)


def delete(path, timeout=30):
    return requests.delete(f"{API}{path}", timeout=timeout)


def mirror_chat(body):
    return post("/mirror/chat", body, timeout=180)


print("=" * 72)
print(f"v8 mirror_chat router regression — {API}")
print("=" * 72)

# A) Boot/Registration
print("\n-- A) BOOT / REGISTRATION SANITY --")
r = get(f"/people/{PETE}")
record("A.1 backend reachable (GET /api/people/{pete})", r.status_code == 200,
       f"status={r.status_code}")

r = requests.post(f"{API}/mirror/chat", json={}, timeout=30)
record("A.2 POST /api/mirror/chat registered (not 404)", r.status_code != 404,
       f"status={r.status_code}")

fake_sid = "v8-nonexistent-" + uuid.uuid4().hex[:8]
r = delete(f"/mirror/chat/{fake_sid}")
record("A.3 DELETE /api/mirror/chat/{session_id} registered (not 404)",
       r.status_code != 404, f"status={r.status_code}")

# B) Mirror chat behaviour
print("\n-- B) /api/mirror/chat BEHAVIOUR --")

# B.1 lens=null
body = {
    "user_id": PETE,
    "message": "I've been feeling restless about my direction lately.",
    "lens": None,
    "session_id": "v8-test-null-" + uuid.uuid4().hex[:8],
    "include_journal": True,
    "include_history": True,
}
r = mirror_chat(body)
if r.status_code == 200:
    j = r.json()
    response_text = j.get("response", "")
    debug = j.get("debug") or {}
    evidence = j.get("evidence") or {}
    has_response = bool(response_text and len(response_text.strip()))
    has_pm = "pattern_memory" in debug
    has_mr = "micro_reflection" in debug
    has_contra = "contradictions" in debug
    has_ev = evidence.get("marker") == "evidence-drawer-v2"
    detail = (f"len={len(response_text)} pm={has_pm} mr={has_mr} contra={has_contra} "
              f"ev.marker={evidence.get('marker')}")
    record("B.1 lens=null returns 200 + response + debug{pm,mr,contra} + evidence.marker",
           has_response and has_pm and has_mr and has_contra and has_ev, detail)
else:
    record("B.1 lens=null 200", False, f"status={r.status_code} body={r.text[:200]}")

# B.2 lens=astrology
body = {
    "user_id": PETE,
    "message": "What's surfacing for me in my chart right now?",
    "lens": "astrology",
    "session_id": "v8-test-astro-" + uuid.uuid4().hex[:8],
    "include_journal": True,
    "include_history": True,
}
r = mirror_chat(body)
if r.status_code == 200:
    j = r.json()
    debug = j.get("debug") or {}
    lc = debug.get("lens_chat") or {}
    nested_ok = lc.get("marker") == "multi-lens-chat-memory-v1" and lc.get("lens") == "astrology"
    flat_ok = debug.get("marker") == "multi-lens-chat-memory-v1" and debug.get("lens") == "astrology"
    detail = (f"nested(marker={lc.get('marker')}, lens={lc.get('lens')}) "
              f"flat(marker={debug.get('marker')}, lens={debug.get('lens')})")
    record("B.2 lens=astrology nested+flat debug shape", nested_ok and flat_ok, detail)
else:
    record("B.2 lens=astrology 200", False, f"status={r.status_code} body={r.text[:200]}")

# B.3 lens=zi_wei
body = {
    "user_id": PETE,
    "message": "What patterns am I noticing this week?",
    "lens": "zi_wei",
    "session_id": "v8-test-ziwei-" + uuid.uuid4().hex[:8],
}
r = mirror_chat(body)
if r.status_code == 200:
    j = r.json()
    debug = j.get("debug") or {}
    lc = debug.get("lens_chat") or {}
    ok = lc.get("marker") == "multi-lens-chat-memory-v1" and lc.get("lens") == "zi_wei"
    record("B.3 lens=zi_wei lens_chat.marker + lens=zi_wei", ok,
           f"marker={lc.get('marker')} lens={lc.get('lens')}")
else:
    record("B.3 lens=zi_wei 200", False, f"status={r.status_code} body={r.text[:200]}")

# B.4 life_domain=relationships
body = {
    "user_id": PETE,
    "message": "Things have been tense with someone close — what should I notice?",
    "life_domain": "relationships",
    "session_id": "v8-test-life-rel-" + uuid.uuid4().hex[:8],
}
r = mirror_chat(body)
if r.status_code == 200:
    j = r.json()
    debug = j.get("debug") or {}
    mv = debug.get("master_voice") or {}
    ok = bool(mv) and mv.get("marker") == "life-tab-master-voice-v1"
    record("B.4 life_domain=relationships -> debug.master_voice marker=life-tab-master-voice-v1",
           ok, f"marker={mv.get('marker')}")
else:
    record("B.4 life_domain=relationships 200", False, f"status={r.status_code} body={r.text[:200]}")

# B.5 life_domain=work
body = {
    "user_id": PETE,
    "message": "Work has been heavy. What's underneath this?",
    "life_domain": "work",
    "session_id": "v8-test-life-work-" + uuid.uuid4().hex[:8],
}
r = mirror_chat(body)
if r.status_code == 200:
    j = r.json()
    debug = j.get("debug") or {}
    mv = debug.get("master_voice") or {}
    record("B.5 life_domain=work -> debug.master_voice present", bool(mv),
           f"marker={mv.get('marker')}")
else:
    record("B.5 life_domain=work 200", False, f"status={r.status_code} body={r.text[:200]}")

# B.6 life_domain=self
body = {
    "user_id": PETE,
    "message": "I've been feeling stuck in my own head. What's surfacing?",
    "life_domain": "self",
    "session_id": "v8-test-life-self-" + uuid.uuid4().hex[:8],
}
r = mirror_chat(body)
if r.status_code == 200:
    j = r.json()
    debug = j.get("debug") or {}
    mv = debug.get("master_voice") or {}
    record("B.6 life_domain=self -> debug.master_voice present", bool(mv),
           f"marker={mv.get('marker')}")
else:
    record("B.6 life_domain=self 200", False, f"status={r.status_code} body={r.text[:200]}")

# C) Shared chat_sessions state
print("\n-- C) SHARED chat_sessions STATE --")
shared_sid = "v8-shared-state-" + uuid.uuid4().hex[:10]
body = {
    "user_id": PETE,
    "message": "Quick check-in to test shared session state.",
    "session_id": shared_sid,
}
r = mirror_chat(body)
if r.status_code == 200:
    returned_sid = r.json().get("session_id")
    record("C.1 POST /mirror/chat with fresh session_id returns same session_id",
           returned_sid == shared_sid, f"sent={shared_sid} got={returned_sid}")
    r2 = delete(f"/mirror/chat/{shared_sid}")
    msg = ""
    try:
        msg = r2.json().get("message", "")
    except Exception:
        pass
    record("C.2 DELETE /mirror/chat/{sid} -> 200 + {'message':'Session cleared'} (shared dict)",
           r2.status_code == 200 and msg == "Session cleared",
           f"status={r2.status_code} message='{msg}'")
else:
    record("C.1 POST shared session", False, f"status={r.status_code} body={r.text[:200]}")
    record("C.2 DELETE shared session", False, "skipped")

# D) Previously extracted routers
print("\n-- D) PREVIOUSLY EXTRACTED ROUTERS (sanity) --")
forum_id = None
r = get(f"/forums/user/{PETE}")
if r.status_code == 200:
    payload = r.json()
    forums_list = payload if isinstance(payload, list) else (
        payload.get("forums") or payload.get("data") or []
    )
    if isinstance(forums_list, list) and forums_list:
        first = forums_list[0]
        forum_id = (first.get("forum_id") or first.get("_id") or first.get("id"))
    record("D.2 GET /forums/user/{pete}", True,
           f"count={len(forums_list) if isinstance(forums_list, list) else 'n/a'} forum_id={forum_id}")
else:
    record("D.2 GET /forums/user/{pete}", False, f"status={r.status_code}")

if forum_id:
    r = get(f"/forums/{forum_id}/chat/history", params={"user_id": PETE, "limit": 2})
    record("D.1 GET /forums/{id}/chat/history?limit=2", r.status_code == 200,
           f"status={r.status_code}")

    r = post(f"/forums/{forum_id}/mirror-chat",
             {"user_id": PETE, "forum_id": forum_id, "message": "v8 sanity"}, timeout=180)
    record("D.3 POST /forums/{id}/mirror-chat", r.status_code == 200,
           f"status={r.status_code}")

    r = get(f"/forums/{forum_id}/story-of-circle", params={"user_id": PETE})
    record("D.4 GET /forums/{id}/story-of-circle", r.status_code == 200,
           f"status={r.status_code}")

    r = get(f"/forums/{forum_id}/topology", params={"user_id": PETE})
    record("D.7 GET /forums/{id}/topology", r.status_code == 200,
           f"status={r.status_code}")
else:
    print("[SKIP] forum-side sanity (no forum found for Pete)")

r = post("/micro-reflection/home-texture",
         {"user_id": PETE, "texture": "open", "domain": "self"}, timeout=60)
record("D.5 POST /micro-reflection/home-texture", r.status_code == 200,
       f"status={r.status_code}")

r = get(f"/pattern-running-me/user/{PETE}")
record("D.6 GET /pattern-running-me/user/{pete}", r.status_code == 200,
       f"status={r.status_code}")

# Summary
print("\n" + "=" * 72)
passed_count = sum(1 for _, ok, _ in results if ok)
total = len(results)
print(f"RESULTS: {passed_count}/{total} passed")
print("=" * 72)
if passed_count != total:
    print("\nFAILED tests:")
    for name, ok, info in results:
        if not ok:
            print(f"  FAIL  {name} — {info}")
    sys.exit(1)
else:
    print("\nv8 mirror_chat refactor — ALL TESTS PASS, no behavioural drift")
    sys.exit(0)
