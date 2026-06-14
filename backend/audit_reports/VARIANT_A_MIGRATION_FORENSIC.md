# Forensic Report — `RUN_VARIANT_A_MIGRATION` / `VARIANT_A_PHASE_5`

| Field | Value |
|---|---|
| Mode | **READ-ONLY forensic** — no code edits performed |
| Report timestamp | 2026-06-14 (in-session) |
| Local DB inspected | `test_database` @ `mongodb://localhost:27017` |
| Production DB | **NOT inspected** (Atlas IP still not whitelisted) |
| Build markers | `variant-a-13-sign-migration-v1`, `variant-a-prod-migration-startup-hook-v1` |

---

## 1. Every file referencing the two strings

Searched recursively across `*.py`, `*.ts/tsx/js`, `*.json`, `*.md`, `*.env*`, `*.sh`, `*.yml`.

### 1.1 Code (live)
| Path | Lines | Role |
|---|---|---|
| `backend/server.py` | 32722, 32726 | Startup-hook call site comment + import |
| `backend/routers/variant_a_startup_hook.py` | 8, 50–51, 200–308 | **Pod-startup runner** — the actual conditional + execution |
| `backend/routers/admin_variant_a_migration.py` | 28, 309, 312, 664, 669 | Admin HTTP gate (`/api/admin/migration-run`) |
| `backend/scripts/migration_phase5_variant_a.py` | 40, 458–459, 507 | Standalone CLI runner (manual invocation) |

### 1.2 Documentation / audits (informational only — no execution path)
| Path | Lines | Role |
|---|---|---|
| `backend/docs/TIMEZONE_INTEGRITY_POSTMORTEM.md` | 581 | Mention only |
| `backend/audit_reports/ADMIN_ROUTE_INVENTORY_2026_06_12.md` | 52, 211 | Inventory table |
| `backend/audit_reports/DEPLOYMENT_REPORT_2026_06_14.md` | 72 | Confirms flag NOT triggered at last deploy |
| `backend/audit_reports/ASTROLOGY_ANGLE_STALENESS_FORENSIC_AUDIT.md` | 28 | Wave map |
| `backend/audit_reports/ANGLE_DEGREE_ANOMALY_FORENSIC.md` | 219 | Mention only |

### 1.3 Env files
**`backend/.env` does NOT contain `RUN_VARIANT_A_MIGRATION` at all** — confirmed via grep, returns empty.  The variable is read from `os.environ` only.

---

## 2. The exact conditional that checks the env var

Two distinct gating sites — both string-equality, both case-sensitive.

### 2.1 Startup hook (auto-on-boot path)
**File:** `backend/routers/variant_a_startup_hook.py:200-208`

```python
ENV_FLAG_NAME  = "RUN_VARIANT_A_MIGRATION"     # L50
ENV_FLAG_VALUE = "VARIANT_A_PHASE_5"           # L51

async def run(db) -> None:
    """Entry point. Safe to call unconditionally — exits early if flag unset."""
    flag = os.environ.get(ENV_FLAG_NAME)                # L202
    if flag != ENV_FLAG_VALUE:                          # L203  ← THE GATE
        logger.info(
            "[Variant A Startup Hook] flag '%s' not set to expected value; skipping.",
            ENV_FLAG_NAME,
        )
        return                                          # L208 — short-circuit
```

A missing env var, a wrong value, or any whitespace difference → short-circuits silently with the "not set to expected value; skipping" log line.

### 2.2 Admin HTTP route (manual trigger path)
**File:** `backend/routers/admin_variant_a_migration.py:664-671`

```python
if confirm != "VARIANT_A_PHASE_5":
    raise HTTPException(
        status_code=400,
        detail={
            "code":    "MISSING_CONFIRM",
            "message": "Add `?confirm=VARIANT_A_PHASE_5` to the URL "
                       "to acknowledge live writes.",
        },
    )
```

Plus an audit-only state report at L309-315 (returns `unset` / `set` / `set_wrong_value`).

### 2.3 CLI script gate
**File:** `backend/scripts/migration_phase5_variant_a.py:458-459`

```python
if not args.dry_run and args.confirm != "VARIANT_A_PHASE_5":
    print("ABORTED: live writes require --confirm VARIANT_A_PHASE_5", file=sys.stderr)
```

---

## 3. The startup path that executes the migration

