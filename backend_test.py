"""
Regression test for server-router-refactor-v3 extraction pass.
Tests the lens_chat debug shape fix and the new admin_forum + forums_core router extractions.
"""

import os
import requests
from pymongo import MongoClient

BACKEND_URL = "https://behavioral-lens-2.preview.emergentagent.com"
API = f"{BACKEND_URL}/api"

PETE = "697f0c6abf35c0528ff06954"
FORUM = "69dd05eaa333335fcbf3ad33"
NON_MEMBER = "697ffffffffffffffffffffe"

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")

results = []

def log(vid, passed, msg=""):
    icon = "✅" if passed else "❌"
    print(f"{icon} {vid}: {msg}")
    results.append((vid, passed, msg))

def get(url, **kw):
    return requests.get(url, timeout=60, **kw)

def post(url, **kw):
    return requests.post(url, timeout=120, **kw)


def v1_zi_wei():
    try:
        r = post(f"{API}/mirror/chat", json={
            "user_id": PETE, "lens": "zi_wei",
            "message": "What does my chart say about pressure?"
        })
        if r.status_code != 200:
            return log("V1", False, f"status {r.status_code}: {r.text[:200]}")
        data = r.json()
        debug = data.get("debug", {})
        checks = []
        if debug.get("marker") != "multi-lens-chat-memory-v1":
            checks.append(f"debug.marker={debug.get('marker')}")
        if debug.get("lens") != "zi_wei":
            checks.append(f"debug.lens={debug.get('lens')}")
        lens_chat = debug.get("lens_chat", {})
        if lens_chat.get("marker") != "multi-lens-chat-memory-v1":
            checks.append(f"debug.lens_chat.marker={lens_chat.get('marker')}")
        if lens_chat.get("lens") != "zi_wei":
            checks.append(f"debug.lens_chat.lens={lens_chat.get('lens')}")
        contradictions = debug.get("contradictions")
        if not contradictions:
            checks.append("debug.contradictions missing")
        elif contradictions.get("marker") != "contradiction-intelligence-v1":
            checks.append(f"contradictions.marker={contradictions.get('marker')}")
        reply = (data.get("response") or data.get("reply") or "").lower()
        forbidden = ['destiny', 'fated', 'palace', 'zi wei', 'hua lu', 'manifestor']
        found = [w for w in forbidden if w in reply]
        if found:
            checks.append(f"forbidden jargon: {found}")
        if checks:
            return log("V1", False, "; ".join(checks))
        return log("V1", True, "marker+lens+lens_chat+contradictions OK; no forbidden jargon")
    except Exception as e:
        return log("V1", False, f"exc: {e}")


def v2_null_lens():
    try:
        r = post(f"{API}/mirror/chat", json={
            "user_id": PETE, "lens": None,
            "message": "Hello, checking in."
        })
        if r.status_code != 200:
            return log("V2", False, f"status {r.status_code}: {r.text[:200]}")
        debug = r.json().get("debug", {})
        c = debug.get("contradictions")
        if not c:
            return log("V2", False, "debug.contradictions missing")
        if c.get("marker") != "contradiction-intelligence-v1":
            return log("V2", False, f"contradictions.marker={c.get('marker')}")
        return log("V2", True, "contradictions marker OK")
    except Exception as e:
        return log("V2", False, f"exc: {e}")


def v3_astrology():
    try:
        r = post(f"{API}/mirror/chat", json={
            "user_id": PETE, "lens": "astrology",
            "message": "What's happening for me lately?"
        })
        if r.status_code != 200:
            return log("V3", False, f"status {r.status_code}: {r.text[:200]}")
        debug = r.json().get("debug", {})
        lens_chat = debug.get("lens_chat", {})
        if lens_chat.get("lens") != "astrology":
            return log("V3", False, f"debug.lens_chat.lens={lens_chat.get('lens')}")
        return log("V3", True, "debug.lens_chat.lens == astrology")
    except Exception as e:
        return log("V3", False, f"exc: {e}")


