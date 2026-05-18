"""
End-to-end backend test for relational-awareness-v1 on POST /api/mirror/chat
User: Pete (697f0c6abf35c0528ff06954)
"""
import json
import time
import requests

BASE = "https://individual-maps-v1.preview.emergentagent.com/api"
USER_ID = "697f0c6abf35c0528ff06954"
ENDPOINT = f"{BASE}/mirror/chat"

results = []

def post(name, body, expect_status=200):
    print(f"\n========== {name} ==========")
    print(f"REQUEST: {json.dumps(body)[:300]}")
    t0 = time.time()
    try:
        r = requests.post(ENDPOINT, json=body, timeout=90)
    except Exception as e:
        print(f"  HTTP error: {e}")
        results.append({"name": name, "status": "ERROR", "err": str(e)})
        return None
    dur = time.time() - t0
    print(f"STATUS: {r.status_code}  ({dur:.2f}s)")
    if r.status_code != expect_status:
        print(f"  body: {r.text[:500]}")
        results.append({"name": name, "status": "HTTP_FAIL", "code": r.status_code, "body": r.text[:1000]})
        return None
    data = r.json()
    debug = data.get("debug")
    rel = (debug or {}).get("relational") if isinstance(debug, dict) else None
    print(f"DEBUG.intensity_mode: {(debug or {}).get('intensity_mode') if isinstance(debug, dict) else None}")
    print(f"DEBUG.intensity_capped_by_relational: {(debug or {}).get('intensity_capped_by_relational') if isinstance(debug, dict) else None}")
    print(f"DEBUG.relational: {json.dumps(rel, indent=2) if rel else rel}")
    print(f"RESPONSE TEXT (truncated 600):")
    print((data.get("response") or "")[:600])
    return data


# R1. CHILD class caps CONFRONTING → DIRECT
r1 = post("R1 CHILD caps CONFRONTING -> DIRECT", {
    "user_id": USER_ID,
    "message": "Challenge me. Don't hold back. Why is Test Child always so avoidant with me?",
    "lens": "enneagram",
    "about_person_id": "rel-test-child"
})

# R2. FRIENDSHIP class preserves CONFRONTING
r2 = post("R2 FRIENDSHIP allows CONFRONTING", {
    "user_id": USER_ID,
    "message": "Be honest, what am I avoiding? Challenge me. Don't hold back.",
    "lens": "enneagram",
    "about_person_id": "6dabc234-80f6-4a4e-9184-522fc4a8e790"
})

# R3. AUTHORITY (boss) caps at DIRECT
r3 = post("R3 AUTHORITY caps at DIRECT", {
    "user_id": USER_ID,
    "message": "Challenge me — what am I missing about my Test Boss?",
    "lens": "human_design",
    "about_person_id": "rel-test-boss"
})

# R4. SPOUSE with absolutist phrasing
r4 = post("R4 SPOUSE absolutist + blame -> high projection", {
    "user_id": USER_ID,
    "message": "Why is my Test Spouse always so cold and distant? It's all his fault we don't connect anymore.",
    "lens": "astrology",
    "about_person_id": "rel-test-spouse"
})

# R5. FORMER (ex_partner)
r5 = post("R5 FORMER ex_partner class", {
    "user_id": USER_ID,
    "message": "I keep thinking about my Test Ex — what does this say about me?",
    "lens": "astrology",
    "about_person_id": "rel-test-ex"
})

# R6. No about_person_id — regression
r6 = post("R6 No about_person_id (regression)", {
    "user_id": USER_ID,
    "message": "Challenge me. Don't hold back. Why is Test Child always so avoidant with me?",
    "lens": "enneagram"
})

# R7. Invalid about_person_id
r7 = post("R7 invalid about_person_id (no crash)", {
    "user_id": USER_ID,
    "message": "Hello, what do you see for me today?",
    "lens": "enneagram",
    "about_person_id": "nonexistent-id-12345"
})

# R8. SOFT preserved
r8 = post("R8 SOFT preserved across relational", {
    "user_id": USER_ID,
    "message": "I feel so lost. I can't stop crying about Test Spouse.",
    "lens": "astrology",
    "about_person_id": "rel-test-spouse"
})

# R9. Generalist regression no lens
r9 = post("R9 Generalist no lens, no person", {
    "user_id": USER_ID,
    "message": "Just thinking through things today.",
    "lens": None
})

# R10. Generalist + about_person_id
r10 = post("R10 Generalist + about_person_id (relational without lens)", {
    "user_id": USER_ID,
    "message": "Challenge me. Don't hold back. Why is Test Child always so avoidant with me?",
    "lens": None,
    "about_person_id": "rel-test-child"
})

