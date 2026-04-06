"""
Numerology Compute Service
===========================

DETERMINISTIC COMPUTATION LAYER
===============================
This service provides pure, deterministic numerology calculations.
No LLM involved. All outputs are reproducible and transparent.

COMPUTE ≠ SURFACED ≠ INTERPRETED

Systems:
1. Pythagorean (Western) - Name-based calculations
2. Lo Shu (Vedic) - Birth date digit distribution

Author: Mirror System
"""

from datetime import datetime
from typing import Dict, List, Optional, Any


# =============================================================================
# PYTHAGOREAN LETTER VALUES (Western Numerology)
# =============================================================================

PYTHAGOREAN_VALUES = {
    'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8, 'I': 9,
    'J': 1, 'K': 2, 'L': 3, 'M': 4, 'N': 5, 'O': 6, 'P': 7, 'Q': 8, 'R': 9,
    'S': 1, 'T': 2, 'U': 3, 'V': 4, 'W': 5, 'X': 6, 'Y': 7, 'Z': 8
}

VOWELS = set('AEIOU')


# =============================================================================
# CORE REDUCTION FUNCTION
# =============================================================================

def reduce_to_single_digit(number: int, allow_master: bool = True) -> int:
    """Reduce number to single digit (or master number 11, 22, 33)"""
    while number > 9:
        if allow_master and number in [11, 22, 33]:
            return number
        number = sum(int(digit) for digit in str(number))
    return number


# =============================================================================
# PYTHAGOREAN CALCULATIONS
# =============================================================================

def compute_life_path(birth_date: datetime) -> int:
    """
    Calculate Life Path number from birth date.
    
    Method: Add all digits of birth date and reduce.
    """
    day = birth_date.day
    month = birth_date.month
    year = birth_date.year
    
    # Reduce each component
    day_sum = reduce_to_single_digit(day)
    month_sum = reduce_to_single_digit(month)
    year_sum = reduce_to_single_digit(sum(int(d) for d in str(year)))
    
    # Combine and reduce
    total = day_sum + month_sum + year_sum
    return reduce_to_single_digit(total)


def compute_expression(full_name: str) -> int:
    """
    Calculate Expression/Destiny number from full name.
    
    Method: Sum all letters using Pythagorean values.
    """
    total = 0
    for char in full_name.upper():
        if char.isalpha():
            total += PYTHAGOREAN_VALUES.get(char, 0)
    return reduce_to_single_digit(total)


def compute_soul_urge(full_name: str) -> int:
    """
    Calculate Soul Urge/Heart's Desire number.
    
    Method: Sum vowels only using Pythagorean values.
    """
    total = 0
    for char in full_name.upper():
        if char in VOWELS:
            total += PYTHAGOREAN_VALUES.get(char, 0)
    return reduce_to_single_digit(total)


def compute_personality(full_name: str) -> int:
    """
    Calculate Personality number.
    
    Method: Sum consonants only using Pythagorean values.
    """
    total = 0
    for char in full_name.upper():
        if char.isalpha() and char not in VOWELS:
            total += PYTHAGOREAN_VALUES.get(char, 0)
    return reduce_to_single_digit(total)


def compute_name_breakdown(full_name: str) -> List[Dict[str, Any]]:
    """
    Generate letter-by-letter breakdown showing Pythagorean values.
    
    Returns list of {letter, value} for each letter in the name.
    """
    breakdown = []
    for char in full_name.upper():
        if char.isalpha():
            breakdown.append({
                "letter": char,
                "value": PYTHAGOREAN_VALUES.get(char, 0)
            })
        elif char == ' ':
            breakdown.append({
                "letter": " ",
                "value": None  # Space marker
            })
    return breakdown


# =============================================================================
# LO SHU GRID COMPUTATION (Vedic)
# =============================================================================

