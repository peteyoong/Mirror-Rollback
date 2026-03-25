"""
NOW SIGNAL ENGINE - Today Pattern v2
=====================================

Architecture:
1. NOW SIGNAL LAYER - Score signals by recency (24h=1.0, 72h=0.6, 7d=0.3)
2. CATEGORY MAPPING - Map signals to: move_forward, hold_back, seek_clarity, avoid_expression, control, release
3. TENSION DETECTION - Detect opposing forces (e.g., move_forward + hold_back = push_pull)
4. MICRO-MOMENT GENERATION - Generate specific behavioral moments, not themes
5. CONFIDENCE FILTER - Soft language for weak signals
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
import random
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# SIGNAL CATEGORIES
# =============================================================================

class SignalCategory(Enum):
    MOVE_FORWARD = "move_forward"
    HOLD_BACK = "hold_back"
    SEEK_CLARITY = "seek_clarity"
    AVOID_EXPRESSION = "avoid_expression"
    CONTROL = "control"
    RELEASE = "release"


# =============================================================================
# TENSION TYPES (when opposing categories combine)
# =============================================================================

class TensionType(Enum):
    PUSH_PULL = "push_pull"           # move_forward + hold_back
    SPEAK_SWALLOW = "speak_swallow"   # expression suppression
    GRIP_RELEASE = "grip_release"     # control + release
    CLARITY_FOG = "clarity_fog"       # seeking + not finding
    STALL = "stall"                   # general stuck feeling
    NONE = "none"                     # single dominant signal


# Tension detection matrix
TENSION_MATRIX = {
    (SignalCategory.MOVE_FORWARD, SignalCategory.HOLD_BACK): TensionType.PUSH_PULL,
    (SignalCategory.HOLD_BACK, SignalCategory.MOVE_FORWARD): TensionType.PUSH_PULL,
    (SignalCategory.CONTROL, SignalCategory.RELEASE): TensionType.GRIP_RELEASE,
    (SignalCategory.RELEASE, SignalCategory.CONTROL): TensionType.GRIP_RELEASE,
    (SignalCategory.SEEK_CLARITY, SignalCategory.HOLD_BACK): TensionType.CLARITY_FOG,
    (SignalCategory.SEEK_CLARITY, SignalCategory.AVOID_EXPRESSION): TensionType.CLARITY_FOG,
    (SignalCategory.MOVE_FORWARD, SignalCategory.AVOID_EXPRESSION): TensionType.SPEAK_SWALLOW,
    (SignalCategory.AVOID_EXPRESSION, SignalCategory.MOVE_FORWARD): TensionType.SPEAK_SWALLOW,
}


# =============================================================================
# RECENCY SCORING
# =============================================================================

def get_recency_weight(timestamp: datetime) -> float:
    """Score signal by recency: 24h=1.0, 72h=0.6, 7d=0.3, older=0.1"""
    now = datetime.now(timezone.utc)
    
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except:
            return 0.3  # default
    
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    
    age_hours = (now - timestamp).total_seconds() / 3600
    
    if age_hours <= 24:
        return 1.0
    elif age_hours <= 72:
        return 0.6
    elif age_hours <= 168:  # 7 days
        return 0.3
    else:
        return 0.1


# =============================================================================
# SIGNAL EXTRACTION FROM DATA SOURCES
# =============================================================================

def extract_journal_signals(entries: List[dict]) -> List[Dict[str, Any]]:
    """Extract behavioral signals from journal entries."""
    signals = []
    
    # Keywords that indicate behavioral states
    BEHAVIORAL_KEYWORDS = {
        SignalCategory.MOVE_FORWARD: [
            "decided", "chose", "started", "began", "moved", "acted", "did",
            "went", "tried", "pushed", "committed", "took", "made the call"
        ],
        SignalCategory.HOLD_BACK: [
            "waited", "stopped", "hesitated", "held back", "paused", "didn't",
            "couldn't", "almost", "nearly", "thought about", "considered",
            "pulled back", "retreated", "avoided"
        ],
        SignalCategory.SEEK_CLARITY: [
            "confused", "unsure", "wondering", "thinking", "processing",
            "figuring out", "trying to understand", "not sure", "unclear",
            "need to think", "weighing", "considering"
        ],
        SignalCategory.AVOID_EXPRESSION: [
            "didn't say", "held my tongue", "kept quiet", "stayed silent",
            "swallowed", "kept to myself", "didn't tell", "couldn't say",
            "wanted to say but"
        ],
        SignalCategory.CONTROL: [
            "tried to control", "managed", "forced", "pushed for", "made sure",
            "had to", "needed to control", "gripped", "held on"
        ],
        SignalCategory.RELEASE: [
            "let go", "surrendered", "accepted", "stopped trying", "released",
            "gave up", "stepped back", "allowed"
        ]
    }
    
    for entry in entries:
        text = entry.get("content", "").lower()
        created_at = entry.get("created_at", datetime.now(timezone.utc))
        recency = get_recency_weight(created_at)
        
        for category, keywords in BEHAVIORAL_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    signals.append({
                        "category": category,
                        "weight": recency,
                        "source": "journal",
                        "timestamp": created_at,
                        "trigger": keyword
                    })
                    break  # One signal per category per entry
    
    return signals


def extract_hd_signals(hd_data: dict) -> List[Dict[str, Any]]:
    """Extract behavioral signals from Human Design data."""
    signals = []
    base_weight = 0.5  # HD is structural, not time-based
    
    hd_type = hd_data.get("type", "").lower()
    authority = hd_data.get("authority", "").lower()
    active_centers = [c.lower() for c in hd_data.get("active_centers", [])]
    
    # Type-based signals
    if hd_type == "manifestor":
        signals.append({"category": SignalCategory.MOVE_FORWARD, "weight": base_weight, "source": "human_design"})
    elif hd_type == "generator" or hd_type == "manifesting generator":
        signals.append({"category": SignalCategory.HOLD_BACK, "weight": base_weight * 0.8, "source": "human_design"})  # Wait to respond
    elif hd_type == "projector":
        signals.append({"category": SignalCategory.HOLD_BACK, "weight": base_weight, "source": "human_design"})  # Wait for invitation
    elif hd_type == "reflector":
        signals.append({"category": SignalCategory.SEEK_CLARITY, "weight": base_weight, "source": "human_design"})  # Lunar cycle
    
    # Authority-based signals
    if "emotional" in authority:
        signals.append({"category": SignalCategory.HOLD_BACK, "weight": base_weight * 0.9, "source": "human_design"})
    elif "sacral" in authority:
        signals.append({"category": SignalCategory.MOVE_FORWARD, "weight": base_weight * 0.7, "source": "human_design"})
    elif "splenic" in authority:
        signals.append({"category": SignalCategory.MOVE_FORWARD, "weight": base_weight * 0.6, "source": "human_design"})
    elif "self" in authority or "identity" in authority:
        signals.append({"category": SignalCategory.SEEK_CLARITY, "weight": base_weight * 0.7, "source": "human_design"})
    
    # Center-based signals
    if "throat" in active_centers:
        signals.append({"category": SignalCategory.AVOID_EXPRESSION, "weight": base_weight * 0.5, "source": "human_design"})
    if "will" in active_centers or "heart" in active_centers:
        signals.append({"category": SignalCategory.CONTROL, "weight": base_weight * 0.6, "source": "human_design"})
    if "ajna" in active_centers or "head" in active_centers:
        signals.append({"category": SignalCategory.SEEK_CLARITY, "weight": base_weight * 0.5, "source": "human_design"})
    
    return signals


def extract_enneagram_signals(enneagram_data: dict) -> List[Dict[str, Any]]:
    """Extract behavioral signals from Enneagram type."""
    signals = []
    base_weight = 0.4  # Enneagram is personality-based
    
    ennea_type = str(enneagram_data.get("type", ""))
    
    # Type-based behavioral tendencies
    TYPE_SIGNALS = {
        "1": [SignalCategory.CONTROL, SignalCategory.HOLD_BACK],
        "2": [SignalCategory.MOVE_FORWARD, SignalCategory.AVOID_EXPRESSION],
        "3": [SignalCategory.MOVE_FORWARD, SignalCategory.CONTROL],
        "4": [SignalCategory.HOLD_BACK, SignalCategory.AVOID_EXPRESSION],
        "5": [SignalCategory.HOLD_BACK, SignalCategory.SEEK_CLARITY],
        "6": [SignalCategory.SEEK_CLARITY, SignalCategory.HOLD_BACK],
        "7": [SignalCategory.MOVE_FORWARD, SignalCategory.RELEASE],
        "8": [SignalCategory.MOVE_FORWARD, SignalCategory.CONTROL],
        "9": [SignalCategory.HOLD_BACK, SignalCategory.RELEASE],
    }
    
    if ennea_type in TYPE_SIGNALS:
        for i, category in enumerate(TYPE_SIGNALS[ennea_type]):
            # First signal stronger than second
            weight = base_weight if i == 0 else base_weight * 0.6
            signals.append({"category": category, "weight": weight, "source": "enneagram"})
    
    return signals


def extract_transit_signals(transit_data: dict) -> List[Dict[str, Any]]:
    """Extract behavioral signals from current transits."""
    signals = []
    base_weight = 0.6  # Transits are current
    
    day_class = transit_data.get("day_class", "").lower()
    dominant_tension = transit_data.get("dominant_tension", "").lower()
    
    # Day class signals
    if "pressure" in day_class or "intense" in day_class:
        signals.append({"category": SignalCategory.CONTROL, "weight": base_weight, "source": "transits"})
    elif "flow" in day_class:
        signals.append({"category": SignalCategory.RELEASE, "weight": base_weight * 0.8, "source": "transits"})
    
    # Tension-based signals
    if "decision" in dominant_tension or "crossroad" in dominant_tension:
        signals.append({"category": SignalCategory.HOLD_BACK, "weight": base_weight, "source": "transits"})
    elif "express" in dominant_tension or "voice" in dominant_tension:
        signals.append({"category": SignalCategory.AVOID_EXPRESSION, "weight": base_weight, "source": "transits"})
    elif "clarity" in dominant_tension or "mental" in dominant_tension:
        signals.append({"category": SignalCategory.SEEK_CLARITY, "weight": base_weight, "source": "transits"})
    elif "action" in dominant_tension or "move" in dominant_tension:
        signals.append({"category": SignalCategory.MOVE_FORWARD, "weight": base_weight, "source": "transits"})
    
    return signals


# =============================================================================
# SIGNAL AGGREGATION & TENSION DETECTION
# =============================================================================

def aggregate_signals(all_signals: List[Dict[str, Any]]) -> Dict[SignalCategory, float]:
    """Aggregate all signals by category, summing weighted scores."""
    category_scores = {cat: 0.0 for cat in SignalCategory}
    
    for signal in all_signals:
        category = signal["category"]
        weight = signal["weight"]
        category_scores[category] += weight
    
    return category_scores


def detect_tension(category_scores: Dict[SignalCategory, float]) -> Tuple[TensionType, List[SignalCategory]]:
    """Detect tension between opposing signal categories."""
    # Get top 2 categories
    sorted_cats = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
    
    if len(sorted_cats) < 2 or sorted_cats[1][1] < 0.3:
        # Single dominant or weak secondary
        return TensionType.NONE, [sorted_cats[0][0]] if sorted_cats else []
    
    top_two = (sorted_cats[0][0], sorted_cats[1][0])
    
    # Check tension matrix
    tension = TENSION_MATRIX.get(top_two, TensionType.STALL)
    
    return tension, list(top_two)


def calculate_confidence(all_signals: List[Dict[str, Any]], category_scores: Dict[SignalCategory, float]) -> float:
    """Calculate confidence based on signal strength and diversity."""
    if not all_signals:
        return 0.2
    
    # Factors:
    # 1. Total signal weight
    total_weight = sum(category_scores.values())
    
    # 2. Number of sources
    sources = set(s["source"] for s in all_signals)
    
    # 3. Recency of strongest signals
    recent_signals = [s for s in all_signals if s.get("weight", 0) >= 0.6]
    
    # Calculate confidence
    confidence = 0.3  # base
    
    if total_weight > 2.0:
        confidence += 0.2
    elif total_weight > 1.0:
        confidence += 0.1
    
    if len(sources) >= 3:
        confidence += 0.2
    elif len(sources) >= 2:
        confidence += 0.1
    
    if len(recent_signals) >= 2:
        confidence += 0.2
    elif len(recent_signals) >= 1:
        confidence += 0.1
    
    return min(confidence, 0.95)


# =============================================================================
# MICRO-MOMENT GENERATION
# =============================================================================

# Micro-moments by tension type - these are SPECIFIC BEHAVIORAL MOMENTS, not themes
MICRO_MOMENTS = {
    TensionType.PUSH_PULL: {
        "openers": [
            "You almost moved—then stopped",
            "You started to act—then hesitated",
            "You reached for it—then pulled back",
            "You were about to—then you weren't",
        ],
        "middles": [
            "Part of you says go. Another part isn't ready",
            "Something in you pushed. Something else pulled",
            "Forward felt right, then it didn't",
            "The yes came first. The wait came after",
        ],
        "closers": [
            "You've been here before",
            "This isn't new",
            "You know this loop",
        ]
    },
    TensionType.SPEAK_SWALLOW: {
        "openers": [
            "You almost said it—then didn't",
            "The words were there—then you swallowed them",
            "You started to speak—then stopped",
            "It was on the tip of your tongue",
        ],
        "middles": [
            "Part of you wanted to say it. Part of you decided not to",
            "The moment came. You let it pass",
            "You chose silence. It wasn't nothing",
            "Some things stay inside for a reason",
        ],
        "closers": [
            "You've held this before",
            "This silence is familiar",
            "You've swallowed this before",
        ]
    },
    TensionType.GRIP_RELEASE: {
        "openers": [
            "You tried to control it—then realized you couldn't",
            "You held on—then felt the grip loosen",
            "You pushed—then stopped pushing",
            "You wanted it your way. It didn't go your way",
        ],
        "middles": [
            "Some of it isn't yours to hold",
            "The tighter you grip, the more it slips",
            "Control felt necessary. Then it didn't",
            "You wanted to force it. You couldn't",
        ],
        "closers": [
            "You've gripped this before",
            "This tension is old",
            "You know this feeling",
        ]
    },
    TensionType.CLARITY_FOG: {
        "openers": [
            "You thought you knew—then you didn't",
            "It felt clear—then the fog rolled back",
            "You almost understood—then lost it",
            "The answer was there. Then it wasn't",
        ],
        "middles": [
            "The more you think, the less you see",
            "Certainty keeps slipping",
            "What made sense yesterday doesn't land today",
            "You're still figuring it out",
        ],
        "closers": [
            "You've searched for this clarity before",
            "This fog isn't new",
            "You've been here before",
        ]
    },
    TensionType.STALL: {
        "openers": [
            "Something stopped you—you're not sure what",
            "You paused. You're still paused",
            "The momentum stalled",
            "You got stuck somewhere",
        ],
        "middles": [
            "It's not a no. It's not a yes",
            "You're waiting for something to shift",
            "Nothing feels quite right to move on",
            "The next step isn't showing itself",
        ],
        "closers": [
            "You've been stuck before",
            "This pause is familiar",
            "You know this in-between",
        ]
    },
    TensionType.NONE: {
        "move_forward": {
            "openers": [
                "You moved—even when it wasn't clear",
                "You took the step",
                "You acted before the doubt could stop you",
            ],
            "middles": [
                "Something in you just goes",
                "Waiting isn't your way",
                "The impulse came. You followed it",
            ],
        },
        "hold_back": {
            "openers": [
                "You didn't move—and you noticed",
                "You waited, even when part of you wanted to go",
                "The pause happened before you could stop it",
            ],
            "middles": [
                "There's a reason you're not moving",
                "The wait isn't nothing. It's a choice",
                "Something is keeping you still",
            ],
        },
        "seek_clarity": {
            "openers": [
                "You're still turning it over",
                "The question keeps coming back",
                "You're not done processing",
            ],
            "middles": [
                "Understanding takes time",
                "The picture isn't complete yet",
                "You're still gathering pieces",
            ],
        },
        "avoid_expression": {
            "openers": [
                "There's something you haven't said",
                "The words are inside—they haven't come out",
                "You're carrying something unspoken",
            ],
            "middles": [
                "Not everything needs to be said",
                "Some things stay inside for now",
                "The silence is intentional",
            ],
        },
        "control": {
            "openers": [
                "You're trying to make it go a certain way",
                "You're holding the reins tight",
                "You need this to land right",
            ],
            "middles": [
                "Some things you can control. Some you can't",
                "The grip feels necessary",
                "You're managing what you can",
            ],
        },
        "release": {
            "openers": [
                "You let something go—or you're about to",
                "The grip is loosening",
                "You stopped trying to force it",
            ],
            "middles": [
                "Sometimes letting go is the move",
                "Surrender isn't giving up",
                "Release doesn't mean you don't care",
            ],
        },
        "closers": [
            "You've been here before",
            "This isn't the first time",
            "You know this feeling",
        ]
    }
}

# Low confidence softeners
LOW_CONFIDENCE_OPENERS = [
    "Something feels off—you can't quite name it",
    "There's a feeling you can't place",
    "Something's stirring—it hasn't landed yet",
    "You sense something, but it's not clear",
]

LOW_CONFIDENCE_MIDDLES = [
    "It hasn't taken shape yet",
    "You're still figuring out what it is",
    "The edges are blurry",
    "It's there, but it's not solid",
]

LOW_CONFIDENCE_CLOSERS = [
    "But it hasn't landed yet",
    "You're still feeling it out",
    "Give it time",
]


def generate_micro_moment(
    tension: TensionType,
    dominant_categories: List[SignalCategory],
    confidence: float,
    day_seed: int
) -> Dict[str, Any]:
    """Generate a specific micro-moment based on detected signals and tension."""
    
    # Low confidence = use softener language
    if confidence < 0.4:
        opener = LOW_CONFIDENCE_OPENERS[day_seed % len(LOW_CONFIDENCE_OPENERS)]
        middle = LOW_CONFIDENCE_MIDDLES[(day_seed + 1) % len(LOW_CONFIDENCE_MIDDLES)]
        closer = LOW_CONFIDENCE_CLOSERS[(day_seed + 2) % len(LOW_CONFIDENCE_CLOSERS)]
        
        return {
            "title": "Something Stirring",
            "lines": [opener, middle, closer],
            "tension_type": "low_confidence",
        }
    
    # Tension-based generation
    if tension != TensionType.NONE:
        moment_pool = MICRO_MOMENTS.get(tension, MICRO_MOMENTS[TensionType.STALL])
        
        opener = moment_pool["openers"][day_seed % len(moment_pool["openers"])]
        middle = moment_pool["middles"][(day_seed + 1) % len(moment_pool["middles"])]
        closer = moment_pool["closers"][(day_seed + 2) % len(moment_pool["closers"])]
        
        # Tension-specific titles
        TENSION_TITLES = {
            TensionType.PUSH_PULL: "Forward and Back",
            TensionType.SPEAK_SWALLOW: "What's Unsaid",
            TensionType.GRIP_RELEASE: "Grip and Release",
            TensionType.CLARITY_FOG: "Still Searching",
            TensionType.STALL: "The Pause",
        }
        
        return {
            "title": TENSION_TITLES.get(tension, "Today's Pattern"),
            "lines": [opener, middle, closer],
            "tension_type": tension.value,
        }
    
    # Single dominant category (no tension)
    if dominant_categories:
        dom_cat = dominant_categories[0].value
        none_pool = MICRO_MOMENTS[TensionType.NONE]
        
        if dom_cat in none_pool:
            cat_pool = none_pool[dom_cat]
            opener = cat_pool["openers"][day_seed % len(cat_pool["openers"])]
            middle = cat_pool["middles"][(day_seed + 1) % len(cat_pool["middles"])]
        else:
            # Fallback
            opener = LOW_CONFIDENCE_OPENERS[day_seed % len(LOW_CONFIDENCE_OPENERS)]
            middle = LOW_CONFIDENCE_MIDDLES[(day_seed + 1) % len(LOW_CONFIDENCE_MIDDLES)]
        
        closer = none_pool["closers"][(day_seed + 2) % len(none_pool["closers"])]
        
        CATEGORY_TITLES = {
            SignalCategory.MOVE_FORWARD: "Moving",
            SignalCategory.HOLD_BACK: "Waiting",
            SignalCategory.SEEK_CLARITY: "Processing",
            SignalCategory.AVOID_EXPRESSION: "Holding Back",
            SignalCategory.CONTROL: "Gripping",
            SignalCategory.RELEASE: "Letting Go",
        }
        
        return {
            "title": CATEGORY_TITLES.get(dominant_categories[0], "Today"),
            "lines": [opener, middle, closer],
            "tension_type": dom_cat,
        }
    
    # Absolute fallback
    return {
        "title": "Something Shifting",
        "lines": [
            LOW_CONFIDENCE_OPENERS[day_seed % len(LOW_CONFIDENCE_OPENERS)],
            LOW_CONFIDENCE_MIDDLES[(day_seed + 1) % len(LOW_CONFIDENCE_MIDDLES)],
            LOW_CONFIDENCE_CLOSERS[(day_seed + 2) % len(LOW_CONFIDENCE_CLOSERS)],
        ],
        "tension_type": "fallback",
    }


# =============================================================================
# MAIN ENGINE FUNCTION
# =============================================================================

async def generate_today_pattern(
    journal_entries: Optional[List[dict]] = None,
    hd_data: Optional[dict] = None,
    enneagram_data: Optional[dict] = None,
    transit_data: Optional[dict] = None,
    day_seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Main engine: Generate today's pattern using signal-based architecture.
    
    Returns:
        dict with: title, lines, confidence, sources, tension_type
    """
    if day_seed is None:
        day_seed = int(datetime.now(timezone.utc).strftime("%d"))
    
    # Step 1: Extract signals from all sources
    all_signals = []
    sources_used = []
    
    if journal_entries:
        journal_signals = extract_journal_signals(journal_entries)
        if journal_signals:
            all_signals.extend(journal_signals)
            sources_used.append("journal")
    
    if hd_data:
        hd_signals = extract_hd_signals(hd_data)
        if hd_signals:
            all_signals.extend(hd_signals)
            sources_used.append("human_design")
    
    if enneagram_data:
        ennea_signals = extract_enneagram_signals(enneagram_data)
        if ennea_signals:
            all_signals.extend(ennea_signals)
            sources_used.append("enneagram")
    
    if transit_data:
        transit_signals = extract_transit_signals(transit_data)
        if transit_signals:
            all_signals.extend(transit_signals)
            sources_used.append("transits")
    
    logger.info(f"[NowSignalEngine] Extracted {len(all_signals)} signals from {sources_used}")
    
    # Step 2: Aggregate signals by category
    category_scores = aggregate_signals(all_signals)
    logger.debug(f"[NowSignalEngine] Category scores: {category_scores}")
    
    # Step 3: Detect tension
    tension, dominant_categories = detect_tension(category_scores)
    logger.info(f"[NowSignalEngine] Detected tension: {tension.value}, dominant: {[c.value for c in dominant_categories]}")
    
    # Step 4: Calculate confidence
    confidence = calculate_confidence(all_signals, category_scores)
    logger.info(f"[NowSignalEngine] Confidence: {confidence}")
    
    # Step 5: Generate micro-moment
    micro_moment = generate_micro_moment(tension, dominant_categories, confidence, day_seed)
    
    return {
        "title": micro_moment["title"],
        "lines": micro_moment["lines"],
        "confidence": confidence,
        "sources": sources_used if sources_used else ["baseline"],
        "tension_type": micro_moment["tension_type"],
        "category_scores": {k.value: round(v, 2) for k, v in category_scores.items()},
    }
