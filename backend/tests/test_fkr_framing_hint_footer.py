"""PFS-2.4 — FKR enforcement footer must surface framing_hint /
domain_bias / rule_bucket when an orchestration plan is supplied.

Pure unit tests against `build_evidence_block`.  Do not touch DB or
network.  Backwards compatibility: callers that omit the plan get
exactly the legacy footer shape (no FRAMING HINT block).
"""
from __future__ import annotations

from services.forum_chat_knowledge_retrieval import (
    build_evidence_block,
    _FRAMING_HINT_INSTRUCTIONS,
)


def _make_minimal_evidence():
    """Single-target FKR shape."""
    targets = [{
        "name": "Mel",
        "role": "spouse",
        "source": "edge",
        "user_id": "mel-001",
    }]
    evidence = [{
        "person": {"name": "Mel", "dob": "1985-04-10", "place": "London"},
        "astro":  None,
        "hd":     None,
    }]
    return ["FACT_LOOKUP"], targets, evidence, None


# ──────────────────────────────────────────────────────────────────────
# Backwards compatibility
# ──────────────────────────────────────────────────────────────────────

def test_legacy_callers_omitting_plan_keep_legacy_footer():
    """Old callers (no orchestration_plan kwarg) must produce exactly
    the legacy block — no FRAMING HINT section."""
    modes, targets, evidence, forum = _make_minimal_evidence()
    block = build_evidence_block(modes, targets, evidence, forum)
    assert "FRAMING HINT" not in block
    assert "MANDATORY (FKR v1 enforcement):" in block


def test_uncomputed_plan_keeps_legacy_footer():
    """Plan with computed=False is treated as no-plan."""
    modes, targets, evidence, forum = _make_minimal_evidence()
    block = build_evidence_block(
        modes, targets, evidence, forum,
        orchestration_plan={"computed": False},
    )
    assert "FRAMING HINT" not in block


def test_self_bucket_does_not_surface_framing():
    """`self` bucket carries no meaningful framing (it's the default
    no-op) — must NOT add the FRAMING HINT block to the FKR footer."""
    modes, targets, evidence, forum = _make_minimal_evidence()
    block = build_evidence_block(
        modes, targets, evidence, forum,
        orchestration_plan={
            "computed":     True,
            "rule_bucket":  "self",
            "framing_hint": "self_inquiry",
            "domain_bias":  "self",
        },
    )
    assert "FRAMING HINT" not in block


# ──────────────────────────────────────────────────────────────────────
# Non-default buckets surface framing_hint / domain_bias / rule_bucket
# ──────────────────────────────────────────────────────────────────────

def test_spouse_bucket_surfaces_framing_in_footer():
    modes, targets, evidence, forum = _make_minimal_evidence()
    block = build_evidence_block(
        modes, targets, evidence, forum,
        orchestration_plan={
            "computed":     True,
            "rule_bucket":  "spouse",
            "framing_hint": "couple_dynamic",
            "domain_bias":  "relationship",
        },
    )
    assert "FRAMING HINT" in block
    assert "role_bucket:  spouse" in block
    assert "framing_hint: couple_dynamic" in block
    assert "domain_bias:  relationship" in block
    # Per-bucket micro-directive must surface for spouse
    assert _FRAMING_HINT_INSTRUCTIONS["spouse"] in block
    # Must remain a CORROBORATION instruction, never override evidence
    assert "CORROBORATES" in block
    assert "does NOT" in block


def test_sibling_pair_bucket_surfaces_specific_directive():
    """PFS-2.4 — sibling_pair must produce the specific
    'siblings to each other, anchor in shared origin' directive."""
    modes, targets, evidence, forum = _make_minimal_evidence()
    block = build_evidence_block(
        modes, targets, evidence, forum,
        orchestration_plan={
            "computed":     True,
            "rule_bucket":  "sibling_pair",
            "framing_hint": "siblings_among_themselves",
            "domain_bias":  "relationship",
        },
    )
    assert "role_bucket:  sibling_pair" in block
    assert "framing_hint: siblings_among_themselves" in block
    # The crucial micro-directive: it must distinguish from sibling
    # (user↔sibling) and explicitly orient the read BETWEEN the two
    # siblings, with the user as observer/parent context.
    directive = _FRAMING_HINT_INSTRUCTIONS["sibling_pair"]
    assert directive in block
    assert "BETWEEN them" in directive
    assert "shared origin" in directive


