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
    # ophiuchus-first-class-content-v1
    'Ophiuchus': {
        'energy': 'integrating',
        'tone': 'grounded, restorative, threshold-crossing',
        'behavior': ['Patterns recognised earlier in the loop than usual',
                     'Less interest in re-explaining; more in finishing',
                     'Body and decision arriving on the same beat'],
        'feeling': ['the depth you carry asking to be moved through',
                    'tension between sitting with it and acting on it'],
        'keyword': 'integration'
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
    """Get all current planet positions (TRUE SIDEREAL).

    Defensive fix (May 2026): historically this used `swe.FLG_SWIEPH`
    only, which produced TROPICAL longitudes — a leak that contradicted
    the canonical Mirror sidereal config (SVP=31.2836°, J2000, no
    yearly increment) used by every other engine (natal chart, At-a-
    Glance, Deep Dive, transit-debug, V5 Today). The v4 endpoint is
    deprecated, but this function is still imported by older code
    paths, so we explicitly switch to the canonical SIDM_USER mode
    here to prevent future tropical leakage.
    """
    if not dt:
        dt = datetime.now(timezone.utc)
    jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60.0)

    # Canonical Mirror sidereal config — must match
    # `calculations.sidereal_config.SVP_DEGREES` and `J2000_EPOCH`.
    swe.set_sid_mode(swe.SIDM_USER, 2451545.0, 31.2836)

    positions = {}
    for name, pid in PLANETS.items():
        result = swe.calc_ut(jd, pid, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
        lon = result[0][0] % 360.0
        speed = result[0][3]
        # Sign attribution honours global mode (uniform_30 or true_sidereal_midpoint).
        # `lon` here is SIDEREAL (FLG_SIDEREAL set above); longitude_to_sign_degree
        # converts back to tropical internally when mode = true_sidereal_midpoint.
        # Build marker: true-sidereal-midpoint-production-migration-v1
        from calculations.astrology import longitude_to_sign_degree as _lts
        _attr = _lts(lon)
        positions[name] = {
            'longitude': lon,
            'sign': _attr['sign'],
            'degree': _attr['degree'],
            'speed': speed,
            'retrograde': speed < 0,
        }
    return positions


def compute_transit_natal_aspects(
    transit_positions: Dict[str, Dict],
    natal_planets: Dict[str, Dict],
    *,
    today_utc: Optional[datetime] = None,
    apply_future_demote: bool = True,
) -> List[Dict]:
    """Compute transit-to-natal aspects, scored by strength.

    ranking-future-demote-v1 (2026-06-06)
    -------------------------------------
    Each aspect is annotated with a signed ``days_to_exact`` (negative =
    past, positive = future). After the default score-sort, aspects whose
    *exact* date is more than 7 days in the future are **demoted** below
    every aspect whose exact date is within ±2 days, but **kept in the
    list** so they remain visible in the signal map / accordion.

    Pure ranking tweak — no natal math, no ayanamsa, no house change.
    See `/app/memory/mel_transit_forensic_2026-06-06.md`.
    """
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
                        # ranking-future-demote-v1: filled in below
                        'days_to_exact': None,
                        'future_demoted': False,
                    })

    # ── days_to_exact computation (ranking-future-demote-v1) ────────────
    if aspects:
        now = today_utc or datetime.now(timezone.utc)
        try:
            from services.lifecycle_engine import _scan_transit_passes
            jd_now = swe.julday(now.year, now.month, now.day,
                                 now.hour + now.minute / 60.0)
            for a in aspects:
                nat = natal_planets.get(a['natal_planet']) or {}
                nat_trop = nat.get('tropical_longitude')
                if nat_trop is None:
                    # Fall back: sidereal + SVP
                    nat_trop = (nat.get('longitude', 0.0) + 31.2836) % 360.0
                # Resolve aspect angle from name (faster than dict lookup
                # below for a small fixed set)
                aspect_angle = next(
                    (k for k, v in ASPECT_TYPES.items() if v['name'] == a['aspect']),
                    None,
                )
                if aspect_angle is None:
                    continue
                passes_pos = _scan_transit_passes(
                    body=a['transit_planet'], target_long=nat_trop,
                    offset_deg=aspect_angle,
                    jd_start=jd_now - 90.0, jd_end=jd_now + 90.0,
                    step_days=2.0,
                )
                passes_neg: List[float] = []
                if aspect_angle not in (0.0, 180.0):
                    passes_neg = _scan_transit_passes(
                        body=a['transit_planet'], target_long=nat_trop,
                        offset_deg=-aspect_angle,
                        jd_start=jd_now - 90.0, jd_end=jd_now + 90.0,
                        step_days=2.0,
                    )
                all_p = sorted(passes_pos + passes_neg)
                if all_p:
                    nearest = min(all_p, key=lambda j: abs(j - jd_now))
                    a['days_to_exact'] = round(nearest - jd_now, 1)
        except Exception as e:
            logger.warning(
                f"[TodayRank] days_to_exact computation skipped: {e}"
            )

    # Sort by score descending (default behaviour preserved)
    aspects.sort(key=lambda x: -x['score'])

    # ── future-exact demotion rule (ranking-future-demote-v1) ──────────
    # If any aspect exact within ±2 days exists, demote every aspect
    # whose exact is >7 days in the future BELOW the "near-exact" group,
    # while preserving relative order inside each bucket.
    if apply_future_demote and aspects:
        near_exact = [
            a for a in aspects
            if a.get('days_to_exact') is not None
            and abs(a['days_to_exact']) <= 2.0
        ]
        if near_exact:
            FUTURE_THRESHOLD = 7.0
            high_priority: List[Dict] = []
            demoted:       List[Dict] = []
            others:        List[Dict] = []
            for a in aspects:
                dte = a.get('days_to_exact')
                if dte is not None and dte > FUTURE_THRESHOLD:
                    a['future_demoted'] = True
                    demoted.append(a)
                else:
                    high_priority.append(a)
            # Preserve score-order within each bucket
            aspects = high_priority + demoted
            logger.info(
                f"[TodayRank] future-demote-v1: demoted={len(demoted)} "
                f"near_exact={len(near_exact)} total={len(aspects)}"
            )

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
    # ophiuchus-first-class-content-v1: element sets via central metadata.
    # Ophiuchus carries element="ether" (5th transcendent element).
    fire_signs = {'Aries', 'Leo', 'Sagittarius'}
    water_signs = {'Cancer', 'Scorpio', 'Pisces'}
    earth_signs = {'Taurus', 'Virgo', 'Capricorn'}
    air_signs = {'Gemini', 'Libra', 'Aquarius'}
    ether_signs = {'Ophiuchus'}

    element_count = {'fire': 0, 'water': 0, 'earth': 0, 'air': 0, 'ether': 0}
    for _, data in transit_positions.items():
        s = data['sign']
        if s in fire_signs: element_count['fire'] += 1
        elif s in water_signs: element_count['water'] += 1
        elif s in earth_signs: element_count['earth'] += 1
        elif s in air_signs: element_count['air'] += 1
        elif s in ether_signs: element_count['ether'] += 1  # Ophiuchus
    
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
    """Build the full Today narrative from ranked signals using
    FOREGROUND / DESTABILIZER / AMPLIFIER model."""
    
    top_concentration = concentrations[0] if concentrations else None
    top_house = house_activations[0] if house_activations else None
    second_house = house_activations[1] if len(house_activations) > 1 else None
    moon = transit_positions.get('Moon', {})
    
    # =========================================================
    # EXTRACT SIGNAL LAYERS
    # =========================================================
    layers = _extract_signal_layers(aspects, concentrations, house_activations, day_energy, transit_positions)
    
    # =========================================================
    # BUILD NARRATIVE FROM LAYERS
    # =========================================================
    headline = _build_headline(layers, top_house, day_energy)
    subhead = _build_subhead(layers, top_house, second_house)
    whats_happening = _build_whats_happening(layers, day_energy)
    how_it_shows_up = _build_how_shows_up(layers, top_house, second_house, moon)
    what_it_feels_like = _build_feelings(layers, day_energy, moon)
    the_move = _build_the_move(layers, day_energy)
    
    where_context = None
    if top_house:
        where_context = f"This lands especially in the area of {top_house['context']}."
    
    # =========================================================
    # TECHNICAL / PROOF LAYER (untouched)
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


