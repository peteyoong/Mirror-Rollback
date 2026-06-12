"""stage1_rollout_dashboard.py
=================================================================
Stage 1 (intent-router-v2-stage1-v1) — shadow-mode dashboard query.

READ-ONLY. Aggregates `mirror_chat_retrieval_receipts` to confirm:

  1. Bucket distribution across receipts is reasonably uniform across
     [0, 99] (no salt bias).
  2. Per-user stickiness — every (user_id) maps to exactly ONE
     stage1_bucket.
  3. Cutover decision reasons + enabled counts under the current
     `INTENT_ROUTER_V2_CUTOVER` / `INTENT_ROUTER_V2_ROLLOUT_PERCENT`
     env values.
  4. Distribution-by-domain so we can spot if any single domain
     (P4 forum-topology, in particular) over-indexes into the
     “enabled” bucket once the percent is flipped.

CLI usage:
    python tools/stage1_rollout_dashboard.py
    python tools/stage1_rollout_dashboard.py --hours 24
    python tools/stage1_rollout_dashboard.py --since-iso 2026-06-12T00:00:00Z

No writes. No flag flips. Safe to run against production.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

# Ensure /app/backend is on sys.path so we can import services/* helpers.
HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(HERE)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from dotenv import load_dotenv  # noqa: E402
from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

load_dotenv()

RECEIPTS_COLLECTION = "mirror_chat_retrieval_receipts"


def _parse_since(args: argparse.Namespace) -> Optional[datetime]:
    if args.since_iso:
        try:
            s = args.since_iso.replace("Z", "+00:00")
            return datetime.fromisoformat(s).astimezone(timezone.utc)
        except Exception as e:
            print(f"[stage1_dashboard] --since-iso parse error: {e}",
                  file=sys.stderr)
            sys.exit(2)
    if args.hours and args.hours > 0:
        return datetime.now(timezone.utc) - timedelta(hours=args.hours)
    return None


async def aggregate(db, since: Optional[datetime]) -> Dict[str, Any]:
    """Read all receipts (filtered by --since if provided) and produce a
    compact dashboard summary. Never writes."""
    query: Dict[str, Any] = {}
    if since is not None:
        query["computed_at"] = {"$gte": since.isoformat()}

    bucket_counts: Counter = Counter()
    enabled_counts: Counter = Counter()
    reason_counts: Counter = Counter()
    domain_counts: Counter = Counter()
    domain_enabled: Counter = Counter()
    user_buckets: Dict[str, set] = defaultdict(set)
    user_enabled: Dict[str, bool] = {}
    rollout_percents: Counter = Counter()
    cutover_flag_seen: Counter = Counter()

    total = 0
    missing_telemetry = 0
    forum_topology_receipts = 0

    async for r in db[RECEIPTS_COLLECTION].find(query):
        total += 1
        bucket = r.get("stage1_bucket")
        decision = r.get("cutover_decision") or {}
        uid = r.get("user_id")
        domain = (r.get("intent_envelope") or {}).get("primary_domain") or "general"
        frame_source = r.get("frame_source") or {}

        if bucket is None or not decision:
            missing_telemetry += 1
            continue

        bucket_counts[int(bucket)] += 1
        enabled = bool(decision.get("enabled"))
        reason = str(decision.get("reason"))
        enabled_counts["enabled" if enabled else "disabled"] += 1
        reason_counts[reason] += 1
        domain_counts[domain] += 1
        if enabled:
            domain_enabled[domain] += 1
        if uid:
            user_buckets[uid].add(int(bucket))
            user_enabled[uid] = enabled
        rp = decision.get("rollout_percent")
        if rp is not None:
            rollout_percents[int(rp)] += 1
        cutover_flag_seen[bool(decision.get("cutover_flag"))] += 1
        if frame_source.get("forum_topology_supplied"):
            forum_topology_receipts += 1

    # Per-user stickiness — flag any user whose receipts straddle >1 bucket.
    unsticky_users = {uid: sorted(b) for uid, b in user_buckets.items()
                      if len(b) > 1}
    unique_users = len(user_buckets)
    enabled_unique_users = sum(1 for v in user_enabled.values() if v)

    # Bucket-distribution uniformity (only meaningful with enough samples).
    nonzero_buckets = len(bucket_counts)
    bucket_max = max(bucket_counts.values()) if bucket_counts else 0
    bucket_min = min(bucket_counts.values()) if bucket_counts else 0

    return {
        "query":                          {"since": since.isoformat() if since else None},
        "total_receipts":                 total,
        "receipts_missing_stage1_fields": missing_telemetry,
        "forum_topology_receipts":        forum_topology_receipts,
        "enabled_counts":                 dict(enabled_counts),
        "reason_counts":                  dict(reason_counts),
        "rollout_percents_observed":      dict(rollout_percents),
        "cutover_flag_observed":          {str(k): v for k, v in cutover_flag_seen.items()},
        "unique_users":                   unique_users,
        "unique_users_enabled":           enabled_unique_users,
        "unsticky_users_count":           len(unsticky_users),
        "unsticky_users_sample":          dict(list(unsticky_users.items())[:5]),
        "bucket_distribution": {
            "nonzero_buckets":     nonzero_buckets,
            "max_bucket_count":    bucket_max,
            "min_bucket_count":    bucket_min,
            "spread_max_minus_min": bucket_max - bucket_min,
        },
        "domain_distribution":            dict(domain_counts),
        "domain_enabled_distribution":    dict(domain_enabled),
        "computed_at":                    datetime.now(timezone.utc).isoformat(),
    }


async def amain() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hours", type=int, default=0,
                        help="Only aggregate receipts from the last N hours.")
    parser.add_argument("--since-iso", type=str, default="",
                        help="Only aggregate receipts >= this ISO timestamp.")
    parser.add_argument("--json", action="store_true",
                        help="Emit the summary as a single JSON line.")
    args = parser.parse_args()

    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    if not mongo_url or not db_name:
        print("[stage1_dashboard] MONGO_URL / DB_NAME not configured", file=sys.stderr)
        return 2

    client = AsyncIOMotorClient(mongo_url)
    try:
        db = client[db_name]
        since = _parse_since(args)
        summary = await aggregate(db, since)
    finally:
        client.close()

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print("=" * 72)
        print(" Stage 1 rollout dashboard — intent-router-v2-stage1-v1")
        print("=" * 72)
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(amain()))