def v4_forum_get():
    try:
        r = get(f"{API}/forums/{FORUM}", params={"user_id": PETE})
        if r.status_code != 200:
            return log("V4", False, f"status {r.status_code}: {r.text[:200]}")
        data = r.json()
        f = data.get("forum", data)
        required = ["id", "name", "invite_token", "created_by", "member_count", "created_at"]
        missing = [k for k in required if k not in f]
        if missing:
            return log("V4", False, f"missing: {missing}; keys={list(f.keys())}")
        v4_forum_get.invite_token = f.get("invite_token")
        return log("V4", True, f"all fields present; invite_token={v4_forum_get.invite_token[:12]}...")
    except Exception as e:
        return log("V4", False, f"exc: {e}")
v4_forum_get.invite_token = None


def v5_user_forums():
    try:
        r = get(f"{API}/forums/user/{PETE}")
        if r.status_code != 200:
            return log("V5", False, f"status {r.status_code}: {r.text[:200]}")
        forums = r.json().get("forums")
        if not isinstance(forums, list):
            return log("V5", False, f"forums not list")
        if len(forums) < 1:
            return log("V5", False, f"len={len(forums)}")
        return log("V5", True, f"forums list len={len(forums)}")
    except Exception as e:
        return log("V5", False, f"exc: {e}")


def v6_post_user_forums():
    try:
        r = post(f"{API}/get-user-forums", json={"user_id": PETE})
        if r.status_code != 200:
            return log("V6", False, f"status {r.status_code}: {r.text[:200]}")
        forums = r.json().get("forums")
        if not isinstance(forums, list):
            return log("V6", False, "forums not list")
        cc = r.headers.get("Cache-Control", "")
        if "no-store" not in cc.lower():
            return log("V6", False, f"Cache-Control='{cc}' missing no-store")
        return log("V6", True, f"forums len={len(forums)}, Cache-Control='{cc}'")
    except Exception as e:
        return log("V6", False, f"exc: {e}")


def v7_members():
    try:
        r = get(f"{API}/forums/{FORUM}/members", params={"user_id": PETE})
        if r.status_code != 200:
            return log("V7", False, f"status {r.status_code}: {r.text[:200]}")
        members = r.json().get("members", [])
        if len(members) != 2:
            return log("V7", False, f"len={len(members)}")
        for m in members:
            for k in ["user_id", "user_name", "role", "joined_at"]:
                if k not in m:
                    return log("V7", False, f"missing field {k}")
        return log("V7", True, f"2 members: {[m['user_name'] for m in members]}")
    except Exception as e:
        return log("V7", False, f"exc: {e}")


def v8_members_non_member():
    try:
        r = get(f"{API}/forums/{FORUM}/members", params={"user_id": NON_MEMBER})
        if r.status_code != 403:
            return log("V8", False, f"status {r.status_code}: {r.text[:200]}")
        detail = r.json().get("detail", "")
        if "not a member" not in detail.lower():
            return log("V8", False, f"detail: {detail}")
        return log("V8", True, f"403 '{detail}'")
    except Exception as e:
        return log("V8", False, f"exc: {e}")


def v9_domains():
    try:
        r = get(f"{API}/forums/domains/list")
        if r.status_code != 200:
            return log("V9", False, f"status {r.status_code}: {r.text[:200]}")
        domains = r.json().get("domains", [])
        if len(domains) != 7:
            return log("V9", False, f"len={len(domains)}")
        ids = [d.get("id") for d in domains]
        if "energy_vitality" not in ids:
            return log("V9", False, f"energy_vitality missing: {ids}")
        return log("V9", True, "7 domains, energy_vitality present")
    except Exception as e:
        return log("V9", False, f"exc: {e}")


def v10_invite():
    try:
        token = v4_forum_get.invite_token
        if not token:
            return log("V10", False, "no token")
        r = get(f"{API}/forums/invite/{token}")
        if r.status_code != 200:
            return log("V10", False, f"status {r.status_code}: {r.text[:200]}")
        data = r.json()
        f = data.get("forum", data)
        required = ["id", "name", "member_count", "created_at"]
        missing = [k for k in required if k not in f]
        if missing:
            return log("V10", False, f"missing: {missing}; keys={list(f.keys())}")
        return log("V10", True, "all fields present")
    except Exception as e:
        return log("V10", False, f"exc: {e}")


