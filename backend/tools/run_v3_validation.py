"""Lightweight golden-set runner for intent_router_v2 v3 iterations.

Runs one or more golden-set YAMLs against classify_intent_v2 and prints
top-1 / top-2 / routing_pass metrics + per-case misses.

Usage:
    python tools/run_v3_validation.py [path1.yaml path2.yaml ...]
    # if no args, runs the v3 suites by default
"""
from __future__ import annotations

import sys
import json
from pathlib import Path
from typing import Any, Dict, List

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import yaml  # type: ignore

from services.intent_router_v2 import classify_intent_v2, reset_lexicon_cache

TESTS_DIR = BACKEND_DIR / "tests" / "intent_router_v2"

DEFAULT_SUITES = [
    "golden_set.yaml",
    "golden_set_founder.yaml",
    "golden_set_founder_v2.yaml",
    "golden_set_founder_v3.yaml",
    "golden_set_lens_jargon.yaml",
    "golden_set_educational_astrology.yaml",
    "golden_set_educational_astrology_v2.yaml",
    "golden_set_educational_astrology_v3.yaml",
    "golden_set_forum_topology.yaml",
    "golden_set_forum_topology_v2.yaml",
    "golden_set_forum_topology_v3.yaml",
]


def run_suite(suite_path: Path) -> Dict[str, Any]:
    if not suite_path.exists():
        return {"suite": suite_path.name, "skipped": True, "reason": "not found"}
    with open(suite_path) as f:
        cases: List[Dict[str, Any]] = yaml.safe_load(f) or []

    n = len(cases)
    top1 = 0
    top2 = 0
    routing_pass = 0
    misses: List[Dict[str, Any]] = []

    for case in cases:
        msg = case["message"]
        frame = case.get("active_frame", "self")
        target = case.get("current_target_id")
        role = case.get("relationship_role")
        forum_topology = case.get("forum_topology")

        if forum_topology and not target:
            try:
                from services.relationship_router_v2 import resolve_relationship_context
                rel = resolve_relationship_context(
                    message=msg,
                    active_frame=frame,
                    forum_topology=forum_topology,
                )
                # resolver returns dict with target_resolved
                target = (rel or {}).get("target_resolved") or forum_topology.get("active_member_id")
                role = (rel or {}).get("relationship_role") or role
            except Exception:
                target = forum_topology.get("active_member_id")

        env = classify_intent_v2(
            message=msg,
            active_frame=frame,
            current_target_id=target,
            relationship_role=role,
            forum_context=forum_topology,
        )
        primary = env.primary_domain
        secondary = env.secondary_domains or []
        expected_primary = case.get("expected_primary")
        expected_sec_in = case.get("expected_secondary_in") or []

        primary_match = (primary == expected_primary)
        sec_match = primary_match or (primary in expected_sec_in) or any(s in expected_sec_in or s == expected_primary for s in secondary)
        routing_ok = primary_match or (primary in expected_sec_in)

        if primary_match:
            top1 += 1
        if sec_match:
            top2 += 1
        if routing_ok:
            routing_pass += 1
        else:
            misses.append({
                "id": case.get("id"),
                "message": msg,
                "expected": expected_primary,
                "got": primary,
                "secondary": secondary,
                "top_score": env.evidence.get("top_score"),
            })

    return {
        "suite": suite_path.name,
        "n": n,
        "top1_pct": round(100.0 * top1 / max(n, 1), 1),
        "top2_pct": round(100.0 * top2 / max(n, 1), 1),
        "routing_pass_pct": round(100.0 * routing_pass / max(n, 1), 1),
        "misses": misses,
    }


def main() -> None:
    reset_lexicon_cache()
    suites = sys.argv[1:] or DEFAULT_SUITES
    suite_paths = [
        Path(s) if Path(s).is_absolute() else TESTS_DIR / s
        for s in suites
    ]

    results = [run_suite(p) for p in suite_paths]
    summary = {
        "router_version": "intent_router_v2",
        "suites": results,
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
