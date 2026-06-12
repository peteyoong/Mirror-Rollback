"""PFS-2.3 shadow probes — pre-vs-post topology orchestration traces.

Read-only validation harness. For every probe we:
  1. Resolve target via PFS-2.1 topology-first resolver.
  2. Compute the OLD P3 plan with the pre-PFS-2.1 role (None or `partner`).
  3. Compute the NEW PFS-2.3 plan with the post-topology role.
  4. Diff `rule_bucket`, `framing_hint`, `domain_bias`, `lens_priority`.

Probes (per PFS-2.3 spec):
  • Mel       (Pete's spouse via topology) → role=spouse expected
  • Isaac     (no topology edge; family forum member) → role=family (PFS-1 heuristic)
  • Jaan      (no member in preview; cofounder per spec) — ENVIRONMENTAL N/A
                synthetic role injection used to demonstrate cofounder bucket
  • Advisor   (synthetic — no advisor edge in preview) — synthetic role
                injection used to demonstrate advisor bucket
"""
import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional

from dotenv import load_dotenv

load_dotenv("/app/backend/.env")

sys.path.insert(0, "/app/backend")

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

from services.mirror_chat_phase4_enrichment import (  # noqa: E402
    resolve_target_via_forums,
)
from services.relationship_orchestration_v1 import (  # noqa: E402
    plan_lens_priority,
)


PETE_ID = "697f0c6abf35c0528ff06954"


def _make_envelope(primary="general"):
    return {
        "primary_domain": primary,
        "lens_priority": [
            "astrology", "human_design", "enneagram",
            "numerology", "relationship", "timeline",
        ],
        "confidence": 0.6,
    }


async def diff_plan(label: str,
                    *,
                    resolved: Optional[Dict[str, Any]],
                    synthetic_role: Optional[str] = None,
                    primary_domain: str = "general") -> None:
    """Print pre/post orchestration plan diff for a probe.

    `resolved` is the dict returned by `resolve_target_via_forums`.
    `synthetic_role` is used for probes where Preview DB has no edge —
    we *inject* the role to demonstrate the orchestration bucket the
    expanded lexicon would assign in production.
    """
    print(f"\n──────── PROBE: {label} ────────")
    if resolved:
        print(f"  resolver  : found={resolved.get('found')} "
              f"role={resolved.get('resolved_role')!r} "
              f"topology={resolved.get('topology_role_found')} "
              f"topology_role_type={resolved.get('topology_role_type')!r}")
    if synthetic_role:
        print(f"  synthetic : role={synthetic_role!r} "
              f"(no edge in Preview — demonstrating lexicon coverage)")

    # PRE-PFS-2.3 simulation: feed plan_lens_priority with the
    # pre-topology role (None for Mel because V2 router has no
    # saved_people row for Mel; synthetic roles always become None
    # pre-topology because they have no V2 path either).
    pre_role: Optional[str] = None  # always None pre-PFS-2.3 for these probes
    pre_target = (resolved or {}).get("resolved_user_id")
    pre_plan = plan_lens_priority(
        intent_envelope=_make_envelope(primary_domain),
        relationship_role=pre_role,
        target_resolved=pre_target,
    )

    # POST-PFS-2.3: feed plan_lens_priority with the topology-resolved
    # role (or synthetic role).
    post_role = (
        synthetic_role
        if synthetic_role
        else (resolved or {}).get("resolved_role")
    )
    post_target = (resolved or {}).get("resolved_user_id") or "synthetic-001"
    post_plan = plan_lens_priority(
        intent_envelope=_make_envelope(primary_domain),
        relationship_role=post_role,
        target_resolved=post_target,
    )

    print(f"  PRE-2.3 plan : bucket={pre_plan['rule_bucket']!r} "
          f"framing={pre_plan['framing_hint']!r} "
          f"domain_bias={pre_plan.get('domain_bias')!r}")
    print(f"                 lens_priority={pre_plan['lens_priority_after']}")
    print(f"  POST-2.3 plan: bucket={post_plan['rule_bucket']!r} "
          f"framing={post_plan['framing_hint']!r} "
          f"domain_bias={post_plan.get('domain_bias')!r}")
    print(f"                 lens_priority={post_plan['lens_priority_after']}")
    if post_plan['lens_priority_after'] != pre_plan['lens_priority_after']:
        print("  LENS_DIFF    : reordered ✓")
    else:
        print("  LENS_DIFF    : unchanged")
    print(f"  applied_rules (post): {post_plan['applied_rules']}")


