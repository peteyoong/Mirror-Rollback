"""
Backend regression tests for server-router-refactor-v5.

Tests the extracted routes in:
  - /app/backend/routers/forums_create_auth.py
  - /app/backend/routers/pattern_running_me.py

Plus regression checks for previously-extracted router groups.
"""
import json
import os
import sys
import time
from typing import Any, Dict, Optional

import requests

BACKEND_URL = "https://behavioral-lens-2.preview.emergentagent.com"
API = f"{BACKEND_URL}/api"

PETE_ID = "697f0c6abf35c0528ff06954"
FORUM_ID = "69dd05eaa333335fcbf3ad33"


class T:
    def __init__(self):
        self.results = []
        self.captured: Dict[str, Any] = {}

    def add(self, name: str, ok: bool, detail: str = ""):
        self.results.append((name, ok, detail))
        flag = "PASS" if ok else "FAIL"
        print(f"[{flag}] {name}: {detail[:240]}")

    def summary(self):
        total = len(self.results)
        passed = sum(1 for _, ok, _ in self.results if ok)
        print(f"\n=== {passed}/{total} passed ===")
        for name, ok, det in self.results:
            if not ok:
                print(f"  FAIL: {name}\n        {det[:300]}")
        return passed, total


t = T()


def req(method: str, path: str, **kw):
    url = f"{API}{path}"
    try:
        resp = requests.request(method, url, timeout=60, **kw)
        return resp
    except Exception as e:
        return e


# === P* New extraction tests ===

# P1. POST /api/forums/login
r = req("POST", "/forums/login", json={"email": "pete@pulsifi.me", "password": "x"})
try:
    if isinstance(r, Exception):
        t.add("P1 /api/forums/login", False, f"exception: {r}")
    else:
        j = r.json()
        ok = (
            r.status_code == 200
            and j.get("success") is True
            and (j.get("user", {}).get("id") == PETE_ID)
        )
        t.add(
            "P1 /api/forums/login",
            ok,
            f"status={r.status_code} success={j.get('success')} user.id={j.get('user', {}).get('id')}",
        )
except Exception as e:
    t.add("P1 /api/forums/login", False, f"parse: {e} body={getattr(r,'text','')[:200]}")


# P2. POST /api/forums get_mappings (valid)
r = req(
    "POST",
    "/forums",
    json={"get_mappings": True, "forum_id": FORUM_ID, "user_id": PETE_ID},
)
try:
    j = r.json()
    ok = r.status_code == 200 and j.get("success") is True and isinstance(j.get("mappings"), list)
    t.add(
        "P2 /api/forums get_mappings valid",
        ok,
        f"status={r.status_code} success={j.get('success')} mappings_len={len(j.get('mappings', []) or [])}",
    )
except Exception as e:
    t.add("P2 /api/forums get_mappings valid", False, f"parse: {e} body={r.text[:200]}")


# P3. POST /api/forums get_mappings missing args -> success=false
r = req("POST", "/forums", json={"get_mappings": True, "forum_id": "", "user_id": ""})
try:
    j = r.json()
    ok = r.status_code == 200 and j.get("success") is False
    t.add(
        "P3 /api/forums get_mappings missing args",
        ok,
        f"status={r.status_code} success={j.get('success')} error={j.get('error')}",
    )
except Exception as e:
    t.add("P3 /api/forums get_mappings missing args", False, f"parse: {e} body={r.text[:200]}")


# P4. POST /api/forums create
forum_name = "V5-Test-Forum-XYZ"
r = req(
    "POST",
    "/forums",
    json={"name": forum_name, "description": "v5 test", "user_id": PETE_ID},
)
try:
    j = r.json()
    fid = j.get("id", "")
    is_hex_24 = isinstance(fid, str) and len(fid) == 24 and all(c in "0123456789abcdef" for c in fid)
    invite = j.get("invite_token", "")
    ok = (
        r.status_code == 200
        and is_hex_24
        and j.get("name") == forum_name
        and isinstance(invite, str)
        and len(invite) == 12
        and j.get("member_count") == 1
    )
    t.add(
        "P4 /api/forums create",
        ok,
        f"status={r.status_code} id={fid} name={j.get('name')} invite_len={len(invite)} member_count={j.get('member_count')}",
    )
    if is_hex_24:
        t.captured["v5_forum_id"] = fid
except Exception as e:
    t.add("P4 /api/forums create", False, f"parse: {e} body={r.text[:300]}")


