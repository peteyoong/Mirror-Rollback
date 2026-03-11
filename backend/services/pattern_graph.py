"""Pattern Graph Aggregation Service

Aggregates signals from Gene Keys, journal entries, and other sources
into 7 core pattern categories for reflective insight.

Philosophy:
- Lightweight, deterministic aggregation
- Reflective, not diagnostic
- "Mirror not guru" - suggest patterns, don't prescribe
"""

from typing import List, Dict, Any, TypedDict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# SIGNAL WEIGHTS
# =============================================================================
# Life-derived signals weigh more than framework signals

SIGNAL_WEIGHTS = {
    "journal": 3,           # Highest - direct user reflection
    "mirror_chat": 2,       # High - user-initiated conversation
    "gene_keys": 1,         # Framework-based
    "human_design_centers": 1,  # Framework-based
    "human_design_gates": 1,    # Framework-based
    "human_design": 1,      # Legacy source name (backward compatibility)
    "enneagram": 1,         # Framework-based - invisible contributor
    "astrology_transit": 0.5,   # Timing layer - amplifies existing patterns only
}


# =============================================================================
# ENNEAGRAM TO PATTERN DOMAIN MAPPING
# =============================================================================
# Maps Enneagram types to the seven life domains they most influence

ENNEAGRAM_DOMAIN_MAPPING = {
    "energy_vitality": [7, 8, 9],           # Energetic, powerful, peaceful types
    "emotional_landscape": [2, 4, 6],       # Heart-centered, emotional depth
    "identity_direction": [3, 4, 6],        # Identity-focused types
    "mind_meaning": [5, 6, 7],              # Head triad, mental processing
    "expression_action": [3, 7, 8],         # Achievement, expression, assertive
    "relationships_boundaries": [2, 6, 9],   # Relational focus, harmony-seeking
    "growth_transformation": [1, 4, 7],     # Growth-oriented, idealistic
}


# =============================================================================
# PLANETARY TRANSIT TO PATTERN DOMAIN MAPPING
# =============================================================================
# Maps real planetary transits to the seven life domains they influence
# This is a TIMING layer - used only to amplify existing patterns, not create new ones
#
# Uses Swiss Ephemeris for actual planetary position calculations

# Planet-to-domain mapping: which planets influence which domains
PLANET_DOMAIN_INFLUENCE = {
    # Energy & Vitality - Mars (action/energy), Saturn (fatigue/discipline)
    "energy_vitality": {
        "primary": ["Mars"],
        "secondary": ["Saturn", "Sun"],
        "themes": {
            "Mars": "activation_pressure",
            "Saturn": "discipline_fatigue",
            "Sun": "vitality_focus"
        }
    },
    # Emotional Landscape - Moon (emotions), Neptune (sensitivity), Venus (feeling)
    "emotional_landscape": {
        "primary": ["Moon"],
        "secondary": ["Neptune", "Venus"],
        "themes": {
            "Moon": "emotional_cycles",
            "Neptune": "emotional_permeability",
            "Venus": "heart_opening"
        }
    },
    # Identity & Direction - Saturn (structure), Pluto (transformation), Sun (self)
    "identity_direction": {
        "primary": ["Saturn", "Sun"],
        "secondary": ["Pluto", "North Node"],
        "themes": {
            "Saturn": "structure_testing",
            "Sun": "identity_illumination",
            "Pluto": "deep_restructuring",
            "North Node": "direction_pull"
        }
    },
    # Mind & Meaning - Mercury (thinking), Uranus (insight), Jupiter (meaning)
    "mind_meaning": {
        "primary": ["Mercury"],
        "secondary": ["Uranus", "Jupiter"],
        "themes": {
            "Mercury": "mental_activation",
            "Uranus": "sudden_insight",
            "Jupiter": "expanded_perspective"
        }
    },
    # Expression & Action - Mars (action), Jupiter (expansion), Sun (expression)
    "expression_action": {
        "primary": ["Mars", "Jupiter"],
        "secondary": ["Sun", "Mercury"],
        "themes": {
            "Mars": "action_drive",
            "Jupiter": "expansion_opportunity",
            "Sun": "visibility_moment",
            "Mercury": "voice_activation"
        }
    },
    # Relationships & Boundaries - Venus (connection), Saturn (boundaries), Moon (needs)
    "relationships_boundaries": {
        "primary": ["Venus", "Saturn"],
        "secondary": ["Moon"],
        "themes": {
            "Venus": "connection_focus",
            "Saturn": "boundary_definition",
            "Moon": "relational_needs"
        }
    },
    # Growth & Transformation - Pluto (deep change), Uranus (disruption), Saturn (maturation)
    "growth_transformation": {
        "primary": ["Pluto", "Uranus"],
        "secondary": ["Saturn", "Jupiter"],
        "themes": {
            "Pluto": "deep_transformation",
            "Uranus": "breakthrough_pressure",
            "Saturn": "maturation_demand",
            "Jupiter": "growth_expansion"
        }
    }
}

# Transit intensity thresholds (orb in degrees)
TRANSIT_ORB_TIGHT = 3.0    # Strong influence
TRANSIT_ORB_MEDIUM = 6.0   # Moderate influence
TRANSIT_ORB_WIDE = 10.0    # Background influence

# Aspect types that indicate activation
ACTIVE_ASPECTS = {
    "conjunction": 0,      # Same position - strong activation
    "opposition": 180,     # Tension/awareness
    "square": 90,          # Challenge/action
    "trine": 120,          # Flow/ease
    "sextile": 60          # Opportunity
}


# Import Human Design center mappings
try:
    from .human_design_centers import GATE_TO_CENTER, CENTER_THEMES
except ImportError:
    logger.warning("Could not import Human Design center mappings")
    GATE_TO_CENTER = {}
    CENTER_THEMES = {}


# =============================================================================
# PATTERN TENSION PAIRS
# =============================================================================
# Curated meaningful tension pairs between pattern categories

TENSION_PAIRS = [
    {
        "category_a_id": "energy_vitality",
        "category_b_id": "relationships_boundaries",
        "summary": "A tension may be appearing between energy and connection—between what you can sustain and what others may need from you.",
        "reflection_prompt": "Where are connection and depletion touching each other right now?"
    },
    {
        "category_a_id": "energy_vitality",
        "category_b_id": "expression_action",
        "summary": "Something may be surfacing between your energy levels and your drive to express or act—between capacity and creative output.",
        "reflection_prompt": "What wants to be expressed, and what does your energy allow right now?"
    },
    {
        "category_a_id": "emotional_landscape",
        "category_b_id": "expression_action",
        "summary": "A tension could be emerging between what you're feeling and what you're expressing—between inner weather and outer voice.",
        "reflection_prompt": "Is there something your emotions are asking you to say or do?"
    },
    {
        "category_a_id": "identity_direction",
        "category_b_id": "relationships_boundaries",
        "summary": "You might be noticing friction between your sense of self and your connections—between who you are and who others need you to be.",
        "reflection_prompt": "Where is your identity asking for more space in your relationships?"
    },
    {
        "category_a_id": "mind_meaning",
        "category_b_id": "emotional_landscape",
        "summary": "A tension may be appearing between thinking and feeling—between what makes sense and what moves through you.",
        "reflection_prompt": "What is your mind trying to understand that your emotions already know?"
    },
    {
        "category_a_id": "growth_transformation",
        "category_b_id": "identity_direction",
        "summary": "Something could be surfacing between who you're becoming and who you've been—between growth and the familiar self.",
        "reflection_prompt": "What part of you is ready to change, and what part is asking to stay?"
    }
]


class PatternTension(TypedDict):
    """A detected tension between two active pattern categories."""
    category_a: str
    category_b: str
    combined_score: int
    summary: str
    reflection_prompt: str


# =============================================================================
# THE 7 CORE PATTERN CATEGORIES
# =============================================================================

