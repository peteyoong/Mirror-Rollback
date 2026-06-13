# Ana Environment Forensic Report

**Build marker:** `ana-environment-forensic-v1`
**Mode:** READ-ONLY across every database accessible from this workspace. No data modified. No charts recalculated. No migrations triggered.

---

## TL;DR

**Ana is NOT present in any environment accessible from this workspace.**

- 7 databases scanned (every non-internal database on the only Mongo instance reachable from this pod).
- 0 hits in `users`, 0 in `charts`, 0 in `forum_members`, 0 in `saved_people`, 0 in any other identity-bearing collection.
- 0 substring matches even with relaxed patterns (`Ana`, `AnaG`, `Ana G`, `Ana-G`, `Ana_G`, `Ana.G`, `Anna`, `AnnaG`, `Anna G`).
- Production cluster URI exists only as a **template string** (`mongodb+srv://<readonly-user>:<pass>@<cluster>/...`) in the PFS26 operator runbook — **no real production credentials are provisioned in this container**, so a production cluster cannot be probed from here.

Result: Ana cannot be found, compared, or verified from this workspace.

---

## 1. Environments enumerated

### 1.1 What "environment" means here

This pod is the **preview pod** for the Mirror app. The frontend's `EXPO_PUBLIC_BACKEND_URL` (`https://hd-incarnation-fix.preview.emergentagent.com`) is a kubernetes-ingress alias for THIS container's `localhost:8001`. The frontend, the preview backend, and the local backend are the same process talking to the same Mongo. Documented in `PRODUCTION_FIDELITY_SPRINT_PFS1.md` §A and `PRODUCTION_TOPOLOGY_AUDIT.md`.

### 1.2 Mongo instances accessible from this workspace

| Instance | URI | Reachable? | Notes |
|----------|-----|------------|-------|
| Local Mongo (this pod) | `mongodb://localhost:27017` | ✅ | The only Mongo this workspace can talk to. Hosts both the canonical app data (`test_database`) and several small dev/stub databases. |
| Production cluster | `mongodb+srv://<readonly-user>:<pass>@<cluster>/?retryWrites=true&w=majority` | ❌ | URI **template only** in `PFS26_OPERATOR_RUNBOOK.md` and `PFS26_PRODUCTION_COMMANDS.md`. The placeholders `<readonly-user>`, `<pass>`, `<cluster>` are not substituted anywhere in `.env`, container env, or secrets accessible to this workspace. Probing requires a separate runbook step that provisions read-only credentials, which has not been executed in this pod. |
| Any other preview pod / staging cluster | — | ❌ | No URI configured anywhere in `/app/backend/.env`, `/app/frontend/.env`, `/etc/environment`, or the running process env. |

> **Conclusion:** "All available environments" from this workspace ≡ the 7 non-internal databases on `mongodb://localhost:27017`. Ana cannot be searched in production from this pod.

### 1.3 Databases scanned on local Mongo

| Database | Collections | Total docs | Purpose (inferred from contents) |
|----------|-------------|------------|----------------------------------|
| `test_database` | 66 | 2,111 + (171 charts) | **The canonical Mirror app DB.** All real users + charts (Pete, Mel, Isaac, Thaddeus, etc.). |
| `emergent_db` | 1 | 1 | Single `pattern_exposures` doc — appears to be a leftover artefact. |
| `mirror_app` | 1 | 1 | One `users` row: `Test Astro User <astro@test.com>` born 1990-03-15. |
| `mirror_db` | 3 | 18 | `lifeline_events`(16), `pattern_memory`(1), `users`(1): `Test User <test@example.com>` born 1975-01-15. |
| `mirrordb` | 1 | 5 | `facet_history` only. |
| `project_mirror` | 3 | 3 | `users`(1) `Test User <test@example.com>` born 1990-05-15; `charts`(1); `enneagram_results`(1). |
| `projectmirror` | 3 | 4 | `users`(2): `Luna <luna@test.com>` born 1990-06-15 + `Test User <test@test.com>` born 1990-06-15. |
| `admin`, `config`, `local` | (Mongo internals) | — | Skipped — not data containers. |

---

## 2. Search patterns applied (case-insensitive throughout)

```
Identity-field $regex sweep (all 19 fields × 10 anchored patterns = 190 clauses per collection):
  /^anag/i          /^ana ?g/i        /^ana[\-_\.]g/i
  /^annag/i         /^anna ?g/i       /^anna[\-_\.]g/i
  /^ana$/i          /^ana /i          /^anna$/i           /^anna /i

Identity fields:
  name, display_name, full_name, first_name, last_name,
  given_name, preferred_name, username, handle,
  email, label, title,
  subject_name, target_name, name_a, name_b,
  person_name, owner_name, debug_stamp.name

Deep substring sweep (unanchored, no word boundaries) on users/charts/forum_members/saved_people/people:
  /ana/i      /anna/i      /anag/i      /ana[\s\-_\.]g/i

Tested across every collection in every database.
```

