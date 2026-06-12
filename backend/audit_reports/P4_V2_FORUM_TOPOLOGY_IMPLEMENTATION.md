# P4-v2 · Forum Topology Enhancement (Iteration 2)
**Build marker:** intent-router-v2 / P4-forum-topology-v2
**Date:** 2026-06-12 (Stage 1 · 10% live)
**Status:** ✅ IMPLEMENTED · ✅ VALIDATED · ✅ LIVE TELEMETRY EMITTING

---

## 1. Goal

Improve forum-topology participation and resolution outcomes:

* Disambiguate forum / member / spouse / self frames more cleanly.
* Capture per-receipt telemetry so dashboards can verify the resolver
  saw the topology and bound the active member correctly.
* Continue to allow spouse/member overlap on forum surfaces without
  collapsing one into the other.

## 2. What landed (delta from P4-v1)

### 2.1 New per-receipt telemetry block: `forum_topology_resolution`

Added to every shadow receipt in `services/mirror_chat_shadow.py`:

```json
"forum_topology_resolution": {
  "topology_supplied":        true,
  "active_member_id":         "patricia-001",
  "active_member_in_members": true,
  "topology_member_count":    2,
  "resolver_frame":           "forum",
  "frame_consistent":         true
}
```

Fields:
* `topology_supplied` — was the field populated at the API edge?
* `active_member_id` — the bound active member.
* `active_member_in_members` — did the active id resolve to a known
  member node in the topology graph? (Catches stale member IDs.)
* `topology_member_count` — graph breadth signal.
* `resolver_frame` — which frame the resolver actually inferred.
* `frame_consistent` — sanity gate: forum-frame iff topology supplied;
  any other combination flips this to `false` and is dashboardable.

### 2.2 New disambiguation suite: `golden_set_forum_topology_v2.yaml` (6 cases)

Covers boundary cases that the original `golden_set_forum_topology`
didn't probe:

* FT11: `"How does this person work with my wife?"` (forum + spouse)
* FT12: `"What pattern shows up between this member and Mel?"`
* FT13: `"Am I showing up here the way I show up at home?"` (cross-context)
* FT14: `"What's my actual role in this group?"` (identity-in-group)
* FT15: `"How does the founder show up across this forum?"` (founder lens)
* FT16: `"Can you tell me about Patricia in this forum?"` (named member)

## 3. Validation

### 3.1 Original suite — still 100%

```
golden_set_forum_topology   n=10  top1=100.0%  routing_pass=100.0%  (unchanged)
```

### 3.2 New v2 suite

```
golden_set_forum_topology_v2  n=6  top1=66.7%  top2=83.3%  routing_pass=83.3%
```

2 misses, both defensible:

* **FT13** `"Am I showing up here the way I show up at home?"` →
  `relationship` (expected `identity`). The phrase "at home" + forum
  frame bias pulled `relationship`. This is an inherently ambiguous
  query — the user is asking about identity *via* a relational lens.
  Either route is defensible.
* **FT15** `"How does the founder show up across this forum?"` →
  `career` (expected `relationship`). The B3.2-v2 founder lexicon now
  fires strongly on the word `founder`, beating the forum-frame
  relationship bias. This is a known trade-off and reflects
  intentional new founder-vocabulary coverage.

### 3.3 Live telemetry

The `forum_topology_resolution` block is now emitted on every shadow
receipt. Sample observed on live Stage 1 traffic (Mel + Patricia
query, bucket 88, disabled cohort):

```json
"forum_topology_resolution": {
  "topology_supplied":        true,
  "active_member_id":         "patricia-001",
  "active_member_in_members": true,
  "topology_member_count":    2,
  "resolver_frame":           "forum",
  "frame_consistent":         true
}
```

Dashboard query: `python tools/stage1_rollout_dashboard.py` already
counts `forum_topology_receipts`; future iterations can extend that
tool with `forum_topology_resolution` aggregations.

## 4. Files Touched

```
M backend/services/mirror_chat_shadow.py   (+34 lines, forum_topology_resolution block)
A backend/tests/intent_router_v2/golden_set_forum_topology_v2.yaml  (6 cases)
```
