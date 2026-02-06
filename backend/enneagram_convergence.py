"""
Enneagram Cross-Lens Convergence Module

This module computes convergence signals from deterministic lenses 
(True Sidereal Astrology + Human Design) to support or weaken 
Enneagram assessment confidence.

CORE PRINCIPLE:
- Enneagram assessment remains the primary determinant
- Other lenses act as confirming or weakening signals, not deciders
- Final output may increase or decrease confidence, but NEVER flips the core type

Version: convergence-v1
"""

from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# CONVERGENCE RULES TABLE
# =============================================================================
# These are deterministic mappings from Astrology/HD signals to Enneagram types
# Each rule adds +0.05 to +0.1 support (capped at +0.15 total)

# TRUE SIDEREAL ASTROLOGY → ENNEAGRAM MAPPINGS
ASTROLOGY_TYPE_SIGNALS = {
    # Sun Sign mappings (primary identity)
    'sun_sign': {
        # Fire signs - expansion, action, assertion
        'Aries': {'types': [7, 8, 3], 'weight': 0.05, 'signal': 'Fire Sun: action-oriented, assertive identity'},
        'Leo': {'types': [3, 7, 8], 'weight': 0.05, 'signal': 'Fire Sun: expressive, recognition-seeking identity'},
        'Sagittarius': {'types': [7, 8, 3], 'weight': 0.07, 'signal': 'Fire Sun: expansion-seeking, freedom-oriented identity'},
        
        # Earth signs - stability, practicality, structure
        'Taurus': {'types': [9, 6, 1], 'weight': 0.05, 'signal': 'Earth Sun: stability-seeking, grounded identity'},
        'Virgo': {'types': [1, 5, 6], 'weight': 0.05, 'signal': 'Earth Sun: detail-oriented, analytical identity'},
        'Capricorn': {'types': [1, 3, 8], 'weight': 0.05, 'signal': 'Earth Sun: duty-focused, achievement-oriented identity'},
        
        # Air signs - mental, social, conceptual
        'Gemini': {'types': [7, 3, 5], 'weight': 0.05, 'signal': 'Air Sun: mentally versatile, variety-seeking identity'},
        'Libra': {'types': [9, 2, 3], 'weight': 0.05, 'signal': 'Air Sun: harmony-seeking, relational identity'},
        'Aquarius': {'types': [5, 7, 4], 'weight': 0.05, 'signal': 'Air Sun: independent, unconventional identity'},
        
        # Water signs - emotional, intuitive, depth
        'Cancer': {'types': [2, 6, 4], 'weight': 0.05, 'signal': 'Water Sun: nurturing, emotionally attuned identity'},
        'Scorpio': {'types': [8, 5, 4], 'weight': 0.05, 'signal': 'Water Sun: intense, investigative identity'},
        'Pisces': {'types': [9, 4, 2], 'weight': 0.05, 'signal': 'Water Sun: receptive, boundary-fluid identity'},
    },
    
    # Moon Sign mappings (emotional patterns)
    'moon_sign': {
        'Aries': {'types': [8, 7, 3], 'weight': 0.04, 'signal': 'Fire Moon: emotionally reactive, quick to act'},
        'Leo': {'types': [3, 2, 7], 'weight': 0.04, 'signal': 'Fire Moon: emotionally expressive, needs recognition'},
        'Sagittarius': {'types': [7, 9, 3], 'weight': 0.05, 'signal': 'Fire Moon: emotionally expansive, optimistic inner life'},
        
        'Taurus': {'types': [9, 6, 2], 'weight': 0.04, 'signal': 'Earth Moon: emotionally steady, comfort-seeking'},
        'Virgo': {'types': [1, 6, 5], 'weight': 0.04, 'signal': 'Earth Moon: emotionally analytical, self-critical'},
        'Capricorn': {'types': [1, 3, 5], 'weight': 0.04, 'signal': 'Earth Moon: emotionally contained, duty-bound'},
        
        'Gemini': {'types': [7, 5, 6], 'weight': 0.04, 'signal': 'Air Moon: emotionally versatile, mentally processing feelings'},
        'Libra': {'types': [9, 2, 3], 'weight': 0.04, 'signal': 'Air Moon: emotionally harmonious, conflict-avoidant'},
        'Aquarius': {'types': [5, 4, 7], 'weight': 0.04, 'signal': 'Air Moon: emotionally detached, independent inner life'},
        
        'Cancer': {'types': [2, 4, 6], 'weight': 0.04, 'signal': 'Water Moon: emotionally nurturing, protective'},
        'Scorpio': {'types': [8, 4, 5], 'weight': 0.04, 'signal': 'Water Moon: emotionally intense, transformative'},
        'Pisces': {'types': [4, 9, 2], 'weight': 0.04, 'signal': 'Water Moon: emotionally absorbent, empathic'},
    },
    
    # Mars Sign mappings (drive, assertion style)
    'mars_sign': {
        'Aries': {'types': [8, 7, 3], 'weight': 0.06, 'signal': 'Mars in Aries: direct, confrontational drive style'},
        'Sagittarius': {'types': [7, 8, 3], 'weight': 0.05, 'signal': 'Mars in Sagittarius: expansive, freedom-seeking drive'},
        'Scorpio': {'types': [8, 5, 4], 'weight': 0.05, 'signal': 'Mars in Scorpio: intense, strategic drive style'},
        'Leo': {'types': [3, 8, 7], 'weight': 0.04, 'signal': 'Mars in Leo: proud, expressive drive style'},
        'Capricorn': {'types': [1, 8, 3], 'weight': 0.04, 'signal': 'Mars in Capricorn: disciplined, ambitious drive'},
    },
    
    # Jupiter Sign mappings (expansion, optimism)
    'jupiter_sign': {
        'Sagittarius': {'types': [7, 9, 3], 'weight': 0.05, 'signal': 'Jupiter in Sagittarius: amplified expansion/optimism'},
        'Leo': {'types': [7, 3, 8], 'weight': 0.04, 'signal': 'Jupiter in Leo: amplified confidence/expression'},
        'Aries': {'types': [7, 8, 3], 'weight': 0.04, 'signal': 'Jupiter in Aries: amplified initiative/action'},
    },
}

