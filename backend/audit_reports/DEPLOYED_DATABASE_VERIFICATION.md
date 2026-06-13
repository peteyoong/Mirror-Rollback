# DEPLOYED DATABASE VERIFICATION

**Target:** `https://mirror-lens-fixes-r-1779710763.emergent.host`
**Generated:** 2026-06-13 (read-only audit)
**Mutation policy:** READ-ONLY. No writes, no chart recomputes, no migrations, no flag flips, no user modifications.

---

## 1. Headline answer

> **Is the deployed application reading the same database as preview/workspace?**
>
> **NO.** The deployed app is wired to a **different MongoDB instance** in a **different database name**, on what is provably **not** a `localhost:27017` URI. All four key debug markers from `/api/health` differ, and the `db_uri_last_4` value (`"rity"`) is the unmistakable tail of an Atlas SRV connection string ending in `?retryWrites=true&w=majority`.

---

## 2. Live evidence — side-by-side `/api/health` diff

Identical endpoint, identical client, called seconds apart. Only the `debug.*` and `env` fields differ:

| `/api/health → debug.*` | Preview/workspace (`hd-incarnation-fix.preview.emergentagent.com`) | **Deployed (`mirror-lens-fixes-r-1779710763.emergent.host`)** | Match? |
|---|---|---|---|
| `env` | `"unknown"` | **`"staging"`** | ❌ |
| `db_name` | `"test_database"` | **`"expo-bundle-issue-mirror_staging"`** | ❌ |
| `db_uri_last_4` | `"7017"` (← `mongodb://localhost:27017`) | **`"rity"`** (← `?retryWrites=true&w=majority`, Atlas SRV) | ❌ |
| `lifeline_events_total` | `22` | **`47`** | ❌ |
| `ask_mirror_astrology_v7` | `true` | `true` | ✅ |
| `mirror_chat_router_version` | `ask-mirror-astrology-v7` | `ask-mirror-astrology-v7` | ✅ |

**Every database-identity marker is different.** Code-version markers happen to match for the v7 router, but the underlying data store is a separate cluster with a separate database.

---

## 3. Deployed `/api/health` — full debug capture

```json
{
  "ok": true,
  "service": "backend",
  "status": "healthy",
  "timestamp": "2026-06-13T11:34:14.171318+00:00",
  "build": {
    "stamp": "vunknown-5ae955",
    "git_revision": null,
    "git_dirty": false,
    "deployed_bundle": {
      "timestamp": "2026-05-31 03:45:49 UTC",
      "hash": "5ae9551bb335",
      "name": "entry-a840aeeb2b1699890e640de9e505b634.js",
      "size_kb": 3843.9
    },
    "source_files": {
      "newest_modified": "2026-06-09 15:51:23 UTC",
      "newest_file": "components/astrology/AstrologyDeepDiveTab.tsx",
      "tracked_count": 8
    },
    "validation": {
      "is_current": false,
      "errors": [
        "STALE DEPLOYMENT: Source file 'components/astrology/AstrologyDeepDiveTab.tsx' (2026-06-09 15:51:23) is newer than deployed bundle (2026-05-31 03:45:49)"
      ],
      "stale_files_count": 1
    }
  },
  "debug": {
    "env": "staging",
    "db_name": "expo-bundle-issue-mirror_staging",
    "db_uri_last_4": "rity",
    "collections": [
      "enneagram_chat_history", "keystone_patterns", "forum_members",
      "pattern_memory", "user_timeline", "resonances", "migration_reports",
      "relationship_today_events", "lifeline_imported_moments",
      "mirror_chat_retrieval_receipts", "user_recent_actions",
      "relationship_patterns", "home_angle_history", "deep_dive_cache",
      "enneagram_feedback", "daily_astrology", "chat_history",
      "daily_focus", "daily_keystones", "pattern_exposures"
    ],
    "lifeline_events_total": 47
  }
}
```

### What each marker means

* **`env: "staging"`** — the deployed container's `APP_ENV` (or equivalent) is set to `staging`. The workspace pod's value is `"unknown"`.
* **`db_name: "expo-bundle-issue-mirror_staging"`** — a literally different database name from the workspace `test_database`. The suffix `_staging` is consistent with an Atlas staging DB; the prefix matches the Emergent workspace slug that originally seeded the deployment (`expo-bundle-issue-mirror`).
* **`db_uri_last_4: "rity"`** — the last four characters of the connection string the Mongo client was constructed with. This is the *tail of `?retryWrites=true&w=majority`*, which is the canonical query-string suffix Atlas appends to SRV URIs and is also the *exact* template suffix used in `audit_reports/PFS26_OPERATOR_RUNBOOK.md`: `mongodb+srv://<readonly-user>:[REDACTED]@<cluster>/?retryWrites=true&w=majority`. The workspace value is `"7017"` (= `localhost:27017`). The deployed value is **not consistent with any `mongodb://...:27017` URI** and is consistent with `mongodb+srv://...?retryWrites=true&w=majority`.
* **`lifeline_events_total: 47`** vs workspace `22` — independent confirmation that this is a *different* dataset. A pod backed by the same `test_database` would produce `22`, not `47`.
* **`collections: [20 items]`** — a different sample of collection names than the workspace returned, again consistent with a separate DB. (The health endpoint truncates to the first 20 collections; the order/selection is driven by the listCollections cursor, not stable, but the *names* are present in both environments — the schema appears compatible.)