PATTERN_CATEGORIES = [
    {
        "id": "energy_vitality",
        "name": "Energy & Vitality",
        "description": "Patterns around energy, pacing, exhaustion, and life force",
        "quiet_summary": "No strong signals around energy themes at the moment.",
        "emerging_summary": "A theme around energy, pacing, or vitality may be starting to surface.",
        "active_summary": "Energy and vitality themes seem to be showing up across multiple areas."
    },
    {
        "id": "emotional_landscape",
        "name": "Emotional Landscape",
        "description": "Patterns around feelings, emotional waves, and inner weather",
        "quiet_summary": "No strong signals around emotional patterns at the moment.",
        "emerging_summary": "Something around your emotional experience may be surfacing.",
        "active_summary": "Emotional themes seem to be moving through multiple parts of your reflection."
    },
    {
        "id": "identity_direction",
        "name": "Identity & Direction",
        "description": "Patterns around sense of self, purpose, and life direction",
        "quiet_summary": "No strong signals around identity or direction themes at the moment.",
        "emerging_summary": "A question about identity or direction may be emerging.",
        "active_summary": "Themes of identity and direction seem to be present across your reflections."
    },
    {
        "id": "mind_meaning",
        "name": "Mind & Meaning",
        "description": "Patterns around thinking, understanding, and sense-making",
        "quiet_summary": "No strong signals around mental themes at the moment.",
        "emerging_summary": "Something around thinking, clarity, or meaning may be surfacing.",
        "active_summary": "Mental and meaning-making themes seem to be active in your current pattern."
    },
    {
        "id": "expression_action",
        "name": "Expression & Action",
        "description": "Patterns around voice, communication, and taking action",
        "quiet_summary": "No strong signals around expression themes at the moment.",
        "emerging_summary": "A theme around expression or action may be emerging.",
        "active_summary": "Expression and action themes seem to be showing up across your experience."
    },
    {
        "id": "relationships_boundaries",
        "name": "Relationships & Boundaries",
        "description": "Patterns around connection, intimacy, and personal limits",
        "quiet_summary": "No strong signals around relationship themes at the moment.",
        "emerging_summary": "Something around relationships or boundaries may be surfacing.",
        "active_summary": "Relationship and boundary themes seem to be present in multiple areas."
    },
    {
        "id": "growth_transformation",
        "name": "Growth & Transformation",
        "description": "Patterns around change, evolution, and personal development",
        "quiet_summary": "No strong signals around transformation themes at the moment.",
        "emerging_summary": "A theme around growth or change may be starting to show.",
        "active_summary": "Transformation and growth themes seem to be active across your reflection."
    }
]


# =============================================================================
# GENE KEYS TO CATEGORY MAPPING
# =============================================================================
# Maps Gene Key numbers to primary pattern categories

GENE_KEY_CATEGORY_MAP = {
    # Energy & Vitality
    5: "energy_vitality",      # Fixed Rhythms
    9: "energy_vitality",      # Focus / Determination
    14: "energy_vitality",     # Power Skills
    27: "energy_vitality",     # Caring / Nourishment
    29: "energy_vitality",     # Saying Yes / Commitment
    34: "energy_vitality",     # Power / Life Force
    40: "energy_vitality",     # Aloneness / Exhaustion
    42: "energy_vitality",     # Completion / Growth
    52: "energy_vitality",     # Stillness
    53: "energy_vitality",     # Starting / New Cycles
    58: "energy_vitality",     # Joy / Vitality
    
    # Emotional Landscape
    6: "emotional_landscape",   # Conflict Resolution / Intimacy
    22: "emotional_landscape",  # Grace / Emotional Charm
    30: "emotional_landscape",  # Feelings / Desire
    36: "emotional_landscape",  # Crisis / Emotional Learning
    37: "emotional_landscape",  # Community / Family (also relationships)
    49: "emotional_landscape",  # Revolution / Principles
    55: "emotional_landscape",  # Spirit / Emotional Range
    
    # Identity & Direction
    1: "identity_direction",    # Self-Expression
    2: "identity_direction",    # Direction
    7: "identity_direction",    # Self-Direction / Leadership
    10: "identity_direction",   # Self-Love / Behavior
    15: "identity_direction",   # Extremes / Humanity
    25: "identity_direction",   # Innocence / Universal Love
    46: "identity_direction",   # Body / Determination
    
    # Mind & Meaning
    4: "mind_meaning",          # Mental Solutions
    11: "mind_meaning",         # Ideas
    17: "mind_meaning",         # Opinions
    24: "mind_meaning",         # Rationalizing
    43: "mind_meaning",         # Insight
    47: "mind_meaning",         # Realization
    61: "mind_meaning",         # Mystery / Inner Truth
    62: "mind_meaning",         # Details / Precision
    63: "mind_meaning",         # Doubt / Questioning
    64: "mind_meaning",         # Confusion / Before Completion
    
    # Expression & Action
    8: "expression_action",     # Contribution
    12: "expression_action",    # Caution / Articulation
    16: "expression_action",    # Skills / Enthusiasm
    20: "expression_action",    # Now / Presence
    23: "expression_action",    # Assimilation / Insight Translation
    31: "expression_action",    # Influence / Leadership
    33: "expression_action",    # Privacy / Retreat
    35: "expression_action",    # Change / Adventure
    45: "expression_action",    # The King/Queen / Gathering
    56: "expression_action",    # Stimulation / Storytelling
    
    # Relationships & Boundaries
    13: "relationships_boundaries",  # Listener / Secrets
    19: "relationships_boundaries",  # Wanting / Sensitivity
    32: "relationships_boundaries",  # Continuity / Duration
    38: "relationships_boundaries",  # The Fighter
    39: "relationships_boundaries",  # Provocation
    41: "relationships_boundaries",  # Fantasy / Anticipation
    44: "relationships_boundaries",  # Alertness / Patterns
    50: "relationships_boundaries",  # Values / Responsibility
    54: "relationships_boundaries",  # Ambition
    59: "relationships_boundaries",  # Intimacy / Breaking Barriers
    
    # Growth & Transformation
    3: "growth_transformation",   # Ordering / Mutation
    18: "growth_transformation",  # Correction / Improvement
    21: "growth_transformation",  # Hunter / Control
    26: "growth_transformation",  # Taming / Influence
    28: "growth_transformation",  # Struggle / Purpose
    48: "growth_transformation",  # Depth / Skill
    51: "growth_transformation",  # Shock / Initiative
    57: "growth_transformation",  # Intuition
    60: "growth_transformation",  # Acceptance / Limitation
}


# =============================================================================
# SHADOW/GIFT KEYWORD TO CATEGORY MAPPING
# =============================================================================
# Additional keyword-based detection for journal/chat signals

KEYWORD_CATEGORY_MAP = {
    "energy_vitality": [
        "tired", "exhausted", "depleted", "energy", "vitality", "rest", "pacing",
        "burnout", "refresh", "recharge", "fatigue", "drained", "power", "strength",
        "weak", "powerful", "alive", "rhythm", "cycles", "sustainable", "endurance"
    ],
    "emotional_landscape": [
        "feel", "feeling", "emotions", "emotional", "mood", "anxious", "anxiety",
        "sad", "happy", "joy", "grief", "anger", "fear", "wave", "overwhelm",
        "calm", "peace", "turbulent", "sensitive", "heart", "hurt", "love"
    ],
    "identity_direction": [
        "who am i", "purpose", "direction", "lost", "identity", "self", "authentic",
        "meaning", "calling", "path", "journey", "belong", "belonging", "role",
        "confused about who", "discovering", "becoming", "true self"
    ],
    "mind_meaning": [
        "think", "thinking", "thought", "understand", "clarity", "confused",
        "insight", "realize", "idea", "concept", "meaning", "sense", "logic",
        "rational", "doubt", "certainty", "question", "answer", "wisdom"
    ],
    "expression_action": [
        "speak", "voice", "express", "action", "do", "doing", "create", "creative",
        "communicate", "say", "said", "tell", "share", "silent", "quiet",
        "stuck", "move", "moving", "manifest", "build", "start"
    ],
    "relationships_boundaries": [
        "relationship", "boundary", "boundaries", "people", "connection", "connect",
        "intimacy", "trust", "family", "friend", "partner", "alone", "lonely",
        "together", "distance", "close", "conflict", "harmony", "support"
    ],
    "growth_transformation": [
        "change", "changing", "grow", "growth", "transform", "evolve", "evolution",
        "learn", "learning", "develop", "progress", "stuck", "breakthrough",
        "challenge", "struggle", "overcome", "heal", "healing", "new"
    ]
}


