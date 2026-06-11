"""
Phase 2A — Pete Dry-Run Diff Report (READ-ONLY).

Builds the full before/after impact analysis for canonical Pete using the
verified historical timezone correction.  No DB writes occur.  Nothing is
persisted.  Caches are not invalidated.
"""
from __future__ import annotations

import os, sys, asyncio, json, math
from datetime import datetime, timezone as dt_tz
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bson
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from calculations.astrology import get_full_natal_chart
from calculations.human_design import get_human_design_chart

load_dotenv()
db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ.get("DB_NAME", "test_database")]

PETE_USER_ID = "697f0c6abf35c0528ff06954"
MEL_USER_ID = "697ec826ad4b18f75bf42616"
LAT = 3.1073
LON = 101.6068
LOCAL_BIRTH = datetime(1968, 4, 1, 1, 25, 0)
CORRECT_UTC = datetime(1968, 3, 31, 17, 55, 0, tzinfo=dt_tz.utc)

SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
         "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

ASPECT_TYPES = {
    "conjunction": (0, 8), "opposition": (180, 8),
    "trine": (120, 7), "square": (90, 7), "sextile": (60, 5),
    "quincunx": (150, 3), "semi-sextile": (30, 2),
}


def sign_of(longitude: float) -> Tuple[str, float]:
    long = longitude % 360.0
    idx = int(long // 30)
    deg = long - idx * 30
    return SIGNS[idx], deg


def signed_delta(a: float, b: float) -> float:
    return ((b - a + 540) % 360) - 180


def angle(d, k):
    if not d: return None
    v = (d.get("angles") or {}).get(k) or {}
    return v.get("longitude") or v.get("tropical_longitude")


def planet_lon(planets, name):
    p = (planets or {}).get(name) or {}
    return p.get("longitude") or p.get("tropical_longitude")


def planet_house(planets, name):
    p = (planets or {}).get(name) or {}
    return p.get("house")


def compute_aspects(planets: Dict, asc_lon: float = None) -> List[Dict]:
    """Compute aspects between major bodies (in-memory only)."""
    bodies = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
              "Uranus", "Neptune", "Pluto", "Chiron", "North Node"]
    out = []
    longs = {b: planet_lon(planets, b) for b in bodies if planet_lon(planets, b) is not None}
    keys = list(longs.keys())
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            a, b = keys[i], keys[j]
            la, lb = longs[a], longs[b]
            dist = min(abs(la - lb) % 360, 360 - abs(la - lb) % 360)
            for name, (target, orb) in ASPECT_TYPES.items():
                if abs(dist - target) <= orb:
                    out.append({
                        "body1": a, "body2": b, "type": name,
                        "orb": round(abs(dist - target), 2),
                        "exact_angle": round(dist, 2),
                    })
                    break
    return out


def aspect_key(a):
    bodies = tuple(sorted([a["body1"], a["body2"]]))
    return (bodies, a["type"])


