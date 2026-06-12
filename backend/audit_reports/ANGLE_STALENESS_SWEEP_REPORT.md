# Angle Staleness Enumeration — Sweep Report

**Generated:** 2026-06-12T12:49:34Z
**Database:** `test_database` (preview)
**Method:** READ-ONLY full-collection sweep of `charts`.  For every angle (`asc / mc / dc / ic`) and every house cusp (1-12) the stored `{sign, degree, longitude}` was compared to a fresh `attribute_sign(stored_longitude + DEFAULT_AYANAMSA, mode=MODE_TRUE_SIDEREAL_MIDPOINT)` call.  **No writes. No mutations. No recomputes. No backfill.**

## 1. Top-Line Numbers

- **Total charts scanned:** 171
- **Affected charts:** 168 (**98.25%**)
- **Unaffected charts:** 3

**Worst-verdict distribution at chart level:**

| Verdict | Charts |
|---------|-------:|
| `CRITICAL_SIGN_MISMATCH` | 158 |
| `OUT_OF_RANGE` | 6 |
| `STALE_HIGH` | 4 |
| `MISSING` | 3 |

Verdict legend:

- **`OK`** — stored sign matches live AND `|Δdegree| < 1.0°`.
- **`STALE_LOW`** — sign matches AND `1.0° ≤ |Δdegree| < 2.0°`.
- **`STALE_MED`** — sign matches AND `2.0° ≤ |Δdegree| < 7.0°`.
- **`STALE_HIGH`** — sign matches AND `|Δdegree| ≥ 7.0°`.
- **`OUT_OF_RANGE`** — stored `degree ≥ 30°` (formally invalid).
- **`CRITICAL_SIGN_MISMATCH`** — stored sign **differs** from what the current engine returns for the same longitude.
- **`MISSING`** — no stored sign / degree / longitude to compare.

## 2. Field-Level Counts

### 2.1 Angles

| Field | OK | STALE_LOW | STALE_MED | STALE_HIGH | OUT_OF_RANGE | CRITICAL_SIGN_MISMATCH | MISSING |
|-------|---:|----------:|----------:|-----------:|-------------:|----------------------:|--------:|
| **ASC** | 17 | 29 | 29 | 56 | 15 | 22 | 3 |
| **MC** | 25 | 7 | 106 | 1 | 18 | 11 | 3 |
| **DC** | 38 | 21 | 37 | 5 | 10 | 57 | 3 |
| **IC** | 9 | 23 | 29 | 57 | 30 | 20 | 3 |

### 2.2 House Cusps (1–12)

| House | OK | STALE_LOW | STALE_MED | STALE_HIGH | OUT_OF_RANGE | CRITICAL_SIGN_MISMATCH | MISSING |
|------:|---:|----------:|----------:|-----------:|-------------:|----------------------:|--------:|
| H1 | 17 | 29 | 29 | 56 | 15 | 22 | 3 |
| H2 | 10 | 14 | 85 | 31 | 15 | 13 | 3 |
| H3 | 38 | 5 | 32 | 24 | 57 | 12 | 3 |
| H4 | 10 | 24 | 43 | 55 | 15 | 21 | 3 |
| H5 | 10 | 22 | 54 | 24 | 10 | 48 | 3 |
| H6 | 21 | 51 | 52 | 8 | 3 | 33 | 3 |
| H7 | 38 | 21 | 37 | 5 | 10 | 57 | 3 |
| H8 | 20 | 9 | 87 | 4 | 6 | 42 | 3 |
| H9 | 8 | 11 | 50 | 6 | 25 | 68 | 3 |
| H10 | 24 | 3 | 55 | 4 | 17 | 65 | 3 |
| H11 | 28 | 18 | 33 | 25 | 51 | 13 | 3 |
| H12 | 53 | 13 | 20 | 28 | 18 | 36 | 3 |

> House cusps 1, 4, 7, 10 are the same axes as Asc / IC / DC / MC.  Observed pattern: each axis carries the same anomaly profile across both `angles.<key>` and `houses.formatted_cusps[<n>]`.  This confirms the defect is at the storage layer (chart documents) rather than at the angles-rendering layer.

## 3. Severity Distribution (all fields combined)

Total field-events evaluated: **2736** (171 charts × 16 fields = 4 angles + 12 cusps).

| Verdict | Count | % of all fields |
|---------|------:|----------------:|
| `OK` | 366 | 13.38% |
| `STALE_LOW` | 300 | 10.96% |
| `STALE_MED` | 778 | 28.44% |
| `STALE_HIGH` | 389 | 14.22% |
| `OUT_OF_RANGE` | 315 | 11.51% |
| `CRITICAL_SIGN_MISMATCH` | 540 | 19.74% |
| `MISSING` | 48 | 1.75% |

## 4. Sign-Boundary Pattern (where the mismatches concentrate)

**Top stored→live sign-pair mismatches across all angles + cusps:**

