"""
Lifeline Pattern Intelligence Service

Generates grounded, non-deterministic insights from user's lifeline events.
Uses Mirror language principles: short, readable, psychologically clear.
Also detects timeline gaps for gentle reverse prompting.
"""

from typing import List, Dict, Any, Optional
from collections import Counter
import logging

logger = logging.getLogger(__name__)

# Gap detection threshold (years)
GAP_THRESHOLD_YEARS = 3
MIN_EVENTS_FOR_GAP_DETECTION = 3


class LifelinePatternAnalyzer:
    """
    Analyzes lifeline events to surface meaningful patterns.
    
    Design principles:
    - Use hedged language (may, seems to, appears to)
    - Never claim certainty or destiny
    - Keep insights short and readable
    - Handle low-data gracefully
    """
    
    # Minimum events needed for meaningful pattern generation
    MIN_EVENTS_FOR_PATTERNS = 3
    MIN_EVENTS_FOR_CLUSTERS = 4
    MIN_EVENTS_FOR_FULL_ANALYSIS = 5
    
    # Category groupings for thematic analysis
    CATEGORY_THEMES = {
        'identity': ['Identity', 'Turning Point', 'Achievement'],
        'connection': ['Family', 'Relationships'],
        'growth': ['Career', 'Achievement', 'Move'],
        'challenge': ['Loss', 'Health'],
        'inner': ['Spirituality', 'Identity'],
    }
    
    def __init__(self, events: List[Dict[str, Any]]):
        """Initialize with user's lifeline events."""
        self.events = events
        self.event_count = len(events)
        
    def generate_patterns(self) -> Dict[str, Any]:
        """
        Generate pattern summary from events.
        
        Returns structured data with:
        - insights: List of readable pattern observations
        - has_patterns: Whether enough data exists
        - low_data_message: Message for insufficient data
        """
        if self.event_count == 0:
            return {
                "has_patterns": False,
                "low_data_message": "Your lifeline is waiting to begin. Add your first moment to start mapping your story.",
                "insights": [],
            }
        
        if self.event_count < self.MIN_EVENTS_FOR_PATTERNS:
            return {
                "has_patterns": False,
                "low_data_message": "As you add more moments, patterns across your life will begin to emerge.",
                "insights": self._generate_minimal_insights(),
            }
        
        # Generate full pattern analysis
        insights = []
        
        # 1. Category repetition insights
        category_insight = self._analyze_category_patterns()
        if category_insight:
            insights.append(category_insight)
        
        # 2. Emotional pattern insights
        emotional_insight = self._analyze_emotional_patterns()
        if emotional_insight:
            insights.append(emotional_insight)
        
        # 3. Intensity cluster insights
        cluster_insight = self._analyze_intensity_clusters()
        if cluster_insight:
            insights.append(cluster_insight)
        
        # 4. Time range framing
        time_insight = self._analyze_time_range()
        if time_insight:
            insights.append(time_insight)
        
        # 5. Thematic overlap insights (if enough data)
        if self.event_count >= self.MIN_EVENTS_FOR_FULL_ANALYSIS:
            thematic_insight = self._analyze_thematic_overlaps()
            if thematic_insight:
                insights.append(thematic_insight)
        
        return {
            "has_patterns": len(insights) > 0,
            "low_data_message": None,
            "insights": insights[:4],  # Cap at 4 insights
        }
    
    def _generate_minimal_insights(self) -> List[Dict[str, str]]:
        """Generate limited insights for 1-2 events."""
        insights = []
        
        if self.event_count == 1:
            event = self.events[0]
            category = event.get('category')
            if category:
                insights.append({
                    "type": "seed",
                    "text": f"Your first recorded moment touches on {category.lower()}—a starting point for your story.",
                })
        elif self.event_count == 2:
            categories = [e.get('category') for e in self.events if e.get('category')]
            if len(categories) == 2:
                if categories[0] == categories[1]:
                    insights.append({
                        "type": "early_pattern",
                        "text": f"Both moments you've recorded involve {categories[0].lower()}. This may be worth noticing.",
                    })
                else:
                    insights.append({
                        "type": "early_range",
                        "text": f"Your moments span {categories[0].lower()} and {categories[1].lower()}—different threads of experience.",
                    })
        
        return insights
    
    def _analyze_category_patterns(self) -> Optional[Dict[str, str]]:
        """Identify repeating categories."""
        categories = [e.get('category') for e in self.events if e.get('category')]
        if not categories:
            return None
        
        category_counts = Counter(categories)
        
        # Find categories that appear 2+ times
        repeated = [(cat, count) for cat, count in category_counts.most_common() if count >= 2]
        
        if not repeated:
            return None
        
        # Single dominant category
        if len(repeated) == 1:
            cat, count = repeated[0]
            if count >= 3:
                return {
                    "type": "category_dominant",
                    "text": f"{cat} keeps showing up in your major moments—it may be a recurring theme for you.",
                }
            else:
                return {
                    "type": "category_repeat",
                    "text": f"{cat} appears more than once in your timeline.",
                }
        
        # Multiple repeated categories
        top_two = repeated[:2]
        return {
            "type": "category_multiple",
            "text": f"{top_two[0][0]} and {top_two[1][0]} appear often in your major moments.",
        }
    
    def _analyze_emotional_patterns(self) -> Optional[Dict[str, str]]:
        """Analyze emotional tone distribution."""
        tones = [e.get('emotional_tone', 'neutral') for e in self.events]
        tone_counts = Counter(tones)
        
        positive = tone_counts.get('positive', 0)
        negative = tone_counts.get('negative', 0)
        mixed = tone_counts.get('mixed', 0)
        
        total = sum(tone_counts.values())
        if total < 3:
            return None
        
        # Check for patterns
        if positive > total * 0.6:
            return {
                "type": "emotional_positive",
                "text": "Many of your recorded moments carry a positive emotional tone.",
            }
        
        if negative > total * 0.5:
            return {
                "type": "emotional_difficult",
                "text": "Your timeline holds several difficult moments—challenges that may have shaped you.",
            }
        
        if mixed >= 2 or (positive >= 2 and negative >= 2):
            return {
                "type": "emotional_mixed",
                "text": "Your timeline includes both difficult and transformative moments—a complex emotional landscape.",
            }
        
        return None
    
    def _analyze_intensity_clusters(self) -> Optional[Dict[str, str]]:
        """Identify clusters of high-impact events by age/year."""
        if self.event_count < self.MIN_EVENTS_FOR_CLUSTERS:
            return None
        
        # Get high-impact events (impact >= 7)
        high_impact = [e for e in self.events if e.get('impact_score', 5) >= 7]
        
        if len(high_impact) < 2:
            return None
        
        # Extract years or ages
        years = []
        ages = []
        for e in high_impact:
            if e.get('year'):
                years.append(e['year'])
            if e.get('age'):
                ages.append(e['age'])
        
        # Check for year clustering (within 3-year window)
        if len(years) >= 2:
            years_sorted = sorted(years)
            for i in range(len(years_sorted) - 1):
                if years_sorted[i + 1] - years_sorted[i] <= 3:
                    # Found a cluster
                    start_year = years_sorted[i]
                    end_year = years_sorted[i + 1]
                    if start_year == end_year:
                        return {
                            "type": "cluster_year",
                            "text": f"Several high-impact moments cluster around {start_year}—an intense period.",
                        }
                    else:
                        return {
                            "type": "cluster_years",
                            "text": f"Several high-impact moments cluster between {start_year} and {end_year}.",
                        }
        
        # Check for age clustering
        if len(ages) >= 2:
            ages_sorted = sorted(ages)
            for i in range(len(ages_sorted) - 1):
                if ages_sorted[i + 1] - ages_sorted[i] <= 5:
                    # Found a cluster
                    start_age = ages_sorted[i]
                    end_age = ages_sorted[i + 1]
                    
                    # Describe life stage
                    life_stage = self._describe_age_range(start_age, end_age)
                    return {
                        "type": "cluster_age",
                        "text": f"Several high-impact moments cluster in your {life_stage}.",
                    }
        
        return None
    
    def _describe_age_range(self, start: int, end: int) -> str:
        """Convert age range to readable life stage description."""
        avg = (start + end) / 2
        
        if avg < 18:
            return "childhood and teenage years"
        elif avg < 25:
            return "early twenties"
        elif avg < 30:
            return "late twenties"
        elif avg < 35:
            return "early thirties"
        elif avg < 40:
            return "mid to late thirties"
        elif avg < 50:
            return "forties"
        elif avg < 60:
            return "fifties"
        else:
            return f"later years"
    
    def _analyze_time_range(self) -> Optional[Dict[str, str]]:
        """Frame the overall time span of recorded events."""
        years = [e.get('year') for e in self.events if e.get('year')]
        
        if len(years) < 2:
            return None
        
        min_year = min(years)
        max_year = max(years)
        span = max_year - min_year
        
        if span == 0:
            return {
                "type": "time_single_year",
                "text": f"Your recorded moments all center around {min_year}.",
            }
        
        return {
            "type": "time_span",
            "text": f"Your recorded moments span from {min_year} to {max_year}—{span} years of your story.",
        }
    
    def _analyze_thematic_overlaps(self) -> Optional[Dict[str, str]]:
        """Find overlapping themes between categories and tags."""
        # Collect all categories
        categories = [e.get('category') for e in self.events if e.get('category')]
        
        # Collect all tags
        all_tags = []
        for e in self.events:
            tags = e.get('tags', [])
            if tags:
                all_tags.extend([t.lower() for t in tags])
        
        if not categories or not all_tags:
            return None
        
        # Look for category-tag resonance
        category_counts = Counter(categories)
        tag_counts = Counter(all_tags)
        
        top_category = category_counts.most_common(1)[0][0] if category_counts else None
        top_tags = [tag for tag, count in tag_counts.most_common(3) if count >= 2]
        
        if top_category and top_tags:
            # Check if top tags appear with top category
            matching_events = [
                e for e in self.events 
                if e.get('category') == top_category 
                and any(t.lower() in [tag.lower() for tag in (e.get('tags') or [])] for t in top_tags)
            ]
            
            if len(matching_events) >= 2:
                tag_str = top_tags[0]
                return {
                    "type": "thematic_overlap",
                    "text": f"When {top_category.lower()} moments appear, '{tag_str}' often shows up alongside.",
                }
        
        # Look for transitions (if there are identity/turning point events)
        turning_points = [e for e in self.events if e.get('category') in ['Turning Point', 'Identity']]
        if len(turning_points) >= 2:
            return {
                "type": "transitions",
                "text": "Your timeline shows multiple turning points—moments where something shifted.",
            }
        
        return None


