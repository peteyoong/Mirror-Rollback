"""
Backend test for Forum Topology + Timing v1 (forum-topology-and-timing-v1).
Tests E1-E7 per review request.
"""
import os
import sys
import json
import time
import asyncio
from typing import Any, Dict, List, Optional

import requests
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId


BASE_URL = "https://narrative-flex-v1.preview.emergentagent.com/api"
PETE_USER_ID = "697f0c6abf35c0528ff06954"
MARKER = "forum-topology-and-timing-v1"

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")

# Banned framework jargon (case-insensitive)
JARGON_TOKENS = [
    "saturn", "pluto", "mercury", "mars", "jupiter", "uranus", "neptune",
    "sun in", "moon in", "gate", "channel",
    "life path", "day master",
    "type 4", "type 7",
    "sacral", "manifestor", "projector", "generator",
    "natal", "transit", "ayanamsa", "enneagram",
]

# Member-level diagnosis red-flags
DIAGNOSIS_PHRASES = [
    "is avoidant", "is toxic", "is the source", "is the difficult",
    "causes tension", "this member", "this person is",
]


results = []


def record(name: str, ok: bool, msg: str = ""):
    status = "PASS" if ok else "FAIL"
    print(f"[{status}]  {name}: {msg}")
    results.append({"name": name, "ok": ok, "msg": msg})


def http(method: str, path: str, **kw):
    url = f"{BASE_URL}{path}"
    r = requests.request(method, url, timeout=60, **kw)
    return r


# ---------- E1 ----------
def test_e1_empty_forum():
    print("\n=== E1: Empty forum / placeholder ===")
    forum_id = "empty-nonexistent"
    r = http("GET", f"/forums/{forum_id}/story-of-circle")
    record("E1.status_200", r.status_code == 200, f"got {r.status_code}")
    if r.status_code != 200:
        return
    j = r.json()
    record("E1.marker", j.get("marker") == MARKER, f"marker={j.get('marker')}")
    story = j.get("story", {})
    record("E1.ready_false", story.get("ready") is False, f"ready={story.get('ready')}")
    placeholder = (story.get("placeholder") or "").lower()
    record(
        "E1.placeholder_text",
        "field is still becoming visible" in placeholder,
        f"placeholder={placeholder[:120]}",
    )
    record(
        "E1.chips_empty",
        story.get("field_state_chips") == [],
        f"chips={story.get('field_state_chips')}",
    )


# ---------- E2 ----------
def test_e2_admin_seed_roundtrip(forum_id: str = "test-e2-forum"):
    print(f"\n=== E2: Admin seeding round-trip (forum={forum_id}) ===")
    body = {"from_user_id": "user-a", "to_user_id": "user-b", "role_type": "mentor"}
    r = http("POST", f"/admin/forums/{forum_id}/seed-topology-edge", json=body)
    record("E2.seed_200", r.status_code == 200, f"got {r.status_code}: {r.text[:200]}")
    if r.status_code != 200:
        return None
    edge = r.json().get("edge", {})
    record("E2.role_type_mentor", edge.get("role_type") == "mentor", f"got {edge.get('role_type')}")
    record(
        "E2.power_gradient_soft",
        edge.get("power_gradient") == "soft_hierarchy",
        f"got {edge.get('power_gradient')}",
    )
    record(
        "E2.emotional_weight_moderate",
        edge.get("emotional_weight") == "moderate",
        f"got {edge.get('emotional_weight')}",
    )
    record("E2.inferred_false", edge.get("inferred") is False, f"got {edge.get('inferred')}")
    edge_id = edge.get("id")
    import re as _re
    uuid_pat = _re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", _re.I)
    record("E2.edge_id_uuid", bool(edge_id) and bool(uuid_pat.match(edge_id)), f"id={edge_id}")

    # GET topology
    r2 = http("GET", f"/forums/{forum_id}/topology")
    record("E2.get_topology_200", r2.status_code == 200, f"got {r2.status_code}")
    j2 = r2.json() if r2.status_code == 200 else {}
    edges = j2.get("edges", [])
    record(
        "E2.edge_present_in_list",
        any(e.get("id") == edge_id for e in edges),
        f"edges={len(edges)}",
    )

    # DELETE edge
    r3 = http("DELETE", f"/forums/{forum_id}/topology/edge/{edge_id}")
    record("E2.delete_200", r3.status_code == 200, f"got {r3.status_code}")
    j3 = r3.json() if r3.status_code == 200 else {}
    record("E2.deleted_eq_1", j3.get("deleted") == 1, f"deleted={j3.get('deleted')}")

    # GET topology again — empty
    r4 = http("GET", f"/forums/{forum_id}/topology")
    j4 = r4.json() if r4.status_code == 200 else {}
    record("E2.edges_empty_after_delete", j4.get("edges") == [], f"edges={j4.get('edges')}")
    return edge_id


