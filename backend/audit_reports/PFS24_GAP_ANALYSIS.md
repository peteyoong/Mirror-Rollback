# PFS-2.4 — Gap Analysis

**Scope:** identify every relationship that *should* carry an explicit
`forum_relationship_edges` edge but doesn't, plus recommendations for
closing those gaps before P3 ungating.

> **Read-only audit. No data changes. No flag changes.**

---

## 1. Preview-Environment Gaps (observable from this agent)

### 1.1 Missing edges for known forum members

| Forum         | Member         | Expected role | Edge present? | Notes |
|---------------|----------------|---------------|----------------|-------|
| Yoong family  | Isaac Yoong    | `child` (Pete→Isaac)  | **NO** | Member doc exists; topology edge absent. PFS-1 family-forum heuristic surfaces `role=family` instead, which lands on `self` per PFS-2.3 lexicon design. |
| Yoong family  | Thaddeus Yoong | `child` (Pete→Thaddeus) | **NO** | Same shape as Isaac. |
| Pete & Mel    | Mel → Pete (inverse) | `spouse` (Mel→Pete) | **NO** | Only the Pete→Mel direction is materialised. When Mel asks about Pete the resolver finds the target by name but `topology_role_found=false` for the reverse direction. |
| Yoong family  | Mel → other family members | `spouse` / `parent` / `sibling` directional from Mel | **NO** | Only Pete→Mel exists; reverse and cross-edges missing. |

### 1.2 Missing forums entirely (production-only)

| Forum (production) | Function | Status in Preview | Edges expected |
|--------------------|----------|--------------------|----------------|
| Pulsifi Leadership | Cofounder / leadership team | **Does not exist** | `cofounder` × N |
| (any advisor forum) | Advisor circle | **Does not exist** | `advisor` × N |
| (any mentor forum) | Mentor circle | **Does not exist** | `mentor`/`mentee` × N |
| (any investor forum) | Investor relations | **Does not exist** | `investor` × N |

## 2. Production-Environment Gaps (NOT observable from this agent)

**Cannot be determined from Preview.** The four diagnostic queries to
run against the production DB once read access is available:

```python
# Query 1: distinct role_types in production
distinct = await prod_db.forum_relationship_edges.distinct("role_type")

# Query 2: per-role count
for rt in distinct:
    n = await prod_db.forum_relationship_edges.count_documents({"role_type": rt})
    print(rt, n)

# Query 3: forum_members WITHOUT a corresponding outbound edge from the forum admin
#   (data-quality alarm: members in a forum with NO topology edge)
#
# Query 4: receipts with unknown_role_token in the last 30 days
from datetime import datetime, timedelta
cutoff = datetime.utcnow() - timedelta(days=30)
n_unknown = await prod_db.mirror_chat_retrieval_receipts.count_documents({
    "_id":   {"$gte": <oid for cutoff>},
    "relationship_orchestration_v1.applied_rules":
        {"$elemMatch": {"$regex": "^self:unknown_role_token:"}},
})
```

The agent that gets production-read access (or the operator running
these queries) should report back:
* distinct `role_type` set;
* per-role count;
* count of `forum_members` without any topology edge;
* `unknown_role_token` event rate over the last 30 days.

## 3. Recommended Remediation Ordering

### Pre-condition for ungating

None of the recommendations below require code changes. They are data-
quality / observability work.

1. **Materialise missing `child` edges** for known parent-child
   relationships in production family forums. Without these the
   PFS-2.3 `child` / `parent` / `parenting` / `lineage` buckets are
   inert in production.
2. **Materialise the inverse `spouse` direction** for every existing
   spouse edge (Mel → Pete, etc.). The directional schema is
   intentional but downstream consumers commonly look up either side.
3. **Materialise `cofounder` edges** inside Pulsifi Leadership and any
   other leadership forum (where each forum admin has acknowledged a
   cofounder relationship). High-value because the `cofounder` bucket
   has the most distinct lens-modulation profile vs. the default.
4. **Materialise `advisor` / `mentor` / `investor` edges** where the
   user has acknowledged the relationship.
5. **Observation gate (data quality):** before flipping
   `RELATIONSHIP_ORCHESTRATION_PROMPT=true`, verify the `unknown_role_token`
   event rate is **< 5%** of `replanned_after_topology=true` receipts.
   Anything higher means the lexicon/heuristic axis is not converging
   on real topology yet.

### Lexicon-side: no work required

PFS-2.3 already covers every production-vocabulary role_type
(see `PFS23_ROLE_COVERAGE_MATRIX.md`). The lexicon will not be the
limiting factor; **data parity is.**

## 4. Summary

| Gap class | Severity | Action |
|-----------|----------|--------|
| Missing `child` edges in known family forums (Preview AND likely production) | HIGH | Data materialisation; needs operator |
| Missing inverse `spouse` direction | MEDIUM | Schema-design call; either materialise or update consumers to query both directions |
| Missing `cofounder` edges in leadership forums | HIGH (for ungating value) | Data materialisation; needs operator |
| Missing `advisor` / `mentor` / `investor` edges | MEDIUM | Data materialisation |
| Lexicon coverage | NONE | Already complete in PFS-2.3 |
| `unknown_role_token` rate in production | UNKNOWN | Required diagnostic query before ungating |

**Conclusion:** ungating is **gated on production data quality**, not on
code. The PFS-2.3 implementation is ready; the production graph likely
is not, and Preview cannot tell us how far off it is.
