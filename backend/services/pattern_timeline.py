"""
Personal Pattern Timeline Service

Aggregates weekly pattern summaries across multiple weeks to build
a longitudinal view of pattern history. Follows Mirror philosophy:
- Show pattern movement, not prediction
- Emphasize continuity and cycles
- Deterministic aggregation
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)

# Pattern domains for reference
PATTERN_DOMAINS = [
    "energy_vitality",
    "emotional_landscape", 
    "identity_direction",
    "mind_meaning",
    "expression_action",
    "relationships_boundaries",
    "growth_transformation"
]

DOMAIN_NAMES = {
    "energy_vitality": "Energy & Vitality",
    "emotional_landscape": "Emotional Landscape",
    "identity_direction": "Identity & Direction",
    "mind_meaning": "Mind & Meaning",
    "expression_action": "Expression & Action",
    "relationships_boundaries": "Relationships & Boundaries",
    "growth_transformation": "Growth & Transformation"
}

# Timeline reflection prompts
TIMELINE_REFLECTION_PROMPTS = [
    "Which pattern has returned in different forms over time?",
    "What has remained consistent across these weeks?",
    "What seems to cycle back, even when other things change?",
    "Where has your attention kept returning?",
    "What theme has accompanied you through this period?",
    "What pattern feels most familiar when you look back?",
    "What has gently persisted across the weeks?"
]


def transform_weekly_to_timeline_entry(weekly_summary: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform a weekly summary into a timeline-friendly entry.
    
    Args:
        weekly_summary: Output from weekly synthesis service
        
    Returns:
        Simplified timeline entry
    """
    top_domains = weekly_summary.get("top_domains", [])
    
    # Get top domain
    top_domain = top_domains[0]["domain"] if top_domains else None
    top_domain_id = top_domains[0]["domain_id"] if top_domains else None
    
    # Get secondary domains (positions 2 and 3)
    secondary_domains = [d["domain"] for d in top_domains[1:3]]
    secondary_domain_ids = [d["domain_id"] for d in top_domains[1:3]]
    
    # Build trend map for top 3
    trend_map = {}
    for d in top_domains[:3]:
        trend_map[d["domain"]] = d.get("trend", "steady")
    
    # Get timing amplified domains
    timing_amplified = [
        d["domain"] for d in top_domains[:3]
        if d.get("timing_amplified", False)
    ]
    
    return {
        "week_start": weekly_summary.get("week_start"),
        "week_end": weekly_summary.get("week_end"),
        "top_domain": top_domain,
        "top_domain_id": top_domain_id,
        "secondary_domains": secondary_domains,
        "secondary_domain_ids": secondary_domain_ids,
        "trend_map": trend_map,
        "timing_amplified_domains": timing_amplified,
        "narrative": weekly_summary.get("narrative", ""),
        "reflection_prompt": weekly_summary.get("reflection_prompt", "")
    }


