"""
BaZi (Four Pillars of Destiny) Deterministic Engine

This module implements the deterministic calculation layer for BaZi astrology.
BaZi uses four pillars (Year, Month, Day, Hour) each consisting of a 
Heavenly Stem and Earthly Branch to derive personality insights.

Calculation Methods:
- Year Pillar: Based on Chinese lunar year cycle (60-year cycle)
- Month Pillar: Based on solar terms and year stem
- Day Pillar: Based on a continuous 60-day cycle count
- Hour Pillar: Based on 2-hour periods and day stem

Reference Epoch: February 4, 1900 (Start of Spring for that year)
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple, List
import math
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# FUNDAMENTAL CONSTANTS
# =============================================================================

# 十天干 (Ten Heavenly Stems)
HEAVENLY_STEMS = [
    "甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"
]

HEAVENLY_STEMS_PINYIN = [
    "Jia", "Yi", "Bing", "Ding", "Wu", "Ji", "Geng", "Xin", "Ren", "Gui"
]

# 十二地支 (Twelve Earthly Branches)
EARTHLY_BRANCHES = [
    "子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"
]

EARTHLY_BRANCHES_PINYIN = [
    "Zi", "Chou", "Yin", "Mao", "Chen", "Si", 
    "Wu", "Wei", "Shen", "You", "Xu", "Hai"
]

# Branch to Animal mapping (Chinese Zodiac)
BRANCH_ANIMALS = {
    "子": "Rat", "丑": "Ox", "寅": "Tiger", "卯": "Rabbit",
    "辰": "Dragon", "巳": "Snake", "午": "Horse", "未": "Goat",
    "申": "Monkey", "酉": "Rooster", "戌": "Dog", "亥": "Pig"
}

# =============================================================================
# FIVE ELEMENTS MAPPING
# =============================================================================

# Stem to Element mapping
STEM_ELEMENTS = {
    "甲": "Wood", "乙": "Wood",
    "丙": "Fire", "丁": "Fire",
    "戊": "Earth", "己": "Earth",
    "庚": "Metal", "辛": "Metal",
    "壬": "Water", "癸": "Water"
}

# Stem Yin/Yang polarity
STEM_POLARITY = {
    "甲": "Yang", "乙": "Yin",
    "丙": "Yang", "丁": "Yin",
    "戊": "Yang", "己": "Yin",
    "庚": "Yang", "辛": "Yin",
    "壬": "Yang", "癸": "Yin"
}

# Branch to Element mapping (main element)
BRANCH_ELEMENTS = {
    "子": "Water", "丑": "Earth", "寅": "Wood", "卯": "Wood",
    "辰": "Earth", "巳": "Fire", "午": "Fire", "未": "Earth",
    "申": "Metal", "酉": "Metal", "戌": "Earth", "亥": "Water"
}

# Branch hidden stems (藏干) - each branch contains hidden stems
BRANCH_HIDDEN_STEMS = {
    "子": ["癸"],
    "丑": ["己", "癸", "辛"],
    "寅": ["甲", "丙", "戊"],
    "卯": ["乙"],
    "辰": ["戊", "乙", "癸"],
    "巳": ["丙", "庚", "戊"],
    "午": ["丁", "己"],
    "未": ["己", "丁", "乙"],
    "申": ["庚", "壬", "戊"],
    "酉": ["辛"],
    "戌": ["戊", "辛", "丁"],
    "亥": ["壬", "甲"]
}

# =============================================================================
# TEN GODS (十神) RELATIONSHIPS
# =============================================================================

# Element production cycle (生)
ELEMENT_PRODUCES = {
    "Wood": "Fire",
    "Fire": "Earth",
    "Earth": "Metal",
    "Metal": "Water",
    "Water": "Wood"
}

# Element control cycle (克)
ELEMENT_CONTROLS = {
    "Wood": "Earth",
    "Fire": "Metal",
    "Earth": "Water",
    "Metal": "Wood",
    "Water": "Fire"
}

# Ten Gods based on relationship and polarity
TEN_GODS = {
    # Same element
    ("same", "same"): "比肩 (Companion)",      # Same element, same polarity
    ("same", "different"): "劫财 (Rob Wealth)", # Same element, different polarity
    # Element I produce
    ("I_produce", "same"): "食神 (Eating God)",     # I produce, same polarity
    ("I_produce", "different"): "伤官 (Hurting Officer)", # I produce, different polarity
    # Element I control
    ("I_control", "same"): "偏财 (Indirect Wealth)",   # I control, same polarity
    ("I_control", "different"): "正财 (Direct Wealth)", # I control, different polarity
    # Element that controls me
    ("controls_me", "same"): "七杀 (Seven Killings)",   # Controls me, same polarity
    ("controls_me", "different"): "正官 (Direct Officer)", # Controls me, different polarity
    # Element that produces me
    ("produces_me", "same"): "偏印 (Indirect Seal)",    # Produces me, same polarity
    ("produces_me", "different"): "正印 (Direct Seal)",  # Produces me, different polarity
}

# =============================================================================
# HOUR BRANCH MAPPING
# =============================================================================

# Hour to Earthly Branch (2-hour periods)
# Chinese hours: 子时 23:00-01:00, 丑时 01:00-03:00, etc.
HOUR_TO_BRANCH_INDEX = {
    23: 0, 0: 0,    # 子 Zi (Rat)
    1: 1, 2: 1,     # 丑 Chou (Ox)
    3: 2, 4: 2,     # 寅 Yin (Tiger)
    5: 3, 6: 3,     # 卯 Mao (Rabbit)
    7: 4, 8: 4,     # 辰 Chen (Dragon)
    9: 5, 10: 5,    # 巳 Si (Snake)
    11: 6, 12: 6,   # 午 Wu (Horse)
    13: 7, 14: 7,   # 未 Wei (Goat)
    15: 8, 16: 8,   # 申 Shen (Monkey)
    17: 9, 18: 9,   # 酉 You (Rooster)
    19: 10, 20: 10, # 戌 Xu (Dog)
    21: 11, 22: 11  # 亥 Hai (Pig)
}

# =============================================================================
# SOLAR TERMS (节气) - Approximate dates for month pillar calculation
# =============================================================================

# Solar terms mark the boundaries of BaZi months
# Each month starts at a specific solar term
SOLAR_TERMS_APPROX = {
    # (month_number, day_range_start, day_range_end)
    1: (2, 3, 5),    # 立春 Li Chun (Start of Spring) - Feb 3-5
    2: (3, 5, 7),    # 惊蛰 Jing Zhe (Awakening of Insects) - Mar 5-7
    3: (4, 4, 6),    # 清明 Qing Ming (Clear and Bright) - Apr 4-6
    4: (5, 5, 7),    # 立夏 Li Xia (Start of Summer) - May 5-7
    5: (6, 5, 7),    # 芒种 Mang Zhong (Grain in Ear) - Jun 5-7
    6: (7, 6, 8),    # 小暑 Xiao Shu (Minor Heat) - Jul 6-8
    7: (8, 7, 9),    # 立秋 Li Qiu (Start of Autumn) - Aug 7-9
    8: (9, 7, 9),    # 白露 Bai Lu (White Dew) - Sep 7-9
    9: (10, 8, 9),   # 寒露 Han Lu (Cold Dew) - Oct 8-9
    10: (11, 7, 8),  # 立冬 Li Dong (Start of Winter) - Nov 7-8
    11: (12, 6, 8),  # 大雪 Da Xue (Major Snow) - Dec 6-8
    12: (1, 5, 7),   # 小寒 Xiao Han (Minor Cold) - Jan 5-7
}


# =============================================================================
# CORE CALCULATION FUNCTIONS
# =============================================================================

def get_chinese_year(dt: datetime) -> int:
    """
    Get the Chinese year number, accounting for the lunar new year.
    Chinese year typically starts around Feb 4 (Start of Spring).
    
    Args:
        dt: datetime object
        
    Returns:
        Chinese year number
    """
    year = dt.year
    # If before Start of Spring (approx Feb 4), use previous year
    start_of_spring = datetime(year, 2, 4)
    if dt < start_of_spring:
        year -= 1
    return year


def calculate_year_pillar(year: int) -> Tuple[str, str, int, int]:
    """
    Calculate the Year Pillar (年柱).
    
    The year pillar follows a 60-year cycle (Sexagenary cycle).
    Reference: 1984 was a 甲子 (Jia Zi) year.
    
    Args:
        year: Chinese year number
        
    Returns:
        Tuple of (stem, branch, stem_index, branch_index)
    """
    # 1984 is Jia Zi (甲子) year - index 0 in the 60-year cycle
    # Stem cycles every 10 years, Branch cycles every 12 years
    offset = year - 1984
    
    stem_index = offset % 10
    branch_index = offset % 12
    
    stem = HEAVENLY_STEMS[stem_index]
    branch = EARTHLY_BRANCHES[branch_index]
    
    return stem, branch, stem_index, branch_index


def get_month_number(dt: datetime) -> int:
    """
    Get the BaZi month number based on solar terms.
    
    BaZi months are based on solar terms, not calendar months.
    Month 1 (Tiger month) starts around Feb 4.
    
    Args:
        dt: datetime object
        
    Returns:
        BaZi month number (1-12)
    """
    month = dt.month
    day = dt.day
    
    # Check which solar term period we're in
    for bazi_month, (solar_month, start_day, _) in SOLAR_TERMS_APPROX.items():
        if month == solar_month:
            if day >= start_day:
                return bazi_month
            else:
                # Before the solar term, use previous month
                return (bazi_month - 2) % 12 + 1
    
    # Default fallback based on calendar month
    # Feb 4 onwards = month 1, Mar 6 onwards = month 2, etc.
    month_map = {
        1: 12, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5,
        7: 6, 8: 7, 9: 8, 10: 9, 11: 10, 12: 11
    }
    return month_map.get(month, 1)


def calculate_month_pillar(year_stem_index: int, bazi_month: int) -> Tuple[str, str, int, int]:
    """
    Calculate the Month Pillar (月柱).
    
    The month stem depends on the year stem according to the 
    "Five Tigers Escape" (五虎遁) formula.
    
    Args:
        year_stem_index: Index of the year's heavenly stem (0-9)
        bazi_month: BaZi month number (1-12)
        
    Returns:
        Tuple of (stem, branch, stem_index, branch_index)
    """
    # Month 1 (Tiger month) corresponds to branch index 2 (寅)
    branch_index = (bazi_month + 1) % 12
    branch = EARTHLY_BRANCHES[branch_index]
    
    # Five Tigers Escape formula for month stem
    # Based on year stem, determine the stem of the first month (Tiger month)
    # 甲/己 year -> 丙寅 month starts
    # 乙/庚 year -> 戊寅 month starts
    # 丙/辛 year -> 庚寅 month starts
    # 丁/壬 year -> 壬寅 month starts
    # 戊/癸 year -> 甲寅 month starts
    
    year_stem_base = year_stem_index % 5
    first_month_stem_map = {
        0: 2,  # 甲/己 -> 丙
        1: 4,  # 乙/庚 -> 戊
        2: 6,  # 丙/辛 -> 庚
        3: 8,  # 丁/壬 -> 壬
        4: 0,  # 戊/癸 -> 甲
    }
    
    first_month_stem = first_month_stem_map[year_stem_base]
    stem_index = (first_month_stem + bazi_month - 1) % 10
    stem = HEAVENLY_STEMS[stem_index]
    
    return stem, branch, stem_index, branch_index


def calculate_day_pillar(dt: datetime) -> Tuple[str, str, int, int]:
    """
    Calculate the Day Pillar (日柱).
    
    The day pillar follows a continuous 60-day cycle.
    Reference: January 1, 1900 was a 甲戌 (Jia Xu) day.
    
    Args:
        dt: datetime object
        
    Returns:
        Tuple of (stem, branch, stem_index, branch_index)
    """
    # Reference: January 1, 1900 = 甲戌 (Jia Xu)
    # Stem index = 0 (甲), Branch index = 10 (戌)
    reference_date = datetime(1900, 1, 1)
    
    days_diff = (dt - reference_date).days
    
    # Calculate stem and branch based on days since reference
    stem_index = (days_diff % 10)
    branch_index = (10 + days_diff) % 12  # Reference branch was 戌 (index 10)
    
    stem = HEAVENLY_STEMS[stem_index]
    branch = EARTHLY_BRANCHES[branch_index]
    
    return stem, branch, stem_index, branch_index


def calculate_hour_pillar(day_stem_index: int, hour: int) -> Tuple[str, str, int, int]:
    """
    Calculate the Hour Pillar (时柱).
    
    The hour stem depends on the day stem according to the
    "Five Rats Escape" (五鼠遁) formula.
    
    Args:
        day_stem_index: Index of the day's heavenly stem (0-9)
        hour: Hour of birth (0-23)
        
    Returns:
        Tuple of (stem, branch, stem_index, branch_index)
    """
    # Get branch from hour
    branch_index = HOUR_TO_BRANCH_INDEX.get(hour, 0)
    branch = EARTHLY_BRANCHES[branch_index]
    
    # Five Rats Escape formula for hour stem
    # Based on day stem, determine the stem of the first hour (Zi hour)
    # 甲/己 day -> 甲子 hour starts
    # 乙/庚 day -> 丙子 hour starts
    # 丙/辛 day -> 戊子 hour starts
    # 丁/壬 day -> 庚子 hour starts
    # 戊/癸 day -> 壬子 hour starts
    
    day_stem_base = day_stem_index % 5
    first_hour_stem_map = {
        0: 0,  # 甲/己 -> 甲
        1: 2,  # 乙/庚 -> 丙
        2: 4,  # 丙/辛 -> 戊
        3: 6,  # 丁/壬 -> 庚
        4: 8,  # 戊/癸 -> 壬
    }
    
    first_hour_stem = first_hour_stem_map[day_stem_base]
    stem_index = (first_hour_stem + branch_index) % 10
    stem = HEAVENLY_STEMS[stem_index]
    
    return stem, branch, stem_index, branch_index


# =============================================================================
# ELEMENT ANALYSIS FUNCTIONS
# =============================================================================

def calculate_five_elements(pillars: Dict[str, Dict[str, str]]) -> Dict[str, int]:
    """
    Calculate the Five Elements distribution from all pillars.
    
    Counts elements from:
    - All 4 heavenly stems (4 points)
    - All 4 earthly branches main elements (4 points)
    - Hidden stems in branches (variable points)
    
    Args:
        pillars: Dictionary containing all four pillars
        
    Returns:
        Dictionary with element counts
    """
    elements = {"Wood": 0, "Fire": 0, "Earth": 0, "Metal": 0, "Water": 0}
    
    for pillar_name, pillar in pillars.items():
        stem = pillar["stem"]
        branch = pillar["branch"]
        
        # Count stem element (weight: 1.0)
        stem_element = STEM_ELEMENTS.get(stem)
        if stem_element:
            elements[stem_element] += 1
        
        # Count main branch element (weight: 0.5)
        branch_element = BRANCH_ELEMENTS.get(branch)
        if branch_element:
            elements[branch_element] += 0.5
        
        # Count hidden stem elements (weight: 0.3 each)
        hidden_stems = BRANCH_HIDDEN_STEMS.get(branch, [])
        for hidden_stem in hidden_stems:
            hidden_element = STEM_ELEMENTS.get(hidden_stem)
            if hidden_element:
                elements[hidden_element] += 0.3
    
    # Round to 1 decimal place
    return {k: round(v, 1) for k, v in elements.items()}


def analyze_element_balance(elements: Dict[str, float], day_master_element: str) -> Dict[str, Any]:
    """
    Analyze the balance of elements relative to the Day Master.
    
    Args:
        elements: Five elements distribution
        day_master_element: Element of the Day Master
        
    Returns:
        Analysis including dominant/weak elements and support recommendations
    """
    total = sum(elements.values())
    
    # Find dominant and weak elements
    sorted_elements = sorted(elements.items(), key=lambda x: x[1], reverse=True)
    dominant = sorted_elements[0][0]
    weak = sorted_elements[-1][0]
    
    # Calculate percentages
    percentages = {k: round((v / total) * 100, 1) if total > 0 else 0 for k, v in elements.items()}
    
    # Determine what supports the Day Master
    # Elements that produce Day Master or same as Day Master
    supporting_elements = []
    for element, produces in ELEMENT_PRODUCES.items():
        if produces == day_master_element:
            supporting_elements.append(element)
    supporting_elements.append(day_master_element)
    
    # Check if Day Master is strong or weak
    day_master_strength = elements.get(day_master_element, 0)
    producing_element = None
    for elem, produces in ELEMENT_PRODUCES.items():
        if produces == day_master_element:
            producing_element = elem
            break
    
    support_total = day_master_strength
    if producing_element:
        support_total += elements.get(producing_element, 0)
    
    is_strong = support_total >= (total / 2)
    
    # Balance assessment
    max_val = max(elements.values())
    min_val = min(elements.values())
    balance_ratio = min_val / max_val if max_val > 0 else 0
    
    if balance_ratio >= 0.7:
        balance_status = "Well Balanced"
    elif balance_ratio >= 0.4:
        balance_status = "Moderately Balanced"
    else:
        balance_status = "Imbalanced"
    
    return {
        "dominant_element": dominant,
        "weak_element": weak,
        "element_percentages": percentages,
        "day_master_strength": "Strong" if is_strong else "Weak",
        "supporting_elements": supporting_elements,
        "balance_status": balance_status,
    }


def calculate_ten_gods(day_master_stem: str, pillars: Dict[str, Dict[str, str]]) -> Dict[str, str]:
    """
    Calculate the Ten Gods relationships for all stems.
    
    The Ten Gods represent different types of relationships between
    the Day Master and other elements in the chart.
    
    Args:
        day_master_stem: The heavenly stem of the day pillar
        pillars: Dictionary containing all four pillars
        
    Returns:
        Dictionary mapping each pillar stem to its Ten God
    """
    day_master_element = STEM_ELEMENTS[day_master_stem]
    day_master_polarity = STEM_POLARITY[day_master_stem]
    
    ten_gods = {}
    
    for pillar_name, pillar in pillars.items():
        stem = pillar["stem"]
        if pillar_name == "day_pillar":
            ten_gods[f"{pillar_name}_stem"] = "Self (Day Master)"
            continue
        
        target_element = STEM_ELEMENTS[stem]
        target_polarity = STEM_POLARITY[stem]
        
        # Determine relationship type
        polarity_match = "same" if day_master_polarity == target_polarity else "different"
        
        if target_element == day_master_element:
            relationship = "same"
        elif ELEMENT_PRODUCES[day_master_element] == target_element:
            relationship = "I_produce"
        elif ELEMENT_CONTROLS[day_master_element] == target_element:
            relationship = "I_control"
        elif ELEMENT_CONTROLS[target_element] == day_master_element:
            relationship = "controls_me"
        elif ELEMENT_PRODUCES[target_element] == day_master_element:
            relationship = "produces_me"
        else:
            relationship = "unknown"
        
        god_key = (relationship, polarity_match)
        ten_god = TEN_GODS.get(god_key, "Unknown")
        ten_gods[f"{pillar_name}_stem"] = ten_god
    
    return ten_gods


# =============================================================================
# MAIN COMPUTATION FUNCTION
# =============================================================================

# =============================================================================
# DATE/TIME PARSING HELPERS
# =============================================================================

def parse_birth_time(time_str: Optional[str]) -> Optional[Tuple[int, int]]:
    """
    Parse birth time string into hours and minutes.
    
    Handles formats like:
    - "14:30"
    - "2:30pm"
    - "2:30 PM"
    - "14:30:00"
    
    Args:
        time_str: Time string in various formats
        
    Returns:
        Tuple of (hour, minute) or None if parsing fails
    """
    if not time_str:
        return None
    
    import re
    
    time_str = time_str.strip().lower()
    
    # Try HH:MM format first
    match = re.match(r'^(\d{1,2}):(\d{2})(?::\d{2})?$', time_str)
    if match:
        return int(match.group(1)), int(match.group(2))
    
    # Try 12-hour format with am/pm
    match = re.match(r'^(\d{1,2}):(\d{2})\s*(am|pm)$', time_str)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        period = match.group(3)
        
        if period == 'pm' and hour != 12:
            hour += 12
        elif period == 'am' and hour == 12:
            hour = 0
        
        return hour, minute
    
    # Try just hour with am/pm
    match = re.match(r'^(\d{1,2})\s*(am|pm)$', time_str)
    if match:
        hour = int(match.group(1))
        period = match.group(2)
        
        if period == 'pm' and hour != 12:
            hour += 12
        elif period == 'am' and hour == 12:
            hour = 0
        
        return hour, 0
    
    return None


def compute_bazi_chart(
    birth_date,
    birth_time: Optional[str] = None,
    timezone: Optional[str] = None
) -> Dict[str, Any]:
    """
    Compute the complete BaZi (Four Pillars) chart.
    
    Args:
        birth_date: Birth date as string "YYYY-MM-DD" or datetime object
        birth_time: Birth time in various formats (optional, defaults to noon)
        timezone: Timezone string (for future use with location adjustment)
        
    Returns:
        Complete BaZi chart data
    """
    # Parse birth date
    try:
        if isinstance(birth_date, datetime):
            # Use the datetime object directly
            dt = birth_date
            # Reset to midnight, we'll apply birth_time separately
            dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        elif isinstance(birth_date, str):
            # Try parsing string date in various formats
            for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d"]:
                try:
                    dt = datetime.strptime(birth_date, fmt)
                    dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
                    break
                except ValueError:
                    continue
            else:
                raise ValueError(f"Could not parse date string: {birth_date}")
        else:
            raise ValueError(f"Unsupported birth_date type: {type(birth_date)}")
        
        # Apply birth time if provided
        time_parts = parse_birth_time(birth_time)
        if time_parts:
            hour, minute = time_parts
            dt = dt.replace(hour=hour, minute=minute)
        else:
            # Default to noon if no time
            dt = dt.replace(hour=12, minute=0)
        
        logger.info(f"[BaZi] Parsed datetime: {dt} (from birth_date={birth_date}, birth_time={birth_time})")
            
    except Exception as e:
        logger.error(f"[BaZi] Date parsing error: {e}")
        raise ValueError(f"Invalid date/time format: {birth_date} {birth_time}")
    
    # Get Chinese year
    chinese_year = get_chinese_year(dt)
    
    # Calculate all four pillars
    year_stem, year_branch, year_stem_idx, year_branch_idx = calculate_year_pillar(chinese_year)
    
    bazi_month = get_month_number(dt)
    month_stem, month_branch, month_stem_idx, month_branch_idx = calculate_month_pillar(year_stem_idx, bazi_month)
    
    day_stem, day_branch, day_stem_idx, day_branch_idx = calculate_day_pillar(dt)
    
    hour_stem, hour_branch, hour_stem_idx, hour_branch_idx = calculate_hour_pillar(day_stem_idx, dt.hour)
    
    # Build pillars structure
    pillars = {
        "year_pillar": {
            "stem": year_stem,
            "stem_pinyin": HEAVENLY_STEMS_PINYIN[year_stem_idx],
            "branch": year_branch,
            "branch_pinyin": EARTHLY_BRANCHES_PINYIN[year_branch_idx],
            "animal": BRANCH_ANIMALS[year_branch],
            "stem_element": STEM_ELEMENTS[year_stem],
            "branch_element": BRANCH_ELEMENTS[year_branch],
        },
        "month_pillar": {
            "stem": month_stem,
            "stem_pinyin": HEAVENLY_STEMS_PINYIN[month_stem_idx],
            "branch": month_branch,
            "branch_pinyin": EARTHLY_BRANCHES_PINYIN[month_branch_idx],
            "animal": BRANCH_ANIMALS[month_branch],
            "stem_element": STEM_ELEMENTS[month_stem],
            "branch_element": BRANCH_ELEMENTS[month_branch],
        },
        "day_pillar": {
            "stem": day_stem,
            "stem_pinyin": HEAVENLY_STEMS_PINYIN[day_stem_idx],
            "branch": day_branch,
            "branch_pinyin": EARTHLY_BRANCHES_PINYIN[day_branch_idx],
            "animal": BRANCH_ANIMALS[day_branch],
            "stem_element": STEM_ELEMENTS[day_stem],
            "branch_element": BRANCH_ELEMENTS[day_branch],
        },
        "hour_pillar": {
            "stem": hour_stem,
            "stem_pinyin": HEAVENLY_STEMS_PINYIN[hour_stem_idx],
            "branch": hour_branch,
            "branch_pinyin": EARTHLY_BRANCHES_PINYIN[hour_branch_idx],
            "animal": BRANCH_ANIMALS[hour_branch],
            "stem_element": STEM_ELEMENTS[hour_stem],
            "branch_element": BRANCH_ELEMENTS[hour_branch],
        },
    }
    
    # Day Master is the stem of the day pillar
    day_master = {
        "stem": day_stem,
        "stem_pinyin": HEAVENLY_STEMS_PINYIN[day_stem_idx],
        "element": STEM_ELEMENTS[day_stem],
        "polarity": STEM_POLARITY[day_stem],
    }
    
    # Calculate Five Elements distribution
    five_elements = calculate_five_elements(pillars)
    
    # Analyze element balance
    element_analysis = analyze_element_balance(five_elements, day_master["element"])
    
    # Calculate Ten Gods
    ten_gods = calculate_ten_gods(day_stem, pillars)
    
    # Build final chart
    chart = {
        "birth_data": {
            "date": birth_date,
            "time": birth_time or "12:00",
            "timezone": timezone,
            "chinese_year": chinese_year,
            "bazi_month": bazi_month,
        },
        "pillars": pillars,
        "day_master": day_master,
        "five_elements": five_elements,
        "element_analysis": element_analysis,
        "ten_gods": ten_gods,
        "summary": {
            "day_master_description": f"{day_master['stem_pinyin']} {day_master['element']} ({day_master['polarity']})",
            "dominant_element": element_analysis["dominant_element"],
            "weak_element": element_analysis["weak_element"],
            "balance_status": element_analysis["balance_status"],
            "day_master_strength": element_analysis["day_master_strength"],
            "supporting_elements": element_analysis["supporting_elements"],
        },
        "calculation_version": "0.5",
    }
    
    logger.info(f"[BaZi] Computed chart: Day Master = {day_master['stem_pinyin']} {day_master['element']}")
    
    return chart


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_element_description(element: str) -> Dict[str, str]:
    """Get descriptions and attributes for an element."""
    descriptions = {
        "Wood": {
            "nature": "Growth and expansion",
            "personality": "Creative, generous, idealistic, compassionate",
            "body_parts": "Liver, gallbladder, eyes, tendons",
            "season": "Spring",
            "direction": "East",
            "color": "Green",
        },
        "Fire": {
            "nature": "Transformation and passion",
            "personality": "Enthusiastic, charismatic, ambitious, restless",
            "body_parts": "Heart, small intestine, tongue, blood vessels",
            "season": "Summer",
            "direction": "South",
            "color": "Red",
        },
        "Earth": {
            "nature": "Stability and nurturing",
            "personality": "Reliable, practical, patient, stubborn",
            "body_parts": "Spleen, stomach, muscles, mouth",
            "season": "Late Summer",
            "direction": "Center",
            "color": "Yellow/Brown",
        },
        "Metal": {
            "nature": "Refinement and precision",
            "personality": "Disciplined, organized, righteous, rigid",
            "body_parts": "Lungs, large intestine, skin, nose",
            "season": "Autumn",
            "direction": "West",
            "color": "White/Gold",
        },
        "Water": {
            "nature": "Wisdom and adaptability",
            "personality": "Intuitive, reflective, diplomatic, indecisive",
            "body_parts": "Kidneys, bladder, bones, ears",
            "season": "Winter",
            "direction": "North",
            "color": "Black/Blue",
        },
    }
    return descriptions.get(element, {})


def format_pillar_display(pillar: Dict[str, str]) -> str:
    """Format a pillar for display."""
    return f"{pillar['stem']}{pillar['branch']} ({pillar['stem_pinyin']} {pillar['branch_pinyin']})"
