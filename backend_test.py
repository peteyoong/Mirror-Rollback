"""
Backend regression test — Server Router Refactor v6
Build marker: server-router-refactor-v6
"""

import os
import json
import time
import sys
import requests

BASE = "https://signup-issues-1.preview.emergentagent.com/api"

FORUM_ID = "69dd05eaa333335fcbf3ad33"
PETE_ID = "697f0c6abf35c0528ff06954"
MEL_ID = "697ec826ad4b18f75bf42616"

results = []

def record(name, ok, detail=""):
    results.append((name, ok, detail))
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}: {detail}")

def get(path, **params):
    return requests.get(BASE + path, params=params, timeout=60)

def post(path, json_body=None, **params):
    return requests.post(BASE + path, params=params, json=json_body, timeout=120)


# ============== A) NEW INTELLIGENCE ROUTES ==============

def test_a1_member_lens():
    r = get(f"/forums/{FORUM_ID}/member-lens/{PETE_ID}", user_id=PETE_ID)
    if r.status_code != 200:
        record("A1 member-lens", False, f"HTTP {r.status_code} - {r.text[:200]}")
        return
    j = r.json()
    if not j.get("success"):
        record("A1 member-lens", False, f"success!=true; {json.dumps(j)[:200]}")
        return
    lens = j.get("lens_data") or {}
    expected = ["human_design", "enneagram", "astrology", "bazi", "numerology", "patterns", "compute_status"]
    missing = [k for k in expected if k not in lens]
    if missing:
        record("A1 member-lens", False, f"missing keys: {missing}")
        return
    record("A1 member-lens", True, f"hd_type={lens['human_design'].get('type')}")

def test_a2_member_mappings():
    r = get(f"/forums/{FORUM_ID}/member-mappings", user_id=PETE_ID)
    if r.status_code != 200:
        record("A2 member-mappings", False, f"HTTP {r.status_code} - {r.text[:200]}")
        return
    j = r.json()
    if not j.get("success") or not isinstance(j.get("mappings"), list) or j.get("current_user_id") != PETE_ID:
        record("A2 member-mappings", False, f"keys={list(j.keys())}")
        return
    record("A2 member-mappings", True, f"mappings={len(j['mappings'])}")

def test_a3_relationship_map_alias():
    r1 = get(f"/forums/{FORUM_ID}/member-mappings", user_id=PETE_ID)
    r2 = get(f"/forums/{FORUM_ID}/relationship-map", user_id=PETE_ID)
    if r1.status_code != 200 or r2.status_code != 200:
        record("A3 relationship-map alias", False, f"HTTP {r1.status_code}/{r2.status_code}")
        return
    j1, j2 = r1.json(), r2.json()
    if set(j1.keys()) != set(j2.keys()) or len(j1.get("mappings", [])) != len(j2.get("mappings", [])):
        record("A3 relationship-map alias", False, "shapes differ")
        return
    record("A3 relationship-map alias", True, "alias identical")

def test_a4_contributions():
    r = get(f"/forums/{FORUM_ID}/contributions", user_id=PETE_ID)
    if r.status_code != 200:
        record("A4 contributions", False, f"HTTP {r.status_code}")
        return
    j = r.json()
    if not j.get("success") or not isinstance(j.get("contributions"), list):
        record("A4 contributions", False, f"keys={list(j.keys())}")
        return
    record("A4 contributions", True, f"n={len(j['contributions'])}")

def test_a5_dynamics_context():
    r = get(f"/forums/{FORUM_ID}/dynamics-context", user_id=PETE_ID)
    if r.status_code != 200:
        record("A5 dynamics-context", False, f"HTTP {r.status_code}")
        return
    j = r.json()
    if not j.get("success"):
        record("A5 dynamics-context", False, "success!=true")
        return
    ctx = j.get("context") or {}
    expected = ["member_count", "hd_type_distribution", "hd_authority_distribution",
                "enneagram_distribution", "astrology_elements"]
    missing = [k for k in expected if k not in ctx]
    if missing:
        record("A5 dynamics-context", False, f"missing: {missing}")
        return
    record("A5 dynamics-context", True,
           f"members={ctx['member_count']}, hd={ctx['hd_type_distribution']}")

