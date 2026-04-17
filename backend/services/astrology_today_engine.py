"""
Astrology Today Engine — Transit Prioritization & Interpretation
================================================================
Replaces the weak template-based system with a real signal hierarchy.

Priority order:
1. Transit-to-natal exact aspects (strongest personal triggers)
2. Sign concentration / stellium emphasis (collective weather)
3. House activation (life area focus)
4. Fast planet tone (Moon = emotional weather)
5. Slow planet backdrop (structural pressure)

Output: Ranked signals → narrative → proof layer
"""

import swisseph as swe
import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)

swe.set_ephe_path(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ephe'))

SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
         'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']

PLANETS = {
    'Sun': swe.SUN, 'Moon': swe.MOON, 'Mercury': swe.MERCURY,
    'Venus': swe.VENUS, 'Mars': swe.MARS, 'Jupiter': swe.JUPITER,
    'Saturn': swe.SATURN, 'Uranus': swe.URANUS, 'Neptune': swe.NEPTUNE,
    'Pluto': swe.PLUTO
}

# Planet importance weights for scoring
PLANET_WEIGHT = {
    'Sun': 10, 'Moon': 9, 'Mercury': 6, 'Venus': 6, 'Mars': 7,
    'Jupiter': 8, 'Saturn': 9, 'Uranus': 8, 'Neptune': 7, 'Pluto': 9
}

ASPECT_TYPES = {
    0: {'name': 'conjunction', 'orb': 8, 'weight': 1.0, 'nature': 'fusion'},
    60: {'name': 'sextile', 'orb': 4, 'weight': 0.4, 'nature': 'opportunity'},
    90: {'name': 'square', 'orb': 7, 'weight': 0.9, 'nature': 'tension'},
    120: {'name': 'trine', 'orb': 7, 'weight': 0.6, 'nature': 'flow'},
    180: {'name': 'opposition', 'orb': 8, 'weight': 0.95, 'nature': 'polarity'},
}

