# PFS-2.6 — Blocker Report

**Sprint:** PFS-2.6 (Production Reality Audit)
**Verdict:** 🔴 **BLOCKED — Production cluster is not reachable from this agent. No production readiness determination is possible from here.**
**Mode:** Documentation only. No code changes. No flag changes. No data writes.

Constraints reaffirmed and verified untouched:

```
INTENT_ROUTER_V2_CUTOVER             = false
INTENT_ROUTER_V2_ROLLOUT_PERCENT     = 10
RELATIONSHIP_ORCHESTRATION_PROMPT    = false
CROSS_LENS_PROMPT_SURFACE            = false
```

---

## A. Why production readiness cannot be determined from Preview

| Fact | Detail |
|------|--------|
| MongoDB URI available to this agent | `mongodb://localhost:27017` |
| Database name                       | `test_database` |
| Cluster identity                    | **Preview** (Kubernetes-pod-local MongoDB) |
| Production MongoDB URI              | **Not present in `/app/backend/.env` or any environment variable** |
| Network reachability                | Local Mongo only; no Atlas / production cluster credential is available |
| `forum_relationship_edges` in scope | 2 edges (both Pete→Mel `spouse`) — see `PFS25_PRODUCTION_GRAPH_INVENTORY.md` |
| Receipts in scope                   | 106 receipts in Preview (synthetic + dev traffic only) |

**Preview is a strict subset of any plausible production graph.** Any
ungating readiness claim derived from Preview would be misleading at
best and harmful at worst, because:

1. Preview has **1 of 20** topology `role_type` values populated.
2. Preview has **0 leadership / advisor / investor forums** — the
   highest-value buckets for Pete's chat experience are entirely
   unexercised here.
3. Preview's `unknown_role_token` denominator is 3 receipts —
   statistically meaningless.
4. Preview has no inverse `spouse` direction — Mel→Pete cannot be
   exercised at all here.

These facts were already documented in `PFS24_PRODUCTION_PARITY_REPORT.md`
and `PFS25_UNGATING_READINESS.md`. PFS-2.6 codifies the resolution path.

---

## B. Unanswered production questions (audit checklist)

Every item below is **unanswered** until production data is provided.
The operator's production run must produce a value for each.

### B.1 — Graph-shape questions

| ID    | Question | Why it matters |
|-------|----------|----------------|
| B1.1  | Distinct `role_type` values in `forum_relationship_edges` (production) | Coverage breadth — ungating needs ≥ 3 of the 6 priority roles |
| B1.2  | Edge count per `role_type` | Statistical mass — ≥ 5 per priority role for meaningful traffic |
| B1.3  | Confidence distribution (`high` / `moderate` / `low`) per role | Quality control — inferred-only edges lower fidelity |
| B1.4  | Inferred vs explicit ratio per role | Same as above |
| B1.5  | Inverse-direction coverage: of edges `A→B`, what fraction has the matching `B→A`? | Schema-semantics question; affects retrieval when the non-primary user chats |
| B1.6  | Duplicate-edge count (same forum + pair + role) | Data quality |
| B1.7  | Contradiction count (same forum + pair, different roles) | Data integrity — must be 0 |
| B1.8  | Forum-member ordered pairs without a topology edge (per forum) | Gap surface — the actual remediation backlog |

### B.2 — Telemetry / observation questions

| ID    | Question | Why it matters |
|-------|----------|----------------|
| B2.1  | `unknown_role_token` event count over last 30 days | Lexicon drift / data gap signal — must be < 5 % of replanned receipts |
| B2.2  | `topology_role_found=true` count over last 30 days | Numerator of topology-aware rate |
| B2.3  | `replanned_after_topology=true` count over last 30 days | Denominator of topology-aware rate |
| B2.4  | `topology_aware_pct` = B2.2 / B2.3 | Must be ≥ 60 % for ungating |
| B2.5  | Distribution of `relationship_orchestration_v1.rule_bucket` across receipts | Sanity — if 99 % land on `self`, ungating yields nothing |

### B.3 — Special-focus role coverage (priority)

| ID    | Question |
|-------|----------|
| B3.1  | spouse  — production edge count, confidence mix, inverse-direction coverage |
| B3.2  | child   — production edge count, confidence mix |
| B3.3  | cofounder — production edge count, confidence mix |
| B3.4  | advisor — production edge count, confidence mix |
| B3.5  | mentor  — production edge count, confidence mix |
| B3.6  | investor — production edge count, confidence mix |
| B3.7  | forum_member — (do explicit edges exist or is this purely an active-member-id surface?) |

### B.4 — Pete-specific reality check

Pete's UID (production): `697f0c6abf35c0528ff06954` (assumed identical to Preview; operator must confirm)

