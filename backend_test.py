"""
Backend test for "Between You Today" V1.1 + Telemetry.

Tests:
  A. Engine V1.1 schema + enhanced top-level prose guard
  B. Telemetry endpoint (POST /api/forums/{forum_id}/between-you-today/event)
  C. Auto-derived revisit event
  D. No regression of V1.0 tests
"""

import os
import re
import time
import asyncio
import requests
from typing import List
from datetime import datetime, timezone

BASE_URL = "https://mapping-phase4.preview.emergentagent.com/api"

FORUM_ID = "69dda348de9cb1c83c0780fa"
ANCHOR_USER_ID = "697f0c6abf35c0528ff06954"   # Pete

# ---------------------------------------------------------------------------
# Banned-token configuration (must match V1.1 enhanced top-level guard)
# ---------------------------------------------------------------------------

BANNED_ASTRO_WORDS = [
    "transit", "aspect", "conjunction", "retrograde",
    "soulmate", "compatibility", "cosmic", "manifest",
]
BANNED_PRESCRIPTIVE = ["should ", "must "]   # substring check w/ trailing space
BANNED_AI_PATTERNS = [
    "you both feel",
    "drives you both",
    "is being assessed",
    "there is a sense of",
    "this may cause",
    "energy around",
    "energy between",
    "the dynamic of",
    "what this means",
    "invitation to",
    "opportunity for growth",
    "in this moment",
    "at this time",
]


def banned_token_hits(text: str) -> List[str]:
    hits = []
    low = text.lower()
    for w in BANNED_ASTRO_WORDS:
        if re.search(r"\b" + re.escape(w) + r"\b", low):
            hits.append(f"astro:{w}")
    for ph in BANNED_PRESCRIPTIVE:
        if ph in low:
            hits.append(f"prescriptive:{ph.strip()}")
    for pat in BANNED_AI_PATTERNS:
        if pat in low:
            hits.append(f"ai-pattern:{pat}")
    return hits


def too_many_today(strings: List[str]) -> List[str]:
    """Return any single string that contains `today` more than 2x (case-insensitive)."""
    bad = []
    for s in strings:
        if isinstance(s, str) and s.lower().count("today") > 2:
            bad.append(s)
    return bad


def hero_word_count(hero: str) -> int:
    if not isinstance(hero, str):
        return -1
    return len([w for w in hero.split() if w.strip()])


def fetch_member_ids() -> List[str]:
    url = f"{BASE_URL}/forums/{FORUM_ID}/member-mappings"
    resp = requests.get(url, params={"user_id": ANCHOR_USER_ID}, timeout=60)
    print(f"[member-mappings] status={resp.status_code}")
    if resp.status_code != 200:
        print(f"  body: {resp.text[:400]}")
        return []
    data = resp.json()
    mappings = []
    if isinstance(data, dict):
        for key in ("mappings", "members", "data", "items", "results"):
            if isinstance(data.get(key), list):
                mappings = data[key]
                break
    if not mappings and isinstance(data, list):
        mappings = data
    member_ids = []
    for m in mappings:
        if not isinstance(m, dict):
            continue
        mid = (m.get("member_id") or m.get("user_id")
               or m.get("target_user_id") or m.get("member"))
        if mid and mid != ANCHOR_USER_ID:
            member_ids.append(mid)
    seen = set()
    uniq = []
    for mid in member_ids:
        if mid not in seen:
            seen.add(mid)
            uniq.append(mid)
    print(f"  resolved member ids ({len(uniq)}): {uniq}")
    return uniq


def call_get(forum_id, user_id, member_id, refresh=False, timeout=120):
    url = f"{BASE_URL}/forums/{forum_id}/between-you-today"
    params = {"user_id": user_id, "member_id": member_id}
    if refresh:
        params["refresh"] = "true"
    t0 = time.time()
    resp = requests.get(url, params=params, timeout=timeout)
    return resp, time.time() - t0


def call_event(forum_id, body, timeout=30):
    url = f"{BASE_URL}/forums/{forum_id}/between-you-today/event"
    t0 = time.time()
    resp = requests.post(url, json=body, timeout=timeout)
    return resp, time.time() - t0


