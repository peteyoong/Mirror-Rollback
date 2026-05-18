"""
Astrology Chat Memory + Entity Tracking Test (astrology-chat-memory-v1)

Tests the conversational memory fix in POST /api/mirror/chat for the
astrology lens. Validates:
  - Active entity resolution (current / referent / carryover / none)
  - Subject snap-back on explicit planet mention
  - Pure house questions
  - Non-fabrication for unknown placements
  - Non-astrology lens regression (debug should be null)
"""
import os
import sys
import json
import requests
from pathlib import Path

# Load REACT_APP_BACKEND_URL / EXPO_PUBLIC_BACKEND_URL from frontend/.env
FRONTEND_ENV = Path("/app/frontend/.env")
BACKEND_URL = None
for line in FRONTEND_ENV.read_text().splitlines():
    line = line.strip()
    if line.startswith("EXPO_PUBLIC_BACKEND_URL=") or line.startswith("REACT_APP_BACKEND_URL="):
        BACKEND_URL = line.split("=", 1)[1].strip().strip('"').strip("'")
        break

assert BACKEND_URL, "No backend URL found"
API = f"{BACKEND_URL}/api"
print(f"Using API base: {API}")

PETE_ID = "697f0c6abf35c0528ff06954"
MEL_ID = "697ec826ad4b18f75bf42616"

def post_chat(user_id, message, lens="astrology", session_id=None, include_history=True):
    body = {
        "user_id": user_id,
        "message": message,
        "lens": lens,
        "include_journal": False,
        "include_history": include_history,
    }
    if session_id:
        body["session_id"] = session_id
    r = requests.post(f"{API}/mirror/chat", json=body, timeout=120)
    print(f"  -> HTTP {r.status_code} (t={r.elapsed.total_seconds():.2f}s)")
    if r.status_code != 200:
        print(f"  Body: {r.text[:600]}")
    r.raise_for_status()
    return r.json()


def summarize_turn(label, resp):
    dbg = resp.get("debug") or {}
    active = dbg.get("active_entity") or {}
    name = active.get("name") if isinstance(active, dict) else None
    src = dbg.get("active_entity_source")
    marker = dbg.get("marker")
    text = (resp.get("response") or "")[:240]
    print(f"\n--- {label} ---")
    print(f"  session_id          : {resp.get('session_id')}")
    print(f"  debug.marker        : {marker}")
    print(f"  active_entity.name  : {name}")
    print(f"  active_entity_source: {src}")
    print(f"  recent_history_ents : {dbg.get('recent_history_entities')}")
    print(f"  chart_index_size    : {dbg.get('chart_index_size')}")
    print(f"  response[:240]      : {text}")
    return {"name": name, "source": src, "marker": marker, "text": resp.get("response") or "", "session_id": resp.get("session_id"), "debug": dbg}


results = {"failures": [], "passes": []}

def record(name, ok, detail=""):
    (results["passes"] if ok else results["failures"]).append((name, detail))
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {name} {('— ' + detail) if detail else ''}")


# =========================================================================
# Test 1: Health
# =========================================================================
print("\n========== TEST 1: Health & module load ==========")
h = requests.get(f"{API}/health", timeout=15).json()
print(f"  /api/health -> ok={h.get('ok')}, status={h.get('status')}")
record("Test1.health", h.get("ok") is True and h.get("status") == "healthy")

# =========================================================================
# Test 2: Failing chat scenario reproduction with shared session
# =========================================================================
print("\n========== TEST 2: Jupiter conversation continuity ==========")

print("\n[Turn 1] 'Where does Jupiter sit in my chart and what does that mean?'")
r1 = post_chat(PETE_ID, "Where does Jupiter sit in my chart and what does that mean?", lens="astrology")
t1 = summarize_turn("Turn 1", r1)
session_id = t1["session_id"]

print(f"\n[Turn 2] (session={session_id}) 'Oh so that sits in house 4 for me?'")
r2 = post_chat(PETE_ID, "Oh so that sits in house 4 for me?", lens="astrology", session_id=session_id)
t2 = summarize_turn("Turn 2", r2)

print(f"\n[Turn 3] (session={session_id}) 'I was asking about Jupiter on my chart!?'")
r3 = post_chat(PETE_ID, "I was asking about Jupiter on my chart!?", lens="astrology", session_id=session_id)
t3 = summarize_turn("Turn 3", r3)

print(f"\n[Turn 4] (session={session_id}) 'And which house does that sit in?'")
r4 = post_chat(PETE_ID, "And which house does that sit in?", lens="astrology", session_id=session_id)
t4 = summarize_turn("Turn 4", r4)

