"""r3b_forensic_validation.py — Phase 4 / R3b forensic validation harness.

Runs the full set of identity-resolution stress tests requested for the
R3b deliverable:
  * MEL CASE
  * FORUM PRECEDENCE
  * COFOUNDER CASE
  * CHILD CASE
  * AMBIGUOUS NAME CASES
  * PRECEDENCE VALIDATION
  * FAILURE TESTS

Outputs:
  * `/app/backend/audit_reports/R3B_FORENSIC_REPORT.md`
  * stdout summary

Read-only.  Does NOT toggle any rollout/cutover flags.  Does NOT touch
P3 surfacing.  Does NOT mutate any DB collections.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Allow `services.*` imports.
sys.path.insert(0, "/app/backend")

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")

from services.mirror_chat_phase4_enrichment import (  # noqa: E402
    resolve_target_via_forums,
    _classify_forum_source,
    _PAIR_FORUM_NAME_RE,
    _FAMILY_FORUM_NAME_RE,
    _SPOUSE_ALIASES,
)
from services.relationship_router_v2 import (  # noqa: E402
    resolve_relationship_context,
    _extract_proper_name_candidates,
)


PETE_ID = "697f0c6abf35c0528ff06954"
MEL_ID = "697ec826ad4b18f75bf42616"
ISAAC_ID = "69dda348de9cb1c83c0780f8"
THADDEUS_ID = "69dd0b2cc92ba973f8838c11"
PAIR_FORUM_ID = "69dd05eaa333335fcbf3ad33"  # Pete & Mel
FAMILY_FORUM_ID = "69dda348de9cb1c83c0780fa"  # Yoong family


# ─────────────────────────────────────────────────────────────────────
# Resolution source inventory  (1)
# ─────────────────────────────────────────────────────────────────────
RESOLUTION_SOURCE_INVENTORY = [
    {
        "source":         "saved_people",
        "where":          "services/relationship_router_v2.py "
                          "(step 2: name in message → saved_people match)",
        "priority":       0,
        "role_inference": "explicit (saved_people.relationship_type)",
        "notes":          "Authoritative.  Wins over any forum-derived source.",
    },
    {
        "source":         "pair_forum",
        "where":          "services/mirror_chat_phase4_enrichment.py "
                          "→ resolve_target_via_forums "
                          "→ _classify_forum_source (regex)",
        "priority":       1,
        "role_inference": "partner (forum name matches _PAIR_FORUM_NAME_RE)",
        "notes":          "Two-person forum named 'X & Y' / 'X and Y' / 'X+Y'.",
    },
    {
        "source":         "family_forum",
        "where":          "services/mirror_chat_phase4_enrichment.py "
                          "→ resolve_target_via_forums "
                          "→ _classify_forum_source (regex)",
        "priority":       2,
        "role_inference": "family (forum name contains 'family' / 'fam')",
        "notes":          "Multi-member forum with 'family' keyword.",
    },
    {
        "source":         "forum_member",
        "where":          "services/mirror_chat_phase4_enrichment.py "
                          "→ resolve_target_via_forums (fallthrough)",
        "priority":       3,
        "role_inference": "None (no role inferred; left to LLM context).",
        "notes":          "Any other shared forum (no pair/family heuristic).",
    },
    {
        "source":         "alias_spouse_via_pair_forum",
        "where":          "services/mirror_chat_phase4_enrichment.py "
                          "→ resolve_target_via_forums (role-noun path)",
        "priority":       1,
        "role_inference": "partner (deterministic)",
        "notes":          "Triggered by 'wife','husband','spouse', etc. "
                          "Resolves to the single non-self member of a "
                          "named pair forum.",
    },
    {
        "source":         "alias_spouse_via_single_other_member",
        "where":          "services/mirror_chat_phase4_enrichment.py "
                          "→ resolve_target_via_forums (role-noun path)",
        "priority":       2,
        "role_inference": "partner (deterministic)",
        "notes":          "Triggered by spouse aliases when forum name "
                          "doesn't match pair regex but forum has exactly "
                          "one other member.",
    },
    {
        "source":         "unresolved",
        "where":          "services/mirror_chat_phase4_enrichment.py "
                          "→ resolve_target_via_forums (fallback)",
        "priority":       99,
        "role_inference": "None.  Surfaces 'target_unresolved_name' to "
                          "the LLM with explicit 'ask the user' framing.",
        "notes":          "Graceful failure mode for unknown names.",
    },
]

# ─────────────────────────────────────────────────────────────────────
# Final precedence ladder  (3)
# ─────────────────────────────────────────────────────────────────────
PRECEDENCE_LADDER = [
    ("explicit_target_id",                    "0a"),
    ("saved_people (name match)",             "0b"),
    ("pronoun_memory + last_target_id",       "0c"),
    ("forum_active_member (forum frame)",     "0d"),
    ("pair_forum",                            "1"),
    ("alias_spouse_via_pair_forum",           "1"),
    ("family_forum",                          "2"),
    ("alias_spouse_via_single_other_member",  "2"),
    ("forum_member",                          "3"),
    ("unresolved → target_unresolved_name",   "99"),
]


# ─────────────────────────────────────────────────────────────────────
# Probe sets  (3-7)
# ─────────────────────────────────────────────────────────────────────
PROBES_MEL = [
    "Tell me about Mel",
    "How does Mel map to me?",
    "What is happening between me and Mel?",
    "Tell me about my wife",
    "How does my spouse map to me?",
    "What should I understand about Melissa?",
]

PROBES_FORUM_PRECEDENCE = [
    # frame variations — the resolver doesn't see "frame" via Pete,
    # so we encode each frame as a `active_frame` argument variation.
    {"message": "Tell me about Mel", "active_frame": "self",
     "label":   "Frame=self"},
    {"message": "Tell me about Mel", "active_frame": "forum",
     "label":   "Frame=forum"},
    {"message": "Tell me about Mel", "active_frame": "member",
     "label":   "Frame=member"},
]

PROBES_COFOUNDER = [
    "Tell me about Jay",
    "Tell me about Jaan",
    "What am I not seeing about JH?",
    "What is happening in Pulsifi leadership?",
]

PROBES_CHILD = [
    "Tell me about Isaac",
    "Tell me about Thaddeus",
    "What does Thaddeus need from me right now?",
]

PROBES_AMBIGUOUS = [
    "Mel",
    "Melissa",
    "wife",
    "spouse",
    "partner",
]

PROBES_FAILURE = [
    "Tell me about Zephyrina",        # unknown person
    "Tell me about Pet",              # partial / substring of Pete
    "Mel or Melissa?",                # multiple possible matches
]


# ─────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────
async def _trace_resolution(
    db, *, user_id: str, message: str, active_frame: str = "self",
    saved_people: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Trace a single message through the full resolution stack.

    Returns the structured trace dict so we can serialise it into the
    forensic report.
    """
    # Step 1 — V2 router (saved_people path)
    sp = saved_people or []
    v2 = resolve_relationship_context(
        self_user_id=user_id,
        user_message=message,
        active_frame=active_frame,
        saved_people=sp,
    )

    # Step 2 — R3b forum fallback (only when V2 didn't already bind)
    forum_resolved: Dict[str, Any] = {}
    if not v2.target:
        forum_resolved = await resolve_target_via_forums(
            db=db,
            user_id=user_id,
            candidate_name=v2.target_unresolved_name,
            message=message,
        )

    # Build the trace
    candidates = _extract_proper_name_candidates(message)
    final_source = (
        "saved_people" if v2.target
        else (forum_resolved.get("resolution_source") or "unresolved")
    )
    final_target_id = (
        v2.target if v2.target
        else forum_resolved.get("resolved_user_id")
    )
    final_role = (
        v2.role if v2.target
        else forum_resolved.get("resolved_role")
    )

    pair_match = any(
        x.get("source") == "pair_forum"
        for x in (forum_resolved.get("all_forums_with_match") or [])
    )
    family_match = any(
        x.get("source") == "family_forum"
        for x in (forum_resolved.get("all_forums_with_match") or [])
    )

    return {
        "message":                  message,
        "active_frame":             active_frame,
        "candidates_extracted":     candidates,
        "v2_router": {
            "target":               v2.target,
            "role":                 v2.role,
            "resolution_path":      v2.resolution_path,
            "target_unresolved_name": v2.target_unresolved_name,
            "missing_data":         v2.missing_data,
            "conflicts":            v2.conflicts,
            "proposed_action":      v2.proposed_action,
        },
        "r3b_forum_fallback":       forum_resolved,
        "telemetry": {
            "target_resolved":          bool(final_target_id),
            "resolved_target_id":       final_target_id,
            "relationship_role":        final_role,
            "target_resolution_source": final_source,
            "pair_forum_match":         pair_match,
            "family_forum_match":       family_match,
            "all_forums_with_match":    forum_resolved.get(
                "all_forums_with_match"
            ) or [],
        },
        "winner": {
            "id":     final_target_id,
            "source": final_source,
            "role":   final_role,
            "why":    _explain_winner(v2, forum_resolved),
        },
    }


