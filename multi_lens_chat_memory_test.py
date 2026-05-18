"""
End-to-end test for multi-lens-chat-memory-v1 across 5 lens chats.

Endpoint: POST /api/mirror/chat
User: Pete (697f0c6abf35c0528ff06954)
"""

import os
import json
import time
import uuid
import requests
from typing import Any, Dict, List, Optional, Tuple

# Use public URL only
BASE_URL = "https://individual-maps-v1.preview.emergentagent.com/api"
USER_ID = "697f0c6abf35c0528ff06954"

results: List[Dict[str, Any]] = []


def chat(
    lens: Optional[str],
    message: str,
    session_id: Optional[str],
    timeout: int = 90,
) -> Tuple[int, Dict[str, Any]]:
    payload = {
        "user_id": USER_ID,
        "message": message,
        "include_journal": False,
        "include_history": True,
    }
    if lens is not None:
        payload["lens"] = lens
    if session_id is not None:
        payload["session_id"] = session_id
    try:
        r = requests.post(f"{BASE_URL}/mirror/chat", json=payload, timeout=timeout)
        try:
            data = r.json()
        except Exception:
            data = {"_raw": r.text[:500]}
        return r.status_code, data
    except Exception as e:
        return -1, {"error": str(e)}


def record(name: str, ok: bool, info: Dict[str, Any]):
    results.append({"name": name, "pass": ok, "info": info})
    status = "PASS" if ok else "FAIL"
    print(f"\n[{status}] {name}")
    for k, v in info.items():
        if isinstance(v, str) and len(v) > 240:
            v = v[:240] + "..."
        print(f"   {k}: {v}")


def pad_debug(data: Dict[str, Any]) -> Dict[str, Any]:
    d = data.get("debug") if isinstance(data, dict) else None
    if not d:
        return {
            "marker": None,
            "lens": None,
            "active_entity": None,
            "active_entity_source": None,
            "grounding_sources": [],
            "missing_sources": [],
            "history_entities": [],
        }
    return {
        "marker": d.get("marker"),
        "lens": d.get("lens"),
        "active_entity": d.get("active_entity"),
        "active_entity_source": d.get("active_entity_source"),
        "grounding_sources": d.get("grounding_sources", []),
        "missing_sources": d.get("missing_sources", []),
        "history_entities": d.get("recent_history_entities", []),
    }


def first200(data: Dict[str, Any]) -> str:
    return (data.get("response") or "")[:200] if isinstance(data, dict) else ""


# =============================================================================
# A. Astrology regression  (3 turns same session — Jupiter referent chain)
# =============================================================================
print("\n" + "=" * 78)
print("A. Astrology regression — Jupiter referent chain")
print("=" * 78)

session_A = f"test-astro-{uuid.uuid4().hex[:8]}"

# Turn 1
status, data = chat("astrology", "Where does Jupiter sit in my chart and what does that mean?", session_A)
d = pad_debug(data)
ok = (
    status == 200
    and d["marker"] == "multi-lens-chat-memory-v1"
    and d["lens"] == "astrology"
    and (d["active_entity"] or {}).get("name") == "Jupiter"
    and d["active_entity_source"] == "current"
)
record("A.T1 Jupiter (current)", ok, {
    "status": status,
    "debug": d,
    "response": first200(data),
})

time.sleep(1)

# Turn 2
status, data = chat("astrology", "Oh so that sits in house 4 for me?", session_A)
d = pad_debug(data)
name = (d["active_entity"] or {}).get("name")
ok = (
    status == 200
    and d["marker"] == "multi-lens-chat-memory-v1"
    and name == "Jupiter"
    and d["active_entity_source"] == "referent"
    and "jupiter" in (data.get("response") or "").lower()
)
record("A.T2 Jupiter (referent, not Nodes/Sun)", ok, {
    "status": status,
    "debug": d,
    "response": first200(data),
})

time.sleep(1)

# Turn 3
status, data = chat("astrology", "And which house does that actually sit in?", session_A)
d = pad_debug(data)
name = (d["active_entity"] or {}).get("name")
ok = (
    status == 200
    and d["marker"] == "multi-lens-chat-memory-v1"
    and name == "Jupiter"
    and d["active_entity_source"] == "referent"
    and "jupiter" in (data.get("response") or "").lower()
)
record("A.T3 Jupiter (referent)", ok, {
    "status": status,
    "debug": d,
    "response": first200(data),
})

