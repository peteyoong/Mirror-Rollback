"""
Backend Tests for Forum Mappings P0 Fixes (Feb 2026)

Verifies:
  A) /api/forum-mappings returns complete data for all 3 members with
     non-null enneagram, bazi (w/ animal emojis), astrology, and HD signals.
  B) /api/fix-deployed-data seeds ALL duplicate user records for
     Pete/Mel/Isaac/Thaddeus, with empty errors.
  C) No regression on /api/get-user-forums and /api/forums/{id}/members.
"""
import json
import re
import sys
import requests

BASE_URL = "http://localhost:8001"

# Test credentials
PETE_USER_ID = "697f0c6abf35c0528ff06954"
MEL_USER_ID = "697ec826ad4b18f75bf42616"
YOONG_FAMILY_FORUM_ID = "69dda348de9cb1c83c0780fa"

EXPECTED_MEMBERS = {"Thaddeus Yoong", "Mel", "Isaac Yoong"}

ANIMAL_EMOJI_PATTERN = re.compile(
    r"🐀|🐁|🐂|🐃|🐄|🐅|🐆|🐇|🐈|🐉|🐊|🐋|🐌|🐍|🐎|🐏|🐐|🐑|🐒|🐓|🐔|🐕|🐖|🐗|🐘|🐙|🐚|🐛|🐜|🐝|🐞|🐟|🐠|🐡|🐢|🐣|🐤|🐥|🐦|🐧|🐨|🐩|🐪|🐫|🐬|🐭|🐮|🐯|🐰|🐱|🐲|🐳"
)

results = []


def pass_(msg):
    print(f"  ✅ {msg}")


def fail_(msg):
    print(f"  ❌ {msg}")


def section(name):
    print(f"\n{'='*70}\n{name}\n{'='*70}")


def test_forum_mappings():
    section("TEST A: POST /api/forum-mappings (complete signals)")
    url = f"{BASE_URL}/api/forum-mappings"
    payload = {"forum_id": YOONG_FAMILY_FORUM_ID, "user_id": PETE_USER_ID}
    try:
        r = requests.post(url, json=payload, timeout=60)
    except Exception as e:
        fail_(f"request failed: {e}")
        results.append(("A: forum-mappings reachable", False))
        return

    ok = r.status_code == 200
    results.append(("A: HTTP 200 OK", ok))
    (pass_ if ok else fail_)(f"HTTP {r.status_code}")
    if not ok:
        print(r.text[:500])
        return

    data = r.json()
    mappings = data.get("mappings", [])
    count_ok = len(mappings) == 3
    results.append(("A: exactly 3 mappings", count_ok))
    (pass_ if count_ok else fail_)(f"mappings count = {len(mappings)} (expected 3)")

    names = {m.get("member_name") for m in mappings}
    names_ok = EXPECTED_MEMBERS.issubset(names)
    results.append(("A: members Thaddeus/Mel/Isaac present", names_ok))
    (pass_ if names_ok else fail_)(f"member names: {names}")

    for m in mappings:
        name = m.get("member_name")
        signals = m.get("signals") or {}
        print(f"\n  --- Member: {name} ---")

        enn = signals.get("enneagram")
        enn_ok = (
            isinstance(enn, dict)
            and isinstance(enn.get("how_you_help_them"), list)
            and isinstance(enn.get("how_they_help_you"), list)
            and len(enn.get("how_you_help_them") or []) > 0
            and len(enn.get("how_they_help_you") or []) > 0
        )
        results.append((f"A: {name} enneagram non-null w/ arrays", enn_ok))
        (pass_ if enn_ok else fail_)(
            f"enneagram: how_you_help_them={len(enn.get('how_you_help_them') or []) if isinstance(enn, dict) else 'N/A'}, "
            f"how_they_help_you={len(enn.get('how_they_help_you') or []) if isinstance(enn, dict) else 'N/A'}"
        )

        bazi = signals.get("bazi")
        bazi_ok = isinstance(bazi, dict) and len(bazi) > 0
        results.append((f"A: {name} bazi non-null object", bazi_ok))
        (pass_ if bazi_ok else fail_)(
            f"bazi keys={list(bazi.keys()) if isinstance(bazi, dict) else 'N/A'}"
        )

        if isinstance(bazi, dict):
            combined = []
            for key in ("support", "tension", "growth"):
                arr = bazi.get(key) or []
                if isinstance(arr, list):
                    combined.extend(arr)
            joined = " | ".join(str(x) for x in combined)
            has_emoji = bool(ANIMAL_EMOJI_PATTERN.search(joined))
            results.append((f"A: {name} bazi has animal emoji", has_emoji))
            (pass_ if has_emoji else fail_)(f"bazi animal emoji present: {has_emoji}")
            if has_emoji:
                for s in combined:
                    if ANIMAL_EMOJI_PATTERN.search(str(s)):
                        print(f"       → '{s}'")
                        break

        astro = signals.get("astrology")
        astro_ok = isinstance(astro, dict) and len(astro) > 0
        results.append((f"A: {name} astrology non-null object", astro_ok))
        (pass_ if astro_ok else fail_)(
            f"astrology keys={list(astro.keys()) if isinstance(astro, dict) else 'N/A'}"
        )

        hd = signals.get("human_design")
        hd_ok = isinstance(hd, list)
        results.append((f"A: {name} human_design is array", hd_ok))
        (pass_ if hd_ok else fail_)(
            f"human_design type={type(hd).__name__}, len={len(hd) if isinstance(hd, list) else 'N/A'}"
        )