async def main():
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]

    print("=" * 78)
    print("PFS-2.3 SHADOW ORCHESTRATION PROBES")
    print(f"Preview DB: {os.environ['DB_NAME']}")
    print(f"Run at: {datetime.utcnow().isoformat()}Z")
    print("=" * 78)

    # Probe 1 — Mel (real topology edge in preview).
    mel = await resolve_target_via_forums(
        db=db, user_id=PETE_ID,
        candidate_name="Mel",
        message="How does Mel map to me?",
    )
    await diff_plan("1. Mel — spouse via topology edge",
                    resolved=mel,
                    primary_domain="relationship")

    # Probe 2 — Isaac (member in family forum, no topology edge).
    isaac = await resolve_target_via_forums(
        db=db, user_id=PETE_ID,
        candidate_name="Isaac",
        message="How does Isaac map to me?",
    )
    await diff_plan(
        "2. Isaac — family_forum heuristic (ENVIRONMENTAL N/A for topology)",
        resolved=isaac,
        primary_domain="relationship",
    )

    # Probe 3 — Jaan (no member in preview at all; demonstrate cofounder
    # lexicon coverage by synthetic injection).
    jaan = await resolve_target_via_forums(
        db=db, user_id=PETE_ID,
        candidate_name="Jaan",
        message="How does Jaan map to me?",
    )
    print(f"\n  [resolver-only sanity] Jaan resolved="
          f"{jaan.get('found')} ← expected False in Preview")
    await diff_plan(
        "3. Jaan — synthetic cofounder injection (lexicon coverage demo)",
        resolved=jaan,
        synthetic_role="cofounder",
        primary_domain="leadership",
    )

    # Probe 4 — Advisor (synthetic — no advisor edge in preview).
    await diff_plan(
        "4. Advisor — synthetic advisor injection (lexicon coverage demo)",
        resolved=None,
        synthetic_role="advisor",
        primary_domain="leadership",
    )

    # Additional buckets exercise (proves no role silently lands on self)
    print("\n" + "=" * 78)
    print("ADDITIONAL LEXICON COVERAGE EXERCISE")
    print("=" * 78)
    for role in [
        "spouse", "former_partner", "child", "parent", "sibling",
        "cofounder", "business_partner", "advisor", "investor",
        "manager", "employee", "collaborator",
        "mentor", "mentee", "coach", "coachee",
        "authority_figure", "close_friend", "forum_mate", "other",
    ]:
        plan = plan_lens_priority(
            intent_envelope=_make_envelope("general"),
            relationship_role=role,
            target_resolved="syn-001",
        )
        print(f"  role={role:<18} → bucket={plan['rule_bucket']:<18} "
              f"framing={plan['framing_hint']:<22} "
              f"domain_bias={plan.get('domain_bias')}")

    # Regression — unknown role still self
    print("\n" + "=" * 78)
    print("REGRESSION — UNKNOWN ROLE / NO ROLE")
    print("=" * 78)
    for label, role in [
        ("None",             None),
        ("empty string",     ""),
        ("unknown_token",    "qwertyxyz"),
    ]:
        plan = plan_lens_priority(
            intent_envelope=_make_envelope("general"),
            relationship_role=role,
            target_resolved=None,
        )
        print(f"  role={label:<18} → bucket={plan['rule_bucket']:<12} "
              f"framing={plan['framing_hint']:<22} "
              f"applied={plan['applied_rules']}")

    print("\n" + "=" * 78)
    print("PROBE RUN COMPLETE")
    print("=" * 78)


if __name__ == "__main__":
    asyncio.run(main())
