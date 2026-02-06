"""Numerology calculations

===============================================================================
DETERMINISTIC COMPUTATION CORE - FROZEN
===============================================================================
This file is part of Project Mirror's deterministic computation core.
Outputs must remain stable across versions.
Do NOT modify without updating regression tests and bumping computation_version.

Current version: mirror-deterministic-v1
===============================================================================
"""
from datetime import datetime
from typing import Dict, List, Optional
from .astrology import ComputeIntegrityError


def reduce_to_single_digit(number: int, allow_master: bool = True) -> int:
    """Reduce number to single digit (or master number 11, 22, 33)"""
    while number > 9:
        if allow_master and number in [11, 22, 33]:
            return number
        number = sum(int(digit) for digit in str(number))
    return number

def calculate_life_path(birth_date: datetime) -> Dict:
    """Calculate Life Path number"""
    # Method: Add all digits of birth date
    day = birth_date.day
    month = birth_date.month
    year = birth_date.year
    
    # Reduce each component
    day_sum = reduce_to_single_digit(day)
    month_sum = reduce_to_single_digit(month)
    year_sum = reduce_to_single_digit(sum(int(d) for d in str(year)))
    
    # Combine and reduce
    total = day_sum + month_sum + year_sum
    life_path = reduce_to_single_digit(total)
    
    return {
        'number': life_path,
        'description': get_life_path_description(life_path)
    }

def calculate_expression_number(full_name: str) -> Dict:
    """Calculate Expression/Destiny number from full name"""
    # Letter to number mapping
    letter_values = {
        'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8, 'I': 9,
        'J': 1, 'K': 2, 'L': 3, 'M': 4, 'N': 5, 'O': 6, 'P': 7, 'Q': 8, 'R': 9,
        'S': 1, 'T': 2, 'U': 3, 'V': 4, 'W': 5, 'X': 6, 'Y': 7, 'Z': 8
    }
    
    total = 0
    for char in full_name.upper():
        if char.isalpha():
            total += letter_values.get(char, 0)
    
    expression = reduce_to_single_digit(total)
    
    return {
        'number': expression,
        'description': get_expression_description(expression)
    }

def get_life_path_description(number: int) -> str:
    """Get description for Life Path number"""
    descriptions = {
        1: 'The Leader - Independent, innovative, ambitious',
        2: 'The Peacemaker - Diplomatic, intuitive, cooperative',
        3: 'The Communicator - Creative, expressive, optimistic',
        4: 'The Builder - Practical, disciplined, reliable',
        5: 'The Freedom Seeker - Adventurous, versatile, dynamic',
        6: 'The Nurturer - Responsible, caring, community-oriented',
        7: 'The Seeker - Analytical, spiritual, introspective',
        8: 'The Powerhouse - Ambitious, successful, authoritative',
        9: 'The Humanitarian - Compassionate, idealistic, generous',
        11: 'The Visionary - Intuitive, inspiring, idealistic (Master Number)',
        22: 'The Master Builder - Visionary, practical, transformative (Master Number)',
        33: 'The Master Teacher - Compassionate, healing, uplifting (Master Number)'
    }
    return descriptions.get(number, 'Unknown')

def get_expression_description(number: int) -> str:
    """Get description for Expression number"""
    descriptions = {
        1: 'Natural leader with strong will',
        2: 'Diplomatic and sensitive nature',
        3: 'Artistic and expressive talents',
        4: 'Methodical and reliable approach',
        5: 'Freedom-loving and adaptable',
        6: 'Nurturing and responsible',
        7: 'Analytical and spiritual seeker',
        8: 'Business-minded and ambitious',
        9: 'Humanitarian and compassionate',
        11: 'Highly intuitive and inspirational',
        22: 'Master builder with grand visions',
        33: 'Master teacher and healer'
    }
    return descriptions.get(number, 'Unknown')


def calculate_birthday_number(birth_date: datetime) -> Dict:
    """Calculate Birthday number (day of birth reduced)"""
    day = birth_date.day
    birthday_number = reduce_to_single_digit(day)
    
    return {
        'number': birthday_number,
        'day': day,
        'description': get_birthday_description(birthday_number)
    }