def compute_lo_shu(birth_date: datetime) -> Dict[str, Any]:
    """
    Compute Lo Shu Grid from birth date.
    
    The Lo Shu Grid is a 3x3 magic square showing presence/absence of numbers 1-9.
    Numbers are derived from birth date digits (excluding 0).
    
    Standard Lo Shu Grid positions:
    4 | 9 | 2
    3 | 5 | 7
    8 | 1 | 6
    
    Returns:
        {
            "digit_counts": {"1": count, "2": count, ...},
            "grid": [[4 or null, 9 or null, 2 or null], ...],
            "missing_numbers": [list of missing 1-9],
            "present_numbers": [list of present 1-9]
        }
    """
    # Extract all digits from birth date (DD/MM/YYYY format)
    date_str = birth_date.strftime('%d%m%Y')
    
    # Count occurrences of each digit 1-9 (EXCLUDE 0 per requirements)
    digit_counts = {str(i): 0 for i in range(1, 10)}
    for d in date_str:
        if d != '0' and d in digit_counts:
            digit_counts[d] += 1
    
    # Identify missing and present numbers
    missing_numbers = [i for i in range(1, 10) if digit_counts[str(i)] == 0]
    present_numbers = [i for i in range(1, 10) if digit_counts[str(i)] > 0]
    
    # Standard Lo Shu grid template (magic square arrangement)
    lo_shu_template = [[4, 9, 2], [3, 5, 7], [8, 1, 6]]
    
    # Build grid with null for missing numbers
    grid = []
    for row in lo_shu_template:
        grid_row = []
        for num in row:
            if digit_counts[str(num)] > 0:
                grid_row.append(num)
            else:
                grid_row.append(None)  # Missing number
        grid.append(grid_row)
    
    return {
        "digit_counts": digit_counts,
        "grid": grid,
        "missing_numbers": missing_numbers,
        "present_numbers": present_numbers
    }


# =============================================================================
# MISSING NUMBER TENSIONS (Behavioral Mapping)
# =============================================================================

MISSING_NUMBER_TENSIONS = {
    1: {
        "label": "Self-initiation gap",
        "behavioral": "You may wait for external permission to begin",
        "tension": "Starting alone can feel uncomfortable"
    },
    2: {
        "label": "Translation difficulty",
        "behavioral": "People don't always follow what feels obvious to you",
        "tension": "Bridging your inner knowing to others takes extra effort"
    },
    3: {
        "label": "Expression gap",
        "behavioral": "You may hold insight without fully expressing it",
        "tension": "What you know doesn't always make it into words"
    },
    4: {
        "label": "Grounding difficulty",
        "behavioral": "Sustained routines can feel draining rather than stabilizing",
        "tension": "Building lasting structures requires conscious effort"
    },
    5: {
        "label": "Adaptability gap",
        "behavioral": "You may get stuck between options when change is needed",
        "tension": "Flexibility doesn't come automatically"
    },
    6: {
        "label": "Responsibility resistance",
        "behavioral": "Domestic duties may feel like interruptions",
        "tension": "Care-taking energy doesn't flow naturally"
    },
    7: {
        "label": "Internal processing gap",
        "behavioral": "You may act before fully analyzing",
        "tension": "Deep reflection requires deliberate space"
    },
    8: {
        "label": "Material focus gap",
        "behavioral": "Results and outcomes may get less attention",
        "tension": "Power dynamics might not register until too late"
    },
    9: {
        "label": "Completion difficulty",
        "behavioral": "Letting go of what's finished can take longer",
        "tension": "Endings don't feel natural"
    }
}


def get_tensions_from_missing(missing_numbers: List[int]) -> List[Dict[str, str]]:
    """
    Map missing numbers to behavioral tensions.
    
    Returns list of tension objects for display.
    """
    tensions = []
    for num in missing_numbers:
        if num in MISSING_NUMBER_TENSIONS:
            tension = MISSING_NUMBER_TENSIONS[num].copy()
            tension["number"] = num
            tensions.append(tension)
    return tensions


# =============================================================================
# MIRROR SYNTHESIS (Behavioral Pattern Combination)
# =============================================================================

LIFE_PATH_BEHAVIORS = {
    1: "You move quickly on what you see",
    2: "You feel the undercurrents before they surface",
    3: "You process by expressing — silence feels stuck",
    4: "You build steadily and value what lasts",
    5: "You sense when something needs to change",
    6: "You take on responsibility, even uninvited",
    7: "You analyze before committing",
    8: "You track power and results instinctively",
    9: "You see the larger arc others miss",
    11: "You catch signals before they become visible",
    22: "You think in structures that span years",
    33: "You absorb what others carry"
}

EXPRESSION_BEHAVIORS = {
    1: "and present as someone who leads",
    2: "and come across as collaborative",
    3: "and appear naturally expressive",
    4: "and seem methodical to others",
    5: "and appear adaptable, sometimes restless",
    6: "and present as caring and responsible",
    7: "and come across as thoughtful, reserved",
    8: "and appear capable and driven",
    9: "and seem warm and broad-minded",
    11: "and appear inspired, visionary",
    22: "and present as masterful, ambitious",
    33: "and come across as nurturing, wise"
}

SOUL_URGE_BEHAVIORS = {
    1: "You want independence and space to move",
    2: "You want connection and harmony",
    3: "You want expression and lightness",
    4: "You want stability and order",
    5: "You want freedom and new experience",
    6: "You want to nurture and be needed",
    7: "You want understanding and solitude",
    8: "You want achievement and recognition",
    9: "You want meaning and completion",
    11: "You want spiritual insight",
    22: "You want to build something lasting",
    33: "You want to heal and guide"
}