def test_cofounder_bucket_surfaces_work_framing():
    modes, targets, evidence, forum = _make_minimal_evidence()
    block = build_evidence_block(
        modes, targets, evidence, forum,
        orchestration_plan={
            "computed":     True,
            "rule_bucket":  "cofounder",
            "framing_hint": "cofounder_strategic",
            "domain_bias":  "work",
        },
    )
    assert "role_bucket:  cofounder" in block
    assert "domain_bias:  work" in block
    assert _FRAMING_HINT_INSTRUCTIONS["cofounder"] in block


def test_unknown_bucket_still_surfaces_basic_framing_without_directive():
    """An unrecognised bucket label (forward compat) must still print
    the framing/domain hints but omit the bucket-specific directive
    line — never crash."""
    modes, targets, evidence, forum = _make_minimal_evidence()
    block = build_evidence_block(
        modes, targets, evidence, forum,
        orchestration_plan={
            "computed":     True,
            "rule_bucket":  "some_future_bucket",
            "framing_hint": "future_framing",
            "domain_bias":  "future_domain",
        },
    )
    assert "FRAMING HINT" in block
    assert "framing_hint: future_framing" in block
    assert "domain_bias:  future_domain" in block
    # No directive line for unknown bucket
    assert "directive:" not in block


# ──────────────────────────────────────────────────────────────────────
# Resilience
# ──────────────────────────────────────────────────────────────────────

def test_malformed_plan_does_not_crash():
    """Misshapen plans (string instead of dict, missing keys, etc.)
    must never crash the builder — they fall through to the legacy
    footer."""
    modes, targets, evidence, forum = _make_minimal_evidence()
    for bad in (
        None,
        "not-a-dict",
        42,
        [],
        {"computed": True},                       # no fields
        {"computed": True, "rule_bucket": None},  # all-None
    ):
        block = build_evidence_block(
            modes, targets, evidence, forum,
            orchestration_plan=bad,
        )
        assert "MANDATORY (FKR v1 enforcement):" in block


def test_framing_hint_block_appears_before_enforcement_footer():
    """The FRAMING HINT block must be inserted BEFORE the MANDATORY
    enforcement footer (so it precedes the strict instructions and
    sets the frame).  Bucket-order regression guard."""
    modes, targets, evidence, forum = _make_minimal_evidence()
    block = build_evidence_block(
        modes, targets, evidence, forum,
        orchestration_plan={
            "computed":     True,
            "rule_bucket":  "spouse",
            "framing_hint": "couple_dynamic",
            "domain_bias":  "relationship",
        },
    )
    framing_idx = block.find("FRAMING HINT")
    mandatory_idx = block.find("MANDATORY (FKR v1 enforcement):")
    assert framing_idx != -1
    assert mandatory_idx != -1
    assert framing_idx < mandatory_idx


# ──────────────────────────────────────────────────────────────────────
# Directive coverage — every bucket in LENS_MODULATIONS (other than
# `self`) MUST have a directive so the propagation never silently
# emits a "directive: None" line.
# ──────────────────────────────────────────────────────────────────────

def test_every_modulation_bucket_has_a_directive():
    from services.relationship_orchestration_v1 import LENS_MODULATIONS
    missing = []
    for bucket in LENS_MODULATIONS.keys():
        if bucket == "self":
            continue
        if bucket not in _FRAMING_HINT_INSTRUCTIONS:
            missing.append(bucket)
    assert not missing, (
        f"Buckets without a FKR micro-directive: {missing}.  "
        f"Add entries to _FRAMING_HINT_INSTRUCTIONS."
    )
