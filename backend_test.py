"""
Backend test for "Between You Today" relationship timing endpoint.

Endpoint: GET /api/forums/{forum_id}/between-you-today
Query params: user_id (anchor), member_id (target), optional refresh=true/false
"""

import re
import time
import requests
from typing import List, Tuple

BASE_URL = "https://mapping-phase4.preview.emergentagent.com/api"

FORUM_ID = "69dda348de9cb1c83c0780fa"
ANCHOR_USER_ID = "697f0c6abf35c0528ff06954"   # Pete

BANNED_TOKENS = [
    "transit", "transits", "retrograde", "aspect", "conjunction", "opposition",
    "trine", "square", "sextile", "house", "houses", "ingress", "decan",
    "natal chart", "ascendant", "rising sign", "soulmate", "twin flame",
    "destiny", "destined", "fated", "karmic", "karma", "compatibility",
    "compatible", "vibes", "cosmic", "manifest", "manifestation",
]
BANNED_PHRASES_SPACED = ["should", "must"]


def banned_token_hits(text: str) -> List[str]:
    hits = []
    low = text.lower()
    for tok in BANNED_TOKENS:
        pattern = r"\b" + re.escape(tok) + r"\b"
        if re.search(pattern, low):
            hits.append(tok)
    for ph in BANNED_PHRASES_SPACED:
        pattern = r"\b" + re.escape(ph) + r"\b"
        if re.search(pattern, low):
            hits.append(ph)
    return hits


def fetch_member_ids() -> List[str]:
    url = f"{BASE_URL}/forums/{FORUM_ID}/member-mappings"
    resp = requests.get(url, params={"user_id": ANCHOR_USER_ID}, timeout=60)
    print(f"[member-mappings] status={resp.status_code}")
    if resp.status_code != 200:
        print(f"  body: {resp.text[:400]}")
        return []
    data = resp.json()
    print(f"  top-level keys: {list(data.keys()) if isinstance(data, dict) else type(data).__name__}")
    mappings = []
    if isinstance(data, dict):
        for key in ("mappings", "members", "data", "items", "results"):
            if isinstance(data.get(key), list):
                mappings = data[key]
                print(f"  using key '{key}' with {len(mappings)} items")
                break
    if not mappings and isinstance(data, list):
        mappings = data
    if not mappings:
        # dump a peek
        print(f"  raw body preview: {str(data)[:500]}")
    member_ids = []
    for m in mappings:
        if not isinstance(m, dict):
            continue
        mid = (m.get("member_id") or m.get("user_id")
               or m.get("target_user_id") or m.get("member"))
        if mid and mid != ANCHOR_USER_ID:
            member_ids.append(mid)
    # de-dup preserving order
    seen = set()
    uniq = []
    for mid in member_ids:
        if mid not in seen:
            seen.add(mid)
            uniq.append(mid)
    print(f"  resolved member ids ({len(uniq)}): {uniq}")
    return uniq


def call_endpoint(forum_id, user_id, member_id, refresh=False, timeout=120):
    url = f"{BASE_URL}/forums/{forum_id}/between-you-today"
    params = {"user_id": user_id, "member_id": member_id}
    if refresh:
        params["refresh"] = "true"
    t0 = time.time()
    resp = requests.get(url, params=params, timeout=timeout)
    elapsed = time.time() - t0
    return resp, elapsed


def validate_envelope(envelope):
    errors = []
    if envelope.get("version") != "between-you-today-v1":
        errors.append(f"version mismatch: {envelope.get('version')}")
    if envelope.get("engine_version") != "between-you-today-v1.0":
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
    print("\n" + "=" * 72)
    print(name)
    print("=" * 72)


# ───── Step 0
section("STEP 0 — Fetch member mappings")
member_ids = fetch_member_ids()
if not member_ids:
    print("FATAL: Cannot fetch member ids – cannot continue.")
    raise SystemExit(2)

