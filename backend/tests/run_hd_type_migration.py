"""
HD Type Migration — motor_to_throat BFS v1
==========================================

Purpose
-------
Recompute cached Human Design type for every chart in db.charts using
the corrected `has_motor_to_throat()` BFS logic (May 2026 fix).  Pre-fix
caches incorrectly classified some Manifesting Generators as Generators
because motor-to-throat detection was direct-edge only.

Surgical scope
--------------
This migration ONLY re-runs the type classifier
(`determine_type(defined_centers, defined_channels)`) against the
existing cached `defined_centers` + `defined_channels` arrays.  It does
NOT recompute:
  - gates, centers, channels, profile, authority, definition
  - Sun/Earth labeling, Incarnation Cross naming
  - astronomy / numerology / bazi outputs
  - birth inputs (read-only)

Modes
-----
  dry_run:    scan + report, no writes
  apply:      write updates for changed records only

Per-document update payload (apply mode):
  human_design.type                       = <new_type>
  human_design.previous_type              = <old_type>
  human_design.type_migrated_at           = <utc datetime>
  human_design.type_migration_version     = "hd_motor_to_throat_bfs_v1"
  human_design.motor_to_throat            = <bool>       (informational)
  human_design.motor_to_throat_path       = "<path str>" (informational, when found)

Run
---
  cd /app/backend
  # dry run (default):
  python -m tests.run_hd_type_migration
  # apply:
  python -m tests.run_hd_type_migration --apply
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

# Ensure we can import calculations.*
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.dirname(THIS_DIR)
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from motor.motor_asyncio import AsyncIOMotorClient  # type: ignore

from calculations.human_design import (  # type: ignore
    has_motor_to_throat,
    determine_type,
    MOTOR_CENTERS,
)


MIGRATION_VERSION = "hd_motor_to_throat_bfs_v1"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize_channels(raw: Any) -> List[Tuple]:
    """Accept both tuple-shape and dict-shape channels; return tuples
    of `(gate1, gate2, center1, center2)` for the classifier."""
    out: List[Tuple] = []
    for c in raw or []:
        if isinstance(c, dict):
            g1 = c.get("gate1")
            g2 = c.get("gate2")
            cc = c.get("centers") or [c.get("center1"), c.get("center2")]
            if g1 is not None and g2 is not None and len(cc) >= 2 and cc[0] and cc[1]:
                out.append((g1, g2, cc[0], cc[1]))
        elif isinstance(c, (list, tuple)):
            try:
                g1, g2, c1, c2 = c
                if g1 is not None and g2 is not None and c1 and c2:
                    out.append((g1, g2, c1, c2))
            except ValueError:
                continue
    return out


def _motor_path_description(channels: List[Tuple]) -> Optional[str]:
    """If motor→Throat is reachable, return a short human-readable path
    string like 'Sacral →(2-14)→ G Center →(1-8)→ Throat'."""
    adjacency: Dict[str, List[Tuple[str, int, int]]] = {}
    for g1, g2, c1, c2 in channels:
        adjacency.setdefault(c1, []).append((c2, g1, g2))
        adjacency.setdefault(c2, []).append((c1, g1, g2))

    if "Throat" not in adjacency:
        return None

    # BFS from Throat back to a motor; carry path of (center, channel)
    from collections import deque
    visited = {"Throat"}
    queue: deque = deque([("Throat", [("Throat", None)])])
    while queue:
        cur, path = queue.popleft()
        for nb, g1, g2 in adjacency.get(cur, []):
            if nb in visited:
                continue
            new_path = path + [(nb, (g1, g2))]
            if nb in MOTOR_CENTERS:
                # Reverse: motor → ... → Throat
                segs = list(reversed(new_path))
                pieces: List[str] = []
                for i, (center, ch) in enumerate(segs):
                    if i == 0:
                        pieces.append(center)
                    else:
                        if ch is None:
                            pieces.append(f" → {center}")
                        else:
                            g1, g2 = ch
                            pieces.append(f" →({g1}-{g2})→ {center}")
                return "".join(pieces)
            visited.add(nb)
            queue.append((nb, new_path))
    return None


# ---------------------------------------------------------------------------
# Migration core
# ---------------------------------------------------------------------------

async def run_migration(*, apply: bool, mongo_url: str, db_name: str) -> Dict[str, Any]:
    cli = AsyncIOMotorClient(mongo_url)
    db = cli[db_name]

    scanned         = 0
    changed         = 0
    unchanged       = 0
    skipped         = 0
    skipped_reasons: Counter = Counter()
    written         = 0

    changes_sample: List[Dict[str, Any]] = []      # max 50 samples
    transition_counts: Counter = Counter()         # "Generator → MG" → N

    cursor = db.charts.find(
        {"human_design": {"$exists": True}},
        {
            "_id":            1,
            "user_id":        1,
            "human_design.type":              1,
            "human_design.defined_channels":  1,
            "human_design.defined_centers":   1,
            "human_design.profile":           1,
            "human_design.type_migration_version": 1,
        },
    )

    async for doc in cursor:
        scanned += 1
        hd = (doc or {}).get("human_design") or {}
        old_type = hd.get("type")
        channels_raw = hd.get("defined_channels")
        centers_raw  = hd.get("defined_centers")

        if not channels_raw or not centers_raw or not old_type:
            skipped += 1
            skipped_reasons["missing_hd_fields"] += 1
            continue

        try:
            channels = _normalize_channels(channels_raw)
            centers = list(centers_raw) if isinstance(centers_raw, (list, tuple)) else [centers_raw]
            new_type = determine_type(centers, channels)
            mtt = has_motor_to_throat(channels)
            mtt_path = _motor_path_description(channels) if mtt else None
        except Exception as e:
            import traceback
            skipped += 1
            skipped_reasons[f"recompute_error:{type(e).__name__}"] += 1
            if skipped_reasons[f"recompute_error:{type(e).__name__}"] <= 2:
                print(f"  [debug] error on user={doc.get('user_id')}: {type(e).__name__}: {e}")
                print(f"  [debug] traceback:\n{traceback.format_exc()[:500]}")
            continue

        if new_type == old_type:
            unchanged += 1
            continue

        # Type changed
        changed += 1
        transition_counts[f"{old_type} → {new_type}"] += 1
        if len(changes_sample) < 50:
            changes_sample.append({
                "user_id":  doc.get("user_id"),
                "chart_id": str(doc.get("_id")),
                "old_type": old_type,
                "new_type": new_type,
                "motor_to_throat":      mtt,
                "motor_to_throat_path": mtt_path,
            })

        if apply:
            try:
                update_doc = {
                    "$set": {
                        "human_design.type":                    new_type,
                        "human_design.previous_type":           old_type,
                        "human_design.type_migrated_at":        datetime.now(timezone.utc),
                        "human_design.type_migration_version":  MIGRATION_VERSION,
                        "human_design.motor_to_throat":         mtt,
                    },
                }
                if mtt_path:
                    update_doc["$set"]["human_design.motor_to_throat_path"] = mtt_path
                res = await db.charts.update_one({"_id": doc["_id"]}, update_doc)
                if res.modified_count:
                    written += 1
            except Exception as e:
                skipped_reasons[f"write_error:{type(e).__name__}"] += 1

    cli.close()

    return {
        "mode":              "apply" if apply else "dry_run",
        "scanned":           scanned,
        "changed":           changed,
        "unchanged":         unchanged,
        "skipped":           skipped,
        "written":           written,
        "skipped_reasons":   dict(skipped_reasons),
        "transition_counts": dict(transition_counts),
        "changes_sample":    changes_sample,
        "migration_version": MIGRATION_VERSION,
    }


# ---------------------------------------------------------------------------
# Validation (post-migration sanity check)
# ---------------------------------------------------------------------------

async def validate_known_users(mongo_url: str, db_name: str) -> Dict[str, Any]:
    cli = AsyncIOMotorClient(mongo_url)
    db = cli[db_name]
    results: Dict[str, Any] = {}
    for uid, name, expected in [
        ("697f0c6abf35c0528ff06954", "Pete",  "Manifestor"),
        ("697ec826ad4b18f75bf42616", "Mel",   "Reflector"),
    ]:
        doc = await db.charts.find_one({"user_id": uid})
        actual = ((doc or {}).get("human_design") or {}).get("type")
        results[name] = {
            "expected": expected,
            "actual":   actual,
            "pass":     actual == expected,
        }
    cli.close()
    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _print_report(report: Dict[str, Any]) -> None:
    print()
    print("=" * 72)
    print(f"HD TYPE MIGRATION — {report['mode'].upper()}  ({report['migration_version']})")
    print("=" * 72)
    print(f"  scanned   : {report['scanned']}")
    print(f"  changed   : {report['changed']}")
    print(f"  unchanged : {report['unchanged']}")
    print(f"  skipped   : {report['skipped']}")
    if report["mode"] == "apply":
        print(f"  written   : {report['written']}")
    if report["skipped_reasons"]:
        print(f"  skipped_reasons: {report['skipped_reasons']}")
    print()
    print("  Transitions:")
    for trans, n in sorted(
        report["transition_counts"].items(), key=lambda x: -x[1]
    ):
        print(f"    {trans:48s}  ×{n}")
    print()
    if report["changes_sample"]:
        print("  Sample changes (up to 50):")
        for s in report["changes_sample"][:25]:
            print(f"    user_id={s['user_id']}  "
                  f"chart={s['chart_id']}  "
                  f"{s['old_type']} → {s['new_type']}")
            if s.get("motor_to_throat_path"):
                print(f"      path: {s['motor_to_throat_path']}")
        if len(report["changes_sample"]) > 25:
            print(f"    ... and {len(report['changes_sample']) - 25} more")
    print("=" * 72)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply", action="store_true",
        help="Apply updates (default is dry-run).",
    )
    parser.add_argument(
        "--mongo-url",
        default=os.environ.get("MONGO_URL", "mongodb://localhost:27017"),
    )
    parser.add_argument(
        "--db-name", default=os.environ.get("DB_NAME", "test_database"),
    )
    args = parser.parse_args()

    # ---- DRY RUN (always first) ----
    print(">>> Running DRY RUN ...")
    dry = await run_migration(
        apply=False, mongo_url=args.mongo_url, db_name=args.db_name,
    )
    _print_report(dry)

    if not args.apply:
        print()
        print("Dry-run only. Re-run with --apply to write the updates above.")
        return

    if dry["changed"] == 0:
        print("Nothing to migrate. Exiting.")
        return

    # ---- APPLY ----
    print()
    print(">>> Applying migration ...")
    applied = await run_migration(
        apply=True, mongo_url=args.mongo_url, db_name=args.db_name,
    )
    _print_report(applied)

    # ---- Validation ----
    print()
    print(">>> Validating known users (Pete=Manifestor, Mel=Reflector):")
    val = await validate_known_users(args.mongo_url, args.db_name)
    for name, r in val.items():
        status = "✓" if r["pass"] else "✗"
        print(f"   {status} {name}: expected={r['expected']}  actual={r['actual']}")


if __name__ == "__main__":
    asyncio.run(main())