def calculate_timeline_insights(
    timeline_entries: List[Dict[str, Any]]
) -> Dict[str, Optional[str]]:
    """
    Calculate cross-week insights from timeline entries.
    
    Args:
        timeline_entries: List of timeline entries (oldest first)
        
    Returns:
        Dict of insight labels
    """
    if not timeline_entries:
        return {
            "most_recurring_domain": None,
            "strongest_recent_domain": None,
            "volatile_domain": None,
            "stable_domain": None,
            "reemerging_domain": None
        }
    
    # Track domain appearances
    domain_appearances: Dict[str, int] = defaultdict(int)
    domain_trends: Dict[str, List[str]] = defaultdict(list)
    domain_weeks_present: Dict[str, List[int]] = defaultdict(list)
    
    for week_idx, entry in enumerate(timeline_entries):
        # Count appearances in top 3
        if entry.get("top_domain"):
            domain_appearances[entry["top_domain"]] += 3  # Weight for #1
            domain_trends[entry["top_domain"]].append(
                entry.get("trend_map", {}).get(entry["top_domain"], "steady")
            )
            domain_weeks_present[entry["top_domain"]].append(week_idx)
        
        for domain in entry.get("secondary_domains", []):
            domain_appearances[domain] += 1
            domain_trends[domain].append(
                entry.get("trend_map", {}).get(domain, "steady")
            )
            domain_weeks_present[domain].append(week_idx)
    
    # 1. Most recurring domain (appears most in top 3 overall)
    most_recurring = None
    if domain_appearances:
        most_recurring = max(domain_appearances, key=domain_appearances.get)
    
    # 2. Strongest recent domain (weighted by recency - last 3 weeks)
    recent_appearances: Dict[str, float] = defaultdict(float)
    recent_count = min(3, len(timeline_entries))
    for i, entry in enumerate(timeline_entries[-recent_count:]):
        weight = 1.0 + (i * 0.5)  # More recent = higher weight
        if entry.get("top_domain"):
            recent_appearances[entry["top_domain"]] += 3 * weight
        for domain in entry.get("secondary_domains", []):
            recent_appearances[domain] += 1 * weight
    
    strongest_recent = None
    if recent_appearances:
        strongest_recent = max(recent_appearances, key=recent_appearances.get)
    
    # 3. Volatile domain (trend changes most)
    volatile = None
    max_changes = 0
    for domain, trends in domain_trends.items():
        if len(trends) < 2:
            continue
        changes = sum(1 for i in range(1, len(trends)) if trends[i] != trends[i-1])
        if changes > max_changes:
            max_changes = changes
            volatile = domain
    
    # 4. Stable domain (consistent "steady" or repeated presence)
    stable = None
    max_steady_count = 0
    for domain, trends in domain_trends.items():
        steady_count = sum(1 for t in trends if t == "steady")
        if steady_count > max_steady_count and len(trends) >= 2:
            max_steady_count = steady_count
            stable = domain
    
    # 5. Re-emerging domain (absent 2+ weeks, then reappears in recent 2)
    reemerging = None
    total_weeks = len(timeline_entries)
    if total_weeks >= 4:
        for domain, weeks in domain_weeks_present.items():
            if len(weeks) < 2:
                continue
            
            # Check for gap followed by recent presence
            weeks_set = set(weeks)
            recent_present = (total_weeks - 1) in weeks_set or (total_weeks - 2) in weeks_set
            
            # Check for gap of 2+ weeks somewhere before
            has_gap = False
            for i in range(len(weeks) - 1):
                if weeks[i+1] - weeks[i] >= 2:
                    has_gap = True
                    break
            
            if recent_present and has_gap:
                reemerging = domain
                break
    
    return {
        "most_recurring_domain": most_recurring,
        "strongest_recent_domain": strongest_recent,
        "volatile_domain": volatile,
        "stable_domain": stable,
        "reemerging_domain": reemerging
    }


def generate_timeline_narrative(
    insights: Dict[str, Optional[str]],
    timeline_entries: List[Dict[str, Any]]
) -> str:
    """
    Generate a narrative summary for the timeline.
    
    Args:
        insights: Cross-week insights
        timeline_entries: List of timeline entries
        
    Returns:
        Narrative string
    """
    if not timeline_entries:
        return "Your pattern timeline is still taking shape. As more weekly patterns accumulate, themes will emerge here."
    
    if len(timeline_entries) < 3:
        return "A few weeks of patterns have begun to form. As more time passes, longer threads will become visible."
    
    parts = []
    
    # Most recurring
    recurring = insights.get("most_recurring_domain")
    if recurring:
        recurring_lower = recurring.lower()
        parts.append(f"Across recent weeks, {recurring_lower} themes appear to have remained present")
    
    # Volatile/shifting
    volatile = insights.get("volatile_domain")
    stable = insights.get("stable_domain")
    
    if volatile and stable and volatile != stable:
        volatile_lower = volatile.lower()
        stable_lower = stable.lower()
        parts.append(f"while {volatile_lower} patterns shifted more noticeably")
    elif volatile:
        volatile_lower = volatile.lower()
        parts.append(f"while {volatile_lower} patterns have shifted across the weeks")
    
    # Re-emerging
    reemerging = insights.get("reemerging_domain")
    if reemerging and reemerging != recurring:
        reemerging_lower = reemerging.lower()
        parts.append(f"with {reemerging_lower} themes appearing to return recently")
    
    if not parts:
        return "Patterns have been forming across recent weeks. Some themes have held steady while others have shifted."
    
    # Join parts
    narrative = parts[0]
    if len(parts) > 1:
        narrative += ", " + parts[1]
    if len(parts) > 2:
        narrative += ", " + parts[2]
    narrative += "."
    
    return narrative


