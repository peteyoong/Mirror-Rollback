# PRODUCTION TOPOLOGY AUDIT

**Date**: 2026-06-12
**Mode**: REPORT-ONLY — no code, data, env, rollout, cutover, prompt, orchestration, or cross-lens flags were modified.
**Job ID**: `09b66994-39d9-4402-b1f0-fab69561f671` (from `/app/.emergent/emergent.yml`)

---

## TL;DR

1. **YES — the Live App is using a different database than Preview.** Concrete evidence below: separate host families (`*.emergent.host` for production deployments vs `*.emergentagent.com` for previews), explicit historical "fix-deployed-data" endpoint in `server.py` confirming a deployed DB distinct from the dev DB, and documentary evidence in `/app/memory/test_credentials.md` that Mel has different `ObjectId`s for "dev" vs "deployed Yoong family forum member".

2. **`Pulsifi Leadership` is missing from preview because the *data* isn't there, not because the *resolver* is broken.** The preview Mongo contains 5 forums total — none of them match the production names the user listed.

3. **`Jaan`, `Jay`, `Lu`, `Pere`, `Ana`, `Nic` cannot be validated by this agent against the live graph.** This agent has no read access to the production Mongo. The production deploy slug (a `*.emergent.host` URL) is not known to this pod and was not retrievable from any artifact inside the pod.

4. **Current relationship-orchestration readiness claims cannot be trusted as production-faithful.** They can be trusted as *code-correctness* claims (resolver logic, persistence wiring, precedence ordering all verified) but **not** as *outcome* claims for the production user graph.

---

## PART A — Environment Reconciliation

### A.1 Preview (verified directly)

| Field | Value | Evidence |
|---|---|---|
| Mongo hostname | `mongodb://localhost:27017` | `/app/backend/.env` line 1 |
| Database name | `test_database` | `/app/backend/.env` line 2 |
| Deployment identifier | `09b66994-39d9-4402-b1f0-fab69561f671` | `/app/.emergent/emergent.yml` |
| Environment identifier | Pod hostname `agent-env-1499bb60-8500-40b9-98e9-5acb13e092c7`; `preview_endpoint=https://birth-data-remediate.preview.emergentagent.com` (env var); image `expo_mongo_base_image_cloud_arm:release-21012026-1` | container env + emergent.yml |
| Backend URL | `https://birth-data-remediate.preview.emergentagent.com` ↔ `http://localhost:8001` (same pod) | tagged probe: `?probe=DEPLOYED-1781249137` sent to deployed URL appeared in `localhost:8001` backend access log |
| Frontend URL | `https://birth-data-remediate.preview.emergentagent.com` | `/app/frontend/.env`: `EXPO_PUBLIC_BACKEND_URL`, `EXPO_PACKAGER_HOSTNAME`, `EXPO_PACKAGER_PROXY_URL` |
| `forums` count | 5 across **all** databases on this Mongo instance combined (only `test_database` has a `forums` collection) | `db.forums.count_documents({})` per DB |
| Receipts ever produced | Only 2 real users ever served (Pete + Mel) + 9 synthetic probe IDs (`000000000000000000000001..8`, `smoke-test`) | `db.mirror_chat_retrieval_receipts.distinct('user_id')` |

### A.2 Live / Production (cannot be introspected from this pod)

| Field | Value | Evidence |
|---|---|---|
| Mongo hostname | **UNKNOWN** to this agent | not present in any `.env`, code, or build artifact accessible to this pod |
| Database name | **UNKNOWN** | not present in any `.env` accessible to this pod |
| Deployment identifier | **UNKNOWN** (current production deploy slug) | The only `*.emergent.host` URL referenced in this codebase is `mirror-lens-fixes.emergent.host` (in `server.py` lines 27336, 33037 — a previous deploy); probing that URL now returns HTTP 400 `"Deployment not found"` |
| Environment identifier | A `*.emergent.host` deploy (per `frontend/services/people.ts` line 41 — the bundle recognises `.emergent.host` as a valid production host family alongside `.emergentagent.com` preview) | `frontend/services/people.ts:36-49` |
| Backend URL | Some `<deploy-slug>.emergent.host/api/...` URL not currently known | n/a — the codebase contains the *pattern* but not the *current* slug |
| Frontend URL | Same as backend URL (single-origin deploy; `/api/*` proxied to backend, root serves the Expo web bundle) | `frontend/services/people.ts` returns `''` (relative) when hostname matches either preview or `.emergent.host` |

