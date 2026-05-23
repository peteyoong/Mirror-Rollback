"""
Backend tests for Timeline V2 / Phase Architecture V1A
GET /api/timeline/governing-chapter/{user_id}
"""
import os
import time
import json
import requests
from datetime import datetime, timezone
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]

# Public URL from frontend .env
BASE = None
with open("/app/frontend/.env") as f:
    for line in f:
        if line.startswith("EXPO_PUBLIC_BACKEND_URL"):
            BASE = line.split("=", 1)[1].strip().strip('"')
            break
API = f"{BASE}/api"
print(f"Using API base: {API}")

mongo = MongoClient(MONGO_URL)
db = mongo[DB_NAME]

PETE = "697f0c6abf35c0528ff06954"
MEL = "697ec826ad4b18f75bf42616"
ACHIEVE = "6a111d24328ffbb9b24c74cd"
UNKNOWN = "000000000000000000000099"


def ENDPOINT(uid, fr=False):
    if fr:
        return f"{API}/timeline/governing-chapter/{uid}?force_refresh=true"
    return f"{API}/timeline/governing-chapter/{uid}"


results = {}


def record(name, ok, detail=""):
    results[name] = (ok, detail)
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}: {detail}")


def test_s2_404_unknown():
    r = requests.get(ENDPOINT(UNKNOWN), timeout=30)
    if r.status_code != 404:
        record("S2_404_unknown_user", False, f"expected 404, got {r.status_code}: {r.text[:200]}")
        return
    try:
        body = r.json()
        if "chart not found" in str(body.get("detail", "")).lower():
            record("S2_404_unknown_user", True, f"detail={body.get('detail')}")
        else:
            record("S2_404_unknown_user", False, f"detail mismatch: {body}")
    except Exception as e:
        record("S2_404_unknown_user", False, f"json parse: {e}")


def test_s1_pete():
    r = requests.get(ENDPOINT(PETE, fr=True), timeout=60)
    if r.status_code != 200:
        record("S1_pete", False, f"status {r.status_code}: {r.text[:200]}")
        return None
    data = r.json()
    cache_control = r.headers.get("cache-control", "")
    if "no-store" not in cache_control.lower():
        record("S1_pete_cache_control", False, f"Cache-Control missing no-store: {cache_control!r}")
    else:
        record("S1_pete_cache_control", True, "Cache-Control: no-store present")

    if data.get("build_marker") != "phase-architecture-v1a":
        record("S1_pete_build_marker", False, f"got {data.get('build_marker')}")
    else:
        record("S1_pete_build_marker", True, "phase-architecture-v1a")

    ch = data.get("chapter") or {}
    chid = ch.get("chapter_id")
    title = ch.get("title")
    sel = data.get("selection_mode")
    sl_ids = [c.get("chapter_id") for c in (data.get("shortlist") or [])]
    if chid != "cost_of_keeping_the_peace":
        record("S1_pete_chapter_id", False, f"expected cost_of_keeping_the_peace, got {chid}; mode={sel}; shortlist={sl_ids}")
    else:
        record("S1_pete_chapter_id", True, f"{chid} (mode={sel})")
    if title != "The Cost Of Keeping The Peace":
        record("S1_pete_title", False, f"got {title!r}")
    else:
        record("S1_pete_title", True, title)
    if sel not in ("llm_from_shortlist", "deterministic_top1"):
        record("S1_pete_selection_mode", False, f"unexpected: {sel}")
    else:
        record("S1_pete_selection_mode", True, sel)
    return data


def test_s1_mel():
    r = requests.get(ENDPOINT(MEL, fr=True), timeout=60)
    if r.status_code != 200:
        record("S1_mel", False, f"status {r.status_code}: {r.text[:200]}")
        return
    data = r.json()
    chid = (data.get("chapter") or {}).get("chapter_id")
    sel = data.get("selection_mode")
    sl_ids = [c.get("chapter_id") for c in (data.get("shortlist") or [])]
    if chid != "cost_of_keeping_the_peace":
        record("S1_mel_chapter_id", False, f"expected cost_of_keeping_the_peace, got {chid}; mode={sel}; shortlist={sl_ids}")
    else:
        record("S1_mel_chapter_id", True, f"{chid} (mode={sel})")