# Sign behavioral translations (how each sign FEELS, not astro jargon)
SIGN_BEHAVIOR = {
    'Aries': {
        'energy': 'activation',
        'tone': 'urgent, direct, initiating',
        'behavior': ['You may feel a push to act before thinking it through',
                     'Impatience rises — waiting feels intolerable',
                     'Conversations get more direct, possibly blunt',
                     'The impulse to start something new is stronger than usual'],
        'feeling': ['restless energy that needs a target',
                    'a surge of courage or irritation — sometimes both',
                    'the body wants to move, not sit'],
        'keyword': 'initiation'
    },
    'Taurus': {
        'energy': 'stabilization',
        'tone': 'grounded, slow, sensory',
        'behavior': ['You may resist change more than usual',
                     'Comfort-seeking intensifies — food, rest, security',
                     'Financial or material concerns surface'],
        'feeling': ['a need for things to feel solid and predictable',
                    'stubbornness that feels like self-preservation'],
        'keyword': 'grounding'
    },
    'Gemini': {
        'energy': 'mental',
        'tone': 'curious, scattered, communicative',
        'behavior': ['Your mind races between options',
                     'Conversations multiply — messaging, calls, ideas',
                     'Difficulty committing to one direction'],
        'feeling': ['mental restlessness', 'information overload'],
        'keyword': 'communication'
    },
    'Cancer': {
        'energy': 'emotional',
        'tone': 'protective, sensitive, nurturing',
        'behavior': ['Emotional reactions feel bigger than expected',
                     'Home and family concerns take priority',
                     'You may withdraw to feel safe'],
        'feeling': ['tenderness that can flip to defensiveness',
                    'nostalgia or longing for comfort'],
        'keyword': 'protection'
    },
    'Leo': {
        'energy': 'expressive',
        'tone': 'confident, creative, dramatic',
        'behavior': ['The need to be seen or acknowledged increases',
                     'Creative impulses demand expression',
                     'Pride can amplify small conflicts'],
        'feeling': ['warmth and generosity — or wounded pride',
                    'a desire to shine or lead'],
        'keyword': 'expression'
    },
    'Virgo': {
        'energy': 'analytical',
        'tone': 'precise, critical, service-oriented',
        'behavior': ['Details demand more attention than usual',
                     'Self-criticism or perfectionism intensifies',
                     'Health and routine come into focus'],
        'feeling': ['anxiety about getting things right',
                    'a need for order and usefulness'],
        'keyword': 'refinement'
    },
    'Libra': {
        'energy': 'relational',
        'tone': 'diplomatic, indecisive, harmony-seeking',
        'behavior': ['Relationships take center stage',
                     'Decision-making slows as you weigh all sides',
                     'Conflict avoidance increases'],
        'feeling': ['a need for fairness and balance',
                    'discomfort with confrontation'],
        'keyword': 'balance'
    },
    'Scorpio': {
        'energy': 'transformative',
        'tone': 'intense, probing, private',
        'behavior': ['Hidden dynamics surface unexpectedly',
                     'Trust becomes a bigger issue',
                     'Power dynamics in relationships sharpen'],
        'feeling': ['emotional intensity that demands honesty',
                    'a pull toward depth, away from surface'],
        'keyword': 'transformation'
    },
    'Sagittarius': {
        'energy': 'expansive',
        'tone': 'restless, optimistic, philosophical',
        'behavior': ['The desire for freedom or escape grows',
                     'Big-picture thinking overrides details',
                     'Commitments can feel constraining'],
        'feeling': ['restlessness and wanderlust',
                    'optimism that may skip important realities'],
        'keyword': 'expansion'
    },
    'Capricorn': {
        'energy': 'structural',
        'tone': 'disciplined, ambitious, serious',
        'behavior': ['Career and responsibility concerns intensify',
                     'Long-term planning feels more urgent',
                     'Authority dynamics become more visible'],
        'feeling': ['pressure to achieve or prove yourself',
                    'a weight of responsibility'],
        'keyword': 'structure'
    },
    'Aquarius': {
        'energy': 'disruptive',
        'tone': 'independent, unconventional, detached',
        'behavior': ['The urge to break from routine or expectations grows',
                     'Group dynamics and social concerns surface',
                     'Emotional detachment can be mistaken for not caring'],
        'feeling': ['a need for space and independence',
                    'frustration with outdated systems or rules'],
        'keyword': 'liberation'
    },
    'Pisces': {
        'energy': 'dissolving',
        'tone': 'intuitive, foggy, compassionate',
        'behavior': ['Boundaries between self and others blur',
                     'Intuition is louder but harder to trust',
                     'Creative or spiritual impulses increase'],
        'feeling': ['emotional sensitivity amplified',
                    'a sense of drifting or surrendering'],
        'keyword': 'dissolution'
    },
}

HOUSE_CONTEXT = {
    1: 'identity, self-image, how you show up',
    2: 'money, resources, self-worth',
    3: 'communication, daily interactions, decisions',
    4: 'home, family, emotional foundations',
    5: 'creativity, self-expression, play, romance',
    6: 'health, daily routine, work, service',
    7: 'relationships, partnerships, one-on-one dynamics',
    8: 'shared resources, intimacy, transformation',
    9: 'beliefs, travel, big-picture meaning',
    10: 'career, public role, reputation, authority',
    11: 'community, friendships, future goals',
    12: 'solitude, unconscious patterns, endings',
}

# Aspect interpretation templates (behavioral, not jargon)
ASPECT_INTERPRETATIONS = {
    ('conjunction', 'tension'): "merging with",
    ('conjunction', 'flow'): "amplifying",
    ('square', 'tension'): "clashing with",
    ('opposition', 'tension'): "pulling against",
    ('trine', 'flow'): "supporting",
    ('sextile', 'flow'): "opening up",
}


def get_current_transits(dt: Optional[datetime] = None) -> Dict[str, Dict]:
    """Get all current planet positions (tropical)."""
    if not dt:
        dt = datetime.now(timezone.utc)
    jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60.0)
    
    positions = {}
    for name, pid in PLANETS.items():
        result = swe.calc_ut(jd, pid, swe.FLG_SWIEPH)
        lon = result[0][0]
        speed = result[0][3]
        sign_idx = int(lon / 30) % 12
        positions[name] = {
            'longitude': lon,
            'sign': SIGNS[sign_idx],
            'degree': lon % 30,
            'speed': speed,
            'retrograde': speed < 0,
        }
    return positions


