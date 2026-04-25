"""
Backend tests for "Ask About My Life — Follow-ups + Reflect CTA".

Tests:
1. POST /api/life/ask/{user_id} — verify follow-ups in response
2. Validation paths (400/400/404)
3. POST /api/reflections — verify ask_reflect source
"""

import os
import re
import json
import sys
import time
from typing import Any, Dict, List, Tuple

import requests

# ---- Config -----------------------------------------------------------------

BASE_URL = "https://reflect-loop-upgrade.preview.emergentagent.com/api"
TIMEOUT = 60

PETE  = "697f0c6abf35c0528ff06954"
MEL   = "697ec826ad4b18f75bf42616"
ISAAC = "69dda348de9cb1c83c0780f8"

BANNED_PHRASES = [
    "human design", "bazi", "astrology", "horoscope", "natal chart",
    "transit", "retrograde", "purple star", "ziwei", "lifeline",
    "pattern memory", "domain weight", "primary domain", "secondary domain",
    "background domain", "system", "the engine", "framework",
    "as an ai", "language model",
]

DOMAIN_KEYWORDS = {
    "money":   ["money", "finance", "financial", "income", "pay", "earn", "earning", "spend", "spending"],
    "family":  ["family", "parent", "parents", "mother", "father", "sibling", "household"],
    "health":  ["body", "energy", "health", "sleep", "stress", "tired"],
    "friends": ["friend", "friendship", "friendships"],
}

# ---- Helpers ----------------------------------------------------------------

PASS: List[str] = []
FAIL: List[Tuple[str, str]] = []

def _log_pass(name: str, info: str = ""):
    print(f"  PASS: {name} {info}".rstrip())
    PASS.append(name)

def _log_fail(name: str, info: str = ""):
    print(f"  FAIL: {name} -- {info}")
    FAIL.append((name, info))

def _check(cond: bool, name: str, info: str = "") -> bool:
    if cond:
        _log_pass(name)
    else:
        _log_fail(name, info)
    return cond


def assert_paragraphs(answer: str) -> Tuple[bool, str]:
    if not isinstance(answer, str) or not answer.strip():
        return False, "answer empty or non-string"
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", answer.strip()) if p.strip()]
    if not (2 <= len(paragraphs) <= 4):
        return False, f"paragraph count = {len(paragraphs)} (need 2-4)"
    return True, f"{len(paragraphs)} paragraphs"


def assert_follow_ups(follow_ups: Any) -> Tuple[bool, str]:
    if not isinstance(follow_ups, list):
        return False, f"follow_ups not list: {type(follow_ups)}"
    if not (2 <= len(follow_ups) <= 3):
        return False, f"follow_ups length = {len(follow_ups)} (need 2-3)"
    for i, f in enumerate(follow_ups):
        if not isinstance(f, str):
            return False, f"follow_ups[{i}] not string"
        if not (4 <= len(f) <= 140):
            return False, f"follow_ups[{i}] length = {len(f)} (need 4-140): {f!r}"
        if not f.endswith(("?", ".", "!")):
            return False, f"follow_ups[{i}] does not end with ?,.,!: {f!r}"
    return True, f"{len(follow_ups)} follow-ups"


def find_banned(text: str) -> List[str]:
    if not text:
        return []
    lc = text.lower()
    hits = []
    for phrase in BANNED_PHRASES:
        if phrase in lc:
            hits.append(phrase)
    return hits


def domain_specificity(chip: str, answer: str, follow_ups: List[str]) -> Tuple[bool, str]:
    keywords = DOMAIN_KEYWORDS.get(chip)
    if not keywords:
        return True, "no specificity check for this chip"
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", answer or "") if p.strip()]
    found_in_answer = any(any(kw in p.lower() for kw in keywords) for p in paragraphs)
    found_in_followups = any(any(kw in (f or "").lower() for kw in keywords) for f in (follow_ups or []))
    if found_in_answer or found_in_followups:
        loc = "answer" if found_in_answer else "follow_ups"
        return True, f"matched keyword in {loc}"
    return False, f"no keyword from {keywords} in answer or follow_ups"


# ---- Test cases -------------------------------------------------------------