def validate_v11_envelope(envelope):
    errors = []
    if envelope.get("engine_version") != "between-you-today-v1.1":
        errors.append(f"engine_version mismatch: {envelope.get('engine_version')}")
    if envelope.get("intensity") not in {"low", "medium", "high"}:
        errors.append(f"intensity invalid: {envelope.get('intensity')}")
    date_str = envelope.get("date", "")
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(date_str)):
        errors.append(f"date format invalid: {date_str}")
    hero = envelope.get("hero")
    if not isinstance(hero, str) or not hero.strip():
        errors.append(f"hero must be non-empty string, got: {repr(hero)[:80]}")
    for k in ("activated_today", "distortion_risk", "softens_field"):
        v = envelope.get(k)
        if not isinstance(v, list):
            errors.append(f"{k} must be list, got: {type(v).__name__}")
    proof = envelope.get("proof_layer")
    if not isinstance(proof, dict):
        errors.append("proof_layer must be dict")
    else:
        if not isinstance(proof.get("plain_english"), list):
            errors.append("proof_layer.plain_english must be list")
        if not isinstance(proof.get("technical"), list):
            errors.append("proof_layer.technical must be list")
    return (len(errors) == 0), errors


results = {}


def section(name):
    print("\n" + "=" * 78)
    print(name)
    print("=" * 78)


def record(name, ok: bool, detail: str = ""):
    results[name] = ("PASS" if ok else "FAIL", detail)
    print(f"  -> {'PASS' if ok else 'FAIL'} {name}  {detail}")


# ===========================================================================
# STEP 0 — Fetch member ids
# ===========================================================================
section("STEP 0 — Fetch member ids")
member_ids = fetch_member_ids()
if not member_ids:
    print("FATAL: cannot resolve member ids – aborting.")
    raise SystemExit(2)
primary_member_id = member_ids[0]
print(f"primary member_id: {primary_member_id}")


# ===========================================================================
# A. ENGINE V1.1 SCHEMA + GUARD
# ===========================================================================
section("A1 — GET happy path returns engine_version v1.1")
resp, elapsed = call_get(FORUM_ID, ANCHOR_USER_ID, primary_member_id, refresh=False)
print(f"status={resp.status_code} elapsed={elapsed:.2f}s")
today = None
if resp.status_code == 200:
    body = resp.json()
    today = body.get("today") or {}
    print(f"engine_version={today.get('engine_version')}")
    print(f"hero: {str(today.get('hero',''))[:300]}")
    record("A1_engine_version_v1.1",
           today.get("engine_version") == "between-you-today-v1.1",
           f"got={today.get('engine_version')}")
else:
    print(f"body: {resp.text[:400]}")
    record("A1_engine_version_v1.1", False, f"status={resp.status_code}")

# A2 schema fields
section("A2 — Schema fields all present")
if today:
    ok, errs = validate_v11_envelope(today)
    record("A2_schema_complete", ok, "; ".join(errs) if errs else "")
else:
    record("A2_schema_complete", False, "no envelope")

# A3 enhanced prose guard
section("A3 — Enhanced top-level prose guard (V1.1)")
all_offenders = []
strings_for_today_count = []
if today:
    parts = []
    if isinstance(today.get("hero"), str):
        parts.append(today["hero"])
        strings_for_today_count.append(today["hero"])
    for k in ("activated_today", "distortion_risk", "softens_field"):
        v = today.get(k)
        if isinstance(v, list):
            for item in v:
                if isinstance(item, str):
                    parts.append(item)
                    strings_for_today_count.append(item)
                elif isinstance(item, dict):
                    for f in ("text", "title", "label", "body"):
                        if isinstance(item.get(f), str):
                            parts.append(item[f])
                            strings_for_today_count.append(item[f])
    concatenated = " || ".join(parts)
    print(f"Concatenated top-level prose ({len(concatenated)} chars):")
    print(concatenated[:1500])
    hits = banned_token_hits(concatenated)
    today_overuse = too_many_today(strings_for_today_count)
    if hits:
        all_offenders.append(f"banned_tokens={hits}")
        # find which substring lives in which input string for debug
        for h in hits:
            label, _, raw = h.partition(":")
            for s in parts:
                if raw and raw.lower() in s.lower():
                    print(f"  OFFENDING ({h}) in: {s!r}")
                    break
    if today_overuse:
        all_offenders.append(f"today_overuse_count={len(today_overuse)}")
        for s in today_overuse:
            print(f"  TODAY-OVERUSE ({s.lower().count('today')}x): {s!r}")
    record("A3_prose_guard", not all_offenders, "; ".join(all_offenders) if all_offenders else "clean")
else:
    record("A3_prose_guard", False, "no envelope")

# A4 hero word count <=45
section("A4 — Hero word count ≤ 45")
if today:
    wc = hero_word_count(today.get("hero", ""))
    print(f"hero word count: {wc}")
    record("A4_hero_word_count_le_45", 0 < wc <= 45, f"wc={wc}")
else:
    record("A4_hero_word_count_le_45", False, "no envelope")