# P5. POST /api/forums create with invalid user_id -> 400
r = req("POST", "/forums", json={"name": "X", "user_id": "not-a-real-id"})
try:
    body = r.text
    j = None
    try:
        j = r.json()
    except Exception:
        pass
    detail = (j or {}).get("detail", "") if isinstance(j, dict) else ""
    ok = r.status_code == 400 and "Invalid user_id" in str(detail)
    t.add(
        "P5 /api/forums create invalid user_id",
        ok,
        f"status={r.status_code} detail={detail!r} body={body[:200]}",
    )
except Exception as e:
    t.add("P5 /api/forums create invalid user_id", False, f"parse: {e}")


# P6. GET /api/pattern-running-me/emotions
r = req("GET", "/pattern-running-me/emotions")
try:
    j = r.json()
    emos = j.get("emotions") or []
    ok = r.status_code == 200 and isinstance(emos, list) and len(emos) >= 5
    t.add(
        "P6 /api/pattern-running-me/emotions",
        ok,
        f"status={r.status_code} count={len(emos)} sample={emos[:3]}",
    )
except Exception as e:
    t.add("P6 /api/pattern-running-me/emotions", False, f"parse: {e} body={r.text[:200]}")


# P7. POST /api/pattern-running-me with minimal valid PatternRunningMePayload
# Required: title, emotions [1..3] (canonical), story, reflection optional
prm_body = {
    "title": "Rushing forward when uncertain",
    "emotions": ["Anxious"],
    "story": "When I feel uncertain about a decision, I notice I push forward harder rather than sitting with the discomfort. Today it happened in a work meeting.",
    "reflection": {
        "meaning": "I cope with uncertainty by accelerating.",
        "importance": "It costs me clarity and connection.",
        "impact": "I leave meetings feeling drained.",
    },
}
r = req("POST", f"/pattern-running-me?user_id={PETE_ID}", json=prm_body)
try:
    j = r.json()
    pid = j.get("id")
    ok = r.status_code == 200 and isinstance(pid, str) and len(pid) > 0
    t.add(
        "P7 POST /api/pattern-running-me create",
        ok,
        f"status={r.status_code} id={pid} keys={list(j.keys())[:8]}",
    )
    if ok:
        t.captured["v5_prm_id"] = pid
except Exception as e:
    t.add("P7 POST /api/pattern-running-me create", False, f"parse: {e} body={r.text[:400]}")


# P8. GET /api/pattern-running-me/user/{Pete}
r = req("GET", f"/pattern-running-me/user/{PETE_ID}")
try:
    j = r.json()
    items = j.get("items") or []
    target = t.captured.get("v5_prm_id")
    found = any(it.get("id") == target for it in items) if target else False
    ok = r.status_code == 200 and isinstance(items, list) and (found or not target)
    t.add(
        "P8 GET /api/pattern-running-me/user/{Pete}",
        ok,
        f"status={r.status_code} items_len={len(items)} found_p7_id={found} target={target}",
    )
except Exception as e:
    t.add("P8 GET /api/pattern-running-me/user/{Pete}", False, f"parse: {e} body={r.text[:300]}")


# P9. POST /api/pattern-running-me with forum where Pete is NOT a member -> 403
non_member_forum = "697ffffffffffffffffffffe"
prm_body_403 = dict(prm_body)
prm_body_403["forum_id"] = non_member_forum
r = req("POST", f"/pattern-running-me?user_id={PETE_ID}", json=prm_body_403)
try:
    ok = r.status_code == 403
    t.add(
        "P9 POST /api/pattern-running-me non-member forum",
        ok,
        f"status={r.status_code} body={r.text[:200]}",
    )
except Exception as e:
    t.add("P9 POST /api/pattern-running-me non-member forum", False, f"parse: {e}")


# === G* REGRESSION ===

# G1. /api/mirror/chat zi_wei
r = req(
    "POST",
    "/mirror/chat",
    json={"user_id": PETE_ID, "lens": "zi_wei", "message": "What does my chart say?"},
)
try:
    j = r.json()
    dbg = j.get("debug", {})
    lc = dbg.get("lens_chat", {}) if isinstance(dbg, dict) else {}
    ok = (
        r.status_code == 200
        and lc.get("lens") == "zi_wei"
        and lc.get("marker") == "multi-lens-chat-memory-v1"
    )
    t.add(
        "G1 /api/mirror/chat zi_wei",
        ok,
        f"status={r.status_code} lens={lc.get('lens')} marker={lc.get('marker')}",
    )
except Exception as e:
    t.add("G1 /api/mirror/chat zi_wei", False, f"parse: {e} body={getattr(r,'text','')[:300]}")