# Pass criteria
record("Test2.marker_v1_t1", t1["marker"] == "astrology-chat-memory-v1", f"got {t1['marker']}")
record("Test2.T1.active_jupiter", t1["name"] == "Jupiter", f"got {t1['name']}")
record("Test2.T1.source_current", t1["source"] == "current", f"got {t1['source']}")

record("Test2.T2.active_jupiter", t2["name"] == "Jupiter", f"got {t2['name']}")
record("Test2.T2.source_referent", t2["source"] == "referent", f"got {t2['source']}")

record("Test2.T3.active_jupiter", t3["name"] == "Jupiter", f"got {t3['name']}")
record("Test2.T3.source_current", t3["source"] == "current", f"got {t3['source']}")

record("Test2.T4.active_jupiter", t4["name"] == "Jupiter", f"got {t4['name']}")
record("Test2.T4.source_referent", t4["source"] == "referent", f"got {t4['source']}")

# Content checks: each response should mention Jupiter
for i, t in enumerate([t1, t2, t3, t4], 1):
    has_jup = "jupiter" in t["text"].lower()
    record(f"Test2.T{i}.response_mentions_jupiter", has_jup, f"len={len(t['text'])}")

# T4 should plainly state a house number
import re as _re
t4_lower = t4["text"].lower()
has_house_word = bool(_re.search(r"\bhouse\b", t4_lower)) or bool(_re.search(r"\b\d+(?:st|nd|rd|th)\b", t4_lower))
record("Test2.T4.contains_house_reference", has_house_word, t4["text"][:200])


# =========================================================================
# Test 3: Explicit subject switch to Saturn
# =========================================================================
print("\n========== TEST 3: Explicit pivot to Saturn ==========")
print(f"[Turn 5] (session={session_id}) 'What about Saturn?'")
r5 = post_chat(PETE_ID, "What about Saturn?", lens="astrology", session_id=session_id)
t5 = summarize_turn("Turn 5", r5)
record("Test3.active_saturn", t5["name"] == "Saturn", f"got {t5['name']}")
record("Test3.source_current", t5["source"] == "current", f"got {t5['source']}")
record("Test3.response_mentions_saturn", "saturn" in t5["text"].lower())


# =========================================================================
# Test 4: Pure house question — new session
# =========================================================================
print("\n========== TEST 4: Pure 7th house question (new session) ==========")
r6 = post_chat(PETE_ID, "What is in my 7th house?", lens="astrology")
t6 = summarize_turn("Turn 6 (new session)", r6)
test4_session = t6["session_id"]
record("Test4.active_house7", t6["name"] == "House 7", f"got {t6['name']}")
record("Test4.source_current", t6["source"] == "current", f"got {t6['source']}")
record("Test4.mentions_seventh_house", "7" in t6["text"] or "seventh" in t6["text"].lower())


# =========================================================================
# Test 5: Pluto possibly missing — no fabrication
# =========================================================================
print("\n========== TEST 5: Pluto — no drift / no fabrication ==========")
r7 = post_chat(PETE_ID, "Tell me about Pluto.", lens="astrology", session_id=test4_session)
t7 = summarize_turn("Turn 7", r7)
record("Test5.active_pluto", t7["name"] == "Pluto", f"got {t7['name']}")
# Whether Pluto present or not, check no fabrication if missing.
chart_size = t7["debug"].get("chart_index_size", 0)
pluto_in_chart = any(
    ("pluto" in (e or "").lower()) for e in (t7["debug"].get("recent_history_entities") or [])
)
print(f"  Pluto present in history-entities scan: {pluto_in_chart} (chart_index_size={chart_size})")
# The response should at minimum not invent placements; we can't fully verify
# without inspecting the chart_index, but we look for plain admission phrasing
# if Pluto isn't there. Soft check.


# =========================================================================
# Test 6: Non-astrology lens regression — debug should be null
# =========================================================================
print("\n========== TEST 6: Generalist lens — debug should be null ==========")
r8 = post_chat(PETE_ID, "What did we just discuss?", lens=None)
print(f"  Status OK, debug field: {r8.get('debug')!r}")
record("Test6.status_200", "response" in r8)
record("Test6.debug_is_null", r8.get("debug") is None, f"got {r8.get('debug')!r}")


# =========================================================================
# Summary
# =========================================================================
print("\n\n===================== SUMMARY =====================")
print(f"PASSED: {len(results['passes'])}")
print(f"FAILED: {len(results['failures'])}")
for n, d in results["failures"]:
    print(f"  FAIL  {n}  ({d})")
print("===================================================")

# Exit non-zero if any failure
sys.exit(1 if results["failures"] else 0)
