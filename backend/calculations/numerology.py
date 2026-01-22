"""Numerology calculations"""
from datetime import datetime
from typing import Dict

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

def get_full_numerology(birth_date: datetime, full_name: str = None) -> Dict:
    """Calculate complete numerology profile"""
    result = {
        'life_path': calculate_life_path(birth_date)
    }
    
    if full_name:
        result['expression'] = calculate_expression_number(full_name)
    
    return result
