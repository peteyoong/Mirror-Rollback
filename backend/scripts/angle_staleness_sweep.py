#!/usr/bin/env python3
"""
P0 — Angle Staleness Enumeration (READ-ONLY)
=============================================

Sweep the entire `charts` collection and enumerate angle / house-cusp
staleness relative to the currently deployed sign-attribution engine.

NO BACKFILL.  NO MUTATIONS.  NO RECOMPUTES.  ENUMERATION ONLY.

For every chart we:
  1. Read stored values for angles (asc, mc, dc, ic) and
     houses.formatted_cusps[0..11].
  2. Re-run the *current* attribute_sign(longitude + DEFAULT_AYANAMSA, mode)
     for the same longitude.
  3. Classify each stored value:
       OK         — sign matches live AND |Δdegree| < 1.0°
       STALE_LOW  — sign matches AND 1.0° ≤ |Δdegree| < 2.0°
       STALE_MED  — sign matches AND 2.0° ≤ |Δdegree| < 7.0°
       STALE_HIGH — sign matches AND |Δdegree| ≥ 7.0°
       OUT_OF_RANGE — stored degree ≥ 30°  (formally impossible for valid record)
       CRITICAL_SIGN_MISMATCH — stored sign != live sign  (factual mismatch)
       MISSING    — field absent / no longitude available
  4. Track per-chart top-level migration/version fields so we can answer
     "do all affected charts share a migration boundary?".
"""

import asyncio
import json
import os
import sys
import time
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Tuple

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

# Use the same routing as the live calculator.
from calculations.sign_attribution import (
    attribute_sign,
    DEFAULT_AYANAMSA,
    MODE_TRUE_SIDEREAL_MIDPOINT,
)

ANGLE_KEYS  = ("asc", "mc", "dc", "ic")
HOUSE_COUNT = 12

OUT_JSON = "/app/backend/audit_reports/ANGLE_STALENESS_SWEEP.json"
OUT_MD   = "/app/backend/audit_reports/ANGLE_STALENESS_SWEEP_REPORT.md"


def classify(stored_sign: Optional[str],
             stored_degree: Optional[float],
             stored_longitude: Optional[float]) -> Dict[str, Any]:
    """Pure read; never writes; never recomputes a chart."""
    if stored_sign is None and stored_degree is None and stored_longitude is None:
        return {"verdict": "MISSING", "reason": "no stored sign/degree/longitude"}

    # Formal validity check first.
    formal_out_of_range = (stored_degree is not None and stored_degree >= 30.0)

    if stored_longitude is None:
        return {
            "verdict": "OUT_OF_RANGE" if formal_out_of_range else "MISSING",
            "reason": (f"stored_degree={stored_degree:.4f} ≥ 30"
                       if formal_out_of_range
                       else "no longitude to recompute against"),
            "stored": {"sign": stored_sign, "degree": stored_degree},
            "live":   None,
            "delta_degree": None,
        }

    trop = (stored_longitude + DEFAULT_AYANAMSA) % 360.0
    live = attribute_sign(trop, mode=MODE_TRUE_SIDEREAL_MIDPOINT)
    live_sign = live["sign"]
    live_deg  = float(live["degree_within_sign"])

    if stored_sign != live_sign:
        return {
            "verdict": "CRITICAL_SIGN_MISMATCH",
            "reason": f"stored sign={stored_sign!r} but live engine says {live_sign!r}",
            "stored": {"sign": stored_sign, "degree": stored_degree,
                       "longitude": stored_longitude},
            "live":   {"sign": live_sign, "degree": live_deg,
                       "sign_start": live.get("sign_start"),
                       "sign_end":   live.get("sign_end"),
                       "engine_version": live.get("engine_version")},
            "delta_degree": None,
        }

    # Same sign — measure Δdegree.
    if formal_out_of_range:
        # We *also* want to surface this even when sign matches.
        verdict = "OUT_OF_RANGE"
    else:
        if stored_degree is None:
            verdict = "STALE_HIGH"  # can't measure but sign matches
            d = None
        else:
            d = abs(stored_degree - live_deg)
            if   d < 1.0: verdict = "OK"
            elif d < 2.0: verdict = "STALE_LOW"
            elif d < 7.0: verdict = "STALE_MED"
            else:         verdict = "STALE_HIGH"
    d = (abs(stored_degree - live_deg)
         if stored_degree is not None else None)
    return {
        "verdict": verdict,
        "reason": (
            f"Δdeg={d:.2f}° (stored={stored_degree:.2f}°, live={live_deg:.2f}°)"
            if d is not None else
            f"stored degree missing; live sign matches ({live_sign})"
        ),
        "stored": {"sign": stored_sign, "degree": stored_degree,
                   "longitude": stored_longitude},
        "live":   {"sign": live_sign, "degree": live_deg,
                   "sign_start": live.get("sign_start"),
                   "sign_end":   live.get("sign_end"),
                   "engine_version": live.get("engine_version")},
        "delta_degree": d,
    }


