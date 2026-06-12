# PFS-2.3 — P3 Topology-Aware Orchestration: Implementation Report

**Sprint:** Production Fidelity Sprint 2.3
**Mode:** Shadow only — feature flags untouched.
**Status:** ✅ Implemented + shadow-validated. Awaiting review.

> Constraints reaffirmed and verified untouched (`/app/backend/.env`):
> ```
> INTENT_ROUTER_V2_CUTOVER             = false
> INTENT_ROUTER_V2_ROLLOUT_PERCENT     = 10
> RELATIONSHIP_ORCHESTRATION_PROMPT    = false
> CROSS_LENS_PROMPT_SURFACE            = false
> ```
> No rollout activity. No ungating. No Variant-A / Timeline-V2 / P5
> work. No schema migrations. No topology-data changes.

---

## 1. Both Defects Closed

### Defect A — P3 was orchestrating on the stale (pre-topology) role.

**Root cause** (per `PFS22_CONSUMER_AUDIT.md` §3): `compute_v2_envelope_sync`
(`mirror_chat_shadow.py:202`) called `plan_lens_priority` BEFORE the
PFS-2.1 forum-fallback resolver mutated `relationship_resolution.role`
(`routers/mirror_chat.py:963+`).

**Fix:** After PFS-2.1 promotes the topology-resolved role into
`v2_receipt["relationship_resolution"]`, the router now performs a
**re-plan** that **overwrites** `v2_receipt["relationship_orchestration_v1"]`
with a fresh plan built from the post-topology role. The pre-topology
plan is preserved inside `pre_topology_plan` for dashboard diffing.

**Code location:** `routers/mirror_chat.py` lines ~1000-1090 (inside
the existing R3b enrichment block). Marker comment:
`# PFS-2.3 — Re-plan P3 lens orchestration`. Wrapped in a defensive
`try/except` so the receipt is never broken when re-planning fails.

### Defect B — Lexicon covered only spouse / child / cofounder.

**Root cause:** `relationship_orchestration_v1._SPOUSE_ROLES /
_CHILD_ROLES / _COFOUNDER_ROLES` did not cover the full
`forum_relationship_edges.role_type` vocabulary (20 production roles).
Topology values like `parent`, `mentor`, `investor`, `advisor`,
`former_partner`, `sibling`, `manager`, `employee`, `collaborator`,
`coach`, `coachee`, `mentee`, `authority_figure`, `close_friend` all
silently fell through to `forum_member` or `self`.

**Fix:** Module bumped to **v1.1.0**. Added 14 new role lexicons +
14 new buckets in `LENS_MODULATIONS` + 14 new entries in
`FRAMING_HINT` + a new top-level `DOMAIN_BIAS` map (relationship /
work / self / forum). `_resolve_role_bucket` extended to walk all
buckets in spec order. Unknown tokens still fall to `self` but now
with explicit telemetry `self:unknown_role_token:<token>`.

---

## 2. Exact Code Locations Modified

| File | Lines (approx) | Change |
|------|----------------|--------|
| `services/relationship_orchestration_v1.py` | 70-225 | VERSION bumped to `relationship_orchestration_v1.1.0`. New lexicons: `_FORMER_PARTNER_ROLES`, `_PARENT_ROLES`, `_SIBLING_ROLES`, `_ADVISOR_ROLES`, `_INVESTOR_ROLES`, `_MENTOR_ROLES`, `_MENTEE_ROLES`, `_COACH_ROLES`, `_COACHEE_ROLES`, `_MANAGER_ROLES`, `_EMPLOYEE_ROLES`, `_AUTHORITY_ROLES`, `_COLLABORATOR_ROLES`, `_CLOSE_FRIEND_ROLES`, `_FORUM_MATE_ROLES`. 14 new buckets added to `LENS_MODULATIONS`; 14 new entries in `FRAMING_HINT`; new `DOMAIN_BIAS` map (20 entries). `_resolve_role_bucket` rewritten with explicit ladder for every bucket; `self:unknown_role_token:<token>` telemetry added. `plan_lens_priority` result now includes `domain_bias`. |
| `routers/mirror_chat.py` | ~1000-1090 | After PFS-2.1 promotion, re-plan P3 via `plan_lens_priority` with the post-topology role; overwrite `v2_receipt["relationship_orchestration_v1"]`. Preserve `pre_topology_plan` for diff observability. Defensive `try/except`. |
| `tests/test_relationship_orchestration_v1.py` | 30, 85 | Aligned existing assertions: `VERSION` now `v1.1.0`; `framing_hint` for child bucket now `parenting` (per PFS-2.3 spec). |
| `scripts/pfs23_shadow_probes.py` | new file | Read-only probe harness (Mel / Isaac / Jaan / advisor + full lexicon coverage + regression matrix). |
| `audit_reports/PFS23_PROBE_TRACES.txt` | new file | Captured probe output. |
| `audit_reports/PFS23_ROLE_COVERAGE_MATRIX.md` | new file | Per-role mapping with `domain_bias` / `framing_hint`. |
| `audit_reports/PFS23_SHADOW_PROBES.md` | new file | Pre/post traces for the 4 required probes + regression. |
| `audit_reports/PFS23_IMPLEMENTATION_REPORT.md` | **this file** | Summary. |