def test_a6_pairwise_dynamics():
    body = {"user_id": PETE_ID, "member_a_id": PETE_ID, "member_b_id": MEL_ID}
    r = post(f"/forums/{FORUM_ID}/pairwise-dynamics", json_body=body)
    if r.status_code != 200:
        record("A6 pairwise-dynamics", False, f"HTTP {r.status_code} - {r.text[:300]}")
        return
    j = r.json()
    if not j.get("success"):
        record("A6 pairwise-dynamics", False, f"success!=true; {json.dumps(j)[:300]}")
        return
    refl = j.get("reflection") or ""
    if not refl or len(refl) < 50:
        record("A6 pairwise-dynamics", False, f"short reflection: {len(refl)}")
        return
    if "member_a" not in j or "member_b" not in j:
        record("A6 pairwise-dynamics", False, "member_a/b missing")
        return
    record("A6 pairwise-dynamics", True, f"reflection_len={len(refl)} (NameError fix verified)")

def test_a7_pattern_map():
    r = get(f"/forums/{FORUM_ID}/pattern-map", user_id=PETE_ID)
    if r.status_code != 200:
        record("A7 pattern-map", False, f"HTTP {r.status_code} - {r.text[:200]}")
        return
    j = r.json()
    expected = ["member_count", "events_total", "shared_patterns", "timeline_clusters"]
    missing = [k for k in expected if k not in j]
    if missing:
        record("A7 pattern-map", False, f"missing keys: {missing}")
        return
    record("A7 pattern-map", True,
           f"m={j['member_count']}, e={j['events_total']}, "
           f"p={len(j['shared_patterns'])}, c={len(j['timeline_clusters'])}")

def test_a8_authorisation():
    non_member = "6971cc4381beab3a8955b256"
    r = get(f"/forums/{FORUM_ID}/member-lens/{PETE_ID}", user_id=non_member)
    if r.status_code == 403:
        record("A8 auth-403 non-member", True, "blocked")
    else:
        record("A8 auth-403 non-member", False, f"expected 403 got {r.status_code}")

def test_a9_invalid_forum_id():
    r = get("/forums/not-a-real-id/member-mappings", user_id=PETE_ID)
    if r.status_code == 400:
        record("A9 invalid forum_id 400", True, "rejected")
    else:
        record("A9 invalid forum_id 400", False, f"expected 400 got {r.status_code}")


# ============== B) FORUMS CHAT (router unchanged, helpers re-wired) ==============

def test_b1_chat_history():
    r = get(f"/forums/{FORUM_ID}/chat/history", user_id=PETE_ID, limit=5)
    if r.status_code != 200:
        record("B1 chat/history", False, f"HTTP {r.status_code}")
        return
    j = r.json()
    record("B1 chat/history", True, f"keys={list(j.keys())[:6] if isinstance(j, dict) else 'list'}")

def _chat_post(mode, target=None, wait_seconds=4):
    if wait_seconds:
        time.sleep(wait_seconds)
    body = {"user_id": PETE_ID, "message": f"Reflection test ({mode}).", "mode": mode}
    if target:
        body["target_member_id"] = target
    return post(f"/forums/{FORUM_ID}/chat", json_body=body)

def test_b2_chat_modes():
    r = _chat_post("forum", wait_seconds=4)
    ok = r.status_code == 200
    record("B2a chat mode=forum", ok, f"HTTP {r.status_code} - {r.text[:200] if not ok else 'ok'}")

    r = _chat_post("self", wait_seconds=4)
    ok = r.status_code == 200
    record("B2b chat mode=self", ok, f"HTTP {r.status_code} - {r.text[:200] if not ok else 'ok'}")

    r = _chat_post("member", target=MEL_ID, wait_seconds=4)
    ok = r.status_code == 200
    record("B2c chat mode=member", ok, f"HTTP {r.status_code} - {r.text[:200] if not ok else 'ok'}")

