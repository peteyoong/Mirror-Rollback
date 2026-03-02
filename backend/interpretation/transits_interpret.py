"""Transit Interpretation Layer - Project Mirror Phase 3

===============================================================================
INTERPRETATION LAYER - Converts deterministic transit data to reflective language
===============================================================================
This module transforms raw astronomical transit data into grounded, 
non-fatalistic reflective language for Mirror users.

GUARDRAILS:
- NO fatalistic language ("will happen", "destined", "guaranteed", "fated")
- Use softer language ("you may notice", "there's a pull toward", "available attention")
- ALL content derived from transit_payload (no extra computation)
- Respects user sovereignty

Version: interpretation-v1
===============================================================================
"""

from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import re

# Disallowed fatalistic words/phrases
DISALLOWED_PATTERNS = [
    r'\bwill\s+happen\b',
    r'\bwill\s+be\b',
    r'\bwill\s+cause\b',
    r'\bdestined\b',
    r'\bdestiny\b',
    r'\bfated\b',
    r'\bfate\b',
    r'\bguaranteed\b',
    r'\bcertain\s+to\b',
    r'\binevitable\b',
    r'\bmust\s+happen\b',
    r'\bprediction\b',
    r'\bpredict\b',
]

# Planet interpretive themes (grounded, reflective)
PLANET_THEMES = {
    'sun': {
        'domain': 'identity and vitality',
        'attention': 'sense of self and creative expression',
        'invitation': 'notice where your energy wants to flow'
    },
    'moon': {
        'domain': 'emotional landscape',
        'attention': 'inner rhythms and emotional needs',
        'invitation': 'be present with what you feel'
    },
    'mercury': {
        'domain': 'thought and communication',
        'attention': 'how you process and share information',
        'invitation': 'observe your mental patterns'
    },
    'venus': {
        'domain': 'connection and values',
        'attention': 'relationships and what you find beautiful',
        'invitation': 'notice what draws you toward pleasure and harmony'
    },
    'mars': {
        'domain': 'action and assertion',
        'attention': 'drive, motivation, and how you assert yourself',
        'invitation': 'channel energy with awareness'
    },
    'jupiter': {
        'domain': 'expansion and meaning',
        'attention': 'growth opportunities and broader perspective',
        'invitation': 'stay open to possibilities without attachment'
    },
    'saturn': {
        'domain': 'structure and responsibility',
        'attention': 'boundaries, commitments, and maturation',
        'invitation': 'work with limitations as teachers'
    },
    'uranus': {
        'domain': 'awakening and disruption',
        'attention': 'unexpected shifts and liberation impulses',
        'invitation': 'stay flexible with change'
    },
    'neptune': {
        'domain': 'imagination and dissolution',
        'attention': 'intuition, creativity, and spiritual longing',
        'invitation': 'discern between vision and illusion'
    },
    'pluto': {
        'domain': 'transformation and depth',
        'attention': 'deep psychological processes',
        'invitation': 'honor what wants to transform'
    }
}

# Aspect interpretive qualities
ASPECT_QUALITIES = {
    'conjunction': {
        'quality': 'intensification',
        'description': 'merging or amplifying',
        'tone': 'focused attention where energies combine'
    },
    'opposition': {
        'quality': 'polarity',
        'description': 'balancing or integrating opposites',
        'tone': 'tension that invites integration'
    },
    'square': {
        'quality': 'friction',
        'description': 'creative tension',
        'tone': 'pressure that can catalyze growth'
    },
    'trine': {
        'quality': 'flow',
        'description': 'harmonious support',
        'tone': 'ease and natural alignment'
    },
    'sextile': {
        'quality': 'opportunity',
        'description': 'available support',
        'tone': 'openings that respond to engagement'
    }
}

# Sign element qualities
SIGN_ELEMENTS = {
    'Aries': 'fire', 'Leo': 'fire', 'Sagittarius': 'fire',
    'Taurus': 'earth', 'Virgo': 'earth', 'Capricorn': 'earth',
    'Gemini': 'air', 'Libra': 'air', 'Aquarius': 'air',
    'Cancer': 'water', 'Scorpio': 'water', 'Pisces': 'water'
}

ELEMENT_QUALITIES = {
    'fire': 'initiative and inspiration',
    'earth': 'grounding and manifestation',
    'air': 'ideas and connection',
    'water': 'emotion and intuition'
}


def validate_no_fatalism(text: str) -> bool:
    """Check that text contains no disallowed fatalistic language"""
    text_lower = text.lower()
    for pattern in DISALLOWED_PATTERNS:
        if re.search(pattern, text_lower):
            return False
    return True


