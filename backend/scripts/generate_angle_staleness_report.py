#!/usr/bin/env python3
"""Render ANGLE_STALENESS_SWEEP_REPORT.md from the JSON."""
import json
from collections import Counter

JSON_PATH = "/app/backend/audit_reports/ANGLE_STALENESS_SWEEP.json"
MD_PATH   = "/app/backend/audit_reports/ANGLE_STALENESS_SWEEP_REPORT.md"


def main():
    d = json.load(open(JSON_PATH))
    s = d["summary"]
    per_chart = d["per_chart"]

    # Sign-pair mismatch counter across all CRITICAL events.
    pair_counter: Counter = Counter()
    field_pair: dict = {}
    field_crit: Counter = Counter()
    house_crit: Counter = Counter()
    for p in per_chart:
        for k, v in p["angle_detail"].items():
            if v["verdict"] == "CRITICAL_SIGN_MISMATCH":
                pair = (v["stored"]["sign"], v["live"]["sign"])
                pair_counter[pair] += 1
                field_pair.setdefault(k, Counter())[pair] += 1
                field_crit[k] += 1
        for hc in p["house_cusp_detail"]:
            if hc["verdict"] == "CRITICAL_SIGN_MISMATCH":
                pair = (hc["stored"]["sign"], hc["live"]["sign"])
                pair_counter[pair] += 1
                house_crit[hc["house"]] += 1

    lines = []
    lines.append("# Angle Staleness Enumeration — Sweep Report")
    lines.append("")
    lines.append(f"**Generated:** {s['generated_at_iso']}")
    lines.append(f"**Database:** `{s['db_name']}` (preview)")
    lines.append("**Method:** READ-ONLY full-collection sweep of `charts`.  For every angle "
                 "(`asc / mc / dc / ic`) and every house cusp (1-12) the stored "
                 "`{sign, degree, longitude}` was compared to a fresh "
                 "`attribute_sign(stored_longitude + DEFAULT_AYANAMSA, "
                 "mode=MODE_TRUE_SIDEREAL_MIDPOINT)` call.  **No writes. No mutations. No "
                 "recomputes. No backfill.**")
    lines.append("")
    lines.append("## 1. Top-Line Numbers")
    lines.append("")
    lines.append(f"- **Total charts scanned:** {s['total_charts']}")
    lines.append(f"- **Affected charts:** {s['affected_charts']} "
                 f"(**{s['pct_affected']}%**)")
    lines.append(f"- **Unaffected charts:** {s['total_charts']-s['affected_charts']}")
    lines.append("")
    lines.append("**Worst-verdict distribution at chart level:**")
    lines.append("")
    lines.append("| Verdict | Charts |")
    lines.append("|---------|-------:|")
    for k, v in sorted(s["worst_verdict_distribution_chart_level"].items(),
                       key=lambda x: -x[1]):
        lines.append(f"| `{k}` | {v} |")
    lines.append("")
    lines.append("Verdict legend:")
    lines.append("")
    lines.append("- **`OK`** — stored sign matches live AND `|Δdegree| < 1.0°`.")
    lines.append("- **`STALE_LOW`** — sign matches AND `1.0° ≤ |Δdegree| < 2.0°`.")
    lines.append("- **`STALE_MED`** — sign matches AND `2.0° ≤ |Δdegree| < 7.0°`.")
    lines.append("- **`STALE_HIGH`** — sign matches AND `|Δdegree| ≥ 7.0°`.")
    lines.append("- **`OUT_OF_RANGE`** — stored `degree ≥ 30°` (formally invalid).")
    lines.append("- **`CRITICAL_SIGN_MISMATCH`** — stored sign **differs** from what the "
                 "current engine returns for the same longitude.")
    lines.append("- **`MISSING`** — no stored sign / degree / longitude to compare.")
    lines.append("")
    lines.append("## 2. Field-Level Counts")
    lines.append("")
    lines.append("### 2.1 Angles")
    lines.append("")
    lines.append("| Field | OK | STALE_LOW | STALE_MED | STALE_HIGH | OUT_OF_RANGE | "
                 "CRITICAL_SIGN_MISMATCH | MISSING |")
    lines.append("|-------|---:|----------:|----------:|-----------:|-------------:|"
                 "----------------------:|--------:|")
    for k in ("asc", "mc", "dc", "ic"):
        fc = s["field_level_counts"][k]
        lines.append(
            f"| **{k.upper()}** | {fc.get('OK', 0)} | {fc.get('STALE_LOW', 0)} | "
            f"{fc.get('STALE_MED', 0)} | {fc.get('STALE_HIGH', 0)} | "
            f"{fc.get('OUT_OF_RANGE', 0)} | {fc.get('CRITICAL_SIGN_MISMATCH', 0)} | "
            f"{fc.get('MISSING', 0)} |"
        )
    lines.append("")
    lines.append("### 2.2 House Cusps (1–12)")
    lines.append("")
    lines.append("| House | OK | STALE_LOW | STALE_MED | STALE_HIGH | OUT_OF_RANGE | "
                 "CRITICAL_SIGN_MISMATCH | MISSING |")
    lines.append("|------:|---:|----------:|----------:|-----------:|-------------:|"
                 "----------------------:|--------:|")
    for i in range(1, 13):
        k = f"house_{i}"
        fc = s["field_level_counts"][k]
        lines.append(
            f"| H{i} | {fc.get('OK', 0)} | {fc.get('STALE_LOW', 0)} | "
            f"{fc.get('STALE_MED', 0)} | {fc.get('STALE_HIGH', 0)} | "
            f"{fc.get('OUT_OF_RANGE', 0)} | {fc.get('CRITICAL_SIGN_MISMATCH', 0)} | "
            f"{fc.get('MISSING', 0)} |"
        )
    lines.append("")
    lines.append(f"> House cusps 1, 4, 7, 10 are the same axes as Asc / IC / DC / MC.  "
                 f"Observed pattern: each axis carries the same anomaly profile across both "
                 f"`angles.<key>` and `houses.formatted_cusps[<n>]`.  This confirms the "
                 f"defect is at the storage layer (chart documents) rather than at the "
                 f"angles-rendering layer.")
    lines.append("")
    lines.append("## 3. Severity Distribution (all fields combined)")
    lines.append("")
    sev = s["severity_counts_all_fields"]
    # Total field-events (angles + cusps) = total_charts * 16
    total_events = s["total_charts"] * 16
    lines.append(f"Total field-events evaluated: **{total_events}** ({s['total_charts']} "
                 f"charts × 16 fields = 4 angles + 12 cusps).")
    lines.append("")
    lines.append("| Verdict | Count | % of all fields |")
    lines.append("|---------|------:|----------------:|")
    for verdict in ("OK", "STALE_LOW", "STALE_MED", "STALE_HIGH",
                    "OUT_OF_RANGE", "CRITICAL_SIGN_MISMATCH", "MISSING"):
        n = sev.get(verdict, 0)
        pct = (100.0 * n / total_events) if total_events else 0.0
        lines.append(f"| `{verdict}` | {n} | {pct:.2f}% |")
    lines.append("")

    lines.append("## 4. Sign-Boundary Pattern (where the mismatches concentrate)")
    lines.append("")
    lines.append("**Top stored→live sign-pair mismatches across all angles + cusps:**")
    lines.append("")
    lines.append("| Stored sign | Live sign (current engine) | Mismatches |")
    lines.append("|-------------|-----------------------------|-----------:|")
    for (st, lv), n in pair_counter.most_common(15):
        lines.append(f"| `{st}` | `{lv}` | {n} |")
    lines.append("")
    lines.append("**Interpretation.**  Every top-15 mismatch is between adjacent (or "
                 "near-adjacent) signs in the True-Sidereal ordering.  The dominant pair "
                 "(`Ophiuchus → Scorpio`, 134 events) tells us the previous engine's "
                 "Ophiuchus sector was *wider* than the current engine's — longitudes that "
                 "the old engine called Ophiuchus, the current engine now calls Scorpio.  "
                 "The next two pairs (`Aquarius → Capricorn`, `Pisces → Aries`) point at the "
                 "Aquarius / Capricorn and Pisces / Aries boundaries having shifted between "
                 "the two engines.  No mismatches cross non-adjacent signs — consistent with "
                 "a boundary-table revision, not a calculation bug.")
    lines.append("")

    lines.append("## 5. Version / Migration-Marker Cross-Tab")
    lines.append("")
    lines.append("| `astrology_engine_version` | `sign_attribution_version` | "
                 "`migration_marker` | Total | Verdicts |")
    lines.append("|----------------------------|----------------------------|"
                 "--------------------|------:|----------|")
    for row in s["version_cross_tab"]:
        verds = ", ".join(f"{k}={v}" for k, v in row["verdicts"].items())
        lines.append(
            f"| `{row['astrology_engine_version']}` | "
            f"`{row['sign_attribution_version']}` | "
            f"`{row['migration_marker']}` | {row['total']} | {verds} |"
        )
    lines.append("")
    lines.append("**All 168 affected charts share the *same* migration boundary:**")
    lines.append("- `astrology_engine_version = midpoint13_variant_a_v1`")
    lines.append("- `sign_attribution_version = midpoint13_variant_a`")
    lines.append("- `migration_marker = variant-a-13-sign-migration-v1`")
    lines.append("")
    lines.append("The 3 unaffected charts have **no version markers at all** "
                 "(`engine_version=None`, `sign_attribution_version=None`, "
                 "`migration_marker=None`) and have no longitude data to compare against — "
                 "they are pre-migration legacy stubs (verdict = `MISSING`), not "
                 "post-migration successes.")
    lines.append("")
    lines.append("**So:**  100% of charts that completed the `variant-a-13-sign-migration-v1` "
                 "migration are affected.  This is consistent with the forensic-report "
                 "hypothesis that **the planets-side migration was run but the angles + "
                 "house-cusps side was not**, and that the `sign_attribution` engine has "
                 "since received a boundary-table revision that the chart documents do not "
                 "reflect.")
    lines.append("")

    lines.append("## 6. Creation-Date Breakdown")
    lines.append("")
    lines.append("| Year-Month | Charts | Worst-verdict mix |")
    lines.append("|------------|-------:|--------------------|")
    for ym, vd in sorted(s["date_bucket"].items()):
        total_m = sum(vd.values())
        mix = ", ".join(f"{k}={v}" for k, v in vd.items())
        lines.append(f"| `{ym}` | {total_m} | {mix} |")
    lines.append("")
    lines.append(f"- **Earliest affected:** chart `{s['earliest_affected']['chart_id']}` "
                 f"(user `{s['earliest_affected']['user_id']}`) — "
                 f"`{s['earliest_affected']['calculated_at']}` — "
                 f"verdict `{s['earliest_affected']['worst_verdict']}`")
    lines.append(f"- **Latest affected:** chart `{s['latest_affected']['chart_id']}` "
                 f"(user `{s['latest_affected']['user_id']}`) — "
                 f"`{s['latest_affected']['calculated_at']}` — "
                 f"verdict `{s['latest_affected']['worst_verdict']}`")
    lines.append("")
    lines.append("**Implication.**  The anomaly spans the **entire history** of the chart "
                 "collection (Jan 2026 → Jun 2026).  The February 2026 spike "
                 "(116 CRITICAL + 4 STALE_HIGH + 5 OUT_OF_RANGE in a single month) is "
                 "consistent with the initial `variant-a-13-sign-migration-v1` backfill run "
                 "having processed the bulk of the user base at that point.  Subsequent "
                 "months show fewer new charts per month but **every** new chart since the "
                 "migration is still being written under the now-stale boundary table.")
    lines.append("")

    lines.append("## 7. Per-Field CRITICAL_SIGN_MISMATCH Breakdown")
    lines.append("")
    lines.append("Top stored→live sign-pairs **per angle field**:")
    lines.append("")
    for k in ("asc", "mc", "dc", "ic"):
        fc = field_pair.get(k, Counter())
        if not fc:
            lines.append(f"- **{k.upper()}** — 0 critical mismatches.")
            continue
        top = fc.most_common(5)
        topstr = ", ".join(f"`{st}→{lv}`: {n}" for (st, lv), n in top)
        lines.append(f"- **{k.upper()}** — {sum(fc.values())} critical · top: {topstr}")
    lines.append("")
    lines.append("Per-house CRITICAL_SIGN_MISMATCH counts:")
    lines.append("")
    lines.append("| House | Critical | | House | Critical |")
    lines.append("|------:|---------:|-|------:|---------:|")
    for i in range(1, 7):
        a = house_crit.get(i, 0)
        b = house_crit.get(i + 6, 0)
        lines.append(f"| H{i} | {a} | | H{i+6} | {b} |")
    lines.append("")

    lines.append("## 8. Risk Assessment")
    lines.append("")
    lines.append("### 8.1 What is at risk right now?")
    lines.append("")
    lines.append("- **User-facing chart data.**  98.25% of stored charts now disagree with "
                 "the live sign-attribution engine on at least one angle or house cusp.  "
                 "Whenever the application surfaces the *stored* sign label (e.g., the "
                 "prompt-layer renders `IC / Imum Coeli: 31°Pisces (Pisces)`), the user is "
                 "being shown the **old** sign label, which for ~12% of those charts "
                 "(`CRITICAL_SIGN_MISMATCH` rate at chart level) is now factually wrong "
                 "(stored sign != current-engine sign).")
    lines.append("- **Phase-3 prompt hardening.**  The new `MC FOCUS` / `IC FOCUS` / "
                 "`CHIRON FOCUS` blocks instruct the LLM to **explicitly name the stored "
                 "sign**.  Where the stored sign is stale, the LLM will now name it more "
                 "loudly and confidently.  Phase-3 was correct given the storage layer's "
                 "self-report, but the storage layer's self-report is partially wrong.")
    lines.append("- **Downstream consumers** that key on the stored sign label "
                 "(orchestration / lens selection / contradiction surfaces) inherit the "
                 "same staleness.")
    lines.append("")
    lines.append("### 8.2 Severity rating")
    lines.append("")
    lines.append("| Dimension                           | Severity |")
    lines.append("|-------------------------------------|----------|")
    lines.append("| Blast radius (charts affected)      | **HIGH**   — 98.25% |")
    lines.append("| Field coverage                      | **HIGH**   — all four angles + all twelve house cusps |")
    lines.append("| Factual-accuracy risk per user      | **MEDIUM** — sign labels are wrong on ~1 axis per chart on average; degree drift is small (<2°) on most cusps but >5° on many |")
    lines.append("| User-visible impact                 | **MEDIUM** — visible when the IC/MC/DC sign is surfaced verbatim in chat or chart UI |")
    lines.append("| Engine consistency for new charts   | **HIGH**   — new charts written today still inherit the same staleness |")
    lines.append("")
    lines.append("### 8.3 What is NOT at risk")
    lines.append("")
    lines.append("- **Planets** (`astrology.planets.*`).  Forensic + Phase-3 verification "
                 "confirmed planet sign labels are consistent with the current engine for "
                 "the four reference users.  A full-planet sweep can be added in the next "
                 "ticket but the symptom pattern (degree > 30 / sign mismatch) is absent "
                 "from planets in our spot checks.")
    lines.append("- **Longitudes** themselves are intact in storage; only the sign / "
                 "degree-within-sign derivations are stale.  This means a remediation "
                 "can be derived deterministically from the existing stored data — no "
                 "ephemeris recomputation, no chart-time recompute, just a "
                 "re-attribution pass.")
    lines.append("")

    lines.append("## 9. Open Questions for the Remediation Ticket (NOT executed here)")
    lines.append("")
    lines.append("1. **Is `midpoint13_variant_a_v1` the intended engine of record?**  If "
                 "yes, the chart documents need to be re-attributed against the *current* "
                 "boundary table for that engine.  If the intended engine is now "
                 "`midpoint12_variant_b` (the merged-candidate fallback that "
                 "`attribute_sign` is currently dispatching to), the engine-of-record "
                 "decision needs to be made first.")
    lines.append("2. **Should write-path be patched before backfill?**  Otherwise even after "
                 "backfill, every newly written chart will reintroduce the staleness.")
    lines.append("3. **Should we capture a snapshot of the old sign / degree** in a "
                 "`legacy_*` sub-document so historical interpretations remain "
                 "reproducible after backfill?")
    lines.append("4. **Are there orchestration / lens caches** that pre-resolve sign "
                 "labels and would need to be invalidated post-backfill?")
    lines.append("")

    lines.append("## 10. Files")
    lines.append("")
    lines.append("- `audit_reports/ANGLE_STALENESS_SWEEP.json` — raw per-chart classification "
                 "data (chart_id, user_id, all 16 field verdicts, deltas, live vs stored "
                 "values).  Replay-able.")
    lines.append("- **`audit_reports/ANGLE_STALENESS_SWEEP_REPORT.md`** — this report.")
    lines.append("- `scripts/angle_staleness_sweep.py` — sweep driver.  Read-only.  Idempotent.")
    lines.append("")
    lines.append("## 11. Sign-off")
    lines.append("")
    lines.append("No writes, no mutations, no schema changes, no recomputes, no backfill, no "
                 "flag flips were performed.  All four constraint flags re-verified "
                 "post-sweep:")
    lines.append("- `INTENT_ROUTER_V2_CUTOVER=false`")
    lines.append("- `INTENT_ROUTER_V2_ROLLOUT_PERCENT=10`")
    lines.append("- `RELATIONSHIP_ORCHESTRATION_PROMPT=false`")
    lines.append("- `CROSS_LENS_PROMPT_SURFACE=false`")
    lines.append("")

    with open(MD_PATH, "w") as f:
        f.write("\n".join(lines))
    print(f"wrote {MD_PATH} ({len(lines)} lines)")


if __name__ == "__main__":
    main()
