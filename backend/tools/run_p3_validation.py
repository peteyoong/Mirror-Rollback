"""P3 Relationship-Aware Orchestration golden-set runner.

Exercises plan_lens_priority across spouse/child/cofounder/forum_member/
self buckets. Verifies:
    * rule_bucket matches expectation
    * framing_hint matches expectation
    * top lens after re-rank matches expectation (when supplied)
    * applied_rules contains expected substrings

Usage:
    python tools/run_p3_validation.py
"""
from __future__ import annotations

import sys
import json
from pathlib import Path
from typing import Any, Dict, List

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import yaml  # type: ignore

from services.relationship_orchestration_v1 import plan_lens_priority
from services.intent_router_v2 import LENS_WEIGHTS_PER_DOMAIN

TESTS_DIR = BACKEND_DIR / "tests" / "intent_router_v2"
GOLDEN_PATH = TESTS_DIR / "golden_set_relationship_orchestration.yaml"


def _lens_priority_for(domain: str) -> List[str]:
    """Mirror of intent_router_v2._lens_priority_for (private helper)."""
    weights = LENS_WEIGHTS_PER_DOMAIN.get(domain, {})
    return [k for k, _ in sorted(weights.items(), key=lambda kv: -kv[1])]


def run_case(case: Dict[str, Any]) -> Dict[str, Any]:
    envelope = {
        "primary_domain": case.get("primary_domain", "identity"),
        "lens_priority":  _lens_priority_for(case.get("primary_domain", "identity")),
    }
    plan = plan_lens_priority(
        intent_envelope=envelope,
        relationship_role=case.get("relationship_role"),
        target_resolved=case.get("target_resolved"),
        forum_topology=case.get("forum_topology"),
        context_mode=case.get("context_mode"),
    )

    misses: List[str] = []

    if plan["rule_bucket"] != case["expected_bucket"]:
        misses.append(
            f"bucket: expected={case['expected_bucket']}, got={plan['rule_bucket']}"
        )

    expected_hint = case.get("expected_framing_hint")
    if expected_hint and plan["framing_hint"] != expected_hint:
        misses.append(
            f"framing_hint: expected={expected_hint}, got={plan['framing_hint']}"
        )

    expected_top = case.get("expected_top_lens")
    if expected_top:
        after = plan["lens_priority_after"]
        if not after or after[0] != expected_top:
            misses.append(
                f"top_lens: expected={expected_top}, got={after[:1]}"
            )

    expected_rules = case.get("expected_applied_rules_contains") or []
    applied_blob = " ".join(plan["applied_rules"])
    for required in expected_rules:
        if required not in applied_blob:
            misses.append(f"applied_rules missing: {required}")

    return {
        "id":          case.get("id"),
        "pass":        not misses,
        "misses":      misses,
        "bucket":      plan["rule_bucket"],
        "framing":     plan["framing_hint"],
        "top_lens":    (plan["lens_priority_after"] or [None])[0],
        "reordered":   plan["reordered"],
    }


def main() -> None:
    with open(GOLDEN_PATH) as f:
        cases: List[Dict[str, Any]] = yaml.safe_load(f) or []

    results = [run_case(c) for c in cases]
    n = len(results)
    passed = sum(1 for r in results if r["pass"])

    by_bucket: Dict[str, Dict[str, int]] = {}
    for r in results:
        b = r["bucket"]
        bb = by_bucket.setdefault(b, {"n": 0, "passed": 0})
        bb["n"] += 1
        if r["pass"]:
            bb["passed"] += 1

    misses = [r for r in results if not r["pass"]]

    print(json.dumps({
        "router_version": "relationship_orchestration_v1.0.0",
        "suite":          GOLDEN_PATH.name,
        "n":              n,
        "passed":         passed,
        "pass_pct":       round(100.0 * passed / max(n, 1), 1),
        "per_bucket":     {b: {**v, "pct": round(100.0 * v["passed"] / max(v["n"], 1), 1)}
                           for b, v in by_bucket.items()},
        "misses":         misses,
    }, indent=2))


if __name__ == "__main__":
    main()
