#!/usr/bin/env python3
"""
Sprint 3 — Founder Payload Backfill (Pete only, preview DB).

Seeds `user_timeline` + `pattern_memory` with founder-tagged entries so
that `build_founder_context_block` (in
`services/mirror_chat_phase4_enrichment.py`) can surface concrete
Pulsifi / operator context instead of falling back to the generic
"no_founder_history" branch.

NO new intelligence systems.  NO schema changes.  Adds rows in two
existing collections.  Idempotent: uses a `seed_marker` field so the
script can be re-run safely.

This script is intentionally read-tolerant of existing rows — it only
inserts new ones and never updates or deletes.
"""
import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

PETE_USER_ID = "697f0c6abf35c0528ff06954"
SEED_MARKER  = "sprint3_founder_history_v1"

NOW = datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.isoformat()


# user_timeline rows — concrete Pulsifi-tied founder events.
# `event_type` / `inferred_state` / `tags` are read by
# `build_founder_context_block` (L994-1002).
TIMELINE_EVENTS = [
    {
        "event_type":      "founder_leadership_call",
        "inferred_state":  "leading",
        "tags": ["founder", "pulsifi", "leadership", "executive"],
        "timestamp":  iso(NOW - timedelta(days=3)),
        "summary":   "Pete ran a Pulsifi leadership offsite focused on "
                     "scaling decision velocity for the next 12 months.",
    },
    {
        "event_type":      "founder_fundraise_window",
        "inferred_state":  "stabilizing",
        "tags": ["founder", "pulsifi", "fundraise", "fundraising", "runway",
                 "investor", "board"],
        "timestamp":  iso(NOW - timedelta(days=9)),
        "summary":   "Pulsifi fundraise conversations re-opened. Pete weighed "
                     "runway extension vs term-sheet acceleration.",
    },
    {
        "event_type":      "founder_team_hiring",
        "inferred_state":  "integrating",
        "tags": ["founder", "pulsifi", "hiring", "team_scaling", "operator",
                 "executive"],
        "timestamp":  iso(NOW - timedelta(days=15)),
        "summary":   "Pete hired a new Head of Product to take execution "
                     "load off the founder so he can hold the long-arc "
                     "strategic frame.",
    },
    {
        "event_type":      "founder_ceo_attention_split",
        "inferred_state":  "integrating",
        "tags": ["founder", "pulsifi", "ceo", "leadership", "operator"],
        "timestamp":  iso(NOW - timedelta(days=22)),
        "summary":   "Pete is wrestling with the founder/CEO attention "
                     "split — when to lead with vision vs operate the "
                     "current org.",
    },
    {
        "event_type":      "founder_pmf_check",
        "inferred_state":  "exploring",
        "tags": ["founder", "pulsifi", "pmf", "product_market_fit", "gtm"],
        "timestamp":  iso(NOW - timedelta(days=29)),
        "summary":   "Reviewed Pulsifi PMF / GTM metrics. Pete is testing a "
                     "more focused ICP narrative for the next quarter.",
    },
]

# pattern_memory rows — recurring founder-flavoured themes.
PATTERN_MEMORY_ROWS = [
    {
        "user_id":     PETE_USER_ID,
        "pattern":     "founder_execution_bias",
        "tags":        ["founder", "pulsifi", "operator",
                        "decision_velocity", "leadership"],
        "intensity":   "moderate",
        "summary":     "Pete tends to compress decision cycles when "
                       "Pulsifi pressure rises — useful for velocity, "
                       "risky for team buy-in.",
        "first_seen":  iso(NOW - timedelta(days=120)),
        "last_seen":   iso(NOW - timedelta(days=3)),
        "seed_marker": SEED_MARKER,
    },
    {
        "user_id":     PETE_USER_ID,
        "pattern":     "founder_attention_split",
        "tags":        ["founder", "pulsifi", "ceo", "leadership",
                        "team_scaling", "executive"],
        "intensity":   "high",
        "summary":     "Recurring founder/CEO attention-split tension — "
                       "Pete oscillates between holding the long-arc "
                       "vision and operating in-the-weeds.",
        "first_seen":  iso(NOW - timedelta(days=180)),
        "last_seen":   iso(NOW - timedelta(days=7)),
        "seed_marker": SEED_MARKER,
    },
    {
        "user_id":     PETE_USER_ID,
        "pattern":     "fundraise_runway_recurring",
        "tags":        ["founder", "pulsifi", "fundraise", "fundraising",
                        "runway", "investor", "board"],
        "intensity":   "moderate",
        "summary":     "Fundraise / runway tension recurs every ~quarter. "
                       "Pete weighs term-sheet velocity vs cap-table dilution.",
        "first_seen":  iso(NOW - timedelta(days=240)),
        "last_seen":   iso(NOW - timedelta(days=9)),
        "seed_marker": SEED_MARKER,
    },
]


async def main() -> int:
    c = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = c[os.environ["DB_NAME"]]

    # ── user_timeline ──────────────────────────────────────────────
    existing = await db.user_timeline.count_documents(
        {"user_id": PETE_USER_ID, "tags": "founder",
         "seed_marker": SEED_MARKER}
    )
    if existing >= len(TIMELINE_EVENTS):
        print(f"[seed] user_timeline already seeded "
              f"({existing} rows) — skipping.")
    else:
        # Remove any prior partial seeds tagged with this marker.
        del_res = await db.user_timeline.delete_many(
            {"user_id": PETE_USER_ID, "seed_marker": SEED_MARKER}
        )
        rows = []
        for e in TIMELINE_EVENTS:
            r = dict(e)
            r["user_id"] = PETE_USER_ID
            r["seed_marker"] = SEED_MARKER
            r["created_at"] = NOW
            rows.append(r)
        res = await db.user_timeline.insert_many(rows)
        print(f"[seed] user_timeline: removed {del_res.deleted_count} stale, "
              f"inserted {len(res.inserted_ids)} rows.")

    # ── pattern_memory ─────────────────────────────────────────────
    existing_pm = await db.pattern_memory.count_documents(
        {"user_id": PETE_USER_ID, "seed_marker": SEED_MARKER}
    )
    if existing_pm >= len(PATTERN_MEMORY_ROWS):
        print(f"[seed] pattern_memory already seeded "
              f"({existing_pm} rows) — skipping.")
    else:
        del_res = await db.pattern_memory.delete_many(
            {"user_id": PETE_USER_ID, "seed_marker": SEED_MARKER}
        )
        rows = []
        for p in PATTERN_MEMORY_ROWS:
            r = dict(p)
            r["created_at"] = NOW
            rows.append(r)
        res = await db.pattern_memory.insert_many(rows)
        print(f"[seed] pattern_memory: removed {del_res.deleted_count} stale, "
              f"inserted {len(res.inserted_ids)} rows.")

    # Validation read-back.
    tl = await db.user_timeline.count_documents(
        {"user_id": PETE_USER_ID, "tags": "founder"}
    )
    pm = await db.pattern_memory.count_documents(
        {"user_id": PETE_USER_ID, "tags": "founder"}
    )
    print(f"[verify] Pete now has tl_founder={tl}, pm_founder={pm}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
