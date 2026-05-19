"""
Backend test for Micro-Reflection v2 (build marker: micro-reflection-v2).

Tests E1–E7 per /app/test_result.md test plan.

Test user: Pete  697f0c6abf35c0528ff06954, pete@pulsifi.me
"""

import json
import os
import sys
import time
from typing import Any, Dict

import requests
from pymongo import MongoClient

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_URL = "https://narrative-flex-v1.preview.emergentagent.com/api"
PETE = "697f0c6abf35c0528ff06954"

# Mongo for direct hygiene + cleanup
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")

HEADERS = {"Content-Type": "application/json"}

PASS = "PASS"
FAIL = "FAIL"


def hr(t: str):
    print(f"\n{'=' * 70}\n{t}\n{'=' * 70}")


# ---------------------------------------------------------------------------
# Mongo helpers (sync via pymongo)
# ---------------------------------------------------------------------------

_client = MongoClient(MONGO_URL)
_db = _client[DB_NAME]


def wipe_pete():
    return _db.micro_reflections.delete_many({"user_id": PETE}).deleted_count


def fetch_raw_docs():
    return list(_db.micro_reflections.find({"user_id": PETE}))


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def post_reflection(body: Dict[str, Any]):
    return requests.post(
        f"{BASE_URL}/micro-reflection", headers=HEADERS, data=json.dumps(body), timeout=30
    )


def get_recent(user_id: str, limit: int = 5):
    return requests.get(
        f"{BASE_URL}/micro-reflection/{user_id}/recent?limit={limit}", timeout=30
    )


