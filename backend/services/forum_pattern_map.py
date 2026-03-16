"""
Forum Pattern Map Service
Task 48: Aggregates and visualizes shared life patterns across forum members.

Detects:
1. Shared Pattern Types - When multiple members have similar pattern arcs
2. Timeline Clusters - Event concentrations across members in time windows
"""

import logging
from typing import List, Dict, Any, Optional
from collections import Counter, defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTS
# =============================================================================

# Pattern arc categories (aligned with lifeline patterns)
PATTERN_ARC_TYPES = {
    'career_growth': {
        'categories': ['Career', 'Achievement'],
        'keywords': ['promotion', 'job', 'founded', 'started', 'company', 'business', 'launch'],
        'summary_template': 'career growth or professional transformation'
    },
    'identity_shift': {
        'categories': ['Identity', 'Turning Point', 'Spirituality'],
        'keywords': ['realized', 'discovered', 'changed', 'awakening', 'transformation'],
        'summary_template': 'identity shifts or personal transformation'
    },
    'relationship_turning': {
        'categories': ['Relationships', 'Family'],
        'keywords': ['married', 'divorced', 'met', 'born', 'child', 'partner', 'breakup'],
        'summary_template': 'significant relationship or family changes'
    },
    'momentum_pressure': {
        'categories': ['Health', 'Loss', 'Career'],
        'keywords': ['pressure', 'stress', 'challenge', 'difficult', 'lost', 'crisis'],
        'summary_template': 'periods of pressure or challenge'
    },
    'reinvention': {
        'categories': ['Move', 'Career', 'Identity'],
        'keywords': ['moved', 'started', 'new', 'relocated', 'pivoted', 'changed'],
        'summary_template': 'reinvention or major life pivots'
    },
    'expression_hesitation': {
        'categories': ['Career', 'Identity', 'Relationships'],
        'keywords': ['hesitated', 'delayed', 'waited', 'uncertain', 'paused'],
        'summary_template': 'periods of reflection or hesitation'
    },
}

# Configuration
MIN_MEMBERS_FOR_SHARED_PATTERN = 2
YEAR_PROXIMITY_WINDOW = 2  # ±2 years for shared pattern detection
CLUSTER_WINDOW_YEARS = 3   # 3 year window for timeline clusters
MIN_EVENTS_FOR_CLUSTER = 3
MIN_MEMBERS_FOR_CLUSTER = 2


# =============================================================================
# PATTERN DETECTION
# =============================================================================

def detect_member_pattern_arcs(events: List[Dict[str, Any]], user_id: str) -> List[Dict[str, Any]]:
    """
    Detect pattern arcs for a single member's lifeline events.
    
    Returns list of detected patterns with years.
    """
    patterns = []
    
    for arc_type, arc_config in PATTERN_ARC_TYPES.items():
        matching_events = []
        
        for event in events:
            category = event.get('category') or ''
            title = (event.get('title') or '').lower()
            description = (event.get('description') or '').lower()
            year = event.get('year')
            
            if not year:
                continue
            
            # Check category match
            category_match = category in arc_config['categories']
            
            # Check keyword match
            text_content = f"{title} {description}"
            keyword_match = any(kw in text_content for kw in arc_config['keywords'])
            
            if category_match or keyword_match:
                matching_events.append({
                    'year': year,
                    'title': event.get('title') or 'Untitled',
                    'category': category,
                })
        
        # If we have matching events, create a pattern arc
        if matching_events:
            years = sorted(set(e['year'] for e in matching_events if e['year']))
            if years:
                patterns.append({
                    'user_id': user_id,
                    'arc_type': arc_type,
                    'years': years,
                    'event_count': len(matching_events),
                    'start_year': min(years),
                    'end_year': max(years),
                })
    
    return patterns


