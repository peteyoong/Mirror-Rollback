"""
Backend tests for "Ask About Person — Relational Awareness Chat Wiring"
Build marker: ask-about-person-v1

POST /api/mirror/chat with about_person_id should:
 - inject relational context block + cap intensity
 - return debug.relational with documented keys
 - pattern_memory debug now always present when dispatcher ran
"""
import json
import time
import uuid
import requests

BASE = "https://narrative-flex-v1.preview.emergentagent.com/api"
USER_ID = "697f0c6abf35c0528ff06954"

# Saved people on file for Pete:
SPOUSE_ID = "rel-test-spouse"    # relationship_type=spouse  -> class=romantic, ceiling=DIRECT
CHILD_ID  = "rel-test-child"     # relationship_type=child   -> class=child,    ceiling=DIRECT (NOT CONFRONTING)
FRIEND_ID = "6dabc234-80f6-4a4e-9184-522fc4a8e790"  # friend -> class=friendship, ceiling=CONFRONTING

results = []

def record(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    results.append({"name": name, "status": status, "detail": detail})
    marker = "OK " if passed else "XX "
    print(f"  {marker}{name}: {status} — {detail}")

def post(payload, timeout=60):
    t0 = time.time()
    r = requests.post(f"{BASE}/mirror/chat", json=payload, timeout=timeout)
    dt = time.time() - t0
    return r, dt


# ---------------------------------------------------------------------------
# E1: Relational layer activates on valid about_person_id
# ---------------------------------------------------------------------------
print("\n=== E1: relational layer activates on valid about_person_id (spouse) ===")
sid_e1 = f"ask-test-{uuid.uuid4().hex[:8]}"
payload = {
    "user_id": USER_ID,
    "message": "What should I understand about them?",
    "lens": None,
    "session_id": sid_e1,
    "include_journal": True,
    "include_history": True,
    "about_person_id": SPOUSE_ID,
}
r, dt = post(payload)
print(f"HTTP {r.status_code} ({dt:.1f}s)")
e1_ok = r.status_code == 200
record("E1.http_200", e1_ok, f"status={r.status_code}")
if e1_ok:
    data = r.json()
    debug = data.get("debug") or {}
    rel = debug.get("relational") or {}
    record("E1.relational_present", bool(rel), f"keys={list(rel.keys())}")
    record("E1.relationship_class_set",
           rel.get("relationship_class") in {"romantic","former","child","family_adult","friendship","professional","authority","power_over","mentorship","other"},
           f"class={rel.get('relationship_class')}")
    record("E1.relationship_class_is_romantic_for_spouse",
           rel.get("relationship_class") == "romantic",
           f"class={rel.get('relationship_class')}")
    record("E1.intensity_applied_set", bool(rel.get("intensity_applied")), f"intensity_applied={rel.get('intensity_applied')}")
    record("E1.intensity_pre_cap_set", bool(rel.get("intensity_pre_cap")), f"intensity_pre_cap={rel.get('intensity_pre_cap')}")
    record("E1.relationship_intensity_ceiling_set", bool(rel.get("relationship_intensity_ceiling")), f"ceiling={rel.get('relationship_intensity_ceiling')}")
    record("E1.projection_risk_set", rel.get("projection_risk") in {"low","moderate","high"}, f"risk={rel.get('projection_risk')}")
    record("E1.marker_relational_v1", rel.get("marker") == "relational-awareness-v1", f"marker={rel.get('marker')}")
    record("E1.about_person_id_matches", (rel.get("about_person") or {}).get("id") == SPOUSE_ID, f"about={rel.get('about_person')}")
    # Save reply for later qualitative review
    e1_reply = data.get("response", "")
    print(f"  reply preview: {e1_reply[:200]!r}")
else:
    print(f"  body: {r.text[:500]}")


# ---------------------------------------------------------------------------
# E2: Session continuity — same session id, follow-up turn
# ---------------------------------------------------------------------------
print("\n=== E2: session continuity (same session_id) ===")
payload2 = {
    "user_id": USER_ID,
    "message": "What about that pattern in work?",
    "lens": None,
    "session_id": sid_e1,
    "include_journal": True,
    "include_history": True,
    "about_person_id": SPOUSE_ID,
}
r2, dt2 = post(payload2)
print(f"HTTP {r2.status_code} ({dt2:.1f}s)")
e2_ok = r2.status_code == 200
record("E2.http_200", e2_ok, f"status={r2.status_code}")
if e2_ok:
    data2 = r2.json()
    debug2 = data2.get("debug") or {}
    rel2 = debug2.get("relational") or {}
    record("E2.relational_still_set_on_followup", bool(rel2), f"keys={list(rel2.keys())}")
    record("E2.same_session_id_returned", data2.get("session_id") == sid_e1, f"session_id={data2.get('session_id')}")
    e2_reply = data2.get("response", "")
    print(f"  reply preview: {e2_reply[:200]!r}")


# ---------------------------------------------------------------------------
# E3: pattern_memory marker always present (always-attach polish)
# ---------------------------------------------------------------------------
print("\n=== E3: pattern_memory marker always present (no trigger msg) ===")
payload3 = {
    "user_id": USER_ID,
    "message": "Tell me what's interesting about them today",
    "lens": None,
    "session_id": f"ask-test-{uuid.uuid4().hex[:8]}",
    "include_journal": True,
    "include_history": True,
    "about_person_id": SPOUSE_ID,
}
r3, dt3 = post(payload3)
print(f"HTTP {r3.status_code} ({dt3:.1f}s)")
e3_ok = r3.status_code == 200
record("E3.http_200", e3_ok, f"status={r3.status_code}")
if e3_ok:
    data3 = r3.json()
    debug3 = data3.get("debug") or {}
    pm = debug3.get("pattern_memory") or {}
    record("E3.pattern_memory_present", bool(pm), f"keys={list(pm.keys())}")
    record("E3.pattern_memory_marker_v1", pm.get("marker") == "pattern-memory-v1", f"marker={pm.get('marker')}")
    matched = pm.get("matched_patterns") or []
    record("E3.matched_patterns_empty_ok", isinstance(matched, list), f"matched={matched}")


# ---------------------------------------------------------------------------
# E4: Invalid about_person_id degrades gracefully
# ---------------------------------------------------------------------------
print("\n=== E4: invalid about_person_id degrades gracefully ===")
payload4 = {
    "user_id": USER_ID,
    "message": "What should I understand about them?",
    "lens": None,
    "session_id": f"ask-test-{uuid.uuid4().hex[:8]}",
    "include_journal": True,
    "include_history": True,
    "about_person_id": "non-existent-id-xyz",
}
r4, dt4 = post(payload4)
print(f"HTTP {r4.status_code} ({dt4:.1f}s)")
e4_ok = r4.status_code == 200
record("E4.http_200_no_crash", e4_ok, f"status={r4.status_code}")
if e4_ok:
    data4 = r4.json()
    debug4 = data4.get("debug") or {}
    rel4 = debug4.get("relational")
    record("E4.relational_absent_or_null", not rel4, f"relational={rel4}")


# ---------------------------------------------------------------------------
# E5: Cap-by-class sanity — child ceiling must NOT be CONFRONTING
# ---------------------------------------------------------------------------
print("\n=== E5: cap-by-class (child) ===")
payload5 = {
    "user_id": USER_ID,
    "message": "What should I understand about them?",
    "lens": None,
    "session_id": f"ask-test-{uuid.uuid4().hex[:8]}",
    "include_journal": True,
    "include_history": True,
    "about_person_id": CHILD_ID,
}
r5, dt5 = post(payload5)
print(f"HTTP {r5.status_code} ({dt5:.1f}s)")
e5_ok = r5.status_code == 200
record("E5.http_200", e5_ok, f"status={r5.status_code}")
if e5_ok:
    data5 = r5.json()
    rel5 = (data5.get("debug") or {}).get("relational") or {}
    ceiling5 = rel5.get("relationship_intensity_ceiling")
    record("E5.child_class_detected", rel5.get("relationship_class") == "child", f"class={rel5.get('relationship_class')}")
    record("E5.ceiling_not_confronting", ceiling5 != "CONFRONTING", f"ceiling={ceiling5}")
    record("E5.intensity_applied_not_confronting", rel5.get("intensity_applied") != "CONFRONTING", f"intensity_applied={rel5.get('intensity_applied')}")


# ---------------------------------------------------------------------------
# E6: Regression — no about_person_id → relational absent, pattern_memory present
# ---------------------------------------------------------------------------
print("\n=== E6: regression — no about_person_id ===")
payload6 = {
    "user_id": USER_ID,
    "message": "What's coming up for me today?",
    "lens": None,
    "session_id": f"ask-test-{uuid.uuid4().hex[:8]}",
    "include_journal": True,
    "include_history": True,
}
r6, dt6 = post(payload6)
print(f"HTTP {r6.status_code} ({dt6:.1f}s)")
e6_ok = r6.status_code == 200
record("E6.http_200", e6_ok, f"status={r6.status_code}")
if e6_ok:
    data6 = r6.json()
    debug6 = data6.get("debug") or {}
    rel6 = debug6.get("relational")
    pm6 = debug6.get("pattern_memory") or {}
    record("E6.relational_absent", not rel6, f"relational={rel6}")
    record("E6.pattern_memory_present_polish", pm6.get("marker") == "pattern-memory-v1", f"pm={pm6.get('marker')}")
    record("E6.latency_baseline", dt6 < 30, f"{dt6:.1f}s (target ~3-12s typical)")


# ---------------------------------------------------------------------------
# E7: Multi-lens with relational layer (astrology, numerology, null)
# ---------------------------------------------------------------------------
print("\n=== E7: multi-lens with relational layer ===")
for lens in ("astrology", "numerology", None):
    sid = f"ask-test-{lens or 'mirror'}-{uuid.uuid4().hex[:6]}"
    pay = {
        "user_id": USER_ID,
        "message": "What's the pattern between us right now?",
        "lens": lens,
        "session_id": sid,
        "include_journal": True,
        "include_history": True,
        "about_person_id": SPOUSE_ID,
    }
    rr, ddt = post(pay)
    print(f"  lens={lens}: HTTP {rr.status_code} ({ddt:.1f}s)")
    ok = rr.status_code == 200
    record(f"E7.{lens or 'null'}.http_200", ok, f"status={rr.status_code}")
    if ok:
        dd = rr.json()
        dbg = dd.get("debug") or {}
        rrel = dbg.get("relational") or {}
        record(f"E7.{lens or 'null'}.relational_present",
               bool(rrel) and rrel.get("relationship_class") == "romantic",
               f"class={rrel.get('relationship_class')}")
        # When lens != null, debug should expose lens-specific top-level fields
        if lens is not None:
            top_keys = [k for k in dbg.keys() if k not in {"relational", "pattern_memory"}]
            record(f"E7.{lens}.lens_specific_debug_present", len(top_keys) > 0, f"top_level_keys={top_keys}")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print("\n=========================================")
print("SUMMARY")
print("=========================================")
total = len(results)
passed = sum(1 for r in results if r["status"] == "PASS")
failed = total - passed
print(f"Total: {total} | PASS: {passed} | FAIL: {failed}")
for r in results:
    if r["status"] == "FAIL":
        print(f"  XX {r['name']}: {r['detail']}")

with open("/app/ask_about_person_results.json", "w") as f:
    json.dump({"total": total, "passed": passed, "failed": failed, "results": results}, f, indent=2)

print("\nResults written to /app/ask_about_person_results.json")