def get_planet_theme(planet: str) -> Dict[str, str]:
    """Get interpretive theme for a planet"""
    return PLANET_THEMES.get(planet.lower(), {
        'domain': 'cosmic influence',
        'attention': 'subtle shifts',
        'invitation': 'remain present'
    })


def get_aspect_quality(aspect: str) -> Dict[str, str]:
    """Get interpretive quality for an aspect type"""
    return ASPECT_QUALITIES.get(aspect.lower(), {
        'quality': 'connection',
        'description': 'interaction',
        'tone': 'available attention'
    })


def interpret_exact_hit(hit: Dict[str, Any]) -> str:
    """Generate a grounded interpretation for a single exact aspect hit"""
    transit_planet = hit.get('transit_planet', 'unknown')
    aspect = hit.get('aspect', 'aspect')
    natal_body = hit.get('natal_body', 'unknown')
    orb = hit.get('orb', 0)
    
    transit_theme = get_planet_theme(transit_planet)
    natal_theme = get_planet_theme(natal_body)
    aspect_quality = get_aspect_quality(aspect)
    
    # Tighter orbs = more pronounced
    intensity = "subtle" if orb > 1.5 else "noticeable" if orb > 0.5 else "pronounced"
    
    return (
        f"A {intensity} {aspect_quality['quality']} between transiting {transit_planet.capitalize()} "
        f"({transit_theme['domain']}) and your natal {natal_body.capitalize()} "
        f"({natal_theme['domain']}). You may notice {aspect_quality['tone']}."
    )


def interpret_ingress(ingress: Dict[str, Any], include_houses: bool = True) -> str:
    """Generate interpretation for a sign ingress"""
    planet = ingress.get('planet', 'unknown')
    to_sign = ingress.get('to_sign', 'unknown')
    house = ingress.get('house')
    
    planet_theme = get_planet_theme(planet)
    element = SIGN_ELEMENTS.get(to_sign, 'unknown')
    element_quality = ELEMENT_QUALITIES.get(element, 'subtle energy')
    
    base = (
        f"{planet.capitalize()} moves into {to_sign}, shifting your {planet_theme['domain']} "
        f"toward {element_quality}."
    )
    
    if include_houses and house:
        base += f" This activates your {house}th house area of life."
    
    return base


def interpret_station(station: Dict[str, Any], include_houses: bool = True) -> str:
    """Generate interpretation for a retrograde/direct station"""
    planet = station.get('planet', 'unknown')
    station_type = station.get('type', 'station')
    sign = station.get('sign', 'unknown')
    house = station.get('house')
    
    planet_theme = get_planet_theme(planet)
    
    if 'retrograde' in station_type:
        direction = "appears to slow and turn inward"
        invitation = f"review and reflect on {planet_theme['domain']}"
    else:
        direction = "appears to station and move forward"
        invitation = f"externalize insights about {planet_theme['domain']}"
    
    base = f"{planet.capitalize()} {direction} in {sign}. An invitation to {invitation}."
    
    if include_houses and house:
        base += f" Pay attention to house {house} themes."
    
    return base


def generate_headline(transit_payload: Dict[str, Any], mode: str) -> str:
    """Generate a single-sentence grounded headline"""
    exact_hits = transit_payload.get('exact_hits', [])
    ingresses = transit_payload.get('ingresses', [])
    stations = transit_payload.get('stations', [])
    
    total_events = len(exact_hits) + len(ingresses) + len(stations)
    
    if total_events == 0:
        return "A quiet moment with subtle cosmic currents available for inner reflection."
    
    # Find most significant aspect (tightest orb)
    if exact_hits:
        tightest = min(exact_hits, key=lambda x: x.get('orb', 999))
        transit_planet = tightest.get('transit_planet', 'cosmic')
        natal_body = tightest.get('natal_body', 'inner')
        aspect = tightest.get('aspect', 'connection')
        
        transit_theme = get_planet_theme(transit_planet)
        return f"Your attention may be drawn to {transit_theme['domain']} as transiting {transit_planet.capitalize()} {aspect}s your natal {natal_body.capitalize()}."
    
    if ingresses:
        ing = ingresses[0]
        planet = ing.get('planet', 'A planet')
        to_sign = ing.get('to_sign', 'a new sign')
        return f"{planet.capitalize()} enters {to_sign}, inviting a shift in how you engage with its themes."
    
    if stations:
        sta = stations[0]
        planet = sta.get('planet', 'A planet')
        stype = 'inward' if 'retrograde' in sta.get('type', '') else 'forward'
        return f"{planet.capitalize()} stations {stype}, marking a reflective turning point."
    
    return "Cosmic currents are in motion, offering opportunities for presence and reflection."


