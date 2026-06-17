"""Unit tests for relationship_orchestration_v1 (P3)."""
from __future__ import annotations

import pytest

from services.relationship_orchestration_v1 import (
    plan_lens_priority,
    VERSION,
    LENS_MODULATIONS,
    FRAMING_HINT,
)


def _make_envelope(primary="relationship",
                   lens_priority=None):
    return {
        "primary_domain": primary,
        "lens_priority": lens_priority or [
            "astrology", "human_design", "enneagram",
            "numerology", "relationship", "timeline",
        ],
    }


# ─────────────────────────────────────────────────────────────────────
# Basic behaviour
# ─────────────────────────────────────────────────────────────────────

def test_version_pinned():
    # PFS-2.4 bumped minor again: added sibling_pair bucket.
    assert VERSION == "relationship_orchestration_v1.2.0"


def test_lens_outputs_preserved_on_success():
    plan = plan_lens_priority(intent_envelope=_make_envelope())
    assert plan["lens_outputs_preserved"] is True
    assert plan["computed"] is True


def test_empty_envelope_does_not_raise():
    plan = plan_lens_priority(intent_envelope={})
    assert plan["computed"] is True
    assert plan["lens_priority_before"] == []
    assert plan["lens_priority_after"] == []


def test_malformed_inputs_do_not_raise():
    plan = plan_lens_priority(intent_envelope=None,
                              relationship_role=None,
                              forum_topology=None)
    assert plan["lens_outputs_preserved"] is True


# ─────────────────────────────────────────────────────────────────────
# Role buckets
# ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("role,bucket", [
    ("spouse",     "spouse"),
    ("partner",    "spouse"),
    ("wife",       "spouse"),
    ("husband",    "spouse"),
    ("girlfriend", "spouse"),
    ("Boyfriend",  "spouse"),   # case-insensitive
])
def test_spouse_bucket(role, bucket):
    plan = plan_lens_priority(
        intent_envelope=_make_envelope(),
        relationship_role=role,
        target_resolved="mel-001",
    )
    assert plan["rule_bucket"] == bucket
    assert plan["framing_hint"] == FRAMING_HINT[bucket]
    assert any("role_match:spouse" in r for r in plan["applied_rules"])
    assert "target_bound" in plan["applied_rules"]


@pytest.mark.parametrize("role", ["child", "son", "daughter", "kid", "teen"])
def test_child_bucket(role):
    plan = plan_lens_priority(
        intent_envelope=_make_envelope(primary="parenting"),
        relationship_role=role,
        target_resolved="kid-001",
    )
    assert plan["rule_bucket"] == "child"
    # PFS-2.3: framing hint aligned with user spec ("parenting" = user is parent).
    assert plan["framing_hint"] == "parenting"


@pytest.mark.parametrize("role", ["cofounder", "co-founder", "business partner"])
def test_cofounder_bucket(role):
    plan = plan_lens_priority(
        intent_envelope=_make_envelope(primary="leadership"),
        relationship_role=role,
        target_resolved="cofounder-001",
    )
    assert plan["rule_bucket"] == "cofounder"
    assert plan["framing_hint"] == "cofounder_strategic"


def test_colleague_with_leadership_intent_routes_to_cofounder():
    plan = plan_lens_priority(
        intent_envelope=_make_envelope(primary="leadership"),
        relationship_role="colleague",
        target_resolved="x-001",
    )
    assert plan["rule_bucket"] == "cofounder"


def test_colleague_without_leadership_intent_stays_self():
    plan = plan_lens_priority(
        intent_envelope=_make_envelope(primary="identity"),
        relationship_role="colleague",
        target_resolved="x-001",
    )
    # No spouse/child/cofounder/forum match → falls through to self
    assert plan["rule_bucket"] == "self"


def test_forum_member_bucket():
    plan = plan_lens_priority(
        intent_envelope=_make_envelope(),
        forum_topology={
            "forum_id": "forum-001",
            "active_member_id": "patricia-001",
            "members": [{"id": "patricia-001", "name": "Patricia"}],
        },
    )
    assert plan["rule_bucket"] == "forum_member"
    assert "forum_member:active_member_id_bound" in plan["applied_rules"]
    assert "forum_member:active_in_members" in plan["applied_rules"]


def test_self_bucket_default():
    plan = plan_lens_priority(intent_envelope=_make_envelope(primary="identity"))
    assert plan["rule_bucket"] == "self"
    assert plan["framing_hint"] == "self_inquiry"
    # No modulation applied for self → ordering unchanged
    assert plan["lens_priority_before"] == plan["lens_priority_after"]
    assert plan["reordered"] is False


