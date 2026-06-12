# PRODUCTION FIDELITY SPRINT — PFS-1
**Forensic Audit Before Any Further P3 / P5 / Cross-Lens Rollout Decisions**

| | |
|---|---|
| Date | 2026-06-12 |
| Mode | READ-ONLY FORENSIC INVESTIGATION |
| Pod | `agent-env-1499bb60-8500-40b9-98e9-5acb13e092c7` |
| Job ID | `09b66994-39d9-4402-b1f0-fab69561f671` |
| Prior audits referenced | `R3B_FORENSIC_REPORT.md`, `PRODUCTION_TOPOLOGY_AUDIT.md` |

**Compliance**: No code changes, no data changes, no migrations, no flag changes, no backfills, no membership changes. Constraint flags re-verified at the foot of this report.

---

## Executive Summary

1. There are **two distinct environment families** in play. The preview pod (this one) and the deployed production pod are **separate**, each backed by a separate Mongo instance. Every audit so far has executed against **Preview only**.

2. Preview's forum collection does **not** contain the production forum names visible in the live UI. The resolver appears to fail for production-style queries, but the failure mode is **data absence**, not code defect.

3. **Concrete regex evidence (this audit) discovered TWO production-fidelity defects** that prior audits missed because preview had no production-shaped forum names:
   - **Defect 1 (HIGH severity)**: `"Mel and I"` — the most natural user-coined pair-forum name — is **NOT** recognised as a `pair_forum` by `_PAIR_FORUM_NAME_RE` because the trailing token `I` fails the regex `[A-Z][a-z\-']{1,30}` (requires ≥ 1 lowercase tail). It silently falls through to `forum_member` with `role=None`.
   - **Defect 2 (HIGH severity)**: Business / co-founder pairs that *do* match the pair regex (`Lu/Pere`, `Pete/Ana`, `Nic & Pete`) are inferred as `role=partner` and injected into the LLM prompt as "relationship_role: partner" — a romantic-relationship mis-classification of professional relationships.

4. **Production-faithful validation cannot be performed by this agent from this pod.** No production Mongo credentials, no production deploy URL, no read-replica access.

5. **Readiness verdict (Task E)**: **Code Correct + Production Not Validated, AND Requires Remediation** (because two concrete heuristic defects are now demonstrated to misclassify production-realistic forum names).

---

## TASK A — Environment Topology Mapping

### A.1 Environments that currently exist

| Environment | Evidence |
|---|---|
| **Preview pod** (this container) | Hostname `agent-env-1499bb60-8500-40b9-98e9-5acb13e092c7`; container env `preview_endpoint=https://birth-data-remediate.preview.emergentagent.com`; emergent.yml `job_id=09b66994-39d9-4402-b1f0-fab69561f671`; image `expo_mongo_base_image_cloud_arm:release-21012026-1` |
| **Local Mongo** (in same pod as preview backend) | `/app/backend/.env` → `MONGO_URL="mongodb://localhost:27017"`, `DB_NAME="test_database"`; 7 application DBs visible (`emergent_db`, `mirror_app`, `mirror_db`, `mirrordb`, `project_mirror`, `projectmirror`, `test_database`) — only `test_database` carries a `forums` collection |
| **Deployed production host(s)** | Exists per `frontend/services/people.ts:39-44` which discriminates two host families: `*.emergent.host` (production deploys) vs `*.emergentagent.com` (preview pods). Historical production URL `mirror-lens-fixes.emergent.host` referenced twice in `server.py` (L27336, L33037) — that specific slug is dead (`HTTP 400 "Deployment not found"`) but the host family is real. |
| **Deployed production Mongo** | Existence inferred from (a) the host-family pattern above, (b) the in-repo `/api/fix-deployed-data` admin endpoint whose docstring states it seeds "missing data" on the *deployed DB*, and (c) `/app/memory/test_credentials.md` which records different `user_id`s for Mel between "dev" and "deployed". Specific hostname/database name **unknown** to this agent. |

### A.2 Which environment each audit has actually used

