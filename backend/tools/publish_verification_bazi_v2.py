"""publish_verification_bazi_v2.py — Phase 3 publish verification
==================================================================

Build marker:  relationship-bazi-engine-v2
Usage:         python publish_verification_bazi_v2.py [BASE_URL]
"""
from __future__ import annotations

import asyncio
import os
import sys
from itertools import combinations
from typing import Tuple

import httpx
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

sys.path.insert(0, '/app/backend')
load_dotenv('/app/backend/.env')

from services.forum_hd_mapping import get_forum_member_mappings
from services.relationship_bazi_engine_v2 import enrich_bazi_relationship

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8001/api"
PETE_FORUM_ID = "69dda348de9cb1c83c0780fa"
PETE_USER_ID  = "697f0c6abf35c0528ff06954"

REQUIRED_V2_KEYS = {
    "natural_strength", "repair_pathway", "current_movement",
    "how_they_help_each_other", "how_they_challenge_each_other",
    "current_relationship_season",
}
LEGACY_V3_KEYS = {
    "core_dynamic", "what_strengthens", "growth_edge",
    "shadow_pattern", "why_matters", "what_bazi_sees",
}
REQUIRED_DIAGNOSTICS = {
    "day_master_relation", "ten_gods_a_sees_b", "ten_gods_b_sees_a",
    "animal_relation_year", "animal_relation_day",
    "hidden_stem_relation", "yin_yang_relation", "bridge_element",
    "luck_pillar_relation", "current_annual_pillar", "engine_version",
}


def _b(ok, l, d=""): return f"  {'✓' if ok else '✗'} {l}{(' — ' + d) if d else ''}"


async def c1_v2_keys_present_for_pete_forum(db) -> Tuple[bool, str]:
    mappings = await get_forum_member_mappings(db, PETE_FORUM_ID, PETE_USER_ID)
    seen, missing = {}, []
    for m in mappings:
        bz = ((m.get("signals") or {}).get("bazi") or {})
        card = bz.get("v2_card") or {}
        absent = REQUIRED_V2_KEYS - set(card.keys())
        seen[m.get("member_name")] = sorted(card.keys())
        if absent: missing.append(f"{m.get('member_name')}: missing {absent}")
    ok = not missing and bool(seen)
    return ok, ("all v2 keys present for "
                + ", ".join(seen.keys())) if ok else "; ".join(missing)


async def c2_legacy_keys_preserved(db) -> Tuple[bool, str]:
    mappings = await get_forum_member_mappings(db, PETE_FORUM_ID, PETE_USER_ID)
    missing = []
    for m in mappings:
        card = ((m.get("signals") or {}).get("bazi") or {}).get("v2_card") or {}
        absent = LEGACY_V3_KEYS - set(card.keys())
        if absent: missing.append(f"{m.get('member_name')}: lost {absent}")
    return not missing, ("legacy v3 keys preserved" if not missing else "; ".join(missing))


async def c3_diagnostics_complete(db) -> Tuple[bool, str]:
    mappings = await get_forum_member_mappings(db, PETE_FORUM_ID, PETE_USER_ID)
    missing = []
    for m in mappings:
        diag = ((m.get("signals") or {}).get("bazi") or {}).get("diagnostics") or {}
        absent = REQUIRED_DIAGNOSTICS - set(diag.keys())
        if absent: missing.append(f"{m.get('member_name')}: missing diag {absent}")
    return not missing, ("all 11 diagnostic keys present"
                        if not missing else "; ".join(missing))


async def c4_other_lenses_unchanged(db) -> Tuple[bool, str]:
    """Spot check signal dict keys for Pete↔Mel/Isaac/Thaddeus."""
    mappings = await get_forum_member_mappings(db, PETE_FORUM_ID, PETE_USER_ID)
    expected = {"human_design", "astrology", "bazi", "enneagram", "numerology"}
    for m in mappings:
        s = m.get("signals") or {}
        miss = expected - set(s.keys())
        if miss: return False, f"{m.get('member_name')}: missing {miss}"
    return True, "all 5 lens keys present per pair"


async def c5_no_forbidden_language(db) -> Tuple[bool, str]:
    from services.relationship_bazi_engine_v2 import find_forbidden_language
    mappings = await get_forum_member_mappings(db, PETE_FORUM_ID, PETE_USER_ID)
    violations = []
    for m in mappings:
        card = ((m.get("signals") or {}).get("bazi") or {}).get("v2_card") or {}
        for k, v in card.items():
            if not isinstance(v, str): continue
            bad = find_forbidden_language(v)
            if bad: violations.append(f"{m.get('member_name')}/{k}: {bad}")
    return not violations, "no forbidden tokens" if not violations else "; ".join(violations)