# =====================================================================
# SIGNAL LAYER EXTRACTION — Foreground / Destabilizer / Amplifier
# =====================================================================

# Planet archetypes for narrative synthesis
PLANET_ARCHETYPE = {
    'Sun': {'domain': 'identity', 'verb': 'demands visibility', 'distortion': 'ego inflation'},
    'Moon': {'domain': 'emotional needs', 'verb': 'shifts the emotional weather', 'distortion': 'reactivity'},
    'Mercury': {'domain': 'thinking and communication', 'verb': 'speeds up the mind', 'distortion': 'overthinking'},
    'Venus': {'domain': 'relationships and values', 'verb': 'draws toward comfort', 'distortion': 'avoidance through pleasure'},
    'Mars': {'domain': 'action and drive', 'verb': 'pressures you to act', 'distortion': 'impulsive confrontation'},
    'Jupiter': {'domain': 'expansion and belief', 'verb': 'amplifies everything', 'distortion': 'overreach and excess'},
    'Saturn': {'domain': 'structure and limitation', 'verb': 'tightens the frame', 'distortion': 'rigidity and pressure'},
    'Neptune': {'domain': 'intuition and illusion', 'verb': 'blurs the lines', 'distortion': 'confusion and projection'},
    'Uranus': {'domain': 'disruption and freedom', 'verb': 'destabilizes the status quo', 'distortion': 'rebellion without direction'},
    'Pluto': {'domain': 'power and transformation', 'verb': 'exposes what was hidden', 'distortion': 'control and obsession'},
}

