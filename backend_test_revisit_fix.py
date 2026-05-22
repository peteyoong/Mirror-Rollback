"""
VERIFICATION RETEST — Between You Today V1.1 telemetry revisit fix.

Tests that the C11 bug (E11000 duplicate _id when inserting the
auto-derived today_card_revisited_same_day event) is fixed.
"""
import os
import sys
import asyncio
from datetime import datetime, timezone

import requests
from motor.motor_asyncio import AsyncIOMotorClient

BACKEND_URL = "https://mapping-phase4.preview.emergentagent.com/api"
MONGO_URL   = "mongodb://localhost:27017"
DB_NAME     = "test_database"
EVENT_COLL  = "relationship_today_events"

FORUM_ID  = "69dda348de9cb1c83c0780fa"
ANCHOR_ID = "697f0c6abf35c0528ff06954"  # Pete
THAD_ID   = "69dd0b2cc92ba973f8838c11"  # Thaddeus
ISAAC_ID  = "69dda348de9cb1c83c0780f8"  # Isaac (fresh / no prior views possibly)

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
INFO = "\033[94mINFO\033[0m"

results = []


def log(label, ok, detail=""):
    tag = PASS if ok else FAIL
    print(f"[{tag}] {label} — {detail}")
    results.append((label, ok, detail))
    return ok


def post_event(member_id, event="today_card_viewed", intensity="high",
               anchor_id=ANCHOR_ID, forum_id=FORUM_ID, extra_payload=None):
    body = {
        "event": event,
        "user_id": anchor_id,
        "member_id": member_id,
        "intensity": intensity,
    }
    if extra_payload:
        body.update(extra_payload)
    url = f"{BACKEND_URL}/forums/{forum_id}/between-you-today/event"
    r = requests.post(url, json=body, timeout=15)
    return r


async def count_events(anchor_id, target_id, date_str):
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    v = await db[EVENT_COLL].count_documents({
        "event": "today_card_viewed",
        "anchor_id": anchor_id,
        "target_id": target_id,
        "date": date_str,
    })
    r = await db[EVENT_COLL].count_documents({
        "event": "today_card_revisited_same_day",
        "anchor_id": anchor_id,
        "target_id": target_id,
        "date": date_str,
    })
    client.close()
    return v, r


