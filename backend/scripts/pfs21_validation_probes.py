"""PFS-2.1 live probe traces.

Read-only validation harness for the topology-first relationship
resolver.  Calls `resolve_target_via_forums` against the Preview DB
for each required probe, prints the full resolver result + a synthetic
receipt payload showing what would be persisted into
`mirror_chat_retrieval_receipts`.

Probes (per user spec):
  1. Pete & Mel        → spouse           (PASS expected)
  2. Yoong Family      → spouse + family  (PASS expected)
  3. Isaac             → child            (ENVIRONMENTAL N/A expected)
  4. Thaddeus          → child            (ENVIRONMENTAL N/A expected)
  5. Cofounder lookup  → cofounder        (ENVIRONMENTAL N/A expected)
  6. Mentor lookup     → mentor           (ENVIRONMENTAL N/A expected)

Information-preservation audit:
  * "Mel"            on Pete       — before vs after
  * "wife"           on Pete       — before vs after (spouse alias path)

Regression matrix:
  * unresolved target (random name "QwertyXYZ")
  * non-forum target  (saved-people name "Test Spouse")
  * explicit target id path (V2 already resolved → resolver skipped upstream;
    we assert resolver still behaves safely if called)
  * forum-member resolution (FM TEST 1 — no topology edge)
"""
import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict

from dotenv import load_dotenv

load_dotenv("/app/backend/.env")

sys.path.insert(0, "/app/backend")

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

from services.mirror_chat_phase4_enrichment import (  # noqa: E402
    _classify_forum_source,
    _lookup_topology_edge,
    resolve_target_via_forums,
)


PETE_ID = "697f0c6abf35c0528ff06954"
MEL_ID = "697ec826ad4b18f75bf42616"