# HUMAN DESIGN → ENNEAGRAM MAPPINGS
HUMAN_DESIGN_TYPE_SIGNALS = {
    # Energy Type mappings
    'energy_type': {
        'Manifestor': {'types': [8, 7, 3], 'weight': 0.08, 'signal': 'HD Manifestor: initiating, non-waiting energy'},
        'Generator': {'types': [2, 9, 6], 'weight': 0.05, 'signal': 'HD Generator: responsive, sustainable energy'},
        'Manifesting Generator': {'types': [7, 8, 3], 'weight': 0.07, 'signal': 'HD MG: fast, multi-tracking energy'},
        'Projector': {'types': [5, 2, 4], 'weight': 0.06, 'signal': 'HD Projector: guiding, conserving energy'},
        'Reflector': {'types': [9, 4, 5], 'weight': 0.05, 'signal': 'HD Reflector: sampling, mirroring energy'},
    },
    
    # Authority mappings (decision-making style)
    'authority': {
        'Emotional': {'types': [4, 2, 8], 'weight': 0.04, 'signal': 'Emotional Authority: feeling-based decisions'},
        'Sacral': {'types': [2, 9, 7], 'weight': 0.04, 'signal': 'Sacral Authority: gut-response decisions'},
        'Splenic': {'types': [7, 8, 3], 'weight': 0.05, 'signal': 'Splenic Authority: instinctive, in-the-moment decisions'},
        'Ego Manifested': {'types': [8, 3, 7], 'weight': 0.06, 'signal': 'Ego Authority: willpower-driven decisions'},
        'Ego Projected': {'types': [3, 8, 7], 'weight': 0.05, 'signal': 'Ego Projected Authority: willpower via recognition'},
        'Self-Projected': {'types': [3, 4, 1], 'weight': 0.04, 'signal': 'Self-Projected Authority: identity-anchored decisions'},
        'Mental (None)': {'types': [5, 6, 9], 'weight': 0.04, 'signal': 'No Inner Authority: environmental/sounding board'},
        'Lunar': {'types': [9, 4, 5], 'weight': 0.04, 'signal': 'Lunar Authority: cyclical, reflective decisions'},
    },
    
    # Profile mappings (role in life)
    'profile': {
        '1/3': {'types': [5, 6, 1], 'weight': 0.05, 'signal': 'Profile 1/3: investigative, trial-and-error learning'},
        '1/4': {'types': [5, 6, 2], 'weight': 0.04, 'signal': 'Profile 1/4: investigative, network-building'},
        '2/4': {'types': [9, 2, 4], 'weight': 0.04, 'signal': 'Profile 2/4: natural talent, called out by others'},
        '2/5': {'types': [5, 4, 8], 'weight': 0.04, 'signal': 'Profile 2/5: hermit with universalizing impact'},
        '3/5': {'types': [7, 8, 3], 'weight': 0.05, 'signal': 'Profile 3/5: experiential, resilient, adaptive'},
        '3/6': {'types': [7, 9, 6], 'weight': 0.04, 'signal': 'Profile 3/6: trial-error transitioning to wisdom'},
        '4/6': {'types': [2, 9, 6], 'weight': 0.04, 'signal': 'Profile 4/6: network-based role model'},
        '4/1': {'types': [6, 5, 2], 'weight': 0.04, 'signal': 'Profile 4/1: fixed, foundational networker'},
        '5/1': {'types': [5, 8, 3], 'weight': 0.05, 'signal': 'Profile 5/1: practical universalizer with foundation'},
        '5/2': {'types': [5, 4, 8], 'weight': 0.04, 'signal': 'Profile 5/2: called heretic with natural gifts'},
        '6/2': {'types': [9, 2, 7], 'weight': 0.04, 'signal': 'Profile 6/2: role model with natural talents'},
        '6/3': {'types': [7, 9, 6], 'weight': 0.04, 'signal': 'Profile 6/3: experiential path to role model'},
    },
    
    # Defined Centers (specific patterns)
    'defined_centers': {
        'Root Defined': {'types': [8, 3, 1], 'weight': 0.03, 'signal': 'Root Defined: consistent pressure/drive handling'},
        'Will (Heart/Ego) Defined': {'types': [8, 3, 7], 'weight': 0.05, 'signal': 'Will Defined: consistent willpower access'},
        'Ajna Defined': {'types': [5, 1, 6], 'weight': 0.03, 'signal': 'Ajna Defined: consistent mental processing'},
        'Throat Defined': {'types': [3, 7, 8], 'weight': 0.03, 'signal': 'Throat Defined: consistent manifestation capacity'},
        'G Center Defined': {'types': [4, 1, 3], 'weight': 0.03, 'signal': 'G Defined: consistent identity/direction'},
        'Spleen Defined': {'types': [7, 8, 6], 'weight': 0.03, 'signal': 'Spleen Defined: consistent survival instincts'},
        'Sacral Defined': {'types': [2, 9, 7], 'weight': 0.03, 'signal': 'Sacral Defined: consistent life force energy'},
        'Solar Plexus Defined': {'types': [4, 2, 8], 'weight': 0.03, 'signal': 'Solar Plexus Defined: emotional wave processing'},
    },
}