# ─────────────────────────────────────────────────────────────────────
# Re-ordering correctness
# ─────────────────────────────────────────────────────────────────────

def test_spouse_promotes_relationship_lens():
    plan = plan_lens_priority(
        intent_envelope=_make_envelope(
            primary="relationship",
            lens_priority=["astrology", "human_design", "enneagram",
                           "numerology", "relationship", "timeline"],
        ),
        relationship_role="spouse",
        target_resolved="mel-001",
    )
    # relationship_lens has modulation +0.40 — should rank higher than
    # numerology / timeline.
    after = plan["lens_priority_after"]
    assert after.index("relationship") < after.index("numerology")
    assert plan["reordered"] is True


def test_child_promotes_human_design():
    plan = plan_lens_priority(
        intent_envelope=_make_envelope(
            primary="parenting",
            lens_priority=["astrology", "human_design", "enneagram",
                           "numerology", "relationship", "timeline"],
        ),
        relationship_role="child",
        target_resolved="kid-001",
    )
    # human_design has +0.30 — should stay top-2 (was already #2)
    after = plan["lens_priority_after"]
    assert "human_design" in after[:3]


def test_cofounder_promotes_human_design_and_enneagram():
    plan = plan_lens_priority(
        intent_envelope=_make_envelope(
            primary="leadership",
            lens_priority=["astrology", "human_design", "enneagram",
                           "numerology", "relationship", "timeline"],
        ),
        relationship_role="cofounder",
        target_resolved="cf-001",
    )
    after = plan["lens_priority_after"]
    # human_design (+0.30) and enneagram (+0.25) should both bubble up
    assert after.index("human_design") <= 1
    # enneagram should beat numerology
    assert after.index("enneagram") < after.index("numerology")


# ─────────────────────────────────────────────────────────────────────
# Context-mode behaviour
# ─────────────────────────────────────────────────────────────────────

def test_context_mode_promotes_self_to_forum_when_forum_mode():
    plan = plan_lens_priority(
        intent_envelope=_make_envelope(),
        context_mode="forum",
    )
    # No role, no active member, but forum context → promote to forum_member
    assert plan["rule_bucket"] == "forum_member"
    assert "forum_promotion:self_to_forum_member" in plan["applied_rules"]


def test_context_mode_recorded():
    plan = plan_lens_priority(
        intent_envelope=_make_envelope(),
        relationship_role="spouse",
        context_mode="reflection_chat",
    )
    assert plan["context_mode"] == "reflection_chat"
    assert "context_mode:reflection_chat" in plan["applied_rules"]


# ─────────────────────────────────────────────────────────────────────
# Modulation map sanity
# ─────────────────────────────────────────────────────────────────────

def test_modulation_maps_match_spec():
    assert LENS_MODULATIONS["spouse"]["relationship"] == 0.40
    assert LENS_MODULATIONS["child"]["human_design"] == 0.30
    assert LENS_MODULATIONS["cofounder"]["human_design"] == 0.30
    assert LENS_MODULATIONS["forum_member"]["relationship"] == 0.40
    assert LENS_MODULATIONS["self"] == {}


# ─────────────────────────────────────────────────────────────────────
# PFS-2.4 — sibling_pair bucket
# ─────────────────────────────────────────────────────────────────────

def test_sibling_pair_bucket_exists_in_all_maps():
    """sibling_pair must be present in modulation, framing, and domain
    bias maps — these are the three keyed dicts downstream consumers
    rely on."""
    from services.relationship_orchestration_v1 import DOMAIN_BIAS
    assert "sibling_pair" in LENS_MODULATIONS
    assert "sibling_pair" in FRAMING_HINT
    assert "sibling_pair" in DOMAIN_BIAS
    # Spec — relationship leads, HD+enneagram corroborate
    assert LENS_MODULATIONS["sibling_pair"]["relationship"] == 0.40
    assert LENS_MODULATIONS["sibling_pair"]["human_design"] == 0.25
    assert LENS_MODULATIONS["sibling_pair"]["enneagram"]    == 0.20
    assert DOMAIN_BIAS["sibling_pair"] == "relationship"
    assert FRAMING_HINT["sibling_pair"] == "siblings_among_themselves"


@pytest.mark.parametrize("role", [
    "sibling_pair", "siblings", "sibling-sibling", "brother_brother",
    "sister_sister", "brother_sister", "sister_brother", "twin_pair",
])
def test_sibling_pair_explicit_role_token(role):
    plan = plan_lens_priority(
        intent_envelope=_make_envelope(),
        relationship_role=role,
        target_resolved="sib-001",
    )
    assert plan["rule_bucket"] == "sibling_pair"
    assert plan["framing_hint"] == "siblings_among_themselves"
    assert any("role_match:sibling_pair" in r for r in plan["applied_rules"])
    assert "target_bound" in plan["applied_rules"]


