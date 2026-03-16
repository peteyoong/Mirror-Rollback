"""
Lifeline Pattern Synthesis - Task 56

Analyzes the user's lifeline events to identify recurring life arcs, 
themes, clusters, and patterns across major turning points.

This transforms lifeline data from a simple timeline into pattern awareness.
Uses Mirror language for observational, non-predictive insights.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
from collections import Counter, defaultdict

logger = logging.getLogger(__name__)

# =============================================================================
# PATTERN ARC DEFINITIONS
# =============================================================================

# Common life pattern arcs
PATTERN_ARCS = [
    {
        "name": "Ambition → Pressure → Transformation",
        "triggers": [
            (["Career", "Achievement"], ["Loss", "Health", "Turning Point"], ["Career", "Identity", "Achievement"]),
        ],
        "themes": ["ambition", "growth", "career", "reinvention"],
    },
    {
        "name": "Expansion → Crisis → Redirection",
        "triggers": [
            (["Career", "Achievement", "Move"], ["Loss", "Health", "Turning Point"], ["Career", "Move", "Identity"]),
        ],
        "themes": ["expansion", "crisis", "change"],
    },
    {
        "name": "Identity Search → Breakthrough → Expression",
        "triggers": [
            (["Identity", "Spirituality"], ["Achievement", "Turning Point"], ["Career", "Identity", "Achievement"]),
        ],
        "themes": ["identity", "growth", "expression"],
    },
    {
        "name": "Connection → Loss → Rebuilding",
        "triggers": [
            (["Relationships", "Family"], ["Loss", "Turning Point"], ["Relationships", "Family", "Identity"]),
        ],
        "themes": ["relationships", "loss", "healing"],
    },
    {
        "name": "Stability → Disruption → Growth",
        "triggers": [
            (["Career", "Family", "Relationships"], ["Loss", "Health", "Move", "Turning Point"], ["Achievement", "Career", "Identity"]),
        ],
        "themes": ["stability", "change", "growth"],
    },
    {
        "name": "Risk → Challenge → Mastery",
        "triggers": [
            (["Career", "Move"], ["Turning Point", "Health"], ["Achievement", "Career"]),
        ],
        "themes": ["risk", "challenge", "mastery"],
    },
]

# Theme keywords to detect from tags and descriptions
THEME_KEYWORDS = {
    "growth": ["grow", "growth", "develop", "expand", "learn", "progress"],
    "reinvention": ["reinvent", "transform", "change", "new direction", "pivot", "restart"],
    "leadership": ["lead", "leader", "leadership", "manage", "team", "mentor"],
    "crisis": ["crisis", "difficult", "struggle", "challenge", "hard", "breakdown"],
    "healing": ["heal", "recover", "therapy", "support", "grief"],
    "relationships": ["relationship", "partner", "married", "divorce", "dating", "love"],
    "career": ["career", "job", "work", "profession", "business", "company", "promotion"],
    "identity": ["identity", "who am i", "purpose", "meaning", "self"],
    "family": ["family", "parent", "child", "mother", "father", "sibling"],
    "ambition": ["ambition", "goal", "dream", "aspiration", "achieve"],
    "transition": ["transition", "move", "change", "shift", "turning point"],
    "pressure": ["pressure", "stress", "overwhelm", "burnout", "intense"],
    "expansion": ["expand", "new", "opportunity", "venture", "start"],
    "loss": ["loss", "lost", "grief", "death", "end", "gone"],
    "breakthrough": ["breakthrough", "realize", "discovery", "clarity", "insight"],
}

# Emotional trajectory patterns
EMOTIONAL_TRAJECTORIES = {
    "difficult_to_growth": {
        "pattern": ["negative", "mixed", "positive"],
        "description": "Your moments often moved from difficulty toward growth."
    },
    "mixed_to_clarity": {
        "pattern": ["mixed", "positive"],
        "description": "Several turning points seem to have moved from uncertainty toward clarity."
    },
    "pressure_to_expansion": {
        "pattern": ["negative", "positive"],
        "description": "Periods of pressure appear to have preceded expansion in your life."
    },
    "growth_through_challenge": {
        "pattern": ["negative", "positive", "positive"],
        "description": "Challenge seems to have been a catalyst for sustained growth."
    },
    "cyclic_renewal": {
        "pattern": ["positive", "negative", "positive"],
        "description": "Your timeline shows a pattern of renewal after periods of difficulty."
    },
}

# =============================================================================
# MIRROR LANGUAGE TEMPLATES
# =============================================================================

CLUSTER_TEMPLATES = [
    "Several important events appear concentrated during this period.",
    "This period seems to have held multiple significant moments.",
    "A cluster of turning points may have occurred during these years.",
]

ARC_TEMPLATES = [
    "This arc appears across several of your turning points.",
    "This pattern seems to emerge from your timeline.",
    "This sequence may be present in your life story.",
]

SUMMARY_TEMPLATES = [
    "Across several turning points, it appears that {pattern}.",
    "Looking at your timeline, it seems that {pattern}.",
    "Your life moments may suggest that {pattern}.",
]

REFLECTION_QUESTIONS = [
    "Looking across these moments, what pattern do you recognise in how your life changes?",
    "What thread seems to connect these turning points?",
    "How does this pattern feel when you see it reflected back?",
    "What might these moments be teaching you about how you navigate change?",
]


# =============================================================================
# ANALYSIS FUNCTIONS
# =============================================================================

def extract_themes_from_event(event: Dict) -> List[str]:
    """Extract themes from an event's category, tags, and description."""
    themes = []
    
    # From category
    category = event.get("category", "")
    if category:
        category_lower = category.lower()
        for theme, keywords in THEME_KEYWORDS.items():
            if category_lower in [k.lower() for k in keywords] or theme in category_lower:
                themes.append(theme)
    
    # From tags
    tags = event.get("tags", [])
    for tag in tags:
        tag_lower = tag.lower()
        for theme, keywords in THEME_KEYWORDS.items():
            for keyword in keywords:
                if keyword in tag_lower:
                    themes.append(theme)
                    break
    
    # From description
    description = event.get("description", "") or ""
    desc_lower = description.lower()
    for theme, keywords in THEME_KEYWORDS.items():
        for keyword in keywords:
            if keyword in desc_lower:
                themes.append(theme)
                break
    
    return list(set(themes))