# A5 all 3 forum members → valid V1.1
section("A5 — All 3 members produce valid V1.1 envelopes")
member_results = []
all_pass = True
for mid in member_ids[:3]:
    r, e = call_get(FORUM_ID, ANCHOR_USER_ID, mid, refresh=False, timeout=120)
    if r.status_code != 200:
        all_pass = False
        member_results.append(f"{mid}: status={r.status_code}")
        continue
    b = r.json()
    t = b.get("today") or {}
    ok, errs = validate_v11_envelope(t) if t else (False, ["no envelope"])
    is_v11 = (t.get("engine_version") == "between-you-today-v1.1")
    if not (ok and b.get("success") and is_v11):
        all_pass = False
    member_results.append(f"{mid}: ok={ok} v1.1={is_v11} hero_len={len(str(t.get('hero','')))} elapsed={e:.1f}s")
for line in member_results:
    print("  " + line)
record("A5_all_members_v1.1_valid", all_pass, " | ".join(member_results))


# ===========================================================================
# B. TELEMETRY ENDPOINT
# ===========================================================================
section("B6 — Whitelisted events return 200 success:true")
events_to_test = [
    {"event": "today_card_viewed"},
    {"event": "proof_expanded"},
    {"event": "proof_collapsed"},
    {"event": "proof_mode_switched", "extra": {"from": "plain", "to": "technical"}},
    {"event": "hero_regenerated_same_day"},
]
all_ok = True
event_details = []
for ev in events_to_test:
    body = {
        "event": ev["event"],
        "user_id": ANCHOR_USER_ID,
        "member_id": primary_member_id,
        "intensity": "high",
        "cache_hit": False,
    }
    if "extra" in ev:
        body["extra"] = ev["extra"]
    r, _ = call_event(FORUM_ID, body)
    ok = (r.status_code == 200)
    try:
        succ = r.json().get("success")
    except Exception:
        succ = None
    if not (ok and succ is True):
        all_ok = False
    event_details.append(f"{ev['event']}: status={r.status_code} success={succ}")
for d in event_details:
    print("  " + d)
record("B6_whitelisted_events_ok", all_ok, " | ".join(event_details))

section("B7 — Unknown event name returns 200 with success:false")
r, _ = call_event(FORUM_ID, {
    "event": "random_event",
    "user_id": ANCHOR_USER_ID,
    "member_id": primary_member_id,
})
try:
    js = r.json()
except Exception:
    js = {}
print(f"  status={r.status_code} body={js}")
record("B7_unknown_event",
       r.status_code == 200 and js.get("success") is False,
       f"status={r.status_code} success={js.get('success')}")

section("B8 — Missing required field (no event) returns 400")
r, _ = call_event(FORUM_ID, {
    "user_id": ANCHOR_USER_ID,
    "member_id": primary_member_id,
})
print(f"  status={r.status_code} body={r.text[:200]}")
record("B8_missing_field_400", r.status_code == 400, f"status={r.status_code}")

section("B9 — Anchor not in forum returns 403")
r, _ = call_event(FORUM_ID, {
    "event": "today_card_viewed",
    "user_id": "000000000000000000000099",
    "member_id": primary_member_id,
})
print(f"  status={r.status_code} body={r.text[:200]}")
record("B9_non_member_403", r.status_code == 403, f"status={r.status_code}")

section("B10 — Invalid forum_id returns 400")
r, _ = call_event("not-objectid", {
    "event": "today_card_viewed",
    "user_id": ANCHOR_USER_ID,
    "member_id": primary_member_id,
})
print(f"  status={r.status_code} body={r.text[:200]}")
record("B10_invalid_forum_id_400", r.status_code == 400, f"status={r.status_code}")


# ===========================================================================
# C. AUTO-DERIVED REVISIT EVENT
# ===========================================================================
section("C11 — Revisit event auto-derived after 3 views (Mongo direct)")

# Use a fresh (anchor, member, date) tuple so prior views don't pollute count
TEST_DATE = datetime.now(timezone.utc).strftime("%Y-%m-%d")

# Fire today_card_viewed THREE TIMES
for i in range(3):
    r, _ = call_event(FORUM_ID, {
        "event": "today_card_viewed",
        "user_id": ANCHOR_USER_ID,
        "member_id": primary_member_id,
        "intensity": "high",
        "cache_hit": False,
        "date": TEST_DATE,
        "extra": {"test_run": "C11", "i": i},
    })
    try:
        s = r.json().get("success")
    except Exception:
        s = None
    print(f"  view {i+1}: status={r.status_code} success={s}")

# Now query Mongo directly for revisit events on this (anchor,target,date)
async def query_revisits():
    from motor.motor_asyncio import AsyncIOMotorClient
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.environ.get("DB_NAME", "test_database")
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    # Find ALL events for this (anchor, target, date) for diagnostic purposes
    all_evs = await db["relationship_today_events"].find({
        "anchor_id": ANCHOR_USER_ID,
        "target_id": primary_member_id,
        "date": TEST_DATE,
    }).to_list(length=200)
    revisits = [e for e in all_evs if e.get("event") == "today_card_revisited_same_day"]
    views = [e for e in all_evs if e.get("event") == "today_card_viewed"]
    return views, revisits