# ---------- Helpers for E3/E4 ----------
async def find_or_create_forum_with_two_members() -> Dict[str, Any]:
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    try:
        forums = db.forums.find({})
        async for f in forums:
            fid = str(f.get("_id"))
            members = []
            async for m in db.forum_members.find({"forum_id": fid}):
                members.append(str(m.get("user_id")))
            if len(members) >= 2:
                return {
                    "forum_id": fid,
                    "member1_id": members[0],
                    "member2_id": members[1],
                    "created": False,
                }
        # Create one
        body = {
            "name": "TopologyTest Circle",
            "description": "Test forum for topology v1",
            "user_id": PETE_USER_ID,
        }
        r = http("POST", "/forums", json=body)
        if r.status_code != 200:
            raise RuntimeError(f"create forum failed: {r.status_code} {r.text}")
        forum_id = r.json()["id"]
        from datetime import datetime, timezone
        synth_uid = "topology-test-user-2"
        await db.forum_members.insert_one({
            "forum_id": forum_id,
            "user_id": synth_uid,
            "role": "member",
            "status": "active",
            "joined_at": datetime.now(timezone.utc),
        })
        return {
            "forum_id": forum_id,
            "member1_id": PETE_USER_ID,
            "member2_id": synth_uid,
            "created": True,
        }
    finally:
        client.close()


async def cleanup_test_forum(forum_id: str, edge_forum_ids: List[str], created_forum_id: Optional[str]):
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    try:
        for fid in edge_forum_ids:
            res = await db.forum_relationship_edges.delete_many({"forum_id": fid})
            print(f"[cleanup] deleted {res.deleted_count} edges for forum {fid}")
        if created_forum_id:
            res2 = await db.forum_members.delete_many({"forum_id": created_forum_id})
            print(f"[cleanup] deleted {res2.deleted_count} member rows for forum {created_forum_id}")
            try:
                res3 = await db.forums.delete_one({"_id": ObjectId(created_forum_id)})
                print(f"[cleanup] deleted forum: {res3.deleted_count}")
            except Exception as e:
                print(f"[cleanup] forum delete error: {e}")
            await db.forum_exercises.delete_many({"forum_id": created_forum_id})
    finally:
        client.close()


# ---------- E3 ----------
def test_e3_confidence_escalation(forum_id: str, m1: str, m2: str) -> str:
    print(f"\n=== E3: Topology confidence escalation (forum={forum_id}) ===")
    roles = ["mentor", "mentee", "cofounder"]
    for role in roles:
        body = {"from_user_id": m1, "to_user_id": m2, "role_type": role}
        r = http("POST", f"/admin/forums/{forum_id}/seed-topology-edge", json=body)
        record(f"E3.seed_{role}_200", r.status_code == 200, f"got {r.status_code}")
    r = http("GET", f"/forums/{forum_id}/topology")
    record("E3.get_topology_200", r.status_code == 200, f"got {r.status_code}")
    state = ""
    if r.status_code == 200:
        j = r.json()
        state = j.get("confidence", {}).get("state", "")
        record(
            "E3.confidence_emerging_or_stable",
            state in ("emerging", "stable"),
            f"state={state}, full_confidence={j.get('confidence')}",
        )
    return state


def _scan_jargon(text: str, source: str) -> List[str]:
    hits = []
    low = (text or "").lower()
    for tok in JARGON_TOKENS:
        if tok in low:
            hits.append(f"{source}:'{tok}'")
    return hits


def _scan_diagnosis(text: str, source: str, member_names: List[str]) -> List[str]:
    import re
    hits = []
    low = (text or "").lower()
    for phrase in DIAGNOSIS_PHRASES:
        if phrase in low:
            hits.append(f"{source}:'{phrase}'")
    for name in member_names:
        if not name:
            continue
        n = name.strip()
        if len(n) < 3:
            continue
        if re.search(r"\b" + re.escape(n.lower()) + r"\b", low):
            hits.append(f"{source}:name='{n}'")
    return hits


async def _get_member_names(member_ids: List[str]) -> List[str]:
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    out = []
    try:
        for uid in member_ids:
            user = None
            try:
                user = await db.users.find_one({"_id": ObjectId(uid)})
            except Exception:
                pass
            if not user:
                user = await db.users.find_one({"id": uid})
            if user:
                nm = user.get("name") or user.get("display_name")
                if nm:
                    out.append(nm)
    finally:
        client.close()
    return out


