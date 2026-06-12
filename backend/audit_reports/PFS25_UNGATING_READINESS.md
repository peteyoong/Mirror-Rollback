# PFS-2.5 — Ungating Readiness

**Sprint:** PFS-2.5
**Decision-grade input for:** `RELATIONSHIP_ORCHESTRATION_PROMPT=true` Stage-1 activation.

---

## TL;DR

* **Code readiness:** ✅ (PFS-2.1 + PFS-2.3 land cleanly; 102/102 tests green).
* **Preview data:** ❌ (only `spouse` covered; 1 / 20 role_types observable).
* **Production data:** **UNKNOWN** — not measurable from this agent.
* **Recommended decision:** **HOLD UNGATING.** Provision production read access OR an operator-curated production snapshot before any flip.

Constraints currently held:

```
INTENT_ROUTER_V2_CUTOVER             = false
INTENT_ROUTER_V2_ROLLOUT_PERCENT     = 10
RELATIONSHIP_ORCHESTRATION_PROMPT    = false
CROSS_LENS_PROMPT_SURFACE            = false
```

---

## A. Is the production graph complete enough for `RELATIONSHIP_ORCHESTRATION_PROMPT=true`?

> **CANNOT BE DETERMINED FROM THIS ENVIRONMENT.**

Preview observation alone is *strictly insufficient* — it carries 2
edges (both `spouse`). Any answer about production graph completeness
requires running the inventory harness against production.

Minimum gating criteria the operator (or a production-read-capable
agent) must verify before flipping the flag:

1. Distinct `role_type` values in production includes ≥ **3 of**
   `{spouse, child, cofounder, advisor, mentor, investor}`.
2. Per-role edge count ≥ **5** for each of the categories meant to be
   exercised by Stage-1 traffic.
3. `unknown_role_token` rate < **5 %** of `replanned_after_topology=true`
   receipts over a 30-day window.
4. `contradictions` (same forum+pair, different role) = **0**.
5. `inverse-direction missing` < **10 %** of total edges (or schema
   documented as intentionally directional with downstream consumers
   adapted).

## B. Which specific missing edges would materially affect Pete’s experience?

High-impact missing edges in Preview that almost certainly also
affect Pete in production:

| Missing edge                          | Production impact                                                                                  |
|---------------------------------------|----------------------------------------------------------------------------------------------------|
| Pete → Isaac : `child`                | When Pete chats about Isaac, orchestration lands on `self` instead of `child / parenting`. The reflection misses the family-developmental framing entirely. |
| Pete → Thaddeus : `child`             | Same as Isaac.                                                                                     |
| Mel → Pete : `spouse` (inverse)       | When Mel chats about Pete, no topology edge → falls back to PFS-1 alias heuristics; weaker fidelity. |
| Pete → (cofounders in Pulsifi Leadership) : `cofounder` | Pete's most operationally important chats (founder topics) cannot land on the `cofounder` bucket without this edge. Stage-1 ungating would be net-neutral for these turns. |
| Pete → (advisor) : `advisor`          | Founder-advisor reflections cannot land on `advisor / guidance`. Same as cofounder.                |
| Pete → (investor) : `investor`        | Investor-touchpoint reflections cannot land on `investor / influence`. Same as cofounder.          |

## C. What percentage of real relationship traffic would be topology-aware if ungated today?

> **Cannot be measured from Preview.**

What *can* be said: in the Preview observation window, of 3 receipts
that triggered `replanned_after_topology=true`:

* 2 were **topology-aware** (Mel → spouse) — 67 %
* 1 fell to **PFS-1 fallback with `unknown_role_token`** (Isaac → family) — 33 %

This 67 % topology-awareness rate is an artifact of Preview's
single-edge-type graph; it is not a production signal.

The diagnostic to run on production after operator access is granted:

```
N_replanned       = count("relationship_orchestration_v1.replanned_after_topology" == true)
N_topology_aware  = count("relationship_resolution.topology_role_found" == true)
topology_aware_pct = N_topology_aware / N_replanned * 100
```

Gating recommendation: **topology_aware_pct ≥ 60 %** before any
ungating. Below that, ungating would surface stale `self` plans more
often than topology-aware plans — net-neutral or net-negative impact.

---

## Final Recommendation

**HOLD.** No flag flips.

Next action sequence:

1. Operator: provision production read-only access for
   `forum_relationship_edges`, `forum_members`, `forums`, and
   `mirror_chat_retrieval_receipts`.
2. Re-run `scripts/pfs25_graph_audit.py` against production.
3. Score against the five gating criteria in section A.
4. **Only if all 5 pass**, proceed with sequenced Stage-1 ungating
   (`RELATIONSHIP_ORCHESTRATION_PROMPT=true` first, then
   `CROSS_LENS_PROMPT_SURFACE=true`), each with rollback ready.
5. Independent of ungating: data-quality work to materialise the
   missing edges identified in `PFS25_MISSING_EDGE_REPORT.md`.

Constraints reaffirmed and verified untouched.