# Aspect natures for role classification
DESTABILIZER_PLANETS = {'Neptune', 'Pluto', 'Uranus'}
AMPLIFIER_NATURES = {'tension', 'polarity'}  # squares and oppositions amplify
AMPLIFIER_PLANETS = {'Jupiter'}  # Jupiter always amplifies


def _extract_signal_layers(aspects, concentrations, house_activations, day_energy, transit_positions):
    """Extract Foreground / Destabilizer / Amplifier from ranked signals."""
    
    foreground = None
    destabilizer = None
    amplifier = None
    
    # --- FOREGROUND: The dominant weather ---
    top_conc = concentrations[0] if concentrations else None
    if top_conc and top_conc['count'] >= 3:
        behavior = top_conc.get('behavior', {})
        foreground = {
            'type': 'concentration',
            'sign': top_conc['sign'],
            'count': top_conc['count'],
            'planets': top_conc['planets'],
            'energy': behavior.get('energy', 'intensity'),
            'keyword': behavior.get('keyword', 'pressure'),
            'tone': behavior.get('tone', ''),
        }
    elif aspects:
        # Strongest aspect IS the foreground
        top = aspects[0]
        archetype = PLANET_ARCHETYPE.get(top['transit_planet'], {})
        foreground = {
            'type': 'aspect',
            'transit_planet': top['transit_planet'],
            'natal_planet': top['natal_planet'],
            'aspect_name': top['aspect'],
            'nature': top['nature'],
            'domain': archetype.get('domain', 'energy'),
            'verb': archetype.get('verb', 'is active'),
        }
    
    # --- DESTABILIZER: What complicates or distorts ---
    for asp in aspects[:8]:
        tp = asp['transit_planet']
        # Neptune/Pluto/Uranus aspects destabilize
        if tp in DESTABILIZER_PLANETS and asp['score'] > 0.15:
            archetype = PLANET_ARCHETYPE.get(tp, {})
            natal_arch = PLANET_ARCHETYPE.get(asp['natal_planet'], {})
            destabilizer = {
                'planet': tp,
                'natal_planet': asp['natal_planet'],
                'aspect': asp['aspect'],
                'nature': asp['nature'],
                'distortion': archetype.get('distortion', 'distortion'),
                'verb': archetype.get('verb', 'complicates'),
                'natal_domain': natal_arch.get('domain', 'instinct'),
                'orb': asp['orb'],
            }
            break
    
    # --- AMPLIFIER: What makes it bigger ---
    for asp in aspects[:8]:
        tp = asp['transit_planet']
        # Jupiter aspects amplify; also squares/oppositions from heavy planets
        if tp in AMPLIFIER_PLANETS and asp['score'] > 0.1:
            archetype = PLANET_ARCHETYPE.get(tp, {})
            natal_arch = PLANET_ARCHETYPE.get(asp['natal_planet'], {})
            amplifier = {
                'planet': tp,
                'natal_planet': asp['natal_planet'],
                'aspect': asp['aspect'],
                'distortion': archetype.get('distortion', 'excess'),
                'verb': archetype.get('verb', 'amplifies'),
                'natal_domain': natal_arch.get('domain', 'energy'),
            }
            break
        # Saturn squares/oppositions also amplify pressure
        if tp == 'Saturn' and asp['nature'] in ('tension', 'polarity') and asp['score'] > 0.15:
            amplifier = {
                'planet': 'Saturn',
                'natal_planet': asp['natal_planet'],
                'aspect': asp['aspect'],
                'distortion': 'weight and pressure',
                'verb': 'tightens the frame around',
                'natal_domain': PLANET_ARCHETYPE.get(asp['natal_planet'], {}).get('domain', 'energy'),
            }
            break
    
    # --- INTENSITY LEVEL ---
    total_aspect_score = sum(a['score'] for a in aspects[:10])
    stellium_count = top_conc['count'] if top_conc else 0
    
    if stellium_count >= 5 or total_aspect_score > 4.0:
        intensity = 'extreme'
    elif stellium_count >= 3 or total_aspect_score > 2.5:
        intensity = 'high'
    elif total_aspect_score > 1.0:
        intensity = 'moderate'
    else:
        intensity = 'low'
    
    return {
        'foreground': foreground,
        'destabilizer': destabilizer,
        'amplifier': amplifier,
        'intensity': intensity,
        'house_primary': house_activations[0] if house_activations else None,
        'house_secondary': house_activations[1] if len(house_activations) > 1 else None,
    }


