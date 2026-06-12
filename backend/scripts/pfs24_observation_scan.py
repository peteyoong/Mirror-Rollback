"""PFS-2.4 — Production Observation: scan persisted shadow receipts.

Read-only inspection of `mirror_chat_retrieval_receipts` to bucket
real traffic by topology role and PFS-2.3 orchestration outcome.

OUTPUT
======
1. Summary counters (per bucket, per topology_role_found, per
   replanned_after_topology, per domain_bias).
2. Up to N sample receipts per role bucket for the trace-samples report.
3. Unknown-role-token events (lexicon gaps in the wild).
4. Resolution-source distribution (topology vs heuristic).
5. Forum/role coverage gaps.
"""
import asyncio
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from dotenv import load_dotenv

load_dotenv("/app/backend/.env")
sys.path.insert(0, "/app/backend")

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

SAMPLE_LIMIT = 5
TRACE_WINDOW_DAYS = 30


def _jsonable(o: Any) -> Any:
    if isinstance(o, dict):
        return {k: _jsonable(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_jsonable(v) for v in o]
    if isinstance(o, datetime):
        return o.isoformat()
    return o


async def main():
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    db_name = os.environ["DB_NAME"]
    print(f"# PFS-2.4 observation scan — DB={db_name}")
    print(f"# run_at={datetime.utcnow().isoformat()}Z")

    cols = await db.list_collection_names()
    print(f"# topology+receipt collections present: "
          f"{[c for c in cols if 'receipt' in c.lower() or 'edge' in c.lower()]}")

    total = await db.mirror_chat_retrieval_receipts.count_documents({})
    print(f"# mirror_chat_retrieval_receipts total = {total}")
    print()

    # Counters
    bucket_counter: Counter = Counter()
    framing_counter: Counter = Counter()
    domain_bias_counter: Counter = Counter()
    resolution_source_counter: Counter = Counter()
    topology_role_type_counter: Counter = Counter()
    replanned_counter: Counter = Counter()
    topology_role_found_counter: Counter = Counter()
    target_name_counter: Counter = Counter()
    unknown_role_token_events: List[Dict[str, Any]] = []
    self_fallback_with_target: List[Dict[str, Any]] = []
    samples_by_bucket: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    cur = db.mirror_chat_retrieval_receipts.find({}).sort([("_id", -1)])
    inspected = 0
    async for r in cur:
        inspected += 1
        rel = (r.get("relationship_resolution") or {}) if isinstance(
            r.get("relationship_resolution"), dict) else {}
        orch = (r.get("relationship_orchestration_v1") or {}) if isinstance(
            r.get("relationship_orchestration_v1"), dict) else {}

        bucket = orch.get("rule_bucket")
        framing = orch.get("framing_hint")
        domain_bias = orch.get("domain_bias")
        target = rel.get("target")
        target_name = rel.get("target_name")
        topology_role_found = rel.get("topology_role_found")
        topology_role_type = rel.get("topology_role_type")
        topology_confidence = rel.get("topology_confidence")
        resolution_source = rel.get("resolution_source")
        applied_rules = orch.get("applied_rules") or []
        replanned = orch.get("replanned_after_topology")

        bucket_counter[bucket or "(missing)"] += 1
        framing_counter[framing or "(missing)"] += 1
        domain_bias_counter[domain_bias or "(missing)"] += 1
        resolution_source_counter[resolution_source or "(missing)"] += 1
        if topology_role_type:
            topology_role_type_counter[topology_role_type] += 1
        topology_role_found_counter[str(topology_role_found)] += 1
        replanned_counter[str(replanned)] += 1
        if target_name:
            target_name_counter[target_name] += 1

        # Unknown role token telemetry
        for rule in applied_rules:
            if isinstance(rule, str) and rule.startswith(
                    "self:unknown_role_token:"):
                unknown_role_token_events.append({
                    "request_id":  r.get("request_id"),
                    "user_id":     r.get("user_id"),
                    "target_name": target_name,
                    "rule":        rule,
                    "topology_role_found": topology_role_found,
                })

        # Self fallback with bound target (resolver found target but
        # planner produced self bucket — lexicon gap candidates)
        if bucket == "self" and target:
            self_fallback_with_target.append({
                "request_id":     r.get("request_id"),
                "target_name":    target_name,
                "topology_role_type": topology_role_type,
                "resolution_source":  resolution_source,
                "applied_rules":  applied_rules,
            })

        # Sample collection
        if bucket and len(samples_by_bucket[bucket]) < SAMPLE_LIMIT:
            samples_by_bucket[bucket].append({
                "request_id":            r.get("request_id"),
                "user_id":               r.get("user_id"),
                "target_name":           target_name,
                "resolved_role":         rel.get("role"),
                "rule_bucket":           bucket,
                "framing_hint":          framing,
                "domain_bias":           domain_bias,
                "replanned_after_topology": replanned,
                "topology_role_found":   topology_role_found,
                "topology_role_type":    topology_role_type,
                "topology_confidence":   topology_confidence,
                "topology_inferred":     rel.get("topology_inferred"),
                "resolution_source":     resolution_source,
                "applied_rules":         applied_rules,
                "lens_priority_before":  orch.get("lens_priority_before"),
                "lens_priority_after":   orch.get("lens_priority_after"),
                "pre_topology_plan":     orch.get("pre_topology_plan"),
                "forum_name":            rel.get("forum_name"),
            })

    print(f"# receipts inspected: {inspected}")
    print()
    print("## bucket distribution")
    print(json.dumps(dict(bucket_counter), indent=2))
    print()
    print("## framing_hint distribution")
    print(json.dumps(dict(framing_counter), indent=2))
    print()
    print("## domain_bias distribution")
    print(json.dumps(dict(domain_bias_counter), indent=2))
    print()
    print("## resolution_source distribution")
    print(json.dumps(dict(resolution_source_counter), indent=2))
    print()
    print("## topology_role_type distribution")
    print(json.dumps(dict(topology_role_type_counter), indent=2))
    print()
    print("## topology_role_found distribution")
    print(json.dumps(dict(topology_role_found_counter), indent=2))
    print()
    print("## replanned_after_topology distribution")
    print(json.dumps(dict(replanned_counter), indent=2))
    print()
    print("## top target_name occurrences")
    print(json.dumps(dict(target_name_counter.most_common(15)), indent=2))
    print()
    print(f"## unknown_role_token events ({len(unknown_role_token_events)})")
    print(json.dumps(_jsonable(unknown_role_token_events[:20]),
                     indent=2, default=str))
    print()
    print(f"## self_fallback_with_bound_target ({len(self_fallback_with_target)})")
    print(json.dumps(_jsonable(self_fallback_with_target[:20]),
                     indent=2, default=str))
    print()
    print("## sample receipts per bucket")
    for bk, lst in samples_by_bucket.items():
        print(f"\n### bucket={bk} ({len(lst)} sample(s))")
        for s in lst:
            print(json.dumps(_jsonable(s), indent=2, default=str))

    # Topology graph health on the same DB
    print("\n## forum_relationship_edges health (this DB)")
    edges_total = await db.forum_relationship_edges.count_documents({})
    high_conf = await db.forum_relationship_edges.count_documents(
        {"confidence": "high"})
    explicit = await db.forum_relationship_edges.count_documents(
        {"inferred": False})
    role_types = await db.forum_relationship_edges.distinct("role_type")
    print(json.dumps({
        "edges_total":             edges_total,
        "high_confidence_edges":   high_conf,
        "explicit_edges":          explicit,
        "distinct_role_types":     role_types,
    }, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
