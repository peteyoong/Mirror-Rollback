# P0 TRACE — ANA LIVE STORED CHART vs FRESH RECOMPUTE
**Date:** 2026-06-26
**Mode:** Trace-only. No writes. No patches.
**Subject:** Ana Gayoso — 3 May 1983, 08:20 local, UTC-03:00, San Miguel, Argentina
  (58°42'44"W, 34°32'36"S → lon = -58.712222, lat = -34.543333)

---

## 0. Live-UI screenshot (what the user sees)

> **DEVELOPMENTAL PRESSURE**
> SATURN — **House 11: community**
> NORTH NODE — **House 6: work & health**

---

## 1. Fresh recompute (current production calculator, locally invoked)

Run via `calculations.astrology.get_full_natal_chart` with the exact stated sidereal config
(`SVP=31.2836`, `reference_year=2000`, `yearly_increment=0.0`, `mode="true_sidereal_user_defined"`,
house_system `"Equal"`):

```
engine_version: midpoint13_variant_a_v1
svp_applied:    31.2836
coordinates:    {lat: -34.543333, lon: -58.712222}
house_system:   Equal
```

### Angles (fresh)
| | sign | deg-in-sign | longitude |
|---|---|---|---|
| **ASC** | Taurus | 0°28' | 20.1934° |
| MC | Aquarius | 3°52' | 298.7070° |
| DC | Libra | 8°52' | 200.1934° |
| IC | Leo | 15°31' | 118.7070° |

### House cusps (Equal — fresh)
| H | longitude | sign |
|---|---|---|
| 1 | 20.193 | Taurus 0°28' |
| 2 | 50.193 | Taurus 30°28' |
| 3 | 80.193 | Gemini 23°36' |
| 4 | 110.193 | Leo 7°00' |
| 5 | 140.193 | Leo 37°00' |
| 6 | 170.193 | Virgo 28°35' |
| 7 | 200.193 | Libra 8°52' |
| 8 | 230.193 | Ophiuchus 6°46' |
| 9 | 260.193 | Sagittarius 24°25' |
| 10 | 290.193 | Capricorn 20°56' |
| 11 | 320.193 | Pisces 2°11' |
| 12 | 350.193 | Pisces 32°11' |

### Key planet placements (fresh)
| body | sign | deg | long | **house** |
|---|---|---|---|---|
| Sun | Aries | 11°25' | 11.42° | **12** |
| Moon | Sagittarius | 27°20' | 263.12° | **9** |
| Mercury | Taurus | 4°38' | 24.37° | **1** |
| Venus | Taurus | 32°27' | 52.17° | **2** |
| Mars | Aries | 19°22' | 19.36° | **12** |
| Jupiter | Scorpio | 7°43' | 217.91° | **7** |
| **Saturn** | **Virgo** | **37°35'** | **179.20°** | **6** ← |
| Uranus | Scorpio | 6°53' | 217.07° | **7** |
| Neptune | Sagittarius | 2°08' | 237.91° | **8** |
| Pluto | Virgo | 35°05' | 176.69° | **6** |
| **North Node** | **Taurus** | **35°07'** | **54.85°** | **2** ← |
| South Node | Ophiuchus | 11°26' | 234.85° | **8** |
| Chiron | Taurus | 5°46' | 25.50° | **1** |

---

## 2. Comparison — live UI vs fresh recompute

| Field | LIVE UI | FRESH RECOMPUTE | Δ |
|---|---|---|---|
| Saturn house | **11** | **6** | **5-house shift** |
| North Node house | **6** | **2** | **4-house shift** |

These are gross-shift mismatches — not "boundary noise". For a planet at longitude 179° to be in H11 under Equal houses, the ASC would have to be around **239°** (Sagittarius); the fresh ASC is **20.19°** (Taurus). The stored chart and the current calculator disagree by approximately **219° of ASC rotation** — i.e. an entirely different rising sign.

---

## 3. Reverse-engineering possible causes

I swept the obvious input-mistake hypotheses and computed Saturn/NN houses for each:

| variant | ASC | Saturn H | NN H |
|---|---|---|---|
| **correct** | Taurus 0.46° | **6** | **2** |
| latitude sign flipped (+34.54) | Taurus 28.99° | 5 | 1 |
| longitude sign flipped (+58.71) | Virgo 6.34° | 2 | 9 |
| both signs flipped (+,+) | Virgo 6.69° | 2 | 9 |
| UTC = local (08:20 not 11:20) | Pisces 24.92° | 7 | 3 |
| UTC = local + 3 (05:20) | Aquarius 10.32° | 8 | 4 |
| UTC = local + 6 (17:20) | Leo 4.76° | 3 | 11 |
| Placidus instead of Equal | Taurus 0.70° | 6 | 2 |

**None of the single-input flips reproduce the live UI values (Saturn=11, NN=6).** The live values correspond to ASC ≈ Sagittarius / Ophiuchus boundary — which I could NOT generate from any reasonable single-variable distortion.

This rules OUT:
- ❌ Wrong house system (Placidus gives the same answer for Ana).
- ❌ Lat/lon sign flip.
- ❌ Simple UTC offset error.

It strongly implies the stored chart was either:
1. Computed with a fundamentally different birth time / date, OR
2. Computed under an older sign-attribution / house-numbering scheme where the cusps had different mappings, OR
3. Belongs to a different person whose user_id was overwritten onto Ana's row, OR
4. Has corrupted/stale `planets.*.house` integer fields that don't match its own house cusps.

The DB read in §4 will distinguish these.

---

## 4. Backend trace — which surface reads which path

The "Developmental Pressure" card consumes:
```ts
B = placements.saturn_house        // frontend: AstrologyAtAGlanceTab.tsx
D = placements.north_node_house
```
The `placements` object is built by `getPlacements(chartData)` in `frontend/services/astrology/astrologyInterpreter.ts:1170-1194`, which reads:
```
planets?.Saturn?.house
nodes?.north?.house
```
on `chartData.natal`.

`chartData` is fetched by `dominantTruthService.ts` →
```
GET /api/astrology/chart/{user_id}
```
The backend handler at `server.py:14949` does the following:

```python
user, chart = await get_user_astrology_data(user_id)       # READS db.charts
astro = chart.get('astrology', {})
needs_recompute = force_recompute or not astro.get('planets', {}).get('Chiron')
if needs_recompute:
    ... # fresh compute, writes to DB
# returns `astro` (stored OR freshly computed)
```

**So the card is reading the STORED chart in `db.charts`** unless the caller passed `force_recompute=true` OR the stored chart pre-dates Chiron support (which is unlikely — V-A migration backfilled Chiron).

**Therefore the live UI is rendering a stale stored value.** This is the same class of issue as the Mel Gemini-Rising regression: stored chart drifted away from what the current calculator produces, and the migration guard either ran with bad inputs or was never re-stamped after the engine changed.

---

## 5. DB-side trace (BLOCKED — needs `user_id`)

To complete steps 2 and 4 of the original ask I need to dump `db.charts.find_one({user_id: ANA_USER_ID})` from production. The read-only audit endpoint is in place:

```
GET https://mirror-lens-fixes-r-1779710763.emergent.host/api/admin/audit_chart
        ?user_id=<ANA_USER_ID>
        &confirm=AUDIT_CHART_V1
```

This will return:
- `astrology.metadata` (`zodiac_mode`, `input_datetime_utc`, `julian_day`, `house_system`)
- `astrology.angles` (`asc`, `mc`, `dc`, `ic`) with longitude + sign
- `astrology.houses` (or stored equivalent)
- `planets.Saturn.house`, `planets.Saturn.sign`, `planets.Saturn.degree`, `planets.Saturn.longitude`
- `nodes.north.house`, full equivalent
- `astrology_engine_version`, `migration_marker`
- `chart_updated_at`, `updated_at`, `calculated_at`, `migration_info.migrated_at`
- `debug_stamp` (cohort repair audit trail if it ever ran)
- Provenance write-timeline (which write last touched this chart, and from which code path)

I cannot run it until you provide Ana's `user_id`.

---

## 6. Mismatch classification (preliminary, pending §5)

| | Symptom | Most-likely class |
|---|---|---|
| 1 | Stored Saturn.house = 11 vs computed 6 | **Stale stored chart** (engine-recompute would produce 6). Confirmed by frontend reading stored cache. |
| 2 | Stored NN.house = 6 vs computed 2 | **Stale stored chart** (same root cause). |
| 3 | ASC mismatch implied by the 5-house Saturn shift | **Stale stored chart** *(NOT* wrong house system, lat/lon sign flip, or simple UTC error — proven by the sweep in §3). |

**Not yet ruled out** (will be after §5 DB dump):
- Did the previous TZ cohort repair touch Ana? (debug_stamp absent ⇒ no)
- Was the chart last written by `check_and_migrate_astrology_chart` AFTER any V-A migration? (`migration_info.migrated_at` newer than V-A version stamp ⇒ yes, the auto-migration overwrote the V-A-correct chart with stale logic).
- Are the stored house integers internally consistent with the stored cusps + planet longitudes?
  (If `house_for_planet(stored_long, stored_cusps) == stored_house` for all bodies, the stored chart is *self-consistent* but generated from wrong inputs. If they disagree, the chart is *corrupted* — house integers were written separately from longitudes.)

---

## 7. Proposed surgical remediation (do not execute yet)

Two-step plan, both read-first then narrowly-targeted writes:

### Step A — Single-user repair endpoint (`/api/admin/repair_chart_for_user`)
**Confirm token, dry_run default true.** For a given `user_id`:
1. Read user's birth inputs (date, time, timezone, lat, lon).
2. Resolve canonical UTC via `resolve_birth_utc_with_debug`.
3. Fresh-compute astrology, HD, BaZi, numerology.
4. Diff stored vs fresh: list every field that differs (house ints, longitudes > 0.1° drift, sign labels, gate.line).
5. If `dry_run=false`, write the fresh chart with `astrology_engine_version = midpoint13_variant_a_v1` and `migration_marker = variant-a-13-sign-migration-v1` stamped to inoculate against the auto-migration overwrite.
6. Stamp `debug_stamp.fix_marker = "ana_repair_v1"` so the cohort-scan endpoint can find it.

### Step B — Cohort drift scan (`/api/admin/scan_house_drift_cohort`)
**Read-only.** For every chart in `db.charts`:
1. Recompute fresh from user inputs.
2. Compare stored vs fresh — flag any chart where any `planets.*.house` or `nodes.*.house` differs from the recompute.
3. Return JSON: `total_scanned`, `house_drift_count`, per-user delta list (user_id, name, email, fields that drift, drift magnitude).
4. Operator reviews the delta list, then can call Step A surgically per-user or in batch.

This is essentially the same shape as `fix_historical_tz_cohort` but keyed off **house integers** rather than **UTC drift**. The TZ-cohort scan caught the time-input issues; this scan would catch the engine-version / migration-leak issues that survived.

---

## 8. STOP CONDITION

**Trace is complete on the read-side (steps 1, 3, 6 of the request).**
Steps 2, 4 (DB-side dump and §5 mismatch row) cannot be completed without Ana's `user_id`.

**No production code has been modified. No DB writes.**

The system reminder about `testing_agent` post-fix is not applicable here — no fix has been applied. I will invoke `testing_agent` immediately after any code patch lands.

---

## 9. Single question to unblock

❓ **What is Ana Gayoso's `user_id` in production?**

(Once provided, I'll call the audit endpoint and update §5 with the stored field values, finalize §6, and then bring the surgical repair endpoint proposal back for your approval.)
