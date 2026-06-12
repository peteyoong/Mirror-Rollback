# PFS-2.5 — Production Relationship Graph Inventory

**Sprint:** PFS-2.5 (Production Relationship Graph Audit)
**Mode:** Read-only.
**Environment audited:** **Preview** (`DB_NAME=test_database`). **Production data is NOT accessible from this agent.**

> Same environmental caveat as PFS-2.4: Preview and Production MongoDB
> clusters are isolated. The harness used here
> (`scripts/pfs25_graph_audit.py`) is parameterised on `MONGO_URL` /
> `DB_NAME` and will run identically against Production once an
> operator provides a read-only URI.

---

## 1. Topline (Preview)

| Metric                                                  | Value |
|---------------------------------------------------------|-------|
| `forum_relationship_edges` total                        | **2** |
| Distinct `role_type` values                             | **1** — `spouse` |
| `high` confidence edges                                 | 2 |
| Explicit edges (`inferred=false`)                       | 2 |
| Duplicates (same forum+from+to+role)                    | **0** |
| Contradictions (same forum+from+to, different role)     | **0** |
| Inverse-direction missing (A→B exists, B→A absent)       | **2** |
| Forum-member ordered pairs without edge                 | **12** |
| `mirror_chat_retrieval_receipts` total                  | 106 |
| Receipts with `replanned_after_topology=true`           | 3 |
| `unknown_role_token` events                             | 1 |
| Unknown rate (% of replanned)                           | **33.3 %** |

---

## 2. Full Edge Inventory (Preview)

| forum_name    | source_user | target_user | stored_role | resolved_bucket | resolved_framing | domain_bias  | topology_confidence | inferred |
|---------------|-------------|-------------|-------------|-----------------|------------------|--------------|---------------------|----------|
| Yoong family  | Pete        | Mel         | `spouse`    | `spouse`        | `couple_dynamic` | relationship | high                | false    |
| Pete & Mel    | Pete        | Mel         | `spouse`    | `spouse`        | `couple_dynamic` | relationship | high                | false    |

## 3. Special-Focus Coverage (Preview)

| Focus role     | Edges present | Status |
|----------------|---------------|--------|
| spouse         | **2**         | ✅ Observable end-to-end |
| child          | 0             | ❌ ENVIRONMENTAL N/A — Isaac/Thaddeus are forum members only |
| cofounder      | 0             | ❌ ENVIRONMENTAL N/A — no leadership forums exist locally |
| advisor        | 0             | ❌ ENVIRONMENTAL N/A |
| mentor         | 0             | ❌ ENVIRONMENTAL N/A |
| investor       | 0             | ❌ ENVIRONMENTAL N/A |
| forum_member   | 0             | ⚠ No explicit `forum_member` / `forum_mate` / `other` edges |
| forum_mate     | 0             | ⚠ Same as above |

## 4. Data Quality Findings (Preview)

* **Duplicates: 0.** Clean.
* **Contradictions: 0.** No (forum, from→to) pair has multiple
  conflicting `role_type` values.
* **Inverse-direction gap: 2.** Pete→Mel exists in both forums; Mel→Pete
  does not. May be intentional (schema is directional) but worth
  confirming with the schema owner.
* **Forum-member-without-edge gap: 12.** Inside Yoong family (4
  members) and Pete & Mel (2 members) there are 12 ordered pairs
  with no edge — e.g. Pete→Isaac, Pete→Thaddeus, Mel→Isaac,
  Isaac→Pete, Thaddeus→Pete, etc. Each is a candidate edge that
  production may or may not carry.

## 5. `unknown_role_token` Telemetry (Preview)

```
replanned_after_topology_T  : 3
unknown_role_token_events   : 1
unknown_rate_pct_of_replanned : 33.33 %
ungating_threshold_pct      : 5.00 %
```

**Above the 5 % ungating threshold** — but the denominator (3) is too
small to be statistically meaningful. The single event is the
documented Isaac `self:unknown_role_token:family` case (PFS-1 family
forum heuristic).

---

## 6. Companion Files

| File                                          | Purpose |
|-----------------------------------------------|---------|
| `PFS25_PRODUCTION_GRAPH_INVENTORY.md`         | **this file** |
| `PFS25_ROLE_COVERAGE_REPORT.md`               | Per-role coverage analysis |
| `PFS25_MISSING_EDGE_REPORT.md`                | Edges that should exist but don't (Preview-observable + production-likely) |
| `PFS25_UNGATING_READINESS.md`                 | Final A/B/C recommendation |
| `PFS25_AUDIT_RAW.txt`                         | Full raw output of the audit harness |
| `scripts/pfs25_graph_audit.py`                | Re-runnable harness — point at production via env vars |

## 7. Constraints Verified

```
INTENT_ROUTER_V2_CUTOVER             = false   ✅ untouched
INTENT_ROUTER_V2_ROLLOUT_PERCENT     = 10      ✅ untouched
RELATIONSHIP_ORCHESTRATION_PROMPT    = false   ✅ untouched
CROSS_LENS_PROMPT_SURFACE            = false   ✅ untouched
```
