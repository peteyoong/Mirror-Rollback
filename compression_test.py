"""
Test: conversational-compression-v1 verification on POST /api/mirror/chat
User: Pete (697f0c6abf35c0528ff06954)
"""
import os
import json
import time
import uuid
import requests

BACKEND_URL = "https://individual-maps-v1.preview.emergentagent.com"
API = f"{BACKEND_URL}/api"
USER_ID = "697f0c6abf35c0528ff06954"

session = requests.Session()
session.headers.update({"Content-Type": "application/json"})

TIMEOUT = 90

def chat(message, lens=None, session_id=None, include_journal=True, include_history=True):
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
    r = session.post(f"{API}/mirror/chat", json=payload, timeout=TIMEOUT)
    return r

def word_count(text):
    return len((text or "").split())

results = []

def record(name, status_code, debug, response_text, passed, rationale):
    wc = word_count(response_text)
    dm = (debug or {}).get("depth_mode") if isinstance(debug, dict) else None
    cm = (debug or {}).get("compression_marker") if isinstance(debug, dict) else None
    print("\n" + "=" * 80)
    print(f"TEST: {name}")
    print(f"HTTP: {status_code}")
    print(f"compression_marker: {cm}")
    print(f"depth_mode: {dm}")
    print(f"word_count: {wc}")
    print(f"response: {(response_text or '')[:500]}{'...' if response_text and len(response_text)>500 else ''}")
    print(f"VERDICT: {'PASS' if passed else 'FAIL'} — {rationale}")
    results.append({
        "test": name, "http": status_code, "compression_marker": cm,
        "depth_mode": dm, "word_count": wc, "response": response_text,
        "passed": passed, "rationale": rationale
    })


# ==============================================================
# C1: Debug payload presence
# ==============================================================
print("\n##### C1: Debug payload presence (astrology) #####")
r = chat("What does my Saturn placement mean?", lens="astrology",
         session_id=f"c1-{uuid.uuid4().hex[:8]}")
ok = r.status_code == 200
body = r.json() if ok else {}
dbg = body.get("debug") or {}
checks = {
    "compression_marker": dbg.get("compression_marker") == "conversational-compression-v1",
    "depth_mode_NORMAL": dbg.get("depth_mode") == "NORMAL",
    "marker_legacy": dbg.get("marker") == "multi-lens-chat-memory-v1",
    "lens_present": "lens" in dbg,
    "active_entity_present": "active_entity" in dbg,
    "active_entity_source_present": "active_entity_source" in dbg,
    "voice_marker_present": "voice_marker" in dbg,
    "interpretive_stance_present": "interpretive_stance" in dbg,
}
passed = all(checks.values())
rationale = f"checks={checks}"
record("C1 debug payload presence", r.status_code, dbg,
       body.get("response", ""), passed, rationale)


# ==============================================================
# C2: LIGHT vs NORMAL vs DEEP — same session
# ==============================================================
print("\n##### C2: LIGHT vs NORMAL vs DEEP (same session) #####")
sid = f"c2-{uuid.uuid4().hex[:8]}"

# Turn 1 - NORMAL
r1 = chat("What does my Saturn placement mean?", lens="astrology", session_id=sid)
b1 = r1.json() if r1.status_code == 200 else {}
d1 = b1.get("debug") or {}
resp1 = b1.get("response", "")
wc1 = word_count(resp1)
record("C2.1 NORMAL — Saturn question", r1.status_code, d1, resp1,
       d1.get("depth_mode") == "NORMAL",
       f"expected depth_mode=NORMAL, got={d1.get('depth_mode')}")

time.sleep(2)

# Turn 2 - LIGHT
r2 = chat("ok", lens="astrology", session_id=sid)
b2 = r2.json() if r2.status_code == 200 else {}
d2 = b2.get("debug") or {}
resp2 = b2.get("response", "")
wc2 = word_count(resp2)
record("C2.2 LIGHT — 'ok' ack", r2.status_code, d2, resp2,
       d2.get("depth_mode") == "LIGHT",
       f"expected depth_mode=LIGHT, got={d2.get('depth_mode')}")

time.sleep(2)

