"""
Home V6 'behavioral-first' refactor verification.

Tests that layers.hook + layers.recognition + layers.cost contain NO astrology
terms, while astrology signals are preserved in why_showing_up.signals.
"""
import re
import sys
import requests
import json

BASE = "https://mirror-forum-fix.preview.emergentagent.com/api"
PETE = "697f0c6abf35c0528ff06954"
MEL  = "697ec826ad4b18f75bf42616"
FORUM_YOONG = "69dda348de9cb1c83c0780fa"

FORBIDDEN = [
    # Planets
    "Sun","Moon","Mercury","Venus","Mars","Jupiter","Saturn","Uranus","Neptune","Pluto","Chiron","Lilith",
    # Signs
    "Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces",
    # Astro terms
    "transit","conjunction","opposition","square","trine","sextile","retrograde","sidereal","tropical","zodiac",
    "ayanamsa","stellium","lunar","eclipse","ascendant","midheaven","house",
    # HD jargon
    "gate","channel","center","profile","authority",
]

FORBIDDEN_PATTERNS = [(w, re.compile(r"\b" + re.escape(w) + r"\b", re.IGNORECASE)) for w in FORBIDDEN]

def whole_word_hits(text: str):
    hits = []
    for word, pat in FORBIDDEN_PATTERNS:
        for m in pat.finditer(text or ""):
            hits.append((word, m.group(0), m.start()))
    return hits

ASTRO_HINT = re.compile(
    r"\b(sun|moon|mercury|venus|mars|jupiter|saturn|uranus|neptune|pluto|chiron|lilith|"
    r"aries|taurus|gemini|cancer|leo|virgo|libra|scorpio|sagittarius|capricorn|aquarius|pisces|"
    r"transit|conjunction|opposition|square|trine|retrograde|sidereal|stellium|lunar|eclipse|"
    r"ascendant|midheaven|house|gate|channel|center|profile|authority)\b",
    re.IGNORECASE,
)

results = []

def record(name, ok, detail=""):
    tag = "✅ PASS" if ok else "❌ FAIL"
    print(f"{tag} {name}")
    if detail:
        for line in detail.splitlines():
            print(f"    {line}")
    results.append((name, ok, detail))
    return ok


def fetch_home(user_id: str):
    url = f"{BASE}/home-insight-v5/{user_id}"
    print(f"\n--- GET {url} ---")
    r = requests.get(url, timeout=60)
    print(f"  status = {r.status_code}")
    r.raise_for_status()
    return r.json()


def check_forbidden(label, text):
    hits = whole_word_hits(text)
    if hits:
        print(f"  FORBIDDEN HITS in {label}:")
        for w, match, pos in hits:
            print(f"    -> {w!r} matched {match!r} at pos {pos}")
    return hits


def test_user(user_id, user_name):
    print(f"\n========== {user_name} ({user_id}) ==========")
    data = fetch_home(user_id)

    # Capture top-level diagnostics
    print(f"  version      = {data.get('version')}")
    print(f"  render_mode  = {data.get('render_mode')}")
    print(f"  signal_count = {data.get('signal_count')}")
    print(f"  distinct_sources = {data.get('distinct_sources')}")

    layers = data.get("layers") or {}
    hook = layers.get("hook") or ""
    recognition = layers.get("recognition") or ""
    cost = layers.get("cost") or ""
    move = layers.get("move") or ""

    print("\n  layers.hook        = " + repr(hook))
    print("  layers.recognition = " + repr(recognition))
    print("  layers.cost        = " + repr(cost))
    print("  layers.move        = " + repr(move))

    # Test A — forbidden words in top 3 lines
    top3 = f"{hook}\n{recognition}\n{cost}"
    hook_hits = check_forbidden("layers.hook", hook)
    recog_hits = check_forbidden("layers.recognition", recognition)
    cost_hits = check_forbidden("layers.cost", cost)
    all_hits = hook_hits + recog_hits + cost_hits

    record(
        f"[{user_name}] Test A — No forbidden words in top 3 lines",
        len(all_hits) == 0,
        f"{len(all_hits)} forbidden word hits." if all_hits else "Clean."
    )

    # Test B — behavioral content
    opens_ok_prefixes = ("You're", "You", "The", "Something", "What", "A part", "There",
                         "It's", "Today", "This")
    hook_starts_ok = any(hook.lstrip().startswith(p) for p in opens_ok_prefixes) and len(hook.strip()) > 0
    record(
        f"[{user_name}] Test B1 — layers.hook is non-empty & starts behaviorally",
        hook_starts_ok,
        f"hook startswith check; first 50 chars: {hook[:50]!r}",
    )

    recog_youre = recognition.count("You're") + recognition.count("you're")
    # Either starts with "You're" or contains multiple "You're"
    recog_ok = (recognition.strip().startswith("You're") or recog_youre >= 1) and len(recognition.strip()) > 0
    record(
        f"[{user_name}] Test B2 — layers.recognition has concrete behavior (contains \"You're\")",
        recog_ok,
        f"'You're' count = {recog_youre}",
    )

    cost_keywords = ["costs", "erodes", "builds", "creates", "cost", "erode", "build", "create"]
    has_cost_word = any(re.search(r"\b" + re.escape(w) + r"\b", cost, re.IGNORECASE) for w in cost_keywords)
    record(
        f"[{user_name}] Test B3 — layers.cost names impact (costs/erodes/builds/creates)",
        has_cost_word,
        f"cost text: {cost!r}",
    )

    imperative_starts = ("Do ", "Write", "Name", "Say", "Send", "Stop", "Pick", "Don't",
                         "Ask", "Choose", "Tell", "Start", "Notice", "Look", "Let",
                         "Put", "Take", "Give", "Make", "Keep", "Leave", "Open", "Close",
                         "Call", "Draw", "Move")
    move_ok = any(move.strip().startswith(p) for p in imperative_starts)
    record(
        f"[{user_name}] Test B4 — layers.move is imperative (action directive)",
        move_ok,
        f"move first word: {move.strip().split(' ')[0] if move.strip() else '(empty)'!r}; full: {move!r}",
    )

    # Test C — astrology lives in proof layer
    why = data.get("why_showing_up") or {}
    proof_signals = why.get("signals") or []
    record(
        f"[{user_name}] Test C1 — why_showing_up.signals is non-empty list of strings",
        isinstance(proof_signals, list) and len(proof_signals) > 0 and all(isinstance(s, str) for s in proof_signals),
        f"proof count = {len(proof_signals)}; sample: {proof_signals[:3]}",
    )
    any_astro = any(ASTRO_HINT.search(s) for s in proof_signals)
    record(
        f"[{user_name}] Test C2 — at least one proof signal contains astrology term",
        any_astro,
        "Astrology is preserved in collapsed proof layer." if any_astro else "NO astrology terms found anywhere in proof!",
    )

    # Also cross-check back-compat mappings
    record(
        f"[{user_name}] headline == layers.hook (back-compat mapping)",
        data.get("headline") == hook,
        f"headline = {data.get('headline')!r}",
    )
    record(
        f"[{user_name}] identity_mirror == layers.recognition",
        data.get("identity_mirror") == recognition,
        f"identity_mirror = {data.get('identity_mirror')!r}",
    )
    record(
        f"[{user_name}] what_this_creates == layers.cost",
        data.get("what_this_creates") == cost,
        f"what_this_creates = {data.get('what_this_creates')!r}",
    )
    record(
        f"[{user_name}] the_move == layers.move",
        data.get("the_move") == move,
        f"the_move = {data.get('the_move')!r}",
    )

    return {
        "hook": hook, "recognition": recognition, "cost": cost, "move": move,
        "proof_signals": proof_signals,
        "version": data.get("version"),
        "render_mode": data.get("render_mode"),
    }