primary_member_id = member_ids[0]
print(f"Primary member_id for tests: {primary_member_id}")

# ───── Test 1: Happy path
section("TEST 1 — Happy path")
resp, elapsed = call_endpoint(FORUM_ID, ANCHOR_USER_ID, primary_member_id, refresh=False)
print(f"status={resp.status_code} elapsed={elapsed:.2f}s")
body = None
today = None
if resp.status_code == 200:
    body = resp.json()
    print(f"success={body.get('success')}")
    today = body.get("today") or {}
    print(f"version={today.get('version')} engine_version={today.get('engine_version')}")
    print(f"date={today.get('date')} intensity={today.get('intensity')}")
    print(f"hero: {str(today.get('hero',''))[:300]}")
    print(f"activated_today ({len(today.get('activated_today') or [])}): {today.get('activated_today')}")
    print(f"distortion_risk ({len(today.get('distortion_risk') or [])}): {today.get('distortion_risk')}")
    print(f"softens_field ({len(today.get('softens_field') or [])}): {today.get('softens_field')}")
    proof = today.get("proof_layer") or {}
    print(f"proof_layer.plain_english ({len(proof.get('plain_english') or [])}): {proof.get('plain_english')}")
    print(f"proof_layer.technical ({len(proof.get('technical') or [])}): {proof.get('technical')}")
    ok, errs = validate_envelope(today)
    if ok and body.get("success") is True:
        results["happy_path"] = ("PASS", None)
    else:
        results["happy_path"] = ("FAIL", f"success={body.get('success')} errors={errs}")
else:
    print(f"body: {resp.text[:500]}")
    results["happy_path"] = ("FAIL", f"status={resp.status_code}")

# ───── Test 2: Prose guard
section("TEST 2 — Top-level prose guard")
if today:
    parts = []
    if isinstance(today.get("hero"), str):
        parts.append(today["hero"])
    for k in ("activated_today", "distortion_risk", "softens_field"):
        v = today.get(k)
        if isinstance(v, list):
            for item in v:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    for f in ("text", "title", "label", "body"):
                        if isinstance(item.get(f), str):
                            parts.append(item[f])
    concatenated = " || ".join(parts)
    print(f"Concatenated top-level prose ({len(concatenated)} chars):")
    print(concatenated[:800])
    hits = banned_token_hits(concatenated)
    if hits:
        results["prose_guard"] = ("FAIL", f"banned tokens at top level: {hits}")
        print(f"  BANNED tokens: {hits}")
    else:
        results["prose_guard"] = ("PASS", None)
        print("  ✅ No banned tokens at top level")
else:
    results["prose_guard"] = ("FAIL", "no envelope from test 1")

# ───── Test 3: Cache hit
section("TEST 3 — Cache hit (call twice without refresh)")
resp2, elapsed2 = call_endpoint(FORUM_ID, ANCHOR_USER_ID, primary_member_id, refresh=False)
print(f"second call status={resp2.status_code} elapsed={elapsed2:.2f}s")
if resp2.status_code == 200 and today:
    body2 = resp2.json()
    today2 = body2.get("today") or {}
    same_hero = (today.get("hero") == today2.get("hero"))
    same_date = (today.get("date") == today2.get("date"))
    cache_hit_flag = today2.get("_cache_hit")
    print(f"same hero={same_hero}  same date={same_date}  _cache_hit={cache_hit_flag}")
    if same_hero and same_date:
        results["cache_hit"] = ("PASS", f"_cache_hit={cache_hit_flag}")
    else:
        print(f"hero1: {today.get('hero')[:200]}")
        print(f"hero2: {today2.get('hero')[:200]}")
        results["cache_hit"] = ("FAIL", f"hero_match={same_hero} date_match={same_date}")
else:
    results["cache_hit"] = ("FAIL", f"status={resp2.status_code}")