def compute_transit_natal_aspects(
    transit_positions: Dict[str, Dict],
    natal_planets: Dict[str, Dict],
) -> List[Dict]:
    """Compute transit-to-natal aspects, scored by strength."""
    aspects = []
    
    for t_name, t_data in transit_positions.items():
        t_lon = t_data['longitude']
        for n_name, n_data in natal_planets.items():
            if not isinstance(n_data, dict):
                continue
            n_lon = n_data.get('longitude', 0)
            if not n_lon:
                continue
            
            # Check each aspect type
            for angle, asp_info in ASPECT_TYPES.items():
                diff = abs(t_lon - n_lon) % 360
                if diff > 180:
                    diff = 360 - diff
                
                orb = abs(diff - angle)
                if orb <= asp_info['orb']:
                    # Score: tighter orb + heavier planets = stronger
                    orb_score = 1.0 - (orb / asp_info['orb'])
                    planet_score = (PLANET_WEIGHT.get(t_name, 5) + PLANET_WEIGHT.get(n_name, 5)) / 20.0
                    total_score = orb_score * asp_info['weight'] * planet_score
                    
                    aspects.append({
                        'transit_planet': t_name,
                        'natal_planet': n_name,
                        'aspect': asp_info['name'],
                        'nature': asp_info['nature'],
                        'orb': round(orb, 1),
                        'score': round(total_score, 3),
                        'transit_sign': t_data['sign'],
                        'natal_sign': n_data.get('sign', '?'),
                    })
    
    # Sort by score descending
    aspects.sort(key=lambda x: -x['score'])
    return aspects


def detect_sign_concentration(positions: Dict[str, Dict]) -> List[Dict]:
    """Detect sign concentrations / stellium-like clusters."""
    sign_groups = {}
    for name, data in positions.items():
        sign = data['sign']
        if sign not in sign_groups:
            sign_groups[sign] = []
        sign_groups[sign].append(name)
    
    concentrations = []
    for sign, planets in sign_groups.items():
        if len(planets) >= 2:
            # Score: more planets = stronger, outer planets count more
            score = sum(PLANET_WEIGHT.get(p, 5) for p in planets) / 10.0
            has_luminaries = 'Sun' in planets or 'Moon' in planets
            has_outers = any(p in planets for p in ['Saturn', 'Uranus', 'Neptune', 'Pluto'])
            
            concentrations.append({
                'sign': sign,
                'planets': planets,
                'count': len(planets),
                'score': round(score, 2),
                'has_luminaries': has_luminaries,
                'has_outers': has_outers,
                'behavior': SIGN_BEHAVIOR.get(sign, {}),
            })
    
    concentrations.sort(key=lambda x: -x['score'])
    return concentrations


def compute_house_activations(
    transit_positions: Dict[str, Dict],
    natal_cusps: List[float],
) -> List[Dict]:
    """Compute which natal houses are most activated by current transits."""
    if not natal_cusps or len(natal_cusps) != 12:
        return []
    
    house_scores = {i+1: {'planets': [], 'score': 0} for i in range(12)}
    
    for name, data in transit_positions.items():
        lon = data['longitude']
        for i in range(12):
            c_start = natal_cusps[i]
            c_end = natal_cusps[(i + 1) % 12]
            in_house = False
            if c_end < c_start:
                in_house = lon >= c_start or lon < c_end
            else:
                in_house = c_start <= lon < c_end
            
            if in_house:
                house_scores[i + 1]['planets'].append(name)
                house_scores[i + 1]['score'] += PLANET_WEIGHT.get(name, 5)
                break
    
    activations = []
    for house, data in house_scores.items():
        if data['planets']:
            activations.append({
                'house': house,
                'planets': data['planets'],
                'score': data['score'],
                'context': HOUSE_CONTEXT.get(house, ''),
            })
    
    activations.sort(key=lambda x: -x['score'])
    return activations


