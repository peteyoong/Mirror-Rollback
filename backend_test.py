"""
Backend tests for Evidence Drawer v2 (build marker: evidence-drawer-v2).
Exercises POST /api/mirror/chat and verifies the curated `evidence`
object alongside the unchanged `debug` field.
"""
from __future__ import annotations

import sys
from typing import Any, Dict, Optional

import requests

BASE_URL = "https://narrative-flex-v1.preview.emergentagent.com"
API = f"{BASE_URL}/api"
PETE = "697f0c6abf35c0528ff06954"
TIMEOUT = 90

JARGON_TOKENS = [
    "saturn", "mercury", "venus", "mars", "jupiter", "pluto",
    "sun in", "moon in", "gate", "channel ", "centre",
    "life path", "day master", "type 4", "type 7",
    "sacral", "manifestor", "projector", "generator",
    "natal", "transit", "ayanamsa",
]


def _post_chat(payload: Dict[str, Any]) -> requests.Response:
    return requests.post(f"{API}/mirror/chat", json=payload, timeout=TIMEOUT)


def _has_jargon(text: str) -> Optional[str]:
    s = (text or "").lower()
    for tok in JARGON_TOKENS:
        if tok in s:
            return tok
    return None


def _check_evidence_no_jargon(ev: Dict[str, Any]) -> Optional[str]:
    if not ev:
        return None
    mv = ev.get("master_voice") or {}
    candidates = []
    if mv.get("dominant_pattern"):
        candidates.append(mv["dominant_pattern"])
    if ev.get("recurrence"):
        candidates.append(ev["recurrence"])
    rel = ev.get("relational") or {}
    for item in rel.get("moderated_by") or []:
        candidates.append(item)
    for item in ev.get("calibration") or []:
        candidates.append(item)
    for c in candidates:
        if not isinstance(c, str):
            continue
        hit = _has_jargon(c)
        if hit:
            return f"{hit!r} found in: {c!r}"
    return None


results = []


def record(name: str, ok: bool, info: str = "") -> None:
    results.append((name, ok, info))
    badge = "PASS" if ok else "FAIL"
    print(f"[{badge}] {name}  {info}")


def test_e1_life_tab_master_voice():
    payload = {"user_id": PETE, "message": "What's surfacing in me right now?",
               "life_domain": "self", "lens": None}
    r = _post_chat(payload)
    record("E1.status_200", r.status_code == 200, f"got {r.status_code}")
    if r.status_code != 200:
        print(r.text[:500]); return None
    data = r.json()
    ev = data.get("evidence")
    record("E1.evidence_is_object", isinstance(ev, dict), f"evidence={ev!r}")
    if not isinstance(ev, dict):
        return data
    record("E1.evidence.marker", ev.get("marker") == "evidence-drawer-v2",
           f"marker={ev.get('marker')!r}")
    mv = ev.get("master_voice") or {}
    dp = mv.get("dominant_pattern")
    record("E1.master_voice.dominant_pattern",
           isinstance(dp, str) and len(dp) > 0, f"dominant_pattern={dp!r}")
    fws = mv.get("frameworks") or []
    record("E1.master_voice.frameworks_nonempty",
           isinstance(fws, list) and len(fws) >= 1, f"frameworks={fws}")
    record("E1.master_voice.frameworks_human_readable",
           all(f in {"Astrology", "Human Design", "Numerology", "Enneagram", "BaZi"} for f in fws),
           f"frameworks={fws}")
    cal = ev.get("calibration") or []
    record("E1.calibration_nonempty",
           isinstance(cal, list) and len(cal) >= 1, f"calibration={cal}")
    record("E1.debug_still_present", isinstance(data.get("debug"), dict))
    hit = _check_evidence_no_jargon(ev)
    record("E1.no_jargon_in_curated_text", hit is None, hit or "")
    return data


