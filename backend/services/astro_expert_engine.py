"""Astrology Today Expert Interpreter V5.0

CORE RULE: Must feel like:
→ "A master astrologer who knows the user"

Must include:
- actual transits
- connection to user's chart
- behavioral translation
- grounded action

STRUCTURE (6 sections):
1. TODAY'S THEME (1 line tension)
2. WHAT'S ACTUALLY HAPPENING (real transit bullets)
3. HOW THIS INTERACTS WITH YOU (personalization - CRITICAL)
4. WHAT THIS MAY FEEL LIKE (concrete felt experience)
5. WHAT TO DO WITH IT (actionable, grounded)
6. ONE QUESTION (clean reflective prompt)

V5.0 UPGRADES:
1. BEHAVIORAL LANGUAGE ENFORCEMENT - Every line maps to real behavior
2. PERSONALIZATION DEPTH - Must reference pattern_memory and known tendencies
3. REAL TRANSIT SIGNALS - Actual planetary positions, not vague descriptions
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
import hashlib

logger = logging.getLogger(__name__)


# =============================================================================
# BEHAVIORAL LANGUAGE ENFORCEMENT (CRITICAL)
# =============================================================================

VAGUE_PHRASES = [
    "a pull toward",
    "energy shifting",
    "weight landing",
    "a door appearing",
    "something emerging",
    "cosmic forces",
    "universal energy",
    "vibration",
    "alignment",
    "the universe wants",
    "stars aligning",
    "flow state",
    "higher self",
    "inner calling",
    "cosmic dance",
    "celestial",
]

BEHAVIORAL_REPLACEMENTS = {
    "a pull toward more": "you're trying to take on more than you can realistically hold right now",
    "energy shifting": "something is changing in how you're approaching this",
    "weight landing": "a decision is pressing on you",
    "a door appearing": "an opportunity is becoming visible, and you're deciding whether to take it",
    "something emerging": "a pattern is becoming clear that you couldn't see before",
    "cosmic forces": "multiple pressures are converging at once",
    "universal energy": "the timing of several things is colliding",
    "cosmic dance": "the collision of timing and circumstances",
    "celestial": "astrological",
}


def enforce_behavioral_language(text: str) -> str:
    """Convert vague/poetic language to concrete behavioral statements."""
    result = text
    
    for vague, behavioral in BEHAVIORAL_REPLACEMENTS.items():
        if vague.lower() in result.lower():
            import re
            pattern = re.compile(re.escape(vague), re.IGNORECASE)
            result = pattern.sub(behavioral, result)
    
    return result


# =============================================================================
# TRANSIT INTERPRETATION LIBRARY (V5.0)
# =============================================================================

PLANET_MEANINGS = {
    "Sun": {
        "theme": "identity and direction",
        "pressure": "who you are vs who you're expected to be",
        "action": "clarify what actually matters to you",
    },
    "Moon": {
        "theme": "emotional needs",
        "pressure": "what you need vs what you're getting",
        "action": "honor what you're actually feeling",
    },
    "Mercury": {
        "theme": "communication and decisions",
        "pressure": "what you're saying vs what you mean",
        "action": "say the thing you've been holding back",
    },
    "Venus": {
        "theme": "relationships and values",
        "pressure": "what you want vs what you're settling for",
        "action": "notice where you're compromising too much",
    },
    "Mars": {
        "theme": "action and assertion",
        "pressure": "what you're doing vs what you want to do",
        "action": "take one decisive step forward",
    },
    "Jupiter": {
        "theme": "expansion and opportunity",
        "pressure": "wanting more vs accepting what is",
        "action": "identify one thing to expand, not everything",
    },
    "Saturn": {
        "theme": "responsibility and limits",
        "pressure": "freedom vs obligation",
        "action": "accept one limit you've been fighting",
    },
    "Uranus": {
        "theme": "disruption and change",
        "pressure": "stability vs breakthrough",
        "action": "let go of one thing that's no longer working",
    },
    "Neptune": {
        "theme": "dreams and illusions",
        "pressure": "idealism vs reality",
        "action": "distinguish hope from expectation",
    },
    "Pluto": {
        "theme": "transformation and power",
        "pressure": "control vs surrender",
        "action": "release what you're gripping too tightly",
    },
}

ASPECT_MEANINGS = {
    "conjunction": {
        "intensity": "high",
        "nature": "fusion of energies",
        "behavioral": "two parts of your life are colliding—they want to be integrated",
    },
    "opposition": {
        "intensity": "high",
        "nature": "tension requiring balance",
        "behavioral": "you're being pulled in two directions—both are valid, neither can win completely",
    },
    "square": {
        "intensity": "high",
        "nature": "friction requiring action",
        "behavioral": "something is blocking something else—the friction is pointing at what needs to change",
    },
    "trine": {
        "intensity": "low",
        "nature": "ease and flow",
        "behavioral": "this is coming easily—don't overthink it, just move with it",
    },
    "sextile": {
        "intensity": "moderate",
        "nature": "opportunity requiring action",
        "behavioral": "there's an opening here—but you have to act on it, it won't just happen",
    },
}

HOUSE_MEANINGS = {
    1: {"area": "identity", "behavioral": "how you're presenting yourself vs who you actually are"},
    2: {"area": "resources", "behavioral": "what you're holding onto vs what you need to release"},
    3: {"area": "communication", "behavioral": "what you're saying vs what you're not saying"},
    4: {"area": "home/foundation", "behavioral": "where you feel safe vs where you're being pushed"},
    5: {"area": "creativity/expression", "behavioral": "what you want to create vs what's blocking it"},
    6: {"area": "work/health", "behavioral": "your daily rhythm vs what's disrupting it"},
    7: {"area": "relationships", "behavioral": "what you're giving vs what you're receiving"},
    8: {"area": "transformation", "behavioral": "what needs to die vs what you're keeping alive"},
    9: {"area": "expansion/beliefs", "behavioral": "what you believe vs what you're learning"},
    10: {"area": "career/public", "behavioral": "how others see you vs how you see yourself"},
    11: {"area": "community/future", "behavioral": "where you belong vs where you're trying to fit"},
    12: {"area": "subconscious", "behavioral": "what's hidden vs what's trying to surface"},
}


# =============================================================================
# PERSONALIZATION ENGINE (CRITICAL)
# =============================================================================

async def get_personalization_context(
    db,
    user_id: str,
    pattern_memory_state: str,
    evolution_state: str
) -> Dict[str, Any]:
    """
    Get personalization context for Astrology Today.
    
    MUST explicitly reference:
    - detected pattern_memory (if exists)
    - known user tendencies (from profile or historical patterns)
    - recent behavioral signals (if available)
    """
    context = {
        "pattern_state_phrase": None,
        "tendency_phrases": [],
        "recent_signals": [],
    }
    
    # Pattern state language
    if pattern_memory_state == "returning_pattern":
        context["pattern_state_phrase"] = "This connects to something you were already dealing with recently."
    elif pattern_memory_state == "recurring_pattern":
        context["pattern_state_phrase"] = "This is the same pattern showing up again — not a one-off."
    
    # Get historical patterns for tendencies
    try:
        from services.pattern_memory_engine import get_pattern_history
        history = await get_pattern_history(db, user_id, days=60)
        
        # Analyze tendency patterns
        tension_counts = {}
        for entry in history:
            tension = entry.get("primary_tension", "")
            if tension:
                tension_counts[tension] = tension_counts.get(tension, 0) + 1
        
        # Get top tendencies
        sorted_tensions = sorted(tension_counts.items(), key=lambda x: x[1], reverse=True)
        
        if sorted_tensions:
            top_tendency = sorted_tensions[0][0]
            count = sorted_tensions[0][1]
            
            if count >= 5:
                context["tendency_phrases"].append(
                    f"Your pattern history shows {top_tendency.replace('_', ' ')} coming up repeatedly."
                )
            elif count >= 3:
                context["tendency_phrases"].append(
                    f"This touches your tendency around {top_tendency.replace('_', ' ')}."
                )
    except Exception as e:
        logger.debug(f"[Personalization] Could not get history: {e}")
    
    # Evolution state phrases
    if evolution_state == "escalating":
        context["tendency_phrases"].append("This tension has been intensifying recently.")
    elif evolution_state == "looping":
        context["tendency_phrases"].append("You've been cycling through this same response pattern.")
    elif evolution_state == "integrating":
        context["tendency_phrases"].append("You're starting to respond to this differently than before.")
    elif evolution_state == "softening":
        context["tendency_phrases"].append("This is less charged than it was recently.")
    
    return context


def generate_how_it_interacts(
    personalization: Dict[str, Any],
    planet_tension: Dict[str, Any],
    house_info: Dict[str, Any]
) -> List[str]:
    """
    Generate HOW THIS INTERACTS WITH YOU bullets.
    
    CRITICAL: Must explicitly reference pattern_memory and tendencies.
    Must feel like: "This system remembers me and sees the pattern continuing"
    """
    bullets = []
    
    # Pattern state reference
    if personalization.get("pattern_state_phrase"):
        bullets.append(personalization["pattern_state_phrase"])
    
    # Tendency references
    for phrase in personalization.get("tendency_phrases", [])[:2]:
        bullets.append(phrase)
    
    # Generic personalization if no history
    if not bullets:
        bullets.append(
            f"This hits your {house_info['area']} area — {house_info['behavioral']}."
        )
        bullets.append(
            f"The {planet_tension['theme']} theme amplifies any existing tension you carry around {planet_tension['pressure']}."
        )
    
    # Ensure behavioral language
    bullets = [enforce_behavioral_language(b) for b in bullets]
    
    return bullets[:3]


# =============================================================================
# MAIN GENERATOR
# =============================================================================

async def generate_astro_expert_diagnosis(
    db,
    user_id: str,
    chart_data: Dict[str, Any],
    transits: List[Dict[str, Any]],
    active_houses: List[int],
    pattern_memory_state: str = "new_pattern",
    evolution_state: str = "none"
) -> Dict[str, Any]:
    """
    V5.0: Generate Astrology Today as Expert Interpreter.
    
    6-SECTION STRUCTURE:
    1. TODAY'S THEME
    2. WHAT'S ACTUALLY HAPPENING
    3. HOW THIS INTERACTS WITH YOU
    4. WHAT THIS MAY FEEL LIKE
    5. WHAT TO DO WITH IT
    6. ONE QUESTION
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Get dominant transit
    dominant_transit = transits[0] if transits else None
    dominant_planet = dominant_transit.get("planet", "Moon") if dominant_transit else "Moon"
    
    planet_info = PLANET_MEANINGS.get(dominant_planet, PLANET_MEANINGS["Moon"])
    
    # Get primary house
    primary_house = active_houses[0] if active_houses else 1
    house_info = HOUSE_MEANINGS.get(primary_house, HOUSE_MEANINGS[1])
    
    # Get aspect if available
    aspect = dominant_transit.get("aspect", "conjunction") if dominant_transit else "conjunction"
    
    # Get personalization context
    personalization = await get_personalization_context(
        db, user_id, pattern_memory_state, evolution_state
    )
    
    # =========================================================================
    # 1. TODAY'S THEME (1 line)
    # =========================================================================
    todays_theme = f"{planet_info['pressure'].title()}"
    
    # =========================================================================
    # 2. WHAT'S ACTUALLY HAPPENING (transit bullets)
    # =========================================================================
    whats_happening = []
    
    for transit in transits[:4]:
        planet = transit.get("planet", "")
        natal_planet = transit.get("natal_planet", "")
        aspect_name = transit.get("aspect", "conjunction")
        house = transit.get("house", primary_house)
        
        a_info = ASPECT_MEANINGS.get(aspect_name, ASPECT_MEANINGS["conjunction"])
        
        if natal_planet:
            bullet = f"{planet} {aspect_name} your natal {natal_planet} → {a_info['behavioral']}"
        else:
            bullet = f"{planet} transiting House {house} → pressure on your {HOUSE_MEANINGS.get(house, house_info)['area']}"
        
        whats_happening.append(enforce_behavioral_language(bullet))
    
    if not whats_happening:
        whats_happening.append(f"{dominant_planet} activating your {house_info['area']} → {planet_info['pressure']}")
    
    # =========================================================================
    # 3. HOW THIS INTERACTS WITH YOU (personalization - CRITICAL)
    # =========================================================================
    how_it_interacts = generate_how_it_interacts(personalization, planet_info, house_info)
    
    # =========================================================================
    # 4. WHAT THIS MAY FEEL LIKE (concrete experience)
    # =========================================================================
    what_it_feels_like = [
        f"Feeling the pull between {planet_info['pressure'].split(' vs ')[0]} and {planet_info['pressure'].split(' vs ')[1] if ' vs ' in planet_info['pressure'] else 'something else'}",
        f"Noticing tension in your {house_info['area']} area — {house_info['behavioral'].split(' vs ')[0]}",
        "Wanting to act but not being sure which direction is right",
        "Sensing that something needs to change but not knowing what yet",
    ]
    
    # Select 2-3 based on context
    seed = f"{user_id}:{today}:feels"
    seed_hash = int(hashlib.md5(seed.encode()).hexdigest()[:8], 16)
    selected_feels = [what_it_feels_like[i % len(what_it_feels_like)] for i in range(seed_hash % 2 + 2, seed_hash % 2 + 5)]
    what_it_feels_like = [enforce_behavioral_language(f) for f in selected_feels[:3]]
    
    # =========================================================================
    # 5. WHAT TO DO WITH IT (actionable)
    # =========================================================================
    what_to_do = [
        planet_info["action"],
        f"Notice where {house_info['behavioral'].split(' vs ')[0]} without rushing to fix it",
        "Move one small thing forward instead of trying to solve everything",
    ]
    what_to_do = [enforce_behavioral_language(w) for w in what_to_do[:3]]
    
    # =========================================================================
    # 6. ONE QUESTION (reflective prompt)
    # =========================================================================
    questions = [
        f"What are you trying to {planet_info['action'].split()[0].lower()} before it's actually ready?",
        f"Where in your {house_info['area']} are you settling for less than you want?",
        f"What would change if you stopped fighting the {planet_info['theme']}?",
        "What are you avoiding that keeps coming back?",
    ]
    one_question = questions[seed_hash % len(questions)]
    
    return {
        "success": True,
        "lens": "astrology",
        "date": today,
        "version": "v5.0_expert",
        # V5.0 6-SECTION STRUCTURE
        "todays_theme": todays_theme,
        "whats_happening": whats_happening,
        "how_it_interacts": how_it_interacts,
        "what_it_feels_like": what_it_feels_like,
        "what_to_do": what_to_do,
        "one_question": one_question,
        # Pattern memory state
        "pattern_memory_state": pattern_memory_state,
        "evolution_state": evolution_state,
        # Signals for collapsed section
        "signals": {
            "transits": transits[:5],
            "active_houses": active_houses[:3],
            "dominant_planet": dominant_planet,
            "primary_house": primary_house,
        },
        "debug": {
            "dominant_planet": dominant_planet,
            "primary_house": primary_house,
            "aspect": aspect,
            "pattern_memory_state": pattern_memory_state,
            "evolution_state": evolution_state,
            "personalization_applied": bool(personalization.get("pattern_state_phrase") or personalization.get("tendency_phrases")),
            "version": "v5.0",
        }
    }
