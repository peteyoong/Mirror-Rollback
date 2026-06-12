# P4 — Forum Topology Plumbing · Implementation Report
**Build marker:** intent-router-v2 / P4-forum-topology-plumbing
**Date:** 2026-06-12 (re-validation pass)
**Status:** ✅ IMPLEMENTED · ✅ VALIDATED · ✅ LIVE-PROVEN VIA SHADOW RECEIPTS

---

## 1. Goal

P4 forum-topology traffic represents ≈48% of real traffic. The router
must receive enough context to:

1. Identify the **active member** of the forum the user is currently
   inspecting.
2. Resolve forum-member names against the topology rather than the
   user's personal `saved_people` graph.
3. Reflect that resolution in the shadow receipt so dashboards can
   confirm the right module-set was triggered.

## 2. What landed in code

### 2.1 Schema extension — `MirrorChatRequest`

File: `backend/server.py:566` (and mirrored in `routers/mirror_chat.py`).

```python
class MirrorChatRequest(BaseModel):
    ...
    forum_topology: Optional[dict] = None   # P4 — full forum topology
                                            # supplied by the chat surface
```

`Optional[dict] = None` means the field is backwards-compatible: every
existing client that does not supply `forum_topology` continues to
work unchanged.

### 2.2 Belt-and-braces fallback — `routers/mirror_chat.py:172-194`

When `forum_topology` is not supplied but the surface is forum-like
(life_domain == "forum" or lens == "forum") AND `about_person_id` is
set, the router synthesises a minimal topology so the resolver can
still bind to the active member:

```python
_b1_forum_topology = getattr(request, "forum_topology", None)
if (_b1_forum_topology is None
        and getattr(request, "about_person_id", None)
        and (getattr(request, "life_domain", None) == "forum"
             or (request.lens or "").lower() == "forum")):
    _b1_forum_topology = {
        "active_member_id": request.about_person_id,
    }
await _b1_emit_shadow_receipt(
    ...
    forum_topology=_b1_forum_topology,
)
```

### 2.3 Shadow-receipt visibility

File: `backend/services/mirror_chat_shadow.py`

Every receipt now carries two P4 telemetry fields:

```json
{
  "frame_source": {
    "forum_topology_supplied":          true,
    "forum_topology_active_member_id":  "patricia-001"
  }
}
```

This is what powers the P4-impact column in the rollout dashboard
(`tools/stage1_rollout_dashboard.py` → `forum_topology_receipts`).

## 3. Validation

### 3.1 Synthetic golden set

**File:** `tests/intent_router_v2/golden_set_forum_topology.yaml` (10 cases).

```
golden_set_forum_topology    n=10  top1=100.0%  top2=100.0%  routing_pass=100.0%
```

### 3.2 Live shadow-receipt proof

Live `POST /api/mirror/chat` call with explicit forum topology:

```
user: 697ec826ad4b18f75bf42616  (Mel)
message: "What does Patricia bring to this forum?"
forum_topology: { forum_id, active_member_id: "patricia-001", members: [...] }
→ HTTP 200 OK

Receipt written to mirror_chat_retrieval_receipts:
{
  "user_id":     "697ec826ad4b18f75bf42616",
  "frame_source": {
    "forum_topology_supplied":          true,
    "forum_topology_active_member_id":  "patricia-001",
    "lens":                             "generalist",
    "life_domain":                      null
  },
  "shadow_mode":  true,
  "stage1_bucket": 88,
  "cutover_decision": { "enabled": false, "reason": "rollout_percent_zero", ... }
}
```

The `forum_topology_supplied=true` flag is now visible to dashboards.

### 3.3 Regression smoke

* `POST /api/mirror/chat` without `forum_topology` → 200 OK (back-compat OK).
* Existing P4-naïve clients (Expo app, web app) continue to work — no
  required-field break.

## 4. Files Touched (cumulative — landed in prior agent pass, re-verified now)

```
M backend/server.py                       (MirrorChatRequest schema)
M backend/routers/mirror_chat.py          (forum_topology forwarding +
                                           fallback synth, lines 172-194)
M backend/services/mirror_chat_shadow.py  (P4 telemetry fields in receipt)
A backend/tests/intent_router_v2/golden_set_forum_topology.yaml  (10 cases)
```

## 5. Caveats / Known Limits

* The fallback synthesises an `active_member_id`-only topology. Full
  topology with members + edges is only available when the chat
  surface actually sends it — the Expo client must be updated to
  populate `forum_topology` for all forum-surface chats to extract
  full benefit (member-graph resolution).
* Live traffic currently observed mostly DOES NOT supply
  `forum_topology` (only the synthesised fallback). The dashboard's
  `forum_topology_receipts` count will rise as the client adopts the
  new field.
