"""
Numerology Pattern System Service

Task: Transform numerology from descriptive personality text into 
diagnostic pattern recognition system.

Provides:
- Lo Shu Grid computation
- Core pattern generation (sharp, confronting)
- Behavioral manifestations
- Internal tensions
- Precise reflection questions
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# =============================================================================
# LO SHU GRID COMPUTATION
# =============================================================================

def compute_lo_shu_grid(birth_date: datetime) -> Dict[str, Any]:
    """
    Compute Lo Shu Grid from birth date.
    
    The Lo Shu Grid is a 3x3 grid showing presence/absence of numbers 1-9.
    Numbers are derived from the birth date digits.
    
    Grid positions:
    4 | 9 | 2
    3 | 5 | 7  
    8 | 1 | 6
    
    Returns:
        {
            'lo_shu_template': [[4,9,2],[3,5,7],[8,1,6]],
            'lo_shu_counts': {'1': 2, '8': 1, ...},
            'lo_shu_display': [["4","9","—"],["—","—","—"],["8","1 1","6"]],
            'present_numbers': {'1': 2, '8': 1, ...},
            'missing_numbers': [3, 5, 7]
        }
    """
    # Extract all digits from birth date
    date_str = birth_date.strftime('%d%m%Y')  # e.g., "01111988"
    digits = [int(d) for d in date_str if d != '0']  # Remove zeros
    
    # Count occurrences of each number 1-9
    present_numbers = {}
    for d in digits:
        if 1 <= d <= 9:
            present_numbers[str(d)] = present_numbers.get(str(d), 0) + 1
    
    # Find missing numbers
    missing_numbers = [n for n in range(1, 10) if str(n) not in present_numbers]
    
    # Standard Lo Shu grid template (positions)
    lo_shu_template = [[4, 9, 2], [3, 5, 7], [8, 1, 6]]
    
    # Build display grid with actual user data
    lo_shu_display = []
    for row in lo_shu_template:
        display_row = []
        for num in row:
            count = present_numbers.get(str(num), 0)
            if count == 0:
                display_row.append("—")
            elif count == 1:
                display_row.append(str(num))
            else:
                # Repeat the number for multiple occurrences
                display_row.append(" ".join([str(num)] * count))
        lo_shu_display.append(display_row)
    
    return {
        'lo_shu_template': lo_shu_template,
        'lo_shu_counts': present_numbers,
        'lo_shu_display': lo_shu_display,
        'present_numbers': present_numbers,
        'missing_numbers': missing_numbers
    }

# =============================================================================
# NUMBER MEANINGS FOR PATTERN GENERATION
# =============================================================================

NUMBER_CORE_MEANINGS = {
    1: {'energy': 'initiation, independence, action', 'shadow': 'isolation, domination', 'verb': 'initiates'},
    2: {'energy': 'sensitivity, partnership, processing', 'shadow': 'dependency, over-accommodation', 'verb': 'connects'},
    3: {'energy': 'expression, creativity, joy', 'shadow': 'superficiality, scattered energy', 'verb': 'expresses'},
    4: {'energy': 'stability, structure, grounding', 'shadow': 'rigidity, limitation', 'verb': 'builds'},
    5: {'energy': 'freedom, change, experience', 'shadow': 'restlessness, excess', 'verb': 'moves'},
    6: {'energy': 'responsibility, care, harmony', 'shadow': 'martyrdom, control', 'verb': 'nurtures'},
    7: {'energy': 'analysis, depth, spirituality', 'shadow': 'isolation, cynicism', 'verb': 'analyzes'},
    8: {'energy': 'power, manifestation, karma', 'shadow': 'materialism, manipulation', 'verb': 'manifests'},
    9: {'energy': 'completion, wisdom, service', 'shadow': 'martyrdom, escapism', 'verb': 'completes'},
    11: {'energy': 'intuition, inspiration, vision', 'shadow': 'anxiety, impracticality', 'verb': 'illuminates'},
    22: {'energy': 'mastery, large-scale building', 'shadow': 'overwhelm, scattered power', 'verb': 'constructs'},
    33: {'energy': 'teaching, healing, compassion', 'shadow': 'self-sacrifice, delusion', 'verb': 'heals'}
}

# =============================================================================
# CORE PATTERN GENERATOR
# =============================================================================

def generate_core_pattern(
    life_path: int,
    expression: Optional[int],
    soul_urge: Optional[int],
    missing_numbers: List[int]
) -> str:
    """
    Generate a sharp, confronting core pattern statement.
    
    Format: 1-2 lines max, direct, no hedging.
    
    Examples:
    - "You are built to see quickly and move quickly—but not naturally built to stabilize or express what you see."
    - "You initiate powerfully but struggle to follow through on emotional commitments."
    """
    lp_meaning = NUMBER_CORE_MEANINGS.get(life_path, {})
    lp_verb = lp_meaning.get('verb', 'moves')
    lp_energy = lp_meaning.get('energy', 'action')
    
    # Start with life path core
    pattern_parts = []
    
    # Life path strength
    if life_path == 1:
        pattern_parts.append("You initiate quickly and act decisively")
    elif life_path == 2:
        pattern_parts.append("You read emotional undercurrents that others miss")
    elif life_path == 3:
        pattern_parts.append("You communicate naturally and crave expression")
    elif life_path == 4:
        pattern_parts.append("You build steadily and value what lasts")
    elif life_path == 5:
        pattern_parts.append("You adapt rapidly and need constant movement")
    elif life_path == 6:
        pattern_parts.append("You take responsibility even when it isn't yours")
    elif life_path == 7:
        pattern_parts.append("You analyze deeply before committing to anything")
    elif life_path == 8:
        pattern_parts.append("You see power dynamics clearly and navigate them well")
    elif life_path == 9:
        pattern_parts.append("You see the larger picture that others struggle to grasp")
    elif life_path == 11:
        pattern_parts.append("You perceive things before they become visible to others")
    elif life_path == 22:
        pattern_parts.append("You think in systems and structures that span years")
    elif life_path == 33:
        pattern_parts.append("You absorb others' pain without being asked")
    else:
        pattern_parts.append("You carry a unique energetic signature")
    
    # Add missing number tension
    if missing_numbers:
        missing_str = ', '.join([str(n) for n in missing_numbers[:3]])
        
        if 3 in missing_numbers:
            pattern_parts.append("—but expressing what you know doesn't come naturally")
        elif 4 in missing_numbers:
            pattern_parts.append("—but stabilizing and grounding your insights is a struggle")
        elif 5 in missing_numbers:
            pattern_parts.append("—but adapting to rapid change feels forced")
        elif 6 in missing_numbers:
            pattern_parts.append("—but domestic harmony eludes you")
        elif 7 in missing_numbers:
            pattern_parts.append("—but deep analysis feels like work, not instinct")
        elif 2 in missing_numbers:
            pattern_parts.append("—but emotional nuance isn't your native language")
        elif 1 in missing_numbers:
            pattern_parts.append("—but initiating alone is uncomfortable")
        elif 8 in missing_numbers:
            pattern_parts.append("—but material mastery doesn't hold your attention")
        elif 9 in missing_numbers:
            pattern_parts.append("—but letting go and completing cycles is hard")
        else:
            pattern_parts.append(f"—missing {missing_str} creates gaps in your natural flow")
    
    return ''.join(pattern_parts) + '.'

# =============================================================================
# HOW THIS SHOWS UP GENERATOR
# =============================================================================

def generate_how_this_shows_up(
    life_path: int,
    expression: Optional[int],
    missing_numbers: List[int],
    present_counts: Dict[str, int]
) -> List[str]:
    """
    Generate 3-5 specific behavioral tendencies.
    
    Rules:
    - Real behavioral patterns only
    - Grounded, not absolute
    - Confronting but fair
    - Behavioral, not mystical
    """
    behaviors = []
    
    # Life path behaviors - refined to be less absolute
    lp_behaviors = {
        1: [
            "You often start projects before fully mapping them out - and frequently finish them anyway",
            "You tend to resist asking for help until you've already tried on your own",
            "Your pace of decision-making can outrun those around you"
        ],
        2: [
            "You often pick up on tension in a room before it's spoken",
            "You tend to over-explain when you sense you're being misunderstood",
            "You may give more than you receive in many relationships"
        ],
        3: [
            "You often have multiple creative threads open at once",
            "Thinking tends to happen out loud for you - talking is processing",
            "Your emotional state can visibly influence the energy around you"
        ],
        4: [
            "Chaotic environments tend to create physical discomfort for you",
            "You often create systems even when no one requests them",
            "Shortcuts that skip necessary steps tend to bother you"
        ],
        5: [
            "Routine can feel constraining even when you chose it",
            "You may leave situations before they become fully unbearable",
            "You're often drawn to people and places that challenge your current setup"
        ],
        6: [
            "You often take on other people's problems as your responsibility",
            "You may sacrifice personal needs to maintain harmony around you",
            "You can feel responsible for outcomes outside your direct control"
        ],
        7: [
            "You tend to research extensively before making commitments",
            "Processing time alone is often necessary, even for positive experiences",
            "Your own analysis usually carries more weight than outside opinions"
        ],
        8: [
            "You often notice the power dynamics in any room you enter",
            "High-stakes decisions tend to feel comfortable rather than stressful",
            "You track value and results in situations where others don't"
        ],
        9: [
            "You often see patterns that connect seemingly unrelated events",
            "Endings and transitions tend to draw your attention",
            "You may release attachments with less difficulty than most"
        ],
        11: [
            "Insights often arrive before you have language for them",
            "You may sense things unfolding before concrete evidence appears",
            "Environments that others tolerate can feel overwhelming to you"
        ],
        22: [
            "Your thinking often operates on longer timelines than those around you",
            "Small-scale solutions can feel frustrating when bigger structures are needed",
            "You tend to build frameworks - physical, organizational, or conceptual"
        ],
        33: [
            "You often absorb the emotional weight others are carrying",
            "People frequently share their struggles with you without prompting",
            "Teaching happens through your presence as much as your words"
        ]
    }
    
    behaviors.extend(lp_behaviors.get(life_path, [
        "Your patterns follow a rhythm that's distinctly yours",
        "Your life operates on a beat that doesn't match conventional timelines"
    ]))
    
    # Add missing number behaviors - softer language
    for missing in missing_numbers[:2]:
        missing_behaviors = {
            1: "Group consensus may carry more weight for you than solo conviction",
            2: "The larger pattern can grab your attention before relational nuance registers",
            3: "Articulating what you're thinking may take more effort than thinking it",
            4: "Starting strong comes naturally, but sustained maintenance can drain energy",
            5: "Familiar patterns can feel safer than necessary change, even when change would help",
            6: "Domestic responsibilities may feel like an interruption rather than a calling",
            7: "Decisions sometimes happen before deep analysis has run its course",
            8: "Value and material results may get less tracking than other priorities",
            9: "Letting go of what's complete can take longer than it needs to"
        }
        if missing in missing_behaviors:
            behaviors.append(missing_behaviors[missing])
    
    # Check for repeated numbers (emphasis) - softer
    for num_str, count in present_counts.items():
        if count >= 2:
            num = int(num_str)
            emphasis_behaviors = {
                1: "Independence is amplified - self-reliance runs strong in your pattern",
                2: "Sensitivity is heightened - you tend to feel things with extra depth",
                3: "Expressiveness is doubled - communication is a constant current",
                4: "Structure needs are intensified - chaos tolerance runs low",
                5: "The pull toward change is urgent - stability can feel like stagnation",
                6: "Responsibility runs strong - you may carry more than your share",
                7: "Analysis runs deep - thinking tends to be thorough, sometimes excessively",
                8: "Power awareness is amplified - results and outcomes stay in focus",
                9: "The big picture dominates - but so does the pull to disengage"
            }
            if num in emphasis_behaviors:
                behaviors.append(emphasis_behaviors[num])
    
    return behaviors[:5]  # Max 5 behaviors

# =============================================================================
# INTERNAL TENSION GENERATOR
# =============================================================================

def generate_internal_tensions(
    life_path: int,
    expression: Optional[int],
    soul_urge: Optional[int],
    missing_numbers: List[int],
    present_counts: Dict[str, int]
) -> List[Dict[str, str]]:
    """
    Generate 2-3 X vs Y tensions.
    
    Format:
    {
        'a': 'Fast action (1)',
        'b': 'emotional processing (2)',
        'description': 'You move before you feel—then the feelings catch up'
    }
    """
    tensions = []
    
    # Life path vs missing number tensions
    lp_meaning = NUMBER_CORE_MEANINGS.get(life_path, {})
    
    for missing in missing_numbers[:2]:
        missing_meaning = NUMBER_CORE_MEANINGS.get(missing, {})
        
        tension_map = {
            (1, 2): {
                'a': f'Fast action ({life_path})',
                'b': f'emotional processing ({missing})',
                'description': 'You move before you feel—then the feelings catch up later'
            },
            (1, 4): {
                'a': f'Quick initiation ({life_path})',
                'b': f'stable foundation ({missing})',
                'description': 'You start quickly but building something lasting takes effort'
            },
            (2, 1): {
                'a': f'Sensitivity ({life_path})',
                'b': f'decisive action ({missing})',
                'description': 'You feel everything but acting on it does not come naturally'
            },
            (3, 7): {
                'a': f'Expression ({life_path})',
                'b': f'deep analysis ({missing})',
                'description': 'You speak before you have fully understood - wisdom lags behind words'
            },
            (5, 4): {
                'a': f'Constant movement ({life_path})',
                'b': f'stable grounding ({missing})',
                'description': 'You crave change but lack the foundation to sustain it'
            },
            (7, 3): {
                'a': f'Deep analysis ({life_path})',
                'b': f'free expression ({missing})',
                'description': 'You understand deeply but struggle to communicate what you know'
            },
            (11, 4): {
                'a': f'Vision ({life_path})',
                'b': f'practical grounding ({missing})',
                'description': 'You see far ahead but building the bridge there is frustrating'
            }
        }
        
        key = (life_path if life_path <= 9 else life_path, missing)
        if key in tension_map:
            tensions.append(tension_map[key])
        elif (missing, life_path if life_path <= 9 else life_path) in tension_map:
            tensions.append(tension_map[(missing, life_path if life_path <= 9 else life_path)])
    
    # Add expression vs soul urge tension if both present
    if expression and soul_urge and expression != soul_urge:
        exp_verb = NUMBER_CORE_MEANINGS.get(expression, {}).get('verb', 'acts')
        su_verb = NUMBER_CORE_MEANINGS.get(soul_urge, {}).get('verb', 'wants')
        
        tensions.append({
            'a': f'How you present ({expression})',
            'b': f'what you truly want ({soul_urge})',
            'description': f'The face you show {exp_verb}—but your soul {su_verb} something different'
        })
    
    # Add doubled number tension
    for num_str, count in present_counts.items():
        if count >= 2:
            num = int(num_str)
            if num in NUMBER_CORE_MEANINGS:
                meaning = NUMBER_CORE_MEANINGS[num]
                tensions.append({
                    'a': f'Amplified {meaning["energy"].split(",")[0]} ({num}×{count})',
                    'b': 'balance and moderation',
                    'description': f'This energy is doubled—making it both a gift and a blind spot'
                })
                break  # Only one doubled number tension
    
    return tensions[:3]  # Max 3 tensions

# =============================================================================
# MIRROR MOMENT GENERATOR
# =============================================================================

def generate_mirror_moment(
    life_path: int,
    tensions: List[Dict[str, str]],
    missing_numbers: List[int]
) -> str:
    """
    Generate a precise reflection question based on the pattern tensions.
    
    Not generic—must be derived from the specific tensions identified.
    """
    if tensions:
        # Use the primary tension to generate the question
        primary_tension = tensions[0]
        a = primary_tension['a'].split('(')[0].strip().lower()
        b = primary_tension['b'].split('(')[0].strip().lower()
        
        return f"Where in your life is {a} running ahead of {b}—and what would it cost to slow down?"
    
    # Fallback based on missing numbers
    if missing_numbers:
        missing = missing_numbers[0]
        missing_energy = NUMBER_CORE_MEANINGS.get(missing, {}).get('energy', 'this energy').split(',')[0]
        return f"Where are you compensating for the absence of {missing_energy}—and is it working?"
    
    # Life path fallback
    lp_energy = NUMBER_CORE_MEANINGS.get(life_path, {}).get('energy', 'your core energy').split(',')[0]
    return f"Where is your {lp_energy} serving you—and where has it become a pattern you're running on autopilot?"

# =============================================================================
# MAIN PATTERN COMPUTATION
# =============================================================================

async def compute_numerology_pattern(
    db,
    user_id: str,
    birth_date: datetime,
    full_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Compute the complete numerology pattern system for a user.
    
    Returns:
        {
            'life_path': int,
            'expression': int | null,
            'soul_urge': int | null,
            'personality': int | null,
            'birth_date': str,
            'lo_shu_grid': [[int]],
            'present_numbers': {str: int},
            'missing_numbers': [int],
            'core_pattern': str,
            'how_this_shows_up': [str],
            'internal_tensions': [{a, b, description}],
            'mirror_moment': str
        }
    """
    from calculations.numerology import (
        calculate_life_path,
        calculate_expression_number,
        calculate_soul_urge,
        calculate_personality_number
    )
    
    # Calculate core numbers
    life_path_result = calculate_life_path(birth_date)
    life_path = life_path_result['number']
    
    expression = None
    soul_urge = None
    personality = None
    
    if full_name:
        expression_result = calculate_expression_number(full_name)
        expression = expression_result['number']
        
        soul_urge_result = calculate_soul_urge(full_name)
        soul_urge = soul_urge_result['number']
        
        personality_result = calculate_personality_number(full_name)
        personality = personality_result['number']
    
    # Compute Lo Shu grid
    lo_shu = compute_lo_shu_grid(birth_date)
    
    # Generate pattern content
    core_pattern = generate_core_pattern(
        life_path, expression, soul_urge, lo_shu['missing_numbers']
    )
    
    how_shows_up = generate_how_this_shows_up(
        life_path, expression, lo_shu['missing_numbers'], lo_shu['present_numbers']
    )
    
    internal_tensions = generate_internal_tensions(
        life_path, expression, soul_urge, 
        lo_shu['missing_numbers'], lo_shu['present_numbers']
    )
    
    mirror_moment = generate_mirror_moment(
        life_path, internal_tensions, lo_shu['missing_numbers']
    )
    
    return {
        'life_path': life_path,
        'expression': expression,
        'soul_urge': soul_urge,
        'personality': personality,
        'birth_date': birth_date.isoformat(),
        # New Lo Shu structure (Task: API Data Contract Cleanup)
        'lo_shu_template': lo_shu['lo_shu_template'],
        'lo_shu_counts': lo_shu['lo_shu_counts'],
        'lo_shu_display': lo_shu['lo_shu_display'],
        # Keep these for backward compatibility
        'present_numbers': lo_shu['present_numbers'],
        'missing_numbers': lo_shu['missing_numbers'],
        # Pattern content
        'core_pattern': core_pattern,
        'how_this_shows_up': how_shows_up,
        'internal_tensions': internal_tensions,
        'mirror_moment': mirror_moment
    }