def test_e2_ask_about_person():
    person_id = None
    try:
        r = requests.get(f"{API}/people/{PETE}", timeout=TIMEOUT)
        record("E2.list_people_status", r.status_code == 200, f"got {r.status_code}")
        if r.status_code == 200:
            body = r.json()
            people = body.get("people") if isinstance(body, dict) else body
            if isinstance(people, list) and people:
                child = next((p for p in people if p.get("relationship_type") == "child"), None)
                person_id = (child or people[0]).get("id")
    except Exception as e:
        record("E2.list_people_status", False, f"exc={e}")

    if not person_id:
        try:
            cp = {"name": "Test Child Person", "relationship_type": "child",
                  "birth_date": "2015-04-12", "birth_time": None,
                  "birth_time_accuracy": "unknown", "birth_location": None,
                  "birth_location_accuracy": "unknown"}
            r = requests.post(f"{API}/people/{PETE}", json=cp, timeout=TIMEOUT)
            if r.status_code == 200:
                person_id = r.json().get("id")
                record("E2.create_person", True, f"id={person_id}")
            else:
                record("E2.create_person", False, f"got {r.status_code}: {r.text[:200]}")
        except Exception as e:
            record("E2.create_person", False, f"exc={e}")

    if not person_id:
        record("E2.skipped", False, "no person id available"); return None

    payload = {"user_id": PETE, "message": "What should I understand about them?",
               "about_person_id": person_id}
    r = _post_chat(payload)
    record("E2.chat_status_200", r.status_code == 200, f"got {r.status_code}")
    if r.status_code != 200:
        print(r.text[:500]); return None
    data = r.json()
    ev = data.get("evidence") or {}
    record("E2.evidence_is_object", isinstance(ev, dict), f"ev={ev!r}")
    rel = ev.get("relational") if isinstance(ev, dict) else None
    record("E2.relational.moderated_by_nonempty",
           bool(rel) and isinstance(rel.get("moderated_by"), list) and len(rel["moderated_by"]) >= 1,
           f"relational={rel!r}")
    cal = ev.get("calibration") if isinstance(ev, dict) else None
    record("E2.calibration_present", isinstance(cal, list) and len(cal) >= 1, f"calibration={cal}")
    dbg = data.get("debug") or {}
    record("E2.debug.relational_present", isinstance(dbg.get("relational"), dict),
           f"debug.relational={dbg.get('relational')!r}")
    hit = _check_evidence_no_jargon(ev if isinstance(ev, dict) else {})
    record("E2.no_jargon_in_curated_text", hit is None, hit or "")
    return data


def test_e3_generic_mirror_chat():
    payload = {"user_id": PETE, "message": "tell me what's interesting today"}
    r = _post_chat(payload)
    record("E3.status_200", r.status_code == 200, f"got {r.status_code}")
    if r.status_code != 200:
        print(r.text[:500]); return None
    data = r.json()
    ev = data.get("evidence")
    record("E3.evidence_is_object", isinstance(ev, dict), f"evidence={ev!r}")
    if isinstance(ev, dict):
        cal = ev.get("calibration") or []
        record("E3.calibration_nonempty",
               isinstance(cal, list) and len(cal) >= 1, f"calibration={cal}")
        hit = _check_evidence_no_jargon(ev)
        record("E3.no_jargon_in_curated_text", hit is None, hit or "")
    return data


def test_e4_curator_never_crashes():
    r1 = _post_chat({"user_id": PETE, "message": "   "})
    record("E4.empty_message_no_500", r1.status_code != 500, f"got {r1.status_code}")
    long_msg = "burnout " * 800
    r2 = _post_chat({"user_id": PETE, "message": long_msg})
    record("E4.long_message_no_500", r2.status_code != 500, f"got {r2.status_code}")
    r3 = _post_chat({"user_id": PETE, "message": "hi"})
    record("E4.short_message_no_500", r3.status_code != 500, f"got {r3.status_code}")
    if r3.status_code == 200:
        record("E4.short_message_has_response", isinstance(r3.json().get("response"), str))


