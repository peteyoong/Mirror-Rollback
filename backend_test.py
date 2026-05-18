"""
Backend test for pattern-memory-v1 longitudinal pattern memory.
Tests POST /api/mirror/chat for user Pete (user_id=697f0c6abf35c0528ff06954).
"""
import os, json, asyncio
import requests

BASE_URL = "https://individual-maps-v1.preview.emergentagent.com/api"
PETE = "697f0c6abf35c0528ff06954"

def call_mirror_chat(message, lens=None):
    body = {"user_id": PETE, "message": message}
    if lens is not None:
        body["lens"] = lens
    return requests.post(f"{BASE_URL}/mirror/chat", json=body, timeout=120)

def pretty(d):
    try:
        return json.dumps(d, indent=2, default=str)
    except Exception:
        return str(d)

def show_response_summary(label, r):
    print(f"\n=== {label} ===")
    print(f"HTTP: {r.status_code}")
    try:
        data = r.json()
    except Exception:
        print("Non-JSON:", r.text[:500])
        return None
    debug = data.get("debug") or {}
    pm = debug.get("pattern_memory")
    print("debug.pattern_memory:", pretty(pm))
    return data

def assert_(label, ok, detail=""):
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {label} {('— ' + detail) if detail else ''}")
    return ok

results = {}

# ---- P1 ----
print("\n########## P1: Strong recurrence (work_exhaustion) ##########")
r = call_mirror_chat("I'm completely burnt out again from work. So drained.", lens="astrology")
data = show_response_summary("P1", r)
checks = []
checks.append(assert_("HTTP 200", r.status_code == 200))
pm = (data.get("debug") or {}).get("pattern_memory") if data else None
checks.append(assert_("pattern_memory present", pm is not None))
if pm:
    checks.append(assert_("marker == pattern-memory-v1", pm.get("marker") == "pattern-memory-v1"))
    keys = [p["pattern_key"] for p in pm.get("matched_patterns", [])]
    checks.append(assert_("matched_patterns includes work_exhaustion",
                          "work_exhaustion" in keys, f"keys={keys}"))
    checks.append(assert_("surfaceable_count >= 1", pm.get("surfaceable_count", 0) >= 1,
                          f"got {pm.get('surfaceable_count')}"))
    checks.append(assert_("surfaced_keys includes work_exhaustion",
                          "work_exhaustion" in (pm.get("surfaced_keys") or [])))
resp_text = (data or {}).get("response", "") or ""
print(f"\n--- P1 RESPONSE TEXT ---\n{resp_text}\n")
checks.append(assert_("response does not quote 'on [date] you said'",
                      "you said" not in resp_text.lower() or "on " not in resp_text.lower()
                      or not any(w in resp_text.lower() for w in [" you said on", "on march", "on april", "on may"])))
results["P1"] = all(checks)

# ---- P2 ----
print("\n########## P2: Moderate recurrence + growth shift (anxiety_loop) ##########")
r = call_mirror_chat("I'm a bit anxious today but it's manageable, just some overthinking",
                     lens="enneagram")
data = show_response_summary("P2", r)
checks = []
checks.append(assert_("HTTP 200", r.status_code == 200))
pm = (data.get("debug") or {}).get("pattern_memory") if data else None
if pm:
    keys = [p["pattern_key"] for p in pm.get("matched_patterns", [])]
    checks.append(assert_("matched_patterns includes anxiety_loop",
                          "anxiety_loop" in keys, f"keys={keys}"))
    checks.append(assert_("growth_shifts_count >= 1",
                          pm.get("growth_shifts_count", 0) >= 1,
                          f"got {pm.get('growth_shifts_count')}"))
    checks.append(assert_("growth_keys includes anxiety_loop",
                          "anxiety_loop" in (pm.get("growth_keys") or [])))
else:
    checks.append(assert_("pattern_memory present", False))
resp_text = (data or {}).get("response", "") or ""
print(f"\n--- P2 RESPONSE TEXT ---\n{resp_text}\n")
results["P2"] = all(checks)

# ---- P3: pre-clean ----
print("\n########## P3: New pattern, weak recurrence (avoidance_pattern) ##########")
async def clean_avoidance():
    from motor.motor_asyncio import AsyncIOMotorClient
    client = AsyncIOMotorClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
    db = client[os.environ.get('DB_NAME', 'test_database')]
    res = await db.longitudinal_pattern_memory.delete_many(
        {"user_id": PETE, "pattern_key": "avoidance_pattern"})
    return res.deleted_count
deleted = asyncio.run(clean_avoidance())
print(f"(cleaned {deleted} pre-existing avoidance_pattern docs)")

r = call_mirror_chat("I've been procrastinating on a big work decision", lens="human_design")
data = show_response_summary("P3", r)
checks = []
checks.append(assert_("HTTP 200", r.status_code == 200))
pm = (data.get("debug") or {}).get("pattern_memory") if data else None
if pm:
    keys = [p["pattern_key"] for p in pm.get("matched_patterns", [])]
    checks.append(assert_("matched_patterns includes avoidance_pattern",
                          "avoidance_pattern" in keys, f"keys={keys}"))
    checks.append(assert_("surfaceable_count == 0",
                          pm.get("surfaceable_count") == 0,
                          f"got {pm.get('surfaceable_count')}"))
