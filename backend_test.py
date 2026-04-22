"""
Home Insight V6 "Signal-Grounded" Engine — backend regression tests
Target endpoint: GET /api/home-insight-v5/{user_id}
"""
import os
import json
import requests

BASE = "https://superpower-synthesis.preview.emergentagent.com/api"

PETE = "697f0c6abf35c0528ff06954"
MEL = "697ec826ad4b18f75bf42616"
FAKE = "000000000000000000000000"

results = []


def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    results.append((status, name, detail))
    print(f"[{status}] {name}  {detail if detail else ''}")
    return cond


def v6_assertions(label, data):
    ok = True
    ok &= check(
        f"{label}: version==v6_signal_grounded",
        data.get("version") == "v6_signal_grounded",
        f"actual={data.get('version')}",
    )
    ok &= check(
        f"{label}: render_mode==signal_grounded",
        data.get("render_mode") == "signal_grounded",
        f"actual={data.get('render_mode')}",
    )
    layers = data.get("layers") or {}
    for fld in ("trigger", "collision", "distortion", "interrupt"):
        v = layers.get(fld)
        ok &= check(
            f"{label}: layers.{fld} non-empty string",
            isinstance(v, str) and len(v.strip()) > 0,
            f"actual={repr(v)[:80]}",
        )
    ok &= check(
        f"{label}: signal_count >= 2",
        (data.get("signal_count") or 0) >= 2,
        f"actual={data.get('signal_count')}",
    )
    ds = data.get("distinct_sources") or []
    ok &= check(
        f"{label}: len(distinct_sources) >= 2",
        len(ds) >= 2,
        f"actual={ds}",
    )
    sigs = data.get("signals_used") or []
    ok &= check(
        f"{label}: signals_used non-empty",
        isinstance(sigs, list) and len(sigs) > 0,
        f"count={len(sigs)}",
    )
    for s in sigs:
        for k in ("source", "kind", "label", "weight", "evidence"):
            if k not in s:
                ok &= check(f"{label}: signal missing key {k}", False, str(s)[:80])
                break
    # Back-compat v5 mappings
    ok &= check(
        f"{label}: headline == layers.trigger",
        data.get("headline") == layers.get("trigger"),
        f"headline={data.get('headline')[:60] if data.get('headline') else None}",
    )
    ok &= check(
        f"{label}: identity_mirror == layers.collision",
        data.get("identity_mirror") == layers.get("collision"),
    )
    ok &= check(
        f"{label}: the_move == layers.interrupt",
        data.get("the_move") == layers.get("interrupt"),
    )
    wsu = (data.get("why_showing_up") or {}).get("signals") or []
    ok &= check(
        f"{label}: why_showing_up.signals non-empty list of strings",
        isinstance(wsu, list) and len(wsu) > 0 and all(isinstance(x, str) for x in wsu),
        f"count={len(wsu)}",
    )
    return ok


def traceability(label, data):
    """Every layer sentence should correspond to at least one signal in signals_used."""
    sigs = data.get("signals_used") or []
    sig_labels = [s.get("label") or "" for s in sigs]
    sig_evidence_blobs = [json.dumps(s.get("evidence") or {}) for s in sigs]
    layers = data.get("layers") or {}
    # Heuristic: check that at least a key token from each layer string appears in some signal
    ok = True
    for fld in ("trigger", "collision", "distortion", "cost", "interrupt"):
        txt = layers.get(fld)
        if not txt:
            continue
        # Extract a salient token: first capitalised sign / key phrase
        tokens = []
        for key in [
            "Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio",
            "Sagittarius","Capricorn","Aquarius","Pisces",
            "New Moon","Full Moon","stellium","Gate","Neptune","Uranus","Saturn",
            "Mars","Jupiter","Mercury","Venus","Sun","Moon",
        ]:
            if key in txt:
                tokens.append(key)
        # Check at least one token appears in any signal label/evidence — trigger layers
        # like "interrupt" tend to be free-form advice, so we accept if layer has no astro
        # token OR if any token matches.
        if tokens:
            match = any(
                any(t in sl for sl in sig_labels) or any(t in ev for ev in sig_evidence_blobs)
                for t in tokens
            )
            ok &= check(
                f"{label}: layer '{fld}' traceable to signals_used (tokens={tokens[:3]})",
                match,
            )
    return ok


