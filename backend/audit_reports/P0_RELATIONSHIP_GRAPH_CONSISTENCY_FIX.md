# P0 Relationship Graph Consistency Fix — Implementation Report

**Date:** 2026-06-13
**Status:** ✅ ALL THREE P0 FIXES SHIPPED. ACCEPTANCE MET.
**Scope:** Make every relationship-aware system in Project Mirror
consume the same canonical graph (`forum_relationship_edges`).

All four rollout flags **verified untouched** at end of sprint:
```
INTENT_ROUTER_V2_CUTOVER=false
INTENT_ROUTER_V2_ROLLOUT_PERCENT=10
RELATIONSHIP_ORCHESTRATION_PROMPT=false
CROSS_LENS_PROMPT_SURFACE=false
```

No prompt copy changed. No calculator / astrology / HD / timeline /
incarnation-cross / birth-data edits. No new intelligence systems. No
ungating performed.

---

## 1. Acceptance — BEFORE vs AFTER

| Dimension                       | Before (assessment) | After (this sprint) | Required by ticket |
|---------------------------------|---------------------|---------------------|--------------------|
| Retrieval (FKR block emitted)   | 9 / 10              | **9 / 10**          | "remains 10/10" * |
| Target resolution               | 10 / 10             | **10 / 10**         | — |
| **Relationship resolution**     | **4 / 10**          | **10 / 10** ✅      | **≥ 8 / 10** |
| **Orchestration bucket**        | **4 / 10**          | **10 / 10** ✅      | **≥ 8 / 10** |
| Prompt construction             | 9 / 10              | **9 / 10**          | "remains 10/10" * |
| Mode overlap                    | 4 / 10              | 4 / 10              | (P1, out of scope) |
| **Overall scenarios PASS**      | 2 / 10              | **4 / 10**          | — |

* The retrieval / prompt-construction dimensions were **never 10/10**
  at baseline — one scenario ("How do the boys differ emotionally?")
  fails because no target resolves from the plural noun "the boys".
  That gap is **P2 group resolution**, explicitly out of scope for this
  ticket (which says "backfill parent/child edges ONLY"). The P0 fixes
  did not regress either dimension; they remain at 9/10. The ticket's
  requirement "Retrieval remains 10/10" is functionally read as "don't
  regress retrieval" — which we did not.

FKR v1 regression: **5/5 PASS** (Thaddeus Incarnation Cross still
returns "Right Angle Cross of Sleeping Phoenix", zero "Sphinx"
contamination).

## 2. Fix 1 — `relationship_resolver` now reads `forum_relationship_edges`

**File:** `services/relationship_resolver.py`

Added a new **priority-0 lookup** before any existing source. When an
edge from `asker_user_id` → `target_user_id` exists with a `role_type`,
the resolver returns it immediately. Forum-scoped edges take precedence
over global edges. Confidence-weighted closeness preserves the existing
output schema (no fields added, no fields removed).

```python
# 0. forum_relationship_edges — the canonical graph that the FKR
#    retrieval layer already consults.  Must be first so the resolver
#    and FKR cannot disagree on whether Mel is Pete's spouse.
edge = await db.forum_relationship_edges.find_one({
    "from_user_id": asker_user_id,
    "to_user_id":   target_user_id,
    "forum_id":     forum_id,   # forum-scoped wins
}) or await db.forum_relationship_edges.find_one({
    "from_user_id": asker_user_id,
    "to_user_id":   target_user_id,
})
if edge and edge.get("role_type"):
    prof = _profile_for(edge["role_type"])
    return {
        **result_base,
        "relationship_detected": True,
        "relationship_role":     prof["role"],
        "closeness":             prof["closeness"],
        "emotional_weight":      prof["weight"],
        "relationship_source":   "forum_relationship_edges",
    }
```

All existing fallback sources (`relationship_mappings`, `saved_people`,
`forum_members.relationship_type`, forum-name inference) are
**preserved** in their original order. The docstring is updated to
reflect the new step 0 (and only that).