def get_birthday_description(number: int) -> str:
    """Get description for Birthday number"""
    descriptions = {
        1: 'Independent spirit, self-starter energy',
        2: 'Sensitive perception, partnership emphasis',
        3: 'Creative expression, social engagement',
        4: 'Structured approach, grounded presence',
        5: 'Adaptable nature, variety-seeking',
        6: 'Care-oriented, harmony-focused',
        7: 'Reflective depth, analytical tendency',
        8: 'Results-oriented, material awareness',
        9: 'Broad perspective, humanitarian lean',
        11: 'Heightened intuition, inspirational quality',
        22: 'Large-scale thinking, practical vision',
        33: 'Teaching energy, compassionate depth'
    }
    return descriptions.get(number, 'Unknown')


def calculate_soul_urge(full_name: str) -> Dict:
    """Calculate Soul Urge number (vowels only)"""
    vowel_values = {'A': 1, 'E': 5, 'I': 9, 'O': 6, 'U': 3}
    
    total = 0
    for char in full_name.upper():
        if char in vowel_values:
            total += vowel_values[char]
    
    soul_urge = reduce_to_single_digit(total)
    
    return {
        'number': soul_urge,
        'description': get_soul_urge_description(soul_urge)
    }


def get_soul_urge_description(number: int) -> str:
    """Get description for Soul Urge number"""
    descriptions = {
        1: 'Inner drive toward independence and originality',
        2: 'Inner pull toward connection and harmony',
        3: 'Inner need for creative expression and joy',
        4: 'Inner desire for stability and structure',
        5: 'Inner craving for freedom and experience',
        6: 'Inner call toward nurturing and responsibility',
        7: 'Inner search for understanding and solitude',
        8: 'Inner drive toward achievement and recognition',
        9: 'Inner motivation toward service and completion',
        11: 'Inner pull toward spiritual insight and inspiration',
        22: 'Inner drive to build something lasting',
        33: 'Inner calling toward healing and teaching'
    }
    return descriptions.get(number, 'Unknown')


def calculate_personality_number(full_name: str) -> Dict:
    """Calculate Personality number (consonants only)"""
    vowels = set('AEIOU')
    letter_values = {
        'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8, 'I': 9,
        'J': 1, 'K': 2, 'L': 3, 'M': 4, 'N': 5, 'O': 6, 'P': 7, 'Q': 8, 'R': 9,
        'S': 1, 'T': 2, 'U': 3, 'V': 4, 'W': 5, 'X': 6, 'Y': 7, 'Z': 8
    }
    
    total = 0
    for char in full_name.upper():
        if char.isalpha() and char not in vowels:
            total += letter_values.get(char, 0)
    
    personality = reduce_to_single_digit(total)
    
    return {
        'number': personality,
        'description': get_personality_description(personality)
    }


def get_personality_description(number: int) -> str:
    """Get description for Personality number"""
    descriptions = {
        1: 'Appears confident and self-directed',
        2: 'Appears approachable and cooperative',
        3: 'Appears friendly and expressive',
        4: 'Appears reliable and methodical',
        5: 'Appears dynamic and versatile',
        6: 'Appears caring and responsible',
        7: 'Appears thoughtful and reserved',
        8: 'Appears capable and authoritative',
        9: 'Appears warm and broad-minded',
        11: 'Appears inspired and visionary',
        22: 'Appears masterful and ambitious',
        33: 'Appears nurturing and wise'
    }
    return descriptions.get(number, 'Unknown')


def calculate_personal_year(birth_date: datetime, current_date: datetime = None) -> Dict:
    """Calculate Personal Year number"""
    if current_date is None:
        current_date = datetime.now()
    
    # Personal Year = Birth Month + Birth Day + Current Year (all reduced)
    month_sum = reduce_to_single_digit(birth_date.month, allow_master=False)
    day_sum = reduce_to_single_digit(birth_date.day, allow_master=False)
    year_sum = reduce_to_single_digit(sum(int(d) for d in str(current_date.year)), allow_master=False)
    
    personal_year = reduce_to_single_digit(month_sum + day_sum + year_sum, allow_master=False)
    
    return {
        'number': personal_year,
        'year': current_date.year,
        'description': get_personal_year_description(personal_year)
    }