def main():
    print("\n=== A) Pete (v6 expected) ===")
    r = requests.get(f"{BASE}/home-insight-v5/{PETE}", timeout=30)
    check("Pete HTTP 200", r.status_code == 200, f"status={r.status_code}")
    pete = r.json()
    v6_assertions("Pete", pete)
    traceability("Pete", pete)

    print("\n=== B) Mel (v6 expected) ===")
    r = requests.get(f"{BASE}/home-insight-v5/{MEL}", timeout=30)
    check("Mel HTTP 200", r.status_code == 200, f"status={r.status_code}")
    mel = r.json()
    v6_assertions("Mel", mel)
    traceability("Mel", mel)

    print("\n=== Per-user personalization (Pete vs Mel) ===")
    pt = (pete.get("layers") or {}).get("trigger")
    mt = (mel.get("layers") or {}).get("trigger")
    pc = (pete.get("layers") or {}).get("collision")
    mc = (mel.get("layers") or {}).get("collision")
    print(f"Pete trigger:   {pt}")
    print(f"Mel  trigger:   {mt}")
    print(f"Pete collision: {pc}")
    print(f"Mel  collision: {mc}")
    check("Pete.trigger != Mel.trigger", pt != mt)
    check("Pete.collision != Mel.collision", pc != mc)

    print("\n=== D) Non-existent user (no 500 regression) ===")
    r = requests.get(f"{BASE}/home-insight-v5/{FAKE}", timeout=30)
    check("Fake user HTTP 200 (not 500)", r.status_code == 200, f"status={r.status_code}")
    fake = r.json()
    check(
        "Fake user: v5 fallback or v5 template (not v6)",
        fake.get("version") in ("v5_fallback", "v5_pattern_engine", "v5_template"),
        f"version={fake.get('version')}",
    )

    print("\n=== E) Forum-mappings regression ===")
    r = requests.post(
        f"{BASE}/forum-mappings",
        json={
            "forum_id": "69dda348de9cb1c83c0780fa",
            "user_id": "697f0c6abf35c0528ff06954",
        },
        timeout=30,
    )
    check("forum-mappings HTTP 200", r.status_code == 200, f"status={r.status_code}")
    fm = r.json()
    check("forum-mappings success=True", fm.get("success") is True)
    mappings = fm.get("mappings") or []
    check("forum-mappings 3 members", len(mappings) == 3, f"count={len(mappings)}")
    emoji_chars = "🐒🐴🐓🐲🐯🐰🐶🐱🐷🐔🐍🐀🐂🐑🐺🐎"
    for m in mappings:
        name = m.get("member_name")
        sig = m.get("signals") or {}
        enn = sig.get("enneagram")
        bz = sig.get("bazi") or {}
        found_emoji = False
        for arr in ("support", "tension", "growth"):
            for s in bz.get(arr, []) or []:
                if any(ch in s for ch in emoji_chars):
                    found_emoji = True
                    break
        check(f"forum-mappings:{name} has enneagram", bool(enn))
        check(f"forum-mappings:{name} has bazi animal emoji", found_emoji)

    print("\n=== SUMMARY ===")
    passed = sum(1 for s, *_ in results if s == "PASS")
    failed = sum(1 for s, *_ in results if s == "FAIL")
    print(f"TOTAL: {passed + failed}  PASS: {passed}  FAIL: {failed}")
    if failed:
        print("\nFailures:")
        for s, n, d in results:
            if s == "FAIL":
                print(f"  - {n}  {d}")


if __name__ == "__main__":
    main()