# =====================================================================
# NARRATIVE BUILDERS — Using Foreground / Destabilizer / Amplifier
# =====================================================================

def _build_headline(layers, top_house, energy) -> str:
    """Build headline that captures the core tension, not just the mood."""
    fg = layers['foreground']
    dest = layers['destabilizer']
    amp = layers['amplifier']
    intensity = layers['intensity']
    
    if not fg:
        return "The day has a specific shape to it. Pay attention to what keeps pulling at you."
    
    # Stellium / concentration foreground
    if fg.get('type') == 'concentration':
        sign = fg['sign']
        count = fg['count']
        
        # WITH destabilizer — headline captures the tension
        if dest:
            tension_headlines = {
                'Aries': {
                    'Neptune': "The pressure to move is real — but not everything pushing you is clarity.",
                    'Pluto': "Something is trying to force a breakthrough, and it won't wait for permission.",
                    'Uranus': "The urge to act is electric — but it's outrunning your ability to aim.",
                    '_default': "The push to act is strong, but something underneath is making it harder to land.",
                },
                'Taurus': {
                    'Neptune': "You're holding on tight — but what you're holding may not be what you think it is.",
                    'Uranus': "Stability feels urgent, but something keeps shaking the ground.",
                    '_default': "The need for solid ground is real, but the ground keeps shifting.",
                },
                'Gemini': {
                    'Neptune': "Your mind is full of signal — but some of it is noise dressed as insight.",
                    '_default': "Information is coming fast, and not all of it deserves your attention.",
                },
                'Cancer': {
                    'Neptune': "Emotional pull is strong today — but it's hard to tell what's yours and what's absorbed.",
                    'Pluto': "Something in the emotional basement is trying to surface, and it's not asking nicely.",
                    '_default': "Protection mode is running — but some of what you're guarding may need to be released.",
                },
                'Leo': {
                    'Neptune': "The desire to be seen is loud — but what you're showing may not be what's actually there.",
                    '_default': "Creative pressure is building and it wants an outlet, but the stakes feel inflated.",
                },
                'Virgo': {
                    'Neptune': "The details feel critical — but perfectionism is disguising itself as discernment.",
                    '_default': "Something demands precision, but the harder you grip, the more it slips.",
                },
                'Libra': {
                    'Pluto': "A relationship dynamic is shifting, and surface diplomacy won't hold.",
                    '_default': "Balance feels impossible today — every adjustment creates a new imbalance.",
                },
                'Scorpio': {
                    'Neptune': "Something hidden wants out — but the truth is wrapped in multiple layers of feeling.",
                    '_default': "Intensity is the baseline today. What you uncover may require time to process.",
                },
                'Sagittarius': {
                    'Neptune': "The pull toward meaning is strong — but belief can outrun evidence right now.",
                    '_default': "Restlessness has a point today — but it needs direction, not just escape.",
                },
                'Capricorn': {
                    'Neptune': "The pressure to perform is real, but the goal line may not be where you think it is.",
                    '_default': "Structure is under pressure. What felt solid may need rebuilding.",
                },
                'Aquarius': {
                    'Neptune': "The urge to break free is strong — but some of that rebellion is running from something.",
                    '_default': "Convention feels intolerable, but the alternative isn't clear yet.",
                },
                'Pisces': {
                    'Neptune': "Everything is dissolving at the edges. Clarity isn't available — but trust might be.",
                    '_default': "Boundaries are thin today. What drifts in may not all belong to you.",
                },
                'Ophiuchus': {
                    'Pluto': "The pattern wants to be moved through, not just understood. The depth alone isn't enough anymore.",
                    'Neptune': "What you've been processing keeps asking to be enacted. Today, name the smallest crossing.",
                    '_default': "A threshold is right in front of you. Today's task is to step across it, not to study it more.",
                },
            }
            
            sign_headlines = tension_headlines.get(sign, {})
            headline = sign_headlines.get(dest['planet'], sign_headlines.get('_default', ''))
            if headline:
                return headline
        
        # WITH amplifier but no destabilizer
        if amp and not dest:
            if amp['planet'] == 'Jupiter':
                return f"The {fg['keyword']} energy is enormous today — and Jupiter is making everything feel bigger than it actually is."
            elif amp['planet'] == 'Saturn':
                return f"There's {fg['keyword']} pressure, and it's being squeezed into a tighter container than it can comfortably fit."
        
        # Concentration only (no destabilizer/amplifier) — pure weather
        if count >= 5:
            pure_headlines = {
                'Aries': "The sky is loaded with fire. Everything is pushing toward action — the question is whether you can aim it.",
                'Taurus': "A wall of grounding energy is active. Nothing wants to move fast, and that's the point.",
                'Gemini': "The mental channel is wide open. Information, conversations, and choices are competing for space.",
                'Cancer': "Emotional gravity is pulling hard today. Home, roots, and protection are the center of everything.",
                'Leo': "Self-expression can't be contained today. The creative pressure wants out.",
                'Virgo': "Everything is under a microscope. The drive to fix, refine, and organize is relentless.",
                'Libra': "Relationships are the entire weather today. Connection, fairness, and compromise dominate.",
                'Scorpio': "The undercurrent is powerful. Whatever was buried is closer to the surface than you think.",
                'Sagittarius': "The need for space, meaning, and movement is the dominant force today.",
                'Capricorn': "Responsibility is the main event. The pressure to deliver is real and structural.",
                'Aquarius': "Something wants to break pattern. The status quo feels suffocating.",
                'Pisces': "The edges are soft today. Intuition is louder than logic, and that's not necessarily wrong.",
                'Ophiuchus': "Something you've been carrying is asking to be moved through today, not just felt.",
            }
            return pure_headlines.get(sign, f"A massive concentration of {fg['keyword']} energy is active today.")
        else:
            return f"The dominant note today is {fg['keyword']} — concentrated, focused, and hard to ignore."
    
    # Aspect-driven foreground (no stellium)
    if fg.get('type') == 'aspect':
        if dest:
            return f"Your {fg['domain']} is being activated — but {dest['verb']}, making it harder to act cleanly."
        return f"Something is touching your {fg['domain']} today. It's specific, not background noise."
    
    return "The sky is active today. Pay attention to what pulls at you — it's telling you something."