# =============================================================================
# HUMAN DESIGN CENTER TO CATEGORY MAPPING
# =============================================================================

HD_CENTER_CATEGORY_MAP = {
    "Head": "mind_meaning",
    "Ajna": "mind_meaning",
    "Throat": "expression_action",
    "G Center": "identity_direction",
    "Solar Plexus": "emotional_landscape",
    "Sacral": "energy_vitality",
    "Root": "energy_vitality",
    "Ego": "expression_action",
    "Spleen": "energy_vitality",
}

# Human-readable center names for display
HD_CENTER_DISPLAY_NAMES = {
    "Head": "Head Center",
    "Ajna": "Ajna (Mind) Center",
    "Throat": "Throat Center",
    "G Center": "G / Identity Center",
    "Solar Plexus": "Solar Plexus Center",
    "Sacral": "Sacral Center",
    "Root": "Root Center",
    "Ego": "Heart / Ego Center",
    "Spleen": "Spleen Center",
}


# =============================================================================
# HUMAN DESIGN GATE TO CATEGORY MAPPING
# =============================================================================
# Maps gates to categories (reuses Gene Key mapping since gates = keys)

HD_GATE_CATEGORY_MAP = GENE_KEY_CATEGORY_MAP.copy()


class MatchedSignal(TypedDict):
    """A single matched signal from a source."""
    source: str  # "gene_keys", "journal", "chat"
    label: str   # Human-readable label
    sphere_name: Optional[str]  # Gene Keys sphere if applicable
    detail: Optional[str]  # Additional context


class CategoryResult(TypedDict):
    """Result for a single pattern category."""
    category_id: str
    category_name: str
    signal_strength: str  # "quiet", "present", "recurring"
    pattern_score: int    # Weighted score
    signal_count: int     # Number of unique signals
    trend: str            # "rising", "steady", "fading"
    matched_sources: List[str]
    matched_signals: List[MatchedSignal]
    summary: str


def get_category_by_id(category_id: str) -> Optional[dict]:
    """Get category metadata by ID."""
    for cat in PATTERN_CATEGORIES:
        if cat["id"] == category_id:
            return cat
    return None


def aggregate_gene_keys_signals(
    gene_keys_profile: dict
) -> Dict[str, List[MatchedSignal]]:
    """Extract pattern signals from Gene Keys profile.
    
    Args:
        gene_keys_profile: Result from build_gene_keys_profile()
    
    Returns:
        Dict mapping category_id to list of matched signals
    """
    category_signals: Dict[str, List[MatchedSignal]] = {
        cat["id"]: [] for cat in PATTERN_CATEGORIES
    }
    
    all_spheres = gene_keys_profile.get("all_spheres", [])
    
    for sphere in all_spheres:
        gene_key = sphere.get("gene_key", 0)
        sphere_name = sphere.get("sphere_name", "Unknown")
        shadow = sphere.get("shadow", "")
        gift = sphere.get("gift", "")
        sequence = sphere.get("sequence", "")
        
        # Map gene key to category
        category_id = GENE_KEY_CATEGORY_MAP.get(gene_key)
        if category_id:
            signal: MatchedSignal = {
                "source": "gene_keys",
                "label": f"{shadow} → {gift}",
                "sphere_name": f"{sphere_name} ({sequence})",
                "detail": f"Gene Key {gene_key}"
            }
            category_signals[category_id].append(signal)
        
        # Also check shadow/gift keywords for additional category signals
        shadow_keywords = sphere.get("shadow_keywords", [])
        gift_keywords = sphere.get("gift_keywords", [])
        all_keywords = shadow_keywords + gift_keywords
        
        for kw in all_keywords:
            kw_lower = kw.lower()
            for cat_id, cat_keywords in KEYWORD_CATEGORY_MAP.items():
                if cat_id != category_id:  # Don't double-count
                    for cat_kw in cat_keywords:
                        if cat_kw in kw_lower or kw_lower in cat_kw:
                            # Found a cross-category keyword match
                            signal: MatchedSignal = {
                                "source": "gene_keys",
                                "label": f"{shadow} ({kw})",
                                "sphere_name": sphere_name,
                                "detail": f"Keyword resonance from Gene Key {gene_key}"
                            }
                            # Only add if not already present
                            existing_labels = [s["label"] for s in category_signals[cat_id]]
                            if signal["label"] not in existing_labels:
                                category_signals[cat_id].append(signal)
                            break
    
    return category_signals


def aggregate_journal_signals(
    journal_entries: List[dict],
    max_entries: int = 10
) -> Dict[str, List[MatchedSignal]]:
    """Extract pattern signals from recent journal entries.
    
    Args:
        journal_entries: List of recent journal entries
        max_entries: Maximum entries to analyze
    
    Returns:
        Dict mapping category_id to list of matched signals
    """
    category_signals: Dict[str, List[MatchedSignal]] = {
        cat["id"]: [] for cat in PATTERN_CATEGORIES
    }
    
    # Analyze recent entries
    for entry in journal_entries[:max_entries]:
        content = entry.get("content", "").lower()
        timestamp = entry.get("timestamp")
        
        if len(content) < 20:
            continue  # Skip very short entries
        
        # Check for keyword matches
        for cat_id, keywords in KEYWORD_CATEGORY_MAP.items():
            matches_found = []
            for kw in keywords:
                if kw in content:
                    matches_found.append(kw)
            
            if matches_found:
                # Create a signal for this category
                date_str = ""
                if timestamp:
                    if hasattr(timestamp, 'strftime'):
                        date_str = timestamp.strftime("%b %d")
                    else:
                        date_str = str(timestamp)[:10]
                
                signal: MatchedSignal = {
                    "source": "journal",
                    "label": f"Journal reflection ({', '.join(matches_found[:2])})",
                    "sphere_name": None,
                    "detail": f"From entry on {date_str}" if date_str else "Recent entry"
                }
                category_signals[cat_id].append(signal)
    
    return category_signals


def aggregate_human_design_center_signals(
    centers_profile: Optional[List[dict]] = None,
    active_gates: Optional[List[int]] = None
) -> Dict[str, List[MatchedSignal]]:
    """Extract pattern signals from Human Design centers and gates.
    
    Args:
        centers_profile: List of center interpretations from build_centers_profile()
        active_gates: List of active gate numbers
    
    Returns:
        Dict mapping category_id to list of matched signals
    """
    category_signals: Dict[str, List[MatchedSignal]] = {
        cat["id"]: [] for cat in PATTERN_CATEGORIES
    }
    
    if not centers_profile and not active_gates:
        return category_signals
    
    # Map center themes to pattern categories
    center_to_category = {
        "Head": "mind_meaning",           # Mental pressure, questions
        "Ajna": "mind_meaning",           # Thinking patterns, opinions
        "Throat": "expression_action",    # Communication, manifestation
        "G Center": "identity_direction", # Identity, direction, self
        "Ego": "energy_vitality",         # Willpower, commitment, resources
        "Solar Plexus": "emotional_landscape", # Emotions, feelings
        "Sacral": "energy_vitality",      # Life force, work energy
        "Spleen": "growth_transformation", # Instinct, survival, health
        "Root": "energy_vitality"         # Pressure, drive, adrenaline
    }
    
    # Process centers if available
    if centers_profile:
        for center in centers_profile:
            center_name = center.get("center_name", "")
            defined = center.get("defined", False)
            gates_present = center.get("gates_present", [])
            
            # Map center to category
            category_id = center_to_category.get(center_name)
            if category_id and gates_present:
                # Create signal for defined centers with active gates
                state = "defined" if defined else "open"
                signal: MatchedSignal = {
                    "source": "human_design",
                    "label": f"{center.get('display_name', center_name)} ({state})",
                    "sphere_name": None,
                    "detail": f"Gates: {', '.join(map(str, gates_present))}"
                }
                category_signals[category_id].append(signal)
    
    # Process individual gates if available
    if active_gates and GATE_TO_CENTER:
        # Group gates by center
        center_gates = {}
        for gate in active_gates:
            center = GATE_TO_CENTER.get(gate)
            if center:
                if center not in center_gates:
                    center_gates[center] = []
                center_gates[center].append(gate)
        
        # Create signals for centers with multiple gates (indicates emphasis)
        for center, gates in center_gates.items():
            if len(gates) >= 2:  # Only signal if multiple gates in same center
                category_id = center_to_category.get(center)
                if category_id:
                    signal: MatchedSignal = {
                        "source": "human_design",
                        "label": f"{center} emphasis",
                        "sphere_name": None,
                        "detail": f"Multiple gates: {', '.join(map(str, gates))}"
                    }
                    # Only add if not already present
                    existing_labels = [s["label"] for s in category_signals[category_id]]
                    if signal["label"] not in existing_labels:
                        category_signals[category_id].append(signal)
    
    return category_signals


