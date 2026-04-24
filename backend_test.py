"""
Backend tests for Life Synthesis Phase 3 (Lifeline + Pattern Memory integration).

Endpoints:
  GET /api/life/role-card/{user_id}
  GET /api/life/{context}/synthesis/{user_id}
  GET /api/life/{context}/today/{user_id}
  GET /api/life/{context}/evidence/{user_id}
"""
import json
import os
import sys
import time
from typing import Any, List, Tuple

import requests

BASE_URL = os.environ.get("BACKEND_BASE_URL") or "https://tension-mapper.preview.emergentagent.com"
API = f"{BASE_URL}/api"

PETE = "697f0c6abf35c0528ff06954"
MEL = "697ec826ad4b18f75bf42616"

BANNED_LENSES = [
    "human design",
    "astrology",
    "bazi",
    "manifestor",
    "reflector",
    "generator",
    "projector",
    "numerology",
    "enneagram",
    "gene keys",
]

EMPHASIS_PHRASES = [
    "harder to step away",
    "more than usual",
    "pull is stronger",
    "shows up more clearly",
]

results: List[Tuple[str, bool, str]] = []


def record(name: str, passed: bool, detail: str = ""):
    results.append((name, passed, detail))
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {name}")
    if detail:
        print(f"       {detail[:600]}")


def do_get(path: str, timeout: int = 180) -> Tuple[int, Any, float]:
    url = f"{API}{path}"
    t0 = time.time()
    try:
        r = requests.get(url, timeout=timeout)
        dt = time.time() - t0
        try:
            data = r.json()
        except Exception:
            data = {"_raw": r.text}
        return r.status_code, data, dt
    except Exception as e:
        return -1, {"_error": str(e)}, time.time() - t0


def trim_json(d: Any, limit: int = 2500) -> str:
    s = json.dumps(d, default=str)
    if len(s) > limit:
        return s[:limit] + "...[truncated]"
    return s


def test_pete_role_card():
    print("\n=== PETE: role-card ===")
    code, data, dt = do_get(f"/life/role-card/{PETE}?refresh=true")
    record("PETE role-card 200", code == 200, f"status={code} time={dt:.2f}s body={trim_json(data, 600)}")
    if code != 200:
        return None

    required = ["role", "tension", "distortion", "orientation", "not_for", "confidence", "dominant_drivers"]
    missing = [k for k in required if k not in data]
    record("PETE role-card has required fields", not missing, f"missing={missing}")

    confidence = data.get("confidence")
    record("PETE role-card confidence=high", confidence == "high", f"confidence={confidence!r}")

    drivers = data.get("dominant_drivers") or []
    record("PETE dominant_drivers is non-empty list", isinstance(drivers, list) and len(drivers) > 0, f"drivers={drivers}")

    drivers_joined = " | ".join(str(d).lower() for d in drivers)
    record("PETE drivers contain 'recurring tension'", "recurring tension" in drivers_joined, f"drivers={drivers}")
    record("PETE drivers contain 'lived history'", "lived history" in drivers_joined, f"drivers={drivers}")

    debug = data.get("debug") or {}
    llm_used = debug.get("llm_used")
    render_error = debug.get("render_error")
    ok_llm = (llm_used is True) or (llm_used is False and bool(render_error))
    record("PETE debug.llm_used=true (or render_error explains fallback)", ok_llm, f"llm_used={llm_used} render_error={render_error!r}")

    banned_hits = debug.get("banned_phrase_hits")
    bad_banned = []
    if banned_hits:
        if not isinstance(banned_hits, list):
            bad_banned = [banned_hits]
        else:
            for b in banned_hits:
                b_low = str(b).lower()
                for lens in BANNED_LENSES:
                    if lens in b_low:
                        bad_banned.append(b)
                        break
    record("PETE debug.banned_phrase_hits empty or free of lens names", not bad_banned, f"banned_hits={banned_hits}")

    text_fields = {k: data.get(k) for k in ["role", "tension", "distortion", "orientation", "not_for"]}
    rendered_bad = []
    for fname, fval in text_fields.items():
        if not isinstance(fval, str):
            continue
        low = fval.lower()
        for lens in BANNED_LENSES:
            if lens in low:
                rendered_bad.append((fname, lens, fval[:120]))
    record("PETE rendered fields free of lens names", not rendered_bad, f"rendered_bad={rendered_bad}")
    return data


