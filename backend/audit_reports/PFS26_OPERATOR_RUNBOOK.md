# PFS-2.6 — Operator Runbook

**Purpose:** Step-by-step instructions for the operator to execute the
production relationship-graph audit and return a deterministic
scorecard back to the next agent for ungating decision.

**Audience:** A human operator with read access to the production
MongoDB cluster (or to a host that has it).

**Mode:** Read-only. No writes. No flag flips.

---

## Step 0 — Preconditions

* Read-only production MongoDB credentials.
* A host (workstation, jump-box, or temporarily-credentialed agent)
  with:
  - Python ≥ 3.10
  - `motor`, `pymongo`, `python-dotenv` installed
  - Network reachability to the production Mongo cluster
* The exact production database name (e.g. `mirror_prod`,
  `mirrorworld_production`, etc. — confirm with infra).

---

## Step 1 — Copy the harness onto the host

The harness already exists at
`/app/backend/scripts/pfs25_graph_audit.py` in this Preview
repository. Copy it to the operator host. If the operator host is a
checkout of the same repo, the file is already present.

Dependencies (only standard ones the harness uses):

```
pip install motor pymongo python-dotenv
```

(`relationship_orchestration_v1` import — either copy
`services/relationship_orchestration_v1.py` to the operator host, or
run the harness inside a clone of the same repo.)

---

## Step 2 — Configure the connection

**DO NOT** edit `/app/backend/.env` to point at production. That
breaks Preview. Instead, set env vars in the operator shell
*for the harness run only*:

```bash
export MONGO_URL='mongodb+srv://<readonly-user>:<pass>@<cluster>/?retryWrites=true&w=majority'
export DB_NAME='<production_db_name>'
```

---

## Step 3 — Smoke test the credential

```bash
python - <<'PY'
import os, asyncio
from motor.motor_asyncio import AsyncIOMotorClient
async def main():
    db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    n = await db.forum_relationship_edges.count_documents({})
    print("forum_relationship_edges count =", n)
    n2 = await db.mirror_chat_retrieval_receipts.count_documents({})
    print("mirror_chat_retrieval_receipts count =", n2)
asyncio.run(main())
PY
```

Expected: integer counts. If you see authentication errors, fix the
credential before continuing.

---

## Step 4 — Run the audit harness

From the operator host (NOT this agent):

```bash
python scripts/pfs25_graph_audit.py > pfs26_production_audit.txt 2>&1
```

Expected runtime: < 60 s on production-scale data (the harness is
linear in `O(edges + members + receipts)`).

---

## Step 5 — Capture the schema JSON

Run the second helper to produce the schema-conformant JSON that
the scoring agent will consume:

```bash
python - <<'PY' > pfs26_production_audit.json
import os, asyncio, json
from datetime import datetime, timedelta, timezone
from collections import Counter, defaultdict
from motor.motor_asyncio import AsyncIOMotorClient

PRIORITY = ["spouse","child","cofounder","advisor","mentor","investor"]
PETE_ID = "697f0c6abf35c0528ff06954"   # confirm in production!

async def main():
    db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]

    # 1. Edges
    edges = []
    async for e in db.forum_relationship_edges.find():
        e.pop("_id", None); edges.append(e)

    role_counter      = Counter(e.get("role_type") for e in edges)
    conf_counter      = Counter(e.get("confidence") for e in edges)
    inferred_counter  = Counter(str(e.get("inferred")) for e in edges)

    # 2. Inverse coverage
    pair_keys = {(str(e["forum_id"]), str(e["from_user_id"]),
                  str(e["to_user_id"])): e.get("role_type") for e in edges}
    inv_present = sum(1 for (fid,a,b) in pair_keys
                      if (fid,b,a) in pair_keys)
    inv_pct = (inv_present / len(pair_keys) * 100.0) if pair_keys else 0.0

    # 3. Duplicates / contradictions
    grouped = defaultdict(list)
    for e in edges:
        grouped[(str(e["forum_id"]), str(e["from_user_id"]),
                 str(e["to_user_id"]))].append(e.get("role_type"))
    duplicates = sum(1 for g in grouped.values() if len(g) > 1
                     and len(set(g)) == 1)
    contradictions = sum(1 for g in grouped.values() if len(set(g)) > 1)

    # 4. Telemetry (last 30 days)
    cutoff = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(days=30)
    q_window = {"$or": [
        {"created_at": {"$gte": cutoff}},
        {"timestamp":  {"$gte": cutoff}},
    ]}
    total_30d     = await db.mirror_chat_retrieval_receipts.count_documents(q_window)
    replanned_30d = await db.mirror_chat_retrieval_receipts.count_documents(
        {"$and":[q_window,{"relationship_orchestration_v1.replanned_after_topology": True}]})
    topo_30d      = await db.mirror_chat_retrieval_receipts.count_documents(
        {"$and":[q_window,{"relationship_resolution.topology_role_found": True}]})
    unknown_30d   = await db.mirror_chat_retrieval_receipts.count_documents({"$and":[
        q_window,
        {"relationship_orchestration_v1.applied_rules":
            {"$elemMatch": {"$regex": "^self:unknown_role_token:"}}}]})

    topo_pct    = (topo_30d / replanned_30d * 100.0) if replanned_30d else 0.0
    unknown_pct = (unknown_30d / replanned_30d * 100.0) if replanned_30d else 0.0

    # 5. Pete reality check
    pete_edges = []
    async for e in db.forum_relationship_edges.find({"from_user_id": PETE_ID}):
        e.pop("_id", None); pete_edges.append(e)
    pete_by_role = Counter(e.get("role_type") for e in pete_edges)

    out = {
        "meta": {
            "environment": "production",
            "db_name":     os.environ["DB_NAME"],
            "run_at_utc":  datetime.utcnow().isoformat() + "Z",
            "window_days": 30,
        },
        "edges": {
            "total":             len(edges),
            "by_role_type":      dict(role_counter),
            "by_confidence":     dict(conf_counter),
            "by_inferred_flag":  dict(inferred_counter),
        },
        "inverse_coverage": {
            "pairs_total":             len(pair_keys),
            "pairs_with_inverse":      inv_present,
            "inverse_coverage_pct":    round(inv_pct, 2),
        },
        "integrity": {
            "duplicates":      duplicates,
            "contradictions": contradictions,
        },
        "telemetry_30d": {
            "receipts_total":          total_30d,
            "replanned_after_topology": replanned_30d,
            "topology_role_found":     topo_30d,
            "unknown_role_token":      unknown_30d,
            "topology_aware_pct":      round(topo_pct, 2),
            "unknown_role_token_pct":  round(unknown_pct, 2),
        },
        "priority_role_coverage": {
            r: role_counter.get(r, 0) for r in PRIORITY
        },
        "pete_reality_check": {
            "user_id":   PETE_ID,
            "total_outbound_edges": len(pete_edges),
            "by_role_type":         dict(pete_by_role),
            "edges": [{
                "forum_id":   e.get("forum_id"),
                "to":         e.get("to_user_id"),
                "role_type":  e.get("role_type"),
                "confidence": e.get("confidence"),
                "inferred":   e.get("inferred"),
            } for e in pete_edges],
        },
    }
    print(json.dumps(out, indent=2, default=str))
asyncio.run(main())
PY
```

Expected output: a JSON document matching
`PFS26_EXPECTED_OUTPUT_SCHEMA.json` exactly.

---

## Step 6 — Score the output

Apply the rubric from `PFS26_BLOCKER_REPORT.md` §C:

| Row | Field in JSON                                       | PASS condition                                                                |
|-----|-----------------------------------------------------|-------------------------------------------------------------------------------|
| 1   | `priority_role_coverage`                            | At least 3 of the 6 priority roles have count ≥ 5                            |
| 2   | `priority_role_coverage`                            | Each priority role appearing in (1) has count ≥ 5                            |
| 3   | `inverse_coverage.inverse_coverage_pct`             | ≥ 80 % — OR — schema documented as intentionally directional with consumer parity |
| 4   | `integrity.contradictions`                          | = 0                                                                           |
| 5   | `telemetry_30d.unknown_role_token_pct`              | < 5 % (only meaningful if `replanned_after_topology` ≥ 100 in the window)    |
| 6   | `telemetry_30d.topology_aware_pct`                  | ≥ 60 %     (only meaningful if `replanned_after_topology` ≥ 100)             |

All six PASS → authorise the Stage-1 observation window.
Any one FAIL → stop, identify missing edges, materialise, re-run.

---

## Step 7 — Return the artefacts

Produce these two files and send them back to the next agent:

* `pfs26_production_audit.txt` — the raw harness output (text).
* `pfs26_production_audit.json` — the schema-conformant JSON.

The scoring agent will not need any further data from production to
produce the final ungating decision.

---

## Step 8 — If FAIL: missing-edge backlog

If any row fails, the operator returns:

* `pfs26_production_audit.json` (which shows the failing rows)
* A human-readable list of relationships that should exist but don't.
  (Format suggestion: `<from_user_name> → <to_user_name> : <expected_role> in <forum_name>`.)

The data team materialises those edges (out of agent scope). After
materialisation, **re-run from Step 4**.

---

## Reminders — do NOT do these

* Do not edit `/app/backend/.env` to point at production. Preview
  will break.
* Do not change any of the four sprint-locked flags.
* Do not write to production from this audit. The harness is read-only.
* Do not invent edge data. If a row shows 0, that's the answer.
