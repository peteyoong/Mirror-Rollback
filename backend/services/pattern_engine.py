"""
Mirror Pattern Engine v0.5 - Task 70

Foundation for cross-lens pattern intelligence that will eventually connect:
- Lunar decisions
- Journal reflections  
- Mirror chat
- Human Design gate activations
- Enneagram patterns
- Future Gene Keys / transit signals

This is the normalized internal signal model and extraction layer.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Literal
from dataclasses import dataclass, asdict
from enum import Enum
import re
from collections import Counter
import hashlib

logger = logging.getLogger(__name__)

# =============================================================================
# ENUMS AND TYPE DEFINITIONS - Task 70
# =============================================================================

class SourceType(str, Enum):
    LUNAR_REFLECTION = "lunar_reflection"
    JOURNAL_ENTRY = "journal_entry"
    MIRROR_CHAT = "mirror_chat"
    HUMAN_DESIGN_GATE = "human_design_gate"
    ENNEAGRAM = "enneagram"
    GENE_KEYS = "gene_keys"
    TRANSIT = "transit"


class Domain(str, Enum):
    EXPRESSION_ACTION = "expression_action"
    EMOTIONAL_LANDSCAPE = "emotional_landscape"
    RELATIONSHIPS = "relationships"
    WORK_PURPOSE = "work_purpose"
    IDENTITY_DIRECTION = "identity_direction"
    PRESSURE_STRESS = "pressure_stress"
    TIMING_READINESS = "timing_readiness"


class SignalType(str, Enum):
    EXCITEMENT = "excitement"
    HESITATION = "hesitation"
    CLARITY = "clarity"
    CONFUSION = "confusion"
    DESIRE = "desire"
    AVOIDANCE = "avoidance"
    CONFIDENCE = "confidence"
    DOUBT = "doubt"
    EXPANSION = "expansion"
    CONTRACTION = "contraction"


class Polarity(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    MIXED = "mixed"
    NEUTRAL = "neutral"


class MomentumState(str, Enum):
    STRONG_POSITIVE = "strong_positive"
    POSITIVE = "positive"
    MIXED = "mixed"
    UNCLEAR = "unclear"
    RESISTANT = "resistant"


class DataSufficiency(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INSUFFICIENT = "insufficient"


# =============================================================================
# PATTERN SIGNAL MODEL - Task 70 Section 8
# =============================================================================

@dataclass
class PatternSignal:
    """Unified pattern signal model for cross-lens intelligence."""
    id: str
    user_id: str
    source_type: str
    source_id: str
    timestamp: datetime
    domain: str
    signal_type: str
    polarity: str
    intensity: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    tags: List[str]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp
        return data


@dataclass
class DecisionPatternSnapshot:
    """Lightweight snapshot of decision patterns for synthesis."""
    decision_id: str
    decision_topic: str
    data_sufficiency: str
    entry_count: int
    days_observed: int
    dominant_signals: List[str]
    repeated_tags: List[str]
    strongest_gate: Optional[int]
    momentum: str
    excitement_score: float
    hesitation_score: float
    confidence: float


# =============================================================================
# IMPROVED EMOTIONAL SCORING - Task 70 Section 4
# =============================================================================

INTENSITY_MODIFIERS = {
    "very": 1.5,
    "really": 1.4,
    "deeply": 1.5,
    "strongly": 1.5,
    "definitely": 1.3,
    "absolutely": 1.5,
    "extremely": 1.6,
    "incredibly": 1.5,
    "truly": 1.3,
    "completely": 1.4,
    "totally": 1.3,
    "quite": 1.2,
    "somewhat": 0.8,
    "slightly": 0.6,
    "maybe": 0.7,
    "perhaps": 0.7,
    "kind of": 0.6,
    "sort of": 0.6,
}

EXCITEMENT_KEYWORDS = {
    # High intensity
    "excited": 0.9, "thrilled": 0.95, "passionate": 0.9, "inspired": 0.85,
    "energized": 0.85, "amazing": 0.8, "wonderful": 0.8, "love": 0.85,
    "can't wait": 0.9, "dream": 0.8, "opportunity": 0.7,
    # Medium intensity  
    "interested": 0.6, "curious": 0.6, "hopeful": 0.65, "eager": 0.7,
    "possibility": 0.6, "potential": 0.6, "looking forward": 0.7,
    "good idea": 0.55, "appealing": 0.6, "attractive": 0.55,
    # Lower intensity
    "nice": 0.4, "pleasant": 0.4, "okay": 0.3, "fine": 0.3,
}

HESITATION_KEYWORDS = {
    # High intensity
    "scared": 0.9, "terrified": 0.95, "afraid": 0.85, "worried": 0.8,
    "anxious": 0.8, "stressed": 0.75, "overwhelmed": 0.85, "fearful": 0.85,
    "dread": 0.9, "panic": 0.95,
    # Medium intensity
    "uncertain": 0.65, "hesitant": 0.7, "concerned": 0.65, "doubtful": 0.7,
    "not sure": 0.6, "risky": 0.65, "dangerous": 0.75, "problem": 0.6,
    "difficult": 0.55, "hard": 0.5, "challenging": 0.5,
    # Lower intensity
    "cautious": 0.45, "careful": 0.4, "wondering": 0.35, "questioning": 0.4,
}

NEUTRAL_KEYWORDS = {
    "thinking": 0.5, "considering": 0.5, "exploring": 0.5, "observing": 0.5,
    "noticing": 0.45, "reflecting": 0.5, "processing": 0.5, "pondering": 0.5,
    "aware": 0.45, "recognize": 0.45, "understand": 0.5, "see": 0.4,
}

# Domain keywords for classification
DOMAIN_KEYWORDS = {
    Domain.WORK_PURPOSE: ["work", "career", "job", "business", "profession", "role", "position", "company"],
    Domain.RELATIONSHIPS: ["family", "partner", "relationship", "friend", "love", "people", "connection", "together"],
    Domain.EXPRESSION_ACTION: ["create", "express", "build", "make", "do", "action", "start", "begin"],
    Domain.EMOTIONAL_LANDSCAPE: ["feel", "emotion", "heart", "sense", "mood", "spirit", "soul"],
    Domain.IDENTITY_DIRECTION: ["who", "identity", "self", "purpose", "meaning", "path", "direction"],
    Domain.PRESSURE_STRESS: ["pressure", "stress", "demand", "expect", "should", "must", "need to"],
    Domain.TIMING_READINESS: ["ready", "time", "when", "wait", "now", "timing", "moment", "prepared"],
}

# Tag extraction keywords
TAG_KEYWORDS = {
    "creative_independence": ["creative", "independent", "freedom", "own way", "autonomous", "self-directed"],
    "financial_security": ["money", "financial", "income", "salary", "stable", "security", "afford"],
    "new_beginning": ["new", "start", "begin", "fresh", "opportunity", "change"],
    "risk": ["risk", "risky", "gamble", "uncertain", "unknown", "venture"],
    "growth": ["grow", "learn", "develop", "evolve", "improve", "better"],
    "visibility": ["visible", "seen", "recognized", "public", "attention", "spotlight"],
    "belonging": ["belong", "community", "group", "tribe", "connection", "together"],
    "responsibility": ["responsible", "responsibility", "duty", "obligation", "accountable"],
    "possibility": ["possible", "possibility", "potential", "opportunity", "chance"],
    "authenticity": ["authentic", "true", "real", "genuine", "honest", "self"],
}

# Human Design Gate Insights for synthesis
GATE_INSIGHTS = {
    1: {"title": "Self-Expression", "insight": "This gate may have invited you to explore how this decision relates to your unique self-expression."},
    2: {"title": "The Direction of Self", "insight": "This gate may have helped you sense the natural direction for this decision."},
    3: {"title": "Ordering", "insight": "This gate may have shown what needs to be ordered or restructured around this decision."},
    13: {"title": "The Listener", "insight": "This gate may have helped you gather experiences and stories relevant to this decision."},
    17: {"title": "Opinions", "insight": "This gate may have surfaced opinions you hold about this decision."},
    19: {"title": "Wanting", "insight": "This gate may have revealed what you truly need from this decision."},
    21: {"title": "The Hunter", "insight": "This gate may have shown what obstacles you're willing to bite through."},
    22: {"title": "Openness", "insight": "This gate may have invited emotional openness in considering this decision."},
    25: {"title": "Innocence", "insight": "This gate may have connected you to what feels pure and innocent about this choice."},
    27: {"title": "Caring", "insight": "This gate may have revealed how this decision impacts those you care for."},
    30: {"title": "Feelings", "insight": "This gate may have surfaced desires for new experiences related to this decision."},
    36: {"title": "Crisis", "insight": "This gate may have brought urgency or crisis energy to your consideration."},
    37: {"title": "Friendship", "insight": "This gate may have revealed how this decision relates to your community."},
    41: {"title": "Contraction", "insight": "This gate may have sparked imagined futures related to this decision."},
    42: {"title": "Growth", "insight": "This gate may have shown what cycle needs completing before moving forward."},
    49: {"title": "Principles", "insight": "This gate may have clarified what principles guide this decision."},
    51: {"title": "Shock", "insight": "This gate may have brought initiating energy to your consideration."},
    55: {"title": "Spirit", "insight": "This gate may have shown how this decision affects your spirit."},
    63: {"title": "Doubt", "insight": "This gate may have surfaced important doubts and questions to address."},
}


def compute_weighted_emotional_score(text: str) -> Dict[str, Any]:
    """
    Compute weighted emotional scores using:
    - Keyword matching with base intensity
    - Intensity modifiers
    - Exclamation marks
    - Reflection length
    - Repeated emotional words
    
    Returns structured score object.
    """
    text_lower = text.lower()
    words = text_lower.split()
    
    # Initialize scores
    excitement_score = 0.0
    hesitation_score = 0.0
    neutrality_score = 0.0
    
    # Track matched keywords
    excitement_matches = []
    hesitation_matches = []
    
    # Find intensity modifier context
    intensity_multiplier = 1.0
    for modifier, mult in INTENSITY_MODIFIERS.items():
        if modifier in text_lower:
            intensity_multiplier = max(intensity_multiplier, mult)
    
    # Score excitement keywords
    for keyword, base_score in EXCITEMENT_KEYWORDS.items():
        count = text_lower.count(keyword)
        if count > 0:
            # Apply diminishing returns for repeated keywords
            score = base_score * (1 + 0.3 * (count - 1))
            excitement_score += score * intensity_multiplier
            excitement_matches.append(keyword)
    
    # Score hesitation keywords
    for keyword, base_score in HESITATION_KEYWORDS.items():
        count = text_lower.count(keyword)
        if count > 0:
            score = base_score * (1 + 0.3 * (count - 1))
            hesitation_score += score * intensity_multiplier
            hesitation_matches.append(keyword)
    
    # Score neutral keywords
    for keyword, base_score in NEUTRAL_KEYWORDS.items():
        if keyword in text_lower:
            neutrality_score += base_score
    
    # Exclamation mark boost
    exclamation_count = text.count('!')
    if exclamation_count > 0:
        excitement_score *= (1 + 0.15 * min(exclamation_count, 3))
    
    # Length factor (longer reflections may indicate more engagement)
    word_count = len(words)
    length_factor = min(1.0 + (word_count / 100), 1.3)
    
    # Apply length factor to dominant score
    if excitement_score > hesitation_score:
        excitement_score *= length_factor
    elif hesitation_score > excitement_score:
        hesitation_score *= length_factor
    
    # Normalize scores to 0-1 range
    max_possible = 5.0  # Rough ceiling
    excitement_normalized = min(excitement_score / max_possible, 1.0)
    hesitation_normalized = min(hesitation_score / max_possible, 1.0)
    neutrality_normalized = min(neutrality_score / max_possible, 1.0)
    
    # Determine dominant tone
    if excitement_normalized > hesitation_normalized * 1.5:
        dominant_tone = "excitement_dominant"
    elif hesitation_normalized > excitement_normalized * 1.5:
        dominant_tone = "hesitation_dominant"
    elif excitement_normalized > 0.2 and hesitation_normalized > 0.2:
        dominant_tone = "mixed"
    else:
        dominant_tone = "neutral"
    
    # Compute confidence based on signal strength
    signal_strength = max(excitement_normalized, hesitation_normalized, neutrality_normalized)
    confidence = min(signal_strength + 0.2, 1.0) if signal_strength > 0.1 else 0.3
    
    return {
        "excitement_score": round(excitement_normalized, 3),
        "hesitation_score": round(hesitation_normalized, 3),
        "neutrality_score": round(neutrality_normalized, 3),
        "dominant_tone": dominant_tone,
        "confidence": round(confidence, 3),
        "intensity_multiplier": intensity_multiplier,
        "excitement_keywords": excitement_matches,
        "hesitation_keywords": hesitation_matches,
    }


def extract_domain(text: str) -> str:
    """Extract primary domain from text."""
    text_lower = text.lower()
    domain_scores = {}
    
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            domain_scores[domain] = score
    
    if domain_scores:
        return max(domain_scores, key=domain_scores.get).value
    return Domain.IDENTITY_DIRECTION.value  # Default


def extract_tags(text: str) -> List[str]:
    """Extract relevant tags from text."""
    text_lower = text.lower()
    tags = []
    
    for tag, keywords in TAG_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            tags.append(tag)
    
    return tags[:5]  # Limit to top 5 tags


# =============================================================================
# PATTERN SIGNAL EXTRACTION - Task 70 Section 9
# =============================================================================

def generate_signal_id(user_id: str, source_type: str, source_id: str, timestamp: datetime) -> str:
    """Generate deterministic signal ID."""
    data = f"{user_id}:{source_type}:{source_id}:{timestamp.isoformat()}"
    return hashlib.sha256(data.encode()).hexdigest()[:16]


def extract_pattern_signals_from_lunar(
    entry: Dict[str, Any],
    user_id: str,
    decision_id: str,
    decision_topic: str
) -> List[PatternSignal]:
    """
    Extract normalized pattern signals from a lunar reflection entry.
    
    Args:
        entry: Lunar journal entry document
        user_id: User ID
        decision_id: Decision/consideration ID
        decision_topic: The decision being observed
    
    Returns:
        List of PatternSignal objects
    """
    content = entry.get("content", "")
    if not content:
        return []
    
    signals = []
    entry_id = str(entry.get("_id", ""))
    timestamp = entry.get("created_at", datetime.now(timezone.utc))
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    
    # Compute emotional scores
    emotional_data = compute_weighted_emotional_score(content)
    
    # Extract domain and tags
    domain = extract_domain(content)
    tags = extract_tags(content)
    
    # Add decision-specific tag
    if "business" in decision_topic.lower():
        tags.append("business_decision")
    elif "coach" in decision_topic.lower():
        tags.append("coaching_decision")
    elif "relocate" in decision_topic.lower() or "move" in decision_topic.lower():
        tags.append("relocation_decision")
    
    # Build metadata
    metadata = {
        "decision_id": decision_id,
        "decision_topic": decision_topic,
        "cycle_day": entry.get("lunar_day"),
        "gate": entry.get("moon_gate"),
        "gate_title": entry.get("gate_title"),
        "content_preview": content[:100] + "..." if len(content) > 100 else content,
        "word_count": len(content.split()),
        "emotional_keywords": {
            "excitement": emotional_data.get("excitement_keywords", []),
            "hesitation": emotional_data.get("hesitation_keywords", []),
        },
    }
    
    # Create primary signal based on dominant tone
    dominant = emotional_data["dominant_tone"]
    
    if dominant == "excitement_dominant":
        signal_type = SignalType.EXCITEMENT.value
        polarity = Polarity.POSITIVE.value
        intensity = emotional_data["excitement_score"]
    elif dominant == "hesitation_dominant":
        signal_type = SignalType.HESITATION.value
        polarity = Polarity.NEGATIVE.value
        intensity = emotional_data["hesitation_score"]
    elif dominant == "mixed":
        signal_type = SignalType.CONFUSION.value if emotional_data["hesitation_score"] > 0.3 else SignalType.CLARITY.value
        polarity = Polarity.MIXED.value
        intensity = max(emotional_data["excitement_score"], emotional_data["hesitation_score"])
    else:
        signal_type = SignalType.CLARITY.value
        polarity = Polarity.NEUTRAL.value
        intensity = emotional_data["neutrality_score"]
    
    primary_signal = PatternSignal(
        id=generate_signal_id(user_id, SourceType.LUNAR_REFLECTION.value, entry_id, timestamp),
        user_id=user_id,
        source_type=SourceType.LUNAR_REFLECTION.value,
        source_id=entry_id,
        timestamp=timestamp,
        domain=domain,
        signal_type=signal_type,
        polarity=polarity,
        intensity=round(intensity, 3),
        confidence=emotional_data["confidence"],
        tags=tags,
        metadata=metadata,
    )
    signals.append(primary_signal)
    
    # If mixed, also create secondary signal for the other emotion
    if dominant == "mixed":
        if emotional_data["excitement_score"] > 0.2:
            secondary = PatternSignal(
                id=generate_signal_id(user_id, SourceType.LUNAR_REFLECTION.value, entry_id + "_exc", timestamp),
                user_id=user_id,
                source_type=SourceType.LUNAR_REFLECTION.value,
                source_id=entry_id,
                timestamp=timestamp,
                domain=domain,
                signal_type=SignalType.EXCITEMENT.value,
                polarity=Polarity.POSITIVE.value,
                intensity=round(emotional_data["excitement_score"], 3),
                confidence=emotional_data["confidence"] * 0.8,
                tags=tags,
                metadata=metadata,
            )
            signals.append(secondary)
        
        if emotional_data["hesitation_score"] > 0.2:
            secondary = PatternSignal(
                id=generate_signal_id(user_id, SourceType.LUNAR_REFLECTION.value, entry_id + "_hes", timestamp),
                user_id=user_id,
                source_type=SourceType.LUNAR_REFLECTION.value,
                source_id=entry_id,
                timestamp=timestamp,
                domain=domain,
                signal_type=SignalType.HESITATION.value,
                polarity=Polarity.NEGATIVE.value,
                intensity=round(emotional_data["hesitation_score"], 3),
                confidence=emotional_data["confidence"] * 0.8,
                tags=tags,
                metadata=metadata,
            )
            signals.append(secondary)
    
    return signals


# =============================================================================
# STUB EXTRACTORS FOR FUTURE SOURCES - Task 70 Section 12
# =============================================================================

def extract_pattern_signals_from_journal(entry: Dict[str, Any], user_id: str) -> List[PatternSignal]:
    """
    STUB: Extract pattern signals from general journal entries.
    To be implemented in future version.
    """
    logger.debug("[PatternEngine] Journal extraction not yet implemented")
    return []


def extract_pattern_signals_from_mirror_chat(message: Dict[str, Any], user_id: str) -> List[PatternSignal]:
    """
    STUB: Extract pattern signals from mirror chat conversations.
    To be implemented in future version.
    """
    logger.debug("[PatternEngine] Mirror chat extraction not yet implemented")
    return []


def extract_pattern_signals_from_human_design(gate_activation: Dict[str, Any], user_id: str) -> List[PatternSignal]:
    """
    STUB: Extract pattern signals from Human Design gate activations.
    To be implemented in future version.
    """
    logger.debug("[PatternEngine] Human Design extraction not yet implemented")
    return []


def extract_pattern_signals_from_enneagram(data: Dict[str, Any], user_id: str) -> List[PatternSignal]:
    """
    STUB: Extract pattern signals from Enneagram patterns.
    To be implemented in future version.
    """
    logger.debug("[PatternEngine] Enneagram extraction not yet implemented")
    return []


# =============================================================================
# DECISION PATTERN SNAPSHOT - Task 70 Section 10
# =============================================================================

def compute_momentum_state(
    excitement_total: float,
    hesitation_total: float,
    entry_count: int,
    tone_consistency: float
) -> MomentumState:
    """Compute decision momentum state from aggregated signals."""
    
    if entry_count < 2:
        return MomentumState.UNCLEAR
    
    ratio = excitement_total / max(hesitation_total, 0.1)
    
    if ratio > 2.5 and tone_consistency > 0.6:
        return MomentumState.STRONG_POSITIVE
    elif ratio > 1.5:
        return MomentumState.POSITIVE
    elif ratio < 0.5 and tone_consistency > 0.5:
        return MomentumState.RESISTANT
    elif abs(ratio - 1.0) < 0.5:
        return MomentumState.MIXED
    else:
        return MomentumState.UNCLEAR


def get_momentum_description(momentum: MomentumState, decision_topic: str) -> str:
    """Get human-readable momentum description."""
    descriptions = {
        MomentumState.STRONG_POSITIVE: f"Your reflections across this cycle about {decision_topic} showed recurring excitement and curiosity, with relatively little hesitation.",
        MomentumState.POSITIVE: f"Your reflections about {decision_topic} lean toward positive energy, though some considerations remain.",
        MomentumState.MIXED: f"Your reflections about {decision_topic} showed both genuine pull and meaningful hesitation.",
        MomentumState.UNCLEAR: "There is not yet enough data to determine the momentum of this decision.",
        MomentumState.RESISTANT: f"Your reflections consistently returned to concern, pressure, or hesitation around {decision_topic}.",
    }
    return descriptions.get(momentum, descriptions[MomentumState.UNCLEAR])


async def get_decision_pattern_snapshot(
    db,
    user_id: str,
    decision_id: str
) -> DecisionPatternSnapshot:
    """
    Generate a lightweight pattern snapshot for a decision.
    
    Args:
        db: Database connection
        user_id: User ID
        decision_id: Decision/consideration ID
    
    Returns:
        DecisionPatternSnapshot with aggregated patterns
    """
    from bson import ObjectId
    
    # Fetch the decision
    consideration = await db.lunar_considerations.find_one({
        "_id": ObjectId(decision_id)
    })
    decision_topic = consideration.get("topic", "this decision") if consideration else "this decision"
    
    # Fetch entries
    entries = await db.lunar_journal.find({
        "user_id": user_id,
        "consideration_id": decision_id,
    }).to_list(length=100)
    
    entry_count = len(entries)
    unique_days = len(set(int(e.get("lunar_day", 0)) for e in entries))
    
    # Determine data sufficiency
    if entry_count >= 10:
        data_sufficiency = DataSufficiency.HIGH.value
    elif entry_count >= 5:
        data_sufficiency = DataSufficiency.MEDIUM.value
    elif entry_count >= 2:
        data_sufficiency = DataSufficiency.LOW.value
    else:
        data_sufficiency = DataSufficiency.INSUFFICIENT.value
    
    # Extract and aggregate signals
    all_signals = []
    total_excitement = 0.0
    total_hesitation = 0.0
    all_tags = []
    dominant_tones = []
    gate_scores = Counter()
    
    for entry in entries:
        signals = extract_pattern_signals_from_lunar(entry, user_id, decision_id, decision_topic)
        all_signals.extend(signals)
        
        for signal in signals:
            if signal.signal_type == SignalType.EXCITEMENT.value:
                total_excitement += signal.intensity
            elif signal.signal_type == SignalType.HESITATION.value:
                total_hesitation += signal.intensity
            
            all_tags.extend(signal.tags)
            dominant_tones.append(signal.signal_type)
            
            if signal.metadata.get("gate"):
                gate_scores[signal.metadata["gate"]] += signal.intensity + 0.5
    
    # Compute repeated tags
    tag_counts = Counter(all_tags)
    repeated_tags = [tag for tag, count in tag_counts.most_common(5) if count >= 1]
    
    # Find strongest gate
    strongest_gate = gate_scores.most_common(1)[0][0] if gate_scores else None
    
    # Compute tone consistency (how often the same tone appears)
    if dominant_tones:
        most_common_tone = Counter(dominant_tones).most_common(1)[0]
        tone_consistency = most_common_tone[1] / len(dominant_tones)
    else:
        tone_consistency = 0.0
    
    # Compute momentum
    momentum = compute_momentum_state(
        total_excitement,
        total_hesitation,
        entry_count,
        tone_consistency
    )
    
    # Determine dominant signals
    dominant_signals = []
    if total_excitement > total_hesitation:
        dominant_signals.append("excitement")
    elif total_hesitation > total_excitement:
        dominant_signals.append("hesitation")
    if abs(total_excitement - total_hesitation) < 0.5 and entry_count >= 2:
        dominant_signals.append("mixed")
    
    # Compute overall confidence
    if entry_count >= 5:
        confidence = 0.8 + (min(entry_count, 10) / 50)
    elif entry_count >= 2:
        confidence = 0.4 + (entry_count * 0.1)
    else:
        confidence = 0.2
    
    return DecisionPatternSnapshot(
        decision_id=decision_id,
        decision_topic=decision_topic,
        data_sufficiency=data_sufficiency,
        entry_count=entry_count,
        days_observed=unique_days,
        dominant_signals=dominant_signals,
        repeated_tags=repeated_tags,
        strongest_gate=strongest_gate,
        momentum=momentum.value,
        excitement_score=round(total_excitement, 3),
        hesitation_score=round(total_hesitation, 3),
        confidence=round(confidence, 3),
    )


# =============================================================================
# PATTERN SIGNAL STORAGE - Task 70 Section 11
# =============================================================================

async def store_pattern_signals(db, signals: List[PatternSignal]) -> int:
    """
    Store pattern signals in the database.
    Uses upsert to avoid duplicates.
    
    Returns number of signals stored.
    """
    if not signals:
        return 0
    
    stored = 0
    for signal in signals:
        try:
            await db.pattern_signals.update_one(
                {"id": signal.id},
                {"$set": signal.to_dict()},
                upsert=True
            )
            stored += 1
        except Exception as e:
            logger.error(f"[PatternEngine] Error storing signal {signal.id}: {e}")
    
    return stored


async def get_user_pattern_signals(
    db,
    user_id: str,
    source_type: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Retrieve pattern signals for a user."""
    query = {"user_id": user_id}
    if source_type:
        query["source_type"] = source_type
    
    cursor = db.pattern_signals.find(query).sort("timestamp", -1).limit(limit)
    return await cursor.to_list(length=limit)