def test_s1_achievement():
    r = requests.get(ENDPOINT(ACHIEVE), timeout=60)
    if r.status_code != 200:
        record("S1_achievement", False, f"status {r.status_code}: {r.text[:200]}")
        return
    data = r.json()
    sl = data.get("shortlist") or []
    chosen = (data.get("chapter") or {}).get("chapter_id")
    if len(sl) < 1 and data.get("selection_mode") != "fallback_no_score":
        record("S1_achievement_shortlist", False, f"shortlist empty without fallback; mode={data.get('selection_mode')}")
    else:
        record("S1_achievement_shortlist", True, f"size={len(sl)} ids={[c.get('chapter_id') for c in sl]}; chosen={chosen}; from_cache={data.get('from_cache')}")


def test_s3_s4_caching():
    r1 = requests.get(ENDPOINT(PETE, fr=True), timeout=60)
    if r1.status_code != 200:
        record("S3_caching", False, f"first force-refresh failed: {r1.status_code}")
        return
    d1 = r1.json()
    iso1 = d1.get("computed_at_iso")
    if d1.get("from_cache") is True:
        record("S3_force_refresh_not_cached", False, f"force_refresh returned from_cache=true: {iso1}")
    else:
        record("S3_force_refresh_not_cached", True, f"computed_at_iso={iso1}, from_cache={d1.get('from_cache')}")

    time.sleep(1)
    r2 = requests.get(ENDPOINT(PETE), timeout=60)
    d2 = r2.json()
    iso2 = d2.get("computed_at_iso")
    if d2.get("from_cache") is True and iso2 == iso1:
        record("S3_cache_hit", True, f"from_cache=True, iso preserved={iso2}")
    else:
        record("S3_cache_hit", False, f"from_cache={d2.get('from_cache')}, iso1={iso1}, iso2={iso2}")

    time.sleep(2)
    r3 = requests.get(ENDPOINT(PETE, fr=True), timeout=60)
    d3 = r3.json()
    iso3 = d3.get("computed_at_iso")
    if d3.get("from_cache") is True:
        record("S3_force_refresh_again_not_cached", False, "from_cache=true unexpectedly")
    else:
        record("S3_force_refresh_again_not_cached", True, "from_cache=False")
    if iso3 and iso3 != iso1:
        record("S3_force_refresh_new_iso", True, f"new iso {iso3} != {iso1}")
    else:
        record("S3_force_refresh_new_iso", False, f"iso did not change: {iso1} vs {iso3}")

    time.sleep(1)
    r4 = requests.get(ENDPOINT(PETE), timeout=60)
    d4 = r4.json()
    if d4.get("from_cache") is True and d4.get("computed_at_iso") == iso3:
        chid_match = (d4.get("chapter") or {}).get("chapter_id") == (d3.get("chapter") or {}).get("chapter_id")
        record("S4_cache_ttl_force_isolation", chid_match, f"iso={d4.get('computed_at_iso')}, chid_match={chid_match}")
    else:
        record("S4_cache_ttl_force_isolation", False, f"from_cache={d4.get('from_cache')} iso={d4.get('computed_at_iso')} vs {iso3}")

    return d3


SYNTHETIC_S5 = "cross_lens_atoms_test_s5_user"


def seed_s5_chart():
    chart = {
        "user_id": SYNTHETIC_S5,
        "human_design": {
            "defined_centers": ["Ajna", "Head"],
            "active_gates": [22, 49],
        },
        "astrology": {
            "planets": {
                "Saturn": {"house": 3, "sign": "Aries"},
                "Moon":   {"house": 5, "sign": "Cancer"},
            },
            "aspects": [
                {"body1": "Saturn", "body2": "Moon",    "type": "square"},
                {"body1": "Saturn", "body2": "Venus",   "type": "opposition"},
                {"body1": "Saturn", "body2": "Mercury", "type": "conjunction"},
            ],
        },
    }
    db.charts.replace_one({"user_id": SYNTHETIC_S5}, chart, upsert=True)


