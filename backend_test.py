"""Integration test for Astrology Timeline Interpreter wiring into /api/life/ask/{user_id}."""
import json
import time
import requests

BASE = "https://decan-tone.preview.emergentagent.com/api"
PETE = "697f0c6abf35c0528ff06954"
MEL = "697ec826ad4b18f75bf42616"

JARGON = ["planet", "house", "transit", "decan", "ayanamsa", "natal chart", "purple star", "ziwei"]
TIMELINE_PHRASES = ["this year", "this period", "the period", "improves", "remains under pressure",
                    "pattern to watch", "crossroads", "this stretch"]


def post(user_id, body, label):
    print(f"\n=== {label} ===")
    url = f"{BASE}/life/ask/{user_id}"
    print(f"POST {url}\nBody: {json.dumps(body)}")
    t0 = time.time()
    try:
        r = requests.post(url, json=body, timeout=120)
    except Exception as e:
        print(f"REQUEST FAILED: {e}")
        return None
    dur = time.time() - t0
    print(f"HTTP {r.status_code} in {dur:.2f}s")
    try:
        data = r.json()
    except Exception:
        print("Non-JSON response:")
        print(r.text[:500])
        return {"_status": r.status_code, "_raw": r.text}
    data["_status"] = r.status_code
    return data


def check_jargon(answer):
    a = (answer or "").lower()
    return [j for j in JARGON if j in a]


def check_timeline_phrases(answer):
    a = (answer or "").lower()
    return [p for p in TIMELINE_PHRASES if p in a]


def report_intent_and_keys(label, data):
    debug = data.get("debug", {}) or {}
    intent = debug.get("intent", {}) or {}
    ck = debug.get("context_keys", {}) or {}
    print(f"--- {label} debug ---")
    print(f"intent: {json.dumps(intent, default=str)}")
    print(f"context_keys: {json.dumps(ck, default=str)}")
    return intent, ck


results = {}

# ---------- TEST 1 ----------
body1 = {
    "domain": "relationships",
    "question": "What's my outlook for relationships this year? I feel it is getting better but my astrology timeline seems to say otherwise.",
}
r1 = post(PETE, body1, "TEST 1: Pete contradiction (relationships)")
if r1:
    intent1, ck1 = report_intent_and_keys("TEST 1", r1)
    answer1 = r1.get("answer", "") or ""
    print(f"answer (first 200): {answer1[:200]}")
    paragraphs1 = [p for p in answer1.split("\n\n") if p.strip()]
    jargon1 = check_jargon(answer1)
    phrases1 = check_timeline_phrases(answer1)
    results["test1"] = {
        "status": r1.get("_status"),
        "has_timeline_context": ck1.get("has_timeline_context"),
        "primary": intent1.get("primary"),
        "is_contradiction": intent1.get("is_contradiction"),
        "is_outlook_timing": intent1.get("is_outlook_timing"),
        "answer_len": len(answer1),
        "paragraphs": len(paragraphs1),
        "jargon_found": jargon1,
        "timeline_phrases_found": phrases1,
        "answer_first_200": answer1[:200],
    }
else:
    results["test1"] = {"error": "request failed"}

# ---------- TEST 2 ----------
body2 = {"domain": "work", "question": "What is the outlook for my career this year?"}
r2 = post(PETE, body2, "TEST 2: Pete outlook (career)")
if r2:
    intent2, ck2 = report_intent_and_keys("TEST 2", r2)
    answer2 = r2.get("answer", "") or ""
    print(f"answer (first 200): {answer2[:200]}")
    jargon2 = check_jargon(answer2)
    results["test2"] = {
        "status": r2.get("_status"),
        "has_timeline_context": ck2.get("has_timeline_context"),
        "is_outlook_timing": intent2.get("is_outlook_timing"),
        "is_contradiction": intent2.get("is_contradiction"),
        "primary": intent2.get("primary"),
        "answer_len": len(answer2),
        "jargon_found": jargon2,
    }
else:
    results["test2"] = {"error": "request failed"}

# ---------- TEST 3 ----------
body3 = {"domain": "self", "question": "Why do I feel stuck right now?"}
r3 = post(PETE, body3, "TEST 3: Pete generic (self)")
if r3:
    intent3, ck3 = report_intent_and_keys("TEST 3", r3)
    answer3 = r3.get("answer", "") or ""
    print(f"answer (first 200): {answer3[:200]}")
    results["test3"] = {
        "status": r3.get("_status"),
        "has_timeline_context": ck3.get("has_timeline_context"),
        "is_outlook_timing": intent3.get("is_outlook_timing"),
        "is_contradiction": intent3.get("is_contradiction"),
        "primary": intent3.get("primary"),
        "answer_len": len(answer3),
        "answer_nonempty": bool(answer3.strip()),
    }
else:
    results["test3"] = {"error": "request failed"}

# ---------- TEST 4 ----------
body4 = {"domain": "relationships", "question": "What's my outlook for relationships this year?"}
r4 = post(MEL, body4, "TEST 4: Mel cold-start")
if r4:
    intent4, ck4 = report_intent_and_keys("TEST 4", r4)
    answer4 = r4.get("answer", "") or ""
    print(f"answer (first 200): {answer4[:200]}")
    results["test4"] = {
        "status": r4.get("_status"),
        "has_timeline_context": ck4.get("has_timeline_context"),
        "answer_nonempty": bool(answer4.strip()),
        "answer_len": len(answer4),
    }
else:
    results["test4"] = {"error": "request failed"}

# ---------- TEST 6 ----------
print("\n=== TEST 6: HD Incarnation Cross deep-dive ===")
url6 = f"{BASE}/human-design/deep-dive/{PETE}"
print(f"GET {url6}")
t0 = time.time()
try:
    r6 = requests.get(url6, timeout=120)
    dur = time.time() - t0
    print(f"HTTP {r6.status_code} in {dur:.2f}s")
    data6 = r6.json()
    cm = data6.get("core_mechanics", {}) or {}
    ics = data6.get("incarnation_cross_structured", {}) or {}
    results["test6"] = {
        "status": r6.status_code,
        "core_mechanics.incarnation_cross": cm.get("incarnation_cross"),
        "core_mechanics.incarnation_cross_gates": cm.get("incarnation_cross_gates"),
        "ics.cross_name": ics.get("cross_name"),
        "ics.gates_display": ics.get("gates_display"),
        "ics_has_variant": "variant" in ics,
        "ics_keys": list(ics.keys()),
    }
except Exception as e:
    results["test6"] = {"error": str(e)}

print("\n\n========== SUMMARY ==========")
print(json.dumps(results, indent=2, default=str))