### Call chain
```
uvicorn → server.py @app.on_event("startup")
       └─→ _safe_run_migrations()                   [server.py:32709]
            ├─→ asyncio.sleep(2)
            ├─→ run_startup_data_migrations()       (non-variant-A migrations)
            └─→ try:
                    from routers.variant_a_startup_hook import run as _variant_a_run
                    await _variant_a_run(db)        [server.py:32727]
                except Exception as e:
                    logger.error(...)               # non-fatal
```

### What `_variant_a_run(db)` does when the flag IS set (`variant_a_startup_hook.py:200-307`)

| Step | Method | Read / Write | Notes |
|---|---|---|---|
| 1 | `_run_preflight(db)` | READ-only | Counts forums/users/charts; detects loopback/preview DB; checks Pulsifi forum + JH/Jay presence; counts charts already carrying the marker. Returns `(payload, abort_reason)`. |
| 1.5 | `_emit_block(PREFLIGHT_BEGIN/END, …)` | WRITES TO STDOUT ONLY | Fenced JSON for Emergent logs view |
| 1.9 | **5 hard-gates** | READ-only | (`is_preview` ∨ `chart_count<=0` ∨ `!pulsifi_found` ∨ `!(jh_found ∨ jay_found)` ∨ `already_marker == chart_count`) → ABORT, no writes |
| 2 | `run_snapshot()` from `migration_snapshot_variant_a` | READ-only | Persists snapshot JSON to `/app/backend/audits/variant_a_migration_snapshot.json` |
| 3 | **`recompute_users(db, dry_run=False)`** | **WRITES `db.charts`** | Upserts every user's `astrology` sub-doc + stamps `astrology_engine_version`, `sign_attribution_version`, `house_system`, `migrated_at`, `migration_marker` |
| 4 | `invalidate_caches(db, dry_run=False)` | **WRITES (delete_many)** to all `SIGN_DEPENDENT_CACHES` collections |
| 5 | `run_validate(db)` | READ-only | Phase-6 anchor checks |
| 6 | `_anchor_signs(db)` | READ-only | Post-migration read-back of Pete/Mel/JH/Jay Sun/Moon/Asc |
| 7 | `_emit_block(REPORT_BEGIN/END, …)` | WRITES TO STDOUT ONLY | Final JSON report |
| 8 | Persist report to `/app/backend/audits/variant_a_prod_migration_report_<ts>.json` | WRITES TO DISK | Best-effort; non-fatal on failure |

### Preflight hard-gates (the safety net)

```python
# variant_a_startup_hook.py:187-197
if is_preview:                          return payload, "preview_or_localhost_db_refused"
if chart_count <= 0:                    return payload, "no_charts_in_db"
if not pulsifi_found:                   return payload, "pulsifi_forum_not_found"
if not jh_found and not jay_found:      return payload, "neither_jh_nor_jay_user_found"
if already_marker == chart_count:       return payload, "already_migrated_all_charts_have_marker"
return payload, None
```

`is_preview = (DB_NAME == "test_database") OR (mongo host in {localhost,127.0.0.1,::1,0.0.0.0})`.

This means **even if the env var were set on the local pod, the migration would refuse to run** because `DB_NAME=test_database` and `MONGO_URL=mongodb://localhost:27017`.

---

## 4. Whether the migration has already run

### 4.1 Current pod state (this session)
`/var/log/supervisor/backend.err.log` — last 20 startups all show:

```
[Variant A Startup Hook] flag 'RUN_VARIANT_A_MIGRATION' not set to expected value; skipping.
```

→ **The startup hook has NEVER fired in this pod's lifetime.**

### 4.2 Local DB chart-marker census (test_database)
```
total charts: 171
  168  midpoint13_variant_a_v1__variant-a-13-sign-migration-v1
    3  <missing>__<missing>
```

→ 168/171 charts already carry the canonical marker, **but those writes did NOT come from the startup hook**.  They came from earlier manual / CLI runs (June 9 reports below).

### 4.3 Disk forensic — past run artefacts
`/app/backend/audits/` contains:

| File | Mtime | Source |
|---|---|---|
| `variant_a_migration_audit_20260609_145605.json` | 2026-06-09 14:56 UTC | Earlier audit |
| `variant_a_migration_audit_20260609_155344.json` | 2026-06-09 15:53 UTC | Earlier audit |
| `variant_a_migration_snapshot.json` | 2026-06-09 16:01 UTC | Snapshot |
| `variant_a_migration_report_20260609_160541.json` | 2026-06-09 16:05 UTC | Report (recompute) |
| `variant_a_migration_report_20260609_160550.json` | 2026-06-09 16:05 UTC | Report (rerun) |
| `variant_a_migration_report_20260609_160834.json` | 2026-06-09 16:08 UTC | Report |
| `variant_a_migration_report_20260609_161031.json` | 2026-06-09 16:10 UTC | Report |
| `variant_a_migration_report_20260609_162027.json` | 2026-06-09 16:20 UTC | **Final canonical report** |

The June 9 16:20 report summary:
```
recompute.dry_run               = False
recompute.users_scanned         = 171
recompute.users_with_birth_data = 168
recompute.users_skipped         =   3
recompute.users_migrated        = 168
recompute.users_inserted        =   0
recompute.users_updated         = 168
recompute.ophiuchus_entries     =  99
recompute.errors_count          =   0
```

NOTE: none of those reports are named `variant_a_prod_migration_report_*` (which is what the **startup-hook** writes).  They are named `variant_a_migration_report_*` — the format produced by the standalone CLI script.  Therefore the local DB was populated via `python3 scripts/migration_phase5_variant_a.py --confirm VARIANT_A_PHASE_5`, **NOT** via the auto-on-boot pod hook.

### 4.4 Production DB
**Unknown — not inspected.**  Atlas IP still requires whitelisting (Issue 2 in handoff, BLOCKED).  Per the deployment report (`DEPLOYMENT_REPORT_2026_06_14.md:72`) the production pod has NOT had the env var set at any observed deploy, and the deployment guard treats the absence of the flag as the expected state.

### 4.5 Local preflight rehearsal (test_database)
If the flag were flipped on this local pod RIGHT NOW, the preflight would abort like this (simulated against current DB):

```
is_preview                              = True   (DB_NAME=test_database, host=localhost)
chart_count                             = 171    OK
pulsifi forum                           = 0      ← would fail
JH user                                 = 0      ← would fail
Jay user                                = 0      ← would fail
charts with marker                      = 168 / 171
```

First failing gate: `preview_or_localhost_db_refused`.  Even if that were bypassed, `pulsifi_forum_not_found` would fire next.  **The hook is safe against accidental local execution.**

---

## 5. Whether the migration is idempotent

### 5.1 Author's intent — YES (docstring claim)
`variant_a_startup_hook.py:19-20`:
> *"Idempotent: on subsequent restarts the recompute body is a no-op because every chart already carries the migration_marker."*

### 5.2 Mechanical analysis — qualified YES, with caveats

#### Pre-write idempotency gate (preflight)
`variant_a_startup_hook.py:195-196`:
```python
if already_marker == chart_count:
    return payload, "already_migrated_all_charts_have_marker"
```
→ **If every chart already carries the marker, the hook exits BEFORE any write.**  This makes re-runs against a fully-migrated DB a true read-only no-op.  ✅

#### Partial-migration re-run
If even **one** chart lacks the marker, the gate does NOT fire and `recompute_users` proceeds for **every user with valid birth data** — not just the unmigrated ones.  The loop unconditionally:

`migration_phase5_variant_a.py:267-298`:
```python
# 1. Computes a fresh chart from birth data (deterministic given the
#    engine version + ephemeris files).
new_chart = get_full_natal_chart(birth_datetime=utc, lat=lat, lon=lon,
                                  house_system=CANONICAL_HOUSE_SYSTEM)
…
update_set = { "astrology": {...},
               "astrology_engine_version": ASTROLOGY_ENGINE_VERSION,
               "sign_attribution_version": SIGN_ATTRIBUTION_VERSION,
               "house_system": CANONICAL_HOUSE_SYSTEM,
               "migrated_at":  stamp_iso,         # ← changes every run
               "migration_marker": MIGRATION_MARKER }
res = await db.charts.update_one(
    {"user_id": str(u["_id"])},
    {"$set": update_set, "$setOnInsert": {"user_id": str(u["_id"])}},
    upsert=True,
)
```

**Determinism of `update_set`:**
| Field | Stable across runs? | Notes |
|---|---|---|
| `astrology.{planets,angles,houses,…}` | **YES** — Variant A engine + canonical ephemeris + Equal houses produce byte-identical sign/degree output for a given birth datetime / location | Engine pinned via `ASTROLOGY_ENGINE_VERSION="midpoint13_variant_a_v1"` |
| `astrology_engine_version` | YES — constant | |
| `sign_attribution_version` | YES — constant | |
| `house_system` | YES — constant | |
| `migration_marker` | YES — constant | |
| `migrated_at` | **NO** — wall-clock at run start (`started_at.isoformat()`) | Re-running flips this timestamp |

