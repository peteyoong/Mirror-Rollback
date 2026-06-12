# PFS-2.5 — Missing Edge Report

**Source:** `scripts/pfs25_graph_audit.py` against Preview.
**Production:** not measurable from this agent.

---

## 1. Missing edges visible in Preview

### 1.1 Forum members without an outbound edge (12 ordered pairs)

Inside the two real forums (Pete & Mel, Yoong family) there are 12
ordered (from→to) member pairs that lack a `forum_relationship_edges`
row.

| Forum         | from → to              | Likely real role (production guess) | Severity |
|---------------|-------------------------|--------------------------------------|----------|
| Yoong family  | Pete → Isaac            | `child`                              | HIGH     |
| Yoong family  | Pete → Thaddeus         | `child`                              | HIGH     |
| Yoong family  | Mel  → Isaac            | `child`                              | HIGH     |
| Yoong family  | Mel  → Thaddeus         | `child`                              | HIGH     |
| Yoong family  | Isaac → Pete            | `parent`                             | MEDIUM   |
| Yoong family  | Isaac → Mel             | `parent`                             | MEDIUM   |
| Yoong family  | Thaddeus → Pete         | `parent`                             | MEDIUM   |
| Yoong family  | Thaddeus → Mel          | `parent`                             | MEDIUM   |
| Yoong family  | Isaac → Thaddeus        | `sibling`                            | LOW      |
| Yoong family  | Thaddeus → Isaac        | `sibling`                            | LOW      |
| Pete & Mel    | Mel → Pete              | `spouse` (inverse)                   | MEDIUM   |
| Yoong family  | Mel → Pete              | `spouse` (inverse)                   | MEDIUM   |

### 1.2 Inverse-direction missing (2 of 2)

Every existing spouse edge points Pete→Mel; the reverse direction
Mel→Pete is absent. The PFS-2.1 resolver looks up the directed pair
`from=user, to=candidate` — if Mel asks about Pete, the resolver
cannot find the topology edge and falls back to the PFS-1 heuristic.

## 2. Missing edges expected in production but invisible from here

Known from prior audits (`PRODUCTION_TOPOLOGY_AUDIT.md`):

* **Pulsifi Leadership forum** + cofounder edges — absent in Preview.
  In production this is the most operationally important missing
  surface for Pete's chat workflow.
* **Advisor / Mentor / Investor circles** — absent in Preview.
* **Any non-Pete primary users** — production has many users with
  their own family/work topology; Preview has only Pete + Mel + two
  child members.

## 3. Ambiguous / contradictory edges (Preview)

* **Duplicates: 0.**
* **Contradictions: 0.**
* **Ambiguous edges: 0** in the strict sense (no (forum, from, to) is
  bound to two conflicting `role_type` values).

## 4. `unknown_role_token` event analysis (Preview)

```
self:unknown_role_token:family  — 1 occurrence (Isaac receipt)
```

Driver: the PFS-1 family-forum heuristic emits `role=family` when a
candidate matches a member of a forum whose name contains "family"
AND no explicit topology edge exists for the pair. The token is the
dashboard-visible flag that production data quality is insufficient
for that target.

**The unknown-rate metric (33.3 % of replanned receipts) is
statistically not meaningful at n=3.** It IS the right metric to
track on production at scale.

## 5. Recommended remediation order (re-stated from PFS-2.4 §3)

1. Materialise explicit `parent`/`child` edges inside known family forums.
2. Materialise inverse-direction `spouse` edges (Mel→Pete).
3. Materialise `cofounder` edges inside leadership forums.
4. Materialise `advisor`/`mentor`/`investor` edges per user acknowledgement.
5. Re-run `scripts/pfs25_graph_audit.py` on production and verify:
   * ≥ 4 of 8 special-focus categories non-zero
   * `unknown_role_token` rate < 5 % of `replanned_after_topology=true` over a 30-day window.