| Audit | Environment used | Proof |
|---|---|---|
| `R3B_FORENSIC_REPORT.md` (this session) | Preview | All `db.*` queries went to `mongodb://localhost:27017/test_database`; all live `POST /api/mirror/chat` probes hit `localhost:8001` which is the preview pod backend |
| `PRODUCTION_TOPOLOGY_AUDIT.md` (this session) | Preview | Same as above |
| Earlier "post-publish verification against the deployed host" calls | Preview (mis-labelled as production) | Tagged probe `?probe=DEPLOYED-1781249137` sent to `https://birth-data-remediate.preview.emergentagent.com` was received by `localhost:8001` access log. The "deployed host" used in those audits is the *same* container as `localhost:8001`. |

### A.3 Environment table

| Environment | Host | Mongo | DB | Accessible from this pod? |
|---|---|---|---|---|
| Preview backend | `https://birth-data-remediate.preview.emergentagent.com` ↔ `http://localhost:8001` | `mongodb://localhost:27017` | `test_database` | **YES** (direct) |
| Preview frontend (Expo web) | Same host as preview backend | n/a (browser) | n/a | YES |
| Production backend | `<slug>.emergent.host` (slug **unknown** — `mirror-lens-fixes.emergent.host` is dead) | **Unknown** Mongo cluster (presumed Atlas or managed) | **Unknown** DB | **NO** |
| Production frontend | Same `<slug>.emergent.host` (single-origin) | n/a | n/a | NO |

### A.4 Where each entity exists

| Entity | Preview | Production | Evidence |
|---|---|---|---|
| Pete | `_id=697f0c6abf35c0528ff06954`, `email=pete@pulsifi.me` | UNKNOWN ObjectId; likely same email | direct lookup + `test_credentials.md` |
| Mel | `_id=697ec826ad4b18f75bf42616`, `email=melissa.mars@gmail.com` | `_id=69b50ecb2b86cfb90750ec04` per `test_credentials.md`. That id **does not exist** in preview's Mongo (verified by `db.users.find_one({_id: ObjectId('69b50ecb2b86cfb90750ec04')})` → `None`). | `/app/memory/test_credentials.md` |
| `Pulsifi Leadership` | **NOT FOUND** in any of the 7 application DBs on this Mongo node | Reported by user; cannot verify | `db.forums.find({name: /pulsifi\|leadership/i})` → 0 hits |
| `Yoong family` / `Yoong Family` | **FOUND** (`forum_id=69dda348de9cb1c83c0780fa`, 4 members: Pete, Mel, Isaac Yoong, Thaddeus Yoong) | Reported by user as present | direct lookup |
| `Mel and I` | **NOT FOUND** (preview has `Pete & Mel` instead — same dyad, different name) | Reported by user as present | direct lookup |
| `Lu/Pere`, `Pete/Ana`, `Nic & Pete` | **NOT FOUND** | Reported by user as present | direct lookup |

Direct receipt evidence that production traffic does not mirror to preview: the preview pod's `mirror_chat_retrieval_receipts` collection contains only 11 distinct `user_id`s, of which 2 are real (Pete + Mel preview ObjectIds) and 9 are synthetic probe ids (`000000000000000000000001..8`, `smoke-test`). **Zero co-founder/Pulsifi-leadership traffic has ever reached this pod.**

A live signal observed during this audit: starting at `2026-06-12T07:25:29Z`, requests appeared in the preview pod's backend log `[Forums] POST getting forums for user: 69b50ecb...` — i.e., the live app *currently* sends the deployed-Mel ObjectId to the preview URL. The API correctly returned `{"forums":[]}` because that `user_id` doesn't exist in preview's Mongo. This is direct evidence that **someone is testing the deployed UI's network calls against the preview backend** — useful as a connectivity confirmation, useless as production data.

---

## TASK B — Production Forum Inventory

**Production access is unavailable from this pod.** The table below reports only what can be proven from preview.

