"""
Regression test for server-router-refactor-v2.

Tests assertions R1–R18 covering:
  - routers/micro_reflection.py (R1–R5)
  - routers/forums_field.py (R6–R11, R15–R16)
  - routers/topology_editor.py (R12–R14)
  - inline /api/mirror/chat still working (R17–R18)

After running, performs cleanup of test artifacts.
"""

import os
import sys
import json
import traceback

import requests

BASE = "https://behavioral-lens-2.preview.emergentagent.com/api"
PETE = "697f0c6abf35c0528ff06954"
FORUM = "69dd05eaa333335fcbf3ad33"

results = []  # (name, ok, msg)


def record(name, ok, msg=""):
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}: {msg}")
    results.append((name, ok, msg))


def safe(name, fn):
    try:
        fn()
    except AssertionError as e:
        record(name, False, f"AssertionError: {e}")
    except Exception as e:
        record(name, False, f"Exception {type(e).__name__}: {e}\n{traceback.format_exc()}")


# Resolve Mel via forum members
print("Resolving Mel's user_id ...")
r = requests.get(f"{BASE}/forums/{FORUM}/members", params={"user_id": PETE}, timeout=30)
r.raise_for_status()
members = r.json().get("members", [])
mel_id = None
for m in members:
    if m.get("user_id") != PETE:
        mel_id = m.get("user_id")
        break
assert mel_id, "Could not resolve Mel's user_id"
print(f"Mel = {mel_id}")

# Track cleanup ids
r12_edge_id = None
r15_edge_id = None


# ----- R1 -----
def t_r1():
    payload = {"user_id": PETE, "label": "lands", "source": "other"}
    r = requests.post(f"{BASE}/micro-reflection", json=payload, timeout=30)
    assert r.status_code == 200, f"status={r.status_code} body={r.text[:200]}"
    j = r.json()
    assert j.get("marker") == "micro-reflection-v2", f"marker={j.get('marker')}"
    assert j["reflection"]["label"] == "lands", f"label={j['reflection']['label']}"
    record("R1", True, "marker ok")


# ----- R2 -----
def t_r2():
    r = requests.get(f"{BASE}/micro-reflection/{PETE}/recent", timeout=30)
    assert r.status_code == 200, f"status={r.status_code}"
    j = r.json()
    assert j.get("marker") == "micro-reflection-v2", f"marker={j.get('marker')}"
    total = j.get("summary", {}).get("total", 0)
    assert total >= 1, f"summary.total={total}"
    record("R2", True, f"total={total}")


# ----- R3 -----
def t_r3():
    payload = {"user_id": PETE, "texture": "open"}
    r = requests.post(f"{BASE}/micro-reflection/home-texture", json=payload, timeout=30)
    assert r.status_code == 200, f"status={r.status_code} body={r.text[:200]}"
    j = r.json()
    assert j.get("marker") == "micro-reflection-v3-home-texture", f"marker={j.get('marker')}"
    refl = j.get("reflection", {})
    assert refl.get("source") == "home_texture", f"source={refl.get('source')}"
    assert refl.get("label") == "true_lately", f"label={refl.get('label')}"
    record("R3", True, "ok")


# ----- R4 -----
def t_r4():
    r = requests.get(f"{BASE}/micro-reflection/{PETE}/home-texture/today", timeout=30)
    assert r.status_code == 200, f"status={r.status_code}"
    j = r.json()
    assert j.get("marker") == "micro-reflection-v3-home-texture", f"marker={j.get('marker')}"
    assert j.get("logged_today") is True, f"logged_today={j.get('logged_today')}"
    last = j.get("last") or {}
    assert last.get("texture") == "open", f"last.texture={last.get('texture')}"
    record("R4", True, "ok")


# ----- R5 -----
def t_r5():
    payload = {"user_id": PETE, "texture": "weird"}
    r = requests.post(f"{BASE}/micro-reflection/home-texture", json=payload, timeout=30)
    assert r.status_code == 400, f"expected 400 got {r.status_code} body={r.text[:200]}"
    record("R5", True, "400 ok")


