# PFS-2.3 — Role Coverage Matrix

**Sprint:** PFS-2.3 (P3 topology-aware orchestration — shadow only)
**Source-of-truth role vocabulary:** `services/forum_topology.py`
**Implementation source:** `services/relationship_orchestration_v1.py` (v1.1.0)
**Run-time verified:** `scripts/pfs23_shadow_probes.py` — see
`audit_reports/PFS23_PROBE_TRACES.txt`.

> Constraints reaffirmed: `INTENT_ROUTER_V2_CUTOVER=false`,
> `INTENT_ROUTER_V2_ROLLOUT_PERCENT=10`,
> `RELATIONSHIP_ORCHESTRATION_PROMPT=false`,
> `CROSS_LENS_PROMPT_SURFACE=false`. **Untouched.**

---

## 1. Discovery — Preview vs. Topology Vocabulary

**Preview DB distinct `role_type` values (live query):** `['spouse']`
(2 edges, both Pete → Mel).

**Topology source-of-truth vocabulary (`forum_topology.py`):**

| Family       | Roles |
|--------------|-------|
| FAMILY_ROLES        | `parent`, `child`, `sibling`, `spouse`, `former_partner` |
| PROFESSIONAL_ROLES  | `cofounder`, `manager`, `employee`, `investor`, `advisor`, `mentor`, `mentee`, `coach`, `coachee`, `business_partner` |
| SOCIAL_ROLES        | `close_friend`, `forum_mate`, `authority_figure`, `collaborator`, `other` |

**Total:** 20 distinct production role types. PFS-2.3 covers all 20 +
common free-text variants and aliases (e.g. `wife`/`husband` map to
`spouse`, `co-founder`/`business_partner` map to `cofounder` bucket).

---

## 2. Full Role → Bucket Mapping

> **No role silently falls through to `forum_member` or `self`.**
> Every topology role lands in an INTENTIONAL bucket. Unknown tokens
> still cleanly fall to `self` with `self:unknown_role_token:<token>`
> telemetry so production drift is visible to observers.

### Verified at runtime (probe output)

```
role=spouse             → bucket=spouse             framing=couple_dynamic         domain_bias=relationship
role=former_partner     → bucket=former_partner     framing=closure_dynamic        domain_bias=relationship
role=child              → bucket=child              framing=parenting              domain_bias=relationship
role=parent             → bucket=parent             framing=lineage                domain_bias=relationship
role=sibling            → bucket=sibling            framing=family_dynamic         domain_bias=relationship
role=cofounder          → bucket=cofounder          framing=cofounder_strategic    domain_bias=work
role=business_partner   → bucket=cofounder          framing=cofounder_strategic    domain_bias=work
role=advisor            → bucket=advisor            framing=guidance               domain_bias=work
role=investor           → bucket=investor           framing=influence              domain_bias=work
role=manager            → bucket=manager            framing=authority              domain_bias=work
role=employee           → bucket=employee           framing=responsibility         domain_bias=work
role=collaborator       → bucket=collaborator       framing=partnership            domain_bias=work
role=mentor             → bucket=mentor             framing=development_giving     domain_bias=work_self
role=mentee             → bucket=mentee             framing=development_receiving  domain_bias=self
role=coach              → bucket=coach              framing=growth_giving          domain_bias=self_work
role=coachee            → bucket=coachee            framing=growth_receiving       domain_bias=self
role=authority_figure   → bucket=authority_figure   framing=power_dynamics         domain_bias=self_work
role=close_friend       → bucket=close_friend       framing=closeness              domain_bias=relationship
role=forum_mate         → bucket=forum_member       framing=forum_member_dynamic   domain_bias=forum
role=other              → bucket=forum_member       framing=forum_member_dynamic   domain_bias=forum
```

### Aligned with sprint spec

| role_type        | orchestration domain | strategy            | fallback     | Status |
|------------------|----------------------|---------------------|--------------|--------|
| spouse           | relationship         | couple_dynamic      | relationship | ✓      |
| child            | relationship         | parenting           | relationship | ✓      |
| parent           | relationship         | lineage             | relationship | ✓      |
| sibling          | relationship         | family_dynamic      | relationship | ✓      |
| cofounder        | work                 | cofounder_strategic | work         | ✓      |
| business_partner | work                 | cofounder_strategic | work         | ✓ (aliased to cofounder bucket per topology semantics) |
| advisor          | work                 | guidance            | work         | ✓      |
| mentor           | work_self            | development_giving  | self         | ✓ (gives development) |
| investor         | work                 | influence           | work         | ✓      |
| collaborator     | work                 | partnership         | work         | ✓      |
| manager          | work                 | authority           | work         | ✓      |
| employee         | work                 | responsibility      | work         | ✓      |
| coach            | self_work            | growth_giving       | self         | ✓      |
| coachee          | self                 | growth_receiving    | self         | ✓      |
| former_partner   | relationship         | closure_dynamic     | relationship | ✓      |
| authority_figure | self_work            | power_dynamics      | self         | ✓      |
| mentee           | self                 | development_receiving | self       | ✓ (added per topology coverage) |
| close_friend     | relationship         | closeness           | relationship | ✓ (added per topology coverage) |
| forum_mate       | forum                | forum_member_dynamic | forum-member | ✓ |
| other            | forum                | forum_member_dynamic | forum-member | ✓ |