def compute_astrology_signals(astrology_data: Dict) -> List[Dict]:
    """
    Extract Enneagram-supporting signals from True Sidereal Astrology data.
    
    Args:
        astrology_data: Dict containing sun_sign, moon_sign, planets, etc.
    
    Returns:
        List of signal dicts with lens, signal text, supported types, and weight
    """
    signals = []
    
    if not astrology_data:
        return signals
    
    # Check planets dict for signs
    planets = astrology_data.get('planets', {})
    
    # Sun Sign
    sun_data = planets.get('Sun', {})
    sun_sign = sun_data.get('sign') if isinstance(sun_data, dict) else None
    if sun_sign and sun_sign in ASTROLOGY_TYPE_SIGNALS['sun_sign']:
        rule = ASTROLOGY_TYPE_SIGNALS['sun_sign'][sun_sign]
        signals.append({
            'lens': 'sidereal_astrology',
            'signal': rule['signal'],
            'supports_types': rule['types'],
            'weight': rule['weight']
        })
    
    # Moon Sign
    moon_data = planets.get('Moon', {})
    moon_sign = moon_data.get('sign') if isinstance(moon_data, dict) else None
    if moon_sign and moon_sign in ASTROLOGY_TYPE_SIGNALS['moon_sign']:
        rule = ASTROLOGY_TYPE_SIGNALS['moon_sign'][moon_sign]
        signals.append({
            'lens': 'sidereal_astrology',
            'signal': rule['signal'],
            'supports_types': rule['types'],
            'weight': rule['weight']
        })
    
    # Mars Sign
    mars_data = planets.get('Mars', {})
    mars_sign = mars_data.get('sign') if isinstance(mars_data, dict) else None
    if mars_sign and mars_sign in ASTROLOGY_TYPE_SIGNALS.get('mars_sign', {}):
        rule = ASTROLOGY_TYPE_SIGNALS['mars_sign'][mars_sign]
        signals.append({
            'lens': 'sidereal_astrology',
            'signal': rule['signal'],
            'supports_types': rule['types'],
            'weight': rule['weight']
        })
    
    # Jupiter Sign
    jupiter_data = planets.get('Jupiter', {})
    jupiter_sign = jupiter_data.get('sign') if isinstance(jupiter_data, dict) else None
    if jupiter_sign and jupiter_sign in ASTROLOGY_TYPE_SIGNALS.get('jupiter_sign', {}):
        rule = ASTROLOGY_TYPE_SIGNALS['jupiter_sign'][jupiter_sign]
        signals.append({
            'lens': 'sidereal_astrology',
            'signal': rule['signal'],
            'supports_types': rule['types'],
            'weight': rule['weight']
        })
    
    return signals


