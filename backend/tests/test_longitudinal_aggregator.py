"""
P5: Longitudinal Aggregator Tests
=================================

Tests for the longitudinal evidence store and aggregator system.

These tests verify:
1. No raw text is stored (only derived signals)
2. Per-event affinity clamp works (<=0.03)
3. Aggregation produces stable outputs for fixed inputs
4. Upshift/downshift rules obey thresholds
5. Summary returns expected schema
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from longitudinal_aggregator import (
    clamp_affinity,
    validate_and_clamp_signals,
    create_evidence_document,
    derive_signals_from_enneagram_result,
    compute_recency_weight,
    compute_type_stability,
    compute_wing_stability,
    compute_top_types_over_time,
    compute_confidence_modifier,
    compute_recommended_next_step,
    compute_longitudinal_summary,
    get_empty_longitudinal_summary,
    EvidenceSource,
    ConfidenceModifier,
    RecommendedNextStep,
    MAX_AFFINITY_PER_EVENT,
    SIGNAL_SCHEMA_VERSION
)


# ============================================
# TEST: AFFINITY CLAMPING
# ============================================

class TestAffinityClamping:
    """Tests for per-event affinity clamping."""
    
    def test_clamp_within_range(self):
        """Values within range should not be clamped."""
        assert clamp_affinity(0.01) == 0.01
        assert clamp_affinity(0.02) == 0.02
        assert clamp_affinity(0.03) == 0.03
        assert clamp_affinity(-0.01) == -0.01
    
    def test_clamp_exceeds_max(self):
        """Values exceeding max should be clamped to max."""
        assert clamp_affinity(0.05) == MAX_AFFINITY_PER_EVENT
        assert clamp_affinity(0.10) == MAX_AFFINITY_PER_EVENT
        assert clamp_affinity(1.0) == MAX_AFFINITY_PER_EVENT
    
    def test_clamp_below_min(self):
        """Values below min should be clamped to -max."""
        assert clamp_affinity(-0.05) == -MAX_AFFINITY_PER_EVENT
        assert clamp_affinity(-0.10) == -MAX_AFFINITY_PER_EVENT
        assert clamp_affinity(-1.0) == -MAX_AFFINITY_PER_EVENT
    
    def test_clamp_zero(self):
        """Zero should remain zero."""
        assert clamp_affinity(0.0) == 0.0


# ============================================
# TEST: SIGNAL VALIDATION
# ============================================

class TestSignalValidation:
    """Tests for signal validation and clamping."""
    
    def test_valid_signals(self):
        """Valid signals should pass validation."""
        signals = {
            "type_affinities": {"6": 0.02, "7": 0.01},
            "wing_affinities": {"6": 0.02},
            "stress_style": "vigilance",
            "avoidance_style": "uncertainty",
            "confidence_hint": 0.7
        }
        result = validate_and_clamp_signals(signals)
        
        assert result["type_affinities"]["6"] == 0.02
        assert result["type_affinities"]["7"] == 0.01
        assert result["wing_affinities"]["6"] == 0.02
        assert result["stress_style"] == "vigilance"
        assert result["avoidance_style"] == "uncertainty"
        assert result["confidence_hint"] == 0.7
    
    def test_clamps_excessive_affinities(self):
        """Affinities exceeding max should be clamped."""
        signals = {
            "type_affinities": {"6": 0.10},  # Exceeds max
            "wing_affinities": {"8": 0.20},  # Exceeds max
            "confidence_hint": 0.5
        }
        result = validate_and_clamp_signals(signals)
        
        assert result["type_affinities"]["6"] == MAX_AFFINITY_PER_EVENT
        assert result["wing_affinities"]["8"] == MAX_AFFINITY_PER_EVENT
    
    def test_filters_invalid_type_keys(self):
        """Invalid type keys (non-numeric, out of range) should be filtered."""
        signals = {
            "type_affinities": {"6": 0.02, "invalid": 0.01, "10": 0.01, "0": 0.01},
            "wing_affinities": {},
            "confidence_hint": 0.5
        }
        result = validate_and_clamp_signals(signals)
        
        assert "6" in result["type_affinities"]
        assert "invalid" not in result["type_affinities"]
        assert "10" not in result["type_affinities"]
        assert "0" not in result["type_affinities"]
    
    def test_unknown_stress_style_becomes_other(self):
        """Unknown stress style should become 'other'."""
        signals = {
            "type_affinities": {},
            "wing_affinities": {},
            "stress_style": "unknown_value",
            "confidence_hint": 0.5
        }
        result = validate_and_clamp_signals(signals)
        assert result["stress_style"] == "other"
    
    def test_null_styles(self):
        """Null/None styles should become 'null'."""
        signals = {
            "type_affinities": {},
            "wing_affinities": {},
            "stress_style": None,
            "avoidance_style": None,
            "confidence_hint": 0.5
        }
        result = validate_and_clamp_signals(signals)
        assert result["stress_style"] == "null"
        assert result["avoidance_style"] == "null"
    
    def test_confidence_hint_clamped_to_range(self):
        """Confidence hint should be clamped to 0-1."""
        signals = {
            "type_affinities": {},
            "wing_affinities": {},
            "confidence_hint": 1.5
        }
        result = validate_and_clamp_signals(signals)
        assert result["confidence_hint"] == 1.0
        
        signals["confidence_hint"] = -0.5
        result = validate_and_clamp_signals(signals)
        assert result["confidence_hint"] == 0.0


# ============================================
# TEST: NO RAW TEXT STORAGE
# ============================================

class TestNoRawTextStorage:
    """Tests ensuring no raw text is stored."""
    
    def test_evidence_document_has_no_raw_text_field(self):
        """Evidence documents should not have any raw text fields."""
        signals = {
            "type_affinities": {"6": 0.02},
            "wing_affinities": {},
            "confidence_hint": 0.5
        }
        doc = create_evidence_document(
            user_id="test_user",
            source="reflection_chat",
            signals=signals
        )
        
        # Check no raw text fields
        assert "raw_text" not in doc
        assert "text" not in doc
        assert "message" not in doc
        assert "content" not in doc
        assert "input" not in doc
        
        # Check signals don't have text
        assert "raw_text" not in doc["signals"]
    
    def test_derived_signals_have_no_text(self):
        """Signals derived from Enneagram results should have no text."""
        result = {
            "inferred_core": 6,
            "inferred_wing": 7,
            "confidence_tier": "medium",
            "top_candidates": [
                {"type": 6, "probability": 0.4},
                {"type": 7, "probability": 0.3}
            ]
        }
        signals = derive_signals_from_enneagram_result(result, "short")
        
        # Check no text fields
        for key, value in signals.items():
            if isinstance(value, str):
                # String values should be enum values, not freeform text
                assert value in ["vigilance", "reframing", "withdrawal", "control", 
                                "uncertainty", "conflict", "limitation", "intensity",
                                "other", "null", None]


# ============================================
# TEST: SIGNAL DERIVATION
# ============================================

class TestSignalDerivation:
    """Tests for deriving signals from Enneagram results."""
    
    def test_derive_from_short_assessment(self):
        """Derive signals from a short assessment."""
        result = {
            "inferred_core": 7,
            "inferred_wing": 6,
            "confidence_tier": "medium",
            "top_candidates": [
                {"type": 7, "probability": 0.45},
                {"type": 3, "probability": 0.25},
                {"type": 9, "probability": 0.15}
            ]
        }
        signals = derive_signals_from_enneagram_result(result, "short")
        
        # Check type affinities exist and are clamped
        assert "7" in signals["type_affinities"]
        assert signals["type_affinities"]["7"] <= MAX_AFFINITY_PER_EVENT
        
        # Check wing affinity for determined wing
        assert "6" in signals["wing_affinities"]
        
        # Check confidence hint
        assert signals["confidence_hint"] == 0.5  # medium tier
    
    def test_derive_with_balanced_wing(self):
        """Derive signals when wing is balanced."""
        result = {
            "inferred_core": 5,
            "inferred_wing": "balanced",
            "confidence_tier": "low",
            "top_candidates": [{"type": 5, "probability": 0.35}]
        }
        signals = derive_signals_from_enneagram_result(result, "short")
        
        # Both adjacent wings should have affinity
        assert "4" in signals["wing_affinities"]
        assert "6" in signals["wing_affinities"]
        assert signals["wing_affinities"]["4"] == 0.01
        assert signals["wing_affinities"]["6"] == 0.01
    
    def test_derive_with_null_wing(self):
        """Derive signals when wing is null."""
        result = {
            "inferred_core": 8,
            "inferred_wing": None,
            "confidence_tier": "low",
            "top_candidates": [{"type": 8, "probability": 0.30}]
        }
        signals = derive_signals_from_enneagram_result(result, "short")
        
        # No wing affinities for null wing
        assert len(signals["wing_affinities"]) == 0
    
    def test_confidence_tier_mapping(self):
        """Test confidence tier to hint mapping."""
        for tier, expected in [("low", 0.2), ("medium", 0.5), ("high", 0.8)]:
            result = {
                "inferred_core": 1,
                "inferred_wing": 9,
                "confidence_tier": tier,
                "top_candidates": []
            }
            signals = derive_signals_from_enneagram_result(result, "short")
            assert signals["confidence_hint"] == expected


# ============================================
# TEST: AGGREGATION STABILITY
# ============================================

class TestAggregationStability:
    """Tests for stable aggregation outputs."""
    
    def get_sample_events(self, top_type="6", count=5):
        """Generate sample events for testing."""
        now = datetime.now(timezone.utc)
        events = []
        for i in range(count):
            events.append({
                "created_at": (now - timedelta(days=i)).isoformat(),
                "source": "enneagram_short",
                "signals": {
                    "type_affinities": {top_type: 0.02, "7": 0.01},
                    "wing_affinities": {"5": 0.02},
                    "confidence_hint": 0.5
                }
            })
        return events
    
    def test_type_stability_all_same(self):
        """Type stability should be 1.0 when all events have same top type."""
        events = self.get_sample_events(top_type="6", count=10)
        now = datetime.now(timezone.utc)
        
        stability = compute_type_stability(events, now)
        assert stability > 0.95  # Allow for small recency weight variations
    
    def test_type_stability_mixed(self):
        """Type stability should be lower with mixed top types."""
        now = datetime.now(timezone.utc)
        events = []
        # 5 events with type 6, 5 events with type 7
        for i in range(5):
            events.append({
                "created_at": (now - timedelta(days=i)).isoformat(),
                "source": "enneagram_short",
                "signals": {"type_affinities": {"6": 0.02}, "wing_affinities": {}}
            })
        for i in range(5, 10):
            events.append({
                "created_at": (now - timedelta(days=i)).isoformat(),
                "source": "enneagram_short",
                "signals": {"type_affinities": {"7": 0.02}, "wing_affinities": {}}
            })
        
        stability = compute_type_stability(events, now)
        assert stability < 0.7  # Should be lower than single-type case
    
    def test_empty_events_stability(self):
        """Empty events should return 0 stability."""
        now = datetime.now(timezone.utc)
        assert compute_type_stability([], now) == 0.0
        assert compute_wing_stability([], now) == 0.0
    
    def test_deterministic_output(self):
        """Same input should produce same output."""
        events = self.get_sample_events(top_type="6", count=10)
        
        result1 = compute_longitudinal_summary(events, days_window=30)
        result2 = compute_longitudinal_summary(events, days_window=30)
        
        assert result1["longitudinal"]["type_stability"] == result2["longitudinal"]["type_stability"]
        assert result1["longitudinal"]["wing_stability"] == result2["longitudinal"]["wing_stability"]


# ============================================
# TEST: CONFIDENCE MODIFIER RULES
# ============================================

class TestConfidenceModifierRules:
    """Tests for confidence modifier threshold enforcement."""
    
    def test_upshift_requires_deep_or_10_events(self):
        """Upshift requires deep assessment OR >=10 events."""
        now = datetime.now(timezone.utc)
        
        # 5 short events with perfect stability - should NOT upshift
        events_short = []
        for i in range(5):
            events_short.append({
                "created_at": (now - timedelta(days=i)).isoformat(),
                "source": "enneagram_short",
                "signals": {"type_affinities": {"6": 0.02}, "wing_affinities": {}}
            })
        
        modifier = compute_confidence_modifier(
            events_short,
            type_stability=0.9,
            top_types=[{"type": 6, "share": 0.85}]
        )
        assert modifier != ConfidenceModifier.UPSHIFT.value
        
        # Same events but with deep assessment - should upshift
        events_short[0]["source"] = "enneagram_deep"
        modifier = compute_confidence_modifier(
            events_short,
            type_stability=0.9,
            top_types=[{"type": 6, "share": 0.85}]
        )
        assert modifier == ConfidenceModifier.UPSHIFT.value
    
    def test_upshift_requires_stability_75(self):
        """Upshift requires type_stability >= 0.75."""
        now = datetime.now(timezone.utc)
        events = [
            {"created_at": now.isoformat(), "source": "enneagram_deep", "signals": {}}
        ] * 15
        
        # Stability 0.74 - should NOT upshift
        modifier = compute_confidence_modifier(
            events,
            type_stability=0.74,
            top_types=[{"type": 6, "share": 0.85}]
        )
        assert modifier != ConfidenceModifier.UPSHIFT.value
        
        # Stability 0.75 - should upshift
        modifier = compute_confidence_modifier(
            events,
            type_stability=0.75,
            top_types=[{"type": 6, "share": 0.85}]
        )
        assert modifier == ConfidenceModifier.UPSHIFT.value
    
    def test_upshift_requires_top1_share_70(self):
        """Upshift requires top-1 share >= 0.70."""
        now = datetime.now(timezone.utc)
        events = [
            {"created_at": now.isoformat(), "source": "enneagram_deep", "signals": {}}
        ] * 15
        
        # Share 0.69 - should NOT upshift
        modifier = compute_confidence_modifier(
            events,
            type_stability=0.90,
            top_types=[{"type": 6, "share": 0.69}]
        )
        assert modifier != ConfidenceModifier.UPSHIFT.value
        
        # Share 0.70 - should upshift
        modifier = compute_confidence_modifier(
            events,
            type_stability=0.90,
            top_types=[{"type": 6, "share": 0.70}]
        )
        assert modifier == ConfidenceModifier.UPSHIFT.value
    
    def test_downshift_requires_low_stability_and_volume(self):
        """Downshift requires stability < 0.50 AND volume >= 8."""
        now = datetime.now(timezone.utc)
        
        # 7 events, low stability - should NOT downshift (not enough volume)
        events_7 = [
            {"created_at": now.isoformat(), "source": "enneagram_short", "signals": {}}
        ] * 7
        modifier = compute_confidence_modifier(
            events_7,
            type_stability=0.40,
            top_types=[{"type": 6, "share": 0.30}]
        )
        assert modifier != ConfidenceModifier.DOWNSHIFT.value
        
        # 8 events, low stability - should downshift
        events_8 = [
            {"created_at": now.isoformat(), "source": "enneagram_short", "signals": {}}
        ] * 8
        modifier = compute_confidence_modifier(
            events_8,
            type_stability=0.40,
            top_types=[{"type": 6, "share": 0.30}]
        )
        assert modifier == ConfidenceModifier.DOWNSHIFT.value
    
    def test_downshift_requires_stability_below_50(self):
        """Downshift requires stability < 0.50."""
        now = datetime.now(timezone.utc)
        events = [
            {"created_at": now.isoformat(), "source": "enneagram_short", "signals": {}}
        ] * 10
        
        # Stability 0.50 - should NOT downshift
        modifier = compute_confidence_modifier(
            events,
            type_stability=0.50,
            top_types=[{"type": 6, "share": 0.30}]
        )
        assert modifier != ConfidenceModifier.DOWNSHIFT.value
        
        # Stability 0.49 - should downshift
        modifier = compute_confidence_modifier(
            events,
            type_stability=0.49,
            top_types=[{"type": 6, "share": 0.30}]
        )
        assert modifier == ConfidenceModifier.DOWNSHIFT.value


# ============================================
# TEST: RECOMMENDED NEXT STEP
# ============================================

class TestRecommendedNextStep:
    """Tests for recommended next step logic."""
    
    def test_high_stability_returns_none(self):
        """High stability should recommend 'none'."""
        events = [{"source": "enneagram_short"}]
        step = compute_recommended_next_step(events, type_stability=0.80)
        assert step == RecommendedNextStep.NONE.value
    
    def test_low_stability_short_only_recommends_deep(self):
        """Low stability with only short assessment should recommend deep."""
        events = [{"source": "enneagram_short"}]
        step = compute_recommended_next_step(events, type_stability=0.50)
        assert step == RecommendedNextStep.TAKE_DEEP_ASSESSMENT.value
    
    def test_low_stability_with_deep_recommends_observing(self):
        """Low stability with deep assessment should recommend keep observing."""
        events = [{"source": "enneagram_deep"}]
        step = compute_recommended_next_step(events, type_stability=0.50)
        assert step == RecommendedNextStep.KEEP_OBSERVING.value


# ============================================
# TEST: SUMMARY SCHEMA
# ============================================

class TestSummarySchema:
    """Tests for summary output schema."""
    
    def test_summary_has_required_fields(self):
        """Summary should have all required fields."""
        events = [{
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source": "enneagram_short",
            "signals": {
                "type_affinities": {"6": 0.02},
                "wing_affinities": {"5": 0.01}
            }
        }]
        
        summary = compute_longitudinal_summary(events, days_window=30)
        
        # Check top-level structure
        assert "longitudinal" in summary
        lng = summary["longitudinal"]
        
        # Check all required fields
        assert "enabled" in lng
        assert "type_stability" in lng
        assert "wing_stability" in lng
        assert "evidence_volume" in lng
        assert "top_types_over_time" in lng
        assert "confidence_modifier" in lng
        assert "recommended_next_step" in lng
        
        # Check types
        assert isinstance(lng["enabled"], bool)
        assert isinstance(lng["type_stability"], float)
        assert isinstance(lng["wing_stability"], float)
        assert isinstance(lng["evidence_volume"], dict)
        assert isinstance(lng["top_types_over_time"], list)
        assert isinstance(lng["confidence_modifier"], str)
        assert isinstance(lng["recommended_next_step"], str)
    
    def test_empty_summary_schema(self):
        """Empty summary should have same schema with default values."""
        summary = get_empty_longitudinal_summary()
        
        assert summary["longitudinal"]["enabled"] is True
        assert summary["longitudinal"]["type_stability"] == 0.0
        assert summary["longitudinal"]["wing_stability"] == 0.0
        assert summary["longitudinal"]["evidence_volume"]["total"] == 0
        assert summary["longitudinal"]["top_types_over_time"] == []
        assert summary["longitudinal"]["confidence_modifier"] == "none"
        assert summary["longitudinal"]["recommended_next_step"] == "none"


# ============================================
# TEST: EVIDENCE DOCUMENT CREATION
# ============================================

class TestEvidenceDocument:
    """Tests for evidence document creation."""
    
    def test_valid_source_accepted(self):
        """Valid sources should be accepted."""
        for source in ["reflection_chat", "journal", "enneagram_short", "enneagram_deep"]:
            doc = create_evidence_document(
                user_id="test",
                source=source,
                signals={"type_affinities": {}, "wing_affinities": {}, "confidence_hint": 0.5}
            )
            assert doc["source"] == source
    
    def test_invalid_source_rejected(self):
        """Invalid sources should raise ValueError."""
        with pytest.raises(ValueError):
            create_evidence_document(
                user_id="test",
                source="invalid_source",
                signals={"type_affinities": {}, "wing_affinities": {}, "confidence_hint": 0.5}
            )
    
    def test_document_has_version(self):
        """Document should include schema version."""
        doc = create_evidence_document(
            user_id="test",
            source="enneagram_short",
            signals={"type_affinities": {}, "wing_affinities": {}, "confidence_hint": 0.5}
        )
        assert doc["version"] == SIGNAL_SCHEMA_VERSION
    
    def test_document_has_timestamp(self):
        """Document should include created_at timestamp."""
        doc = create_evidence_document(
            user_id="test",
            source="enneagram_short",
            signals={"type_affinities": {}, "wing_affinities": {}, "confidence_hint": 0.5}
        )
        assert "created_at" in doc
        # Should be ISO format
        datetime.fromisoformat(doc["created_at"].replace('Z', '+00:00'))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
