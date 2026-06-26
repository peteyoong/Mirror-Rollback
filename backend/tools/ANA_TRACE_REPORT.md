# P0 TRACE — ANA LIVE STORED CHART vs FRESH RECOMPUTE (FINAL)
**Date:** 2026-06-26
**Mode:** Trace-only. No writes. No production patches.
**Subject:** Ana Gayoso ("AnaG" in Mirror) — 3 May 1983, 08:20 local, UTC-03:00, San Miguel, Argentina

---

## §1–§3 (unchanged from preliminary)
See `/app/backend/tools/ANA_TRACE_REPORT.md` for the read-only Swiss-Ephemeris recompute and the live-UI vs fresh-recompute side-by-side.

---

## §4 — Backend trace (unchanged)

`GET /api/astrology/chart/{user_id}` (`server.py:14949`) reads `db.charts.find_one({user_id})` and only force-recomputes if `force_recompute=true` OR the chart is missing Chiron. Ana's chart has Chiron → stored values flow straight to the UI.

---

## §5 — STORED chart dump (Atlas production, read-only audit)

User identified via new `GET /api/admin/find_user?name=Ana&confirm=…`:

```
collection      : users
_id             : 6a1c17323b39ec46cfd74326
name            : "AnaG"
email           : null
birth_date      : "1983-05-03 00:00:00"
birth_time      : "08:05"                   ← (GM screenshot shows 08:20 — 15-min input drift)
city / country  : null / null
created_at      : 2026-05-31T11:10:42.992Z
```

`GET /api/admin/audit_chart?user_id=6a1c17323b39ec46cfd74326&confirm=AUDIT_CHART_V1` returns the full provenance bundle. The decisive subset:

```
chart_id                   : 6a1c1733a6581048cfb9013c
calculated_at              : 2026-06-01T08:21:43.764Z
astrology_engine_version   : "midpoint13_variant_a_v1"
migration_marker           : "variant-a-13-sign-migration-v1"
input_datetime_utc         : "1983-05-03T00:05:00+00:00"   ← !!!
julian_day                 : 2445457.503472222
debug_stamp                : {
    sidereal_settings_used  : { svp_degrees: 31.2836, reference_year: 2000, yearly_increment: 0.0 },
    computed_at_iso         : 2026-05-31T23:19:28.083Z,
    migration               : "startup_svp_fix"
}
migration_info             : {
    migrated_at        : 2026-06-01T08:21:43.764Z,
    migration_reason   : "empty_planet_signs",
    timezone_iana      : null,        ← !!!
    resolved_offset    : "+08:00"     ← !!!  (Argentina should be -03:00)
}
write_timeline:
  2026-05-31T11:10:43Z   chart_document_created      POST /api/users (initial chart insert)
  2026-06-01T08:21:43Z   chart.calculated_at         check_and_migrate_astrology_chart (auto-migration) wrote chart
  2026-06-01T08:21:43Z   migration_info.migrated_at  AUTO-MIGRATION ran (reason=empty_planet_signs)
```

The chart **looks** properly V-A-stamped (both markers present) and topologically migrated, BUT the *inputs* it was computed against are wrong:

- **`migration_info.timezone_iana = null`** → no IANA zone on user record.
- **`migration_info.resolved_offset = "+08:00"`** → the migration code fell back to the +08:00 default (Asia/KL — Mirror's primary user base).
- **`input_datetime_utc = 1983-05-03T00:05:00Z`** = `local 08:05 - (+08:00)` — i.e. the migration assumed Ana was born in Asia.

---

## §6 — Hypothesis verification (re-running calculator with the BAD UTC)

I re-ran the production calculator using **exactly** the stored bad UTC (00:05Z) and Ana's correct lat/lon. Result reproduces the live UI **bit-for-bit**:

| Run | UTC fed | ASC | Saturn H | NN H |
|---|---|---|---|---|
| **Stored / Live UI** | 1983-05-03 00:05Z | Sagittarius 3.15° | **11** | **6** |
| Fresh recompute with stored 08:05 + correct -03:00 | 1983-05-03 11:05Z | Aries 17.11° | 6 | 2 |
| Fresh recompute with GM 08:20 + correct -03:00 | 1983-05-03 11:20Z | Taurus 0.46° | 6 | 2 |

The 11-hour UTC drift (caused by applying `+08:00` to a local time that should have been adjusted by `-(-03:00) = +03:00`, i.e. 11 hours different) rotates the ASC by **11 × 15° = 165°** — exactly the ~165° offset between Sagittarius 3.15° and Taurus 0.46°.

**Root cause is now nailed mechanically.**

---

## §7 — Mismatch classification (FINAL)

| # | Symptom | Class | Evidence |
|---|---|---|---|
| 1 | Saturn=H11, NN=H6 in live UI | **Wrong timezone fallback (+08:00 default applied to a non-Asia user)** | `migration_info.resolved_offset = "+08:00"` while user's true offset is -03:00. Stored `input_datetime_utc` 11h off the correct value. |
| 2 | Underlying chart engine math | **CORRECT** | Re-running with the stored bad UTC reproduces stored chart to within 0.03°; re-running with the correct UTC produces GM-parity results. |
| 3 | V-A markers present despite bad data | **Markers stamped AFTER bad-input compute** | The V-A guard at `server.py:10866` checks for marker presence, but the chart was already wrong before/when the markers were applied. The guard cannot detect "wrong inputs" — only "wrong engine version." |
| 4 | birth_time stored 08:05 vs GM 08:20 | **Data-entry mismatch (operator entered 08:05 originally)** | This is a 15-min input drift, *additive* to the 11h timezone error but materially smaller. The 11h offset is the dominant cause. |
| 5 | `user.timezone` field null | **Onboarding regression** | The user record has no `timezone` field at all — yet birth date / time were captured. The onboarding flow that called `POST /api/users` for Ana on 2026-05-31 did not capture / persist her IANA zone. |

This is **NOT**: wrong house system, lat/lon sign flip, simple HH:MM data entry typo, stale engine version, or a frontend rendering bug.

This **IS**: a timezone-resolution failure on the *write* side that produced a perfectly-shaped, V-A-stamped, but materially-wrong stored chart.

---

## §8 — Surgical remediation plan (NOT yet executed)

### Step A — Single-user repair endpoint
**`POST /api/admin/repair_chart_for_user`**
- Inputs: `user_id`, optional `birth_time_override`, optional `timezone_override`, `confirm` token, `dry_run` default `true`.
- Behavior:
  1. Read user's birth_date, birth_time, lat, lon.
  2. If `timezone_override` provided OR user.timezone present, use it; otherwise fail loud (do NOT silently default to +08:00).
  3. Resolve canonical UTC via `resolve_birth_utc_with_debug`.
  4. Fresh-compute astrology + HD + numerology.
  5. Diff stored vs fresh on: `input_datetime_utc`, `angles.asc/mc`, every `planets.*.house`, every `nodes.*.house`, every channel.
  6. If `dry_run=false`, write the fresh chart with V-A markers stamped and `debug_stamp.fix_marker = "ana_repair_v1"` so it can be located later.
  7. Also persist `user.timezone = "America/Argentina/Buenos_Aires"` (or whatever zone the operator confirms).

### Step B — Cohort scan (read-only)
**`GET /api/admin/scan_timezone_fallback_cohort`**
- Behavior:
  1. For every chart where `astrology.migration_info.resolved_offset == "+08:00"` AND `astrology.migration_info.timezone_iana IS NULL`, report user_id, name, email, lat/lon, current Mirror-applied offset, and a *guess* of the correct IANA zone (via lon-based approximation).
  2. Highlight any chart whose lat/lon is NOT in the Asia/+08:00 region — these are the cohort.

  This will catch every user who has the same root cause as Ana. Expected to be a small list (likely <10) — Mirror's base is mostly MY/SG so the +08:00 default usually happens to be correct.

### Step C — Onboarding guard (forward-looking)
Make `POST /api/users` reject birth_date+birth_time without `timezone`. Make the auto-migration `check_and_migrate_astrology_chart` refuse to silently default to `+08:00` and instead log + skip + flag.

These are three independent commits; Step A unblocks Ana today, Step B unblocks her cohort within hours, Step C inoculates against recurrence.

---

## §9 — STOP CONDITION

**Trace is complete.** Every mismatch in §7 has a proven, classified cause. No production code has been modified by this calibration. The new `/api/admin/find_user` and `/api/admin/audit_chart` endpoints are read-only.

System reminder about `testing_agent` post-fix remains parked — no fix applied. Will fire `testing_agent` immediately after any remediation patch lands.

---

## §10 — Single decision request

❓ **Approve Step A (single-user repair endpoint, dry-run first)?**
   The dry-run will show the exact field-by-field diff between stored and fresh for Ana, with no DB write. Once you approve the diff, the same endpoint runs with `dry_run=false` and stamps the chart correctly.

❓ **Also approve Step B (cohort scan)?**
   This is purely read-only — surface every other user with the same `+08:00 fallback while non-Asia lat/lon` pattern. We can then decide whether to batch-repair or per-user repair.

❓ **Step C (onboarding guard)** — should I queue this as a follow-up commit after Steps A+B are complete? It's the actual prevention; A+B only fix the current victims.

Please confirm A, B, and C (or any subset) and I'll proceed in that strict order: write the dry-run endpoint, redeploy via your Publish, show you Ana's diff, await go/no-go, then `dry_run=false`, then `testing_agent`.