def compute_human_design_signals(hd_data: Dict) -> List[Dict]:
    """
    Extract Enneagram-supporting signals from Human Design data.
    
    Args:
        hd_data: Dict containing energy_type, authority, profile, defined_centers, etc.
    
    Returns:
        List of signal dicts with lens, signal text, supported types, and weight
    """
    signals = []
    
    if not hd_data:
        return signals
    
    # Energy Type
    energy_type = hd_data.get('type') or hd_data.get('energy_type')
    if energy_type and energy_type in HUMAN_DESIGN_TYPE_SIGNALS['energy_type']:
        rule = HUMAN_DESIGN_TYPE_SIGNALS['energy_type'][energy_type]
        signals.append({
            'lens': 'human_design',
            'signal': rule['signal'],
            'supports_types': rule['types'],
            'weight': rule['weight']
        })
    
    # Authority
    authority = hd_data.get('authority')
    if authority:
        # Normalize authority names
        auth_key = authority
        if 'Emotional' in authority or 'Solar Plexus' in authority:
            auth_key = 'Emotional'
        elif 'Sacral' in authority:
            auth_key = 'Sacral'
        elif 'Splenic' in authority:
            auth_key = 'Splenic'
        elif 'Ego Manifested' in authority:
            auth_key = 'Ego Manifested'
        elif 'Ego Projected' in authority:
            auth_key = 'Ego Projected'
        elif 'Self-Projected' in authority or 'Self Projected' in authority:
            auth_key = 'Self-Projected'
        elif 'None' in authority or 'Mental' in authority:
            auth_key = 'Mental (None)'
        elif 'Lunar' in authority:
            auth_key = 'Lunar'
            
        if auth_key in HUMAN_DESIGN_TYPE_SIGNALS['authority']:
            rule = HUMAN_DESIGN_TYPE_SIGNALS['authority'][auth_key]
            signals.append({
                'lens': 'human_design',
                'signal': rule['signal'],
                'supports_types': rule['types'],
                'weight': rule['weight']
            })
    
    # Profile
    profile = hd_data.get('profile')
    if profile and profile in HUMAN_DESIGN_TYPE_SIGNALS['profile']:
        rule = HUMAN_DESIGN_TYPE_SIGNALS['profile'][profile]
        signals.append({
            'lens': 'human_design',
            'signal': rule['signal'],
            'supports_types': rule['types'],
            'weight': rule['weight']
        })
    
    # Defined Centers
    defined_centers = hd_data.get('defined_centers', [])
    if isinstance(defined_centers, list):
        for center in defined_centers:
            center_key = f"{center} Defined"
            if center_key in HUMAN_DESIGN_TYPE_SIGNALS.get('defined_centers', {}):
                rule = HUMAN_DESIGN_TYPE_SIGNALS['defined_centers'][center_key]
                signals.append({
                    'lens': 'human_design',
                    'signal': rule['signal'],
                    'supports_types': rule['types'],
                    'weight': rule['weight']
                })
    
    return signals