def test_b3_rate_limit():
    time.sleep(4)
    body = {"user_id": PETE_ID, "message": "RL probe 1.", "mode": "forum"}
    r1 = post(f"/forums/{FORUM_ID}/chat", json_body=body)
    body2 = {"user_id": PETE_ID, "message": "RL probe 2.", "mode": "forum"}
    r2 = post(f"/forums/{FORUM_ID}/chat", json_body=body2)
    if r1.status_code == 200 and r2.status_code == 429:
        record("B3 rate-limit", True, "second req blocked 429")
    else:
        record("B3 rate-limit", False, f"r1={r1.status_code}, r2={r2.status_code}")


# ============== C) STILL-INLINE FORUM ROUTES ==============

def test_c1_story_of_circle():
    r = get(f"/forums/{FORUM_ID}/story-of-circle", user_id=PETE_ID)
    if r.status_code != 200:
        record("C1 story-of-circle", False, f"HTTP {r.status_code} - {r.text[:200]}")
        return
    j = r.json()
    record("C1 story-of-circle", True, f"keys={list(j.keys())[:6]}")

def test_c2_mirror_chat_forum():
    time.sleep(4)
    body = {"user_id": PETE_ID, "forum_id": FORUM_ID, "message": "Brief check-in."}
    r = post(f"/forums/{FORUM_ID}/mirror-chat", json_body=body)
    if r.status_code != 200:
        record("C2 forum/mirror-chat", False, f"HTTP {r.status_code} - {r.text[:200]}")
        return
    record("C2 forum/mirror-chat", True, "HTTP 200")

def test_c3_member_summary():
    r = get(f"/forums/{FORUM_ID}/member-summary/{MEL_ID}", user_id=PETE_ID)
    if r.status_code != 200:
        record("C3 member-summary inline", False, f"HTTP {r.status_code}")
        return
    record("C3 member-summary inline", True, "HTTP 200")


# ============== D) /api/mirror/chat debug payload preservation ==============

def test_d_mirror_chat_lenses():
    for label, lens in [("astrology", "astrology"), ("zi_wei", "zi_wei"), ("null", None)]:
        time.sleep(2)
        body = {"user_id": PETE_ID, "message": f"Quick reflection ({label})."}
        if lens is not None:
            body["lens"] = lens
        r = post("/mirror/chat", json_body=body)
        if r.status_code != 200:
            record(f"D mirror/chat lens={label}", False, f"HTTP {r.status_code} - {r.text[:200]}")
            continue
        j = r.json()
        has_resp = bool(j.get("response"))
        debug = j.get("debug") or {}
        lens_chat = debug.get("lens_chat") or {}
        if lens is not None:
            marker_ok = ("marker" in lens_chat) or ("marker" in debug)
            lens_ok = ("lens" in lens_chat) or ("lens" in debug)
            ok = has_resp and marker_ok and lens_ok
            detail = f"resp={has_resp}, debug.keys={list(debug.keys())}, lens_chat.keys={list(lens_chat.keys())}"
        else:
            ok = has_resp
            detail = f"resp={has_resp}, debug.keys={list(debug.keys())}"
        record(f"D mirror/chat lens={label}", ok, detail)


# ============== E) Previously extracted routers (sanity) ==============

def test_e1_admin_forum_wrong_key():
    r = get("/admin/forum/export/PeteAndMel", admin_key="wrong")
    if r.status_code == 403:
        try:
            j = r.json()
            detail = j.get("detail", "")
        except Exception:
            detail = ""
        record("E1 admin_forum 403", True, f"detail='{detail}'")
    else:
        record("E1 admin_forum 403", False, f"expected 403 got {r.status_code}")

def test_e2_forums_core_list():
    r = get(f"/forums/user/{PETE_ID}")
    if r.status_code != 200:
        record("E2 forums_core list", False, f"HTTP {r.status_code}")
        return
    j = r.json()
    record("E2 forums_core list", True, f"type={type(j).__name__}")

def test_e3_forums_field():
    candidates = [
        f"/forums/{FORUM_ID}/forum-field?user_id={PETE_ID}",
        f"/forums/{FORUM_ID}/field?user_id={PETE_ID}",
        f"/forums/{FORUM_ID}/field/state?user_id={PETE_ID}",
        f"/forums/{FORUM_ID}/live-field?user_id={PETE_ID}",
    ]
    for c in candidates:
        r = requests.get(BASE + c, timeout=30)
        if r.status_code == 200:
            record("E3 forums_field", True, f"{c.split('?')[0]} HTTP 200")
            return
    record("E3 forums_field", False, "no forum_field route responded 200")