# ───── Test 4: Cache bypass refresh=true
section("TEST 4 — Cache bypass (refresh=true)")
resp3, elapsed3 = call_endpoint(FORUM_ID, ANCHOR_USER_ID, primary_member_id, refresh=True)
print(f"refresh call status={resp3.status_code} elapsed={elapsed3:.2f}s")
if resp3.status_code == 200:
    body3 = resp3.json()
    today3 = body3.get("today") or {}
    ok3, errs3 = validate_envelope(today3)
    print(f"envelope valid={ok3} errors={errs3}")
    if ok3 and body3.get("success") is True:
        results["cache_bypass"] = ("PASS", None)
    else:
        results["cache_bypass"] = ("FAIL", f"errors={errs3}")
else:
    print(f"body: {resp3.text[:500]}")
    results["cache_bypass"] = ("FAIL", f"status={resp3.status_code}")

# ───── Test 5: Unauthorized
section("TEST 5 — Unauthorized (user_id not a member)")
fake_user = "000000000000000000000001"
resp5, _ = call_endpoint(FORUM_ID, fake_user, primary_member_id, refresh=False, timeout=30)
print(f"status={resp5.status_code} body={resp5.text[:300]}")
if resp5.status_code == 403:
    results["unauthorized_403"] = ("PASS", None)
else:
    results["unauthorized_403"] = ("FAIL", f"expected 403, got {resp5.status_code}")

# ───── Test 6: Member not in forum
section("TEST 6 — Member not in forum")
fake_member = "000000000000000000000002"
resp6, _ = call_endpoint(FORUM_ID, ANCHOR_USER_ID, fake_member, refresh=False, timeout=30)
print(f"status={resp6.status_code} body={resp6.text[:300]}")
if resp6.status_code == 404:
    results["member_not_in_forum_404"] = ("PASS", None)
else:
    results["member_not_in_forum_404"] = ("FAIL", f"expected 404, got {resp6.status_code}")

# ───── Test 7: Invalid forum id
section("TEST 7 — Invalid forum id")
resp7, _ = call_endpoint("not-an-objectid", ANCHOR_USER_ID, primary_member_id, refresh=False, timeout=30)
print(f"status={resp7.status_code} body={resp7.text[:300]}")
if resp7.status_code == 400:
    results["invalid_forum_id_400"] = ("PASS", None)
else:
    results["invalid_forum_id_400"] = ("FAIL", f"expected 400, got {resp7.status_code}")

# ───── Test 8: Parallel members
section("TEST 8 — Parallel members (all from member-mappings)")
all_ok = True
details = []
for idx, mid in enumerate(member_ids[:3]):
    r, e = call_endpoint(FORUM_ID, ANCHOR_USER_ID, mid, refresh=False, timeout=120)
    if r.status_code != 200:
        all_ok = False
        details.append(f"  member {idx}={mid}: status={r.status_code} body={r.text[:200]}")
        continue
    b = r.json()
    t = b.get("today") or {}
    ok, errs = validate_envelope(t) if t else (False, ["no envelope"])
    if not (ok and b.get("success") and t):
        all_ok = False
    details.append(f"  member {idx}={mid}: status=200 success={b.get('success')} valid={ok} hero_len={len(str(t.get('hero','')))} intensity={t.get('intensity')}")
for d in details:
    print(d)
if all_ok and len(member_ids) >= 1:
    results["parallel_members"] = ("PASS", f"{len(member_ids[:3])} members all valid")
else:
    results["parallel_members"] = ("FAIL", "; ".join(details))

# ───── Summary
section("RESULTS SUMMARY")
passed = 0
failed = 0
for name, (status, detail) in results.items():
    marker = "PASS" if status == "PASS" else "FAIL"
    print(f"[{marker}] {name:30s}  {detail or ''}")
    if status == "PASS":
        passed += 1
    else:
        failed += 1
print(f"\nTOTAL: {passed} passed / {failed} failed")
