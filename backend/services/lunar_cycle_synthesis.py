"""
Lunar Cycle Synthesis - Task 55

Generates an observational synthesis of a Reflector's journal entries
across a lunar cycle, helping them see patterns in how their perspective
shifted across different gates.

This is NOT predictive - it is purely observational, using Mirror language.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from collections import Counter

logger = logging.getLogger(__name__)

# =============================================================================
# MIRROR LANGUAGE TEMPLATES
# =============================================================================

CONSISTENT_THEME_TEMPLATES = [
    "You seemed to return several times to the idea of {theme}.",
    "A recurring thread appears to be {theme}.",
    "Throughout the cycle, {theme} may have been a central consideration.",
    "It looks like {theme} remained present across multiple reflections.",
]

PERSPECTIVE_SHIFT_TEMPLATES = [
    "Across different gates, your perspective appears to have shifted between {shift}.",
    "There may have been movement between {shift} throughout the cycle.",
    "Your reflections seem to show a journey between {shift}.",
    "It looks like your view evolved, moving between {shift}.",
]

CLARITY_TEMPLATES = {
    "increasing": [
        "Clarity appears to have grown as the cycle progressed.",
        "Your later entries seem to carry more certainty than earlier ones.",
        "There may be a sense of things becoming clearer over time.",
    ],
    "decreasing": [
        "The cycle seems to have brought more questions than answers.",
        "Complexity may have increased as you explored different perspectives.",
        "Your reflections appear to show deepening inquiry rather than resolution.",
    ],
    "mixed": [
        "Clarity seems to have ebbed and flowed across the cycle.",
        "Some aspects may have become clearer while others remained uncertain.",
        "The cycle appears to have revealed both answers and new questions.",
    ],
    "stable": [
        "Your perspective appears to have remained relatively consistent.",
        "There seems to be a steady thread of knowing throughout.",
        "Your clarity may have stayed present across different gates.",
    ],
}

GATE_REFLECTION_TEMPLATES = [
    "Your strongest reflections appear to have come during Gate {gate} ({title}).",
    "Gate {gate} ({title}) seems to have sparked particularly deep consideration.",
    "The energy of Gate {gate} ({title}) may have been especially significant.",
]

SUMMARY_TEMPLATES = [
    "Looking at this lunar cycle as a whole, it appears that {summary}",
    "Across these {count} days of observation, {summary}",
    "This cycle seems to have been about {summary}",
]

SUGGESTED_QUESTIONS = [
    "Looking back across this lunar cycle, what now feels most reliable to act on?",
    "What feels clearer now than it did at the beginning of the cycle?",
    "Which perspective from this cycle seems most trustworthy?",
    "What has this cycle of observation revealed that you can now trust?",
    "Having moved through these different gates, what understanding remains steady?",
]

# =============================================================================
# THEME AND KEYWORD DETECTION
# =============================================================================

THEME_KEYWORDS = {
    "growth": ["grow", "expand", "develop", "progress", "forward", "evolve", "change"],
    "caution": ["careful", "wait", "hesitate", "uncertain", "pause", "slow", "consider"],
    "readiness": ["ready", "prepared", "time", "now", "move", "act", "decision"],
    "fear": ["afraid", "worry", "anxious", "scared", "nervous", "doubt"],
    "excitement": ["excited", "eager", "anticipate", "looking forward", "energy"],
    "clarity": ["clear", "understand", "see", "realize", "know", "certain"],
    "confusion": ["confused", "unsure", "unclear", "don't know", "mixed", "conflicted"],
    "connection": ["connect", "relationship", "belong", "community", "together"],
    "independence": ["alone", "independent", "self", "own", "separate", "individual"],
    "security": ["safe", "secure", "stable", "grounded", "settled", "comfortable"],
    "adventure": ["adventure", "new", "explore", "discover", "unknown", "risk"],
    "rest": ["rest", "peace", "calm", "quiet", "still", "pause", "slow down"],
    "action": ["do", "make", "create", "build", "start", "begin", "move"],
}

EMOTIONAL_MARKERS = {
    "positive": ["happy", "hopeful", "excited", "grateful", "peaceful", "confident", "light", "open"],
    "negative": ["heavy", "worried", "sad", "frustrated", "stuck", "afraid", "confused", "resistant"],
    "neutral": ["notice", "observe", "see", "wonder", "curious", "interesting"],
}


# =============================================================================
# ANALYSIS FUNCTIONS
# =============================================================================

def extract_themes(entries: List[Dict]) -> Dict[str, int]:
    """Extract themes from entry content based on keyword matching."""
    theme_counts = Counter()
    
    for entry in entries:
        content = entry.get("content", "").lower()
        
        for theme, keywords in THEME_KEYWORDS.items():
            for keyword in keywords:
                if keyword in content:
                    theme_counts[theme] += 1
                    break  # Count each theme once per entry
    
    return dict(theme_counts)


def detect_emotional_tone(entries: List[Dict]) -> Dict[str, List[int]]:
    """Detect emotional tone across entries by lunar day."""
    tone_by_day = {}
    
    for entry in entries:
        content = entry.get("content", "").lower()
        day = int(entry.get("lunar_day", 0))
        
        # Score: positive=1, negative=-1, neutral=0
        score = 0
        for marker in EMOTIONAL_MARKERS["positive"]:
            if marker in content:
                score += 1
        for marker in EMOTIONAL_MARKERS["negative"]:
            if marker in content:
                score -= 1
        
        if day not in tone_by_day:
            tone_by_day[day] = []
        tone_by_day[day].append(score)
    
    return tone_by_day


def analyze_clarity_trend(entries: List[Dict]) -> str:
    """Analyze whether clarity increased, decreased, or remained mixed."""
    if len(entries) < 2:
        return "stable"
    
    # Sort entries by lunar day
    sorted_entries = sorted(entries, key=lambda e: e.get("lunar_day", 0))
    
    # Check for clarity keywords in early vs late entries
    early_count = len(sorted_entries) // 3 or 1
    late_count = len(sorted_entries) // 3 or 1
    
    early_entries = sorted_entries[:early_count]
    late_entries = sorted_entries[-late_count:]
    
    clarity_keywords = ["clear", "certain", "know", "understand", "see", "realize", "decided"]
    confusion_keywords = ["unsure", "unclear", "confused", "don't know", "uncertain", "question"]
    
    def clarity_score(text):
        text = text.lower()
        score = 0
        for kw in clarity_keywords:
            if kw in text:
                score += 1
        for kw in confusion_keywords:
            if kw in text:
                score -= 1
        return score
    
    early_score = sum(clarity_score(e.get("content", "")) for e in early_entries)
    late_score = sum(clarity_score(e.get("content", "")) for e in late_entries)
    
    diff = late_score - early_score
    
    if diff > 1:
        return "increasing"
    elif diff < -1:
        return "decreasing"
    elif abs(diff) <= 1 and len(entries) > 3:
        return "mixed"
    else:
        return "stable"


def find_notable_gates(entries: List[Dict]) -> List[Dict]:
    """Find gates with the most substantive entries."""
    gate_data = {}
    
    for entry in entries:
        gate = entry.get("moon_gate")
        if not gate:
            continue
        
        content = entry.get("content", "")
        
        if gate not in gate_data:
            gate_data[gate] = {
                "gate": gate,
                "title": entry.get("gate_title", ""),
                "entry_count": 0,
                "total_length": 0,
            }
        
        gate_data[gate]["entry_count"] += 1
        gate_data[gate]["total_length"] += len(content)
    
    # Score gates by entry count and content length
    for gate in gate_data.values():
        gate["score"] = gate["entry_count"] * 10 + gate["total_length"] // 50
    
    # Sort by score and return top 3
    sorted_gates = sorted(gate_data.values(), key=lambda g: g["score"], reverse=True)
    return sorted_gates[:3]


def detect_perspective_shifts(themes: Dict[str, int], entries: List[Dict]) -> Optional[str]:
    """Detect what perspective shifts occurred across the cycle."""
    if not themes:
        return None
    
    # Look for opposing themes
    opposing_pairs = [
        ("caution", "readiness"),
        ("fear", "excitement"),
        ("clarity", "confusion"),
        ("security", "adventure"),
        ("rest", "action"),
        ("connection", "independence"),
    ]
    
    for theme_a, theme_b in opposing_pairs:
        if themes.get(theme_a, 0) >= 1 and themes.get(theme_b, 0) >= 1:
            return f"{theme_a} and {theme_b}"
    
    # If no opposing themes, just describe the top themes
    top_themes = sorted(themes.items(), key=lambda x: x[1], reverse=True)[:2]
    if len(top_themes) >= 2:
        return f"{top_themes[0][0]} and {top_themes[1][0]}"
    
    return None


# =============================================================================
# MAIN SYNTHESIS FUNCTION
# =============================================================================

async def generate_lunar_cycle_synthesis(
    db,
    user_id: str,
    consideration_id: str
) -> Dict[str, Any]:
    """
    Generate an observational synthesis of the user's lunar cycle entries.
    
    This analyzes journal entries and produces a Mirror-language summary
    of patterns, shifts, and notable moments across the cycle.
    """
    import random
    
    logger.info(f"[LunarSynthesis] Generating synthesis for user {user_id[:8]}, consideration {consideration_id[:8]}")
    
    try:
        # Fetch entries for this consideration
        entries = await db.lunar_journal.find({
            "user_id": user_id,
            "consideration_id": consideration_id,
        }).sort("lunar_day", 1).to_list(length=100)
        
        if not entries:
            logger.info("[LunarSynthesis] No entries found for synthesis")
            return {
                "success": True,
                "has_synthesis": False,
                "message": "Not enough entries to generate a synthesis.",
            }
        
        # Fetch the consideration topic
        from bson import ObjectId
        consideration = await db.lunar_considerations.find_one({
            "_id": ObjectId(consideration_id),
        })
        topic = consideration.get("topic", "this consideration") if consideration else "this consideration"
        
        # Run analysis
        themes = extract_themes(entries)
        clarity_trend = analyze_clarity_trend(entries)
        notable_gates = find_notable_gates(entries)
        perspective_shifts = detect_perspective_shifts(themes, entries)
        emotional_tones = detect_emotional_tone(entries)
        
        # Generate synthesis components
        synthesis = {
            "success": True,
            "has_synthesis": True,
            "consideration_topic": topic,
            "entry_count": len(entries),
            "days_observed": len(set(int(e.get("lunar_day", 0)) for e in entries)),
        }
        
        # 1. Consistent theme
        if themes:
            top_theme = max(themes.items(), key=lambda x: x[1])[0]
            template = random.choice(CONSISTENT_THEME_TEMPLATES)
            synthesis["consistent_theme"] = template.format(theme=top_theme)
            synthesis["top_themes"] = list(themes.keys())[:3]
        else:
            synthesis["consistent_theme"] = "Your reflections appear to have touched on many different aspects."
            synthesis["top_themes"] = []
        
        # 2. Perspective shifts
        if perspective_shifts:
            template = random.choice(PERSPECTIVE_SHIFT_TEMPLATES)
            synthesis["perspective_shifts"] = template.format(shift=perspective_shifts)
        else:
            synthesis["perspective_shifts"] = "Your perspective may have remained relatively steady across the cycle."
        
        # 3. Clarity trend
        templates = CLARITY_TEMPLATES.get(clarity_trend, CLARITY_TEMPLATES["mixed"])
        synthesis["clarity_trend"] = random.choice(templates)
        synthesis["clarity_direction"] = clarity_trend
        
        # 4. Notable gates
        if notable_gates:
            primary_gate = notable_gates[0]
            template = random.choice(GATE_REFLECTION_TEMPLATES)
            synthesis["notable_gate_text"] = template.format(
                gate=primary_gate["gate"],
                title=primary_gate["title"]
            )
            synthesis["notable_gates"] = [
                {"gate": g["gate"], "title": g["title"], "entry_count": g["entry_count"]}
                for g in notable_gates
            ]
        else:
            synthesis["notable_gate_text"] = "Your reflections were distributed across the cycle."
            synthesis["notable_gates"] = []
        
        # 5. Overall summary
        summary_parts = []
        if themes:
            top_theme = max(themes.items(), key=lambda x: x[1])[0]
            summary_parts.append(f"your exploration of {top_theme}")
        if perspective_shifts:
            summary_parts.append(f"movement between {perspective_shifts}")
        
        if summary_parts:
            summary = " and ".join(summary_parts) + " may have been central to this cycle"
            template = random.choice(SUMMARY_TEMPLATES)
            synthesis["reflection_summary"] = template.format(
                summary=summary,
                count=len(entries)
            )
        else:
            synthesis["reflection_summary"] = f"This cycle of {len(entries)} reflections appears to have been a time of observation and inquiry."
        
        # 6. Suggested question
        synthesis["suggested_question"] = random.choice(SUGGESTED_QUESTIONS)
        
        logger.info(f"[LunarSynthesis] Generated synthesis with {len(entries)} entries, top themes: {list(themes.keys())[:3]}")
        
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
    consideration_id: str
) -> Optional[Dict[str, Any]]:
    """
    Get cached synthesis for a consideration, or generate and cache if not exists.
    """
    from bson import ObjectId
    
    try:
        # Check for cached synthesis
        cached = await db.lunar_synthesis_cache.find_one({
            "user_id": user_id,
            "consideration_id": consideration_id,
        })
        
        if cached:
            logger.info(f"[LunarSynthesis] Returning cached synthesis for {consideration_id[:8]}")
            # Return cached data (excluding MongoDB _id)
            return {k: v for k, v in cached.items() if k != "_id"}
        
        # Generate new synthesis
        synthesis = await generate_lunar_cycle_synthesis(db, user_id, consideration_id)
        
        if synthesis.get("success") and synthesis.get("has_synthesis"):
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
