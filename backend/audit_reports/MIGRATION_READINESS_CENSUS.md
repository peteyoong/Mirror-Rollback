# Migration Readiness Census — Pre-Migration Verification

**Build marker:** `migration-readiness-census-v1`
**Mode:** READ-ONLY. No data modified. No charts recalculated. No migration triggered.
**Database:** `test_database` on `mongodb://localhost:27017` (only DB configured in `/app/backend/.env`)
**Audit timestamp:** captured live during this run
**Canonical target engine:** `midpoint13_variant_a_v1`
**Companion JSON:** `/app/backend/audit_reports/MIGRATION_READINESS_CENSUS.json`

---

## TL;DR

The chart corpus is **stable and clean**.

| Verdict | Detail |
|---------|--------|
| Total charts | **171** (unchanged since the previous P0 forensic audit) |
| Already on canonical `midpoint13_variant_a_v1` | **168 / 171 (98.2%)** |
| Stamped with the prior Variant-B migration marker (legacy demo seeds) | **3 / 171 (1.8%)** |
| Non-canonical with full birth data → eligible for migration | **0** |
| Non-canonical missing birth data → INELIGIBLE | **3** (all three demo seeds; deterministic synthetic charts, no birth-data user rows) |
| Charts that would be SKIPPED by migration (no `user_id` linkage) | **0** |
| Net delta vs previous 171-chart audit | **+0 — corpus unchanged** |

**Recommendation:** A "global chart migration" would have **zero work to do** for non-canonical user charts. The three remaining non-canonical chart documents are demo-seed records whose parent users carry no birth data — they cannot be recomputed through `get_full_natal_chart` and are deterministic test fixtures, not real users. If you still want them brought to the Variant A stamp, that requires a separate "demo-seed re-stamp" path that bypasses the birth-data preflight (out of scope for a normal migration).

---

## 1. Totals

