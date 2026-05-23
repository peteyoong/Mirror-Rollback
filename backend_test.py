"""
Backend test for Astrology Chat — Transit Grounding Fix V1
Build marker: astro-chat-transit-grounding-v1

Tests:
  A1-A7  Deterministic /api/astrology/transit-object endpoint
  B1-B5  Mirror chat transit-grounding integration
"""
from __future__ import annotations

import re
import subprocess
import time
from typing import Any, Dict, List, Optional, Tuple

import requests

BASE = "https://mapping-phase4.preview.emergentagent.com"
USER = "697f0c6abf35c0528ff06954"
TIMEOUT = 120

BANNED_PHRASES = [
    "themes around",
    "healing and vulnerability",
    "current life context",
    "might be useful to explore",
    "what feels tender",
]

results: List[Tuple[str, bool, str]] = []

def record(name: str, ok: bool, detail: str = ""):
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}: {detail[:400]}")
    results.append((name, ok, detail))

def get(path: str) -> requests.Response:
    return requests.get(f"{BASE}{path}", timeout=TIMEOUT)

def post(path: str, body: Dict[str, Any]) -> requests.Response:
    return requests.post(
        f"{BASE}{path}",
        json=body,
        headers={"Content-Type": "application/json"},
        timeout=TIMEOUT,
    )

def tail_backend_log(n: int = 400) -> str:
    try:
        out = subprocess.check_output(
            ["tail", "-n", str(n), "/var/log/supervisor/backend.out.log"],
            stderr=subprocess.STDOUT,
        ).decode("utf-8", errors="replace")
        err = subprocess.check_output(
            ["tail", "-n", str(n), "/var/log/supervisor/backend.err.log"],
            stderr=subprocess.STDOUT,
        ).decode("utf-8", errors="replace")
        return out + "\n" + err
    except Exception as e:
        return f"<log error: {e}>"


# =====================================================================
# A. DETERMINISTIC /transit-object ENDPOINT
# =====================================================================

print("\n=== A. DETERMINISTIC ENDPOINT ===\n")

# A1: Chiron
a1_env: Optional[Dict[str, Any]] = None
try:
    r = get(f"/api/astrology/transit-object/{USER}?object=Chiron")
    ok = r.status_code == 200
    j = r.json() if ok else {}
    a1_env = j
    cond = (
        ok
        and j.get("success") is True
        and j.get("data_mode") == "transit_object"
        and "transit_position" in j
        and "natal_house" in j
        and isinstance(j.get("aspects_to_natal"), list)
        and "proof" in j
        and j.get("zodiac_system") == "True Sidereal"
        and j.get("house_system") == "Equal"
    )
    sign = (j.get("transit_position") or {}).get("sign")
    record(
        "A1 Chiron",
        cond,
        f"status={r.status_code} success={j.get('success')} sign={sign} "
        f"zodiac={j.get('zodiac_system')} house_system={j.get('house_system')}",
    )
except Exception as e:
    record("A1 Chiron", False, f"exception: {e}")

# A2: Saturn
a2_env: Optional[Dict[str, Any]] = None
try:
    r = get(f"/api/astrology/transit-object/{USER}?object=Saturn")
    ok = r.status_code == 200
    j = r.json() if ok else {}
    a2_env = j
    cond = ok and j.get("success") is True and j.get("object") == "Saturn"
    sign = (j.get("transit_position") or {}).get("sign")
    record(
        "A2 Saturn",
        cond,
        f"status={r.status_code} success={j.get('success')} sign={sign} "
        f"natal_house={j.get('natal_house')}",
    )
except Exception as e:
    record("A2 Saturn", False, f"exception: {e}")

# A3: Juno -> object_not_yet_enabled
try:
    r = get(f"/api/astrology/transit-object/{USER}?object=Juno")
    ok = r.status_code == 200
    j = r.json() if ok else {}
    cond = (
        ok
        and j.get("success") is False
        and j.get("reason") == "object_not_yet_enabled"
    )
    record("A3 Juno -> object_not_yet_enabled", cond,
           f"status={r.status_code} success={j.get('success')} reason={j.get('reason')}")
except Exception as e:
    record("A3 Juno -> object_not_yet_enabled", False, f"exception: {e}")

# A4: Gobbledygook -> unknown_object
try:
    r = get(f"/api/astrology/transit-object/{USER}?object=Gobbledygook")
    ok = r.status_code == 200
    j = r.json() if ok else {}
    cond = ok and j.get("success") is False and j.get("reason") == "unknown_object"
    record("A4 Gobbledygook -> unknown_object", cond,
           f"status={r.status_code} success={j.get('success')} reason={j.get('reason')}")