def test_e6_recurrence_softness():
    payload = {"user_id": PETE,
               "message": "I am completely burned out from work again",
               "life_domain": "work"}
    r = _post_chat(payload)
    record("E6.status_200", r.status_code == 200, f"got {r.status_code}")
    if r.status_code != 200:
        print(r.text[:500]); return
    data = r.json()
    ev = data.get("evidence") or {}
    rec = ev.get("recurrence") if isinstance(ev, dict) else None
    dbg = data.get("debug") or {}
    pm = dbg.get("pattern_memory") or {}
    if rec:
        soft_tokens = ["surfaced", "recently", "this thread", "has surfaced", "this has"]
        is_soft = any(t in rec.lower() for t in soft_tokens)
        record("E6.recurrence_soft_language", is_soft, f"recurrence={rec!r}")
        bad_tokens = ["january", "february", "march", "april", "may", "june",
                      "july", "august", "september", "october", "november",
                      "december", "you said", '"', "'"]
        bad_hit = next((t for t in bad_tokens if t in rec.lower()), None)
        record("E6.recurrence_no_absolute_dates_quotes",
               bad_hit is None, f"hit={bad_hit!r}, recurrence={rec!r}")
    else:
        suppressed = pm.get("suppressed_due_to_fatigue") or pm.get("suppressed_keys")
        record("E6.recurrence_absent_ok_if_suppressed",
               bool(suppressed) or pm.get("matched_patterns") in (None, []),
               f"pattern_memory_keys={list(pm.keys())}")


def test_e7_backward_compat_debug(e1_data: Optional[Dict[str, Any]]):
    if not e1_data:
        record("E7.skipped_no_e1_data", False); return
    dbg = e1_data.get("debug")
    record("E7.debug_is_object", isinstance(dbg, dict), f"debug type={type(dbg).__name__}")
    if not isinstance(dbg, dict):
        return
    record("E7.debug.compression_or_intensity",
           any(k in dbg for k in ("compression_mode", "intensity_mode", "depth_mode")),
           f"keys={list(dbg.keys())}")
    mv = dbg.get("master_voice") or {}
    record("E7.debug.master_voice.marker",
           mv.get("marker") == "life-tab-master-voice-v1", f"marker={mv.get('marker')}")
    record("E7.debug.master_voice.domain", mv.get("domain") == "self",
           f"domain={mv.get('domain')}")
    record("E7.debug.master_voice.contributing_frameworks",
           isinstance(mv.get("contributing_frameworks"), list))
    record("E7.debug.master_voice.dominant_signal",
           isinstance(mv.get("dominant_signal"), dict))
    record("E7.debug.master_voice.signals_count",
           isinstance(mv.get("signals_count"), int))


def test_e8_saved_people_endpoint():
    r = requests.get(f"{API}/people/{PETE}", timeout=TIMEOUT)
    record("E8.status_200", r.status_code == 200, f"got {r.status_code}")
    if r.status_code != 200:
        print(r.text[:500]); return
    body = r.json()
    if isinstance(body, dict):
        people = body.get("people")
        record("E8.response_has_people_list", isinstance(people, list),
               f"keys={list(body.keys())}")
    else:
        people = body
        record("E8.response_is_list", isinstance(people, list))
    if isinstance(people, list) and people:
        sample = people[0]
        record("E8.birth_time_accuracy_serialised",
               sample.get("birth_time_accuracy") in {"exact", "unknown"},
               f"sample.birth_time_accuracy={sample.get('birth_time_accuracy')}")


if __name__ == "__main__":
    print(f"\n=== Evidence Drawer v2 backend test against {API} ===\n")
    e1 = test_e1_life_tab_master_voice()
    test_e2_ask_about_person()
    test_e3_generic_mirror_chat()
    test_e4_curator_never_crashes()
    test_e6_recurrence_softness()
    test_e7_backward_compat_debug(e1)
    test_e8_saved_people_endpoint()

    print("\n=== Summary ===")
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"{passed}/{total} checks passed")
    for name, ok, info in results:
        if not ok:
            print(f"  FAIL  {name}  {info}")
    sys.exit(0 if passed == total else 1)
