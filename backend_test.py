"""
Regression test for server-router-refactor-v4 extraction pass.
Tests forums_chat + forums_exercise router extractions plus full G-suite
regression on previously extracted routes.
"""

import os
import time
import requests
from pymongo import MongoClient
from bson import ObjectId

BACKEND_URL = "https://behavioral-lens-2.preview.emergentagent.com"
API = f"{BACKEND_URL}/api"

PETE = "697f0c6abf35c0528ff06954"
FORUM = "69dd05eaa333335fcbf3ad33"
NON_MEMBER = "697ffffffffffffffffffffe"

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")

results = []


def log(vid, passed, msg=""):
    icon = "PASS" if passed else "FAIL"
    print(f"[{icon}] {vid}: {msg}")
    results.append((vid, passed, msg))


def get(url, **kw):
    return requests.get(url, timeout=120, **kw)


def post(url, **kw):
    return requests.post(url, timeout=180, **kw)


def delete(url, **kw):
    return requests.delete(url, timeout=60, **kw)


# ─────────── WAIT helper to clear the 3-sec forum-chat rate-limit ───────────
def cool():
    time.sleep(4)


# ════════════════════════════ W1-W14: NEW ROUTES ════════════════════════════

def w1():
    try:
        r = get(f"{API}/forums/{FORUM}/chat/history", params={"user_id": PETE, "limit": 5})
        if r.status_code != 200:
            return log("W1", False, f"status {r.status_code}: {r.text[:200]}")
        d = r.json()
        if d.get("success") is not True:
            return log("W1", False, f"success={d.get('success')}")
        if not isinstance(d.get("messages"), list):
            return log("W1", False, f"messages not list")
        log("W1", True, f"history returned {len(d['messages'])} messages")
    except Exception as e:
        log("W1", False, f"exception: {e}")


def w2():
    try:
        r = get(f"{API}/forums/{FORUM}/chat/history", params={"user_id": NON_MEMBER, "limit": 5})
        if r.status_code != 403:
            return log("W2", False, f"status {r.status_code}: {r.text[:200]}")
        detail = r.json().get("detail", "")
        if "not a member" not in detail.lower():
            return log("W2", False, f"unexpected detail: {detail}")
        log("W2", True, f"403 returned")
    except Exception as e:
        log("W2", False, f"exception: {e}")


def w3():
    try:
        r = post(f"{API}/forums/{FORUM}/chat",
                 json={"user_id": NON_MEMBER, "message": "hi", "mode": "forum"})
        if r.status_code != 403:
            return log("W3", False, f"status {r.status_code}: {r.text[:200]}")
        log("W3", True, "403 for non-member POST")
    except Exception as e:
        log("W3", False, f"exception: {e}")


_w4_message_id = None


def w4():
    global _w4_message_id
    try:
        cool()  # ensure rate limit window cleared
        r = post(f"{API}/forums/{FORUM}/chat", json={
            "user_id": PETE,
            "message": "What's the energy of this forum?",
            "mode": "forum",
        })
        if r.status_code != 200:
            return log("W4", False, f"status {r.status_code}: {r.text[:300]}")
        d = r.json()
        if not d.get("success"):
            return log("W4", False, "success != true")
        resp = d.get("response", "")
        if not isinstance(resp, str) or len(resp) <= 50:
            return log("W4", False, f"response too short: len={len(resp) if resp else 0}")
        ts = d.get("timestamp")
        if not ts or not isinstance(ts, str):
            return log("W4", False, "timestamp missing")
        mid = d.get("message_id")
        if not mid:
            return log("W4", False, "message_id missing")
        _w4_message_id = mid

        soft = ["may", "might", "could", "seems", "one possibility", "there's often", "might indicate"]
        certs = ["definitely", "always", "never", "must", "guaranteed"]
        resp_l = resp.lower()
        if not any(s in resp_l for s in soft):
            return log("W4", False, f"no reflective marker found in response")
        # Check for certainty markers as whole words (avoid false hits like "summit"
        # containing "must"). Simple split-on-non-alnum is good enough.
        import re
        tokens = set(re.findall(r"[a-z']+", resp_l))
        bad = [c for c in certs if c in tokens]
        if bad:
            return log("W4", False, f"certainty markers found: {bad}")
        log("W4", True, f"reply len={len(resp)}, mid={mid[:8]}")
    except Exception as e:
        log("W4", False, f"exception: {e}")


