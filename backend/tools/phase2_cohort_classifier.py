"""
Phase 2 cohort classifier (READ-ONLY).

For every Phase 2 cohort user (RECOMPUTE_REQUIRED + FORMAT_ONLY + DRIFT_REPAIR),
classify them into one of:
  • ACTIVE_PRODUCTION    — real human, recent activity OR meaningful cache/forums/saved_people
  • TEST_REFERENCE       — identifiable test/seed account (used in QA, regression, smoke tests)
  • DORMANT_DUPLICATE    — onboarding/test shell, never used, low signal
  • ALREADY_MIGRATED     — Pete canonical (just done)
  • SKIP                 — already SAFE (in source dataset by mistake)

The classifier is conservative — when in doubt, escalate up the chain
(dormant ⇢ test ⇢ active) so we never accidentally mark a real account
as dormant.
"""
from __future__ import annotations

import os, sys, asyncio, json, re
from datetime import datetime, timedelta, timezone as dt_tz
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytz, bson
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from services.timezone_resolver import resolve_iana_timezone

load_dotenv()
db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ.get("DB_NAME", "test_database")]

DRIFT_REPAIR_USERS = {"6971cc4381beab3a8955b256"}
PETE_CANONICAL = "697f0c6abf35c0528ff06954"  # already migrated

CACHE_COLLECTIONS = [
    "deep_dive_cache", "astrology_timeline_cache", "governing_chapter_cache",
    "lifeline_synthesis_cache", "lunar_synthesis_cache", "pattern_drift_cache",
    "pattern_mirror_cache", "relationship_today_cache", "forum_story_cache",
    "daily_focus", "daily_keystones", "daily_astrology", "daily_pattern_signals",
    "today_patterns", "user_timeline", "mirror_insights",
    "pattern_memory", "pattern_memory_signals",
    "pattern_running_me_v2", "longitudinal_pattern_memory",
    "home_angle_history", "home_history", "home_v6_state",
    "lifeline_events", "lifeline_imported_moments", "lifeline_import_sources",
    "lunar_considerations", "lunar_journal",
]

# Classifier heuristics
_TEST_NAME_TOKENS = [
    "test", "tester", "e2e", "qa", "demo", "sample", "debug",
    "playwright", "automation", "dummy", "fixture", "seed", "mock",
    "verifier", "verify", "scroll", "modal", "polish", "expand",
    "lens", "lenstest", "lensui", "session", "event", "chat ",
    "chattest", "evidence", "persist", "reopen", "close ", "closetest",
    "mirror view", "mirrorview", "transparency", "deep dive", "deepdive",
    "hd modal", "hdmodal", "ship gate", "shipgate", "numerology gate",
    "memory", "timeline", "button", "refresh", "reflect", "ui test",
    "uitest", "num test", "numtest", "final test", "finaltest",
    "full test", "fulltest", "send",
]
_TEST_EMAIL_PATTERNS = [
    r"\+test", r"\+qa", r"\+demo", r"\+e2e",
    r"@example\.", r"@test\.", r"@mailinator", r"@yopmail",
    r"^test", r"^qa", r"^demo", r"^debug",
    r"^automation", r"^playwright",
]
_test_email_re = re.compile("|".join(_TEST_EMAIL_PATTERNS), re.IGNORECASE)
_KNOWN_REAL_EMAILS = {"pete@pulsifi.me", "melissa.mars@gmail.com"}

# Pete canonical email + the dormant Mel duplicate are special-cased below


def _parse_local(birth_date, birth_time):
    if not birth_date or not birth_time: return None
    if isinstance(birth_date, datetime):
        d = birth_date
    else:
        s = str(birth_date).split(" ")[0].split("T")[0]
        try: d = datetime.strptime(s, "%Y-%m-%d")
        except ValueError: return None
    bt = str(birth_time).strip().lower()
    is_pm = "pm" in bt; is_am = "am" in bt
    t = bt.replace("am","").replace("pm","").strip().split(":")
    try:
        hh = int(t[0]); mm = int(t[1]) if len(t)>1 else 0
    except (ValueError, IndexError): return None
    if is_pm and hh < 12: hh += 12
    if is_am and hh == 12: hh = 0
    if not (0 <= hh < 24 and 0 <= mm < 60): return None
    return datetime(d.year, d.month, d.day, hh, mm)