def find_shared_patterns(
    all_member_patterns: List[Dict[str, Any]],
    user_names: Dict[str, str]
) -> List[Dict[str, Any]]:
    """
    Find patterns shared across multiple members.
    
    A pattern is "shared" if 2+ members have the same arc type
    with overlapping years (within ±YEAR_PROXIMITY_WINDOW).
    """
    shared_patterns = []
    
    # Group patterns by arc type
    patterns_by_type = defaultdict(list)
    for pattern in all_member_patterns:
        patterns_by_type[pattern['arc_type']].append(pattern)
    
    for arc_type, patterns in patterns_by_type.items():
        if len(patterns) < MIN_MEMBERS_FOR_SHARED_PATTERN:
            continue
        
        # Find year overlaps
        # Create a "year presence" map for each member
        member_years = {}
        for p in patterns:
            member_years[p['user_id']] = set(p['years'])
        
        # Find the years where multiple members have activity
        all_years = set()
        for years in member_years.values():
            all_years.update(years)
        
        # For each year range, check if multiple members overlap
        year_to_members = defaultdict(set)
        for year in all_years:
            for user_id, years in member_years.items():
                # Check if this member has activity within ±YEAR_PROXIMITY_WINDOW
                for member_year in years:
                    if abs(member_year - year) <= YEAR_PROXIMITY_WINDOW:
                        year_to_members[year].add(user_id)
                        break
        
        # Find contiguous year ranges with 2+ members
        overlapping_years = sorted([y for y, members in year_to_members.items() 
                                     if len(members) >= MIN_MEMBERS_FOR_SHARED_PATTERN])
        
        if not overlapping_years:
            continue
        
        # Group into ranges (allow 1 year gaps)
        year_ranges = []
        current_range = [overlapping_years[0]]
        
        for year in overlapping_years[1:]:
            if year - current_range[-1] <= 2:
                current_range.append(year)
            else:
                year_ranges.append(current_range)
                current_range = [year]
        year_ranges.append(current_range)
        
        # Create shared pattern for each range
        for year_range in year_ranges:
            if len(year_range) < 1:
                continue
            
            # Get members active in this range
            active_members = set()
            for year in year_range:
                active_members.update(year_to_members[year])
            
            if len(active_members) < MIN_MEMBERS_FOR_SHARED_PATTERN:
                continue
            
            arc_config = PATTERN_ARC_TYPES.get(arc_type, {})
            summary_template = arc_config.get('summary_template', 'similar life patterns')
            
            # Create human-readable member display names
            member_display = [user_names.get(uid, f"Member {uid[:4]}") for uid in active_members]
            
            shared_patterns.append({
                'pattern_type': arc_type,
                'years': sorted(year_range),
                'start_year': min(year_range),
                'end_year': max(year_range),
                'member_count': len(active_members),
                'members': list(active_members),
                'member_names': member_display,
                'summary': f"Several members appear to have experienced {summary_template} during this period.",
            })
    
    # Sort by member count (most shared first), then by recency
    shared_patterns.sort(key=lambda x: (-x['member_count'], -x['end_year']))
    
    return shared_patterns


def find_timeline_clusters(
    all_events: List[Dict[str, Any]],
    user_names: Dict[str, str]
) -> List[Dict[str, Any]]:
    """
    Detect clusters of events across members within time windows.
    
    A cluster is: 3+ events from 2+ members within a 3-year window.
    """
    clusters = []
    
    # Get all years with events
    events_by_year = defaultdict(list)
    for event in all_events:
        year = event.get('year')
        if year:
            events_by_year[year].append(event)
    
    if not events_by_year:
        return clusters
    
    years = sorted(events_by_year.keys())
    min_year = min(years)
    max_year = max(years)
    
    # Slide a window across the timeline
    window_start = min_year
    processed_ranges = set()
    
    while window_start <= max_year:
        window_end = window_start + CLUSTER_WINDOW_YEARS - 1
        
        # Collect events in this window
        window_events = []
        for year in range(window_start, window_end + 1):
            window_events.extend(events_by_year.get(year, []))
        
        # Check if this forms a valid cluster
        if len(window_events) >= MIN_EVENTS_FOR_CLUSTER:
            members_in_window = set(e.get('user_id') for e in window_events if e.get('user_id'))
            
            if len(members_in_window) >= MIN_MEMBERS_FOR_CLUSTER:
                range_key = (window_start, window_end)
                
                # Avoid overlapping clusters
                if range_key not in processed_ranges:
                    processed_ranges.add(range_key)
                    
                    # Calculate intensity score
                    intensity = len(window_events) / CLUSTER_WINDOW_YEARS
                    
                    # Get sample event titles
                    sample_events = [e.get('title', 'Untitled')[:50] for e in window_events[:3]]
                    
                    clusters.append({
                        'start_year': window_start,
                        'end_year': window_end,
                        'event_count': len(window_events),
                        'member_count': len(members_in_window),
                        'members': list(members_in_window),
                        'intensity': round(intensity, 2),
                        'sample_events': sample_events,
                    })
        
        window_start += 1
    
    # Merge overlapping clusters and keep the most significant ones
    clusters = _merge_overlapping_clusters(clusters)
    
    # Sort by event count (most active first)
    clusters.sort(key=lambda x: (-x['event_count'], -x['member_count']))
    
    return clusters[:10]  # Return top 10 clusters


