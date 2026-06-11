"""
Phase 2 — Final Pre-Execution Verification (READ-ONLY).

Builds the canonical-account map for Pete and Mel before Phase 2 writes.
No mutation, no snapshot, no cache invalidation.
"""
from __future__ import annotations

import os, sys, asyncio, json, re
from datetime import datetime
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()
db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ.get("DB_NAME", "test_database")]

# Cohort-search regex per user request
PETE_RE = re.compile(r"\b(pete|peter|yoong\s+weng\s+hong|yoong)\b", re.IGNORECASE)
MEL_RE = re.compile(r"\b(mel|melissa)\b", re.IGNORECASE)

# Collections to count per user_id when measuring cache footprint
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
# Activity-signal collections used to derive `last_active_at`
ACTIVITY_COLLECTIONS = [
    ("user_timeline", "created_at"),
    ("user_timeline", "ts"),
    ("home_engagement_sessions", "created_at"),
    ("home_engagement_sessions", "started_at"),
    ("chat_history", "created_at"),
    ("user_recent_actions", "ts"),
    ("user_recent_actions", "created_at"),
    ("daily_focus", "created_at"),
    ("daily_keystones", "created_at"),
    ("home_history", "created_at"),
    ("mirror_insights", "created_at"),
    ("forum_chat_messages", "created_at"),
    ("forum_mirror_chat_messages", "created_at"),
    ("forum_reflections", "created_at"),
    ("reflections", "created_at"),
    ("journal", "created_at"),
    ("lunar_journal", "created_at"),
    ("pattern_memory", "created_at"),
]
PER_USER_COLLECTIONS = ["chat_history", "forum_chat_messages",
                        "forum_mirror_chat_messages", "home_engagement_sessions"]


async def _last_active(uid: str) -> Optional[datetime]:
    """Return the latest timestamp we can find for this user across many cols."""
    best: Optional[datetime] = None
    for coll, ts_field in ACTIVITY_COLLECTIONS:
        try:
            doc = await db[coll].find_one(
                {"user_id": uid, ts_field: {"$exists": True}},
                sort=[(ts_field, -1)],
                projection={ts_field: 1},
            )
        except Exception:
            doc = None
        if doc:
            t = doc.get(ts_field)
            if isinstance(t, datetime):
                if best is None or t > best:
                    best = t
    return best


async def _cache_breakdown(uid: str) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for c in CACHE_COLLECTIONS:
        try:
            n = await db[c].count_documents({"user_id": uid})
        except Exception:
            n = 0
        if n:
            out[c] = n
    return out


async def _profile(uid: str, u: Dict[str, Any]) -> Dict[str, Any]:
    chart = await db.charts.find_one({"user_id": uid}, projection={"_id": 1})
    cache = await _cache_breakdown(uid)
    forums = await db.forum_members.count_documents({"user_id": uid})
    saved = await db.saved_people.count_documents({"user_id": uid})
    last_active = await _last_active(uid)
    return {
        "user_id": uid,
        "name": u.get("name"),
        "email": u.get("email"),
        "timezone": u.get("timezone"),
        "created_at": u.get("created_at"),
        "last_active_at": last_active,
        "chart_exists": bool(chart),
        "cache_row_count": sum(cache.values()),
        "cache_breakdown": cache,
        "forum_memberships": forums,
        "saved_people_refs": saved,
    }


async def _gather(regex: re.Pattern) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    cursor = db.users.find({})
    async for u in cursor:
        n = (u.get("name") or "")
        e = (u.get("email") or "")
        if regex.search(n) or regex.search(e):
            out.append(await _profile(str(u["_id"]), u))
    out.sort(key=lambda r: (r.get("last_active_at") or datetime.min), reverse=True)
    return out


def _fmt_ts(t):
    if not t:
        return "—"
    if isinstance(t, datetime):
        return t.strftime("%Y-%m-%d %H:%M")
    return str(t)[:16]


def _print_table(label: str, rows: List[Dict[str, Any]]):
    print(f"\n─── {label}  ({len(rows)} rows) " + "─" * (60 - len(label)))
    if not rows:
        print("   (none)")
        return
    header = (f"{'user_id':<26}{'name':<26}{'email':<24}{'tz':<22}"
              f"{'created':<18}{'last_active':<18}{'chart':>6}{'cache':>8}"
              f"{'forum':>7}{'saved':>7}")
    print(header)
    print("-" * len(header))
    for r in rows:
        print(f"{r['user_id']:<26}"
              f"{(str(r.get('name') or '')[:24]):<26}"
              f"{(str(r.get('email') or '—')[:22]):<24}"
              f"{(str(r.get('timezone') or '—')[:20]):<22}"
              f"{_fmt_ts(r.get('created_at')):<18}"
              f"{_fmt_ts(r.get('last_active_at')):<18}"
              f"{('Y' if r.get('chart_exists') else 'N'):>6}"
              f"{r.get('cache_row_count', 0):>8}"
              f"{r.get('forum_memberships', 0):>7}"
              f"{r.get('saved_people_refs', 0):>7}")


