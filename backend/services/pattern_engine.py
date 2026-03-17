"""
Mirror Pattern Engine v0.15 - Task 71

Enhanced foundation for cross-lens pattern intelligence:
- Persistent signal storage with idempotency
- Source stub interfaces for future multi-lens expansion
- Improved decision snapshots with confidence logic
- Time window filtering support
- Tag/signal normalization

Sources (active and stubbed):
- Lunar reflections (ACTIVE)
- Journal entries (STUB)
- Mirror chat (STUB)
- Human Design gate activations (STUB)
- Enneagram patterns (STUB)
- Gene Keys (STUB)
- Transits (STUB)
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Literal, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import re
from collections import Counter
import hashlib

logger = logging.getLogger(__name__)

# =============================================================================
# ENUMS AND TYPE DEFINITIONS - v0.15
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


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"


class TimeWindow(str, Enum):
    ALL_TIME = "all_time"
    LAST_30_DAYS = "last_30_days"
    LAST_7_DAYS = "last_7_days"
    CURRENT_CYCLE = "current_cycle"
    CURRENT_DECISION = "current_decision"


# =============================================================================
# PATTERN SIGNAL MODEL - v0.15 Enhanced
# =============================================================================

@dataclass
class PatternSignal:
    """
    Unified pattern signal model for cross-lens intelligence.
    v0.15: Added source_event_id, created_at, updated_at for persistence.
    """
    id: str
    user_id: str
    source_type: str
    source_id: str  # e.g., decision_id, journal_entry_id
    source_event_id: str  # Specific event ID (e.g., reflection entry ID)
    timestamp: datetime
    domain: str
    signal_type: str
    polarity: str
    intensity: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    tags: List[str]
    metadata: Dict[str, Any]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        for key in ['timestamp', 'created_at', 'updated_at']:
            if isinstance(data.get(key), datetime):
                data[key] = data[key].isoformat()
        return data
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'PatternSignal':
        """Create PatternSignal from dictionary."""
        # Parse datetime fields
        for key in ['timestamp', 'created_at', 'updated_at']:
            if key in data and isinstance(data[key], str):
                data[key] = datetime.fromisoformat(data[key].replace('Z', '+00:00'))
        return PatternSignal(**data)
    
    def get_dedupe_key(self) -> str:
        """
        Generate stable dedupe key for idempotent ingestion.
        Key components: user_id, source_type, source_id, source_event_id, signal_type, domain
        """
        key_parts = [
            self.user_id,
            self.source_type,
            self.source_id,
            self.source_event_id,
            self.signal_type,
            self.domain
        ]
        key_string = "|".join(str(p) for p in key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()[:24]


@dataclass
class DecisionPatternSnapshot:
    """
    Lightweight snapshot of decision patterns for synthesis.
    v0.15: Added confidence_level, source_breakdown, recent_signal_count
    """
    decision_id: str
    decision_topic: str
    data_sufficiency: str
    entry_count: int
    days_observed: int
    distinct_days: int  # v0.15: Actual unique observation days
    dominant_signals: List[str]
    repeated_tags: List[str]
    strongest_gate: Optional[int]
    momentum: str
    excitement_score: float
    hesitation_score: float
    confidence: float
    confidence_level: str  # v0.15: low/moderate/high
    total_signals: int  # v0.15
    source_breakdown: Dict[str, int]  # v0.15
    domain_distribution: Dict[str, int]  # v0.15
    recent_signal_count: int  # v0.15: Signals in last 7 days


# =============================================================================
# TAG AND LABEL NORMALIZATION - v0.15 Section 7
# =============================================================================

TAG_NORMALIZATION_MAP = {
    # Common variations to canonical form
    "creative independence": "creative_independence",
    "creative-independence": "creative_independence",
    "new beginning": "new_beginning",
    "new beginnings": "new_beginning",
    "new-beginning": "new_beginning",
    "financial security": "financial_security",
    "financial-security": "financial_security",
    "work purpose": "work_purpose",
    "work-purpose": "work_purpose",
}


def normalize_tag(tag: str) -> str:
    """Normalize a tag to canonical form."""
    # Lowercase and strip
    normalized = tag.lower().strip()
    # Check normalization map
    if normalized in TAG_NORMALIZATION_MAP:
        return TAG_NORMALIZATION_MAP[normalized]
    # Replace spaces and hyphens with underscores
    normalized = re.sub(r'[\s\-]+', '_', normalized)
    # Remove duplicate underscores
    normalized = re.sub(r'_+', '_', normalized)
    return normalized


def normalize_tags(tags: List[str]) -> List[str]:
    """Normalize a list of tags and remove duplicates."""
    normalized = [normalize_tag(t) for t in tags]
    # Remove duplicates while preserving order
    seen = set()
    result = []
    for tag in normalized:
        if tag not in seen:
            seen.add(tag)
            result.append(tag)
    return result


def normalize_source_type(source_type: str) -> str:
    """Normalize source type to canonical form."""
    return source_type.lower().strip().replace("-", "_").replace(" ", "_")


def normalize_domain(domain: str) -> str:
    """Normalize domain to canonical form."""
    return domain.lower().strip().replace("-", "_").replace(" ", "_")


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

def generate_signal_id(user_id: str, source_type: str, source_id: str, timestamp: datetime, suffix: str = "") -> str:
    """Generate deterministic signal ID."""
    data = f"{user_id}:{source_type}:{source_id}:{timestamp.isoformat()}:{suffix}"
    return hashlib.sha256(data.encode()).hexdigest()[:16]


def extract_pattern_signals_from_lunar(
    entry: Dict[str, Any],
    user_id: str,
    decision_id: str,
    decision_topic: str
) -> List[PatternSignal]:
    """
    Extract normalized pattern signals from a lunar reflection entry.
    
    v0.15: Added source_event_id for better deduplication, created_at/updated_at tracking.
    
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
    
    now = datetime.now(timezone.utc)
    
    # Compute emotional scores
    emotional_data = compute_weighted_emotional_score(content)
    
    # Extract domain and tags (with normalization)
    domain = extract_domain(content)
    tags = normalize_tags(extract_tags(content))
    
    # Add decision-specific tag
    if "business" in decision_topic.lower():
        tags.append(normalize_tag("business_decision"))
    elif "coach" in decision_topic.lower():
        tags.append(normalize_tag("coaching_decision"))
    elif "relocate" in decision_topic.lower() or "move" in decision_topic.lower():
        tags.append(normalize_tag("relocation_decision"))
    
    # Dedupe tags
    tags = list(dict.fromkeys(tags))[:5]
    
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
        id=generate_signal_id(user_id, SourceType.LUNAR_REFLECTION.value, entry_id, timestamp, "primary"),
        user_id=user_id,
        source_type=SourceType.LUNAR_REFLECTION.value,
        source_id=decision_id,  # v0.15: source_id is now decision_id
        source_event_id=entry_id,  # v0.15: specific entry ID
        timestamp=timestamp,
        domain=domain,
        signal_type=signal_type,
        polarity=polarity,
        intensity=round(intensity, 3),
        confidence=emotional_data["confidence"],
        tags=tags,
        metadata=metadata,
        created_at=now,
        updated_at=now,
    )
    signals.append(primary_signal)
    
    # If mixed, also create secondary signal for the other emotion
    if dominant == "mixed":
        if emotional_data["excitement_score"] > 0.2:
            secondary = PatternSignal(
                id=generate_signal_id(user_id, SourceType.LUNAR_REFLECTION.value, entry_id, timestamp, "excitement"),
                user_id=user_id,
                source_type=SourceType.LUNAR_REFLECTION.value,
                source_id=decision_id,
                source_event_id=entry_id,
                timestamp=timestamp,
                domain=domain,
                signal_type=SignalType.EXCITEMENT.value,
                polarity=Polarity.POSITIVE.value,
                intensity=round(emotional_data["excitement_score"], 3),
                confidence=emotional_data["confidence"] * 0.8,
                tags=tags,
                metadata=metadata,
                created_at=now,
                updated_at=now,
            )
            signals.append(secondary)
        
        if emotional_data["hesitation_score"] > 0.2:
            secondary = PatternSignal(
                id=generate_signal_id(user_id, SourceType.LUNAR_REFLECTION.value, entry_id, timestamp, "hesitation"),
                user_id=user_id,
                source_type=SourceType.LUNAR_REFLECTION.value,
                source_id=decision_id,
                source_event_id=entry_id,
                timestamp=timestamp,
                domain=domain,
                signal_type=SignalType.HESITATION.value,
                polarity=Polarity.NEGATIVE.value,
                intensity=round(emotional_data["hesitation_score"], 3),
                confidence=emotional_data["confidence"] * 0.8,
                tags=tags,
                metadata=metadata,
                created_at=now,
                updated_at=now,
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


def extract_pattern_signals_from_gene_keys(data: Dict[str, Any], user_id: str) -> List[PatternSignal]:
    """
    STUB: Extract pattern signals from Gene Keys data.
    To be implemented in future version.
    """
    logger.debug("[PatternEngine] Gene Keys extraction not yet implemented")
    return []


def extract_pattern_signals_from_transit(transit_data: Dict[str, Any], user_id: str) -> List[PatternSignal]:
    """
    STUB: Extract pattern signals from planetary transits.
    To be implemented in future version.
    """
    logger.debug("[PatternEngine] Transit extraction not yet implemented")
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
    
    v0.15: Enhanced with confidence_level, source_breakdown, domain_distribution,
    distinct_days, and recent_signal_count for better trust indicators.
    
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
    
    # v0.15: Calculate distinct observation days
    observation_days = set()
    recent_cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    recent_entry_count = 0
    
    for entry in entries:
        lunar_day = entry.get("lunar_day")
        if lunar_day:
            observation_days.add(int(lunar_day))
        
        # Check if entry is recent
        entry_time = entry.get("created_at")
        if entry_time:
            if isinstance(entry_time, str):
                entry_time = datetime.fromisoformat(entry_time.replace('Z', '+00:00'))
            # Ensure timezone-aware comparison
            if entry_time.tzinfo is None:
                entry_time = entry_time.replace(tzinfo=timezone.utc)
            if entry_time >= recent_cutoff:
                recent_entry_count += 1
    
    distinct_days = len(observation_days)
    unique_days = distinct_days  # Backward compatibility alias
    
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
    domain_counts = Counter()
    source_counts = Counter()
    
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
            domain_counts[signal.domain] += 1
            source_counts[signal.source_type] += 1
            
            if signal.metadata.get("gate"):
                gate_scores[signal.metadata["gate"]] += signal.intensity + 0.5
    
    total_signals = len(all_signals)
    
    # Compute repeated tags (with normalization)
    normalized_tags = normalize_tags(all_tags)
    tag_counts = Counter(normalized_tags)
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
    
    # v0.15: Compute confidence level based on multiple factors
    # Factors: entry_count, distinct_days, distinct_tags, recency
    confidence_score = 0.0
    
    # Entry count factor (max 0.3)
    confidence_score += min(entry_count / 10, 1.0) * 0.3
    
    # Distinct observation days factor (max 0.25)
    confidence_score += min(distinct_days / 15, 1.0) * 0.25
    
    # Tag diversity factor (max 0.2)
    unique_tag_count = len(set(normalized_tags))
    confidence_score += min(unique_tag_count / 8, 1.0) * 0.2
    
    # Recency factor (max 0.25) - how active is recent data
    if entry_count > 0:
        recency_ratio = recent_entry_count / entry_count
        confidence_score += recency_ratio * 0.25
    
    # Map score to level
    if confidence_score >= 0.65:
        confidence_level = ConfidenceLevel.HIGH.value
    elif confidence_score >= 0.35:
        confidence_level = ConfidenceLevel.MODERATE.value
    else:
        confidence_level = ConfidenceLevel.LOW.value
    
    # Legacy confidence value (for backward compatibility)
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
        distinct_days=distinct_days,
        dominant_signals=dominant_signals,
        repeated_tags=repeated_tags,
        strongest_gate=strongest_gate,
        momentum=momentum.value,
        excitement_score=round(total_excitement, 3),
        hesitation_score=round(total_hesitation, 3),
        confidence=round(confidence, 3),
        confidence_level=confidence_level,
        total_signals=total_signals,
        source_breakdown=dict(source_counts),
        domain_distribution=dict(domain_counts),
        recent_signal_count=recent_entry_count,
    )


