"""relationship_router_v2 — Mirror Chat V2 Slice B1 (SHADOW MODE).

Resolves who the user is currently talking about based on explicit target,
name mention, last-target memory, and active frame.  Shadow-only; does not
mutate any user state.
"""
from __future__ import annotations

import re, logging
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

log = logging.getLogger("relationship_router_v2")
ROUTER_VERSION = "relationship_router_v2.0.0"

_PRONOUN_RE = re.compile(r"\b(us|we|he|she|they|them|him|her)\b", re.IGNORECASE)


@dataclass
class RelationshipResolution:
    self_user_id: str
    target: Optional[str]
    role: Optional[str]
    closeness: float
    relationship_weight: float
    active_frame: str
    context_mode: str  # SELF | OTHER | RELATIONAL
    resolution_path: List[str]
    conflicts: List[str]
    missing_data: List[str]
    router_version: str = ROUTER_VERSION

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _name_in_message(text: str, names: List[str]) -> Optional[str]:
    tl = (text or "").lower()
    best = None
    for n in names:
        if not n: continue
        if n.lower() in tl:
            if best is None or len(n) > len(best):
                best = n
    return best


def resolve_relationship_context(
    *, self_user_id: str,
    user_message: str,
    active_frame: str = "self",
    target_id: Optional[str] = None,
    saved_people: Optional[List[Dict[str, Any]]] = None,
    forum_topology: Optional[Dict[str, Any]] = None,
    last_target_id: Optional[str] = None,
) -> RelationshipResolution:
    saved_people = saved_people or []
    resolution_path: List[str] = []
    missing: List[str] = []
    conflicts: List[str] = []

    target = None
    role = None
    closeness = 0.0
    weight = 0.0

    # 1. explicit target id wins
    if target_id:
        target = target_id
        resolution_path.append("explicit_target_id")
        match = next((p for p in saved_people if p.get("id") == target_id), None)
        if match:
            role = match.get("role")
            closeness = float(match.get("closeness") or 0.0)
            weight = float(match.get("weight") or closeness)
        else:
            missing.append("target_not_in_saved_people")

    # 2. name in message
    if not target and saved_people:
        names = [p.get("name") for p in saved_people if p.get("name")]
        hit = _name_in_message(user_message or "", names)
        if hit:
            match = max((p for p in saved_people if p.get("name") == hit),
                        key=lambda p: float(p.get("closeness") or 0.0), default=None)
            if match:
                target = match.get("id") or match.get("name")
                role = match.get("role")
                closeness = float(match.get("closeness") or 0.0)
                weight = float(match.get("weight") or closeness)
                resolution_path.append("mentioned_name")

    # 3. implicit pronoun + last-target memory
    if not target and last_target_id and _PRONOUN_RE.search(user_message or ""):
        target = last_target_id
        match = next((p for p in saved_people if p.get("id") == last_target_id), None)
        if match:
            role = match.get("role")
            closeness = float(match.get("closeness") or 0.0)
            weight = float(match.get("weight") or closeness)
        resolution_path.append("pronoun_memory")

    # 4. forum frame default
    if not target and active_frame == "forum" and forum_topology:
        active = (forum_topology or {}).get("active_member_id")
        if active:
            target = active
            resolution_path.append("forum_active_member")

    if not target and active_frame in ("forum", "member"):
        missing.append("forum_target_unresolved")

    context_mode = "RELATIONAL" if target else "SELF"
    if active_frame == "member" and not target:
        # frame demanded a target but we couldn't find one
        conflicts.append("frame=member_but_no_target")

    return RelationshipResolution(
        self_user_id=self_user_id,
        target=target,
        role=role,
        closeness=round(closeness, 3),
        relationship_weight=round(weight, 3),
        active_frame=active_frame,
        context_mode=context_mode,
        resolution_path=resolution_path or ["none"],
        conflicts=conflicts,
        missing_data=missing,
    )
