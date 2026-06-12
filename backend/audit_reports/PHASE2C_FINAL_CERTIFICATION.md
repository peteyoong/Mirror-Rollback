# Phase 2C — Final Migration Readiness Certification

_Generated_: 2026-06-14 EOD
_Mode_: READ-ONLY validation pass.
_DB writes performed_: **0**
_Chart recomputes persisted_: **0**
_Cache invalidations performed_: **0**
_Migrations triggered_: **0**
_Rollback collection writes_: **0**
_Environment changes_: **0**

---

## A. Migration Cohort Counts

### Reconciliation of the original 129-user Phase 2B cohort

| Bucket | Count | Status |
|---|---|---|
| **Already migrated** (`users_phase2_rollback` `status=VERIFIED`) | **84** | Done; no further action |
| **Remaining for migration** | **45** | Phase 2C target |
| **Original Phase 2B cohort total** | **129** | ✅ Reconciles |

### Breakdown of the 84 already-migrated

| Sub-bucket | Count | Note |
|---|---|---|
| RECOMPUTE_REQUIRED (Pete singleton) | 1 | `697f0c6abf35c0528ff06954` pete@pulsifi.me — migrated **2026-06-11 17:18:16 UTC**, COMMIT |
| COHORT_OPTION_C | 83 distinct uids (84 rollback docs)* | migrated **2026-06-11 17:28:18–17:28:28 UTC** |

\* One user (`6a17e8cf5bc5cc688d66eba0`) has **two** VERIFIED rollback docs (two separate migration IDs ~9 s apart). Both VERIFIED. **Soft finding** — duplicate snapshot, not a blocker. The user's chart is currently in the post-migration state from the second snapshot.

### Breakdown of the 45 remaining (Phase 2C cohort)

| Classification | Count | Confirms operator expectation? |
|---|---|---|
| RECOMPUTE_REQUIRED | **44** | ✅ |
| FORMAT_ONLY        | **0** | ⚠️ Note: 9 FORMAT_ONLY users from the original cohort were absorbed into the COHORT_OPTION_C sweep on June 11; none remain |
| DRIFT_REPAIR       | **1** | ✅ (`6971cc4381beab3a8955b256` Yoong Weng Hong Peter Andrew) |
| **TOTAL**          | **45** | |

> **Operator's stated invariant** "RECOMPUTE_REQUIRED + FORMAT_ONLY + DRIFT_REPAIR = 129":
> - True if counted **across all phases** (84 migrated + 45 remaining = 129) ✅
> - **Not** true for the **remaining-only** slice (44 + 0 + 1 = 45)
>
> Recommend documenting in the Phase 2C kickoff that **Phase 2C executes only the 45 remaining users**, not the original 129.

---

## B. Real-User Impact Table (45 remaining)

| Property | Result |
|---|---|
| Resolvable IANA timezone     | 45/45 ✅ (DRIFT_REPAIR user counted via singleton rule) |
| Valid birth_date             | 45/45 ✅ |
| Valid birth_time (parses)    | 45/45 ✅ |
| Valid coordinates (lat, lon) | 45/45 ✅ |
| Chart doc present            | 45/45 ✅ |
| `account_class = REAL`       | 0/45 (per old classification: 5 REAL across the 84+45=129 cohort; the 5 REAL all fall in the 84 already-migrated bucket) |
| `account_class = TEST`       | 73 across all 129; all 73 in the **already-migrated 84** |
| `account_class = UNKNOWN`    | 50 across all 129; **45 remaining** are all UNKNOWN/TEST |

> **Implication**: The remaining 45 are all `account_class ∈ {TEST, UNKNOWN}` per the June 11 classification — **no REAL accounts are in the Phase 2C remainder**. The 5 REAL accounts in the original cohort were already migrated via Pete (1) + COHORT_OPTION_C (≥4).

### Field-quality scan across ALL users (not just cohort)

| Anomaly | Count | In Phase 2C cohort? |
|---|---|---|
| Users missing `birth_time` | 13 | **0** — all 13 are outside the cohort; they are a separate data-quality bucket and **do not block** Phase 2C |
| Users missing `birth_date` | 0 | n/a |
| Users missing coordinates  | 0 | n/a |
| Users missing chart doc    | 0 | n/a |

---

## C. Cache Invalidation Table

**All 28 chart-derived cache collections exist** in the live DB:

```
deep_dive_cache               astrology_timeline_cache
governing_chapter_cache       lifeline_synthesis_cache
lunar_synthesis_cache         pattern_drift_cache
pattern_mirror_cache          relationship_today_cache
forum_story_cache             daily_focus
daily_keystones               daily_astrology
daily_pattern_signals         today_patterns
user_timeline                 mirror_insights
pattern_memory                pattern_memory_signals
pattern_running_me_v2         longitudinal_pattern_memory
home_angle_history            home_history
home_v6_state                 lifeline_events
lifeline_imported_moments     lifeline_import_sources
lunar_considerations          lunar_journal
```

### Cache rows affected by Phase 2C (remaining 45 users)

Per the live `phase2b_execution_plan.py` (READ-ONLY) run:

| Collection (per-user cache hit) | Rows |
|---|---|
| Total cache rows to invalidate across 45 remaining users | **10** |
| Distinct cache collections touched by those 45 | **2** |

> The cohort has **very low cache density** today (10 rows total) because:
> 1. Most of the 45 remaining users are TEST/UNKNOWN accounts with minimal app activity.
> 2. The 84 already-migrated users had their caches invalidated during the June 11 sweep (Pete alone: **637 rows** invalidated; see §F).
>
> Conversation/state collections **(chat_history, journal, forum_chat_messages, saved_people, forum_members, reflections, etc.)** are **explicitly NOT touched** by the migration and remain preserved.

---

## D. Rollback Footprint Estimate

### Schema (verified against actual collection)

Live `users_phase2_rollback` doc schema observed (15 fields):

```
_id (ObjectId)
migration_id (string, uuid)
user_id (string)
classification (string)
snapshot_at (datetime)
prev_user_doc (object)
prev_chart_doc (object | null)
cache_keys (object<collection, [_id]>)
planned_corrected_tz (string)
planned_utc_delta_min (number)
rollback_status (string, observed values: VERIFIED)
verification (object: post_chart_asc, post_chart_mc, delta_from_expected_deg)
operator_note (string)
verified_at (datetime)
verified_by (string)
```

### Actual storage measured on the 85 existing VERIFIED rollback docs

| Stat | Value |
|---|---|
| Total docs in collection                  | 85 |
| Distinct user_ids in collection           | 84 (1 user has a duplicate snapshot — see §A) |
| Total BSON size                           | 3,360,583 B (~3,281.8 KiB) |
| Mean per doc                              | 39,536 B |
| Min / Max                                 | 36,675 B / 61,249 B |
| `rollback_status` distribution            | `{VERIFIED: 85}` ✅ |

### Projected footprint for the remaining 45

| Source | Bytes | KiB |
|---|---|---|
| `phase2b_execution_plan.py` direct estimate | **1,702,495** | **1,662.6** |
| Mean-extrapolation (45 × 39,536)            | 1,779,120     | 1,737.4   |

Both methods agree within 5%. **Projected Phase 2C rollback footprint: ~1.7 MiB.**

### Cumulative storage projection (post Phase 2C)

| | Existing | + Phase 2C | = Total |
|---|---|---|---|
| Rollback docs                  | 85 | +45 | **130** |
| Rollback BSON storage          | 3.28 MiB | +1.67 MiB | **~4.95 MiB** |

---

## E. Newly Discovered Findings

