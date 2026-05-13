#!/usr/bin/env python3
"""
Backend test for HD startup migration + Astrology cache contracts (Today V5 + Timeline V1).
Tests:
  1) HD startup migration log (idempotent, non-blocking, failed=0)
  2) GET /api/astrology/today-v5/{user_id} — daily cache + force_refresh
  3) GET /api/astrology/timeline/{user_id} — weekly cache + force_refresh
  4) MongoDB-level verification
"""

import os
import re
import datetime as dt

import requests
from pymongo import MongoClient

BASE_URL = "https://micro-reflect-v2.preview.emergentagent.com"
API = f"{BASE_URL}/api"

PETE = "697f0c6abf35c0528ff06954"
MEL = "697ec826ad4b18f75bf42616"

BACKEND_LOG = "/var/log/supervisor/backend.err.log"


def section(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def report(label, ok, detail=""):
    icon = "PASS" if ok else "FAIL"
    print(f"[{icon}] {label}")
    if detail:
        for line in detail.splitlines():
            print(f"        {line}")
    return ok


def test_hd_migration_log():
    section("1) HD Startup Migration — log block + non-blocking")
    results = []

    try:
        with open(BACKEND_LOG, "r") as f:
            log = f.read()
    except Exception as e:
        results.append(report("Read backend.err.log", False, str(e)))
        return results

    report_idx = log.rfind("HD TYPE MIGRATION REPORT (hd_motor_to_throat_bfs_v1)")
    start_idx = log.rfind("[Migration] Starting background data migrations...")

    results.append(report("HD TYPE MIGRATION REPORT block present", report_idx != -1,
                          f"found at offset {report_idx}"))
    results.append(report("Background migrations started log present", start_idx != -1,
                          f"found at offset {start_idx}"))

    if report_idx != -1:
        block = log[report_idx: report_idx + 1500]
        end_match = re.search(r"\n.*={20,}", block[100:])
        if end_match:
            block = block[: 100 + end_match.end()]
        print("\n--- Migration Report Block (last) ---")
        print(block)
        print("--- end block ---\n")

        def grab(key):
            m = re.search(rf"{key}\s*:\s*(\d+)", block)
            return int(m.group(1)) if m else None

        scanned = grab("scanned")
        migrated = grab("migrated")
        unchanged = grab("unchanged")
        skipped = grab("skipped")
        failed = grab("failed")

        results.append(report("failed: 0", failed == 0, f"actual failed={failed}"))
        results.append(report("migrated: 0 (preview DB already migrated)",
                              migrated == 0, f"actual migrated={migrated}"))
        results.append(report("skipped: 3 expected", skipped == 3,
                              f"actual skipped={skipped}, scanned={scanned}, unchanged={unchanged}"))

        # Timing: report within ~5s of start
        ts_re = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d+)")
        starts = [(m.start(), m.group(1)) for m in ts_re.finditer(log)
                  if "Starting background data migrations" in log[m.start():m.start() + 200]]
        if starts:
            last_start_ts = starts[-1][1]
            preceding = log[max(0, report_idx - 200): report_idx]
            ts_match = list(ts_re.finditer(preceding))
            if ts_match:
                rep_ts = ts_match[-1].group(1)
                fmt = "%Y-%m-%d %H:%M:%S,%f"
                d_start = dt.datetime.strptime(last_start_ts, fmt)
                d_rep = dt.datetime.strptime(rep_ts, fmt)
                delta = (d_rep - d_start).total_seconds()
                results.append(report("Report within ~5s of migration start",
                                      0 <= delta <= 5,
                                      f"delta = {delta:.3f}s (start={last_start_ts}, report={rep_ts})"))
            else:
                results.append(report("Could not parse report timestamp", False))

        win_start = max(0, report_idx - 2000)
        win_end = min(len(log), report_idx + 2000)
        window = log[win_start:win_end]
        has_traceback = "Traceback (most recent call last)" in window
        results.append(report("No exception traceback near HD-Migration block",
                              not has_traceback,
                              "Traceback found" if has_traceback else "clean"))

    # /api/health
    try:
        r = requests.get(f"{API}/health", timeout=15)
        results.append(report("GET /api/health returns 200",
                              r.status_code == 200,
                              f"status={r.status_code}, body={r.text[:200]}"))
    except Exception as e:
        results.append(report("GET /api/health", False, str(e)))

    return results