def _build_subhead(layers, top_house, second_house) -> str:
    """Build a subhead that anchors WHERE this lands in life."""
    primary = top_house
    secondary = second_house
    
    if primary and secondary:
        return f"This is showing up around {primary['context']} — with secondary pressure around {secondary['context']}."
    elif primary:
        return f"Watch for this in the area of {primary['context']}."
    return ""


def _build_whats_happening(layers, energy) -> List[str]:
    """Build what's happening using foreground + destabilizer + amplifier."""
    items = []
    fg = layers['foreground']
    dest = layers['destabilizer']
    amp = layers['amplifier']
    intensity = layers['intensity']
    
    # FOREGROUND — the dominant dynamic
    if fg and fg.get('type') == 'concentration':
        sign = fg['sign']
        count = fg['count']
        behavior = SIGN_BEHAVIOR.get(sign, {})
        behaviors = behavior.get('behavior', [])
        
        if intensity == 'extreme':
            items.append(f"{count} planets are concentrated in a single zone — this isn't background noise, it's the whole weather system")
        elif behaviors:
            items.append(behaviors[0])
    elif fg and fg.get('type') == 'aspect':
        items.append(f"Current transits are directly touching your {fg['domain']} — this makes today personal, not just atmospheric")
    
    # DESTABILIZER — what complicates it
    if dest:
        dp = dest['planet']
        if dp == 'Neptune':
            items.append(f"Neptune is distorting your {dest['natal_domain']} right now — instincts feel present but unreliable, like seeing through fog")
        elif dp == 'Pluto':
            items.append(f"Pluto is pressuring your {dest['natal_domain']} — something wants to surface or transform, and it's not asking for permission")
        elif dp == 'Uranus':
            items.append(f"Uranus is disrupting your {dest['natal_domain']} — expect sudden shifts in how you think about what's stable")
        else:
            items.append(f"Your {dest['natal_domain']} is being complicated by current conditions — what usually feels clear may feel contested")
    
    # AMPLIFIER — what makes it bigger
    if amp:
        ap = amp['planet']
        if ap == 'Jupiter':
            items.append(f"Jupiter is inflating your {amp['natal_domain']} — reactions, beliefs, and emotional responses may all feel bigger than warranted")
        elif ap == 'Saturn':
            items.append(f"Saturn is adding weight to your {amp['natal_domain']} — what might normally pass quickly feels heavier and more consequential")
    
    if not items:
        items.append("The transit weather is moderate today — no single signal is dominating, which gives you more room to choose")
    
    return items[:3]