# Save results for human inspection
all_data = {
    "R1": r1, "R2": r2, "R3": r3, "R4": r4, "R5": r5,
    "R6": r6, "R7": r7, "R8": r8, "R9": r9, "R10": r10,
}
with open("/app/relational_awareness_results.json", "w") as f:
    json.dump(all_data, f, indent=2, default=str)

print("\n\n========== VERDICT SUMMARY ==========")

def get_dbg(d):
    return (d or {}).get("debug")

def get_rel(d):
    dbg = get_dbg(d)
    return (dbg or {}).get("relational") if isinstance(dbg, dict) else None

def verdict(name, ok, reason=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {reason}")

# R1 checks
if r1:
    dbg = get_dbg(r1)
    rel = get_rel(r1)
    checks = []
    checks.append(("marker", rel and rel.get("marker") == "relational-awareness-v1"))
    checks.append(("class=child", rel and rel.get("relationship_class") == "child"))
    checks.append(("ceiling=DIRECT", rel and rel.get("relationship_intensity_ceiling") == "DIRECT"))
    checks.append(("intensity_applied=DIRECT", rel and rel.get("intensity_applied") == "DIRECT"))
    checks.append(("absolutist_language=true", rel and rel.get("projection_signals", {}).get("absolutist_language") == True))
    checks.append(("projection_risk in {moderate,high}", rel and rel.get("projection_risk") in ("moderate","high")))
    checks.append(("debug.intensity_mode=DIRECT", dbg and dbg.get("intensity_mode") == "DIRECT"))
    pre = rel and rel.get("intensity_pre_cap")
    checks.append(("intensity_pre_cap in {CONFRONTING,DIRECT}", pre in ("CONFRONTING","DIRECT")))
    if pre == "CONFRONTING":
        checks.append(("intensity_capped_by_relational=True", dbg.get("intensity_capped_by_relational") is True))
    for label, ok in checks:
        verdict(f"R1 {label}", ok)

# R2 checks
if r2:
    rel = get_rel(r2)
    verdict("R2 class=friendship", rel and rel.get("relationship_class") == "friendship")
    verdict("R2 ceiling=CONFRONTING", rel and rel.get("relationship_intensity_ceiling") == "CONFRONTING")
    if rel:
        verdict("R2 intensity_was_capped=False OR applied==pre_cap",
                rel.get("intensity_was_capped") is False or rel.get("intensity_applied") == rel.get("intensity_pre_cap"))

# R3 checks
if r3:
    rel = get_rel(r3)
    verdict("R3 class=authority", rel and rel.get("relationship_class") == "authority")
    if rel:
        rank = {"SOFT":0,"OBSERVATIONAL":1,"DIRECT":2,"CONFRONTING":3}
        verdict("R3 intensity_applied <= DIRECT", rank.get(rel.get("intensity_applied"),1) <= 2)

# R4 checks
if r4:
    rel = get_rel(r4)
    verdict("R4 class=romantic", rel and rel.get("relationship_class") == "romantic")
    if rel:
        sig = rel.get("projection_signals") or {}
        verdict("R4 absolutist_language=true", sig.get("absolutist_language") is True)
        verdict("R4 blame_focus=true", sig.get("blame_focus") is True)
        verdict("R4 projection_risk=high", rel.get("projection_risk") == "high")

# R5 checks
if r5:
    rel = get_rel(r5)
    verdict("R5 class=former", rel and rel.get("relationship_class") == "former")
    verdict("R5 ceiling=DIRECT", rel and rel.get("relationship_intensity_ceiling") == "DIRECT")

# R6 checks (no about_person_id)
if r6:
    dbg = get_dbg(r6)
    rel = get_rel(r6)
    verdict("R6 debug.relational absent", rel is None or rel == {} )
    verdict("R6 lens-level debug intact (intensity_mode present)", isinstance(dbg, dict) and "intensity_mode" in dbg)

# R7 checks
if r7:
    dbg = get_dbg(r7)
    rel = get_rel(r7)
    verdict("R7 HTTP 200 (no crash) AND debug.relational absent", rel is None or rel == {})

# R8 checks
if r8:
    dbg = get_dbg(r8)
    rel = get_rel(r8)
    verdict("R8 debug.intensity_mode=SOFT", dbg and dbg.get("intensity_mode") == "SOFT")
    verdict("R8 relational.intensity_applied=SOFT", rel and rel.get("intensity_applied") == "SOFT")

# R9 checks
if r9:
    dbg = get_dbg(r9)
    verdict("R9 debug is None", dbg is None)

# R10 checks
if r10:
    dbg = get_dbg(r10)
    rel = get_rel(r10)
    verdict("R10 debug is NOT None", dbg is not None)
    verdict("R10 relational.marker present", rel and rel.get("marker") == "relational-awareness-v1")

print("\nResults JSON written to /app/relational_awareness_results.json")
