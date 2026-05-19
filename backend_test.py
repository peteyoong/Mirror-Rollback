"""
Zi Wei / Purple Star Integration (zi-wei-master-v1) — backend test.

Tests POST /api/mirror/chat with lens=zi_wei against the deployed backend.
"""
import json
import re
import os
import sys
import time
from typing import Any, Dict, Tuple

import requests

BASE = "https://behavioral-lens-2.preview.emergentagent.com/api"
PETE = "697f0c6abf35c0528ff06954"

FORBIDDEN_TOKENS = [
    "destiny", "fated", "guarantees", "you are meant to", "your true role",
    "zi wei", "ziwei", "tian fu", "tan lang", "qi sha", "po jun", "wu qu",
    "tian xiang", "tian ji", "tai yang", "tai yin", "lian zhen",
    "ju men", "tian tong", "tian liang",
    "hua lu", "hua quan", "hua ke", "hua ji",
    "命宫", "palace", "purple star",
]

PROBABILISTIC_MARKERS = [
    "tends to", "may ", " may.", "often", "under pressure",
    "in some phases", " can ", "can be", "sometimes",
]


def post_chat(body: Dict[str, Any], timeout: int = 90) -> Tuple[int, Dict[str, Any]]:
    r = requests.post(f"{BASE}/mirror/chat", json=body, timeout=timeout)
    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, {"_raw": r.text}


def check_forbidden(text: str) -> list:
    """Return list of forbidden tokens found in text (case-insensitive)."""
    t = text.lower()
    return [tok for tok in FORBIDDEN_TOKENS if tok in t]


def check_probabilistic(text: str) -> list:
    """Return list of probabilistic markers found in reply."""
    t = text.lower()
    return [m for m in PROBABILISTIC_MARKERS if m.strip() in t]