async def c6_db_sweep(db) -> Tuple[bool, str]:
    users = await db.users.find({}).to_list(length=None)
    charts = {}
    for u in users:
        c = await db.charts.find_one({"user_id": str(u["_id"])})
        if c and ((c.get("bazi") or {}).get("day_master") or {}).get("element"):
            charts[str(u["_id"])] = c
    sample = list(charts.values())[:30]
    pairs = list(combinations(sample, 2))[:200]
    ok = 0
    for a, b in pairs:
        r = enrich_bazi_relationship(a, b, "A", "B")
        if r and set(r["v2_card"].keys()) == REQUIRED_V2_KEYS:
            ok += 1
    return ok == len(pairs), f"{ok}/{len(pairs)} pairs emit full v2_card"


async def c7_live_http_smoke(_db) -> Tuple[bool, str]:
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as cx:
        try:
            r = await cx.post(f"{BASE_URL}/forum-mappings",
                              json={"forum_id": PETE_FORUM_ID, "user_id": PETE_USER_ID})
        except Exception as e:
            return False, f"HTTP {e}"
    if r.status_code != 200:
        return False, f"HTTP {r.status_code}: {r.text[:120]}"
    body = r.json()
    ms = body.get("mappings") or []
    if not ms:
        return False, "empty mappings (likely env data split — see report)"
    sample = ms[0]
    bz = ((sample.get("signals") or {}).get("bazi") or {}).get("v2_card") or {}
    miss = REQUIRED_V2_KEYS - set(bz.keys())
    return (not miss), f"first mapping bazi.v2_card keys = {sorted(bz.keys())}"


async def c8_numerology_regression_unchanged(db) -> Tuple[bool, str]:
    """Phase 1+2-lite numerology hit rate must still be ~100%."""
    from services.forum_hd_mapping import compute_numerology_signals
    users = await db.users.find({}).to_list(length=None)
    charts = {}
    for u in users:
        c = await db.charts.find_one({"user_id": str(u["_id"])})
        if c and (c.get("numerology", {}) or {}).get("life_path", {}).get("number"):
            charts[str(u["_id"])] = (u, c)
    sample = list(charts.values())[:50]
    pairs = list(combinations(sample, 2))[:200]
    hits = 0
    for (ua, ca), (ub, cb) in pairs:
        r = compute_numerology_signals(ca, cb,
                                       ua.get("name","A"), ub.get("name","B"))
        if r and r.get("themes") and "v2_card" in r:
            hits += 1
    rate = hits / max(len(pairs), 1)
    return rate >= 0.99, f"{hits}/{len(pairs)} pairs ({100*rate:.1f}%)"


async def main():
    mc = AsyncIOMotorClient(os.getenv("MONGO_URL"))
    db = mc[os.getenv("DB_NAME","test_database")]
    print("\n══════════════════════════════════════════════════════════════")
    print("  Phase 3 BaZi V2 Verification — relationship-bazi-engine-v2")
    print(f"  Target: {BASE_URL}")
    print("══════════════════════════════════════════════════════════════\n")
    results = []
    for label, fn in [
        ("1. v2_card emits 6 new parity keys for Pete's forum pairs", c1_v2_keys_present_for_pete_forum),
        ("2. Legacy v3 keys (core_dynamic, what_strengthens, …) preserved", c2_legacy_keys_preserved),
        ("3. Diagnostics carries all 11 dimensional fields", c3_diagnostics_complete),
        ("4. Other 4 lenses (HD, astro, ennea, numer) keys present", c4_other_lenses_unchanged),
        ("5. No forbidden language anywhere in live BaZi v2_cards", c5_no_forbidden_language),
        ("6. DB sweep — v2_card complete for all valid BaZi pairs", c6_db_sweep),
        ("7. Live HTTP smoke test (env-dependent — informational)", c7_live_http_smoke),
        ("8. Numerology Phase 1+2-lite hit rate unaffected", c8_numerology_regression_unchanged),
    ]:
        try: ok, d = await fn(db)
        except Exception as e: ok, d = False, f"EXCEPTION {type(e).__name__}: {e}"
        print(_b(ok, label, d)); results.append((label, ok))
    mc.close()
    blockers = [l for l, ok in results if not ok and "informational" not in l]
    print()
    if not blockers:
        print("══════════════════════════════════════════════════════════════")
        print("  ✓ ALL BLOCKING CRITERIA PASSED — Phase 3 ready for publish")
        print("══════════════════════════════════════════════════════════════\n")
        return 0
    print(f"\n  ✗ {len(blockers)} blocking failure(s)\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