### Build / staleness markers

* `deployed_bundle.timestamp = 2026-05-31 03:45:49 UTC` (hash `5ae9551bb335`)
* `source_files.newest_modified = 2026-06-09 15:51:23 UTC`
* `validation.errors[0] = "STALE DEPLOYMENT"` — the deployed JS bundle predates the most recent source file by ~9 days. **This is a build-staleness flag on the bundle, not a DB staleness claim.** It does not bear on the database identity, but it does mean the deployed runtime is several builds behind the workspace.
* `git_revision: null`, `git_dirty: false` — the deployed image was built without a git revision stamp (unlike the workspace, which shows `c384a6f3`).

---

## 4. What I tried to query and what is **not** reachable on the deployed instance

The following endpoints **exist** on the workspace backend but return `404` on the deployed image, confirming the deployed bundle is older and intentionally exposes a **narrower diagnostic surface**:

| Endpoint | Deployed | Why this matters |
|---|---|---|
| `/api/diagnostics` (list root) | `404` | No discovery surface. |
| `/api/diagnostics/mongo-status` | `404` | Would have exposed cluster/replica-set names. **Not available.** |
| `/api/diagnostics/db`, `/database`, `/collections`, `/charts` | `404` each | Would have exposed per-collection counts. **Not available.** |
| `/api/diagnostics/migration`, `/migration-status`, `/variant-a` | `404` each | Would have exposed Variant A migration progress. **Not available.** |
| `/api/admin/db-stats`, `/admin/stats` | `404` each | No admin-stats surface exposed. |
| `/api/build`, `/api/version` | `404` each | Build/version info only via `/api/health.build`. |

Endpoints that **do** respond on deployed (with limited DB info):
* `GET /api/` → `{"message":"Project Mirror API","version":"1.0"}` (no DB info)
* `GET /api/health` → full debug block (above)
* `GET /api/diagnostics/astro-system` → astrology engine config; returns `zodiac_mode = midpoint13_variant_a_v1`, `ophiuchus_enabled = true`, `runtime_guard_active = true`, `ayanamsa_or_svp = 31.2836`. This proves the *engine config* on the deployed runtime is Variant A canonical, but it does **not** prove anything about how many *stored charts* in `expo-bundle-issue-mirror_staging` are tagged as Variant A.

---

## 5. Comparison against the previously-verified workspace baseline

| Metric | Workspace / Preview (proven) | Deployed (proven) | Same DB? |
|---|---:|---:|---|
| `MONGO_URL` | `mongodb://localhost:27017` | URI ending in `…retryWrites=true&w=majority` (Atlas SRV signature) | **NO** |
| `DB_NAME` | `test_database` | `expo-bundle-issue-mirror_staging` | **NO** |
| `env` marker | `unknown` | `staging` | **NO** |
| Users count | 175 | **UNKNOWN** (no endpoint exposes this on deployed) | unverifiable |
| Charts count | 171 | **UNKNOWN** (no endpoint exposes this on deployed) | unverifiable |
| Variant A charts | 168 | **UNKNOWN** (no migration endpoint on deployed) | unverifiable |
| `lifeline_events_total` | 22 | 47 | **NO — different dataset confirmed** |

---

## 6. Conclusive determinations

### Q1. Is deployed == preview?
**No.** Different `db_name`, different `db_uri_last_4`, different `lifeline_events_total`, different `env` label. Four independent markers all disagree.

### Q2. Is deployed using localhost?
**No.** `db_uri_last_4 = "rity"` is incompatible with any `mongodb://...:27017` URI (which always ends in `7017`). It is the unambiguous tail of `?retryWrites=true&w=majority`, the canonical Atlas SRV query-string suffix.

### Q3. Is deployed using Atlas?
**Yes — with high confidence, by inference.** The evidence chain:
1. `db_uri_last_4 = "rity"` is the last 4 chars of `?retryWrites=true&w=majority`, the standard Atlas SRV suffix.
2. The Emergent dashboard Database tab shows `mongodb+srv://…onkipa.mongodb.net` for this deployment.
3. The deployed environment label is `staging`, and the database name `expo-bundle-issue-mirror_staging` carries an explicit `_staging` suffix matching the workspace slug.
4. No `mongodb://localhost`-style URI ever ends in `"rity"`.