def select_timeline_reflection_prompt(weeks_count: int) -> str:
    """
    Select a reflection prompt based on timeline length.
    """
    hash_val = weeks_count * 7
    prompt_idx = hash_val % len(TIMELINE_REFLECTION_PROMPTS)
    return TIMELINE_REFLECTION_PROMPTS[prompt_idx]


def generate_pattern_timeline(
    weekly_summaries: List[Dict[str, Any]],
    weeks_count: int = 8
) -> Dict[str, Any]:
    """
    Main function to generate the pattern timeline from weekly summaries.
    
    Args:
        weekly_summaries: List of weekly summary objects (oldest first)
        weeks_count: Number of weeks requested
        
    Returns:
        Timeline JSON contract
    """
    # Handle empty or insufficient data
    if not weekly_summaries:
        return {
            "range_label": f"Last {weeks_count} weeks",
            "weeks": [],
            "insights": {
                "most_recurring_domain": None,
                "strongest_recent_domain": None,
                "volatile_domain": None,
                "stable_domain": None,
                "reemerging_domain": None
            },
            "narrative_summary": "Your pattern timeline is still taking shape. As more weekly patterns accumulate, a longer view of recurring themes will appear here.",
            "reflection_prompt": select_timeline_reflection_prompt(0),
            "is_partial": True,
            "weeks_available": 0
        }
    
    # Transform each weekly summary to timeline entry
    timeline_entries = [
        transform_weekly_to_timeline_entry(summary)
        for summary in weekly_summaries
    ]
    
    # Calculate cross-week insights
    insights = calculate_timeline_insights(timeline_entries)
    
    # Generate narrative
    narrative = generate_timeline_narrative(insights, timeline_entries)
    
    # Select reflection prompt
    reflection_prompt = select_timeline_reflection_prompt(len(timeline_entries))
    
    # Determine if partial
    is_partial = len(timeline_entries) < weeks_count
    
    return {
        "range_label": f"Last {weeks_count} weeks",
        "weeks": timeline_entries,
        "insights": insights,
        "narrative_summary": narrative,
        "reflection_prompt": reflection_prompt,
        "is_partial": is_partial,
        "weeks_available": len(timeline_entries)
    }


# =============================================================================
# FUTURE HOOKS
# =============================================================================

async def generate_monthly_comparison(
    current_month_summaries: List[Dict],
    previous_month_summaries: List[Dict]
) -> Optional[Dict]:
    """
    Future: Compare this month vs previous month patterns.
    """
    logger.debug("[Timeline] Monthly comparison not yet implemented")
    return None


async def detect_recurring_cycles(
    timeline_entries: List[Dict],
    min_cycle_length: int = 3
) -> Optional[List[Dict]]:
    """
    Future: Detect recurring pattern cycles.
    """
    logger.debug("[Timeline] Cycle detection not yet implemented")
    return None


async def detect_pattern_turning_points(
    timeline_entries: List[Dict]
) -> Optional[List[Dict]]:
    """
    Future: Detect significant pattern shifts/turning points.
    """
    logger.debug("[Timeline] Turning point detection not yet implemented")
    return None


async def generate_llm_retrospective(
    timeline: Dict[str, Any]
) -> Optional[str]:
    """
    Future: Generate LLM-powered long-form retrospective.
    """
    logger.debug("[Timeline] LLM retrospective not yet implemented")
    return None