def _explain_winner(v2, forum_resolved: Dict[str, Any]) -> str:
    if v2.target:
        return (
            f"saved_people MATCH (priority 0) — name found in user's "
            f"explicit saved_people list; role={v2.role}; "
            f"resolution_path={v2.resolution_path}."
        )
    if forum_resolved.get("found"):
        src = forum_resolved.get("resolution_source")
        all_matches = forum_resolved.get("all_forums_with_match") or []
        if len(all_matches) > 1:
            losers = [m for m in all_matches[1:]]
            loser_strs = [
                f"{m['source']} ('{m['forum_name']}')" for m in losers
            ]
            return (
                f"R3b matched in {len(all_matches)} forums; sorted by "
                f"priority (pair_forum=0 > family_forum=1 > "
                f"forum_member=2). Winner: {src} ('"
                f"{forum_resolved.get('forum_name')}'). Defeated: "
                f"{'; '.join(loser_strs)}."
            )
        return (
            f"R3b single-forum match: {src} ('"
            f"{forum_resolved.get('forum_name')}'). No precedence "
            f"contest needed."
        )
    return (
        "UNRESOLVED — name not in saved_people, not in any of the "
        "user's forums, and no spouse-alias matched a pair-forum."
    )


def _fmt_trace_md(trace: Dict[str, Any]) -> str:
    out = []
    out.append(f"#### Message: `{trace['message']}`")
    if trace.get("active_frame") != "self":
        out.append(f"_active_frame_: `{trace['active_frame']}`")
    out.append("")
    out.append(f"- **Winner**: `{trace['winner']['source']}` → "
               f"id=`{trace['winner']['id']}`, role=`{trace['winner']['role']}`")
    out.append(f"- **Why**: {trace['winner']['why']}")
    out.append("")
    tel = trace["telemetry"]
    out.append("**Telemetry**:")
    out.append("```json")
    out.append(json.dumps({
        "target_resolved":          tel["target_resolved"],
        "resolved_target_id":       tel["resolved_target_id"],
        "relationship_role":        tel["relationship_role"],
        "target_resolution_source": tel["target_resolution_source"],
        "pair_forum_match":         tel["pair_forum_match"],
        "family_forum_match":       tel["family_forum_match"],
        "all_forums_with_match":    tel["all_forums_with_match"],
    }, indent=2))
    out.append("```")
    out.append("")
    # V2 detail
    v2 = trace["v2_router"]
    out.append("<details><summary>V2 router trace</summary>")
    out.append("")
    out.append("```json")
    out.append(json.dumps(v2, indent=2, default=str))
    out.append("```")
    out.append("</details>")
    out.append("")
    fr = trace["r3b_forum_fallback"]
    if fr:
        out.append("<details><summary>R3b forum fallback trace</summary>")
        out.append("")
        out.append("```json")
        out.append(json.dumps(fr, indent=2, default=str))
        out.append("```")
        out.append("</details>")
        out.append("")
    return "\n".join(out)


