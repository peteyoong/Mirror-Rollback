# P4 — Forum-Topology Plumbing

_Issued under operator priority change (pre-Stage-1 rollout). All work
performed **with** `INTENT_ROUTER_V2_CUTOVER=false` and
`INTENT_ROUTER_V2_ROLLOUT_PERCENT=0`._

## Context

`relationship_router_v2.resolve_relationship_context()` **already
supports** the `forum_topology={"active_member_id": <id>, "forum_id":
<id>, "members": [...]}` argument (verified in
`B2_FOUNDER_OPERATOR_VALIDATION_JUNE14.md` Part 2b — the forum bucket
flips from 0% to 100% pass with no router changes).

The wiring gap is in the **call sites**:

- `mirror_chat_shadow.emit_shadow_receipt()` does not accept a
  `forum_topology` argument today.
- `routers/mirror_chat.py` does not extract a `forum_topology` field
  from `MirrorChatRequest`.
- `server.py::MirrorChatRequest` has no `forum_topology` field.
- The replay / benchmark tools don't carry it either.

P4 closes the entire gap end-to-end.

## Traffic share

Forum-topology-dependent prompts represent ~47.8% of real traffic
(per current telemetry classifier `is_forum_topology_dependent`). Until
P4 lands, `context_mode` for those prompts collapses to `SELF` even
when the user is clearly addressing a specific forum member.

## Scope of edits

### Backend

1. `server.py::MirrorChatRequest`:
   ```python
   forum_topology: Optional[dict] = None
   ```
   - Shape: `{"forum_id": str, "active_member_id": str,
     "members": [{"id": str, "name": str, "role": str?}, ...]}`
   - All keys optional; absent field is treated as no-op (current
     behaviour preserved).

2. `routers/mirror_chat.py`:
   - Pass `forum_topology=getattr(request, "forum_topology", None)`
     through to `emit_shadow_receipt`.
   - **Belt-and-braces fallback**: if `forum_topology` not provided
     but `lens` or `life_domain` strongly implies a forum context,
     synthesise a minimal `forum_topology = {"active_member_id":
     about_person_id}` — this lets the existing "Ask about Member"
     CTA on the forum surface route correctly even before frontend
     ships the explicit field.

3. `services/mirror_chat_shadow.emit_shadow_receipt()`:
   - New parameter `forum_topology: Optional[Dict[str, Any]] = None`.
   - Promote `frame` to `"forum"` when `forum_topology` is provided.
   - Forward the whole dict into
     `resolve_relationship_context(forum_topology=…)`.

4. `tools/b2_replay_runner.py`:
   - Add an optional `forum_topology` column to the row dict so that
     replay rows hydrated from `forum_chat_messages` (where we know
     the active member from `target_member_id`) get a proper
     `forum_topology` synthesised — closing the offline replay gap.

5. `tools/intent_router_v2_benchmark.py`:
   - Pass `forum_topology` through `classify_intent_v2` and
     `resolve_relationship_context` when present in the case YAML.

### Frontend (best-effort, non-blocking)

If a forum-chat screen exists that emits `lens="forum"` (or similar)
requests, ensure the request body includes `forum_topology` with
`active_member_id` whenever a member is currently focused in the UI.
Where that path doesn't exist yet, the backend belt-and-braces
fallback in (2) keeps the routing correct as a temporary bridge.

## Acceptance criteria

- `mirror_chat_retrieval_receipts` will (post-rollout) show
  `is_forum_topology_dependent=true` rows resolving with
  `resolution_path = [..., "forum_active_member"]` and
  `context_mode="RELATIONAL"`.
- New `golden_set_forum_topology.yaml` (10 cases) benchmark top-1 ≥ 95%.
- Existing relationship/forum golden set remains 100% top-1.
- Founder/operator suite Part-2b mirror (`active_member_id` wired) is
  reproducible by anyone with `python tools/forum_topology_validation.py`.
- §6.3 Stage-1 telemetry category `routing_pass_rate` ≥ 90% in offline
  replay.

## Halt criteria (none of these should trip)

- Any pre-existing replay regression bucket flipping to FAIL.
- Relationship-context-loss rate going **up** vs baseline.
- Couple/forum-bleed counter > 0.

## Order of operations

```
Step 1  Add forum_topology field to MirrorChatRequest
Step 2  Plumb through routers/mirror_chat.py and
        services/mirror_chat_shadow.py
Step 3  Add golden_set_forum_topology.yaml (10 cases)
Step 4  Extend benchmark + replay tools to honour the new field
Step 5  Rerun all four legacy benchmark suites — no regressions
Step 6  Rerun replay runner — forum_topology_dependent slice
        pass-rate ≥ 0.90
Step 7  Re-run forum bucket of founder/operator suite with
        active_member_id supplied — must show 100% pass
```

All steps preserve `INTENT_ROUTER_V2_CUTOVER=false` and
`INTENT_ROUTER_V2_ROLLOUT_PERCENT=0`. No production traffic shifts
under P4 — the wiring only changes what **shadow** receipts see.