---

## 3. Lens Modulation Reference (v1.1.0)

| Bucket            | astrology | human_design | enneagram | relationship | timeline |
|-------------------|-----------|--------------|-----------|--------------|----------|
| spouse            | +0.30     | +0.20        | —         | +0.40        | +0.10    |
| former_partner    | +0.20     | +0.20        | +0.15     | +0.40        | +0.10    |
| child             | +0.20     | +0.30        | +0.15     | +0.10        | +0.20    |
| parent            | +0.25     | +0.20        | +0.20     | +0.20        | +0.15    |
| sibling           | +0.20     | +0.20        | +0.15     | +0.30        | +0.05    |
| cofounder         | +0.15     | +0.30        | +0.25     | +0.20        | +0.10    |
| advisor           | +0.20     | +0.30        | +0.20     | +0.15        | +0.10    |
| investor          | +0.20     | +0.30        | +0.15     | +0.15        | +0.10    |
| manager           | +0.15     | +0.25        | +0.25     | +0.20        | +0.10    |
| employee          | +0.15     | +0.25        | +0.25     | +0.20        | +0.10    |
| mentor            | +0.15     | +0.30        | +0.30     | +0.10        | +0.10    |
| mentee            | +0.15     | +0.25        | +0.30     | +0.10        | +0.20    |
| coach             | +0.15     | +0.30        | +0.30     | +0.10        | +0.15    |
| coachee           | +0.15     | +0.25        | +0.30     | +0.10        | +0.20    |
| authority_figure  | +0.20     | +0.20        | +0.30     | +0.20        | +0.10    |
| collaborator      | +0.20     | +0.20        | +0.15     | +0.25        | +0.10    |
| close_friend      | +0.20     | +0.20        | +0.15     | +0.35        | +0.10    |
| forum_member      | +0.20     | +0.20        | +0.10     | +0.40        | —        |
| self              | —         | —            | —         | —            | —        |

All modulations are intentionally moderate (≤ 0.40). They re-rank the
lens stack derived from the intent envelope's `lens_priority` but never
zero out a lens, so existing recall is intact (per
`relationship_orchestration_v1` design contract).

---

## 4. Coverage Audit Outcome

| Check                                                            | Result |
|------------------------------------------------------------------|--------|
| Every topology `role_type` lands in an intentional bucket        | **PASS** |
| No topology role silently lands on `self`                        | **PASS** |
| No topology role silently lands on `forum_member` fallback       | **PASS** (only explicit `forum_mate`/`other`/`forum_member` tokens) |
| Back-compat: legacy `colleague` + leadership → `cofounder`       | **PASS** (test suite green) |
| Unknown tokens still cleanly land on `self` with telemetry       | **PASS** (`self:unknown_role_token:<token>`) |
| Free-text aliases (wife/husband/co-founder) map to canonical     | **PASS** |
| Family-context aggregate "family" (PFS-1 heuristic, not a topology role_type) | Intentional `self` with `self:unknown_role_token:family` telemetry — see §5 |

---

## 5. Known Behavior — PFS-1 "family" Aggregate

`_classify_forum_source` (PFS-1) emits `role="family"` when the
candidate matched a member of a forum whose name carries the family
keyword (`Yoong family`, etc.) **and** no explicit
`forum_relationship_edges` edge exists for the pair. This is a
forum-level signal, **not** a topology role_type — neither `parent`,
`child`, nor `sibling`.

PFS-2.3 deliberately leaves `family` outside the lexicon: in production
the resolver should consume an explicit edge like
`Pete → Isaac : child` and land on the `child` bucket. When the explicit
edge is missing, the orchestration plan falls cleanly to `self` with
the dashboard-visible telemetry `self:unknown_role_token:family`, which
flags the data gap for production observability.

> This is the deliberate "topology before heuristic" outcome
> — Preview demonstrates it correctly because Pete → Isaac has no
> explicit edge in Preview.
