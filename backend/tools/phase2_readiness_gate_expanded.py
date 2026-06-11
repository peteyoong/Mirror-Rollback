"""
Phase 2 Readiness Gate — EXPANDED Audit (READ-ONLY).

Extends phase2_readiness_gate.py with:
  • Real-user vs test/demo classification
  • RECOMPUTE_REQUIRED cohort breakdown
  • Real-user impact table (UTC Δ, Asc Δ, MC Δ)
  • Full MISMATCH inventory
  • Production-risk assessment
  • Final GO / CONDITIONAL GO / NO-GO with blockers

No writes occur. No migrations. No cache invalidations.
Pure Mongo reads + in-memory chart recompute.
"""
from __future__ import annotations

import os, sys, re, asyncio, json
from datetime import datetime, timedelta, timezone as dt_tz
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytz
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from services.timezone_resolver import resolve_iana_timezone
from calculations.astrology import get_full_natal_chart

load_dotenv()
db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ.get("DB_NAME", "test_database")]

MATCH_TOL_DEG = 0.5
UTC_TOL_MIN = 1

# ------------------------------------------------------------------
# Test / Demo classifier
# ------------------------------------------------------------------
# Substring tokens (case-insensitive, NO word boundary so they catch
# camelCase names like "ScrollTest", "ModalTest2", "HDModalTest", etc.)
_TEST_NAME_TOKENS = [
    "test", "tester", "e2e", " qa ", "qauser", "demo", "sample",
    "debug", "playwright", "automation", "dummy", "fixture",
    "seed", "mock", "verifier", "verify", "scroll", "modal",
    "polish", "expand", "send", "lens ", "lensui", "lenstest",
    "session", "event", "chat ", "chattest", "evidence",
    "persist", "reopen", "close ", "closetest", "mirror view",
    "mirrorview", "transparency", "deep dive", "deepdive",
    "hd modal", "hdmodal", "ship gate", "shipgate", "numerology gate",
    "memory", "timeline", "button", "refresh", "reflect",
    "ui test", "uitest", "ui ", "num test", "numtest",
    "final test", "finaltest", "full test", "fulltest",
    "foo", "bar", "baz",
]
_TEST_EMAIL_PATTERNS = [
    r"\+test", r"\+qa", r"\+demo", r"\+e2e",
    r"@example\.", r"@test\.", r"@mailinator", r"@yopmail",
    r"\.test@", r"\.qa@", r"\.demo@",
    r"^test", r"^qa", r"^demo", r"^debug",
    r"^automation", r"^playwright",
]
_KNOWN_REAL_EMAILS = {
    "pete@pulsifi.me",
    "melissa.mars@gmail.com",
}
# Names that on their own (when there are multiple copies in the DB)
# strongly suggest seed/demo data.
_AMBIGUOUS_DEMO_NAMES = {
    "luna", "verifier", "tester", "tester2", "pat", "peteteat",
}

_test_email_re = re.compile("|".join(_TEST_EMAIL_PATTERNS), re.IGNORECASE)


def _contains_test_token(name_lower: str) -> bool:
    for tok in _TEST_NAME_TOKENS:
        if tok in name_lower:
            return True
    return False


def classify_account(name: Optional[str], email: Optional[str]) -> str:
    e = (email or "").strip().lower()
    n = (name or "").strip()
    n_low = n.lower()
    if e and e in _KNOWN_REAL_EMAILS:
        return "REAL"
    if not n and not e:
        return "UNKNOWN"
    if n_low and _contains_test_token(n_low):
        return "TEST"
    if e and _test_email_re.search(e):
        return "TEST"
    if n_low in _AMBIGUOUS_DEMO_NAMES:
        return "TEST"
    # Single-word lowercase tokens with no email are almost always seed accounts
    if n and " " not in n and not e and len(n) <= 12:
        return "TEST"
    # Looks like a real human name (must contain a space or be a recognizable
    # human name with an email).
    if e and "@" in e and re.search(r"[A-Za-z]{2,}", n):
        return "REAL"
    if " " in n and re.search(r"[A-Za-z]{2,}", n):
        return "REAL"
    return "UNKNOWN"