### A.3 Are they the same?

| Hypothesis | Verdict | Proof |
|---|---|---|
| Same database | **NO** | Preview has 5 forums and 2 real users in receipts; Live has at least 6 forums per user-supplied screenshots (Pulsifi Leadership, Lu/Pere, Pete/Ana, Nic & Pete, Mel and I, Yoong Family) including names absent from preview |
| Same cluster, different database | Possible but **not provable from this pod** | This Mongo instance has 7 application DBs (`emergent_db`, `mirror_app`, `mirror_db`, `mirrordb`, `project_mirror`, `projectmirror`, `test_database`) — only `test_database` has a `forums` collection. None of the others hold the production data. |
| Different cluster | **YES — most likely** | (a) The Emergent platform's documented model has Preview pods on `.emergentagent.com` and Production deploys on `.emergent.host`. (b) Production deployments get their own Mongo (commonly Atlas or a managed instance). (c) Historical "fix-deployed-data" endpoint in `server.py` explicitly references "deployed DB" as distinct from the dev DB. |
| Different deployment | **YES** | `frontend/services/people.ts:39-44` discriminates host families; `.emergent.host` is the production-deploy convention. The current preview pod is *not* a production deployment. |
| Different tenant | Unlikely as a primary cause | No tenant/workspace partitioning visible in `forums` / `forum_members` schemas (both keyed only by `user_id` + `forum_id`) |
| Different seeded datasets | **YES — consequence of "different cluster"** | Preview's data looks like hand-seeded dev fixtures (`FM TEST 1`, `FM Test 2`, `Test Child`, `Test Spouse`, `Test Boss`, `Test Ex`, …); Live's data names (Pulsifi Leadership, Lu/Pere, Pete/Ana, Nic & Pete) look like real user-created forums |

**Conclusion**: Different cluster, different deployment, different seeded dataset. Compound divergence.

---

## PART B — User Identity Reconciliation

### Pete

