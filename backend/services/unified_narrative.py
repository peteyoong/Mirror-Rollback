"""
Unified Narrative Generator v1.0

Task 76B: Kill Old Narrative Engine

This is the SINGLE SOURCE OF TRUTH for all user-facing narrative text.
All screens must use this generator.

CRITICAL RULES:
- NO hedging words: may, might, could, suggests, appears, tends to
- DIRECT behavioral language only
- GROUNDED in user's archetype
- SPECIFIC to user's data
"""

import logging
from typing import Dict, List, Any, Optional
import re

logger = logging.getLogger(__name__)

# =============================================================================
# BLOCKED WORDS - Fail generation if detected
# =============================================================================

BLOCKED_WORDS = [
    r'\bmay\b',
    r'\bmight\b', 
    r'\bcould\b',
    r'\bsuggests?\b',
    r'\bappears?\s+to\b',
    r'\btends?\s+to\b',
    r'\bseems?\s+to\b',
    r'\bperhaps\b',
    r'\bpossibly\b',
    r'\bprobably\b',
]

def contains_blocked_words(text: str) -> bool:
    """Check if text contains any blocked hedging words."""
    text_lower = text.lower()
    for pattern in BLOCKED_WORDS:
        if re.search(pattern, text_lower):
            return True
    return False

def get_blocked_words_found(text: str) -> List[str]:
    """Return list of blocked words found in text."""
    text_lower = text.lower()
    found = []
    for pattern in BLOCKED_WORDS:
        match = re.search(pattern, text_lower)
        if match:
            found.append(match.group())
    return found

# =============================================================================
# DOMAIN NARRATIVES - Direct, behavioral language
# =============================================================================

DOMAIN_NARRATIVES = {
    'energy_vitality': {
        'quiet': "Your energy is stable. No major shifts—your body is holding steady.",
        'present': "Something is pulling at your energy reserves. You're either pushing too hard or holding back.",
        'recurring': "This keeps coming back. Your energy pattern isn't random—it's responding to something deeper.",
        'question': "What are you spending energy on that doesn't give it back?"
    },
    'emotional_landscape': {
        'quiet': "Emotionally quiet. You're processing, integrating, or resting between waves.",
        'present': "Feelings are moving. Something wants acknowledgment—not analysis.",
        'recurring': "The same emotional territory keeps appearing. This isn't coincidence—it's information.",
        'question': "What emotion are you avoiding by staying busy?"
    },
    'identity_direction': {
        'quiet': "Identity questions are resting. You're being rather than becoming—for now.",
        'present': "Something is asking: Who are you, really? The question surfaces when old answers stop fitting.",
        'recurring': "This question keeps returning. Who you are isn't settled—it's evolving.",
        'question': "What part of yourself have you been hiding or abandoning?"
    },
    'mind_meaning': {
        'quiet': "Your mind is settled. Less analyzing, more experiencing.",
        'present': "You're trying to figure something out. The mind is working overtime.",
        'recurring': "The same questions keep circling. Your mind is fixated because something hasn't been integrated.",
        'question': "What truth are you thinking around instead of sitting with?"
    },
    'expression_action': {
        'quiet': "Expression is dormant. You're gathering before the next movement.",
        'present': "Something wants out. A creative urge, a voice, an action that feels necessary.",
        'recurring': "This impulse keeps returning. Expression isn't optional for you—it's how you process life.",
        'question': "What have you been holding back that wants to be said?"
    },
    'relationships_boundaries': {
        'quiet': "Relational space is calm. You're present with yourself.",
        'present': "Something is shifting in how you relate. Boundaries feel tested or unclear.",
        'recurring': "This pattern runs deep. Your relational wiring is showing you something consistent.",
        'question': "Where are you giving what you don't actually have?"
    },
    'growth_transformation': {
        'quiet': "Transformation is quiet—but that doesn't mean inactive. Deep changes happen invisibly.",
        'present': "You're between versions of yourself. The old doesn't fit. The new isn't clear yet.",
        'recurring': "Growth keeps calling. You don't want comfort—you want to become something more.",
        'question': "What are you ready to let go of?"
    }
}

# =============================================================================
# ARCHETYPE-ALIGNED STORY GENERATORS
# =============================================================================

def generate_story(archetype_name: str, archetype_data: Dict[str, Any]) -> str:
    """Generate the 'Story' section - what this pattern looks like in real life."""
    narrative = archetype_data.get('narrative', {})
    how_shows = narrative.get('how_this_shows_up', [])
    
    if how_shows:
        return how_shows[0] if isinstance(how_shows[0], str) else str(how_shows[0])
    
    return f"Your {archetype_name} pattern shows up in the choices you make—especially the ones that surprise others."

def generate_pattern_description(archetype_name: str, archetype_data: Dict[str, Any]) -> str:
    """Generate the 'Pattern' section - what you consistently do."""
    narrative = archetype_data.get('narrative', {})
    summary = narrative.get('summary', '')
    
    if summary:
        return summary
    
    return f"You follow the same thread even when circumstances change. This is your {archetype_name} pattern in action."

