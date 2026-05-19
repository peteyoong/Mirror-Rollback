"""
Backend test for Life Tab Master Voice (life-tab-master-voice-v1).

Test plan (per review request):
  E1. Activation on life_domain="self"
  E2. Activation on life_domain="relationships" with pattern trigger
  E3. Session continuity (multi-turn)
  E4. Voice quality (qualitative, jargon scan)
  E5. Framework reveal on explicit ask
  E6. No regression — lens chat without life_domain
  E7. Mutual exclusion (lens wins)
"""
import re
import time
import uuid
import requests
from pathlib import Path

# Load EXPO_PUBLIC_BACKEND_URL from /app/frontend/.env
FRONTEND_ENV = Path("/app/frontend/.env")
BASE_URL = None
for line in FRONTEND_ENV.read_text().splitlines():
    if line.startswith("EXPO_PUBLIC_BACKEND_URL="):
        BASE_URL = line.split("=", 1)[1].strip().strip('"').strip("'")
        break

assert BASE_URL, "EXPO_PUBLIC_BACKEND_URL not found"
API = BASE_URL.rstrip("/") + "/api"

USER_ID = "697f0c6abf35c0528ff06954"  # Pete
ENDPOINT = f"{API}/mirror/chat"

print(f"[CONFIG] API: {API}")
print(f"[CONFIG] User ID: {USER_ID}")
print(f"[CONFIG] Endpoint: {ENDPOINT}")
print("=" * 78)


def _post(payload: dict, timeout: int = 120) -> tuple[int, dict]:
    t0 = time.time()
    r = requests.post(ENDPOINT, json=payload, timeout=timeout)
    dur = time.time() - t0
    try:
        body = r.json()
    except Exception:
        body = {"_raw": r.text[:500]}
    print(f"  -> HTTP {r.status_code} in {dur:.2f}s")
    return r.status_code, body


# Forbidden tokens in user-facing `response` text (case-insensitive).
HARD_JARGON_TOKENS = [
    r"\bSaturn\b",
    r"\bMercury\b",
    r"\bVenus\b",
    r"\bMars\b",
    r"\bJupiter\b",
    r"\bPluto\b",
    r"\bUranus\b",
    r"\bNeptune\b",
    r"\bSun in\b",
    r"\bMoon in\b",
    r"\bGate \d+",
    r"\bChannel \d+",
    r"\bLife Path\b",
    r"\bDay Master\b",
    r"\bEnneagram\b",
    r"\bType 4\b",
    r"\bType 7\b",
    r"\bSacral\b",
    r"\bManifestor\b",
    r"\bProjector\b",
    r"\bGenerator\b",
    r"\bBaZi\b",
    r"\bnatal\b",
    r"\btransit(s)?\b",
    r"\bayanamsa\b",
    r"\bThroat (centre|center)\b",
]


def scan_jargon(text: str) -> list[str]:
    found = []
    for pat in HARD_JARGON_TOKENS:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            found.append(m.group(0))
    return sorted(set(found))


LOG_PATHS = [
    "/var/log/supervisor/backend.err.log",
    "/var/log/supervisor/backend.out.log",
]


def grep_logs(needle: str, lookback_chars: int = 300_000) -> bool:
    for p in LOG_PATHS:
        try:
            data = Path(p).read_text(errors="ignore")[-lookback_chars:]
            if needle in data:
                return True
        except Exception:
            pass
    return False


# ===========================================================================
# E1
# ===========================================================================
print("\n[E1] Activation on life_domain='self'")
e1_session = f"life-test-e1-{uuid.uuid4().hex[:8]}"
e1_payload = {
    "user_id": USER_ID,
    "message": "What's surfacing in me right now?",
    "lens": None,
    "session_id": e1_session,
    "include_journal": True,
    "include_history": True,
    "life_domain": "self",
}
status, body = _post(e1_payload)

e1_pass = True
e1_failures = []
if status != 200:
    e1_pass = False
    e1_failures.append(f"HTTP {status}: {body}")