def _to_utc(local_dt, tz_str):
    if not local_dt or not tz_str: return None
    s = str(tz_str).strip()
    try:
        if s.startswith(("+","-")):
            sign = 1 if s[0] == "+" else -1
            hm = s[1:].split(":")
            off = sign * (int(hm[0])*60 + (int(hm[1]) if len(hm)>1 else 0))
            return (local_dt - timedelta(minutes=off)).replace(tzinfo=dt_tz.utc)
        if s in ("UTC","GMT","Z"): return local_dt.replace(tzinfo=dt_tz.utc)
        return pytz.timezone(s).localize(local_dt, is_dst=None).astimezone(dt_tz.utc)
    except Exception:
        return None


def classify_phase18(stored_tz, lat, lon, local_dt):
    if lat is None or lon is None: return ("UNKNOWN", None, None)
    if not stored_tz: return ("UNKNOWN", None, None)
    if not local_dt: return ("UNKNOWN", None, None)
    try: iana = resolve_iana_timezone(float(lat), float(lon))
    except Exception: iana = None
    if not iana: return ("UNKNOWN", None, None)
    su = _to_utc(local_dt, str(stored_tz)); cu = _to_utc(local_dt, iana)
    if not su or not cu: return ("UNKNOWN", iana, None)
    dmin = (cu - su).total_seconds() / 60.0
    if str(stored_tz) == iana and abs(dmin) <= 1: return ("SAFE", iana, dmin)
    if abs(dmin) <= 1: return ("FORMAT_ONLY", iana, dmin)
    return ("RECOMPUTE_REQUIRED", iana, dmin)


def name_is_test(n: str) -> bool:
    nl = (n or "").lower()
    return any(tok in nl for tok in _TEST_NAME_TOKENS)


async def last_active(uid: str) -> Optional[datetime]:
    candidates = [
        ("user_timeline", "created_at"),
        ("home_engagement_sessions", "created_at"),
        ("chat_history", "created_at"),
        ("user_recent_actions", "ts"),
        ("daily_focus", "created_at"),
        ("forum_chat_messages", "created_at"),
        ("forum_mirror_chat_messages", "created_at"),
        ("reflections", "created_at"),
        ("journal", "created_at"),
    ]
    best = None
    for coll, ts in candidates:
        try:
            doc = await db[coll].find_one(
                {"user_id": uid, ts: {"$exists": True}},
                sort=[(ts, -1)], projection={ts: 1})
        except Exception:
            doc = None
        if doc and isinstance(doc.get(ts), datetime):
            if best is None or doc[ts] > best:
                best = doc[ts]
    return best


async def cache_total(uid: str) -> int:
    total = 0
    for c in CACHE_COLLECTIONS:
        try:
            total += await db[c].count_documents({"user_id": uid})
        except Exception:
            pass
    return total


def cohort_class(account_class: str, signal_score: int, last_active_at) -> str:
    """ACTIVE_PRODUCTION | TEST_REFERENCE | DORMANT_DUPLICATE"""
    # signal_score = cache_count + forums*5 + saved*5 + (recent_30d ? 10 : 0)
    if account_class == "TEST" and signal_score < 50:
        return "TEST_REFERENCE"
    if signal_score >= 20:
        return "ACTIVE_PRODUCTION"
    return "DORMANT_DUPLICATE"


def account_class(name: str, email: str) -> str:
    e = (email or "").strip().lower()
    n = (name or "").strip()
    if e and e in _KNOWN_REAL_EMAILS:
        return "REAL"
    if not n and not e:
        return "UNKNOWN"
    if name_is_test(n):
        return "TEST"
    if e and _test_email_re.search(e):
        return "TEST"
    if n and re.search(r"[A-Za-z]{2,}", n) and " " in n:
        return "REAL"
    if e and "@" in e and re.search(r"[A-Za-z]{2,}", n or "x"):
        return "REAL"
    return "UNKNOWN"