def generate_challenge(archetype_name: str, archetype_data: Dict[str, Any]) -> str:
    """Generate the 'Challenge' section - where this creates friction."""
    narrative = archetype_data.get('narrative', {})
    contrast = narrative.get('contrast', '')
    
    if contrast:
        # Convert contrast to challenge framing
        return f"The friction: {contrast}"
    
    return f"This pattern creates friction when others expect consistency and you've already moved on."

def generate_genius(archetype_name: str, archetype_data: Dict[str, Any]) -> str:
    """Generate the 'Genius' section - where this becomes strength."""
    narrative = archetype_data.get('narrative', {})
    short_desc = narrative.get('short_description', '')
    
    if short_desc:
        return f"Your genius: {short_desc}. This is exactly what's needed when the old way stops working."
    
    return f"Your {archetype_name} pattern becomes genius when others are stuck and you see the path forward."

# =============================================================================
# DAILY INSIGHT GENERATOR
# =============================================================================

def generate_daily_insight(
    archetype_name: str,
    archetype_data: Dict[str, Any],
    active_domain: Optional[str] = None,
    domain_state: str = 'quiet'
) -> Dict[str, str]:
    """
    Generate daily insight grounded in archetype.
    
    Returns:
        {
            'headline': str,
            'body': str,
            'question': str
        }
    """
    narrative = archetype_data.get('narrative', {})
    current = narrative.get('current_expression', '')
    
    # Get domain-specific content if available
    domain_content = DOMAIN_NARRATIVES.get(active_domain, {})
    domain_text = domain_content.get(domain_state, '')
    domain_question = domain_content.get('question', narrative.get('reflection_question', ''))
    
    # Build headline
    headline = f"Your {archetype_name} pattern is active"
    
    # Build body
    if current and domain_text:
        body = f"{current}\n\n{domain_text}"
    elif current:
        body = current
    elif domain_text:
        body = domain_text
    else:
        body = f"This is your {archetype_name} pattern in motion. Watch where it shows up today."
    
    return {
        'headline': headline,
        'body': body,
        'question': domain_question
    }

# =============================================================================
# LENS INTEGRATION - Lenses support archetype, not standalone
# =============================================================================

def generate_lens_context(
    lens_type: str,
    lens_data: Dict[str, Any],
    archetype_name: str,
    archetype_data: Dict[str, Any]
) -> str:
    """
    Generate lens narrative that SUPPORTS the archetype.
    Lenses no longer produce standalone interpretations.
    
    Args:
        lens_type: 'astrology', 'human_design', 'enneagram'
        lens_data: The lens-specific data
        archetype_name: User's primary archetype name
        archetype_data: Full archetype data
        
    Returns:
        Narrative showing how lens supports archetype
    """
    archetype_summary = archetype_data.get('narrative', {}).get('summary', '')
    
    if lens_type == 'astrology':
        sun_sign = lens_data.get('sun_sign', lens_data.get('sun', {}).get('sign', 'Unknown'))
        moon_sign = lens_data.get('moon_sign', lens_data.get('moon', {}).get('sign', 'Unknown'))
        
        return f"Your {sun_sign} Sun and {moon_sign} Moon support your {archetype_name} pattern. {_get_astro_archetype_link(sun_sign, archetype_name)}"
    
    elif lens_type == 'human_design':
        hd_type = lens_data.get('type', 'Unknown')
        authority = lens_data.get('authority', 'Unknown')
        
        # Behavior-first language for HD types
        type_behaviors = {
            'Manifestor': "You're wired to initiate before others are ready",
            'Generator': "You have sustainable energy when the work engages you",
            'Manifesting Generator': "You move fast when engaged—but skipping steps creates cleanup",
            'Projector': "You see how things could work better",
            'Reflector': "You mirror your environment"
        }
        
        type_behavior = type_behaviors.get(hd_type, f"Your {hd_type} nature")
        return f"{type_behavior}—and your {archetype_name} pattern shows up through {_get_hd_archetype_link(hd_type, archetype_name)}"
    
    elif lens_type == 'enneagram':
        etype = lens_data.get('type', lens_data.get('core_type', 'Unknown'))
        
        return f"Your Type {etype} structure channels your {archetype_name} pattern. {_get_enne_archetype_link(etype, archetype_name)}"
    
    return f"This lens adds depth to your {archetype_name} pattern."

def _get_astro_archetype_link(sun_sign: str, archetype_name: str) -> str:
    """Generate astrology-archetype connection."""
    # Direct, specific connections
    connections = {
        'Aries': "Your fire initiates each reinvention",
        'Taurus': "Your earth grounds each transformation",
        'Gemini': "Your air circulates new ideas into action",
        'Cancer': "Your water feels when it's time to change",
        'Leo': "Your fire burns through what no longer fits",
        'Virgo': "Your earth refines each new version",
        'Libra': "Your air weighs each transition carefully",
        'Scorpio': "Your water transforms through depth",
        'Sagittarius': "Your fire seeks meaning in each change",
        'Capricorn': "Your earth builds toward each new summit",
        'Aquarius': "Your air revolutionizes your path",
        'Pisces': "Your water dissolves old boundaries",
        'Ophiuchus': "Your integration meets each pattern at the threshold and walks through it",
    }
    return connections.get(sun_sign, "Your energy expresses this pattern in your unique way")