# =============================================================================
# B. Human Design referent resolution
# =============================================================================
print("\n" + "=" * 78)
print("B. Human Design referent resolution")
print("=" * 78)

session_B = f"test-hd-{uuid.uuid4().hex[:8]}"

# Turn 1
status, data = chat("human_design", "What is my Authority and what does it mean?", session_B)
d = pad_debug(data)
name = (d["active_entity"] or {}).get("name")
kind = (d["active_entity"] or {}).get("kind")
ok = (
    status == 200
    and d["marker"] == "multi-lens-chat-memory-v1"
    and d["lens"] == "human_design"
    and name == "Authority"
    and d["active_entity_source"] == "current"
)
record("B.T1 Authority (current)", ok, {
    "status": status,
    "debug": d,
    "response": first200(data),
})

time.sleep(1)

# Turn 2
status, data = chat("human_design", "How does that show up under pressure?", session_B)
d = pad_debug(data)
name = (d["active_entity"] or {}).get("name")
ok = (
    status == 200
    and name == "Authority"
    and d["active_entity_source"] == "referent"
)
record("B.T2 Authority (referent)", ok, {
    "status": status,
    "debug": d,
    "response": first200(data),
})

time.sleep(1)

# Turn 3
status, data = chat("human_design", "What about my Profile?", session_B)
d = pad_debug(data)
name = (d["active_entity"] or {}).get("name")
grounding = d["grounding_sources"]
expected_grounding_present = all(
    any(g.lower() == s.lower() or s.lower() in g.lower() for g in grounding)
    for s in ["Type", "Strategy", "Authority", "Profile"]
)
ok = (
    status == 200
    and name == "Profile"
    and d["active_entity_source"] == "current"
    and expected_grounding_present
)
record("B.T3 Profile (current, explicit pivot)", ok, {
    "status": status,
    "debug": d,
    "response": first200(data),
    "expected_grounding_present": expected_grounding_present,
})

# =============================================================================
# C. Numerology referent resolution
# =============================================================================
print("\n" + "=" * 78)
print("C. Numerology referent resolution")
print("=" * 78)

session_C = f"test-num-{uuid.uuid4().hex[:8]}"

# Turn 1
status, data = chat("numerology", "Tell me about my Life Path.", session_C)
d = pad_debug(data)
name = (d["active_entity"] or {}).get("name")
grounding = d["grounding_sources"]
has_life_path = any("life path" in g.lower() for g in grounding)
ok = (
    status == 200
    and d["marker"] == "multi-lens-chat-memory-v1"
    and d["lens"] == "numerology"
    and name == "Life Path"
    and d["active_entity_source"] == "current"
    and has_life_path
)
record("C.T1 Life Path (current)", ok, {
    "status": status,
    "debug": d,
    "response": first200(data),
    "has_life_path_grounding": has_life_path,
})

time.sleep(1)

# Turn 2
status, data = chat("numerology", "What does that mean for my career?", session_C)
d = pad_debug(data)
name = (d["active_entity"] or {}).get("name")
ok = (
    status == 200
    and name == "Life Path"
    and d["active_entity_source"] == "referent"
)
record("C.T2 Life Path (referent)", ok, {
    "status": status,
    "debug": d,
    "response": first200(data),
})

# =============================================================================
# D. Enneagram missing-data honesty (CRITICAL)
# =============================================================================
print("\n" + "=" * 78)
print("D. Enneagram (results may or may not exist)")
print("=" * 78)

session_D = f"test-enn-{uuid.uuid4().hex[:8]}"

# Check whether Pete has enneagram results
status_e, data_e = -1, None
try:
    re_ = requests.get(f"{BASE_URL}/enneagram/results/{USER_ID}", timeout=30)
    status_e = re_.status_code
    data_e = re_.json()
except Exception as ex:
    data_e = {"error": str(ex)}
has_enn_result = bool(data_e.get("has_result")) if isinstance(data_e, dict) else False
print(f"Pete enneagram results: has_result={has_enn_result} (status={status_e})")

# Turn 1
status, data = chat("enneagram", "What is my Enneagram type?", session_D)
d = pad_debug(data)
resp = (data.get("response") or "").lower()

if has_enn_result:
    name = (d["active_entity"] or {}).get("name")
    grounding = d["grounding_sources"]
    has_core_type = any("core type" in g.lower() for g in grounding)
    ok = (
        status == 200
        and d["marker"] == "multi-lens-chat-memory-v1"
        and d["lens"] == "enneagram"
        and name == "Core Type"
        and has_core_type
    )
    record("D.T1 Enneagram Core Type (has data)", ok, {
        "status": status,
        "debug": d,
        "response": first200(data),
        "has_core_type_grounding": has_core_type,
    })