except Exception as e:
    record("A4 Gobbledygook -> unknown_object", False, f"exception: {e}")

# A5: Non-existent user -> 404
try:
    r = get(f"/api/astrology/transit-object/000000000000000000000099?object=Chiron")
    cond = r.status_code == 404
    record("A5 Non-existent user -> 404", cond, f"status={r.status_code} body={r.text[:200]}")
except Exception as e:
    record("A5 Non-existent user -> 404", False, f"exception: {e}")

# A6: Chiron date=2026-12-01 differs from A1 by >0.1°
try:
    r = get(f"/api/astrology/transit-object/{USER}?object=Chiron&date=2026-12-01")
    ok = r.status_code == 200
    j = r.json() if ok else {}
    if ok and j.get("success") and a1_env and a1_env.get("success"):
        lon_now = a1_env["transit_position"]["absolute_longitude"]
        lon_dec = j["transit_position"]["absolute_longitude"]
        diff = abs(lon_now - lon_dec)
        if diff > 180:
            diff = 360 - diff
        cond = diff > 0.1
        record(
            "A6 Chiron 2026-12-01 differs from today",
            cond,
            f"lon_today={lon_now} lon_dec={lon_dec} diff={diff:.4f}",
        )
    else:
        record(
            "A6 Chiron 2026-12-01 differs from today",
            False,
            f"status={r.status_code} success={j.get('success')}",
        )
except Exception as e:
    record("A6 Chiron 2026-12-01 differs from today", False, f"exception: {e}")

# A7: Ascendant -> asc_mc_not_a_transit_body
try:
    r = get(f"/api/astrology/transit-object/{USER}?object=Ascendant")
    ok = r.status_code == 200
    j = r.json() if ok else {}
    cond = (
        ok
        and j.get("success") is False
        and j.get("reason") == "asc_mc_not_a_transit_body"
    )
    record("A7 Ascendant -> asc_mc_not_a_transit_body", cond,
           f"status={r.status_code} success={j.get('success')} reason={j.get('reason')}")
except Exception as e:
    record("A7 Ascendant -> asc_mc_not_a_transit_body", False, f"exception: {e}")


# =====================================================================
# B. MIRROR CHAT TRANSIT GROUNDING
# =====================================================================

print("\n=== B. MIRROR CHAT TRANSIT GROUNDING ===\n")

def mirror_chat(message: str, session_suffix: str) -> Tuple[Optional[Dict[str, Any]], int]:
    body = {
        "user_id": USER,
        "message": message,
        "lens": "astrology",
        "session_id": f"test-transit-{session_suffix}",
    }
    r = post("/api/mirror/chat", body)
    try:
        return r.json(), r.status_code
    except Exception:
        return {"raw": r.text}, r.status_code


def check_banned(text: str) -> List[str]:
    lt = (text or "").lower()
    return [p for p in BANNED_PHRASES if p in lt]


# B1: "Where is Chiron in my transit chart now?"
try:
    j, sc = mirror_chat("Where is Chiron in my transit chart now?", "1")
    resp = (j or {}).get("response", "") if isinstance(j, dict) else ""
    expected_sign = ((a1_env or {}).get("transit_position") or {}).get("sign")
    contains_sign = bool(expected_sign) and expected_sign.lower() in resp.lower()
    banned_hits = check_banned(resp)
    says_no_data = (
        "i don't have transit data" in resp.lower()
        or "i do not have transit data" in resp.lower()
    )
    time.sleep(1)
    log_now = tail_backend_log(1000)
    log_has_router = (
        "[TransitRouter] intent=transit_object" in log_now
        and "object=Chiron" in log_now
    )
    cond = (
        sc == 200
        and contains_sign
        and not banned_hits
        and not says_no_data
        and log_has_router
    )
    detail = (
        f"status={sc} expected_sign={expected_sign} contains_sign={contains_sign} "
        f"banned={banned_hits} says_no_data={says_no_data} "
        f"log_has_router={log_has_router}"
    )
    if not cond and resp:
        detail += f" | SNIPPET={resp[:400]!r}"
    record("B1 Chiron transit-now", cond, detail)
except Exception as e:
    record("B1 Chiron transit-now", False, f"exception: {e}")