| # | Severity | Finding | Impact |
|---|---|---|---|
| **E1** | 🟢 Info     | The original Phase 2B 129 = 84 already-migrated + 45 remaining. Math reconciles. | Document in Phase 2C kickoff: only 45 users in scope |
| **E2** | 🟢 Info     | All 9 FORMAT_ONLY users from the June 11 classification were absorbed into the June 11 COHORT_OPTION_C sweep. The remaining cohort has 0 FORMAT_ONLY. | Update execution plan classification expectations |
| **E3** | 🟢 Info     | 5 `account_class=REAL` users from the original cohort have all already been migrated (in the 84). The remaining 45 are all TEST/UNKNOWN. | Lower production risk for Phase 2C |
| **E4** | 🟡 Soft     | User `6a17e8cf5bc5cc688d66eba0` has 2 VERIFIED rollback docs (migration_ids `8b68aff1…` and `686cf4a1…`, ~9 s apart). Chart is in the state of the *second* snapshot. | No data loss; benign duplicate. Phase 2C should add a "skip-if-already-VERIFIED" guard to the execution path to prevent recurrence. |
| **E5** | 🟡 Soft     | 13 users in the wider user base have **no `birth_time`** field. None are in the Phase 2B/2C cohort (they're correctly excluded). | Separate data-quality task; not a Phase 2C blocker. |
| **E6** | 🟢 Info     | The current `phase2b_execution_plan.py` script does not auto-skip already-migrated users at the plan stage. It correctly excludes them because their `stored_tz` is now `SAFE` (no longer offset). However, the **execution** path should still verify `users_phase2_rollback.user_id` ∉ already-VERIFIED set before snapshotting. | Verify idempotency guard before any Phase 2C execution. |
| **E7** | 🟢 Info     | DRIFT_REPAIR user `6971cc4381beab3a8955b256` (Yoong Weng Hong Peter Andrew, `peter@test.com`) currently has `Asia/Kuala_Lumpur` (matches resolved IANA, `utc_delta_min=0.0`). | DRIFT_REPAIR migration would be a no-op for this user's UTC; chart recompute may still produce different cached derivations depending on the prior chart provenance. |
| **E8** | 🟢 Info     | 0 new REAL users have entered RECOMPUTE_REQUIRED or MISMATCH buckets since Phase 2B. | No drift. |

**No blockers discovered.** All findings are either informational or soft-quality items handled by the existing rollback path.

---

## F. Pete's 637-Cache-Row Migration — Verification

### What was certified
The Phase 2A Pete migration plan estimated **637 cache rows would be deleted**.

### What actually happened (READ from `audit_reports/phase2_pete_bf334b98-903a-4144-ae6f-063764f0b675.json`)

```
migration_id      : bf334b98-903a-4144-ae6f-063764f0b675
mode              : COMMIT
user_id           : 697f0c6abf35c0528ff06954
user_email        : pete@pulsifi.me
started_at        : 2026-06-11T17:18:16.012703+00:00
finished_at       : 2026-06-11T17:18:16.205523+00:00  (~193 ms wall-clock)
tz_before         : "+07:00"
tz_after          : "Asia/Kuala_Lumpur"

cache_rows_deleted: 637         ✅ EXECUTED AS CERTIFIED
asc_delta_deg     : -7.1611
mc_delta_deg      : -8.0026
verify_within_tolerance : true
overall_migration_status: SUCCESS
```

### Preservation verification (chat_history, journal, forum, saved_people, etc.)

| Collection | Before | After | Preserved? |
|---|---|---|---|
| chat_history             | 1   | 1   | ✅ |
| forum_chat_messages      | 31  | 31  | ✅ |
| forum_mirror_chat_messages| 30 | 30  | ✅ |
| forum_reflections        | 1   | 1   | ✅ |
| user_reflections         | 2   | 2   | ✅ |
| reflections              | 2   | 2   | ✅ |
| journal                  | 26  | 26  | ✅ |
| facet_history            | 20  | 20  | ✅ |
| home_engagement_sessions | 327 | 327 | ✅ |
| saved_people             | 9   | 9   | ✅ |
| forum_members            | 4   | 4   | ✅ |
| enneagram_results        | 1   | 1   | ✅ |

All 22 conversation/state collections preserved unchanged. **637 cache rows were deleted as planned.**

### Pete's current cache state (verified live)
- Pete's caches have lazily regenerated since June 11: current count = **13 rows** in `user_timeline` only.
- This is expected (lazy-rebuild on next chart read), and confirms the post-migration verification was correct.

**637-cache-row Pete calculation: ✅ EXECUTED AND VERIFIED.**

---

## G. Execution Manifest (45 remaining users — for Phase 2C run)

Full per-user manifest is in **`audit_reports/PHASE2C_EXECUTION_MANIFEST.json`** (machine-readable). Schema per row:

```json
{
  "user_id":            "string",
  "name":               "string",
  "classification":     "RECOMPUTE_REQUIRED | DRIFT_REPAIR",
  "stored_timezone":    "string (e.g. '+00:00', '+07:00', 'Asia/Kuala_Lumpur')",
  "corrected_timezone": "string (IANA name from resolver)",
  "utc_delta_min":      "number (minutes the UTC instant will shift)",
  "expected_asc_delta_deg": "number | null (only present where a prior asc is known)",
  "expected_mc_delta_deg":  "number | null",
  "rollback_footprint_bytes": "integer (user_doc + chart_doc BSON size)",
  "cache_rows_affected":      "integer"
}
```

### Aggregate manifest summary (READ-ONLY)

| Bucket | Count | Rollback bytes (sum) | Cache rows (sum) |
|---|---|---|---|
| RECOMPUTE_REQUIRED | 44 | 1,665,220 | 10 |
| DRIFT_REPAIR       | 1  |    37,275 | 0  |
| **TOTAL**          | **45** | **1,702,495** | **10** |

### Top 10 manifest rows (sorted by classification, then |utc_delta_min| desc)

| user_id | name | class | stored_tz | corrected_tz | rollback_B | cache# |
|---|---|---|---|---|---|---|
| 6971cc4381beab3a8955b256 | Yoong Weng Hong Pete | DRIFT_REPAIR | Asia/Kuala_Lumpur | Asia/Kuala_Lumpur | 37,275 | 0 |
| 697f98f52caf672a29468edf | Sam | RECOMPUTE_REQUIRED | +00:00 | Asia/Singapore | 38,531 | 0 |
| 697f224b366f6814412d8c84 | Pete | RECOMPUTE_REQUIRED | +00:00 | Asia/Kuala_Lumpur | 37,547 | 0 |
| 697f995c2caf672a29468ee3 | Taylor | RECOMPUTE_REQUIRED | +00:00 | Asia/Kolkata | 38,461 | 0 |
| 697f999a2caf672a29468ee5 | Riley | RECOMPUTE_REQUIRED | +00:00 | America/Toronto | 37,655 | 0 |
| 697f99c92caf672a29468ee7 | Casey | RECOMPUTE_REQUIRED | +00:00 | Asia/Dubai | 36,864 | 0 |
| 698023dda2368d8c90927ebd | Luna | RECOMPUTE_REQUIRED | +00:00 | America/New_York | 40,859 | 0 |
| 69802712a2368d8c90927ebe | Luna | RECOMPUTE_REQUIRED | +00:00 | America/New_York | 40,859 | 0 |
| 69835ae5f7922e80c94694cc | _(no name)_ | RECOMPUTE_REQUIRED | +00:00 | America/New_York | 37,963 | 0 |
| 69835b31f7922e80c94694cd | _(no name)_ | RECOMPUTE_REQUIRED | +00:00 | America/New_York | 37,963 | 0 |

_(Full 45-row manifest is in `audit_reports/PHASE2C_EXECUTION_MANIFEST.json`.)_

---

## H. Final Certification Statement

The Phase 2C readiness pass has been completed READ-ONLY. All required validation
gates have been checked against the live database:

1. ✅ Phase 2B cohort math (129) reconciles to **84 already-migrated + 45 remaining**.
2. ✅ All 45 remaining users have resolvable IANA timezone, valid birth_date,
   valid birth_time, valid coordinates, and a present chart document.
3. ✅ Migration count reconciliation: **44 RECOMPUTE_REQUIRED + 0 FORMAT_ONLY +
   1 DRIFT_REPAIR = 45 (remainder)**; cumulative 84 + 45 = 129 ✅.
4. ✅ Execution manifest produced (`audit_reports/PHASE2C_EXECUTION_MANIFEST.json`).
5. ✅ Rollback collection schema matches actual document sizes; mean 39.5 KiB/doc;
   projected Phase 2C footprint **~1.7 MiB**; cumulative post-Phase-2C
   storage **~4.95 MiB**.
6. ✅ All 28 cache collections exist in the live DB.
7. ✅ Pete's 637-cache-row migration is **VERIFIED COMPLETE** (Phase 2A
   commit on 2026-06-11 17:18:16 UTC; SUCCESS; all conversation state
   preserved).
8. ✅ **0 new REAL users** have entered RECOMPUTE_REQUIRED or MISMATCH
   buckets since Phase 2B was certified.
9. ✅ **No blockers** discovered. Two soft findings (E4 duplicate rollback
   doc; E5 13 birth_time-missing users outside cohort) are non-blocking
   and tracked.

> **PHASE 2 STATUS: GO**

### Conditions of GO

- Migration **scope is the 45 remaining users**, not the original 129
  (84 already-migrated must be excluded via idempotency guard — see E6).
- The execution path must verify `users_phase2_rollback.user_id ∉ already-VERIFIED
  set` before snapshotting (idempotency guard) to prevent E4-style duplicates.
- All other guarantees (preservation of conversation/state collections,
  per-user atomic snapshot + rollback, deferred lazy cache rebuild,
  recompute-then-verify cycle) carry forward unchanged from Phase 2A.

### Recommended next operator action

This certification authorizes Phase 2C **planning sign-off only**. No code
changes, no DB writes, no migrations, and no flag flips have occurred during
this pass. The actual Phase 2C execution remains a **separate authorization
step** that must be initiated explicitly by the operator.