def _build_how_shows_up(layers, top_house, second_house, moon) -> List[str]:
    """Build lived scene translations from the signal layers."""
    items = []
    fg = layers['foreground']
    dest = layers['destabilizer']
    intensity = layers['intensity']
    
    # House-based lived scenes
    if top_house:
        house = top_house['house']
        scenes = {
            1: "You may catch yourself reacting before you've decided what you actually think",
            2: "Financial decisions or questions of self-worth may feel more charged than usual",
            3: "Conversations, messages, or a decision you've been deferring may demand attention",
            4: "Something at home — family, living situation, emotional roots — can't stay backgrounded anymore",
            5: "A creative or romantic impulse may push through before it's fully formed",
            6: "Work routines, health habits, or daily obligations may feel more pressured or disrupted",
            7: "A relationship dynamic — business or personal — may need to be addressed directly",
            8: "Shared finances, intimacy, or a power dynamic may surface with unexpected force",
            9: "A belief, plan, or philosophical stance you held may get challenged or expanded",
            10: "Your public role, reputation, or a career matter may demand more from you today",
            11: "A friendship, community dynamic, or future goal may shift or demand attention",
            12: "Something you've been avoiding internally may surface — through dreams, fatigue, or a feeling you can't name",
        }
        scene = scenes.get(house, f"Watch for this showing up around {top_house['context']}")
        items.append(scene)
    
    # Destabilizer scene
    if dest:
        dp = dest['planet']
        if dp == 'Neptune':
            items.append("You may misread a situation or project meaning onto something that isn't there yet")
        elif dp == 'Pluto':
            items.append("A power dynamic or emotional undercurrent may surface in a way that surprises you")
        elif dp == 'Uranus':
            items.append("Something you thought was settled may suddenly feel uncertain or rearranged")
    
    # Moon emotional scene
    moon_sign = moon.get('sign', '')
    if moon_sign:
        moon_scenes = {
            'Aries': "Emotional reactions are fast and sharp — what you feel, you feel immediately",
            'Taurus': "Emotionally you want comfort and predictability — disruption feels personal",
            'Gemini': "Feelings are showing up as thoughts — you're processing emotion through talking or writing",
            'Cancer': "You're more emotionally porous than usual — other people's moods can land on you",
            'Leo': "There's an emotional need to be acknowledged or appreciated — invisibility stings",
            'Virgo': "Worry or self-criticism may be running higher — the inner editor is loud",
            'Libra': "You're absorbing relational tension — harmony-seeking can look like people-pleasing",
            'Scorpio': "Emotional intensity is high and it's seeking depth, not surface resolution",
            'Sagittarius': "Emotionally you're restless — staying put feels like giving up",
            'Capricorn': "Feelings are getting filtered through duty — you may not let yourself feel what's actually there",
            'Aquarius': "Emotional detachment is the default — which works until someone needs you present",
            'Pisces': "Emotional boundaries are thin — what drifts in may not all be yours to carry",
        }
        moon_scene = moon_scenes.get(moon_sign)
        if moon_scene and moon_scene not in items:
            items.append(moon_scene)
    
    if not items:
        items.append("The effects are subtle — they'll show up in how you respond to small moments, not in big events")
    
    return items[:3]