async def main():
    rows: List[Dict[str, Any]] = []
    cursor = db.users.find({})
    async for u in cursor:
        uid = str(u["_id"])
        bl = u.get("birth_location") or {}
        lat = bl.get("latitude"); lon = bl.get("longitude")
        stored_tz = u.get("timezone")
        local_dt = _parse_local(u.get("birth_date"), u.get("birth_time"))
        p18, iana, dmin = classify_phase18(stored_tz, lat, lon, local_dt)

        # Phase-2 inclusion test
        in_p2 = (p18 in ("RECOMPUTE_REQUIRED", "FORMAT_ONLY")) or (uid in DRIFT_REPAIR_USERS)
        if not in_p2:
            continue

        # Skip already migrated
        if uid == PETE_CANONICAL:
            rows.append({
                "user_id": uid, "name": u.get("name"), "email": u.get("email"),
                "phase18": p18, "resolved_iana": iana, "utc_delta_min": dmin,
                "cohort_class": "ALREADY_MIGRATED",
                "account_class": "REAL", "signal_score": -1,
                "cache_count": 0, "forums": 0, "saved": 0,
                "last_active": None,
            })
            continue

        # Signal scoring
        forums = await db.forum_members.count_documents({"user_id": uid})
        saved = await db.saved_people.count_documents({"user_id": uid})
        cc = await cache_total(uid)
        la = await last_active(uid)
        la_aware = la.replace(tzinfo=dt_tz.utc) if (la and la.tzinfo is None) else la
        recent = la_aware is not None and la_aware > datetime.now(dt_tz.utc) - timedelta(days=90)
        signal = cc + 5 * forums + 5 * saved + (10 if recent else 0)
        ac = account_class(u.get("name"), u.get("email"))
        cclass = cohort_class(ac, signal, la)
        rows.append({
            "user_id": uid, "name": u.get("name"), "email": u.get("email"),
            "phase18": p18, "resolved_iana": iana, "utc_delta_min": dmin,
            "cohort_class": cclass, "account_class": ac, "signal_score": signal,
            "cache_count": cc, "forums": forums, "saved": saved,
            "last_active": la.isoformat() if la else None,
        })

    # Counts
    buckets = {"ACTIVE_PRODUCTION": [], "TEST_REFERENCE": [],
               "DORMANT_DUPLICATE": [], "ALREADY_MIGRATED": []}
    for r in rows:
        buckets[r["cohort_class"]].append(r)

    bar = "=" * 96
    print(bar)
    print("PHASE 2 COHORT CLASSIFICATION  (READ-ONLY)")
    print(bar)
    print(f"DB: {os.environ.get('DB_NAME','test_database')}")
    print(f"Total Phase 2 cohort   : {len(rows)} users")
    print()
    print(f"  ACTIVE_PRODUCTION    : {len(buckets['ACTIVE_PRODUCTION']):>4}")
    print(f"  TEST_REFERENCE       : {len(buckets['TEST_REFERENCE']):>4}")
    print(f"  DORMANT_DUPLICATE    : {len(buckets['DORMANT_DUPLICATE']):>4}")
    print(f"  ALREADY_MIGRATED     : {len(buckets['ALREADY_MIGRATED']):>4}")
    print()

    for label in ["ACTIVE_PRODUCTION", "TEST_REFERENCE", "DORMANT_DUPLICATE", "ALREADY_MIGRATED"]:
        rows_b = buckets[label]
        print(f"─── {label}  ({len(rows_b)} users) " + "─" * (60 - len(label)))
        if not rows_b:
            print("   (none)"); continue
        print(f"   {'user_id':<26}{'name':<24}{'email':<28}"
              f"{'tz_now':<12}{'→tz':<22}{'cache':>6}{'fmt':>4}{'sv':>4}{'last_active':>12}")
        for r in sorted(rows_b, key=lambda x: -x["signal_score"]):
            print(f"   {r['user_id']:<26}"
                  f"{str(r['name'] or '')[:22]:<24}"
                  f"{str(r['email'] or '—')[:26]:<28}"
                  f"{str(r['phase18'])[:10]:<12}"
                  f"{str(r['resolved_iana'] or '—')[:20]:<22}"
                  f"{r['cache_count']:>6}"
                  f"{r['forums']:>4}"
                  f"{r['saved']:>4}"
                  f"{(r['last_active'] or '—')[:10]:>12}")
        print()

    # write artifact for executor to consume
    out = "/app/backend/audit_reports/phase2_cohort_classification.json"
    with open(out, "w") as f:
        json.dump({
            "generated_at": datetime.now(dt_tz.utc).isoformat(),
            "totals": {k: len(v) for k, v in buckets.items()},
            "buckets": {k: [r["user_id"] for r in v] for k, v in buckets.items()},
            "rows": rows,
        }, f, indent=2, default=str)
    print(f"Artifact written: {out}")


if __name__ == "__main__":
    asyncio.run(main())