| ID    | Relationship | Required output |
|-------|---------------|-----------------|
| B4.1  | Pete → Mel         | edge present (Y/N), role_type, confidence, inferred, forum_name(s) |
| B4.2  | Pete → Isaac       | edge present (Y/N), role_type, confidence, inferred, forum_name |
| B4.3  | Pete → Thaddeus    | edge present (Y/N), role_type, confidence, inferred, forum_name |
| B4.4  | Pete → Jaan        | edge present (Y/N), role_type, confidence, inferred, forum_name |
| B4.5  | Pete → advisors    | enumerate any `advisor` / `mentor` edges with source=Pete |
| B4.6  | Pete → investors   | enumerate any `investor` edges with source=Pete |
| B4.7  | Pulsifi Leadership | does the forum exist? if yes — enumerate cofounder edges originating from Pete |

---

## C. Final scoring rubric — PASS / FAIL

**Both flags share the same rubric.** Ungating either flag requires
ALL six rows = PASS. Falling any row = HOLD.

| Criterion                        | PASS threshold | FAIL threshold | Notes |
|----------------------------------|----------------|----------------|-------|
| Role coverage                    | ≥ 3 of `{spouse, child, cofounder, advisor, mentor, investor}` present with edges | < 3 | Maps to B1.1 + B3.* |
| Edge counts per priority role    | ≥ 5 edges each | < 5 for any priority role | Maps to B1.2 |
| Inverse-direction coverage       | ≥ 80 % of edges have inverse, OR schema is documented as one-way with consumer parity | < 80 % AND schema is implicitly bidirectional | Maps to B1.5 |
| Contradiction rate               | 0 contradictions | ≥ 1 contradiction | Maps to B1.7 — hard fail; data integrity |
| `unknown_role_token` rate (30d)  | < 5 % of replanned receipts | ≥ 5 % | Maps to B2.1 / B2.3 |
| `topology_aware_pct` (30d)       | ≥ 60 %     | < 60 % | Maps to B2.4 |

**Per-flag specialisation:**

* `RELATIONSHIP_ORCHESTRATION_PROMPT=true` requires the full rubric.
* `CROSS_LENS_PROMPT_SURFACE=true` additionally requires the
  Relationship-Orchestration flag to have completed an observation
  window ≥ 7 days at the current 10 % rollout without alert-level
  regression. Cross-lens is sequenced AFTER orchestration.

---

## D. Decision tree

```
  │ Operator runs the harness in section C of PFS26_PRODUCTION_COMMANDS.md
  │
  ▼
  All 6 rubric rows = PASS ?
      │
      ├── YES ───────────────────────────────────────
      │     │
      │     │  Operator authorises Stage-1 observation window:
      │     │    set RELATIONSHIP_ORCHESTRATION_PROMPT=true
      │     │    keep INTENT_ROUTER_V2_ROLLOUT_PERCENT=10
      │     │    keep INTENT_ROUTER_V2_CUTOVER=false
      │     │    keep CROSS_LENS_PROMPT_SURFACE=false
      │     │
      │     ▼
      │     Run observation window ≥ 7 days.
      │     Re-run PFS25 harness against production at end of window.
      │     If still PASS → authorise CROSS_LENS_PROMPT_SURFACE=true.
      │     If any row drops to FAIL → rollback the flag, return here.
      │
      └── NO ────────────────────────────────────────
            │
            │  Identify missing / contradictory / low-coverage edges
            │  using the per-failing-row output of the harness.
            │
            ▼
            Data team materialises the missing edges (out of agent scope).
            │
            ▼
            Re-run PFS25 harness against production.
            │
            ▼
            (back to the top of this tree)
```

---

## E. Companion files

| File                                     | Purpose |
|------------------------------------------|---------|
| `PFS26_BLOCKER_REPORT.md`                | **this file** — why we're blocked, full unanswered-question checklist, rubric, decision tree |
| `PFS26_OPERATOR_RUNBOOK.md`              | Step-by-step the operator follows |
| `PFS26_PRODUCTION_COMMANDS.md`           | Exact shell commands + ad-hoc Mongo queries |
| `PFS26_EXPECTED_OUTPUT_SCHEMA.json`      | The exact JSON shape the operator's run must produce, so a downstream agent can score it deterministically |

---

## F. Constraints reaffirmed

```
$ grep INTENT_ROUTER_V2 RELATIONSHIP_ORCHESTRATION CROSS_LENS /app/backend/.env
INTENT_ROUTER_V2_CUTOVER=false
INTENT_ROUTER_V2_ROLLOUT_PERCENT=10
RELATIONSHIP_ORCHESTRATION_PROMPT=false
CROSS_LENS_PROMPT_SURFACE=false
```

No flag was flipped during this report. No code was changed. No data
was written. No migration was run.