def test_pete_synthesis(context: str):
    print(f"\n=== PETE: {context} synthesis ===")
    code, data, dt = do_get(f"/life/{context}/synthesis/{PETE}?refresh=true")
    record(f"PETE {context} synthesis 200", code == 200, f"status={code} time={dt:.2f}s body={trim_json(data, 500)}")
    if code != 200:
        return None

    has_role_card = isinstance(data.get("role_card"), dict)
    record(f"PETE {context} synthesis has role_card", has_role_card, "")

    ds = data.get("domain_synthesis") or {}
    for k in ["pattern", "default_tension", "distortion_under_pressure", "what_this_pattern_needs"]:
        v = ds.get(k)
        record(f"PETE {context} domain_synthesis.{k} non-empty", isinstance(v, str) and len(v.strip()) > 0, f"value={v!r}")

    ev = data.get("evidence_signals") or []
    record(f"PETE {context} evidence_signals 3-5 items", isinstance(ev, list) and 3 <= len(ev) <= 5, f"len={len(ev) if isinstance(ev, list) else 'not list'}")

    if isinstance(ev, list):
        for i, sig in enumerate(ev):
            has_keys = isinstance(sig, dict) and all(k in sig for k in ("lens", "signal", "weight"))
            record(f"PETE {context} evidence_signals[{i}] has lens/signal/weight", has_keys, f"sig={sig}")

        if context == "work":
            pm = next((s for s in ev if isinstance(s, dict) and str(s.get("lens", "")).lower() == "pattern_memory"), None)
            record("PETE work has pattern_memory signal", pm is not None, f"lenses={[s.get('lens') for s in ev if isinstance(s, dict)]}")
            if pm:
                w = pm.get("weight", 0)
                record("PETE work pattern_memory weight>=0.7", isinstance(w, (int, float)) and w >= 0.7, f"weight={w}")
                signal_text = str(pm.get("signal", ""))
                low = signal_text.lower()
                has_repeat = (
                    "\u00d7" in signal_text  # unicode multiplication sign
                    or "×" in signal_text
                    or "repeated" in low
                    or "repeat" in low
                    or any(f"{n}x" in low.replace(" ", "") for n in ["2", "3", "4", "5", "6", "7", "8", "9"])
                )
                record("PETE work pattern_memory signal contains repeat count", has_repeat, f"signal={signal_text!r}")

            ll = next((s for s in ev if isinstance(s, dict) and str(s.get("lens", "")).lower() == "lifeline_echoes"), None)
            record("PETE work has lifeline_echoes signal", ll is not None, f"lenses={[s.get('lens') for s in ev if isinstance(s, dict)]}")
            if ll:
                w = ll.get("weight", 0)
                record("PETE work lifeline_echoes weight>=0.5", isinstance(w, (int, float)) and w >= 0.5, f"weight={w}")
                signal_text = str(ll.get("signal", ""))
                low = signal_text.lower()
                has_count = any(ch.isdigit() for ch in signal_text) and (
                    "event" in low or "moment" in low or "time" in low or "history" in low or "×" in signal_text
                )
                record("PETE work lifeline_echoes signal mentions event count", has_count, f"signal={signal_text!r}")
    return data


def test_pete_cross_domain_differs(work_data, rel_data, self_data):
    print("\n=== PETE: cross-domain differ ===")
    ds_map = {}
    for name, data in (("work", work_data), ("relationships", rel_data), ("self", self_data)):
        if not data:
            continue
        ds = data.get("domain_synthesis") or {}
        ds_map[name] = {k: (ds.get(k) or "").strip() for k in ["pattern", "default_tension", "distortion_under_pressure", "what_this_pattern_needs"]}
    if len(ds_map) < 3:
        record("PETE cross-domain differ (all 3 available)", False, f"only have {list(ds_map.keys())}")
        return
    for key in ["pattern", "default_tension", "distortion_under_pressure", "what_this_pattern_needs"]:
        vals = {dom: ds_map[dom][key] for dom in ds_map}
        all_same = len(set(vals.values())) == 1 and all(v for v in vals.values())
        record(f"PETE {key} differs across domains", not all_same, f"vals={vals}")


def test_pete_work_today():
    print("\n=== PETE: work today ===")
    code, data, dt = do_get(f"/life/work/today/{PETE}?refresh=true")
    record("PETE work today 200", code == 200, f"status={code} time={dt:.2f}s body={trim_json(data, 600)}")
    if code != 200:
        return None

    intensity = data.get("intensity_level")
    record("PETE work today intensity_level=high", intensity == "high", f"intensity_level={intensity!r}")

    reasons = data.get("intensity_reasons") or []
    reasons_joined = " | ".join(str(r).lower() for r in reasons)
    record("PETE work today intensity_reasons contains 'pattern is cycling'", "pattern is cycling" in reasons_joined, f"reasons={reasons}")
    record("PETE work today intensity_reasons contains 'recent lived events echo the pattern'", "recent lived events echo the pattern" in reasons_joined, f"reasons={reasons}")

    text_candidates = []
    for k, v in data.items():
        if isinstance(v, str):
            text_candidates.append((k, v))
        elif isinstance(v, dict):
            for k2, v2 in v.items():
                if isinstance(v2, str):
                    text_candidates.append((f"{k}.{k2}", v2))

    over_cap = []
    for fname, text in text_candidates:
        low = text.lower()
        hits = sum(1 for p in EMPHASIS_PHRASES if p in low)
        if hits > 2:
            over_cap.append((fname, hits, text[:200]))
    record("PETE work today no field stacks more than 2 emphasis phrases", not over_cap, f"over_cap={over_cap}")
    return data