def test_s5_guardrail():
    seed_s5_chart()
    db.governing_chapter_cache.delete_one({"user_id": SYNTHETIC_S5})
    r = requests.get(ENDPOINT(SYNTHETIC_S5, fr=True), timeout=60)
    if r.status_code != 200:
        record("S5_guardrail", False, f"status {r.status_code}: {r.text[:300]}")
        return
    data = r.json()
    sl = data.get("shortlist") or []
    sl_ids = [c["chapter_id"] for c in sl]
    if not (2 <= len(sl) <= 3):
        record("S5_shortlist_size", False, f"len={len(sl)} ids={sl_ids}")
    else:
        record("S5_shortlist_size", True, f"size={len(sl)} ids={sl_ids}")
    chosen_id = (data.get("chapter") or {}).get("chapter_id")
    if chosen_id not in sl_ids:
        record("S5_chosen_in_shortlist", False, f"chosen={chosen_id} not in {sl_ids}")
    else:
        record("S5_chosen_in_shortlist", True, f"chosen={chosen_id}")
    mode = data.get("selection_mode")
    reason = data.get("selection_reason")
    if mode == "llm_from_shortlist":
        if reason and isinstance(reason, str) and 0 < len(reason) < 250:
            record("S5_selection_reason", True, f"len={len(reason)} reason={reason!r}")
        else:
            record("S5_selection_reason", False, f"reason invalid: {reason!r}")
    else:
        record("S5_selection_reason", True, f"mode={mode} (skipped)")
    proof_score = (data.get("proof") or {}).get("score")
    sl_score = next((c["score"] for c in sl if c["chapter_id"] == chosen_id), None)
    if proof_score == sl_score:
        record("S5_proof_score_matches", True, f"score={proof_score}")
    else:
        record("S5_proof_score_matches", False, f"proof.score={proof_score} != shortlist={sl_score}")


SYNTHETIC_S6 = "cross_lens_atoms_test_s6_user"


def seed_s6_chart():
    chart = {
        "user_id": SYNTHETIC_S6,
        "human_design": {
            "defined_centers": ["Ajna"],
            "active_gates": [1, 2, 3],
        },
        "astrology": {
            "planets": {
                "Saturn": {"house": 5, "sign": "Leo"},
                "Moon":   {"house": 8, "sign": "Pisces"},
            },
            "aspects": [],
        },
        "numerology": {},
    }
    db.charts.replace_one({"user_id": SYNTHETIC_S6}, chart, upsert=True)


def test_s6_fallback():
    seed_s6_chart()
    db.governing_chapter_cache.delete_one({"user_id": SYNTHETIC_S6})
    r = requests.get(ENDPOINT(SYNTHETIC_S6, fr=True), timeout=60)
    if r.status_code != 200:
        record("S6_fallback", False, f"status {r.status_code}: {r.text[:300]}")
        return
    data = r.json()
    if data.get("selection_mode") != "fallback_no_score":
        record("S6_selection_mode", False, f"got {data.get('selection_mode')}; signals={data.get('signals_extracted')}; shortlist={data.get('shortlist')}")
    else:
        record("S6_selection_mode", True, "fallback_no_score")
    chid = (data.get("chapter") or {}).get("chapter_id")
    if chid != "active_recalibration":
        record("S6_chapter_id", False, f"got {chid}")
    else:
        record("S6_chapter_id", True, chid)
    score = (data.get("proof") or {}).get("score")
    if score != 0.0:
        record("S6_proof_score_zero", False, f"got {score}")
    else:
        record("S6_proof_score_zero", True, "0.0")
    sl = data.get("shortlist")
    record("S6_shortlist", True, f"shortlist={sl}")


SYNTHETIC_S7 = "cross_lens_atoms_test_s7_user"


def seed_s7_chart():
    chart = {"user_id": SYNTHETIC_S7}
    db.charts.replace_one({"user_id": SYNTHETIC_S7}, chart, upsert=True)


def test_s7_resilience():
    seed_s7_chart()
    db.governing_chapter_cache.delete_one({"user_id": SYNTHETIC_S7})
    try:
        r = requests.get(ENDPOINT(SYNTHETIC_S7, fr=True), timeout=60)
    except Exception as e:
        record("S7_resilience", False, f"request error: {e}")
        return
    if r.status_code != 200:
        record("S7_resilience", False, f"status {r.status_code}: {r.text[:300]}")
        return
    data = r.json()
    chid = (data.get("chapter") or {}).get("chapter_id")
    if chid == "active_recalibration":
        record("S7_resilience", True, f"200 with fallback; mode={data.get('selection_mode')}")
    else:
        record("S7_resilience", False, f"200 but chapter={chid}")


