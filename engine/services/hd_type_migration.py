"""
HD Type Startup Migration — motor_to_throat BFS v1
==================================================

Production-safe one-shot migration. Runs at backend startup. Idempotent.

Purpose
-------
After the May 2026 motor-to-throat BFS fix to
`calculations.human_design.has_motor_to_throat`, cached chart documents
in `db.charts` may still carry the pre-fix `human_design.type` value
(e.g. "Generator" where the new BFS would yield "Manifesting Generator"
via an indirect motor → bridge center → Throat path).

This migration recomputes `human_design.type` from the *cached*
`defined_centers` + `defined_channels` arrays (no astrology / numerology
/ BaZi / Sun-Earth labeling / Incarnation Cross recompute) and writes
audit fields when the type changes.

Idempotency
-----------
Every chart processed in this run — even when unchanged — receives a
`human_design.type_migration_version = "hd_motor_to_throat_bfs_v1"`
stamp. Future startup invocations filter on
`type_migration_version != "hd_motor_to_throat_bfs_v1"` so already
migrated charts are skipped O(1) via the index scan.

Safety
------
- All exceptions in per-doc loops are caught and counted as `failed`.
- The outer caller wraps this in another try/except so backend startup
  cannot crash regardless of migration state.
- Birth data, astrology, BaZi, numerology, timeline, Sun/Earth labels,
  Incarnation Crosses, and sidereal constants are NEVER touched.

Run modes
---------
- Called from `server.py` `_safe_run_migrations()` background task at
  startup (production self-heal).
- Also callable from CLI: `python -m tests.run_hd_type_migration --apply`
  (preview / dev / one-off ops).
"""

from __future__ import annotations

import logging as _logging
from collections import Counter, deque
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from calculations.human_design import (  # type: ignore
    MOTOR_CENTERS,
    determine_type,
    has_motor_to_throat,
)

MIGRATION_VERSION = "hd_motor_to_throat_bfs_v1"


# ---------------------------------------------------------------------------
# Channel normalization (tuple OR dict shape both supported)
# ---------------------------------------------------------------------------

def _normalize_channels(raw: Any) -> List[Tuple]:
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
    """Return short readable path 'Sacral →(8-1)→ G Center → Throat'."""
    adjacency: Dict[str, List[Tuple[str, int, int]]] = {}
    for g1, g2, c1, c2 in channels:
        adjacency.setdefault(c1, []).append((c2, g1, g2))
        adjacency.setdefault(c2, []).append((c1, g1, g2))

    if "Throat" not in adjacency:
        return None

    visited = {"Throat"}
    queue: deque = deque([("Throat", [("Throat", None)])])
    while queue:
        cur, path = queue.popleft()
        for nb, g1, g2 in adjacency.get(cur, []):
            if nb in visited:
                continue
            new_path = path + [(nb, (g1, g2))]
            if nb in MOTOR_CENTERS:
                segs = list(reversed(new_path))
                pieces: List[str] = []
                for i, (center, ch) in enumerate(segs):
                    if i == 0:
                        pieces.append(center)
                    else:
                        if ch is None:
                            pieces.append(f" → {center}")
                        else:
                            cg1, cg2 = ch
                            pieces.append(f" →({cg1}-{cg2})→ {center}")
                return "".join(pieces)
            visited.add(nb)
            queue.append((nb, new_path))
    return None


# ---------------------------------------------------------------------------
# Core migration
# ---------------------------------------------------------------------------