def _build_feelings(layers, energy, moon) -> List[str]:
    """Build feelings proportionate to actual intensity."""
    items = []
    fg = layers['foreground']
    dest = layers['destabilizer']
    amp = layers['amplifier']
    intensity = layers['intensity']
    
    # Intensity-scaled feelings
    if fg and fg.get('type') == 'concentration':
        sign = fg['sign']
        feelings = SIGN_BEHAVIOR.get(sign, {}).get('feeling', [])
        
        if intensity == 'extreme':
            items.append(f"an intensity that's hard to contain — like the volume is all the way up and there's no dial")
            if feelings:
                items.append(feelings[0])
        elif intensity == 'high':
            if feelings:
                items.extend(feelings[:2])
        else:
            if feelings:
                items.append(feelings[0])
    
    # Destabilizer feeling overlay
    if dest:
        dp = dest['planet']
        if dp == 'Neptune':
            items.append("a disorienting quality underneath — like you can feel something but can't quite name it or trust it")
        elif dp == 'Pluto':
            items.append("a sense of something churning below the surface — pressure that isn't about today alone")
        elif dp == 'Uranus':
            items.append("a restless, electric quality — like something could shift at any moment")
    
    # Amplifier feeling overlay
    if amp and amp['planet'] == 'Jupiter':
        items.append("everything feels slightly larger than it should — reactions, hopes, and fears are all running hot")
    
    if not items:
        items.append("a background hum of energy — not dramatic, but present enough to shape your responses")
    
    return items[:3]