else:
    debug = (body.get("debug") or {})
    mv = debug.get("master_voice")
    if not mv:
        e1_pass = False
        e1_failures.append(f"debug.master_voice missing. debug keys: {list(debug.keys())}")
    else:
        if mv.get("marker") != "life-tab-master-voice-v1":
            e1_pass = False
            e1_failures.append(f"marker={mv.get('marker')}")
        if mv.get("domain") != "self":
            e1_pass = False
            e1_failures.append(f"domain={mv.get('domain')}")
        if not isinstance(mv.get("contributing_frameworks"), list):
            e1_pass = False
            e1_failures.append("contributing_frameworks not a list")
        if "dominant_signal" not in mv:
            e1_pass = False
            e1_failures.append("dominant_signal key missing")
        else:
            ds = mv["dominant_signal"]
            if ds is not None and not isinstance(ds, dict):
                e1_pass = False
                e1_failures.append(f"dominant_signal not dict/null: {type(ds).__name__}")
        print(f"  marker={mv.get('marker')} domain={mv.get('domain')}")
        print(f"  contributing_frameworks={mv.get('contributing_frameworks')}")
        print(f"  signals_count={mv.get('signals_count')}")
        print(f"  dominant_signal={mv.get('dominant_signal')}")
        print(f"  depth_mode={mv.get('depth_mode')} intensity_mode={mv.get('intensity_mode')}")

time.sleep(1.5)
log_marker = "[MIRROR_CHAT][life-tab-master-voice-v1]"
log_found = grep_logs(log_marker)
if not log_found:
    e1_pass = False
    e1_failures.append(f"Backend log line '{log_marker}' not found")

print(f"  log marker found: {log_found}")
print(f"  E1 result: {'PASS' if e1_pass else 'FAIL'}  failures={e1_failures}")

e1_response_text = body.get("response", "") if status == 200 else ""

# ===========================================================================
# E2
# ===========================================================================
print("\n[E2] Activation on life_domain='relationships'")
e2_session = f"life-test-e2-{uuid.uuid4().hex[:8]}"
e2_payload = {
    "user_id": USER_ID,
    "message": "I feel like we're drifting apart from my partner",
    "lens": None,
    "session_id": e2_session,
    "include_journal": True,
    "include_history": True,
    "life_domain": "relationships",
}
status, body = _post(e2_payload)

e2_pass = True
e2_failures = []
if status != 200:
    e2_pass = False
    e2_failures.append(f"HTTP {status}")
else:
    debug = (body.get("debug") or {})
    mv = debug.get("master_voice")
    if not mv:
        e2_pass = False
        e2_failures.append("debug.master_voice missing")
    elif mv.get("domain") != "relationships":
        e2_pass = False
        e2_failures.append(f"domain={mv.get('domain')}")
    pm = debug.get("pattern_memory")
    if not pm:
        e2_pass = False
        e2_failures.append(f"debug.pattern_memory missing. debug keys: {list(debug.keys())}")
    else:
        print(f"  pattern_memory marker={pm.get('marker')}")
    print(f"  master_voice domain={(mv or {}).get('domain')} contributing={(mv or {}).get('contributing_frameworks')}")

time.sleep(1.5)
log_mv = grep_logs("[MIRROR_CHAT][life-tab-master-voice-v1]")
log_pm = grep_logs("[MIRROR_CHAT][pattern-memory-v1]")
if not log_mv:
    e2_pass = False
    e2_failures.append("life-tab marker not in logs")
if not log_pm:
    e2_pass = False
    e2_failures.append("pattern-memory-v1 marker not in logs")
print(f"  log master_voice: {log_mv}  log pattern_memory: {log_pm}")
print(f"  E2 result: {'PASS' if e2_pass else 'FAIL'}  failures={e2_failures}")

e2_response_text = body.get("response", "") if status == 200 else ""