def test_life_ask(user_id: str, chip: str, question: str, label: str) -> Dict[str, Any]:
    print(f"\n--- TEST: {label} | user={user_id[:8]}.. | chip={chip} ---")
    url = f"{BASE_URL}/life/ask/{user_id}"
    body = {"domain": chip, "question": question}
    t0 = time.time()
    try:
        r = requests.post(url, json=body, timeout=TIMEOUT)
    except requests.RequestException as e:
        _log_fail(f"{label} request error", str(e))
        return {}
    dur = time.time() - t0

    if not _check(r.status_code == 200, f"{label} status 200",
                  f"got {r.status_code}, body={r.text[:300]}"):
        return {}

    try:
        data = r.json()
    except Exception as e:
        _log_fail(f"{label} JSON parse", str(e))
        return {}

    _check(isinstance(data, dict), f"{label} response is dict")

    answer = data.get("answer")
    ok, info = assert_paragraphs(answer)
    _check(ok, f"{label} answer 2-4 paragraphs", info)

    follow_ups = data.get("follow_ups")
    ok, info = assert_follow_ups(follow_ups)
    _check(ok, f"{label} follow_ups well-formed", info)

    _check(data.get("chip_domain") == chip, f"{label} chip_domain matches",
           f"got {data.get('chip_domain')}")

    _check(data.get("synthesis_domain") in ("self", "work", "relationships"),
           f"{label} synthesis_domain valid",
           f"got {data.get('synthesis_domain')}")

    _check(data.get("generator_version") == "life_interpreter_v2",
           f"{label} generator_version",
           f"got {data.get('generator_version')}")

    debug = data.get("debug")
    _check(isinstance(debug, dict) and "context_keys" in debug,
           f"{label} debug.context_keys present",
           f"debug={debug}")

    combined = (answer or "") + "\n" + "\n".join(follow_ups or [])
    hits = find_banned(combined)
    _check(len(hits) == 0, f"{label} no banned phrases", f"hits={hits}")

    ok, info = domain_specificity(chip, answer or "", follow_ups or [])
    _check(ok, f"{label} domain-specificity ({chip})", info)

    print(f"   (took {dur:.1f}s, llm_used={debug.get('llm_used') if isinstance(debug, dict) else '?'}, "
          f"parse_error={debug.get('parse_error') if isinstance(debug, dict) else '?'})")
    print(f"   answer preview: {(answer or '')[:160]!r}")
    print(f"   follow_ups: {follow_ups}")
    return data


def test_validation():
    print("\n--- TEST: VALIDATION PATHS ---")
    r = requests.post(f"{BASE_URL}/life/ask/{PETE}",
                      json={"domain": "unknown", "question": "x"}, timeout=TIMEOUT)
    _check(r.status_code == 400, "invalid chip -> 400", f"got {r.status_code}, body={r.text[:200]}")

    r = requests.post(f"{BASE_URL}/life/ask/{PETE}",
                      json={"domain": "self", "question": ""}, timeout=TIMEOUT)
    _check(r.status_code == 400, "empty question -> 400", f"got {r.status_code}, body={r.text[:200]}")

    r = requests.post(f"{BASE_URL}/life/ask/nonexistent_user",
                      json={"domain": "self", "question": "why?"}, timeout=TIMEOUT)
    _check(r.status_code == 404, "nonexistent user -> 404", f"got {r.status_code}, body={r.text[:200]}")


def test_reflections_ask_reflect():
    print("\n--- TEST: POST /api/reflections (source=ask_reflect) + GET ---")
    body = {
        "user_id": PETE,
        "text": "This pattern of pulling back when I'm overwhelmed shows up everywhere.",
        "domain": "self",
        "source": "ask_reflect",
        "phase_label": "Building",
        "pattern_hint": "Why do I keep pulling away from people lately?",
    }
    r = requests.post(f"{BASE_URL}/reflections", json=body, timeout=TIMEOUT)
    if not _check(r.status_code == 200, "POST /reflections status 200",
                  f"got {r.status_code}, body={r.text[:300]}"):
        return
    try:
        doc = r.json()
    except Exception as e:
        _log_fail("POST /reflections JSON parse", str(e))
        return

    _check(doc.get("source") == "ask_reflect", "stored doc.source == ask_reflect",
           f"got {doc.get('source')}")
    _check(doc.get("user_id") == PETE, "stored doc.user_id matches")
    _check(doc.get("domain") == "self", "stored doc.domain == self")
    _check(doc.get("phase_label") == "Building", "stored doc.phase_label preserved")
    _check((doc.get("pattern_hint") or "").startswith("Why do I keep pulling"),
           "stored doc.pattern_hint preserved")
    reflection_id = doc.get("id")
    _check(bool(reflection_id), "stored doc.id present")

    r = requests.get(f"{BASE_URL}/reflections/{PETE}", timeout=TIMEOUT)
    if not _check(r.status_code == 200, "GET /reflections status 200",
                  f"got {r.status_code}"):
        return
    listing = r.json()
    items = listing.get("reflections") or []
    found = any(x.get("id") == reflection_id and x.get("source") == "ask_reflect"
                for x in items)
    _check(found, "new reflection appears in GET list with source=ask_reflect",
           f"id={reflection_id}, list_count={len(items)}")


# ---- Main -------------------------------------------------------------------

def main():
    print(f"Backend URL: {BASE_URL}")
    print(f"Timeout: {TIMEOUT}s")

    pete_cases = [
        ("self",          "Why do I keep pulling away from people lately?"),
        ("work",          "Why am I dragging my feet at work?"),
        ("money",         "Why am I always anxious about money lately?"),
        ("relationships", "Why does the same friction keep showing up in my relationships?"),
        ("health",        "Why does my body feel tired all the time?"),
        ("friends",       "Why do my friendships feel distant right now?"),
        ("family",        "Why does my family situation keep weighing on me?"),
    ]
    for chip, q in pete_cases:
        test_life_ask(PETE, chip, q, f"Pete-{chip}")

    test_life_ask(MEL,   "money", "Why am I always anxious about money lately?", "Mel-money")
    test_life_ask(ISAAC, "money", "Why am I always anxious about money lately?", "Isaac-money")

    test_validation()
    test_reflections_ask_reflect()

    print("\n" + "=" * 70)
    print(f"RESULTS: {len(PASS)} passed, {len(FAIL)} failed")
    if FAIL:
        print("\nFAILURES:")
        for name, info in FAIL:
            print(f"  - {name}: {info}")
    print("=" * 70)
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