def detect_event_clusters(events: List[Dict]) -> List[Dict]:
    """Detect periods where multiple events occurred close together."""
    clusters = []
    
    # Filter events with years
    dated_events = [e for e in events if e.get("year")]
    if len(dated_events) < 3:
        return clusters
    
    # Sort by year
    sorted_events = sorted(dated_events, key=lambda e: e["year"])
    
    # Find clusters (3+ events within 3 years)
    i = 0
    while i < len(sorted_events) - 2:
        cluster_events = [sorted_events[i]]
        j = i + 1
        
        while j < len(sorted_events) and sorted_events[j]["year"] - cluster_events[0]["year"] <= 3:
            cluster_events.append(sorted_events[j])
            j += 1
        
        if len(cluster_events) >= 3:
            start_year = cluster_events[0]["year"]
            end_year = cluster_events[-1]["year"]
            
            clusters.append({
                "years": f"{start_year}–{end_year}" if start_year != end_year else str(start_year),
                "event_count": len(cluster_events),
                "events": [e.get("title", "Event") for e in cluster_events],
                "description": CLUSTER_TEMPLATES[len(clusters) % len(CLUSTER_TEMPLATES)],
            })
            
            i = j  # Skip past this cluster
        else:
            i += 1
    
    return clusters[:3]  # Return max 3 clusters


def detect_pattern_arcs(events: List[Dict]) -> List[Dict]:
    """Detect life pattern arcs across sequences of events."""
    detected_arcs = []
    
    # Sort events by year
    dated_events = [e for e in events if e.get("year")]
    if len(dated_events) < 3:
        return detected_arcs
    
    sorted_events = sorted(dated_events, key=lambda e: e["year"])
    
    # Check each arc pattern
    for arc_def in PATTERN_ARCS:
        for trigger_sequence in arc_def["triggers"]:
            phase_1, phase_2, phase_3 = trigger_sequence
            
            # Try to find a matching sequence in events
            for i in range(len(sorted_events) - 2):
                e1_cat = sorted_events[i].get("category", "")
                e2_cat = sorted_events[i + 1].get("category", "")
                e3_cat = sorted_events[i + 2].get("category", "")
                
                if (e1_cat in phase_1 and 
                    e2_cat in phase_2 and 
                    e3_cat in phase_3):
                    
                    detected_arcs.append({
                        "arc": arc_def["name"],
                        "events_involved": [
                            sorted_events[i].get("title", "Event 1"),
                            sorted_events[i + 1].get("title", "Event 2"),
                            sorted_events[i + 2].get("title", "Event 3"),
                        ],
                        "years": f"{sorted_events[i].get('year')}–{sorted_events[i + 2].get('year')}",
                    })
                    break  # Only one match per arc type
            
            if len(detected_arcs) > 0 and detected_arcs[-1]["arc"] == arc_def["name"]:
                break  # Move to next arc pattern
    
    return detected_arcs[:3]  # Max 3 arcs