def main():
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"\n{INFO} Testing {BACKEND_URL}")
    print(f"{INFO} forum_id={FORUM_ID}  anchor={ANCHOR_ID}  date={today_str}\n")

    # --- BASELINE counts BEFORE we fire 3 views (Thaddeus pair) ---
    v_before, r_before = asyncio.run(count_events(ANCHOR_ID, THAD_ID, today_str))
    print(f"{INFO} BASELINE (Pete,Thaddeus,{today_str}): views={v_before}, revisits={r_before}")

    # ------------------------------------------------------------------
    # 1. Fire today_card_viewed three times and ensure each returns 200/success:true
    # ------------------------------------------------------------------
    success_codes = []
    for i in range(3):
        r = post_event(THAD_ID, event="today_card_viewed", intensity="high")
        ok = (r.status_code == 200) and bool(r.json().get("success"))
        success_codes.append((r.status_code, r.json()))
        log(f"V1 call#{i+1} (today_card_viewed) → 200 success:true",
            ok, f"status={r.status_code}, body={r.json()}")

    # Allow async writes to settle
    import time as _t
    _t.sleep(0.5)

    # ------------------------------------------------------------------
    # 2. Recount and check deltas
    # ------------------------------------------------------------------
    v_after, r_after = asyncio.run(count_events(ANCHOR_ID, THAD_ID, today_str))
    dV = v_after - v_before
    dR = r_after - r_before
    print(f"\n{INFO} AFTER (Pete,Thaddeus,{today_str}): views={v_after}, revisits={r_after}")
    print(f"{INFO} ΔV={dV}, ΔR={dR}")

    log("ΔV == 3 (3 view rows persisted)", dV == 3, f"got ΔV={dV}")
    log("ΔR == 2 (revisits fire on 2nd & 3rd view)", dR == 2, f"got ΔR={dR}")

    # ------------------------------------------------------------------
    # 3. Indirect proof — fire 3 views on a fresh-ish pair (Isaac)
    # ------------------------------------------------------------------
    v_before_i, r_before_i = asyncio.run(count_events(ANCHOR_ID, ISAAC_ID, today_str))
    print(f"\n{INFO} BASELINE (Pete,Isaac,{today_str}): views={v_before_i}, revisits={r_before_i}")
    for i in range(3):
        r = post_event(ISAAC_ID, event="today_card_viewed", intensity="high")
        ok = r.status_code == 200 and r.json().get("success")
        log(f"Isaac call#{i+1} returns 200 success:true", ok,
            f"status={r.status_code}, body={r.json()}")
    _t.sleep(0.5)
    v_after_i, r_after_i = asyncio.run(count_events(ANCHOR_ID, ISAAC_ID, today_str))
    print(f"{INFO} AFTER (Pete,Isaac,{today_str}): views={v_after_i}, revisits={r_after_i}")
    log("Isaac ΔV == 3", v_after_i - v_before_i == 3, f"ΔV={v_after_i - v_before_i}")
    log("Isaac ΔR == 2", r_after_i - r_before_i == 2, f"ΔR={r_after_i - r_before_i}")

    # ------------------------------------------------------------------
    # 4. REGRESSION GUARDS
    # ------------------------------------------------------------------
    # 4a) GET endpoint returns engine_version v1.1
    print(f"\n{INFO} === REGRESSION GUARDS ===")
    rget = requests.get(
        f"{BACKEND_URL}/forums/{FORUM_ID}/between-you-today",
        params={"user_id": ANCHOR_ID, "member_id": THAD_ID},
        timeout=30,
    )
    body = rget.json() if rget.status_code == 200 else {}
    eng = body.get("engine_version") or (body.get("envelope") or {}).get("engine_version")
    log("GET returns engine_version 'between-you-today-v1.1'",
        rget.status_code == 200 and eng == "between-you-today-v1.1",
        f"status={rget.status_code} engine_version={eng}")

    # 4b) Unknown event name → success:false
    r_unk = post_event(THAD_ID, event="totally_made_up_event")
    body_unk = r_unk.json()
    log("Unknown event → 200 success:false",
        r_unk.status_code == 200 and body_unk.get("success") is False,
        f"status={r_unk.status_code} body={body_unk}")

    # 4c) Missing event field → 400
    r_missing = requests.post(
        f"{BACKEND_URL}/forums/{FORUM_ID}/between-you-today/event",
        json={"user_id": ANCHOR_ID, "member_id": THAD_ID, "intensity": "high"},
        timeout=15,
    )
    log("Missing event field → 400",
        r_missing.status_code == 400,
        f"status={r_missing.status_code} body={r_missing.text[:200]}")

    # 4d) Non-member anchor → 403
    fake_anchor = "000000000000000000000099"
    r_nm = requests.post(
        f"{BACKEND_URL}/forums/{FORUM_ID}/between-you-today/event",
        json={"event": "today_card_viewed", "user_id": fake_anchor,
              "member_id": THAD_ID, "intensity": "high"},
        timeout=15,
    )
    log("Non-member anchor → 403",
        r_nm.status_code == 403,
        f"status={r_nm.status_code} body={r_nm.text[:200]}")

    # ------------------------------------------------------------------
    # 5. Backend log check — no E11000 errors
    # ------------------------------------------------------------------
    print(f"\n{INFO} === BACKEND LOG CHECK ===")
    try:
        import subprocess
        out = subprocess.run(
            ["bash", "-c",
             "tail -n 400 /var/log/supervisor/backend.err.log /var/log/supervisor/backend.out.log 2>/dev/null | "
             "grep -E 'E11000|revisit derive failed|today_card_revisited|today_card_viewed' | tail -40"],
            capture_output=True, text=True, timeout=10
        )
        log_chunk = out.stdout
        print(log_chunk if log_chunk else "(no relevant log lines)")
        has_e11000 = "E11000" in log_chunk
        has_revisit_warn = "revisit derive failed" in log_chunk
        log("No E11000 duplicate key errors recently", not has_e11000,
            "E11000 STILL APPEARS" if has_e11000 else "clean")
        log("No 'revisit derive failed' warnings recently", not has_revisit_warn,
            "WARNING STILL APPEARS" if has_revisit_warn else "clean")
    except Exception as e:
        print(f"Could not check logs: {e}")

    # ------------------------------------------------------------------
    # SUMMARY
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    passes = sum(1 for _, ok, _ in results if ok)
    fails = sum(1 for _, ok, _ in results if not ok)
    print(f"SUMMARY: {passes} PASS / {fails} FAIL out of {len(results)}")
    print("=" * 70)
    for label, ok, detail in results:
        if not ok:
            print(f"  FAIL — {label}: {detail}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
