# DATABASE TOPOLOGY TRUTH REPORT
**Generated:** 2026-06-13 (read-only audit)
**Scope:** Determine the actual `MONGO_URL` / `DB_NAME` in use by the workspace backend, the preview endpoint, and the deployed app. Reconcile with the Atlas URI (`mongodb+srv://…onkipa.mongodb.net`) seen in the Emergent deployment "Database" tab.
**Mutation policy:** **READ-ONLY.** No DB writes, no chart recomputes, no migrations, no flag flips. All credentials redacted.

---

## 1. Workspace backend (this pod)

| Field | Value |
|---|---|
| `MONGO_URL` (from `/app/backend/.env`) | `mongodb://localhost:27017` |
| `DB_NAME` (from `/app/backend/.env`) | `test_database` |
| Loader | `dotenv.load_dotenv()` in `server.py` |
| Supervisor `environment=` override | **None for Mongo** — only `APP_URL`, `INTEGRATION_PROXY_URL` are injected (see `/etc/supervisor/conf.d/supervisord.conf` `[program:backend]`) |
| `/proc/<backend-pid>/environ` contains `MONGO_URL`? | **No** — confirms the value is read from the `.env` file at process start, not inherited from the kernel/supervisor environment |
| Local mongod process | `mongod --bind_ip_all` running as PID 185 on default port `27017` |

**Conclusion:** Workspace backend uses `mongodb://localhost:27017` / `test_database`. No Atlas connection from this process.

---

## 2. Preview backend (`https://hd-incarnation-fix.preview.emergentagent.com`)

Live probe of the public preview URL — self-reported by the backend's own health endpoint (no shell access required):

```
GET /api/health
{
  "ok": true,
  "service": "backend",
  "timestamp": "2026-06-13T11:21:34Z",
  "debug": {
    "env": "unknown",
    "db_name": "test_database",
    "db_uri_last_4": "7017",        // last 4 chars of "mongodb://localhost:27017"
    "collections": [ "user_recent_actions", "pattern_memory", "forum_relationship_edges",
                     "home_history", "forum_mirror_chat_messages", "migration_reports",
                     "lifeline_events", "charts", "user_timeline", ... ],
    "lifeline_events_total": 22
  },
  "build": {
    "git_revision": "c384a6f3",
    "git_dirty": true,
    "deployed_bundle": { "timestamp": "2026-05-31 03:45:49 UTC", "hash": "5ae9551bb335" }
  }
}
```

The reported `lifeline_events_total = 22` and the collection set exactly match what `mongosh` reports for the local `test_database` (`lifeline_events` = 22 docs — see §6). The `db_uri_last_4 = "7017"` is the last four characters of `mongodb://localhost:27017`.

**Conclusion:** The **preview URL is identical to the workspace backend** — it terminates at the same uvicorn process inside this pod (port 8001), backed by local mongod. **Preview ≠ a separate environment.**

---

## 3. Deployed backend (Emergent "Publish" / `emergent.host` namespace)

| Hostname probed | Status |
|---|---|
| `https://hd-incarnation-fix.emergent.host/api/health` | `HTTP 400 — "Deployment not found"` |
| `https://hd-incarnation.emergent.host/api/health` | `HTTP 400 — "Deployment not found"` |
| `https://8e5a01c3-…-b92600529403.emergent.host/api/health` | `HTTP 400 — "Deployment not found"` |
| `https://8e5a01c3-…-b92600529403.preview.emergentagent.com/api/diagnostics/astro-system` | `HTTP 404` (not the live tunnel) |

**No `.emergent.host` deployment is currently reachable for this workspace.** The only live, externally reachable backend that responds is the **preview URL** (= workspace pod), which is provably on `mongodb://localhost:27017`.

If a separate published instance does exist on the user's Emergent dashboard and is bound to the Atlas URI (`mongodb+srv://…onkipa.mongodb.net`), **it runs in a different container that this workspace cannot reach.** No truth-claim about that deployed instance can be made from inside this pod beyond what the dashboard UI shows.

---

## 4. Is the deployed app actually connected to localhost or Atlas?

| Environment | Verified `MONGO_URL` | Verified `DB_NAME` | Source of truth |
|---|---|---|---|
| Workspace pod (uvicorn PID 182) | `mongodb://localhost:27017` | `test_database` | `/app/backend/.env`, supervisor env, `/proc/<pid>/environ` |
| Preview URL (`hd-incarnation-fix.preview.emergentagent.com`) | `mongodb://localhost:27017` | `test_database` | `GET /api/health` self-report (`db_uri_last_4=7017`, collection set matches local) |
| Deployed URL (`*.emergent.host` namespace) | **UNKNOWN — endpoint not reachable from this pod** | **UNKNOWN** | "Deployment not found" for every probed hostname |
| Atlas cluster `mongodb+srv://…onkipa.mongodb.net` | **NOT CONNECTED FROM THIS POD** | n/a | No credentials present in `.env`, `/proc/<pid>/environ`, `/etc/secrets`, `/run/secrets`, or any code path. The only references to Atlas in the codebase are *template strings* in audit runbooks (see §5). |

**Definitive answer for what this pod runs:** localhost / `test_database`.
**Definitive answer for the published deployed instance:** **cannot be proven from inside this workspace.** The Atlas URI shown in the Emergent deployment Database tab is the configured target for the *published* container, but verifying that the running deployed backend actually connects to it requires either (a) a live, reachable deployed URL we can hit, or (b) operator credentials/runbook execution outside this workspace.

---

## 5. What can and cannot be proven from this workspace