def _merge_overlapping_clusters(clusters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Merge clusters that significantly overlap, keeping the more significant one."""
    if len(clusters) <= 1:
        return clusters
    
    merged = []
    clusters = sorted(clusters, key=lambda x: x['start_year'])
    
    current = clusters[0]
    
    for next_cluster in clusters[1:]:
        # Check for significant overlap (more than 1 year)
        overlap = current['end_year'] - next_cluster['start_year'] + 1
        
        if overlap >= 2:
            # Keep the more significant cluster
            if next_cluster['event_count'] > current['event_count']:
                current = next_cluster
        else:
            merged.append(current)
            current = next_cluster
    
    merged.append(current)
    return merged


# =============================================================================
# MAIN AGGREGATION FUNCTION
# =============================================================================

async def generate_forum_pattern_map(
    db,
    forum_id: str,
) -> Dict[str, Any]:
    """
    Generate the complete Forum Pattern Map for a forum.
    
    Args:
        db: Database connection
        forum_id: The forum ID to analyze
        
    Returns:
        Complete pattern map data structure
    """
    logger.info(f"[ForumPatternMap] Generating pattern map for forum: {forum_id}")
    
    # Get all forum members
    members_cursor = db.forum_members.find({
        "forum_id": forum_id,
        "status": "active"
    })
    members = []
    async for member in members_cursor:
        members.append(member)
    
    member_count = len(members)
    member_user_ids = [m['user_id'] for m in members]
    
    logger.info(f"[ForumPatternMap] Forum has {member_count} members")
    
    if member_count == 0:
        return {
            "forum_id": forum_id,
            "member_count": 0,
            "events_total": 0,
            "shared_patterns": [],
            "timeline_clusters": [],
            "has_data": False,
            "empty_state_message": "No members have joined this forum yet.",
        }
    
    # Get user names for display
    user_names = {}
    for user_id in member_user_ids:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if user:
            user_names[user_id] = user.get('name') or f"Member {user_id[:4]}"
        else:
            user_names[user_id] = f"Member {user_id[:4]}"
    
    # Get all lifeline events for forum members
    all_events = []
    for user_id in member_user_ids:
        events_cursor = db.lifeline_events.find({"user_id": user_id})
        async for event in events_cursor:
            event_data = {
                'user_id': user_id,
                'year': event.get('year'),
                'title': event.get('title', ''),
                'description': event.get('description', ''),
                'category': event.get('category', ''),
                'impact_score': event.get('impact_score', 5),
            }
            all_events.append(event_data)
    
    events_total = len(all_events)
    logger.info(f"[ForumPatternMap] members={member_count} events={events_total}")
    
    if events_total == 0:
        return {
            "forum_id": forum_id,
            "member_count": member_count,
            "events_total": 0,
            "shared_patterns": [],
            "timeline_clusters": [],
            "has_data": False,
            "empty_state_message": "Forum patterns will appear once members add more turning points to their timelines.",
        }
    
    # Detect individual member pattern arcs
    all_member_patterns = []
    for user_id in member_user_ids:
        user_events = [e for e in all_events if e['user_id'] == user_id]
        if user_events:
            patterns = detect_member_pattern_arcs(user_events, user_id)
            all_member_patterns.extend(patterns)
    
    # Find shared patterns
    shared_patterns = find_shared_patterns(all_member_patterns, user_names)
    logger.info(f"[ForumPatternMap] shared_patterns={len(shared_patterns)}")
    
    # Find timeline clusters
    timeline_clusters = find_timeline_clusters(all_events, user_names)
    logger.info(f"[ForumPatternMap] clusters={len(timeline_clusters)}")
    
    # Determine if we have meaningful data
    has_data = len(shared_patterns) > 0 or len(timeline_clusters) > 0
    
    return {
        "forum_id": forum_id,
        "member_count": member_count,
        "events_total": events_total,
        "shared_patterns": shared_patterns,
        "timeline_clusters": timeline_clusters,
        "has_data": has_data,
        "empty_state_message": None if has_data else "Forum patterns will appear once members add more turning points to their timelines.",
        "generated_at": datetime.utcnow().isoformat(),
    }


# Import ObjectId for user lookup
from bson import ObjectId
