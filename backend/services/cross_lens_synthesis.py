"""
Cross-Lens Synthesis Service

Creates grounded, non-deterministic insights by connecting data across:
- Lifeline (life events and patterns)
- Pattern Engine (current active themes)
- BaZi (elemental tendencies and operating style)

Uses Mirror language principles:
- grounded
- readable
- short
- psychologically clear
- non-deterministic
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# SYNTHESIS CONFIGURATION
# =============================================================================

# Minimum requirements for synthesis
MIN_LIFELINE_EVENTS = 2
MIN_PATTERN_SIGNALS = 1
BAZI_REQUIRED = True

# Element to domain/category mapping for cross-referencing
ELEMENT_DOMAIN_MAP = {
    'Wood': ['growth', 'creativity', 'identity', 'career', 'achievement'],
    'Fire': ['relationships', 'connection', 'visibility', 'expression', 'family'],
    'Earth': ['stability', 'health', 'nurturing', 'grounding', 'home'],
    'Metal': ['structure', 'standards', 'discipline', 'career', 'achievement'],
    'Water': ['wisdom', 'reflection', 'intuition', 'spirituality', 'inner'],
}

# Category normalization for matching
CATEGORY_NORMALIZE = {
    'career': 'career',
    'work': 'career',
    'job': 'career',
    'identity': 'identity',
    'self': 'identity',
    'turning point': 'identity',
    'relationships': 'relationships',
    'family': 'relationships',
    'love': 'relationships',
    'health': 'health',
    'move': 'transition',
    'loss': 'loss',
    'achievement': 'achievement',
    'spirituality': 'inner',
}


# =============================================================================
# SYNTHESIS GENERATOR
# =============================================================================

class CrossLensSynthesis:
    """
    Generates cross-lens synthesis insights from multiple data sources.
    """
    
    def __init__(
        self,
        lifeline_data: Optional[Dict[str, Any]],
        pattern_data: Optional[Dict[str, Any]],
        bazi_data: Optional[Dict[str, Any]],
    ):
        self.lifeline = lifeline_data
        self.patterns = pattern_data
        self.bazi = bazi_data
        
        # Extracted data for synthesis
        self.lifeline_categories = []
        self.lifeline_themes = []
        self.lifeline_gaps = []
        self.pattern_domains = []
        self.pattern_themes = []
        self.bazi_element = None
        self.bazi_dominant = None
        self.bazi_weak = None
        self.bazi_tension = None
        
        self._extract_data()
    
    def _extract_data(self):
        """Extract relevant data from each source."""
        # Extract Lifeline data
        if self.lifeline and self.lifeline.get('has_patterns'):
            insights = self.lifeline.get('insights', [])
            for insight in insights:
                if insight.get('type') in ['category_dominant', 'category_repeat', 'category_multiple']:
                    text = insight.get('text', '')
                    # Extract category names from insight text
                    for cat in CATEGORY_NORMALIZE.keys():
                        if cat.lower() in text.lower():
                            normalized = CATEGORY_NORMALIZE[cat]
                            if normalized not in self.lifeline_categories:
                                self.lifeline_categories.append(normalized)
            
            # Get missing periods
            missing = self.lifeline.get('missing_periods', [])
            self.lifeline_gaps = missing[:2]  # Limit to 2 gaps
            
            # Get themes from insights
            self.lifeline_themes = [i.get('text', '') for i in insights if i.get('type') == 'thematic_overlap']
        
        # Extract Pattern Engine data - handle both 'domains' and 'categories' format
        if self.patterns:
            # Try 'categories' format first (actual API response)
            categories = self.patterns.get('categories', [])
            if categories:
                for cat in categories:
                    if isinstance(cat, dict) and cat.get('signal_count', 0) > 0:
                        self.pattern_domains.append({
                            'name': cat.get('category_name', cat.get('category_id', 'unknown')),
                            'count': cat.get('signal_count', 0),
                            'themes': [s.get('label', '') for s in cat.get('matched_signals', [])[:3]],
                        })
            else:
                # Fallback to 'domains' format
                domains = self.patterns.get('domains', {})
                for domain, data in domains.items():
                    if isinstance(data, dict) and data.get('signal_count', 0) > 0:
                        self.pattern_domains.append({
                            'name': domain,
                            'count': data.get('signal_count', 0),
                            'themes': data.get('themes', [])[:3],
                        })
            
            # Sort by signal count
            self.pattern_domains.sort(key=lambda x: x['count'], reverse=True)
            
            # Extract active themes
            for domain in self.pattern_domains[:3]:
                self.pattern_themes.extend(domain.get('themes', []))
        
        # Extract BaZi data
        if self.bazi and self.bazi.get('has_bazi'):
            summary = self.bazi.get('summary', {})
            self.bazi_element = summary.get('day_master_element')
            self.bazi_dominant = summary.get('dominant_element')
            self.bazi_weak = summary.get('weak_element')
            
            # Calculate tension
            if self.bazi_dominant and self.bazi_weak:
                self.bazi_tension = f"{self.bazi_dominant} (strong) vs {self.bazi_weak} (weak)"
    
    def has_sufficient_data(self) -> bool:
        """Check if we have enough data for meaningful synthesis."""
        has_lifeline = len(self.lifeline_categories) > 0 or len(self.lifeline_themes) > 0
        has_patterns = len(self.pattern_domains) > 0
        has_bazi = self.bazi_element is not None
        
        # Need at least 2 of 3 sources with meaningful data
        sources = sum([has_lifeline, has_patterns, has_bazi])
        return sources >= 2
    
    def generate_synthesis(self) -> Dict[str, Any]:
        """Generate the cross-lens synthesis."""
        if not self.has_sufficient_data():
            return self._low_data_response()
        
        insights = []
        signals_used = []
        
        # Track which sources contributed
        if self.lifeline_categories or self.lifeline_themes:
            signals_used.append('lifeline')
        if self.pattern_domains:
            signals_used.append('pattern_engine')
        if self.bazi_element:
            signals_used.append('bazi')
        
        # Generate different types of insights
        
        # 1. Repetition insight (Lifeline + Patterns overlap)
        repetition = self._find_repetition_insight()
        if repetition:
            insights.append(repetition)
        
        # 2. Tension insight (BaZi + Lifeline or Patterns)
        tension = self._find_tension_insight()
        if tension:
            insights.append(tension)
        
        # 3. Active pattern insight (BaZi + Patterns)
        active = self._find_active_pattern_insight()
        if active:
            insights.append(active)
        
        # 4. Reflection question
        question = self._generate_reflection_question()
        if question:
            insights.append(question)
        
        # Generate headline and summary
        headline = self._generate_headline(insights)
        summary = self._generate_summary(insights)
        
        return {
            "has_synthesis": True,
            "headline": headline,
            "summary": summary,
            "signals_used": signals_used,
            "insights": insights[:4],  # Cap at 4 insights
        }
    
    def _low_data_response(self) -> Dict[str, Any]:
        """Return a low-data state response."""
        return {
            "has_synthesis": False,
            "headline": "Synthesis Building",
            "summary": "As Mirror gathers more moments and patterns, cross-lens connections will begin to appear.",
            "signals_used": [],
            "insights": [],
            "low_data_hint": "Add more lifeline moments or continue reflecting to unlock synthesis.",
        }
    
    def _find_repetition_insight(self) -> Optional[Dict[str, str]]:
        """Find overlaps between Lifeline categories and Pattern domains."""
        if not self.lifeline_categories or not self.pattern_domains:
            return None
        
        # Check for category-domain overlap
        for category in self.lifeline_categories:
            for domain in self.pattern_domains[:3]:
                domain_name = domain['name'].lower()
                if category in domain_name or domain_name in category:
                    return {
                        "type": "repetition",
                        "text": f"A theme of {category} keeps returning in your timeline, and your current patterns suggest this may be active again now.",
                    }
                
                # Check theme overlap
                domain_themes = [t.lower() for t in domain.get('themes', [])]
                if any(category in t or t in category for t in domain_themes):
                    return {
                        "type": "repetition",
                        "text": f"Your lifeline shows {category} as a recurring theme, and similar patterns appear in your current active signals.",
                    }
        
        # If no direct overlap, note the parallel
        if self.lifeline_categories and self.pattern_domains:
            top_category = self.lifeline_categories[0]
            top_domain = self.pattern_domains[0]['name']
            return {
                "type": "repetition",
                "text": f"Your life story shows repeating moments around {top_category}, while your current patterns are most active around {top_domain.lower()}. Notice if these connect.",
            }
        
        return None
    
    def _find_tension_insight(self) -> Optional[Dict[str, str]]:
        """Find tension between BaZi tendencies and life patterns."""
        if not self.bazi_element or not self.bazi_dominant:
            return None
        
        # Get element qualities
        dominant_domains = ELEMENT_DOMAIN_MAP.get(self.bazi_dominant, [])
        weak_domains = ELEMENT_DOMAIN_MAP.get(self.bazi_weak, [])
        
        # Check if lifeline categories align with weak element
        for category in self.lifeline_categories:
            if category in weak_domains:
                return {
                    "type": "tension",
                    "text": f"Your BaZi shows {self.bazi_weak} as a less natural energy, yet your lifeline has key moments around {category}. This may point to areas where growth has required extra effort.",
                }
        
        # Check pattern domains against element map
        for domain in self.pattern_domains[:2]:
            domain_name = domain['name'].lower()
            if any(d in domain_name for d in weak_domains):
                return {
                    "type": "tension",
                    "text": f"Your current patterns show activity in {domain_name}, which connects to {self.bazi_weak}—an element that may require more conscious attention in your chart.",
                }
        
        # Default tension based on element balance
        if self.bazi_dominant and self.bazi_weak:
            return {
                "type": "tension",
                "text": f"Your chart naturally leans toward {self.bazi_dominant} qualities, with {self.bazi_weak} requiring more effort. Notice where this shows up in what feels easy versus what feels like work.",
            }
        
        return None
    
    def _find_active_pattern_insight(self) -> Optional[Dict[str, str]]:
        """Connect BaZi operating style to current patterns."""
        if not self.bazi_element or not self.pattern_domains:
            return None
        
        # Map day master to behavioral tendency
        element_tendency = {
            'Wood': 'growth and forward movement',
            'Fire': 'connection and expression',
            'Earth': 'stability and grounding',
            'Metal': 'refinement and clear standards',
            'Water': 'reflection and adaptability',
        }
        
        tendency = element_tendency.get(self.bazi_element, 'your natural style')
        top_domain = self.pattern_domains[0]['name'].lower()
        
        return {
            "type": "operating_style",
            "text": f"Your Day Master suggests {tendency} as a core operating style. Your active patterns around {top_domain} may be an expression of this, or a place where it meets friction.",
        }
    
    def _generate_reflection_question(self) -> Dict[str, str]:
        """Generate a synthesis-based reflection question."""
        questions = []
        
        # Based on repetition
        if self.lifeline_categories:
            top_cat = self.lifeline_categories[0]
            questions.append(f"What would it mean to approach {top_cat} differently this time?")
        
        # Based on BaZi tension
        if self.bazi_weak:
            weak_domains = ELEMENT_DOMAIN_MAP.get(self.bazi_weak, [])
            if weak_domains:
                questions.append(f"Where might you be avoiding the {weak_domains[0]} that wants your attention?")
        
        # Based on patterns
        if self.pattern_domains:
            top_domain = self.pattern_domains[0]['name'].lower()
            questions.append(f"What would change if you paused before acting on the {top_domain} signals you're noticing?")
        
        # Default question
        if not questions:
            questions.append("What thread connects the different parts of your life right now?")
        
        return {
            "type": "question",
            "text": questions[0],
        }
    
    def _generate_headline(self, insights: List[Dict]) -> str:
        """Generate a synthesis headline."""
        if not insights:
            return "Patterns Emerging"
        
        # Use the first insight type to shape the headline
        first_type = insights[0].get('type', '')
        
        if first_type == 'repetition':
            return "A Familiar Theme Returns"
        elif first_type == 'tension':
            return "Where Ease Meets Effort"
        elif first_type == 'operating_style':
            return "Your Style in Motion"
        else:
            return "Threads Connecting"
    
    def _generate_summary(self, insights: List[Dict]) -> str:
        """Generate a short synthesis summary."""
        parts = []
        
        if self.lifeline_categories:
            parts.append(f"lifeline themes around {self.lifeline_categories[0]}")
        
        if self.pattern_domains:
            parts.append(f"active patterns in {self.pattern_domains[0]['name'].lower()}")
        
        if self.bazi_element:
            parts.append(f"your {self.bazi_element} Day Master")
        
        if len(parts) >= 2:
            return f"Mirror is noticing connections between {parts[0]} and {parts[1]}. These may point to something worth exploring."
        elif parts:
            return f"Mirror is tracking {parts[0]}. More connections will emerge as your data grows."
        else:
            return "Mirror is beginning to connect patterns across your lenses."


# =============================================================================
# MAIN SYNTHESIS FUNCTION
# =============================================================================

async def generate_cross_lens_synthesis(
    user_id: str,
    lifeline_summary: Optional[Dict[str, Any]] = None,
    pattern_graph: Optional[Dict[str, Any]] = None,
    bazi_summary: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate cross-lens synthesis for a user.
    
    Args:
        user_id: The user ID
        lifeline_summary: Output from /api/lifeline/{user_id}/summary
        pattern_graph: Output from /api/pattern-graph/{user_id}
        bazi_summary: Output from /api/bazi/{user_id}/summary
        
    Returns:
        Synthesis object with headline, summary, and insights
    """
    logger.info(f"[Synthesis] Generating cross-lens synthesis for user {user_id}")
    
    # Extract patterns data from lifeline summary
    lifeline_patterns = None
    if lifeline_summary and lifeline_summary.get('patterns'):
        lifeline_patterns = lifeline_summary['patterns']
    
    # Create synthesis generator
    synthesis = CrossLensSynthesis(
        lifeline_data=lifeline_patterns,
        pattern_data=pattern_graph,
        bazi_data=bazi_summary,
    )
    
    # Generate synthesis
    result = synthesis.generate_synthesis()
    
    logger.info(f"[Synthesis] Generated {'full' if result.get('has_synthesis') else 'low-data'} synthesis for user {user_id}")
    
    return result


# =============================================================================
# CONDENSED SYNTHESIS FOR HOMEPAGE
# =============================================================================

def condense_synthesis_for_homepage(synthesis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a condensed version of synthesis for homepage teaser.
    
    Args:
        synthesis: Full synthesis object
        
    Returns:
        Condensed version with headline, one-line summary, and CTA
    """
    if not synthesis.get('has_synthesis'):
        return {
            "show_teaser": False,
            "headline": synthesis.get('headline', 'Synthesis Building'),
            "summary": synthesis.get('summary', ''),
        }
    
    # Get first insight that isn't a question
    first_insight = None
    for insight in synthesis.get('insights', []):
        if insight.get('type') != 'question':
            first_insight = insight
            break
    
    return {
        "show_teaser": True,
        "headline": synthesis.get('headline', 'Patterns Connecting'),
        "summary": first_insight.get('text', synthesis.get('summary', '')) if first_insight else synthesis.get('summary', ''),
        "signals_used": synthesis.get('signals_used', []),
        "cta_text": "Explore Patterns",
    }