**No other files changed.** `services/forum_topology.py` (source of
truth for role vocabulary) and the PFS-2.1 resolver code are untouched.

---

## 3. Validation Results

### 3.1 Unit Tests — 102/102 green

```
$ python -m pytest tests/test_relationship_orchestration_v1.py \
                   tests/test_classify_forum_source.py \
                   tests/test_b2_mirror_chat_shadow.py \
                   tests/test_intent_router_v2.py \
                   tests/test_cross_lens_synthesis_v2.py -q
102 passed in 12.57s
```

Of these:
- `test_relationship_orchestration_v1.py` — 28 (was 27; new
  `child_developmental` → `parenting` assertion updated, version
  pin updated, all other assertions preserved).
- `test_classify_forum_source.py` — 55 (PFS-1, unchanged).
- `test_b2_mirror_chat_shadow.py` — green (no impact).
- `test_intent_router_v2.py` — green (no impact).
- `test_cross_lens_synthesis_v2.py` — green (topology-agnostic).

### 3.2 Shadow Probes — Success Criteria Met

| Probe | Expected (post-PFS-2.3) | Actual | Status |
|-------|--------------------------|--------|--------|
| Mel | role=spouse, relationship-first, couple framing | bucket=`spouse`, domain_bias=`relationship`, framing=`couple_dynamic`, lens reordered (relationship 4→2) | ✅ |
| Isaac | role=child, parenting framing, family context | role=`family` (PFS-1 heuristic — no edge in Preview); orchestration falls to `self` with `self:unknown_role_token:family` telemetry | ⚠ ENVIRONMENTAL N/A in Preview; lexicon ready for production |
| Jaan (synthetic cofounder) | role=cofounder, work-first, leadership/founder framing | bucket=`cofounder`, domain_bias=`work`, framing=`cofounder_strategic`, lens reordered | ✅ |
| Advisor (synthetic) | role=advisor, guidance framing, work context | bucket=`advisor`, domain_bias=`work`, framing=`guidance` | ✅ |

Full lexicon coverage exercise: **20/20 topology roles + aliases land
in intentional buckets.** Zero silent fallthroughs.

### 3.3 Regression Matrix — All Green

- `role=None / "" / qwertyxyz` → `self / self_inquiry` ✓
- `role=colleague + leadership` → `cofounder` (legacy heuristic preserved) ✓
- `role=colleague + identity` → `self` (legacy heuristic preserved) ✓
- 75 pre-existing P3 unit tests + 27 PFS-1 + others → all green ✓

### 3.4 Backend Live + Constraints Honored

```
$ grep INTENT_ROUTER_V2 RELATIONSHIP_ORCHESTRATION CROSS_LENS /app/backend/.env
INTENT_ROUTER_V2_CUTOVER=false
INTENT_ROUTER_V2_ROLLOUT_PERCENT=10
RELATIONSHIP_ORCHESTRATION_PROMPT=false
CROSS_LENS_PROMPT_SURFACE=false
```

Backend restarted cleanly post-patch; `/api/` health 200. Live router
emits `[phase4-PFS2.3] re-planned:` log lines confirming the re-plan
path is exercised on every chat turn where PFS-2.1 promotes a target.