# Turn 3 - DEEP
r3 = chat("go deeper on Saturn please", lens="astrology", session_id=sid)
b3 = r3.json() if r3.status_code == 200 else {}
d3 = b3.get("debug") or {}
resp3 = b3.get("response", "")
wc3 = word_count(resp3)
record("C2.3 DEEP — go deeper", r3.status_code, d3, resp3,
       d3.get("depth_mode") == "DEEP",
       f"expected depth_mode=DEEP, got={d3.get('depth_mode')}")

# Monotone check
monotone = wc3 > wc1 > wc2
light_short = wc2 <= 80
deep_long = wc3 >= 150
print(f"\nC2 SUMMARY:")
print(f"  LIGHT wc={wc2} (target <=80) {'OK' if light_short else 'OUT-OF-BAND'}")
print(f"  NORMAL wc={wc1}")
print(f"  DEEP wc={wc3} (target >=150) {'OK' if deep_long else 'OUT-OF-BAND'}")
print(f"  monotone DEEP>NORMAL>LIGHT: {monotone}")
results.append({
    "test": "C2 monotone length",
    "wc_light": wc2, "wc_normal": wc1, "wc_deep": wc3,
    "monotone": monotone, "light_short": light_short, "deep_long": deep_long,
    "passed": monotone and light_short and deep_long,
    "rationale": f"DEEP({wc3})>NORMAL({wc1})>LIGHT({wc2}); LIGHT≤80={light_short}; DEEP≥150={deep_long}"
})


# ==============================================================
# C3: Imperative-aware LIGHT exclusion
# ==============================================================
print("\n##### C3: Imperative-aware LIGHT exclusion #####")
sid_a = f"c3a-{uuid.uuid4().hex[:8]}"
r = chat("Tell me about my Moon", lens="astrology", session_id=sid_a)
b = r.json() if r.status_code == 200 else {}
d = b.get("debug") or {}
record("C3.1 imperative 'Tell me about my Moon' should be NORMAL",
       r.status_code, d, b.get("response", ""),
       d.get("depth_mode") == "NORMAL",
       f"expected NORMAL, got {d.get('depth_mode')}")

time.sleep(2)

sid_b = f"c3b-{uuid.uuid4().hex[:8]}"
# Need a prior turn so an ack makes sense (LIGHT detection looks at prior context for some acks)
chat("What does my Sun mean?", lens="astrology", session_id=sid_b)
time.sleep(2)
r = chat("Yes definitely", lens="astrology", session_id=sid_b)
b = r.json() if r.status_code == 200 else {}
d = b.get("debug") or {}
record("C3.2 'Yes definitely' should be LIGHT",
       r.status_code, d, b.get("response", ""),
       d.get("depth_mode") == "LIGHT",
       f"expected LIGHT, got {d.get('depth_mode')}")


# ==============================================================
# C4: Memory + voice regression
# ==============================================================
print("\n##### C4: Memory + voice regression #####")
sid_c4 = f"c4-{uuid.uuid4().hex[:8]}"

# LIGHT regression: substantive Jupiter Q then ack
r = chat("What does my Jupiter placement mean?", lens="astrology", session_id=sid_c4)
b_jup = r.json() if r.status_code == 200 else {}
d_jup = b_jup.get("debug") or {}
record("C4.1a Jupiter setup (NORMAL)", r.status_code, d_jup, b_jup.get("response", ""),
       d_jup.get("depth_mode") == "NORMAL",
       f"got {d_jup.get('depth_mode')}")

time.sleep(2)

r = chat("got it", lens="astrology", session_id=sid_c4)
b_got = r.json() if r.status_code == 200 else {}
d_got = b_got.get("debug") or {}
text_got = b_got.get("response", "")
wc_got = word_count(text_got)
# LIGHT regression checks: short response, no fresh chart tour
forbidden = ["sun in", "moon in", "rising", "ascendant"]
has_chart_tour = any(t in text_got.lower() for t in forbidden)
record("C4.1b 'got it' LIGHT regression",
       r.status_code, d_got, text_got,
       d_got.get("depth_mode") == "LIGHT" and wc_got <= 80 and not has_chart_tour,
       f"depth_mode={d_got.get('depth_mode')} wc={wc_got} fresh_chart_tour={has_chart_tour}")