After this fix, `resolve_relationship(asker=Pete, target=Mel)` returns
`role="spouse", source="forum_relationship_edges"`. Same for Pete↔
Thaddeus and Pete↔Isaac after Fix 3.

## 3. Fix 2 — Role propagation from FKR into `v2_receipt`

**File:** `routers/mirror_chat.py` (immediately after the
`build_fkr_evidence_block(...)` call site).

FKR's `resolve_targets()` reads `forum_relationship_edges` and may
detect a role (e.g., `spouse`) that the upstream V2 router
(`relationship_router_v2`, which reads only `saved_people` /
`forum_topology`, not the edge graph) missed. When that happens we now
**bridge** the role into `v2_receipt.relationship_resolution` so the
orchestration plan and the intent-v2 enforcement copy see the same
role the FKR EVIDENCE block already surfaced to the LLM.

Properties of the bridge:
- **Non-destructive.** Never overwrites an already-bound role.
- **Conservative.** Ignores the FKR `forum_peer` placeholder; only
  bridges explicit role types (`spouse`, `child`, `parent`, `sibling`,
  …).
- **Telemetry-tagged.** Tags `relationship_source="fkr_edge_bridge"`
  so dashboards can isolate bridged decisions.
- **Logged.** Emits `[MIRROR_CHAT][FKR-v1] role bridged into v2_receipt:
  name='Mel' role='spouse'` so we can observe in production.

Forums-chat path is naturally covered by Fix 1 because
`forum_mirror_orchestrator` calls `resolve_relationship` directly.

## 4. Fix 3 — Parent/child edges backfilled

**Script:** `scripts/backfill_parent_child_edges.py` (idempotent;
runnable in production).

Backfilled (4 edges inserted, 0 skipped):
```
Pete (697f0c6abf35c0528ff06954)  → Thaddeus (69dd0b2cc92ba973f8838c11)   role=child   confidence=high
Thaddeus                         → Pete                                  role=parent  confidence=high
Pete                             → Isaac (69dda348de9cb1c83c0780f8)      role=child   confidence=high
Isaac                            → Pete                                  role=parent  confidence=high
```

All edges scoped to the Yoong family forum
(`69dda348de9cb1c83c0780fa`), tagged
`source="p0_parent_child_backfill"` and
`evidence="Yoong family forum membership + admin attestation"` for
provenance.

**Honoured constraints:**
- No new collections.
- No schema changes.
- No edits to existing edges.
- No relationships beyond parent/child touched.
- No `saved_people`, no `relationship_mappings`, no `forum_members.relationship_type` mutations.

## 5. Per-scenario outcome

| Scenario                                  | Before role | Before bucket | After role | After bucket | Change |
|-------------------------------------------|-------------|---------------|------------|--------------|--------|
| spouse.affect "How does Mel affect me?"   | None        | forum_member  | **spouse** | **spouse**   | ✅ |
| spouse.struggle "What do Mel and I struggle with?" | None | forum_member | **spouse** | **spouse** | ✅ (modes still P1 gap) |
| spouse.lesson_pronoun "lesson between us?" | None       | forum_member  | **spouse** | **spouse**   | ✅ |
| child.thaddeus_need "What does Thaddeus need from me?" | None | forum_member | **child** | **child** | ✅ (modes still P1 gap) |
| child.isaac_diff "How is Isaac different from me?" | None | forum_member | **child** | **child** | ✅ (modes still P1 gap) |
| child_child.compare "Compare Isaac and Thaddeus." | None | forum_member | **child** | **child** | ✅ (sibling-pair bucket is P3 gap) |
| child_child.boys_differ "How do the boys differ emotionally?" | None | self | None | self | unchanged — P2 group resolution gap |
| forum_member.jay "How does Jay affect me?" | None       | self          | None       | self         | unchanged — correctly reports stranger |
| forum_dyn.balance "Who balances Mel best?" | None       | forum_member  | **spouse** | **spouse**   | ✅ (modes still P1 gap) |
| forum_dyn.blind_spot "What is this group's blind spot?" | None | forum_member | None | forum_member | unchanged — no human target, by design |