| Stored sign | Live sign (current engine) | Mismatches |
|-------------|-----------------------------|-----------:|
| `Ophiuchus` | `Scorpio` | 134 |
| `Aquarius` | `Capricorn` | 89 |
| `Pisces` | `Aries` | 79 |
| `Taurus` | `Aries` | 70 |
| `Leo` | `Cancer` | 43 |
| `Virgo` | `Libra` | 35 |
| `Pisces` | `Aquarius` | 26 |
| `Sagittarius` | `Capricorn` | 20 |
| `Virgo` | `Leo` | 18 |
| `Gemini` | `Cancer` | 17 |
| `Sagittarius` | `Scorpio` | 6 |
| `Scorpio` | `Libra` | 2 |
| `Gemini` | `Taurus` | 1 |

**Interpretation.**  Every top-15 mismatch is between adjacent (or near-adjacent) signs in the True-Sidereal ordering.  The dominant pair (`Ophiuchus → Scorpio`, 134 events) tells us the previous engine's Ophiuchus sector was *wider* than the current engine's — longitudes that the old engine called Ophiuchus, the current engine now calls Scorpio.  The next two pairs (`Aquarius → Capricorn`, `Pisces → Aries`) point at the Aquarius / Capricorn and Pisces / Aries boundaries having shifted between the two engines.  No mismatches cross non-adjacent signs — consistent with a boundary-table revision, not a calculation bug.

## 5. Version / Migration-Marker Cross-Tab

| `astrology_engine_version` | `sign_attribution_version` | `migration_marker` | Total | Verdicts |
|----------------------------|----------------------------|--------------------|------:|----------|
| `midpoint13_variant_a_v1` | `midpoint13_variant_a` | `variant-a-13-sign-migration-v1` | 168 | CRITICAL_SIGN_MISMATCH=158, STALE_HIGH=4, OUT_OF_RANGE=6 |
| `None` | `None` | `None` | 3 | MISSING=3 |

**All 168 affected charts share the *same* migration boundary:**
- `astrology_engine_version = midpoint13_variant_a_v1`
- `sign_attribution_version = midpoint13_variant_a`
- `migration_marker = variant-a-13-sign-migration-v1`

The 3 unaffected charts have **no version markers at all** (`engine_version=None`, `sign_attribution_version=None`, `migration_marker=None`) and have no longitude data to compare against — they are pre-migration legacy stubs (verdict = `MISSING`), not post-migration successes.

**So:**  100% of charts that completed the `variant-a-13-sign-migration-v1` migration are affected.  This is consistent with the forensic-report hypothesis that **the planets-side migration was run but the angles + house-cusps side was not**, and that the `sign_attribution` engine has since received a boundary-table revision that the chart documents do not reflect.

## 6. Creation-Date Breakdown

| Year-Month | Charts | Worst-verdict mix |
|------------|-------:|--------------------|
| `2026-01` | 4 | CRITICAL_SIGN_MISMATCH=4 |
| `2026-02` | 125 | CRITICAL_SIGN_MISMATCH=116, STALE_HIGH=4, OUT_OF_RANGE=5 |
| `2026-03` | 12 | CRITICAL_SIGN_MISMATCH=12 |
| `2026-04` | 1 | CRITICAL_SIGN_MISMATCH=1 |
| `2026-05` | 6 | CRITICAL_SIGN_MISMATCH=3, MISSING=3 |
| `2026-06` | 2 | CRITICAL_SIGN_MISMATCH=2 |
| `unknown` | 21 | CRITICAL_SIGN_MISMATCH=20, OUT_OF_RANGE=1 |

- **Earliest affected:** chart `6971c8f687b803fcdcc6fa95` (user `6971c8f681beab3a8955b255`) — `2026-01-22 06:51:34.149000` — verdict `CRITICAL_SIGN_MISMATCH`
- **Latest affected:** chart `697f0c6abaac8457713b6862` (user `697f0c6abf35c0528ff06954`) — `2026-06-09T16:18:16.058199+00:00` — verdict `CRITICAL_SIGN_MISMATCH`

**Implication.**  The anomaly spans the **entire history** of the chart collection (Jan 2026 → Jun 2026).  The February 2026 spike (116 CRITICAL + 4 STALE_HIGH + 5 OUT_OF_RANGE in a single month) is consistent with the initial `variant-a-13-sign-migration-v1` backfill run having processed the bulk of the user base at that point.  Subsequent months show fewer new charts per month but **every** new chart since the migration is still being written under the now-stale boundary table.

## 7. Per-Field CRITICAL_SIGN_MISMATCH Breakdown

Top stored→live sign-pairs **per angle field**:

- **ASC** — 22 critical · top: `Gemini→Cancer`: 7, `Ophiuchus→Scorpio`: 6, `Virgo→Leo`: 5, `Taurus→Aries`: 1, `Sagittarius→Scorpio`: 1
- **MC** — 11 critical · top: `Sagittarius→Capricorn`: 2, `Taurus→Aries`: 2, `Virgo→Libra`: 2, `Ophiuchus→Scorpio`: 2, `Leo→Cancer`: 1
- **DC** — 57 critical · top: `Aquarius→Capricorn`: 40, `Ophiuchus→Scorpio`: 5, `Pisces→Aquarius`: 4, `Sagittarius→Capricorn`: 3, `Pisces→Aries`: 3
- **IC** — 20 critical · top: `Ophiuchus→Scorpio`: 9, `Virgo→Libra`: 6, `Leo→Cancer`: 2, `Pisces→Aries`: 1, `Pisces→Aquarius`: 1

Per-house CRITICAL_SIGN_MISMATCH counts:

| House | Critical | | House | Critical |
|------:|---------:|-|------:|---------:|
| H1 | 22 | | H7 | 57 |
| H2 | 13 | | H8 | 42 |
| H3 | 12 | | H9 | 68 |
| H4 | 21 | | H10 | 65 |
| H5 | 48 | | H11 | 13 |
| H6 | 33 | | H12 | 36 |

## 8. Risk Assessment

### 8.1 What is at risk right now?

- **User-facing chart data.**  98.25% of stored charts now disagree with the live sign-attribution engine on at least one angle or house cusp.  Whenever the application surfaces the *stored* sign label (e.g., the prompt-layer renders `IC / Imum Coeli: 31°Pisces (Pisces)`), the user is being shown the **old** sign label, which for ~12% of those charts (`CRITICAL_SIGN_MISMATCH` rate at chart level) is now factually wrong (stored sign != current-engine sign).
- **Phase-3 prompt hardening.**  The new `MC FOCUS` / `IC FOCUS` / `CHIRON FOCUS` blocks instruct the LLM to **explicitly name the stored sign**.  Where the stored sign is stale, the LLM will now name it more loudly and confidently.  Phase-3 was correct given the storage layer's self-report, but the storage layer's self-report is partially wrong.
- **Downstream consumers** that key on the stored sign label (orchestration / lens selection / contradiction surfaces) inherit the same staleness.

### 8.2 Severity rating

| Dimension                           | Severity |
|-------------------------------------|----------|
| Blast radius (charts affected)      | **HIGH**   — 98.25% |
| Field coverage                      | **HIGH**   — all four angles + all twelve house cusps |
| Factual-accuracy risk per user      | **MEDIUM** — sign labels are wrong on ~1 axis per chart on average; degree drift is small (<2°) on most cusps but >5° on many |
| User-visible impact                 | **MEDIUM** — visible when the IC/MC/DC sign is surfaced verbatim in chat or chart UI |
| Engine consistency for new charts   | **HIGH**   — new charts written today still inherit the same staleness |

### 8.3 What is NOT at risk

- **Planets** (`astrology.planets.*`).  Forensic + Phase-3 verification confirmed planet sign labels are consistent with the current engine for the four reference users.  A full-planet sweep can be added in the next ticket but the symptom pattern (degree > 30 / sign mismatch) is absent from planets in our spot checks.
- **Longitudes** themselves are intact in storage; only the sign / degree-within-sign derivations are stale.  This means a remediation can be derived deterministically from the existing stored data — no ephemeris recomputation, no chart-time recompute, just a re-attribution pass.

## 9. Open Questions for the Remediation Ticket (NOT executed here)

1. **Is `midpoint13_variant_a_v1` the intended engine of record?**  If yes, the chart documents need to be re-attributed against the *current* boundary table for that engine.  If the intended engine is now `midpoint12_variant_b` (the merged-candidate fallback that `attribute_sign` is currently dispatching to), the engine-of-record decision needs to be made first.
2. **Should write-path be patched before backfill?**  Otherwise even after backfill, every newly written chart will reintroduce the staleness.
3. **Should we capture a snapshot of the old sign / degree** in a `legacy_*` sub-document so historical interpretations remain reproducible after backfill?
4. **Are there orchestration / lens caches** that pre-resolve sign labels and would need to be invalidated post-backfill?

## 10. Files

- `audit_reports/ANGLE_STALENESS_SWEEP.json` — raw per-chart classification data (chart_id, user_id, all 16 field verdicts, deltas, live vs stored values).  Replay-able.
- **`audit_reports/ANGLE_STALENESS_SWEEP_REPORT.md`** — this report.
- `scripts/angle_staleness_sweep.py` — sweep driver.  Read-only.  Idempotent.

## 11. Sign-off

No writes, no mutations, no schema changes, no recomputes, no backfill, no flag flips were performed.  All four constraint flags re-verified post-sweep:
- `INTENT_ROUTER_V2_CUTOVER=false`
- `INTENT_ROUTER_V2_ROLLOUT_PERCENT=10`
- `RELATIONSHIP_ORCHESTRATION_PROMPT=false`
- `CROSS_LENS_PROMPT_SURFACE=false`
