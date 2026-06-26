"""
Admin: read-only user lookup by name or email.
==============================================
Surface: GET /api/admin/find_user
Auth: required `confirm` token (matches the pattern used by other admin
read-only forensic endpoints in this codebase).

Searches the following collections for any record whose name/display_name/
email matches (case-insensitive regex):
  * db.users
  * db.forum_members
  * db.saved_people
  * db.charts        (when a name field has been denormalized into chart)

Returns a single JSON payload listing every match with the chart_id (when
known) so the operator can paste a `user_id` into the audit_chart
endpoint to dump the full chart. NO writes are performed.

Build marker: find-user-readonly-v1
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/admin", tags=["find-user-readonly-v1"])
logger = logging.getLogger(__name__)

CONFIRM_TOKEN = "FIND_USER_READONLY_2026_06_26"


def _stringify_id(d: Dict[str, Any]) -> Dict[str, Any]:
    """Convert ObjectId to str for JSON serialization, recursively shallow."""
    out: Dict[str, Any] = {}
    for k, v in d.items():
        if k == "_id":
            out["_id"] = str(v)
        elif hasattr(v, "isoformat"):
            out[k] = v.isoformat()
        elif isinstance(v, dict):
            out[k] = {kk: (str(vv) if kk == "_id" else (vv.isoformat() if hasattr(vv, "isoformat") else vv))
                      for kk, vv in v.items()
                      if not isinstance(vv, (bytes,))}
        elif isinstance(v, (str, int, float, bool, type(None), list)):
            out[k] = v
    return out


@router.get("/find_user")
async def find_user(
    name: Optional[str] = None,
    email: Optional[str] = None,
    confirm: str = "",
):
    """Read-only name/email lookup across users + forum_members + saved_people + charts.

    Query params:
      name     case-insensitive partial match against name / display_name / full_name
      email    case-insensitive exact match against email
      confirm  must equal CONFIRM_TOKEN

    Returns a JSON list of matches, each shaped:
      {
        "collection": "users" | "forum_members" | "saved_people" | "charts",
        "_id":        <hex string>,
        "user_id":    <string or null>,
        "name":       <display name>,
        "email":      <email if any>,
        "forum_id":   <forum id if any>,
        "chart_present": <bool>,
        "chart_id":   <hex string or null>,
        "chart_calculated_at": <iso8601 or null>,
        "engine_version":     <string or null>,
        "migration_marker":   <string or null>
      }
    """
    if confirm != CONFIRM_TOKEN:
        raise HTTPException(status_code=403, detail="confirm token required (read-only audit endpoint)")
    if not name and not email:
        raise HTTPException(status_code=400, detail="provide either ?name=… or ?email=…")

    from server import db  # avoid circular import at module load

    matches: List[Dict[str, Any]] = []

    name_re = re.compile(re.escape(name), re.IGNORECASE) if name else None
    email_norm = (email or "").strip().lower() or None

    async def _add_chart_meta(record: Dict[str, Any], uid: Optional[str]) -> None:
        record["chart_present"] = False
        record["chart_id"] = None
        record["chart_calculated_at"] = None
        record["engine_version"] = None
        record["migration_marker"] = None
        if not uid:
            return
        chart = await db.charts.find_one({"user_id": uid})
        if chart:
            record["chart_present"] = True
            record["chart_id"] = str(chart.get("_id"))
            ca = chart.get("calculated_at") or chart.get("updated_at")
            record["chart_calculated_at"] = ca.isoformat() if hasattr(ca, "isoformat") else (str(ca) if ca else None)
            astro = chart.get("astrology") or {}
            record["engine_version"] = astro.get("astrology_engine_version")
            record["migration_marker"] = astro.get("migration_marker") or (astro.get("metadata") or {}).get("migration_marker")

    # ---- users ----
    user_query: Dict[str, Any] = {}
    or_clauses: List[Dict[str, Any]] = []
    if name_re:
        or_clauses.append({"name": name_re})
        or_clauses.append({"display_name": name_re})
        or_clauses.append({"full_name": name_re})
    if email_norm:
        or_clauses.append({"email": email_norm})
    if or_clauses:
        user_query["$or"] = or_clauses
    async for u in db.users.find(user_query).limit(50):
        uid = str(u.get("_id"))
        rec = {
            "collection": "users",
            "_id": uid,
            "user_id": uid,
            "name": u.get("name") or u.get("display_name") or u.get("full_name"),
            "email": u.get("email"),
            "forum_id": None,
            "birth_date": str(u.get("birth_date")) if u.get("birth_date") else None,
            "birth_time": u.get("birth_time"),
            "city": u.get("city"),
            "country": u.get("country"),
            "created_at": u.get("created_at").isoformat() if hasattr(u.get("created_at"), "isoformat") else None,
        }
        await _add_chart_meta(rec, uid)
        matches.append(rec)

    # ---- forum_members ----
    fm_or: List[Dict[str, Any]] = []
    if name_re:
        fm_or.append({"name": name_re})
        fm_or.append({"display_name": name_re})
    if email_norm:
        fm_or.append({"email": email_norm})
    if fm_or:
        async for m in db.forum_members.find({"$or": fm_or}).limit(50):
            uid = m.get("user_id")
            rec = {
                "collection": "forum_members",
                "_id": str(m.get("_id")),
                "user_id": uid,
                "name": m.get("name") or m.get("display_name"),
                "email": m.get("email"),
                "forum_id": m.get("forum_id"),
                "role": m.get("role") or m.get("relationship_type"),
            }
            await _add_chart_meta(rec, uid)
            matches.append(rec)

    # ---- saved_people ----
    if name_re:
        async for sp in db.saved_people.find({"name": name_re}).limit(50):
            uid = sp.get("linked_user_id") or sp.get("emergent_user_id")
            rec = {
                "collection": "saved_people",
                "_id": str(sp.get("_id")),
                "user_id": uid,
                "name": sp.get("name"),
                "email": sp.get("email"),
                "forum_id": None,
                "linked_user_id": sp.get("linked_user_id"),
                "owner_user_id": sp.get("user_id"),
            }
            await _add_chart_meta(rec, uid)
            matches.append(rec)

    # ---- charts (denormalized) ----
    chart_or: List[Dict[str, Any]] = []
    if name_re:
        chart_or.append({"name": name_re})
        chart_or.append({"display_name": name_re})
    if email_norm:
        chart_or.append({"email": email_norm})
    if chart_or:
        async for c in db.charts.find({"$or": chart_or}).limit(50):
            uid = c.get("user_id") or str(c.get("_id"))
            rec = {
                "collection": "charts",
                "_id": str(c.get("_id")),
                "user_id": uid,
                "name": c.get("name") or c.get("display_name"),
                "email": c.get("email"),
                "forum_id": None,
            }
            await _add_chart_meta(rec, uid)
            matches.append(rec)

    return JSONResponse(
        content={
            "build_marker": "find-user-readonly-v1",
            "query": {"name": name, "email": email},
            "match_count": len(matches),
            "matches": matches,
        },
        headers={"Cache-Control": "no-store"},
    )
