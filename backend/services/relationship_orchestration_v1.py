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

VERSION = "relationship_orchestration_v1.2.0"

# Role lexicon — first match wins in `_resolve_role_bucket`.
# Keys are role-noun tokens (lower-cased, substring-friendly).
#
# PFS-2.3 — lexicon expanded to cover the full `forum_relationship_edges.role_type`
# vocabulary defined in `services/forum_topology.py`:
#   FAMILY:        parent, child, sibling, spouse, former_partner
#   PROFESSIONAL:  cofounder, manager, employee, investor, advisor,
#                  mentor, mentee, coach, coachee, business_partner
#   SOCIAL:        close_friend, forum_mate, authority_figure,
#                  collaborator, other
# Each topology role lands in an INTENTIONAL bucket — no role silently
# falls through to `forum_member` / `self` unless that is the intended
# orchestration shape for that role.
_SPOUSE_ROLES         = {"spouse", "partner", "wife", "husband",
                         "girlfriend", "boyfriend", "fiance", "fiancee"}
_FORMER_PARTNER_ROLES = {"former_partner", "ex", "ex_wife", "ex_husband",
                         "ex_partner", "ex_spouse", "former_spouse"}
_CHILD_ROLES          = {"child", "son", "daughter", "kid", "teen",
                         "baby", "toddler"}
_PARENT_ROLES         = {"parent", "mom", "mother", "dad", "father",
                         "mama", "papa", "mum"}
_SIBLING_ROLES        = {"sibling", "brother", "sister", "twin"}
_SIBLING_PAIR_ROLES   = {"sibling_pair", "siblings", "sibling-sibling",
                         "sibling_sibling", "brother_brother",
                         "sister_sister", "brother_sister",
                         "sister_brother", "twin_pair"}
_COFOUNDER_ROLES      = {"cofounder", "co-founder", "co_founder",
                         "business_partner", "biz_partner"}
_ADVISOR_ROLES        = {"advisor", "adviser"}
_INVESTOR_ROLES       = {"investor", "lp", "limited_partner",
                         "lead_investor"}
_MENTOR_ROLES         = {"mentor"}
_MENTEE_ROLES         = {"mentee", "protege", "protégé"}
_COACH_ROLES          = {"coach"}
_COACHEE_ROLES        = {"coachee", "client"}
_MANAGER_ROLES        = {"manager", "boss", "supervisor", "lead", "head"}
_EMPLOYEE_ROLES       = {"employee", "report", "direct_report",
                         "subordinate"}
_AUTHORITY_ROLES      = {"authority_figure", "authority"}
_COLLABORATOR_ROLES   = {"collaborator"}
_CLOSE_FRIEND_ROLES   = {"close_friend", "best_friend", "friend"}
_FORUM_MATE_ROLES     = {"forum_mate", "forum_member", "other"}