def mirror_chat(message: str, lens=None, life_domain=None):
    body = {
        "user_id": PETE,
        "message": message,
        "include_history": True,
        "include_journal": False,
    }
    if lens is not None:
        body["lens"] = lens
    if life_domain is not None:
        body["life_domain"] = life_domain
    return requests.post(
        f"{BASE_URL}/mirror/chat", headers=HEADERS, data=json.dumps(body), timeout=180
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

results: Dict[str, Dict[str, Any]] = {}


def record(name, ok, detail=""):
    results[name] = {"ok": ok, "detail": detail}
    sym = PASS if ok else FAIL
    print(f"[{sym}] {name}  {detail}")


def e1_single_tap():
    hr("E1. Single tap stores successfully")
    body = {
        "user_id": PETE,
        "label": "lands",
        "source": "mirror",
        "context_lens": "astrology",
    }
    r = post_reflection(body)
    if r.status_code != 200:
        record("E1.status", False, f"got {r.status_code}: {r.text[:200]}")
        return
    record("E1.status", True, "HTTP 200")
    data = r.json()
    record("E1.ok_field", data.get("ok") is True, f"ok={data.get('ok')}")
    record("E1.marker", data.get("marker") == "micro-reflection-v2",
           f"marker={data.get('marker')}")
    refl = data.get("reflection") or {}
    rid = refl.get("id")
    import re
    uuid_re = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
    ok_uuid = bool(rid and uuid_re.match(rid))
    record("E1.uuid_id", ok_uuid, f"id={rid}")
    must = {"user_id": PETE, "label": "lands", "source": "mirror"}
    for k, v in must.items():
        record(f"E1.refl.{k}", refl.get(k) == v, f"got {refl.get(k)!r}")
    record("E1.refl.ts", bool(refl.get("ts")), f"ts={refl.get('ts')}")


def e2_validation():
    hr("E2. Validation")
    # Invalid label
    r = post_reflection({"user_id": PETE, "label": "invalid_label", "source": "mirror"})
    ok = r.status_code == 400 and ("lands" in r.text.lower() or "allowed" in r.text.lower())
    record("E2.invalid_label_400", ok, f"status={r.status_code}, body={r.text[:200]}")

    # Invalid texture
    r = post_reflection(
        {"user_id": PETE, "label": "lands", "source": "mirror", "texture": "invalid_tex"}
    )
    ok = r.status_code == 400 and ("tense" in r.text.lower() or "allowed" in r.text.lower())
    record("E2.invalid_texture_400", ok, f"status={r.status_code}, body={r.text[:200]}")


def e3_get_recent():
    hr("E3. GET recent")
    r = get_recent(PETE, limit=5)
    if r.status_code != 200:
        record("E3.status", False, f"got {r.status_code}: {r.text[:200]}")
        return
    record("E3.status", True)
    data = r.json()
    record("E3.marker", data.get("marker") == "micro-reflection-v2", f"{data.get('marker')}")
    record("E3.user_id", data.get("user_id") == PETE)
    refls = data.get("reflections")
    record("E3.refls_list", isinstance(refls, list), f"type={type(refls).__name__}")

    # newest-first
    if isinstance(refls, list) and len(refls) >= 2:
        ts_list = [r.get("ts") for r in refls]
        is_desc = all(ts_list[i] >= ts_list[i + 1] for i in range(len(ts_list) - 1))
        record("E3.newest_first", is_desc, f"ts_order={ts_list[:3]}")
    else:
        record("E3.newest_first", True, "fewer than 2 to compare")

    summ = data.get("summary") or {}
    required = [
        "counts_label", "counts_texture", "growth_score",
        "resistance_score", "resonance_score",
        "per_pattern_growth", "per_pattern_resistance",
        "lookback_days", "marker", "total",
    ]
    missing = [k for k in required if k not in summ]
    record("E3.summary_fields", not missing, f"missing={missing}")
    return data


def e4_softening_loop():
    hr("E4. Softening-with-pattern loop integration")
    wipe_pete()
    # Seed 3
    for i in range(3):
        r = post_reflection({
            "user_id": PETE,
            "label": "less_intense",
            "source": "life_tab",
            "context_pattern_keys": ["work_exhaustion"],
            "context_life_domain": "work",
        })
        if r.status_code != 200:
            record("E4.seed", False, f"seed {i} status={r.status_code} body={r.text[:200]}")
            return
    record("E4.seed", True, "3 less_intense seeded")

    # Now do mirror chat
    r = mirror_chat("checking in today", lens=None, life_domain="work")
    if r.status_code != 200:
        record("E4.chat_status", False, f"status={r.status_code}: {r.text[:500]}")
        return
    record("E4.chat_status", True)
    body = r.json()
    debug = body.get("debug") or {}
    micro = debug.get("micro_reflection")
    if not micro:
        record("E4.micro_present", False, f"debug keys: {list(debug.keys())}")
        return
    record("E4.micro_present", True, f"keys={list(micro.keys())}")
    record("E4.marker", micro.get("marker") == "micro-reflection-v2",
           f"marker={micro.get('marker')}")
    softened = micro.get("softened_patterns") or []
    record("E4.softened_includes_work_exhaustion",
           "work_exhaustion" in softened,
           f"softened={softened}")
    record("E4.loop_applied",
           micro.get("loop_applied") == "softening_with_pattern",
           f"loop_applied={micro.get('loop_applied')}")
    # Surveillance language check
    reply = (body.get("response") or "").lower()
    forbidden = ["you tapped", "your reflections", "i'm tracking",
                 "im tracking", "tracking your", "your taps"]
    hits = [f for f in forbidden if f in reply]
    record("E4.no_surveillance_language", not hits, f"hits={hits}")
    print(f"\n[E4 FULL DEBUG MICRO_REFLECTION]\n{json.dumps(micro, indent=2)}")
    print(f"\n[E4 LLM REPLY]\n{body.get('response')}\n")
    return body


def e5_resistance_loop():
    hr("E5. Resistance loop")
    wipe_pete()
    for i in range(3):
        r = post_reflection({
            "user_id": PETE,
            "label": "resisting",
            "source": "life_tab",
            "context_pattern_keys": ["work_exhaustion"],
        })
        if r.status_code != 200:
            record("E5.seed", False, f"status={r.status_code} body={r.text[:200]}")
            return
    record("E5.seed", True, "3 resisting seeded")

    r = mirror_chat("checking in today", lens=None, life_domain="work")
    if r.status_code != 200:
        record("E5.chat_status", False, f"status={r.status_code}: {r.text[:500]}")
        return
    record("E5.chat_status", True)
    body = r.json()
    debug = body.get("debug") or {}
    micro = debug.get("micro_reflection")
    if not micro:
        record("E5.micro_present", False)
        return
    record("E5.micro_present", True)
    stuck = micro.get("stuck_patterns") or []
    record("E5.stuck_includes_work_exhaustion",
           "work_exhaustion" in stuck,
           f"stuck={stuck}")
    record("E5.loop_applied",
           micro.get("loop_applied") == "resistance_recent",
           f"loop_applied={micro.get('loop_applied')}")
    reply = (body.get("response") or "")
    print(f"\n[E5 FULL DEBUG MICRO_REFLECTION]\n{json.dumps(micro, indent=2)}")
    print(f"\n[E5 LLM REPLY]\n{reply}\n")
    # Soft check: no aggressive insight push
    aggressive = ["you should", "you must", "you need to"]
    hits = [a for a in aggressive if a in reply.lower()]
    record("E5.tone_soft_no_aggressive", not hits, f"hits={hits}")
    return body


def e6_no_signal():
    hr("E6. No-signal idle")
    wipe_pete()
    r = mirror_chat("checking in today", lens=None, life_domain="work")
    if r.status_code != 200:
        record("E6.chat_status", False, f"status={r.status_code}: {r.text[:500]}")
        return
    record("E6.chat_status", True)
    body = r.json()
    debug = body.get("debug") or {}
    micro = debug.get("micro_reflection")
    if not micro:
        record("E6.micro_present", False, f"debug keys={list(debug.keys())}")
        return
    record("E6.micro_present", True)
    record("E6.loop_applied_null", micro.get("loop_applied") is None,
           f"loop_applied={micro.get('loop_applied')}")
    record("E6.total_recent_zero", micro.get("total_recent") == 0,
           f"total_recent={micro.get('total_recent')}")
    print(f"\n[E6 FULL DEBUG MICRO_REFLECTION]\n{json.dumps(micro, indent=2)}")


def e7_hygiene():
    hr("E7. Data hygiene")
    # Seed one to ensure docs exist
    post_reflection({"user_id": PETE, "label": "lands", "source": "mirror"})
    docs = fetch_raw_docs()
    record("E7.docs_exist", len(docs) > 0, f"count={len(docs)}")
    allowed = {
        "_id", "id", "user_id", "ts", "label", "texture",
        "source", "source_session", "source_message",
        "context_pattern_keys", "context_lens",
        "context_life_domain", "context_about_person_id",
    }
    all_ok = True
    extra_fields_global = set()
    for d in docs:
        extras = set(d.keys()) - allowed
        if extras:
            all_ok = False
            extra_fields_global |= extras
    record("E7.fields_only_whitelisted", all_ok,
           f"extra_fields={extra_fields_global}")
    record("E7.no_raw_text_field",
           "text" not in extra_fields_global and "message" not in extra_fields_global)
    if docs:
        sample = dict(docs[0])
        sample["_id"] = str(sample.get("_id"))
        sample["ts"] = str(sample.get("ts"))
        print(f"\n[E7 SAMPLE DOC]\n{json.dumps(sample, indent=2, default=str)}")


def cleanup():
    hr("Cleanup")
    cnt = wipe_pete()
    print(f"Deleted {cnt} reflections for Pete")


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def main():
    e1_single_tap()
    e2_validation()
    e3_get_recent()
    e4_softening_loop()
    time.sleep(1)
    e5_resistance_loop()
    time.sleep(1)
    e6_no_signal()
    e7_hygiene()
    cleanup()

    hr("SUMMARY")
    passed = sum(1 for r in results.values() if r["ok"])
    total = len(results)
    print(f"{passed}/{total} assertions passed")
    fails = [k for k, v in results.items() if not v["ok"]]
    if fails:
        print("\nFAILURES:")
        for k in fails:
            print(f"  [{FAIL}] {k}: {results[k]['detail']}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
