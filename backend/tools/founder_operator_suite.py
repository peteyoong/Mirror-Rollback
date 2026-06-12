"""founder_operator_suite.py — Reproduces the June 14 30-prompt
Founder/Operator/Spouse/Forum validation suite as a first-class tool
(was previously a one-shot script in /tmp).

Usage:
    python tools/founder_operator_suite.py
    python tools/founder_operator_suite.py --wire-active-member-id   # P4 simulation

Writes:
    audit_reports/B3_FOUNDER_OPERATOR_VALIDATION.json
    audit_reports/B3_FOUNDER_OPERATOR_VALIDATION.md
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone as dt_tz
from pathlib import Path
from typing import Any, Dict, List, Optional

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from services.intent_router_v2 import classify_intent_v2, reset_lexicon_cache  # noqa: E402
from services.relationship_router_v2 import resolve_relationship_context  # noqa: E402

OUT_JSON = BACKEND_DIR / "audit_reports" / "B3_FOUNDER_OPERATOR_VALIDATION.json"
OUT_MD = BACKEND_DIR / "audit_reports" / "B3_FOUNDER_OPERATOR_VALIDATION.md"

# saved_people for spouse/forum prompts.
SAVED_PEOPLE = [
    {"id": "mel-001", "name": "Mel", "role": "spouse",
     "closeness": 0.95, "weight": 0.95},
    {"id": "kara-001", "name": "Kara", "role": "colleague",
     "closeness": 0.6, "weight": 0.6},
]

# Forum topology used in P4-wired mode.
FORUM_TOPOLOGY_KARA = {
    "forum_id": "forum-001",
    "active_member_id": "kara-001",
    "members": [{"id": "kara-001", "name": "Kara"}],
}

# 30-prompt validation suite (10 founder/operator, 10 spouse, 10 forum).
FOUNDER_PROMPTS: List[Dict[str, Any]] = [
    {"i": 1,  "msg": "Should I restructure my leadership team?",                            "exp": "leadership"},
    {"i": 2,  "msg": "My cofounder and I disagree about product direction.",                "exp": "leadership"},
    {"i": 3,  "msg": "Should I let this executive go?",                                     "exp": "leadership"},
    {"i": 4,  "msg": "How do I think about downsizing?",                                    "exp": "leadership"},
    {"i": 5,  "msg": "Which relationship is creating friction in the company?",             "exp": "leadership"},
    {"i": 6,  "msg": "What is the blind spot in my leadership right now?",                  "exp": "leadership"},
    {"i": 7,  "msg": "Am I avoiding a decision?",                                           "exp": "identity"},
    {"i": 8,  "msg": "Should I prioritize fundraising or profitability?",                   "exp": "career"},
    {"i": 9,  "msg": "What dynamic exists between me and my management team?",              "exp": "leadership"},
    {"i": 10, "msg": "What is the next growth constraint in the business?",                 "exp": "career"},
]
SPOUSE_PROMPTS: List[Dict[str, Any]] = [
    {"i": 11, "msg": "How does Mel map to me right now?",                                   "exp": "relationship"},
    {"i": 12, "msg": "What is happening between me and my spouse?",                         "exp": "relationship"},
    {"i": 13, "msg": "What tension are we carrying?",                                       "exp": "relationship"},
    {"i": 14, "msg": "What does Mel most need from me?",                                    "exp": "relationship"},
    {"i": 15, "msg": "How do I show up in this relationship?",                              "exp": "relationship"},
    {"i": 16, "msg": "What relationship pattern keeps repeating?",                          "exp": "relationship"},
    {"i": 17, "msg": "What should I understand about my partner?",                          "exp": "relationship"},
    {"i": 18, "msg": "Where are we aligned?",                                               "exp": "relationship"},
    {"i": 19, "msg": "What dynamic is asking for attention?",                               "exp": "relationship"},
    {"i": 20, "msg": "What is the growth edge in this relationship?",                       "exp": "relationship"},
]
FORUM_PROMPTS: List[Dict[str, Any]] = [
    {"i": 21, "msg": "Tell me about this forum member.",                                    "exp": "relationship"},
    {"i": 22, "msg": "How does this person map to me?",                                     "exp": "relationship"},
    {"i": 23, "msg": "What role do they play in the group?",                                "exp": "relationship"},
    {"i": 24, "msg": "What tension exists between us?",                                     "exp": "relationship"},
    {"i": 25, "msg": "What should I understand about this member?",                         "exp": "relationship"},
    {"i": 26, "msg": "How do I work with them effectively?",                                "exp": "relationship"},
    {"i": 27, "msg": "What contribution do they bring?",                                    "exp": "relationship"},
    {"i": 28, "msg": "How are they experienced by the forum?",                              "exp": "relationship"},
    {"i": 29, "msg": "What relationship pattern exists here?",                              "exp": "relationship"},
    {"i": 30, "msg": "What dynamic is emerging in the forum?",                              "exp": "relationship"},
]

FOUNDER_OK = {"leadership", "career", "identity"}
SPOUSE_OK = {"relationship", "family", "growth"}
FORUM_OK = {"relationship", "growth"}


def _run_case(*, message: str, frame: str, target_id: Optional[str],
              role: Optional[str], forum_topology: Optional[dict]) -> Dict[str, Any]:
    rel = resolve_relationship_context(
        self_user_id="pete-001",
        user_message=message,
        active_frame=frame,
        target_id=target_id,
        saved_people=SAVED_PEOPLE,
        forum_topology=forum_topology,
    )
    env = classify_intent_v2(
        message=message,
        active_frame=frame,
        current_target_id=rel.target or target_id,
        relationship_role=rel.role or role,
    )
    envd = env.to_dict()
    return {
        "primary_domain": envd["primary_domain"],
        "confidence": envd["confidence"],
        "frame": frame,
        "rel_target": rel.target,
        "rel_role": rel.role,
        "rel_context_mode": rel.context_mode,
        "rel_resolution_path": rel.resolution_path,
    }


def run_suite(wire_active_member: bool) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for p in FOUNDER_PROMPTS:
        res = _run_case(message=p["msg"], frame="self", target_id=None,
                        role=None, forum_topology=None)
        passed = res["primary_domain"] in FOUNDER_OK
        rows.append({"category": "founder", **p, **res, "pass": passed})
    for p in SPOUSE_PROMPTS:
        res = _run_case(message=p["msg"], frame="self", target_id="mel-001",
                        role="spouse", forum_topology=None)
        passed = (
            res["primary_domain"] in SPOUSE_OK
            and res["rel_context_mode"] == "RELATIONAL"
            and res["rel_target"] == "mel-001"
        )
        rows.append({"category": "spouse", **p, **res, "pass": passed})
    for p in FORUM_PROMPTS:
        ftop = FORUM_TOPOLOGY_KARA if wire_active_member else None
        res = _run_case(message=p["msg"], frame="forum", target_id=None,
                        role=None, forum_topology=ftop)
        passed = (
            res["primary_domain"] in FORUM_OK
            and res["rel_context_mode"] == "RELATIONAL"
        )
        rows.append({"category": "forum", **p, **res, "pass": passed})

    # Aggregate per-category.
    cats: Dict[str, List[Dict[str, Any]]] = {"founder": [], "spouse": [], "forum": []}
    for r in rows:
        cats[r["category"]].append(r)

    def _stats(items: List[Dict[str, Any]]) -> Dict[str, Any]:
        n = len(items)
        passes = sum(1 for r in items if r["pass"])
        dom_mix = Counter(r["primary_domain"] for r in items)
        return {
            "n": n,
            "passes": passes,
            "pass_rate": round(passes / max(n, 1), 4),
            "predicted_domain_mix": dict(dom_mix),
        }

    summary = {
        "wire_active_member_id": wire_active_member,
        "founder": _stats(cats["founder"]),
        "spouse":  _stats(cats["spouse"]),
        "forum":   _stats(cats["forum"]),
        "overall_pass_rate": round(sum(1 for r in rows if r["pass"]) / 30, 4),
    }
    return {"summary": summary, "rows": rows}


def write_markdown(both: Dict[str, Any]) -> None:
    cur = both["current_wiring"]["summary"]
    p4 = both["p4_wired"]["summary"]

    def cat_md(label: str) -> str:
        c1 = cur[label]
        c2 = p4[label]
        return (
            f"| {label:<8} | "
            f"{c1['pass_rate']*100:5.1f}% ({c1['passes']}/{c1['n']}) | "
            f"{c2['pass_rate']*100:5.1f}% ({c2['passes']}/{c2['n']}) | "
            f"{c1['predicted_domain_mix']} |"
        )

    md = [
        "# B3 — Founder/Operator/Spouse/Forum Validation Suite",
        "",
        f"_Generated: {datetime.now(dt_tz.utc).isoformat()}_",
        "",
        "Re-run of the original June 14 30-prompt suite **after** B3.2 lexicon",
        "expansion, B3.1 educational-mode disambiguation, and P4 forum-topology",
        "plumbing.",
        "",
        "## Aggregate accuracy",
        "",
        "| Category | Current wiring | P4 wired (`active_member_id` supplied) | Domain mix (current) |",
        "|----------|----------------|-----------------------------------------|----------------------|",
        cat_md("founder"),
        cat_md("spouse"),
        cat_md("forum"),
        "",
        f"**Overall pass-rate** — current wiring: {cur['overall_pass_rate']*100:.1f}%, "
        f"P4-wired: {p4['overall_pass_rate']*100:.1f}%.",
        "",
        "## Per-prompt detail (current wiring)",
        "",
        "| # | Category | Prompt | Expected ∈ | Actual | Target | Pass |",
        "|---|----------|--------|------------|--------|--------|------|",
    ]
    expected_label = {"founder": "{leadership,career,identity}",
                      "spouse":  "{relationship,family,growth}",
                      "forum":   "{relationship,growth}"}
    for r in both["current_wiring"]["rows"]:
        md.append(
            f"| {r['i']:>2} | {r['category']:<8} | {r['msg']} | "
            f"{expected_label[r['category']]} | {r['primary_domain']} | "
            f"{r['rel_target'] or '—'} | "
            f"{'✅' if r['pass'] else '❌'} |"
        )
    md.append("")
    md.append("## Per-prompt detail (P4 wired)")
    md.append("")
    md.append("| # | Category | Prompt | Expected ∈ | Actual | Target | Pass |")
    md.append("|---|----------|--------|------------|--------|--------|------|")
    for r in both["p4_wired"]["rows"]:
        md.append(
            f"| {r['i']:>2} | {r['category']:<8} | {r['msg']} | "
            f"{expected_label[r['category']]} | {r['primary_domain']} | "
            f"{r['rel_target'] or '—'} | "
            f"{'✅' if r['pass'] else '❌'} |"
        )
    OUT_MD.write_text("\n".join(md))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wire-active-member-id", action="store_true",
                    help="Pass forum_topology.active_member_id for forum prompts (P4 simulation)")
    ap.add_argument("--both", action="store_true", default=True,
                    help="Run both current and P4-wired modes (default)")
    args = ap.parse_args()

    reset_lexicon_cache()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)

    current = run_suite(wire_active_member=False)
    p4 = run_suite(wire_active_member=True)
    out = {
        "generated_at": datetime.now(dt_tz.utc).isoformat(),
        "current_wiring": current,
        "p4_wired": p4,
    }
    OUT_JSON.write_text(json.dumps(out, indent=2, default=str))
    write_markdown(out)

    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    print()
    print("=== Current wiring ===")
    for cat in ("founder", "spouse", "forum"):
        s = current["summary"][cat]
        print(f"  {cat:<8} pass={s['pass_rate']*100:5.1f}%  "
              f"({s['passes']}/{s['n']})  mix={s['predicted_domain_mix']}")
    print(f"  Overall: {current['summary']['overall_pass_rate']*100:.1f}%")
    print()
    print("=== P4 wired (active_member_id supplied) ===")
    for cat in ("founder", "spouse", "forum"):
        s = p4["summary"][cat]
        print(f"  {cat:<8} pass={s['pass_rate']*100:5.1f}%  "
              f"({s['passes']}/{s['n']})  mix={s['predicted_domain_mix']}")
    print(f"  Overall: {p4['summary']['overall_pass_rate']*100:.1f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
