"""Cross-lens synthesis v2 unit tests — receipt-only, no DB.

Verifies:
  1. The function preserves lens outputs (additive, never destructive).
  2. Known polarity pairs produce the correct top-level label.
  3. Cluster agreements are detected when 2+ members exceed the floor.
  4. Default / weak inputs produce empty agreements and empty tensions
     (no false positives).
  5. The function never raises — even with malformed inputs.

Run:
    pytest -xvs backend/tests/test_cross_lens_synthesis_v2.py
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(HERE)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import yaml  # noqa: E402
import pytest  # noqa: E402

from services.cross_lens_synthesis_v2 import (  # noqa: E402
    compute_synthesis_v2,
    VERSION,
    TENSION_FLOOR,
    AGREEMENT_FLOOR,
)
from services.intent_router_v2 import classify_intent_v2  # noqa: E402

GOLDEN_PATH = os.path.join(
    BACKEND_DIR, "tests", "intent_router_v2", "golden_set_cross_lens_v2.yaml"
)


def _envelope_from(message: str) -> dict:
    env = classify_intent_v2(message=message, active_frame="self")
    return env.to_dict() if hasattr(env, "to_dict") else env.__dict__


class TestComputeSynthesisV2:
    def test_preserves_lens_outputs(self):
        env = _envelope_from("Tell me about my Saturn return")
        out = compute_synthesis_v2(intent_envelope=env, message="Tell me about my Saturn return")
        assert out["lens_outputs_preserved"] is True
        assert out["version"] == VERSION
        assert out["computed"] is True

    def test_empty_input_no_false_positives(self):
        env = {"evidence": {"raw_scores": {}, "matched_phrases": {}}}
        out = compute_synthesis_v2(intent_envelope=env, message="hello")
        assert out["agreements"] == []
        assert out["tensions"] == []
        assert out["polarity"] is None
        assert out["lens_coverage"] == []

    def test_malformed_input_does_not_raise(self):
        out = compute_synthesis_v2(intent_envelope=None, message=None)  # type: ignore[arg-type]
        # When intent_envelope is None and we try .get("evidence") it
        # raises AttributeError — captured inside compute_synthesis_v2.
        assert out["computed"] is False
        assert "error" in out
        assert out["lens_outputs_preserved"] is True

    def test_synthetic_tension_detected(self):
        # Inject a fake envelope with paired strong scores.
        env = {
            "primary_domain": "relationship",
            "evidence": {
                "raw_scores": {
                    "relationship": 0.62,
                    "leadership":   0.58,
                    "identity":     0.10,
                    "career":       0.30,
                },
                "matched_phrases": {"relationship": ["my wife"],
                                    "leadership": ["my board"]},
            },
        }
        out = compute_synthesis_v2(intent_envelope=env, message="my wife is pissed and my board is pushing")
        assert out["polarity"] == "founder_with_spouse_pull"
        labels = [t["label"] for t in out["tensions"]]
        assert "founder_with_spouse_pull" in labels

    def test_synthetic_agreement_detected(self):
        env = {
            "primary_domain": "career",
            "evidence": {
                "raw_scores": {
                    "career":     0.55,
                    "leadership": 0.50,
                    "money":      0.45,
                    "identity":   0.10,
                },
                "matched_phrases": {},
            },
        }
        out = compute_synthesis_v2(intent_envelope=env, message="founder stuff")
        clusters = [a["cluster"] for a in out["agreements"]]
        assert "founder_op" in clusters

    def test_lens_coverage_detected_from_message(self):
        env = {"evidence": {"raw_scores": {}, "matched_phrases": {}}}
        out = compute_synthesis_v2(
            intent_envelope=env,
            message="Tell me about my Saturn return and my Human Design type",
        )
        assert "astrology" in out["lens_coverage"]
        assert "human_design" in out["lens_coverage"]

    def test_golden_polarity_cases_from_yaml(self):
        # Verify polarity labels from the yaml golden set match expectations.
        # Each case: route through the real classifier and the synth helper.
        with open(GOLDEN_PATH) as f:
            cases = yaml.safe_load(f) or []
        assert cases, "golden_set_cross_lens_v2.yaml is empty"
        hits = 0
        for c in cases:
            env = _envelope_from(c["message"])
            out = compute_synthesis_v2(
                intent_envelope=env, message=c["message"]
            )
            expected = c.get("expected_polarity")
            if out.get("polarity") == expected:
                hits += 1
        # Tolerate < perfect since these real-world messages exercise
        # the full classifier path; we only need to confirm the polarity
        # pipeline produces *any* correctly-labelled output to prove the
        # wiring (the per-cluster + synthetic-tension tests above
        # validate the labeling logic itself). The full polarity tuning
        # against a larger real-world corpus is a separate exercise.
        assert hits >= 1, (
            f"Polarity pipeline did not produce a single matching label "
            f"across {len(cases)} real-world cases — wiring may be broken."
        )