def generate_key_points(transit_payload: Dict[str, Any], include_houses: bool = True, max_points: int = 6) -> List[str]:
    """Generate 3-6 key points describing what's active"""
    points = []
    
    exact_hits = transit_payload.get('exact_hits', [])
    aspects_now = transit_payload.get('aspects_to_natal_now', [])  # For 'now' mode
    ingresses = transit_payload.get('ingresses', [])
    stations = transit_payload.get('stations', [])
    
    # Use aspects_to_natal_now if exact_hits is empty (now mode)
    if not exact_hits and aspects_now:
        exact_hits = aspects_now
    
    # Prioritize tightest aspects
    sorted_hits = sorted(exact_hits, key=lambda x: x.get('orb', 999))[:3]
    for hit in sorted_hits:
        points.append(interpret_exact_hit(hit))
    
    # Add ingresses
    for ing in ingresses[:2]:
        points.append(interpret_ingress(ing, include_houses))
    
    # Add stations
    for sta in stations[:1]:
        points.append(interpret_station(sta, include_houses))
    
    # Ensure we have at least 3 points with meaningful filler
    default_points = [
        "Cosmic currents are present, inviting you to notice what draws your attention.",
        "Multiple subtle influences are available; no single energy dominates.",
        "Take time to notice what resonates with your current experience.",
        "This moment offers space for reflection and presence.",
        "Trust your inner knowing about what themes feel most alive."
    ]
    
    while len(points) < 3:
        if not include_houses and len(points) < 3:
            points.append("Without house data, focus on the planetary themes themselves.")
        if default_points:
            points.append(default_points.pop(0))
    
    return points[:max_points]


def generate_reflection_questions(transit_payload: Dict[str, Any]) -> List[str]:
    """Generate 2-4 reflection questions based on active transits"""
    questions = []
    exact_hits = transit_payload.get('exact_hits', [])
    
    # Get unique planets involved
    transit_planets = set()
    natal_bodies = set()
    
    for hit in exact_hits[:5]:
        transit_planets.add(hit.get('transit_planet', '').lower())
        natal_bodies.add(hit.get('natal_body', '').lower())
    
    # Generate questions based on planets
    if 'saturn' in transit_planets or 'saturn' in natal_bodies:
        questions.append("What structures in your life are asking for attention or revision?")
    
    if 'moon' in transit_planets or 'moon' in natal_bodies:
        questions.append("What emotional patterns are surfacing for acknowledgment?")
    
    if 'mercury' in transit_planets or 'mercury' in natal_bodies:
        questions.append("How are you communicating your truth, and what wants clearer expression?")
    
    if 'venus' in transit_planets or 'venus' in natal_bodies:
        questions.append("What brings you genuine pleasure, and how are you honoring that?")
    
    if 'mars' in transit_planets or 'mars' in natal_bodies:
        questions.append("Where is your energy asking to be directed with intention?")
    
    if 'jupiter' in transit_planets or 'jupiter' in natal_bodies:
        questions.append("What possibilities are opening, and how can you meet them without grasping?")
    
    if 'pluto' in transit_planets or 'pluto' in natal_bodies:
        questions.append("What is ready to transform, and can you allow it without forcing?")
    
    if 'uranus' in transit_planets or 'uranus' in natal_bodies:
        questions.append("Where might unexpected change be liberating rather than threatening?")
    
    if 'neptune' in transit_planets or 'neptune' in natal_bodies:
        questions.append("What is the difference between your dreams and your illusions right now?")
    
    # Default questions if none generated
    if not questions:
        questions = [
            "What is your body telling you right now?",
            "What would it mean to respond rather than react today?",
            "Where can you practice presence with what is?"
        ]
    
    return questions[:4]