async def _side_by_side_mel(db, *, saved_people: List[Dict[str, Any]]) -> str:
    """The user explicitly asked for a side-by-side table for Mel
    showing the candidate found / confidence / role / priority /
    accepted-or-rejected for each source.
    """
    # Run the resolver ONCE
    trace = await _trace_resolution(
        db, user_id=PETE_ID,
        message="Tell me about Mel",
        saved_people=saved_people,
    )
    fr = trace["r3b_forum_fallback"] or {}
    all_matches = fr.get("all_forums_with_match") or []

    rows: List[List[str]] = [
        ["Source", "Candidate found?", "Confidence", "Role",
         "Priority", "Accepted/Rejected", "Reason"],
        ["---"] * 7,
    ]

    # saved_people row
    sp_match_names = [
        p["name"] for p in saved_people
        if (p.get("name") or "").lower() == "mel"
    ]
    sp_found = bool(sp_match_names)
    rows.append([
        "saved_people",
        "Yes" if sp_found else "No",
        "1.00 (explicit)" if sp_found else "n/a",
        sp_match_names[0] if sp_found else "n/a",
        "0",
        "Accepted" if sp_found else "Skipped",
        "Mel not in Pete's saved_people"
        if not sp_found else "Mel found in saved_people",
    ])

    # pair_forum row
    pf = next((m for m in all_matches if m["source"] == "pair_forum"), None)
    if pf:
        rows.append([
            "pair_forum",
            f"Yes ('{pf['forum_name']}')",
            "high",
            pf.get("role") or "partner",
            "1",
            "ACCEPTED" if fr.get("resolution_source") == "pair_forum"
            else "Rejected (saved_people wins)",
            "Forum name matches X & Y pattern → partner",
        ])
    else:
        rows.append([
            "pair_forum", "No", "n/a", "n/a", "1", "Skipped",
            "Mel not found in any pair forum"
        ])

    # family_forum row
    ff = next((m for m in all_matches if m["source"] == "family_forum"), None)
    if ff:
        winner_src = fr.get("resolution_source")
        accepted = winner_src == "family_forum"
        if winner_src == "pair_forum":
            rejected_reason = "pair_forum has higher precedence (1 < 2)"
        elif winner_src == "saved_people":
            rejected_reason = "saved_people has higher precedence (0)"
        else:
            rejected_reason = "Accepted"
        rows.append([
            "family_forum",
            f"Yes ('{ff['forum_name']}')",
            "moderate",
            ff.get("role") or "family",
            "2",
            "ACCEPTED" if accepted
            else f"Rejected ({rejected_reason})",
            "Forum name contains 'family' → family role"
            if accepted else rejected_reason,
        ])
    else:
        rows.append([
            "family_forum", "No", "n/a", "n/a", "2", "Skipped",
            "Mel not found in any family forum"
        ])

    # forum_member row
    fm = next((m for m in all_matches if m["source"] == "forum_member"), None)
    if fm:
        rows.append([
            "forum_member",
            f"Yes ('{fm['forum_name']}')",
            "low", "n/a", "3",
            "Rejected (pair/family wins)" if fr.get("resolution_source") != "forum_member"
            else "Accepted",
            "Generic forum membership only",
        ])
    else:
        rows.append([
            "forum_member", "No", "n/a", "n/a", "3", "Skipped",
            "No other (non-pair, non-family) shared forum"
        ])

    # alias mapping row
    rows.append([
        "alias_mapping",
        "n/a (message uses 'Mel' directly)",
        "n/a", "n/a", "1/2", "Not triggered",
        "Spouse-alias path only fires when "
        "message contains 'wife','husband','spouse', etc.",
    ])

    # Pretty-print as markdown
    md_lines = []
    md_lines.append("| " + " | ".join(rows[0]) + " |")
    md_lines.append("| " + " | ".join(rows[1]) + " |")
    for row in rows[2:]:
        md_lines.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(md_lines)