def _canonical(rows: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Canonical = highest signal: chart_exists + most recent activity + most cache."""
    if not rows:
        return None
    def score(r):
        return (
            1 if r.get("chart_exists") else 0,
            r.get("last_active_at") or datetime.min,
            r.get("cache_row_count", 0),
            r.get("forum_memberships", 0),
            r.get("saved_people_refs", 0),
            r.get("created_at") or datetime.min,
        )
    return max(rows, key=score)


async def main():
    bar = "=" * 110
    print(bar)
    print("PHASE 2 — FINAL PRE-EXECUTION VERIFICATION  (READ-ONLY)")
    print(bar)
    print(f"DB: {os.environ.get('DB_NAME','test_database')}")
    print("No writes. No snapshots. No recomputes. No cache invalidations.")

    pete_rows = await _gather(PETE_RE)
    mel_rows = await _gather(MEL_RE)

    _print_table("Pete / Peter / Yoong Weng Hong cohort", pete_rows)
    _print_table("Mel / Melissa cohort", mel_rows)

    # Cohort-membership cross-check vs Phase 2B plan
    cohort_ids_pete = set()
    cohort_ids_mel = set()
    # Re-derive who is in the Phase 2 cohort by classification:
    # RECOMPUTE_REQUIRED, FORMAT_ONLY, or the explicit drift-repair user.
    DRIFT_REPAIR = {"6971cc4381beab3a8955b256"}
    from services.timezone_resolver import resolve_iana_timezone
    import pytz
    from datetime import timedelta, timezone as dt_tz

    def _parse_local(birth_date, birth_time):
        if not birth_date or not birth_time:
            return None
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
            hh = int(t[0]); mm = int(t[1]) if len(t) > 1 else 0
        except (ValueError, IndexError): return None
        if is_pm and hh < 12: hh += 12
        if is_am and hh == 12: hh = 0
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

    async def _in_cohort(uid: str):
        u = await db.users.find_one({"_id": __import__("bson").ObjectId(uid)})
        if not u: return (None, None)
        if uid in DRIFT_REPAIR: return ("DRIFT_REPAIR", None)
        bl = u.get("birth_location") or {}
        lat = bl.get("latitude"); lon = bl.get("longitude")
        stored_tz = u.get("timezone")
        local_dt = _parse_local(u.get("birth_date"), u.get("birth_time"))
        if lat is None or lon is None or not stored_tz or not local_dt:
            return (None, None)
        try: iana = resolve_iana_timezone(float(lat), float(lon))
        except Exception: iana = None
        if not iana: return (None, None)
        su = _to_utc(local_dt, str(stored_tz)); cu = _to_utc(local_dt, iana)
        if not su or not cu: return (None, None)
        dmin = (cu - su).total_seconds() / 60.0
        if str(stored_tz) == iana and abs(dmin) <= 1: return ("SAFE", iana)
        if abs(dmin) <= 1: return ("FORMAT_ONLY", iana)
        return ("RECOMPUTE_REQUIRED", iana)

    print("\n─── Phase 2 cohort membership check ──────────────────────────────────────────────")
    print(f"{'user_id':<26}{'name':<24}{'phase18':<22}{'in_phase2_cohort':<18} target_tz")
    for r in pete_rows + mel_rows:
        cls, iana = await _in_cohort(r["user_id"])
        will_migrate = cls in ("RECOMPUTE_REQUIRED", "FORMAT_ONLY", "DRIFT_REPAIR")
        print(f"{r['user_id']:<26}"
              f"{(str(r.get('name') or '')[:22]):<24}"
              f"{(cls or '—'):<22}"
              f"{('YES' if will_migrate else 'no'):<18} {iana or '—'}")

    # Canonical pick
    pete_canon = _canonical(pete_rows)
    mel_canon  = _canonical(mel_rows)

    print("\n─── Canonical-Account Map ────────────────────────────────────────────────────────")
    if pete_canon:
        print(f"Pete canonical : {pete_canon['user_id']}  ({pete_canon.get('name')!r})")
        print(f"   tz={pete_canon['timezone']}  chart={'Y' if pete_canon['chart_exists'] else 'N'}"
              f"  cache={pete_canon['cache_row_count']}  forums={pete_canon['forum_memberships']}"
              f"  saved={pete_canon['saved_people_refs']}  last_active={_fmt_ts(pete_canon['last_active_at'])}")
        if pete_canon.get("cache_breakdown"):
            print("   cache breakdown:")
            for k,v in sorted(pete_canon["cache_breakdown"].items(), key=lambda kv:-kv[1]):
                print(f"     {k:<32} {v}")
    if mel_canon:
        print(f"\nMel canonical  : {mel_canon['user_id']}  ({mel_canon.get('name')!r})")
        print(f"   tz={mel_canon['timezone']}  chart={'Y' if mel_canon['chart_exists'] else 'N'}"
              f"  cache={mel_canon['cache_row_count']}  forums={mel_canon['forum_memberships']}"
              f"  saved={mel_canon['saved_people_refs']}  last_active={_fmt_ts(mel_canon['last_active_at'])}")
        if mel_canon.get("cache_breakdown"):
            print("   cache breakdown:")
            for k,v in sorted(mel_canon["cache_breakdown"].items(), key=lambda kv:-kv[1]):
                print(f"     {k:<32} {v}")

    print("\n" + bar)
    print(json.dumps({
        "write_count": 0, "charts_updated": 0, "migrations_triggered": False,
        "pete_total": len(pete_rows), "mel_total": len(mel_rows),
        "pete_canonical": pete_canon["user_id"] if pete_canon else None,
        "mel_canonical": mel_canon["user_id"] if mel_canon else None,
    }, indent=2))
    print(bar)


if __name__ == "__main__":
    asyncio.run(main())