def test_fix_deployed_data():
    section("TEST B: GET /api/fix-deployed-data (seeds all duplicates)")
    url = f"{BASE_URL}/api/fix-deployed-data"
    try:
        r = requests.get(url, timeout=60)
    except Exception as e:
        fail_(f"request failed: {e}")
        results.append(("B: fix-deployed-data reachable", False))
        return

    ok = r.status_code == 200
    results.append(("B: HTTP 200 OK", ok))
    (pass_ if ok else fail_)(f"HTTP {r.status_code}")
    if not ok:
        print(r.text[:500])
        return

    data = r.json()
    fixes = data.get("fixes", [])
    errors = data.get("errors", [])

    errors_ok = len(errors) == 0
    results.append(("B: errors array is empty", errors_ok))
    (pass_ if errors_ok else fail_)(f"errors: {errors}")

    pete_count = sum(1 for f in fixes if f.startswith("Pete"))
    mel_count = sum(1 for f in fixes if f.startswith("Mel"))
    thad_count = sum(1 for f in fixes if f.startswith("Thaddeus Yoong"))
    isaac_count = sum(1 for f in fixes if f.startswith("Isaac Yoong"))

    pete_ok = pete_count >= 2
    mel_ok = mel_count >= 2  # handles "Mel" and "Mel "
    thad_ok = thad_count >= 1
    isaac_ok = isaac_count >= 1

    results.append(("B: Pete duplicates (>=2) seeded", pete_ok))
    (pass_ if pete_ok else fail_)(f"Pete records in fixes: {pete_count}")

    results.append(("B: Mel duplicates (>=2) seeded", mel_ok))
    (pass_ if mel_ok else fail_)(f"Mel records in fixes: {mel_count}")

    results.append(("B: Thaddeus Yoong seeded (>=1)", thad_ok))
    (pass_ if thad_ok else fail_)(f"Thaddeus Yoong records in fixes: {thad_count}")

    results.append(("B: Isaac Yoong seeded (>=1)", isaac_ok))
    (pass_ if isaac_ok else fail_)(f"Isaac Yoong records in fixes: {isaac_count}")

    print(f"\n  Total fixes: {len(fixes)}, summary={data.get('summary')}")


def test_get_user_forums():
    section("TEST C1: POST /api/get-user-forums (regression)")
    url = f"{BASE_URL}/api/get-user-forums"
    try:
        r = requests.post(url, json={"user_id": PETE_USER_ID}, timeout=30)
    except Exception as e:
        fail_(f"request failed: {e}")
        results.append(("C1: get-user-forums reachable", False))
        return
    ok = r.status_code == 200
    results.append(("C1: HTTP 200 OK", ok))
    (pass_ if ok else fail_)(f"HTTP {r.status_code}")
    if not ok:
        return
    data = r.json()
    forums = data.get("forums", [])
    list_ok = isinstance(forums, list) and len(forums) > 0
    results.append(("C1: forums list non-empty", list_ok))
    (pass_ if list_ok else fail_)(f"forums count = {len(forums)}")


def test_get_forum_members():
    section("TEST C2: GET /api/forums/{id}/members (regression)")
    url = f"{BASE_URL}/api/forums/{YOONG_FAMILY_FORUM_ID}/members"
    try:
        r = requests.get(url, params={"user_id": PETE_USER_ID}, timeout=30)
    except Exception as e:
        fail_(f"request failed: {e}")
        results.append(("C2: forums/{id}/members reachable", False))
        return
    ok = r.status_code == 200
    results.append(("C2: HTTP 200 OK", ok))
    (pass_ if ok else fail_)(f"HTTP {r.status_code}")
    if not ok:
        return
    data = r.json()
    members = data.get("members", [])
    list_ok = isinstance(members, list) and len(members) > 0
    results.append(("C2: members list non-empty", list_ok))
    (pass_ if list_ok else fail_)(f"members count = {len(members)}")


def main():
    test_forum_mappings()
    test_fix_deployed_data()
    test_get_user_forums()
    test_get_forum_members()

    section("FINAL SUMMARY")
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    for label, ok in results:
        icon = "✅" if ok else "❌"
        print(f"  {icon} {label}")
    print(f"\n  {passed}/{total} assertions passed")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