def _build_the_move(layers, energy) -> str:
    """Build one behavioral shift that addresses the actual tension."""
    fg = layers['foreground']
    dest = layers['destabilizer']
    amp = layers['amplifier']
    intensity = layers['intensity']
    
    # Destabilizer + Foreground = specific move
    if dest and fg:
        dp = dest['planet']
        if dp == 'Neptune':
            if fg.get('sign') in ('Aries', 'Leo', 'Sagittarius'):
                return "Before you act on the urgency, pause and ask: am I seeing this clearly, or am I seeing what I want to see?"
            return "Don't trust the first interpretation. Give yourself until tomorrow before you decide what something means."
        elif dp == 'Pluto':
            return "Name what's actually bothering you — not the surface version, the real one. You don't have to share it. Just know it."
        elif dp == 'Uranus':
            return "If something suddenly changes, resist the urge to immediately fix it. Let the new shape settle before you respond."
    
    # Amplifier-driven move
    if amp and amp['planet'] == 'Jupiter':
        return "Scale back one reaction today. Whatever feels enormous may be 40% real and 60% amplification."
    
    # Concentration-driven move
    if fg and fg.get('type') == 'concentration':
        sign = fg.get('sign', '')
        if intensity == 'extreme':
            moves = {
                'Aries': "Pick one target for your energy and commit. Trying to act on everything will scatter what could actually land.",
                'Taurus': "Choose one area where 'good enough' is acceptable today. You can refine later.",
                'Gemini': "Write the three things competing for your attention. Pick one and give it thirty real minutes.",
                'Cancer': "Before you protect someone else, check: are you avoiding something of your own?",
                'Leo': "Create one thing — even tiny — before the day ends. The pressure is creative, not performative.",
                'Virgo': "Let one thing be imperfect today. Notice that the world doesn't end.",
                'Libra': "Make one decision you've been deferring. The discomfort of choosing is less than the cost of waiting.",
                'Scorpio': "Let one thing stay unresolved today. Not everything needs to be confronted right now.",
                'Sagittarius': "Ground yourself in one concrete commitment before noon. Freedom is easier with an anchor.",
                'Capricorn': "Distinguish between what you must do and what you think you should do. Drop one 'should.'",
                'Aquarius': "Before you rebel, ask yourself what you're actually building. Freedom needs a direction.",
                'Pisces': "Ground yourself in something physical — a walk, a meal, a list. Your body is more reliable than your feelings today.",
                'Ophiuchus': "Pick the smallest action that turns what you already know into something you do today. The integration moves through small, repeatable crossings.",
            }
            return moves.get(sign, "Focus your energy on the one thing that matters most right now. Let the rest orbit.")
    
    # Fallback
    tags = energy.get('tags', [])
    if 'tension-heavy' in tags:
        return "Don't try to resolve the tension. Just notice where it lands in your body — that's where the message is."
    if 'action-heavy' in tags:
        return "Move your body before you make any big decisions. The energy is physical and needs a physical outlet first."
    if 'emotionally-charged' in tags:
        return "Give yourself permission to feel without having to explain or justify it to anyone."
    
    return "Pay attention to the one moment today that feels different from the rest. It's pointing at something real."


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