def analyze_emotional_trajectory(events: List[Dict]) -> Optional[Dict]:
    """Analyze the emotional trajectory across events."""
    dated_events = [e for e in events if e.get("year") and e.get("emotional_tone")]
    if len(dated_events) < 3:
        return None
    
    sorted_events = sorted(dated_events, key=lambda e: e["year"])
    tones = [e.get("emotional_tone", "neutral") for e in sorted_events]
    
    # Check for trajectory patterns
    for traj_name, traj_def in EMOTIONAL_TRAJECTORIES.items():
        pattern = traj_def["pattern"]
        
        # Sliding window match
        for i in range(len(tones) - len(pattern) + 1):
            window = tones[i:i + len(pattern)]
            if window == pattern:
                return {
                    "pattern": traj_name,
                    "description": traj_def["description"],
                }
    
    # If no exact match, describe the general trend
    positive_count = tones.count("positive")
    negative_count = tones.count("negative")
    
    if positive_count > negative_count * 2:
        return {"pattern": "growth_oriented", "description": "Your turning points appear to carry mostly positive energy."}
    elif negative_count > positive_count * 2:
        return {"pattern": "challenge_oriented", "description": "Your timeline seems to include many challenging moments that may have shaped you."}
    else:
        return {"pattern": "mixed", "description": "Your turning points show a mix of challenging and affirming moments."}


def identify_recurring_themes(events: List[Dict]) -> List[str]:
    """Identify recurring themes across all events."""
    all_themes = []
    
    for event in events:
        themes = extract_themes_from_event(event)
        all_themes.extend(themes)
    
    # Count and filter
    theme_counts = Counter(all_themes)
    
    # Return themes that appear in at least 2 events
    recurring = [theme for theme, count in theme_counts.most_common() if count >= 2]
    
    return recurring[:5]  # Top 5 recurring themes


def identify_major_turning_points(events: List[Dict]) -> List[Dict]:
    """Identify events with high impact scores (8-10)."""
    major = []
    
    for event in events:
        impact = event.get("impact_score", 5)
        if impact >= 8:
            major.append({
                "title": event.get("title", "Major Event"),
                "year": event.get("year"),
                "impact": impact,
                "category": event.get("category"),
            })
    
    return sorted(major, key=lambda e: e.get("impact", 0), reverse=True)[:5]


def generate_life_pattern_summary(
    arcs: List[Dict],
    themes: List[str],
    clusters: List[Dict],
    emotional: Optional[Dict]
) -> str:
    """Generate a summary insight about the user's life patterns."""
    import random
    
    summary_parts = []
    
    # From arcs
    if arcs:
        arc_name = arcs[0]["arc"].lower()
        summary_parts.append(f"sequences of {arc_name.split(' → ')[0].lower()} often lead to {arc_name.split(' → ')[-1].lower()}")
    
    # From themes
    if len(themes) >= 2:
        summary_parts.append(f"{themes[0]} and {themes[1]} appear as recurring threads")
    
    # From emotional trajectory
    if emotional:
        if "growth" in emotional.get("description", "").lower():
            summary_parts.append("difficult moments often precede growth")
        elif "challenge" in emotional.get("description", "").lower():
            summary_parts.append("you have navigated significant challenges")
    
    if not summary_parts:
        return "Your turning points form a unique pattern that reflects your individual journey."
    
    pattern = " and ".join(summary_parts[:2])
    template = random.choice(SUMMARY_TEMPLATES)
    
    return template.format(pattern=pattern)


