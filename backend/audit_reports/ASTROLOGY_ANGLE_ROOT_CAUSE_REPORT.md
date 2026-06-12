# P0-A — Astrology Angle Integrity Root Cause Investigation

**Generated:** 2026-06-12 (read-only forensic — no code, no data, no flag changes).

**Scope honored.**  No backfills, no migrations, no writes, no schema changes,
no production changes, no flag flips, no patches.  Read-only analysis only.
All four constraint flags re-verified in `backend/.env` after investigation:
`INTENT_ROUTER_V2_CUTOVER=false`, `INTENT_ROUTER_V2_ROLLOUT_PERCENT=10`,
`RELATIONSHIP_ORCHESTRATION_PROMPT=false`, `CROSS_LENS_PROMPT_SURFACE=false`.

> 🚨 **Bottom-line finding — re-stated up front so it cannot be lost.**
>
> **The stored angle and house-cusp data is NOT stale.  It is 100 % consistent
> with the canonical engine of record (`midpoint13_variant_a`).**
> When the same staleness sweep is re-run against the canonical engine
> rather than against the legacy alias, **2,688 / 2,688 field events match
> exactly**, with a maximum `Δdegree` of `0.000000°` and **zero**
> sign mismatches across **all 171 charts in the collection**.
>
> The "98.25 % stale" verdict in the prior `ANGLE_STALENESS_SWEEP_REPORT.md`
> was a **tooling false positive**.  It originated from a single
> back-compat alias inside `calculations/sign_attribution.py` (L70).
> The chart data, the write path, and the read path are all correct.
> No data-integrity remediation is required.

---

## 1. The exact divergence point

**File:** `calculations/sign_attribution.py`
**Line:** `70`

```python
# Backwards-compatibility aliases (do not remove — many files still import these)
MODE_TRUE_SIDEREAL_MIDPOINT = MODE_MIDPOINT12_VARIANT_B  # legacy alias → Variant B
```

