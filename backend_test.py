"""
Backend test for emotional-timing-v1 (conversational intensity) on
POST /api/mirror/chat for user Pete (697f0c6abf35c0528ff06954).

Runs the 10 test scenarios from the review request and reports:
- HTTP status
- debug.intensity_mode / intensity_marker / lens_intensity_ceiling
- debug.depth_mode (sanity)
- Response text (full)
- PASS / FAIL per scenario
"""

import json
import os
import sys
import time
import uuid
import requests

BACKEND_URL = "https://individual-maps-v1.preview.emergentagent.com"
API = f"{BACKEND_URL}/api"
USER_ID = "697f0c6abf35c0528ff06954"
TIMEOUT = 120

results = []


def chat(message, lens, session_id=None, include_journal=True, include_history=True):
    payload = {
        "user_id": USER_ID,
        "message": message,
        "include_journal": include_journal,
        "include_history": include_history,
    }
    if lens is not None:
        payload["lens"] = lens
    if session_id is not None:
        payload["session_id"] = session_id
    t0 = time.time()
    r = requests.post(f"{API}/mirror/chat", json=payload, timeout=TIMEOUT)
    dt = time.time() - t0
    try:
        data = r.json()
    except Exception:
        data = {"_raw": r.text}
    return r.status_code, data, dt


def summarize(name, status, data, dt, expected_mode, expected_ceiling=None,
              expected_marker="emotional-timing-v1", expect_debug_null=False,
              extra_checks=None):
    debug = data.get("debug") if isinstance(data, dict) else None
    resp_text = data.get("response", "") if isinstance(data, dict) else ""
    print(f"\n{'='*80}\n{name}  ({dt:.1f}s)  HTTP {status}\n{'='*80}")

    if expect_debug_null:
        ok = (status == 200) and (debug is None)
        print(f"debug == None? {debug is None}")
        print(f"Response (first 300 chars):\n{resp_text[:300]}")
        verdict = "PASS" if ok else "FAIL"
        rationale = "debug is None as expected" if ok else f"debug should be None, got: {debug}"
        results.append((name, verdict, rationale))
        print(f"VERDICT: {verdict} — {rationale}")
        return debug, resp_text

    if not isinstance(debug, dict):
        verdict = "FAIL"
        rationale = f"debug missing or not dict: {debug}"
        results.append((name, verdict, rationale))
        print(f"VERDICT: {verdict} — {rationale}")
        print(f"Raw response keys: {list(data.keys()) if isinstance(data, dict) else 'n/a'}")
        print(f"Response: {resp_text[:400]}")
        return debug, resp_text

    intensity_mode = debug.get("intensity_mode")
    intensity_marker = debug.get("intensity_marker")
    lens_intensity_ceiling = debug.get("lens_intensity_ceiling")
    depth_mode = debug.get("depth_mode")

    print(f"intensity_mode           = {intensity_mode}")
    print(f"intensity_marker         = {intensity_marker}")
    print(f"lens_intensity_ceiling   = {lens_intensity_ceiling}")
    print(f"depth_mode (sanity)      = {depth_mode}")
    print(f"\nResponse:\n{resp_text}\n")

    checks = []
    checks.append(("HTTP 200", status == 200))
    checks.append((f"intensity_mode == {expected_mode}", intensity_mode == expected_mode))
    checks.append((f"intensity_marker == {expected_marker}", intensity_marker == expected_marker))
    if expected_ceiling:
        checks.append((f"lens_intensity_ceiling == {expected_ceiling}",
                       lens_intensity_ceiling == expected_ceiling))
    if extra_checks:
        for label, fn in extra_checks:
            try:
                checks.append((label, bool(fn(resp_text, debug))))
            except Exception:
                checks.append((label, False))

    all_ok = all(ok for _, ok in checks)
    for label, ok in checks:
        print(f"  [{'OK' if ok else 'FAIL'}] {label}")
    verdict = "PASS" if all_ok else "FAIL"
    rationale = "; ".join(f"{lbl}={'OK' if ok else 'FAIL'}" for lbl, ok in checks)
    results.append((name, verdict, rationale))
    print(f"VERDICT: {verdict}")
    return debug, resp_text