def w5():
    try:
        cool()
        r = post(f"{API}/forums/{FORUM}/chat", json={
            "user_id": PETE, "message": "about me", "mode": "member"
        })
        if r.status_code != 400:
            return log("W5", False, f"status {r.status_code}: {r.text[:200]}")
        detail = r.json().get("detail", "")
        if "target_member_id" not in detail:
            return log("W5", False, f"detail missing target_member_id mention: {detail}")
        log("W5", True, "400 with target_member_id mention")
    except Exception as e:
        log("W5", False, f"exception: {e}")


_w6_result = {"status": None}
_w7_result = {"status": None, "body": None}


def w6_and_w7():
    """W6 and W7 must fire close enough together that the rate-limit
    window has not expired.  The rate-limit timestamp is set at the
    start of the W6 request, and W6's LLM call typically takes >3s
    to return — so we MUST fire W7 in parallel (not sequentially)
    to observe the 429.  Per the spec: 'immediately after W6 ...
    within 1 second'."""
    import threading

    cool()  # clear w4's rate-limit window first

    def fire_w6():
        try:
            r = post(f"{API}/forums/{FORUM}/chat", json={
                "user_id": PETE,
                "message": "how am I showing up?",
                "mode": "self",
            })
            _w6_result["status"] = r.status_code
            _w6_result["body"] = r.text
        except Exception as e:
            _w6_result["status"] = f"exc:{e}"

    def fire_w7():
        try:
            r = post(f"{API}/forums/{FORUM}/chat", json={
                "user_id": PETE,
                "message": "again",
                "mode": "self",
            })
            _w7_result["status"] = r.status_code
            _w7_result["body"] = r.text
        except Exception as e:
            _w7_result["status"] = f"exc:{e}"

    t6 = threading.Thread(target=fire_w6)
    t6.start()
    time.sleep(0.5)  # within 1 second
    t7 = threading.Thread(target=fire_w7)
    t7.start()
    t6.join()
    t7.join()

    # W6 must be 200
    if _w6_result["status"] != 200:
        log("W6", False, f"status {_w6_result['status']}: {str(_w6_result.get('body', ''))[:200]}")
    else:
        log("W6", True, "self-mode 200")

    # W7 must be 429 with "wait a moment" in detail
    if _w7_result["status"] != 429:
        log("W7", False, f"status {_w7_result['status']}: {str(_w7_result.get('body', ''))[:200]}")
        return
    try:
        import json as _json
        detail = _json.loads(_w7_result["body"]).get("detail", "")
    except Exception:
        detail = _w7_result["body"] or ""
    if "wait a moment" not in detail.lower():
        return log("W7", False, f"detail unexpected: {detail}")
    log("W7", True, "429 rate-limit (parallel fire)")


def w8():
    try:
        r = get(f"{API}/forums/{FORUM}/exercise", params={"user_id": PETE})
        if r.status_code != 200:
            return log("W8", False, f"status {r.status_code}: {r.text[:200]}")
        d = r.json()
        if "exercise" not in d:
            return log("W8", False, "exercise key missing")
        ex = d.get("exercise")
        if ex is None:
            log("W8", True, "no active exercise (acceptable)")
            return
        for k in ("slug", "title", "prompts"):
            if k not in ex:
                return log("W8", False, f"exercise missing {k}")
        if not isinstance(d.get("domains"), list) or len(d["domains"]) != 7:
            return log("W8", False, f"domains not list of 7: {d.get('domains')}")
        if not isinstance(d.get("has_submitted"), bool):
            return log("W8", False, f"has_submitted not bool: {d.get('has_submitted')}")
        log("W8", True, "exercise + domains(7) + has_submitted")
    except Exception as e:
        log("W8", False, f"exception: {e}")


def w9():
    try:
        r = get(f"{API}/forums/{FORUM}/exercise", params={"user_id": NON_MEMBER})
        if r.status_code != 403:
            return log("W9", False, f"status {r.status_code}: {r.text[:200]}")
        log("W9", True, "403 returned")
    except Exception as e:
        log("W9", False, f"exception: {e}")


