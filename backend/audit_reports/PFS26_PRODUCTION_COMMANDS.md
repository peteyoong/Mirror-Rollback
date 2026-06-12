# PFS-2.6 — Production Commands (Exact)

Copy / paste / execute. Read-only. No writes.

---

## 1. Configure connection (operator shell, one-shot)

```bash
export MONGO_URL='mongodb+srv://<readonly-user>:<pass>@<cluster>/?retryWrites=true&w=majority'
export DB_NAME='<production_db_name>'
```

---

## 2. Smoke test

```bash
python - <<'PY'
import os, asyncio
from motor.motor_asyncio import AsyncIOMotorClient
async def m():
    db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    print("forum_relationship_edges            =",
          await db.forum_relationship_edges.count_documents({}))
    print("mirror_chat_retrieval_receipts      =",
          await db.mirror_chat_retrieval_receipts.count_documents({}))
    print("forum_members                       =",
          await db.forum_members.count_documents({}))
    print("forums                              =",
          await db.forums.count_documents({}))
asyncio.run(m())
PY
```

---

## 3. Full harness run

```bash
python /app/backend/scripts/pfs25_graph_audit.py > pfs26_production_audit.txt 2>&1
```

---

## 4. Schema-conformant JSON (the only file the scoring agent needs)

Use the script embedded in `PFS26_OPERATOR_RUNBOOK.md` Step 5 verbatim.
Output goes to `pfs26_production_audit.json`.

---

## 5. Direct ad-hoc Mongo queries (mongosh) — for spot checks only

### 5.1 — Distinct role_types

```javascript
db.forum_relationship_edges.distinct("role_type")
```

### 5.2 — Edge counts by role

```javascript
db.forum_relationship_edges.aggregate([
  { $group: { _id: "$role_type", n: { $sum: 1 } } },
  { $sort: { n: -1 } }
])
```

### 5.3 — Confidence distribution per role

```javascript
db.forum_relationship_edges.aggregate([
  { $group: {
      _id: { role_type: "$role_type", confidence: "$confidence" },
      n: { $sum: 1 } } },
  { $sort: { "_id.role_type": 1 } }
])
```

### 5.4 — Pete outbound edges

```javascript
db.forum_relationship_edges.find(
  { from_user_id: "697f0c6abf35c0528ff06954" },
  { _id: 0, forum_id: 1, to_user_id: 1, role_type: 1,
    confidence: 1, inferred: 1 }
).toArray()
```

### 5.5 — Inverse-direction coverage

```javascript
const edges = db.forum_relationship_edges.find({},
  { _id: 0, forum_id: 1, from_user_id: 1, to_user_id: 1, role_type: 1 }
).toArray();
const keys = new Set(edges.map(e =>
  `${e.forum_id}|${e.from_user_id}|${e.to_user_id}`));
let present = 0;
for (const e of edges) {
  if (keys.has(`${e.forum_id}|${e.to_user_id}|${e.from_user_id}`)) present++;
}
printjson({
  total: edges.length,
  with_inverse: present,
  pct: edges.length ? (present / edges.length * 100).toFixed(2) : 0
});
```

### 5.6 — Contradictions (same forum + pair, different role)

```javascript
db.forum_relationship_edges.aggregate([
  { $group: {
      _id: { forum_id: "$forum_id",
             from: "$from_user_id",
             to:   "$to_user_id" },
      roles: { $addToSet: "$role_type" },
      n: { $sum: 1 } } },
  { $match: { $expr: { $gt: [ { $size: "$roles" }, 1 ] } } }
]).toArray()
```

Must return `[]`. Any rows = data-integrity failure.

### 5.7 — Telemetry: topology_aware_pct (last 30 days)

```javascript
const cutoff = new Date(Date.now() - 30*24*3600*1000);
const window = { $or: [{ created_at: { $gte: cutoff } },
                       { timestamp:  { $gte: cutoff } }] };
const replanned = db.mirror_chat_retrieval_receipts.countDocuments({
  $and: [ window,
          { "relationship_orchestration_v1.replanned_after_topology": true } ]
});
const topo_aware = db.mirror_chat_retrieval_receipts.countDocuments({
  $and: [ window,
          { "relationship_resolution.topology_role_found": true } ]
});
const pct = replanned ? (topo_aware / replanned * 100).toFixed(2) : 0;
printjson({ replanned, topo_aware, topology_aware_pct: pct });
```

### 5.8 — unknown_role_token frequency (last 30 days)

```javascript
const cutoff = new Date(Date.now() - 30*24*3600*1000);
const window = { $or: [{ created_at: { $gte: cutoff } },
                       { timestamp:  { $gte: cutoff } }] };
const replanned = db.mirror_chat_retrieval_receipts.countDocuments({
  $and: [ window,
          { "relationship_orchestration_v1.replanned_after_topology": true } ]
});
const unknown = db.mirror_chat_retrieval_receipts.countDocuments({
  $and: [ window,
          { "relationship_orchestration_v1.applied_rules":
              { $elemMatch: { $regex: "^self:unknown_role_token:" } } } ]
});
const pct = replanned ? (unknown / replanned * 100).toFixed(2) : 0;
printjson({ replanned, unknown_role_token: unknown,
            unknown_role_token_pct: pct });
```

---

## 6. NEVER run these (they would write to production)

* `db.forum_relationship_edges.insert*`
* `db.forum_relationship_edges.update*`
* `db.forum_relationship_edges.delete*`
* `db.forum_relationship_edges.drop*`
* Anything against the `INTENT_ROUTER_V2_*`, `RELATIONSHIP_ORCHESTRATION_PROMPT`,
  `CROSS_LENS_PROMPT_SURFACE` env vars.

If any of those appear in a paste, **stop**. Read-only audit.
