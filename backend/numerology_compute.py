"""
Numerology Name Number Calculator
=================================

Computes Expression, Soul Urge, and Personality numbers from a full birth name.
"""

import re
from typing import Dict, Optional

# Pythagorean numerology letter values
LETTER_VALUES = {
    'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8, 'I': 9,
    'J': 1, 'K': 2, 'L': 3, 'M': 4, 'N': 5, 'O': 6, 'P': 7, 'Q': 8, 'R': 9,
    'S': 1, 'T': 2, 'U': 3, 'V': 4, 'W': 5, 'X': 6, 'Y': 7, 'Z': 8
}

VOWELS = set('AEIOU')
# Y is sometimes a vowel - we treat it as a consonant for simplicity


def reduce_to_single_digit(num: int, preserve_master: bool = True) -> int:
    """
    Reduce a number to a single digit (1-9), optionally preserving master numbers (11, 22, 33).
    """
    while num > 9:
        if preserve_master and num in (11, 22, 33):
            return num
        num = sum(int(d) for d in str(num))
    return num


def calculate_expression_number(name: str) -> int:
    """
    Calculate Expression Number (Destiny Number).
    Sum of all letters in the full birth name.
    """
    name_upper = name.upper()
    total = sum(LETTER_VALUES.get(char, 0) for char in name_upper if char.isalpha())
    return reduce_to_single_digit(total)


def calculate_soul_urge_number(name: str) -> int:
    """
    Calculate Soul Urge Number (Heart's Desire).
    Sum of all vowels in the full birth name.
    """
    name_upper = name.upper()
    total = sum(LETTER_VALUES.get(char, 0) for char in name_upper if char in VOWELS)
    return reduce_to_single_digit(total)


def calculate_personality_number(name: str) -> int:
    """
    Calculate Personality Number.
    Sum of all consonants in the full birth name.
    """
    name_upper = name.upper()
    total = sum(LETTER_VALUES.get(char, 0) for char in name_upper if char.isalpha() and char not in VOWELS)
    return reduce_to_single_digit(total)


def calculate_numerology_name_numbers(full_name: str) -> Dict[str, Optional[int]]:
    """
    Calculate all name-based numerology numbers.
    
    Args:
        full_name: Full birth name
        
    Returns:
        {
            "expression": int,
            "soul_urge": int,
            "personality": int
        }
    """
    if not full_name or not full_name.strip():
        return {
            "expression": None,
            "soul_urge": None,
            "personality": None
        }
    
    clean_name = full_name.strip()
    
    return {
        "expression": calculate_expression_number(clean_name),
        "soul_urge": calculate_soul_urge_number(clean_name),
        "personality": calculate_personality_number(clean_name)
    }


if __name__ == "__main__":
    # Test with a sample name
    test_name = "John Michael Smith"
    numbers = calculate_numerology_name_numbers(test_name)
    print(f"Name: {test_name}")
    print(f"Expression: {numbers['expression']}")
    print(f"Soul Urge: {numbers['soul_urge']}")
    print(f"Personality: {numbers['personality']}")