# ----- R6 -----
def t_r6():
    r = requests.get(f"{BASE}/forums/{FORUM}/topology", timeout=30)
    assert r.status_code == 200, f"status={r.status_code}"
    j = r.json()
    assert j.get("marker") == "forum-topology-and-timing-v1", f"marker={j.get('marker')}"
    for k in ("edges", "confidence", "field_stability"):
        assert k in j, f"missing field {k}"
    record("R6", True, f"edges={len(j.get('edges') or [])}")


# ----- R7 -----
def t_r7():
    r = requests.post(f"{BASE}/forums/{FORUM}/topology/infer", timeout=60)
    assert r.status_code == 200, f"status={r.status_code} body={r.text[:200]}"
    j = r.json()
    assert j.get("marker") == "forum-topology-and-timing-v1", f"marker={j.get('marker')}"
    mc = j.get("members_count", 0)
    assert mc >= 2, f"members_count={mc}"
    record("R7", True, f"members_count={mc}")


# ----- R8 -----
def t_r8():
    r = requests.get(f"{BASE}/forums/{FORUM}/story-of-circle", timeout=60)
    assert r.status_code == 200, f"status={r.status_code}"
    j = r.json()
    assert j.get("marker") == "forum-topology-and-timing-v1", f"marker={j.get('marker')}"
    assert isinstance(j.get("story"), dict), f"story type={type(j.get('story'))}"
    record("R8", True, "ok")


# ----- R9 -----
def t_r9():
    payload = {"user_id": PETE, "forum_id": FORUM, "message": "What softens this room?"}
    r = requests.post(f"{BASE}/forums/{FORUM}/mirror-chat", json=payload, timeout=120)
    assert r.status_code == 200, f"status={r.status_code} body={r.text[:300]}"
    j = r.json()
    assert (j.get("response") or "").strip(), f"empty response: {j.get('response')!r}"
    dbg = j.get("debug") or {}
    assert dbg.get("marker") == "forum-conversational-field-v1", f"debug.marker={dbg.get('marker')}"
    contras = dbg.get("contradictions")
    assert contras is not None, "debug.contradictions missing"
    contra_str = json.dumps(contras)
    assert "contradiction-intelligence-v1" in contra_str, f"contradiction-intelligence-v1 not in contras: {contra_str[:400]}"
    sid = j.get("session_id")
    assert sid, "session_id missing"
    record("R9", True, f"session_id={sid[:8]}")


# ----- R10 -----
def t_r10():
    payload = {"user_id": PETE, "forum_id": FORUM, "message": "What softens this room?"}
    r = requests.post(f"{BASE}/forums/{FORUM}/mirror-chat", json=payload, timeout=120)
    assert r.status_code == 200, f"status={r.status_code} body={r.text[:300]}"
    j = r.json()
    assert (j.get("response") or "").strip(), "empty response on 2nd turn"
    assert j.get("session_id"), "session_id missing on 2nd turn"
    record("R10", True, "2nd turn ok")


# ----- R11 -----
def t_r11():
    r = requests.get(
        f"{BASE}/forums/{FORUM}/mirror-chat/history",
        params={"user_id": PETE, "limit": 10},
        timeout=30,
    )
    assert r.status_code == 200, f"status={r.status_code}"
    j = r.json()
    assert j.get("marker") == "forum-conversational-field-v1", f"marker={j.get('marker')}"
    msgs = j.get("messages") or []
    assert len(msgs) >= 4, f"len(messages)={len(msgs)}"
    record("R11", True, f"messages={len(msgs)}")


# ----- R12 -----
def t_r12():
    global r12_edge_id
    payload = {"from_user_id": PETE, "to_user_id": mel_id, "role_type": "close_friend"}
    r = requests.post(f"{BASE}/forums/{FORUM}/topology/edge", json=payload, timeout=30)
    assert r.status_code == 200, f"status={r.status_code} body={r.text[:300]}"
    j = r.json()
    assert j.get("marker") == "topology-editor-v2", f"marker={j.get('marker')}"
    edge = j.get("edge") or {}
    assert edge.get("inferred") is False, f"inferred={edge.get('inferred')}"
    r12_edge_id = edge.get("id")
    assert r12_edge_id, "edge.id missing"
    record("R12", True, f"edge_id={r12_edge_id}")