# ------------------------------------------------------------------
# Helpers (copied verbatim from phase2_readiness_gate.py)
# ------------------------------------------------------------------
def _parse_local(birth_date, birth_time):
    if not birth_date or not birth_time:
        return None
    if isinstance(birth_date, datetime):
        d = birth_date
    else:
        s = str(birth_date).split(" ")[0].split("T")[0]
        try:
            d = datetime.strptime(s, "%Y-%m-%d")
        except ValueError:
            return None
    bt = str(birth_time).strip().lower()
    is_pm = "pm" in bt
    is_am = "am" in bt
    t = bt.replace("am", "").replace("pm", "").strip().split(":")
    try:
        hh = int(t[0])
        mm = int(t[1]) if len(t) > 1 else 0
    except (ValueError, IndexError):
        return None
    if is_pm and hh < 12:
        hh += 12
    if is_am and hh == 12:
        hh = 0
    if not (0 <= hh < 24 and 0 <= mm < 60):
        return None
    return datetime(d.year, d.month, d.day, hh, mm)


def _to_utc(local_dt, tz_str):
    if not local_dt or not tz_str:
        return None
    s = str(tz_str).strip()
    try:
        if s.startswith(("+", "-")):
            sign = 1 if s[0] == "+" else -1
            hm = s[1:].split(":")
            off = sign * (int(hm[0]) * 60 + (int(hm[1]) if len(hm) > 1 else 0))
            return (local_dt - timedelta(minutes=off)).replace(tzinfo=dt_tz.utc)
        if s in ("UTC", "GMT", "Z"):
            return local_dt.replace(tzinfo=dt_tz.utc)
        return pytz.timezone(s).localize(local_dt, is_dst=None).astimezone(dt_tz.utc)
    except Exception:
        try:
            return pytz.timezone(s).localize(local_dt, is_dst=True).astimezone(dt_tz.utc)
        except Exception:
            return None


def _ang_delta(a, b):
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def _stored_asc_mc(chart):
    a = (chart.get("astrology") or {}) if chart else {}
    ang = a.get("angles") or {}
    asc = (ang.get("asc") or {}).get("longitude") or (ang.get("asc") or {}).get("tropical_longitude")
    mc = (ang.get("mc") or {}).get("longitude") or (ang.get("mc") or {}).get("tropical_longitude")
    return (float(asc) if asc is not None else None,
            float(mc) if mc is not None else None)


