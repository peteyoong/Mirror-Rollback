# Timezone Integrity Initiative — Final Closure Postmortem

> **Status:** CLOSED — full cohort migrated, write paths hardened, monitoring in place.
> **Audience:** Engineers, on-call, future maintainers, security/compliance reviewers.
> **Last update:** 2026-06-14 EOD (Phase 2C execution closed at 2026-06-12 03:11 UTC).
> **Owner:** Track 4 (Data Integrity).
> **Scope:** All `users.timezone`, `charts.astrology`, `charts.human_design`, and dependent chart-derived caches in the production database.

---

## 0. TL;DR

A class of latent timezone defects in user onboarding (silent acceptance of
client-supplied offsets, no coordinate→IANA enforcement, and a legacy hardcoded
`estimate_timezone(longitude)` writer) produced incorrect natal charts for
**129 users**. The problem was discovered while investigating the **AnaG**
regression case, surfaced through Phase 18 impact analysis, hardened in the
write path during Phase 19, and fully remediated across three execution
phases (2A → 2B → 2C). The full 129-user cohort is now migrated with
verified Δasc/Δmc = 0.0° against in-memory recompute, with per-user atomic
rollback records and untouched conversation/state data. Permanent guardrails
(coord→IANA resolver, IANA-only persistence, write-path tests,
`tz_provenance` flag, and admin integrity endpoint) are now in place.

---

## 1. Original Defect

### 1.1 The two clusters

| Cluster | Description | Population | Symptom |
|---|---|---|---|
| **`+00:00` cluster** | Users whose stored `timezone` was the bare offset `"+00:00"` despite living far from UTC longitudes. Common pattern: client onboarding code sending UTC offset of the *device* (often a CI runner or a US-defaulted dev environment) instead of resolving from coordinates. | 73 users | Natal chart computed with wrong UTC anchor; ascendant/MC shifts of **±8°** to **±12°** depending on longitude; wrong house placements for ~70% of cusp planets. |
| **`+08:00` cluster** | Users whose stored `timezone` was `"+08:00"` (SGT/CST/MYT/AWST) when the actual coordinate-resolved zone was a different IANA name (Asia/Kuala_Lumpur vs Asia/Singapore vs Asia/Shanghai vs Australia/Perth). Subtler than `+00:00` because the UTC math is correct **today** but the IANA name carries **DST history**, which Asia/Kuala_Lumpur (no DST), Asia/Singapore (no DST), Asia/Shanghai (no DST), and Australia/Perth (rare DST) handle differently. | 11 users (mostly Pete-named test accounts + canonical Pete prior to remediation) | Charts computed correctly for post-1982 births but incorrect for **any historical date** where regional DST or zone-boundary changes apply. Particularly bad for Pete's 1968 chart (Singapore time changed from GMT+7:30 to GMT+8:00 in 1981; pre-1982 events need GMT+7:30 — see §6.2). |

### 1.2 The AnaG discovery

The investigation was triggered by the **AnaG regression case** (Ana G., a
regression reference account). Symptoms reported by the operator:

- Ana's natal chart rendered with planets in different houses across two
  consecutive app loads.
- The forum reflection generated for Ana referenced a Sun house that didn't
  match the deep-dive view.
- Manual recomputation against a Swiss-ephemeris baseline showed a ~7° ascendant
  shift vs. the stored chart.

Root inspection of Ana's user document revealed:
- `birth_location.latitude/longitude` — correct (Buenos Aires).
- `timezone` — stored as `"-03:00"` (offset, not IANA).
- `tz_provenance` — absent (no flag indicating which writer set the field).
- `charts.{user_id}` — last `updated_at` ~6 weeks old, recomputed during a
  feature that has since been removed.

Cross-referencing Ana's stored UTC anchor against the timezonefinder library's
resolution of her coordinates showed `"-03:00"` (no IANA) was being persisted
where `"America/Argentina/Buenos_Aires"` (with full historical zone changes
from 1969/1974/1988/1999/2008) should have been.

> AnaG was not unique. The same pattern affected 128 other users.

### 1.3 Historical onboarding behaviour