def w10():
    try:
        r = post(f"{API}/forums/{FORUM}/reflections", json={
            "user_id": NON_MEMBER,
            "selected_domain": "energy_vitality",
            "reflection_text": "x",
            "is_shared": False,
        })
        if r.status_code != 403:
            return log("W10", False, f"status {r.status_code}: {r.text[:200]}")
        log("W10", True, "403 returned")
    except Exception as e:
        log("W10", False, f"exception: {e}")


def w11():
    try:
        r = get(f"{API}/forums/{FORUM}/reflections/shared", params={"user_id": NON_MEMBER})
        if r.status_code != 403:
            return log("W11", False, f"status {r.status_code}: {r.text[:200]}")
        log("W11", True, "403 returned")
    except Exception as e:
        log("W11", False, f"exception: {e}")


def w12():
    try:
        r = get(f"{API}/forums/{FORUM}/updates", params={"user_id": PETE})
        if r.status_code != 200:
            return log("W12", False, f"status {r.status_code}: {r.text[:200]}")
        d = r.json()
        if not isinstance(d.get("updates"), list):
            return log("W12", False, "updates not list")
        log("W12", True, f"updates len={len(d['updates'])}")
    except Exception as e:
        log("W12", False, f"exception: {e}")


def w13():
    try:
        r = get(f"{API}/forums/{FORUM}/my-update", params={"user_id": PETE})
        if r.status_code != 200:
            return log("W13", False, f"status {r.status_code}: {r.text[:200]}")
        d = r.json()
        if not isinstance(d.get("found"), bool):
            return log("W13", False, "found not bool")
        log("W13", True, f"found={d['found']}")
    except Exception as e:
        log("W13", False, f"exception: {e}")


def w14():
    try:
        r = post(f"{API}/forums/update", json={
            "forum_id": FORUM,
            "user_id": NON_MEMBER,
            "one_word_checkin": {},
            "updates": {},
        })
        if r.status_code != 403:
            return log("W14", False, f"status {r.status_code}: {r.text[:200]}")
        log("W14", True, "403 returned")
    except Exception as e:
        log("W14", False, f"exception: {e}")


# ════════════════════════════ G1-G13: REGRESSION ════════════════════════════

def g1():
    try:
        r = post(f"{API}/mirror/chat", json={
            "user_id": PETE, "lens": "zi_wei",
            "message": "What does my chart say?",
        })
        if r.status_code != 200:
            return log("G1", False, f"status {r.status_code}: {r.text[:200]}")
        debug = r.json().get("debug", {})
        lc = debug.get("lens_chat", {})
        if lc.get("lens") != "zi_wei":
            return log("G1", False, f"lens_chat.lens={lc.get('lens')}")
        if lc.get("marker") != "multi-lens-chat-memory-v1":
            return log("G1", False, f"lens_chat.marker={lc.get('marker')}")
        log("G1", True, "zi_wei lens_chat shape OK")
    except Exception as e:
        log("G1", False, f"exception: {e}")


def g2():
    try:
        r = post(f"{API}/mirror/chat", json={
            "user_id": PETE, "lens": "astrology",
            "message": "how am I?",
        })
        if r.status_code != 200:
            return log("G2", False, f"status {r.status_code}: {r.text[:200]}")
        lc = r.json().get("debug", {}).get("lens_chat", {})
        if lc.get("lens") != "astrology":
            return log("G2", False, f"lens_chat.lens={lc.get('lens')}")
        log("G2", True, "astrology lens_chat shape OK")
    except Exception as e:
        log("G2", False, f"exception: {e}")


def g3():
    try:
        r = post(f"{API}/mirror/chat", json={
            "user_id": PETE, "lens": None, "message": "hi",
        })
        if r.status_code != 200:
            return log("G3", False, f"status {r.status_code}: {r.text[:200]}")
        debug = r.json().get("debug", {})
        ct = debug.get("contradictions", {})
        if ct.get("marker") != "contradiction-intelligence-v1":
            return log("G3", False, f"contradictions.marker={ct.get('marker')}")
        log("G3", True, "contradictions marker present")
    except Exception as e:
        log("G3", False, f"exception: {e}")


def g4():
    try:
        r = get(f"{API}/forums/{FORUM}/story-of-circle", params={"user_id": PETE})
        if r.status_code != 200:
            return log("G4", False, f"status {r.status_code}: {r.text[:200]}")
        d = r.json()
        marker = d.get("marker") or d.get("debug", {}).get("marker")
        if marker != "forum-topology-and-timing-v1":
            return log("G4", False, f"marker={marker}")
        log("G4", True, "story-of-circle marker OK")
    except Exception as e:
        log("G4", False, f"exception: {e}")