def calculate_weighted_score(signals: List[MatchedSignal]) -> int:
    """Calculate weighted score based on signal sources.
    
    Weights:
    - journal: 3 (highest - direct user reflection)
    - mirror_chat: 2 (user-initiated conversation)
    - gene_keys: 1 (framework-based)
    - human_design_*: 1 (framework-based)
    
    Returns:
        Total weighted score
    """
    if not signals:
        return 0
    
    total_score = 0
    for signal in signals:
        source = signal.get("source", "")
        weight = SIGNAL_WEIGHTS.get(source, 1)
        total_score += weight
    
    return total_score


def calculate_signal_strength_from_score(score: int) -> str:
    """Calculate signal strength from weighted score.
    
    Thresholds:
    - 0-2: Quiet
    - 3-6: Present
    - 7+:  Recurring
    
    Returns:
        "quiet", "present", or "recurring"
    """
    if score <= 2:
        return "quiet"
    elif score <= 6:
        return "present"
    else:
        return "recurring"


def calculate_signal_strength(signals: List[MatchedSignal]) -> str:
    """Calculate signal strength based on weighted scoring.
    
    This is the main function used by aggregate_pattern_graph.
    
    Returns:
        "quiet", "present", or "recurring"
    """
    score = calculate_weighted_score(signals)
    return calculate_signal_strength_from_score(score)


def get_category_summary(category: dict, strength: str) -> str:
    """Get the appropriate summary text for a category and strength level."""
    if strength == "quiet":
        return category.get("quiet_summary", "No strong signals at the moment.")
    elif strength == "present":
        return category.get("emerging_summary", "A theme may be starting to surface.")
    else:  # recurring
        return category.get("active_summary", "This theme seems to be present across your reflection.")


def aggregate_enneagram_signals(
    enneagram_type: Optional[int] = None,
    enneagram_wing: Optional[int] = None
) -> Dict[str, List[MatchedSignal]]:
    """Aggregate Enneagram signals into pattern categories.
    
    Maps Enneagram type to the relevant life domains it influences.
    This is an invisible contributor - it affects scoring but doesn't
    expose separate Enneagram UI.
    
    Args:
        enneagram_type: User's core Enneagram type (1-9)
        enneagram_wing: User's Enneagram wing (optional)
    
    Returns:
        Dict mapping category_id to list of Enneagram-derived signals
    """
    category_signals: Dict[str, List[MatchedSignal]] = {
        cat["id"]: [] for cat in PATTERN_CATEGORIES
    }
    
    if not enneagram_type or enneagram_type < 1 or enneagram_type > 9:
        return category_signals
    
    # Map the core type to relevant domains
    for category_id, types in ENNEAGRAM_DOMAIN_MAPPING.items():
        if enneagram_type in types:
            # Create a subtle signal that contributes to scoring
            # without exposing Enneagram specifics
            signal: MatchedSignal = {
                "source": "enneagram",
                "label": f"Personality pattern resonance",
                "sphere_name": None,
                "detail": f"Core type influence on this domain"
            }
            category_signals[category_id].append(signal)
    
    # If wing is provided and different from core type, add secondary influence
    if enneagram_wing and enneagram_wing != enneagram_type and 1 <= enneagram_wing <= 9:
        for category_id, types in ENNEAGRAM_DOMAIN_MAPPING.items():
            if enneagram_wing in types:
                # Check if we already added this category from core type
                existing_labels = [s["label"] for s in category_signals[category_id]]
                if "Personality pattern resonance" not in existing_labels:
                    signal: MatchedSignal = {
                        "source": "enneagram",
                        "label": f"Personality pattern resonance (secondary)",
                        "sphere_name": None,
                        "detail": f"Wing influence on this domain"
                    }
                    category_signals[category_id].append(signal)
    
    return category_signals


# =============================================================================
# TRANSIT INFLUENCE FUNCTIONS - Real Swiss Ephemeris Implementation
# =============================================================================

def calculate_current_planetary_positions() -> Dict[str, Dict]:
    """Calculate current positions of all planets using Swiss Ephemeris.
    
    Returns:
        Dict mapping planet names to their position data including:
        - longitude: sidereal longitude
        - sign: zodiac sign
        - degree: degree within sign
        - retrograde: whether planet is retrograde
    """
    try:
        from datetime import datetime, timezone
        from calculations.astrology import (
            PLANETS, get_julian_day, calculate_planet_position_sidereal
        )
        
        # Get current UTC time
        now = datetime.now(timezone.utc)
        jd = get_julian_day(
            now.year, now.month, now.day,
            now.hour, now.minute, now.second
        )
        
        positions = {}
        for planet_name, planet_id in PLANETS.items():
            if planet_name == "South Node":
                continue  # Skip, we use North Node
            try:
                pos = calculate_planet_position_sidereal(planet_id, jd)
                positions[planet_name] = {
                    "longitude": pos["longitude"],
                    "sign": pos["sign"],
                    "degree": pos["degree"],
                    "retrograde": pos.get("retrograde", False),
                    "speed": pos.get("speed", 0)
                }
            except Exception as e:
                logger.debug(f"[Transit] Could not calculate {planet_name}: {e}")
                continue
        
        return positions
    except Exception as e:
        logger.warning(f"[Transit] Swiss Ephemeris calculation failed: {e}")
        return {}


