"""
Backend test for the new Astrology House SSOT Forensic Endpoint.

GET /api/admin/astrology/house_forensic/{user_id}
"""
import os
import sys
import json
import requests

BASE = os.environ.get("BACKEND_URL", "https://sidereal-debug.preview.emergentagent.com") + "/api"

PETE = "697f0c6abf35c0528ff06954"
MEL = "697ec826ad4b18f75bf42616"

REQUIRED_PLANETS_PETE = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"]


def test_user(user_id: str, label: str, asc_low=None, asc_high=None,
              check_planets=None, expect_ws_divergence=False):
    print(f"\n=== {label} ({user_id}) ===")
    url = f"{BASE}/admin/astrology/house_forensic/{user_id}"
    r = requests.get(url, timeout=30)
    print(f"GET {url} -> {r.status_code}")
    if r.status_code != 200:
        print(f"  FAIL: status {r.status_code}: {r.text[:300]}")
        return False, {}, [f"status {r.status_code}"]
    data = r.json()
    failures = []

    if data.get("ok") is not True:
        failures.append(f"ok != true: {data.get('ok')}")

    if data.get("ssot_ok") is not True:
        failures.append(f"ssot_ok != true: {data.get('ssot_ok')}")

    if data.get("ssot_violations") != []:
        failures.append(f"ssot_violations not empty: {data.get('ssot_violations')}")

    if data.get("house_system") != "Equal":
        failures.append(f"house_system != 'Equal': {data.get('house_system')}")

    svp = data.get("svp_applied")
    if svp is None or abs(svp - 31.2836) > 0.01:
        failures.append(f"svp_applied not ~31.2836: {svp}")

    asc = data.get("ascendant_sidereal_degrees")
    if asc_low is not None and asc_high is not None:
        if asc is None or not (asc_low <= asc <= asc_high):
            failures.append(f"ascendant not in [{asc_low},{asc_high}]: {asc}")

    cusps = data.get("house_cusps") or []
    if len(cusps) != 12:
        failures.append(f"house_cusps not 12: {len(cusps)}")
    else:
        house_nums = [c.get("house") for c in cusps]
        if house_nums != list(range(1, 13)):
            failures.append(f"house cusps not 1..12 monotonic: {house_nums}")

    planets = data.get("planets") or []
    planet_map = {p["planet"]: p for p in planets}

    if check_planets:
        for pname in check_planets:
            if pname not in planet_map:
                failures.append(f"missing planet {pname}")
                continue
            p = planet_map[pname]
            if p.get("ssot_ok") is not True:
                failures.append(f"{pname}.ssot_ok != true")
            if p.get("house_stored") != p.get("house_equal_recomputed"):
                failures.append(
                    f"{pname} house_stored({p.get('house_stored')}) != "
                    f"house_equal_recomputed({p.get('house_equal_recomputed')})"
                )

    if expect_ws_divergence:
        ws_div = data.get("whole_sign_divergences_for_reference_only") or []
        if len(ws_div) < 1:
            failures.append("expected >=1 whole_sign_divergences entry")

    print(f"  ok={data.get('ok')} ssot_ok={data.get('ssot_ok')} "
          f"house_system={data.get('house_system')} svp={data.get('svp_applied')} "
          f"asc={data.get('ascendant_sidereal_degrees')} cusps={len(cusps)} "
          f"planets={len(planets)} violations={len(data.get('ssot_violations') or [])} "
          f"ws_div={len(data.get('whole_sign_divergences_for_reference_only') or [])}")

    if failures:
        print("  FAIL items:")
        for f in failures:
            print(f"    - {f}")
        return False, data, failures
    print("  PASS")
    return True, data, []


def test_invalid_user():
    print("\n=== Invalid user (does_not_exist_999) ===")
    url = f"{BASE}/admin/astrology/house_forensic/does_not_exist_999"
    r = requests.get(url, timeout=30)
    print(f"GET {url} -> {r.status_code}")
    if r.status_code != 404:
        print(f"  FAIL: expected 404, got {r.status_code}: {r.text[:300]}")
        return False
    try:
        body = r.json()
        detail = body.get("detail", "")
        if "No chart" not in detail:
            print(f"  FAIL: detail missing 'No chart': {detail}")
            return False
        print(f"  PASS detail='{detail}'")
        return True
    except Exception as e:
        print(f"  FAIL: response not JSON: {e}")
        return False


def main():
    print(f"Base URL: {BASE}")
    results = {}

    pete_ok, pete_data, pete_fails = test_user(
        PETE, "Pete", asc_low=262, asc_high=263,
        check_planets=REQUIRED_PLANETS_PETE, expect_ws_divergence=True,
    )
    results["Pete"] = (pete_ok, pete_fails)

    mel_ok, mel_data, mel_fails = test_user(
        MEL, "Mel", asc_low=None, asc_high=None,
        check_planets=None, expect_ws_divergence=False,
    )
    extra = []
    asc_mel = mel_data.get("ascendant_sidereal_degrees")
    if asc_mel is None or not (88 <= asc_mel <= 91):
        extra.append(f"Mel asc not ~89.1: {asc_mel}")
    for p in mel_data.get("planets", []):
        if p.get("ssot_ok") is not True:
            extra.append(f"Mel planet {p.get('planet')} ssot_ok != true")
    if extra:
        mel_ok = False
        mel_fails.extend(extra)
        for f in extra:
            print(f"    - {f}")
    results["Mel"] = (mel_ok, mel_fails)

    invalid_ok = test_invalid_user()
    results["Invalid"] = (invalid_ok, [])

    print("\n=== SUMMARY ===")
    all_pass = True
    for name, (ok, fails) in results.items():
        status = "PASS" if ok else "FAIL"
        print(f"  {name}: {status}")
        if not ok:
            all_pass = False
            for f in fails:
                print(f"      - {f}")

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
