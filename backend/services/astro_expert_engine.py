"""Astrology Today Expert Interpreter V5.1 with Event Priority

CORE RULE: Must feel like:
→ "A master astrologer who knows the user"
→ If Full Moon is happening: "Oh — THAT'S why everything feels heightened"

Must include:
- actual transits
- connection to user's chart
- behavioral translation
- grounded action

STRUCTURE (6 sections):
1. TODAY'S THEME (1 line tension) - MUST derive from Tier 1 event if present
2. WHAT'S ACTUALLY HAPPENING (real transit bullets)
3. HOW THIS INTERACTS WITH YOU (personalization - CRITICAL)
4. WHAT THIS MAY FEEL LIKE (concrete felt experience)
5. WHAT TO DO WITH IT (actionable, grounded)
6. ONE QUESTION (clean reflective prompt)

V5.1 UPGRADES:
1. EVENT PRIORITY ENGINE - Tier 1 events DOMINATE theme generation
2. EXPLICIT EVENT NAMING - "Full Moon in Libra", not vague descriptions
3. BEHAVIORAL LANGUAGE ENFORCEMENT - Every line maps to real behavior
4. PERSONALIZATION DEPTH - References pattern_memory, known tendencies
5. REAL TRANSIT SIGNALS - Actual planetary positions, not vague descriptions

PRIORITY TIERS:
- Tier 1 (DOMINANT): Full Moon, New Moon, Eclipses, exact Sun/Moon/ASC/MC hits
- Tier 2 (STRONG): Jupiter/Saturn/Pluto aspects, tight orbs (<2°)
- Tier 3 (SUPPORTING): Minor aspects, wider orbs, fast-moving transits
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
# TRANSIT INTERPRETATION LIBRARY (V5.0) - LIVED TEXTURE
# =============================================================================
# Themes should feel lived and immediate, not abstract/conceptual

PLANET_MEANINGS = {
    "Sun": {
        "theme": "identity pressure",
        "tension": "Feeling pressure to be someone you're not sure you are",
        "pressure": "the pull between who you're becoming and who you're expected to stay",
        "action": "notice where you're performing vs where you're being real",
        "felt_experience": [
            "tension in the chest when pretending",
            "wanting to be seen but not sure how",
            "irritation when expectations feel heavy",
        ],
    },
    "Moon": {
        "theme": "emotional needs",
        "tension": "Needing something you're not getting—or not asking for",
        "pressure": "the gap between what you need and what you're allowing yourself to receive",
        "action": "name what you actually need without justifying it",
        "felt_experience": [
            "tightness in the stomach when needs go unmet",
            "wanting comfort but pushing it away",
            "emotional noise that won't settle",
        ],
    },
    "Mercury": {
        "theme": "communication and clarity",
        "tension": "Wanting to say something but not trusting how it will land",
        "pressure": "the distance between what you're thinking and what you're saying",
        "action": "say the thing you keep editing in your head",
        "felt_experience": [
            "rehearsing conversations that haven't happened",
            "overthinking before speaking",
            "frustration when misunderstood",
        ],
    },
    "Venus": {
        "theme": "relationships and worth",
        "tension": "Settling for less than what you actually want",
        "pressure": "wanting connection but not sure you deserve it on your terms",
        "action": "notice where you're over-giving or under-asking",
        "felt_experience": [
            "resentment building slowly",
            "wanting reassurance but not asking",
            "loneliness even when not alone",
        ],
    },
    "Mars": {
        "theme": "action and assertion",
        "tension": "Wanting to move but not trusting the direction",
        "pressure": "the urge to act vs the fear of acting wrong",
        "action": "move one small thing instead of waiting for certainty",
        "felt_experience": [
            "restlessness in the body",
            "irritability with no clear target",
            "energy that needs somewhere to go",
        ],
    },
    "Jupiter": {
        "theme": "expansion and excess",
        "tension": "Wanting more without being sure it's the right more",
        "pressure": "the pull to grow vs the risk of overextending",
        "action": "choose one thing to expand, release the others",
        "felt_experience": [
            "excitement that might be escapism",
            "optimism that hasn't been tested",
            "saying yes before checking capacity",
        ],
    },
    "Saturn": {
        "theme": "responsibility and limits",
        "tension": "Carrying weight that may or may not be yours",
        "pressure": "obligation pressing on freedom",
        "action": "name one limit you've been fighting and stop fighting it",
        "felt_experience": [
            "heaviness in the shoulders",
            "fatigue that rest doesn't fix",
            "guilt when resting",
        ],
    },
    "Uranus": {
        "theme": "disruption and change",
        "tension": "Something wants to break free, but you're not sure what it is",
        "pressure": "stability vs the need for breakthrough",
        "action": "identify what's no longer working and let it go",
        "felt_experience": [
            "sudden urges to change everything",
            "boredom with what used to work",
            "restlessness that won't be satisfied by small adjustments",
        ],
    },
    "Neptune": {
        "theme": "dreams and confusion",
        "tension": "Not being sure what's real and what you're hoping is real",
        "pressure": "idealism vs reality",
        "action": "distinguish hope from expectation—and accept the difference",
        "felt_experience": [
            "brain fog when trying to decide",
            "romanticizing what hasn't happened",
            "feeling lost without clear reason",
        ],
    },
    "Pluto": {
        "theme": "power and transformation",
        "tension": "Something is ending, and you're not in control of how",
        "pressure": "gripping vs surrendering",
        "action": "release what you're holding too tightly",
        "felt_experience": [
            "fear of losing control",
            "intensity in small interactions",
            "old patterns resurfacing for clearing",
        ],
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
    
    CRITICAL: All output must be sanitized - no internal pattern keys in user-facing copy
    """
    from services.pattern_sanitizer import sanitize_pattern_key, sanitize_tendency_phrase
    
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
            top_tendency_raw = sorted_tensions[0][0]
            count = sorted_tensions[0][1]
            
            # SANITIZE: Convert internal pattern key to human-readable
            top_tendency_clean = sanitize_pattern_key(top_tendency_raw)
            
            if count >= 5:
                context["tendency_phrases"].append(
                    f"This touches a pattern that's been showing up a lot for you lately — {top_tendency_clean}."
                )
            elif count >= 3:
                context["tendency_phrases"].append(
                    f"This connects to your tendency toward {top_tendency_clean} when pressure builds."
                )
    except Exception as e:
        logger.debug(f"[Personalization] Could not get history: {e}")
    
    # Evolution state phrases (already clean - no internal tokens)
    if evolution_state == "escalating":
        context["tendency_phrases"].append("This tension has been intensifying recently — it's not settling.")
    elif evolution_state == "looping":
        context["tendency_phrases"].append("You've been cycling through this same response pattern — it wants something different.")
    elif evolution_state == "integrating":
        context["tendency_phrases"].append("You're starting to respond to this differently than before. That's real progress.")
    elif evolution_state == "softening":
        context["tendency_phrases"].append("This is less charged than it was recently — something has loosened.")
    
    # Sanitize all tendency phrases before returning
    context["tendency_phrases"] = [
        sanitize_tendency_phrase(p) for p in context["tendency_phrases"]
    ]
    
    return context


