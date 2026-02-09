"""
P1: Deep Assessment Scoring Engine
==================================

Deterministic scoring engine for the 45-question deep Enneagram assessment.
Converts responses to type probabilities, performs wing analysis, and 
determines confidence tier.

CRITICAL: Must pass P4 invariants (probability sum, floors, etc.)
"""

import math
from typing import Dict, List, Any, Optional, Literal, Tuple
from enum import Enum
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

# ============================================
# CONSTANTS
# ============================================

# All valid Enneagram types
VALID_TYPES = [1, 2, 3, 4, 5, 6, 7, 8, 9]

# Minimum probability floor per P4 contract
PROBABILITY_FLOOR = 0.001

# Sum tolerance for probability normalization
SUM_TOLERANCE = 0.001

# Wing adjacency map
WING_MAP: Dict[int, Dict[str, int]] = {
    1: {"left": 9, "right": 2},
    2: {"left": 1, "right": 3},
    3: {"left": 2, "right": 4},
    4: {"left": 3, "right": 5},
    5: {"left": 4, "right": 6},
    6: {"left": 5, "right": 7},
    7: {"left": 6, "right": 8},
    8: {"left": 7, "right": 9},
    9: {"left": 8, "right": 1},
}

# Wing state thresholds
WING_DOMINANT_THRESHOLD = 0.15  # Difference for dominant wing
WING_LEANING_THRESHOLD = 0.05  # Difference for leaning wing
WING_BALANCED_THRESHOLD = 0.05  # Max difference for balanced


class WingState(str, Enum):
    """Valid wing states per P4 contract."""
    DOMINANT = "dominant"
    LEANING = "leaning"
    BALANCED = "balanced"
    NOT_CLEAR = "not_clear"


