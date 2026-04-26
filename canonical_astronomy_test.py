"""
Canonical Astronomy Validation Layer — Backend Test
Tests per the review request.
"""
import json
import sys
import requests

BASE = "https://metaphor-control.preview.emergentagent.com/api"

PETE = "697f0c6abf35c0528ff06954"
MEL = "697ec826ad4b18f75bf42616"

results = []


def record(name, passed, detail=""):
    results.append({"name": name, "passed": bool(passed), "detail": detail})
    prefix = "PASS" if passed else "FAIL"
    print(f"[{prefix}] {name}" + (f" — {detail}" if detail else ""))


def test_canonical_diagnostic(user_id, label):
    print(f"\n===== Canonical Diagnostic: {label} ({user_id}) =====")
    url = f"{BASE}/diagnostics/canonical-astronomy/{user_id}"
    try:
        r = requests.get(url, timeout=60)
    except Exception as e:
        record(f"{label} HTTP 200", False, f"request error: {e}")
        return None

    record(f"{label} HTTP 200", r.status_code == 200,
           f"status={r.status_code} body={r.text[:250] if r.status_code!=200 else ''}")
    if r.status_code != 200:
        return None

    try:
        data = r.json()
    except Exception as e:
        record(f"{label} valid JSON", False, f"parse error: {e}")
        return None

    # pass == true
    record(f"{label} pass == true", data.get("pass") is True,
           f"pass={data.get('pass')} summary={data.get('summary')!r}")

    # summary starts with "✓"
    summary = data.get("summary") or ""
    record(f"{label} summary starts with ✓", summary.startswith("✓"),
           f"summary={summary!r}")

    # Drift subreports
    astro_drift = data.get("astrology_drift") or {}
    hd_pers_drift = data.get("hd_personality_drift") or {}
    hd_des_drift = data.get("hd_design_drift") or {}

    record(f"{label} astrology_drift.pass", astro_drift.get("pass") is True,
           f"drift={astro_drift.get('max_drift_degrees')} note={astro_drift.get('note', '')}")
    record(f"{label} hd_personality_drift.pass", hd_pers_drift.get("pass") is True,
           f"drift={hd_pers_drift.get('max_drift_degrees')} note={hd_pers_drift.get('note', '')}")
    record(f"{label} hd_design_drift.pass", hd_des_drift.get("pass") is True,
           f"drift={hd_des_drift.get('max_drift_degrees')} note={hd_des_drift.get('note', '')}")

    # sample_sun_cross_lens_match
    sm = data.get("sample_sun_cross_lens_match") or {}
    record(f"{label} astrology_matches_canonical",
           sm.get("astrology_matches_canonical") is True,
           f"={sm.get('astrology_matches_canonical')}")
    record(f"{label} hd_matches_canonical",
           sm.get("hd_matches_canonical") is True,
           f"={sm.get('hd_matches_canonical')}")

    # Three-way equality Sun longitudes at 6 decimals
    csun = sm.get("canonical_sun_longitude")
    asun = sm.get("astrology_sun_longitude")
    hdsun = sm.get("hd_personality_sun_longitude")
    three_way_equal = (
        csun is not None and asun is not None and hdsun is not None
        and round(csun, 6) == round(asun, 6) == round(hdsun, 6)
    )
    record(f"{label} three-way Sun longitude equality (6 dp)",
           three_way_equal,
           f"canonical={csun} astrology={asun} hd_personality={hdsun}")

    # Canonical layer checks
    canonical = data.get("canonical") or {}
    canonical_layer = canonical.get("canonical_layer") or {}
    cfg = canonical_layer.get("sidereal_config") or {}

    record(f"{label} svp_degrees == 31.2836",
           abs(float(cfg.get("svp_degrees", 0)) - 31.2836) < 1e-6,
           f"svp_degrees={cfg.get('svp_degrees')}")
    record(f"{label} ayanamsa_type == SIDM_USER",
           cfg.get("ayanamsa_type") == "SIDM_USER",
           f"ayanamsa_type={cfg.get('ayanamsa_type')}")
    record(f"{label} ephemeris_flag == 'FLG_SWIEPH | FLG_SIDEREAL'",
           cfg.get("ephemeris_flag") == "FLG_SWIEPH | FLG_SIDEREAL",
           f"ephemeris_flag={cfg.get('ephemeris_flag')}")

    # B) Runtime anti-drift guard — verify locked config
    record(f"{label} reference_epoch == J2000",
           cfg.get("reference_epoch") == "J2000",
           f"reference_epoch={cfg.get('reference_epoch')}")
    record(f"{label} yearly_increment == 0.0",
           float(cfg.get("yearly_increment", -1)) == 0.0,
           f"yearly_increment={cfg.get('yearly_increment')}")
    record(f"{label} house_system == equal",
           cfg.get("house_system") == "equal",
           f"house_system={cfg.get('house_system')}")

    # fingerprint: 16-char hex string
    fp = canonical_layer.get("fingerprint") or ""
    is_16_hex = len(fp) == 16 and all(c in "0123456789abcdef" for c in fp.lower())
    record(f"{label} fingerprint is 16-char hex",
           is_16_hex,
           f"fingerprint={fp!r}")

    # Print Sun longitudes (Task D)
    print(f"  >> {label} Sun longitudes (6 dp):")
    print(f"     canonical            = {csun}")
    print(f"     astrology            = {asun}")
    print(f"     hd_personality       = {hdsun}")

    return data