def test_s8_signals(pete_data):
    if not pete_data:
        r = requests.get(ENDPOINT(PETE), timeout=60)
        pete_data = r.json()
    sigs = set(pete_data.get("signals_extracted") or [])
    required = {"astro_saturn_house_3_4_7", "hd_channel_22", "hd_channel_49", "hd_defined_heart"}
    missing = required - sigs
    if missing:
        record("S8_signals_extracted", False, f"missing: {missing}; got: {sorted(sigs)}")
    else:
        record("S8_signals_extracted", True, f"all 4 present; total={len(sigs)}: {sorted(sigs)}")


def test_s9_tone(pete_data):
    if not pete_data:
        r = requests.get(ENDPOINT(PETE), timeout=60)
        pete_data = r.json()
    ch = pete_data.get("chapter") or {}
    title = ch.get("title") or ""
    body = ch.get("body_visible") or ""
    forbidden = ["communication", "house", "vedic", "jyotish", "transit", "ascendant"]
    title_v = [t for t in forbidden if t in title.lower()]
    if title_v:
        record("S9_title_clean", False, f"violations: {title_v}; title={title!r}")
    else:
        record("S9_title_clean", True, title)
    bv = [t for t in ("you must", "you should") if t in body.lower()]
    if bv:
        record("S9_body_no_prescriptive", False, f"found: {bv}")
    else:
        record("S9_body_no_prescriptive", True, "ok")
    if len(body) < 100:
        record("S9_body_length", False, f"len={len(body)}")
    else:
        record("S9_body_length", True, f"len={len(body)}")
    topics = (pete_data.get("proof") or {}).get("internal_topics")
    if isinstance(topics, list):
        record("S9_internal_topics_array", True, f"{topics}")
    else:
        record("S9_internal_topics_array", False, f"type={type(topics).__name__}")


def test_s10_regression():
    r = requests.get(f"{API}/synthesis/atoms/{PETE}", timeout=60)
    if r.status_code != 200:
        record("S10_atoms_regression", False, f"status {r.status_code}: {r.text[:200]}")
        return
    data = r.json()
    atoms = data.get("atoms") or []
    atom_ids = [a.get("atom_id") for a in atoms]
    titles = [a.get("title", "") for a in atoms]
    blob = " ".join(str(x) for x in atom_ids + titles).lower()
    if "achievement" in blob and "stabil" in blob:
        record("S10_atoms_regression", True, f"Achievement-as-Stabilization found; total atoms={len(atoms)}")
    else:
        record("S10_atoms_regression", False, f"atom_ids={atom_ids}, titles={titles}")


def test_s11_cache_isolation():
    rp = requests.get(ENDPOINT(PETE, fr=True), timeout=60)
    dp = rp.json()
    pete_chid = (dp.get("chapter") or {}).get("chapter_id")
    pete_iso = dp.get("computed_at_iso")
    rm = requests.get(ENDPOINT(MEL), timeout=60)
    dm = rm.json()
    mel_chid = (dm.get("chapter") or {}).get("chapter_id")
    mel_iso = dm.get("computed_at_iso")
    if mel_iso == pete_iso:
        record("S11_cache_isolation", False, f"Mel iso == Pete iso ({mel_iso}) — cache leak")
    else:
        record("S11_cache_isolation", True, f"Pete({pete_chid},{pete_iso}); Mel({mel_chid},{mel_iso})")


def cleanup():
    for uid in (SYNTHETIC_S5, SYNTHETIC_S6, SYNTHETIC_S7):
        db.charts.delete_one({"user_id": uid})
        db.governing_chapter_cache.delete_one({"user_id": uid})
    print("Cleanup complete: synthetic charts removed.")


if __name__ == "__main__":
    print("=" * 80)
    print("Timeline V2 / Phase Architecture V1A Backend Tests")
    print("=" * 80)

    try:
        test_s2_404_unknown()
        pete_data = test_s1_pete()
        test_s1_mel()
        test_s1_achievement()
        test_s3_s4_caching()
        test_s5_guardrail()
        test_s6_fallback()
        test_s7_resilience()
        rp = requests.get(ENDPOINT(PETE), timeout=60)
        rp_data = rp.json() if rp.status_code == 200 else {}
        test_s8_signals(rp_data)
        test_s9_tone(rp_data)
        test_s10_regression()
        test_s11_cache_isolation()
    finally:
        cleanup()

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    passed = sum(1 for ok, _ in results.values() if ok)
    failed = sum(1 for ok, _ in results.values() if not ok)
    for name, (ok, detail) in results.items():
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print(f"\nTotal: {passed} passed, {failed} failed out of {len(results)}")