def classify_day_energy(
    aspects: List[Dict],
    concentrations: List[Dict],
    transit_positions: Dict[str, Dict],
) -> Dict[str, Any]:
    """Classify the overall day energy type."""
    
    tension_score = sum(a['score'] for a in aspects if a['nature'] in ('tension', 'polarity'))
    flow_score = sum(a['score'] for a in aspects if a['nature'] in ('flow', 'opportunity'))
    fusion_score = sum(a['score'] for a in aspects if a['nature'] == 'fusion')
    
    # Check Moon for emotional tone
    moon = transit_positions.get('Moon', {})
    moon_sign = moon.get('sign', '')
    
    # Determine primary energy
    fire_signs = {'Aries', 'Leo', 'Sagittarius'}
    water_signs = {'Cancer', 'Scorpio', 'Pisces'}
    earth_signs = {'Taurus', 'Virgo', 'Capricorn'}
    air_signs = {'Gemini', 'Libra', 'Aquarius'}
    
    element_count = {'fire': 0, 'water': 0, 'earth': 0, 'air': 0}
    for _, data in transit_positions.items():
        s = data['sign']
        if s in fire_signs: element_count['fire'] += 1
        elif s in water_signs: element_count['water'] += 1
        elif s in earth_signs: element_count['earth'] += 1
        elif s in air_signs: element_count['air'] += 1
    
    dominant_element = max(element_count, key=element_count.get)
    
    # Classify
    tags = []
    if tension_score > flow_score * 1.5:
        tags.append('tension-heavy')
    if flow_score > tension_score * 1.5:
        tags.append('opportunity-heavy')
    if element_count['fire'] >= 4:
        tags.append('action-heavy')
    if element_count['water'] >= 3:
        tags.append('emotionally-charged')
    if element_count['air'] >= 3:
        tags.append('mentally-active')
    if element_count['earth'] >= 3:
        tags.append('grounded')
    if moon_sign in water_signs:
        tags.append('emotionally-charged')
    
    # Check for stellium
    top_conc = concentrations[0] if concentrations else None
    if top_conc and top_conc['count'] >= 4:
        tags.append('stellium-active')
    
    if not tags:
        tags.append('mixed')
    
    return {
        'tags': tags,
        'tension_score': round(tension_score, 2),
        'flow_score': round(flow_score, 2),
        'dominant_element': dominant_element,
        'element_counts': element_count,
        'moon_sign': moon_sign,
    }


def build_today_narrative(
    aspects: List[Dict],
    concentrations: List[Dict],
    house_activations: List[Dict],
    day_energy: Dict,
    transit_positions: Dict[str, Dict],
) -> Dict[str, Any]:
    """Build the full Today narrative from ranked signals."""
    
    top_concentration = concentrations[0] if concentrations else None
    top_aspects = aspects[:3]
    top_house = house_activations[0] if house_activations else None
    moon = transit_positions.get('Moon', {})
    
    # =========================================================
    # HEADLINE — The single most important thing about today
    # =========================================================
    headline = _build_headline(top_concentration, top_aspects, day_energy, moon)
    
    # =========================================================
    # WHAT'S HAPPENING — 2-3 real-world dynamics
    # =========================================================
    whats_happening = _build_whats_happening(top_concentration, top_aspects, day_energy)
    
    # =========================================================
    # HOW IT SHOWS UP — Observable behaviors
    # =========================================================
    how_it_shows_up = _build_how_shows_up(top_concentration, top_aspects, top_house, moon)
    
    # =========================================================
    # WHAT IT FEELS LIKE — Physical/emotional signals
    # =========================================================
    what_it_feels_like = _build_feelings(top_concentration, day_energy, moon)
    
    # =========================================================
    # THE MOVE — One behavioral shift
    # =========================================================
    the_move = _build_the_move(top_concentration, top_aspects, day_energy)
    
    # =========================================================
    # WHERE CONTEXT — Life area
    # =========================================================
    where_context = None
    if top_house:
        where_context = f"This lands especially in the area of {top_house['context']}."
    
    # =========================================================
    # TECHNICAL / PROOF LAYER
    # =========================================================
    technical = _build_proof_layer(aspects, concentrations, house_activations, day_energy, transit_positions)
    
    return {
        'headline': headline,
        'whats_happening': whats_happening,
        'how_it_shows_up': how_it_shows_up,
        'what_it_feels_like': what_it_feels_like,
        'the_move': the_move,
        'where_context': where_context,
        'technical': technical,
        'tension_type': day_energy['tags'][0] if day_energy['tags'] else 'mixed',
        'day_class': 'stellium' if top_concentration and top_concentration['count'] >= 4 else 'transit_dominant',
        'success': True,
    }