def collect_angle_data(astrology: Dict[str, Any]) -> Dict[str, Any]:
    """Extract a normalised view of all angles + house cusps from one chart."""
    out: Dict[str, Any] = {"angles": {}, "house_cusps": []}
    angles_doc = (astrology or {}).get("angles") or {}
    for k in ANGLE_KEYS:
        doc = angles_doc.get(k) or {}
        out["angles"][k] = {
            "sign":      doc.get("sign"),
            "degree":    doc.get("degree"),
            "longitude": doc.get("longitude"),
            "formatted": doc.get("formatted"),
        }
    houses = (astrology or {}).get("houses") or {}
    cusps  = houses.get("formatted_cusps") or []
    for i in range(HOUSE_COUNT):
        if i < len(cusps):
            c = cusps[i]
            if not isinstance(c, dict):
                # Legacy format: cusp stored as string like "23°Virgo".
                out["house_cusps"].append({
                    "house":     i + 1,
                    "sign":      None,
                    "degree":    None,
                    "longitude": None,
                    "formatted": c if isinstance(c, str) else None,
                    "_legacy_string_format": True,
                })
                continue
            out["house_cusps"].append({
                "house":     i + 1,
                "sign":      c.get("sign"),
                "degree":    c.get("degree"),
                "longitude": c.get("cusp") or c.get("longitude"),
                "formatted": c.get("formatted"),
            })
        else:
            out["house_cusps"].append({
                "house": i + 1, "sign": None, "degree": None,
                "longitude": None, "formatted": None,
            })
    return out


