"""
Lunar Cycle Synthesis - Task 69: Mirror Cycle Intelligence Engine (v1)

Generates structured insights from a Reflector's journal entries across a lunar cycle.
Analyzes reflection content, emotional signals, gate patterns, and timing.

This is NOT predictive - it uses Mirror language to reflect patterns back to the user.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from collections import Counter
import random

logger = logging.getLogger(__name__)

# =============================================================================
# EMOTIONAL SIGNAL KEYWORDS - Task 69
# =============================================================================

EXCITEMENT_SIGNALS = [
    "excited", "energized", "interested", "curious", "inspired",
    "good idea", "love", "amazing", "wonderful", "opportunity",
    "thrilled", "hopeful", "passionate", "eager", "possibility",
    "potential", "looking forward", "can't wait", "dream"
]

HESITATION_SIGNALS = [
    "worried", "uncertain", "scared", "risk", "not sure", "doubt",
    "stress", "anxious", "afraid", "concerned", "hesitant",
    "nervous", "overwhelming", "difficult", "hard", "challenging",
    "fear", "what if", "risky", "dangerous", "problem"
]

NEUTRAL_SIGNALS = [
    "thinking", "considering", "exploring", "wondering", "observing",
    "noticing", "reflecting", "processing", "pondering", "curious about"
]

# =============================================================================
# THEME DETECTION KEYWORDS
# =============================================================================

THEME_KEYWORDS = {
    "creative_independence": ["create", "creative", "independent", "freedom", "own way", "expression", "art", "unique"],
    "financial_security": ["money", "financial", "income", "salary", "pay", "bills", "budget", "stable", "security"],
    "relationship_impact": ["family", "partner", "relationship", "friends", "support", "together", "love ones"],
    "personal_growth": ["grow", "learn", "develop", "evolve", "better", "improve", "skill", "capability"],
    "lifestyle_change": ["life", "lifestyle", "change", "different", "new", "routine", "daily", "balance"],
    "career_path": ["career", "work", "job", "profession", "path", "direction", "opportunity", "role"],
    "risk_assessment": ["risk", "safe", "careful", "cautious", "uncertain", "unknown", "venture"],
    "timing_readiness": ["ready", "time", "now", "when", "wait", "timing", "moment", "prepared"],
    "values_alignment": ["value", "meaning", "purpose", "important", "matter", "authentic", "align"],
    "external_factors": ["others", "expect", "should", "society", "people", "opinion", "pressure"],
}

# =============================================================================
# GATE INSIGHTS - Human Design Gate Meanings
# =============================================================================

GATE_INSIGHTS = {
    1: {"title": "Self-Expression", "insight": "This gate often brings focus to authentic creative expression and individuality."},
    2: {"title": "The Direction of Self", "insight": "This gate relates to receptivity and natural direction without forcing."},
    3: {"title": "Ordering", "insight": "This gate involves innovation and bringing order to new beginnings."},
    13: {"title": "The Listener", "insight": "This gate connects to collecting stories and learning from experience."},
    17: {"title": "Opinions", "insight": "This gate relates to following and sharing one's perspective."},
    19: {"title": "Wanting", "insight": "This gate connects to sensitivity around needs and resources."},
    21: {"title": "The Hunter", "insight": "This gate involves control and pushing through obstacles."},
    22: {"title": "Openness", "insight": "This gate relates to emotional grace and openness to experience."},
    25: {"title": "Innocence", "insight": "This gate connects to universal love and approaching things fresh."},
    27: {"title": "Caring", "insight": "This gate involves nourishment and caring for self and others."},
    30: {"title": "Feelings", "insight": "This gate relates to recognizing feelings and desire for new experience."},
    36: {"title": "Crisis", "insight": "This gate connects to emotional exploration and moving through intensity."},
    37: {"title": "Friendship", "insight": "This gate involves family, community, and belonging."},
    41: {"title": "Contraction", "insight": "This gate often initiates cycles through imagination and desire."},
    42: {"title": "Growth", "insight": "This gate relates to completing cycles and growth through experience."},
    49: {"title": "Principles", "insight": "This gate connects to revolution and standing by one's principles."},
    51: {"title": "Shock", "insight": "This gate involves initiative and the shock of new beginnings."},
    55: {"title": "Spirit", "insight": "This gate relates to emotional abundance and spirit."},
    63: {"title": "Doubt", "insight": "This gate connects to logical questioning and pressure to find answers."},
}

# =============================================================================
# MIRROR LANGUAGE TEMPLATES
# =============================================================================

LOW_DATA_TEMPLATES = [
    "You recorded {count} reflection during this cycle. More entries may reveal clearer patterns in how your perspective evolves.",
    "With {count} reflection logged, there may not be enough data to identify clear patterns. Consider continuing observation.",
]

PATTERN_INSIGHT_TEMPLATES = [
    "Across the cycle, your reflections seem to return to the theme of {theme}, suggesting this may be an important consideration.",
    "A thread that appears consistently is {theme}. This may point to something worth exploring further.",
    "Your reflections suggest that {theme} has been on your mind throughout this observation period.",
]

EMOTIONAL_SUMMARY_TEMPLATES = {
    "excitement_dominant": "Your reflections carry a sense of excitement and possibility around this decision.",
    "hesitation_dominant": "Your reflections suggest some hesitation or caution about moving forward.",
    "mixed": "Your reflections show a mix of excitement and hesitation, which may reflect the complexity of this decision.",
    "neutral": "Your reflections appear thoughtful and measured, without strong emotional pulls either way.",
}

GATE_SIGNIFICANCE_TEMPLATES = [
    "Your most substantive reflection came during Gate {gate} — {title}. {insight}",
    "Gate {gate} ({title}) appears to have sparked particularly deep consideration. {insight}",
    "The energy of Gate {gate} — {title} may have been significant for you. {insight}",
]

CLOSING_QUESTIONS = [
    "What now feels clearer about this decision than it did at the beginning of the cycle?",
    "Looking back across this cycle, what perspective feels most trustworthy?",
    "Which insights from this observation period feel most reliable to act on?",
    "What has this cycle revealed that you can now trust?",
    "Having moved through these different gates, what understanding remains steady?",
]


# =============================================================================
# ANALYSIS FUNCTIONS - Task 69
# =============================================================================

def detect_emotional_signals(text: str) -> Dict[str, int]:
    """Detect emotional signals in text and return counts."""
    text_lower = text.lower()
    
    excitement_count = sum(1 for signal in EXCITEMENT_SIGNALS if signal in text_lower)
    hesitation_count = sum(1 for signal in HESITATION_SIGNALS if signal in text_lower)
    neutral_count = sum(1 for signal in NEUTRAL_SIGNALS if signal in text_lower)
    
    return {
        "excitement": excitement_count,
        "hesitation": hesitation_count,
        "neutral": neutral_count,
    }


def analyze_entries_emotional_signals(entries: List[Dict]) -> Dict[str, Any]:
    """Analyze emotional signals across all entries."""
    total_excitement = 0
    total_hesitation = 0
    total_neutral = 0
    
    excitement_examples = []
    hesitation_examples = []
    
    for entry in entries:
        content = entry.get("content", "")
        signals = detect_emotional_signals(content)
        
        total_excitement += signals["excitement"]
        total_hesitation += signals["hesitation"]
        total_neutral += signals["neutral"]
        
        # Collect example phrases
        content_lower = content.lower()
        for signal in EXCITEMENT_SIGNALS:
            if signal in content_lower and signal not in excitement_examples:
                excitement_examples.append(signal)
        for signal in HESITATION_SIGNALS:
            if signal in content_lower and signal not in hesitation_examples:
                hesitation_examples.append(signal)
    
    # Determine dominant tone
    if total_excitement > total_hesitation * 1.5:
        dominant = "excitement_dominant"
    elif total_hesitation > total_excitement * 1.5:
        dominant = "hesitation_dominant"
    elif total_excitement > 0 and total_hesitation > 0:
        dominant = "mixed"
    else:
        dominant = "neutral"
    
    return {
        "excitement_count": total_excitement,
        "hesitation_count": total_hesitation,
        "neutral_count": total_neutral,
        "dominant_tone": dominant,
        "excitement_examples": excitement_examples[:5],
        "hesitation_examples": hesitation_examples[:5],
    }


def extract_themes(entries: List[Dict]) -> Dict[str, Any]:
    """Extract themes from all entries."""
    theme_counts = Counter()
    theme_examples = {}
    
    for entry in entries:
        content = entry.get("content", "").lower()
        
        for theme, keywords in THEME_KEYWORDS.items():
            for keyword in keywords:
                if keyword in content:
                    theme_counts[theme] += 1
                    if theme not in theme_examples:
                        theme_examples[theme] = keyword
                    break
    
    # Get top themes
    top_themes = theme_counts.most_common(3)
    
    return {
        "all_themes": dict(theme_counts),
        "top_themes": [{"theme": t, "count": c} for t, c in top_themes],
        "theme_examples": theme_examples,
    }


def find_strongest_gate(entries: List[Dict]) -> Optional[Dict[str, Any]]:
    """Find the gate with the most significant reflections."""
    gate_data = {}
    
    for entry in entries:
        gate = entry.get("moon_gate")
        if not gate:
            continue
        
        content = entry.get("content", "")
        signals = detect_emotional_signals(content)
        
        if gate not in gate_data:
            gate_data[gate] = {
                "gate": gate,
                "entry_count": 0,
                "total_length": 0,
                "emotional_intensity": 0,
                "longest_entry": "",
            }
        
        gate_data[gate]["entry_count"] += 1
        gate_data[gate]["total_length"] += len(content)
        gate_data[gate]["emotional_intensity"] += signals["excitement"] + signals["hesitation"]
        
        if len(content) > len(gate_data[gate]["longest_entry"]):
            gate_data[gate]["longest_entry"] = content
    
    if not gate_data:
        return None
    
    # Score gates by: entry count, content length, emotional intensity
    for gate in gate_data.values():
        gate["score"] = (
            gate["entry_count"] * 15 +
            gate["total_length"] // 30 +
            gate["emotional_intensity"] * 5
        )
    
    # Find strongest
    strongest = max(gate_data.values(), key=lambda g: g["score"])
    
    # Get gate insight
    gate_info = GATE_INSIGHTS.get(strongest["gate"], {
        "title": f"Gate {strongest['gate']}",
        "insight": "This gate may have brought a unique perspective to your observation."
    })
    
    return {
        "gate": strongest["gate"],
        "title": gate_info["title"],
        "insight": gate_info["insight"],
        "entry_count": strongest["entry_count"],
        "longest_entry_preview": strongest["longest_entry"][:150] + "..." if len(strongest["longest_entry"]) > 150 else strongest["longest_entry"],
    }


def build_pattern_insight(themes: Dict[str, Any], emotional: Dict[str, Any]) -> Optional[str]:
    """Build a pattern insight from themes and emotional data."""
    top_themes = themes.get("top_themes", [])
    
    if not top_themes:
        return None
    
    # Format theme name for display
    theme_name = top_themes[0]["theme"].replace("_", " ")
    
    template = random.choice(PATTERN_INSIGHT_TEMPLATES)
    return template.format(theme=theme_name)


def format_emotional_themes(emotional: Dict[str, Any], themes: Dict[str, Any]) -> Dict[str, Any]:
    """Format emotional themes for display."""
    excitement_themes = []
    hesitation_themes = []
    
    top_themes = themes.get("top_themes", [])
    
    # Map themes to emotional categories based on their nature
    positive_themes = ["creative_independence", "personal_growth", "values_alignment"]
    cautious_themes = ["financial_security", "risk_assessment", "external_factors"]
    
    for theme_data in top_themes:
        theme = theme_data["theme"]
        display_name = theme.replace("_", " ").title()
        
        if theme in positive_themes:
            excitement_themes.append(display_name)
        elif theme in cautious_themes:
            hesitation_themes.append(display_name)
        else:
            # Assign based on emotional dominance
            if emotional.get("dominant_tone") == "excitement_dominant":
                excitement_themes.append(display_name)
            else:
                hesitation_themes.append(display_name)
    
    return {
        "excitement_themes": excitement_themes[:3],
        "hesitation_themes": hesitation_themes[:3],
    }


# =============================================================================
# MAIN SYNTHESIS FUNCTION - Task 69
# =============================================================================

async def generate_lunar_cycle_synthesis(
    db,
    user_id: str,
    consideration_id: str,
    cycle_completed: bool = False
) -> Dict[str, Any]:
    """
    Generate structured cycle insights from journal entries.
    
    Args:
        db: Database connection
        user_id: User ID
        consideration_id: Consideration/decision ID
        cycle_completed: Whether the cycle has been completed (affects synthesis depth)
    
    Returns:
        Structured synthesis data with insights
    """
    logger.info(f"[LunarSynthesis] Generating synthesis for user {user_id[:8]}, consideration {consideration_id[:8]}, completed={cycle_completed}")
    
    try:
        # Fetch entries for this consideration
        entries = await db.lunar_journal.find({
            "user_id": user_id,
            "consideration_id": consideration_id,
        }).sort("lunar_day", 1).to_list(length=100)
        
        # Fetch the consideration
        from bson import ObjectId
        consideration = await db.lunar_considerations.find_one({
            "_id": ObjectId(consideration_id),
        })
        topic = consideration.get("topic", "this decision") if consideration else "this decision"
        status = consideration.get("status", "active") if consideration else "active"
        
        # Calculate days observed
        unique_days = len(set(int(e.get("lunar_day", 0)) for e in entries))
        unique_gates = len(set(e.get("moon_gate") for e in entries if e.get("moon_gate")))
        
        # Handle low-data scenario (< 2 entries)
        if len(entries) < 2:
            logger.info("[LunarSynthesis] Low data - returning minimal synthesis")
            return {
                "success": True,
                "has_synthesis": True,
                "is_low_data": True,
                "consideration_topic": topic,
                "entry_count": len(entries),
                "days_observed": unique_days,
                "gates_touched": unique_gates,
                "low_data_message": random.choice(LOW_DATA_TEMPLATES).format(count=len(entries)),
                "suggestion": "You may wish to continue observing this decision through another cycle.",
            }
        
        # Run full analysis
        emotional_analysis = analyze_entries_emotional_signals(entries)
        theme_analysis = extract_themes(entries)
        strongest_gate = find_strongest_gate(entries)
        pattern_insight = build_pattern_insight(theme_analysis, emotional_analysis)
        formatted_themes = format_emotional_themes(emotional_analysis, theme_analysis)
        
        # Build synthesis response
        synthesis = {
            "success": True,
            "has_synthesis": True,
            "is_low_data": False,
            "consideration_topic": topic,
            "cycle_completed": status == "completed" or cycle_completed,
            
            # Cycle Overview
            "entry_count": len(entries),
            "days_observed": unique_days,
            "gates_touched": unique_gates,
            
            # Emotional Signals
            "emotional_signals": {
                "dominant_tone": emotional_analysis["dominant_tone"],
                "excitement_count": emotional_analysis["excitement_count"],
                "hesitation_count": emotional_analysis["hesitation_count"],
                "summary": EMOTIONAL_SUMMARY_TEMPLATES.get(
                    emotional_analysis["dominant_tone"],
                    EMOTIONAL_SUMMARY_TEMPLATES["neutral"]
                ),
            },
            "emotional_themes": formatted_themes,
            
            # Notable Gate
            "strongest_gate": strongest_gate,
            
            # Pattern Insight
            "pattern_insight": pattern_insight,
            "top_themes": [t["theme"].replace("_", " ").title() for t in theme_analysis.get("top_themes", [])],
            
            # Reflection Question
            "reflection_question": random.choice(CLOSING_QUESTIONS),
        }
        
        # Add gate significance text if we have a strongest gate
        if strongest_gate:
            template = random.choice(GATE_SIGNIFICANCE_TEMPLATES)
            synthesis["gate_significance_text"] = template.format(
                gate=strongest_gate["gate"],
                title=strongest_gate["title"],
                insight=strongest_gate["insight"]
            )
        
        logger.info(f"[LunarSynthesis] Generated synthesis with {len(entries)} entries, dominant tone: {emotional_analysis['dominant_tone']}")
        
        return synthesis
        
    except Exception as e:
        logger.error(f"[LunarSynthesis] Error generating synthesis: {e}")
        return {
            "success": False,
            "error": str(e),
        }


async def get_cached_synthesis(
    db,
    user_id: str,
    consideration_id: str,
    force_regenerate: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Get cached synthesis or generate new one.
    
    Args:
        db: Database connection
        user_id: User ID
        consideration_id: Consideration ID
        force_regenerate: If True, regenerate even if cached
    """
    from bson import ObjectId
    
    try:
        if not force_regenerate:
            # Check for cached synthesis
            cached = await db.lunar_synthesis_cache.find_one({
                "user_id": user_id,
                "consideration_id": consideration_id,
            })
            
            if cached:
                logger.info(f"[LunarSynthesis] Returning cached synthesis for {consideration_id[:8]}")
                return {k: v for k, v in cached.items() if k != "_id"}
        
        # Generate new synthesis
        synthesis = await generate_lunar_cycle_synthesis(db, user_id, consideration_id)
        
        if synthesis.get("success") and synthesis.get("has_synthesis"):
            # Remove old cache
            await db.lunar_synthesis_cache.delete_many({
                "user_id": user_id,
                "consideration_id": consideration_id,
            })
            
            # Cache the result
            cache_doc = {
                "user_id": user_id,
                "consideration_id": consideration_id,
                "created_at": datetime.now(timezone.utc),
                **synthesis,
            }
            await db.lunar_synthesis_cache.insert_one(cache_doc)
            logger.info(f"[LunarSynthesis] Cached new synthesis for {consideration_id[:8]}")
        
        return synthesis
        
    except Exception as e:
        logger.error(f"[LunarSynthesis] Error getting/caching synthesis: {e}")
        return await generate_lunar_cycle_synthesis(db, user_id, consideration_id)