# ---------- E4 + E5 + E6 + E7 ----------
def test_e4_e5_e6_e7(forum_id: str, member_ids: List[str], member_names: List[str]):
    print(f"\n=== E4-E7: Story populated + jargon + diagnosis + debug schema ===")
    r = http("GET", f"/forums/{forum_id}/story-of-circle", params={"debug": "true"})
    record("E4.status_200", r.status_code == 200, f"got {r.status_code}")
    if r.status_code != 200:
        return
    j = r.json()
    record("E4.marker_top", j.get("marker") == MARKER, f"marker={j.get('marker')}")
    story = j.get("story", {})
    record("E4.story_ready_true", story.get("ready") is True, f"ready={story.get('ready')}")
    tf = story.get("the_field") or ""
    mt = story.get("moves_toward") or ""
    record("E4.the_field_nonempty", bool(tf and isinstance(tf, str)), f"len={len(tf)}")
    record("E4.moves_toward_nonempty", bool(mt and isinstance(mt, str)), f"len={len(mt)}")
    chips = story.get("field_state_chips")
    record(
        "E4.chips_array_0_to_2",
        isinstance(chips, list) and 0 <= len(chips) <= 2,
        f"chips={chips}",
    )
    debug = j.get("debug", {}).get("forum_field", {})
    record("E4.debug_marker", debug.get("marker") == MARKER, f"marker={debug.get('marker')}")
    record(
        "E4.debug_topology_confidence",
        debug.get("topology_confidence") in ("emerging", "stable"),
        f"conf={debug.get('topology_confidence')}",
    )

    sections = {
        "the_field": story.get("the_field") or "",
        "moves_toward": story.get("moves_toward") or "",
        "softening": story.get("softening") or "",
        "unsaid": story.get("unsaid") or "",
    }
    print("\n[story sections]")
    for k, v in sections.items():
        print(f"  {k}: {v}")

    # E5
    jargon_hits = []
    for k, v in sections.items():
        jargon_hits.extend(_scan_jargon(v, k))
    record("E5.no_jargon_leak", not jargon_hits, f"hits={jargon_hits}")

    # E6
    diag_hits = []
    for k, v in sections.items():
        diag_hits.extend(_scan_diagnosis(v, k, member_names))
    record("E6.no_member_diagnosis", not diag_hits, f"hits={diag_hits}; names={member_names}")

    # E7
    required_keys = [
        "marker", "topology_confidence", "topology_summary", "edge_summary",
        "field_stability_score", "dominant_field_state", "secondary_field_state",
        "convergence_signals", "softening_signals", "unresolved_tensions",
        "topology_roles_present", "timing_pressure_summary", "power_gradient_count",
        "member_count",
    ]
    missing = [k for k in required_keys if k not in debug]
    record("E7.all_required_keys", not missing, f"missing={missing}")

    fss = debug.get("field_stability_score", {})
    record(
        "E7.field_stability_score_dict",
        isinstance(fss, dict) and "score" in fss
        and "topology_density" in fss and "recurrence_score" in fss
        and "reflection_score" in fss,
        f"fss={fss}",
    )
    score = fss.get("score") if isinstance(fss, dict) else None
    record(
        "E7.score_0_to_1_float",
        isinstance(score, (int, float)) and 0 <= score <= 1,
        f"score={score}",
    )
    pgc = debug.get("power_gradient_count", {})
    record(
        "E7.power_gradient_count_keys",
        isinstance(pgc, dict)
        and {"equal", "soft_hierarchy", "hard_hierarchy"}.issubset(set(pgc.keys())),
        f"pgc={pgc}",
    )


def main():
    e2_forum_id = "test-e2-forum"
    test_e1_empty_forum()
    test_e2_admin_seed_roundtrip(e2_forum_id)

    info = asyncio.run(find_or_create_forum_with_two_members())
    print(f"\n[setup] Using forum_id={info['forum_id']} m1={info['member1_id']} m2={info['member2_id']} created={info['created']}")
    forum_id = info["forum_id"]
    m1 = info["member1_id"]
    m2 = info["member2_id"]

    test_e3_confidence_escalation(forum_id, m1, m2)
    member_names = asyncio.run(_get_member_names([m1, m2]))
    test_e4_e5_e6_e7(forum_id, [m1, m2], member_names)

    # Cleanup
    print("\n=== Cleanup ===")
    asyncio.run(cleanup_test_forum(
        forum_id=forum_id,
        edge_forum_ids=[e2_forum_id, forum_id],
        created_forum_id=forum_id if info["created"] else None,
    ))

    total = len(results)
    passed = sum(1 for r in results if r["ok"])
    print(f"\n========= SUMMARY: {passed}/{total} checks passed =========")
    for r in results:
        if not r["ok"]:
            print(f" FAIL: {r['name']} -> {r['msg']}")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