def test_pete_work_evidence():
    print("\n=== PETE: work evidence ===")
    code, data, dt = do_get(f"/life/work/evidence/{PETE}?refresh=true")
    record("PETE work evidence 200", code == 200, f"status={code} time={dt:.2f}s body={trim_json(data, 600)}")
    if code != 200:
        return None
    is_valid = isinstance(data, (dict, list)) and (len(data) > 0)
    record("PETE work evidence valid non-empty JSON", is_valid, f"type={type(data).__name__}")
    return data


def test_mel_role_card():
    print("\n=== MEL: role-card ===")
    code, data, dt = do_get(f"/life/role-card/{MEL}?refresh=true")
    record("MEL role-card 200", code == 200, f"status={code} time={dt:.2f}s body={trim_json(data, 600)}")
    if code != 200:
        return None

    confidence = data.get("confidence")
    record("MEL role-card confidence in (medium, high)", confidence in ("medium", "high"), f"confidence={confidence!r}")

    drivers = data.get("dominant_drivers") or []
    drivers_joined = " | ".join(str(d).lower() for d in drivers)
    record("MEL drivers do NOT contain 'recurring tension'", "recurring tension" not in drivers_joined, f"drivers={drivers}")
    record("MEL drivers do NOT contain 'lived history'", "lived history" not in drivers_joined, f"drivers={drivers}")
    return data


def test_mel_synthesis():
    print("\n=== MEL: domain synthesis ===")
    any_ok = False
    for ctx in ["work", "relationships", "self"]:
        code, data, dt = do_get(f"/life/{ctx}/synthesis/{MEL}?refresh=true")
        print(f"  MEL {ctx} synth -> status={code} time={dt:.2f}s")
        if code == 200:
            any_ok = True
            ds = (data.get("domain_synthesis") or {})
            if any(ds.get(k) for k in ("pattern", "default_tension")):
                record(f"MEL {ctx} synthesis 200 with content", True, f"pattern={ds.get('pattern')!r}")
                break
        else:
            print(f"    body={trim_json(data, 300)}")
    record("MEL at least one domain synthesis 200", any_ok, "")


def test_mel_work_today():
    print("\n=== MEL: work today ===")
    code, data, dt = do_get(f"/life/work/today/{MEL}?refresh=true")
    record("MEL work today 200", code == 200, f"status={code} time={dt:.2f}s body={trim_json(data, 500)}")
    if code != 200:
        return None

    intensity = data.get("intensity_level")
    record("MEL work today intensity_level=low", intensity == "low", f"intensity_level={intensity!r}")
    return data


def test_invalid_context():
    print("\n=== EDGE: invalid context ===")
    code, data, dt = do_get(f"/life/foo/synthesis/{PETE}")
    record("Invalid context returns 400", code == 400, f"status={code} body={trim_json(data, 300)}")


def test_non_existent_user():
    print("\n=== EDGE: non-existent user ===")
    code, data, dt = do_get("/life/role-card/doesnotexist")
    record("Non-existent user role-card returns 404", code == 404, f"status={code} body={trim_json(data, 300)}")


def main():
    print(f"BASE_URL = {API}")

    test_pete_role_card()
    pete_work = test_pete_synthesis("work")
    pete_rel = test_pete_synthesis("relationships")
    pete_self = test_pete_synthesis("self")
    test_pete_cross_domain_differs(pete_work, pete_rel, pete_self)
    test_pete_work_today()
    test_pete_work_evidence()

    test_mel_role_card()
    test_mel_synthesis()
    test_mel_work_today()

    test_invalid_context()
    test_non_existent_user()

    print("\n" + "=" * 70)
    passed = sum(1 for _, p, _ in results if p)
    failed = sum(1 for _, p, _ in results if not p)
    print(f"SUMMARY: {passed}/{passed + failed} passed, {failed} failed")
    if failed:
        print("\nFAILED TESTS:")
        for name, p, detail in results:
            if not p:
                print(f"  FAIL {name}")
                if detail:
                    print(f"     {detail[:500]}")
    return failed


if __name__ == "__main__":
    sys.exit(main())