def calculate_transit_aspects_to_natal(
    transit_positions: Dict[str, Dict],
    natal_chart: Optional[Dict] = None
) -> List[Dict]:
    """Calculate aspects between current transits and natal chart.
    
    If natal chart is not provided, returns general transit activations
    based on current planetary configurations.
    
    Args:
        transit_positions: Current planetary positions from calculate_current_planetary_positions()
        natal_chart: Optional user's natal chart data
    
    Returns:
        List of active transit aspects with:
        - transiting_planet: name of transiting planet
        - aspect_type: conjunction, opposition, square, etc.
        - intensity: tight, medium, wide based on orb
        - domain_influence: list of affected domains
    """
    active_transits = []
    
    if not transit_positions:
        return active_transits
    
    # If we have a natal chart, calculate transits to natal positions
    if natal_chart and natal_chart.get("planets"):
        natal_planets = natal_chart.get("planets", {})
        
        for transit_name, transit_pos in transit_positions.items():
            if transit_name in ["Sun", "Moon", "Mercury", "Venus"]:
                # Fast-moving planets: only tight aspects
                max_orb = TRANSIT_ORB_TIGHT
            elif transit_name in ["Mars", "Jupiter"]:
                # Medium planets: medium orbs
                max_orb = TRANSIT_ORB_MEDIUM
            else:
                # Outer planets: wider orbs (longer influence)
                max_orb = TRANSIT_ORB_WIDE
            
            transit_lon = transit_pos.get("longitude", 0)
            
            # Check aspects to key natal points (Sun, Moon, Ascendant)
            for natal_name in ["Sun", "Moon", "Mercury", "Venus", "Mars", "Saturn"]:
                if natal_name not in natal_planets:
                    continue
                    
                natal_lon = natal_planets[natal_name].get("longitude", 0)
                if natal_lon is None:
                    continue
                
                # Calculate aspect
                diff = abs(transit_lon - natal_lon)
                if diff > 180:
                    diff = 360 - diff
                
                # Check each aspect type
                for aspect_name, aspect_angle in ACTIVE_ASPECTS.items():
                    orb = abs(diff - aspect_angle)
                    if orb <= max_orb:
                        intensity = "tight" if orb <= TRANSIT_ORB_TIGHT else "medium" if orb <= TRANSIT_ORB_MEDIUM else "wide"
                        
                        active_transits.append({
                            "transiting_planet": transit_name,
                            "natal_point": natal_name,
                            "aspect_type": aspect_name,
                            "orb": orb,
                            "intensity": intensity,
                            "retrograde": transit_pos.get("retrograde", False)
                        })
    else:
        # No natal chart - use general transit weather
        # Focus on outer planet positions and lunar phase
        for planet_name, pos in transit_positions.items():
            if planet_name in ["Saturn", "Jupiter", "Mars", "Pluto", "Uranus", "Neptune"]:
                active_transits.append({
                    "transiting_planet": planet_name,
                    "natal_point": None,
                    "aspect_type": "general_influence",
                    "orb": 0,
                    "intensity": "medium",
                    "retrograde": pos.get("retrograde", False)
                })
        
        # Add Moon position for emotional timing
        if "Moon" in transit_positions:
            moon_sign = transit_positions["Moon"].get("sign", "")
            active_transits.append({
                "transiting_planet": "Moon",
                "natal_point": None,
                "aspect_type": "lunar_cycle",
                "orb": 0,
                "intensity": "tight",
                "sign": moon_sign
            })
    
    return active_transits


def map_transits_to_domains(
    active_transits: List[Dict]
) -> Dict[str, Dict]:
    """Map active transits to pattern domains with intensity scores.
    
    Args:
        active_transits: List of transit aspects from calculate_transit_aspects_to_natal()
    
    Returns:
        Dict mapping domain_id to:
        - intensity: float score (0-1)
        - planets: list of influencing planets
        - theme: primary theme label
    """
    domain_influence: Dict[str, Dict] = {}
    
    for domain_id, domain_config in PLANET_DOMAIN_INFLUENCE.items():
        primary_planets = domain_config.get("primary", [])
        secondary_planets = domain_config.get("secondary", [])
        themes = domain_config.get("themes", {})
        
        domain_intensity = 0.0
        active_planets = []
        active_theme = None
        
        for transit in active_transits:
            planet = transit.get("transiting_planet")
            intensity_str = transit.get("intensity", "medium")
            
            # Calculate intensity multiplier
            if intensity_str == "tight":
                intensity_mult = 1.0
            elif intensity_str == "medium":
                intensity_mult = 0.6
            else:
                intensity_mult = 0.3
            
            # Check if this planet influences this domain
            if planet in primary_planets:
                domain_intensity += 0.5 * intensity_mult
                active_planets.append(planet)
                if not active_theme and planet in themes:
                    active_theme = themes[planet]
            elif planet in secondary_planets:
                domain_intensity += 0.25 * intensity_mult
                active_planets.append(planet)
                if not active_theme and planet in themes:
                    active_theme = themes[planet]
        
        if domain_intensity > 0:
            domain_influence[domain_id] = {
                "intensity": min(domain_intensity, 1.0),  # Cap at 1.0
                "planets": list(set(active_planets)),  # Deduplicate
                "theme": active_theme or "timing_emphasis"
            }
    
    return domain_influence


def get_transit_influenced_domains(
    natal_chart: Optional[Dict] = None
) -> Dict[str, Dict]:
    """Main function to get transit influence on pattern domains.
    
    Uses real Swiss Ephemeris calculations when available,
    falls back to simplified heuristics if needed.
    
    Args:
        natal_chart: Optional user's natal chart for personalized transits
    
    Returns:
        Dict mapping domain_id to influence data (intensity, theme, planets)
    """
    try:
        # Calculate current planetary positions
        transit_positions = calculate_current_planetary_positions()
        
        if not transit_positions:
            logger.debug("[Transit] No planetary positions - falling back to basic timing")
            return _get_fallback_transit_influence()
        
        # Calculate aspects to natal chart (or general influence)
        active_transits = calculate_transit_aspects_to_natal(
            transit_positions=transit_positions,
            natal_chart=natal_chart
        )
        
        if not active_transits:
            logger.debug("[Transit] No active transits found")
            return _get_fallback_transit_influence()
        
        # Map transits to domains
        domain_influence = map_transits_to_domains(active_transits)
        
        logger.debug(f"[Transit] Real transit calculation: {len(domain_influence)} domains influenced")
        for domain_id, influence in domain_influence.items():
            logger.debug(f"  {domain_id}: intensity={influence['intensity']:.2f}, planets={influence['planets']}")
        
        return domain_influence
        
    except Exception as e:
        logger.warning(f"[Transit] Error calculating transits: {e}")
        return _get_fallback_transit_influence()


def _get_fallback_transit_influence() -> Dict[str, Dict]:
    """Fallback transit influence when Swiss Ephemeris is unavailable.
    
    Uses day-of-week and lunar cycle as basic timing indicators.
    """
    from datetime import datetime
    
    today = datetime.now()
    day_of_week = today.weekday()
    day_of_month = today.day
    
    # Day-of-week planetary rulerships
    day_planets = {
        0: "Moon",      # Monday
        1: "Mars",      # Tuesday
        2: "Mercury",   # Wednesday
        3: "Jupiter",   # Thursday
        4: "Venus",     # Friday
        5: "Saturn",    # Saturday
        6: "Sun"        # Sunday
    }
    ruling_planet = day_planets.get(day_of_week, "Sun")
    
    # Build basic influence from ruling planet
    domain_influence = {}
    for domain_id, domain_config in PLANET_DOMAIN_INFLUENCE.items():
        primary = domain_config.get("primary", [])
        secondary = domain_config.get("secondary", [])
        themes = domain_config.get("themes", {})
        
        if ruling_planet in primary:
            domain_influence[domain_id] = {
                "intensity": 0.5,
                "planets": [ruling_planet],
                "theme": themes.get(ruling_planet, "timing_emphasis")
            }
        elif ruling_planet in secondary:
            domain_influence[domain_id] = {
                "intensity": 0.25,
                "planets": [ruling_planet],
                "theme": themes.get(ruling_planet, "timing_emphasis")
            }
    
    # Add lunar influence to emotional landscape
    lunar_phase = (day_of_month % 28) / 28.0
    if 0.4 < lunar_phase < 0.6:  # Near full moon
        if "emotional_landscape" not in domain_influence:
            domain_influence["emotional_landscape"] = {
                "intensity": 0.4,
                "planets": ["Moon"],
                "theme": "emotional_cycles"
            }
        else:
            domain_influence["emotional_landscape"]["intensity"] += 0.2
    
    return domain_influence