def generate_how_it_interacts(
    personalization: Dict[str, Any],
    planet_info: Dict[str, Any],
    house_info: Dict[str, Any]
) -> List[str]:
    """
    Generate HOW THIS INTERACTS WITH YOU bullets.
    
    CRITICAL: Must explicitly reference pattern_memory and tendencies.
    Must feel like: "This system remembers me and sees the pattern continuing"
    
    NO INTERNAL TOKENS. All output must be clean, human-readable.
    """
    from services.pattern_sanitizer import sanitize_text_content
    
    bullets = []
    
    # Pattern state reference
    if personalization.get("pattern_state_phrase"):
        bullets.append(personalization["pattern_state_phrase"])
    
    # Tendency references
    for phrase in personalization.get("tendency_phrases", [])[:2]:
        bullets.append(phrase)
    
    # Add lived-texture personalization if we have planet info
    if planet_info.get("tension"):
        bullets.append(f"{planet_info['tension']}.")
    
    # Generic personalization if no history
    if not bullets:
        bullets.append(
            f"This is hitting your {house_info['area']} area — {house_info['behavioral']}."
        )
        if planet_info.get("pressure"):
            bullets.append(
                f"You may feel the pull between {planet_info['pressure']}."
            )
    
    # Ensure behavioral language and sanitize
    cleaned_bullets = []
    for b in bullets:
        b = enforce_behavioral_language(b)
        b = sanitize_text_content(b)
        cleaned_bullets.append(b)
    
    return cleaned_bullets[:3]


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
    evolution_state: str = "none",
    moon_data: Optional[Dict[str, Any]] = None,
    eclipse_data: Optional[Dict[str, Any]] = None,
    timeframe: str = "today"
) -> Dict[str, Any]:
    """
    V5.1: Generate Astrology Today as Expert Interpreter with Event Priority.
    
    CRITICAL: If Tier 1 event exists (Full Moon, New Moon, Eclipse),
    theme MUST derive from that event. No averaging.
    
    6-SECTION STRUCTURE:
    1. TODAY'S THEME - MUST derive from Tier 1 event if present
    2. WHAT'S ACTUALLY HAPPENING - Main event + supporting transits
    3. HOW THIS INTERACTS WITH YOU - Personalization
    4. WHAT THIS MAY FEEL LIKE - Concrete felt experience
    5. WHAT TO DO WITH IT - Actionable
    6. ONE QUESTION - Reflective prompt
    """
    from services.event_priority_engine import (
        compute_event_priority, 
        detect_dominant_event,
        prioritize_transits
    )
    from services.field_signals import calculate_moon_phase, check_eclipse_season
    
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")
    
    # Get moon and eclipse data if not provided
    if moon_data is None:
        moon_data = calculate_moon_phase(now)
    if eclipse_data is None:
        eclipse_data = check_eclipse_season(now)
    
    # =========================================================================
    # EVENT PRIORITY ENGINE - Detect Tier 1 dominant events
    # =========================================================================
    event_priority = compute_event_priority(
        transits=transits,
        moon_data=moon_data,
        eclipse_data=eclipse_data,
        timeframe=timeframe,
        dt=now
    )
    
    has_dominant_event = event_priority.get("has_dominant_event", False)
    dominant_event = event_priority.get("dominant_event")
    main_event = event_priority.get("main_event", {})
    
    # Get dominant transit for fallback
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
    # 1. TODAY'S THEME (MUST derive from Tier 1 event if present)
    # =========================================================================
    if has_dominant_event and dominant_event:
        # TIER 1 ACTIVE — Theme MUST come from dominant event
        todays_theme = main_event.get("headline", "Major Event Active")
        explicit_event_name = dominant_event.get("explicit_name", "")
        event_sign = dominant_event.get("sign", "")
    else:
        # No Tier 1 — Use planet-based theme
        todays_theme = planet_info.get('tension', planet_info['pressure'].title())
        explicit_event_name = None
        event_sign = None
    
    # =========================================================================
    # 2. WHAT'S ACTUALLY HAPPENING (Main Event + Supporting Transits)
    # =========================================================================
    whats_happening = []
    
    if has_dominant_event and dominant_event:
        # FIRST: Explicitly name the main event
        event_type = dominant_event.get("type", "")
        if "full_moon" in event_type:
            whats_happening.append(f"🌕 **{explicit_event_name}** — This is a peak/release moment")
        elif "new_moon" in event_type:
            whats_happening.append(f"🌑 **{explicit_event_name}** — A new cycle is seeding")
        elif "eclipse" in event_type:
            whats_happening.append(f"⬤ **{explicit_event_name}** — Portal event, major shifts possible")
        
        # Add the meaning
        whats_happening.append(main_event.get("what_it_means", ""))
    
    # Add supporting transits (Tier 2 and 3)
    supporting_transits = event_priority.get("supporting_transits", [])
    for transit in (supporting_transits if supporting_transits else transits)[:3]:
        planet = transit.get("planet", "")
        natal_planet = transit.get("natal_planet", "")
        aspect_name = transit.get("aspect", "conjunction")
        house = transit.get("house", primary_house)
        
        t_planet_info = PLANET_MEANINGS.get(planet, {})
        a_info = ASPECT_MEANINGS.get(aspect_name, ASPECT_MEANINGS["conjunction"])
        h_info = HOUSE_MEANINGS.get(house, HOUSE_MEANINGS[1])
        
        # Build more lived-texture transit description
        if natal_planet:
            bullet = f"{planet} {aspect_name} your natal {natal_planet} — {a_info['behavioral']}"
        else:
            planet_tension = t_planet_info.get('tension', t_planet_info.get('pressure', 'pressure'))
            bullet = f"{planet} in your {h_info['area']} area — {planet_tension.lower()}"
        
        whats_happening.append(enforce_behavioral_language(bullet))
    
    if not whats_happening:
        whats_happening.append(f"{dominant_planet} activating your {house_info['area']} — {planet_info.get('tension', planet_info['pressure'])}")
    
    # =========================================================================
    # 3. HOW THIS INTERACTS WITH YOU (personalization - CRITICAL)
    # =========================================================================
    how_it_interacts = generate_how_it_interacts(personalization, planet_info, house_info)
    
    # If dominant event, add event-specific personalization
    if has_dominant_event and dominant_event:
        event_type = dominant_event.get("type", "")
        if "full_moon" in event_type:
            how_it_interacts.insert(0, "The Full Moon is amplifying whatever you've been holding back.")
        elif "new_moon" in event_type:
            how_it_interacts.insert(0, "The New Moon is inviting you to start fresh — but not force clarity.")
        elif "eclipse" in event_type:
            how_it_interacts.insert(0, "Eclipse energy accelerates change. What shifts now won't come back the same.")
    
    # =========================================================================
    # 4. WHAT THIS MAY FEEL LIKE (concrete experience - LIVED TEXTURE)
    # =========================================================================
    what_it_feels_like = []
    
    # If dominant event, use its felt texture FIRST
    if has_dominant_event:
        event_felt_texture = event_priority.get("felt_texture", [])
        what_it_feels_like.extend(event_felt_texture[:2])
    
    # Add planet-specific felt experiences
    if planet_info.get("felt_experience"):
        for exp in planet_info["felt_experience"][:2]:
            if exp not in what_it_feels_like:
                what_it_feels_like.append(exp.capitalize() if exp[0].islower() else exp)
    
    # Add house-related felt experience
    if len(what_it_feels_like) < 3:
        what_it_feels_like.append(f"Tension in your {house_info['area']} area — {house_info['behavioral'].split(' vs ')[0]}")
    
    # Add generic lived-texture experiences
    generic_experiences = [
        "Wanting to act but not trusting the timing",
        "Restlessness that won't settle until something moves",
        "Pressure in the body when trying to decide",
        "Overthinking before speaking or acting",
        "Irritability without a clear target",
    ]
    
    # Fill to 3 if needed
    seed = f"{user_id}:{today}:feels"
    seed_hash = int(hashlib.md5(seed.encode()).hexdigest()[:8], 16)
    while len(what_it_feels_like) < 3:
        idx = (seed_hash + len(what_it_feels_like)) % len(generic_experiences)
        what_it_feels_like.append(generic_experiences[idx])
    
    what_it_feels_like = [enforce_behavioral_language(f) for f in what_it_feels_like[:3]]
    
    # =========================================================================
    # 5. WHAT TO DO WITH IT (actionable)
    # =========================================================================
    what_to_do = []
    
    # If dominant event, use its action FIRST
    if has_dominant_event:
        event_action = event_priority.get("action", "")
        if event_action:
            what_to_do.append(event_action)
    
    what_to_do.extend([
        planet_info["action"],
        f"Notice where {house_info['behavioral'].split(' vs ')[0]} without rushing to fix it",
        "Move one small thing forward instead of trying to solve everything",
    ])
    what_to_do = [enforce_behavioral_language(w) for w in what_to_do[:3]]
    
    # =========================================================================
    # 6. ONE QUESTION (reflective prompt)
    # =========================================================================
    # Event-specific questions
    if has_dominant_event:
        event_type = dominant_event.get("type", "") if dominant_event else ""
        if "full_moon" in event_type:
            questions = [
                "What have you been waiting for 'the right moment' to release?",
                "What clarity are you avoiding because it requires action?",
                "What's reaching a peak that you've been hoping would just resolve itself?",
            ]
        elif "new_moon" in event_type:
            questions = [
                "What new beginning have you been hesitant to seed?",
                "What do you want to start that you keep talking yourself out of?",
                "If clarity isn't coming yet, can you plant the intention anyway?",
            ]
        elif "eclipse" in event_type:
            questions = [
                "What's changing that you can't control?",
                "What would shift if you stopped resisting this transition?",
                "What old version of yourself is this eclipse asking you to release?",
            ]
        else:
            questions = [
                f"What are you trying to {planet_info['action'].split()[0].lower()} before it's actually ready?",
                f"Where in your {house_info['area']} are you settling for less than you want?",
                "What are you avoiding that keeps coming back?",
            ]
    else:
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
        "version": "v5.1_event_priority",
        # V5.1 6-SECTION STRUCTURE
        "todays_theme": todays_theme,
        "whats_happening": whats_happening,
        "how_it_interacts": how_it_interacts,
        "what_it_feels_like": what_it_feels_like,
        "what_to_do": what_to_do,
        "one_question": one_question,
        # Event priority metadata
        "event_priority": {
            "has_dominant_event": has_dominant_event,
            "dominant_event": dominant_event,
            "explicit_event_name": explicit_event_name,
            "event_sign": event_sign,
            "tier_summary": event_priority.get("tier_summary", {}),
            "moon_phase": moon_data.get("phase_name", "Unknown"),
            "days_to_full": round(moon_data.get("days_to_full", 0), 1),
            "days_to_new": round(moon_data.get("days_to_new", 0), 1),
        },
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
            "event_priority_active": has_dominant_event,
            "version": "v5.1",
        }
    }
