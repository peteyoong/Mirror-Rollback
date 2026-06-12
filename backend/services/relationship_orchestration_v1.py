"""relationship_orchestration_v1 — P3 relationship-aware lens orchestration.

Receipt-only enrichment that re-prioritizes the lens stack based on the
resolved relationship context. Strictly additive and shadow-only —
never participates in the live response path (matches the P4 / cross-
lens-synthesis-v2 pattern).

Design properties
-----------------
* Pure function. No DB / network / randomness.
* Existing lens outputs preserved. The plan is emitted alongside the
  existing `lens_priority` from `intent_envelope` — the live response
  reads the envelope, not the plan.
* Conservative modulations. The deltas re-rank the lens stack without
  ever zeroing out a lens (so the existing recall is intact).

Rule resolution
---------------
A "role bucket" is computed from the resolved `relationship_role`,
`target_resolved`, and `forum_topology` payload. Order matters — first
match wins:

    1. spouse        - role in {spouse, partner, wife, husband, …}
    2. child         - role in {child, son, daughter, kid, teen, …}
    3. cofounder     - role in {cofounder, co-founder, business partner}
                       OR (colleague + leadership/career intent)
    4. forum_member  - active_member_id present in topology
                       (and no role-noun match above)
    5. self          - default (no modulation)

Each bucket carries a fixed additive lens-modulation map:

    spouse:       astrology +0.30, relationship_lens +0.40,
                  human_design +0.20, timeline +0.10
    child:        astrology +0.20, human_design +0.30, enneagram +0.15,
                  timeline +0.20, relationship_lens +0.10
    cofounder:    human_design +0.30, astrology +0.15, enneagram +0.25,
                  relationship_lens +0.20, timeline +0.10
    forum_member: relationship_lens +0.40, astrology +0.20,
                  human_design +0.20, enneagram +0.10
    self:         (no modulation)

The plan re-ranks `lens_priority` by `prior_rank_weight + modulation`
where `prior_rank_weight = LENS_WEIGHTS_PER_DOMAIN[primary_domain]`.

Output shape
------------
```
{
  "version":                "relationship_orchestration_v1.0.0",
  "computed":               true,
  "role_resolved":          "spouse",
  "rule_bucket":            "spouse",
  "applied_rules":          ["role_match:spouse", "target_bound"],
  "lens_priority_before":   [...],
  "lens_priority_after":    [...],
  "lens_weight_modulation": {"astrology": 0.3, ...},
  "framing_hint":           "spouse_focus",
  "context_mode":           "reflection" | "chart" | "forum" | "planning",
  "target_resolved":        "mel-001" | null,
  "active_member_id":       "patricia-001" | null,
  "lens_outputs_preserved": true
}
```
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

VERSION = "relationship_orchestration_v1.0.0"

# Role lexicon — first match wins in `_resolve_role_bucket`.
# Keys are role-noun tokens (lower-cased, substring-friendly).
_SPOUSE_ROLES    = {"spouse", "partner", "wife", "husband",
                    "girlfriend", "boyfriend", "fiance", "fiancee"}
_CHILD_ROLES     = {"child", "son", "daughter", "kid", "teen",
                    "baby", "toddler"}
_COFOUNDER_ROLES = {"cofounder", "co-founder", "co_founder",
                    "business_partner", "biz_partner"}
_COLLEAGUE_ROLES = {"colleague", "coworker", "teammate", "boss",
                    "report", "direct_report", "manager"}

# Per-bucket lens modulation (additive). Keys MUST match the lens names
# used by intent_router_v2.LENS_WEIGHTS_PER_DOMAIN.
LENS_MODULATIONS: Dict[str, Dict[str, float]] = {
    "spouse": {
        "astrology":    0.30,
        "relationship": 0.40,
        "human_design": 0.20,
        "timeline":     0.10,
    },
    "child": {
        "astrology":    0.20,
        "human_design": 0.30,
        "enneagram":    0.15,
        "timeline":     0.20,
        "relationship": 0.10,
    },
    "cofounder": {
        "human_design": 0.30,
        "astrology":    0.15,
        "enneagram":    0.25,
        "relationship": 0.20,
        "timeline":     0.10,
    },
    "forum_member": {
        "relationship": 0.40,
        "astrology":    0.20,
        "human_design": 0.20,
        "enneagram":    0.10,
    },
    "self": {},  # no modulation
}

# Friendly framing hint per bucket — useful for downstream rendering
# but never consumed by the live response path in this iteration.
FRAMING_HINT: Dict[str, str] = {
    "spouse":       "spouse_focus",
    "child":        "child_developmental",
    "cofounder":    "cofounder_strategic",
    "forum_member": "forum_member_dynamic",
    "self":         "self_inquiry",
}


def _normalize_role(role: Optional[str]) -> str:
    if not role:
        return ""
    return str(role).strip().lower().replace("-", "_").replace(" ", "_")


def _resolve_role_bucket(
    *,
    relationship_role: Optional[str],
    target_resolved: Optional[str],
    forum_topology: Optional[Dict[str, Any]],
    primary_domain: Optional[str],
) -> Tuple[str, List[str]]:
    """Return (bucket, applied_rules).

    Order matters: spouse > child > cofounder > forum_member > self.
    `applied_rules` is a list of human-readable reasons the rule fired
    so dashboards can audit the routing.
    """
    rules: List[str] = []
    role = _normalize_role(relationship_role)

    # 1. spouse — direct role match
    if role in _SPOUSE_ROLES:
        rules.append(f"role_match:spouse:{role}")
        if target_resolved:
            rules.append("target_bound")
        return "spouse", rules

    # 2. child — direct role match
    if role in _CHILD_ROLES:
        rules.append(f"role_match:child:{role}")
        if target_resolved:
            rules.append("target_bound")
        return "child", rules

    # 3. cofounder — direct role match
    if role in _COFOUNDER_ROLES:
        rules.append(f"role_match:cofounder:{role}")
        if target_resolved:
            rules.append("target_bound")
        return "cofounder", rules

    # 3b. cofounder via colleague + leadership/career intent
    if role in _COLLEAGUE_ROLES and primary_domain in ("leadership", "career"):
        rules.append(f"role_match:cofounder:via_colleague_leadership:{role}")
        if target_resolved:
            rules.append("target_bound")
        return "cofounder", rules

    # 4. forum_member — topology with active member binding
    ft = forum_topology or {}
    active_id = ft.get("active_member_id")
    if active_id:
        rules.append("forum_member:active_member_id_bound")
        # Promote if the active id resolves in the topology graph
        members = ft.get("members") or []
        if any((m or {}).get("id") == active_id for m in members):
            rules.append("forum_member:active_in_members")
        return "forum_member", rules

    # 5. self — default
    if target_resolved:
        # Target bound but no recognized role — treat as relationship-leaning
        # self frame; still self bucket but flag for dashboards.
        rules.append("self:target_bound_unknown_role")
    else:
        rules.append("self:default")
    return "self", rules


def _reorder_lens_priority(
    lens_priority_before: List[str],
    modulation: Dict[str, float],
) -> List[str]:
    """Apply modulation deltas and re-rank by (rank_weight + modulation).

    The pre-modulation rank weight is computed from the position in the
    incoming list (1.0 at index 0, falling linearly to 0.1 at the tail).
    This preserves the *relative* preference encoded in the intent
    envelope while still letting strong modulations bubble a lens up.
    """
    if not lens_priority_before:
        return list(lens_priority_before)

    n = len(lens_priority_before)
    if n == 1:
        return list(lens_priority_before)

    scored: List[Tuple[str, float]] = []
    for idx, lens in enumerate(lens_priority_before):
        # Linear rank weight from 1.0 (first) down to 0.1 (last).
        rank_w = 1.0 - (idx * (0.9 / max(n - 1, 1)))
        mod = modulation.get(lens, 0.0)
        scored.append((lens, rank_w + mod))

    scored.sort(key=lambda kv: -kv[1])
    return [k for k, _ in scored]


def plan_lens_priority(
    *,
    intent_envelope: Dict[str, Any],
    relationship_role: Optional[str] = None,
    target_resolved: Optional[str] = None,
    forum_topology: Optional[Dict[str, Any]] = None,
    context_mode: Optional[str] = None,
) -> Dict[str, Any]:
    """Compute the relationship-aware lens priority plan.

    Pure function. Never raises (catches its own errors and returns a
    `computed=false` payload so the receipt builder never fails).
    """
    try:
        primary_domain = (intent_envelope or {}).get("primary_domain")
        lens_priority_before: List[str] = list(
            (intent_envelope or {}).get("lens_priority") or []
        )

        bucket, applied_rules = _resolve_role_bucket(
            relationship_role=relationship_role,
            target_resolved=target_resolved,
            forum_topology=forum_topology,
            primary_domain=primary_domain,
        )

        modulation = LENS_MODULATIONS.get(bucket, {})

        lens_priority_after = _reorder_lens_priority(
            lens_priority_before, modulation
        )

        # Context-mode applied rule — useful for dashboard splits.
        mode = (context_mode or "").strip().lower() or None
        if mode in ("chart", "forum", "planning", "reflection",
                    "reflection_chat", "forum_chat", "chart_view"):
            applied_rules.append(f"context_mode:{mode}")

        # Promote forum_member if context_mode is forum and we landed on
        # self due to missing role.
        if mode in ("forum", "forum_chat") and bucket == "self":
            applied_rules.append("forum_promotion:self_to_forum_member")
            bucket = "forum_member"
            modulation = LENS_MODULATIONS["forum_member"]
            lens_priority_after = _reorder_lens_priority(
                lens_priority_before, modulation
            )

        # Detect re-ordering happened so dashboards can count it.
        reordered = lens_priority_after != lens_priority_before

        return {
            "version":                VERSION,
            "computed":               True,
            "role_resolved":          _normalize_role(relationship_role) or None,
            "rule_bucket":            bucket,
            "applied_rules":          applied_rules,
            "lens_priority_before":   lens_priority_before,
            "lens_priority_after":    lens_priority_after,
            "lens_weight_modulation": dict(modulation),
            "framing_hint":           FRAMING_HINT.get(bucket, "self_inquiry"),
            "context_mode":           mode,
            "target_resolved":        target_resolved,
            "active_member_id":       (forum_topology or {}).get("active_member_id"),
            "reordered":              reordered,
            "lens_outputs_preserved": True,
        }
    except Exception as e:
        return {
            "version":                VERSION,
            "computed":               False,
            "error":                  f"{type(e).__name__}: {e!s}",
            "lens_outputs_preserved": True,
        }