# ===========================================================================
# E3
# ===========================================================================
print("\n[E3] Session continuity (reuse E1 session, switch to work)")
e3_payload = {
    "user_id": USER_ID,
    "message": "What about that pattern in work?",
    "lens": None,
    "session_id": e1_session,
    "include_journal": True,
    "include_history": True,
    "life_domain": "work",
}
status, body = _post(e3_payload)

e3_pass = True
e3_failures = []
e3_response_text = ""
if status != 200:
    e3_pass = False
    e3_failures.append(f"HTTP {status}")
else:
    debug = (body.get("debug") or {})
    mv = debug.get("master_voice")
    if not mv:
        e3_pass = False
        e3_failures.append("debug.master_voice missing")
    else:
        print(f"  domain={mv.get('domain')}  contributing={mv.get('contributing_frameworks')}")
    e3_response_text = body.get("response", "")
    print(f"  Reply (first 320 chars): {e3_response_text[:320]}")
print(f"  E3 result: {'PASS' if e3_pass else 'FAIL'}  failures={e3_failures}")

# ===========================================================================
# E4
# ===========================================================================
print("\n[E4] Voice quality — one msg per domain, jargon scan")

E4_PROMPTS = {
    "self": "I keep feeling restless inside but I can't name why.",
    "work": "Lately work feels heavy and I don't know if it's burnout or misalignment.",
    "relationships": "Why do I keep pulling away when someone gets close?",
}
DOMAIN_TEXTURES = {
    "self":          ["inside", "identity", "you", "self", "pattern", "alive", "weather", "inner"],
    "work":          ["work", "pressure", "structure", "capacity", "ambition", "exhaust", "responsibility", "authority", "burn"],
    "relationships": ["partner", "people", "between", "distance", "attach", "withdraw", "close", "intima", "field", "connect"],
}

e4_pass = True
e4_failures = []
e4_replies: dict[str, str] = {}

for dom, msg in E4_PROMPTS.items():
    sess = f"life-test-e4-{dom}-{uuid.uuid4().hex[:6]}"
    payload = {
        "user_id": USER_ID,
        "message": msg,
        "lens": None,
        "session_id": sess,
        "include_journal": True,
        "include_history": True,
        "life_domain": dom,
    }
    print(f"  -> domain={dom}, msg='{msg}'")
    status, body = _post(payload)
    if status != 200:
        e4_pass = False
        e4_failures.append(f"{dom}: HTTP {status}")
        continue
    debug = body.get("debug") or {}
    mv = debug.get("master_voice")
    if not mv or mv.get("domain") != dom:
        e4_pass = False
        e4_failures.append(f"{dom}: master_voice missing or wrong domain ({(mv or {}).get('domain')})")
    reply = body.get("response", "") or ""
    e4_replies[dom] = reply
    jargon_hits = scan_jargon(reply)
    if jargon_hits:
        e4_pass = False
        e4_failures.append(f"{dom}: jargon found {jargon_hits}")
    rlow = reply.lower()
    matches = [k for k in DOMAIN_TEXTURES[dom] if k.lower() in rlow]
    print(f"     reply 1st 260c: {reply[:260]}")
    print(f"     jargon_hits={jargon_hits}  domain_texture_matches={matches}")
    if not matches:
        e4_failures.append(f"{dom}: WARNING no domain texture words matched")

print(f"  E4 result: {'PASS' if e4_pass else 'FAIL'}  failures={e4_failures}")

# ===========================================================================
# E5
# ===========================================================================
print("\n[E5] Framework reveal on explicit ask")
e5_sess = f"life-test-e5-{uuid.uuid4().hex[:6]}"
_post({
    "user_id": USER_ID,
    "message": "I notice the same pattern of pulling away.",
    "lens": None,
    "session_id": e5_sess,
    "include_journal": True,
    "include_history": True,
    "life_domain": "self",
})
time.sleep(0.5)

e5_payload = {
    "user_id": USER_ID,
    "message": "Why is this showing up? Is this from my astrology or my Human Design?",
    "lens": None,
    "session_id": e5_sess,
    "include_journal": True,
    "include_history": True,
    "life_domain": "self",
}
status, body = _post(e5_payload)