**Verdict:** the `$set` is *value-equivalent* across runs except for `migrated_at`.  Mongo's `update_one` will still count the doc as *modified* because `migrated_at` differs.  Therefore:

- No semantic drift: identical Sun/Moon/Asc, identical engine stamp.
- The `users_updated` counter will report all 168 users as "updated" again even though only `migrated_at` actually changed.
- The cache-invalidation step (`invalidate_caches`) is destructive on every run regardless of whether anything changed.

#### Cache invalidation (Step 4)
Iterates `SIGN_DEPENDENT_CACHES` (15+ collections including `astrology_timeline_cache`, `deep_dive_cache`, `relationship_today_cache`, `relationship_mappings`, etc.) and unconditionally `delete_many({})`.  Idempotent in the sense that it always converges to "empty", but **not** in the sense of "no side effect on a re-run" — it wipes caches every time.

#### Snapshot (Step 2)
`run_snapshot()` overwrites `/app/backend/audits/variant_a_migration_snapshot.json` each invocation (last-writer-wins).

### 5.3 Idempotency summary

| Aspect | Idempotent? | Comment |
|---|---|---|
| Fully-migrated DB short-circuit | ✅ TRUE | `already_migrated_all_charts_have_marker` exits at preflight |
| Chart `astrology` field values | ✅ TRUE | Deterministic Variant-A engine |
| Engine / marker stamps | ✅ TRUE | Constants |
| `migrated_at` field | ⚠️ NO | Wall-clock; flips on every run |
| `users_updated` counter | ⚠️ MISLEADING | Counts all users as "updated" on re-run because of `migrated_at` |
| Cache invalidation | ⚠️ Destructive but convergent | Wipes 15+ collections every run |
| Snapshot file | ⚠️ Overwrites | Last-writer-wins on disk |
| User charts on partial-migration re-run | ✅ Value-stable | Recomputes everyone but produces same astrology output |

**Bottom line:** The hook is **safe to re-run** on a fully-migrated DB (early exit) and **value-stable** on a partially-migrated DB (recomputes everyone but the math is deterministic).  It is **not pure idempotent** in the strict sense: every run that gets past preflight will (a) bump `migrated_at`, (b) wipe sign-dependent caches, and (c) overwrite the snapshot file.

---

## 6. Risk surface summary

| Risk | Severity | Mitigation in place |
|---|---|---|
| Accidental run on local/preview DB | LOW | `_looks_like_preview_db` hard-gate catches both `DB_NAME=test_database` and loopback hosts |
| Accidental run on wrong production DB | MEDIUM | Pulsifi + (JH ∨ Jay) anchor-presence gate fails if it's the wrong DB |
| Double-run on same DB | LOW | `already_marker == chart_count` short-circuits before any write |
| Partial-state re-run wipes valuable caches | MEDIUM | Caches are designed to be regenerable; no user-visible data loss expected |
| `migrated_at` drift triggers downstream cache thrash | LOW | Only `chart.migrated_at` changes; downstream invalidation is also explicit (Step 4) |
| Snapshot file lost (overwrite) | LOW | Reports persist to timestamped files; snapshot is single-shot anyway |
| Hook silently does nothing | EXPECTED | Default state: `flag != "VARIANT_A_PHASE_5"` → log-and-return |

---

## 7. Open questions / things this report did NOT verify

1. **Production DB state.** Atlas IP not whitelisted → I could not inspect the production `charts` collection to confirm marker coverage there.
2. **Whether the pod env in production has the flag set right now.** The deployment report from 2026-06-14 said no, but I cannot read live deploy env from this session.
3. **Anchor-validation success rates on production.** Phase-6 validation results are baked into `run_validate(db)` (called by step 5 of the hook), but no production run report exists yet.
4. **Whether the 3 charts WITHOUT the marker on local are intentional** (e.g. brand-new users post-migration) or legacy artefacts. Worth a follow-up if we ever flip the local flag — they'd cause `already_marker != chart_count` and force a full re-run.

---

## 8. Files produced by this forensic

- `/app/backend/audit_reports/VARIANT_A_MIGRATION_FORENSIC.md` (this file)

No code edits, no DB writes, no env changes.

— end of report —