else:
    checks.append(assert_("pattern_memory present", False))
results["P3"] = all(checks)

# ---- P4 ----
print("\n########## P4: Persistence — 2nd avoidance message ##########")
r = call_mirror_chat("I've been procrastinating on a big work decision", lens="human_design")
data = show_response_summary("P4 second call", r)
checks = []
checks.append(assert_("HTTP 200", r.status_code == 200))
pm = (data.get("debug") or {}).get("pattern_memory") if data else None
if pm:
    avoid_entry = next((p for p in pm.get("matched_patterns", [])
                        if p["pattern_key"] == "avoidance_pattern"), None)
    if avoid_entry:
        oc = avoid_entry.get("occurrence_count", 0)
        checks.append(assert_("avoidance_pattern occurrence_count >= 2",
                              oc >= 2, f"got {oc}"))
    else:
        checks.append(assert_("avoidance_pattern present", False))
    checks.append(assert_("surfaceable_count >= 1",
                          pm.get("surfaceable_count", 0) >= 1,
                          f"got {pm.get('surfaceable_count')}"))
else:
    checks.append(assert_("pattern_memory present", False))
results["P4"] = all(checks)

# ---- P5 ----
print("\n########## P5: Clean message, no pattern triggers ##########")
r = call_mirror_chat("Tell me about my Saturn placement", lens="astrology")
data = show_response_summary("P5", r)
checks = []
checks.append(assert_("HTTP 200", r.status_code == 200))
debug = (data or {}).get("debug") or {}
pm = debug.get("pattern_memory")
checks.append(assert_("debug.pattern_memory is absent",
                      pm is None, f"got {pretty(pm)}"))
checks.append(assert_("lens debug still present (non-empty debug)",
                      bool(debug), "expected lens debug for lens=astrology"))
results["P5"] = all(checks)

# ---- P6 ----
print("\n########## P6: Generalist lens + multiple triggers ##########")
r = call_mirror_chat("I'm so exhausted from work and feeling not good enough", lens=None)
data = show_response_summary("P6", r)
checks = []
checks.append(assert_("HTTP 200", r.status_code == 200))
pm = (data.get("debug") or {}).get("pattern_memory") if data else None
if pm:
    keys = [p["pattern_key"] for p in pm.get("matched_patterns", [])]
    print(f"  matched keys: {keys}")
    checks.append(assert_("matched at least one pattern", len(keys) >= 1))
results["P6"] = all(checks)

# ---- P7 ----
print("\n########## P7: Multiple patterns in one message ##########")
r = call_mirror_chat(
    "I feel so distant from my partner and I'm always anxious about being abandoned",
    lens=None)
data = show_response_summary("P7", r)
checks = []
checks.append(assert_("HTTP 200", r.status_code == 200))
pm = (data.get("debug") or {}).get("pattern_memory") if data else None
if pm:
    keys = [p["pattern_key"] for p in pm.get("matched_patterns", [])]
    print(f"  matched keys: {keys}")
    checks.append(assert_("relational_distance present", "relational_distance" in keys))
    checks.append(assert_("attachment_anxiety present", "attachment_anxiety" in keys))
else:
    checks.append(assert_("pattern_memory present", False))
results["P7"] = all(checks)

# ---- P8 ----
print("\n########## P8: Data hygiene — no raw transcript ##########")
async def check_hygiene():
    from motor.motor_asyncio import AsyncIOMotorClient
    client = AsyncIOMotorClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
    db = client[os.environ.get('DB_NAME', 'test_database')]
    docs = await db.longitudinal_pattern_memory.find(
        {"user_id": PETE}).to_list(length=50)
    return docs

docs = asyncio.run(check_hygiene())
allowed_fields = {
    "user_id", "pattern_key", "category", "first_seen_at", "last_seen_at",
    "occurrence_count", "recent_seen_at", "lens_contexts", "intensity_contexts",
    "domain_contexts", "last_observed_intensity", "peak_intensity",
    "growth_shifts_count", "_id"
}
print(f"  Found {len(docs)} documents for Pete")
all_ok = True
for d in docs[:5]:
    keys = set(d.keys())
    extra = keys - allowed_fields
    print(f"   - pattern_key={d.get('pattern_key')} fields={sorted(keys - {'_id'})}")
    print(f"       occurrence_count={d.get('occurrence_count')} peak={d.get('peak_intensity')} "
          f"last={d.get('last_observed_intensity')} growth={d.get('growth_shifts_count')}")
    print(f"       lens_contexts={d.get('lens_contexts')} intensity_contexts={d.get('intensity_contexts')} "
          f"domain_contexts={d.get('domain_contexts')}")
    if extra:
        print(f"       UNEXPECTED FIELDS: {extra}")
        all_ok = False
    for k, v in d.items():
        if isinstance(v, str) and len(v) > 60 and k != "_id":
            print(f"       SUSPICIOUSLY LONG STRING in {k}: {v[:120]}")
            all_ok = False
results["P8"] = assert_("Only allowed fields, no transcripts", all_ok)

print("\n\n############### SUMMARY ###############")
for k, v in results.items():
    print(f"{k}: {'PASS' if v else 'FAIL'}")