def aggregate_transit_signals(
    natal_chart: Optional[Dict] = None,
    existing_domain_scores: Optional[Dict[str, float]] = None
) -> Dict[str, List[MatchedSignal]]:
    """Aggregate transit signals into pattern categories.
    
    IMPORTANT: Transits are an AMPLIFICATION layer only.
    They should boost existing patterns, not create new ones.
    
    Args:
        transit_themes: List of active transit theme keys
        existing_domain_scores: Dict of domain_id -> score (to check for existing support)
    
    Returns:
        Dict mapping category_id to list of transit-derived signals
    """
    category_signals: Dict[str, List[MatchedSignal]] = {
        cat["id"]: [] for cat in PATTERN_CATEGORIES
    }
    
    if not transit_themes:
        transit_themes = get_current_transit_themes()
    
    # Track which domains receive transit emphasis
    domain_emphasis: Dict[str, int] = {}
    theme_labels: Dict[str, str] = {}  # Store theme descriptions per domain
    
    for theme in transit_themes:
        if theme in TRANSIT_THEME_DOMAINS:
            domains = TRANSIT_THEME_DOMAINS[theme]
            for domain_id in domains:
                domain_emphasis[domain_id] = domain_emphasis.get(domain_id, 0) + 1
                # Store the first theme as the label
                if domain_id not in theme_labels:
                    # Convert theme_key to readable label
                    readable = theme.replace("_", " ").title()
                    theme_labels[domain_id] = readable
    
    # Only add transit signals to domains that have emphasis
    for domain_id, emphasis_count in domain_emphasis.items():
        # Skip if this domain has no existing support (amplification only)
        if existing_domain_scores:
            existing_score = existing_domain_scores.get(domain_id, 0)
            if existing_score < 0.5:  # Minimum threshold for amplification
                logger.debug(f"[Transit] Skipping {domain_id} - insufficient existing support ({existing_score})")
                continue
        
        # Create subtle transit signal
        signal: MatchedSignal = {
            "source": "astrology_transit",
            "label": "Current transit emphasis",
            "sphere_name": None,
            "detail": theme_labels.get(domain_id, "Timing resonance")
        }
        category_signals[domain_id].append(signal)
    
    return category_signals


def calculate_transit_amplification(
    base_score: float,
    has_transit_emphasis: bool,
    transit_weight: float = 0.5
) -> float:
    """Calculate amplified score for domains with transit emphasis.
    
    Transit amplification only applies when:
    1. The domain already has some support (base_score > 0)
    2. There is transit emphasis for this domain
    
    Args:
        base_score: The domain's score from lived/framework data
        has_transit_emphasis: Whether transits emphasize this domain
        transit_weight: How much to amplify (default 0.5)
    
    Returns:
        Amplified score
    """
    if not has_transit_emphasis or base_score <= 0:
        return base_score
    
    # Amplification is proportional to existing strength
    # Strong patterns get amplified more than weak ones
    amplification = transit_weight * (base_score / 10.0)  # Normalize
    return base_score + amplification


def aggregate_pattern_graph(
    gene_keys_profile: Optional[dict] = None,
    journal_entries: Optional[List[dict]] = None,
    human_design_centers: Optional[List[dict]] = None,
    human_design_gates: Optional[List[int]] = None,
    chat_signals: Optional[List[dict]] = None,  # Future: from Mirror Chat
    enneagram_type: Optional[int] = None,       # Enneagram core type (1-9)
    enneagram_wing: Optional[int] = None,       # Enneagram wing (optional)
    include_transits: bool = True               # Whether to include transit amplification
) -> Dict[str, Any]:
    """Main aggregation function for Pattern Graph.
    
    Combines signals from all available sources into the 7 pattern categories.
    
    Args:
        gene_keys_profile: Result from build_gene_keys_profile()
        journal_entries: List of recent journal entries
        human_design_centers: List of center interpretations from build_centers_profile()
        human_design_gates: List of active gate numbers
        chat_signals: Future - signals from Mirror Chat analysis
        enneagram_type: User's Enneagram type (invisible contributor)
        enneagram_wing: User's Enneagram wing (optional)
    
    Returns:
        Complete pattern graph response
    """
    # Initialize category results
    all_signals: Dict[str, List[MatchedSignal]] = {
        cat["id"]: [] for cat in PATTERN_CATEGORIES
    }
    
    # Aggregate Gene Keys signals
    if gene_keys_profile:
        gk_signals = aggregate_gene_keys_signals(gene_keys_profile)
        for cat_id, signals in gk_signals.items():
            all_signals[cat_id].extend(signals)
    
    # Aggregate journal signals
    if journal_entries:
        journal_sigs = aggregate_journal_signals(journal_entries)
        for cat_id, signals in journal_sigs.items():
            all_signals[cat_id].extend(signals)
    
    # Aggregate Human Design center signals
    if human_design_centers or human_design_gates:
        hd_signals = aggregate_human_design_center_signals(
            centers_profile=human_design_centers,
            active_gates=human_design_gates
        )
        for cat_id, signals in hd_signals.items():
            all_signals[cat_id].extend(signals)
    
    # Aggregate Enneagram signals (invisible contributor)
    if enneagram_type:
        ennea_signals = aggregate_enneagram_signals(
            enneagram_type=enneagram_type,
            enneagram_wing=enneagram_wing
        )
        for cat_id, signals in ennea_signals.items():
            all_signals[cat_id].extend(signals)
    
    # First pass: Calculate preliminary scores (before transit amplification)
    # This is needed to determine which domains have existing support
    preliminary_scores: Dict[str, float] = {}
    for cat in PATTERN_CATEGORIES:
        cat_id = cat["id"]
        signals = all_signals.get(cat_id, [])
        # Quick score calculation for transit amplification check
        seen_labels = set()
        unique_sigs = []
        for sig in signals:
            if sig["label"] not in seen_labels:
                seen_labels.add(sig["label"])
                unique_sigs.append(sig)
        preliminary_scores[cat_id] = calculate_weighted_score(unique_sigs[:5])
    
    # Get current transit themes and add transit signals (amplification only)
    transit_themes = []
    transit_emphasized_domains = set()
    if include_transits:
        transit_themes = get_current_transit_themes()
        logger.debug(f"[PatternGraph] Active transit themes: {transit_themes}")
        
        # Aggregate transit signals (only for domains with existing support)
        transit_signals = aggregate_transit_signals(
            transit_themes=transit_themes,
            existing_domain_scores=preliminary_scores
        )
        for cat_id, signals in transit_signals.items():
            if signals:  # Only if transit added signals to this domain
                all_signals[cat_id].extend(signals)
                transit_emphasized_domains.add(cat_id)
        
        logger.debug(f"[PatternGraph] Transit-emphasized domains: {transit_emphasized_domains}")
    
    # Calculate trends for all categories
    trends = calculate_pattern_trends(
        gene_keys_profile=gene_keys_profile,
        journal_entries=journal_entries,
        human_design_centers=human_design_centers,
        human_design_gates=human_design_gates
    )
    
    # Build category results
    categories: List[CategoryResult] = []
    
    for cat in PATTERN_CATEGORIES:
        cat_id = cat["id"]
        signals = all_signals.get(cat_id, [])
        
        # Deduplicate signals by label
        seen_labels = set()
        unique_signals = []
        transit_signal = None
        for sig in signals:
            if sig["label"] not in seen_labels:
                seen_labels.add(sig["label"])
                # Keep transit signal separate for later inclusion
                if sig["source"] == "astrology_transit":
                    transit_signal = sig
                else:
                    unique_signals.append(sig)
        
        # Limit non-transit signals per category (leave room for transit if present)
        max_non_transit = 5 if transit_signal is None else 4
        unique_signals = unique_signals[:max_non_transit]
        
        # Add transit signal at the end if present
        if transit_signal:
            unique_signals.append(transit_signal)
        
        # Calculate strength using weighted scoring
        pattern_score = calculate_weighted_score(unique_signals)
        
        # Apply transit amplification if this domain has transit emphasis
        has_transit = cat_id in transit_emphasized_domains
        if has_transit and pattern_score > 0:
            pattern_score = calculate_transit_amplification(
                base_score=pattern_score,
                has_transit_emphasis=True,
                transit_weight=SIGNAL_WEIGHTS.get("astrology_transit", 0.5)
            )
        
        strength = calculate_signal_strength_from_score(pattern_score)
        
        # Get matched sources
        sources = list(set(s["source"] for s in unique_signals))
        
        # Get summary
        summary = get_category_summary(cat, strength)
        
        # Add transit emphasis flag for sorting/highlighting top patterns
        result: CategoryResult = {
            "category_id": cat_id,
            "category_name": cat["name"],
            "signal_strength": strength,
            "pattern_score": pattern_score,
            "signal_count": len(unique_signals),
            "trend": trends.get(cat_id, "steady"),
            "matched_sources": sources,
            "matched_signals": unique_signals,
            "summary": summary,
            "has_transit_emphasis": has_transit  # For frontend highlighting
        }
        categories.append(result)
    
    # Sort categories by pattern_score to prioritize top patterns
    # Transit-amplified patterns with existing support will naturally rise to top
    categories.sort(key=lambda c: c["pattern_score"], reverse=True)
    
    # Calculate overall stats (using new terminology)
    recurring_count = sum(1 for c in categories if c["signal_strength"] == "recurring")
    present_count = sum(1 for c in categories if c["signal_strength"] == "present")
    
    return {
        "categories": categories,
        "summary": {
            "active_categories": recurring_count,      # Renamed internally to recurring
            "emerging_categories": present_count,      # Renamed internally to present
            "total_signals": sum(c["signal_count"] for c in categories)
        },
        "updated_at": datetime.utcnow().isoformat()
    }