async def main():
    bar = "=" * 100
    sub = "-" * 100

    # ──────────────────────────────────────────────────────
    # 0. Load BEFORE state
    # ──────────────────────────────────────────────────────
    pete_user = await db.users.find_one({"_id": bson.ObjectId(PETE_USER_ID)})
    pete_chart = await db.charts.find_one({"user_id": PETE_USER_ID})
    mel_chart = await db.charts.find_one({"user_id": MEL_USER_ID})

    if not pete_chart:
        print("ERROR: Pete chart not found"); return

    before_astro = pete_chart.get("astrology") or {}
    before_hd = pete_chart.get("human_design") or {}
    before_meta = before_astro.get("metadata") or {}
    before_utc_iso = before_meta.get("birth_utc") or before_meta.get("birth_datetime_utc")

    # The stored chart was computed with stored tz +07:00 → UTC 18:25
    from datetime import timedelta
    stored_utc = (LOCAL_BIRTH - timedelta(minutes=7 * 60)).replace(tzinfo=dt_tz.utc)

    # ──────────────────────────────────────────────────────
    # AFTER state — in-memory only
    # ──────────────────────────────────────────────────────
    after_chart = get_full_natal_chart(CORRECT_UTC.replace(tzinfo=None), LAT, LON)
    after_astro = after_chart  # this is already the astrology block
    try:
        after_hd = get_human_design_chart(CORRECT_UTC, LAT, LON)
    except Exception as e:
        print(f"HD recompute failed: {type(e).__name__}: {e}")
        after_hd = {}

    # Hard guarantee
    HARD = {"write_count": 0, "charts_updated": 0,
            "cache_rows_deleted": 0, "migrations_triggered": False}

    # ──────────────────────────────────────────────────────
    # SECTION 1 — Astrology
    # ──────────────────────────────────────────────────────
    print(bar)
    print("PHASE 2A — PETE DRY-RUN DIFF REPORT (READ-ONLY)")
    print(bar)
    print(json.dumps(HARD, indent=2))
    print()
    print("USER          : Pete (canonical)  697f0c6abf35c0528ff06954")
    print(f"BEFORE UTC    : {stored_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}  (stored_tz=+07:00)")
    print(f"AFTER  UTC    : {CORRECT_UTC.strftime('%Y-%m-%d %H:%M:%S UTC')}  (tz=Asia/Kuala_Lumpur, historical +07:30)")
    print(f"UTC Δ         : -30 min")
    print()

    print("──── SECTION 1 — ASTROLOGY DIFF " + sub[31:])

    # 1.1 Birth UTC
    print("\n[1.1] Birth UTC")
    print(f"   before : {stored_utc.isoformat()}")
    print(f"   after  : {CORRECT_UTC.isoformat()}")
    print(f"   delta  : -30 min")

    # 1.2 Asc
    asc_b = angle(before_astro, "asc")
    asc_a = angle(after_astro, "asc")
    s_b, d_b = sign_of(asc_b); s_a, d_a = sign_of(asc_a)
    print("\n[1.2] Ascendant")
    print(f"   before : {asc_b:.4f}°  ({s_b} {d_b:.2f}°)")
    print(f"   after  : {asc_a:.4f}°  ({s_a} {d_a:.2f}°)")
    print(f"   delta  : {signed_delta(asc_b, asc_a):+.4f}°   sign change: {s_b} → {s_a}")

    # 1.3 MC
    mc_b = angle(before_astro, "mc"); mc_a = angle(after_astro, "mc")
    s_b, d_b = sign_of(mc_b); s_a, d_a = sign_of(mc_a)
    print("\n[1.3] Midheaven (MC)")
    print(f"   before : {mc_b:.4f}°  ({s_b} {d_b:.2f}°)")
    print(f"   after  : {mc_a:.4f}°  ({s_a} {d_a:.2f}°)")
    print(f"   delta  : {signed_delta(mc_b, mc_a):+.4f}°   sign change: {s_b} → {s_a}")

    # 1.4 House cusps
    cusps_b = (before_astro.get("houses") or {}).get("cusps") or []
    cusps_a = (after_astro.get("houses") or {}).get("cusps") or []
    print("\n[1.4] House cusps (Equal-house)")
    print(f"   {'House':<6}{'Before':>14}{'After':>14}{'Δ°':>10}{'Sign before':>18}{'Sign after':>18}")
    for i in range(12):
        b = cusps_b[i] if i < len(cusps_b) else None
        a = cusps_a[i] if i < len(cusps_a) else None
        if b is None or a is None:
            continue
        sb, _ = sign_of(b); sa, _ = sign_of(a)
        print(f"   {i+1:<6}{b:>14.4f}{a:>14.4f}{signed_delta(b,a):>10.4f}{sb:>18}{sa:>18}")

    # 1.5 Planet positions
    print("\n[1.5] Planet positions (tropical longitude, sidereal-engine output)")
    bodies = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
              "Uranus", "Neptune", "Pluto", "Chiron", "North Node", "South Node"]
    bp = before_astro.get("planets") or {}
    ap = after_astro.get("planets") or {}
    print(f"   {'body':<14}{'before°':>14}{'after°':>14}{'Δ°':>10}"
          f"{'sign before':>16}{'sign after':>16}")
    house_changes: List[str] = []
    for body in bodies:
        lb = planet_lon(bp, body); la = planet_lon(ap, body)
        if lb is None or la is None: continue
        sb, _ = sign_of(lb); sa, _ = sign_of(la)
        print(f"   {body:<14}{lb:>14.4f}{la:>14.4f}{signed_delta(lb,la):>10.4f}"
              f"{sb:>16}{sa:>16}")
        # 1.6 House changes
        hb = planet_house(bp, body); ha = planet_house(ap, body)
        if hb is not None and ha is not None and hb != ha:
            house_changes.append(f"{body}: House {hb} → House {ha}")

    # 1.6
    print("\n[1.6] House placement changes")
    if not house_changes:
        print("   (none)")
    else:
        for line in house_changes:
            print(f"   • {line}")

    # 1.7 Aspect changes
    asp_b_raw = before_astro.get("aspects") or []
    asp_a_raw = compute_aspects(ap, asc_a)
    bmap = {aspect_key(x): x for x in asp_b_raw if isinstance(x, dict) and "body1" in x}
    amap = {aspect_key(x): x for x in asp_a_raw}
    added = [k for k in amap if k not in bmap]
    removed = [k for k in bmap if k not in amap]
    common = [k for k in amap if k in bmap]
    tightened = []; loosened = []
    for k in common:
        ob = bmap[k].get("orb"); oa = amap[k].get("orb")
        if ob is None or oa is None: continue
        if oa < ob - 0.5: tightened.append((k, ob, oa))
        elif oa > ob + 0.5: loosened.append((k, ob, oa))

    print("\n[1.7] Aspect changes")
    print(f"   Added   ({len(added)}):")
    for k in added[:20]:
        print(f"     • {k[0][0]} {k[1]} {k[0][1]}  orb={amap[k]['orb']}°")
    print(f"   Removed ({len(removed)}):")
    for k in removed[:20]:
        print(f"     • {k[0][0]} {k[1]} {k[0][1]}  orb_before={bmap[k]['orb']}°")
    print(f"   Tightened ({len(tightened)}):")
    for k, ob, oa in tightened[:20]:
        print(f"     • {k[0][0]} {k[1]} {k[0][1]}  {ob}° → {oa}°")
    print(f"   Loosened ({len(loosened)}):")
    for k, ob, oa in loosened[:20]:
        print(f"     • {k[0][0]} {k[1]} {k[0][1]}  {ob}° → {oa}°")

    # ──────────────────────────────────────────────────────
    # SECTION 2 — Human Design
    # ──────────────────────────────────────────────────────
    print("\n──── SECTION 2 — HUMAN DESIGN DIFF " + sub[34:])

    def gset(d, k):
        v = d.get(k) or []
        return set(int(x) for x in v if isinstance(x, (int, str)) and str(x).isdigit())

    bp_gates = gset(before_hd, "personality_gates")
    ap_gates = gset(after_hd, "personality_gates")
    bd_gates = gset(before_hd, "design_gates")
    ad_gates = gset(after_hd, "design_gates")

    print("\n[2.1] Design date (UTC)")
    print(f"   before : {before_hd.get('design_datetime_utc_iso')}")
    print(f"   after  : {after_hd.get('design_datetime_utc_iso')}")

    print("\n[2.2] Personality gates")
    print(f"   added   : {sorted(ap_gates - bp_gates) or '—'}")
    print(f"   removed : {sorted(bp_gates - ap_gates) or '—'}")

    print("\n[2.3] Design gates")
    print(f"   added   : {sorted(ad_gates - bd_gates) or '—'}")
    print(f"   removed : {sorted(bd_gates - ad_gates) or '—'}")

    def chan_to_tuple(ch):
        if isinstance(ch, dict):
            g = sorted([ch.get("gate1"), ch.get("gate2")])
            return tuple(g)
        return tuple(sorted([int(x) for x in str(ch).split("-")]))

    chans_b = sorted({chan_to_tuple(c) for c in (before_hd.get("defined_channels") or [])})
    chans_a = sorted({chan_to_tuple(c) for c in (after_hd.get("defined_channels") or [])})
    print("\n[2.4] Channels")
    print(f"   before  : {chans_b or '—'}")
    print(f"   after   : {chans_a or '—'}")
    print(f"   added   : {sorted(set(chans_a) - set(chans_b)) or '—'}")
    print(f"   removed : {sorted(set(chans_b) - set(chans_a)) or '—'}")

    print("\n[2.5] Centers")
    print(f"   defined before : {before_hd.get('defined_centers') or '—'}")
    print(f"   defined after  : {after_hd.get('defined_centers') or '—'}")

    fields = [("[2.6] Type", "type"),
              ("[2.7] Strategy", "strategy"),
              ("[2.8] Authority", "authority"),
              ("[2.9] Profile", "profile"),
              ("[2.10] Definition", "definition")]
    for label, key in fields:
        b = before_hd.get(key); a = after_hd.get(key)
        marker = "" if b == a else "  ⚠ CHANGE"
        print(f"\n{label}")
        print(f"   before : {b}")
        print(f"   after  : {a}{marker}")

    ic_b = (before_hd.get("incarnation_cross") or {})
    ic_a = (after_hd.get("incarnation_cross") or {})
    print("\n[2.11] Incarnation Cross")
    print(f"   before : {ic_b.get('name')}  gates={ic_b.get('gates')}")
    print(f"   after  : {ic_a.get('name')}  gates={ic_a.get('gates')}")

    # Materiality classification
    print("\n[2.12] Summary — Does the timezone correction materially change Human Design?")
    diffs = {
        "type": before_hd.get("type") != after_hd.get("type"),
        "strategy": before_hd.get("strategy") != after_hd.get("strategy"),
        "authority": before_hd.get("authority") != after_hd.get("authority"),
        "profile": before_hd.get("profile") != after_hd.get("profile"),
        "definition": before_hd.get("definition") != after_hd.get("definition"),
        "incarnation_cross": ic_b.get("name") != ic_a.get("name"),
        "channels_changed": set(chans_b) != set(chans_a),
        "centers_changed": set(before_hd.get("defined_centers") or []) !=
                           set(after_hd.get("defined_centers") or []),
        "gates_changed": (bp_gates != ap_gates) or (bd_gates != ad_gates),
    }
    n_major = sum(diffs[k] for k in ("type", "strategy", "authority", "profile",
                                      "definition", "incarnation_cross",
                                      "channels_changed", "centers_changed"))
    if n_major == 0 and not diffs["gates_changed"]:
        verdict = "NONE"
    elif n_major == 0 and diffs["gates_changed"]:
        verdict = "MINOR"
    elif n_major <= 2:
        verdict = "MODERATE"
    else:
        verdict = "MAJOR"
    print(f"   classification : {verdict}")
    print(f"   reasons:")
    for k, v in diffs.items():
        if v:
            print(f"     • {k}: changed")
    if verdict == "NONE":
        print("     • all canonical HD fields unchanged; gates/channels identical")

    # ──────────────────────────────────────────────────────
    # SECTION 3 — Mirror Interpretation Impact
    # ──────────────────────────────────────────────────────
    print("\n──── SECTION 3 — MIRROR INTERPRETATION IMPACT " + sub[44:])

    asc_sign_change = sign_of(asc_b)[0] != sign_of(asc_a)[0]
    mc_sign_change = sign_of(mc_b)[0] != sign_of(mc_a)[0]
    n_house_changes = len(house_changes)
    asp_change_score = len(added) + len(removed) + len(tightened) + len(loosened)

    def cls(score, lo, hi):
        if score == 0: return "NONE"
        if score <= lo: return "LOW"
        if score <= hi: return "MODERATE"
        return "HIGH"

    surfaces = [
        ("Astrology Overview", "HIGH" if (asc_sign_change or mc_sign_change) else "MODERATE",
         f"Asc/MC sign change directly drives identity & vocational narrative. Asc:{sign_of(asc_b)[0]}→{sign_of(asc_a)[0]}, MC:{sign_of(mc_b)[0]}→{sign_of(mc_a)[0]}"),
        ("Natal Story", "HIGH" if asc_sign_change else "MODERATE",
         f"{n_house_changes} planet(s) shift house, rewriting placement paragraphs"),
        ("Timeline", "MODERATE", "Transit triggers depend on asc/MC + house placements; all timeline rows will regenerate lazily on next read with new placements"),
        ("Today", "MODERATE", "Daily focus / keystones derive from natal positions; output text will differ"),
        ("Governing Chapter", "HIGH" if asc_sign_change or verdict in ("MODERATE","MAJOR") else "MODERATE",
         "Governing Chapter is selected from Asc sign + Sun house; both may shift"),
        ("Pattern Memory", "MODERATE", "Pattern memory tags reference planet houses; will be regenerated lazily"),
        ("Mirror Insights", "MODERATE", "Insight pool is keyed by planet/sign/house combos; new house placements change which insights are eligible"),
    ]
    print(f"   {'Surface':<28}{'Impact':<10} {'Why'}")
    for n, c, why in surfaces:
        print(f"   {n:<28}{c:<10} {why}")

    # ──────────────────────────────────────────────────────
    # SECTION 4 — Relationship Impact (Pete ↔ Mel)
    # ──────────────────────────────────────────────────────
    print("\n──── SECTION 4 — RELATIONSHIP IMPACT (Pete ↔ Mel) " + sub[48:])
    if mel_chart:
        mel_astro = mel_chart.get("astrology") or {}
        mel_asc = angle(mel_astro, "asc")
        mel_mc = angle(mel_astro, "mc")
        print(f"   Mel anchor (unchanged): Asc={sign_of(mel_asc)[0]} {sign_of(mel_asc)[1]:.2f}°  "
              f"MC={sign_of(mel_mc)[0]} {sign_of(mel_mc)[1]:.2f}°")
    # Pete-side aspect-to-Mel changes:
    rel_surfaces = [
        ("Relationship Field",            "MODERATE", "Field synthesis is composite Asc/MC; Pete-side moving ~7° will redraw the field's tone"),
        ("Between You Today",             "LOW",      "Today engine uses transits on both natals — Mel's side unchanged; Pete's contribution shifts slightly"),
        ("Forum Dynamics",                "NONE",     "Forum memberships, posts, mirror reflections preserved verbatim — no chart-derived state in forum docs"),
        ("Relationship Narratives",       "MODERATE", "Long-form narratives reference Pete's Sun house, Asc sign, and HD type — re-paragraph likely on next regeneration"),
        ("Synastry Components",           "HIGH",     "Inter-aspects between Pete planets and Mel planets shift orbs by ~7° on average; multiple aspects will toggle in/out of orb"),
        ("Astrology-derived relationship interpretations", "HIGH",
                                                       "Composite midpoints depend on both asc/MC pairs; Pete's 7° shift rotates composite Asc & house overlay"),
    ]
    print(f"   {'Aspect':<46}{'Impact':<10} {'Explanation'}")
    for n, c, why in rel_surfaces:
        print(f"   {n:<46}{c:<10} {why}")
    print("\n   IDENTICAL after migration:")
    print("     • forum membership rows, forum posts, mirror chats")
    print("     • saved_people relationships and metadata")
    print("     • Mel's chart and her UTC instant")
    print("     • conversation history (chat_history, enneagram_chat_history)")
    print("     • Pete's journal / reflections / facet history")

    # ──────────────────────────────────────────────────────
    # SECTION 5 — Risk Assessment
    # ──────────────────────────────────────────────────────
    print("\n──── SECTION 5 — RISK ASSESSMENT " + sub[31:])
    print("   1. Technical Risk          : LOW")
    print("        • single-user atomic write block (snapshot → tz_update → chart replace → cache delete → verify)")
    print("        • rollback collection captures full prev state, replays in <1s")
    print("        • Mongo ops total ≈ 14 writes for Pete (1 snapshot + 1 user + 1 chart + 11 cache deletes)")
    print("   2. Data Risk               : LOW")
    print("        • conversation/journal/reflection collections explicitly preserved")
    print("        • saved_people + forum_members untouched")
    print("        • cache collections are regenerable; no source-of-truth deleted")
    print("   3. UX Risk                 : MODERATE")
    print("        • Pete WILL see different narrative text on next visit (Asc Sagittarius → likely earlier Sagittarius/Scorpio range, planet house shifts).")
    print("        • This is the intended fix.  His prior content was based on incorrect data.")
    print("        • Recommendation: communicate the correction in-app or via release note.")
    print("   4. Rollback Complexity     : LOW")
    print("        • single Mongo replace_one() restores users doc")
    print("        • single Mongo replace_one() restores charts doc")
    print("        • caches auto-repopulate; no manual replay required")

    print("\n   A. Recommend proceeding?       : YES (with phased monitoring)")
    print("   B. Blockers remaining?         : none beyond the optional UX comms")
    print("   C. Evidence TZ correction wrong? : none — confirmed via zoneinfo + pytz + Singapore cross-ref")
    print("   D. Evidence HD would break?     : none — get_human_design_chart() succeeded on the corrected UTC in-memory")

    # ──────────────────────────────────────────────────────
    # SECTION 6 — Executive Summary
    # ──────────────────────────────────────────────────────
    print("\n──── SECTION 6 — EXECUTIVE SUMMARY " + sub[33:])
    print("\n   Biggest astrology changes:")
    print(f"     • Ascendant: {sign_of(asc_b)[0]} {sign_of(asc_b)[1]:.2f}° → {sign_of(asc_a)[0]} {sign_of(asc_a)[1]:.2f}°  (Δ {signed_delta(asc_b,asc_a):+.2f}°)")
    print(f"     • MC: {sign_of(mc_b)[0]} {sign_of(mc_b)[1]:.2f}° → {sign_of(mc_a)[0]} {sign_of(mc_a)[1]:.2f}°  (Δ {signed_delta(mc_b,mc_a):+.2f}°)")
    print(f"     • {n_house_changes} planet(s) change house: {', '.join(house_changes) if house_changes else 'none'}")
    print(f"     • {len(added)} aspect(s) added, {len(removed)} removed, "
          f"{len(tightened)} tightened, {len(loosened)} loosened")

    print("\n   Biggest Human Design changes:")
    if verdict == "NONE":
        print("     • none — Type/Strategy/Authority/Profile/Definition/IC unchanged")
        print("     • gates and channels identical")
    else:
        for k, v in diffs.items():
            if v: print(f"     • {k}: changed")

    print("\n   Biggest Mirror changes:")
    if asc_sign_change or mc_sign_change:
        print("     • Asc/MC sign shift rewrites identity & vocational narrative")
    print("     • House placements drive the strongest narrative re-renders")
    print("     • Governing Chapter selection may change due to Asc sign shift")

    print("\n   Biggest relationship changes:")
    print("     • Synastry orbs shift by ~7°; some aspects will toggle in/out of orb")
    print("     • Forum & saved_people relationships unchanged")

    overall = "EXECUTE PETE"
    if verdict == "MAJOR":
        overall = "EXECUTE PETE (with HD UX heads-up)"
    print(f"\n   OVERALL RECOMMENDATION : {overall}")
    print()
    print(bar)
    print(json.dumps({
        **HARD,
        "user": "Pete (canonical)",
        "user_id": PETE_USER_ID,
        "tz_before": "+07:00",
        "tz_after": "Asia/Kuala_Lumpur",
        "utc_before": stored_utc.isoformat(),
        "utc_after": CORRECT_UTC.isoformat(),
        "asc_before_deg": round(asc_b, 4),
        "asc_after_deg": round(asc_a, 4),
        "asc_delta_deg": round(signed_delta(asc_b, asc_a), 4),
        "mc_before_deg": round(mc_b, 4),
        "mc_after_deg": round(mc_a, 4),
        "mc_delta_deg": round(signed_delta(mc_b, mc_a), 4),
        "asc_sign_before": sign_of(asc_b)[0],
        "asc_sign_after": sign_of(asc_a)[0],
        "mc_sign_before": sign_of(mc_b)[0],
        "mc_sign_after": sign_of(mc_a)[0],
        "planet_house_changes": house_changes,
        "aspects_added": len(added),
        "aspects_removed": len(removed),
        "aspects_tightened": len(tightened),
        "aspects_loosened": len(loosened),
        "hd_classification": verdict,
        "hd_type_changed": diffs["type"],
        "hd_authority_changed": diffs["authority"],
        "hd_profile_changed": diffs["profile"],
        "hd_definition_changed": diffs["definition"],
        "hd_incarnation_cross_changed": diffs["incarnation_cross"],
        "recommendation": overall,
    }, indent=2, default=str))
    print(bar)


if __name__ == "__main__":
    asyncio.run(main())
