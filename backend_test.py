"""
Backend tests for:
  A) Micro-Reflection v3 — Home daily texture check-in
     (marker: micro-reflection-v3-home-texture)
  B) Topology Editor v2 — user-declared edges
     (marker: topology-editor-v2)
"""

import os
import sys
import time
import json
import asyncio
from pathlib import Path

import requests
from dotenv import load_dotenv

# Load frontend .env for the public URL.
load_dotenv(dotenv_path="/app/frontend/.env")
BASE = os.environ.get("EXPO_PUBLIC_BACKEND_URL") or os.environ.get("REACT_APP_BACKEND_URL")
if not BASE:
    print("ERROR: EXPO_PUBLIC_BACKEND_URL is not set in /app/frontend/.env")
    sys.exit(2)
API = f"{BASE.rstrip('/')}/api"
print(f"[CONFIG] API base: {API}")

PETE = "697f0c6abf35c0528ff06954"
FORUM_ID = "69dd05eaa333335fcbf3ad33"

results = []  # list of (test_id, passed, info)

def record(tid, passed, info=""):
    results.append((tid, passed, info))
    tag = "PASS" if passed else "FAIL"
    print(f"  [{tag}] {tid} :: {info}")


def get_json(resp):
    try:
        return resp.json()
    except Exception:
        return None


# =========================================================
# FEATURE A — Micro-Reflection v3 — Home daily texture
# =========================================================
print("\n=== FEATURE A — Micro-Reflection v3 (home texture) ===")

# Cleanup any prior home_texture data for Pete via mongo before testing? We
# will just track count via /recent.
def recent_count():
    r = requests.get(f"{API}/micro-reflection/{PETE}/recent", timeout=20)
    try:
        data = r.json()
        return data.get("summary", {}).get("total", 0), data
    except Exception:
        return -1, None

before_count, _ = recent_count()
print(f"[INFO] pre-test recent total for Pete: {before_count}")

# --- M1: POST texture=open ---
try:
    r = requests.post(
        f"{API}/micro-reflection/home-texture",
        json={"user_id": PETE, "texture": "open"},
        timeout=20,
    )
    body = get_json(r) or {}
    refl = body.get("reflection") or {}
    cond = (
        r.status_code == 200
        and body.get("marker") == "micro-reflection-v3-home-texture"
        and refl.get("label") == "true_lately"
        and refl.get("source") == "home_texture"
        and refl.get("texture") == "open"
    )
    record(
        "M1",
        cond,
        f"status={r.status_code} marker={body.get('marker')} "
        f"label={refl.get('label')} source={refl.get('source')} texture={refl.get('texture')}",
    )
except Exception as e:
    record("M1", False, f"exception: {e}")

# --- M2: POST texture=open, domain=work ---
try:
    r = requests.post(
        f"{API}/micro-reflection/home-texture",
        json={"user_id": PETE, "texture": "open", "domain": "work"},
        timeout=20,
    )
    body = get_json(r) or {}
    refl = body.get("reflection") or {}
    cond = (
        r.status_code == 200
        and refl.get("context_life_domain") == "work"
    )
    record("M2", cond, f"status={r.status_code} context_life_domain={refl.get('context_life_domain')}")
except Exception as e:
    record("M2", False, f"exception: {e}")

# --- M3: invalid texture → 400 ---
try:
    r = requests.post(
        f"{API}/micro-reflection/home-texture",
        json={"user_id": PETE, "texture": "banana"},
        timeout=20,
    )
    record("M3", r.status_code == 400, f"status={r.status_code} body={r.text[:120]}")
except Exception as e:
    record("M3", False, f"exception: {e}")

# --- M4: invalid domain → 400 ---
try:
    r = requests.post(
        f"{API}/micro-reflection/home-texture",
        json={"user_id": PETE, "texture": "open", "domain": "weird"},
        timeout=20,
    )
    record("M4", r.status_code == 400, f"status={r.status_code} body={r.text[:120]}")
except Exception as e:
    record("M4", False, f"exception: {e}")

# --- M5: domain=not_sure stored as null ---
try:
    r = requests.post(
        f"{API}/micro-reflection/home-texture",
        json={"user_id": PETE, "texture": "open", "domain": "not_sure"},
        timeout=20,
    )
    body = get_json(r) or {}
    refl = body.get("reflection") or {}
    cond = r.status_code == 200 and refl.get("context_life_domain") in (None, "null")
    record("M5", cond, f"status={r.status_code} context_life_domain={refl.get('context_life_domain')!r}")