# ----- R13 -----
def t_r13():
    r = requests.get(f"{BASE}/forums/{FORUM}/topology/roles", timeout=30)
    assert r.status_code == 200, f"status={r.status_code}"
    j = r.json()
    assert j.get("marker") == "topology-editor-v2", f"marker={j.get('marker')}"
    roles = j.get("roles") or []
    assert "mentor" in roles, f"mentor not in roles={roles}"
    record("R13", True, f"{len(roles)} roles, contains mentor")


# ----- R14 -----
def t_r14():
    global r12_edge_id
    assert r12_edge_id, "R12 edge id missing"
    r = requests.delete(
        f"{BASE}/forums/{FORUM}/topology/edge/{r12_edge_id}/by/{PETE}",
        timeout=30,
    )
    assert r.status_code == 200, f"status={r.status_code} body={r.text[:200]}"
    j = r.json()
    assert j.get("marker") == "topology-editor-v2", f"marker={j.get('marker')}"
    assert j.get("deleted", 0) >= 1, f"deleted={j.get('deleted')}"
    record("R14", True, f"deleted={j.get('deleted')}")
    r12_edge_id = None  # cleaned


# ----- R15 -----
def t_r15():
    global r15_edge_id
    payload = {
        "from_user_id": PETE,
        "to_user_id": mel_id,
        "role_type": "close_friend",
        "confidence": "moderate",
    }
    r = requests.post(f"{BASE}/admin/forums/{FORUM}/seed-topology-edge", json=payload, timeout=30)
    assert r.status_code == 200, f"status={r.status_code} body={r.text[:300]}"
    j = r.json()
    assert j.get("marker") == "forum-topology-and-timing-v1", f"marker={j.get('marker')}"
    edge = j.get("edge") or {}
    r15_edge_id = edge.get("id")
    assert r15_edge_id, "edge.id missing in seed response"
    record("R15", True, f"edge_id={r15_edge_id}")


# ----- R16 -----
def t_r16():
    global r15_edge_id
    assert r15_edge_id, "R15 edge id missing"
    r = requests.delete(
        f"{BASE}/forums/{FORUM}/topology/edge/{r15_edge_id}",
        timeout=30,
    )
    assert r.status_code == 200, f"status={r.status_code} body={r.text[:200]}"
    j = r.json()
    assert j.get("marker") == "forum-topology-and-timing-v1", f"marker={j.get('marker')}"
    assert j.get("deleted", 0) >= 1, f"deleted={j.get('deleted')}"
    record("R16", True, f"deleted={j.get('deleted')}")
    r15_edge_id = None  # cleaned


# ----- R17 -----
def t_r17():
    payload = {"user_id": PETE, "message": "Hello"}
    r = requests.post(f"{BASE}/mirror/chat", json=payload, timeout=120)
    assert r.status_code == 200, f"status={r.status_code} body={r.text[:300]}"
    j = r.json()
    dbg = j.get("debug") or {}
    contras = dbg.get("contradictions")
    assert contras is not None, "debug.contradictions missing"
    contra_str = json.dumps(contras)
    assert "contradiction-intelligence-v1" in contra_str, f"marker not in contradictions: {contra_str[:400]}"
    record("R17", True, "marker contradiction-intelligence-v1 present")


# ----- R18 -----
def t_r18():
    payload = {
        "user_id": PETE,
        "lens": "zi_wei",
        "message": "What does my chart say about pressure?",
    }
    r = requests.post(f"{BASE}/mirror/chat", json=payload, timeout=120)
    assert r.status_code == 200, f"status={r.status_code} body={r.text[:300]}"
    j = r.json()
    dbg = j.get("debug") or {}
    lc = dbg.get("lens_chat") or {}
    assert lc.get("marker") == "multi-lens-chat-memory-v1", f"lens_chat.marker={lc.get('marker')}"
    assert lc.get("lens") == "zi_wei", f"lens_chat.lens={lc.get('lens')}"
    reply = j.get("response") or ""
    forbidden = ["Zi Wei", "Hua Lu", "destiny"]
    found = [w for w in forbidden if w.lower() in reply.lower()]
    assert not found, f"forbidden jargon found: {found} | reply={reply[:300]}"
    record("R18", True, "lens_chat ok, no jargon")


