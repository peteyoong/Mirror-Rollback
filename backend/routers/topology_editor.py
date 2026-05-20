"""
Topology Editor v2 routes (server-router-refactor-v1 · topology-editor-v2)
==========================================================================

Extracted from server.py.  Behavior, paths, schemas, markers and log
lines are identical to the original inline implementation — this is
an infrastructure-only move.

Endpoints:

    POST   /api/forums/{forum_id}/topology/edge
    DELETE /api/forums/{forum_id}/topology/edge/{edge_id}/by/{user_id}
    GET    /api/forums/{forum_id}/topology/by/{user_id}
    GET    /api/forums/{forum_id}/topology/roles

Call `register(api_router, db, logger)` from `server.py` to attach
these routes.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


class TopologyEditorUpsert(BaseModel):
    """User-declared outbound edge from `from_user_id` → `to_user_id`."""
    from_user_id: str
    to_user_id: str
    role_type: str
    emotional_weight: Optional[str] = None
    power_gradient: Optional[str] = None
    intimacy_level: Optional[str] = None


def register(api_router: APIRouter, db, logger) -> None:
    """
    Attach the 4 topology-editor-v2 endpoints onto `api_router`.

    The signatures, response shapes and log lines below match the
    pre-refactor server.py implementation byte-for-byte.
    """

    @api_router.post("/forums/{forum_id}/topology/edge")
    async def topology_editor_upsert(forum_id: str, body: TopologyEditorUpsert):
        from services.forum_topology import upsert_edge, ALL_ROLES

        if not body.from_user_id or not body.to_user_id:
            raise HTTPException(status_code=400, detail="from_user_id and to_user_id are required")
        if body.from_user_id == body.to_user_id:
            raise HTTPException(status_code=400, detail="cannot declare an edge to yourself")
        if body.role_type not in ALL_ROLES:
            raise HTTPException(
                status_code=400,
                detail=f"unknown role_type; allowed: {sorted(list(ALL_ROLES))}",
            )

        member_ids: List[str] = []
        async for r in db.forum_members.find({"forum_id": forum_id}):
            uid = r.get("user_id")
            if uid:
                member_ids.append(str(uid))
        if body.from_user_id not in member_ids:
            raise HTTPException(
                status_code=403,
                detail="from_user_id is not a member of this forum",
            )
        if body.to_user_id not in member_ids:
            raise HTTPException(
                status_code=400,
                detail="to_user_id is not a member of this forum",
            )

        if body.emotional_weight and body.emotional_weight not in ("heavy", "moderate", "light"):
            raise HTTPException(status_code=400, detail="invalid emotional_weight")
        if body.power_gradient and body.power_gradient not in ("hard_hierarchy", "soft_hierarchy", "equal"):
            raise HTTPException(status_code=400, detail="invalid power_gradient")
        if body.intimacy_level and body.intimacy_level not in ("high", "medium", "low"):
            raise HTTPException(status_code=400, detail="invalid intimacy_level")

        edge = await upsert_edge(
            db,
            forum_id=forum_id,
            from_user_id=body.from_user_id,
            to_user_id=body.to_user_id,
            role_type=body.role_type,
            inferred=False,
            confidence="high",
            emotional_weight=body.emotional_weight,
            power_gradient=body.power_gradient,
            intimacy_level=body.intimacy_level,
        )
        for k in ("created_at", "updated_at"):
            if isinstance(edge.get(k), datetime):
                edge[k] = edge[k].isoformat()
        logger.info(
            f"[TOPOLOGY_EDITOR_V2] upsert forum={forum_id} "
            f"from={body.from_user_id} -> to={body.to_user_id} role={body.role_type}"
        )
        return {"ok": True, "edge": edge, "marker": "topology-editor-v2"}

    @api_router.delete("/forums/{forum_id}/topology/edge/{edge_id}/by/{user_id}")
    async def topology_editor_delete(forum_id: str, edge_id: str, user_id: str):
        from services.forum_topology import delete_edge
        edge = await db.forum_relationship_edges.find_one({"forum_id": forum_id, "id": edge_id})
        if not edge:
            raise HTTPException(status_code=404, detail="edge not found")
        if str(edge.get("from_user_id")) != str(user_id):
            raise HTTPException(
                status_code=403,
                detail="only the edge owner can delete this edge",
            )
        n = await delete_edge(db, forum_id=forum_id, edge_id=edge_id)
        logger.info(
            f"[TOPOLOGY_EDITOR_V2] delete forum={forum_id} edge={edge_id} by user={user_id}"
        )
        return {"ok": True, "deleted": n, "marker": "topology-editor-v2"}

    @api_router.get("/forums/{forum_id}/topology/by/{user_id}")
    async def topology_editor_list_for_user(forum_id: str, user_id: str):
        from services.forum_topology import list_edges
        edges = await list_edges(db, forum_id=forum_id)
        outbound = [e for e in edges if str(e.get("from_user_id")) == str(user_id)]
        inbound = [e for e in edges if str(e.get("to_user_id")) == str(user_id)]
        return {
            "marker": "topology-editor-v2",
            "forum_id": forum_id,
            "user_id": user_id,
            "outbound": outbound,
            "inbound": inbound,
            "all_roles": sorted(list({e.get("role_type") for e in edges if e.get("role_type")})),
        }

    @api_router.get("/forums/{forum_id}/topology/roles")
    async def topology_editor_roles(forum_id: str):
        from services.forum_topology import ALL_ROLES
        return {
            "marker": "topology-editor-v2",
            "roles": sorted(list(ALL_ROLES)),
        }