time.sleep(2)

# DEEP regression
sid_c4b = f"c4b-{uuid.uuid4().hex[:8]}"
r = chat("Walk me through how my Saturn interacts with the rest of my chart",
         lens="astrology", session_id=sid_c4b)
b_deep = r.json() if r.status_code == 200 else {}
d_deep = b_deep.get("debug") or {}
text_deep = b_deep.get("response", "")
wc_deep = word_count(text_deep)
voice_marker = d_deep.get("voice_marker", "")
record("C4.2 DEEP regression — Saturn interacts",
       r.status_code, d_deep, text_deep,
       d_deep.get("depth_mode") == "DEEP" and wc_deep >= 150,
       f"depth_mode={d_deep.get('depth_mode')} wc={wc_deep} voice_marker={voice_marker}")


# ==============================================================
# C5: Multi-lens regression — HD + BaZi
# ==============================================================
print("\n##### C5: Multi-lens regression — HD + BaZi #####")
# HD
sid_hd = f"c5hd-{uuid.uuid4().hex[:8]}"
r = chat("What is my Authority?", lens="human_design", session_id=sid_hd)
b = r.json() if r.status_code == 200 else {}
d = b.get("debug") or {}
hd_wc_normal = word_count(b.get("response", ""))
record("C5.1 HD Authority NORMAL", r.status_code, d, b.get("response", ""),
       d.get("depth_mode") == "NORMAL",
       f"got {d.get('depth_mode')}")

time.sleep(2)

r = chat("why?", lens="human_design", session_id=sid_hd)
b = r.json() if r.status_code == 200 else {}
d = b.get("debug") or {}
hd_wc_deep = word_count(b.get("response", ""))
record("C5.2 HD 'why?' DEEP", r.status_code, d, b.get("response", ""),
       d.get("depth_mode") == "DEEP" and hd_wc_deep > hd_wc_normal,
       f"got {d.get('depth_mode')} wc_deep={hd_wc_deep} wc_normal={hd_wc_normal}")

time.sleep(2)

# BaZi
sid_bz = f"c5bz-{uuid.uuid4().hex[:8]}"
r = chat("What does my Day Master mean?", lens="bazi", session_id=sid_bz)
b = r.json() if r.status_code == 200 else {}
d = b.get("debug") or {}
bz_wc_normal = word_count(b.get("response", ""))
record("C5.3 BaZi Day Master NORMAL", r.status_code, d, b.get("response", ""),
       d.get("depth_mode") == "NORMAL",
       f"got {d.get('depth_mode')}")

time.sleep(2)

r = chat("ok", lens="bazi", session_id=sid_bz)
b = r.json() if r.status_code == 200 else {}
d = b.get("debug") or {}
bz_wc_light = word_count(b.get("response", ""))
record("C5.4 BaZi 'ok' LIGHT", r.status_code, d, b.get("response", ""),
       d.get("depth_mode") == "LIGHT" and bz_wc_light <= 80 and bz_wc_light < bz_wc_normal,
       f"got {d.get('depth_mode')} wc_light={bz_wc_light} wc_normal={bz_wc_normal}")


# ==============================================================
# C6: Generalist regression (lens=null → no debug)
# ==============================================================
print("\n##### C6: Generalist regression #####")
r = chat("What did we just talk about?")  # no lens
b = r.json() if r.status_code == 200 else {}
d = b.get("debug")
passed = (r.status_code == 200) and (d is None)
record("C6 generalist — debug should be None", r.status_code, d, b.get("response", ""),
       passed, f"debug is {('None' if d is None else 'present: ' + str(d)[:200])}")


# ==============================================================
# Final summary
# ==============================================================
print("\n\n" + "#" * 80)
print("FINAL REPORT")
print("#" * 80)
total = 0
passed = 0
for r in results:
    total += 1
    if r.get("passed"):
        passed += 1
    print(f"[{'PASS' if r.get('passed') else 'FAIL'}] {r.get('test')}")

print(f"\nTOTAL: {passed}/{total} passed")

with open("/app/compression_test_results.json", "w") as f:
    json.dump(results, f, indent=2)
print("\nResults JSON: /app/compression_test_results.json")
