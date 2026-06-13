"""
Relationship Resolver (V10)
============================

Build marker: relationship-aware-astrology-v10

Resolves the relationship role between asker and target person so the
master-astrologer engine can produce RELATIONAL synthesis instead of
"generic assistant discussing another person".

Resolution priority:
  0. `forum_relationship_edges` (the canonical graph also consumed by
     FKR v1) — wins when an edge from asker→target carries a
     `role_type`.  Forum-scoped edges take precedence over global
     edges.
  1. Explicit map in `relationship_mappings` collection (asker → target)
  2. `saved_people.relationship_type` for the asker (name or
     linked_user_id match)
  3. `forum_members.relationship_type` (when populated)
  4. Inferred from forum context — a private two-person forum named with
     two first names ("Pete & Mel") is treated as a `partner` field.
     A small (≤4 member) private forum is treated as `close_circle`.
     Larger forums default to `forum_member`.
  5. Default fallback: `forum_member`.

Returns:
  {
    "relationship_detected":  bool,
    "relationship_role":      "spouse" | "partner" | "child" | "parent" |
                              "sibling" | "close_friend" | "forum_member"
                              | "close_circle" | "colleague" | "ex_partner"
                              | "boss" | "friend" | None,
    "closeness":              "high" | "medium" | "low",
    "emotional_weight":       "high" | "medium" | "low",
    "relationship_source":    "explicit_map" | "saved_people" |
                              "forum_relationship" | "forum_inference" |
                              "default",
    "forum_id":               str | None,
    "forum_name":             str | None,
  }
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

BUILD_MARKER = "relationship-aware-astrology-v10"

# Map raw relationship_type strings to canonical roles + closeness profile
_ROLE_PROFILE: Dict[str, Dict[str, str]] = {
    "spouse":      {"role": "spouse",       "closeness": "high",   "weight": "high"},
    "partner":     {"role": "partner",      "closeness": "high",   "weight": "high"},
    "husband":     {"role": "spouse",       "closeness": "high",   "weight": "high"},
    "wife":        {"role": "spouse",       "closeness": "high",   "weight": "high"},
    "ex_partner":  {"role": "ex_partner",   "closeness": "medium", "weight": "high"},
    "ex":          {"role": "ex_partner",   "closeness": "medium", "weight": "high"},
    "child":       {"role": "child",        "closeness": "high",   "weight": "high"},
    "son":         {"role": "child",        "closeness": "high",   "weight": "high"},
    "daughter":    {"role": "child",        "closeness": "high",   "weight": "high"},
    "parent":      {"role": "parent",       "closeness": "high",   "weight": "high"},
    "mother":      {"role": "parent",       "closeness": "high",   "weight": "high"},
    "father":      {"role": "parent",       "closeness": "high",   "weight": "high"},
    "sibling":     {"role": "sibling",      "closeness": "medium", "weight": "high"},
    "brother":     {"role": "sibling",      "closeness": "medium", "weight": "high"},
    "sister":      {"role": "sibling",      "closeness": "medium", "weight": "high"},
    "close_friend": {"role": "close_friend","closeness": "high",   "weight": "medium"},
    "best_friend": {"role": "close_friend", "closeness": "high",   "weight": "medium"},
    "friend":      {"role": "friend",       "closeness": "medium", "weight": "medium"},
    "boss":        {"role": "boss",         "closeness": "low",    "weight": "medium"},
    "colleague":   {"role": "colleague",    "closeness": "low",    "weight": "low"},
    "coworker":    {"role": "colleague",    "closeness": "low",    "weight": "low"},
    "forum_member": {"role": "forum_member","closeness": "medium", "weight": "medium"},
    "close_circle": {"role": "close_circle","closeness": "high",   "weight": "medium"},
}


def _profile_for(raw: Optional[str]) -> Dict[str, str]:
    if not raw:
        return _ROLE_PROFILE["forum_member"]
    return _ROLE_PROFILE.get(raw.lower(), _ROLE_PROFILE["forum_member"])


async def resolve_relationship(
    *,
    db,
    asker_user_id: str,
    target_user_id: Optional[str],
    target_name: Optional[str],
    forum_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Resolve the relationship between asker and target.

    See module docstring for priority order.
    """
    result_base = {
        "relationship_detected": False,
        "relationship_role":     None,
        "closeness":             "medium",
        "emotional_weight":      "medium",
        "relationship_source":   "default",
        "forum_id":              forum_id,
        "forum_name":            None,
        "build_marker":          BUILD_MARKER,
    }

    # 0. forum_relationship_edges — the canonical graph that the FKR
    #    retrieval layer already consults.  Must be first so the resolver
    #    and FKR cannot disagree on whether Mel is Pete's spouse.  Only
    #    edges with explicit `role_type` are honoured here; everything
    #    else falls through to the existing priority chain.
    try:
        if target_user_id:
            edge_query: Dict[str, Any] = {
                "from_user_id": asker_user_id,
                "to_user_id":   target_user_id,
            }
            # Prefer an edge scoped to the active forum first; fall back
            # to any edge between the same pair of users.
            edge = None
            if forum_id:
                edge = await db.forum_relationship_edges.find_one({
                    **edge_query, "forum_id": forum_id,
                })
            if not edge:
                edge = await db.forum_relationship_edges.find_one(edge_query)
            if edge and edge.get("role_type"):
                prof = _profile_for(edge["role_type"])
                # Confidence-weighted closeness: 'high' bumps emotional
                # weight; 'low' demotes closeness one notch.
                conf = (edge.get("confidence") or "").lower()
                closeness = prof["closeness"]
                weight = prof["weight"]
                if conf == "low":
                    closeness = "medium" if closeness == "high" else closeness
                    weight = "medium" if weight == "high" else weight
                return {
                    **result_base,
                    "relationship_detected": True,
                    "relationship_role":     prof["role"],
                    "closeness":             closeness,
                    "emotional_weight":      weight,
                    "relationship_source":   "forum_relationship_edges",
                }
    except Exception as e:
        logger.debug(f"[RelationshipResolver] edges lookup skipped: {e}")

    # 1. Explicit map (user-defined via /api/admin/map-relationship)
    try:
        mapping = await db.relationship_mappings.find_one({
            "asker_user_id":  asker_user_id,
            "$or": [
                {"target_user_id": target_user_id} if target_user_id else {"_no_match": True},
                {"target_name":    target_name} if target_name else {"_no_match": True},
            ],
        })
        if mapping and mapping.get("relationship_type"):
            prof = _profile_for(mapping["relationship_type"])
            return {
                **result_base,
                "relationship_detected": True,
                "relationship_role":     prof["role"],
                "closeness":             prof["closeness"],
                "emotional_weight":      prof["weight"],
                "relationship_source":   "explicit_map",
            }
    except Exception as e:
        logger.debug(f"[RelationshipResolver] explicit-map lookup skipped: {e}")

    # 2. saved_people — name match within asker's people
    try:
        query: Dict[str, Any] = {"user_id": asker_user_id}
        if target_user_id:
            sp = await db.saved_people.find_one({
                **query, "linked_user_id": target_user_id,
            })
            if not sp:
                sp = await db.saved_people.find_one({
                    **query, "emergent_user_id": target_user_id,
                })
        else:
            sp = None
        if not sp and target_name:
            import re as _re
            sp = await db.saved_people.find_one({
                **query, "name": _re.compile(rf"^{_re.escape(target_name)}$", _re.IGNORECASE),
            })
        if sp and sp.get("relationship_type"):
            prof = _profile_for(sp["relationship_type"])
            return {
                **result_base,
                "relationship_detected": True,
                "relationship_role":     prof["role"],
                "closeness":             prof["closeness"],
                "emotional_weight":      prof["weight"],
                "relationship_source":   "saved_people",
            }
    except Exception as e:
        logger.debug(f"[RelationshipResolver] saved_people lookup skipped: {e}")

    # 3. forum_members explicit relationship_type
    forum_name: Optional[str] = None
    forum_member_count: Optional[int] = None
    forum_is_private: Optional[bool] = None
    try:
        if forum_id and target_user_id:
            fm = await db.forum_members.find_one({
                "forum_id": forum_id, "user_id": target_user_id,
            })
            if fm and fm.get("relationship_type"):
                prof = _profile_for(fm["relationship_type"])
                return {
                    **result_base,
                    "relationship_detected": True,
                    "relationship_role":     prof["role"],
                    "closeness":             prof["closeness"],
                    "emotional_weight":      prof["weight"],
                    "relationship_source":   "forum_relationship",
                }
        if forum_id:
            from bson import ObjectId
            try:
                fdoc = await db.forums.find_one({"_id": ObjectId(forum_id)})
            except Exception:
                fdoc = await db.forums.find_one({"_id": forum_id})
            if fdoc:
                forum_name = fdoc.get("name")
                forum_member_count = fdoc.get("member_count")
                forum_is_private = fdoc.get("is_private")
    except Exception as e:
        logger.debug(f"[RelationshipResolver] forum_members lookup skipped: {e}")

    # 4. Inference from forum context
    try:
        if forum_id:
            # Two-person private forum with a name like "X & Y" → partner
            if forum_is_private and forum_member_count == 2:
                if forum_name and (" & " in forum_name or " and " in forum_name.lower()):
                    return {
                        **result_base,
                        "relationship_detected": True,
                        "relationship_role":     "partner",
                        "closeness":             "high",
                        "emotional_weight":      "high",
                        "relationship_source":   "forum_inference",
                        "forum_name":            forum_name,
                    }
                # Two-person private without "&" pattern → close_circle
                return {
                    **result_base,
                    "relationship_detected": True,
                    "relationship_role":     "close_circle",
                    "closeness":             "high",
                    "emotional_weight":      "medium",
                    "relationship_source":   "forum_inference",
                    "forum_name":            forum_name,
                }
            # Small (≤4 member) private forum → close_circle
            if forum_is_private and (forum_member_count or 0) <= 4:
                return {
                    **result_base,
                    "relationship_detected": True,
                    "relationship_role":     "close_circle",
                    "closeness":             "medium",
                    "emotional_weight":      "medium",
                    "relationship_source":   "forum_inference",
                    "forum_name":            forum_name,
                }
    except Exception as e:
        logger.debug(f"[RelationshipResolver] inference skipped: {e}")

    # 5. Default fallback — known to be in a forum but no specific role
    if forum_id:
        prof = _ROLE_PROFILE["forum_member"]
        return {
            **result_base,
            "relationship_detected": True,
            "relationship_role":     prof["role"],
            "closeness":             prof["closeness"],
            "emotional_weight":      prof["weight"],
            "relationship_source":   "default",
            "forum_name":            forum_name,
        }
    return result_base