def detect_pattern_tensions(categories: List[CategoryResult], max_tensions: int = 2) -> List[PatternTension]:
    """Detect meaningful tensions between active pattern categories.
    
    Only considers categories with signal_strength of "present" or "recurring".
    Uses curated TENSION_PAIRS for meaningful psychological tensions.
    
    Args:
        categories: List of CategoryResult from aggregate_pattern_graph
        max_tensions: Maximum number of tensions to return (default: 2)
    
    Returns:
        List of PatternTension objects, ranked by combined_score
    """
    # Build lookup for active categories (present or recurring)
    active_categories: Dict[str, CategoryResult] = {}
    for cat in categories:
        if cat["signal_strength"] in ("present", "recurring"):
            active_categories[cat["category_id"]] = cat
    
    # No active categories means no tensions
    if len(active_categories) < 2:
        return []
    
    # Check each tension pair
    tension_candidates: List[PatternTension] = []
    
    for pair in TENSION_PAIRS:
        cat_a_id = pair["category_a_id"]
        cat_b_id = pair["category_b_id"]
        
        # Both categories must be active
        if cat_a_id in active_categories and cat_b_id in active_categories:
            cat_a = active_categories[cat_a_id]
            cat_b = active_categories[cat_b_id]
            
            combined_score = cat_a["pattern_score"] + cat_b["pattern_score"]
            
            tension: PatternTension = {
                "category_a": cat_a["category_name"],
                "category_b": cat_b["category_name"],
                "combined_score": combined_score,
                "summary": pair["summary"],
                "reflection_prompt": pair["reflection_prompt"]
            }
            tension_candidates.append(tension)
    
    # Sort by combined score (highest first) and return top N
    tension_candidates.sort(key=lambda t: t["combined_score"], reverse=True)
    
    return tension_candidates[:max_tensions]


# =============================================================================
# TIMELINE AGGREGATION
# =============================================================================

class TimelineCategoryResult(TypedDict):
    """Result for a single category in a time bucket."""
    category_id: str
    category_name: str
    signal_strength: str  # "quiet", "present", "recurring"
    total_signals: int
    matched_sources: List[str]
    summary: str


class TimeBucketResult(TypedDict):
    """Result for a single time bucket."""
    bucket_name: str
    bucket_label: str
    start_date: str
    end_date: str
    categories: List[TimelineCategoryResult]
    has_activity: bool


def calculate_timeline_signal_strength(signal_count: int, source_count: int) -> str:
    """Calculate signal strength for timeline display.
    
    Uses user-facing language:
    - quiet: 0 signals
    - present: 1-2 signals
    - recurring: 3+ signals OR 2+ sources
    """
    if signal_count == 0:
        return "quiet"
    elif signal_count >= 3 or source_count >= 2:
        return "recurring"
    else:
        return "present"


def get_timeline_summary(category: dict, strength: str) -> str:
    """Get timeline-appropriate summary for a category."""
    cat_name = category["name"]
    
    if strength == "quiet":
        return f"No signals in {cat_name.lower()} themes during this period."
    elif strength == "present":
        return f"{cat_name} themes appeared occasionally during this period."
    else:  # recurring
        return f"{cat_name} themes showed up repeatedly during this period."


def aggregate_journal_signals_for_period(
    journal_entries: List[dict],
    start_date: datetime,
    end_date: datetime
) -> Dict[str, List[MatchedSignal]]:
    """Aggregate journal signals within a specific time period.
    
    Args:
        journal_entries: All journal entries
        start_date: Period start (inclusive)
        end_date: Period end (inclusive)
    
    Returns:
        Dict mapping category_id to list of matched signals
    """
    category_signals: Dict[str, List[MatchedSignal]] = {
        cat["id"]: [] for cat in PATTERN_CATEGORIES
    }
    
    for entry in journal_entries:
        timestamp = entry.get("timestamp")
        if not timestamp:
            continue
        
        # Convert timestamp to datetime if needed
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                continue
        
        # Check if within period
        entry_date = timestamp.replace(tzinfo=None) if hasattr(timestamp, 'tzinfo') else timestamp
        if not (start_date <= entry_date <= end_date):
            continue
        
        content = entry.get("content", "").lower()
        if len(content) < 20:
            continue
        
        # Check for keyword matches
        for cat_id, keywords in KEYWORD_CATEGORY_MAP.items():
            matches_found = []
            for kw in keywords:
                if kw in content:
                    matches_found.append(kw)
            
            if matches_found:
                date_str = entry_date.strftime("%b %d")
                signal: MatchedSignal = {
                    "source": "journal",
                    "label": f"Journal ({', '.join(matches_found[:2])})",
                    "sphere_name": None,
                    "detail": f"Entry on {date_str}"
                }
                category_signals[cat_id].append(signal)
    
    return category_signals


def build_time_bucket(
    bucket_name: str,
    bucket_label: str,
    start_date: datetime,
    end_date: datetime,
    gene_keys_signals: Dict[str, List[MatchedSignal]],
    hd_signals: Dict[str, List[MatchedSignal]],
    journal_signals: Dict[str, List[MatchedSignal]]
) -> TimeBucketResult:
    """Build a single time bucket result.
    
    Args:
        bucket_name: Internal bucket identifier
        bucket_label: User-facing label
        start_date: Period start
        end_date: Period end
        gene_keys_signals: Gene Keys signals (always present, not time-filtered)
        hd_signals: Human Design signals (always present, not time-filtered)
        journal_signals: Journal signals filtered to this period
    
    Returns:
        TimeBucketResult with categories
    """
    categories: List[TimelineCategoryResult] = []
    
    for cat in PATTERN_CATEGORIES:
        cat_id = cat["id"]
        
        # Collect signals from all sources
        all_signals: List[MatchedSignal] = []
        all_signals.extend(gene_keys_signals.get(cat_id, []))
        all_signals.extend(hd_signals.get(cat_id, []))
        all_signals.extend(journal_signals.get(cat_id, []))
        
        # Deduplicate by label
        seen_labels = set()
        unique_signals = []
        for sig in all_signals:
            if sig["label"] not in seen_labels:
                seen_labels.add(sig["label"])
                unique_signals.append(sig)
        
        # Calculate metrics
        sources = list(set(s["source"] for s in unique_signals))
        total_signals = len(unique_signals)
        
        # Calculate strength using timeline language
        strength = calculate_timeline_signal_strength(total_signals, len(sources))
        
        # Get summary
        summary = get_timeline_summary(cat, strength)
        
        result: TimelineCategoryResult = {
            "category_id": cat_id,
            "category_name": cat["name"],
            "signal_strength": strength,
            "total_signals": total_signals,
            "matched_sources": sources,
            "summary": summary
        }
        categories.append(result)
    
    # Check if there's any activity
    has_activity = any(c["signal_strength"] != "quiet" for c in categories)
    
    return {
        "bucket_name": bucket_name,
        "bucket_label": bucket_label,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "categories": categories,
        "has_activity": has_activity
    }