def v11_join():
    try:
        token = v4_forum_get.invite_token
        if not token:
            return log("V11", False, "no token")
        r = post(f"{API}/forums/join/{token}", json={"user_id": PETE})
        if r.status_code != 200:
            return log("V11", False, f"status {r.status_code}: {r.text[:200]}")
        d = r.json()
        if d.get("already_member") is not True:
            return log("V11", False, f"already_member={d.get('already_member')}; resp={d}")
        return log("V11", True, "already_member=true")
    except Exception as e:
        return log("V11", False, f"exc: {e}")


def v12_delete_non_owner():
    try:
        r = post(f"{API}/forums/{FORUM}/delete", params={"user_id": NON_MEMBER})
        if r.status_code != 403:
            return log("V12", False, f"status {r.status_code}: {r.text[:200]}")
        detail = r.json().get("detail", "")
        if "creator" not in detail.lower():
            return log("V12", False, f"detail: {detail}")
        return log("V12", True, f"403 '{detail}'")
    except Exception as e:
        return log("V12", False, f"exc: {e}")


def v13_export_wrong_key():
    try:
        r = get(f"{API}/admin/forum/export/PeteAndMel", params={"admin_key": "wrongkey"})
        if r.status_code != 403:
            return log("V13", False, f"status {r.status_code}: {r.text[:200]}")
        detail = r.json().get("detail", "")
        if detail != "Invalid admin key":
            return log("V13", False, f"detail: {detail}")
        return log("V13", True, "403 'Invalid admin key'")
    except Exception as e:
        return log("V13", False, f"exc: {e}")


def v14_import_wrong_key():
    try:
        r = post(f"{API}/admin/forum/import", json={"forum_data": {}, "admin_key": "wrong"})
        if r.status_code != 403:
            return log("V14", False, f"status {r.status_code}: {r.text[:200]}")
        detail = r.json().get("detail", "")
        if detail != "Invalid admin key":
            return log("V14", False, f"detail: {detail}")
        return log("V14", True, "403 'Invalid admin key'")
    except Exception as e:
        return log("V14", False, f"exc: {e}")


def v15_field_routes():
    sub = []
    try:
        r = get(f"{API}/forums/{FORUM}/topology", params={"user_id": PETE})
        ok = r.status_code == 200
        marker = ""
        if ok:
            try:
                j = r.json()
                marker = (j.get("debug", {}) or {}).get("marker") or j.get("marker", "")
            except: pass
        sub.append(("V15a", ok, f"status={r.status_code} marker='{marker}'"))
    except Exception as e:
        sub.append(("V15a", False, f"exc {e}"))

    try:
        r = post(f"{API}/forums/{FORUM}/topology/infer", json={"user_id": PETE})
        sub.append(("V15b", r.status_code == 200, f"status={r.status_code}"))
    except Exception as e:
        sub.append(("V15b", False, f"exc {e}"))

    try:
        r = get(f"{API}/forums/{FORUM}/story-of-circle", params={"user_id": PETE})
        ok = r.status_code == 200
        marker = ""
        if ok:
            try:
                j = r.json()
                marker = (j.get("debug", {}) or {}).get("marker") or j.get("marker", "")
            except: pass
        sub.append(("V15c", ok, f"status={r.status_code} marker='{marker}'"))
    except Exception as e:
        sub.append(("V15c", False, f"exc {e}"))

    try:
        r = post(f"{API}/forums/{FORUM}/mirror-chat", json={"user_id": PETE, "forum_id": FORUM, "message": "What softens?"})
        ok = r.status_code == 200
        marker = ""
        if ok:
            try:
                marker = (r.json().get("debug", {}) or {}).get("marker", "")
            except: pass
        ok2 = ok and marker == "forum-conversational-field-v1"
        sub.append(("V15d", ok2, f"status={r.status_code} marker='{marker}'"))
    except Exception as e:
        sub.append(("V15d", False, f"exc {e}"))

    try:
        r = get(f"{API}/forums/{FORUM}/mirror-chat/history", params={"user_id": PETE})
        sub.append(("V15e", r.status_code == 200, f"status={r.status_code}"))
    except Exception as e:
        sub.append(("V15e", False, f"exc {e}"))

    try:
        r = get(f"{API}/forums/{FORUM}/topology/roles", params={"user_id": PETE})
        ok = r.status_code == 200
        marker = ""
        if ok:
            try:
                j = r.json()
                marker = (j.get("debug", {}) or {}).get("marker") or j.get("marker", "")
            except: pass
        ok2 = ok and marker == "topology-editor-v2"
        sub.append(("V15f", ok2, f"status={r.status_code} marker='{marker}'"))
    except Exception as e:
        sub.append(("V15f", False, f"exc {e}"))

    all_ok = all(s[1] for s in sub)
    return log("V15", all_ok, "; ".join(f"{s[0]}={'OK' if s[1] else 'FAIL'}({s[2]})" for s in sub))


