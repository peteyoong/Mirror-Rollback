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
    
    # Pattern state language - V5.2: Direct, not explanatory
    if pattern_memory_state == "returning_pattern":
        context["pattern_state_phrase"] = "This was here recently. Still unresolved."
    elif pattern_memory_state == "recurring_pattern":
        context["pattern_state_phrase"] = "Again. You've circled this before."
    
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
            
            # V5.2: More DIRECT phrasing - no generic explanation language
            if count >= 5:
                context["tendency_phrases"].append(
                    f"This isn't new. You do this — {top_tendency_clean} — when pressure builds."
                )
            elif count >= 3:
                context["tendency_phrases"].append(
                    f"You've been here before. {top_tendency_clean.capitalize()} is your go-to response."
                )
    except Exception as e:
        logger.debug(f"[Personalization] Could not get history: {e}")
    
    # Evolution state phrases - V5.2: More DIRECT, less explanation
    if evolution_state == "escalating":
        context["tendency_phrases"].append("This is getting louder. You've ignored it, and now it's demanding attention.")
    elif evolution_state == "looping":
        context["tendency_phrases"].append("Same response, different situation. You keep circling this.")
    elif evolution_state == "integrating":
        context["tendency_phrases"].append("You're handling this differently now. Something has shifted.")
    elif evolution_state == "softening":
        context["tendency_phrases"].append("This doesn't hit as hard anymore. You've loosened your grip.")
    
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
# MAIN GENERATOR V5.2 WITH HORIZON INTERPRETATION
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
    V5.2: Generate Astrology Today with TRUE HORIZON INTERPRETATION.
    
    CRITICAL: Today / Week / Month MUST produce DISTINCT interpretations.
    Same event, DIFFERENT framing based on time horizon.
    
    THREE MODES:
    - TODAY: "What is peaking or loud right now?"
    - WEEK: "What keeps surfacing across these days?"
    - MONTH: "What larger arc is this part of?"
    
    GUARDRAILS:
    - Headlines MUST differ across horizons
    - Themes MUST differ across horizons
    - what_it_means MUST differ across horizons
    """
    from services.event_priority_engine import (
        compute_event_priority,
        detect_dominant_event,
        prioritize_transits
    )
    from services.field_signals import calculate_moon_phase, check_eclipse_season
    from services.horizon_interpretation_layer import get_horizon_interpretation
    
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
    # HORIZON INTERPRETATION LAYER - Get timeframe-specific content
    # =========================================================================
    if has_dominant_event and dominant_event:
        event_type = dominant_event.get("type", "full_moon")
        event_sign = dominant_event.get("sign", "Aries")
        
        # Get HORIZON-SPECIFIC interpretation
        horizon_content = get_horizon_interpretation(
            event_type=event_type,
            sign=event_sign,
            timeframe=timeframe,
            moon_data=moon_data,
            eclipse_data=eclipse_data
        )
        
        # Use horizon-specific content
        todays_theme = horizon_content.get("headline", "Event Active")
        theme_description = horizon_content.get("theme", "")
        event_what_it_means = horizon_content.get("what_it_means", "")
        event_felt_texture = horizon_content.get("felt_texture", [])
        event_action = horizon_content.get("action", "")
        event_question = horizon_content.get("question", "")
        explicit_event_name = dominant_event.get("explicit_name", "")
        
        logger.info(f"[AstroExpert] Horizon: {timeframe}, Event: {event_type}, Sign: {event_sign}")
    else:
        # No dominant event - use planet-based theme
        todays_theme = planet_info.get('tension', planet_info['pressure'].title())
        theme_description = ""
        event_what_it_means = ""
        event_felt_texture = []
        event_action = ""
        event_question = ""
        explicit_event_name = None
        event_sign = None
        horizon_content = {}
    
    # =========================================================================
    # 2. WHAT'S ACTUALLY HAPPENING (Horizon-specific framing)
    # =========================================================================
    whats_happening = []
    
    if has_dominant_event and dominant_event:
        event_type = dominant_event.get("type", "")
        
        # Timeframe-specific event announcement
        if timeframe == "today":
            if "full_moon" in event_type:
                whats_happening.append(f"🌕 **{explicit_event_name}** — This is a peak/release moment happening NOW")
            elif "new_moon" in event_type:
                whats_happening.append(f"🌑 **{explicit_event_name}** — A new cycle is seeding TODAY")
            elif "eclipse" in event_type:
                whats_happening.append(f"⬤ **{explicit_event_name}** — Portal event active RIGHT NOW")
        elif timeframe == "week":
            if "full_moon" in event_type:
                whats_happening.append(f"🌕 **{explicit_event_name} Week** — The same peak energy keeps returning this week")
            elif "new_moon" in event_type:
                whats_happening.append(f"🌑 **{explicit_event_name} Week** — New patterns emerging through repetition")
            elif "eclipse" in event_type:
                whats_happening.append("⬤ **Eclipse Week** — Rapid shifts rippling through multiple days")
        else:  # month
            if "full_moon" in event_type:
                whats_happening.append("🌕 **This Month's Lunation** — The Full Moon is ONE peak in a larger arc")
            elif "new_moon" in event_type:
                whats_happening.append("🌑 **This Month's Seed Point** — What's planted now grows over weeks")
            elif "eclipse" in event_type:
                whats_happening.append("⬤ **Eclipse Season Month** — Permanent shifts unfolding over the arc")
        
        # Add the horizon-specific meaning
        if event_what_it_means:
            whats_happening.append(event_what_it_means)
    
    # Add supporting transits (with horizon-appropriate framing)
    supporting_transits = event_priority.get("supporting_transits", [])
    for transit in (supporting_transits if supporting_transits else transits)[:2]:
        planet = transit.get("planet", "")
        natal_planet = transit.get("natal_planet", "")
        aspect_name = transit.get("aspect", "conjunction")
        house = transit.get("house", primary_house)
        
        t_planet_info = PLANET_MEANINGS.get(planet, {})
        a_info = ASPECT_MEANINGS.get(aspect_name, ASPECT_MEANINGS["conjunction"])
        h_info = HOUSE_MEANINGS.get(house, HOUSE_MEANINGS[1])
        
        if natal_planet:
            bullet = f"{planet} {aspect_name} your natal {natal_planet} — {a_info['behavioral']}"
        else:
            planet_tension = t_planet_info.get('tension', t_planet_info.get('pressure', 'pressure'))
            bullet = f"{planet} in your {h_info['area']} area — {planet_tension.lower()}"
        
        whats_happening.append(enforce_behavioral_language(bullet))
    
    if not whats_happening:
        whats_happening.append(f"{dominant_planet} activating your {house_info['area']} — {planet_info.get('tension', planet_info['pressure'])}")
    
    # =========================================================================
    # 3. HOW THIS INTERACTS WITH YOU (Horizon-specific personalization)
    # =========================================================================
    how_it_interacts = generate_how_it_interacts(personalization, planet_info, house_info)
    
    # Add horizon-specific event personalization - V5.2: More distinct per horizon
    if has_dominant_event and dominant_event:
        event_type = dominant_event.get("type", "")
        
        if timeframe == "today":
            if "full_moon" in event_type:
                how_it_interacts.insert(0, "The Full Moon is amplifying whatever you've been holding back — RIGHT NOW.")
            elif "new_moon" in event_type:
                how_it_interacts.insert(0, "The New Moon is inviting a fresh start TODAY — not forcing clarity.")
            elif "eclipse" in event_type:
                how_it_interacts.insert(0, "Eclipse energy is accelerating change TODAY. What shifts now won't come back.")
        elif timeframe == "week":
            if "full_moon" in event_type:
                how_it_interacts.insert(0, "The same intensity keeps finding different targets this week.")
            elif "new_moon" in event_type:
                how_it_interacts.insert(0, "New patterns are emerging through repetition — watch what keeps appearing.")
            elif "eclipse" in event_type:
                how_it_interacts.insert(0, "Eclipse ripples are spreading through multiple areas this week.")
        else:  # month
            if "full_moon" in event_type:
                how_it_interacts.insert(0, "The Full Moon is one moment. The month is the lesson.")
            elif "new_moon" in event_type:
                how_it_interacts.insert(0, "What you seed this month grows over the next cycle.")
            elif "eclipse" in event_type:
                how_it_interacts.insert(0, "This month marks a before/after. Integration takes time.")
    
    # =========================================================================
    # 4. WHAT THIS MAY FEEL LIKE (Horizon-specific felt texture)
    # =========================================================================
    what_it_feels_like = []
    
    # Use horizon-specific felt texture from event
    if event_felt_texture:
        what_it_feels_like.extend(event_felt_texture[:2])
    
    # Add planet-specific felt experiences
    if planet_info.get("felt_experience") and len(what_it_feels_like) < 3:
        for exp in planet_info["felt_experience"][:2]:
            if exp not in what_it_feels_like and len(what_it_feels_like) < 3:
                what_it_feels_like.append(exp.capitalize() if exp[0].islower() else exp)
    
    # Horizon-specific generic experiences
    if timeframe == "today":
        generic_experiences = [
            "Pressure in the body right now when trying to decide",
            "Restlessness that demands movement today",
            "Emotional intensity peaking in the moment",
        ]
    elif timeframe == "week":
        generic_experiences = [
            "The same tension surfacing in different situations this week",
            "Repeated moments of the same frustration",
            "Patterns that keep finding new forms",
        ]
    else:  # month
        generic_experiences = [
            "A gradual shift in how you're responding to familiar pressures",
            "Old patterns slowly loosening their grip",
            "New capacity emerging through the month's arc",
        ]
    
    # Fill to 3 if needed
    seed = f"{user_id}:{today}:{timeframe}:feels"
    seed_hash = int(hashlib.md5(seed.encode()).hexdigest()[:8], 16)
    while len(what_it_feels_like) < 3:
        idx = (seed_hash + len(what_it_feels_like)) % len(generic_experiences)
        what_it_feels_like.append(generic_experiences[idx])
    
    what_it_feels_like = [enforce_behavioral_language(f) for f in what_it_feels_like[:3]]
    
    # =========================================================================
    # 5. WHAT TO DO WITH IT (Horizon-specific action)
    # =========================================================================
    what_to_do = []
    
    # Use horizon-specific action from event
    if event_action:
        what_to_do.append(event_action)
    
    # Horizon-specific generic actions - V5.2: More distinct per horizon
    if timeframe == "today":
        what_to_do.extend([
            planet_info["action"],
            "Do one small thing. Not the whole list — just one.",
        ])
    elif timeframe == "week":
        what_to_do.extend([
            "Track what triggers the same reaction twice",
            "When the pattern repeats, notice — don't react",
        ])
    else:  # month
        what_to_do.extend([
            "Ask: what is this month teaching me that last month couldn't?",
            "By month's end, name what has permanently changed",
        ])
    
    what_to_do = [enforce_behavioral_language(w) for w in what_to_do[:3]]
    
    # =========================================================================
    # 6. ONE QUESTION (Horizon-specific reflective prompt)
    # =========================================================================
    # Use horizon-specific question from event
    if event_question:
        one_question = event_question
    else:
        # Fallback questions based on horizon
        if timeframe == "today":
            questions = [
                "What is most loud or urgent for you RIGHT NOW?",
                "What decision are you trying to force today that isn't ready?",
                "What are you avoiding that keeps pressing?",
            ]
        elif timeframe == "week":
            questions = [
                "What keeps surfacing this week that you haven't fully addressed?",
                "What pattern is repeating in different forms?",
                "What keeps triggering the same response?",
            ]
        else:  # month
            questions = [
                "What is this month teaching you that previous months couldn't?",
                "What phase are you in, and what does it require?",
                "What larger transformation is this period part of?",
            ]
        one_question = questions[seed_hash % len(questions)]
    
    return {
        "success": True,
        "lens": "astrology",
        "date": today,
        "version": "v5.2_horizon",
        "timeframe": timeframe,
        # V5.2 6-SECTION STRUCTURE (HORIZON-SPECIFIC)
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
            "event_sign": event_sign if has_dominant_event else None,
            "tier_summary": event_priority.get("tier_summary", {}),
            "moon_phase": moon_data.get("phase_name", "Unknown"),
            "days_to_full": round(moon_data.get("days_to_full", 0), 1),
            "days_to_new": round(moon_data.get("days_to_new", 0), 1),
        },
        # Horizon interpretation metadata
        "horizon_interpretation": {
            "timeframe": timeframe,
            "theme_description": theme_description,
            "horizon_source": "horizon_interpretation_layer" if horizon_content else "fallback",
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
            "horizon_mode": timeframe,
            "version": "v5.2",
        }
    }