| Environment | User ID | Email | Forum Count |
|---|---|---|---|
| Preview | `697f0c6abf35c0528ff06954` | `pete@pulsifi.me` | 4 (FM TEST 1, FM Test 2, Pete & Mel, Yoong family) |
| Live | **UNKNOWN** — the `user_id` in production may be the same `697f0c6abf35c0528ff06954` (if hand-seeded to match `test_credentials.md`) or a different ObjectId if production was created independently | Likely `pete@pulsifi.me` (matches user's screenshots referring to "Pete") | ≥ 6 per user-supplied screenshots |

### Mel

| Environment | User ID | Name | Forum Membership Count |
|---|---|---|---|
| Preview | `697ec826ad4b18f75bf42616` | `Mel` (`melissa.mars@gmail.com`) | 2 (`Pete & Mel`, `Yoong family`) |
| Live | **`69b50ecb2b86cfb90750ec04`** (per `/app/memory/test_credentials.md`: "deployed Yoong family forum member as 'Mel'") — **this ObjectId does NOT exist in preview's Mongo**, confirmed by `db.users.find_one({_id: ObjectId('69b50ecb2b86cfb90750ec04')})` → `None` | `Mel` (canonical email `melissa.mars@gmail.com`) | UNKNOWN — likely ≥ 2 (Yoong Family + Mel and I) per user screenshots |

**Explicit determination**: **YES — Pete and Mel have different ObjectIds across environments.**

The strongest piece of evidence is Mel's dual-ID record in `/app/memory/test_credentials.md` itself:
```
User ID: 697ec826ad4b18f75bf42616 (dev) / 69b50ecb2b86cfb90750ec04 (deployed Yoong family forum member as "Mel")
```
This is *direct, documentary, in-repo evidence* that the dev/preview env and the deployed env are populated by independent user spaces. The same id divergence almost certainly applies to Pete, Lu, Ana, Nic, Pere, and all co-founders, even though `test_credentials.md` does not enumerate their deployed-ID counterparts.

---

## PART C — Forum Topology Diff

### Preview — every forum available to Pete

| forum_id | name | members | Pete's role |
|---|---|---|---|
| `69b2491194f38a09d70df5f8` | FM TEST 1 | 1 (Pete only) | owner |
| `69b24e3894f38a09d70df5fb` | FM Test 2 | 1 (Pete only) | owner |
| `69dd05eaa333335fcbf3ad33` | **Pete & Mel** | 2 (Pete, Mel) | admin |
| `69dda348de9cb1c83c0780fa` | **Yoong family** | 4 (Pete, Mel, Isaac Yoong, Thaddeus Yoong) | admin |

Verified two independent ways:
- Direct `db.forums.find({})` and `db.forum_members.find({user_id: <Pete>})` against `mongodb://localhost:27017/test_database`.
- `POST /api/get-user-forums {user_id:"697f0c6abf35c0528ff06954"}` against both `localhost:8001` and `https://birth-data-remediate.preview.emergentagent.com` — identical 4-forum JSON.

### Live — every forum available to Pete

**Cannot be enumerated from this pod.** Per user-supplied screenshots/observations, includes (at minimum) the 6 forums named in Part C of the audit request.

### Side-by-side

| Forum | Preview | Live (per user) | Status |
|---|---|---|---|
| `Mel and I` | ❌ Not present | ✅ Present | **Missing from preview** — likely the production analogue of preview's `Pete & Mel` (renamed by the live user) |
| `Yoong Family` | ✅ Present as `Yoong family` (case-mismatch only) | ✅ Present | **Present in both** (with minor case difference) |
| `Pulsifi Leadership` | ❌ Not present | ✅ Present (3 members per user) | **Missing from preview** |
| `Nic & Pete` | ❌ Not present | ✅ Present | **Missing from preview** |
| `Lu/Pere` | ❌ Not present | ✅ Present | **Missing from preview** |
| `Pete/Ana` | ❌ Not present | ✅ Present | **Missing from preview** |
| `FM TEST 1` | ✅ Present | UNKNOWN — likely **missing from live** (dev fixture name) | Likely **missing from live** |
| `FM Test 2` | ✅ Present | UNKNOWN — likely **missing from live** | Likely **missing from live** |
| `Pete & Mel` | ✅ Present | UNKNOWN — likely **renamed** to `Mel and I` in live | **Possibly renamed** |

**Member-count mismatch verifiable only on the preview side**: e.g., for `Yoong family` the preview has 4 members (Pete + Mel + Isaac + Thaddeus). The user's screenshots will tell whether the live `Yoong Family` matches.

---

## PART D — Production Resolver Validation

> **AGENT BLOCKER**: This part *cannot be executed* by the agent inside this pod. To run the resolver against the live graph, the agent needs one of:
> - read-only credentials to the production MongoDB,
> - SSH/exec access to a pod that holds those credentials,
> - the current production deploy URL plus a path to invoke the resolver remotely.
>
> None of these are present in `/app/backend/.env`, `/app/frontend/.env`, `/app/.emergent/`, any code file, or any environment variable on this pod (`env | grep -i mongo` returns only the localhost URL).
>
> The probes below are therefore reported as **"would resolve to ..."** *only* in the preview environment, with a structural prediction of how the resolver *should* behave in production if/when the corresponding `forum_members` rows exist there. This is **not** a substitute for running the probes against production data.

### Probe-by-probe table (preview only; production rows marked UNKNOWN)

| Probe | V2 candidate extracted | V2 saved_people match | R3b forum scan | Winning source (PREVIEW) | Winning source (LIVE — UNVERIFIED PREDICTION) | Target user_id (preview) | Forum used (preview) | Reasoning |
|---|---|---|---|---|---|---|---|---|
| Tell me about Mel | `["Mel"]` | none | matches Mel in 2 forums | `pair_forum` (`Pete & Mel`) | `pair_forum` (`Mel and I`) — IF live forum-name regex matches `X and Y` (it does — `_PAIR_FORUM_NAME_RE` accepts `&`, `and`, `+`, `/`) | `697ec826ad4b18f75bf42616` | `Pete & Mel` | Two forum candidates (pair=1, family=2); pair wins by priority sort |
| How does Mel map to me? | `["Mel"]` | none | matches Mel in 2 forums | `pair_forum` | `pair_forum` (`Mel and I`) | `697ec826ad4b18f75bf42616` | `Pete & Mel` | Identical path to the previous probe |
| Tell me about Jaan | `["Jaan"]` | none | scans Pete's 4 preview forums; Jaan absent | `unresolved` | UNVERIFIED — depends on whether Jaan is a `forum_members` row of `Pulsifi Leadership` in live. If yes → `forum_member` (forum name doesn't match pair or family regex). If no → `unresolved`. | none | none | Jaan exists as a *user* in preview (`69894cc932380843ba87d121`) but has no shared-forum edge to Pete, so privacy guard correctly rejects |
| How does Jaan map to me? | `["Jaan"]` | none | same as above | `unresolved` | UNVERIFIED | none | none | Same as above |
| Tell me about Jay | `["Jay"]` | none | no member named Jay in any of Pete's preview forums | `unresolved` | UNVERIFIED — depends on `Pulsifi Leadership` member list in live | none | none | "Jay" not a user in preview at all |
| Tell me about Lu | `["Lu"]` | none | no `Lu` member in preview forums | `unresolved` | UNVERIFIED — depends on `Lu/Pere` forum membership in live. Note: `Lu/Pere` matches `_PAIR_FORUM_NAME_RE` (accepts `/`), so if Lu is a member → `pair_forum`, role=`partner` | none | none | "Lu" returns 5 preview users named `Luna`/`ModalUI` — all unrelated |
| Tell me about Pere | `["Pere"]` | none | no `Pere` in preview | `unresolved` | UNVERIFIED — same as Lu (pair forum candidate) | none | none | |
| Tell me about Ana | `["Ana"]` | none | no `Ana` in preview | `unresolved` | UNVERIFIED — `Pete/Ana` matches `_PAIR_FORUM_NAME_RE` (accepts `/`), so if Ana is a member → `pair_forum`, role=`partner` | none | none | |
| Tell me about Nic | `["Nic"]` | none | no `Nic` in preview | `unresolved` | UNVERIFIED — `Nic & Pete` matches `_PAIR_FORUM_NAME_RE` (accepts `&`), so if Nic is a member → `pair_forum`, role=`partner` | none | none | |
| What is happening in Pulsifi Leadership? | `["Pulsifi"]` (note: `Leadership` is capitalised in middle of sentence so it IS extracted as a second candidate by `_NAME_TOKEN_RE`. Re-checking: the regex `\b([A-Z][a-z]{1,30})\b` will match both `Pulsifi` and `Leadership`. The resolver takes the **first** unresolved candidate — `Pulsifi`.) | none | none in preview | `unresolved` | UNVERIFIED — **AND** an architecture gap: R3b matches *members*, not *forum names*. Even in live, asking _"what is happening in Pulsifi Leadership?"_ would resolve `Pulsifi` against the *member roster* of Pete's forums, not against forum NAMES. To resolve this query type, a `forum_name` resolution source would need to be added. | none | none | Distinct issue from "missing data" — this is an architectural limit |