class ConfidenceTier(str, Enum):
    """Confidence tier per P4 contract."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


# ============================================
# SCORING FUNCTIONS
# ============================================

def score_forced_choice(
    question: Dict[str, Any],
    response_value: str
) -> Dict[int, float]:
    """
    Score a forced choice question.
    
    Args:
        question: Question dict with options
        response_value: Selected option ID ("A", "B", etc.)
        
    Returns:
        Dict mapping type numbers to score contributions
    """
    scores: Dict[int, float] = {t: 0.0 for t in VALID_TYPES}
    
    # Find selected option
    selected_option = None
    for opt in question.get("options", []):
        if opt.get("id") == response_value:
            selected_option = opt
            break
    
    if not selected_option:
        logger.warning(f"[DeepScoring] Invalid response {response_value} for question {question.get('id')}")
        return scores
    
    # Apply primary type score
    primary_type = selected_option.get("primary_type")
    weight = selected_option.get("weight", 1.0)
    
    if primary_type and primary_type in VALID_TYPES:
        scores[primary_type] += weight
    
    # Apply secondary type score (reduced weight)
    secondary_type = selected_option.get("secondary_type")
    if secondary_type and secondary_type in VALID_TYPES:
        scores[secondary_type] += weight * 0.3  # Secondary gets 30% of primary weight
    
    return scores


def score_likert(
    question: Dict[str, Any],
    response_value: int
) -> Dict[int, float]:
    """
    Score a Likert scale question.
    
    Args:
        question: Question dict with scoring info
        response_value: Likert value (1-5)
        
    Returns:
        Dict mapping type numbers to score contributions
    """
    scores: Dict[int, float] = {t: 0.0 for t in VALID_TYPES}
    
    scoring = question.get("scoring", {})
    primary_type = scoring.get("primary_type")
    secondary_type = scoring.get("secondary_type")
    direction = scoring.get("direction", "positive")
    weight = scoring.get("weight", 1.0)
    
    scale = question.get("scale", {})
    min_val = scale.get("min", 1)
    max_val = scale.get("max", 5)
    
    # Normalize response to 0-1 range
    if direction == "positive":
        # Higher values = stronger endorsement
        normalized = (response_value - min_val) / (max_val - min_val)
    else:
        # Lower values = stronger endorsement (reverse scored)
        normalized = 1.0 - ((response_value - min_val) / (max_val - min_val))
    
    # Apply primary type score
    if primary_type and primary_type in VALID_TYPES:
        scores[primary_type] += normalized * weight
    
    # Apply secondary type score (reduced weight)
    if secondary_type and secondary_type in VALID_TYPES:
        scores[secondary_type] += normalized * weight * 0.3
    
    return scores


def score_ranked(
    question: Dict[str, Any],
    response_value: List[str]
) -> Dict[int, float]:
    """
    Score a ranked preference question.
    
    Args:
        question: Question dict with options and weight multipliers
        response_value: List of option IDs in rank order (first = rank 1)
        
    Returns:
        Dict mapping type numbers to score contributions
    """
    scores: Dict[int, float] = {t: 0.0 for t in VALID_TYPES}
    
    options = {opt["id"]: opt for opt in question.get("options", [])}
    
    for rank_idx, option_id in enumerate(response_value):
        if option_id not in options:
            continue
            
        option = options[option_id]
        primary_type = option.get("primary_type")
        weight_multipliers = option.get("weight_multipliers", {})
        
        # Get multiplier for this rank (1-indexed in multiplier keys)
        rank_key = f"rank_{rank_idx + 1}"
        multiplier = weight_multipliers.get(rank_key, 0.0)
        
        if primary_type and primary_type in VALID_TYPES:
            scores[primary_type] += multiplier
    
    return scores


def aggregate_raw_scores(
    questions: List[Dict[str, Any]],
    responses: List[Dict[str, Any]]
) -> Dict[int, float]:
    """
    Aggregate raw scores from all question responses.
    
    Args:
        questions: List of question dicts
        responses: List of response dicts with question_id and response values
        
    Returns:
        Dict mapping type numbers to raw aggregate scores
    """
    aggregate: Dict[int, float] = {t: 0.0 for t in VALID_TYPES}
    
    # Build question lookup
    question_lookup = {q["id"]: q for q in questions}
    
    # Process each response
    for resp in responses:
        question_id = resp.get("question_id")
        question = question_lookup.get(question_id)
        
        if not question:
            logger.warning(f"[DeepScoring] Unknown question_id: {question_id}")
            continue
        
        question_type = question.get("type")
        response_obj = resp.get("response", {})
        response_value = response_obj.get("value")
        
        if response_value is None:
            continue
        
        # Score based on question type
        if question_type == "forced_choice":
            scores = score_forced_choice(question, response_value)
        elif question_type == "likert":
            scores = score_likert(question, int(response_value))
        elif question_type == "ranked":
            # Response should be a list of option IDs
            if isinstance(response_value, list):
                scores = score_ranked(question, response_value)
            else:
                scores = {t: 0.0 for t in VALID_TYPES}
        else:
            logger.warning(f"[DeepScoring] Unknown question type: {question_type}")
            scores = {t: 0.0 for t in VALID_TYPES}
        
        # Add to aggregate
        for type_num, score in scores.items():
            aggregate[type_num] += score
    
    return aggregate


def normalize_to_probabilities(
    raw_scores: Dict[int, float]
) -> Dict[str, float]:
    """
    Normalize raw scores to probabilities that sum to 1.0.
    
    Applies probability floor per P4 contract.
    
    Args:
        raw_scores: Dict mapping type numbers to raw scores
        
    Returns:
        Dict mapping type strings to probabilities
    """
    # Apply softmax-like normalization for smoother distribution
    # First, shift scores to be positive
    min_score = min(raw_scores.values()) if raw_scores else 0
    shifted = {t: max(0.01, s - min_score + 0.01) for t, s in raw_scores.items()}
    
    # Apply exponential scaling for discrimination
    scaled = {t: math.exp(s * 0.5) for t, s in shifted.items()}
    
    total = sum(scaled.values())
    
    if total == 0:
        # Uniform distribution if no scores
        uniform = 1.0 / len(VALID_TYPES)
        return {str(t): uniform for t in VALID_TYPES}
    
    # Normalize
    probabilities = {str(t): s / total for t, s in scaled.items()}
    
    # Apply floor
    for t in probabilities:
        if probabilities[t] < PROBABILITY_FLOOR:
            probabilities[t] = PROBABILITY_FLOOR
    
    # Re-normalize to sum to 1.0
    total = sum(probabilities.values())
    probabilities = {t: p / total for t, p in probabilities.items()}
    
    # Verify sum (P4 invariant)
    final_sum = sum(probabilities.values())
    if abs(final_sum - 1.0) > SUM_TOLERANCE:
        logger.error(f"[DeepScoring] Probability sum {final_sum} exceeds tolerance")
        # Force correction
        largest = max(probabilities, key=probabilities.get)
        probabilities[largest] += (1.0 - final_sum)
    
    return probabilities


def get_top_types(
    probabilities: Dict[str, float],
    n: int = 2
) -> List[Dict[str, Any]]:
    """
    Get top N types by probability.
    
    Args:
        probabilities: Dict mapping type strings to probabilities
        n: Number of top types to return
        
    Returns:
        List of {type, probability} dicts sorted by probability desc
    """
    sorted_types = sorted(
        probabilities.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    return [
        {"type": int(t), "probability": round(p, 4)}
        for t, p in sorted_types[:n]
    ]


def compute_confidence_tier(
    probabilities: Dict[str, float],
    response_completeness: float
) -> str:
    """
    Compute confidence tier based on probability distribution and completeness.
    
    Args:
        probabilities: Dict mapping type strings to probabilities
        response_completeness: Fraction of questions answered (0-1)
        
    Returns:
        Confidence tier string
    """
    if response_completeness < 1.0:
        return ConfidenceTier.LOW.value
    
    top_types = get_top_types(probabilities, 2)
    
    if len(top_types) < 2:
        return ConfidenceTier.LOW.value
    
    top_1_prob = top_types[0]["probability"]
    top_2_prob = top_types[1]["probability"]
    gap = top_1_prob - top_2_prob
    
    # High confidence: clear leader with significant gap
    if top_1_prob >= 0.35 and gap >= 0.12:
        return ConfidenceTier.HIGH.value
    
    # Moderate confidence: reasonable leader with some gap
    if top_1_prob >= 0.25 and gap >= 0.05:
        return ConfidenceTier.MODERATE.value
    
    # Low confidence: no clear leader or small gap
    return ConfidenceTier.LOW.value


def compute_wing_analysis(
    probabilities: Dict[str, float],
    core_type: int
) -> Dict[str, Any]:
    """
    Compute wing analysis for a given core type.
    
    Args:
        probabilities: Dict mapping type strings to probabilities
        core_type: The primary/core type
        
    Returns:
        Wing analysis dict with wing_state, inferred_wing, adjacent_scores
    """
    wings = WING_MAP.get(core_type, {"left": 0, "right": 0})
    left_wing = wings["left"]
    right_wing = wings["right"]
    
    left_score = probabilities.get(str(left_wing), 0.0)
    right_score = probabilities.get(str(right_wing), 0.0)
    
    diff = abs(left_score - right_score)
    
    # Determine wing state
    if diff >= WING_DOMINANT_THRESHOLD:
        wing_state = WingState.DOMINANT.value
        inferred_wing = left_wing if left_score > right_score else right_wing
    elif diff >= WING_LEANING_THRESHOLD:
        wing_state = WingState.LEANING.value
        inferred_wing = left_wing if left_score > right_score else right_wing
    elif diff <= WING_BALANCED_THRESHOLD and left_score > 0.05 and right_score > 0.05:
        wing_state = WingState.BALANCED.value
        inferred_wing = None
    else:
        wing_state = WingState.NOT_CLEAR.value
        inferred_wing = None
    
    return {
        "wing_state": wing_state,
        "inferred_wing": inferred_wing,
        "adjacent_scores": {
            "left": round(left_score, 4),
            "right": round(right_score, 4),
            "left_type": left_wing,
            "right_type": right_wing
        }
    }


def score_deep_assessment(
    questions: List[Dict[str, Any]],
    responses: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Main scoring function for deep assessment.
    
    Converts responses to a complete result including:
    - type_probabilities
    - top_types
    - confidence_tier
    - assessment_depth
    - wing_analysis
    
    Args:
        questions: List of question dicts
        responses: List of response dicts
        
    Returns:
        Complete scoring result dict
    """
    # Calculate completeness
    total_questions = len(questions)
    answered_questions = len([r for r in responses if r.get("response", {}).get("value") is not None])
    completeness = answered_questions / total_questions if total_questions > 0 else 0.0
    
    # Aggregate raw scores
    raw_scores = aggregate_raw_scores(questions, responses)
    
    # Normalize to probabilities
    type_probabilities = normalize_to_probabilities(raw_scores)
    
    # Get top types
    top_types = get_top_types(type_probabilities, 2)
    
    # Determine core type
    core_type = top_types[0]["type"] if top_types else 5  # Default to 5 if no data
    
    # Compute confidence tier
    confidence_tier = compute_confidence_tier(type_probabilities, completeness)
    
    # Compute wing analysis
    wing_analysis = compute_wing_analysis(type_probabilities, core_type)
    
    # Build result
    result = {
        "type_probabilities": type_probabilities,
        "top_types": top_types,
        "confidence_tier": confidence_tier,
        "assessment_depth": "deep",
        "wing_analysis": wing_analysis,
        "scoring_metadata": {
            "questions_total": total_questions,
            "questions_answered": answered_questions,
            "completeness": round(completeness, 4),
            "raw_scores": {str(k): round(v, 4) for k, v in raw_scores.items()}
        },
        "completed_at": datetime.now(timezone.utc).isoformat()
    }
    
    return result