e5_pass = True
e5_failures = []
if status != 200:
    e5_pass = False
    e5_failures.append(f"HTTP {status}")
else:
    debug = body.get("debug") or {}
    mv = debug.get("master_voice")
    if not mv:
        e5_pass = False
        e5_failures.append("master_voice missing")
    else:
        cf = mv.get("contributing_frameworks")
        if not isinstance(cf, list):
            e5_pass = False
            e5_failures.append("contributing_frameworks not a list")
        else:
            print(f"  contributing_frameworks={cf}")
    reply = body.get("response", "") or ""
    print(f"  reply 1st 320c: {reply[:320]}")

print(f"  E5 result: {'PASS' if e5_pass else 'FAIL'}  failures={e5_failures}")

# ===========================================================================
# E6
# ===========================================================================
print("\n[E6] No regression: lens='astrology', life_domain=None")
e6_payload = {
    "user_id": USER_ID,
    "message": "tell me about my Sun",
    "lens": "astrology",
    "session_id": f"life-test-e6-{uuid.uuid4().hex[:6]}",
    "include_journal": True,
    "include_history": True,
    "life_domain": None,
}
status, body = _post(e6_payload)

e6_pass = True
e6_failures = []
if status != 200:
    e6_pass = False
    e6_failures.append(f"HTTP {status}")
else:
    debug = body.get("debug") or {}
    mv = debug.get("master_voice")
    if mv is not None:
        e6_pass = False
        e6_failures.append(f"master_voice should be absent, got: {mv}")
    reply = body.get("response", "") or ""
    print(f"  master_voice present: {mv is not None}")
    print(f"  reply 1st 220c: {reply[:220]}")
print(f"  E6 result: {'PASS' if e6_pass else 'FAIL'}  failures={e6_failures}")

# ===========================================================================
# E7
# ===========================================================================
print("\n[E7] Mutual exclusion: lens='enneagram' + life_domain='self'")
e7_payload = {
    "user_id": USER_ID,
    "message": "What's surfacing in me right now?",
    "lens": "enneagram",
    "session_id": f"life-test-e7-{uuid.uuid4().hex[:6]}",
    "include_journal": True,
    "include_history": True,
    "life_domain": "self",
}
status, body = _post(e7_payload)

e7_pass = True
e7_failures = []
if status != 200:
    e7_pass = False
    e7_failures.append(f"HTTP {status}")
else:
    debug = body.get("debug") or {}
    mv = debug.get("master_voice")
    if mv is not None:
        e7_pass = False
        e7_failures.append(f"master_voice should be absent (lens wins), got: {mv}")
    print(f"  master_voice present: {mv is not None}")
print(f"  E7 result: {'PASS' if e7_pass else 'FAIL'}  failures={e7_failures}")

# ===========================================================================
# Summary
# ===========================================================================
print("\n" + "=" * 78)
results = {
    "E1 self activation": e1_pass,
    "E2 relationships + pattern_memory": e2_pass,
    "E3 session continuity": e3_pass,
    "E4 voice quality (jargon)": e4_pass,
    "E5 framework reveal": e5_pass,
    "E6 no regression (astrology lens)": e6_pass,
    "E7 mutual exclusion (lens wins)": e7_pass,
}
for k, v in results.items():
    print(f"  {'PASS' if v else 'FAIL'}  {k}")

print("\nE4 replies (qualitative excerpts):")
for dom, txt in e4_replies.items():
    print(f"\n  --- {dom} ---")
    print(f"  {txt[:500]}")

print("\nE1 response excerpt:")
print(f"  {e1_response_text[:320]}")
print("\nE2 response excerpt:")
print(f"  {e2_response_text[:320]}")
print("\nE3 response excerpt:")
print(f"  {e3_response_text[:320]}")

overall = all(results.values())
print("\n" + ("OVERALL: PASS" if overall else "OVERALL: FAIL"))