def test_e4_forums_create_auth():
    # POST /forums with empty body should be 4xx (router responding, not 5xx)
    r = post("/forums", json_body={})
    ok = r.status_code in (400, 401, 403, 422)
    record("E4 forums_create_auth probe", ok, f"HTTP {r.status_code}")

def test_e5_forums_exercise():
    r = get(f"/forums/{FORUM_ID}/exercise", user_id=PETE_ID)
    ok = r.status_code == 200
    record("E5 forums_exercise", ok, f"HTTP {r.status_code}")

def test_e6_micro_reflection():
    body = {"user_id": PETE_ID, "texture": "open", "domain": "self"}
    r = post("/micro-reflection/home-texture", json_body=body)
    ok = r.status_code == 200
    record("E6 micro-reflection/home-texture", ok, f"HTTP {r.status_code} - {r.text[:200] if not ok else 'ok'}")

def test_e7_pattern_running_me():
    r = get(f"/pattern-running-me/user/{PETE_ID}")
    ok = r.status_code == 200
    record("E7 pattern-running-me", ok, f"HTTP {r.status_code}")

def test_e8_topology_editor():
    candidates = [
        f"/topology/forum/{FORUM_ID}?user_id={PETE_ID}",
        f"/topology/{FORUM_ID}?user_id={PETE_ID}",
        f"/forums/{FORUM_ID}/topology?user_id={PETE_ID}",
        f"/topology-editor/forum/{FORUM_ID}?user_id={PETE_ID}",
    ]
    for c in candidates:
        r = requests.get(BASE + c, timeout=30)
        if r.status_code in (200,):
            record("E8 topology_editor", True, f"{c.split('?')[0]} HTTP 200")
            return
        if r.status_code in (400, 403, 404, 405):
            # Router is alive but route shape differs — note last attempt
            last = (c, r.status_code)
    record("E8 topology_editor", False, f"no topology route returned 200")


def run_all():
    print(f"\n=== Backend Regression: server-router-refactor-v6 ===")
    print(f"Base URL: {BASE}\n")

    print("--- A) Intelligence routes ---")
    for t in [test_a1_member_lens, test_a2_member_mappings, test_a3_relationship_map_alias,
              test_a4_contributions, test_a5_dynamics_context, test_a6_pairwise_dynamics,
              test_a7_pattern_map, test_a8_authorisation, test_a9_invalid_forum_id]:
        try:
            t()
        except Exception as e:
            record(t.__name__, False, f"exception: {e}")

    print("\n--- B) Forums chat ---")
    for t in [test_b1_chat_history, test_b2_chat_modes, test_b3_rate_limit]:
        try:
            t()
        except Exception as e:
            record(t.__name__, False, f"exception: {e}")

    print("\n--- C) Still-inline ---")
    for t in [test_c1_story_of_circle, test_c2_mirror_chat_forum, test_c3_member_summary]:
        try:
            t()
        except Exception as e:
            record(t.__name__, False, f"exception: {e}")

    print("\n--- D) /api/mirror/chat ---")
    try:
        test_d_mirror_chat_lenses()
    except Exception as e:
        record("D mirror_chat_lenses", False, f"exception: {e}")

    print("\n--- E) Previously extracted routers ---")
    for t in [test_e1_admin_forum_wrong_key, test_e2_forums_core_list, test_e3_forums_field,
              test_e4_forums_create_auth, test_e5_forums_exercise, test_e6_micro_reflection,
              test_e7_pattern_running_me, test_e8_topology_editor]:
        try:
            t()
        except Exception as e:
            record(t.__name__, False, f"exception: {e}")

    print("\n=== Summary ===")
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"PASS: {passed}/{total}")
    fails = [(n, d) for n, ok, d in results if not ok]
    if fails:
        print("\nFAILURES:")
        for n, d in fails:
            print(f"  FAIL {n}: {d}")
    return passed, total, fails


if __name__ == "__main__":
    p, t, f = run_all()
    sys.exit(0 if not f else 1)