# G2. /api/mirror/chat astrology
r = req(
    "POST",
    "/mirror/chat",
    json={"user_id": PETE_ID, "lens": "astrology", "message": "how am I?"},
)
try:
    j = r.json()
    dbg = j.get("debug", {})
    lc = dbg.get("lens_chat", {}) if isinstance(dbg, dict) else {}
    ok = r.status_code == 200 and lc.get("lens") == "astrology"
    t.add(
        "G2 /api/mirror/chat astrology",
        ok,
        f"status={r.status_code} lens={lc.get('lens')}",
    )
except Exception as e:
    t.add("G2 /api/mirror/chat astrology", False, f"parse: {e} body={getattr(r,'text','')[:300]}")


# G3. /api/mirror/chat lens=null contradictions marker
r = req(
    "POST",
    "/mirror/chat",
    json={"user_id": PETE_ID, "lens": None, "message": "hi"},
)
try:
    j = r.json()
    dbg = j.get("debug", {})
    contr = dbg.get("contradictions", {}) if isinstance(dbg, dict) else {}
    ok = (
        r.status_code == 200
        and contr.get("marker") == "contradiction-intelligence-v1"
    )
    t.add(
        "G3 /api/mirror/chat lens=null contradictions",
        ok,
        f"status={r.status_code} marker={contr.get('marker')}",
    )
except Exception as e:
    t.add("G3 /api/mirror/chat lens=null contradictions", False, f"parse: {e} body={getattr(r,'text','')[:300]}")


# G4. GET /api/forums/{forum}/story-of-circle
r = req("GET", f"/forums/{FORUM_ID}/story-of-circle")
try:
    j = r.json()
    # marker may be nested at top-level or inside data
    marker = j.get("marker")
    if not marker and isinstance(j.get("debug"), dict):
        marker = j["debug"].get("marker")
    ok = r.status_code == 200 and marker == "forum-topology-and-timing-v1"
    t.add(
        "G4 GET /api/forums/{forum}/story-of-circle",
        ok,
        f"status={r.status_code} marker={marker}",
    )
except Exception as e:
    t.add("G4 GET /api/forums/{forum}/story-of-circle", False, f"parse: {e} body={getattr(r,'text','')[:200]}")


# G5. POST /api/forums/{forum}/mirror-chat
r = req(
    "POST",
    f"/forums/{FORUM_ID}/mirror-chat",
    json={"user_id": PETE_ID, "forum_id": FORUM_ID, "message": "what's softening?"},
)
try:
    j = r.json()
    dbg = j.get("debug", {}) if isinstance(j, dict) else {}
    marker = dbg.get("marker") if isinstance(dbg, dict) else None
    ok = r.status_code == 200 and marker == "forum-conversational-field-v1"
    t.add(
        "G5 POST /api/forums/{forum}/mirror-chat",
        ok,
        f"status={r.status_code} marker={marker}",
    )
except Exception as e:
    t.add("G5 POST /api/forums/{forum}/mirror-chat", False, f"parse: {e} body={getattr(r,'text','')[:200]}")


# G6. GET /api/forums/{forum}/chat/history?user_id=Pete
r = req("GET", f"/forums/{FORUM_ID}/chat/history?user_id={PETE_ID}")
try:
    j = r.json()
    ok = r.status_code == 200 and j.get("success") is True
    t.add(
        "G6 GET /api/forums/{forum}/chat/history",
        ok,
        f"status={r.status_code} success={j.get('success')}",
    )
except Exception as e:
    t.add("G6 GET /api/forums/{forum}/chat/history", False, f"parse: {e} body={getattr(r,'text','')[:200]}")


# G7. GET /api/forums/{forum}/exercise?user_id=Pete
r = req("GET", f"/forums/{FORUM_ID}/exercise?user_id={PETE_ID}")
ok = (not isinstance(r, Exception)) and r.status_code == 200
t.add(
    "G7 GET /api/forums/{forum}/exercise",
    ok,
    f"status={getattr(r,'status_code',None)}",
)


# G8. GET /api/forums/{forum}/members?user_id=Pete
r = req("GET", f"/forums/{FORUM_ID}/members?user_id={PETE_ID}")
try:
    j = r.json()
    members = j.get("members") or []
    ok = r.status_code == 200 and len(members) == 2
    t.add(
        "G8 GET /api/forums/{forum}/members",
        ok,
        f"status={r.status_code} members_len={len(members)}",
    )
except Exception as e:
    t.add("G8 GET /api/forums/{forum}/members", False, f"parse: {e} body={getattr(r,'text','')[:200]}")