def _build_headline(conc, aspects, energy, moon) -> str:
    """Build the main headline from dominant signal."""
    tags = energy.get('tags', [])
    
    if conc and conc['count'] >= 4:
        sign = conc['sign']
        behavior = conc.get('behavior', {})
        keyword = behavior.get('keyword', 'intensity')
        
        headlines = {
            'Aries': "Everything is pushing you to act — and not gently.",
            'Taurus': "The pull toward stability is strong. Change feels threatening today.",
            'Gemini': "Your mind is everywhere at once. Focus is the real challenge.",
            'Cancer': "Emotional currents are running deep. Protection mode is on.",
            'Leo': "The need to be seen, heard, or recognized is louder than usual.",
            'Virgo': "Details are demanding attention. Nothing feels good enough.",
            'Libra': "Relationships are the weather today. Balance feels impossible.",
            'Scorpio': "Something hidden wants to surface. Intensity is unavoidable.",
            'Sagittarius': "Restlessness is the dominant note. Containment feels wrong.",
            'Capricorn': "Pressure to perform or deliver is real. The stakes feel higher.",
            'Aquarius': "The urge to break free or push back is driving everything.",
            'Pisces': "Boundaries are dissolving. What's yours and what's theirs is blurred.",
        }
        return headlines.get(sign, f"A concentration of energy is building around {keyword}.")
    
    if aspects and aspects[0]['score'] > 0.5:
        asp = aspects[0]
        if asp['nature'] == 'tension':
            return f"There's friction between what you want and what the day demands."
        elif asp['nature'] == 'polarity':
            return f"You're being pulled in two directions — and both feel real."
        elif asp['nature'] == 'fusion':
            return f"Something is amplifying inside you. It's hard to ignore."
        else:
            return f"An opening is forming — but you have to notice it to use it."
    
    if 'emotionally-charged' in tags:
        return "The emotional volume is turned up today. Not everything needs a response."
    
    if 'action-heavy' in tags:
        return "The energy is pushing you forward. The question is: toward what?"
    
    return "The day has a specific shape to it. Pay attention to what keeps pulling you."


def _build_whats_happening(conc, aspects, energy) -> List[str]:
    """Build 2-3 real-world dynamics."""
    items = []
    
    if conc and conc['count'] >= 3:
        sign = conc['sign']
        behavior = conc.get('behavior', {})
        behaviors = behavior.get('behavior', [])
        if behaviors:
            items.append(behaviors[0])
        if conc['count'] >= 4:
            items.append(f"With {conc['count']} planets concentrated in one zone, the pressure is focused, not spread out — which makes it harder to avoid")
    
    if aspects:
        top = aspects[0]
        if top['nature'] in ('tension', 'polarity'):
            items.append(f"Your {top['natal_planet'].lower()} instinct — the part of you it represents — is being challenged by current conditions")
        elif top['nature'] == 'fusion':
            items.append(f"Current energy is merging with your natal {top['natal_planet'].lower()}, intensifying how it normally operates")
        else:
            items.append(f"There's support flowing toward your {top['natal_planet'].lower()} — something is being unlocked or made easier")
    
    if not items:
        items.append("The transit weather today is moderate — no single signal dominates")
        items.append("This is a day where subtler patterns have room to surface")
    
    return items[:3]


def _build_how_shows_up(conc, aspects, top_house, moon) -> List[str]:
    """Build observable behavior predictions."""
    items = []
    
    if conc and conc['count'] >= 3:
        behaviors = conc.get('behavior', {}).get('behavior', [])
        items.extend(behaviors[1:3])
    
    if top_house:
        items.append(f"Watch for this showing up around {top_house['context']}")
    
    moon_sign = moon.get('sign', '')
    if moon_sign:
        moon_behavior = SIGN_BEHAVIOR.get(moon_sign, {})
        moon_behaviors = moon_behavior.get('behavior', [])
        if moon_behaviors:
            items.append(moon_behaviors[0])
    
    if not items:
        items.append("The effects today are subtle — they'll show up in how you respond to small moments, not big events")
    
    return items[:3]