def g5():
    try:
        r = post(f"{API}/forums/{FORUM}/mirror-chat", json={
            "user_id": PETE,
            "forum_id": FORUM,
            "message": "what's softening?",
        })
        if r.status_code != 200:
            return log("G5", False, f"status {r.status_code}: {r.text[:200]}")
        debug = r.json().get("debug", {})
        if debug.get("marker") != "forum-conversational-field-v1":
            return log("G5", False, f"debug.marker={debug.get('marker')}")
        log("G5", True, "forum mirror-chat marker OK")
    except Exception as e:
        log("G5", False, f"exception: {e}")


def g6():
    try:
        r = get(f"{API}/forums/{FORUM}/mirror-chat/history", params={"user_id": PETE})
        if r.status_code != 200:
            return log("G6", False, f"status {r.status_code}: {r.text[:200]}")
        d = r.json()
        marker = d.get("marker") or d.get("debug", {}).get("marker")
        if marker != "forum-conversational-field-v1":
            return log("G6", False, f"marker={marker}")
        log("G6", True, "history marker OK")
    except Exception as e:
        log("G6", False, f"exception: {e}")


def g7():
    try:
        r = get(f"{API}/forums/{FORUM}/topology", params={"user_id": PETE})
        if r.status_code != 200:
            return log("G7", False, f"status {r.status_code}: {r.text[:200]}")
        d = r.json()
        marker = d.get("marker") or d.get("debug", {}).get("marker")
        if marker != "forum-topology-and-timing-v1":
            return log("G7", False, f"marker={marker}")
        log("G7", True, "topology marker OK")
    except Exception as e:
        log("G7", False, f"exception: {e}")


_g8_edge_id = None


def g8():
    global _g8_edge_id
    try:
        # First need to resolve Mel's user_id via members list
        r = get(f"{API}/forums/{FORUM}/members", params={"user_id": PETE})
        if r.status_code != 200:
            return log("G8", False, f"members lookup failed {r.status_code}")
        members = r.json().get("members", [])
        mel_id = None
        for m in members:
            if m.get("user_id") != PETE:
                mel_id = m.get("user_id")
                break
        if not mel_id:
            return log("G8", False, "could not resolve Mel id")

        r = post(f"{API}/forums/{FORUM}/topology/edge", json={
            "from_user_id": PETE,
            "to_user_id": mel_id,
            "role_type": "close_friend",
        })
        if r.status_code != 200:
            return log("G8", False, f"edge POST {r.status_code}: {r.text[:200]}")
        d = r.json()
        marker = d.get("marker") or d.get("debug", {}).get("marker")
        if marker != "topology-editor-v2":
            return log("G8", False, f"marker={marker}")
        edge = d.get("edge") or {}
        if edge.get("inferred") is not False:
            return log("G8", False, f"edge.inferred={edge.get('inferred')}")
        edge_id = edge.get("id")
        if not edge_id:
            return log("G8", False, "edge.id missing")
        _g8_edge_id = edge_id

        # Now delete it
        r2 = delete(f"{API}/forums/{FORUM}/topology/edge/{edge_id}/by/{PETE}")
        if r2.status_code != 200:
            return log("G8", False, f"edge DELETE {r2.status_code}: {r2.text[:200]}")
        log("G8", True, f"edge created+deleted (id={edge_id[:8]})")
    except Exception as e:
        log("G8", False, f"exception: {e}")


def g9():
    try:
        r = get(f"{API}/forums/{FORUM}/members", params={"user_id": PETE})
        if r.status_code != 200:
            return log("G9", False, f"status {r.status_code}: {r.text[:200]}")
        members = r.json().get("members", [])
        if len(members) != 2:
            return log("G9", False, f"member count={len(members)}")
        log("G9", True, "2 members")
    except Exception as e:
        log("G9", False, f"exception: {e}")