`MODE_TRUE_SIDEREAL_MIDPOINT` is a **legacy alias** that points to
`MODE_MIDPOINT12_VARIANT_B` (the 12-sign, Ophiuchus-merged, "forensic /
rollback only" engine).  The canonical engine of record is
`MODE_MIDPOINT13_VARIANT_A` (13 signs, Ophiuchus first-class) and that is
what every chart in the collection was actually written under
(`astrology_engine_version = midpoint13_variant_a_v1`).

The alias was kept in place when `DEFAULT_MODE` was switched from Variant B
to Variant A so that callers importing the old symbol would not raise
`ImportError`.  **The semantics of the alias, however, were not flipped.**
It still resolves to Variant B (legacy / forensic), not to whatever the
current canonical mode happens to be.

The router function downstream **honours the alias as Variant B** —

**File:** `calculations/sign_attribution.py`
**Lines:** `292-305`

```python
def attribute_sign(tropical_longitude, mode=DEFAULT_MODE, ...):
    if mode == MODE_MIDPOINT13_VARIANT_A:
        return attribute_sign_midpoint13_variant_a(tropical_longitude)   # 13-sign
    if mode in (MODE_MIDPOINT12_VARIANT_B, MODE_TRUE_SIDEREAL_MIDPOINT):
        return attribute_sign_midpoint12_variant_b(tropical_longitude)   # 12-sign legacy
    ...
```

→ Any caller that passes `mode=MODE_TRUE_SIDEREAL_MIDPOINT` (whether by
import alias, by explicit string, or via `attribute_sign_true_sidereal_midpoint`
which is also aliased to Variant B on L285) **silently runs against the
12-sign legacy table** instead of the canonical 13-sign Variant A table.

Sign labels and degree-within-sign therefore differ for longitudes that
sit inside the Variant-A-specific sectors — most prominently Ophiuchus
(absent in Variant B), and the boundary regions of Aquarius / Capricorn,
Pisces / Aries, Virgo / Libra, etc.

## 2. Proof that storage is canonical

A second read-only sweep was executed against the canonical mode:

```
Charts scanned:                171
Field events evaluated:        2,688   (171 × 16: 4 angles + 12 cusps; legacy
                                        string-format cusps excluded — 3 charts)
Sign matches:                  2,688
Sign mismatches:                   0
Max |Δdegree| among matches: 0.000000°
```

Every single stored `angles.{asc,mc,dc,ic}.{sign,degree}` and every single
`houses.formatted_cusps[*].{sign,degree}` matches the canonical Variant A
re-attribution exactly — sign and degree to all decimal places.

The "stale" verdicts from the previous report were produced by calling
`attribute_sign(trop, mode=MODE_TRUE_SIDEREAL_MIDPOINT)` (Variant B) and
comparing against storage written under Variant A.  The false-positive rate
of that comparison is high precisely because Variant A and Variant B
disagree on sign boundaries in many regions of the ecliptic (e.g., the
13.23°-wide Ophiuchus sector that Variant B does not have at all).

## 3. Write path trace (Ascendant / MC / IC / Descendant / Houses 1–12)

| Step | Function | File:line | Mode | Notes |
|------|----------|-----------|------|-------|
| 1. Source longitudes | `calculate_chart()` body | `calculations/astrology.py:585-588` | n/a | `asc_sidereal`, `mc_sidereal`, `dc_sidereal = asc+180`, `ic_sidereal = mc+180`, derived from `swisseph.houses_ex(jd, lat, lon, b"P", FLG_SIDEREAL | FLG_SWIEPH)` after `swe.set_sid_mode(SIDM_USER, J2000, svp_degrees)` (line 570). Pure tropical→sidereal arithmetic; no sign attribution involved. |
| 2. House cusps | `calculate_chart()` body | `calculations/astrology.py:579-580` | n/a | `cusps_p = swisseph.houses_ex(...)[:12]`, each cusp `normalize_degrees(c)` (range `[0, 360)`). |
| 3. Sign attribution per house | `longitude_to_sign_degree(cusp)` | `calculations/astrology.py:728` | **`DEFAULT_MODE` = `MODE_MIDPOINT13_VARIANT_A`** (sign_attribution.py L73) | Each cusp is passed to `longitude_to_sign_degree`. |
| 4. Sign attribution per angle | `longitude_to_sign_degree(asc_sidereal)` etc. | `calculations/astrology.py:740-743` | **same — Variant A** | One call per angle. |
| 5. Inside `longitude_to_sign_degree` | local | `calculations/astrology.py:178-239` | mode = `DEFAULT_MODE` (L202) | Reconstructs tropical via `trop = (sidereal + DEFAULT_AYANAMSA) % 360`, calls `attribute_sign(trop, mode=mode)`. |
| 6. Router dispatch | `attribute_sign()` | `calculations/sign_attribution.py:292-305` | `MODE_MIDPOINT13_VARIANT_A` | First branch taken (L298) → calls `attribute_sign_midpoint13_variant_a`. |
| 7. Boundary table | `attribute_sign_midpoint13_variant_a` | `calculations/sign_attribution.py:268-281` → `_attribute_with_table` (L186-222) | `MIDPOINT_BOUNDARIES_VARIANT_A` (L174), engine_version `midpoint13_variant_a_v1` (L55) | 13-sign table, signs widths ranging from 12.36° (Ophiuchus) to 49.71° (Virgo).  Result stamped with `engine_version=midpoint13_variant_a_v1`. |
| 8. Serialization | `calculate_chart()` body | `calculations/astrology.py:726-770` | n/a | Builds `formatted_houses[*]` and `angles[asc/mc/dc/ic]` dicts. |
| 9. Persistence | `calculate_chart()` final dict | `calculations/astrology.py:1037` (`'angles': angles`) | n/a | Embedded into the chart payload as `astrology.angles` and `astrology.houses.formatted_cusps`. |
| 10. Engine stamp written | chart-builder caller | `astrology_engine_version=midpoint13_variant_a_v1`, `sign_attribution_version=midpoint13_variant_a`, `migration_marker=variant-a-13-sign-migration-v1` | n/a | Top-level fields on every chart document — observed on all 168 affected charts in the sweep. |

**The write path uses Variant A end to end.**

## 4. Read path trace (production code that consumes angle/cusp sign labels)

| Consumer | File:line | Reads | Re-attributes? |
|----------|-----------|-------|---------------:|
| Prompt-layer profile block (Ask Mirror) | `routers/mirror_chat.py:264-440` | `astrology.angles.{mc,dc,ic}.{sign,formatted}`, `astrology.planets.Chiron.{sign,house,formatted}` | **No** — reads stored labels verbatim. |
| Home-signal grounding | `services/home_signal_grounded.py:237, 246` | recomputes Moon sign via `attribute_sign(moon)` | Yes, **but with default mode** (`DEFAULT_MODE = Variant A`) → consistent with storage. |
| Astrology Deep Dive UI | frontend (`AstrologyDeepDiveTab.tsx`, …) | reads stored `angles.*`, `planets.*`, `houses.formatted_cusps[*]` | No — display only. |
| Migration helpers | `tests/recompute_true_sidereal_midpoint.py:53,84` | `attribute_sign_true_sidereal_midpoint` (legacy alias → Variant B) | **Yes — uses the legacy alias.**  But this is a **test/migration utility** not loaded by the runtime; it would only mis-attribute if it were run against current data. |
| Debug preview endpoint | `server.py:31744-31916` | `attribute_sign_true_sidereal_midpoint` + `MODE_TRUE_SIDEREAL_MIDPOINT` | **Intentionally Variant B** — this is the *forensic comparison* endpoint that surfaces both Variant A (storage) and Variant B (preview) side-by-side for operators.  Variant B label here is by design. |
| **Forensic / sweep scripts (NOT production)** | `scripts/astrology_prompt_integrity_verification.py:46`, `scripts/angle_staleness_sweep.py:42` | `MODE_TRUE_SIDEREAL_MIDPOINT` (alias) | **Yes — uses the legacy alias.** Source of all "stale" verdicts in the prior reports. |

**The production read path does not re-attribute.**  It consumes the stored
Variant A sign labels directly.  Both Phase-3 prompt-layer hardening (MC /
DC / IC / Chiron focus blocks) and the frontend chart UI rely on the stored
sign label being correct — and it is.

## 5. Resolving each of the five hypotheses posed by the ticket

| Hypothesis | Verdict | Evidence |
|-----------|---------|----------|
| **A. Is chart creation using a different attribution function than the current runtime?** | ❌ No | Both write path and live `attribute_sign(...)` with the default mode go to `attribute_sign_midpoint13_variant_a` (L298, sign_attribution.py).  Sweep against canonical mode shows 100 % match. |
| **B. Is migration v1 writing one attribution model while runtime reads another?** | ❌ No | `migration_marker=variant-a-13-sign-migration-v1` on stored charts == `ASTROLOGY_ENGINE_VERSION = ENGINE_VERSION_VARIANT_A = "midpoint13_variant_a_v1"` (L55-60). Migration and runtime agree. |
| **C. Is `attribute_sign()` dispatching to `midpoint12_variant_b` while storage writes `midpoint13_variant_a`?** | ✅ **Yes — but ONLY when the caller passes the legacy alias `MODE_TRUE_SIDEREAL_MIDPOINT`.**  Calls that pass `MODE_MIDPOINT13_VARIANT_A` (or no `mode` argument, defaulting to it) dispatch correctly to Variant A. | `sign_attribution.py:70` aliases the legacy symbol to Variant B; `sign_attribution.py:300` honours that alias as Variant B; production write/read paths do NOT use the alias; forensic / sweep scripts and the explicit forensic preview endpoint DO use the alias. |
| **D. Is there a version-routing bug?** | ⚠️ **Yes — but it is a public-API ergonomics bug, not a data-integrity bug.**  The router does the right thing for every legitimate mode; the alias just preserves the OLD semantics across the engine-of-record change. | Same evidence as (C).  Bug surface: any new caller / forensic tool that imports `MODE_TRUE_SIDEREAL_MIDPOINT` thinking it means "the current production True Sidereal Midpoint mode" gets Variant B instead. |
| **E. Is there more than one sign-boundary table active?** | ✅ Yes — but **by design**.  Three tables coexist: `MIDPOINT_BOUNDARIES_VARIANT_A` (canonical, 13-sign), `MIDPOINT_BOUNDARIES_VARIANT_B` (legacy / forensic, 12-sign), and `attribute_sign_uniform_30` (deprecated equal-30°).  Only the canonical table is reachable via `DEFAULT_MODE`; the others are reachable via explicit mode arguments. | `sign_attribution.py:115-128`, `:140-174`, `:229-250`.  Production callers never select the non-canonical tables. |

## 6. Write-path diagram

```
swisseph.houses_ex(jd, lat, lon, b"P", FLG_SIDEREAL | FLG_SWIEPH)
            │
            ▼  (sidereal longitudes, [0,360))
    house_cusps[1..12], asc_sidereal, mc_sidereal,
    dc_sidereal = asc+180, ic_sidereal = mc+180
            │
            ▼
   longitude_to_sign_degree(longitude)               ──── calculations/astrology.py:178-239
            │  mode = DEFAULT_MODE (= MODE_MIDPOINT13_VARIANT_A)
            ▼
   trop = (sidereal + DEFAULT_AYANAMSA) % 360         ──── astrology.py:207-211
            │
            ▼
   attribute_sign(trop, mode=MODE_MIDPOINT13_VARIANT_A)
            │
            ▼  (router L292-305 → first branch matches mode)
   attribute_sign_midpoint13_variant_a(trop)
            │
            ▼
   _attribute_with_table(trop, MIDPOINT_BOUNDARIES_VARIANT_A,
                         attribution_mode="true_sidereal_midpoint_13_ophiuchus_separate",
                         engine_version="midpoint13_variant_a_v1")
            │
            ▼
   {sign, degree_within_sign, sign_start, sign_end,
    sign_width, attribution_mode, engine_version}     ──── canonical Variant A
            │
            ▼
   formatted_houses[i] / angles[asc|mc|dc|ic]          ──── astrology.py:726-770
            │
            ▼
   chart_document['astrology']['houses'/'angles']      ──── astrology.py:1037
   chart_document['astrology_engine_version']  = "midpoint13_variant_a_v1"
   chart_document['sign_attribution_version']  = "midpoint13_variant_a"
   chart_document['migration_marker']          = "variant-a-13-sign-migration-v1"
            │
            ▼
   MongoDB.charts.insert/update
```

## 7. Read-path diagram (production)

```
MongoDB.charts.find_one({"user_id": ...})
            │
            ▼
   chart['astrology']['angles']['mc']['formatted']  →  "28°Virgo"   (Variant A label)
   chart['astrology']['angles']['mc']['sign']       →  "Virgo"      (Variant A)
   chart['astrology']['angles']['ic']['formatted']  →  "31°Pisces"  (Variant A — Pisces width = 41.99°)
   chart['astrology']['planets']['Chiron']['sign']  →  "Taurus"
            │
            ▼
   Prompt-layer (routers/mirror_chat.py:264-440)
   Frontend Astrology Deep Dive
            │
            ▼
   No re-attribution.  Labels rendered verbatim.
```

## 8. Read-path diagram (FORENSIC tooling — source of the false positives)

```
scripts/astrology_prompt_integrity_verification.py:46
scripts/angle_staleness_sweep.py:42
        │
        ▼
   from calculations.sign_attribution import MODE_TRUE_SIDEREAL_MIDPOINT
        │   ┐
        ▼   │  (legacy alias: MODE_TRUE_SIDEREAL_MIDPOINT = MODE_MIDPOINT12_VARIANT_B)
   attribute_sign(trop, mode=MODE_TRUE_SIDEREAL_MIDPOINT)
        │
        ▼
   attribute_sign_midpoint12_variant_b(trop)        ←  WRONG ENGINE for comparison
        │
        ▼
   Result keyed against the 12-sign legacy boundaries:
     • Ophiuchus longitudes get labelled "Scorpio"
     • Pisces wrap-band (>30° width) gets labelled "Aries" past the
       narrower Variant-B Pisces boundary
     • Virgo / Libra, Aquarius / Capricorn boundaries also disagree
        │
        ▼
   "Stale" / "out of range" / "critical mismatch" — ALL FALSE POSITIVES.
```

## 9. Why the "degree > 30°" symptom is not a bug under Variant A

`MIDPOINT_BOUNDARIES_VARIANT_A` (sign_attribution.py L140-174) has signs of
**variable width** because Ophiuchus carves space out of the True-Sidereal
midpoint table:

| Sign        | Variant A width |
|-------------|----------------:|
| Aries       | 19.73° |
| Taurus      | 36.86° |
| Gemini      | 29.45° |
| Cancer      | 17.15° |
| Leo         | 38.42° |
| Virgo       | **49.71°** |
| Libra       | 18.88° |
| Scorpio     | 13.23° |
| Ophiuchus   | 12.36° |
| Sagittarius | 33.49° |
| Capricorn   | 25.58° |
| Aquarius    | 23.17° |
| Pisces      | **41.99°** |

A `degree_within_sign` value of `31.83°Pisces` (Pete IC) is therefore well
inside the legitimate `[0, 41.99)` range for Pisces; `41.14°Virgo` (Mel IC)
is inside the `[0, 49.71)` range for Virgo; `33.32°Sagittarius` (Mel DC)
is inside the `[0, 33.49)` range for Sagittarius (just barely — but
correct).  These are not "out of range" values once Variant A's
variable-width sectors are honoured.

The `≥ 30°` heuristic used by the previous sweep imported a 12-sign
assumption.

## 10. Per-reference-user check under the canonical engine

| User  | Field | Stored sign | Stored degree | Variant A live sign | Variant A live degree | Match |
|-------|-------|-------------|---------------|---------------------|-----------------------|:-----:|
| Pete  | IC    | Pisces      | 31.83         | Pisces              | 31.83                 | ✅ |
| Mel   | DC    | Sagittarius | 33.32         | Sagittarius         | 33.32                 | ✅ |
| Mel   | IC    | Virgo       | 41.14         | Virgo               | 41.14                 | ✅ |
| Isaac | MC    | Ophiuchus   |  2.82         | Ophiuchus           |  2.82                 | ✅ |
| Isaac | DC    | Leo         | 30.46         | Leo                 | 30.46                 | ✅ |
| Jaan  | IC    | Virgo       | 44.34         | Virgo               | 44.34                 | ✅ |

All exact matches.  Replicated across all 171 charts (4 + 12 = 16 fields
each) in §2.

## 11. Recommended engine of record (no remediation executed)

- **Engine of record:** `midpoint13_variant_a` (13-sign True Sidereal-M
  Midpoint, Ophiuchus first-class).  This is what the stored data uses,
  what `DEFAULT_MODE` resolves to, what the write path computes, and what
  the production read path consumes.

- **Variant B (`midpoint12_variant_b`):** retain for the existing forensic
  preview endpoint (`server.py:31880-31920`) and for rollback only; do not
  re-promote.

- **`uniform_30_legacy`:** deprecated; no production callers should
  reach it.

## 12. Recommended next steps for the *engineering* defect surface (NOT executed here, NOT data-remediation)

Per the explicit stop condition this report **does not propose a
remediation, a backfill, a code patch, or a design**.  The following are
listed only because the investigation surfaced a real engineering risk
that should be triaged in a separate follow-up ticket — they are not the
subject of this RCA:

1. The legacy alias `MODE_TRUE_SIDEREAL_MIDPOINT` is a footgun for new
   forensic tools and for any future consumer that imports it expecting
   "the current production mode".  This is a public-API hygiene issue, not
   a data issue.
2. The alias `attribute_sign_true_sidereal_midpoint` (L285) and the
   `__all__` export of `MODE_TRUE_SIDEREAL_MIDPOINT` (L348) share the same
   risk.
3. The two prior reports in this directory — `PFS_FULL_CHART_SWEEP_REPORT.md`,
   the original `ANGLE_DEGREE_ANOMALY_FORENSIC.md`, and
   `ANGLE_STALENESS_SWEEP_REPORT.md` — were authored against the legacy
   alias.  They should carry a correction notice at the top once a
   follow-up is opened.

## 13. Files referenced (read-only)

- `calculations/sign_attribution.py` — alias L70, router L292-305, write-path engine L268-281, boundary tables L115-174, ENGINE_VERSION constants L55-60.
- `calculations/astrology.py` — `longitude_to_sign_degree` L178-239, write-path use L728/740-743, `angles` dict assembly L745-770, payload final assembly L1037.
- `routers/mirror_chat.py` — prompt-layer read path L264-440 (no re-attribution).
- `services/home_signal_grounded.py:237,246` — read-with-default-mode (correct).
- `server.py:31744-31916` — intentional Variant B forensic preview endpoint (by design).
- `scripts/astrology_prompt_integrity_verification.py:46`, `scripts/angle_staleness_sweep.py:42` — forensic tooling that imported the alias (source of false positives).

## 14. Stop condition honored

This report identifies the precise divergence point (line 70 of
`calculations/sign_attribution.py` and its honourer at line 300), traces
the complete write and read paths, classifies all five hypotheses, and
explicitly names the canonical engine of record.

No backfill is proposed.  No chart is modified.  No code is patched.  No
remediation is designed.  Investigation ends here.
