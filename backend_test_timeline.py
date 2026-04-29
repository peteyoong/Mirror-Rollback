#!/usr/bin/env python3
"""
Backend tests for new Real Astrology Timeline wiring into Ask About My Life.
"""
import json
import time
import sys
import requests

BASE = "https://decan-tone.preview.emergentagent.com/api"
PETE = "697f0c6abf35c0528ff06954"
MEL = "697ec826ad4b18f75bf42616"

JARGON = ["planet", "house ", "transit", "decan", "ayanamsa", "natal chart",
          "purple star", "ziwei", "ascendant", "sun sign", "moon sign"]
STRUCT_TERMS = ["this period", "this year", "the period", "next phase",
                "crossroads", "improves", "remains under pressure",
                "pattern to watch"]


def call_life_ask(user_id, body, timeout=60):
    t0 = time.time()
    r = requests.post(f"{BASE}/life/ask/{user_id}", json=body, timeout=timeout)
    dt = time.time() - t0
    return r, dt


def report(name, status, dt, data, body=None):
    print(f"\n=== {name} ===")
    print(f"HTTP: {status} | duration: {dt:.2f}s")
    if status != 200:
        print(f"BODY: {data}")
        return None
    debug = data.get("debug", {}) or {}
    ckeys = debug.get("context_keys", {}) or {}
    intent = debug.get("intent", {}) or {}
    answer = data.get("answer") or data.get("response") or ""
    print(f"context_keys.has_timeline_context = {ckeys.get('has_timeline_context')}")
    print(f"context_keys.timeline_source = {ckeys.get('timeline_source')}")
    print(f"context_keys.timeline_confidence = {ckeys.get('timeline_confidence')}")
    print(f"intent = {json.dumps(intent)[:200]}")
    print(f"answer (first 200): {answer[:200]!r}")
    return {"ckeys": ckeys, "intent": intent, "answer": answer}


def has_jargon(answer):
    a = answer.lower()
    found = [j for j in JARGON if j in a]
    return found


def has_structural(answer):
    a = answer.lower()
    return [t for t in STRUCT_TERMS if t in a]


fails = []


def test2():
    body = {
        "domain": "relationships",
        "question": "What's my outlook for relationships this year? I feel it is getting better but my astrology timeline seems to say otherwise.",
    }
    r, dt = call_life_ask(PETE, body)
    try:
        data = r.json()
    except Exception:
        data = {"_raw": r.text}
    res = report("Test 2: Pete contradiction (REAL timeline)", r.status_code, dt, data, body)
    if r.status_code != 200 or not res:
        fails.append("Test2: HTTP non-200")
        return
    ck, intent, ans = res["ckeys"], res["intent"], res["answer"]
    if ck.get("has_timeline_context") is not True:
        fails.append(f"Test2: has_timeline_context expected True, got {ck.get('has_timeline_context')}")
    if ck.get("timeline_source") != "real_astrology_timeline":
        fails.append(f"Test2: timeline_source expected real_astrology_timeline, got {ck.get('timeline_source')}")
    if ck.get("timeline_confidence") != "high":
        fails.append(f"Test2: timeline_confidence expected high, got {ck.get('timeline_confidence')}")
    is_contra = intent.get("is_contradiction")
    if is_contra is None:
        # alt format
        is_contra = intent.get("primary") == "contradiction" or "contradiction" in (intent.get("all") or [])
    if not is_contra:
        fails.append(f"Test2: is_contradiction expected True, got {intent}")
    # chart-driven phase language
    chart_terms = ["communication", "emotional", "home", "pace", "timing"]
    found_chart = [t for t in chart_terms if t in ans.lower()]
    if not found_chart:
        fails.append(f"Test2: no chart-driven phase language found from {chart_terms}")
    else:
        print(f"  chart-driven terms found: {found_chart}")
    jargon_found = has_jargon(ans)
    if jargon_found:
        fails.append(f"Test2: jargon found: {jargon_found}")
    structural = has_structural(ans)
    if not structural:
        fails.append(f"Test2: no structural timing terms found")
    else:
        print(f"  structural terms: {structural}")
    return res


def test3():
    body = {"domain": "work", "question": "What is the outlook for my career this year?"}
    r, dt = call_life_ask(PETE, body)
    try:
        data = r.json()
    except Exception:
        data = {"_raw": r.text}
    res = report("Test 3: Pete career outlook", r.status_code, dt, data, body)
    if r.status_code != 200 or not res:
        fails.append("Test3: HTTP non-200")
        return
    ck = res["ckeys"]
    if ck.get("timeline_source") != "real_astrology_timeline":
        fails.append(f"Test3: timeline_source expected real_astrology_timeline, got {ck.get('timeline_source')}")
    if ck.get("timeline_confidence") != "high":
        fails.append(f"Test3: timeline_confidence expected high, got {ck.get('timeline_confidence')}")
    jargon_found = has_jargon(res["answer"])
    if jargon_found:
        fails.append(f"Test3: jargon found: {jargon_found}")


