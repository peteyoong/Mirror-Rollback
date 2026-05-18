"""
Lens Voice Differentiation V1 test (lens-voice-differentiation-v1)
Tests POST /api/mirror/chat for user Pete (697f0c6abf35c0528ff06954).
"""

import json
import os
import sys
import time
import uuid
from typing import Any, Dict, Optional, List, Tuple

import requests

BASE_URL = os.environ.get(
    "BACKEND_URL",
    "https://individual-maps-v1.preview.emergentagent.com",
).rstrip("/")
API = f"{BASE_URL}/api"

USER_ID = "697f0c6abf35c0528ff06954"
TIMEOUT = 180

EXPECTED_STANCES = {
    "astrology": "symbolic cartographer",
    "human_design": "energetic mechanic",
    "numerology": "life-pattern decoder",
    "enneagram": "motivational psychologist",
    "bazi": "elemental strategist",
}

V1_MESSAGES = {
    "astrology": "Tell me about my Saturn placement",
    "human_design": "What does my Authority mean?",
    "numerology": "What does my Life Path number say about me?",
    "enneagram": "How does my type show up under stress?",
    "bazi": "What does my Day Master say about me?",
}

REQUIRED_DEBUG_FIELDS = [
    "marker",
    "lens",
    "active_entity",
    "active_entity_source",
    "recent_history_entities",
    "grounding_sources",
    "missing_sources",
    "conversation_turns_used",
]

FORBIDDEN = {
    "astrology": [
        "the universe is asking",
        "your stars say",
        "today's horoscope",
    ],
    "human_design": [
        " mars ",
        " sun sign",
        " your sign",
        " 4th house",
        " 8th house",
        "trust the flow",
        "zodiac",
        "horoscope",
    ],
    "numerology": [
        "lucky number",
        "vibration",
    ],
    "enneagram": [
        "8s are bullies",
        "7s are addicts",
    ],
    "bazi": [
        " your sign",
        "horoscope",
        "zodiac",
        " mars ",
        " saturn ",
        "how does that make you feel",
        "lucky element",
    ],
}


def post_chat(lens, message, session_id=None):
    body = {
        "user_id": USER_ID,
        "message": message,
        "lens": lens,
        "include_journal": True,
        "include_history": True,
    }
    if session_id:
        body["session_id"] = session_id
    t0 = time.time()
    r = requests.post(f"{API}/mirror/chat", json=body, timeout=TIMEOUT)
    dt = time.time() - t0
    try:
        data = r.json()
    except Exception:
        data = {"_raw": r.text}
    return r.status_code, data, dt


def find_forbidden(text, phrases):
    t = (text or "").lower()
    padded = f" {t} "
    hits = []
    for p in phrases:
        if p.lower() in padded:
            hits.append(p.strip())
    return hits


def banner(title):
    print(f"\n{'=' * 90}\n{title}\n{'=' * 90}")


def short(s, n=400):
    s = str(s)
    return s if len(s) <= n else s[:n] + "..."


def test_v1():
    banner("V1 — Debug payload presence for all 5 lenses")
    results = {}
    passed = 0
    failed = 0
    for lens, msg in V1_MESSAGES.items():
        session_id = f"voice-v1-{lens}-{uuid.uuid4().hex[:8]}"
        status, data, dt = post_chat(lens, msg, session_id=session_id)
        debug = (data or {}).get("debug") or {}
        resp_text = (data or {}).get("response", "")
        problems = []
        if status != 200:
            problems.append(f"HTTP {status}")
        vmarker = debug.get("voice_marker")
        if vmarker != "lens-voice-differentiation-v1":
            problems.append(f"voice_marker={vmarker!r}")
        stance = debug.get("interpretive_stance")
        expected_stance = EXPECTED_STANCES[lens]
        if stance != expected_stance:
            problems.append(f"interpretive_stance={stance!r} (expected {expected_stance!r})")
        missing_fields = [f for f in REQUIRED_DEBUG_FIELDS if f not in debug]
        if missing_fields:
            problems.append(f"missing fields: {missing_fields}")
        marker = debug.get("marker")
        if marker != "multi-lens-chat-memory-v1":
            problems.append(f"marker={marker!r}")
        d_lens = debug.get("lens")
        if d_lens != lens:
            problems.append(f"lens={d_lens!r}")
        verdict = "PASS" if not problems else "FAIL"
        if not problems:
            passed += 1
        else:
            failed += 1
        results[lens] = {
            "status": status,
            "duration_s": round(dt, 2),
            "voice_marker": vmarker,
            "interpretive_stance": stance,
            "marker": marker,
            "lens": d_lens,
            "active_entity": debug.get("active_entity"),
            "active_entity_source": debug.get("active_entity_source"),
            "grounding_sources": debug.get("grounding_sources"),
            "missing_sources": debug.get("missing_sources"),
            "response_preview": short(resp_text, 250),
            "problems": problems,
            "verdict": verdict,
        }
        print(f"\n[{lens}] {verdict} ({status}, {dt:.2f}s)")
        print(f"  voice_marker={vmarker}")
        print(f"  interpretive_stance={stance}")
        print(f"  active_entity={debug.get('active_entity')} src={debug.get('active_entity_source')}")
        print(f"  marker={marker} lens={d_lens}")
        print(f"  grounding={debug.get('grounding_sources')} missing={debug.get('missing_sources')}")
        print(f"  resp: {short(resp_text, 220)}")
        if problems:
            print(f"  PROBLEMS: {problems}")
    print(f"\nV1 SUMMARY: {passed} pass / {failed} fail")
    return results, passed, failed