except Exception as e:
    record("M5", False, f"exception: {e}")

# --- M6: today endpoint shows last record ---
try:
    r = requests.get(f"{API}/micro-reflection/{PETE}/home-texture/today", timeout=20)
    body = get_json(r) or {}
    last = body.get("last") or {}
    # Most recent post above had texture=open and domain=not_sure -> stored None
    cond = (
        r.status_code == 200
        and body.get("logged_today") is True
        and last.get("texture") == "open"
    )
    record(
        "M6",
        cond,
        f"status={r.status_code} logged_today={body.get('logged_today')} last_texture={last.get('texture')}",
    )
except Exception as e:
    record("M6", False, f"exception: {e}")

# --- M7: /recent includes home_texture, total > 0 ---
try:
    r = requests.get(f"{API}/micro-reflection/{PETE}/recent", timeout=20)
    body = get_json(r) or {}
    refls = body.get("reflections") or []
    has_home_texture = any(d.get("source") == "home_texture" for d in refls)
    summary_total = (body.get("summary") or {}).get("total", 0)
    cond = r.status_code == 200 and has_home_texture and summary_total > 0
    record(
        "M7",
        cond,
        f"status={r.status_code} has_home_texture={has_home_texture} summary.total={summary_total} reflections_len={len(refls)}",
    )
except Exception as e:
    record("M7", False, f"exception: {e}")

# --- M8: two POSTs with different textures yield 2 NEW records ---
try:
    # baseline count
    r0 = requests.get(f"{API}/micro-reflection/{PETE}/recent", timeout=20)
    base_total = (r0.json().get("summary") or {}).get("total", 0)

    r1 = requests.post(
        f"{API}/micro-reflection/home-texture",
        json={"user_id": PETE, "texture": "tense"},
        timeout=20,
    )
    r2 = requests.post(
        f"{API}/micro-reflection/home-texture",
        json={"user_id": PETE, "texture": "clear"},
        timeout=20,
    )
    time.sleep(0.5)
    r3 = requests.get(f"{API}/micro-reflection/{PETE}/recent", timeout=20)
    new_total = (r3.json().get("summary") or {}).get("total", 0)
    cond = r1.status_code == 200 and r2.status_code == 200 and (new_total - base_total) >= 2
    record(
        "M8",
        cond,
        f"r1={r1.status_code} r2={r2.status_code} delta={new_total - base_total} (base={base_total} new={new_total})",
    )
except Exception as e:
    record("M8", False, f"exception: {e}")


# =========================================================
# FEATURE B — Topology Editor v2
# =========================================================
print("\n=== FEATURE B — Topology Editor v2 ===")

# 1. Discover Mel
mel = None
try:
    r = requests.get(f"{API}/forums/{FORUM_ID}/members", params={"user_id": PETE}, timeout=20)
    body = get_json(r) or {}
    members = body.get("members") or []
    print(f"[INFO] members count={len(members)} ids={[m.get('user_id') for m in members]}")
    for m in members:
        if str(m.get("user_id")) != PETE:
            mel = str(m.get("user_id"))
            break
    if not mel:
        print(f"ERROR: could not resolve Mel; members={members}")
except Exception as e:
    print(f"ERROR: members fetch failed: {e}")

if not mel:
    record("T-PRE", False, "Mel user_id not found — cannot run topology tests")
else:
    print(f"[INFO] Mel user_id resolved as: {mel}")

# Cleanup any prior explicit edges Pete declared to Mel (so tests start clean)
def cleanup_petes_edges():
    try:
        r = requests.get(f"{API}/forums/{FORUM_ID}/topology/by/{PETE}", timeout=20)
        body = get_json(r) or {}
        for e in body.get("outbound") or []:
            if not e.get("inferred", True) and str(e.get("from_user_id")) == PETE:
                eid = e.get("id") or e.get("edge_id")
                if eid:
                    requests.delete(
                        f"{API}/forums/{FORUM_ID}/topology/edge/{eid}/by/{PETE}",
                        timeout=20,
                    )
    except Exception as ex:
        print(f"[WARN] cleanup failed: {ex}")

if mel:
    cleanup_petes_edges()