def validate_response_type(
    question: Dict[str, Any],
    response: Dict[str, Any]
) -> Tuple[bool, Optional[str]]:
    """
    Validate that a response matches the expected question type.
    
    Args:
        question: Question dict
        response: Response dict with type and value
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    question_type = question.get("type")
    response_type = response.get("type")
    value = response.get("value")
    
    if response_type != question_type:
        return False, f"Response type '{response_type}' does not match question type '{question_type}'"
    
    if question_type == "forced_choice":
        valid_options = [opt["id"] for opt in question.get("options", [])]
        if value not in valid_options:
            return False, f"Invalid option '{value}'. Valid options: {valid_options}"
    
    elif question_type == "likert":
        scale = question.get("scale", {})
        min_val = scale.get("min", 1)
        max_val = scale.get("max", 5)
        try:
            int_value = int(value)
            if not (min_val <= int_value <= max_val):
                return False, f"Likert value {value} out of range [{min_val}, {max_val}]"
        except (ValueError, TypeError):
            return False, f"Likert value must be an integer, got: {value}"
    
    elif question_type == "ranked":
        if not isinstance(value, list):
            return False, "Ranked response must be a list of option IDs"
        valid_options = [opt["id"] for opt in question.get("options", [])]
        for opt in value:
            if opt not in valid_options:
                return False, f"Invalid ranked option '{opt}'. Valid options: {valid_options}"
    
    else:
        return False, f"Unknown question type: {question_type}"
    
    return True, None


# ============================================
# P4 CONTRACT VALIDATION
# ============================================

def validate_result_contract(result: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate that a scoring result passes P4 contract invariants.
    
    Args:
        result: Scoring result dict
        
    Returns:
        Tuple of (is_valid, list of violation messages)
    """
    violations = []
    
    # Check type_probabilities sum
    probs = result.get("type_probabilities", {})
    prob_sum = sum(probs.values())
    if abs(prob_sum - 1.0) > SUM_TOLERANCE:
        violations.append(f"Probability sum {prob_sum} != 1.0 (tolerance: {SUM_TOLERANCE})")
    
    # Check probability floors
    for t, p in probs.items():
        if p < PROBABILITY_FLOOR:
            violations.append(f"Type {t} probability {p} below floor {PROBABILITY_FLOOR}")
    
    # Check wing_state is valid
    wing_analysis = result.get("wing_analysis", {})
    wing_state = wing_analysis.get("wing_state")
    valid_states = [s.value for s in WingState]
    if wing_state not in valid_states:
        violations.append(f"Invalid wing_state '{wing_state}'. Valid: {valid_states}")
    
    # Check top_types format
    top_types = result.get("top_types", [])
    if len(top_types) < 2:
        violations.append(f"top_types must have at least 2 entries, got {len(top_types)}")
    
    for tt in top_types:
        if not isinstance(tt.get("type"), int):
            violations.append(f"top_types entry missing integer 'type': {tt}")
        if not isinstance(tt.get("probability"), (int, float)):
            violations.append(f"top_types entry missing numeric 'probability': {tt}")
    
    # Check confidence_tier is valid
    confidence_tier = result.get("confidence_tier")
    valid_tiers = [t.value for t in ConfidenceTier]
    if confidence_tier not in valid_tiers:
        violations.append(f"Invalid confidence_tier '{confidence_tier}'. Valid: {valid_tiers}")
    
    # Check assessment_depth
    if result.get("assessment_depth") != "deep":
        violations.append(f"assessment_depth must be 'deep', got '{result.get('assessment_depth')}'")
    
    return len(violations) == 0, violations