async def run_hd_type_startup_migration(
    db,
    *,
    logger: Optional[_logging.Logger] = None,
    stamp_unchanged: bool = True,
    max_sample: int = 20,
) -> Dict[str, Any]:
    """
    Run the HD-type migration against `db.charts`.

    Args:
        db: motor AsyncIOMotorDatabase instance.
        logger: optional logger; falls back to module logger.
        stamp_unchanged: if True (default), even charts whose recomputed
            type matches the cached type receive a
            `type_migration_version` stamp so they are skipped on
            future startup runs (true idempotency).
        max_sample: max number of changed records to include in the
            sample list in the returned report.

    Returns:
        Report dict:
            {
              "version", "scanned", "migrated", "unchanged",
              "skipped", "failed", "transitions": {...},
              "sample": [...]
            }
    """
    log = logger or _logging.getLogger("hd_type_migration")

    scanned = 0
    migrated = 0
    unchanged = 0
    skipped = 0
    failed = 0
    transitions: Counter = Counter()
    skipped_reasons: Counter = Counter()
    sample: List[Dict[str, Any]] = []

    # Idempotency filter — only scan docs that don't already carry the
    # current migration stamp.
    query = {
        "human_design": {"$exists": True},
        "human_design.type_migration_version": {"$ne": MIGRATION_VERSION},
    }
    projection = {
        "_id": 1,
        "user_id": 1,
        "human_design.type": 1,
        "human_design.defined_channels": 1,
        "human_design.defined_centers": 1,
    }

    cursor = db.charts.find(query, projection)

    async for doc in cursor:
        scanned += 1
        hd = (doc or {}).get("human_design") or {}
        old_type = hd.get("type")
        channels_raw = hd.get("defined_channels")
        centers_raw = hd.get("defined_centers")

        if not channels_raw or not centers_raw or not old_type:
            skipped += 1
            skipped_reasons["missing_hd_fields"] += 1
            continue

        try:
            channels = _normalize_channels(channels_raw)
            centers = (
                list(centers_raw)
                if isinstance(centers_raw, (list, tuple))
                else [centers_raw]
            )
            new_type = determine_type(centers, channels)
            mtt = has_motor_to_throat(channels)
            mtt_path = _motor_path_description(channels) if mtt else None
        except Exception as e:  # noqa: BLE001 — per-doc safety
            failed += 1
            skipped_reasons[f"recompute_error:{type(e).__name__}"] += 1
            log.warning(
                "[HD-Migration] recompute error user=%s err=%s: %s",
                doc.get("user_id"), type(e).__name__, e,
            )
            continue

        if new_type == old_type:
            unchanged += 1
            # Stamp version so this doc is not re-scanned next startup.
            if stamp_unchanged:
                try:
                    await db.charts.update_one(
                        {"_id": doc["_id"]},
                        {"$set": {
                            "human_design.type_migration_version": MIGRATION_VERSION,
                            "human_design.motor_to_throat": mtt,
                            **({"human_design.motor_to_throat_path": mtt_path}
                               if mtt_path else {}),
                        }},
                    )
                except Exception as e:  # noqa: BLE001
                    failed += 1
                    skipped_reasons[f"stamp_error:{type(e).__name__}"] += 1
            continue

        # Type changed — write full audit payload
        try:
            update_doc = {
                "$set": {
                    "human_design.type": new_type,
                    "human_design.previous_type": old_type,
                    "human_design.type_migrated_at": datetime.now(timezone.utc),
                    "human_design.type_migration_version": MIGRATION_VERSION,
                    "human_design.motor_to_throat": mtt,
                },
            }
            if mtt_path:
                update_doc["$set"]["human_design.motor_to_throat_path"] = mtt_path
            res = await db.charts.update_one({"_id": doc["_id"]}, update_doc)
            if res.modified_count:
                migrated += 1
                transitions[f"{old_type} → {new_type}"] += 1
                if len(sample) < max_sample:
                    sample.append({
                        "user_id": doc.get("user_id"),
                        "chart_id": str(doc.get("_id")),
                        "old_type": old_type,
                        "new_type": new_type,
                        "motor_to_throat": mtt,
                        "motor_to_throat_path": mtt_path,
                    })
        except Exception as e:  # noqa: BLE001
            failed += 1
            skipped_reasons[f"write_error:{type(e).__name__}"] += 1
            log.warning(
                "[HD-Migration] write error user=%s err=%s: %s",
                doc.get("user_id"), type(e).__name__, e,
            )

    return {
        "version": MIGRATION_VERSION,
        "scanned": scanned,
        "migrated": migrated,
        "unchanged": unchanged,
        "skipped": skipped,
        "failed": failed,
        "transitions": dict(transitions),
        "skipped_reasons": dict(skipped_reasons),
        "sample": sample,
    }


def format_report(report: Dict[str, Any]) -> str:
    """Pretty-format a report dict for log output."""
    lines = [
        "[HD-Migration] " + ("=" * 56),
        f"[HD-Migration] HD TYPE MIGRATION REPORT ({report['version']})",
        f"[HD-Migration]   scanned   : {report['scanned']}",
        f"[HD-Migration]   migrated  : {report['migrated']}",
        f"[HD-Migration]   unchanged : {report['unchanged']}",
        f"[HD-Migration]   skipped   : {report['skipped']}",
        f"[HD-Migration]   failed    : {report['failed']}",
    ]
    if report.get("transitions"):
        lines.append("[HD-Migration]   transitions:")
        for tr, n in sorted(
            report["transitions"].items(), key=lambda x: -x[1]
        ):
            lines.append(f"[HD-Migration]     {tr:48s} ×{n}")
    if report.get("skipped_reasons"):
        lines.append(f"[HD-Migration]   skipped_reasons: {report['skipped_reasons']}")
    if report.get("sample"):
        lines.append("[HD-Migration]   sample changed records:")
        for s in report["sample"][:10]:
            lines.append(
                f"[HD-Migration]     user_id={s.get('user_id')} "
                f"{s.get('old_type')} → {s.get('new_type')}"
            )
            if s.get("motor_to_throat_path"):
                lines.append(f"[HD-Migration]       path: {s['motor_to_throat_path']}")
    lines.append("[HD-Migration] " + ("=" * 56))
    return "\n".join(lines)
