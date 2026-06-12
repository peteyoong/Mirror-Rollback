# PFS-2.4 — Trace Samples (post-PFS-2.3 receipts in Preview)

**Source:** `mirror_chat_retrieval_receipts` filtered to
`relationship_orchestration_v1.version = "relationship_orchestration_v1.1.0"`.
**Count:** 8 receipts (synthetic chat traffic generated against the
live Preview backend on 2026-06-12 08:36 UTC).

> See `PFS24_PRODUCTION_PARITY_REPORT.md` for the environmental caveat:
> production receipts are not visible from this agent. The traces below
> are Preview-only, used to prove end-to-end PFS-2.3 correctness.

---

## Trace 1 — Mel (spouse) — PASS

```
request_id              : mc-aa21891e-0d44-41e6-ae4f-b201902cb8eb
target_person           : Mel
resolved_role           : spouse
resolved_bucket         : spouse
domain_bias             : relationship
framing_hint            : couple_dynamic
replanned_after_topology: true
topology_role_found     : true
topology_role_type      : spouse
topology_confidence     : high
topology_inferred       : false
resolution_source       : pair_forum
forum_name              : Pete & Mel
applied_rules           : ["role_match:spouse:spouse", "target_bound"]
lens_priority_after     : [relationship, astrology, human_design, enneagram, timeline, numerology]
pre_topology_plan       : {bucket:self, framing:self_inquiry, domain_bias:self,
                            applied_rules:[self:default]}
```

**Verdict:** ✅ correct role + bucket + framing + domain_bias.
Lens stack already had `relationship` at index 0 from the V2 router,
so reorder unnecessary. Pre-vs-post plan diff is visible and correct.

---

## Trace 2 — Mel (spouse) — PASS (second turn)

```
request_id              : mc-da14e329-7097-419c-a816-6a35c2790169
target_person           : Mel
resolved_role           : spouse
resolved_bucket         : spouse
domain_bias             : relationship
framing_hint            : couple_dynamic
replanned_after_topology: true
topology_role_found     : true
topology_role_type      : spouse
topology_confidence     : high
topology_inferred       : false
resolution_source       : pair_forum
forum_name              : Pete & Mel
applied_rules           : ["role_match:spouse:spouse", "target_bound"]
pre_topology_plan       : {bucket:self, framing:self_inquiry, domain_bias:self}
```

**Verdict:** ✅ reproduces Trace 1 — deterministic. Same chat user,
different message ("My wife and I had a hard conversation last night"),
same topology-resolved spouse outcome.

---

## Trace 3 — Isaac Yoong (no topology edge) — ENVIRONMENTAL N/A

```
request_id              : mc-146f8c07-b075-40f3-a5aa-8d822d319600
target_person           : Isaac Yoong
resolved_role           : family   (PFS-1 family-forum heuristic)
resolved_bucket         : self     (← `family` is not a topology role_type)
domain_bias             : self
framing_hint            : self_inquiry
replanned_after_topology: true     (← re-plan ran and confirmed self)
topology_role_found     : false
topology_role_type      : null
topology_confidence     : null
resolution_source       : family_forum
forum_name              : Yoong family
applied_rules           : ["self:target_bound_unknown_role",
                           "self:unknown_role_token:family"]
```

**Verdict:** ⚠ Expected behaviour. In production a
`Pete → Isaac : child` edge would surface `role=child` and land on the
`child` bucket with `framing=parenting`, `domain_bias=relationship`.
In Preview the edge is absent — the resolver correctly falls back to
the PFS-1 heuristic, the planner correctly refuses to invent a
non-vocab role, and the dashboard-visible telemetry
`self:unknown_role_token:family` flags the data gap.

**This is the most important diagnostic the audit produced:** it is
the exact signal that production-data observers should be alert to.

---

## Trace 4 — no resolved target (`self:default`) — expected

```
request_id              : mc-329645de-9567-4aae-b897-2c687fdd82fc
                          (also #1, #2, #5, #8 — 5 receipts total in this class)
target_person           : null
resolved_role           : null
resolved_bucket         : self
domain_bias             : self
framing_hint            : self_inquiry
replanned_after_topology: null   (resolver returned no target; re-plan didn't fire)
topology_role_found     : null
applied_rules           : ["self:default"]
```

**Verdict:** ✅ Correct. Messages that didn't mention a person
(e.g. "How am I doing today?") legitimately produce `self`. The
`replanned_after_topology` field stays `null` because the PFS-2.1
resolver returned no target — no re-plan needed.

---

## Trace 5 — "my cofounder Lu" — UNRESOLVED in Preview

The probe message `"I need to talk to my cofounder about runway"`
produced a `relationship_orchestration_v1` receipt with `bucket=self`
and `target=None`, because:

* No cofounder forum exists in Preview.
* No `forum_relationship_edges.role_type='cofounder'` edge exists.
* The V2 router's `saved_people` lookup for Pete contains no cofounder rows.

**Verdict:** Environmental N/A. PFS-2.3 lexicon supports `cofounder` →
`cofounder` bucket end-to-end (proven in `PFS23_SHADOW_PROBES.md`
Probe 3 with synthetic injection); the gap is *production data*
— the cofounder forum and edge do not exist in Preview.

Same status applies to the `"my advisor"` probe.

---

## Summary Table

| Trace # | target_person | resolved_role | resolved_bucket | domain_bias    | topology_role_found | replanned | Status |
|---------|---------------|---------------|-----------------|----------------|---------------------|-----------|--------|
| 1 (Mel) | Mel           | spouse        | spouse          | relationship   | true                | true      | ✅ PASS |
| 2 (Mel) | Mel           | spouse        | spouse          | relationship   | true                | true      | ✅ PASS |
| 3 (Isaac) | Isaac Yoong | family (heur) | self            | self           | false               | true      | ⚠ ENV N/A — needs `child` edge in prod |
| 4–8 (no target) | (null)| null          | self            | self           | null                | null      | ✅ Expected |

## Final note

**Zero `cofounder` / `advisor` / `mentor` / `investor` / `close_friend` /
`child`-via-edge traces observed.** This is the only outcome possible
in Preview given the topology graph state. Production observation is
required to validate those buckets in real traffic.