**Reasoning traces** (the resolver execution stack for each):

1. `_extract_proper_name_candidates(message)` → V2 token regex (`[A-Z][a-z]{1,30}`), filtered by `_NAME_BLOCKLIST` (planets, signs, wh-words, etc.).
2. `resolve_relationship_context(...)` (V2 router): explicit_target_id → mentioned_name in `saved_people` → pronoun_memory → forum_active_member → missing_target_fallback.
3. If V2 returns no `target`: `resolve_target_via_forums(...)` (R3b) is invoked: list Pete's `forum_members` → hydrate `forums` + per-forum `forum_members` + their `users` → match `candidate_name` against name / email-stem (with alias logic `mel→melissa`, `cand_lc + " "` startswith, etc.) → classify each forum hit via `_classify_forum_source` (pair / family / forum_member) → sort by priority `pair_forum=0 < family_forum=1 < forum_member=2` → top match wins.
4. Spouse-alias fallback: if candidate is empty but the message contains `wife/husband/spouse/partner/...`, find the user's single-other-member pair forum and bind to that member with `role=partner`.
5. Final outcome stamped into `v2_receipt.target_resolution_source` + `v2_receipt.forum_fallback_resolution` (post-fix: persisted to `mirror_chat_retrieval_receipts` only AFTER this enrichment runs).