def v16_micro_reflection():
    sub = []
    try:
        r = post(f"{API}/micro-reflection/home-texture", json={"user_id": PETE, "texture": "open"})
        sub.append(("V16a", r.status_code == 200, f"status={r.status_code}"))
    except Exception as e:
        sub.append(("V16a", False, f"exc {e}"))

    try:
        r = get(f"{API}/micro-reflection/{PETE}/home-texture/today")
        ok = r.status_code == 200
        logged = False
        if ok:
            try:
                logged = r.json().get("logged_today") is True
            except: pass
        sub.append(("V16b", ok and logged, f"status={r.status_code} logged_today={logged}"))
    except Exception as e:
        sub.append(("V16b", False, f"exc {e}"))

    try:
        r = post(f"{API}/micro-reflection", json={"user_id": PETE, "label": "lands", "source": "other"})
        sub.append(("V16c", r.status_code == 200, f"status={r.status_code}"))
    except Exception as e:
        sub.append(("V16c", False, f"exc {e}"))

    try:
        r = get(f"{API}/micro-reflection/{PETE}/recent")
        sub.append(("V16d", r.status_code == 200, f"status={r.status_code}"))
    except Exception as e:
        sub.append(("V16d", False, f"exc {e}"))

    all_ok = all(s[1] for s in sub)
    return log("V16", all_ok, "; ".join(f"{s[0]}={'OK' if s[1] else 'FAIL'}({s[2]})" for s in sub))


def cleanup():
    try:
        client = MongoClient(MONGO_URL)
        db = client[DB_NAME]
        d1 = db.micro_reflections.delete_many({"user_id": PETE, "source": "home_texture"})
        recs = list(db.micro_reflections.find(
            {"user_id": PETE, "label": "lands", "source": "other"}
        ).sort("created_at", -1).limit(1))
        d2 = 0
        if recs:
            d2 = db.micro_reflections.delete_one({"_id": recs[0]["_id"]}).deleted_count
        print(f"\n🧹 CLEANUP: home_texture deleted={d1.deleted_count}, lands/other deleted={d2}")
        client.close()
    except Exception as e:
        print(f"⚠️ cleanup error: {e}")


def main():
    print("=" * 80)
    print(f"Server router refactor v3 — regression suite")
    print(f"Backend: {API}")
    print("=" * 80)

    v1_zi_wei()
    v2_null_lens()
    v3_astrology()
    v4_forum_get()
    v5_user_forums()
    v6_post_user_forums()
    v7_members()
    v8_members_non_member()
    v9_domains()
    v10_invite()
    v11_join()
    v12_delete_non_owner()
    v13_export_wrong_key()
    v14_import_wrong_key()
    v15_field_routes()
    v16_micro_reflection()

    cleanup()

    print("\n" + "=" * 80)
    passed = sum(1 for r in results if r[1])
    total = len(results)
    print(f"RESULT: {passed}/{total} passed")
    for vid, ok, msg in results:
        icon = "✅" if ok else "❌"
        print(f"  {icon} {vid}: {msg}")
    print("=" * 80)
    return 0 if passed == total else 1


if __name__ == "__main__":
    exit(main())
