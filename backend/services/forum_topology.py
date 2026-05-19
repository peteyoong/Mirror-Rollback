"""
Forum Topology  (forum-topology-and-timing-v1)
==============================================

Directional relational edges between forum members.  Used internally by
the field-synthesis engine to weight emotional gravity, power gradients
and intimacy distance.  NEVER exposed to users as a structured graph.

Collection: `forum_relationship_edges`
Schema (Mongo doc):
    {
        id, forum_id,
        from_user_id, to_user_id,
        role_type, directional: True,
        inferred: bool, confidence: "low" | "moderate" | "high",
        emotional_weight: "light" | "moderate" | "heavy",
        power_gradient: "equal" | "soft_hierarchy" | "hard_hierarchy",
        intimacy_level: "low" | "medium" | "high",
        created_at, updated_at
    }
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional


# Role catalog — three families.
FAMILY_ROLES = {
    "parent", "child", "sibling", "spouse", "former_partner",
}
PROFESSIONAL_ROLES = {
    "cofounder", "manager", "employee", "investor", "advisor",
    "mentor", "mentee", "coach", "coachee", "business_partner",
}
SOCIAL_ROLES = {
    "close_friend", "forum_mate", "authority_figure",
    "collaborator", "other",
}
ALL_ROLES = FAMILY_ROLES | PROFESSIONAL_ROLES | SOCIAL_ROLES


# Inverse-role pairing used when materialising both directions of an
# inferred relationship.  Keys map a role to its likely counterpart.
_INVERSE_ROLE: Dict[str, str] = {
    "parent": "child", "child": "parent",
    "mentor": "mentee", "mentee": "mentor",
    "coach": "coachee", "coachee": "coach",
    "manager": "employee", "employee": "manager",
    "spouse": "spouse", "sibling": "sibling",
    "cofounder": "cofounder", "former_partner": "former_partner",
    "investor": "advisor", "advisor": "investor",
    "business_partner": "business_partner",
    "close_friend": "close_friend",
    "forum_mate": "forum_mate",
    "authority_figure": "other",
    "collaborator": "collaborator",
    "other": "other",
}


# Role → (power_gradient, emotional_weight, intimacy_level) defaults
# for inference.  Used silently — never named.
_ROLE_PRESETS: Dict[str, Dict[str, str]] = {
    "spouse":           {"pg": "equal",            "ew": "heavy",    "il": "high"},
    "former_partner":   {"pg": "equal",            "ew": "moderate", "il": "high"},
    "parent":           {"pg": "hard_hierarchy",   "ew": "heavy",    "il": "high"},
    "child":            {"pg": "hard_hierarchy",   "ew": "heavy",    "il": "high"},
    "sibling":          {"pg": "equal",            "ew": "moderate", "il": "medium"},
    "cofounder":        {"pg": "equal",            "ew": "heavy",    "il": "medium"},
    "manager":          {"pg": "hard_hierarchy",   "ew": "moderate", "il": "medium"},
    "employee":         {"pg": "hard_hierarchy",   "ew": "moderate", "il": "medium"},
    "investor":         {"pg": "soft_hierarchy",   "ew": "moderate", "il": "low"},
    "advisor":          {"pg": "soft_hierarchy",   "ew": "light",    "il": "low"},
    "mentor":           {"pg": "soft_hierarchy",   "ew": "moderate", "il": "medium"},
    "mentee":           {"pg": "soft_hierarchy",   "ew": "moderate", "il": "medium"},
    "coach":            {"pg": "soft_hierarchy",   "ew": "moderate", "il": "medium"},
    "coachee":          {"pg": "soft_hierarchy",   "ew": "moderate", "il": "medium"},
    "business_partner": {"pg": "equal",            "ew": "moderate", "il": "medium"},
    "close_friend":     {"pg": "equal",            "ew": "moderate", "il": "high"},
    "forum_mate":       {"pg": "equal",            "ew": "light",    "il": "low"},
    "authority_figure": {"pg": "hard_hierarchy",   "ew": "moderate", "il": "low"},
    "collaborator":     {"pg": "equal",            "ew": "light",    "il": "low"},
    "other":            {"pg": "equal",            "ew": "light",    "il": "low"},
}


# Compatibility map: relationship_type stored on saved_people → role used
# by the topology layer.  Best-effort; unknown types map to "other".
_SAVED_PEOPLE_TO_ROLE: Dict[str, str] = {
    "spouse": "spouse", "partner": "spouse", "romantic_partner": "spouse",
    "ex_partner": "former_partner", "former_partner": "former_partner",
    "parent": "parent", "mother": "parent", "father": "parent",
    "child": "child", "son": "child", "daughter": "child",
    "child_minor": "child", "child_adult": "child",
    "sibling": "sibling", "brother": "sibling", "sister": "sibling",
    "friend": "close_friend", "close_friend": "close_friend",
    "best_friend": "close_friend",
    "boss": "manager", "manager": "manager",
    "direct_report": "employee", "employee": "employee",
    "cofounder": "cofounder", "business_partner": "business_partner",
    "mentor": "mentor", "mentee": "mentee",
    "coach": "coach", "client": "coachee",
    "investor": "investor", "advisor": "advisor",
    "colleague": "collaborator", "collaborator": "collaborator",
    "forum_mate": "forum_mate", "forum_member": "forum_mate",
    "authority": "authority_figure", "professional": "collaborator",
    "other": "other",
}


def role_for_relationship_type(rel_type: Optional[str]) -> str:
    if not rel_type:
        return "other"
    return _SAVED_PEOPLE_TO_ROLE.get(rel_type.strip().lower(), "other")


# --------------------------------------------------------------------------
# Edge CRUD
# --------------------------------------------------------------------------


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def upsert_edge(
    db,
    *,
    forum_id: str,
    from_user_id: str,
    to_user_id: str,
    role_type: str,
    inferred: bool = False,
    confidence: str = "moderate",
    emotional_weight: Optional[str] = None,
    power_gradient: Optional[str] = None,
    intimacy_level: Optional[str] = None,
) -> Dict[str, Any]:
    """Insert or update an edge.  Returns the stored doc."""
    if role_type not in ALL_ROLES:
        role_type = "other"
    preset = _ROLE_PRESETS.get(role_type, _ROLE_PRESETS["other"])
    doc = {
        "forum_id": forum_id,
        "from_user_id": from_user_id,
        "to_user_id": to_user_id,
        "role_type": role_type,
        "directional": True,
        "inferred": bool(inferred),
        "confidence": confidence if confidence in ("low", "moderate", "high") else "moderate",
        "emotional_weight": emotional_weight or preset["ew"],
        "power_gradient": power_gradient or preset["pg"],
        "intimacy_level": intimacy_level or preset["il"],
        "updated_at": _now(),
    }
    existing = await db.forum_relationship_edges.find_one({
        "forum_id": forum_id,
        "from_user_id": from_user_id,
        "to_user_id": to_user_id,
        "role_type": role_type,
    })
    if existing:
        await db.forum_relationship_edges.update_one(
            {"_id": existing["_id"]}, {"$set": doc},
        )
        doc["id"] = existing.get("id") or str(existing["_id"])
        doc["created_at"] = existing.get("created_at", _now())
    else:
        doc["id"] = str(uuid.uuid4())
        doc["created_at"] = _now()
        await db.forum_relationship_edges.insert_one(dict(doc))
    return doc


async def list_edges(db, *, forum_id: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    cursor = db.forum_relationship_edges.find({"forum_id": forum_id})
    async for row in cursor:
        row.pop("_id", None)
        for k in ("created_at", "updated_at"):
            if isinstance(row.get(k), datetime):
                row[k] = row[k].isoformat()
        out.append(row)
    return out


async def delete_edge(db, *, forum_id: str, edge_id: str) -> int:
    res = await db.forum_relationship_edges.delete_one({
        "forum_id": forum_id, "id": edge_id,
    })
    return int(res.deleted_count or 0)


# --------------------------------------------------------------------------
# Auto-inference
# --------------------------------------------------------------------------


async def _forum_member_user_ids(db, forum_id: str) -> List[str]:
    rows = db.forum_members.find({"forum_id": forum_id})
    ids: List[str] = []
    async for r in rows:
        uid = r.get("user_id")
        if uid:
            ids.append(str(uid))
    return ids


async def infer_forum_topology_edges(db, *, forum_id: str) -> Dict[str, Any]:
    """
    Walk forum members.  For each member, look at their saved_people docs.
    Where a saved_person matches another forum member (by display name
    or user_id), infer an edge.  Always also materialise an inverse edge
    via _INVERSE_ROLE.  Idempotent — uses upsert_edge.
    """
    members = await _forum_member_user_ids(db, forum_id)
    if len(members) < 2:
        return {
            "marker": "forum-topology-and-timing-v1",
            "members_count": len(members),
            "inferred_count": 0,
            "edges": [],
        }

    # Build (lower-cased) name → user_id map for the forum members so we
    # can cross-reference saved_people docs by name when no user_id link
    # is present.
    name_to_uid: Dict[str, str] = {}
    for uid in members:
        user = await db.users.find_one({"id": uid}) or await db.users.find_one({"_id": uid})
        if user:
            nm = (user.get("name") or user.get("display_name") or "").strip().lower()
            if nm:
                name_to_uid[nm] = uid

    inferred = 0
    inferred_edges: List[Dict[str, Any]] = []
    for from_uid in members:
        cursor = db.saved_people.find({"user_id": from_uid})
        async for sp in cursor:
            target_name = (sp.get("name") or "").strip().lower()
            target_uid = name_to_uid.get(target_name)
            if not target_uid or target_uid == from_uid:
                continue
            role = role_for_relationship_type(sp.get("relationship_type"))
            edge = await upsert_edge(
                db,
                forum_id=forum_id,
                from_user_id=from_uid,
                to_user_id=target_uid,
                role_type=role,
                inferred=True,
                confidence="moderate" if role != "other" else "low",
            )
            inferred += 1
            inferred_edges.append(edge)
            # Materialise inverse direction too.
            inv = _INVERSE_ROLE.get(role, "other")
            await upsert_edge(
                db,
                forum_id=forum_id,
                from_user_id=target_uid,
                to_user_id=from_uid,
                role_type=inv,
                inferred=True,
                confidence="low",
            )
            inferred += 1

    return {
        "marker": "forum-topology-and-timing-v1",
        "members_count": len(members),
        "inferred_count": inferred,
    }


# --------------------------------------------------------------------------
# Topology confidence + stability — INTERNAL ONLY
# --------------------------------------------------------------------------


async def get_topology_confidence_state(
    db, *, forum_id: str,
) -> Dict[str, Any]:
    """
    Returns: one of "none" | "sparse" | "emerging" | "stable", plus the
    raw counts for debug.  Used to scale the assertiveness of the field
    synthesis.
    """
    members = await _forum_member_user_ids(db, forum_id)
    edges = await list_edges(db, forum_id=forum_id)
    n_members = len(members)
    n_edges = len(edges)
    high_conf = sum(1 for e in edges if e.get("confidence") == "high")
    family_or_heavy = sum(
        1 for e in edges
        if e.get("role_type") in FAMILY_ROLES
        or e.get("emotional_weight") == "heavy"
    )

    state: str
    if n_members < 2 or n_edges == 0:
        state = "none"
    elif n_edges < max(2, n_members // 2):
        state = "sparse"
    elif high_conf >= 2 or family_or_heavy >= 2 or n_edges >= n_members:
        state = "stable"
    else:
        state = "emerging"

    return {
        "state": state,
        "members": n_members,
        "edges": n_edges,
        "high_confidence_edges": high_conf,
        "heavy_or_family_edges": family_or_heavy,
    }


async def compute_field_stability_score(
    db, *, forum_id: str,
) -> Dict[str, Any]:
    """
    Internal-only.  Composite of topology density, recurrence
    consistency, participation continuity, reflection continuity.
    Returns a small numeric score (0-1) plus contributing factors.
    Never surfaced to users.
    """
    topo = await get_topology_confidence_state(db, forum_id=forum_id)
    # Density: edges per member, capped at 1.
    members = max(1, topo["members"])
    density = min(1.0, topo["edges"] / (members * 1.5))

    # Recurrence consistency — peek at pattern memory by member.
    pat_recurring = 0
    member_ids = await _forum_member_user_ids(db, forum_id)
    for uid in member_ids[:8]:  # cap for cost
        try:
            cnt = await db.longitudinal_pattern_memory.count_documents({
                "user_id": uid,
                "occurrence_count": {"$gte": 3},
            })
            pat_recurring += int(cnt or 0)
        except Exception:
            pass
    recurrence_score = min(1.0, pat_recurring / max(1, len(member_ids) * 2))

    # Reflection continuity — micro-reflection presence anywhere.
    refl_count = 0
    try:
        refl_count = await db.micro_reflections.count_documents({
            "user_id": {"$in": member_ids}
        }) if member_ids else 0
    except Exception:
        refl_count = 0
    reflection_score = min(1.0, refl_count / max(1, len(member_ids) * 3))

    composite = round(0.5 * density + 0.3 * recurrence_score + 0.2 * reflection_score, 3)
    return {
        "score": composite,
        "topology_density": round(density, 3),
        "recurrence_score": round(recurrence_score, 3),
        "reflection_score": round(reflection_score, 3),
    }
