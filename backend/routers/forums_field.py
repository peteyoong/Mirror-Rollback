"""
Forum Field routes  (server-router-refactor-v2)
================================================

Extracted from server.py.  Behavior, paths, schemas, markers and log
lines are byte-identical to the original inline implementation.

Endpoints attached here:

  POST   /api/admin/forums/{forum_id}/seed-topology-edge        forum-topology-and-timing-v1
  POST   /api/forums/{forum_id}/topology/infer                  forum-topology-and-timing-v1
  GET    /api/forums/{forum_id}/topology                        forum-topology-and-timing-v1
  DELETE /api/forums/{forum_id}/topology/edge/{edge_id}         forum-topology-and-timing-v1
  GET    /api/forums/{forum_id}/story-of-circle                 forum-topology-and-timing-v1
  POST   /api/forums/{forum_id}/mirror-chat                     forum-conversational-field-v1
  GET    /api/forums/{forum_id}/mirror-chat/history             forum-conversational-field-v1

NOT extracted (left in server.py because they are deeply coupled to
the giant /api/forums/{id}/chat business logic): forum CRUD, member
listing, exercise, contributions, dynamics, pulse, live-field,
member-lens, pattern-map, etc.

Call signature:

  forums_field.register(api_router, db, logger,
                        check_rate_limit_fn, emergent_llm_key)

`check_rate_limit_fn` is the existing server.py function so the
rate-limit window stays shared with the rest of the app.
"""

from __future__ import annotations

import os
import time as _time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


class ForumTopologySeedEdge(BaseModel):
    """Admin/test endpoint payload for deterministic edge seeding."""
    from_user_id: str
    to_user_id: str
    role_type: str
    confidence: Optional[str] = "moderate"
    emotional_weight: Optional[str] = None
    power_gradient: Optional[str] = None
    intimacy_level: Optional[str] = None


class ForumMirrorChatRequest(BaseModel):
    user_id: str
    forum_id: str
    message: str
    session_id: Optional[str] = None
    include_history: bool = True


class ForumMirrorChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: str
    debug: Optional[dict] = None
    evidence: Optional[dict] = None