# Per-bucket lens modulation (additive). Keys MUST match the lens names
# used by intent_router_v2.LENS_WEIGHTS_PER_DOMAIN.
# All modulations are intentionally moderate (≤0.40) so they re-rank
# without overwhelming the envelope's primary domain signal.
LENS_MODULATIONS: Dict[str, Dict[str, float]] = {
    # ── Relationship family ────────────────────────────────────────
    "spouse": {
        "astrology":    0.30,
        "relationship": 0.40,
        "human_design": 0.20,
        "timeline":     0.10,
    },
    "former_partner": {
        "astrology":    0.20,
        "relationship": 0.40,
        "human_design": 0.20,
        "enneagram":    0.15,
        "timeline":     0.10,
    },
    "child": {
        "astrology":    0.20,
        "human_design": 0.30,
        "enneagram":    0.15,
        "timeline":     0.20,
        "relationship": 0.10,
    },
    "parent": {
        "astrology":    0.25,
        "human_design": 0.20,
        "enneagram":    0.20,
        "relationship": 0.20,
        "timeline":     0.15,
    },
    "sibling": {
        "astrology":    0.20,
        "human_design": 0.20,
        "relationship": 0.30,
        "enneagram":    0.15,
        "timeline":     0.05,
    },
    # sibling_pair — when the SUBJECTS of the read are two siblings to
    # each other (e.g. user asks about the dynamic between their two
    # children, or two of their forum members who are siblings).  This
    # is NOT the same as `sibling` (which is user↔sibling).  Reads of
    # this kind want a relationship-led frame anchored in shared origin,
    # with human-design + enneagram as the strong corroborating lenses
    # (because birth-order, type, and tri-fix differentiation often
    # explain the dynamic better than mid-strength astrology).
    "sibling_pair": {
        "relationship": 0.40,
        "human_design": 0.25,
        "enneagram":    0.20,
        "astrology":    0.15,
        "timeline":     0.05,
    },
    # ── Work / founder family ──────────────────────────────────────
    "cofounder": {
        "human_design": 0.30,
        "astrology":    0.15,
        "enneagram":    0.25,
        "relationship": 0.20,
        "timeline":     0.10,
    },
    "advisor": {
        "human_design": 0.30,
        "astrology":    0.20,
        "enneagram":    0.20,
        "relationship": 0.15,
        "timeline":     0.10,
    },
    "investor": {
        "human_design": 0.30,
        "astrology":    0.20,
        "enneagram":    0.15,
        "relationship": 0.15,
        "timeline":     0.10,
    },
    "manager": {
        "human_design": 0.25,
        "enneagram":    0.25,
        "astrology":    0.15,
        "relationship": 0.20,
        "timeline":     0.10,
    },
    "employee": {
        "human_design": 0.25,
        "enneagram":    0.25,
        "astrology":    0.15,
        "relationship": 0.20,
        "timeline":     0.10,
    },
    # ── Development family (mentor / coach axis) ───────────────────
    "mentor": {
        "human_design": 0.30,
        "enneagram":    0.30,
        "astrology":    0.15,
        "relationship": 0.10,
        "timeline":     0.10,
    },
    "mentee": {
        "human_design": 0.25,
        "enneagram":    0.30,
        "astrology":    0.15,
        "relationship": 0.10,
        "timeline":     0.20,
    },
    "coach": {
        "human_design": 0.30,
        "enneagram":    0.30,
        "astrology":    0.15,
        "relationship": 0.10,
        "timeline":     0.15,
    },
    "coachee": {
        "human_design": 0.25,
        "enneagram":    0.30,
        "astrology":    0.15,
        "relationship": 0.10,
        "timeline":     0.20,
    },
    # ── Social / generic ───────────────────────────────────────────
    "authority_figure": {
        "human_design": 0.20,
        "enneagram":    0.30,
        "astrology":    0.20,
        "relationship": 0.20,
        "timeline":     0.10,
    },
    "collaborator": {
        "relationship": 0.25,
        "human_design": 0.20,
        "astrology":    0.20,
        "enneagram":    0.15,
        "timeline":     0.10,
    },
    "close_friend": {
        "relationship": 0.35,
        "astrology":    0.20,
        "human_design": 0.20,
        "enneagram":    0.15,
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
# Phrases follow the PFS-2.3 spec (strategy column).
FRAMING_HINT: Dict[str, str] = {
    "spouse":           "couple_dynamic",
    "former_partner":   "closure_dynamic",
    "child":            "parenting",
    "parent":           "lineage",
    "sibling":          "family_dynamic",
    "sibling_pair":     "siblings_among_themselves",
    "cofounder":        "cofounder_strategic",
    "advisor":          "guidance",
    "investor":         "influence",
    "manager":          "authority",
    "employee":         "responsibility",
    "mentor":           "development_giving",
    "mentee":           "development_receiving",
    "coach":            "growth_giving",
    "coachee":          "growth_receiving",
    "authority_figure": "power_dynamics",
    "collaborator":     "partnership",
    "close_friend":     "closeness",
    "forum_member":     "forum_member_dynamic",
    "self":             "self_inquiry",
}

# PFS-2.3 — domain bias label per bucket. Useful for dashboard splits
# and for downstream consumers that want a quick relationship/work/self
# axis tag without re-deriving it from the bucket name.
DOMAIN_BIAS: Dict[str, str] = {
    "spouse":           "relationship",
    "former_partner":   "relationship",
    "child":            "relationship",
    "parent":           "relationship",
    "sibling":          "relationship",
    "sibling_pair":     "relationship",
    "cofounder":        "work",
    "advisor":          "work",
    "investor":         "work",
    "manager":          "work",
    "employee":         "work",
    "mentor":           "work_self",
    "mentee":           "self",
    "coach":            "self_work",
    "coachee":          "self",
    "authority_figure": "self_work",
    "collaborator":     "work",
    "close_friend":     "relationship",
    "forum_member":     "forum",
    "self":             "self",
}


def _normalize_role(role: Optional[str]) -> str:
    if not role:
        return ""
    return str(role).strip().lower().replace("-", "_").replace(" ", "_")


def _looks_like_sibling_pair(forum_topology: Optional[Dict[str, Any]]) -> bool:
    """Topology-based detection for the `sibling_pair` bucket.

    Fires when the topology indicates the read concerns TWO people who
    are siblings to each other (not just the user's sibling).  Three
    signals, any one of which is sufficient:

      1) `forum_topology['pair_relationship']` == 'sibling' or
         'sibling_pair' — explicit pair label from the resolver.
      2) `forum_topology['pair_members']` is a 2-list and both members
         share the same parent in the topology (siblings of each other).
      3) `forum_topology['active_pair']['role_between']` is a sibling-
         family token ('sibling', 'brother', 'sister', 'twin',
         'sibling_pair', 'siblings').

    Conservative: returns False on any malformed shape so misshapen
    topology never accidentally re-buckets a non-sibling-pair read.
    """
    if not isinstance(forum_topology, dict):
        return False

    # Signal 1 — explicit pair label
    pair_rel = _normalize_role(forum_topology.get("pair_relationship"))
    if pair_rel in {"sibling", "sibling_pair", "siblings", "brother",
                    "sister", "twin", "twin_pair"}:
        return True

    # Signal 3 — active_pair carries an explicit role_between
    active_pair = forum_topology.get("active_pair")
    if isinstance(active_pair, dict):
        role_between = _normalize_role(active_pair.get("role_between"))
        if role_between in {"sibling", "sibling_pair", "siblings",
                            "brother", "sister", "twin"}:
            return True

    # Signal 2 — pair_members share a common parent
    pair_members = forum_topology.get("pair_members")
    if isinstance(pair_members, (list, tuple)) and len(pair_members) == 2:
        try:
            parents_a = {
                str(p) for p in (pair_members[0] or {}).get("parent_ids", [])
                if p
            }
            parents_b = {
                str(p) for p in (pair_members[1] or {}).get("parent_ids", [])
                if p
            }
        except Exception:
            return False
        # At least one shared, non-empty parent → siblings of each other.
        if parents_a and parents_b and (parents_a & parents_b):
            return True

    return False


def _resolve_role_bucket(
    *,
    relationship_role: Optional[str],
    target_resolved: Optional[str],
    forum_topology: Optional[Dict[str, Any]],
    primary_domain: Optional[str],
) -> Tuple[str, List[str]]:
    """Return (bucket, applied_rules).

    Order matters — most specific match wins. PFS-2.3 expanded the
    lexicon so every `forum_relationship_edges.role_type` lands in an
    intentional bucket (relationship / work / development / social /
    self) rather than silently falling through to `forum_member` or
    `self`.

    Resolution ladder:
      1. relationship family  — spouse, former_partner, child, parent,
                                sibling, close_friend
      2. development family   — mentor, mentee, coach, coachee
      3. work family          — cofounder, advisor, investor, manager,
                                employee, collaborator
      4. authority            — authority_figure
      5. collegial fallback   — colleague + leadership/career intent
                                → cofounder (legacy heuristic kept)
      6. forum_member         — active_member_id in topology with no
                                role-noun match above
      7. self                 — default
    """
    rules: List[str] = []
    role = _normalize_role(relationship_role)

    # 1a. spouse — relationship-family direct match
    if role in _SPOUSE_ROLES:
        rules.append(f"role_match:spouse:{role}")
        if target_resolved:
            rules.append("target_bound")
        return "spouse", rules

    # 1b. former_partner — relationship-family, closure framing
    if role in _FORMER_PARTNER_ROLES:
        rules.append(f"role_match:former_partner:{role}")
        if target_resolved:
            rules.append("target_bound")
        return "former_partner", rules

    # 1c. child — relationship-family, parenting framing (user is parent)
    if role in _CHILD_ROLES:
        rules.append(f"role_match:child:{role}")
        if target_resolved:
            rules.append("target_bound")
        return "child", rules

    # 1d. parent — relationship-family, lineage framing (user is child)
    if role in _PARENT_ROLES:
        rules.append(f"role_match:parent:{role}")
        if target_resolved:
            rules.append("target_bound")
        return "parent", rules

    # 1e. sibling_pair — both parties are siblings to each other (e.g.
    # two of the user's children, or two forum members linked by a
    # sibling edge).  This is distinct from `sibling` (user↔sibling)
    # and prefers a relationship-led frame anchored in shared origin.
    # Resolution order: explicit role token first, then topology check.
    if role in _SIBLING_PAIR_ROLES:
        rules.append(f"role_match:sibling_pair:{role}")
        if target_resolved:
            rules.append("target_bound")
        return "sibling_pair", rules
    if _looks_like_sibling_pair(forum_topology):
        rules.append("topology_match:sibling_pair")
        if target_resolved:
            rules.append("target_bound")
        return "sibling_pair", rules

    # 1f. sibling — relationship-family, family_dynamic framing
    if role in _SIBLING_ROLES:
        rules.append(f"role_match:sibling:{role}")
        if target_resolved:
            rules.append("target_bound")
        return "sibling", rules

    # 1g. close_friend — relationship-family, closeness framing
    if role in _CLOSE_FRIEND_ROLES:
        rules.append(f"role_match:close_friend:{role}")
        if target_resolved:
            rules.append("target_bound")
        return "close_friend", rules

    # 2a. mentor (giver) — development family
    if role in _MENTOR_ROLES:
        rules.append(f"role_match:mentor:{role}")
        if target_resolved:
            rules.append("target_bound")
        return "mentor", rules

    # 2b. mentee (receiver) — development family
    if role in _MENTEE_ROLES:
        rules.append(f"role_match:mentee:{role}")
        if target_resolved:
            rules.append("target_bound")
        return "mentee", rules

    # 2c. coach (giver) — growth family
    if role in _COACH_ROLES:
        rules.append(f"role_match:coach:{role}")
        if target_resolved:
            rules.append("target_bound")
        return "coach", rules

    # 2d. coachee (receiver) — growth family
    if role in _COACHEE_ROLES:
        rules.append(f"role_match:coachee:{role}")
        if target_resolved:
            rules.append("target_bound")
        return "coachee", rules

    # 3a. cofounder / business_partner — work-family, leadership framing
    if role in _COFOUNDER_ROLES:
        rules.append(f"role_match:cofounder:{role}")
        if target_resolved:
            rules.append("target_bound")
        return "cofounder", rules

    # 3b. advisor — work-family, guidance framing
    if role in _ADVISOR_ROLES:
        rules.append(f"role_match:advisor:{role}")
        if target_resolved:
            rules.append("target_bound")
        return "advisor", rules

    # 3c. investor — work-family, influence framing
    if role in _INVESTOR_ROLES:
        rules.append(f"role_match:investor:{role}")
        if target_resolved:
            rules.append("target_bound")
        return "investor", rules

    # 3d. manager — work-family, authority framing
    if role in _MANAGER_ROLES:
        rules.append(f"role_match:manager:{role}")
        if target_resolved:
            rules.append("target_bound")
        return "manager", rules

    # 3e. employee — work-family, responsibility framing
    if role in _EMPLOYEE_ROLES:
        rules.append(f"role_match:employee:{role}")
        if target_resolved:
            rules.append("target_bound")
        return "employee", rules

    # 3f. collaborator — work-family, partnership framing
    if role in _COLLABORATOR_ROLES:
        rules.append(f"role_match:collaborator:{role}")
        if target_resolved:
            rules.append("target_bound")
        return "collaborator", rules

    # 4. authority_figure — self/work axis, power_dynamics framing
    if role in _AUTHORITY_ROLES:
        rules.append(f"role_match:authority_figure:{role}")
        if target_resolved:
            rules.append("target_bound")
        return "authority_figure", rules

    # 4b. explicit forum_mate / other / forum_member tokens (topology
    #     social-family) land on the generic forum_member bucket — this
    #     is the INTENDED bucket, not a silent fallthrough.
    if role in _FORUM_MATE_ROLES:
        rules.append(f"role_match:forum_member:{role}")
        if target_resolved:
            rules.append("target_bound")
        return "forum_member", rules

    # 5. Legacy heuristic: colleague-style role + leadership/career
    #    intent → cofounder. Kept for back-compat with the V2 router
    #    free-text role classifier.
    _LEGACY_COLLEAGUE = {"colleague", "coworker", "teammate",
                         "co_worker", "boss"}
    if role in _LEGACY_COLLEAGUE and primary_domain in ("leadership", "career"):
        rules.append(f"role_match:cofounder:via_colleague_leadership:{role}")
        if target_resolved:
            rules.append("target_bound")
        return "cofounder", rules

    # 6. forum_member — topology with active member binding
    ft = forum_topology or {}
    active_id = ft.get("active_member_id")
    if active_id:
        rules.append("forum_member:active_member_id_bound")
        # Promote if the active id resolves in the topology graph
        members = ft.get("members") or []
        if any((m or {}).get("id") == active_id for m in members):
            rules.append("forum_member:active_in_members")
        return "forum_member", rules

    # 7. self — default
    if target_resolved:
        # Target bound but no recognized role — treat as relationship-leaning
        # self frame; still self bucket but flag for dashboards.
        rules.append("self:target_bound_unknown_role")
        if role:
            # PFS-2.3 telemetry: record the unknown role so observers
            # can spot lexicon-coverage drift in production.
            rules.append(f"self:unknown_role_token:{role}")
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
            "domain_bias":            DOMAIN_BIAS.get(bucket, "self"),
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