# B2: "What house is Saturn transiting for me today?"
try:
    j, sc = mirror_chat("What house is Saturn transiting for me today?", "2")
    resp = (j or {}).get("response", "") if isinstance(j, dict) else ""
    expected_house = (a2_env or {}).get("natal_house") if a2_env else None
    nums_found = re.findall(r"\b([1-9]|1[0-2])(?:st|nd|rd|th)?\b", resp)
    has_house_num = bool(nums_found)
    has_expected = False
    if expected_house:
        ord_suffix = {1:"st",2:"nd",3:"rd"}.get(expected_house%10 if not (10 <= expected_house%100 <= 20) else 0, "th")
        has_expected = bool(re.search(rf"\b{expected_house}(?:st|nd|rd|th)?\b", resp))
    time.sleep(1)
    log_now = tail_backend_log(1000)
    log_has_router = (
        "[TransitRouter] intent=transit_object" in log_now
        and "object=Saturn" in log_now
    )
    cond = sc == 200 and has_house_num and log_has_router and has_expected
    detail = (
        f"status={sc} expected_house={expected_house} has_house_num={has_house_num} "
        f"has_expected={has_expected} log_has_router={log_has_router}"
    )
    if not cond and resp:
        detail += f" | SNIPPET={resp[:400]!r}"
    record("B2 Saturn transit-house", cond, detail)
except Exception as e:
    record("B2 Saturn transit-house", False, f"exception: {e}")

# B3: "Where is Juno now?"
try:
    j, sc = mirror_chat("Where is Juno now?", "3")
    resp = (j or {}).get("response", "") if isinstance(j, dict) else ""
    lt = resp.lower()
    politely_refuses = (
        "not yet enabled" in lt
        or "not enabled" in lt
        or "don't yet support" in lt
        or "do not yet support" in lt
        or "currently not supported" in lt
        or "not currently support" in lt
        or "can compute the" in lt  # the canned message includes this
    )
    cond = sc == 200 and politely_refuses
    detail = f"status={sc} politely_refuses={politely_refuses}"
    if not cond and resp:
        detail += f" | SNIPPET={resp[:400]!r}"
    record("B3 Juno not-yet-enabled refusal", cond, detail)
except Exception as e:
    record("B3 Juno not-yet-enabled refusal", False, f"exception: {e}")

# B4: "Where is my natal Chiron?"
try:
    log_pre = tail_backend_log(2000)
    pre_count = log_pre.count("[TransitRouter] intent=transit_object")

    j, sc = mirror_chat("Where is my natal Chiron?", "4")
    resp = (j or {}).get("response", "") if isinstance(j, dict) else ""
    lt = resp.lower()

    time.sleep(1)
    log_post = tail_backend_log(2000)
    post_count = log_post.count("[TransitRouter] intent=transit_object")
    fired_transit_object = post_count > pre_count
    fired_natal = "[TransitRouter] intent=natal_object" in log_post[len(log_pre):] if len(log_post) > len(log_pre) else "[TransitRouter] intent=natal_object" in log_post

    references_natal = "natal" in lt and "chiron" in lt
    cond = (
        sc == 200
        and references_natal
        and not fired_transit_object
    )
    detail = (
        f"status={sc} references_natal={references_natal} "
        f"fired_transit_object_router={fired_transit_object} "
        f"fired_natal_intent={fired_natal}"
    )
    if not cond and resp:
        detail += f" | SNIPPET={resp[:400]!r}"
    record("B4 Natal Chiron query", cond, detail)
except Exception as e:
    record("B4 Natal Chiron query", False, f"exception: {e}")

# B5: "Is Uranus aspecting my natal Sun?"
try:
    j, sc = mirror_chat("Is Uranus aspecting my natal Sun?", "5")
    resp = (j or {}).get("response", "") if isinstance(j, dict) else ""
    time.sleep(1)
    log_now = tail_backend_log(1200)
    log_has_router = (
        "[TransitRouter] intent=transit_to_natal" in log_now
        and "object=Uranus" in log_now
    )
    ur = get(f"/api/astrology/transit-object/{USER}?object=Uranus").json()
    ur_sign = (ur.get("transit_position") or {}).get("sign")
    contains_ur_sign = bool(ur_sign) and ur_sign.lower() in resp.lower()
    cond = sc == 200 and log_has_router and contains_ur_sign
    detail = (
        f"status={sc} log_has_router={log_has_router} "
        f"uranus_sign={ur_sign} contains_uranus_sign={contains_ur_sign}"
    )
    if not cond and resp:
        detail += f" | SNIPPET={resp[:400]!r}"
    record("B5 Uranus transit_to_natal Sun", cond, detail)
except Exception as e:
    record("B5 Uranus transit_to_natal Sun", False, f"exception: {e}")


# =====================================================================
# SUMMARY
# =====================================================================
print("\n=== SUMMARY ===")
passed = sum(1 for _, ok, _ in results if ok)
total = len(results)
print(f"{passed}/{total} passed")
for name, ok, detail in results:
    sym = "PASS" if ok else "FAIL"
    print(f"  [{sym}] {name}")