# =============================================================================
# PATTERN SIGNAL STORAGE - v0.15 Idempotent Persistence
# =============================================================================

async def store_pattern_signals(db, signals: List[PatternSignal]) -> Tuple[int, int]:
    """
    Store pattern signals in the database with idempotent upsert.
    
    v0.15: Uses dedupe_key for reliable idempotency.
    Re-ingesting the same data will update existing signals, not create duplicates.
    
    Args:
        db: Database connection
        signals: List of PatternSignal objects to store
    
    Returns:
        Tuple of (inserted_count, updated_count)
    """
    if not signals:
        return (0, 0)
    
    inserted = 0
    updated = 0
    
    for signal in signals:
        try:
            dedupe_key = signal.get_dedupe_key()
            now = datetime.now(timezone.utc)
            
            # Check if signal exists by dedupe key
            existing = await db.pattern_signals.find_one({"dedupe_key": dedupe_key})
            
            signal_data = signal.to_dict()
            signal_data["dedupe_key"] = dedupe_key
            signal_data["updated_at"] = now.isoformat()
            
            if existing:
                # Update existing signal
                await db.pattern_signals.update_one(
                    {"dedupe_key": dedupe_key},
                    {"$set": signal_data}
                )
                updated += 1
            else:
                # Insert new signal
                signal_data["created_at"] = now.isoformat()
                await db.pattern_signals.insert_one(signal_data)
                inserted += 1
                
        except Exception as e:
            logger.error(f"[PatternEngine] Error storing signal {signal.id}: {e}")
    
    logger.info(f"[PatternEngine] Storage complete: {inserted} inserted, {updated} updated")
    return (inserted, updated)


