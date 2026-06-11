"""intent_router_v2_benchmark.py

Slice B1 validation runner.

Executes the golden set against `classify_intent_v2` (offline tier) and
optionally a second pass with the embeddings tier (when implemented).
Reports:
  - top-1 / top-2 accuracy
  - per-domain misses + confusion matrix
  - low-confidence cases
  - retrieval-receipt coverage (PASS / WARNING / FAIL) using
    retrieval_validation_v1.build_receipt against a representative
    mandatory-module set
  - latency per item (mean, p50, p95)
  - blockers
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure the backend dir is importable when called as a script
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import yaml  # type: ignore

from services.intent_router_v2 import (  # noqa: E402
    classify_intent_v2,
    DOMAINS,
    ROUTER_VERSION,
)
from services.retrieval_validation_v1 import (  # noqa: E402
    build_receipt,
    mandatory_modules,
)

GOLDEN_PATH = BACKEND_DIR / "tests" / "intent_router_v2" / "golden_set.yaml"


def load_cases(path: Path) -> List[Dict[str, Any]]:
    with open(path) as f:
        return yaml.safe_load(f) or []


def run_pass(cases: List[Dict[str, Any]], *, use_embeddings: bool) -> Dict[str, Any]:
    """Run one full pass over the golden set."""
    results: List[Dict[str, Any]] = []
    latencies_ms: List[float] = []
    confusion: Dict[str, Counter] = defaultdict(Counter)
    low_conf: List[Dict[str, Any]] = []
    receipt_status_counts: Counter = Counter()

    # NB: embeddings tier not implemented yet → use_embeddings=True currently
    # returns the same envelope as the offline tier.  We still measure latency
    # delta when that tier is added.
    for case in cases:
        msg = case["message"]
        frame = case.get("active_frame", "self")
        target = case.get("current_target_id")
        role = case.get("relationship_role")

        t0 = time.perf_counter()
        env = classify_intent_v2(
            message=msg,
            active_frame=frame,
            current_target_id=target,
            relationship_role=role,
        )
        if use_embeddings:
            # Reserved for Pass-2 embeddings tier; currently a no-op
            # (records the additional latency budget when wired up).
            pass
        dt_ms = (time.perf_counter() - t0) * 1000
        latencies_ms.append(dt_ms)

        expected_primary = case["expected_primary"]
        envd = env.to_dict()
        predicted = envd["primary_domain"]
        secondary = envd.get("secondary_domains") or []

        # top-1 / top-2 hits
        top1_hit = predicted == expected_primary
        top2_hit = top1_hit or expected_primary in secondary

        # optional gates from the golden set
        expected_secondary_in = case.get("expected_secondary_in") or []
        secondary_check = (
            None if not expected_secondary_in
            else any(s in expected_secondary_in for s in secondary)
        )
        expected_min_conf = case.get("expected_min_confidence")
        expected_max_conf = case.get("expected_max_confidence")
        confidence = envd.get("confidence", 0.0) or 0.0
        confidence_ok = True
        if expected_min_conf is not None and confidence < expected_min_conf:
            confidence_ok = False
        if expected_max_conf is not None and confidence > expected_max_conf:
            confidence_ok = False

        confusion[expected_primary][predicted] += 1
        if confidence < 0.05 and predicted != "general":
            low_conf.append({"id": case.get("id"), "msg": msg,
                             "predicted": predicted, "confidence": confidence})

        # retrieval-receipt coverage: simulate that every mandatory module
        # for the predicted domain is invoked with a non-empty payload
        modules = mandatory_modules(predicted)
        fake_payloads: Dict[str, Any] = {m: {"sim": True} for m in modules}
        receipt = build_receipt(
            request_id=f"bench-{case.get('id')}",
            intent_envelope=envd,
            relationship_resolution=None,
            modules_invoked=modules,
            payloads=fake_payloads,
        )
        receipt_status_counts[receipt["validation_status"]] += 1

        results.append({
            "id": case.get("id"),
            "message": msg,
            "expected": expected_primary,
            "predicted": predicted,
            "secondary": secondary,
            "confidence": confidence,
            "signal_strength": envd.get("signal_strength", 0.0),
            "margin": envd.get("margin", 0.0),
            "top1_hit": top1_hit,
            "top2_hit": top2_hit,
            "secondary_check": secondary_check,
            "confidence_ok": confidence_ok,
            "latency_ms": round(dt_ms, 3),
            "retrieval_status": receipt.get("retrieval_status", receipt["validation_status"]),
            "routing_status": receipt.get("routing_status", "n/a"),
            "fallback_reason": (envd.get("evidence") or {}).get("fallback_reason"),
        })

    total = len(results) or 1
    top1 = sum(1 for r in results if r["top1_hit"])
    top2 = sum(1 for r in results if r["top2_hit"])
    sec_checked = [r for r in results if r["secondary_check"] is not None]
    sec_ok = sum(1 for r in sec_checked if r["secondary_check"])
    conf_gate_failed = [r for r in results if not r["confidence_ok"]]

    # Per-domain misses
    per_domain_misses: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in results:
        if not r["top1_hit"]:
            per_domain_misses[r["expected"]].append({
                "id": r["id"],
                "message": r["message"],
                "predicted": r["predicted"],
                "secondary": r["secondary"],
                "confidence": r["confidence"],
                "signal_strength": r["signal_strength"],
                "margin": r["margin"],
                "fallback_reason": r["fallback_reason"],
            })

    # Confidence distribution histogram (buckets of 0.10)
    buckets = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    conf_hist: Dict[str, int] = {}
    signal_hist: Dict[str, int] = {}
    for i in range(len(buckets) - 1):
        lo, hi = buckets[i], buckets[i + 1]
        key = f"{lo:.1f}-{hi:.1f}"
        conf_hist[key] = sum(1 for r in results if lo <= r["confidence"] < hi or
                             (hi == 1.0 and r["confidence"] >= 1.0))
        signal_hist[key] = sum(1 for r in results if lo <= r["signal_strength"] < hi or
                               (hi == 1.0 and r["signal_strength"] >= 1.0))

    # Routing status breakdown
    routing_counts: Counter = Counter(r["routing_status"] for r in results)
    retrieval_counts: Counter = Counter(r["retrieval_status"] for r in results)

    summary = {
        "router_version": ROUTER_VERSION,
        "pass": "embeddings" if use_embeddings else "offline",
        "total": total,
        "top1_accuracy": round(top1 / total, 4),
        "top2_accuracy": round(top2 / total, 4),
        "secondary_constraint": {
            "checked": len(sec_checked),
            "ok": sec_ok,
            "accuracy": round(sec_ok / max(len(sec_checked), 1), 4),
        },
        "confidence_gate": {
            "failed": len(conf_gate_failed),
            "items": conf_gate_failed,
        },
        "latency_ms": {
            "mean": round(statistics.mean(latencies_ms), 3) if latencies_ms else 0,
            "p50": round(statistics.median(latencies_ms), 3) if latencies_ms else 0,
            "p95": round(sorted(latencies_ms)[int(0.95 * (len(latencies_ms) - 1))], 3)
            if latencies_ms else 0,
            "max": round(max(latencies_ms), 3) if latencies_ms else 0,
        },
        "retrieval_status_counts": dict(retrieval_counts),
        "routing_status_counts": dict(routing_counts),
        "retrieval_pass_rate": round(retrieval_counts.get("PASS", 0) / total, 4),
        "routing_pass_rate": round(routing_counts.get("PASS", 0) / total, 4),
        "confidence_distribution": conf_hist,
        "signal_distribution": signal_hist,
        "per_domain_misses": dict(per_domain_misses),
        "confusion_matrix": {
            exp: dict(cnts) for exp, cnts in confusion.items()
        },
        "low_confidence_cases": low_conf,
        "results": results,
    }
    return summary


def diff_passes(p1: Dict[str, Any], p2: Dict[str, Any]) -> Dict[str, Any]:
    """Compute deltas between offline (p1) and embeddings (p2)."""
    by_id_1 = {r["id"]: r for r in p1["results"]}
    by_id_2 = {r["id"]: r for r in p2["results"]}
    corrected_by_emb = []
    regressed_by_emb = []
    for cid, r1 in by_id_1.items():
        r2 = by_id_2.get(cid)
        if not r2:
            continue
        if not r1["top1_hit"] and r2["top1_hit"]:
            corrected_by_emb.append({"id": cid, "message": r1["message"],
                                     "offline": r1["predicted"],
                                     "embeddings": r2["predicted"]})
        elif r1["top1_hit"] and not r2["top1_hit"]:
            regressed_by_emb.append({"id": cid, "message": r1["message"],
                                     "offline": r1["predicted"],
                                     "embeddings": r2["predicted"]})
    return {
        "top1_delta": round(p2["top1_accuracy"] - p1["top1_accuracy"], 4),
        "top2_delta": round(p2["top2_accuracy"] - p1["top2_accuracy"], 4),
        "latency_delta_mean_ms": round(
            p2["latency_ms"]["mean"] - p1["latency_ms"]["mean"], 3),
        "latency_delta_p95_ms": round(
            p2["latency_ms"]["p95"] - p1["latency_ms"]["p95"], 3),
        "corrected_by_embeddings": corrected_by_emb,
        "regressed_by_embeddings": regressed_by_emb,
    }


def print_section(title: str) -> None:
    bar = "=" * len(title)
    print(f"\n{title}\n{bar}")


def render(report: Dict[str, Any]) -> None:
    print_section(f"PASS: {report['pass']} ({report['router_version']})")
    print(f"Cases:            {report['total']}")
    print(f"Top-1 accuracy:   {report['top1_accuracy']*100:.2f}%")
    print(f"Top-2 accuracy:   {report['top2_accuracy']*100:.2f}%")
    sec = report["secondary_constraint"]
    if sec["checked"]:
        print(f"Secondary check:  {sec['ok']}/{sec['checked']} "
              f"({sec['accuracy']*100:.2f}%)")
    print(f"Retrieval status: {report['retrieval_status_counts']} "
          f"(PASS rate {report['retrieval_pass_rate']*100:.2f}%)")
    print(f"Routing status:   {report['routing_status_counts']} "
          f"(PASS rate {report['routing_pass_rate']*100:.2f}%)")
    print(f"Latency (ms):     mean={report['latency_ms']['mean']}  "
          f"p50={report['latency_ms']['p50']}  "
          f"p95={report['latency_ms']['p95']}  max={report['latency_ms']['max']}")

    print("\nConfidence distribution:")
    for k, v in report["confidence_distribution"].items():
        bar = "#" * v
        print(f"  conf  {k}: {v:3d} {bar}")
    print("\nSignal strength distribution:")
    for k, v in report["signal_distribution"].items():
        bar = "#" * v
        print(f"  sig   {k}: {v:3d} {bar}")

    cg = report["confidence_gate"]
    if cg["failed"]:
        print(f"\nConfidence-gate failures: {cg['failed']}")
        for item in cg["items"]:
            print(f"  - id={item['id']} msg={item['message']!r} "
                  f"predicted={item['predicted']} conf={item['confidence']}")
    if report["per_domain_misses"]:
        print_section("Per-domain misses")
        for dom, misses in report["per_domain_misses"].items():
            print(f"  {dom}: {len(misses)} miss(es)")
            for m in misses:
                print(f"     id={m['id']} → predicted={m['predicted']}, "
                      f"sig={m['signal_strength']}, margin={m['margin']}, "
                      f"fb={m['fallback_reason']}, msg={m['message']!r}")
    if report["low_confidence_cases"]:
        print_section("Low-confidence non-general predictions")
        for lc in report["low_confidence_cases"]:
            print(f"  id={lc['id']} pred={lc['predicted']} "
                  f"conf={lc['confidence']} msg={lc['msg']!r}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--golden", default=str(GOLDEN_PATH),
                    help="comma-separated list of golden-set yaml files")
    ap.add_argument("--json-out", default=None,
                    help="optional path to write the full JSON report")
    ap.add_argument("--skip-embeddings", action="store_true",
                    help="run only the offline pass")
    args = ap.parse_args()

    suite_files = [Path(p.strip()) for p in args.golden.split(",") if p.strip()]
    all_cases: List[Dict[str, Any]] = []
    for sf in suite_files:
        cases = load_cases(sf)
        if not cases:
            print(f"warn: no cases in {sf}", file=sys.stderr)
            continue
        # tag each case with suite name
        suite_name = sf.stem
        for c in cases:
            c.setdefault("suite", suite_name)
        all_cases.extend(cases)
        print(f"  Loaded {len(cases):>3} case(s) from {sf.name}")

    if not all_cases:
        print("No cases found in any golden set", file=sys.stderr)
        return 2

    p1 = run_pass(all_cases, use_embeddings=False)
    render(p1)

    # Per-suite breakdown
    by_suite: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in p1["results"]:
        suite = next((c.get("suite") for c in all_cases if c.get("id") == r["id"]), "default")
        by_suite[suite].append(r)
    if len(by_suite) > 1:
        print_section("Per-suite accuracy")
        for suite, rows in by_suite.items():
            t1 = sum(1 for r in rows if r["top1_hit"]) / len(rows)
            t2 = sum(1 for r in rows if r["top2_hit"]) / len(rows)
            ret_pass = sum(1 for r in rows if r["retrieval_status"] == "PASS") / len(rows)
            rou_pass = sum(1 for r in rows if r["routing_status"] == "PASS") / len(rows)
            print(f"  {suite:<32} n={len(rows):>3}  top1={t1*100:5.1f}%  "
                  f"top2={t2*100:5.1f}%  retrieval_pass={ret_pass*100:5.1f}%  "
                  f"routing_pass={rou_pass*100:5.1f}%")

    full = {"offline": p1}
    if not args.skip_embeddings:
        p2 = run_pass(all_cases, use_embeddings=True)
        render(p2)
        full["embeddings"] = p2
        delta = diff_passes(p1, p2)
        print_section("Delta (embeddings − offline)")
        print(json.dumps(delta, indent=2))
        full["delta"] = delta

    if args.json_out:
        Path(args.json_out).parent.mkdir(parents=True, exist_ok=True)
        with open(args.json_out, "w") as f:
            json.dump(full, f, indent=2, default=str)
        print(f"\nJSON report written → {args.json_out}")

    # Exit non-zero if Pass-1 top-1 < 0.6 (sanity floor)
    return 0 if p1["top1_accuracy"] >= 0.6 else 1


if __name__ == "__main__":
    sys.exit(main())