---

## PART E — Readiness Decision

| Surface | Verdict | Evidence |
|---|---|---|
| P3 relationship orchestration surfacing | **NOT READY** | (1) Cannot validate against production graph. (2) `RELATIONSHIP_ORCHESTRATION_PROMPT=false` remains correctly off per constraints. (3) Orchestration depends on relationship target being resolved with high confidence — that confidence is unverified for production for any name beyond Mel and Yoong family members. |
| Relationship-aware prompt injection | **PARTIAL — READY for code, NOT READY for outcomes** | Phase 4 R2/R3b prompt-injection wiring is **code-correct** (verified end-to-end: target binds → prompt block emitted → LLM sees relationship context → receipt persists telemetry). However, the *quality* of the injected content for production users is unproven. Currently safe to keep enabled (`INTENT_V2_PROMPT_INJECTION=true`) because the resolver gracefully degrades to `unresolved` rather than fabricating, but the *value-add* claim is unverified for the 5 missing forum types. |
| Cofounder resolution | **NOT READY** | Zero validated probes against live cofounder forum (`Pulsifi Leadership`). Even structurally, professional/leadership forums have *no role-inference* in `_classify_forum_source` — they fall through to generic `forum_member` (priority 3, role=`None`). This means even when production data is reached, the cofounder LLM context will be weaker than partner/family context. |
| Family resolution | **PARTIAL — READY in preview, UNVERIFIED in live** | Preview `Yoong family` correctly resolves Isaac and Thaddeus to `family_forum` (priority 2, role=`family`). The same code path will work in live if the live `Yoong Family` is named with a `family`/`fam` token. **Empirically unverified for live.** |
| Forum-member resolution | **NOT READY for live, READY in preview** | `forum_member` source has zero coverage in preview because no non-pair/non-family/non-self forums exist for Pete. Cannot validate live. |
| **Forum-as-target queries** (e.g., "Pulsifi Leadership" as the subject, not a person) | **NOT READY anywhere** | Architectural gap: R3b does not match forum NAMES, only member names. Would require adding a `forum_name`/`forum_alias` resolution source. **Out of scope** per user instructions; flagging only. |

---

## Success Criteria — Direct Answers

### 1. Is the live app using a different database than preview?

**YES.** Evidence:
- `frontend/services/people.ts` lines 39–44 explicitly recognise two host families (`*.emergent.host` for production deploys, `*.emergentagent.com` for preview pods). The current pod serves `*.emergentagent.com` only.
- `server.py` lines 27336 + 33037 reference a previous production URL on `*.emergent.host` and a "fix-deployed-data" admin endpoint that exists precisely because the deployed DB is independent of the dev DB.
- `/app/memory/test_credentials.md` records Mel's `user_id` as `697ec826ad4b18f75bf42616` in dev and `69b50ecb2b86cfb90750ec04` in "deployed". The deployed ObjectId does not exist in this pod's Mongo.
- The forum names the user reports from the live app (`Pulsifi Leadership`, `Lu/Pere`, `Pete/Ana`, `Nic & Pete`, `Mel and I`) are absent from every database on this Mongo instance.
- Receipts collection on this pod has only ever served 2 real users (Pete and Mel) — there has been zero traffic from production co-founders, indicating no traffic mirroring from live to preview.

### 2. Is Pulsifi Leadership missing because of resolver logic or because preview lacks the forum?

**Because preview lacks the forum.** The resolver code:
- has no special-casing that would exclude leadership/cofounder forums,
- iterates `forum_members` for every forum the user belongs to,
- joins to `users` for each member's name and email-stem,
- matches the message-extracted candidate against those names.