async def get_user_pattern_signals(
    db,
    user_id: str,
    source_type: Optional[str] = None,
    decision_id: Optional[str] = None,
    time_window: Optional[TimeWindow] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Retrieve pattern signals for a user with filtering options.
    
    v0.15: Added decision_id and time_window filtering support.
    
    Args:
        db: Database connection
        user_id: User ID
        source_type: Optional filter by source type
        decision_id: Optional filter by decision ID
        time_window: Optional time window filter
        limit: Maximum number of signals to return
    
    Returns:
        List of signal dictionaries
    """
    query = {"user_id": user_id}
    
    if source_type:
        query["source_type"] = normalize_source_type(source_type)
    
    if decision_id:
        query["source_id"] = decision_id
    
    # Apply time window filter
    if time_window:
        now = datetime.now(timezone.utc)
        
        if time_window == TimeWindow.LAST_7_DAYS:
            cutoff = now - timedelta(days=7)
            query["timestamp"] = {"$gte": cutoff.isoformat()}
        elif time_window == TimeWindow.LAST_30_DAYS:
            cutoff = now - timedelta(days=30)
            query["timestamp"] = {"$gte": cutoff.isoformat()}
        elif time_window == TimeWindow.CURRENT_CYCLE:
            # Approximately one lunar cycle
            cutoff = now - timedelta(days=30)
            query["timestamp"] = {"$gte": cutoff.isoformat()}
        # ALL_TIME and CURRENT_DECISION don't need time filters
    
    cursor = db.pattern_signals.find(query).sort("timestamp", -1).limit(limit)
    return await cursor.to_list(length=limit)


async def count_pattern_signals_by_source(db, user_id: str) -> Dict[str, int]:
    """
    Count pattern signals by source type for a user.
    
    Returns:
        Dictionary mapping source_type to count
    """
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": "$source_type", "count": {"$sum": 1}}},
    ]
    
    results = await db.pattern_signals.aggregate(pipeline).to_list(length=20)
    
    # Initialize all source types with 0
    counts = {
        SourceType.LUNAR_REFLECTION.value: 0,
        SourceType.JOURNAL_ENTRY.value: 0,
        SourceType.MIRROR_CHAT.value: 0,
        SourceType.HUMAN_DESIGN_GATE.value: 0,
        SourceType.ENNEAGRAM.value: 0,
        SourceType.GENE_KEYS.value: 0,
        SourceType.TRANSIT.value: 0,
    }
    
    for result in results:
        source = result["_id"]
        if source in counts:
            counts[source] = result["count"]
    
    return counts


async def delete_user_pattern_signals(
    db,
    user_id: str,
    source_type: Optional[str] = None,
    decision_id: Optional[str] = None
) -> int:
    """
    Delete pattern signals for a user.
    
    Args:
        db: Database connection
        user_id: User ID
        source_type: Optional filter by source type
        decision_id: Optional filter by decision ID
    
    Returns:
        Number of signals deleted
    """
    query = {"user_id": user_id}
    
    if source_type:
        query["source_type"] = normalize_source_type(source_type)
    
    if decision_id:
        query["source_id"] = decision_id
    
    result = await db.pattern_signals.delete_many(query)
    logger.info(f"[PatternEngine] Deleted {result.deleted_count} signals for user {user_id[:8]}...")
    return result.deleted_count


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


# =============================================================================
# PATTERN GRAPH SNAPSHOT - v0.1 User-Level Aggregation
# =============================================================================

@dataclass
class DomainSummary:
    """Summary of a single domain in the pattern graph."""
    domain: str
    domain_label: str
    signal_count: int
    dominant_signals: List[str]
    dominant_tags: List[str]
    average_intensity: float
    polarity_breakdown: Dict[str, int]


@dataclass
class PatternGraphSnapshot:
    """
    User-level pattern graph snapshot.
    Aggregates all signals across sources into a unified view.
    """
    user_id: str
    generated_at: datetime
    total_signals: int
    active_domains: List[DomainSummary]
    strongest_signals: List[Dict[str, Any]]
    recent_signals: List[Dict[str, Any]]
    source_breakdown: Dict[str, int]
    repeated_tags: List[str]
    overall_momentum: str
    data_sufficiency: str


DOMAIN_LABELS = {
    Domain.WORK_PURPOSE.value: "Work & Purpose",
    Domain.EMOTIONAL_LANDSCAPE.value: "Emotional Landscape",
    Domain.RELATIONSHIPS.value: "Relationships",
    Domain.EXPRESSION_ACTION.value: "Expression & Action",
    Domain.IDENTITY_DIRECTION.value: "Identity & Direction",
    Domain.PRESSURE_STRESS.value: "Pressure & Stress",
    Domain.TIMING_READINESS.value: "Timing & Readiness",
}


# =============================================================================
# LIFELINE SIGNAL EXTRACTION
# =============================================================================

# Map Lifeline categories to pattern domains
LIFELINE_CATEGORY_DOMAIN_MAP = {
    "career": Domain.WORK_PURPOSE.value,
    "work": Domain.WORK_PURPOSE.value,
    "job": Domain.WORK_PURPOSE.value,
    "professional": Domain.WORK_PURPOSE.value,
    "relationship": Domain.RELATIONSHIPS.value,
    "relationships": Domain.RELATIONSHIPS.value,
    "family": Domain.RELATIONSHIPS.value,
    "marriage": Domain.RELATIONSHIPS.value,
    "divorce": Domain.RELATIONSHIPS.value,
    "friendship": Domain.RELATIONSHIPS.value,
    "growth": Domain.IDENTITY_DIRECTION.value,
    "transformation": Domain.IDENTITY_DIRECTION.value,
    "turning point": Domain.IDENTITY_DIRECTION.value,
    "milestone": Domain.IDENTITY_DIRECTION.value,
    "achievement": Domain.EXPRESSION_ACTION.value,
    "challenge": Domain.PRESSURE_STRESS.value,
    "identity": Domain.IDENTITY_DIRECTION.value,
    "move": Domain.IDENTITY_DIRECTION.value,
    "relocation": Domain.IDENTITY_DIRECTION.value,
    "education": Domain.WORK_PURPOSE.value,
    "learning": Domain.WORK_PURPOSE.value,
    "health": Domain.PRESSURE_STRESS.value,
    "illness": Domain.PRESSURE_STRESS.value,
    "recovery": Domain.EMOTIONAL_LANDSCAPE.value,
    "loss": Domain.EMOTIONAL_LANDSCAPE.value,
    "grief": Domain.EMOTIONAL_LANDSCAPE.value,
    "joy": Domain.EMOTIONAL_LANDSCAPE.value,
    "trauma": Domain.EMOTIONAL_LANDSCAPE.value,
}


def extract_signals_from_lifeline_events(
    lifeline_events: List[dict],
    user_id: str
) -> List[Dict[str, Any]]:
    """
    Extract pattern signals from Lifeline events.
    
    Creates signals for:
    - Individual events (mapped to domains)
    - Repeated categories (strong signals)
    - High-impact events
    - Time-clustered periods
    
    Args:
        lifeline_events: List of Lifeline events from the database
        user_id: User ID
    
    Returns:
        List of signal dictionaries in the pattern_signals format
    """
    signals = []
    category_counts: Dict[str, int] = {}
    high_impact_events = []
    decade_clusters: Dict[int, List[dict]] = {}
    
    for event in lifeline_events:
        event_id = str(event.get("_id", event.get("id", "")))
        event_category = (event.get("category") or "").lower()
        event_year = event.get("year")
        event_title = event.get("title", "")[:50]
        impact_score = event.get("impact_score", 5)
        
        # Track category counts
        if event_category:
            category_counts[event_category] = category_counts.get(event_category, 0) + 1
        
        # Track high-impact events
        if impact_score and impact_score >= 7:
            high_impact_events.append(event)
        
        # Track decade clusters
        if event_year:
            decade = (event_year // 10) * 10
            if decade not in decade_clusters:
                decade_clusters[decade] = []
            decade_clusters[decade].append(event)
        
        # Determine domain from category
        domain = Domain.IDENTITY_DIRECTION.value  # Default
        for cat_key, domain_val in LIFELINE_CATEGORY_DOMAIN_MAP.items():
            if cat_key in event_category:
                domain = domain_val
                break
        
        # Create signal for this event
        signal = {
            "id": f"lifeline_{event_id}",
            "user_id": user_id,
            "source_type": "lifeline",
            "signal_type": "clarity" if impact_score >= 6 else "experience",
            "domain": domain,
            "intensity": min(0.9, 0.5 + (impact_score or 5) * 0.05),
            "polarity": "positive" if event.get("emotional_tone") == "positive" else "mixed",
            "tags": [t for t in (event.get("tags") or [])[:3]],
            "preview": event_title,
            "timestamp": event.get("date") or (f"{event_year}-01-01" if event_year else None),
            "context": {
                "year": event_year,
                "category": event.get("category"),
                "source": "lifeline"
            }
        }
        signals.append(signal)
    
    # Add signals for REPEATED CATEGORIES (strong pattern evidence)
    for cat_name, count in category_counts.items():
        if count >= 2:  # At least 2 events in same category
            domain = Domain.IDENTITY_DIRECTION.value
            for cat_key, domain_val in LIFELINE_CATEGORY_DOMAIN_MAP.items():
                if cat_key in cat_name:
                    domain = domain_val
                    break
            
            signal = {
                "id": f"lifeline_pattern_{cat_name}_{count}",
                "user_id": user_id,
                "source_type": "lifeline_pattern",
                "signal_type": "clarity" if count >= 3 else "direction",
                "domain": domain,
                "intensity": min(0.9, 0.5 + count * 0.1),
                "polarity": "positive",
                "tags": [cat_name, "recurring", "life_theme"],
                "preview": f"Recurring {cat_name.title()} theme ({count} events)",
                "timestamp": None,
                "context": {
                    "pattern_type": "repeated_category",
                    "event_count": count,
                    "source": "lifeline"
                }
            }
            signals.append(signal)
    
    # Add signals for HIGH-IMPACT EVENTS
    for event in high_impact_events[:3]:
        event_id = str(event.get("_id", event.get("id", "")))
        event_category = (event.get("category") or "").lower()
        
        domain = Domain.IDENTITY_DIRECTION.value
        for cat_key, domain_val in LIFELINE_CATEGORY_DOMAIN_MAP.items():
            if cat_key in event_category:
                domain = domain_val
                break
        
        signal = {
            "id": f"lifeline_impact_{event_id}",
            "user_id": user_id,
            "source_type": "lifeline_impact",
            "signal_type": "clarity",
            "domain": domain,
            "intensity": 0.85,
            "polarity": "mixed" if event.get("emotional_tone") == "mixed" else "positive",
            "tags": ["high_impact", "pivotal_moment"],
            "preview": f"Major: {event.get('title', 'Pivotal moment')[:40]}",
            "timestamp": event.get("date"),
            "context": {
                "impact_score": event.get("impact_score", 7),
                "year": event.get("year"),
                "source": "lifeline"
            }
        }
        signals.append(signal)
    
    # Add signals for DECADE CLUSTERS
    for decade, events in decade_clusters.items():
        if len(events) >= 3:
            signal = {
                "id": f"lifeline_cluster_{decade}s",
                "user_id": user_id,
                "source_type": "lifeline_cluster",
                "signal_type": "direction",
                "domain": Domain.TIMING_READINESS.value,
                "intensity": min(0.85, 0.5 + len(events) * 0.08),
                "polarity": "positive",
                "tags": ["time_cluster", f"{decade}s", "active_period"],
                "preview": f"Active period: {decade}s ({len(events)} events)",
                "timestamp": f"{decade}-01-01",
                "context": {
                    "decade": decade,
                    "event_count": len(events),
                    "source": "lifeline"
                }
            }
            signals.append(signal)
    
    logger.info(f"[PatternEngine] Extracted {len(signals)} signals from Lifeline events")
    return signals


async def get_pattern_graph_snapshot(
    db,
    user_id: str,
    include_debug: bool = False
) -> Dict[str, Any]:
    """
    Generate a user-level pattern graph snapshot.
    
    Aggregates all pattern signals from all sources into a unified view:
    - Stored pattern signals (from Lunar reflections)
    - Live Lunar journal signals
    - Lifeline events (categories, high-impact moments, time clusters)
    
    Args:
        db: Database connection
        user_id: User ID
        include_debug: Include debug information
    
    Returns:
        Pattern graph snapshot as a dictionary
    """
    # Fetch all stored signals for user
    stored_signals = await get_user_pattern_signals(db, user_id, limit=500)
    
    # Also generate live signals from lunar entries if not enough stored
    if len(stored_signals) < 5:
        # Fetch all lunar entries and generate signals on the fly
        lunar_entries = await db.lunar_journal.find({
            "user_id": user_id
        }).to_list(length=200)
        
        # Get all considerations to map entries
        considerations = await db.lunar_considerations.find({
            "user_id": user_id
        }).to_list(length=50)
        consideration_map = {str(c["_id"]): c.get("topic", "Unknown") for c in considerations}
        
        # Generate signals from lunar entries
        live_signals = []
        for entry in lunar_entries:
            consideration_id = entry.get("consideration_id", "")
            decision_topic = consideration_map.get(consideration_id, "Decision")
            signals = extract_pattern_signals_from_lunar(
                entry, user_id, consideration_id, decision_topic
            )
            live_signals.extend([s.to_dict() for s in signals])
        
        # Combine with stored signals (dedupe by id)
        seen_ids = {s.get("id") for s in stored_signals}
        for signal in live_signals:
            if signal.get("id") not in seen_ids:
                stored_signals.append(signal)
    
    # =========================================================================
    # NEW: Generate signals from Lifeline events
    # =========================================================================
    lifeline_events = await db.lifeline_events.find({
        "user_id": user_id
    }).sort("year", -1).limit(30).to_list(30)
    
    if lifeline_events:
        lifeline_signals = extract_signals_from_lifeline_events(lifeline_events, user_id)
        
        # Add Lifeline signals (they won't have IDs that conflict with stored_signals)
        stored_signals.extend(lifeline_signals)
        logger.info(f"[PatternEngine] Added {len(lifeline_signals)} Lifeline signals for user {user_id}")
    
    if not stored_signals:
        return {
            "user_id": user_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_signals": 0,
            "active_domains": [],
            "strongest_signals": [],
            "recent_signals": [],
            "source_breakdown": {},
            "repeated_tags": [],
            "overall_momentum": "unclear",
            "data_sufficiency": "insufficient",
            "message": "Pattern signals begin to appear when you add moments, reflections, or decision observations. Mirror looks for repeated themes across your life and journal.",
        }
    
    # Aggregate by domain
    domain_signals = {}
    all_tags = []
    source_counts = Counter()
    total_excitement = 0.0
    total_hesitation = 0.0
    
    for signal in stored_signals:
        domain = signal.get("domain", Domain.IDENTITY_DIRECTION.value)
        if domain not in domain_signals:
            domain_signals[domain] = []
        domain_signals[domain].append(signal)
        
        # Collect tags
        all_tags.extend(signal.get("tags", []))
        
        # Track source types
        source_counts[signal.get("source_type", "unknown")] += 1
        
        # Aggregate emotional scores
        signal_type = signal.get("signal_type", "")
        intensity = signal.get("intensity", 0.5)
        if signal_type == SignalType.EXCITEMENT.value:
            total_excitement += intensity
        elif signal_type == SignalType.HESITATION.value:
            total_hesitation += intensity
    
    # Build domain summaries
    active_domains = []
    for domain, signals in domain_signals.items():
        if not signals:
            continue
        
        # Calculate domain metrics
        signal_types = Counter(s.get("signal_type") for s in signals)
        polarity_breakdown = Counter(s.get("polarity") for s in signals)
        domain_tags = []
        intensities = []
        
        for s in signals:
            domain_tags.extend(s.get("tags", []))
            intensities.append(s.get("intensity", 0.5))
        
        avg_intensity = sum(intensities) / len(intensities) if intensities else 0.5
        
        active_domains.append({
            "domain": domain,
            "domain_label": DOMAIN_LABELS.get(domain, domain.replace("_", " ").title()),
            "signal_count": len(signals),
            "dominant_signals": [st[0] for st in signal_types.most_common(3)],
            "dominant_tags": [t[0] for t in Counter(domain_tags).most_common(3)],
            "average_intensity": round(avg_intensity, 2),
            "polarity_breakdown": dict(polarity_breakdown),
        })
    
    # Sort domains by signal count
    active_domains.sort(key=lambda d: d["signal_count"], reverse=True)
    
    # Get strongest signals (highest intensity)
    sorted_by_intensity = sorted(
        stored_signals,
        key=lambda s: s.get("intensity", 0),
        reverse=True
    )
    strongest_signals = [
        {
            "signal_type": s.get("signal_type"),
            "domain": s.get("domain"),
            "intensity": s.get("intensity"),
            "polarity": s.get("polarity"),
            "source_type": s.get("source_type"),
            "tags": s.get("tags", [])[:3],
            "preview": s.get("metadata", {}).get("content_preview", "")[:60],
        }
        for s in sorted_by_intensity[:5]
    ]
    
    # Get recent signals (most recent first)
    # Handle None timestamps by using empty string as fallback
    sorted_by_time = sorted(
        stored_signals,
        key=lambda s: s.get("timestamp") or "",
        reverse=True
    )
    recent_signals = [
        {
            "signal_type": s.get("signal_type"),
            "domain": s.get("domain"),
            "intensity": s.get("intensity"),
            "polarity": s.get("polarity"),
            "source_type": s.get("source_type"),
            "gate": s.get("metadata", {}).get("gate"),
            "timestamp": s.get("timestamp"),
        }
        for s in sorted_by_time[:10]
    ]
    
    # Repeated tags
    tag_counts = Counter(all_tags)
    repeated_tags = [tag for tag, count in tag_counts.most_common(8) if count >= 1]
    
    # Overall momentum
    if len(stored_signals) < 3:
        overall_momentum = "unclear"
    elif total_excitement > total_hesitation * 1.5:
        overall_momentum = "positive"
    elif total_hesitation > total_excitement * 1.5:
        overall_momentum = "resistant"
    else:
        overall_momentum = "mixed"
    
    # Data sufficiency
    total_signals = len(stored_signals)
    if total_signals >= 15:
        data_sufficiency = "high"
    elif total_signals >= 8:
        data_sufficiency = "medium"
    elif total_signals >= 3:
        data_sufficiency = "low"
    else:
        data_sufficiency = "insufficient"
    
    result = {
        "user_id": user_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_signals": total_signals,
        "active_domains": active_domains[:5],  # Top 5 domains
        "strongest_signals": strongest_signals,
        "recent_signals": recent_signals,
        "source_breakdown": dict(source_counts),
        "repeated_tags": repeated_tags,
        "overall_momentum": overall_momentum,
        "data_sufficiency": data_sufficiency,
    }
    
    if include_debug:
        result["debug"] = {
            "total_excitement": round(total_excitement, 3),
            "total_hesitation": round(total_hesitation, 3),
            "raw_signal_count": len(stored_signals),
            "all_domains": list(domain_signals.keys()),
        }
    
    return result


async def ingest_lunar_signals_to_graph(
    db,
    user_id: str,
    decision_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Ingest lunar reflections into the pattern signal store.
    
    v0.15: Enhanced with idempotent storage - re-running will update, not duplicate.
    
    Args:
        db: Database connection
        user_id: User ID
        decision_id: Optional specific decision to ingest
    
    Returns:
        Summary of ingested signals including insert/update counts
    """
    # Build query
    query = {"user_id": user_id}
    if decision_id:
        query["consideration_id"] = decision_id
    
    # Fetch entries
    entries = await db.lunar_journal.find(query).to_list(length=500)
    
    # Get consideration topics
    considerations = await db.lunar_considerations.find({
        "user_id": user_id
    }).to_list(length=50)
    consideration_map = {str(c["_id"]): c.get("topic", "Unknown") for c in considerations}
    
    # Extract and store signals
    total_inserted = 0
    total_updated = 0
    signals_by_type = Counter()
    signals_by_domain = Counter()
    all_signals = []
    
    for entry in entries:
        consideration_id = entry.get("consideration_id", "")
        decision_topic = consideration_map.get(consideration_id, "Decision")
        
        signals = extract_pattern_signals_from_lunar(
            entry, user_id, consideration_id, decision_topic
        )
        all_signals.extend(signals)
        
        for signal in signals:
            signals_by_type[signal.signal_type] += 1
            signals_by_domain[signal.domain] += 1
    
    # Store all signals (idempotent)
    if all_signals:
        inserted, updated = await store_pattern_signals(db, all_signals)
        total_inserted = inserted
        total_updated = updated
    
    logger.info(f"[PatternEngine] Ingested signals for user {user_id[:8]}...: {total_inserted} new, {total_updated} updated")
    
    return {
        "user_id": user_id,
        "entries_processed": len(entries),
        "signals_total": len(all_signals),
        "signals_inserted": total_inserted,
        "signals_updated": total_updated,
        "signals_by_type": dict(signals_by_type),
        "signals_by_domain": dict(signals_by_domain),
        "idempotent": True,
    }