t1_edge_id = None
# --- T1: POST close_friend ---
if mel:
    try:
        r = requests.post(
            f"{API}/forums/{FORUM_ID}/topology/edge",
            json={
                "from_user_id": PETE,
                "to_user_id": mel,
                "role_type": "close_friend",
            },
            timeout=20,
        )
        body = get_json(r) or {}
        edge = body.get("edge") or {}
        t1_edge_id = edge.get("id")
        cond = (
            r.status_code == 200
            and body.get("marker") == "topology-editor-v2"
            and edge.get("inferred") is False
            and edge.get("confidence") == "high"
        )
        record(
            "T1",
            cond,
            f"status={r.status_code} marker={body.get('marker')} inferred={edge.get('inferred')} conf={edge.get('confidence')} edge_id={t1_edge_id}",
        )
    except Exception as e:
        record("T1", False, f"exception: {e}")

# --- T2: POST mentor + facets; both edges coexist ---
t2_edge_id = None
if mel:
    try:
        r = requests.post(
            f"{API}/forums/{FORUM_ID}/topology/edge",
            json={
                "from_user_id": PETE,
                "to_user_id": mel,
                "role_type": "mentor",
                "emotional_weight": "moderate",
                "intimacy_level": "medium",
            },
            timeout=20,
        )
        body = get_json(r) or {}
        edge = body.get("edge") or {}
        t2_edge_id = edge.get("id")
        # Now GET topology/by/Pete and confirm BOTH edges present
        rg = requests.get(f"{API}/forums/{FORUM_ID}/topology/by/{PETE}", timeout=20)
        gb = get_json(rg) or {}
        outbound = gb.get("outbound") or []
        role_set = {e.get("role_type") for e in outbound if str(e.get("to_user_id")) == mel and e.get("inferred") is False}
        cond = (
            r.status_code == 200
            and "close_friend" in role_set
            and "mentor" in role_set
        )
        record(
            "T2",
            cond,
            f"status={r.status_code} outbound_roles_to_mel={role_set} edge_id={t2_edge_id}",
        )
    except Exception as e:
        record("T2", False, f"exception: {e}")

# --- T3: non-member → 403 ---
if mel:
    try:
        r = requests.post(
            f"{API}/forums/{FORUM_ID}/topology/edge",
            json={
                "from_user_id": "non-member-id-aaaaaaaaaaaa",
                "to_user_id": mel,
                "role_type": "close_friend",
            },
            timeout=20,
        )
        record("T3", r.status_code == 403, f"status={r.status_code} body={r.text[:120]}")
    except Exception as e:
        record("T3", False, f"exception: {e}")

# --- T4: self → 400 ---
try:
    r = requests.post(
        f"{API}/forums/{FORUM_ID}/topology/edge",
        json={"from_user_id": PETE, "to_user_id": PETE, "role_type": "close_friend"},
        timeout=20,
    )
    record("T4", r.status_code == 400, f"status={r.status_code} body={r.text[:120]}")
except Exception as e:
    record("T4", False, f"exception: {e}")

# --- T5: unknown role → 400 ---
if mel:
    try:
        r = requests.post(
            f"{API}/forums/{FORUM_ID}/topology/edge",
            json={"from_user_id": PETE, "to_user_id": mel, "role_type": "cult-leader"},
            timeout=20,
        )
        record("T5", r.status_code == 400, f"status={r.status_code} body={r.text[:120]}")
    except Exception as e:
        record("T5", False, f"exception: {e}")

# --- T6: DELETE by Mel (non-owner) → 403 ---
if mel and t1_edge_id:
    try:
        r = requests.delete(
            f"{API}/forums/{FORUM_ID}/topology/edge/{t1_edge_id}/by/{mel}",
            timeout=20,
        )
        record("T6", r.status_code == 403, f"status={r.status_code} body={r.text[:120]}")
    except Exception as e:
        record("T6", False, f"exception: {e}")

# --- T7: POST /topology/infer; explicit edges remain inferred=False ---
if mel:
    try:
        r = requests.post(f"{API}/forums/{FORUM_ID}/topology/infer", timeout=30)
        rg = requests.get(f"{API}/forums/{FORUM_ID}/topology/by/{PETE}", timeout=20)
        gb = get_json(rg) or {}
        outbound = gb.get("outbound") or []
        explicit_intact = True
        for e in outbound:
            if str(e.get("to_user_id")) == mel and e.get("role_type") in ("close_friend", "mentor"):
                if e.get("inferred") is True:
                    explicit_intact = False
        cond = r.status_code == 200 and explicit_intact
        record("T7", cond, f"infer_status={r.status_code} explicit_still_explicit={explicit_intact}")
    except Exception as e:
        record("T7", False, f"exception: {e}")