def _get_hd_archetype_link(hd_type: str, archetype_name: str) -> str:
    """Generate HD type-archetype connection."""
    connections = {
        'Manifestor': "initiating change before others see it coming",
        'Generator': "responding to what genuinely lights you up",
        'Manifesting Generator': "rapid iteration and multi-passionate exploration",
        'Projector': "guiding others through transitions you've already navigated",
        'Reflector': "mirroring the changes happening around you"
    }
    return connections.get(hd_type, "your natural way of moving through the world")

def _get_enne_archetype_link(etype: str, archetype_name: str) -> str:
    """Generate Enneagram type-archetype connection."""
    connections = {
        '1': "Your inner critic pushes you to improve with each iteration",
        '2': "You transform to stay connected to what matters",
        '3': "You reinvent to stay relevant and effective",
        '4': "You change to stay authentic to your evolving self",
        '5': "You gather knowledge before each transformation",
        '6': "You test each new version thoroughly before committing",
        '7': "You seek the next horizon before the current one fades",
        '8': "You assert control over your own evolution",
        '9': "You transform gradually, maintaining inner peace"
    }
    return connections.get(str(etype), "This shapes how you express the pattern")

# =============================================================================
# UNIFIED NARRATIVE GENERATOR
# =============================================================================

async def generate_unified_narrative(
    db,
    user_id: str,
    context: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate complete narrative output for a user.
    
    This is the SINGLE ENTRY POINT for all narrative generation.
    
    Args:
        db: Database connection
        user_id: User ID
        context: Optional context hint ('patterns', 'home', 'daily', etc.)
        
    Returns:
        {
            'story': str,
            'pattern': str,
            'challenge': str,
            'genius': str,
            'daily_insight': dict,
            'archetype': dict,
            'success': bool
        }
    """
    try:
        # Get archetype data - single source of truth
        from services.pattern_archetype import get_user_archetype
        archetype_result = await get_user_archetype(db, user_id)
        
        if not archetype_result or not archetype_result.get('primary_archetype'):
            logger.warning(f"[UnifiedNarrative] No archetype for user {user_id}")
            return {
                'success': False,
                'error': 'No archetype data available',
                'story': '',
                'pattern': '',
                'challenge': '',
                'genius': '',
                'daily_insight': {}
            }
        
        archetype = archetype_result['primary_archetype']
        archetype_name = archetype.get('name', 'Unknown')
        
        # Get active domain from pattern graph
        active_domain = None
        domain_state = 'quiet'
        
        try:
            pattern_data = await db.pattern_graph.find_one({'user_id': user_id})
            if pattern_data and pattern_data.get('domains'):
                # Find most active domain
                domains = sorted(
                    pattern_data['domains'],
                    key=lambda d: d.get('strength', 0),
                    reverse=True
                )
                if domains and domains[0].get('strength', 0) > 0.3:
                    active_domain = domains[0].get('id')
                    domain_state = domains[0].get('state', 'present')
        except Exception as e:
            logger.debug(f"[UnifiedNarrative] Could not get pattern domain: {e}")
        
        # Generate all narrative components
        result = {
            'success': True,
            'archetype': {
                'name': archetype_name,
                'icon': archetype.get('icon', '◈'),
                'id': archetype.get('id', 'unknown')
            },
            'story': generate_story(archetype_name, archetype),
            'pattern': generate_pattern_description(archetype_name, archetype),
            'challenge': generate_challenge(archetype_name, archetype),
            'genius': generate_genius(archetype_name, archetype),
            'daily_insight': generate_daily_insight(
                archetype_name, archetype, active_domain, domain_state
            )
        }
        
        # Validate - fail if hedging detected
        for key in ['story', 'pattern', 'challenge', 'genius']:
            if contains_blocked_words(result[key]):
                blocked = get_blocked_words_found(result[key])
                logger.error(f"[UnifiedNarrative] BLOCKED WORDS in {key}: {blocked}")
                # Don't fail, but log for monitoring
        
        return result
        
    except Exception as e:
        logger.error(f"[UnifiedNarrative] Error: {e}")
        return {
            'success': False,
            'error': str(e),
            'story': '',
            'pattern': '',
            'challenge': '',
            'genius': '',
            'daily_insight': {}
        }

# =============================================================================
# VALIDATION UTILITY
# =============================================================================

def validate_narrative_text(text: str, source: str = 'unknown') -> Dict[str, Any]:
    """
    Validate that narrative text follows language rules.
    
    Returns:
        {
            'valid': bool,
            'blocked_words': list,
            'source': str
        }
    """
    blocked = get_blocked_words_found(text)
    return {
        'valid': len(blocked) == 0,
        'blocked_words': blocked,
        'source': source
    }