def _build_feelings(conc, energy, moon) -> List[str]:
    """Build physical/emotional signals."""
    items = []
    
    if conc and conc['count'] >= 3:
        feelings = conc.get('behavior', {}).get('feeling', [])
        items.extend(feelings[:2])
    
    moon_sign = moon.get('sign', '')
    if moon_sign:
        moon_feelings = SIGN_BEHAVIOR.get(moon_sign, {}).get('feeling', [])
        if moon_feelings and moon_feelings[0] not in items:
            items.append(moon_feelings[0])
    
    if not items:
        tags = energy.get('tags', [])
        if 'tension-heavy' in tags:
            items.append("a low-grade friction that makes relaxation harder")
        elif 'emotionally-charged' in tags:
            items.append("emotional sensitivity that catches you off guard")
        else:
            items.append("a background hum of energy — not dramatic but present")
    
    return items[:3]


def _build_the_move(conc, aspects, energy) -> str:
    """Build one behavioral shift suggestion."""
    tags = energy.get('tags', [])
    
    if conc and conc['count'] >= 4:
        sign = conc['sign']
        moves = {
            'Aries': "Channel the activation energy into one clear action — don't spray it everywhere.",
            'Taurus': "Let yourself slow down without guilt. Stability is the move, not stagnation.",
            'Gemini': "Write down the three things competing for attention. Pick one.",
            'Cancer': "Check in with yourself before you check in with everyone else.",
            'Leo': "Create something — even small. The energy needs an outlet.",
            'Virgo': "Accept 'good enough' for today. Perfection is consuming energy you need elsewhere.",
            'Libra': "Make one decision you've been deferring. Even a small one breaks the pattern.",
            'Scorpio': "Name what's actually bothering you — to yourself, not anyone else.",
            'Sagittarius': "Find one thing to commit to today — even temporarily.",
            'Capricorn': "Separate what you must do from what you think you should do.",
            'Aquarius': "Before you rebel, ask: is this about freedom or avoidance?",
            'Pisces': "Ground yourself in one concrete thing before noon.",
        }
        return moves.get(sign, "Focus your energy on the one thing that matters most right now.")
    
    if 'tension-heavy' in tags:
        return "Don't try to resolve the tension — just notice where it lands in your body."
    if 'action-heavy' in tags:
        return "Move your body. The energy is physical and needs a physical outlet."
    if 'emotionally-charged' in tags:
        return "Give yourself permission to feel without having to explain it to anyone."
    
    return "Pay attention to the one moment today that feels slightly different from the rest."


