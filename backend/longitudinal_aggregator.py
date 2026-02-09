"""
P5: Longitudinal Evidence Store + Aggregator
============================================

V1-safe shadow system for collecting derived evidence signals over time,
computing stability + confidence evolution, and exposing results only in DEBUG mode.

This module implements:
1. Signal schema validation and clamping
2. Evidence storage/retrieval operations
3. Aggregation logic (stability, top types, confidence modifier)
4. Recommended next step computation

CRITICAL: This is a SHADOW system - NO changes to user-facing Enneagram results.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, Literal
from enum import Enum
import logging
import math

logger = logging.getLogger(__name__)

# ============================================
# CONSTANTS & CONFIGURATION
# ============================================

# Maximum per-event contribution for any type/wing affinity
MAX_AFFINITY_PER_EVENT = 0.03

# Version for signal schema
SIGNAL_SCHEMA_VERSION = "1.0"

# Supported evidence sources
class EvidenceSource(str, Enum):
    REFLECTION_CHAT = "reflection_chat"
    JOURNAL = "journal"
    ENNEAGRAM_SHORT = "enneagram_short"
    ENNEAGRAM_DEEP = "enneagram_deep"

# Stress and avoidance style enums
class StressStyle(str, Enum):
    VIGILANCE = "vigilance"
    REFRAMING = "reframing"
    WITHDRAWAL = "withdrawal"
    CONTROL = "control"
    OTHER = "other"
    NONE = "null"

class AvoidanceStyle(str, Enum):
    UNCERTAINTY = "uncertainty"
    CONFLICT = "conflict"
    LIMITATION = "limitation"
    INTENSITY = "intensity"
    OTHER = "other"
    NONE = "null"

# Confidence modifier states
class ConfidenceModifier(str, Enum):
    NONE = "none"
    UPSHIFT = "upshift"
    DOWNSHIFT = "downshift"

# Recommended next steps
class RecommendedNextStep(str, Enum):
    NONE = "none"
    TAKE_DEEP_ASSESSMENT = "take_deep_assessment"
    KEEP_OBSERVING = "keep_observing"


# ============================================
# SIGNAL SCHEMA VALIDATION & CLAMPING
# ============================================

def clamp_affinity(value: float) -> float:
    """Clamp affinity value to [-MAX, +MAX] range."""
    return max(-MAX_AFFINITY_PER_EVENT, min(MAX_AFFINITY_PER_EVENT, value))


def validate_and_clamp_signals(signals: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and clamp all signal values.
    
    Args:
        signals: Raw signal dictionary
        
    Returns:
        Validated and clamped signals
        
    Raises:
        ValueError: If signals contain invalid structure
    """
    validated = {}
    
    # Type affinities (clamp each value)
    type_affinities = signals.get("type_affinities", {})
    if not isinstance(type_affinities, dict):
        raise ValueError("type_affinities must be a dictionary")
    validated["type_affinities"] = {
        str(k): clamp_affinity(float(v)) 
        for k, v in type_affinities.items()
        if str(k).isdigit() and 1 <= int(k) <= 9
    }
    
    # Wing affinities (clamp each value)
    wing_affinities = signals.get("wing_affinities", {})
    if not isinstance(wing_affinities, dict):
        raise ValueError("wing_affinities must be a dictionary")
    validated["wing_affinities"] = {
        str(k): clamp_affinity(float(v))
        for k, v in wing_affinities.items()
        if str(k).isdigit() and 1 <= int(k) <= 9
    }
    
    # Stress style (validate enum)
    stress_style = signals.get("stress_style")
    if stress_style:
        try:
            validated["stress_style"] = StressStyle(stress_style).value
        except ValueError:
            validated["stress_style"] = StressStyle.OTHER.value
    else:
        validated["stress_style"] = StressStyle.NONE.value
    
    # Avoidance style (validate enum)
    avoidance_style = signals.get("avoidance_style")
    if avoidance_style:
        try:
            validated["avoidance_style"] = AvoidanceStyle(avoidance_style).value
        except ValueError:
            validated["avoidance_style"] = AvoidanceStyle.OTHER.value
    else:
        validated["avoidance_style"] = AvoidanceStyle.NONE.value
    
    # Confidence hint (clamp 0-1)
    confidence_hint = signals.get("confidence_hint", 0.0)
    validated["confidence_hint"] = max(0.0, min(1.0, float(confidence_hint)))
    
    return validated