else:
    missing = d["missing_sources"]
    mentions_missing = any(("enneagram" in m.lower() and ("not" in m.lower() or "missing" in m.lower())) for m in missing)
    # Response should not guess a type
    no_guess_phrases = [
        "i don't have your enneagram",
        "haven't completed",
        "not completed",
        "not been completed",
        "not computed",
        "no enneagram",
    ]
    response_honest = any(p in resp for p in no_guess_phrases)
    ok = status == 200 and mentions_missing and response_honest
    record("D.T1 Enneagram missing-data honesty (no result)", ok, {
        "status": status,
        "debug": d,
        "response": first200(data),
        "missing_mentions_enneagram": mentions_missing,
        "response_admits_missing": response_honest,
    })

# =============================================================================
# E. BaZi referent resolution
# =============================================================================
print("\n" + "=" * 78)
print("E. BaZi referent resolution")
print("=" * 78)

session_E = f"test-bz-{uuid.uuid4().hex[:8]}"

# Turn 1
status, data = chat("bazi", "What is my Day Master and what does it tell me?", session_E)
d = pad_debug(data)
name = (d["active_entity"] or {}).get("name")
grounding = d["grounding_sources"]
has_day_master = any("day master" in g.lower() for g in grounding)
has_four_pillars = any("four pillars" in g.lower() or "4 pillars" in g.lower() for g in grounding)
ok = (
    status == 200
    and d["marker"] == "multi-lens-chat-memory-v1"
    and d["lens"] == "bazi"
    and name == "Day Master"
    and d["active_entity_source"] == "current"
    and has_day_master
    and has_four_pillars
)
record("E.T1 Day Master (current)", ok, {
    "status": status,
    "debug": d,
    "response": first200(data),
    "grounding_has_day_master": has_day_master,
    "grounding_has_four_pillars": has_four_pillars,
})

time.sleep(1)

# Turn 2
status, data = chat("bazi", "How does that interact with my Month Pillar?", session_E)
d = pad_debug(data)
name = (d["active_entity"] or {}).get("name")
ok = (
    status == 200
    and name == "Month Pillar"
    and d["active_entity_source"] == "current"
)
record("E.T2 Month Pillar (explicit pivot wins over referent)", ok, {
    "status": status,
    "debug": d,
    "response": first200(data),
})

# =============================================================================
# F. Generalist regression
# =============================================================================
print("\n" + "=" * 78)
print("F. Generalist regression — debug=null")
print("=" * 78)

status, data = chat(None, "What did we just talk about?", None)
debug_field = data.get("debug") if isinstance(data, dict) else "missing"
ok = status == 200 and debug_field is None and isinstance(data.get("response"), str)
record("F. Generalist (debug=null)", ok, {
    "status": status,
    "debug_field": debug_field,
    "response_length": len(data.get("response") or "") if isinstance(data, dict) else 0,
    "response": first200(data),
})

# =============================================================================
# G. No-crash regression — ambiguous referent-only with empty session
# =============================================================================
print("\n" + "=" * 78)
print("G. No-crash regression for each lens")
print("=" * 78)

for lens in ["astrology", "human_design", "numerology", "enneagram", "bazi"]:
    status, data = chat(lens, "that's interesting, tell me more about that", "")
    d = pad_debug(data)
    ok = (
        status == 200
        and d["marker"] == "multi-lens-chat-memory-v1"
        and d["active_entity_source"] == "none"
        and bool(data.get("response"))
    )
    record(f"G. {lens} ambiguous referent (no crash)", ok, {
        "status": status,
        "debug": d,
        "response": first200(data),
    })

# =============================================================================
# Summary
# =============================================================================
print("\n" + "=" * 78)
print("SUMMARY")
print("=" * 78)
passed = sum(1 for r in results if r["pass"])
total = len(results)
print(f"{passed}/{total} tests PASSED")
for r in results:
    print(f"  [{'PASS' if r['pass'] else 'FAIL'}] {r['name']}")

# Write json artifact
with open("/app/multi_lens_chat_memory_results.json", "w") as f:
    json.dump(results, f, indent=2, default=str)

print(f"\nResults JSON: /app/multi_lens_chat_memory_results.json")