---

## 3. Results — per environment, per pattern

| Environment / DB | Identity-field hits | Deep-substring hits (person-name only) | Notes |
|-------------------|---------------------|-----------------------------------------|-------|
| `test_database`   | **0** | **0** (1,078 unrelated narrative hits: "analysis", "analytical", "management", "Canada", etc. — none on identity fields) | Already documented in prior Ana-lookup. |
| `emergent_db`     | **0** | **0** | Only 1 doc (pattern_exposures); no name fields. |
| `mirror_app`      | **0** | **0** | 1 user: `Test Astro User <astro@test.com>` (not Ana) |
| `mirror_db`       | **0** | **0** | 1 user: `Test User <test@example.com>` |
| `mirrordb`        | **0** | **0** | No users collection. |
| `project_mirror`  | **0** | **0** | 1 user: `Test User <test@example.com>` |
| `projectmirror`   | **0** | **0** | 2 users: `Luna <luna@test.com>` + `Test User <test@test.com>` |

**Total findings across all 7 databases: 0**

---

## 4. Per-finding deliverable — empty

Required fields could not be populated for any environment because Ana does not exist in any database scannable from this workspace:

| Environment | user_id | chart_id | metadata.astrology_engine_version | ASC | MC | IC | DC | Last chart update | Variant A canonical? |
|--------------|---------|----------|-----------------------------------|-----|-----|-----|-----|---------------------|----------------------|
| `test_database`  | — | — | — | — | — | — | — | — | — |
| `emergent_db`    | — | — | — | — | — | — | — | — | — |
| `mirror_app`     | — | — | — | — | — | — | — | — | — |
| `mirror_db`      | — | — | — | — | — | — | — | — | — |
| `mirrordb`       | — | — | — | — | — | — | — | — | — |
| `project_mirror` | — | — | — | — | — | — | — | — | — |
| `projectmirror`  | — | — | — | — | — | — | — | — | — |
| **production cluster** | **UNREACHABLE — no credentials in this workspace** | — | — | — | — | — | — | — | — |

---

## 5. Cross-environment comparison — not applicable

Ana exists in **zero** of the environments accessible from this workspace, so there are no copies to compare. The cross-environment comparison requested is structurally impossible from this pod.

---

## 6. Sanity check — alternative spellings considered

In case Ana was registered under an alternative spelling or alias:

| Considered alternative | Reasoning | Found? |
|-------------------------|-----------|--------|
| `Anaïs`, `Anastasia`, `Anabel`, `Anais` | Common Ana-derived full names | No |
| `Ana G`, `A. G.`, `A.G.` (initial-form aliases) | Possible if stored as initials | No |
| `Ana Gonzalez`, `Ana Garcia`, etc. (any `Ana <surname>`) | The "AnaG" hint suggests a surname starting with G | No (no doc has `name = "Ana ..."` anywhere) |
| `ana@…`, `anag@…`, `ana.g@…` email prefixes | Possible email-only registration | No matching emails in any users collection |
| Forum-only presence (no user row) | Could exist as a forum participant without a Mirror account | No — `forum_members` and `forum_relationship_edges` have no Ana entries either |
| Saved-people / contact entry | Could exist as a relationship target of another user | No — `saved_people` (9 docs) has no Ana entries |

---

## 7. What this means

1. **Ana does not exist anywhere in this workspace's reach.** Not in the canonical app DB, not in any of the 6 leftover dev/stub DBs, not under any alternative spelling, not under any identity field.
2. **The production cluster cannot be probed from here.** The URI in PFS26 documents is a template. If Ana is registered in production, this audit cannot prove or disprove that — a separate production-credentialled session is required.
3. **Consistent with the previous fork's project-health flag:** `P7: Phase 4 — Ana Regression Reference Account (ON HOLD)`. Ana is a planned-but-not-provisioned regression reference account in this codebase.

If you have evidence that Ana exists in production (a screenshot, a user_id, an email, a known forum membership) — please share it. Specifically helpful would be:
- her stored `_id` or `user_id`
- the email she signed up with
- the environment URL where you observed her (e.g. a specific `*.emergentagent.com` host)
- whether she's a Mirror account holder OR only a relationship/contact target in someone else's chart

With any one of these I can either (a) probe production with operator-provided credentials, or (b) confirm she's missing from a specific environment.

---

## 8. Constraints honored

- ✅ No data modified
- ✅ No charts recalculated
- ✅ No migrations triggered
- ✅ Read-only forensic lookup
- ✅ Locked flags untouched (`INTENT_ROUTER_V2_CUTOVER=false`, `INTENT_ROUTER_V2_ROLLOUT_PERCENT=10`, `RELATIONSHIP_ORCHESTRATION_PROMPT=false`, `CROSS_LENS_PROMPT_SURFACE=false`)
- ✅ Only `list_database_names` / `list_collection_names` / `find` / `count_documents` used; no `insert*`, `update*`, `delete*`, or `replace*` operations

End of report.