def get_personal_year_description(number: int) -> str:
    """Get description for Personal Year number"""
    descriptions = {
        1: 'Year of new beginnings and fresh starts',
        2: 'Year of patience, partnerships, and gestation',
        3: 'Year of creative expression and social expansion',
        4: 'Year of building foundations and hard work',
        5: 'Year of change, freedom, and new experiences',
        6: 'Year of responsibility, home, and family focus',
        7: 'Year of reflection, study, and inner development',
        8: 'Year of achievement, material focus, and power',
        9: 'Year of completion, letting go, and transition'
    }
    return descriptions.get(number, 'Unknown')


def calculate_personal_month(birth_date: datetime, current_date: datetime = None) -> Dict:
    """Calculate Personal Month number"""
    if current_date is None:
        current_date = datetime.now()
    
    personal_year = calculate_personal_year(birth_date, current_date)['number']
    current_month = reduce_to_single_digit(current_date.month, allow_master=False)
    
    personal_month = reduce_to_single_digit(personal_year + current_month, allow_master=False)
    
    return {
        'number': personal_month,
        'month': current_date.month,
        'year': current_date.year,
        'description': get_personal_month_description(personal_month)
    }


def get_personal_month_description(number: int) -> str:
    """Get description for Personal Month number"""
    descriptions = {
        1: 'Month emphasizing initiative and new starts',
        2: 'Month emphasizing cooperation and waiting',
        3: 'Month emphasizing expression and communication',
        4: 'Month emphasizing work and practical matters',
        5: 'Month emphasizing change and variety',
        6: 'Month emphasizing responsibility and care',
        7: 'Month emphasizing reflection and solitude',
        8: 'Month emphasizing business and achievement',
        9: 'Month emphasizing completion and release'
    }
    return descriptions.get(number, 'Unknown')


def calculate_personal_day(birth_date: datetime, current_date: datetime = None) -> Dict:
    """Calculate Personal Day number"""
    if current_date is None:
        current_date = datetime.now()
    
    personal_month = calculate_personal_month(birth_date, current_date)['number']
    current_day = reduce_to_single_digit(current_date.day, allow_master=False)
    
    personal_day = reduce_to_single_digit(personal_month + current_day, allow_master=False)
    
    return {
        'number': personal_day,
        'date': current_date.strftime('%Y-%m-%d'),
        'description': get_personal_day_description(personal_day)
    }


def get_personal_day_description(number: int) -> str:
    """Get description for Personal Day number"""
    descriptions = {
        1: 'Day for initiative and independent action',
        2: 'Day for patience and cooperation',
        3: 'Day for creativity and social connection',
        4: 'Day for practical work and organization',
        5: 'Day for flexibility and new experiences',
        6: 'Day for care, home, and relationships',
        7: 'Day for reflection and inner focus',
        8: 'Day for business and material matters',
        9: 'Day for completion and broad perspective'
    }
    return descriptions.get(number, 'Unknown')


def get_full_numerology(birth_date: datetime, full_name: str = None) -> Dict:
    """Calculate complete numerology profile (legacy function)"""
    result = {
        'life_path': calculate_life_path(birth_date),
        'birthday': calculate_birthday_number(birth_date)
    }
    
    if full_name:
        result['expression'] = calculate_expression_number(full_name)
        result['soul_urge'] = calculate_soul_urge(full_name)
        result['personality'] = calculate_personality_number(full_name)
        result['has_name_numbers'] = True
    else:
        result['has_name_numbers'] = False
    
    return result


def get_numerology_cycles(birth_date: datetime, current_date: datetime = None) -> Dict:
    """Calculate current numerology cycles"""
    if current_date is None:
        current_date = datetime.now()
    
    return {
        'personal_year': calculate_personal_year(birth_date, current_date),
        'personal_month': calculate_personal_month(birth_date, current_date),
        'personal_day': calculate_personal_day(birth_date, current_date)
    }


# =============================================================================
# CANONICAL COMPUTE FUNCTION WITH INTEGRITY CONTRACT
# =============================================================================