def create_evidence_document(
    user_id: str,
    source: str,
    signals: Dict[str, Any],
    event_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a validated evidence document for storage.
    
    Args:
        user_id: User identifier
        source: Evidence source type
        signals: Signal data (will be validated and clamped)
        event_id: Optional pre-generated event ID
        
    Returns:
        Complete evidence document ready for storage
    """
    # Validate source
    try:
        source_enum = EvidenceSource(source)
    except ValueError:
        raise ValueError(f"Invalid source: {source}. Must be one of {[e.value for e in EvidenceSource]}")
    
    # Validate and clamp signals
    validated_signals = validate_and_clamp_signals(signals)
    
    return {
        "id": event_id or None,  # Will be set by MongoDB
        "user_id": user_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": source_enum.value,
        "signals": validated_signals,
        "version": SIGNAL_SCHEMA_VERSION
    }


# ============================================
# EVIDENCE DERIVATION FROM ENNEAGRAM ASSESSMENT
# ============================================

def derive_signals_from_enneagram_result(
    result: Dict[str, Any],
    assessment_type: Literal["short", "deep"]
) -> Dict[str, Any]:
    """
    Derive longitudinal signals from an Enneagram assessment result.
    
    This is called AFTER an assessment completes to emit evidence.
    
    Args:
        result: Enneagram result dictionary containing:
            - inferred_core: int (1-9)
            - inferred_wing: int or 'balanced' or None
            - confidence_tier: 'low' | 'medium' | 'high'
            - top_candidates: List[{type, probability}]
            - debug_scores: optional scoring details
            
        assessment_type: 'short' or 'deep'
        
    Returns:
        Signal dictionary for longitudinal storage
    """
    signals = {
        "type_affinities": {},
        "wing_affinities": {},
        "stress_style": None,
        "avoidance_style": None,
        "confidence_hint": 0.0
    }
    
    # Derive type affinities from probability vector
    top_candidates = result.get("top_candidates", [])
    for candidate in top_candidates[:3]:  # Top 3 only
        type_num = str(candidate.get("type", 0))
        prob = candidate.get("probability", 0)
        
        # Scale probability to small contribution (max 0.03)
        # Higher probability = higher contribution, but clamped
        contribution = min(prob * 0.05, MAX_AFFINITY_PER_EVENT)
        signals["type_affinities"][type_num] = contribution
    
    # Derive wing affinities (if wing determined)
    inferred_wing = result.get("inferred_wing")
    if isinstance(inferred_wing, int) and 1 <= inferred_wing <= 9:
        # Wing is determined - give small affinity
        signals["wing_affinities"][str(inferred_wing)] = 0.02
    elif inferred_wing == "balanced":
        # Both wings equally active - split contribution
        core = result.get("inferred_core", 5)
        left_wing = 9 if core == 1 else core - 1
        right_wing = 1 if core == 9 else core + 1
        signals["wing_affinities"][str(left_wing)] = 0.01
        signals["wing_affinities"][str(right_wing)] = 0.01
    
    # Confidence hint from tier
    confidence_tier = result.get("confidence_tier", "low")
    confidence_map = {
        "low": 0.2,
        "medium": 0.5,
        "moderate": 0.5,  # Alias
        "high": 0.8
    }
    signals["confidence_hint"] = confidence_map.get(confidence_tier, 0.2)
    
    return signals


# ============================================
# AGGREGATION LOGIC
# ============================================

def compute_recency_weight(created_at: str, reference_time: datetime, half_life_days: int = 14) -> float:
    """
    Compute recency weight using exponential decay.
    
    More recent events count more; half_life_days defines the decay rate.
    
    Args:
        created_at: ISO timestamp of the event
        reference_time: Reference time for computing age
        half_life_days: Days until weight is halved
        
    Returns:
        Weight between 0 and 1
    """
    try:
        event_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        if event_time.tzinfo is None:
            event_time = event_time.replace(tzinfo=timezone.utc)
        
        age_days = (reference_time - event_time).total_seconds() / (24 * 3600)
        if age_days < 0:
            age_days = 0
            
        # Exponential decay: weight = 0.5^(age/half_life)
        decay_factor = math.pow(0.5, age_days / half_life_days)
        return max(0.01, decay_factor)  # Minimum weight 0.01
        
    except Exception:
        return 0.5  # Default weight on parse error


def compute_type_stability(events: List[Dict[str, Any]], reference_time: datetime) -> float:
    """
    Compute type stability: consistency of top-1 type across events.
    
    Args:
        events: List of evidence events
        reference_time: Current time for recency weighting
        
    Returns:
        Stability score 0-1 (1 = perfectly stable)
    """
    if not events:
        return 0.0
    
    # Count weighted occurrences of each top-1 type
    type_weights: Dict[str, float] = {}
    total_weight = 0.0
    
    for event in events:
        weight = compute_recency_weight(event.get("created_at", ""), reference_time)
        signals = event.get("signals", {})
        type_affinities = signals.get("type_affinities", {})
        
        # Find top type in this event
        if type_affinities:
            top_type = max(type_affinities.items(), key=lambda x: x[1])[0]
            type_weights[top_type] = type_weights.get(top_type, 0) + weight
            total_weight += weight
    
    if total_weight == 0:
        return 0.0
    
    # Stability = weight share of most common type
    if type_weights:
        max_weight = max(type_weights.values())
        return max_weight / total_weight
    
    return 0.0


def compute_wing_stability(events: List[Dict[str, Any]], reference_time: datetime) -> float:
    """
    Compute wing stability: consistency of wing across events.
    
    Args:
        events: List of evidence events
        reference_time: Current time for recency weighting
        
    Returns:
        Stability score 0-1 (1 = perfectly stable)
    """
    if not events:
        return 0.0
    
    wing_weights: Dict[str, float] = {}
    total_weight = 0.0
    
    for event in events:
        weight = compute_recency_weight(event.get("created_at", ""), reference_time)
        signals = event.get("signals", {})
        wing_affinities = signals.get("wing_affinities", {})
        
        if wing_affinities:
            top_wing = max(wing_affinities.items(), key=lambda x: x[1])[0]
            wing_weights[top_wing] = wing_weights.get(top_wing, 0) + weight
            total_weight += weight
    
    if total_weight == 0:
        return 0.0
    
    if wing_weights:
        max_weight = max(wing_weights.values())
        return max_weight / total_weight
    
    return 0.0


def compute_top_types_over_time(events: List[Dict[str, Any]], reference_time: datetime) -> List[Dict[str, Any]]:
    """
    Compute top types based on weighted frequency/affinity across events.
    
    Args:
        events: List of evidence events
        reference_time: Current time for recency weighting
        
    Returns:
        List of {type, share} sorted by share descending
    """
    if not events:
        return []
    
    type_scores: Dict[str, float] = {}
    total_score = 0.0
    
    for event in events:
        weight = compute_recency_weight(event.get("created_at", ""), reference_time)
        signals = event.get("signals", {})
        type_affinities = signals.get("type_affinities", {})
        
        for type_num, affinity in type_affinities.items():
            score = weight * max(0, affinity)  # Only positive affinities
            type_scores[type_num] = type_scores.get(type_num, 0) + score
            total_score += score
    
    if total_score == 0:
        return []
    
    # Convert to shares and sort
    result = [
        {"type": int(t), "share": round(s / total_score, 2)}
        for t, s in type_scores.items()
    ]
    result.sort(key=lambda x: x["share"], reverse=True)
    
    return result[:5]  # Top 5


def has_deep_assessment(events: List[Dict[str, Any]]) -> bool:
    """Check if any event is from a deep assessment."""
    return any(
        event.get("source") == EvidenceSource.ENNEAGRAM_DEEP.value
        for event in events
    )


def compute_confidence_modifier(
    events: List[Dict[str, Any]],
    type_stability: float,
    top_types: List[Dict[str, Any]],
    days_window: int = 30
) -> str:
    """
    Compute confidence modifier based on longitudinal evidence.
    
    Rules (deterministic, explicit):
    - UPSHIFT only if:
        - deep assessment exists in window OR enough evidence events (>=10)
        - type_stability >= 0.75
        - top-1 share >= 0.70
    - DOWNSHIFT if:
        - type_stability < 0.50 AND evidence_volume >= 8
    - Otherwise NONE
    
    Args:
        events: Evidence events within the time window
        type_stability: Computed type stability score
        top_types: List of {type, share} from top types computation
        days_window: Number of days to consider
        
    Returns:
        "none" | "upshift" | "downshift"
    """
    evidence_count = len(events)
    has_deep = has_deep_assessment(events)
    
    # Get top-1 share
    top_1_share = top_types[0]["share"] if top_types else 0.0
    
    # Check UPSHIFT conditions
    if (has_deep or evidence_count >= 10):
        if type_stability >= 0.75 and top_1_share >= 0.70:
            return ConfidenceModifier.UPSHIFT.value
    
    # Check DOWNSHIFT conditions
    if evidence_count >= 8 and type_stability < 0.50:
        return ConfidenceModifier.DOWNSHIFT.value
    
    return ConfidenceModifier.NONE.value


def compute_recommended_next_step(
    events: List[Dict[str, Any]],
    type_stability: float
) -> str:
    """
    Compute recommended next step for the user.
    
    Rules:
    - If assessment_depth is short and stability is low → take_deep_assessment
    - If deep exists but stability remains low → keep_observing
    - If stability high → none
    
    Args:
        events: Evidence events
        type_stability: Computed type stability score
        
    Returns:
        "none" | "take_deep_assessment" | "keep_observing"
    """
    has_deep = has_deep_assessment(events)
    has_any_assessment = any(
        event.get("source") in [EvidenceSource.ENNEAGRAM_SHORT.value, EvidenceSource.ENNEAGRAM_DEEP.value]
        for event in events
    )
    
    # High stability = no action needed
    if type_stability >= 0.75:
        return RecommendedNextStep.NONE.value
    
    # Low stability scenarios
    if type_stability < 0.60:
        if has_deep:
            # Already has deep assessment but still unstable
            return RecommendedNextStep.KEEP_OBSERVING.value
        elif has_any_assessment:
            # Only has short assessment and unstable
            return RecommendedNextStep.TAKE_DEEP_ASSESSMENT.value
    
    return RecommendedNextStep.NONE.value


def compute_evidence_volume(events: List[Dict[str, Any]], reference_time: datetime, days: int = 30) -> Dict[str, int]:
    """
    Compute evidence volume statistics.
    
    Args:
        events: All evidence events
        reference_time: Current time
        days: Window for "recent" count
        
    Returns:
        {total, last_X_days}
    """
    total = len(events)
    cutoff = reference_time - timedelta(days=days)
    
    recent_count = 0
    for event in events:
        try:
            created = datetime.fromisoformat(event.get("created_at", "").replace('Z', '+00:00'))
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            if created >= cutoff:
                recent_count += 1
        except Exception:
            pass
    
    return {
        "total": total,
        f"last_{days}_days": recent_count
    }


def compute_longitudinal_summary(
    events: List[Dict[str, Any]],
    days_window: int = 30
) -> Dict[str, Any]:
    """
    Compute the full longitudinal summary for a user.
    
    This is the main aggregation entry point.
    
    Args:
        events: All evidence events for the user (within window)
        days_window: Time window for aggregation
        
    Returns:
        Complete longitudinal summary object
    """
    reference_time = datetime.now(timezone.utc)
    
    # Filter to window
    cutoff = reference_time - timedelta(days=days_window)
    windowed_events = []
    for event in events:
        try:
            created = datetime.fromisoformat(event.get("created_at", "").replace('Z', '+00:00'))
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            if created >= cutoff:
                windowed_events.append(event)
        except Exception:
            windowed_events.append(event)  # Include on parse error
    
    # Compute all metrics
    type_stability = compute_type_stability(windowed_events, reference_time)
    wing_stability = compute_wing_stability(windowed_events, reference_time)
    top_types = compute_top_types_over_time(windowed_events, reference_time)
    evidence_volume = compute_evidence_volume(events, reference_time, days_window)
    
    confidence_modifier = compute_confidence_modifier(
        windowed_events, type_stability, top_types, days_window
    )
    recommended_next_step = compute_recommended_next_step(windowed_events, type_stability)
    
    return {
        "longitudinal": {
            "enabled": True,
            "type_stability": round(type_stability, 2),
            "wing_stability": round(wing_stability, 2),
            "evidence_volume": evidence_volume,
            "top_types_over_time": top_types,
            "confidence_modifier": confidence_modifier,
            "recommended_next_step": recommended_next_step
        }
    }


# ============================================
# EMPTY/DEFAULT SUMMARY
# ============================================

def get_empty_longitudinal_summary() -> Dict[str, Any]:
    """Return empty longitudinal summary when no data exists."""
    return {
        "longitudinal": {
            "enabled": True,
            "type_stability": 0.0,
            "wing_stability": 0.0,
            "evidence_volume": {"total": 0, "last_30_days": 0},
            "top_types_over_time": [],
            "confidence_modifier": ConfidenceModifier.NONE.value,
            "recommended_next_step": RecommendedNextStep.NONE.value
        }
    }