def build_relational_synthesis_block(
    *,
    asker_name: Optional[str],
    target_name: Optional[str],
    relationship_ctx: Dict[str, Any],
    field_synthesis: Optional[Dict[str, Any]] = None,
) -> str:
    """Return a system-prompt block that injects relational synthesis
    instructions on top of the V8 field synthesis.

    The block does NOT replace the V8 field synthesis — it ADDS a
    relational layer the LLM must weave in.
    """
    role = relationship_ctx.get("relationship_role") or "forum_member"
    closeness = relationship_ctx.get("closeness", "medium")
    weight = relationship_ctx.get("emotional_weight", "medium")
    source = relationship_ctx.get("relationship_source", "default")

    # Role-specific framing templates
    role_framing = {
        "spouse":       "Frame this as a SPOUSE dynamic — describe how the target's field shows up inside the marriage / partnership specifically.",
        "partner":      "Frame this as a PARTNER dynamic — describe how the target's field shows up inside the intimate partnership specifically.",
        "ex_partner":   "Frame this as an EX-PARTNER dynamic — acknowledge the historical relational charge without re-inflaming it.",
        "child":        "Frame this as the asker's CHILD — describe how the child's field is held within the parent-child relationship.",
        "parent":       "Frame this as the asker's PARENT — describe how the parent's field shaped the asker's foundation.",
        "sibling":      "Frame this as a SIBLING dynamic — describe how the field interacts inside a shared origin.",
        "close_friend": "Frame this as a CLOSE FRIENDSHIP — describe how the target's field shows up in the chosen-family field.",
        "close_circle": "Frame this as a CLOSE-CIRCLE dynamic — small trusted group; describe how the field shows up inside that container.",
        "friend":       "Frame this as a FRIENDSHIP — describe how the target's field shows up in casual ongoing contact.",
        "colleague":    "Frame this as a COLLEAGUE dynamic — describe how the field shows up inside the professional container.",
        "boss":         "Frame this as the asker's BOSS — describe how the field shows up across the authority gradient.",
        "forum_member": "Frame this as a FORUM-MEMBER dynamic — describe how the field shows up inside the shared reflective space.",
    }.get(role, "Frame as a forum-member dynamic.")

    asker_ref = asker_name or "the asker"
    target_ref = target_name or "the target person"

    return (
        "\n=== RELATIONAL SYNTHESIS — relationship-aware-astrology-v10 ===\n"
        f"asker:              {asker_ref}\n"
        f"target:             {target_ref}\n"
        f"relationship_role:  {role}\n"
        f"closeness:          {closeness}\n"
        f"emotional_weight:   {weight}\n"
        f"source:             {source}\n"
        "\n"
        "INSTRUCTION:\n"
        f"  {role_framing}\n"
        "\n"
        "After describing the target's field (per the field-synthesis\n"
        "proof block above), you MUST add a RELATIONAL paragraph that\n"
        "answers: 'How does this field manifest INSIDE the relationship\n"
        f"between {asker_ref} and {target_ref}?'\n"
        "\n"
        "This relational paragraph must:\n"
        "  • Name the asker by name (or 'you' if asker_name unavailable).\n"
        "  • Describe a SPECIFIC interaction loop between the two fields\n"
        "    (e.g. 'When you hold steady space, Mel reads the silence as\n"
        "    emotional absence and her nervous system starts searching\n"
        "    for what is missing').\n"
        "  • Cite the destabilising planet by name when relevant.\n"
        "  • NOT pivot into reflective coaching prompts.\n"
        "  • NOT use any BANNED phrases ('how does this resonate', 'reflect on',\n"
        "    'consider how', 'in astrology').\n"
        "\n"
        "STRUCTURE OF FULL ANSWER:\n"
        "  Paragraph 1 — Field synthesis (per the V8 proof block above)\n"
        "  Paragraph 2 — Relational mapping inside this specific dynamic\n"
        "===========================================================\n"
    )


__all__ = [
    "resolve_relationship",
    "build_relational_synthesis_block",
    "BUILD_MARKER",
]