def compute_convergence(
    enneagram_result: Dict,
    astrology_data: Optional[Dict] = None,
    human_design_data: Optional[Dict] = None
) -> Dict:
    """
    Compute cross-lens convergence score for Enneagram determination.
    
    This function:
    1. Extracts signals from Astrology and Human Design
    2. Computes support score for the inferred Enneagram type
    3. Adjusts confidence (capped at +0.15, never flips type)
    4. Generates user-facing summary
    
    Args:
        enneagram_result: Dict with inferred_core, confidence, confidence_tier, etc.
        astrology_data: Optional dict with astrology chart data
        human_design_data: Optional dict with HD chart data
    
    Returns:
        Dict with convergence data including:
        - supported_types: list of types supported by other lenses
        - support_score: 0.0-0.15 aggregate support
        - confidence_adjustment: -0.1, 0, or +0.1
        - signals: list of individual signal objects
        - convergence_summary: user-facing string
    """
    inferred_core = enneagram_result.get('inferred_core')
    original_confidence = enneagram_result.get('confidence', 0)
    original_tier = enneagram_result.get('confidence_tier', 'low')
    
    if not inferred_core:
        return {
            'supported_types': [],
            'support_score': 0.0,
            'confidence_adjustment': 0,
            'signals': [],
            'convergence_summary': 'No Enneagram type to converge on.'
        }
    
    # Collect all signals
    all_signals = []
    all_signals.extend(compute_astrology_signals(astrology_data or {}))
    all_signals.extend(compute_human_design_signals(human_design_data or {}))
    
    if not all_signals:
        return {
            'supported_types': [],
            'support_score': 0.0,
            'confidence_adjustment': 0,
            'signals': [],
            'convergence_summary': 'Other lenses show mixed or neutral alignment.'
        }
    
    # Compute support score for inferred type
    type_support = {t: 0.0 for t in range(1, 10)}
    formatted_signals = []
    
    for sig in all_signals:
        supported = sig['supports_types']
        weight = sig['weight']
        
        # Add weight to supported types
        for t in supported:
            type_support[t] += weight
        
        # Format signal for output
        formatted_signals.append({
            'lens': sig['lens'],
            'signal': sig['signal'],
            'supports_types': supported
        })
    
    # Get support for inferred type (capped at 0.15)
    raw_support = type_support.get(inferred_core, 0.0)
    support_score = min(raw_support, 0.15)
    
    # Determine which types are most supported
    sorted_support = sorted(type_support.items(), key=lambda x: x[1], reverse=True)
    supported_types = [t for t, s in sorted_support if s > 0][:3]
    
    # Compute confidence adjustment
    # Rule: Never flip type, only adjust confidence
    confidence_adjustment = 0.0
    
    if support_score >= 0.10:
        # Strong convergence
        if original_tier == 'high':
            # Already high - reinforce language only (or +0.05 optional)
            confidence_adjustment = 0.05
        elif original_tier == 'medium':
            # Medium can become high
            confidence_adjustment = 0.10
        else:
            # Low gets moderate boost
            confidence_adjustment = 0.05
    elif support_score >= 0.05:
        # Moderate convergence
        if original_tier == 'medium':
            confidence_adjustment = 0.05
        elif original_tier == 'low':
            confidence_adjustment = 0.05
    elif support_score < 0.02 and len(all_signals) >= 3:
        # Weak/no support despite having signals = potential mismatch
        confidence_adjustment = -0.05
    
    # Check if inferred type is actually supported by other lenses
    inferred_rank = next((i for i, (t, s) in enumerate(sorted_support) if t == inferred_core), 9)
    if inferred_rank > 2 and support_score < 0.05:
        # Inferred type not in top 3 supported types - weak convergence
        confidence_adjustment = min(confidence_adjustment, 0)
    
    # Generate user-facing summary
    if support_score >= 0.10:
        convergence_summary = f"Multiple lenses align with Type {inferred_core} patterns."
    elif support_score >= 0.05:
        convergence_summary = f"Some cross-lens support for Type {inferred_core} patterns."
    elif inferred_core in supported_types:
        convergence_summary = "Partial alignment with other lens patterns."
    else:
        convergence_summary = "Other lenses show mixed or neutral alignment."
    
    return {
        'supported_types': supported_types,
        'support_score': round(support_score, 4),
        'confidence_adjustment': round(confidence_adjustment, 2),
        'signals': formatted_signals,
        'convergence_summary': convergence_summary,
        # Debug data
        'type_support_breakdown': {str(t): round(s, 4) for t, s in sorted_support if s > 0}
    }