def test_v2():
    banner("V2 — Same-question voice divergence")
    captures = {}
    passed = 0
    failed = 0
    pairs = [
        {
            "name": "PairA-relationships",
            "items": [
                {"lens": "astrology", "msg": "How does my chart show up in relationships?"},
                {"lens": "human_design", "msg": "How does my design show up in relationships?"},
            ],
        },
        {
            "name": "PairB-work",
            "items": [
                {"lens": "numerology", "msg": "How does my Life Path show up at work?"},
                {"lens": "bazi", "msg": "How does my Day Master show up at work?"},
            ],
        },
    ]
    for pair in pairs:
        print(f"\n--- {pair['name']} ---")
        for item in pair["items"]:
            lens = item["lens"]
            msg = item["msg"]
            session_id = f"voice-v2-{lens}-{uuid.uuid4().hex[:8]}"
            status, data, dt = post_chat(lens, msg, session_id=session_id)
            debug = (data or {}).get("debug") or {}
            resp_text = (data or {}).get("response", "")
            problems = []
            if status != 200:
                problems.append(f"HTTP {status}")
            if debug.get("voice_marker") != "lens-voice-differentiation-v1":
                problems.append(f"voice_marker={debug.get('voice_marker')!r}")
            if debug.get("interpretive_stance") != EXPECTED_STANCES[lens]:
                problems.append(f"interpretive_stance={debug.get('interpretive_stance')!r}")
            verdict = "PASS" if not problems else "FAIL"
            if not problems:
                passed += 1
            else:
                failed += 1
            key = f"{pair['name']}::{lens}"
            captures[key] = {
                "lens": lens,
                "message": msg,
                "status": status,
                "duration_s": round(dt, 2),
                "voice_marker": debug.get("voice_marker"),
                "interpretive_stance": debug.get("interpretive_stance"),
                "active_entity": debug.get("active_entity"),
                "active_entity_source": debug.get("active_entity_source"),
                "grounding_sources": debug.get("grounding_sources"),
                "response": resp_text,
                "problems": problems,
                "verdict": verdict,
            }
            print(f"\n>>> {lens.upper()} ({status}, {dt:.2f}s) — {verdict}")
            print(f"    voice_marker={debug.get('voice_marker')}")
            print(f"    interpretive_stance={debug.get('interpretive_stance')}")
            print(f"    active_entity={debug.get('active_entity')} src={debug.get('active_entity_source')}")
            print(f"--- FULL RESPONSE ---")
            print(resp_text)
            print(f"--- END RESPONSE ---")
            if problems:
                print(f"    PROBLEMS: {problems}")
    print(f"\nV2 SUMMARY: {passed} pass / {failed} fail")
    return captures, passed, failed


def test_v3(v2_captures):
    banner("V3 — Forbidden phrasing scan")
    hits_by = {}
    clean = 0
    dirty = 0
    for key, cap in v2_captures.items():
        lens = cap["lens"]
        resp = cap["response"]
        hits = find_forbidden(resp, FORBIDDEN.get(lens, []))
        hits_by[key] = hits
        if not hits:
            clean += 1
            print(f"\n[{key}] lens={lens} CLEAN")
        else:
            dirty += 1
            print(f"\n[{key}] lens={lens} HITS={hits}")
    print(f"\nV3 SUMMARY: {clean} clean / {dirty} with hits")
    return hits_by, clean, dirty