async def _saved_people_promotion_check(db) -> Dict[str, Any]:
    """Simulate what happens if Mel were added to Pete's saved_people.
    No DB mutation — we feed a synthetic saved_people list to the
    resolver and confirm saved_people wins.
    """
    synthetic = [
        {"id": MEL_ID, "name": "Mel", "relationship_type": "spouse",
         "closeness": 0.9, "weight": 0.9, "role": "spouse"},
    ]
    trace_before = await _trace_resolution(
        db, user_id=PETE_ID, message="Tell me about Mel",
        saved_people=[],
    )
    trace_after = await _trace_resolution(
        db, user_id=PETE_ID, message="Tell me about Mel",
        saved_people=synthetic,
    )
    return {
        "before": trace_before["winner"],
        "after":  trace_after["winner"],
        "saved_people_wins":
            trace_after["winner"]["source"] == "saved_people",
    }


# ─────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────
async def main() -> None:
    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = cli[os.environ["DB_NAME"]]

    print(f"=== R3b Forensic Validation @ {datetime.now(timezone.utc).isoformat()} ===")
    print(f"PETE_ID={PETE_ID}  MEL_ID={MEL_ID}")
    print()

    # Real Pete saved_people (for accurate traces)
    pete_saved = []
    async for sp in db.saved_people.find({"user_id": PETE_ID}):
        pete_saved.append({
            "id":    sp.get("id") or str(sp.get("_id")),
            "name":  sp.get("name"),
            "role":  sp.get("relationship_type"),
            "relationship_type": sp.get("relationship_type"),
            "closeness": sp.get("closeness", 0.5),
            "weight":    sp.get("weight", 0.5),
        })
    print(f"Loaded {len(pete_saved)} saved_people for Pete.")

    report_sections: List[str] = []

    # Header
    report_sections.append(
        "# R3b Forum-Topology Fallback — Forensic Validation Report\n"
        f"\n_Generated: {datetime.now(timezone.utc).isoformat()}_\n"
        "\n_Scope: Phase 4 / R3b only.  No rollout/cutover flags were "
        "touched.  No P3 surfacing or P5 work executed.  No DB "
        "mutations._\n"
    )

    # (1) Resolution source inventory
    report_sections.append("## 1. Resolution Source Inventory\n")
    report_sections.append(
        "| Source | Priority | Role Inference | Defined In |\n"
        "|---|---|---|---|\n"
        + "\n".join(
            f"| `{s['source']}` | {s['priority']} | "
            f"{s['role_inference']} | {s['where']} |"
            for s in RESOLUTION_SOURCE_INVENTORY
        )
        + "\n"
    )
    report_sections.append("**Notes**:")
    for s in RESOLUTION_SOURCE_INVENTORY:
        report_sections.append(f"- `{s['source']}` — {s['notes']}")
    report_sections.append("")

    # (3) Precedence ladder
    report_sections.append("## 3. Final Precedence Ladder\n")
    report_sections.append(
        "| Order | Step | Module |\n|---|---|---|\n"
        + "\n".join(
            f"| {prio} | {step} | `relationship_router_v2.py` "
            f"or `mirror_chat_phase4_enrichment.py` |"
            for step, prio in PRECEDENCE_LADDER
        )
        + "\n"
    )
    report_sections.append(
        "_Implementation_: see `_src_priority` in "
        "`resolve_target_via_forums` (`pair_forum=0`, `family_forum=1`, "
        "`forum_member=2`) and the resolution-ladder ordering in "
        "`resolve_relationship_context`.\n"
    )

    # (2) Side-by-side Mel table
    report_sections.append("## 2. Side-by-Side Resolution Trace for Mel "
                           "(`Tell me about Mel`)\n")
    side_by_side_md = await _side_by_side_mel(db, saved_people=pete_saved)
    report_sections.append(side_by_side_md)
    report_sections.append("")

    # (4) Before/after forensic traces — core 4
    report_sections.append("## 4. Forensic Traces — Core 4 Probes\n")
    for msg in [
        "How does Mel map to me?",
        "Tell me about Mel",
        "What is happening between me and Mel?",
        "How does my wife map to me?",
    ]:
        t = await _trace_resolution(db, user_id=PETE_ID, message=msg,
                                    saved_people=pete_saved)
        report_sections.append(_fmt_trace_md(t))

    # (6) Explicit verification — pair_forum beats family_forum for Mel
    report_sections.append(
        "## 6. Pair-Forum vs Family-Forum Precedence Verification\n"
    )
    t_precedence = await _trace_resolution(
        db, user_id=PETE_ID, message="Tell me about Mel",
        saved_people=pete_saved,
    )
    tel = t_precedence["telemetry"]
    pair_wins = (
        tel["pair_forum_match"]
        and tel["family_forum_match"]
        and tel["target_resolution_source"] == "pair_forum"
    )
    report_sections.append(
        f"- `pair_forum_match`: **{tel['pair_forum_match']}** "
        f"(forum: `Pete & Mel`)\n"
        f"- `family_forum_match`: **{tel['family_forum_match']}** "
        f"(forum: `Yoong family`)\n"
        f"- `target_resolution_source` (winner): "
        f"**`{tel['target_resolution_source']}`**\n"
        f"- **Pair-forum precedence held**: "
        f"**{'YES ✅' if pair_wins else 'NO ❌'}**\n"
    )

    # (7) saved_people promotion check
    report_sections.append("## 7. saved_people Precedence Promotion Check\n")
    promo = await _saved_people_promotion_check(db)
    report_sections.append(
        "If Mel is later added to Pete's `saved_people`, the resolver "
        "must prefer `saved_people` over any forum source.\n\n"
        f"- **Before (no saved_people row)**: source=`{promo['before']['source']}`, "
        f"id=`{promo['before']['id']}`, role=`{promo['before']['role']}`\n"
        f"- **After (synthetic saved_people row added)**: "
        f"source=`{promo['after']['source']}`, "
        f"id=`{promo['after']['id']}`, role=`{promo['after']['role']}`\n"
        f"- **saved_people wins**: "
        f"**{'YES ✅' if promo['saved_people_wins'] else 'NO ❌'}**\n"
    )

    # Identity-resolution stress tests (probes)
    report_sections.append("## 5. Identity-Resolution Stress Tests\n")

    async def run_block(title: str, probes: List[Any]) -> None:
        report_sections.append(f"### {title}\n")
        for p in probes:
            if isinstance(p, dict):
                t = await _trace_resolution(
                    db, user_id=PETE_ID,
                    message=p["message"],
                    active_frame=p["active_frame"],
                    saved_people=pete_saved,
                )
                report_sections.append(f"_{p.get('label', '')}_")
            else:
                t = await _trace_resolution(
                    db, user_id=PETE_ID, message=p,
                    saved_people=pete_saved,
                )
            report_sections.append(_fmt_trace_md(t))

    await run_block("Mel Case", PROBES_MEL)
    await run_block("Forum Precedence (frame variations)",
                    PROBES_FORUM_PRECEDENCE)
    await run_block("Cofounder Case (expected: mostly unresolved — no "
                    "Pulsifi forum exists for Pete)", PROBES_COFOUNDER)
    await run_block("Child Case", PROBES_CHILD)
    await run_block("Ambiguous Name Cases", PROBES_AMBIGUOUS)
    await run_block("Failure Tests", PROBES_FAILURE)

    # Spec-compliance proof — at least one example for each priority
    report_sections.append(
        "## 8. Precedence Validation — Examples of Each Tier\n"
    )

    # pair_forum wins
    pair_wins_trace = await _trace_resolution(
        db, user_id=PETE_ID, message="Tell me about Mel",
        saved_people=pete_saved,
    )
    # family_forum wins (Isaac / Thaddeus only in family forum)
    family_wins_trace = await _trace_resolution(
        db, user_id=PETE_ID, message="Tell me about Isaac",
        saved_people=pete_saved,
    )
    # saved_people wins (synthetic — Mel)
    sp_wins_trace = await _trace_resolution(
        db, user_id=PETE_ID, message="Tell me about Mel",
        saved_people=[{
            "id": MEL_ID, "name": "Mel",
            "relationship_type": "spouse",
            "closeness": 0.95, "weight": 0.95, "role": "spouse",
        }],
    )

    report_sections.append("### Tier 0 — saved_people wins\n")
    report_sections.append(_fmt_trace_md(sp_wins_trace))
    report_sections.append("### Tier 1 — pair_forum wins\n")
    report_sections.append(_fmt_trace_md(pair_wins_trace))
    report_sections.append("### Tier 2 — family_forum wins\n")
    report_sections.append(_fmt_trace_md(family_wins_trace))

    # Constraint compliance
    report_sections.append("## 9. Constraint Compliance\n")
    report_sections.append(
        "| Flag | Required | Actual |\n|---|---|---|\n"
        f"| `INTENT_ROUTER_V2_CUTOVER`         | `false` | "
        f"`{os.environ.get('INTENT_ROUTER_V2_CUTOVER','<unset>')}` |\n"
        f"| `INTENT_ROUTER_V2_ROLLOUT_PERCENT` | `10`    | "
        f"`{os.environ.get('INTENT_ROUTER_V2_ROLLOUT_PERCENT','<unset>')}` |\n"
        f"| `RELATIONSHIP_ORCHESTRATION_PROMPT`| `false` | "
        f"`{os.environ.get('RELATIONSHIP_ORCHESTRATION_PROMPT','<unset>')}` |\n"
        f"| `CROSS_LENS_PROMPT_SURFACE`        | `false` | "
        f"`{os.environ.get('CROSS_LENS_PROMPT_SURFACE','<unset>')}` |\n"
        f"| `INTENT_V2_PROMPT_INJECTION`       | `true`  | "
        f"`{os.environ.get('INTENT_V2_PROMPT_INJECTION','<unset>')}` |\n"
        f"| `TIMELINE_V2_READ_ENABLED`         | `true`  | "
        f"`{os.environ.get('TIMELINE_V2_READ_ENABLED','<unset>')}` |\n"
        f"| `FOUNDER_CONTEXT_ENABLED`          | `true`  | "
        f"`{os.environ.get('FOUNDER_CONTEXT_ENABLED','<unset>')}` |\n"
    )

    # ─────────────────────────────────────────────────────────────────
    # 10. Live persistence verification (R3b telemetry persistence fix)
    # ─────────────────────────────────────────────────────────────────
    # Pull the two most-recent receipts for Pete from
    # `mirror_chat_retrieval_receipts` and show that R3b telemetry now
    # makes it onto disk.  This validates the deferred-persist fix.
    report_sections.append(
        "## 10. Live Persistence Verification — `mirror_chat_retrieval_receipts`\n"
    )
    report_sections.append(
        "_During validation, a telemetry gap was discovered: the V2 "
        "receipt was being persisted **before** R3b enrichment ran, so "
        "`target_resolution_source` and `forum_fallback_resolution` "
        "were dropped from the persisted record. The persistence call "
        "was moved to **after** the Phase 4 enrichment block in "
        "`routers/mirror_chat.py`. Below are the two most-recent "
        "receipts for Pete to demonstrate the fix._\n"
    )
    try:
        cur = db.mirror_chat_retrieval_receipts.find(
            {"user_id": PETE_ID}
        ).sort([("computed_at", -1)]).limit(2)
        idx = 0
        async for r in cur:
            r.pop("_id", None)
            idx += 1
            label = "most recent" if idx == 1 else f"#{idx}"
            report_sections.append(f"### Receipt {idx} ({label})\n")
            ff = r.get("forum_fallback_resolution") or {}
            rel = r.get("relationship_resolution") or {}
            report_sections.append(
                f"- `request_id`: `{r.get('request_id')}`\n"
                f"- `computed_at`: `{r.get('computed_at')}`\n"
                f"- `target_resolution_source`: "
                f"**`{r.get('target_resolution_source')}`**\n"
                f"- `forum_fallback_resolution.found`: `{ff.get('found')}`\n"
                f"- `forum_fallback_resolution.resolution_source`: "
                f"`{ff.get('resolution_source')}`\n"
                f"- `forum_fallback_resolution.resolved_name`: "
                f"`{ff.get('resolved_name')}`\n"
                f"- `forum_fallback_resolution.resolved_role`: "
                f"`{ff.get('resolved_role')}`\n"
                f"- `forum_fallback_resolution.forum_name`: "
                f"`{ff.get('forum_name')}`\n"
                f"- `relationship_resolution.target`: `{rel.get('target')}`\n"
                f"- `relationship_resolution.target_name`: "
                f"`{rel.get('target_name')}`\n"
                f"- `relationship_resolution.role`: `{rel.get('role')}`\n"
                f"- `relationship_resolution.resolution_source`: "
                f"`{rel.get('resolution_source')}`\n"
            )
            if ff.get("all_forums_with_match"):
                report_sections.append(
                    "  - `all_forums_with_match`:\n```json\n"
                    f"{json.dumps(ff['all_forums_with_match'], indent=2)}\n```\n"
                )
    except Exception as e:
        report_sections.append(f"_Persistence verification failed: {e}_\n")

    # Write the report
    out_path = "/app/backend/audit_reports/R3B_FORENSIC_REPORT.md"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        f.write("\n".join(report_sections))

    print(f"Report written to: {out_path}")
    print(f"Pair-forum wins for Mel: "
          f"{pair_wins_trace['telemetry']['target_resolution_source'] == 'pair_forum'}")
    print(f"saved_people wins after promotion: "
          f"{sp_wins_trace['telemetry']['target_resolution_source'] == 'saved_people'}")
    print(f"family_forum wins for Isaac: "
          f"{family_wins_trace['telemetry']['target_resolution_source'] == 'family_forum'}")


if __name__ == "__main__":
    asyncio.run(main())