# Run sequence
sequence = [
    ("R1", t_r1),
    ("R2", t_r2),
    ("R3", t_r3),
    ("R4", t_r4),
    ("R5", t_r5),
    ("R6", t_r6),
    ("R7", t_r7),
    ("R8", t_r8),
    ("R9", t_r9),
    ("R10", t_r10),
    ("R11", t_r11),
    ("R12", t_r12),
    ("R13", t_r13),
    ("R14", t_r14),
    ("R15", t_r15),
    ("R16", t_r16),
    ("R17", t_r17),
    ("R18", t_r18),
]

for name, fn in sequence:
    safe(name, fn)

# Cleanup
print("\n----- CLEANUP -----")

if r12_edge_id:
    try:
        requests.delete(f"{BASE}/forums/{FORUM}/topology/edge/{r12_edge_id}/by/{PETE}", timeout=20)
        print(f"Cleanup: deleted leftover R12 edge {r12_edge_id}")
    except Exception as e:
        print(f"Cleanup R12 edge failed: {e}")
if r15_edge_id:
    try:
        requests.delete(f"{BASE}/forums/{FORUM}/topology/edge/{r15_edge_id}", timeout=20)
        print(f"Cleanup: deleted leftover R15 edge {r15_edge_id}")
    except Exception as e:
        print(f"Cleanup R15 edge failed: {e}")

# Delete home_texture and lands micro_reflection docs directly via Mongo
try:
    import asyncio
    from motor.motor_asyncio import AsyncIOMotorClient

    mongo_url = None
    db_name = None
    env_path = "/app/backend/.env"
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("MONGO_URL"):
                    mongo_url = line.split("=", 1)[1].strip().strip('"').strip("'")
                if line.startswith("DB_NAME"):
                    db_name = line.split("=", 1)[1].strip().strip('"').strip("'")
    print(f"Mongo URL: {mongo_url} db={db_name}")

    async def _cleanup():
        client = AsyncIOMotorClient(mongo_url)
        target_db = None
        if db_name:
            d = client[db_name]
            cnt = await d.micro_reflections.count_documents({"user_id": PETE})
            print(f"db '{db_name}' Pete micro_reflections count={cnt}")
            if cnt > 0:
                target_db = d
        if target_db is None:
            try:
                names = await client.list_database_names()
            except Exception:
                names = []
            for n in names:
                if n in ("admin", "config", "local"):
                    continue
                d = client[n]
                try:
                    cnt = await d.micro_reflections.count_documents({"user_id": PETE})
                except Exception:
                    continue
                if cnt > 0:
                    target_db = d
                    print(f"Using db '{n}' (Pete micro_reflections count={cnt})")
                    break
        if target_db is None:
            print("No db with Pete's micro_reflections found.")
            return
        r1 = await target_db.micro_reflections.delete_many(
            {"user_id": PETE, "source": "home_texture"}
        )
        print(f"Cleanup: deleted {r1.deleted_count} home_texture docs")
        doc = await target_db.micro_reflections.find_one(
            {"user_id": PETE, "label": "lands", "source": "other"},
            sort=[("ts", -1)],
        )
        if doc:
            r2 = await target_db.micro_reflections.delete_one({"_id": doc["_id"]})
            print(f"Cleanup: deleted {r2.deleted_count} lands/other doc")
        else:
            print("Cleanup: no lands/other doc found to delete")

    asyncio.run(_cleanup())
except Exception as e:
    print(f"Cleanup mongo error: {e}\n{traceback.format_exc()}")

# Summary
print("\n----- SUMMARY -----")
passed = sum(1 for _, ok, _ in results if ok)
failed = sum(1 for _, ok, _ in results if not ok)
print(f"PASS: {passed}  FAIL: {failed}")
for name, ok, msg in results:
    if not ok:
        print(f"  FAIL {name}: {msg}")
sys.exit(0 if failed == 0 else 1)