def apply_convergence_to_result(
    enneagram_result: Dict,
    convergence: Dict
) -> Dict:
    """
    Apply convergence adjustments to Enneagram result.
    
    IMPORTANT: This NEVER changes inferred_core type.
    It only adjusts confidence metrics.
    
    Args:
        enneagram_result: Original Enneagram result dict
        convergence: Convergence data from compute_convergence()
    
    Returns:
        Updated Enneagram result with convergence-adjusted confidence
    """
    result = enneagram_result.copy()
    
    adjustment = convergence.get('confidence_adjustment', 0)
    original_confidence = result.get('confidence', 0)
    original_tier = result.get('confidence_tier', 'low')
    
    # Apply adjustment (keep within 0-1 bounds)
    new_confidence = max(0.0, min(1.0, original_confidence + adjustment))
    result['confidence'] = round(new_confidence, 4)
    
    # Recalculate confidence tier based on new confidence + gap
    top_candidates = result.get('top_candidates', [])
    if len(top_candidates) >= 2:
        gap = top_candidates[0].get('probability', 0) - top_candidates[1].get('probability', 0)
    else:
        gap = new_confidence
    
    # Apply tier rules with convergence boost
    support_score = convergence.get('support_score', 0)
    
    if new_confidence >= 0.45 and gap >= 0.15:
        new_tier = 'high'
    elif new_confidence >= 0.33 and gap >= 0.08:
        # Check if convergence pushes medium → high
        if original_tier == 'medium' and support_score >= 0.10:
            new_tier = 'high'
        else:
            new_tier = 'medium'
    else:
        new_tier = 'low'
    
    result['confidence_tier'] = new_tier
    result['convergence'] = convergence
    
    return result


# =============================================================================
# CONVERGENCE RULES TABLE (for documentation)
# =============================================================================

CONVERGENCE_RULES_TABLE = """
CROSS-LENS CONVERGENCE RULES (v1)
=================================

TRUE SIDEREAL ASTROLOGY → ENNEAGRAM
-----------------------------------
| Signal Type | Condition | Supports Types | Weight |
|-------------|-----------|----------------|--------|
| Sun Sign | Fire (Aries/Leo/Sag) | 7, 8, 3 | +0.05-0.07 |
| Sun Sign | Earth (Taurus/Virgo/Cap) | 1, 5, 6, 9 | +0.05 |
| Sun Sign | Air (Gemini/Libra/Aqua) | 5, 7, 9 | +0.05 |
| Sun Sign | Water (Cancer/Scorp/Pisces) | 2, 4, 8 | +0.05 |
| Moon Sign | Fire | 7, 8, 3 | +0.04-0.05 |
| Moon Sign | Water | 2, 4, 8 | +0.04 |
| Mars Sign | Aries/Scorpio | 8, 7, 5 | +0.05-0.06 |
| Jupiter Sign | Sag/Leo/Aries | 7, 3, 8 | +0.04-0.05 |

HUMAN DESIGN → ENNEAGRAM
------------------------
| Signal Type | Condition | Supports Types | Weight |
|-------------|-----------|----------------|--------|
| Energy Type | Manifestor | 8, 7, 3 | +0.08 |
| Energy Type | Manifesting Generator | 7, 8, 3 | +0.07 |
| Energy Type | Generator | 2, 9, 6 | +0.05 |
| Energy Type | Projector | 5, 2, 4 | +0.06 |
| Authority | Splenic | 7, 8, 3 | +0.05 |
| Authority | Ego Manifested | 8, 3, 7 | +0.06 |
| Authority | Emotional | 4, 2, 8 | +0.04 |
| Profile | 3/5 | 7, 8, 3 | +0.05 |
| Profile | 1/3 | 5, 6, 1 | +0.05 |
| Profile | 5/1 | 5, 8, 3 | +0.05 |
| Defined Center | Will/Ego | 8, 3, 7 | +0.05 |
| Defined Center | Spleen | 7, 8, 6 | +0.03 |

CONFIDENCE ADJUSTMENT RULES
---------------------------
| Support Score | Original Tier | Adjustment | New Tier Possible |
|---------------|---------------|------------|-------------------|
| ≥0.10 | High | +0.05 | High (reinforced) |
| ≥0.10 | Medium | +0.10 | → High |
| ≥0.10 | Low | +0.05 | → Medium |
| ≥0.05 | Medium | +0.05 | Medium |
| ≥0.05 | Low | +0.05 | Low |
| <0.02 (3+ signals) | Any | -0.05 | Lower |

HARD CONSTRAINTS
----------------
- Total support_score CAPPED at 0.15
- confidence_adjustment RANGE: -0.10 to +0.10
- NEVER flip dominant type
- NEVER introduce new dominant type
"""


def get_convergence_rules_table() -> str:
    """Return the convergence rules documentation."""
    return CONVERGENCE_RULES_TABLE