def get_canonical_numerology(
    birth_date: datetime,
    numerology_full_name: Optional[str] = None,
    current_date: Optional[datetime] = None
) -> Dict:
    """Calculate complete numerology profile with compute integrity contract.
    
    NUMEROLOGY COMPUTE INTEGRITY CONTRACT:
    This function MUST return a complete, validated canonical payload or raise
    ComputeIntegrityError. Partial charts are NEVER returned.
    
    REQUIRED COMPUTED OBJECTS:
    - core.life_path (always required)
    - core.birthday_number (always required)
    - core.expression (null if no name, numeric if name provided)
    - core.soul_urge (null if no name, numeric if name provided)
    - core.personality (null if no name, numeric if name provided)
    - cycles.personal_year (always required)
    - cycles.personal_month (always required)
    - cycles.personal_day (always required)
    
    Args:
        birth_date: Birth date (datetime)
        numerology_full_name: Full birth name for Expression/Soul Urge/Personality (optional)
        current_date: Date for cycles calculation (defaults to now)
    
    Returns:
        Dict with canonical numerology payload
    
    Raises:
        ComputeIntegrityError: If any required data is missing or invalid
    """
    if current_date is None:
        current_date = datetime.now()
    
    compute_errors = []
    
    # =========================================================================
    # CALCULATE CORE NUMBERS
    # =========================================================================
    
    # Life Path (REQUIRED)
    try:
        life_path_data = calculate_life_path(birth_date)
        life_path = life_path_data.get('number')
        if life_path is None:
            compute_errors.append("Core: life_path calculation failed")
    except Exception as e:
        compute_errors.append(f"Core: life_path error - {str(e)}")
        life_path = None
        life_path_data = {}
    
    # Birthday Number (REQUIRED)
    try:
        birthday_data = calculate_birthday_number(birth_date)
        birthday_number = birthday_data.get('number')
        if birthday_number is None:
            compute_errors.append("Core: birthday_number calculation failed")
    except Exception as e:
        compute_errors.append(f"Core: birthday_number error - {str(e)}")
        birthday_number = None
        birthday_data = {}
    
    # Name-based numbers (CONDITIONAL)
    has_name = bool(numerology_full_name and numerology_full_name.strip())
    
    if has_name:
        # Expression (REQUIRED if name provided)
        try:
            expression_data = calculate_expression_number(numerology_full_name)
            expression = expression_data.get('number')
            if expression is None:
                compute_errors.append("Core: expression calculation failed (name provided)")
        except Exception as e:
            compute_errors.append(f"Core: expression error - {str(e)}")
            expression = None
            expression_data = {}
        
        # Soul Urge (REQUIRED if name provided)
        try:
            soul_urge_data = calculate_soul_urge(numerology_full_name)
            soul_urge = soul_urge_data.get('number')
            if soul_urge is None:
                compute_errors.append("Core: soul_urge calculation failed (name provided)")
        except Exception as e:
            compute_errors.append(f"Core: soul_urge error - {str(e)}")
            soul_urge = None
            soul_urge_data = {}
        
        # Personality (REQUIRED if name provided)
        try:
            personality_data = calculate_personality_number(numerology_full_name)
            personality = personality_data.get('number')
            if personality is None:
                compute_errors.append("Core: personality calculation failed (name provided)")
        except Exception as e:
            compute_errors.append(f"Core: personality error - {str(e)}")
            personality = None
            personality_data = {}
    else:
        # Name not provided - these must be null but keys must exist
        expression = None
        soul_urge = None
        personality = None
        expression_data = {"number": None, "description": "Locked - add birth name to unlock"}
        soul_urge_data = {"number": None, "description": "Locked - add birth name to unlock"}
        personality_data = {"number": None, "description": "Locked - add birth name to unlock"}
    
    # =========================================================================
    # CALCULATE CYCLES
    # =========================================================================
    
    # Personal Year (REQUIRED)
    try:
        personal_year_data = calculate_personal_year(birth_date, current_date)
        personal_year = personal_year_data.get('number')
        if personal_year is None:
            compute_errors.append("Cycles: personal_year calculation failed")
    except Exception as e:
        compute_errors.append(f"Cycles: personal_year error - {str(e)}")
        personal_year = None
        personal_year_data = {}
    
    # Personal Month (REQUIRED)
    try:
        personal_month_data = calculate_personal_month(birth_date, current_date)
        personal_month = personal_month_data.get('number')
        if personal_month is None:
            compute_errors.append("Cycles: personal_month calculation failed")
    except Exception as e:
        compute_errors.append(f"Cycles: personal_month error - {str(e)}")
        personal_month = None
        personal_month_data = {}
    
    # Personal Day (REQUIRED)
    try:
        personal_day_data = calculate_personal_day(birth_date, current_date)
        personal_day = personal_day_data.get('number')
        if personal_day is None:
            compute_errors.append("Cycles: personal_day calculation failed")
    except Exception as e:
        compute_errors.append(f"Cycles: personal_day error - {str(e)}")
        personal_day = None
        personal_day_data = {}
    
    # =========================================================================
    # COMPUTE INTEGRITY ASSERTIONS
    # =========================================================================
    
    # Validate core numbers exist
    if life_path is None:
        compute_errors.append("Core: life_path is required")
    if birthday_number is None:
        compute_errors.append("Core: birthday_number is required")
    
    # Validate cycles exist
    if personal_year is None:
        compute_errors.append("Cycles: personal_year is required")
    if personal_month is None:
        compute_errors.append("Cycles: personal_month is required")
    if personal_day is None:
        compute_errors.append("Cycles: personal_day is required")
    
    # If name provided, validate name-based numbers are numeric
    if has_name:
        if not isinstance(expression, int):
            compute_errors.append("Core: expression must be numeric when name is provided")
        if not isinstance(soul_urge, int):
            compute_errors.append("Core: soul_urge must be numeric when name is provided")
        if not isinstance(personality, int):
            compute_errors.append("Core: personality must be numeric when name is provided")
    
    # =========================================================================
    # FAIL FAST - DO NOT RETURN PARTIAL DATA
    # =========================================================================
    if compute_errors:
        partial_data = {
            'life_path': life_path,
            'birthday_number': birthday_number,
            'personal_year': personal_year,
            'has_name': has_name
        }
        raise ComputeIntegrityError(compute_errors, partial_data)
    
    # =========================================================================
    # BUILD CANONICAL PAYLOAD
    # =========================================================================
    return {
        # CANONICAL NORMALIZED STRUCTURE
        "core": {
            "life_path": life_path,
            "life_path_description": life_path_data.get('description'),
            "birthday_number": birthday_number,
            "birthday_description": birthday_data.get('description'),
            "expression": expression,
            "expression_description": expression_data.get('description'),
            "soul_urge": soul_urge,
            "soul_urge_description": soul_urge_data.get('description'),
            "personality": personality,
            "personality_description": personality_data.get('description')
        },
        "cycles": {
            "personal_year": personal_year,
            "personal_year_description": personal_year_data.get('description'),
            "personal_year_context": personal_year_data.get('year'),
            "personal_month": personal_month,
            "personal_month_description": personal_month_data.get('description'),
            "personal_month_context": personal_month_data.get('month'),
            "personal_day": personal_day,
            "personal_day_description": personal_day_data.get('description'),
            "personal_day_date": personal_day_data.get('date')
        },
        "inputs": {
            "birth_date": birth_date.strftime('%Y-%m-%d') if hasattr(birth_date, 'strftime') else str(birth_date),
            "numerology_full_name": numerology_full_name if has_name else None
        },
        
        # Metadata
        "has_name_numbers": has_name,
        "locked_numbers": [] if has_name else ["expression", "soul_urge", "personality"],
        "computation_version": "mirror-deterministic-v1",
        "computed_at": current_date.isoformat() if hasattr(current_date, 'isoformat') else str(current_date),
        
        # Compute integrity confirmation
        "compute_integrity": {
            "valid": True,
            "life_path_valid": isinstance(life_path, int),
            "birthday_valid": isinstance(birthday_number, int),
            "cycles_valid": all([
                isinstance(personal_year, int),
                isinstance(personal_month, int),
                isinstance(personal_day, int)
            ]),
            "name_numbers_status": "computed" if has_name else "locked"
        }
    }