| Forum | Exists (preview)? | Exists (production)? | Members (preview) | Roles (preview) | Forum-type guess from name (analytic only, no data) |
|---|---|---|---|---|---|
| `Mel and I` | ❌ NOT in preview | UNVERIFIABLE (user-reported present) | n/a | n/a | Romantic pair (canonical "<name> and I" pattern). **Caveat — see Task C Defect 1: this name does *not* match the current pair regex.** |
| `Yoong Family` | ✅ exists as `Yoong family` (case-mismatch only) | UNVERIFIABLE (user-reported present) | 4 (Pete admin, Mel member, Isaac Yoong member, Thaddeus Yoong member) | admin / member | Family forum (correctly classifies as `family_forum`) |
| `Pulsifi Leadership` | ❌ NOT in preview | UNVERIFIABLE (user-reported present, 3 members) | n/a | n/a | Professional / leadership team. Will classify as generic `forum_member`, no role inferred. |
| `Lu/Pere` | ❌ NOT in preview | UNVERIFIABLE (user-reported present) | n/a | n/a | Likely co-founder pair. **Defect 2 risk** — current regex classifies as `pair_forum`, role=`partner`. |
| `Pete/Ana` | ❌ NOT in preview | UNVERIFIABLE (user-reported present) | n/a | n/a | Likely co-founder pair. **Defect 2 risk.** |
| `Nic & Pete` | ❌ NOT in preview | UNVERIFIABLE (user-reported present) | n/a | n/a | Likely co-founder pair. **Defect 2 risk.** |

**No inferences about production members, roles, or counts are made. Only the analytic forum-type guess from the literal forum name string is reported, because the name string is the only signal we have.**

---

## TASK C — Relationship Classification Audit

### C.1 Are `pair_forum / family_forum / forum_member` sufficient?

**NO.** Concrete evidence below.

The current classifier is `services/mirror_chat_phase4_enrichment.py::_classify_forum_source`:

```python
_PAIR_FORUM_NAME_RE = re.compile(
    r"^\s*([A-Z][a-z\-']{1,30})\s*(?:&|and|\+|/)\s*([A-Z][a-z\-']{1,30})\s*$",
    re.I,
)
_FAMILY_FORUM_NAME_RE = re.compile(r"\bfamily\b|\bfam\b", re.I)

def _classify_forum_source(forum_name):
    if _PAIR_FORUM_NAME_RE.match(forum_name):
        return "pair_forum", "partner"
    if _FAMILY_FORUM_NAME_RE.search(forum_name):
        return "family_forum", "family"
    return "forum_member", None
```

### C.2 Direct classification trace against the user's production forum names

Run against the **live, unmodified** `_classify_forum_source` (this audit, today):

| forum_name | `pair_re` matches | `family_re` matches | Classified source | Inferred role | Defect? |
|---|---|---|---|---|---|
| `Mel and I` | **False** | False | **`forum_member`** | **None** | ⚠️ **Defect 1 — HIGH** |
| `Mel & I` | **False** | False | `forum_member` | None | ⚠️ Same root cause as Defect 1 |
| `Yoong Family` | False | True | `family_forum` | family | ✅ correct |
| `Yoong family` | False | True | `family_forum` | family | ✅ correct |
| `Pulsifi Leadership` | False | False | `forum_member` | None | ✅ correct (graceful degradation; no false-role inference) |
| `Lu/Pere` | True | False | **`pair_forum`** | **partner** | ⚠️ **Defect 2 — HIGH** if Lu/Pere are cofounders |
| `Pete/Ana` | True | False | **`pair_forum`** | **partner** | ⚠️ **Defect 2 — HIGH** if Pete/Ana are cofounders |
| `Nic & Pete` | True | False | **`pair_forum`** | **partner** | ⚠️ **Defect 2 — HIGH** if Nic/Pete are cofounders |
| `Pete & Mel` (preview canonical) | True | False | `pair_forum` | partner | ✅ correct (Pete + Mel are spouses) |
| `Me and Mel` (canonical alt) | True | False | `pair_forum` | partner | ✅ correct |
| `Pete and Mel` | True | False | `pair_forum` | partner | ✅ correct |
| `The Pulsifi Team` | False | False | `forum_member` | None | ✅ correct |
| `Pulsifi Cofounders` | False | False | `forum_member` | None | ✅ correct |

### C.3 Defect 1 — `"Mel and I"` does NOT classify as a pair_forum (HIGH severity)

**Root cause**: the second capture group `([A-Z][a-z\-']{1,30})` requires *at least one* lowercase / hyphen / apostrophe character after the leading uppercase. The token `I` is a bare uppercase letter with no tail → regex fails → classification falls through to `forum_member` with `role=None`.