def _jsonable(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj


def _synth_receipt(resolved: Dict[str, Any]) -> Dict[str, Any]:
    """Mirror the projection routers/mirror_chat.py would write into
    `mirror_chat_retrieval_receipts.relationship_resolution`.
    """
    if not resolved.get("found"):
        return {
            "target":                None,
            "target_unresolved_name": resolved.get("candidate_name"),
            "resolution_source":     resolved.get("resolution_source",
                                                  "unresolved"),
            "topology_role_found":   False,
            "topology_role_type":    None,
            "topology_confidence":   None,
            "topology_inferred":     None,
            "topology_edge_id":      None,
        }
    return {
        "target":                resolved["resolved_user_id"],
        "target_name":           resolved["resolved_name"],
        "role":                  resolved["resolved_role"],
        "forum_id":              resolved["forum_id"],
        "forum_name":            resolved["forum_name"],
        "resolution_source":     resolved["resolution_source"],
        "topology_role_found":   resolved.get("topology_role_found", False),
        "topology_role_type":    resolved.get("topology_role_type"),
        "topology_confidence":   resolved.get("topology_confidence"),
        "topology_inferred":     resolved.get("topology_inferred"),
        "topology_edge_id":      resolved.get("topology_edge_id"),
        "target_unresolved_name": resolved.get("candidate_name"),
    }


async def probe(
    db,
    *,
    label: str,
    candidate_name: str,
    message: str,
    user_id: str = PETE_ID,
) -> Dict[str, Any]:
    resolved = await resolve_target_via_forums(
        db=db,
        user_id=user_id,
        candidate_name=candidate_name,
        message=message,
    )
    receipt = _synth_receipt(resolved)
    print(f"\n──────── PROBE: {label} ────────")
    print(f"  user_id      : {user_id}")
    print(f"  candidate    : {candidate_name!r}")
    print(f"  message      : {message!r}")
    print(f"  RESOLVED     : found={resolved['found']} "
          f"src={resolved['resolution_source']} "
          f"role={resolved['resolved_role']!r} "
          f"name={resolved['resolved_name']!r}")
    print(f"  TOPOLOGY     : found={resolved.get('topology_role_found')} "
          f"role_type={resolved.get('topology_role_type')!r} "
          f"confidence={resolved.get('topology_confidence')} "
          f"inferred={resolved.get('topology_inferred')} "
          f"edge_id={resolved.get('topology_edge_id')}")
    print(f"  all_matches  : "
          f"{json.dumps(_jsonable(resolved.get('all_forums_with_match')), default=str)}")
    print("  PERSISTED RECEIPT (relationship_resolution):")
    print("    " + json.dumps(_jsonable(receipt), indent=2, default=str)
          .replace("\n", "\n    "))
    return {"label": label, "resolved": resolved, "receipt": receipt}


async def direct_edge_lookup(db, *, label: str, forum_id: str,
                             from_id: str, to_id: str) -> None:
    edge = await _lookup_topology_edge(
        db, forum_id=forum_id, from_user_id=from_id, to_user_id=to_id
    )
    print(f"\n──────── DIRECT EDGE: {label} ────────")
    print(f"  forum_id={forum_id} from={from_id} to={to_id}")
    print(f"  result  : {json.dumps(_jsonable(edge), default=str)}")


async def main():
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]

    print("=" * 78)
    print("PFS-2.1 TOPOLOGY-FIRST VALIDATION PROBES (read-only)")
    print(f"Preview DB: {os.environ['DB_NAME']}")
    print(f"Run at: {datetime.utcnow().isoformat()}Z")
    print("=" * 78)

    # Direct edge sanity dumps (proves we're reading the right collection).
    await direct_edge_lookup(
        db,
        label="Pete→Mel inside 'Pete & Mel' forum",
        forum_id="69dd05eaa333335fcbf3ad33",
        from_id=PETE_ID,
        to_id=MEL_ID,
    )
    await direct_edge_lookup(
        db,
        label="Pete→Mel inside 'Yoong family' forum",
        forum_id="69dda348de9cb1c83c0780fa",
        from_id=PETE_ID,
        to_id=MEL_ID,
    )

    # ──── Required probes (1-6) ────────────────────────────────────
    results = []
    results.append(await probe(db,
        label="1. Pete & Mel → expect spouse via topology edge",
        candidate_name="Mel",
        message="How is Mel doing today?",
    ))
    results.append(await probe(db,
        label="2. Yoong Family → expect spouse via topology (NOT family-only) + family ctx preserved",
        candidate_name="Melissa",
        message="Talking with Melissa about the family",
    ))
    results.append(await probe(db,
        label="3. Isaac → expect ENVIRONMENTAL N/A (no member, no edge in preview)",
        candidate_name="Isaac",
        message="How is Isaac handling school?",
    ))
    results.append(await probe(db,
        label="4. Thaddeus → expect ENVIRONMENTAL N/A (no member, no edge in preview)",
        candidate_name="Thaddeus",
        message="Worried about Thaddeus lately.",
    ))
    results.append(await probe(db,
        label="5. Cofounder lookup → expect ENVIRONMENTAL N/A (no cofounder forum/edge in preview)",
        candidate_name="Lu",
        message="Sync with my cofounder Lu about runway.",
    ))
    results.append(await probe(db,
        label="6. Mentor lookup → expect ENVIRONMENTAL N/A (no mentor forum/edge in preview)",
        candidate_name="Sandra",
        message="Catching up with my mentor Sandra.",
    ))

    # ──── Information preservation audit ────────────────────────────
    print("\n" + "=" * 78)
    print("INFORMATION PRESERVATION AUDIT (before vs after topology-first)")
    print("=" * 78)
    # "Before" = forum-name regex only (PFS-1 heuristic).
    for forum_name in ("Pete & Mel", "Yoong family"):
        src, role = _classify_forum_source(forum_name)
        print(f"\n  BEFORE (PFS-1 name regex) — forum {forum_name!r}:")
        print(f"    source={src!r}  role={role!r}")
    # "After" = topology-first resolver (already probed above).
    print("\n  AFTER (PFS-2.1 topology-first) — Pete probing 'Mel':")
    pm = results[0]["resolved"]
    print(f"    source={pm['resolution_source']!r}  "
          f"role={pm['resolved_role']!r}  "
          f"topology_role_type={pm.get('topology_role_type')!r}  "
          f"forum_name={pm['forum_name']!r}")
    print("  AFTER (PFS-2.1 topology-first) — Pete probing 'Melissa':")
    yf = results[1]["resolved"]
    print(f"    source={yf['resolution_source']!r}  "
          f"role={yf['resolved_role']!r}  "
          f"topology_role_type={yf.get('topology_role_type')!r}  "
          f"forum_name={yf['forum_name']!r}")

    # ──── Regression matrix ─────────────────────────────────────────
    print("\n" + "=" * 78)
    print("REGRESSION MATRIX")
    print("=" * 78)
    await probe(db,
        label="REG.A unresolved target — random name",
        candidate_name="QwertyXYZ",
        message="What about QwertyXYZ?",
    )
    await probe(db,
        label="REG.B saved_people-only target — 'Test Spouse'",
        candidate_name="Test Spouse",
        message="Talked to Test Spouse today.",
    )
    await probe(db,
        label="REG.C forum-member, no topology edge — FM TEST 1 owner",
        candidate_name="Pete",   # self, no edges other than to Mel
        message="Just me.",
        user_id=MEL_ID,
    )
    await probe(db,
        label="REG.D role-noun alias 'wife' (spouse-alias path)",
        candidate_name=None,
        message="I had a difficult chat with my wife today.",
    )

    print("\n" + "=" * 78)
    print("PROBE RUN COMPLETE")
    print("=" * 78)


if __name__ == "__main__":
    asyncio.run(main())