def test_today_v5():
    section("2) GET /api/astrology/today-v5/{user_id} — daily cache + force_refresh")
    results = []
    url = f"{API}/astrology/today-v5/{PETE}"
    today_str = dt.date.today().isoformat()

    expected_key_pattern = re.compile(
        rf"^astrology_today_v5::{PETE}::\d{{4}}-\d{{2}}-\d{{2}}::today_v5\.\d+(\.\d+)?$"
    )

    try:
        r1 = requests.get(url, timeout=90)
        try:
            data1 = r1.json()
        except Exception:
            data1 = {}
    except Exception as e:
        results.append(report("Today V5 call A", False, str(e)))
        return results

    ok_status = r1.status_code == 200
    results.append(report("Call A: status 200", ok_status,
                          f"status={r1.status_code}, body={r1.text[:500] if not ok_status else ''}"))

    cache_key_1 = data1.get("cache_key")
    engine_v_1 = data1.get("engine_version")
    key_ok = bool(cache_key_1) and bool(expected_key_pattern.match(cache_key_1))
    date_in_key_today = today_str in (cache_key_1 or "")
    results.append(report("Call A: cache_key shape astrology_today_v5::<pete>::<today>::today_v5.x",
                          key_ok and date_in_key_today,
                          f"cache_key={cache_key_1}, today={today_str}"))
    results.append(report("Call A: engine_version == 'today_v5.1'",
                          engine_v_1 == "today_v5.1",
                          f"engine_version={engine_v_1}"))

    try:
        r2 = requests.get(url, timeout=60)
        data2 = r2.json()
    except Exception as e:
        results.append(report("Today V5 call B", False, str(e)))
        return results
    results.append(report("Call B: status 200", r2.status_code == 200,
                          f"status={r2.status_code}"))
    from_cache_2 = data2.get("from_cache")
    results.append(report("Call B: from_cache == True",
                          from_cache_2 is True,
                          f"from_cache={from_cache_2}, cache_key={data2.get('cache_key')}"))

    try:
        r3 = requests.get(url, params={"force_refresh": "true"}, timeout=90)
        data3 = r3.json()
    except Exception as e:
        results.append(report("Today V5 call C", False, str(e)))
        return results
    results.append(report("Call C: status 200", r3.status_code == 200,
                          f"status={r3.status_code}"))
    results.append(report("Call C: from_cache == False",
                          data3.get("from_cache") is False,
                          f"from_cache={data3.get('from_cache')}"))
    results.append(report("Call C: refresh_reason == 'force_refresh'",
                          data3.get("refresh_reason") == "force_refresh",
                          f"refresh_reason={data3.get('refresh_reason')}"))

    return results


def test_timeline_v1():
    section("3) GET /api/astrology/timeline/{user_id} — weekly cache + force_refresh")
    results = []
    url = f"{API}/astrology/timeline/{PETE}"
    expected_key = f"astrology_timeline::{PETE}::2026::timeline_v1.0"

    try:
        r1 = requests.get(url, timeout=120)
        try:
            data1 = r1.json()
        except Exception:
            data1 = {}
    except Exception as e:
        results.append(report("Timeline call A", False, str(e)))
        return results

    ok_a = r1.status_code == 200
    results.append(report("Call A: status 200", ok_a,
                          f"status={r1.status_code}, body={r1.text[:600] if not ok_a else ''}"))

    meta1 = data1.get("_cache_meta") or {}
    results.append(report("Call A: _cache_meta present", bool(meta1),
                          f"keys={list(meta1.keys())[:10]}"))
    results.append(report("Call A: _cache_meta.source in {cache, generated}",
                          meta1.get("source") in ("cache", "generated"),
                          f"source={meta1.get('source')}"))
    results.append(report("Call A: _cache_meta.year == 2026",
                          meta1.get("year") == 2026,
                          f"year={meta1.get('year')}"))
    results.append(report("Call A: _cache_meta.engine_version == 'timeline_v1.0'",
                          meta1.get("engine_version") == "timeline_v1.0",
                          f"engine_version={meta1.get('engine_version')}"))
    results.append(report(f"Call A: _cache_meta.cache_key == {expected_key}",
                          meta1.get("cache_key") == expected_key,
                          f"cache_key={meta1.get('cache_key')}"))
    bdh1 = meta1.get("birth_data_hash")
    results.append(report("Call A: birth_data_hash not null", bool(bdh1),
                          f"birth_data_hash={bdh1}"))

    try:
        r2 = requests.get(url, timeout=60)
        data2 = r2.json()
    except Exception as e:
        results.append(report("Timeline call B", False, str(e)))
        return results
    results.append(report("Call B: status 200", r2.status_code == 200,
                          f"status={r2.status_code}"))
    meta2 = data2.get("_cache_meta") or {}
    results.append(report("Call B: _cache_meta.source == 'cache'",
                          meta2.get("source") == "cache",
                          f"source={meta2.get('source')}, refresh_reason={meta2.get('refresh_reason')}"))
    age2 = meta2.get("age_seconds")
    results.append(report("Call B: age_seconds > 0",
                          isinstance(age2, (int, float)) and age2 > 0,
                          f"age_seconds={age2}"))

    try:
        r3 = requests.get(url, params={"force_refresh": "true"}, timeout=120)
        data3 = r3.json()
    except Exception as e:
        results.append(report("Timeline call C", False, str(e)))
        return results
    results.append(report("Call C: status 200", r3.status_code == 200,
                          f"status={r3.status_code}"))
    meta3 = data3.get("_cache_meta") or {}
    results.append(report("Call C: _cache_meta.source == 'generated'",
                          meta3.get("source") == "generated",
                          f"source={meta3.get('source')}"))
    results.append(report("Call C: _cache_meta.refresh_reason == 'force_refresh'",
                          meta3.get("refresh_reason") == "force_refresh",
                          f"refresh_reason={meta3.get('refresh_reason')}"))

    return results