**Concrete consequence in the prompt block** (the actual string the LLM would receive in production once the forum exists):

- Current (defective) prompt block, for "Tell me about Mel" inside the `Mel and I` forum:
  > `Relationship target: 'Mel' (resolved via forum_member in the 'Mel and I' forum). This person is in the user's saved relationship topology — ground your reflection in the actual relationship between them, not in generic projection language.`

  No `relationship_role` is surfaced. The LLM does not know the relationship is romantic/spousal.

- Expected (correct) prompt block:
  > `Relationship target: 'Mel' (resolved via pair_forum in the 'Mel and I' forum (relationship_role: partner)). …`

**Severity**: HIGH — this is the canonical name pattern a user is most likely to coin for a romantic pair forum. Every "<their-name> and I" forum in production currently degrades to `forum_member` and loses the partner role inference. The LLM-facing context is materially weaker.

### C.4 Defect 2 — Cofounder / business pairs misclassified as `partner` (HIGH severity)

**Root cause**: `_PAIR_FORUM_NAME_RE` is purely syntactic — it triggers on *any* `Capitalised & Capitalised` / `Capitalised and Capitalised` / `Capitalised/Capitalised` / `Capitalised+Capitalised` shape. It cannot distinguish a marital pair from a business/co-founder pair from a sibling pair.

**Concrete consequence**:

- For a forum named `Lu/Pere` whose semantic meaning is "Lu and Pere are co-founders" (very common pattern), the prompt block becomes:
  > `Relationship target: 'Pere' (resolved via pair_forum in the 'Lu/Pere' forum (relationship_role: partner)). This person is in the user's saved relationship topology — ground your reflection in the actual relationship between them, not in generic projection language.`

  The LLM is now grounded on a **partner / romantic-pair** frame for what is actually a **co-founder / business** relationship. Downstream, the relationship lens, intimacy heuristics, and (when ungated in the future) the P3 orchestration's framing_hint will all skew toward intimacy/attachment language.