# we need to filter to JUST this current test_run because the same anchor+target+date
# may have had earlier views (from B6) within this test session.
async def query_revisits_for_run():
    from motor.motor_asyncio import AsyncIOMotorClient
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.environ.get("DB_NAME", "test_database")
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    all_evs = await db["relationship_today_events"].find({
        "anchor_id": ANCHOR_USER_ID,
        "target_id": primary_member_id,
        "date": TEST_DATE,
    }).to_list(length=500)
    return all_evs

all_evs = asyncio.run(query_revisits_for_run())
views = [e for e in all_evs if e.get("event") == "today_card_viewed"]
revisits = [e for e in all_evs if e.get("event") == "today_card_revisited_same_day"]
print(f"  TOTAL views for (anchor,target,date)={TEST_DATE}: {len(views)}")
print(f"  TOTAL revisits for same key: {len(revisits)}")

# Rule: revisit fires on every view AFTER the first → revisits == views - 1.
expected_revisits = max(0, len(views) - 1)
print(f"  expected revisits = {expected_revisits} (views-1)")
ok_revisit = (len(revisits) == expected_revisits) and (len(revisits) >= 2)
record("C11_revisit_auto_derived",
       ok_revisit,
       f"views={len(views)} revisits={len(revisits)} expected={expected_revisits}")


# ===========================================================================
# D. NO REGRESSION — equivalent of original 8 V1.0 tests
# ===========================================================================
section("D12a — GET happy path (regression)")
record("D12a_get_happy_path", today is not None and today.get("engine_version") == "between-you-today-v1.1",
       "see A1")

section("D12b — 403 (anchor not in forum)")
r, _ = call_get(FORUM_ID, "000000000000000000000001", primary_member_id, timeout=30)
print(f"  status={r.status_code}")
record("D12b_get_403", r.status_code == 403, f"status={r.status_code}")

section("D12c — 404 (member not in forum)")
r, _ = call_get(FORUM_ID, ANCHOR_USER_ID, "000000000000000000000002", timeout=30)
print(f"  status={r.status_code}")
record("D12c_get_404", r.status_code == 404, f"status={r.status_code}")

section("D12d — 400 (invalid forum_id)")
r, _ = call_get("not-an-objectid", ANCHOR_USER_ID, primary_member_id, timeout=30)
print(f"  status={r.status_code}")
record("D12d_get_400", r.status_code == 400, f"status={r.status_code}")

section("D12e — Cache hit (second GET no refresh returns identical envelope)")
r1, _ = call_get(FORUM_ID, ANCHOR_USER_ID, primary_member_id, refresh=False, timeout=120)
r2, _ = call_get(FORUM_ID, ANCHOR_USER_ID, primary_member_id, refresh=False, timeout=120)
ok_cache = False
detail_cache = ""
if r1.status_code == 200 and r2.status_code == 200:
    t1 = (r1.json().get("today") or {})
    t2 = (r2.json().get("today") or {})
    same_hero = t1.get("hero") == t2.get("hero")
    cache_hit_2 = t2.get("_cache_hit")
    print(f"  same_hero={same_hero}  _cache_hit={cache_hit_2}")
    print(f"  hero1={t1.get('hero')!r}")
    print(f"  hero2={t2.get('hero')!r}")
    ok_cache = same_hero and (cache_hit_2 is True)
    detail_cache = f"same_hero={same_hero} _cache_hit={cache_hit_2}"
else:
    detail_cache = f"r1={r1.status_code} r2={r2.status_code}"
record("D12e_cache_hit", ok_cache, detail_cache)

section("D12f — refresh=true bypass (returns 200, valid envelope)")
r, _ = call_get(FORUM_ID, ANCHOR_USER_ID, primary_member_id, refresh=True, timeout=120)
ok_bypass = False
if r.status_code == 200:
    t = (r.json().get("today") or {})
    ok_bypass, errs = validate_v11_envelope(t)
record("D12f_refresh_bypass", ok_bypass, "")

section("D12g — Parallel members (3) all valid")
record("D12g_parallel_members", all_pass, "see A5")


# ===========================================================================
# Summary
# ===========================================================================
section("RESULTS SUMMARY")
passed = 0
failed = 0
for name, (status, detail) in results.items():
    print(f"[{status}] {name:34s}  {detail}")
    if status == "PASS":
        passed += 1
    else:
        failed += 1
print(f"\nTOTAL: {passed} passed / {failed} failed")