| Metric | Value |
|--------|-------|
| Total users (`db.users` count) | **175** |
| Total charts (`db.charts` count) | **171** |
| Users without a chart (175 − 171) | **4** (counts only — IDs not listed because that's outside the scope of "chart corpus") |

---

## 2. Count grouped by engine-version stamps

### 2.1 `astrology.metadata.astrology_engine_version` (embedded — written by `get_full_natal_chart`)

| Metadata Engine Version | Count |
|--------------------------|-------|
| `midpoint13_variant_a_v1` | **168** |
| `<missing>` | **3** |

### 2.2 Top-level `astrology_engine_version` (written by migration script)

| Engine Version | Count |
|----------------|-------|
| `midpoint13_variant_a_v1` | **168** |
| `<missing>` | **3** |

### 2.3 `migration_marker`

Top-level marker:

| Migration Marker (top-level) | Count |
|--------------------------------|-------|
| `variant-a-13-sign-migration-v1` | **168** |
| `<missing>` | **3** |

Embedded marker (`astrology.migration_marker`) — surfaced for the 3 "missing top-level" charts:

| Embedded Marker (astrology.migration_marker) | Count |
|------------------------------------------------|-------|
| `true-sidereal-midpoint-production-migration-v1` (legacy Variant-B-candidate marker) | **3** |

> **Important refinement:** the 3 charts that appear "unmigrated" at the top-level inspection ARE migration-stamped — but with the **prior** marker (`true-sidereal-midpoint-production-migration-v1`, the pre-Variant-A "Variant B 12-merged candidate" migration). They were never re-stamped to the canonical Variant A marker because the migration script's preflight rejects charts whose parent user has no birth data.

---

## 3. Cross-tab — full engine/marker/house combination matrix

| Top-level engine | Metadata engine | Migration marker | House system | Count |
|--------------------|-------------------|-------------------|--------------|-------|
| `midpoint13_variant_a_v1` | `midpoint13_variant_a_v1` | `variant-a-13-sign-migration-v1` | `Equal` | **168** |
| `<None>` | `<None>` (but embedded `astrology.migration_marker = true-sidereal-midpoint-production-migration-v1`) | `<None>` | `<None>` | **3** |

The 168-chart cohort is internally consistent across all four stamps. The 3-chart cohort is internally consistent with each other (all three are Variant-B-marker, no house system stamp, demo seed shape).

---

## 4. Engine Version Table

| Engine Version | Count |
|----------------|-------|
| `midpoint13_variant_a_v1` (canonical Variant A) | **168** |
| `<missing top-level>` (3 demo seeds embedded-stamped with `true-sidereal-midpoint-production-migration-v1`) | **3** |
| **Total** | **171** |

---

## 5. Categorical breakdown

| Category | Count | Notes |
|----------|-------|-------|
| Charts already on canonical `midpoint13_variant_a_v1` | **168** | Top-level + metadata + migration_marker all agree; House system = Equal |
| Charts on legacy engines (non-canonical) | **3** | `true-sidereal-midpoint-production-migration-v1` embedded marker; no top-level stamps |
| Charts missing engine stamps (all three stamps absent at top-level) | **3** | Same 3 demo seeds — embedded `astrology.migration_marker` IS present (prior generation) |
| Charts missing birth data | **3** | Same 3 demo seeds — parent users have null `birth_data`, `birth_datetime`, `birth_location` |
| Charts that would be SKIPPED by migration | **0** | All 171 charts have a `user_id` linkage; all 171 have a user row. **But** the 3 non-canonical ones would fail the script's `_parse_user_birth` preflight (no birth-date / birth-time / lat / lon). The migration script counts these as "skipped — no birth data", which is equivalent to ineligible. |

> **Definition clarification:** "Skipped by migration" can mean either (a) the chart has no `user_id` and therefore cannot be matched to a birth-data row (zero such charts here) or (b) the chart's user has no birth data so the calculator preflight rejects it (3 such charts here — the demo seeds). Treating (b) as "ineligible" rather than "skipped" gives the cleaner reading: **0 truly skipped, 3 ineligible**.

---

## 6. Non-canonical chart detail (all 3)

| # | chart_id (last 8) | user_id (last 8) | display name | top engine | metadata engine | embedded marker | top marker | birth_data | eligibility |
|---|---------------------|------------------|--------------|------------|------------------|-------------------|------------|-------------|-------------|
| 1 | `f4e1e962` | `f4e1e961` | **Certainty Demo** | `<None>` | `<None>` | `true-sidereal-midpoint-production-migration-v1` | `<None>` | MISSING `lat,lon,date,time` | **INELIGIBLE — no birth data** |
| 2 | `a04a389d` | `a04a389c` | **Permeability Demo** | `<None>` | `<None>` | `true-sidereal-midpoint-production-migration-v1` | `<None>` | MISSING `lat,lon,date,time` | **INELIGIBLE — no birth data** |
| 3 | `b24c74ce` | `b24c74cd` | **Achievement Demo** | `<None>` | `<None>` | `true-sidereal-midpoint-production-migration-v1` | `<None>` | MISSING `lat,lon,date,time` | **INELIGIBLE — no birth data** |

### What these three charts actually are

All three are **synthetic demo-seed accounts** created by `scripts/seed_permeability_demo.py` (and sibling seed scripts) on 2026-05-23. They have:
- `astrology.chart_type = "True Sidereal User-Defined (SVP 31.2836°, Equal Houses)"`
- `astrology.zodiac_mode = "true_sidereal_midpoint_12_merged_candidate"` (Variant B candidate)
- `astrology.svp = 31.2836`
- `astrology.planets.Sun.longitude` values like `29.0`, `348.0`, `243.0` — clean integers, not real ephemeris output, indicating **handcrafted demonstration values** rather than computed positions
- `astrology.angles = {}` — EMPTY (no ASC / MC / IC / DC ever computed)
- `astrology.aspects` populated
- `astrology.houses` present but empty cusps

Their parent user docs have `birth_data = None`, `birth_datetime = None`, `birth_location = None`. They cannot be re-computed through `calculations/astrology.get_full_natal_chart` because that function requires `(year, month, day, hour, minute, lat, lon)` — none of which exist for these records.

### Eligibility verdict for the 3 demo seeds

| Question | Answer |
|----------|--------|
| Are they real users? | No — synthetic demo-seed fixtures from `scripts/seed_*_demo.py` |
| Do they have birth data? | No — null on every required field |
| Can `get_full_natal_chart` recompute them? | No — calculator requires birth data |
| Would the migration script attempt them? | Yes — it iterates all charts; but they would be REJECTED at `_parse_user_birth` preflight and counted as `skipped_no_birth_data` |
| Are they user-facing? | No — these are seed records consumed by `/app/backend/scripts/seed_*_demo.py` for demonstration/QA only |
| Recommended action | Either (a) leave as-is and exclude from the canonical census, or (b) delete and re-seed against the canonical engine via a dedicated demo-seed script. **Do NOT include in a global migration without first deciding which.** |

---

## 7. Continuity check vs the previous P0 forensic audit

| Metric | Previous P0 audit | This census | Delta |
|--------|---------------------|--------------|-------|
| Total charts in `db.charts` | 171 | **171** | **+0** |
| Charts on canonical `midpoint13_variant_a_v1` | 168 | **168** | **+0** |
| Charts on prior `true-sidereal-midpoint-production-migration-v1` | 3 (embedded marker) | **3** | **+0** |
| Engine-stamp distribution | 168 canonical / 3 orphan | 168 canonical / 3 orphan (same docs) | **identical** |

**No charts have been added, removed, modified in stamping, or upgraded since the previous P0 audit.** The corpus is byte-stable in count and category for migration-readiness purposes.

---

## 8. What a "global migration" would actually do today

| Migration script step | Outcome on current corpus |
|------------------------|----------------------------|
| Iterate `db.charts.find({})` | 171 chart docs visited |
| For each chart, fetch parent user → `_parse_user_birth` | 168 succeed (canonical cohort); 3 fail (demo seeds, no birth data) |
| Skip charts already on canonical (`migration_marker == "variant-a-13-sign-migration-v1"`) | 168 skipped — "already canonical" |
| Recompute via `get_full_natal_chart` and update | **0 charts recomputed** |
| Counted as `skipped_no_birth_data` | 3 |
| Counted as `migrated` | 0 |
| Counted as `failed` | 0 |

**A global migration run today would be a no-op.** The 168 canonical charts are already canonical; the 3 demo seeds are ineligible by design.

---

## 9. Health observations (read-only — not blocking)

These were noticed during the census and are flagged here for awareness, not action:

1. **Inconsistent stamp surface for demo seeds.** Demo seeds carry their migration marker under `astrology.migration_marker` (embedded), whereas the canonical 168 carry it at the top-level `chart.migration_marker` PLUS embedded `astrology.metadata.astrology_engine_version`. The two cohorts use different fields for the same concept. This makes "is this chart migrated?" queries non-uniform — a query against top-level `migration_marker` shows 168/171 hits, but a query against embedded `astrology.migration_marker` shows 171/171 hits with two different marker values. Documented in the prior `ASTROLOGY_ANGLE_STALENESS_FORENSIC_AUDIT.md §4.3` as "stamp-vs-data drift."
2. **4 user rows without a chart** (`users.count() − charts.count() = 175 − 171 = 4`). These are not migration blockers (no chart → no migration target) but worth noting for separate cleanup if you want a 1:1 invariant.
3. **Demo-seed `angles = {}`.** Even if these were "migrated", they would still have no ASC/MC/IC/DC because `get_full_natal_chart` was never invoked. Any downstream code that assumes `astrology.angles.{asc,dc,mc,ic}` always populated will silently degrade on these 3 accounts. (Verified during the prior parity audit that the chat path doesn't crash on this; it just yields empty CHART SIGNALS angle rows for them.)

---

## 10. Constraints honored

| Constraint | Status |
|------------|--------|
| No data modified | ✅ |
| No charts recalculated | ✅ — `db.charts.find({})` is the only DB operation |
| No migration triggered | ✅ |
| No Mongo writes | ✅ — only `find` / `count_documents` |
| Read-only verification | ✅ |
| Locked flags untouched | ✅ — verified `.env`: `INTENT_ROUTER_V2_CUTOVER=false`, `INTENT_ROUTER_V2_ROLLOUT_PERCENT=10`, `RELATIONSHIP_ORCHESTRATION_PROMPT=false`, `CROSS_LENS_PROMPT_SURFACE=false` |

End of census.