**Worked example — Lu/Pere co-founder probe** (preview-structural, since live data isn't reachable):
- Query: "Tell me about Pere"
- V2 extracts: `["Pere"]`
- saved_people match: assumed none in production
- R3b scan: `forum_members.find(user_id=Pete)` returns `Lu/Pere` forum; `_classify_forum_source("Lu/Pere") → pair_forum, partner`
- Receipt persistence: `target_resolution_source=pair_forum`, `relationship_role=partner`
- Prompt injection: includes "relationship_role: partner"
- LLM response: anchored on partner/intimacy lens

**Severity**: HIGH — this is a *category error* (intimate vs professional), not a confidence error. The downstream LLM has no way to recover; it is being told the relationship type categorically.

**Note on Pulsifi Leadership**: `Pulsifi Leadership` correctly classifies as `forum_member` with `role=None` (because the regex requires the `Capitalised(separator)Capitalised` shape). The degraded behaviour here is acceptable — no false role is asserted. The defect is *only* in the subset of cofounder pairs that *also* happen to match the pair regex (`X/Y`, `X & Y`, `X and Y`, `X+Y`).

### C.5 Risk severity summary

| Defect | Severity | Production trigger | LLM-facing impact |
|---|---|---|---|
| 1 — `"Mel and I"` → forum_member, no role | HIGH | Any forum whose name ends in "and I" / "& I" — canonical user pattern | Loses partner-role context for spousal/romantic forums |
| 2 — Cofounder pairs → partner | HIGH | Any pair-shaped forum that's actually professional (`Lu/Pere`, `Pete/Ana`, `Nic & Pete`) | Asserts romantic/partner frame on professional relationship |
| 3 — Sibling / parent-child non-family-named forums | MEDIUM (not concretely triggered in user data but architecturally adjacent) | Any non-`family`-named forum containing only siblings or parent–child | Falls to `forum_member` instead of `family_forum` |
| 4 — Forum-as-target queries (Pulsifi Leadership *as topic*) | MEDIUM | Queries asking *about the forum*, not about a member | R3b has no `forum_name` resolution source — currently unresolvable |

Defects 1 and 2 are within scope of the current pair/family/forum_member taxonomy; defects 3 and 4 indicate the *taxonomy itself* may need expansion (`professional_pair`, `cofounder_forum`, `sibling_forum`, `forum_as_topic`).

---

## TASK D — Production-Faithful Probe Matrix

| Probe | Preview Valid? | Production Valid? | Why |
|---|---|---|---|
| Tell me about Mel | **YES** — resolves to `pair_forum` (`Pete & Mel`), role=`partner`, target_id=`697ec826ad4b18f75bf42616` | **PARTIAL** — if production stores the same dyad as `"Mel and I"`, Defect 1 means the resolver returns `forum_member`/`role=None`, which is structurally weaker but **not wrong**. The role attribute is lost. |
| Tell me about Isaac | **YES** — resolves to `family_forum` (`Yoong family`), role=`family`, target_id=`69dda348de9cb1c83c0780f8` | **UNVERIFIABLE** — depends on the production `Yoong Family` forum's actual member roster. If Isaac is a member there, classification should still be correct (family regex still matches `Yoong Family`). |
| Tell me about Jaan | **No** — Jaan exists as a preview user (`69894cc932380843ba87d121`) but has no shared-forum edge to Pete → `unresolved` | **UNVERIFIABLE** — depends on whether Jaan is a forum_member of `Pulsifi Leadership` in production. If yes: would correctly classify as `forum_member`, `role=None`. |
| Tell me about Jay | **No** — "Jay" does not exist as a user in preview at all → `unresolved` | **UNVERIFIABLE** — same dependency on production `Pulsifi Leadership` roster. |
| Tell me about Lu | **No** — no `Lu/Pere` forum exists in preview → `unresolved` | **UNVERIFIABLE — and at risk** — if/when production data is reached, Defect 2 will misclassify as `partner`. |
| Tell me about Pere | **No** — same | **UNVERIFIABLE — at risk** — Defect 2 |
| Tell me about Ana | **No** — no `Pete/Ana` forum in preview → `unresolved` | **UNVERIFIABLE — at risk** — Defect 2 |
| Tell me about Nic | **No** — no `Nic & Pete` forum in preview → `unresolved` | **UNVERIFIABLE — at risk** — Defect 2 |
| What is happening in Pulsifi Leadership? | **No** — both data missing and architectural gap (R3b doesn't match forum names) | **UNVERIFIABLE** — even with production data, Defect 4 means the query type itself is unresolvable until a forum-name resolution source is added. |

### D.1 What "preview valid" means

A probe is "preview valid" if the resolver returns the *intended* binding given preview's actual data. A probe is **not** preview-validatable for production if (a) the relevant forum doesn't exist in preview, OR (b) the relevant person isn't a forum_member of Pete in preview.

Only 2 of 9 probes are preview-valid as end-to-end outcome validations. The remaining 7 cannot be validated end-to-end here — they can only be validated as *code paths*.

### D.2 What would unblock production-valid probes

(Listed for the user's decision — no action taken.)

- Read-only access to the production Mongo cluster (e.g., a `PROD_MONGO_URL` added to this pod's `.env`).
- The current production deploy URL (a `*.emergent.host` slug) plus credentials/auth for an internal forensic endpoint that emits the resolver receipt for a probe message.
- A preview-side fabricated seed (clearly marked as test fixture) of forums named `Pulsifi Leadership`, `Mel and I`, `Lu/Pere`, `Pete/Ana`, `Nic & Pete` with fake member rosters, so the resolver outcomes can be empirically observed against production-shaped forum names — explicitly approved by the user before seeding.

---

## TASK E — Readiness Verdict

# Verdict: **(3) Code Correct + Production Not Validated** — **AND** **(4) Requires Remediation**

### Evidence supporting "Code Correct"

- R3b ladder ordering (`pair_forum=0 > family_forum=1 > forum_member=2`) functions correctly under preview data — verified in `R3B_FORENSIC_REPORT.md` with concrete probe traces and verified live persistence of `target_resolution_source` and `forum_fallback_resolution` into `mirror_chat_retrieval_receipts`.
- Spouse-alias path (`wife / husband / spouse / partner`) deterministically resolves to the single non-self member of a pair forum — verified in preview.
- Telemetry persistence is now correct (the fire-and-forget persist call was moved to *after* the Phase 4 enrichment block).
- Constraint flags are unchanged.

### Evidence supporting "Production Not Validated"

- The preview pod is a separate environment from the production deploy (proven in Task A).
- Every probe matrix entry that depends on production data is `UNVERIFIABLE` from this pod (Task D).
- The preview `mirror_chat_retrieval_receipts` collection has zero traffic from production users (Task A.4).

### Evidence supporting "Requires Remediation"

Two **concrete, reproducible, today** classification defects in `_classify_forum_source` whose impact is realised the moment production data is wired in:

- **Defect 1**: `"Mel and I"` is currently classified as `forum_member` (no role). Production user-coined romantic pair forums silently lose the partner role.
- **Defect 2**: Cofounder / business pairs whose names match the pair regex (`Lu/Pere`, `Pete/Ana`, `Nic & Pete`) are asserted as `relationship_role=partner` to the LLM.

Both defects are *visible in the current preview code under live test*, even without production data. They are not speculative — they are demonstrated above with direct function calls against the unmodified production code path.

### Why this matters for P3 / P5 / cross-lens decisions

P3 relationship-aware orchestration uses `relationship_resolution.role` as one of its primary ordering signals. Cross-lens contradiction surfacing reads the same field. If `role=partner` is asserted for a cofounder pair, every downstream component (orchestration, cross-lens, contradiction synthesis, Timeline V2 soft modulation) inherits the mis-classification.

**Ungating any of these surfaces before remediation will amplify, not contain, Defect 2.**

---

## Suggested Remediation Sketch (for user review only — no action taken)

These are *suggestions for the user to authorise separately*. **Not implemented.**

1. **Defect 1 fix** (regex tightening):
   - Extend `_PAIR_FORUM_NAME_RE` to accept the bare token `I` as a second-group alternation, e.g. `([A-Z][a-z\-']{1,30}|I)`.
   - Add a unit-test fixture covering `Mel and I`, `Pete and I`, `Mel & I`, `Pete & I`.

2. **Defect 2 fix** (taxonomy expansion):
   - Introduce a new resolution source `professional_pair` (or `cofounder_forum`) with `role=cofounder` (or `business_partner`).
   - Either:
     - **Heuristic**: keyword detection on forum names containing `co-founder/cofounder/founders/leadership/team/biz/business/work` *before* the pair regex matches → reclassify as `professional_pair`.
     - **Or structural**: surface the forum's `category` field (if present) or `created_with_intent` metadata to drive classification rather than relying purely on the name.
     - **Or user-driven**: ask the forum creator a one-question "What kind of forum is this?" at creation time; persist `forum.kind ∈ {pair, family, professional, friend, other}`.

3. **Defect 4 (forum-as-topic) — out of scope but worth surfacing**:
   - Add a new resolution source `forum_name` that scans the message for substring matches against the user's forum names. This would unblock queries like "What is happening in Pulsifi Leadership?".

4. **Production-fidelity validation gate**: before any further P3/P5 ungating decisions, run the PFS probe matrix against the live production Mongo (read-only) and append the results to this report as Part F.

---

## Appendix — Constraint Compliance (re-verified at report-generation time)

| Flag | Required | Actual | Modified during PFS-1? |
|---|---|---|---|
| `INTENT_ROUTER_V2_CUTOVER` | `false` | `false` | No |
| `INTENT_ROUTER_V2_ROLLOUT_PERCENT` | `10` | `10` | No |
| `RELATIONSHIP_ORCHESTRATION_PROMPT` | `false` | `false` | No |
| `CROSS_LENS_PROMPT_SURFACE` | `false` | `false` | No |
| `INTENT_V2_PROMPT_INJECTION` | `true` | `true` | No |
| `TIMELINE_V2_READ_ENABLED` | `true` | `true` | No |
| `FOUNDER_CONTEXT_ENABLED` | `true` | `true` | No |
| Production data | unchanged | unchanged | No (no access) |
| Preview data | unchanged | unchanged | No |
| Code | unchanged | unchanged | No |
| Migrations | none | none | No |
| User backfills | none | none | No |
| Forum membership | unchanged | unchanged | No |

🛑 **Stopped after report generation.** Awaiting user review before any remediation, ungating, or further audit work.