# =============================================================================
# MAIN SYNTHESIS FUNCTION
# =============================================================================

async def generate_lifeline_pattern_synthesis(
    db,
    user_id: str
) -> Dict[str, Any]:
    """
    Generate a pattern synthesis of the user's lifeline events.
    
    Analyzes turning points to identify arcs, themes, clusters, and patterns.
    Returns Mirror-language observations about life patterns.
    """
    import random
    
    logger.info(f"[LifelineSynthesis] Generating synthesis for user {user_id[:8]}...")
    
    try:
        # Fetch lifeline events
        events = await db.lifeline_events.find({
            "user_id": user_id
        }).sort("year", 1).to_list(length=500)
        
        if len(events) < 5:
            logger.info(f"[LifelineSynthesis] Not enough events ({len(events)}) for synthesis")
            return {
                "success": True,
                "has_synthesis": False,
                "event_count": len(events),
                "minimum_required": 5,
                "message": "Add more turning points to reveal patterns in your timeline.",
            }
        
        # Run all analysis
        major_turning_points = identify_major_turning_points(events)
        pattern_arcs = detect_pattern_arcs(events)
        recurring_themes = identify_recurring_themes(events)
        cluster_periods = detect_event_clusters(events)
        emotional_pattern = analyze_emotional_trajectory(events)
        
        # Generate summary
        life_pattern_summary = generate_life_pattern_summary(
            pattern_arcs, recurring_themes, cluster_periods, emotional_pattern
        )
        
        # Build synthesis result
        synthesis = {
            "success": True,
            "has_synthesis": True,
            "event_count": len(events),
            "major_turning_points": len(major_turning_points),
            "major_events": major_turning_points,
            "pattern_arcs": pattern_arcs,
            "recurring_themes": recurring_themes,
            "cluster_periods": cluster_periods,
            "emotional_pattern": emotional_pattern.get("description") if emotional_pattern else None,
            "life_pattern_summary": life_pattern_summary,
            "reflection_question": random.choice(REFLECTION_QUESTIONS),
        }
        
        # Calculate year range
        dated_events = [e for e in events if e.get("year")]
        if dated_events:
            years = [e["year"] for e in dated_events]
            synthesis["year_range"] = {
                "start": min(years),
                "end": max(years),
                "span": max(years) - min(years),
            }
        
        logger.info(f"[LifelineSynthesis] Generated synthesis: {len(pattern_arcs)} arcs, {len(recurring_themes)} themes")
        
        return synthesis
        
    except Exception as e:
        logger.error(f"[LifelineSynthesis] Error generating synthesis: {e}")
        return {
            "success": False,
            "error": str(e),
        }


async def get_cached_lifeline_synthesis(
    db,
    user_id: str
) -> Dict[str, Any]:
    """
    Get cached synthesis or generate new one.
    Cache is invalidated when new events are added.
    """
    try:
        # Check for cached synthesis
        cached = await db.lifeline_synthesis_cache.find_one({
            "user_id": user_id,
        })
        
        # Get latest event timestamp
        latest_event = await db.lifeline_events.find_one(
            {"user_id": user_id},
            sort=[("updated_at", -1)]
        )
        
        if cached:
            cache_time = cached.get("created_at")
            event_time = latest_event.get("updated_at") if latest_event else None
            
            # If cache is newer than latest event, use cache
            if cache_time and event_time and cache_time > event_time:
                logger.info(f"[LifelineSynthesis] Returning cached synthesis")
                return {k: v for k, v in cached.items() if k != "_id"}
        
        # Generate new synthesis
        synthesis = await generate_lifeline_pattern_synthesis(db, user_id)
        
        if synthesis.get("success") and synthesis.get("has_synthesis"):
            # Update or insert cache
            cache_doc = {
                "user_id": user_id,
                "created_at": datetime.now(timezone.utc),
                **synthesis,
            }
            
            await db.lifeline_synthesis_cache.update_one(
                {"user_id": user_id},
                {"$set": cache_doc},
                upsert=True
            )
            logger.info(f"[LifelineSynthesis] Cached new synthesis")
        
        return synthesis
        
    except Exception as e:
        logger.error(f"[LifelineSynthesis] Error getting/caching synthesis: {e}")
        return await generate_lifeline_pattern_synthesis(db, user_id)