def main():
    # ---------- I1 SOFT detection (astrology, vulnerability) ----------
    msg = ("I'm completely lost. My partner left me yesterday and I can't stop crying. "
           "What does my chart say about why this keeps happening to me?")
    status, data, dt = chat(msg, lens="astrology", session_id=str(uuid.uuid4()))
    def i1_no_shadow_phrases(text, debug):
        bad = ["the pattern here is", "what you're avoiding", "what you are avoiding"]
        return not any(b.lower() in text.lower() for b in bad)
    summarize("I1 SOFT — vulnerability wins (astrology)", status, data, dt,
              expected_mode="SOFT", expected_ceiling="DIRECT",
              extra_checks=[("no harsh shadow phrases", i1_no_shadow_phrases)])

    # ---------- I2 SOFT beats DIRECT (enneagram) ----------
    msg = "I feel broken. Please be honest with me — what am I doing wrong?"
    status, data, dt = chat(msg, lens="enneagram", session_id=str(uuid.uuid4()))
    def i2_no_shadow(text, debug):
        bad = ["the pattern here is", "what you're avoiding", "shadow"]
        return not any(b.lower() in text.lower() for b in bad)
    summarize("I2 SOFT beats DIRECT (enneagram, vulnerable + be honest)", status, data, dt,
              expected_mode="SOFT", expected_ceiling="CONFRONTING",
              extra_checks=[("gentler — avoid harsh pattern/shadow naming", i2_no_shadow)])

    # ---------- I3 DIRECT (astrology, explicit invitation) ----------
    msg = "Be honest with me. What am I avoiding in my Saturn placement?"
    status, data, dt = chat(msg, lens="astrology", session_id=str(uuid.uuid4()))
    summarize("I3 DIRECT — explicit invitation (astrology)", status, data, dt,
              expected_mode="DIRECT", expected_ceiling="DIRECT")

    # ---------- I4 CONFRONTING — Enneagram with prior probing (3 turns same session) ----------
    sid = str(uuid.uuid4())
    print(f"\n--- I4 session_id: {sid} ---")
    status1, data1, dt1 = chat("What is my Enneagram type and what is its core fear?",
                                lens="enneagram", session_id=sid)
    summarize("I4.1 OBSERVATIONAL — Enneagram intro question", status1, data1, dt1,
              expected_mode="OBSERVATIONAL", expected_ceiling="CONFRONTING")

    status2, data2, dt2 = chat("Be honest with me — what am I really avoiding?",
                                lens="enneagram", session_id=sid)
    summarize("I4.2 DIRECT — probing follow-up", status2, data2, dt2,
              expected_mode="DIRECT", expected_ceiling="CONFRONTING")

    status3, data3, dt3 = chat("Challenge me. Don't hold back. What do I need to hear?",
                                lens="enneagram", session_id=sid)
    summarize("I4.3 CONFRONTING — Enneagram earned after prior probing",
              status3, data3, dt3,
              expected_mode="CONFRONTING", expected_ceiling="CONFRONTING")

    # ---------- I5 CONFRONTING earn-the-ramp (Enneagram, no prior probing) ----------
    msg = "Challenge me. Don't hold back."
    status, data, dt = chat(msg, lens="enneagram", session_id=str(uuid.uuid4()))
    summarize("I5 Earn-the-ramp — Enneagram CONFRONTING without prior probing → DIRECT",
              status, data, dt,
              expected_mode="DIRECT", expected_ceiling="CONFRONTING")

    # ---------- I6 Astrology ceiling — caps at DIRECT ----------
    sid = str(uuid.uuid4())
    print(f"\n--- I6 session_id: {sid} ---")
    status6a, data6a, dt6a = chat("be honest with me about my chart",
                                   lens="astrology", session_id=sid)
    summarize("I6.1 DIRECT — astrology probing", status6a, data6a, dt6a,
              expected_mode="DIRECT", expected_ceiling="DIRECT")

    status6b, data6b, dt6b = chat("Challenge me. Don't hold back.",
                                   lens="astrology", session_id=sid)
    summarize("I6.2 Astrology ceiling cap — CONFRONTING invitation → DIRECT",
              status6b, data6b, dt6b,
              expected_mode="DIRECT", expected_ceiling="DIRECT")

    # ---------- I7 BaZi reaches CONFRONTING ----------
    sid = str(uuid.uuid4())
    print(f"\n--- I7 session_id: {sid} ---")
    status7a, data7a, dt7a = chat("be real with me about my Day Master",
                                   lens="bazi", session_id=sid)
    summarize("I7.1 DIRECT — bazi probing", status7a, data7a, dt7a,
              expected_mode="DIRECT", expected_ceiling="CONFRONTING")

    status7b, data7b, dt7b = chat("Hit me with it. What am I missing?",
                                   lens="bazi", session_id=sid)
    summarize("I7.2 BaZi CONFRONTING", status7b, data7b, dt7b,
              expected_mode="CONFRONTING", expected_ceiling="CONFRONTING")

    # ---------- I8 Momentum — 2+ probing turns moves floor to DIRECT ----------
    sid = str(uuid.uuid4())
    print(f"\n--- I8 session_id: {sid} ---")
    status8a, data8a, dt8a = chat("be honest with me", lens="astrology", session_id=sid)
    summarize("I8.1 DIRECT — astrology probing #1", status8a, data8a, dt8a,
              expected_mode="DIRECT", expected_ceiling="DIRECT")
    status8b, data8b, dt8b = chat("what am I avoiding?", lens="astrology", session_id=sid)
    summarize("I8.2 DIRECT — astrology probing #2", status8b, data8b, dt8b,
              expected_mode="DIRECT", expected_ceiling="DIRECT")
    status8c, data8c, dt8c = chat("What about my Saturn placement?",
                                   lens="astrology", session_id=sid)
    summarize("I8.3 Momentum — neutral msg but momentum keeps DIRECT floor",
              status8c, data8c, dt8c,
              expected_mode="DIRECT", expected_ceiling="DIRECT")

    # ---------- I9 Default OBSERVATIONAL ----------
    msg = "What does my Saturn mean?"
    status, data, dt = chat(msg, lens="astrology", session_id=str(uuid.uuid4()))
    summarize("I9 Default OBSERVATIONAL (astrology)", status, data, dt,
              expected_mode="OBSERVATIONAL", expected_ceiling="DIRECT")

    # ---------- I10 Generalist regression (lens=None) ----------
    msg = "be honest with me, what am I avoiding?"
    status, data, dt = chat(msg, lens=None, session_id=str(uuid.uuid4()))
    summarize("I10 Generalist regression — debug should be None",
              status, data, dt,
              expected_mode=None, expect_debug_null=True)

    # ---------- Final summary ----------
    print(f"\n\n{'#'*80}\nFINAL SUMMARY\n{'#'*80}")
    p = sum(1 for _, v, _ in results if v == "PASS")
    f = sum(1 for _, v, _ in results if v == "FAIL")
    for name, verdict, rationale in results:
        mark = "PASS" if verdict == "PASS" else "FAIL"
        print(f"[{mark}] {name}  →  {rationale}")
    print(f"\nTOTAL: {p} PASS / {f} FAIL  (of {len(results)})")


if __name__ == "__main__":
    main()