def test_forum_mappings_regression():
    print("\n========== Test E.1 — POST /api/forum-mappings regression ==========")
    url = f"{BASE}/forum-mappings"
    payload = {"forum_id": FORUM_YOONG, "user_id": PETE}
    print(f"POST {url}")
    print(f"payload = {payload}")
    r = requests.post(url, json=payload, timeout=60)
    print(f"  status = {r.status_code}")
    ok = r.status_code == 200
    if not ok:
        print(f"  body: {r.text[:500]}")
        record("Test E.1 — POST /api/forum-mappings HTTP 200", False, r.text[:300])
        return
    body = r.json()
    mappings = body.get("mappings") or body.get("members") or body.get("result") or []
    # Some endpoints use different keys; try both
    if not mappings and isinstance(body, dict):
        for k, v in body.items():
            if isinstance(v, list) and v and isinstance(v[0], dict) and "signals" in v[0]:
                mappings = v
                break
    record("Test E.1 — POST /api/forum-mappings HTTP 200", True, f"keys={list(body.keys())}")
    record("Test E.1 — 3 mappings returned", len(mappings) == 3, f"got {len(mappings)}")

    # Each mapping has signals for Enneagram + BaZi + Astrology + HD
    for i, m in enumerate(mappings):
        name = m.get("name") or m.get("user_name") or f"#{i}"
        sigs = m.get("signals") or {}
        keys = set(sigs.keys()) if isinstance(sigs, dict) else set()
        # Expected keys
        has_enne = any("enneagram" in k.lower() for k in keys) or "enneagram" in keys
        has_bazi = any("bazi" in k.lower() for k in keys) or "bazi" in keys
        has_astro = any("astrology" in k.lower() or "astro" in k.lower() for k in keys)
        has_hd = any(("human_design" in k.lower()) or k.lower() in ("hd",) for k in keys)
        record(
            f"Test E.1 [{name}] signals has enneagram+bazi+astrology+HD",
            has_enne and has_bazi and has_astro and has_hd,
            f"keys present: {sorted(keys)}",
        )


def test_canonical_regression():
    print("\n========== Test E.2 — GET /api/diagnostics/canonical-astronomy (Pete) ==========")
    url = f"{BASE}/diagnostics/canonical-astronomy/{PETE}"
    r = requests.get(url, timeout=60)
    print(f"  status = {r.status_code}")
    record("Test E.2 — canonical-astronomy HTTP 200", r.status_code == 200)
    if r.status_code == 200:
        body = r.json()
        record("Test E.2 — pass == true", body.get("pass") is True, f"pass={body.get('pass')}")


def main():
    pete = test_user(PETE, "Pete")
    mel  = test_user(MEL,  "Mel")

    # Test D — per-user differentiation
    print("\n========== Test D — Pete vs Mel differentiation ==========")
    different = pete["hook"] != mel["hook"]
    record(
        "Test D — Pete.hook != Mel.hook (per-user personalization)",
        different,
        f"Pete.hook = {pete['hook']!r}\nMel.hook  = {mel['hook']!r}",
    )

    # Regression tests
    test_forum_mappings_regression()
    test_canonical_regression()

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    total = len(results)
    passed = sum(1 for _, ok, _ in results if ok)
    for name, ok, _ in results:
        print(f"  {'✅' if ok else '❌'} {name}")
    print(f"\n{passed}/{total} tests passed")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