async def main():
    rows: List[Dict[str, Any]] = []
    cursor = db.users.find({})
    async for u in cursor:
        uid = str(u["_id"])
        bl = u.get("birth_location") or {}
        lat = bl.get("latitude")
        lon = bl.get("longitude")
        stored_tz = u.get("timezone")
        bdate = u.get("birth_date")
        btime = u.get("birth_time")
        chart = await db.charts.find_one({"user_id": uid})

        row: Dict[str, Any] = {
            "user_id": uid,
            "name": u.get("name"),
            "email": u.get("email"),
            "account_class": classify_account(u.get("name"), u.get("email")),
            "stored_tz": stored_tz,
            "lat": lat,
            "lon": lon,
            "city": bl.get("city"),
            "country": bl.get("country"),
        }

        # ---- Phase 1.8 classification ----
        local_dt = _parse_local(bdate, btime)
        if lat is None or lon is None:
            row["phase18"] = "UNKNOWN"
            row["p18_reason"] = "no_coords"
        elif not stored_tz:
            row["phase18"] = "UNKNOWN"
            row["p18_reason"] = "no_stored_tz"
        elif not local_dt:
            row["phase18"] = "UNKNOWN"
            row["p18_reason"] = "no_local_dt"
        else:
            try:
                iana = resolve_iana_timezone(float(lat), float(lon))
            except Exception:
                iana = None
            if not iana:
                row["phase18"] = "UNKNOWN"
                row["p18_reason"] = "resolver_failed"
            else:
                stored_utc = _to_utc(local_dt, str(stored_tz))
                corrected_utc = _to_utc(local_dt, iana)
                if not stored_utc or not corrected_utc:
                    row["phase18"] = "UNKNOWN"
                    row["p18_reason"] = "utc_conversion_failed"
                else:
                    dmin = (corrected_utc - stored_utc).total_seconds() / 60.0
                    row["resolved_iana"] = iana
                    row["utc_delta_min"] = round(dmin, 2)
                    if str(stored_tz) == iana and abs(dmin) <= UTC_TOL_MIN:
                        row["phase18"] = "SAFE"
                    elif abs(dmin) <= UTC_TOL_MIN:
                        row["phase18"] = "FORMAT_ONLY"
                    else:
                        row["phase18"] = "RECOMPUTE_REQUIRED"

        # ---- Phase 1.9 consistency ----
        if not chart:
            row["phase19"] = "UNKNOWN"
            row["p19_reason"] = "no_stored_chart"
        else:
            stored_asc, stored_mc = _stored_asc_mc(chart)
            md = ((chart.get("astrology") or {}).get("metadata")) or {}
            row["engine_version"] = md.get("astrology_engine_version")
            row["computation_version"] = md.get("computation_version")
            row["debug_stamp_migration"] = (chart.get("debug_stamp") or {}).get("migration")
            row["forensic_variant_b"] = bool(chart.get("forensic_variant_b"))
            row["stored_asc"] = stored_asc
            row["stored_mc"] = stored_mc
            if stored_asc is None or stored_mc is None:
                row["phase19"] = "UNKNOWN"
                row["p19_reason"] = "no_stored_asc_mc"
            elif row.get("phase18") == "UNKNOWN":
                row["phase19"] = "UNKNOWN"
                row["p19_reason"] = "phase18_unknown"
            else:
                stored_utc_for_recompute = _to_utc(local_dt, str(stored_tz))
                try:
                    ch = get_full_natal_chart(stored_utc_for_recompute, float(lat), float(lon))
                    ang = ch.get("angles") or {}
                    rasc = (ang.get("asc") or {}).get("longitude") or (ang.get("asc") or {}).get("tropical_longitude")
                    rmc = (ang.get("mc") or {}).get("longitude") or (ang.get("mc") or {}).get("tropical_longitude")
                    if rasc is None or rmc is None:
                        row["phase19"] = "UNKNOWN"
                        row["p19_reason"] = "recompute_missing_angles"
                    else:
                        da = _ang_delta(stored_asc, float(rasc))
                        dm = _ang_delta(stored_mc, float(rmc))
                        row["recomp_asc"] = round(float(rasc), 4)
                        row["recomp_mc"] = round(float(rmc), 4)
                        row["asc_delta_deg"] = round(da, 4)
                        row["mc_delta_deg"] = round(dm, 4)
                        row["phase19"] = ("MATCH" if (da <= MATCH_TOL_DEG and dm <= MATCH_TOL_DEG) else "MISMATCH")
                except Exception as e:
                    row["phase19"] = "UNKNOWN"
                    row["p19_reason"] = f"recompute_error:{type(e).__name__}"

        rows.append(row)

    # ==================================================
    # 1. Consistency matrix
    # ==================================================
    p18_buckets = ["SAFE", "FORMAT_ONLY", "RECOMPUTE_REQUIRED", "UNKNOWN"]
    p19_buckets = ["MATCH", "MISMATCH", "UNKNOWN"]
    mat = {a: {b: 0 for b in p19_buckets} for a in p18_buckets}
    for r in rows:
        a = r.get("phase18", "UNKNOWN")
        b = r.get("phase19", "UNKNOWN")
        if a not in mat:
            a = "UNKNOWN"
        if b not in mat[a]:
            b = "UNKNOWN"
        mat[a][b] += 1

    total = len(rows)
    bar = "=" * 84

    print(bar)
    print("PHASE 2 READINESS GATE — EXPANDED AUDIT  (READ-ONLY)")
    print(bar)
    print(f"Database         : {os.environ.get('DB_NAME', 'test_database')}")
    print(f"Total users      : {total}")
    print(f"Writes performed : 0")
    print(f"Charts updated   : 0")
    print(f"Migrations fired : false")
    print()

    print("─── 1. Full Consistency Matrix ───────────────────────────────────────────────")
    print(f"{'Classification':<24}{'MATCH':>10}{'MISMATCH':>12}{'UNKNOWN':>10}{'Total':>10}")
    for a in p18_buckets:
        ttl = sum(mat[a].values())
        print(f"{a:<24}{mat[a]['MATCH']:>10}{mat[a]['MISMATCH']:>12}{mat[a]['UNKNOWN']:>10}{ttl:>10}")
    grand_match = sum(mat[a]['MATCH'] for a in p18_buckets)
    grand_mis = sum(mat[a]['MISMATCH'] for a in p18_buckets)
    grand_unk = sum(mat[a]['UNKNOWN'] for a in p18_buckets)
    print(f"{'TOTAL':<24}{grand_match:>10}{grand_mis:>12}{grand_unk:>10}{total:>10}")
    print()

    # ==================================================
    # 2. Real vs Test split
    # ==================================================
    real = [r for r in rows if r["account_class"] == "REAL"]
    test = [r for r in rows if r["account_class"] == "TEST"]
    unk = [r for r in rows if r["account_class"] == "UNKNOWN"]

    print("─── 2. Real Users vs Test/Demo Users ─────────────────────────────────────────")
    print(f"{'Cohort':<24}{'Count':>10}")
    print(f"{'REAL':<24}{len(real):>10}")
    print(f"{'TEST/DEMO':<24}{len(test):>10}")
    print(f"{'UNKNOWN':<24}{len(unk):>10}")
    print(f"{'TOTAL':<24}{total:>10}")
    print()

    # ==================================================
    # 3. RECOMPUTE_REQUIRED breakdown
    # ==================================================
    rec = [r for r in rows if r.get("phase18") == "RECOMPUTE_REQUIRED"]
    rec_real = [r for r in rec if r["account_class"] == "REAL"]
    rec_test = [r for r in rec if r["account_class"] == "TEST"]
    rec_unk = [r for r in rec if r["account_class"] == "UNKNOWN"]

    print("─── 3. RECOMPUTE_REQUIRED Cohort Breakdown ───────────────────────────────────")
    print(f"{'Cohort':<24}{'Count':>10}")
    print(f"{'Real users':<24}{len(rec_real):>10}")
    print(f"{'Test/demo users':<24}{len(rec_test):>10}")
    print(f"{'Unknown':<24}{len(rec_unk):>10}")
    print(f"{'Total':<24}{len(rec):>10}")
    print()

    # ==================================================
    # 4. Real-user impact table
    # ==================================================
    print("─── 4. Real-User Impact Table (RECOMPUTE_REQUIRED ∧ account=REAL) ────────────")
    if not rec_real:
        print("   (no real users in RECOMPUTE_REQUIRED bucket)")
    else:
        print(f"{'user_id':<26}{'name':<22}{'stored_tz':<14}{'resolved_tz':<22}"
              f"{'UTCΔ(min)':>11}{'AscΔ(deg)':>11}{'MCΔ(deg)':>10}  consistency")
        for r in sorted(rec_real, key=lambda x: -abs(x.get("utc_delta_min") or 0)):
            print(f"{r['user_id']:<26}"
                  f"{str(r.get('name') or '')[:20]:<22}"
                  f"{str(r.get('stored_tz') or '')[:12]:<14}"
                  f"{str(r.get('resolved_iana') or '')[:20]:<22}"
                  f"{r.get('utc_delta_min', '?'):>11}"
                  f"{r.get('asc_delta_deg', '—'):>11}"
                  f"{r.get('mc_delta_deg', '—'):>10}  "
                  f"{r.get('phase19', '?')}")
    print()

    # ==================================================
    # 5. MISMATCH inventory
    # ==================================================
    mismatches = [r for r in rows if r.get("phase19") == "MISMATCH"]
    mis_real = [r for r in mismatches if r["account_class"] == "REAL"]
    mis_test = [r for r in mismatches if r["account_class"] == "TEST"]
    mis_unk = [r for r in mismatches if r["account_class"] == "UNKNOWN"]

    print("─── 5. MISMATCH Cohort (Silent Corruption Audit) ─────────────────────────────")
    print(f"Total MISMATCH users     : {len(mismatches)}")
    print(f"   ↳ REAL              : {len(mis_real)}")
    print(f"   ↳ TEST/DEMO         : {len(mis_test)}")
    print(f"   ↳ UNKNOWN           : {len(mis_unk)}")
    print()
    if mismatches:
        print(f"{'user_id':<26}{'name':<22}{'class':<8}{'phase18':<22} reason")
        for r in sorted(mismatches, key=lambda x: -(x.get("asc_delta_deg") or 0)):
            p18 = r.get("phase18", "?")
            if p18 == "RECOMPUTE_REQUIRED":
                reason = "timezone corruption — recompute will fix"
            elif p18 in ("SAFE", "FORMAT_ONLY"):
                reason = "chart drift outside Phase 2's write set (engine/stale)"
            elif p18 == "UNKNOWN":
                reason = "input data missing — manual triage"
            else:
                reason = "unclassified"
            print(f"{r['user_id']:<26}"
                  f"{str(r.get('name') or '')[:20]:<22}"
                  f"{r['account_class']:<8}"
                  f"{p18:<22} {reason}")
    print()

    # ==================================================
    # 6. Production-risk assessment
    # ==================================================
    real_recompute_material = [r for r in rec_real if (abs(r.get("utc_delta_min") or 0) > UTC_TOL_MIN)]
    test_recompute_material = [r for r in rec_test if (abs(r.get("utc_delta_min") or 0) > UTC_TOL_MIN)]
    real_silent_skip = [r for r in mis_real if r.get("phase18") in ("SAFE", "FORMAT_ONLY")]
    hidden_corruption = [
        r for r in rows
        if r.get("phase19") == "MISMATCH" and r.get("phase18") in ("SAFE", "FORMAT_ONLY")
    ]

    print("─── 6. Production-Risk Assessment ─────────────────────────────────────────────")
    print(f"A. Real users that would receive a materially different chart   : {len(real_recompute_material)}")
    print(f"B. Test/demo users that would receive a materially different    : {len(test_recompute_material)}")
    print(f"C. Real users skipped due to chart/input drift (silent-skip)    : {len(real_silent_skip)}")
    print(f"D. Hidden corruption beyond timezone (drift in SAFE/FORMAT_ONLY): {len(hidden_corruption)}")
    if real_silent_skip:
        print()
        print("   Silent-skip real users (would be missed by Phase 2 write set):")
        for r in real_silent_skip:
            print(f"     • {r['user_id']}  {r.get('name')}  ({r.get('email')})  phase18={r.get('phase18')}  ascΔ={r.get('asc_delta_deg')}")
    print()

    # ==================================================
    # 7. Final recommendation
    # ==================================================
    print("─── 7. Final Recommendation ──────────────────────────────────────────────────")
    blockers: List[str] = []
    soft: List[str] = []

    if len(real_silent_skip) > 0:
        blockers.append(
            f"{len(real_silent_skip)} real user(s) sit in SAFE/FORMAT_ONLY but their stored "
            "chart does not reproduce from stored inputs — Phase 2 would skip them and leave "
            "the corruption in place."
        )
    if len(hidden_corruption) > 0 and len(real_silent_skip) == 0:
        soft.append(
            f"{len(hidden_corruption)} test/demo account(s) show non-timezone chart drift; "
            "harmless to production but suggests at least one historical engine-version "
            "discontinuity exists in the chart store."
        )
    rec_unknown = [r for r in rec if r.get("phase19") == "UNKNOWN"]
    if rec_unknown:
        soft.append(
            f"{len(rec_unknown)} RECOMPUTE_REQUIRED user(s) could not be cross-verified "
            "(missing chart, missing angles, or recompute error). Acceptable to migrate "
            "with caution but worth logging for QA after Phase 2."
        )

    if not blockers and not soft:
        verdict = "GO"
    elif blockers:
        verdict = "NO GO"
    else:
        verdict = "CONDITIONAL GO"

    print(f"VERDICT: {verdict}")
    if blockers:
        print()
        print("BLOCKERS (must be resolved before Phase 2 writes):")
        for i, b in enumerate(blockers, 1):
            print(f"   {i}. {b}")
    if soft:
        print()
        print("SOFT CAVEATS (acceptable with monitoring):")
        for i, s in enumerate(soft, 1):
            print(f"   {i}. {s}")
    print()
    print(bar)
    print(json.dumps({
        "write_count": 0,
        "charts_updated": 0,
        "migrations_triggered": False,
        "verdict": verdict,
        "total_users": total,
        "real_users": len(real),
        "test_users": len(test),
        "unknown_users": len(unk),
        "recompute_required_real": len(rec_real),
        "recompute_required_test": len(rec_test),
        "recompute_required_unknown": len(rec_unk),
        "mismatch_total": len(mismatches),
        "mismatch_real": len(mis_real),
        "mismatch_test": len(mis_test),
        "real_silent_skip": len(real_silent_skip),
        "hidden_corruption_count": len(hidden_corruption),
    }, indent=2))
    print(bar)


if __name__ == "__main__":
    asyncio.run(main())