### ✅ Provable (and proven above)
1. The workspace backend process (PID 182, uvicorn on `0.0.0.0:8001`) is wired to `mongodb://localhost:27017` / `test_database` — confirmed by `.env`, supervisor config, and `/proc/<pid>/environ`.
2. The public preview hostname `hd-incarnation-fix.preview.emergentagent.com` is served by that same process — confirmed by `db_uri_last_4=7017`, `db_name=test_database`, and collection cardinality matching local `mongosh`.
3. No Atlas connection string is present anywhere this workspace can see:
   - `/app/backend/.env` — localhost only.
   - `/app/backend/.env.bak.pre-stage1-2026-06-12` — localhost only.
   - `/proc/182/environ` — no `MONGO_*` keys.
   - `/etc/secrets`, `/run/secrets` — not present.
   - Atlas references in the codebase are **template strings only**:
     - `audit_reports/PFS26_OPERATOR_RUNBOOK.md` → `mongodb+srv://<readonly-user>:[REDACTED]@<cluster>/…`
     - `audit_reports/PFS26_PRODUCTION_COMMANDS.md` → same placeholder.
     - `scripts/pfs25_graph_audit.py` → docstring example `mongodb+srv://...`.
   - **No file contains a substituted Atlas hostname, user, or password.** `onkipa.mongodb.net` does not appear in any file under `/app`.

### ❌ Not provable from this workspace
1. Whether the **published** deployed container points at `mongodb+srv://…onkipa.mongodb.net` or at a different URI. The `.emergent.host` namespace returns `Deployment not found` for every candidate hostname we could derive locally; the deployed container's env is set by the Emergent control plane, not by anything in this pod.
2. The **document counts, user list, or migration state** of the Atlas cluster. Without credentials and network reachability, we cannot enumerate, sample, or even confirm cluster existence beyond the URI string visible in the user-facing dashboard.
3. Whether the Atlas cluster shares schema, IDs, or data with the local `test_database`. There is no evidence either way.

To close these gaps the user must either (i) provision a read-only Atlas connection string into the pod for a one-shot read-only census, or (ii) share the deployed `.emergent.host` URL so we can hit `/api/health` and read its self-reported `db_name` / `db_uri_last_4`.

---

## 6. User / chart counts per accessible database (local mongod only)

`mongosh --quiet` against `mongodb://localhost:27017` — read-only `estimatedDocumentCount` on `users` and `charts` for every non-system database:

| Database | `users` | `charts` | Notes |
|---|---:|---:|---|
| **`test_database`** | **175** | **171** | Active app DB — matches `DB_NAME` in `.env`. Contains all 66 application collections (`user_timeline`=363, `forum_chat_messages`=38, `mirror_chat_retrieval_receipts`=354, `home_engagement_sessions`=342, etc.). |
| `project_mirror` | 1 | 1 | Orphan, almost empty. |
| `projectmirror` | 2 | 1 | Orphan, almost empty. |
| `mirror_db` | 1 | 0 | Orphan (only `lifeline_events`=16, `pattern_memory`=1, `users`=1). |
| `mirror_app` | 1 | 0 | Orphan (only `users`=1). |
| `mirrordb` | 0 | 0 | Orphan (only `facet_history`=5). |
| `emergent_db` | 0 | 0 | Orphan (only `pattern_exposures`=1). |

No Atlas DB counts can be listed (see §5).

---

## 7. Does the 168 / 171 migration census apply to the live deployed app?

The previously published `MIGRATION_READINESS_CENSUS.md` (171 charts total, 168 canonical, 3 unmigratable demo seeds) was generated by querying `mongodb://localhost:27017/test_database` from inside this workspace.

| Environment | Census applies? |
|---|---|
| Workspace backend | **YES** — same DB. |
| Preview URL (`hd-incarnation-fix.preview.emergentagent.com`) | **YES** — proven in §2 to be the same process / same DB. |
| Deployed (Atlas-bound) container | **NO** — the census was never run against Atlas. Atlas chart and user counts, migration status, and ID overlap with the local `test_database` are **unverified**. Treat the 168/171 figure as a **workspace-only fact**, not a production fact. |

---

## Auditor's read-only commands (for reproducibility)

```bash
# 1. .env contents (redacted)
grep -E "^(MONGO_URL|DB_NAME)" /app/backend/.env

# 2. Confirm running backend inherits no MONGO_* from kernel
tr '\0' '\n' < /proc/182/environ | grep -iE "MONGO|ATLAS"   # → empty

# 3. Preview self-report
curl -s https://hd-incarnation-fix.preview.emergentagent.com/api/health | jq '.debug'

# 4. Atlas reachability from pod
grep -RniE "(onkipa|mongodb\+srv)" /app --include="*.py" --include="*.md" --include="*.env*"
#   → only template strings, no substituted credentials

# 5. Deployed host reachability
for h in hd-incarnation-fix.emergent.host hd-incarnation.emergent.host; do
  curl -sS -o /dev/null -w "%{http_code} $h\n" -m 8 "https://$h/api/health"
done   # → 400 "Deployment not found" for all

# 6. Per-DB counts on local mongod
mongosh --quiet --eval '...estimatedDocumentCount on users/charts...'
```

---

## Bottom line (one sentence each)

1. **Workspace + preview = same pod = `mongodb://localhost:27017` / `test_database`.** Proven.
2. **The Atlas URI seen in the Emergent dashboard cannot be verified, probed, or reconciled from inside this workspace.** No credentials, no reachability.
3. **The 168/171 migration census is a `test_database` fact, not a deployed/Atlas fact.** Do **not** assume the deployed cluster shares that state until either (a) the deployed `/api/health` is reachable, or (b) read-only Atlas credentials are provisioned for a one-shot census.

**No DB writes, no chart recomputes, no migrations, no flag flips occurred during this audit.**