def test_home_insight_v5():
    print("\n===== Home Insight V5 (Pete) =====")
    url = f"{BASE}/home-insight-v5/{PETE}"
    try:
        r = requests.get(url, timeout=60)
    except Exception as e:
        record("home-insight-v5 HTTP 200", False, f"request error: {e}")
        return
    record("home-insight-v5 HTTP 200", r.status_code == 200,
           f"status={r.status_code}")
    if r.status_code != 200:
        return
    data = r.json()
    record("home-insight-v5 version == v6_signal_grounded",
           data.get("version") == "v6_signal_grounded",
           f"version={data.get('version')}")
    record("home-insight-v5 render_mode == signal_grounded",
           data.get("render_mode") == "signal_grounded",
           f"render_mode={data.get('render_mode')}")
    layers = data.get("layers") or {}
    trigger = layers.get("trigger") or ""
    record("home-insight-v5 layers.trigger non-empty",
           isinstance(trigger, str) and len(trigger) > 0,
           f"trigger={trigger!r}")


def test_forum_mappings():
    print("\n===== Forum Mappings (Pete) =====")
    url = f"{BASE}/forum-mappings"
    payload = {"forum_id": "69dda348de9cb1c83c0780fa", "user_id": PETE}
    try:
        r = requests.post(url, json=payload, timeout=60)
    except Exception as e:
        record("forum-mappings HTTP 200", False, f"request error: {e}")
        return
    record("forum-mappings HTTP 200", r.status_code == 200,
           f"status={r.status_code} body={r.text[:200] if r.status_code!=200 else ''}")
    if r.status_code != 200:
        return
    data = r.json()
    # Try a few container keys
    members = data.get("members") or data.get("mappings") or data.get("results") or []
    record("forum-mappings 3 mappings returned", len(members) == 3,
           f"count={len(members)}")
    if members:
        # Check signals richness
        enn_count = 0
        bazi_count = 0
        astro_count = 0
        hd_count = 0
        for m in members:
            sig = m.get("signals") or {}
            if sig.get("enneagram"):
                enn_count += 1
            if sig.get("bazi"):
                bazi_count += 1
            if sig.get("astrology"):
                astro_count += 1
            if sig.get("human_design") or sig.get("hd"):
                hd_count += 1
        record("forum-mappings all have enneagram signals",
               enn_count == len(members), f"{enn_count}/{len(members)}")
        record("forum-mappings all have bazi signals",
               bazi_count == len(members), f"{bazi_count}/{len(members)}")
        record("forum-mappings all have astrology signals",
               astro_count == len(members), f"{astro_count}/{len(members)}")
        record("forum-mappings all have HD signals",
               hd_count == len(members), f"{hd_count}/{len(members)}")


def test_fix_deployed_data():
    print("\n===== Fix Deployed Data =====")
    url = f"{BASE}/fix-deployed-data"
    try:
        r = requests.get(url, timeout=180)
    except Exception as e:
        record("fix-deployed-data HTTP 200", False, f"request error: {e}")
        return
    record("fix-deployed-data HTTP 200", r.status_code == 200,
           f"status={r.status_code}")
    if r.status_code != 200:
        return
    data = r.json()
    errs = data.get("errors") or []
    record("fix-deployed-data errors == []",
           isinstance(errs, list) and len(errs) == 0,
           f"errors={errs[:3]}... (n={len(errs)})")


if __name__ == "__main__":
    pete_data = test_canonical_diagnostic(PETE, "Pete")
    mel_data = test_canonical_diagnostic(MEL, "Mel")
    test_home_insight_v5()
    test_forum_mappings()
    test_fix_deployed_data()

    # Print Sun longitudes summary (Task D)
    print("\n===== D) SUN LONGITUDE REPORT (6 dp) =====")
    for label, data in [("Pete", pete_data), ("Mel", mel_data)]:
        if not data:
            print(f"{label}: N/A (no data)")
            continue
        sm = data.get("sample_sun_cross_lens_match") or {}
        print(f"{label}:")
        print(f"  canonical_sun_longitude      = {sm.get('canonical_sun_longitude')}")
        print(f"  astrology_sun_longitude      = {sm.get('astrology_sun_longitude')}")
        print(f"  hd_personality_sun_longitude = {sm.get('hd_personality_sun_longitude')}")

    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    print(f"\n===== SUMMARY: {passed}/{total} assertions passed =====")
    for r in results:
        if not r["passed"]:
            print(f"  FAIL: {r['name']} — {r['detail']}")
    sys.exit(0 if passed == total else 1)