def generate_pattern_synthesis(
    life_path: int,
    expression: Optional[int],
    soul_urge: Optional[int],
    missing_numbers: List[int]
) -> Dict[str, Any]:
    """
    Generate behavioral synthesis combining all pattern elements.
    
    This is the "HOW THIS PATTERN PLAYS OUT" section.
    No mystical language. Grounded behavioral observations.
    """
    lines = []
    
    # Life path behavior
    if life_path in LIFE_PATH_BEHAVIORS:
        line = LIFE_PATH_BEHAVIORS[life_path]
        if expression and expression in EXPRESSION_BEHAVIORS:
            line += f" {EXPRESSION_BEHAVIORS[expression]}"
        lines.append(line)
    
    # Soul urge
    if soul_urge and soul_urge in SOUL_URGE_BEHAVIORS:
        lines.append(SOUL_URGE_BEHAVIORS[soul_urge])
    
    # Missing number consequence
    if missing_numbers:
        missing_labels = []
        for num in missing_numbers[:3]:  # Top 3 missing
            if num in MISSING_NUMBER_TENSIONS:
                missing_labels.append(MISSING_NUMBER_TENSIONS[num]["label"].lower())
        
        if missing_labels:
            missing_str = " and ".join(missing_labels[:2])
            lines.append(f"But {missing_str} don't come naturally")
    
    # Consequence line
    consequence = generate_consequence_line(life_path, missing_numbers)
    if consequence:
        lines.append(consequence)
    
    return {
        "lines": lines,
        "summary": " ".join(lines)
    }


def generate_consequence_line(life_path: int, missing_numbers: List[int]) -> str:
    """Generate the consequence/result line based on pattern."""
    
    consequences = {
        (1, 2): "So you often end up ahead of people — and alone in it.",
        (1, 4): "So you start strong but the follow-through costs extra energy.",
        (2, 1): "So you feel everything but acting on it takes effort.",
        (3, 7): "So you express before you've fully understood.",
        (5, 4): "So you crave change but struggle to sustain what you build.",
        (7, 3): "So you know deeply but communicating it is work.",
        (11, 4): "So you see far ahead but building the bridge there is frustrating.",
    }
    
    for missing in missing_numbers[:2]:
        key = (life_path if life_path <= 9 else life_path, missing)
        if key in consequences:
            return consequences[key]
    
    # Default
    return "So the pattern keeps running — sometimes serving you, sometimes not."


# =============================================================================
# MAIN COMPUTE FUNCTION
# =============================================================================

def compute_numerology_deterministic(
    birth_date: datetime,
    full_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Compute complete deterministic numerology profile.
    
    This is the canonical compute function that returns:
    - Input data
    - Pythagorean calculations (name-based)
    - Lo Shu grid (date-based)
    
    NO LLM. NO interpretation. Pure computation.
    
    Args:
        birth_date: User's birth date
        full_name: User's full birth name (optional)
    
    Returns:
        Complete deterministic numerology payload
    """
    
    # === PYTHAGOREAN (Name-based) ===
    life_path = compute_life_path(birth_date)
    
    pythagorean = {
        "life_path": life_path,
        "expression": None,
        "soul_urge": None,
        "personality": None,
        "name_breakdown": None
    }
    
    if full_name and full_name.strip():
        pythagorean["expression"] = compute_expression(full_name)
        pythagorean["soul_urge"] = compute_soul_urge(full_name)
        pythagorean["personality"] = compute_personality(full_name)
        pythagorean["name_breakdown"] = compute_name_breakdown(full_name)
    
    # === LO SHU (Date-based) ===
    lo_shu = compute_lo_shu(birth_date)
    
    # === TENSIONS (Behavioral mapping) ===
    tensions = get_tensions_from_missing(lo_shu["missing_numbers"])
    
    # === PATTERN SYNTHESIS (Behavioral interpretation) ===
    synthesis = generate_pattern_synthesis(
        life_path=life_path,
        expression=pythagorean["expression"],
        soul_urge=pythagorean["soul_urge"],
        missing_numbers=lo_shu["missing_numbers"]
    )
    
    return {
        "input": {
            "full_name": full_name,
            "birth_date": birth_date.strftime('%Y-%m-%d')
        },
        "pythagorean": pythagorean,
        "lo_shu": lo_shu,
        "tensions": tensions,
        "synthesis": synthesis,
        "computation_version": "mirror-numerology-v2",
        "computed_at": datetime.now().isoformat()
    }