def test_v4():
    banner("V4 — Regression: multi-lens-chat-memory-v1 referent resolution")
    results = {}
    passed = 0
    failed = 0

    # Astro Jupiter chain
    astro_session = f"v4-astro-{uuid.uuid4().hex[:8]}"
    s1, d1, _ = post_chat("astrology", "Tell me about my Jupiter placement.", session_id=astro_session)
    db1 = (d1 or {}).get("debug") or {}
    time.sleep(0.5)
    s2, d2, _ = post_chat("astrology", "And how does it show up day-to-day?", session_id=astro_session)
    db2 = (d2 or {}).get("debug") or {}

    a_t1 = (db1.get("active_entity") or {})
    a_t2 = (db2.get("active_entity") or {})
    a_t1_ok = (a_t1.get("name") or "").lower() == "jupiter" and db1.get("active_entity_source") == "current"
    a_t2_ok = (a_t2.get("name") or "").lower() == "jupiter" and db2.get("active_entity_source") == "referent"
    a_ok = a_t1_ok and a_t2_ok and s1 == 200 and s2 == 200

    results["astrology_jupiter_T1_T2"] = {
        "T1": {"status": s1, "active_entity": a_t1, "src": db1.get("active_entity_source"),
               "marker": db1.get("marker"), "voice_marker": db1.get("voice_marker"),
               "interpretive_stance": db1.get("interpretive_stance"),
               "response_preview": short((d1 or {}).get("response", ""), 200)},
        "T2": {"status": s2, "active_entity": a_t2, "src": db2.get("active_entity_source"),
               "marker": db2.get("marker"), "voice_marker": db2.get("voice_marker"),
               "interpretive_stance": db2.get("interpretive_stance"),
               "response_preview": short((d2 or {}).get("response", ""), 200)},
        "verdict": "PASS" if a_ok else "FAIL",
    }
    if a_ok:
        passed += 1
    else:
        failed += 1
    print(f"\n[Astro Jupiter T1→T2] {'PASS' if a_ok else 'FAIL'}")
    print(f"  T1 ae={a_t1} src={db1.get('active_entity_source')}")
    print(f"  T2 ae={a_t2} src={db2.get('active_entity_source')}")

    # HD Authority chain
    hd_session = f"v4-hd-{uuid.uuid4().hex[:8]}"
    s3, d3, _ = post_chat("human_design", "Walk me through my Authority.", session_id=hd_session)
    db3 = (d3 or {}).get("debug") or {}
    time.sleep(0.5)
    s4, d4, _ = post_chat("human_design", "What's the most common way I miss it?", session_id=hd_session)
    db4 = (d4 or {}).get("debug") or {}

    b_t1 = (db3.get("active_entity") or {})
    b_t2 = (db4.get("active_entity") or {})
    b_t1_ok = (b_t1.get("name") or "").lower() == "authority" and db3.get("active_entity_source") == "current"
    b_t2_ok = (b_t2.get("name") or "").lower() == "authority" and db4.get("active_entity_source") == "referent"
    b_ok = b_t1_ok and b_t2_ok and s3 == 200 and s4 == 200

    results["hd_authority_T1_T2"] = {
        "T1": {"status": s3, "active_entity": b_t1, "src": db3.get("active_entity_source"),
               "marker": db3.get("marker"), "voice_marker": db3.get("voice_marker"),
               "interpretive_stance": db3.get("interpretive_stance"),
               "response_preview": short((d3 or {}).get("response", ""), 200)},
        "T2": {"status": s4, "active_entity": b_t2, "src": db4.get("active_entity_source"),
               "marker": db4.get("marker"), "voice_marker": db4.get("voice_marker"),
               "interpretive_stance": db4.get("interpretive_stance"),
               "response_preview": short((d4 or {}).get("response", ""), 200)},
        "verdict": "PASS" if b_ok else "FAIL",
    }
    if b_ok:
        passed += 1
    else:
        failed += 1
    print(f"\n[HD Authority T1→T2] {'PASS' if b_ok else 'FAIL'}")
    print(f"  T1 ae={b_t1} src={db3.get('active_entity_source')}")
    print(f"  T2 ae={b_t2} src={db4.get('active_entity_source')}")

    print(f"\nV4 SUMMARY: {passed} pass / {failed} fail")
    return results, passed, failed


def main():
    print(f"Base API: {API}")
    print(f"User: {USER_ID}")
    v1, v1p, v1f = test_v1()
    v2, v2p, v2f = test_v2()
    v3, v3c, v3d = test_v3(v2)
    v4, v4p, v4f = test_v4()
    banner("OVERALL")
    print(f"V1: {v1p}/{v1p+v1f} pass | V2: {v2p}/{v2p+v2f} pass | V3: {v3c}/{v3c+v3d} clean | V4: {v4p}/{v4p+v4f} pass")
    with open("/app/lens_voice_diff_results.json", "w") as f:
        json.dump({"V1": v1, "V2": v2, "V3": v3, "V4": v4}, f, indent=2, default=str)
    print("\nSaved → /app/lens_voice_diff_results.json")
    return 0 if (v1f == 0 and v2f == 0 and v4f == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