def generate_lifeline_patterns(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Main entry point for generating lifeline patterns.
    
    Args:
        events: List of lifeline event documents
        
    Returns:
        Dictionary with pattern insights
    """
    analyzer = LifelinePatternAnalyzer(events)
    return analyzer.generate_patterns()


def detect_timeline_gaps(events: List[Dict[str, Any]], threshold_years: int = GAP_THRESHOLD_YEARS) -> List[Dict[str, Any]]:
    """
    Detect gaps in the user's timeline where no events are recorded.
    
    Args:
        events: List of lifeline event documents
        threshold_years: Minimum gap size to detect (default: 3 years)
        
    Returns:
        List of gap objects with start_year, end_year, and gap_length
    """
    if len(events) < MIN_EVENTS_FOR_GAP_DETECTION:
        return []
    
    # Extract years from events
    years = sorted(set(e.get('year') for e in events if e.get('year')))
    
    if len(years) < 2:
        return []
    
    gaps = []
    
    for i in range(len(years) - 1):
        current_year = years[i]
        next_year = years[i + 1]
        gap_length = next_year - current_year - 1  # Subtract 1 because we want years between
        
        if gap_length >= threshold_years:
            gaps.append({
                "start_year": current_year + 1,  # The year after the last event
                "end_year": next_year - 1,       # The year before the next event
                "gap_length": gap_length,
            })
    
    return gaps


def generate_gap_prompts(gaps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate gentle, supportive prompts for detected timeline gaps.
    
    Uses Mirror language principles:
    - Curious, not demanding
    - Supportive, not intrusive
    - Optional, not pressuring
    
    Args:
        gaps: List of gap objects from detect_timeline_gaps
        
    Returns:
        List of prompt objects with text and metadata
    """
    prompts = []
    
    for gap in gaps:
        start = gap['start_year']
        end = gap['end_year']
        length = gap['gap_length']
        
        # Format the time period description
        if start == end:
            period_text = f"{start}"
        else:
            period_text = f"{start} to {end}"
        
        # Generate the main prompt text (gentle, curious, psychologically safe)
        if length <= 4:
            main_text = f"Sometimes the quiet periods matter just as much.\n\nWas there something subtle, difficult, or meaningful during {period_text}?"
        elif length <= 7:
            main_text = f"Sometimes the quiet periods matter just as much.\n\nWas there something subtle, difficult, or meaningful between {period_text}?"
        else:
            main_text = f"Sometimes the quiet periods matter just as much.\n\nWas there something subtle, difficult, or meaningful during this time ({period_text})?"
        
        # Generate the reflection invitation - small secondary line
        reflection = "Not all important moments are obvious."
        
        prompts.append({
            "start_year": start,
            "end_year": end,
            "gap_length": length,
            "prompt_text": main_text,
            "reflection_text": reflection,
            "cta_text": "Add a moment from this time",
        })
    
    return prompts


def generate_full_lifeline_analysis(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate complete lifeline analysis including patterns and missing periods.
    
    Args:
        events: List of lifeline event documents
        
    Returns:
        Dictionary with patterns, insights, and missing_periods
    """
    # Generate patterns
    patterns = generate_lifeline_patterns(events)
    
    # Detect gaps
    gaps = detect_timeline_gaps(events)
    
    # Generate prompts for gaps
    missing_periods = generate_gap_prompts(gaps)
    
    return {
        **patterns,
        "missing_periods": missing_periods,
    }