The investigation surfaced **three historical onboarding paths**, each with
a different timezone-writing strategy:

| Path | Origin | Writer | Failure mode |
|---|---|---|---|
| **Path A** (mobile onboarding) | `POST /api/users/onboard` | Frontend sent `timezone` field directly from `Intl.DateTimeFormat().resolvedOptions().timeZone` (IANA — correct format) **OR** from `new Date().getTimezoneOffset()` (offset — wrong) depending on device + browser fingerprint. | Devices with locked locales or older OSes returned offset, which the backend silently persisted. |
| **Path B** (web onboarding) | `POST /api/auth/register` | Backend ran the legacy `estimate_timezone(longitude)` helper — `floor(longitude / 15)` → bare offset like `"+07:00"`. This is mathematically wrong for any country whose political timezone deviates from its solar meridian (Argentina, India, China, Newfoundland, parts of Russia, etc.). | The 73-user `+00:00` cluster came almost entirely from this path. |
| **Path C** (admin import / seed scripts) | `seed_users.py`, `e2e_create_user.py`, RL probe scripts | Hardcoded `"+08:00"` regardless of coordinates (most seed scripts targeted Kuala Lumpur users; the maintainer set offset, not IANA). | Created the `+08:00` cluster of 11 Pete-named test accounts. |

All three paths persisted directly to `users.timezone` with **no
provenance, no validation, no coord→IANA enforcement**.

---

## 2. Root Cause Analysis

### 2.1 Client-supplied timezone acceptance (Path A)

The backend trusted `request.body.timezone` as authoritative without:
- Verifying the string was a valid IANA name (it accepted both IANA names AND
  bare offsets).
- Cross-checking against `birth_location.{latitude, longitude}`.
- Persisting *who set the field* (no `tz_provenance` flag).

This means a single mobile client running on an older Android with a
locale-broken `Intl` would persist `"+05:30"` indefinitely, and downstream
chart math would silently use the offset, masking the actual IANA zone
(Asia/Kolkata, with its 1942–1945 wartime variation and pre-1941 +05:21:10
offset).

### 2.2 Lack of coord→IANA enforcement

Even on the paths where the backend *could* have resolved the correct timezone
(coordinates are required at onboarding), there was no call to a coord→IANA
resolver. The legacy `estimate_timezone(longitude)` function was a
**pre-database approximation** — `int(longitude / 15)` — accurate only for
countries whose political timezone follows their solar meridian. This is
**wrong** for at least:

- Argentina (`-03:00` despite longitudes spanning `-58°` to `-73°`)
- India (`+05:30` — half-hour, not on the 15° grid)
- China (`+08:00` across longitudes `73°` to `135°` — most of China is solar-misaligned)
- France (`+01:00` despite Paris being on the `+0:09` meridian)
- Spain (`+01:00` despite Madrid being on the `-0:15` meridian)
- Newfoundland (`-03:30` — half-hour)
- Nepal (`+05:45` — quarter-hour)

For users in any of these regions, `estimate_timezone(longitude)` is silently
incorrect. The defect was hidden because:
- Most app surfaces show **only the final synthesized text**, not the raw UTC instant.
- House calculations are tropical (sign placements look "close enough" for
  hours-scale errors).
- Aspect calculations are degree-based and tolerate small absolute errors as
  long as **both** planets shift together (which they do under a wrong UTC
  anchor — preserving the *aspect structure* but rotating it on the house
  wheel).

### 2.3 Legacy hardcoded timezone writers

Three call sites wrote `users.timezone` with **hardcoded offsets**:

| File (legacy) | Writer | Offset written |
|---|---|---|
| `seed_users.py` | seed script for canonical Pete + Mel | `"+08:00"` |
| `e2e_create_user.py` | E2E test user factory | `"+00:00"` (default UTC) |
| `tools/rl_probe_seed.py` | RL probe seed generator | `"+00:00"` |

These all bypassed the resolver and accumulated 73 + 11 + the rest of the
DORMANT_DUPLICATE/TEST_REFERENCE cohort = the bulk of the 129 affected
users.

### 2.4 Why this stayed latent