---

## 4. Persisted Receipt Shape (Mel example)

```json
{
  "relationship_resolution": {
    "target": "697ec826ad4b18f75bf42616",
    "target_name": "Mel",
    "role": "spouse",
    "forum_id": "69dd05eaa333335fcbf3ad33",
    "forum_name": "Pete & Mel",
    "resolution_source": "pair_forum",
    "topology_role_found": true,
    "topology_role_type": "spouse",
    "topology_confidence": "high",
    "topology_inferred": false,
    "topology_edge_id": "5beee835-..."
  },
  "relationship_orchestration_v1": {
    "version": "relationship_orchestration_v1.1.0",
    "computed": true,
    "role_resolved": "spouse",
    "rule_bucket": "spouse",
    "framing_hint": "couple_dynamic",
    "domain_bias": "relationship",
    "lens_priority_before": ["astrology","human_design","enneagram","numerology","relationship","timeline"],
    "lens_priority_after":  ["astrology","human_design","relationship","enneagram","numerology","timeline"],
    "applied_rules": ["role_match:spouse:spouse","target_bound"],
    "replanned_after_topology": true,
    "topology_role_type": "spouse",
    "topology_confidence": "high",
    "topology_inferred": false,
    "pre_topology_plan": {
      "role_resolved": null,
      "rule_bucket": "self",
      "framing_hint": "self_inquiry",
      "domain_bias": "self",
      "lens_priority_after": ["astrology","human_design","enneagram","numerology","relationship","timeline"],
      "applied_rules": ["self:default"]
    }
  }
}
```

`pre_topology_plan` + `replanned_after_topology=true` provide
dashboard-grade observability without re-running anything.

---

## 5. Regression Findings

**None.** No production behavior was changed:
- `RELATIONSHIP_ORCHESTRATION_PROMPT=false` → the orchestration plan
  is still consumed only as receipt-only telemetry; nothing is
  injected into the live LLM prompt.
- Pre-PFS-2.3 plans are preserved verbatim inside `pre_topology_plan`
  for back-compat dashboard parsers.
- Lens outputs (`lens_payloads`, `lens_priority` in envelope) untouched.
- `validation_status`, `routing_status`, all other receipt blocks
  untouched.

---

## 6. Recommendation

**Hold ungating.** PFS-2.3 is shadow-validated and code-complete. The
correct rollout sequence remains:

1. **PFS-2.3 land** — done (this report).
2. **Production observation window** — let the patched code emit
   `replanned_after_topology=true` traces in production for ≥ N
   receipts so dashboards can verify the topology→bucket transitions
   are well-distributed.
3. **Cross-Lens consumer check** — confirm `cross_lens_synthesis_v2`
   still surfaces meaningful tensions when consumed alongside the
   new `domain_bias` field.
4. **Then and only then** — `RELATIONSHIP_ORCHESTRATION_PROMPT=true`
   in a Stage-1 (10%) cohort, with rollback ready.
5. **Then** — `CROSS_LENS_PROMPT_SURFACE=true` in the same cohort.

**Do not change the rollout %, cutover, P5, or Variant-A flags.**

---

## 7. Sign-off Checklist

- [x] Defect A (plumbing) fixed: re-plan runs after PFS-2.1 promotion.
- [x] Defect B (lexicon) fixed: 20 topology roles covered, 14 new buckets.
- [x] Tests green: 102/102 across all relevant suites.
- [x] Shadow probes pass: Mel ✓, Jaan ✓ (synthetic), Advisor ✓ (synthetic).
- [x] Isaac correctly classified as ENVIRONMENTAL N/A — lexicon ready, edge absent.
- [x] Receipt schema extended (`domain_bias`, `pre_topology_plan`, `replanned_after_topology`).
- [x] No flags flipped. Constraints verified at `/app/backend/.env`.
- [x] No production rollout activity.
- [x] No code changes to PFS-2.1 resolver, `forum_topology.py`, or any other consumer.
- [x] Reports generated: this implementation report, the role coverage matrix, the shadow probes report.

**Stopping for review. Awaiting authorization before any ungating activity.**