def aggregate_pattern_timeline(
    gene_keys_profile: Optional[dict] = None,
    journal_entries: Optional[List[dict]] = None,
    human_design_centers: Optional[List[dict]] = None,
    human_design_gates: Optional[List[int]] = None
) -> Dict[str, Any]:
    """Build pattern timeline with time buckets.
    
    Returns data for:
    - Last 7 days
    - Last 30 days
    
    Gene Keys and Human Design signals are "always present" (not time-filtered)
    since they're based on birth chart, not recent activity.
    
    Journal signals ARE time-filtered to show what was reflected on during each period.
    
    Args:
        gene_keys_profile: Result from build_gene_keys_profile()
        journal_entries: All journal entries (will be filtered by date)
        human_design_centers: List of center interpretations
        human_design_gates: List of active gate numbers
    
    Returns:
        Timeline response with time buckets
    """
    now = datetime.utcnow()
    
    # Define time buckets
    buckets_config = [
        {
            "name": "last_7_days",
            "label": "Last 7 Days",
            "start": now - timedelta(days=7),
            "end": now
        },
        {
            "name": "last_30_days",
            "label": "Last 30 Days",
            "start": now - timedelta(days=30),
            "end": now
        }
    ]
    
    # Pre-compute static signals (always present)
    gk_signals: Dict[str, List[MatchedSignal]] = {}
    if gene_keys_profile:
        gk_signals = aggregate_gene_keys_signals(gene_keys_profile)
    
    hd_signals: Dict[str, List[MatchedSignal]] = {}
    if human_design_centers or human_design_gates:
        hd_signals = aggregate_human_design_center_signals(
            centers_profile=human_design_centers,
            active_gates=human_design_gates
        )
    
    # Build time buckets
    buckets: List[TimeBucketResult] = []
    
    for bucket_config in buckets_config:
        # Get journal signals for this period
        journal_sigs: Dict[str, List[MatchedSignal]] = {}
        if journal_entries:
            journal_sigs = aggregate_journal_signals_for_period(
                journal_entries=journal_entries,
                start_date=bucket_config["start"],
                end_date=bucket_config["end"]
            )
        
        bucket = build_time_bucket(
            bucket_name=bucket_config["name"],
            bucket_label=bucket_config["label"],
            start_date=bucket_config["start"],
            end_date=bucket_config["end"],
            gene_keys_signals=gk_signals,
            hd_signals=hd_signals,
            journal_signals=journal_sigs
        )
        buckets.append(bucket)
    
    # Calculate summary
    any_activity = any(b["has_activity"] for b in buckets)
    
    return {
        "buckets": buckets,
        "has_any_activity": any_activity,
        "generated_at": now.isoformat()
    }



# =============================================================================
# PATTERN TREND DETECTION
# =============================================================================

def calculate_weighted_score_for_signals(signals: List[MatchedSignal]) -> int:
    """Calculate weighted score for a list of signals.
    
    Uses SIGNAL_WEIGHTS to compute total score.
    """
    if not signals:
        return 0
    
    total_score = 0
    for signal in signals:
        source = signal.get("source", "")
        weight = SIGNAL_WEIGHTS.get(source, 1)
        total_score += weight
    
    return total_score


def calculate_category_scores_for_period(
    gene_keys_signals: Dict[str, List[MatchedSignal]],
    hd_signals: Dict[str, List[MatchedSignal]],
    journal_signals: Dict[str, List[MatchedSignal]]
) -> Dict[str, int]:
    """Calculate weighted scores per category for a time period.
    
    Args:
        gene_keys_signals: Gene Keys signals (always present)
        hd_signals: Human Design signals (always present)
        journal_signals: Journal signals (time-filtered)
    
    Returns:
        Dict mapping category_id to weighted score
    """
    scores: Dict[str, int] = {}
    
    for cat in PATTERN_CATEGORIES:
        cat_id = cat["id"]
        
        # Collect all signals for this category
        all_signals: List[MatchedSignal] = []
        all_signals.extend(gene_keys_signals.get(cat_id, []))
        all_signals.extend(hd_signals.get(cat_id, []))
        all_signals.extend(journal_signals.get(cat_id, []))
        
        # Deduplicate by label
        seen_labels = set()
        unique_signals = []
        for sig in all_signals:
            if sig["label"] not in seen_labels:
                seen_labels.add(sig["label"])
                unique_signals.append(sig)
        
        # Calculate weighted score
        scores[cat_id] = calculate_weighted_score_for_signals(unique_signals)
    
    return scores


def calculate_trend(score_7_days: int, score_30_days: int) -> str:
    """Calculate trend direction by comparing 7-day and 30-day scores.
    
    Rules:
    - rising: score_7_days > score_30_days
    - fading: score_7_days < score_30_days
    - steady: scores are approximately equal (within 1 point tolerance)
    
    Returns:
        "rising", "steady", or "fading"
    """
    # Both scores are 0 means no activity
    if score_7_days == 0 and score_30_days == 0:
        return "steady"
    
    diff = score_7_days - score_30_days
    
    # Use a small tolerance for "steady" (within 1 point)
    if abs(diff) <= 1:
        return "steady"
    elif diff > 0:
        return "rising"
    else:
        return "fading"


def calculate_pattern_trends(
    gene_keys_profile: Optional[dict] = None,
    journal_entries: Optional[List[dict]] = None,
    human_design_centers: Optional[List[dict]] = None,
    human_design_gates: Optional[List[int]] = None
) -> Dict[str, str]:
    """Calculate trend direction for each pattern category.
    
    Compares weighted scores between last 7 days and last 30 days.
    
    Args:
        gene_keys_profile: Gene Keys profile data
        journal_entries: All journal entries
        human_design_centers: Human Design centers data
        human_design_gates: Active gate numbers
    
    Returns:
        Dict mapping category_id to trend ("rising", "steady", "fading")
    """
    now = datetime.utcnow()
    
    # Define time periods
    period_7_days = {
        "start": now - timedelta(days=7),
        "end": now
    }
    period_30_days = {
        "start": now - timedelta(days=30),
        "end": now
    }
    
    # Pre-compute static signals (Gene Keys, Human Design)
    gk_signals: Dict[str, List[MatchedSignal]] = {}
    if gene_keys_profile:
        gk_signals = aggregate_gene_keys_signals(gene_keys_profile)
    
    hd_signals: Dict[str, List[MatchedSignal]] = {}
    if human_design_centers or human_design_gates:
        hd_signals = aggregate_human_design_center_signals(
            centers_profile=human_design_centers,
            active_gates=human_design_gates
        )
    
    # Get journal signals for each period
    journal_7_days: Dict[str, List[MatchedSignal]] = {}
    journal_30_days: Dict[str, List[MatchedSignal]] = {}
    
    if journal_entries:
        journal_7_days = aggregate_journal_signals_for_period(
            journal_entries=journal_entries,
            start_date=period_7_days["start"],
            end_date=period_7_days["end"]
        )
        journal_30_days = aggregate_journal_signals_for_period(
            journal_entries=journal_entries,
            start_date=period_30_days["start"],
            end_date=period_30_days["end"]
        )
    
    # Calculate scores for each period
    scores_7_days = calculate_category_scores_for_period(
        gene_keys_signals=gk_signals,
        hd_signals=hd_signals,
        journal_signals=journal_7_days
    )
    
    scores_30_days = calculate_category_scores_for_period(
        gene_keys_signals=gk_signals,
        hd_signals=hd_signals,
        journal_signals=journal_30_days
    )
    
    # Calculate trends for each category
    trends: Dict[str, str] = {}
    for cat in PATTERN_CATEGORIES:
        cat_id = cat["id"]
        score_7 = scores_7_days.get(cat_id, 0)
        score_30 = scores_30_days.get(cat_id, 0)
        trends[cat_id] = calculate_trend(score_7, score_30)
    
    return trends