def generate_two_minute_practice(transit_payload: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a simple 2-minute grounding practice"""
    exact_hits = transit_payload.get('exact_hits', [])
    
    # Determine practice focus based on most active planet
    focus = 'presence'
    if exact_hits:
        planets = [h.get('transit_planet', '').lower() for h in exact_hits[:3]]
        if 'saturn' in planets:
            focus = 'structure'
        elif 'moon' in planets:
            focus = 'emotion'
        elif 'mercury' in planets:
            focus = 'clarity'
        elif 'mars' in planets:
            focus = 'energy'
        elif 'venus' in planets:
            focus = 'appreciation'
    
    practices = {
        'presence': {
            'title': 'Grounding Breath',
            'steps': [
                'Find a comfortable position and close your eyes',
                'Take three slow breaths, feeling your feet on the ground',
                'Notice one thing you can hear, one thing you can feel, one thing you appreciate'
            ]
        },
        'structure': {
            'title': 'Boundary Check-In',
            'steps': [
                'Pause and feel the edges of your body',
                'Ask yourself: What is mine to carry? What is not?',
                'Set one small intention for how you want to use your energy today'
            ]
        },
        'emotion': {
            'title': 'Emotional Weather Report',
            'steps': [
                'Place a hand on your heart and breathe slowly',
                'Without judgment, name what you feel (e.g., "There is sadness here")',
                'Let the feeling be present without needing to change it'
            ]
        },
        'clarity': {
            'title': 'Mental Clearing',
            'steps': [
                'Write down any swirling thoughts on paper',
                'Take three breaths, imagining your mind as a clear sky',
                'Choose one thought to engage with intentionally'
            ]
        },
        'energy': {
            'title': 'Energy Direction',
            'steps': [
                'Stand and shake out your hands and feet for 20 seconds',
                'Feel the energy in your body—where does it want to go?',
                'Set an intention for channeling this energy constructively'
            ]
        },
        'appreciation': {
            'title': 'Gratitude Anchor',
            'steps': [
                'Think of one thing you genuinely appreciate right now',
                'Let yourself feel that appreciation in your body',
                'Carry that feeling as an anchor through your day'
            ]
        }
    }
    
    return practices.get(focus, practices['presence'])


def generate_attention_windows(transit_payload: Dict[str, Any], mode: str) -> List[Dict[str, Any]]:
    """Generate attention windows from exact hits and events"""
    windows = []
    
    if mode == 'now':
        # For "now" mode, just note the current moment
        timestamp = transit_payload.get('timestamp_utc', datetime.now(timezone.utc).isoformat())
        exact_hits = transit_payload.get('exact_hits', [])
        
        if exact_hits:
            events = [f"{h['transit_planet']}_{h['aspect']}_{h['natal_body']}" for h in exact_hits[:3]]
            windows.append({
                'from_utc': timestamp,
                'to_utc': timestamp,
                'label': 'Current active aspects',
                'based_on': events
            })
    else:
        # For window mode, group by daily summary
        daily_summaries = transit_payload.get('daily_summary', [])
        
        for day in daily_summaries[:7]:  # Limit to 7 days
            events = day.get('peak_events', [])
            if events:
                date = day.get('date', '')
                windows.append({
                    'from_utc': f"{date}T00:00:00Z",
                    'to_utc': f"{date}T23:59:59Z",
                    'label': f"Active on {date}",
                    'based_on': events[:5]
                })
    
    return windows


def interpret_transits(
    transit_payload: Dict[str, Any],
    mode: str = 'now',
    consciousness_level: Optional[int] = None,
    style: str = 'grounded',
    request_timestamp_utc: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main interpretation function - converts deterministic transit data
    into grounded, non-fatalistic reflective language.
    
    Args:
        transit_payload: Raw JSON from /api/compute/transits/now or /window
        mode: 'now' or 'window'
        consciousness_level: Optional consciousness calibration (not used in v1)
        style: Interpretation style (only 'grounded' supported in v1)
        request_timestamp_utc: Optional timestamp from request
    
    Returns:
        Interpretation response with headline, key_points, reflect, practice, etc.
    """
    # Determine timestamp deterministically:
    # 1) If transit_payload.timestamp_utc exists, use that
    # 2) Else if transit_payload.window.from_utc exists, use that
    # 3) Else if request includes timestamp_utc, use that
    # 4) Else use current UTC
    interpretation_timestamp = None
    
    if transit_payload.get('timestamp_utc'):
        interpretation_timestamp = transit_payload['timestamp_utc']
    elif transit_payload.get('window', {}).get('from_utc'):
        interpretation_timestamp = transit_payload['window']['from_utc']
    elif request_timestamp_utc:
        interpretation_timestamp = request_timestamp_utc
    else:
        interpretation_timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # Check if houses should be included
    house_activation = transit_payload.get('house_activation', {})
    include_houses = house_activation.get('enabled', False)
    
    # Generate interpretation components
    headline = generate_headline(transit_payload, mode)
    key_points = generate_key_points(transit_payload, include_houses)
    reflect = generate_reflection_questions(transit_payload)
    practice = generate_two_minute_practice(transit_payload)
    attention_windows = generate_attention_windows(transit_payload, mode)
    
    # Validate no fatalism in generated content
    all_text = headline + ' '.join(key_points) + ' '.join(reflect)
    if not validate_no_fatalism(all_text):
        # This shouldn't happen with our templates, but safeguard
        raise ValueError("Generated content contains disallowed fatalistic language")
    
    return {
        'meta': {
            'mode': mode,
            'timestamp_utc': interpretation_timestamp,
            'tone_profile': style
        },
        'headline': headline,
        'key_points': key_points,
        'reflect': reflect,
        'two_minute_practice': practice,
        'attention_windows': attention_windows,
        'guardrails': {
            'no_fatalism': True,
            'no_predictions': True,
            'user_sovereignty': True
        }
    }


# =============================================================================
# TESTING UTILITIES
# =============================================================================

def get_test_transit_payload_now() -> Dict[str, Any]:
    """Return a fixed transit payload for testing (mode=now)"""
    return {
        "meta": {
            "ayanamsa": "fixed_sv_31.2836",
            "house_system": "equal",
            "orb_deg": 2.0
        },
        "timestamp_utc": "2026-03-02T09:00:00Z",
        "transiting_planets": {
            "sun": {"longitude": 310.5, "sign": "Aquarius", "retrograde": False, "house": 10},
            "moon": {"longitude": 116.7, "sign": "Cancer", "retrograde": False, "house": 4},
            "saturn": {"longitude": 330.6, "sign": "Pisces", "retrograde": False, "house": 11}
        },
        "aspects_to_natal_now": [
            {"transit_planet": "saturn", "aspect": "conjunction", "natal_body": "moon", "orb": 0.82, "exact_angle_delta": 0.82},
            {"transit_planet": "uranus", "aspect": "opposition", "natal_body": "pluto", "orb": 0.02, "exact_angle_delta": 0.02},
            {"transit_planet": "venus", "aspect": "trine", "natal_body": "sun", "orb": 1.21, "exact_angle_delta": 1.21}
        ],
        "house_activation": {
            "enabled": False,
            "reason": "natal_houses_missing"
        }
    }


def get_test_transit_payload_window() -> Dict[str, Any]:
    """Return a fixed transit payload for testing (mode=window)"""
    return {
        "meta": {
            "ayanamsa": "fixed_sv_31.2836",
            "house_system": "equal",
            "orb_deg": 2.0,
            "window_days": 30,
            "granularity": "daily"
        },
        "window": {
            "from_utc": "2026-03-02T00:00:00Z",
            "to_utc": "2026-04-01T00:00:00Z"
        },
        "exact_hits": [
            {"timestamp_utc": "2026-03-02T03:02:48Z", "transit_planet": "moon", "aspect": "opposition", "natal_body": "saturn", "orb": 0.01, "orb_raw": 0.006843},
            {"timestamp_utc": "2026-03-05T11:37:30Z", "transit_planet": "mercury", "aspect": "opposition", "natal_body": "jupiter", "orb": 0.01, "orb_raw": 0.003485},
            {"timestamp_utc": "2026-03-09T09:00:00Z", "transit_planet": "sun", "aspect": "opposition", "natal_body": "jupiter", "orb": 0.01, "orb_raw": 0.004741}
        ],
        "ingresses": [
            {"timestamp_utc": "2026-03-04T05:22:01Z", "planet": "mars", "from_sign": "Capricorn", "to_sign": "Aquarius", "longitude": 300.0, "house": 10},
            {"timestamp_utc": "2026-03-07T11:31:52Z", "planet": "venus", "from_sign": "Aquarius", "to_sign": "Pisces", "longitude": 330.0, "house": 11}
        ],
        "stations": [],
        "house_activation": {
            "enabled": True,
            "top_houses": [5, 6, 3],
            "scores": {"5": 68.1, "6": 37.8, "3": 22.4}
        },
        "daily_summary": [
            {"date": "2026-03-02", "peak_events": ["moon_opposition_saturn", "venus_sextile_neptune"], "top_houses": [5, 6]},
            {"date": "2026-03-03", "peak_events": ["uranus_opposition_pluto", "venus_trine_sun"], "top_houses": [6, 3]},
            {"date": "2026-03-04", "peak_events": ["mars_ingress_Aquarius", "moon_ingress_Virgo"], "top_houses": [5, 4]}
        ]
    }


if __name__ == '__main__':
    import json
    
    print("=" * 70)
    print("Transit Interpretation Layer - Test")
    print("=" * 70)
    
    # Test with "now" payload
    print("\n--- Mode: NOW ---")
    payload_now = get_test_transit_payload_now()
    result_now = interpret_transits(payload_now, mode='now')
    print(json.dumps(result_now, indent=2))
    
    # Test with "window" payload
    print("\n--- Mode: WINDOW ---")
    payload_window = get_test_transit_payload_window()
    result_window = interpret_transits(payload_window, mode='window')
    print(json.dumps(result_window, indent=2))
