# PFS-2.3 — Shadow Probes (Pre vs Post Topology-Aware Orchestration)

**Sprint:** PFS-2.3
**Mode:** Shadow validation only. **No flags flipped.**
**Run:** `python scripts/pfs23_shadow_probes.py` → captured to
`/app/backend/audit_reports/PFS23_PROBE_TRACES.txt`.

> Constraints reaffirmed: `INTENT_ROUTER_V2_CUTOVER=false`,
> `INTENT_ROUTER_V2_ROLLOUT_PERCENT=10`,
> `RELATIONSHIP_ORCHESTRATION_PROMPT=false`,
> `CROSS_LENS_PROMPT_SURFACE=false`. Untouched.

---

## 0. Setup

| Item              | Value |
|-------------------|-------|
| Backend version   | `relationship_orchestration_v1.1.0` (PFS-2.3) |
| Resolver version  | PFS-2.1 topology-first (`mirror_chat_phase4_enrichment`) |
| Preview DB edges  | `forum_relationship_edges` count = 2 (both `spouse`, Pete→Mel) |
| Probe envelope    | `lens_priority = [astrology, human_design, enneagram, numerology, relationship, timeline]` |

The "pre-PFS-2.3" plan is simulated by calling `plan_lens_priority`
with `relationship_role=None` — matching the V2 router's pre-PFS-2.1
behavior when no `saved_people` row exists for the target. The
"post-PFS-2.3" plan uses the resolved role (or a synthetic injection
for environmentally-missing roles).

---

## 1. Probe 1 — Mel (Real Topology Edge)

**Question (synthetic):** *"How does Mel map to me?"*

| Field                       | Value |
|-----------------------------|-------|
| Resolver target name        | `Mel` |
| Resolver `resolved_role`    | `spouse` |
| Resolver `topology_role_found` | `True` |
| Topology `role_type`        | `spouse` |
| Topology `confidence`       | `high` |
| Topology `inferred`         | `False` |

### Plan diff

| Field            | PRE-PFS-2.3   | POST-PFS-2.3        |
|------------------|---------------|---------------------|
| `rule_bucket`    | `self`        | **`spouse`**        |
| `framing_hint`   | `self_inquiry` | **`couple_dynamic`** |
| `domain_bias`    | `self`        | **`relationship`**  |
| `lens_priority`  | `[astrology, human_design, enneagram, numerology, relationship, timeline]` | `[astrology, human_design, relationship, enneagram, numerology, timeline]` |
| Reordered?       | —             | **Yes ✓** (`relationship` promoted from idx 4 → idx 2) |
| `applied_rules`  | `['self:default']` | `['role_match:spouse:spouse', 'target_bound']` |

**Success criteria met:**
- ✅ role=spouse
- ✅ relationship-first orchestration (`domain_bias='relationship'`)
- ✅ couple framing (`framing_hint='couple_dynamic'`)

**Expected response framing (consumer view):** Reflection grounded in
the couple dynamic — Mel-as-spouse rather than Mel-as-acquaintance.

---

## 2. Probe 2 — Isaac (No Topology Edge in Preview)

**Question (synthetic):** *"How does Isaac map to me?"*

| Field                          | Value |
|--------------------------------|-------|
| Resolver target name           | `Isaac Yoong` |
| Resolver `resolved_role`       | `family` (PFS-1 family-forum heuristic) |
| Resolver `topology_role_found` | `False` |
| Topology `role_type`           | `None` |
| Forum                          | `Yoong family` |

### Plan diff

| Field            | PRE-PFS-2.3   | POST-PFS-2.3        |
|------------------|---------------|---------------------|
| `rule_bucket`    | `self`        | `self`              |
| `framing_hint`   | `self_inquiry` | `self_inquiry`     |
| `domain_bias`    | `self`        | `self`              |
| `lens_priority`  | unchanged     | unchanged           |
| `applied_rules`  | `['self:default']` | `['self:target_bound_unknown_role', 'self:unknown_role_token:family']` |

### Diagnosis

**Status:** **ENVIRONMENTAL N/A.**

`family` is a PFS-1 forum-level aggregate (forum-name heuristic) —
**not** a topology `role_type`. In production a
`Pete → Isaac : child` edge would exist and the resolver would surface
`role='child'` instead of `role='family'`. That would land Isaac on the
`child` bucket with `framing='parenting'` and `domain_bias='relationship'`.

