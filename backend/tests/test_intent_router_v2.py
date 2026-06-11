"""Pytest for intent_router_v2 golden set + retrieval_validation_v1 receipts."""
import os, sys, yaml
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.intent_router_v2 import classify_intent_v2, ROUTER_VERSION
from services.relationship_router_v2 import resolve_relationship_context
from services.retrieval_validation_v1 import build_receipt, mandatory_modules

GOLDEN = Path(__file__).parent / "intent_router_v2" / "golden_set.yaml"


def _load_golden():
    with open(GOLDEN) as f:
        return yaml.safe_load(f) or []


def test_router_version():
    assert ROUTER_VERSION.startswith("intent_router_v2")


def test_golden_set_top1_accuracy():
    rows = _load_golden()
    correct = 0
    failures = []
    for row in rows:
        env = classify_intent_v2(
            message=row["message"],
            active_frame=row.get("active_frame", "self"),
            current_target_id=row.get("current_target_id"),
            relationship_role=row.get("relationship_role"),
        )
        expected = row["expected_primary"]
        if env.primary_domain == expected:
            correct += 1
        else:
            failures.append((row["id"], row["message"], expected, env.primary_domain, env.confidence))
    acc = correct / max(1, len(rows))
    print(f"\nGolden-set top1 accuracy: {correct}/{len(rows)} = {acc:.1%}")
    for f in failures:
        print(f"   ✗ #{f[0]}: '{f[1]}' expected={f[2]} got={f[3]} conf={f[4]}")
    assert acc >= 0.80, f"top-1 accuracy {acc:.1%} below 0.80 floor"


def test_low_confidence_routes_to_general():
    env = classify_intent_v2(message="hello", active_frame="self")
    assert env.primary_domain == "general"
    assert env.confidence <= 0.05


def test_relationship_router_explicit_target():
    r = resolve_relationship_context(
        self_user_id="pete",
        user_message="What's between us today?",
        active_frame="self",
        target_id="mel",
        saved_people=[{"id": "mel", "name": "Mel", "role": "partner", "closeness": 0.9, "weight": 0.95}],
    )
    assert r.context_mode == "RELATIONAL"
    assert r.target == "mel"
    assert r.role == "partner"
    assert "explicit_target_id" in r.resolution_path


def test_relationship_router_name_mention():
    r = resolve_relationship_context(
        self_user_id="pete",
        user_message="How is Mel doing?",
        saved_people=[{"id": "mel", "name": "Mel", "role": "partner", "closeness": 0.9}],
    )
    assert r.target == "mel"
    assert "mentioned_name" in r.resolution_path


def test_relationship_router_pronoun_memory():
    r = resolve_relationship_context(
        self_user_id="pete",
        user_message="What about us today?",
        last_target_id="mel",
        saved_people=[{"id": "mel", "name": "Mel", "role": "partner", "closeness": 0.9}],
    )
    assert r.target == "mel"
    assert "pronoun_memory" in r.resolution_path


def test_retrieval_receipt_pass():
    env = classify_intent_v2(message="How should I navigate this promotion talk?")
    r = build_receipt(
        request_id="req-test",
        intent_envelope=env.to_dict(),
        relationship_resolution=None,
        modules_invoked=mandatory_modules(env.primary_domain),
        payloads={"astrology": "x" * 100, "human_design": "y" * 80, "user_chart": True},
    )
    assert r["validation_status"] in ("PASS", "WARNING")
    assert r["domain_selected"] == env.primary_domain


def test_retrieval_receipt_fail_when_module_missing():
    env = classify_intent_v2(message="What's between Mel and me today?",
                              current_target_id="mel", relationship_role="partner")
    r = build_receipt(
        request_id="req-test-fail",
        intent_envelope=env.to_dict(),
        relationship_resolution=None,
        modules_invoked=["relationship_resolver"],  # intentionally missing others
        payloads={"user_chart": True},
    )
    assert r["validation_status"] == "FAIL"
    assert len(r["mandatory_modules_missing"]) > 0
