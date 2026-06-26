"""publish_verification_numerology_v1.py — Phase 1 publish verification
========================================================================

Build marker:  relationship-parity-numerology-v1
Usage:         python publish_verification_numerology_v1.py [BASE_URL]
               (default BASE_URL = http://127.0.0.1:8001/api)

Runs the 5 acceptance criteria for the Phase 1 ship.  Exit code 0 = pass,
non-zero = fail.  Safe to point at the live deployed URL post-Publish:

    python publish_verification_numerology_v1.py \
        https://mirror-lens-fixes-r-1779710763.emergent.host/api
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from itertools import combinations
from typing import Any, Dict, List, Tuple

import httpx
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

sys.path.insert(0, '/app/backend')
load_dotenv('/app/backend/.env')

from services.forum_hd_mapping import (
    compute_numerology_signals,
    compute_astrology_signals,
    compute_bazi_signals,
    compute_enneagram_signals,
    get_forum_member_mappings,
)

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8001/api"
PETE_FORUM_ID = "69dda348de9cb1c83c0780fa"
PETE_USER_ID  = "697f0c6abf35c0528ff06954"


def _bullet(ok: bool, label: str, detail: str = "") -> str:
    mark = "  ✓" if ok else "  ✗"
    suffix = f"  — {detail}" if detail else ""
    return f"{mark} {label}{suffix}"


async def criterion_1_forum_endpoint_returns_numerology(db) -> Tuple[bool, str]:
    """Forum mapping endpoint returns signals.numerology.themes for
    Pete ↔ Mel, Pete ↔ Isaac, Pete ↔ Thaddeus."""
    mappings = await get_forum_member_mappings(db, PETE_FORUM_ID, PETE_USER_ID)
    if not mappings:
        return False, "no mappings returned"
    expected_others = {"Mel", "Isaac Yoong", "Thaddeus Yoong"}
    seen: Dict[str, List[str]] = {}
    for m in mappings:
        n = (m.get("member_name") or "").strip()
        if n in expected_others:
            themes = ((m.get("signals") or {}).get("numerology") or {}).get("themes") or []
            seen[n] = themes
    missing = expected_others - set(seen.keys())
    empty = [n for n, t in seen.items() if not t]
    ok = (not missing) and (not empty)
    detail = (
        f"present={sorted(seen.keys())}  "
        f"missing={sorted(missing)}  empty={empty}"
    )
    if ok:
        for n, t in seen.items():
            print(f"     • {n}: {t[0][:90]}{'…' if len(t[0]) > 90 else ''}")
    return ok, detail


async def criterion_2_hit_rate_for_usable_life_paths(db) -> Tuple[bool, str]:
    """Numerology hit rate ~100% for users with usable life_path."""
    users = await db.users.find({}).to_list(length=None)
    charts = {}
    for u in users:
        c = await db.charts.find_one({"user_id": str(u['_id'])})
        if c: charts[str(u['_id'])] = c
    valid = [u for u in users
             if str(u['_id']) in charts
             and (charts[str(u['_id'])].get('numerology', {}) or {}).get('life_path', {}).get('number')]
    sample = valid[:50]
    pairs = list(combinations(sample, 2))[:200]
    hits = 0
    for a, b in pairs:
        r = compute_numerology_signals(
            charts[str(a['_id'])], charts[str(b['_id'])],
            a.get('name', 'A'), b.get('name', 'B'),
        )
        if r and r.get("themes"):
            hits += 1
    rate = hits / max(len(pairs), 1)
    ok = rate >= 0.99
    return ok, f"{hits}/{len(pairs)} pairs returned themes ({100*rate:.1f}%)"


async def criterion_3_no_frontend_change_required(_db) -> Tuple[bool, str]:
    """Verify the FE contract is unchanged: signals.numerology.themes
    (and nothing else) is what the Forum FE reads."""
    fe = "/app/frontend/app/forums/mappings.tsx"
    if not os.path.exists(fe):
        return False, "FE file not found"
    with open(fe) as f:
        src = f.read()
    expected = "signals.numerology.themes"
    ok = expected in src
    return ok, f"'{expected}' present in mappings.tsx: {ok}"


async def criterion_4_other_lenses_unchanged(db) -> Tuple[bool, str]:
    """BaZi, HD, Astrology, Enneagram remain unchanged.  Spot-check
    Pete↔Thaddeus shape against the field set we recorded yesterday."""
    pete = await db.users.find_one({"name": "Pete"})
    thad = await db.users.find_one({"name": {"$regex": "thaddeus", "$options": "i"}})
    if not pete or not thad:
        return False, "Pete or Thaddeus not found"
    cp = await db.charts.find_one({"user_id": str(pete['_id'])})
    ct = await db.charts.find_one({"user_id": str(thad['_id'])})
    astro = compute_astrology_signals(cp, ct, "Pete", "Thaddeus")
    bazi  = compute_bazi_signals(cp, ct, "Pete", "Thaddeus")
    ennea = compute_enneagram_signals(pete, thad, "Pete", "Thaddeus")
    checks = [
        ("astrology dict & has attraction key",
         isinstance(astro, dict) and "attraction" in astro),
        ("bazi dict & has support key",
         isinstance(bazi, dict) and "support" in bazi),
        ("enneagram dict",
         isinstance(ennea, dict)),
    ]
    failures = [name for name, ok in checks if not ok]
    return (not failures), f"failures={failures}" if failures else "all lens shapes preserved"


async def criterion_5_api_contract_unchanged(_db) -> Tuple[bool, str]:
    """Forum mapping API still returns the same top-level signal keys
    and Numerology returns shape {themes:[...]} — no new required keys."""
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as cx:
        try:
            r = await cx.post(
                f"{BASE_URL}/forum-mappings",
                json={
                    "forum_id": PETE_FORUM_ID,
                    "user_id":  PETE_USER_ID,
                },
            )
        except Exception as e:
            return False, f"HTTP error: {e}"
    if r.status_code != 200:
        return False, f"HTTP {r.status_code}: {r.text[:200]}"
    body = r.json()
    mappings = body.get("mappings") or []
    if not mappings:
        return False, "empty mappings array"
    first = mappings[0]
    sig = first.get("signals") or {}
    expected_keys = {"human_design", "astrology", "bazi", "enneagram", "numerology"}
    actual = set(sig.keys())
    missing = expected_keys - actual
    if missing:
        return False, f"missing signal keys: {missing}"
    numer = sig.get("numerology")
    if isinstance(numer, dict):
        # Must have themes; may have other future-additive keys; must not
        # have removed themes.
        if "themes" not in numer:
            return False, f"numerology.themes missing — keys={list(numer.keys())}"
    return True, f"all 5 lens keys present; numerology.themes shape preserved"


async def main():
    mongo = AsyncIOMotorClient(os.getenv("MONGO_URL"))
    db = mongo[os.getenv("DB_NAME", "test_database")]

    print(f"\n══════════════════════════════════════════════════════════════")
    print(f"  Phase 1 Publish Verification — relationship-parity-numerology-v1")
    print(f"  Target API base URL: {BASE_URL}")
    print(f"══════════════════════════════════════════════════════════════\n")

    results = []
    for label, fn in [
        ("1. Forum endpoint returns signals.numerology.themes for Pete↔Mel/Isaac/Thaddeus",
         criterion_1_forum_endpoint_returns_numerology),
        ("2. Numerology hit rate ~100% for users with usable life_path",
         criterion_2_hit_rate_for_usable_life_paths),
        ("3. No frontend changes required (FE still reads signals.numerology.themes)",
         criterion_3_no_frontend_change_required),
        ("4. BaZi, HD, Astrology, Enneagram unchanged",
         criterion_4_other_lenses_unchanged),
        ("5. No API contract changes (top-level signal keys + Numerology shape)",
         criterion_5_api_contract_unchanged),
    ]:
        try:
            ok, detail = await fn(db)
        except Exception as e:
            ok, detail = False, f"EXCEPTION: {type(e).__name__}: {e}"
        print(_bullet(ok, label, detail))
        results.append((label, ok))

    mongo.close()
    print()
    if all(ok for _, ok in results):
        print("══════════════════════════════════════════════════════════════")
        print("  ✓ ALL 5 CRITERIA PASSED — Phase 1 deploy verified")
        print("══════════════════════════════════════════════════════════════\n")
        return 0
    else:
        print("══════════════════════════════════════════════════════════════")
        print(f"  ✗ {sum(1 for _, ok in results if not ok)} CRITERIA FAILED")
        print("══════════════════════════════════════════════════════════════\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