def register(
    api_router: APIRouter,
    db,
    logger,
    check_rate_limit_fn,
    emergent_llm_key: Optional[str],
) -> None:
    """Attach all forum-field routes to `api_router`."""

    # ──────────────────────────────────────────────────────────────────
    # Admin / topology infrastructure
    # ──────────────────────────────────────────────────────────────────

    @api_router.post("/admin/forums/{forum_id}/seed-topology-edge")
    async def admin_seed_topology_edge(forum_id: str, body: ForumTopologySeedEdge):
        from services.forum_topology import upsert_edge, ALL_ROLES
        role = body.role_type if body.role_type in ALL_ROLES else "other"
        edge = await upsert_edge(
            db,
            forum_id=forum_id,
            from_user_id=body.from_user_id,
            to_user_id=body.to_user_id,
            role_type=role,
            inferred=False,
            confidence=body.confidence or "moderate",
            emotional_weight=body.emotional_weight,
            power_gradient=body.power_gradient,
            intimacy_level=body.intimacy_level,
        )
        for k in ("created_at", "updated_at"):
            if isinstance(edge.get(k), datetime):
                edge[k] = edge[k].isoformat()
        logger.info(
            f"[FORUM_TOPOLOGY] seed edge forum={forum_id} "
            f"from={body.from_user_id} -> to={body.to_user_id} role={role}"
        )
        return {"ok": True, "edge": edge, "marker": "forum-topology-and-timing-v1"}

    @api_router.post("/forums/{forum_id}/topology/infer")
    async def forum_topology_infer(forum_id: str):
        from services.forum_topology import infer_forum_topology_edges
        result = await infer_forum_topology_edges(db, forum_id=forum_id)
        logger.info(
            f"[FORUM_TOPOLOGY] infer forum={forum_id} "
            f"members={result.get('members_count')} inferred={result.get('inferred_count')}"
        )
        return result

    @api_router.get("/forums/{forum_id}/topology")
    async def forum_topology_list(forum_id: str):
        from services.forum_topology import (
            list_edges, get_topology_confidence_state, compute_field_stability_score,
        )
        edges = await list_edges(db, forum_id=forum_id)
        confidence = await get_topology_confidence_state(db, forum_id=forum_id)
        stability = await compute_field_stability_score(db, forum_id=forum_id)
        return {
            "marker": "forum-topology-and-timing-v1",
            "forum_id": forum_id,
            "edges": edges,
            "confidence": confidence,
            "field_stability": stability,
        }

    @api_router.delete("/forums/{forum_id}/topology/edge/{edge_id}")
    async def forum_topology_delete_edge(forum_id: str, edge_id: str):
        from services.forum_topology import delete_edge
        n = await delete_edge(db, forum_id=forum_id, edge_id=edge_id)
        return {"ok": True, "deleted": n, "marker": "forum-topology-and-timing-v1"}

    # ──────────────────────────────────────────────────────────────────
    # Story of This Circle
    # ──────────────────────────────────────────────────────────────────

    @api_router.get("/forums/{forum_id}/story-of-circle")
    async def forum_story_of_circle(forum_id: str, debug: bool = False):
        from services.forum_field_intelligence import compose_story_of_circle
        result = await compose_story_of_circle(db, forum_id=forum_id)
        story = result["story"]
        logger.info(
            f"[FORUM_FIELD] forum={forum_id} ready={story.get('ready')} "
            f"chips={story.get('field_state_chips')} "
            f"confidence={result['debug'].get('topology_confidence')}"
        )
        out = {"story": story, "marker": "forum-topology-and-timing-v1"}
        if debug:
            out["debug"] = {"forum_field": result["debug"]}
        return out

    # ──────────────────────────────────────────────────────────────────
    # Forum Conversational Field — mirror-chat
    # ──────────────────────────────────────────────────────────────────

    @api_router.post(
        "/forums/{forum_id}/mirror-chat",
        response_model=ForumMirrorChatResponse,
    )
    async def forum_mirror_chat(forum_id: str, request: ForumMirrorChatRequest):
        started_at = _time.time()
        request.forum_id = forum_id

        # EMERGENT_LLM_KEY may have changed since the router was
        # registered (env reload).  Re-read at call-time to be safe but
        # fall back to the value captured at registration.
        llm_key = os.environ.get("EMERGENT_LLM_KEY") or emergent_llm_key
        if not llm_key:
            logger.error("[FORUM_MIRROR_CHAT] EMERGENT_LLM_KEY missing")
            raise HTTPException(status_code=500, detail="AI service not configured")

        if not (request.message or "").strip():
            raise HTTPException(status_code=400, detail="message is required")

        session_id = request.session_id or str(uuid.uuid4())

        try:
            if not check_rate_limit_fn(request.user_id, False):
                raise HTTPException(
                    status_code=429,
                    detail="The room needs a pause. Try again shortly.",
                )
        except HTTPException:
            raise
        except Exception:
            pass

        try:
            from services.forum_topology import infer_forum_topology_edges
            await infer_forum_topology_edges(db, forum_id=forum_id)
        except Exception:
            pass

        try:
            from services.forum_conversational_field import compose_forum_field_prompt
            system_prompt, ff_debug, ff_evidence = await compose_forum_field_prompt(
                db, forum_id=forum_id, user_id=request.user_id,
                user_message=request.message,
            )
        except Exception as e:
            logger.error(
                f"[FORUM_MIRROR_CHAT] compose error: {type(e).__name__}: {e}"
            )
            raise HTTPException(
                status_code=500,
                detail="The room couldn't be read just now.",
            )

        history_text = ""
        if request.include_history:
            try:
                cursor = db.forum_mirror_chat_messages.find(
                    {"user_id": request.user_id, "forum_id": forum_id}
                ).sort("ts", -1).limit(10)
                history_rows = []
                async for r in cursor:
                    history_rows.append(r)
                history_rows.reverse()
                lines: List[str] = []
                for r in history_rows:
                    role = (r.get("role") or "").upper()
                    content = (r.get("content") or "").strip()
                    if role and content:
                        lines.append(f"{role}: {content}")
                if lines:
                    history_text = "\n".join(lines)
            except Exception:
                history_text = ""

        response_text: str = ""
        try:
            # ── ADVANCED-OBJECT-RESOLVER-V1 ─────────────────────────────
            # Same shared resolver as /api/mirror/chat and
            # /api/forums/{id}/chat.  Frame is treated as SELF for this
            # forum-mirror-chat surface (no target_member_id in the
            # request payload) — the orchestrator already injects
            # forum-context evidence; the resolver only adds Mirror-voiced
            # natal-object proof blocks when the message names one.
            try:
                from services.advanced_object_resolver import (
                    resolve_advanced_object, FRAME_SELF,
                )
                _self_chart = await db.charts.find_one(
                    {"user_id": request.user_id},
                    sort=[("created_at", -1)],
                )
                _resolved = resolve_advanced_object(
                    query=request.message,
                    self_chart=_self_chart,
                    target_chart=None,
                    frame=FRAME_SELF,
                    self_name="you",
                    target_name=None,
                    route_tag="forums_mirror_chat",
                )
                if _resolved.get("matched") and _resolved.get("proof_block"):
                    system_prompt += "\n\n" + _resolved["proof_block"]
                    logger.info(
                        f"[ForumMirrorChat][AdvObjResolver] matched=True "
                        f"mode={_resolved.get('mode')} "
                        f"objects={_resolved.get('objects')} "
                        f"axis={_resolved.get('axis')}"
                    )
            except Exception as _aor_err:
                logger.warning(
                    f"[ForumMirrorChat][AdvObjResolver] soft-failed: "
                    f"{type(_aor_err).__name__}: {_aor_err!r}"
                )

            from emergent_contract import emergent_generate
            from llm_model_config import get_primary_model
            context_blob: Dict[str, Any] = {"forum_id": forum_id}
            if history_text:
                context_blob["conversation_history"] = history_text
            response_text = await emergent_generate(
                mode="reflection_chat",
                user_message=request.message,
                endpoint="forum_mirror_chat",
                user_id=request.user_id,
                context=context_blob,
                additional_system_prompt=system_prompt,
                model=get_primary_model(),
            )
        except Exception as e:
            logger.error(
                f"[FORUM_MIRROR_CHAT] LLM error: {type(e).__name__}: {e}"
            )
            response_text = (
                "The room felt a little quiet just now — try once more in a "
                "moment."
            )

        try:
            now_ts = datetime.now(timezone.utc)
            await db.forum_mirror_chat_messages.insert_many([
                {
                    "id": str(uuid.uuid4()),
                    "user_id": request.user_id,
                    "forum_id": forum_id,
                    "session_id": session_id,
                    "role": "user",
                    "content": request.message,
                    "ts": now_ts,
                },
                {
                    "id": str(uuid.uuid4()),
                    "user_id": request.user_id,
                    "forum_id": forum_id,
                    "session_id": session_id,
                    "role": "assistant",
                    "content": response_text,
                    "ts": now_ts + timedelta(milliseconds=1),
                },
            ])
        except Exception as e:
            logger.error(
                f"[FORUM_MIRROR_CHAT] persist error: {type(e).__name__}: {e}"
            )

        duration = _time.time() - started_at
        logger.info(
            f"[FORUM_MIRROR_CHAT][forum-conversational-field-v1] "
            f"user={request.user_id} forum={forum_id} "
            f"story_ready={ff_debug.get('story_ready')} "
            f"contra_forum_level={(ff_debug.get('contradictions') or {}).get('forum',{}).get('contradiction_level')} "
            f"contra_individual_level={(ff_debug.get('contradictions') or {}).get('individual',{}).get('contradiction_level')} "
            f"duration={duration:.2f}s"
        )

        return ForumMirrorChatResponse(
            response=response_text,
            session_id=session_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            debug={"marker": "forum-conversational-field-v1", **ff_debug},
            evidence=ff_evidence,
        )

    @api_router.get("/forums/{forum_id}/mirror-chat/history")
    async def forum_mirror_chat_history(
        forum_id: str,
        user_id: str,
        limit: int = 50,
    ):
        try:
            cursor = db.forum_mirror_chat_messages.find(
                {"user_id": user_id, "forum_id": forum_id}
            ).sort("ts", -1).limit(max(1, min(int(limit), 200)))
            rows: List[Dict[str, Any]] = []
            async for r in cursor:
                r.pop("_id", None)
                ts = r.get("ts")
                if isinstance(ts, datetime):
                    r["ts"] = ts.isoformat()
                rows.append(r)
            rows.reverse()
            return {
                "marker": "forum-conversational-field-v1",
                "forum_id": forum_id,
                "user_id": user_id,
                "messages": rows,
            }
        except Exception as e:
            logger.error(
                f"[FORUM_MIRROR_CHAT] history error: {type(e).__name__}: {e}"
            )
            return {
                "marker": "forum-conversational-field-v1",
                "forum_id": forum_id,
                "user_id": user_id,
                "messages": [],
            }