async def main() -> int:
    c = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = c[os.environ["DB_NAME"]]
    print(f"[sweep] starting against {os.environ['DB_NAME']}", flush=True)

    per_chart: List[Dict[str, Any]] = []
    cursor = db.charts.find({})

    total = 0
    async for ch in cursor:
        total += 1
        astrology  = ch.get("astrology") or {}
        chart_id   = str(ch.get("_id"))
        user_id    = ch.get("user_id")
        created_at = ch.get("calculated_at") or ch.get("created_at")
        migrated_at = ch.get("migrated_at")
        eng_ver    = ch.get("astrology_engine_version")
        sign_attr_ver = ch.get("sign_attribution_version")
        mig_marker = ch.get("migration_marker")
        audit_keys = sorted(list((ch.get("zodiac_migration_audit") or {}).keys()))

        data = collect_angle_data(astrology)

        # Classify each angle.
        angle_classes: Dict[str, Any] = {}
        for k in ANGLE_KEYS:
            d = data["angles"][k]
            angle_classes[k] = classify(d["sign"], d["degree"], d["longitude"])

        # Classify each house cusp.
        house_classes: List[Dict[str, Any]] = []
        for hc in data["house_cusps"]:
            r = classify(hc["sign"], hc["degree"], hc["longitude"])
            r["house"] = hc["house"]
            house_classes.append(r)

        # Worst per-chart verdict (priority order).
        VERDICT_RANK = {
            "OK": 0,
            "MISSING": 0,
            "STALE_LOW": 1,
            "STALE_MED": 2,
            "STALE_HIGH": 3,
            "OUT_OF_RANGE": 4,
            "CRITICAL_SIGN_MISMATCH": 5,
        }
        all_verdicts = [angle_classes[k]["verdict"] for k in ANGLE_KEYS] + \
                       [h["verdict"] for h in house_classes]
        worst = max(all_verdicts, key=lambda v: VERDICT_RANK.get(v, 0))
        worst_rank = VERDICT_RANK.get(worst, 0)

        per_chart.append({
            "chart_id": chart_id,
            "user_id":  user_id,
            "calculated_at": str(created_at) if created_at else None,
            "migrated_at":   str(migrated_at) if migrated_at else None,
            "astrology_engine_version":  eng_ver,
            "sign_attribution_version":  sign_attr_ver,
            "migration_marker":          mig_marker,
            "zodiac_migration_audit_keys": audit_keys,
            "worst_verdict": worst,
            "worst_rank":    worst_rank,
            "angle_verdicts": {k: angle_classes[k]["verdict"] for k in ANGLE_KEYS},
            "angle_deltas":   {k: angle_classes[k].get("delta_degree")
                               for k in ANGLE_KEYS},
            "house_cusp_verdicts": [h["verdict"] for h in house_classes],
            "house_cusp_deltas":   [h.get("delta_degree") for h in house_classes],
            # detail blocks (kept verbose so we don't lose info)
            "angle_detail": angle_classes,
            "house_cusp_detail": house_classes,
        })

    print(f"[sweep] scanned {total} charts", flush=True)

    # -------------------------------------------------------------- aggregates
    affected = [p for p in per_chart if p["worst_rank"] >= 1]   # anything not OK/MISSING
    affected_count = len(affected)
    pct_affected = (100.0 * affected_count / total) if total else 0.0

    # Per-field verdict counts.
    field_counts: Dict[str, Counter] = {
        "asc": Counter(), "mc": Counter(), "dc": Counter(), "ic": Counter(),
        **{f"house_{i+1}": Counter() for i in range(HOUSE_COUNT)},
    }
    for p in per_chart:
        for k in ANGLE_KEYS:
            field_counts[k][p["angle_verdicts"][k]] += 1
        for i, v in enumerate(p["house_cusp_verdicts"]):
            field_counts[f"house_{i+1}"][v] += 1

    # Worst-verdict distribution at chart level.
    worst_dist = Counter(p["worst_verdict"] for p in per_chart)

    # Earliest / latest affected.
    affected_with_date = [p for p in affected if p.get("calculated_at")]
    affected_with_date.sort(key=lambda p: p["calculated_at"])
    earliest = affected_with_date[0] if affected_with_date else None
    latest   = affected_with_date[-1] if affected_with_date else None

    # Version breakdown: cross-tab worst_verdict by (engine_version, sign_attr_version, migration_marker)
    version_cross = defaultdict(lambda: Counter())
    for p in per_chart:
        key = (p["astrology_engine_version"],
               p["sign_attribution_version"],
               p["migration_marker"])
        version_cross[key][p["worst_verdict"]] += 1

    # Creation-date buckets (year-month).
    date_bucket: Dict[str, Counter] = defaultdict(lambda: Counter())
    for p in per_chart:
        ca = p.get("calculated_at") or ""
        ym = ca[:7] if isinstance(ca, str) and len(ca) >= 7 else "unknown"
        date_bucket[ym][p["worst_verdict"]] += 1

    # Severity counts at field level.
    severity = Counter()
    for p in per_chart:
        severity.update(p["angle_verdicts"].values())
        severity.update(p["house_cusp_verdicts"])

    summary = {
        "generated_at_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "db_name": os.environ.get("DB_NAME"),
        "total_charts": total,
        "affected_charts": affected_count,
        "pct_affected": round(pct_affected, 2),
        "worst_verdict_distribution_chart_level": dict(worst_dist),
        "field_level_counts": {
            k: dict(v) for k, v in field_counts.items()
        },
        "severity_counts_all_fields": dict(severity),
        "earliest_affected": {
            "chart_id": earliest["chart_id"],
            "user_id":  earliest["user_id"],
            "calculated_at": earliest["calculated_at"],
            "worst_verdict": earliest["worst_verdict"],
        } if earliest else None,
        "latest_affected": {
            "chart_id": latest["chart_id"],
            "user_id":  latest["user_id"],
            "calculated_at": latest["calculated_at"],
            "worst_verdict": latest["worst_verdict"],
        } if latest else None,
        "version_cross_tab": [
            {
                "astrology_engine_version": k[0],
                "sign_attribution_version": k[1],
                "migration_marker":         k[2],
                "verdicts": dict(v),
                "total":   sum(v.values()),
            }
            for k, v in sorted(version_cross.items(),
                               key=lambda kv: -sum(kv[1].values()))
        ],
        "date_bucket": {
            ym: dict(v) for ym, v in sorted(date_bucket.items())
        },
    }

    out = {
        "summary": summary,
        "per_chart": per_chart,
    }
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"[sweep] wrote {OUT_JSON}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
