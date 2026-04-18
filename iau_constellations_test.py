"""
Backend test for IAU Constellation Overlay feature.

Tests (per review request):
  1. GET /api/astrology/constellations/{user_id} for 4 known users (Pete/Mel/Isaac/Thaddeus).
  2. GET /api/astrology/constellations/nonexistent_user_id → expect 404.
  3. GET /api/astrology/chart/{user_id} — regression: `natal.signs` unchanged, `natal.constellations` additive.
  4. GET /api/astrology/deep-dive/{user_id} — regression: must still return 200.
  5. POST /api/forum-mappings — regression: 3 distinct headlines.
"""
import json
import os
import sys
import time
import requests

BACKEND_URL = os.environ.get("BACKEND_URL", "https://astro-hd-routes-v6.preview.emergentagent.com")
API = BACKEND_URL.rstrip("/") + "/api"

USERS = {
    "Pete":     "697f0c6abf35c0528ff06954",
    "Mel":      "697ec826ad4b18f75bf42616",
    "Isaac":    "69dda348de9cb1c83c0780f8",
    "Thaddeus": "69dd0b2cc92ba973f8838c11",
}

# Known fixtures from the review request
EXPECTED_OPHIUCHUS = {
    "Pete": {"has_ophiuchus": False, "required_body": None},
    "Mel": {"has_ophiuchus": True, "required_body": "Neptune"},
    "Isaac": {"has_ophiuchus": True, "required_body": "Midheaven"},
    "Thaddeus": {"has_ophiuchus": True, "required_body": "Ascendant"},
}

VALID_IAU_NAMES = {
    "Pisces", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpius", "Ophiuchus", "Sagittarius", "Capricornus", "Aquarius"
}

results = []   # (test_name, passed, detail)