def _build_proof_layer(
    aspects: List[Dict],
    concentrations: List[Dict],
    house_activations: List[Dict],
    day_energy: Dict,
    transit_positions: Dict[str, Dict],
) -> Dict[str, Any]:
    """Build the structured proof / technical layer."""
    
    # Dominant pattern title
    top_conc = concentrations[0] if concentrations else None
    if top_conc and top_conc['count'] >= 3:
        pattern_title = f"{top_conc['count']}-planet {top_conc['sign']} concentration"
        pattern_detail = f"{', '.join(top_conc['planets'])} all in {top_conc['sign']} — focused {SIGN_BEHAVIOR.get(top_conc['sign'], {}).get('keyword', 'energy')}"
    elif aspects:
        asp = aspects[0]
        pattern_title = f"{asp['transit_planet']} {asp['aspect']} natal {asp['natal_planet']}"
        pattern_detail = f"Transit {asp['transit_planet']} in {asp['transit_sign']} {asp['aspect']} your natal {asp['natal_planet']} ({asp['orb']}° orb)"
    else:
        pattern_title = "Moderate transit weather"
        pattern_detail = "No dominant single signal — subtler patterns at play"
    
    # Active transits list
    active_transits = []
    for asp in aspects[:5]:
        nature_label = {'tension': '⚡', 'polarity': '↔', 'fusion': '⊕', 'flow': '✦', 'opportunity': '○'}
        icon = nature_label.get(asp['nature'], '•')
        active_transits.append(
            f"{icon} {asp['transit_planet']} {asp['aspect']} your {asp['natal_planet']} ({asp['orb']}° orb) — {asp['nature']}"
        )
    
    # Sign concentration
    sign_emphasis = []
    for conc in concentrations:
        if conc['count'] >= 2:
            keyword = SIGN_BEHAVIOR.get(conc['sign'], {}).get('keyword', '')
            sign_emphasis.append(
                f"{conc['sign']}: {conc['count']} planets ({', '.join(conc['planets'])}) — {keyword}"
            )
    
    # House emphasis
    house_emphasis = []
    for ha in house_activations[:3]:
        if ha['score'] >= 10:
            house_emphasis.append(
                f"House {ha['house']}: {', '.join(ha['planets'])} — {ha['context']}"
            )
    
    # Background slow planets
    slow_planets = []
    for name in ['Saturn', 'Uranus', 'Neptune', 'Pluto']:
        pos = transit_positions.get(name, {})
        if pos:
            retro = " (retrograde)" if pos.get('retrograde') else ""
            slow_planets.append(f"{name} in {pos['sign']} at {pos['degree']:.0f}°{retro}")
    
    return {
        'dominant_pattern': pattern_title,
        'pattern_detail': pattern_detail,
        'active_transits': active_transits,
        'sign_emphasis': sign_emphasis,
        'house_emphasis': house_emphasis,
        'slow_planet_backdrop': slow_planets,
        'day_tags': day_energy.get('tags', []),
        'tension_score': day_energy.get('tension_score', 0),
        'flow_score': day_energy.get('flow_score', 0),
    }


def generate_today_intelligence(
    user_id: str,
    natal_planets: Dict[str, Dict],
    natal_house_cusps: Optional[List[float]] = None,
    dt: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Main entry point: Generate a full Astrology Today intelligence report.
    
    Args:
        user_id: User ID for logging
        natal_planets: User's natal planet positions (from charts.astrology.planets)
        natal_house_cusps: User's natal house cusps (from charts.astrology.houses.cusps)
        dt: Optional datetime override (defaults to now)
    
    Returns:
        Full Today insight with narrative + proof layer
    """
    try:
        # 1. Get current transit positions
        transit_positions = get_current_transits(dt)
        
        # 2. Compute transit-to-natal aspects
        aspects = compute_transit_natal_aspects(transit_positions, natal_planets)
        
        # 3. Detect sign concentrations
        concentrations = detect_sign_concentration(transit_positions)
        
        # 4. Compute house activations
        house_activations = compute_house_activations(transit_positions, natal_house_cusps) if natal_house_cusps else []
        
        # 5. Classify day energy
        day_energy = classify_day_energy(aspects, concentrations, transit_positions)
        
        # 6. Build narrative from ranked signals
        result = build_today_narrative(aspects, concentrations, house_activations, day_energy, transit_positions)
        
        logger.info(f"[TodayEngine] User {user_id[:8]}: tags={day_energy['tags']}, "
                     f"aspects={len(aspects)}, top_conc={concentrations[0]['sign'] if concentrations else 'none'}({concentrations[0]['count'] if concentrations else 0}), "
                     f"houses={len(house_activations)}")
        
        return result
        
    except Exception as e:
        logger.error(f"[TodayEngine] Error for {user_id}: {e}", exc_info=True)
        return {
            'headline': "The sky is active today. Pay attention to what pulls you.",
            'whats_happening': ["Transit conditions are complex — multiple signals are competing"],
            'how_it_shows_up': ["Watch for moments that feel slightly more charged than usual"],
            'what_it_feels_like': ["A background intensity that's hard to name"],
            'the_move': "Focus on the one thing that matters most right now.",
            'where_context': None,
            'technical': {'dominant_pattern': 'Complex transit weather', 'error': str(e)},
            'tension_type': 'mixed',
            'day_class': 'fallback',
            'success': True,
        }