If a `Pulsifi Leadership` forum existed in this Mongo and Pete were a member, the resolver would find Jay/Jaan/JH (assuming they're forum members with those names) and resolve via the `forum_member` source (priority 3, role=`None`).

The reason it returns `unresolved` here is simply that `db.forum_members.find({user_id: '697f0c6abf35c0528ff06954'})` returns 4 rows and none reference any forum named `Pulsifi Leadership`.

### 3. Can Jaan, Jay, Lu, Pere, Ana and Nic actually resolve in the live graph?

**UNVERIFIED.** Per Part D, this agent cannot run probes against the live graph from this pod. Structural prediction:

| Name | Predicted live source IF live `forum_members` includes them | Confidence |
|---|---|---|
| Jaan | `forum_member` (`Pulsifi Leadership` — name doesn't match pair/family regex) | high (structural) |
| Jay | `forum_member` (`Pulsifi Leadership`) | high (structural) |
| Lu | `pair_forum` (`Lu/Pere` — `/` matches `_PAIR_FORUM_NAME_RE`) — role would be inferred as `partner` ⚠️ even though Lu/Pere may not be a romantic pair | medium — **possible role mis-inference**, see Architectural Issue #1 below |
| Pere | `pair_forum` (`Lu/Pere`) — same role mis-inference risk | medium |
| Ana | `pair_forum` (`Pete/Ana`) — same | medium |
| Nic | `pair_forum` (`Nic & Pete`) — same | medium |

**Architectural Issue #1 (surfaced, not fixed):** `_classify_forum_source` treats any 2-name pattern (`X & Y`, `X and Y`, `X+Y`, `X/Y`) as a `pair_forum` with inferred role `partner`. In production this will produce a *false partner* role for **co-founder pairs** (`Lu/Pere`, `Pete/Ana`, `Nic & Pete`) which are professional, not romantic. The LLM prompt block reads "Relationship target: '<name>' (resolved via pair_forum in the 'Lu/Pere' forum, relationship_role: partner)" — which is misleading for a cofounder pair. This is a *production-data-shape-meets-current-heuristic* problem invisible in preview.

### 4. Can we trust current relationship-orchestration readiness claims?

**NO, not as production-faithful claims.** They can be trusted as:
- **Code-correctness** claims: resolver ladder, regex precedence, telemetry persistence, prompt-injection wiring — all verified.
- **Preview-fixture** claims: Mel/Isaac/Thaddeus all resolve correctly in the preview fixture.

They **cannot** be trusted as:
- **Production-outcome** claims: any forum type beyond `pair_forum` (binary) and `family_forum` is empirically untested. Specifically the `forum_member` source (which would handle `Pulsifi Leadership`) has *zero* production probes against it.
- **Role-inference fidelity** claims for cofounder pairs (Issue #1 above).
- **Real-traffic** claims: of the user's reported 6 live forums, 5 are absent from preview.

---

## What would unblock a production-faithful validation

(Listed for the user to decide on — no action taken by the agent.)

1. **Read-only Mongo credentials for the production cluster** in this pod's `.env` (e.g., a separate `PROD_MONGO_URL` for forensic-only access), gated to read-only.
2. **The current production deploy URL** so the agent can hit `/api/get-user-forums` against live for Pete and snapshot the actual forum_members topology.
3. **A small seed script run in preview** that fabricates the 5 missing forum names + plausible member rosters (Pulsifi Leadership: Jay, Jaan, JH; Lu/Pere: Lu, Pere; Pete/Ana: Pete, Ana; Nic & Pete: Nic, Pete; Mel and I: Pete, Mel) so the resolver can be empirically validated against production-shaped data, even if the underlying ObjectIds remain dev-side.
4. **OR**: explicit user confirmation to defer P3/P5/cross-lens readiness gating to the next deployment review window, when the user can run an in-production verification harness manually.

---

## Constraint Compliance

| Flag | Required | Actual | Modified? |
|---|---|---|---|
| `INTENT_ROUTER_V2_CUTOVER` | `false` | `false` | No |
| `INTENT_ROUTER_V2_ROLLOUT_PERCENT` | `10` | `10` | No |
| `RELATIONSHIP_ORCHESTRATION_PROMPT` | `false` | `false` | No |
| `CROSS_LENS_PROMPT_SURFACE` | `false` | `false` | No |
| `INTENT_V2_PROMPT_INJECTION` | `true` | `true` | No |
| `TIMELINE_V2_READ_ENABLED` | `true` | `true` | No |
| `FOUNDER_CONTEXT_ENABLED` | `true` | `true` | No |
| forums / users / saved_people data | unchanged | unchanged | No |
| code | unchanged | unchanged | No |

No writes. No migrations. No repairs. Read-only investigation.

🛑 **Stopped after report generation.**