- **Forum/reflection paths cache aggressively** — once a user's chart was
  computed (even with a wrong UTC), the cached interpretation was served
  for weeks; the wrong-anchor chart wasn't re-rendered when the bug fix
  *would* have caught it.
- **No integrity probe** — `/api/admin/timezone-integrity-summary` did not
  exist. The first time anyone counted `"+00:00"`-tz users was during the
  AnaG investigation.
- **`account_class=TEST` masking** — most of the affected accounts (73 of 129)
  were test or dormant-duplicate accounts. They didn't generate user complaints,
  so the defect didn't surface through support channels.

---

## 3. Fixes Shipped

### 3.1 `services/timezone_resolver.py` — single source of truth

New module (`TIMEZONE_RESOLVER_VERSION = "1.0.0"`) exposing one function:

```python
def resolve_iana_timezone(lat: float, lon: float) -> Optional[str]:
    """Returns an IANA timezone name for (lat, lon), or None if unresolvable."""
```

Backed by the `timezonefinder` library, which uses the IANA tz database
shape files (~30 MB compiled) to resolve any (lat, lon) on Earth to the
correct IANA name with the correct **historical** zone-change handling
(critical for births before 1985 — see Pete's case in §6).

The module is **read-only** — it never writes the DB. It is the only
sanctioned coord→tz resolver in the codebase. All other call sites
(`estimate_timezone(longitude)`) are deprecated.

### 3.2 Write-path hardening

`users.timezone` writes are now constrained at three layers:

1. **API request schema** (`pydantic` validator on `UserCreate` /
   `UserOnboard`): `timezone` field is **either** a valid IANA name (matched
   against `pytz.all_timezones`) **or** `None`. Bare offsets `"+HH:MM"` are
   rejected at the API boundary.
2. **Service layer** (`services/user_service.py` `create_user_with_birth_data`):
   if `timezone` is `None` or the request payload doesn't include it, the
   service calls `resolve_iana_timezone(lat, lon)`. If the resolver returns
   `None` (e.g., coords are in international waters), the user record is
   created with `timezone=None` and `tz_provenance="unresolved"`, and the
   chart-recompute path raises `UserChartUnavailable("NO_TIMEZONE")` until
   the user re-enters birth location.
3. **DB write hook** (`users` collection): a write observer in
   `db_observer.py` rejects any update to `users.timezone` where the value
   is a bare offset string. Logged + alerted.

### 3.3 `tz_provenance` field

Every user document now carries a `tz_provenance` field documenting which
writer set the timezone:

| Value | Meaning |
|---|---|
| `"client_supplied_iana"`     | Frontend sent a valid IANA name (Intl.DateTimeFormat). |
| `"coord_resolver_v1"`        | Backend resolved from `(lat, lon)` via `timezone_resolver`. |
| `"phase2_migration_v1"`      | Set by the Phase 2 migration executor. |
| `"admin_manual_override"`    | Set by an authenticated admin via `/api/admin/user-tz-override`. |
| `"unresolved"`               | Resolver could not determine zone (rare; coords in international waters). |

This makes future audits trivial: any user with `tz_provenance ∉ allowed_set`
is investigated immediately.

### 3.4 IANA enforcement

All chart-recompute paths now refuse to compute a chart from a non-IANA
timezone:

```python
def _to_utc_iana(local_dt, iana):
    return pytz.timezone(iana).localize(local_dt, is_dst=None).astimezone(dt_tz.utc)
```

`is_dst=None` raises `AmbiguousTimeError` or `NonExistentTimeError` on
DST-fold/spring-forward boundaries — the chart-recompute caller catches
these and routes to a manual review queue rather than silently picking
a wrong UTC anchor.

### 3.5 Legacy stamper disablement

The three hardcoded writers were neutered:

- `seed_users.py` — `timezone` removed from the seed dict; the seed script
  now calls `resolve_iana_timezone` after coords are set.
- `e2e_create_user.py` — same fix; tests now exercise the production
  resolver path.
- `tools/rl_probe_seed.py` — removed entirely (RL probes now use existing
  pre-resolved users).

The function `estimate_timezone(longitude)` was kept in the codebase but
marked `@deprecated_use_resolver_instead` with a unit test that raises
`DeprecationWarning` so any future re-introduction is loud.

### 3.6 Admin integrity endpoint

`GET /api/admin/timezone-integrity-summary` now returns:

```json
{
  "total_users": N,
  "by_tz_format": {"iana": N1, "offset": N2, "null": N3},
  "by_tz_provenance": {"client_supplied_iana": ..., "phase2_migration_v1": ...},
  "non_iana_users": [{"user_id": "...", "name": "...", "tz": "+00:00"}, ...],
  "drift_candidates": [{"user_id": "...", "stored": "+08:00",
                        "resolved": "Asia/Kuala_Lumpur"}, ...],
  "post_migration": true
}
```

Called from the admin dashboard and from the cron-style probe (§7.3).

---

## 4. Migration Summary

### 4.1 Phased execution

| Phase | Scope | Outcome |
|---|---|---|
| **Phase 18** | Impact simulation (READ-ONLY). Classified all DB users as `SAFE` / `FORMAT_ONLY` / `RECOMPUTE_REQUIRED` / `UNKNOWN`. | 129 users identified for remediation. |
| **Phase 19** | Consistency audit (READ-ONLY). Verified write-path hardening didn't reintroduce defects on new signups. | Pass. |
| **Phase 2A** | Singleton COMMIT for canonical Pete (`pete@pulsifi.me`, `697f0c6abf35c0528ff06954`). Migration plan proven end-to-end. | 1 user migrated. Asc shifted −7.16°, MC −8.00°. 637 cache rows invalidated. All conversation/state collections preserved. |
| **Phase 2B (COHORT_OPTION_C)** | 83 dormant + test users (TEST_REFERENCE + DORMANT_DUPLICATE) in a single sweep on 2026-06-11 17:28 UTC. | 84 rollback docs (1 user has duplicate snapshot — benign, see Phase 2C §E4). 100% VERIFIED. |
| **Phase 2C** | Remaining 45 (44 RECOMPUTE_REQUIRED + 1 DRIFT_REPAIR singleton). Manifest-driven, idempotency-guarded. | **45/45 APPLIED**, Δasc=Δmc=0.0°, 10 cache rows, 2.48 s wall-clock, 0 rollbacks. |

**Total: 129 users audited, 129 migrated (Pete + 83 + 45 = 129), 0 unrecoverable failures.**

### 4.2 Per-user atomic write sequence

Identical across phases (proven on Pete):

1. **SNAPSHOT** `users_phase2_rollback` insert with `prev_user_doc`,
   `prev_chart_doc`, per-collection `cache_keys`, planned target,
   `rollback_status="PENDING"`.
2. **TZ UPDATE** `users.{_id}` `$set` `timezone`, `tz_provenance`,
   `tz_migration_id`, `tz_migrated_at`, `tz_batch_id`.
3. **RECOMPUTE** `get_full_natal_chart()` + `get_human_design_chart()`
   from the corrected UTC anchor → `charts.replace_one(upsert=True)`.
4. **CACHE INVAL.** `delete_many({_id: {$in: cache_keys[coll]}})` per
   collection — **bounded** to the exact `_id`s captured in step 1.
5. **VERIFY** Re-read chart; compare asc/mc against in-memory recompute;
   tolerance **0.01°**.
6. **STATUS** Mark rollback `APPLIED`/`VERIFIED` (or `VERIFY_FAILED` /
   `PRESERVATION_FAILED` on mismatch).

**On any failure** (exception in 2–5, verify mismatch, preservation
mismatch), the executor restored `prev_user_doc` + `prev_chart_doc`
and marked rollback `ROLLED_BACK`. `STOP_ON_ERROR=True` halts the batch.

### 4.3 Rollback strategy

Every migrated user has a complete rollback record in
`users_phase2_rollback`:

```
{
  migration_id, batch_id, user_id,
  classification,
  snapshot_at,
  prev_user_doc,    // full BSON copy
  prev_chart_doc,   // full BSON copy or null
  cache_keys: {<coll>: [<_id>...]},   // exact rows that were deleted
  planned_corrected_tz, planned_utc, planned_utc_delta_min,
  rollback_status: VERIFIED|APPLIED|ROLLED_BACK|PENDING,
  verification: {post_chart_asc, post_chart_mc,
                 asc_delta_from_expected, mc_delta_from_expected,
                 preserved_collections_unchanged, cache_rows_deleted}
}
```

**Storage cost**: 130 docs, 4.95 MiB total. Mean 39.5 KiB/doc.

**Rollback procedure** (single user):
```python
db.users.replace_one({"_id": prev_user_doc["_id"]}, prev_user_doc)
if prev_chart_doc:
    db.charts.replace_one({"user_id": user_id}, prev_chart_doc, upsert=True)
db.users_phase2_rollback.update_one(
    {"_id": snapshot_doc["_id"]},
    {"$set": {"rollback_status": "ROLLED_BACK"}})
# Caches will repopulate lazily on next read.
```

**Rollback procedure** (batch): iterate `users_phase2_rollback.find({batch_id, rollback_status: "APPLIED"})` and replay the single-user rollback for each. Idempotent.

### 4.4 Cache invalidation strategy

Two principles:

1. **Bounded invalidation** — we delete the **exact `_id`s captured at
   snapshot time**, not blanket `delete_many({user_id: uid})`. This
   prevents a cache row created by a concurrent request between snapshot
   and delete from being collateral-damaged.
2. **Conversation/state collections are NEVER deleted** — 21 collections
   are on the explicit `PRESERVED_COLLECTIONS` list:
   `chat_history`, `enneagram_chat_history`, `forum_chat_messages`,
   `forum_mirror_chat_messages`, `forum_reflections`, `user_reflections`,
   `reflections`, `journal`, `facet_history`, `user_memory`,
   `user_thread_state`, `user_engagement_state`, `user_recent_actions`,
   `home_engagement_sessions`, `enneagram_results`, `saved_people`,
   `forum_members`, `forums`, `forum_updates`, `forum_exercises`,
   `forum_relationship_edges`.

**28 cache collections are invalidatable** (chart-derived):
`deep_dive_cache`, `astrology_timeline_cache`, `governing_chapter_cache`,
`lifeline_synthesis_cache`, `lunar_synthesis_cache`, `pattern_drift_cache`,
`pattern_mirror_cache`, `relationship_today_cache`, `forum_story_cache`,
`daily_focus`, `daily_keystones`, `daily_astrology`, `daily_pattern_signals`,
`today_patterns`, `user_timeline`, `mirror_insights`, `pattern_memory`,
`pattern_memory_signals`, `pattern_running_me_v2`,
`longitudinal_pattern_memory`, `home_angle_history`, `home_history`,
`home_v6_state`, `lifeline_events`, `lifeline_imported_moments`,
`lifeline_import_sources`, `lunar_considerations`, `lunar_journal`.

**Total cache rows invalidated across all phases**: 637 (Pete, Phase 2A) +
(Phase 2B cohort sweep, COHORT_OPTION_C) + 10 (Phase 2C) — bounded and
documented in each per-user rollback record.

---

## 5. Validation Results

### 5.1 Adversarial tests (added during write-path hardening)

| Test | What it asserts |
|---|---|
| `test_user_create_rejects_offset_tz` | API returns 422 if `timezone="+08:00"`. |
| `test_user_create_accepts_iana_tz` | API persists `timezone="Asia/Kuala_Lumpur"`. |
| `test_user_create_resolves_when_no_tz` | Omitted `timezone` triggers `resolve_iana_timezone(lat, lon)` and persists the result. |
| `test_user_create_marks_unresolved_for_ocean_coords` | Coords in mid-Pacific persist `tz_provenance="unresolved"` and chart-compute is deferred. |
| `test_recompute_refuses_offset_tz` | `get_full_natal_chart` raises if user's stored tz is an offset. |
| `test_estimate_timezone_is_deprecated` | The legacy `estimate_timezone(longitude)` emits `DeprecationWarning`. |
| `test_db_observer_rejects_offset_write` | A `users.update_one({_id}, {$set: {timezone: "+08:00"}})` is rejected at the observer layer. |
| `test_resolve_iana_known_cities` | Resolver returns correct IANA for 30 known cities including DST-misaligned countries (Argentina, India, China, Newfoundland, Nepal, France, Spain). |
| `test_historical_dst_pete_1968` | Resolver + chart-recompute produce Asc=255.54°, MC=169.84° for Pete's 1968 birth (matches Swiss Ephemeris baseline within 0.001°). |

All pass on every CI run; the suite is gated on PRs touching `timezone_resolver.py`, `user_service.py`, `db_observer.py`, or any tool under `/app/backend/tools/phase2*`.

### 5.2 Consistency audits

`phase19_consistency_audit.py` reports (READ-ONLY):
- New users created post-Phase-19: **0** have offset-format `timezone`.
- All new users have `tz_provenance ∈ {client_supplied_iana, coord_resolver_v1}`.
- `GET /api/admin/timezone-integrity-summary`: `non_iana_users.length == 0`,
  `drift_candidates.length == 0` post Phase 2C.

### 5.3 Migration verification

| Metric (post Phase 2C) | Value |
|---|---|
| Users with `tz_provenance=phase2_migration_v1` | **129** |
| `users_phase2_rollback` docs | 130 (129 distinct user_ids + 1 benign duplicate) |
| Rollback status distribution | VERIFIED: 85, APPLIED: 45, PENDING: 0, ROLLED_BACK: 0 |
| Chart `asc_delta_from_expected` max across 130 records | **0.0°** |
| Chart `mc_delta_from_expected` max across 130 records | **0.0°** |
| `preserved_collections_unchanged` | **130/130 OK** |
| Re-running `phase2b_execution_plan.py` post-commit | `RECOMPUTE_REQUIRED=0, FORMAT_ONLY=0` ✅ |
| Adversarial test suite | **9/9 PASS** |

### 5.4 Conversation/state preservation (spot-check on canonical Pete)

| Collection | Pre-Phase-2A | Post-Phase-2A | Post-Phase-2C | Delta |
|---|---|---|---|---|
| chat_history             | 1 | 1 | 1 | 0 |
| journal                  | 26 | 26 | 26 | 0 |
| forum_chat_messages      | 31 | 31 | 31 | 0 |
| forum_mirror_chat_messages| 30 | 30 | 30 | 0 |
| forum_reflections        | 1 | 1 | 1 | 0 |
| user_reflections         | 2 | 2 | 2 | 0 |
| reflections              | 2 | 2 | 2 | 0 |
| facet_history            | 20 | 20 | 20 | 0 |
| user_memory              | 1 | 1 | 1 | 0 |
| saved_people             | 9 | 9 | 9 | 0 |
| forum_members            | 4 | 4 | 4 | 0 |
| home_engagement_sessions | 327 | 327 | 327 | 0 |

Identical across every spot-check on every phase. **No conversation, reflection, journal, forum, saved-people, or engagement data was touched during the migration.**

---

## 6. Lessons Learned

### 6.1 Timezone is not a presentational concern — it's an identity input

Timezone determines the UTC instant of an event. For natal charts, the
event is the birth itself, and an incorrect UTC anchor rotates the
**entire chart wheel** by the offset error. A 1-hour offset error =
**15° of ascendant rotation** = wrong rising sign for 50% of births
near sign cusps + wrong house for every transiting planet for the
rest of the user's life.

> **Don't treat timezone as a UX nicety. Treat it as a uniqueness key.**

### 6.2 Historical offsets are mandatory, not optional

A bare offset `"+08:00"` is *correct* for present-day Kuala Lumpur but
**wrong** for any pre-1982 event in Singapore (which used `+07:30` until
December 1981). The IANA database encodes these transitions; bare offsets
do not. Pete's 1968 birth is computed correctly with
`Asia/Kuala_Lumpur` but **incorrectly** with `+08:00` (Δasc = −7.16°).

The bug surfaced precisely because of this: any system that stores bare
offsets is correct only for *present-day computations*, which is exactly
the kind of latent defect that survives unit tests written today.

**Mandate**: every persisted timezone is an IANA name. No exceptions.

### 6.3 Chart reproducibility is a regression surface

A chart is a pure function of `(local birth time, IANA timezone, latitude,
longitude, ephemeris, ayanamsa, house system)`. Any change in any input
should be either:
- **Deterministic and audit-logged** (e.g., the Phase 2 `tz_provenance`
  trail), or
- **Refused at the write boundary** (e.g., the offset-rejection observer).

The Phase 2 migration succeeded specifically because we:
1. Computed the expected post-migration asc/mc *in memory* before any DB write.
2. Snapshot the prev state into a rollback collection.
3. Wrote the new state.
4. Re-read the chart and compared against the expectation to within 0.01°.

Any production-mutating change to chart-input fields (timezone,
coords, birth date, birth time, ayanamsa, house system) **must** carry
this verify-on-write contract going forward.

### 6.4 Migration design

The four design choices that made the migration safe:

1. **Per-user atomicity**, not batch atomicity. Each user is a separable
   migration unit with its own snapshot + verify + rollback.
2. **Bounded cache invalidation** (capture `_id`s at snapshot, delete by
   exact `_id`). Prevents accidental over-deletion from concurrent
   writes between snapshot and delete.
3. **Preservation list as an allowlist**, not a denylist. The list of
   *collections to delete from* is explicit; everything else is preserved
   by default. Adding a new derived-cache collection forces an explicit
   PR review.
4. **`STOP_ON_ERROR=True` + immediate rollback**. The first failure
   halts the cohort. No partially-migrated batch. This was the design
   that survived the AnaG-style ambiguity without ever shipping a bad
   chart.

### 6.5 Idempotency guards from day 0

The Phase 2C executor checks `users_phase2_rollback.user_id ∉
already-VERIFIED` before snapshotting. This prevented re-migration of
the 84 already-completed users when Phase 2C ran against the same DB.
The single benign duplicate (one user with 2 VERIFIED docs from
~9 s apart in the COHORT_OPTION_C sweep) showed the original Phase 2B
executor *didn't* have this guard. **Lesson:** every state-changing
batch tool gets an idempotency precondition from the first commit.

---

## 7. Future Guardrails

### 7.1 Required invariants (must hold at all times)

| # | Invariant | Enforced by |
|---|---|---|
| I1 | Every `users.timezone` value is either `null` or a valid IANA name | API schema validator + DB write observer |
| I2 | Every user with non-null `timezone` has a non-null `tz_provenance` from the allowed set | DB write observer |
| I3 | `resolve_iana_timezone(lat, lon)` is the only sanctioned coord→tz function | Code review + deprecated-function CI gate |
| I4 | Chart-recompute paths never accept an offset-format timezone | `_to_utc_iana` raises on non-IANA input |
| I5 | `users_phase2_rollback` is the canonical migration audit trail; status flips are observable in the audit log | `rollback_status` indexed; admin dashboard |
| I6 | `chart_doc.debug_stamp.tz_provenance` is set on every chart write | `charts.replace_one` wrapper in `chart_service.py` |
| I7 | New chart-derived caches are added to `CACHE_COLLECTIONS` (in `phase2_execute_cohort.py`) and never to `PRESERVED_COLLECTIONS` | Code review + linter rule |
| I8 | Conversation/state collections never appear in `CACHE_COLLECTIONS` | Lint check + adversarial test |

### 7.2 Tests (CI-gated)

All from §5.1, plus these added during the closure:

- `test_timezone_provenance_non_null_after_migration` — every user with
  a non-null timezone has a provenance flag.
- `test_no_offset_timezones_in_db` — the count of users with
  offset-format `timezone` must remain at **0**.
- `test_resolver_versioning` — bumping `TIMEZONE_RESOLVER_VERSION`
  triggers a re-audit run before deployment.
- `test_chart_replay_idempotent` — recomputing the same chart twice
  produces byte-identical output (modulo timestamps).

### 7.3 Monitoring

| Probe | Cadence | Alert threshold |
|---|---|---|
| `/api/admin/timezone-integrity-summary` cron | every 6 hours | `non_iana_users > 0` OR `drift_candidates > 0` → page on-call |
| `users` collection writes with offset-format `timezone` | real-time via DB observer | any occurrence → page on-call + auto-revert the write |
| `users_phase2_rollback` writes with `status != VERIFIED` after `verified_at + 1h` | real-time | any occurrence → notify Track 4 |
| `charts.debug_stamp.tz_provenance` missing | nightly | `count > 0` → ticket |
| `estimate_timezone` import attempts | real-time (linter + runtime warning) | any import → ticket |
| Onboarding payloads with `timezone` matching `^[+-]\d{2}:\d{2}$` | real-time | rate > 0 over 1h window → engineering review (frontend bug) |

### 7.4 Operational runbook

- **If a non-IANA timezone is detected for a user**: confirm via
  integrity summary, run a focused recompute via
  `phase2_execute_cohort.py --limit 1`, verify the rollback doc and
  asc/mc match in-memory.
- **If a migration fails verification**: the executor will auto-mark
  `ROLLED_BACK`. No manual rollback is required. Open a ticket and
  re-run with the same `batch_id` after fixing the root cause.
- **If a chart-derived cache is suspected stale post-migration**:
  these caches repopulate lazily on next read. No action required;
  if surfaced as a UX issue, the user can re-load the relevant view.
- **If the rollback collection grows beyond 10 MB**: archive entries
  with `status=VERIFIED` and `verified_at > 90d` to cold storage
  (`users_phase2_rollback_archive`). Do not delete from the primary
  collection without an export.

### 7.5 Documentation

The following references must be kept up to date:

- `/app/backend/docs/TIMEZONE_INTEGRITY_POSTMORTEM.md` — this document (canonical).
- `/app/backend/audit_reports/PHASE2C_FINAL_CERTIFICATION.md` — pre-execution certification.
- `/app/backend/audit_reports/PHASE2C_FINAL_EXECUTION_REPORT.md` — execution log.
- `/app/backend/audit_reports/PHASE2C_EXECUTION_MANIFEST.json` — final cohort manifest.
- `/app/backend/audit_reports/phase2_pete_bf334b98-903a-4144-ae6f-063764f0b675.json` — Phase 2A canonical reference run.
- `/app/backend/audit_reports/phase2_cohort_classification.json` — Phase 18 classification snapshot.
- `/app/backend/audit_reports/phase2c_execution_b4351980-7af2-43b4-aa54-e8fa48625af6.json` — Phase 2C execution artifact.

---

## 8. Closure

The Timezone Integrity Initiative is **closed**. The original defect is
remediated for all 129 affected users, the write path is hardened with
schema + service + observer-layer defenses, every chart write is
verifiable via the `tz_provenance` trail, and a monitoring suite catches
any future regression at multiple layers.

Future work is **incremental hardening**, not remediation:

- B3.x lens-jargon and founder-lexicon work (separate Mirror Chat V2
  track) — unrelated to timezone, but documented here because it shares
  the same "lexicon weighting" pattern of latent quality drift.
- Variant A migration (`RUN_VARIANT_A_MIGRATION`) — a separate
  initiative; not affected by Phase 2 outcomes.
- Educational-mode disambiguation for charts (B3.1) — independent of
  timezone correctness.

This document is the canonical reference for *why* the timezone fields
exist the way they do, *why* the migration was sequenced the way it was,
and *what* must remain true forever about how the system handles
timezones.

---

### Sign-off

```
Initiative          : Timezone Integrity
Phases executed     : 18, 19, 2A, 2B (COHORT_OPTION_C), 2C
Users audited       : entire DB
Users migrated      : 129 (1 Pete + 83 cohort_option_c + 45 phase 2c)
Failures            : 0
Rollbacks executed  : 0
Verification        : 100% within 0.01° (max observed: 0.0°)
Preservation        : 21/21 collections intact across 129 users
Closed by           : Track 4 (Data Integrity)
Closure date        : 2026-06-14 EOD
```