def test_sibling_role_still_resolves_to_sibling_not_sibling_pair():
    """Single sibling (user↔sibling) must continue to land in the
    `sibling` bucket, NOT `sibling_pair`.  Critical regression guard."""
    for role in ("sibling", "brother", "sister", "twin"):
        plan = plan_lens_priority(
            intent_envelope=_make_envelope(),
            relationship_role=role,
            target_resolved="sib-001",
        )
        assert plan["rule_bucket"] == "sibling", (
            f"{role!r} unexpectedly bucketed as {plan['rule_bucket']!r}"
        )


def test_sibling_pair_topology_pair_relationship():
    """Topology signal 1: explicit `pair_relationship` label."""
    plan = plan_lens_priority(
        intent_envelope=_make_envelope(),
        forum_topology={
            "forum_id":           "forum-001",
            "pair_relationship":  "sibling",
        },
    )
    assert plan["rule_bucket"] == "sibling_pair"
    assert "topology_match:sibling_pair" in plan["applied_rules"]


def test_sibling_pair_topology_active_pair_role_between():
    """Topology signal 3: active_pair.role_between is a sibling token."""
    plan = plan_lens_priority(
        intent_envelope=_make_envelope(),
        forum_topology={
            "forum_id": "forum-001",
            "active_pair": {
                "a_id": "kid-001",
                "b_id": "kid-002",
                "role_between": "brother",
            },
        },
    )
    assert plan["rule_bucket"] == "sibling_pair"


def test_sibling_pair_topology_shared_parent():
    """Topology signal 2: pair_members share a parent → siblings of
    each other."""
    plan = plan_lens_priority(
        intent_envelope=_make_envelope(),
        forum_topology={
            "forum_id": "forum-001",
            "pair_members": [
                {"id": "kid-001", "parent_ids": ["parent-007"]},
                {"id": "kid-002", "parent_ids": ["parent-007", "parent-008"]},
            ],
        },
    )
    assert plan["rule_bucket"] == "sibling_pair"


def test_sibling_pair_topology_disjoint_parents_does_not_match():
    """Non-overlapping parent_ids must NOT trigger sibling_pair.
    Critical false-positive guard."""
    plan = plan_lens_priority(
        intent_envelope=_make_envelope(),
        forum_topology={
            "forum_id": "forum-001",
            "pair_members": [
                {"id": "kid-001", "parent_ids": ["parent-007"]},
                {"id": "kid-002", "parent_ids": ["parent-099"]},
            ],
        },
    )
    assert plan["rule_bucket"] != "sibling_pair"


def test_sibling_pair_topology_malformed_does_not_raise():
    """Misshapen topology must never crash the planner — must just
    decline to match."""
    for topo in (
        {"pair_members": "not-a-list"},
        {"pair_members": [None, None]},
        {"pair_members": [{}, {}]},
        {"active_pair": "not-a-dict"},
        {"pair_relationship": 42},
    ):
        plan = plan_lens_priority(
            intent_envelope=_make_envelope(),
            forum_topology=topo,
        )
        assert plan["computed"] is True
        assert plan["rule_bucket"] != "sibling_pair"


def test_sibling_pair_promotes_relationship_and_hd():
    """sibling_pair modulation: relationship (+0.40), HD (+0.25),
    enneagram (+0.20).  Lens ordering must reflect those promotions."""
    plan = plan_lens_priority(
        intent_envelope=_make_envelope(
            primary="relationship",
            lens_priority=["astrology", "human_design", "enneagram",
                           "numerology", "relationship", "timeline"],
        ),
        relationship_role="sibling_pair",
        target_resolved="sib-001",
    )
    after = plan["lens_priority_after"]
    # relationship must beat numerology
    assert after.index("relationship") < after.index("numerology")
    # human_design must stay top-3
    assert "human_design" in after[:3]
    # enneagram must beat numerology
    assert after.index("enneagram") < after.index("numerology")
    assert plan["reordered"] is True


def test_sibling_pair_explicit_role_wins_over_topology():
    """If both an explicit role token AND a topology signal would
    match, the explicit token must win (it is the more specific
    intent declaration)."""
    plan = plan_lens_priority(
        intent_envelope=_make_envelope(),
        relationship_role="sibling_pair",
        forum_topology={
            "pair_relationship":  "sibling",  # would also match
        },
    )
    assert plan["rule_bucket"] == "sibling_pair"
    # explicit role rule wins; topology rule still records is fine but
    # the FIRST applied rule should be the role match
    assert any("role_match:sibling_pair" in r for r in plan["applied_rules"])