def test_mongo_state():
    section("4) MongoDB-level verification")
    results = []
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    try:
        cli = MongoClient(mongo_url, serverSelectionTimeoutMS=5000)
        db = cli["test_database"]
        cli.admin.command("ping")
    except Exception as e:
        results.append(report("Connect to MongoDB test_database", False, str(e)))
        return results

    try:
        n_stamped = db.charts.count_documents(
            {"human_design.type_migration_version": "hd_motor_to_throat_bfs_v1"}
        )
    except Exception as e:
        results.append(report("count_documents on db.charts", False, str(e)))
        return results

    results.append(report("db.charts: stamped type_migration_version count >= 145",
                          n_stamped >= 145, f"actual count = {n_stamped}"))

    # Try several common id keys
    def find_chart_for(uid):
        for q in [{"user_id": uid}, {"_id": uid}, {"userId": uid}]:
            doc = db.charts.find_one(q)
            if doc:
                return doc, q
        return None, None

    pete_chart, pete_q = find_chart_for(PETE)
    pete_type = (pete_chart or {}).get("human_design", {}).get("type") if pete_chart else None
    results.append(report("Pete human_design.type == 'Manifestor'",
                          pete_type == "Manifestor",
                          f"query={pete_q}, found={pete_chart is not None}, type={pete_type}"))

    mel_chart, mel_q = find_chart_for(MEL)
    mel_type = (mel_chart or {}).get("human_design", {}).get("type") if mel_chart else None
    results.append(report("Mel human_design.type == 'Reflector'",
                          mel_type == "Reflector",
                          f"query={mel_q}, found={mel_chart is not None}, type={mel_type}"))

    try:
        tl_docs = list(db.astrology_timeline_cache.find({"user_id": PETE}))
    except Exception as e:
        results.append(report("Read db.astrology_timeline_cache for Pete", False, str(e)))
        return results

    results.append(report("db.astrology_timeline_cache: >=1 doc for Pete",
                          len(tl_docs) >= 1, f"docs found = {len(tl_docs)}"))

    if tl_docs:
        doc = tl_docs[0]
        eng = doc.get("engine_version")
        ck = doc.get("cache_key")
        expected_ck = f"astrology_timeline::{PETE}::2026::timeline_v1.0"
        results.append(report("timeline cache: engine_version == 'timeline_v1.0'",
                              eng == "timeline_v1.0", f"engine_version={eng}"))
        results.append(report(f"timeline cache: cache_key == {expected_ck}",
                              ck == expected_ck, f"cache_key={ck}"))
        print(f"        doc fields = {sorted(list(doc.keys()))}")

    return results


def main():
    all_results = []
    all_results += test_hd_migration_log()
    all_results += test_today_v5()
    all_results += test_timeline_v1()
    all_results += test_mongo_state()

    section("SUMMARY")
    passed = sum(1 for r in all_results if r)
    failed = sum(1 for r in all_results if not r)
    print(f"Passed: {passed}/{len(all_results)}")
    print(f"Failed: {failed}/{len(all_results)}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