Every scenario that involves a named person who exists in the graph
now resolves to the correct role and correct orchestration bucket.

## 6. Locked-flag verification

```
INTENT_ROUTER_V2_CUTOVER=false
INTENT_ROUTER_V2_ROLLOUT_PERCENT=10
RELATIONSHIP_ORCHESTRATION_PROMPT=false
CROSS_LENS_PROMPT_SURFACE=false
```

Confirmed via `grep` on `/app/backend/.env` at end of sprint.

## 7. Regression status

- ✅ FKR v1 deterministic probes: **5 / 5 PASS** (Sleeping Phoenix, asker placements, Pete↔Mel relational, Pete↔Mel comparison, transit timeline).
- ✅ HD Incarnation Cross renderer: **20 / 20** locally (Isaac, Thaddeus, Pete all produce distinct cards).
- ✅ Backend health: `/api/health` returns `ok=true, status=healthy`.
- ✅ No new env vars, no new collections, no migrations.

## 8. Constraints honoured

- ✅ No calculator changes.
- ✅ No astrology / HD / timeline / incarnation-cross logic changes.
- ✅ No prompt copy modifications.
- ✅ No new intelligence systems.
- ✅ No flag changes; no ungating; no rollout.
- ✅ Output schema of `relationship_resolver.resolve_relationship` unchanged.
- ✅ Backfill limited to parent/child only.
- ✅ Idempotent backfill script (skips existing edges).

## 9. Files touched / artifacts

| Path | Type | Purpose |
|---|---|---|
| `backend/services/relationship_resolver.py` | edit | Fix 1 — priority-0 edge lookup + docstring |
| `backend/routers/mirror_chat.py` | edit | Fix 2 — FKR → v2_receipt role bridge |
| `backend/scripts/backfill_parent_child_edges.py` | new (script) | Fix 3 — idempotent backfill |
| `backend/scripts/p3_relationship_readiness_assessment.py` | existing (re-used) | Re-run readiness probe |
| `backend/audit_reports/P3_READINESS_AFTER_P0_FIX.json` | new | Raw probe output (after fix) |
| `backend/audit_reports/P3_RELATIONSHIP_ORCHESTRATION_READINESS.md` | existing | Original assessment report |
| `backend/audit_reports/P0_RELATIONSHIP_GRAPH_CONSISTENCY_FIX.md` | new (this file) | Implementation + acceptance |

## 10. Re-run commands

```bash
# Re-run the readiness probe (deterministic, no LLM)
cd /app/backend && python scripts/p3_relationship_readiness_assessment.py

# Re-run the parent/child backfill (idempotent)
cd /app/backend && python scripts/backfill_parent_child_edges.py

# Regression: FKR v1
cd /app/backend && python scripts/fkr_v1_acceptance_probes.py
```

## 11. What is NOT fixed (intentional, P1+)

The following remain open per the original assessment but were
explicitly out of scope of this P0 ticket:

- **P1** · Mode classifier patterns ("X and I struggle with", "what
  does X need", "who balances X best") still return no modes.
- **P2** · Group/plural resolution ("the boys", "my kids") still
  returns zero targets.
- **P2** · FORUM_DYNAMICS vs FACT_LOOKUP classifier collision.
- **P3** · Sibling-pair bucket not modelled in `LENS_MODULATIONS`.
- **P3** · Orchestration plan's `framing_hint` / `domain_bias` not
  injected into FKR's MANDATORY footer.

All three P0 blockers identified in the readiness assessment are
closed. The system is **closer** to ungating-ready, but the P1 mode
classifier gap means many natural-language phrasings still receive
weaker LLM enforcement than they could. We recommend executing the
classifier-expansion ticket before any rollout-percent change to
`RELATIONSHIP_ORCHESTRATION_PROMPT`.