# G9. GET /api/forums/domains/list
r = req("GET", "/forums/domains/list")
try:
    j = r.json()
    domains = j.get("domains") or []
    ok = r.status_code == 200 and len(domains) == 7
    t.add(
        "G9 GET /api/forums/domains/list",
        ok,
        f"status={r.status_code} domains_len={len(domains)}",
    )
except Exception as e:
    t.add("G9 GET /api/forums/domains/list", False, f"parse: {e} body={getattr(r,'text','')[:200]}")


# G10. GET /api/admin/forum/export/PeteAndMel?admin_key=wrong -> 403
r = req("GET", "/admin/forum/export/PeteAndMel?admin_key=wrong")
ok = (not isinstance(r, Exception)) and r.status_code == 403
t.add("G10 admin export wrong key -> 403", ok, f"status={getattr(r,'status_code',None)}")


# G11. POST /api/micro-reflection/home-texture
r = req(
    "POST",
    "/micro-reflection/home-texture",
    json={"user_id": PETE_ID, "texture": "open"},
)
try:
    j = r.json()
    marker = j.get("marker") or (j.get("debug", {}) or {}).get("marker")
    ok = r.status_code == 200 and marker == "micro-reflection-v3-home-texture"
    t.add(
        "G11 POST /api/micro-reflection/home-texture",
        ok,
        f"status={r.status_code} marker={marker}",
    )
    hid = j.get("id") or j.get("_id")
    if hid:
        t.captured["v5_hometex_id"] = hid
except Exception as e:
    t.add("G11 POST /api/micro-reflection/home-texture", False, f"parse: {e} body={getattr(r,'text','')[:200]}")


# === CLEANUP ===

# P10. delete forum from P4
fid = t.captured.get("v5_forum_id")
if fid:
    r = req("POST", f"/forums/{fid}/delete?user_id={PETE_ID}")
    try:
        j = r.json()
        ok = r.status_code == 200 and j.get("success") is True
        t.add("P10 cleanup delete forum", ok, f"status={r.status_code} success={j.get('success')}")
    except Exception as e:
        t.add("P10 cleanup delete forum", False, f"parse: {e} body={getattr(r,'text','')[:200]}")
else:
    t.add("P10 cleanup delete forum", False, "no forum_id captured")


# P11 + G11c cleanup via mongo
try:
    import asyncio
    from motor.motor_asyncio import AsyncIOMotorClient
    sys.path.insert(0, "/app/backend")
    from dotenv import load_dotenv
    load_dotenv("/app/backend/.env")
    from bson import ObjectId
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME") or "test_database"

    async def cleanup():
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        prm_id = t.captured.get("v5_prm_id")
        if prm_id:
            try:
                res = await db.pattern_running_me_v2.delete_one({"_id": ObjectId(prm_id)})
                t.add("P11 cleanup pattern_running_me_v2 doc", res.deleted_count == 1, f"deleted={res.deleted_count}")
            except Exception as e:
                t.add("P11 cleanup pattern_running_me_v2 doc", False, f"err={e}")
        else:
            # fallback: delete most recent for Pete
            try:
                doc = await db.pattern_running_me_v2.find_one({"user_id": PETE_ID}, sort=[("created_at", -1)])
                if doc:
                    await db.pattern_running_me_v2.delete_one({"_id": doc["_id"]})
                    t.add("P11 cleanup pattern_running_me_v2 doc (fallback)", True, "deleted most-recent")
                else:
                    t.add("P11 cleanup pattern_running_me_v2 doc (fallback)", False, "no doc")
            except Exception as e:
                t.add("P11 cleanup pattern_running_me_v2 doc (fallback)", False, f"err={e}")
        try:
            res = await db.micro_reflections.delete_many({"user_id": PETE_ID, "source": "home_texture"})
            t.add("G11c cleanup home_texture", True, f"deleted={res.deleted_count}")
        except Exception as e:
            # collection name may differ; try alternative
            try:
                res = await db.home_texture.delete_many({"user_id": PETE_ID})
                t.add("G11c cleanup home_texture (alt collection)", True, f"deleted={res.deleted_count}")
            except Exception as e2:
                t.add("G11c cleanup home_texture", False, f"err1={e} err2={e2}")
        client.close()

    asyncio.run(cleanup())
except Exception as e:
    t.add("cleanup (mongo)", False, f"err={e}")


print("\n\n===== FINAL SUMMARY =====")
passed, total = t.summary()
sys.exit(0 if passed == total else 1)