def record(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {name}")
    if detail:
        for line in str(detail).splitlines():
            print(f"        {line}")
    results.append((name, passed, detail))


def test_constellation_endpoint_for_user(label, user_id):
    url = f"{API}/astrology/constellations/{user_id}"
    try:
        r = requests.get(url, timeout=30)
    except Exception as e:
        record(f"[{label}] GET /astrology/constellations/{user_id}", False, f"Request error: {e}")
        return None

    if r.status_code != 200:
        record(f"[{label}] HTTP 200", False, f"Got {r.status_code}: {r.text[:300]}")
        return None

    record(f"[{label}] HTTP 200", True, f"status=200 (elapsed {r.elapsed.total_seconds():.2f}s)")

    try:
        body = r.json()
    except Exception as e:
        record(f"[{label}] JSON parse", False, f"{e}: {r.text[:200]}")
        return None

    # success: true
    record(f"[{label}] success==true", body.get("success") is True, f"success={body.get('success')}")

    overlay = body.get("overlay", {}) or {}

    # version
    record(
        f"[{label}] overlay.version=='iau_1930_v1'",
        overlay.get("version") == "iau_1930_v1",
        f"version={overlay.get('version')}"
    )

    # Sun constellation
    bodies = overlay.get("bodies", {}) or {}
    sun_entry = bodies.get("Sun", {}) or {}
    sun_const = sun_entry.get("constellation")
    record(
        f"[{label}] overlay.bodies.Sun.constellation is present",
        sun_const is not None,
        f"Sun constellation={sun_const}"
    )
    record(
        f"[{label}] Sun constellation is valid IAU name",
        sun_const in VALID_IAU_NAMES,
        f"value={sun_const!r} (valid set: {sorted(VALID_IAU_NAMES)})"
    )

    # summary keys
    summary = overlay.get("summary", {}) or {}
    for key in ["sun_constellation", "moon_constellation", "ascendant_constellation", "mc_constellation"]:
        present = key in summary and summary[key] is not None
        record(f"[{label}] summary.{key} present", present, f"{key}={summary.get(key)!r}")

    # has_ophiuchus
    expected = EXPECTED_OPHIUCHUS[label]
    actual_has = overlay.get("has_ophiuchus")
    ophiuchus_bodies = overlay.get("ophiuchus_bodies", []) or []
    record(
        f"[{label}] has_ophiuchus matches fixture ({expected['has_ophiuchus']})",
        actual_has == expected["has_ophiuchus"],
        f"expected={expected['has_ophiuchus']}, actual={actual_has}, ophiuchus_bodies={ophiuchus_bodies}"
    )

    # narrative when has_ophiuchus
    narrative = overlay.get("overlay_narrative")
    if expected["has_ophiuchus"]:
        ok = isinstance(narrative, str) and len(narrative) > 0 and "Ophiuchus" in narrative
        record(
            f"[{label}] overlay_narrative is non-empty and contains 'Ophiuchus'",
            ok,
            f"narrative={narrative!r}"
        )

    # Required specific body in ophiuchus_bodies
    if expected["required_body"]:
        req = expected["required_body"]
        record(
            f"[{label}] '{req}' in overlay.ophiuchus_bodies",
            req in ophiuchus_bodies,
            f"ophiuchus_bodies={ophiuchus_bodies}"
        )

    return body


def test_nonexistent_user_returns_404():
    url = f"{API}/astrology/constellations/nonexistent_user_id"
    try:
        r = requests.get(url, timeout=30)
    except Exception as e:
        record("nonexistent_user returns 404", False, f"Request error: {e}")
        return
    passed = r.status_code == 404
    record("GET /astrology/constellations/nonexistent_user_id → 404", passed,
           f"status_code={r.status_code}, body={r.text[:300]}")


def test_chart_additive_regression(user_id):
    url = f"{API}/astrology/chart/{user_id}"
    try:
        r = requests.get(url, timeout=60)
    except Exception as e:
        record(f"chart regression {user_id}", False, f"Request error: {e}")
        return
    record(f"[Pete] GET /astrology/chart/{user_id} HTTP 200", r.status_code == 200,
           f"status_code={r.status_code}")
    if r.status_code != 200:
        print("        body:", r.text[:400])
        return
    body = r.json()
    natal = body.get("natal", {}) or {}

    # natal.signs present
    signs = natal.get("signs")
    record("[Pete] natal.signs still present (12-sign zodiac preserved)", isinstance(signs, dict) and bool(signs),
           f"signs keys={list(signs.keys()) if isinstance(signs, dict) else signs}")

    # natal.constellations present
    constellations = natal.get("constellations", {}) or {}
    record("[Pete] natal.constellations.version == 'iau_1930_v1'",
           constellations.get("version") == "iau_1930_v1",
           f"version={constellations.get('version')}")

    # bodies with Sun/Moon/Ascendant
    cbodies = constellations.get("bodies", {}) or {}
    has_all = all(b in cbodies for b in ["Sun", "Moon", "Ascendant"])
    record("[Pete] natal.constellations.bodies has at least Sun/Moon/Ascendant",
           has_all, f"body keys={sorted(cbodies.keys())}")

    # 12-sign zodiac NOT impacted: natal.signs.sun is a 12-sign name (not Ophiuchus)
    twelve_signs = {"Pisces", "Aries", "Taurus", "Gemini", "Cancer", "Leo",
                    "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius"}
    sun_sign = None
    if isinstance(signs, dict):
        sun_sign = signs.get("sun") or signs.get("Sun") or signs.get("sun_sign")
    record("[Pete] natal.signs.sun is a 12-sign name (not Ophiuchus)",
           sun_sign in twelve_signs,
           f"natal.signs.sun={sun_sign!r}")


def test_deep_dive_regression(user_id):
    url = f"{API}/astrology/deep-dive/{user_id}"
    try:
        r = requests.get(url, timeout=120)
    except Exception as e:
        record(f"deep-dive regression {user_id}", False, f"Request error: {e}")
        return
    passed = r.status_code == 200
    detail = f"status_code={r.status_code}"
    if passed:
        try:
            body = r.json()
            detail += f", top-level keys={list(body.keys())[:10]}"
        except Exception as e:
            passed = False
            detail += f", JSON parse error: {e}"
    else:
        detail += f", body={r.text[:300]}"
    record(f"[Pete] GET /astrology/deep-dive/{user_id} HTTP 200", passed, detail)


def test_forum_mappings_regression():
    url = f"{API}/forum-mappings"
    payload = {
        "forum_id": "69dda348de9cb1c83c0780fa",
        "user_id": "697f0c6abf35c0528ff06954"
    }
    try:
        r = requests.post(url, json=payload, timeout=90)
    except Exception as e:
        record("forum-mappings regression", False, f"Request error: {e}")
        return
    record("POST /forum-mappings HTTP 200", r.status_code == 200,
           f"status_code={r.status_code}")
    if r.status_code != 200:
        print("        body:", r.text[:500])
        return
    body = r.json()

    # Expected shape: body["mappings"] list with each having story.headline? Let's
    # inspect flexibly — mappings could be list or under different key.
    def find_mappings(obj):
        if isinstance(obj, dict):
            if "mappings" in obj and isinstance(obj["mappings"], list):
                return obj["mappings"]
            for v in obj.values():
                r = find_mappings(v)
                if r is not None:
                    return r
        return None

    mappings = find_mappings(body) or []
    # Collect headlines keyed by member name when possible
    headlines = []
    for m in mappings:
        story = m.get("story") if isinstance(m, dict) else None
        if isinstance(story, dict):
            headline = story.get("headline")
            name = m.get("name") or m.get("member_name") or m.get("user_id")
            if headline:
                headlines.append((name, headline))

    record("forum-mappings: got at least 3 mappings with story.headline",
           len(headlines) >= 3,
           f"headlines_found={len(headlines)}; sample={headlines[:5]}")
    if len(headlines) >= 3:
        distinct = len({h for _, h in headlines[:3]})
        # Exact requirement: Thaddeus/Mel/Isaac distinct. Filter by name if identifiable.
        target_names = {"Thaddeus", "Mel", "Isaac"}
        target_hs = [(n, h) for (n, h) in headlines if n in target_names]
        if len(target_hs) >= 3:
            target_distinct = len({h for _, h in target_hs})
            record("forum-mappings: Thaddeus/Mel/Isaac have 3 DISTINCT headlines",
                   target_distinct == 3,
                   f"entries={target_hs}")
        else:
            # Fall back to just 'are any 3 distinct'
            record("forum-mappings: at least 3 distinct story.headline values",
                   distinct == 3,
                   f"first-3={headlines[:3]}")


def main():
    print(f"BACKEND={API}")
    print("=" * 78)

    # Test 1: 4 users constellation endpoint
    for label, uid in USERS.items():
        print(f"\n--- Test: Constellation overlay for {label} ({uid}) ---")
        test_constellation_endpoint_for_user(label, uid)

    # Test 2: 404
    print(f"\n--- Test: Non-existent user 404 ---")
    test_nonexistent_user_returns_404()

    # Test 3: chart regression for Pete
    print(f"\n--- Test: Chart additive regression (Pete) ---")
    test_chart_additive_regression(USERS["Pete"])

    # Test 4: Deep dive regression for Pete
    print(f"\n--- Test: Deep dive regression (Pete) ---")
    test_deep_dive_regression(USERS["Pete"])

    # Test 5: forum mappings regression
    print(f"\n--- Test: Forum mappings regression ---")
    test_forum_mappings_regression()

    # Summary
    total = len(results)
    passed = sum(1 for _, p, _ in results if p)
    failed = total - passed
    print("\n" + "=" * 78)
    print(f"TOTAL: {total}  PASS: {passed}  FAIL: {failed}")
    if failed:
        print("\nFailed assertions:")
        for n, p, d in results:
            if not p:
                print(f"  - {n}")
                if d:
                    for line in str(d).splitlines():
                        print(f"      {line}")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