# =============================================================================
# DEBUG MODE - Task 70 Section 13
# =============================================================================

async def get_debug_pattern_analysis(
    db,
    user_id: str,
    decision_id: str
) -> Dict[str, Any]:
    """
    Get detailed debug information about pattern analysis.
    Developer-facing only.
    """
    from bson import ObjectId
    
    # Fetch the decision
    consideration = await db.lunar_considerations.find_one({
        "_id": ObjectId(decision_id)
    })
    decision_topic = consideration.get("topic", "this decision") if consideration else "this decision"
    
    # Fetch entries
    entries = await db.lunar_journal.find({
        "user_id": user_id,
        "consideration_id": decision_id,
    }).to_list(length=100)
    
    # Analyze each entry
    entry_analyses = []
    for entry in entries:
        content = entry.get("content", "")
        emotional_data = compute_weighted_emotional_score(content)
        signals = extract_pattern_signals_from_lunar(entry, user_id, decision_id, decision_topic)
        
        entry_analyses.append({
            "entry_id": str(entry.get("_id", "")),
            "cycle_day": entry.get("lunar_day"),
            "gate": entry.get("moon_gate"),
            "content_preview": content[:80] + "..." if len(content) > 80 else content,
            "emotional_scores": {
                "excitement": emotional_data["excitement_score"],
                "hesitation": emotional_data["hesitation_score"],
                "neutrality": emotional_data["neutrality_score"],
            },
            "dominant_tone": emotional_data["dominant_tone"],
            "confidence": emotional_data["confidence"],
            "intensity_multiplier": emotional_data["intensity_multiplier"],
            "matched_keywords": {
                "excitement": emotional_data.get("excitement_keywords", []),
                "hesitation": emotional_data.get("hesitation_keywords", []),
            },
            "extracted_tags": extract_tags(content),
            "extracted_domain": extract_domain(content),
            "signals_generated": len(signals),
        })
    
    # Get snapshot
    snapshot = await get_decision_pattern_snapshot(db, user_id, decision_id)
    
    return {
        "debug_mode": True,
        "decision_id": decision_id,
        "decision_topic": decision_topic,
        "total_entries": len(entries),
        "snapshot": {
            "data_sufficiency": snapshot.data_sufficiency,
            "dominant_signals": snapshot.dominant_signals,
            "repeated_tags": snapshot.repeated_tags,
            "strongest_gate": snapshot.strongest_gate,
            "momentum": snapshot.momentum,
            "excitement_total": snapshot.excitement_score,
            "hesitation_total": snapshot.hesitation_score,
            "confidence": snapshot.confidence,
        },
        "momentum_description": get_momentum_description(
            MomentumState(snapshot.momentum),
            decision_topic
        ),
        "entry_analyses": entry_analyses,
    }