def g10():
    try:
        r = get(f"{API}/forums/domains/list")
        if r.status_code != 200:
            return log("G10", False, f"status {r.status_code}: {r.text[:200]}")
        d = r.json()
        domains = d.get("domains") or d
        if not isinstance(domains, list) or len(domains) != 7:
            return log("G10", False, f"domains len={len(domains) if isinstance(domains, list) else 'na'}")
        log("G10", True, "7 domains")
    except Exception as e:
        log("G10", False, f"exception: {e}")


def g11():
    try:
        r = get(f"{API}/admin/forum/export/PeteAndMel", params={"admin_key": "wrongkey"})
        if r.status_code != 403:
            return log("G11", False, f"status {r.status_code}: {r.text[:200]}")
        log("G11", True, "403 returned")
    except Exception as e:
        log("G11", False, f"exception: {e}")


_g12_id = None


def g12():
    global _g12_id
    try:
        r = post(f"{API}/micro-reflection", json={
            "user_id": PETE,
            "label": "lands",
            "source": "other",
        })
        if r.status_code != 200:
            return log("G12", False, f"status {r.status_code}: {r.text[:200]}")
        d = r.json()
        marker = d.get("marker") or d.get("debug", {}).get("marker")
        if marker != "micro-reflection-v2":
            return log("G12", False, f"marker={marker}")
        _g12_id = d.get("id") or d.get("reflection_id") or d.get("_id")
        log("G12", True, f"micro-reflection v2 (id={_g12_id})")
    except Exception as e:
        log("G12", False, f"exception: {e}")


_g13_id = None


def g13():
    global _g13_id
    try:
        r = post(f"{API}/micro-reflection/home-texture", json={
            "user_id": PETE,
            "texture": "open",
        })
        if r.status_code != 200:
            return log("G13", False, f"status {r.status_code}: {r.text[:200]}")
        d = r.json()
        marker = d.get("marker") or d.get("debug", {}).get("marker")
        if marker != "micro-reflection-v3-home-texture":
            return log("G13", False, f"marker={marker}")
        _g13_id = d.get("id") or d.get("reflection_id") or d.get("_id")
        log("G13", True, f"home-texture v3 (id={_g13_id})")
    except Exception as e:
        log("G13", False, f"exception: {e}")


# ═══════════════════════════════ CLEANUP ═══════════════════════════════

def cleanup():
    try:
        client = MongoClient(MONGO_URL)
        db = client[DB_NAME]
        # home-texture deletes
        ht = db.micro_reflections.delete_many({"user_id": PETE, "source": "home_texture"})
        # lands/other reflection from G12
        lr = db.micro_reflections.delete_many({"user_id": PETE, "label": "lands", "source": "other"})
        # Verify no edges from G8 remain
        edge_remaining = None
        if _g8_edge_id:
            try:
                edge_remaining = db.forum_topology_edges.find_one({"_id": ObjectId(_g8_edge_id)})
            except Exception:
                edge_remaining = db.forum_topology_edges.find_one({"id": _g8_edge_id})
        print(f"[CLEANUP] home_texture deleted={ht.deleted_count}, "
              f"lands/other deleted={lr.deleted_count}, "
              f"g8 edge remaining={edge_remaining}")
    except Exception as e:
        print(f"[CLEANUP] exception: {e}")


# ═══════════════════════════════ MAIN ═══════════════════════════════

def main():
    print("=" * 70)
    print("Server router refactor v4 — regression suite")
    print(f"API: {API}")
    print(f"Pete: {PETE}, Forum: {FORUM}, Non-member: {NON_MEMBER}")
    print("=" * 70)

    # NEW (W*)
    w1()
    w2()
    w3()
    w4()
    w5()
    # W6 and W7 must be tested together (parallel fire) to observe the
    # 3-sec rate-limit window before W6's LLM call (typically >3s) returns.
    w6_and_w7()
    w8()
    w9()
    w10()
    w11()
    w12()
    w13()
    w14()

    # Regression (G*)
    g1()
    g2()
    g3()
    g4()
    g5()
    g6()
    g7()
    g8()
    g9()
    g10()
    g11()
    g12()
    g13()

    cleanup()

    print("=" * 70)
    passed = sum(1 for _, p, _ in results if p)
    total = len(results)
    print(f"RESULT: {passed}/{total} passed")
    if passed != total:
        print("\nFAILED:")
        for vid, p, msg in results:
            if not p:
                print(f"  {vid}: {msg}")
    print("=" * 70)


if __name__ == "__main__":
    main()