# --- T8: outbound contains both edges; all_roles non-empty ---
if mel:
    try:
        r = requests.get(f"{API}/forums/{FORUM_ID}/topology/by/{PETE}", timeout=20)
        body = get_json(r) or {}
        outbound = body.get("outbound") or []
        all_roles = body.get("all_roles") or []
        roles_to_mel = {
            e.get("role_type")
            for e in outbound
            if str(e.get("to_user_id")) == mel and e.get("inferred") is False
        }
        cond = (
            r.status_code == 200
            and "close_friend" in roles_to_mel
            and "mentor" in roles_to_mel
            and len(all_roles) > 0
        )
        record(
            "T8",
            cond,
            f"status={r.status_code} roles_to_mel={roles_to_mel} all_roles_len={len(all_roles)}",
        )
    except Exception as e:
        record("T8", False, f"exception: {e}")

# --- T9: /topology/roles includes required set ---
try:
    r = requests.get(f"{API}/forums/{FORUM_ID}/topology/roles", timeout=20)
    body = get_json(r) or {}
    roles = set(body.get("roles") or [])
    required = {"mentor", "cofounder", "spouse", "close_friend", "forum_mate", "other"}
    missing = required - roles
    cond = r.status_code == 200 and not missing
    record("T9", cond, f"status={r.status_code} missing={missing} roles_count={len(roles)}")
except Exception as e:
    record("T9", False, f"exception: {e}")

# --- T10: /story-of-circle marker ---
try:
    r = requests.get(f"{API}/forums/{FORUM_ID}/story-of-circle", timeout=30)
    body = get_json(r) or {}
    cond = r.status_code == 200 and body.get("marker") == "forum-topology-and-timing-v1"
    record("T10", cond, f"status={r.status_code} marker={body.get('marker')}")
except Exception as e:
    record("T10", False, f"exception: {e}")

# --- T11: mirror-chat regression ---
try:
    r = requests.post(
        f"{API}/forums/{FORUM_ID}/mirror-chat",
        json={
            "user_id": PETE,
            "forum_id": FORUM_ID,
            "message": "How does the room feel today?",
        },
        timeout=60,
    )
    body = get_json(r) or {}
    dbg = body.get("debug") or {}
    cond = r.status_code == 200 and dbg.get("marker") == "forum-conversational-field-v1"
    record("T11", cond, f"status={r.status_code} debug.marker={dbg.get('marker')}")
except Exception as e:
    record("T11", False, f"exception: {e}")


# =========================================================
# CLEANUP
# =========================================================
print("\n=== CLEANUP ===")
# Delete the explicit edges
if mel:
    for eid in [t1_edge_id, t2_edge_id]:
        if not eid:
            continue
        try:
            r = requests.delete(
                f"{API}/forums/{FORUM_ID}/topology/edge/{eid}/by/{PETE}",
                timeout=20,
            )
            print(f"  deleted edge {eid}: {r.status_code}")
        except Exception as e:
            print(f"  delete error edge {eid}: {e}")

# Clean up home_texture micro_reflections for Pete via direct Mongo
try:
    sys.path.insert(0, "/app/backend")
    from dotenv import load_dotenv as _ld
    _ld(dotenv_path="/app/backend/.env")
    from motor.motor_asyncio import AsyncIOMotorClient
    MONGO_URL = os.environ.get("MONGO_URL")
    DB_NAME = os.environ.get("DB_NAME", "test_database")

    async def _cleanup_mongo():
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        r = await db.micro_reflections.delete_many({"user_id": PETE, "source": "home_texture"})
        print(f"  micro_reflections deleted: {r.deleted_count}")
        client.close()

    asyncio.run(_cleanup_mongo())
except Exception as e:
    print(f"  mongo cleanup error: {e}")


# =========================================================
# REPORT
# =========================================================
print("\n=== RESULTS ===")
passed = sum(1 for _, ok, _ in results if ok)
total = len(results)
for tid, ok, info in results:
    print(f"  {'PASS' if ok else 'FAIL'}  {tid}  {info}")
print(f"\n{passed}/{total} passed")
sys.exit(0 if passed == total else 1)