def section(title: str):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def main():
    summary = {"passed": [], "failed": [], "soft_warnings": []}

    # ---------------------------------------------------------------
    # TEST 1: Pete + lens=zi_wei base call
    # ---------------------------------------------------------------
    section("TEST 1 — POST /api/mirror/chat lens=zi_wei (Pete)")
    body1 = {
        "user_id": PETE,
        "lens": "zi_wei",
        "message": "What does my chart say about how I handle pressure at work?",
        "include_journal": False,
        "include_history": False,
    }
    status1, data1 = post_chat(body1, timeout=120)
    print(f"HTTP status: {status1}")
    if status1 != 200:
        print(f"BODY: {json.dumps(data1)[:1500]}")
        summary["failed"].append(f"T1 HTTP {status1}")
        write_report(summary, data1, None)
        print_summary(summary)
        return

    reply1 = data1.get("response") or data1.get("reply") or ""
    debug1 = data1.get("debug") or {}
    print(f"reply length: {len(reply1)}")
    print(f"reply preview: {reply1[:600]}")
    print(f"debug keys: {list(debug1.keys())}")
    print(f"debug.marker: {debug1.get('marker')}")
    print(f"debug.lens: {debug1.get('lens')}")
    if "lens_chat" in debug1:
        print(f"debug.lens_chat.marker: {debug1['lens_chat'].get('marker')}")
        print(f"debug.lens_chat.lens: {debug1['lens_chat'].get('lens')}")

    if status1 == 200:
        summary["passed"].append("T1a HTTP 200")
    else:
        summary["failed"].append(f"T1a HTTP {status1}")

    lc = debug1.get("lens_chat") or {}
    actual_marker = lc.get("marker") or debug1.get("marker")
    actual_lens = lc.get("lens") or debug1.get("lens")
    if actual_marker == "multi-lens-chat-memory-v1":
        summary["passed"].append("T1b lens_chat marker == multi-lens-chat-memory-v1")
    else:
        summary["failed"].append(f"T1b lens_chat marker mismatch: got {actual_marker!r} (expected multi-lens-chat-memory-v1)")

    if actual_lens == "zi_wei":
        summary["passed"].append("T1c lens_chat lens == zi_wei")
    else:
        summary["failed"].append(f"T1c lens_chat lens mismatch: got {actual_lens!r} (expected zi_wei)")

    forbidden_found = check_forbidden(reply1)
    if not forbidden_found:
        summary["passed"].append("T1d no forbidden jargon tokens in reply")
    else:
        summary["failed"].append(f"T1d forbidden tokens found in reply: {forbidden_found}")

    prob_found = check_probabilistic(reply1)
    if prob_found:
        summary["passed"].append(f"T1e probabilistic markers present: {prob_found[:3]}")
    else:
        summary["failed"].append("T1e no probabilistic / behavioural markers in reply")

    gs = lc.get("grounding_sources") or debug1.get("grounding_sources") or []
    if gs:
        summary["passed"].append(f"T1f grounding_sources_present: {gs}")
    else:
        summary["soft_warnings"].append("T1f grounding_sources empty in debug payload")

    # ---------------------------------------------------------------
    # TEST 2: Follow-up referent ("How does that show up in relationships?")
    # ---------------------------------------------------------------
    section("TEST 2 — Follow-up referent ('How does that show up in relationships?')")
    session_id = data1.get("session_id")
    body2 = {
        "user_id": PETE,
        "lens": "zi_wei",
        "message": "How does that show up in relationships?",
        "session_id": session_id,
        "include_journal": False,
        "include_history": True,
    }
    status2, data2 = post_chat(body2, timeout=120)
    print(f"HTTP status: {status2}")
    reply2 = data2.get("response") or data2.get("reply") or ""
    debug2 = data2.get("debug") or {}
    lc2 = debug2.get("lens_chat") or {}
    print(f"reply preview: {reply2[:600]}")
    print(f"debug2 keys: {list(debug2.keys())}")
    print(f"debug2.lens_chat: {lc2}")
    print(f"debug2.active_entity: {lc2.get('active_entity') or debug2.get('active_entity')}")

    if status2 == 200:
        summary["passed"].append("T2a HTTP 200 on follow-up")
    else:
        summary["failed"].append(f"T2a HTTP {status2} on follow-up")

    forbidden_found2 = check_forbidden(reply2)
    if not forbidden_found2:
        summary["passed"].append("T2b no forbidden tokens in follow-up reply")
    else:
        summary["failed"].append(f"T2b forbidden tokens in follow-up reply: {forbidden_found2}")

    prob_found2 = check_probabilistic(reply2)
    if prob_found2:
        summary["passed"].append("T2c probabilistic markers in follow-up reply")
    else:
        summary["soft_warnings"].append("T2c no probabilistic markers in follow-up reply")

    active_ent = lc2.get("active_entity") or debug2.get("active_entity")
    if active_ent:
        summary["passed"].append(f"T2d active_entity resolved on referent: {active_ent}")
    else:
        summary["soft_warnings"].append(
            "T2d active_entity empty on referent follow-up — soft warning (not blocking)"
        )

    # ---------------------------------------------------------------
    # TEST 3: Missing birth-date probe (direct module call)
    # ---------------------------------------------------------------
    section("TEST 3 — Missing birth_date probe (direct module call)")
    try:
        sys.path.insert(0, "/app/backend")
        from services.lens_registries.zi_wei import ZI_WEI_REGISTRY  # type: ignore
        empty_ctx = {"user": {}, "chart": {}}
        ms = ZI_WEI_REGISTRY.missing_sources(empty_ctx)
        gs_empty = ZI_WEI_REGISTRY.grounding_sources_present(empty_ctx)
        print(f"missing_sources (no user) = {ms}")
        print(f"grounding_sources_present (no user) = {gs_empty}")
        if any("birth date missing" in m.lower() for m in ms):
            summary["passed"].append("T3a missing_sources includes 'birth date missing — cannot build profile'")
        else:
            summary["failed"].append(f"T3a missing_sources missing expected entry: {ms}")
        if gs_empty == []:
            summary["passed"].append("T3b grounding_sources_present empty when no birth_date")
        else:
            summary["failed"].append(f"T3b grounding_sources_present should be [] when no birth_date, got: {gs_empty}")

        pete_ctx = {"user": {"birth_date": "1968-04-01", "birth_time": "01:25", "birth_time_accuracy": "exact"}, "chart": {}}
        gs_pete = ZI_WEI_REGISTRY.grounding_sources_present(pete_ctx)
        print(f"grounding_sources_present (Pete-like) = {gs_pete}")
        if gs_pete:
            summary["passed"].append(f"T3c Pete grounding_sources_present non-empty: {gs_pete}")
        else:
            summary["failed"].append("T3c Pete grounding_sources_present empty")
    except Exception as e:
        summary["failed"].append(f"T3 exception: {type(e).__name__}: {e}")

    # ---------------------------------------------------------------
    # TEST 4: Stability — call interpreter twice
    # ---------------------------------------------------------------
    section("TEST 4 — Stability of zi_wei profile (deterministic)")
    try:
        from services.zi_wei_interpreter import compute_zi_wei_profile  # type: ignore
        p1 = compute_zi_wei_profile(birth_date="1968-04-01", birth_time="01:25", birth_time_accuracy="exact")
        p2 = compute_zi_wei_profile(birth_date="1968-04-01", birth_time="01:25", birth_time_accuracy="exact")
        ms1 = p1.get("major_stars")
        ms2 = p2.get("major_stars")
        print(f"major_stars run1: {ms1}")
        print(f"major_stars run2: {ms2}")
        if ms1 == ms2:
            summary["passed"].append("T4a major_stars identical across two consecutive calls (deterministic)")
        else:
            summary["failed"].append(f"T4a major_stars NOT identical: {ms1} vs {ms2}")

        dp1 = p1.get("dominant_patterns")
        dp2 = p2.get("dominant_patterns")
        if dp1 == dp2:
            summary["passed"].append("T4b dominant_patterns identical across runs")
        else:
            summary["failed"].append(f"T4b dominant_patterns differ across runs: {dp1} vs {dp2}")

        wp1 = p1.get("work_patterns")
        wp2 = p2.get("work_patterns")
        if wp1 == wp2:
            summary["passed"].append("T4c work_patterns identical across runs")
        else:
            summary["failed"].append(f"T4c work_patterns differ across runs: {wp1} vs {wp2}")
    except Exception as e:
        summary["failed"].append(f"T4 exception: {type(e).__name__}: {e}")

    # ---------------------------------------------------------------
    # TEST 5: API stability (two calls with same Pete body)
    # ---------------------------------------------------------------
    section("TEST 5 — API stability w/ Pete")
    body5 = {
        "user_id": PETE,
        "lens": "zi_wei",
        "message": "What does my chart say about how I handle pressure at work?",
        "include_journal": False,
        "include_history": False,
    }
    _, data5a = post_chat(body5, timeout=120)
    time.sleep(1)
    _, data5b = post_chat(body5, timeout=120)
    debug5a = data5a.get("debug") or {}
    debug5b = data5b.get("debug") or {}
    gs5a = (debug5a.get("lens_chat") or {}).get("grounding_sources") or debug5a.get("grounding_sources") or []
    gs5b = (debug5b.get("lens_chat") or {}).get("grounding_sources") or debug5b.get("grounding_sources") or []
    if gs5a == gs5b and gs5a:
        summary["passed"].append("T5 grounding_sources stable across two consecutive Pete API calls")
    elif not gs5a and not gs5b:
        summary["soft_warnings"].append("T5 grounding_sources empty in both calls — cannot verify stability via API")
    else:
        summary["failed"].append(f"T5 grounding_sources differ: {gs5a} vs {gs5b}")

    write_report(summary, data1, data2)
    print_summary(summary)
    return summary


def print_summary(summary):
    section("RESULTS SUMMARY")
    print(f"PASSED ({len(summary['passed'])}):")
    for x in summary["passed"]:
        print(f"  PASS {x}")
    print(f"\nFAILED ({len(summary['failed'])}):")
    for x in summary["failed"]:
        print(f"  FAIL {x}")
    print(f"\nSOFT WARNINGS ({len(summary['soft_warnings'])}):")
    for x in summary["soft_warnings"]:
        print(f"  WARN {x}")


def write_report(summary, data1, data2):
    try:
        with open("/app/backend_test_report.json", "w") as fh:
            json.dump({
                "summary": summary,
                "reply1_excerpt": ((data1 or {}).get("response") or "")[:2000] if data1 else None,
                "reply2_excerpt": ((data2 or {}).get("response") or "")[:2000] if data2 else None,
                "debug1": (data1 or {}).get("debug"),
                "debug2": (data2 or {}).get("debug"),
            }, fh, indent=2, default=str)
    except Exception as e:
        print(f"Could not write report: {e}")


if __name__ == "__main__":
    main()