def test4():
    body = {"domain": "self", "question": "Why do I keep falling into the same trap?"}
    r, dt = call_life_ask(PETE, body)
    try:
        data = r.json()
    except Exception:
        data = {"_raw": r.text}
    res = report("Test 4: Generic non-timeline", r.status_code, dt, data, body)
    if r.status_code != 200 or not res:
        fails.append("Test4: HTTP non-200")
        return
    ck = res["ckeys"]
    if ck.get("has_timeline_context") is not False:
        fails.append(f"Test4: has_timeline_context expected False, got {ck.get('has_timeline_context')}")
    if ck.get("timeline_source") != "none":
        fails.append(f"Test4: timeline_source expected none, got {ck.get('timeline_source')}")
    if not res["answer"] or len(res["answer"]) < 20:
        fails.append("Test4: empty or too-short answer")


def test5():
    body = {"domain": "relationships", "question": "What's my outlook this year?"}
    r, dt = call_life_ask(MEL, body)
    try:
        data = r.json()
    except Exception:
        data = {"_raw": r.text}
    res = report("Test 5: Mel cold-start", r.status_code, dt, data, body)
    if r.status_code != 200 or not res:
        fails.append("Test5: HTTP non-200")
        return
    ck = res["ckeys"]
    if ck.get("has_timeline_context") is not True:
        fails.append(f"Test5: has_timeline_context expected True, got {ck.get('has_timeline_context')}")
    src = ck.get("timeline_source")
    if src not in ("real_astrology_timeline", "deterministic_scaffold"):
        fails.append(f"Test5: timeline_source expected real_astrology_timeline or deterministic_scaffold, got {src}")


def test6():
    body = {
        "domain": "relationships",
        "question": "What's my outlook for relationships this year? I feel it is getting better but my astrology timeline seems to say otherwise.",
    }
    r1, dt1 = call_life_ask(PETE, body)
    try:
        d1 = r1.json()
    except Exception:
        d1 = {}
    r2, dt2 = call_life_ask(PETE, body)
    try:
        d2 = r2.json()
    except Exception:
        d2 = {}
    print(f"\n=== Test 6: Cache sanity ===")
    print(f"Call1: {r1.status_code} {dt1:.2f}s | Call2: {r2.status_code} {dt2:.2f}s")
    if r1.status_code != 200 or r2.status_code != 200:
        fails.append("Test6: non-200")
        return
    src1 = d1.get("debug", {}).get("context_keys", {}).get("timeline_source")
    src2 = d2.get("debug", {}).get("context_keys", {}).get("timeline_source")
    print(f"src1={src1} src2={src2}")
    if src1 != "real_astrology_timeline" or src2 != "real_astrology_timeline":
        fails.append(f"Test6: timeline_source not real both times: {src1} {src2}")
    if dt2 > 15:
        fails.append(f"Test6: 2nd call too slow ({dt2:.2f}s)")


def test7():
    print(f"\n=== Test 7: HD Incarnation Cross deep-dive regression ===")
    t0 = time.time()
    r = requests.get(f"{BASE}/human-design/deep-dive/{PETE}", timeout=60)
    dt = time.time() - t0
    print(f"HTTP: {r.status_code} | {dt:.2f}s")
    if r.status_code != 200:
        fails.append(f"Test7: status {r.status_code}")
        return
    data = r.json()
    cm = data.get("core_mechanics", {}) or {}
    ic = cm.get("incarnation_cross")
    icg = cm.get("incarnation_cross_gates")
    print(f"core_mechanics.incarnation_cross = {ic!r}")
    print(f"core_mechanics.incarnation_cross_gates = {icg!r}")
    if ic != "Left Angle Cross of Migration":
        fails.append(f"Test7: incarnation_cross expected Left Angle Cross of Migration, got {ic!r}")
    if icg != "Gates: 37 · 5 · 40 · 35":
        fails.append(f"Test7: incarnation_cross_gates expected 'Gates: 37 · 5 · 40 · 35', got {icg!r}")
    structured = data.get("incarnation_cross_structured") or cm.get("incarnation_cross_structured")
    print(f"incarnation_cross_structured = {json.dumps(structured)[:300] if structured else None}")
    if not structured or structured.get("cross_name") != "Left Angle Cross of Migration":
        fails.append(f"Test7: structured cross_name mismatch: {structured}")
    if structured and "variant" in structured:
        fails.append(f"Test7: 'variant' key should NOT be in structured")


if __name__ == "__main__":
    print(f"Testing against {BASE}")
    test2()
    test3()
    test4()
    test5()
    test6()
    test7()
    print("\n\n========== SUMMARY ==========")
    if fails:
        print(f"FAILURES ({len(fails)}):")
        for f in fails:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("ALL TESTS PASSED")