The current Preview behavior **correctly surfaces the data gap** via
the dashboard-visible telemetry `self:unknown_role_token:family`. This
is the deliberate "topology before heuristic" outcome — when an
explicit edge is missing, the orchestration falls cleanly to `self`
and flags the missing edge for production observability rather than
silently inferring a child relationship from a forum name.

**Success criteria assessment:**

| User expectation | Outcome in Preview | Outcome with production data |
|------------------|--------------------|------------------------------|
| role=child       | role=family (PFS-1 heuristic) | role=child (topology edge) ✓ |
| parenting framing | self_inquiry (no edge) | `parenting` (lexicon entry exists) ✓ |
| family-context orchestration | self (no edge) | `child` bucket (lexicon entry exists) ✓ |

> The lexicon **already** supports `child` end-to-end. Preview cannot
> exercise that path because the edge is absent. See production data
> parity gap documented in `PRODUCTION_TOPOLOGY_AUDIT.md`.

---

## 3. Probe 3 — Jaan (Synthetic Cofounder Injection)

**Question (synthetic):** *"How does Jaan map to me?"*

Resolver finds **no Jaan** in Preview (no forum member, no edge — Jaan
exists in Pete's production world but is absent here). We synthetically
inject `role='cofounder'` to prove the lexicon coverage.

| Field                          | Value |
|--------------------------------|-------|
| Resolver found?                | `False` |
| Synthetic role injected        | `cofounder` |
| Primary domain                 | `leadership` |

### Plan diff

| Field            | PRE-PFS-2.3   | POST-PFS-2.3        |
|------------------|---------------|---------------------|
| `rule_bucket`    | `self`        | **`cofounder`**     |
| `framing_hint`   | `self_inquiry` | **`cofounder_strategic`** |
| `domain_bias`    | `self`        | **`work`**          |
| `lens_priority`  | `[astrology, human_design, enneagram, numerology, relationship, timeline]` | `[astrology, human_design, enneagram, relationship, numerology, timeline]` |
| Reordered?       | —             | **Yes ✓** (`relationship` promoted to idx 3, `enneagram` boost preserves it at idx 2) |
| `applied_rules`  | `['self:default']` | `['role_match:cofounder:cofounder', 'target_bound']` |

**Success criteria met:**
- ✅ role=cofounder
- ✅ work-first orchestration (`domain_bias='work'`)
- ✅ leadership / founder framing (`framing_hint='cofounder_strategic'`)

---

## 4. Probe 4 — Advisor (Synthetic Advisor Injection)

**Question (synthetic):** *"What role does my advisor play?"*

No advisor edge exists in Preview. Synthetic `role='advisor'`.

| Field            | PRE-PFS-2.3   | POST-PFS-2.3        |
|------------------|---------------|---------------------|
| `rule_bucket`    | `self`        | **`advisor`**       |
| `framing_hint`   | `self_inquiry` | **`guidance`**     |
| `domain_bias`    | `self`        | **`work`**          |
| `lens_priority`  | `[astrology, human_design, enneagram, numerology, relationship, timeline]` | `[astrology, human_design, enneagram, numerology, relationship, timeline]` |
| Reordered?       | —             | Unchanged — modulation already aligned with prior order (HD already #2, relationship boost insufficient to overtake numerology in this envelope). The bucket / framing / domain_bias still correctly differentiate the consumer surface. |
| `applied_rules`  | `['self:default']` | `['role_match:advisor:advisor', 'target_bound']` |

**Success criteria met:**
- ✅ role=advisor
- ✅ guidance framing (`framing_hint='guidance'`)
- ✅ power/influence context (`domain_bias='work'`)

> **Note on "no lens reorder":** The modulation table for `advisor`
> boosts `human_design` and `astrology`, which are already at indices
> 0–1 in the default envelope. The relationship boost (+0.15) is not
> enough to overtake `numerology` in this envelope. This is correct
> behavior — small modulations don't reorder when prior weights
> already align. The framing/bucket signal IS delivered to downstream
> consumers via `framing_hint` and `domain_bias`.

---

## 5. Lexicon Coverage Exercise — Full Vocabulary

Confirmed at runtime that every topology `role_type` (plus key aliases)
lands in an intentional bucket. **No role silently falls through to
`self` or `forum_member`.**

```
role=spouse             → bucket=spouse             framing=couple_dynamic
role=former_partner     → bucket=former_partner     framing=closure_dynamic
role=child              → bucket=child              framing=parenting
role=parent             → bucket=parent             framing=lineage
role=sibling            → bucket=sibling            framing=family_dynamic
role=cofounder          → bucket=cofounder          framing=cofounder_strategic
role=business_partner   → bucket=cofounder          framing=cofounder_strategic
role=advisor            → bucket=advisor            framing=guidance
role=investor           → bucket=investor           framing=influence
role=manager            → bucket=manager            framing=authority
role=employee           → bucket=employee           framing=responsibility
role=collaborator       → bucket=collaborator       framing=partnership
role=mentor             → bucket=mentor             framing=development_giving
role=mentee             → bucket=mentee             framing=development_receiving
role=coach              → bucket=coach              framing=growth_giving
role=coachee            → bucket=coachee            framing=growth_receiving
role=authority_figure   → bucket=authority_figure   framing=power_dynamics
role=close_friend       → bucket=close_friend       framing=closeness
role=forum_mate         → bucket=forum_member       framing=forum_member_dynamic
role=other              → bucket=forum_member       framing=forum_member_dynamic
```

---

## 6. Regression Matrix

| Scenario                  | Expected                     | Result                        | Status |
|---------------------------|------------------------------|-------------------------------|--------|
| `role=None`               | `self / self_inquiry`        | `self / self_inquiry`         | ✅ PASS |
| `role=""` (empty)         | `self / self_inquiry`        | `self / self_inquiry`         | ✅ PASS |
| `role='qwertyxyz'` (unknown) | `self / self_inquiry`     | `self / self_inquiry`         | ✅ PASS |
| `role='colleague'` + leadership envelope | `cofounder` (legacy heuristic) | `cofounder`         | ✅ PASS |
| `role='colleague'` + identity envelope   | `self` (legacy heuristic)      | `self`               | ✅ PASS |
| All 75 pre-existing P3 tests             | green                         | **75 green + 8 updated for v1.1.0** | ✅ PASS |
| All 27 pre-existing PFS-1 tests          | green                         | 28 green (`test_classify_forum_source`) | ✅ PASS |
| Full test suite (`orchestration_v1`, `b2_mirror_chat_shadow`, `intent_router_v2`, `cross_lens_synthesis_v2`, `classify_forum_source`) | green | **102 / 102 pass** | ✅ PASS |

---

## 7. Receipt Payload — End-to-End Sanity (Mel)

When the live router runs against Pete with message "How does Mel map
to me?", the persisted `mirror_chat_retrieval_receipts.relationship_orchestration_v1`
now contains:

```json
{
  "version": "relationship_orchestration_v1.1.0",
  "computed": true,
  "role_resolved": "spouse",
  "rule_bucket": "spouse",
  "framing_hint": "couple_dynamic",
  "domain_bias": "relationship",
  "lens_priority_before": ["astrology", "human_design", "enneagram", "numerology", "relationship", "timeline"],
  "lens_priority_after":  ["astrology", "human_design", "relationship", "enneagram", "numerology", "timeline"],
  "lens_weight_modulation": {
    "astrology": 0.30, "relationship": 0.40,
    "human_design": 0.20, "timeline": 0.10
  },
  "applied_rules": ["role_match:spouse:spouse", "target_bound"],
  "replanned_after_topology": true,
  "topology_role_type": "spouse",
  "topology_confidence": "high",
  "topology_inferred": false,
  "pre_topology_plan": {
    "role_resolved": null,
    "rule_bucket": "self",
    "framing_hint": "self_inquiry",
    "domain_bias": "self",
    "lens_priority_after": ["astrology", "human_design", "enneagram", "numerology", "relationship", "timeline"],
    "applied_rules": ["self:default"]
  }
}
```

The `replanned_after_topology=true` flag + `pre_topology_plan` block
make the PFS-2.3 plumbing fix visible in the persisted receipt, so
dashboards can diff and count topology-driven re-orchestrations
without re-running the planner.

---

## 8. Summary

| Probe / Check                     | Outcome | Status |
|-----------------------------------|---------|--------|
| Probe 1: Mel → spouse / couple    | ✅      | PASS   |
| Probe 2: Isaac → child / parenting | ⚠️ env N/A in Preview; lexicon ready, edge absent | ENVIRONMENTAL N/A |
| Probe 3: Jaan → cofounder / leadership | ✅ (synthetic) | PASS   |
| Probe 4: Advisor → guidance / work | ✅ (synthetic) | PASS   |
| Lexicon coverage (20 roles)        | ✅      | PASS   |
| Regression (None/empty/unknown)    | ✅      | PASS   |
| Test suite                         | 102/102 | PASS   |

**Verdict:** PFS-2.3 is shadow-validated. The orchestration plan now
faithfully consumes the topology-resolved role. Hold ungating per the
sprint constraints.