**Caveat (the one thing not directly proven):** the deployed `/api/health` endpoint deliberately exposes only the last 4 chars of the URI, so we cannot read the cluster hostname (`onkipa.mongodb.net`) off the wire. The dashboard says it; the suffix is consistent with it; nothing contradicts it; but the deployed runtime does not echo the full hostname back. Treat the Atlas-cluster identity as **dashboard-attested + suffix-consistent**, not byte-for-byte echoed.

### Q4. Does the prior 168/171 migration census apply to deployed?
**No, and cannot be assumed.** The census was generated against `mongodb://localhost:27017/test_database`. The deployed app is wired to `expo-bundle-issue-mirror_staging` on Atlas — a **different database**. Because:
* the deployed image exposes no `/api/diagnostics/charts`, `/migration`, or `/variant-a` endpoint,
* and no read-only Atlas credentials are provisioned in this workspace,

we have **zero direct evidence** for how many charts, users, or Variant A records the deployed DB contains. The `lifeline_events_total` divergence (22 vs 47) is independent proof that the deployed DB holds *different data*, so transposing the 168/171 figure would be unsound.

---

## 7. What remains unprovable from this workspace

| Question | Why not provable | What would unblock it |
|---|---|---|
| Full Atlas cluster hostname | `/api/health` truncates URI to last 4 chars | A `/api/diagnostics/mongo-status` endpoint on the deployed bundle that exposes `{cluster_host, replica_set, srv: true}`, or a deploy that ships the existing diagnostics; **or** dashboard inspection (out-of-band, already done by user) |
| Deployed `users` / `charts` counts | No `/api/diagnostics/db` on deployed bundle | Either ship a newer deployed bundle (the workspace already has this endpoint), or provision read-only Atlas creds for a one-shot `db.collection.estimatedDocumentCount()` census |
| Deployed Variant A migration progress | No `/api/diagnostics/migration` or `/variant-a` on deployed | Same — ship newer bundle **or** read-only Atlas creds |
| ID overlap between workspace `test_database` and deployed Atlas `expo-bundle-issue-mirror_staging` | Cannot enumerate Atlas from here | Read-only Atlas creds for a one-shot `_id` set intersection |
| Whether deployed has any users that workspace lacks (incl. `Ana`) | Same | Same |

---

## 8. Read-only reproduction commands

```bash
DEPLOY="https://mirror-lens-fixes-r-1779710763.emergent.host"
PREVIEW="https://hd-incarnation-fix.preview.emergentagent.com"

# Deployed health (no auth, no writes)
curl -s "$DEPLOY/api/health" | jq '{env: .debug.env, db_name: .debug.db_name, last4: .debug.db_uri_last_4, lifeline: .debug.lifeline_events_total, build: .build.deployed_bundle, validation: .build.validation}'

# Preview health (baseline)
curl -s "$PREVIEW/api/health"  | jq '{env: .debug.env, db_name: .debug.db_name, last4: .debug.db_uri_last_4, lifeline: .debug.lifeline_events_total}'

# Deployed astro-engine config
curl -s "$DEPLOY/api/diagnostics/astro-system" | jq '{zodiac_mode, ophiuchus_enabled, runtime_guard_active, svp: .ayanamsa_or_svp}'

# Deployed diagnostic surface inventory (most return 404 → narrower than workspace)
for ep in /api/diagnostics /api/diagnostics/mongo-status /api/diagnostics/db /api/diagnostics/charts /api/diagnostics/migration /api/diagnostics/variant-a; do
  printf "%3s %s\n" "$(curl -s -o /dev/null -w '%{http_code}' "$DEPLOY$ep")" "$ep"
done
```

---

## 9. One-paragraph bottom line

The deployed container at `mirror-lens-fixes-r-1779710763.emergent.host` is a **separate environment** from the workspace. It runs in `env=staging`, against database `expo-bundle-issue-mirror_staging`, on a Mongo URI whose tail (`…rity`) is unambiguously the Atlas SRV suffix `?retryWrites=true&w=majority` — fully consistent with the `mongodb+srv://…onkipa.mongodb.net` cluster shown in the Emergent dashboard, and *incompatible* with the workspace's `mongodb://localhost:27017`. The two environments are **not reading the same database**. The 168/171 Variant A census applies to the workspace only and **must not be transposed** onto the deployed Atlas DB without a fresh, read-only census run against Atlas itself. The deployed bundle is also stale (built 2026-05-31, source last touched 2026-06-09) and exposes a narrower diagnostic surface, so deeper count/migration verification against Atlas requires either a newer deployed bundle that ships the existing `/api/diagnostics/*` endpoints, or read-only Atlas credentials provisioned into this workspace.

**No DB writes, no chart recomputes, no migrations, no flag flips occurred during this audit.**
