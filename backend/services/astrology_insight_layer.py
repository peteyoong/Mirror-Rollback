"""
Astrology Insight Layer (V1)
============================

Redesigns the Astrology lens to follow the same Mirror system as BaZi and Numerology.

Astrology must NOT feel like a chart report.
It must feel like:
- immediate recognition first
- system proof second
- current-life relevance throughout

GOAL:
- Hit with truth immediately
- Show there is real structure underneath it
- Mirror-style insight on the surface
- chart/transit proof underneath
- no jargon-first experience

STRUCTURE:
1. CONTINUATION
2. CORE TRUTH
3. ECHO
4. HOW THIS SHOWS UP
5. WHEN THIS BACKFIRES
6. GENIUS
7. WHAT THIS COSTS
8. ONE SHIFT
9. WHY THIS IS SHOWING UP (collapsible proof layer)
10. SEE YOUR ASTROLOGY DETAILS (collapsible raw data)
"""

import random
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


# =============================================================================
# CONTINUATION LAYER - Bridge from Mirror Home
# =============================================================================

CONTINUATION_LINES = [
    "This is the same pattern — just from a different angle.",
    "You've seen this already.",
    "Same signal. Different proof.",
    "This keeps showing up.",
    "You know this one.",
    "Same pattern. Just clearer here.",
    "This connects to what showed up earlier."
]

def generate_continuation_line() -> str:
    """Short continuation line at the top - bridges from Mirror Home."""
    return random.choice(CONTINUATION_LINES)


# =============================================================================
# ECHO LAYER - Cross-lens recognition
# =============================================================================

ECHO_LINES = [
    # Neutral
    "This isn't new.",
    "You've felt this before.",
    "You know this one.",
    # Sharp / Lived
    "You keep ending up here.",
    "You've hit this before.",
    "This is where it loops.",
    "You don't get past this — it resets.",
    "You've already been here recently.",
    "You thought you moved past this.",
    "This part again.",
    "You're back in the same spot."
]

def generate_echo_line() -> str:
    """Short recognition line that reinforces recurrence."""
    return random.choice(ECHO_LINES)


# =============================================================================
# CROSS-LENS LINKING (V1) - Connect patterns across features
# =============================================================================

CROSS_LINK_LINES = [
    "This showed up earlier today.",
    "You've already seen this.",
    "Same thing — just showing up here too.",
    "This isn't the first place you've seen this.",
    "You're seeing it again.",
    "This is showing up everywhere.",
    "Same pattern, different angle.",
    "You noticed this already."
]

def generate_cross_link_line() -> str:
    """
    Generate a short cross-link line that connects patterns across features.
    
    Purpose: Make user feel "This is the same pattern showing up everywhere"
    
    Rules:
    - 1 short line
    - calm
    - no explanation
    - no system jargon (no "numerology", "astrology", etc.)
    - Must feel like recognition, not instruction
    """
    return random.choice(CROSS_LINK_LINES)


# =============================================================================
# CORE TRUTH - The Hero (No astrology terms)
# =============================================================================

# Core truths based on dominant chart energy
# Format: "[Observable truth]. [Why it creates tension]."
SUN_CORE_TRUTHS = {
    "aries": "You don't wait once something feels real. That's why half-clear situations drive you crazy.",
    "taurus": "You hold on until you're sure. That's why forced change feels like betrayal.",
    "gemini": "You need to understand before you commit. That's why certainty often comes too late.",
    "cancer": "You feel the room before you enter it. That's why other people's tension becomes yours.",
    "leo": "You need to be seen doing it right. That's why invisible effort drains you.",
    "virgo": "You notice what's wrong before what's working. That's why you're already fixing things no one asked about.",
    "libra": "You hold the middle until someone moves first. That's why decisions feel like they're never really yours.",
    "scorpio": "You see what people are hiding. That's why surface-level relationships don't hold your attention.",
    "sagittarius": "You need to know where this is going. That's why commitment feels like a cage.",
    "capricorn": "You measure progress constantly. That's why invisible growth feels like standing still.",
    "aquarius": "You see patterns others miss. That's why being misunderstood feels personal.",
    "pisces": "You absorb before you filter. That's why other people's emotions feel like your own."
}

MOON_EMOTIONAL_TRUTHS = {
    "aries": "Your first reaction is usually right — but it arrives before you're ready to act on it.",
    "taurus": "You need time to feel safe. Rushing that process always backfires.",
    "gemini": "You process by talking. Silence doesn't mean you've figured it out.",
    "cancer": "You remember everything that mattered. That's why letting go takes longer.",
    "leo": "You need your feelings witnessed. Unexpressed emotions turn inward.",
    "virgo": "You analyze feelings instead of feeling them. Sometimes that's protective, sometimes it's avoidance.",
    "libra": "You feel through relationship. Being alone with emotions is harder than it should be.",
    "scorpio": "You feel everything at full intensity. Moderation isn't an option.",
    "sagittarius": "You escape discomfort through movement. Staying with the feeling is the work.",
    "capricorn": "You handle feelings by handling tasks. Productivity is sometimes a disguise.",
    "aquarius": "You observe your emotions from a distance. Getting closer is the harder move.",
    "pisces": "You feel everything, even what isn't yours. Boundaries are the lesson."
}

RISING_APPROACH_TRUTHS = {
    "aries": "You approach new situations by taking charge — even when you don't know what you're doing yet.",
    "taurus": "You take your time with new things. People mistake it for resistance.",
    "gemini": "You read the room by asking questions. Sometimes you're gathering intel, sometimes you're stalling.",
    "cancer": "You test safety before opening up. The delay is protective, not cold.",
    "leo": "You enter with confidence — even when you don't feel it.",
    "virgo": "You watch before you participate. People think you're judging, but you're calibrating.",
    "libra": "You make space for others first. It looks generous, but it's also a delay tactic.",
    "scorpio": "You reveal nothing until you've read the room. It's strategy, not paranoia.",
    "sagittarius": "You treat new situations like adventure. Sometimes that bypasses necessary caution.",
    "capricorn": "You present the composed version. The messy parts stay private.",
    "aquarius": "You stand slightly apart. It's not rejection — it's observation.",
    "pisces": "You adapt to the energy around you. Sometimes you lose your own shape."
}


def generate_core_truth(sun_sign: str, moon_sign: str, rising_sign: str) -> str:
    """
    Generate the hero core truth statement.
    
    Rules:
    - 1-2 lines max
    - no astrology terms
    - must feel like immediate recognition
    - same Mirror tone as BaZi / Numerology
    """
    sun = sun_sign.lower() if sun_sign else "aries"
    return SUN_CORE_TRUTHS.get(sun, 
        "You run a pattern that's invisible to you but obvious to everyone else."
    )


# =============================================================================
# GENIUS LAYER - Why the pattern exists
# =============================================================================

SUN_GENIUS = {
    "aries": "You move fast once something feels clear. That's why waiting feels unbearable.",
    "taurus": "You see what will last. That's why shortcuts feel like waste.",
    "gemini": "You connect ideas others miss. That's why focus feels limiting.",
    "cancer": "You remember what mattered. That's why moving on takes longer.",
    "leo": "You create energy where there was none. That's why invisibility feels wrong.",
    "virgo": "You see the flaw before the finish. That's why 'good enough' never lands.",
    "libra": "You see both sides at once. That's why choosing feels like losing.",
    "scorpio": "You see what's hidden. That's why surfaces frustrate you.",
    "sagittarius": "You see where it's going. That's why staying put feels like giving up.",
    "capricorn": "You see the long game. That's why shortcuts feel like failure.",
    "aquarius": "You see what doesn't fit. That's why conformity feels like loss.",
    "pisces": "You feel what isn't said. That's why clarity sometimes hurts."
}

def generate_genius_line(sun_sign: str) -> str:
    """
    Generate the GENIUS line explaining why the pattern exists.
    
    Rules:
    - no separate card
    - no hype
    - no "you are gifted"
    - must explain the mechanism without softening it
    """
    sun = sun_sign.lower() if sun_sign else "aries"
    return SUN_GENIUS.get(sun,
        "You run the pattern before you check if it's working. That's why the same results keep showing up."
    )


# =============================================================================
# HOW THIS SHOWS UP - Observable behaviors
# =============================================================================

SUN_BEHAVIORS = {
    "aries": [
        "You decide fast once you feel the direction",
        "You push for movement when things feel stuck",
        "You lose patience with half-formed answers",
        "You start before you have the full picture",
        "You feel stuck when forced to wait"
    ],
    "taurus": [
        "You resist changes that weren't your idea",
        "You stay longer than most would",
        "You value consistency over excitement",
        "You build slowly but permanently",
        "You feel betrayed by sudden shifts"
    ],
    "gemini": [
        "You process by talking it through",
        "You hold multiple perspectives at once",
        "You get bored once you've understood something",
        "You ask questions before making moves",
        "You change direction when new info arrives"
    ],
    "cancer": [
        "You remember what others forget",
        "You feel the room before you enter it",
        "You take on other people's emotions",
        "You protect before being asked",
        "You retreat when you feel unsafe"
    ],
    "leo": [
        "You need your effort acknowledged",
        "You create energy where there was none",
        "You lead when no one else steps up",
        "You struggle with invisible contribution",
        "You feel drained by ungrateful dynamics"
    ],
    "virgo": [
        "You notice what's wrong first",
        "You fix things before being asked",
        "You hold yourself to impossible standards",
        "You analyze instead of feel",
        "You struggle to accept 'good enough'"
    ],
    "libra": [
        "You wait for others to move first",
        "You see merit on both sides",
        "You avoid conflict by over-adapting",
        "You feel paralyzed by either/or choices",
        "You lose track of what you actually want"
    ],
    "scorpio": [
        "You see past what people say",
        "You test before you trust",
        "You feel betrayal deeply",
        "You remember who did what",
        "You don't do shallow connection"
    ],
    "sagittarius": [
        "You need to know where this is going",
        "You leave before things get stale",
        "You see meaning before you see logistics",
        "You overcommit when excited",
        "You struggle with routine that doesn't lead anywhere"
    ],
    "capricorn": [
        "You measure progress constantly",
        "You feel responsible for outcomes",
        "You work when others rest",
        "You delay gratification instinctively",
        "You carry more than you should"
    ],
    "aquarius": [
        "You notice what doesn't fit",
        "You question what others accept",
        "You think in systems, not moments",
        "You need space more than closeness",
        "You feel misunderstood often"
    ],
    "pisces": [
        "You absorb the room's energy",
        "You feel what isn't being said",
        "You escape when things get heavy",
        "You blur your needs with others'",
        "You give more than you track"
    ]
}

def generate_how_this_shows_up(sun_sign: str, moon_sign: str) -> List[str]:
    """
    Generate 3-5 observable behavior bullets.
    
    Rules:
    - observable behavior only
    - no chart jargon
    - must sound like something a friend could say about them
    """
    sun = sun_sign.lower() if sun_sign else "aries"
    behaviors = SUN_BEHAVIORS.get(sun, [
        "You run your patterns before checking if they work",
        "You react before you process",
        "You repeat cycles without noticing"
    ])
    return behaviors[:4]


# =============================================================================
# WHEN THIS BACKFIRES - Confronting consequences
# =============================================================================

SUN_BACKFIRES = {
    "aries": [
        "You force movement before trust is there",
        "You make the call just to end the tension",
        "You act first, then clean up later",
        "You push when patience would've worked better"
    ],
    "taurus": [
        "You hold on past the point of reason",
        "You mistake stubbornness for loyalty",
        "You resist changes that would help",
        "You stay comfortable instead of growing"
    ],
    "gemini": [
        "You talk past the point where it helps",
        "You change direction before giving things time",
        "You gather information instead of committing",
        "You overthink simple decisions"
    ],
    "cancer": [
        "You absorb problems that aren't yours",
        "You protect people who don't need protecting",
        "You retreat when showing up matters",
        "You remember wounds longer than necessary"
    ],
    "leo": [
        "You perform when presence was enough",
        "You need validation for things that shouldn't require it",
        "You take rejection personally when it wasn't about you",
        "You dim others' light to brighten your own"
    ],
    "virgo": [
        "You critique before you understand",
        "You fix things that weren't broken",
        "You over-prepare instead of starting",
        "You hold impossible standards against yourself"
    ],
    "libra": [
        "You delay decisions until others decide for you",
        "You accommodate until you disappear",
        "You avoid conflict until it explodes",
        "You lose yourself in someone else's position"
    ],
    "scorpio": [
        "You test people who've already proven themselves",
        "You hold grudges past their usefulness",
        "You see betrayal where there was just carelessness",
        "You manipulate when directness would've worked"
    ],
    "sagittarius": [
        "You leave before giving things time",
        "You commit to too many directions at once",
        "You chase meaning instead of building foundations",
        "You optimize for freedom over connection"
    ],
    "capricorn": [
        "You work when rest would've been more useful",
        "You measure progress when presence was needed",
        "You delay rewards past the point of motivation",
        "You carry burdens that weren't yours to carry"
    ],
    "aquarius": [
        "You observe when participating was the move",
        "You intellectualize feelings instead of feeling them",
        "You detach when connection was needed",
        "You prioritize being right over being close"
    ],
    "pisces": [
        "You absorb when boundaries were needed",
        "You escape when staying was the work",
        "You give until empty, then resent the asking",
        "You confuse their needs for your own"
    ]
}

def generate_when_backfires(sun_sign: str) -> List[str]:
    """
    Generate 3-4 confronting backfire bullets.
    
    Rules:
    - slightly confronting
    - concrete
    - no "may/can/tends to"
    """
    sun = sun_sign.lower() if sun_sign else "aries"
    backfires = SUN_BACKFIRES.get(sun, [
        "You repeat the pattern before you notice it",
        "You react before you understand",
        "You push when stillness was the answer"
    ])
    return backfires[:4]


# =============================================================================
# WHAT THIS COSTS - Concrete cost framing
# =============================================================================

SUN_COSTS = {
    "aries": {
        "energy": "You waste energy cleaning up what wasn't ready",
        "relationships": "People feel rushed before they feel included",
        "trust": "You trade short-term relief for long-term friction"
    },
    "taurus": {
        "energy": "You spend energy resisting what was inevitable anyway",
        "relationships": "People stop sharing because you don't want to hear it",
        "trust": "You lose opportunities by waiting too long"
    },
    "gemini": {
        "energy": "You scatter energy across options that never land",
        "relationships": "People feel like another conversation, not a commitment",
        "trust": "Your word carries less weight because it shifts"
    },
    "cancer": {
        "energy": "You exhaust yourself carrying what isn't yours",
        "relationships": "People feel smothered before they feel loved",
        "trust": "Your boundaries lose meaning because they bend"
    },
    "leo": {
        "energy": "You drain yourself performing for empty rooms",
        "relationships": "People feel like audiences, not partners",
        "trust": "Your confidence gets mistaken for arrogance"
    },
    "virgo": {
        "energy": "You exhaust yourself perfecting what doesn't need it",
        "relationships": "People feel criticized before they feel seen",
        "trust": "Your help gets rejected because it feels like judgment"
    },
    "libra": {
        "energy": "You spend energy maintaining balance that isn't yours to hold",
        "relationships": "People don't know what you actually want",
        "trust": "Your yes loses weight because you say it too easily"
    },
    "scorpio": {
        "energy": "You exhaust yourself guarding against threats that aren't there",
        "relationships": "People feel tested instead of trusted",
        "trust": "Your intensity pushes away what you're trying to protect"
    },
    "sagittarius": {
        "energy": "You waste energy chasing horizons that keep moving",
        "relationships": "People feel like pit stops, not destinations",
        "trust": "Your commitments lose credibility because they shift"
    },
    "capricorn": {
        "energy": "You exhaust yourself climbing when rest was the answer",
        "relationships": "People feel like projects instead of connections",
        "trust": "Your reliability becomes an impossible standard"
    },
    "aquarius": {
        "energy": "You spend energy observing instead of connecting",
        "relationships": "People feel studied instead of understood",
        "trust": "Your detachment reads as not caring"
    },
    "pisces": {
        "energy": "You drain yourself feeling what isn't yours",
        "relationships": "People don't know where you end and they begin",
        "trust": "Your giving becomes invisible because you don't track it"
    }
}

def generate_costs(sun_sign: str) -> Dict[str, str]:
    """Generate concrete cost statements."""
    sun = sun_sign.lower() if sun_sign else "aries"
    return SUN_COSTS.get(sun, {
        "energy": "You run the pattern until you're depleted",
        "relationships": "People can't find you inside your patterns",
        "trust": "Your autopilot erodes credibility over time"
    })


# =============================================================================
# ONE SHIFT - Practical move
# =============================================================================

SUN_SHIFTS = {
    "aries": "Wait one more beat before you decide.",
    "taurus": "Let one thing change without resisting it.",
    "gemini": "Commit to one direction before you have all the info.",
    "cancer": "Put down one thing that isn't yours to carry.",
    "leo": "Do one thing without needing acknowledgment.",
    "virgo": "Let one thing stay imperfect today.",
    "libra": "Make one decision without checking what others think.",
    "scorpio": "Trust one person who hasn't fully proven themselves.",
    "sagittarius": "Stay with one thing longer than feels comfortable.",
    "capricorn": "Rest before you've earned it.",
    "aquarius": "Participate before you've observed enough.",
    "pisces": "Say no to one thing that felt like your responsibility."
}

def generate_one_shift(sun_sign: str) -> str:
    """
    Generate one practical move.
    
    Rules:
    - one move only
    - grounded
    - immediately usable
    - no philosophy
    """
    sun = sun_sign.lower() if sun_sign else "aries"
    return SUN_SHIFTS.get(sun,
        "Pause before running the pattern again."
    )


# =============================================================================
# TODAY TAB - Insight-first daily guidance
# =============================================================================

def generate_today_insight(
    sun_sign: str,
    transit_tension: Optional[str] = None,
    day_class: str = "normal_flow"
) -> Dict[str, str]:
    """
    Generate today tab content using insight-first approach.
    
    Structure:
    1. Today's truth
    2. What today rewards
    3. What backfires today
    4. One move
    """
    sun = sun_sign.lower() if sun_sign else "aries"
    
    # Default today's truth based on sun sign
    today_truths = {
        "aries": "You'll feel pressure to move before things are fully clear.",
        "taurus": "Something will ask you to change before you're ready.",
        "gemini": "You'll want to gather more information before deciding.",
        "cancer": "You'll feel the weight of something that isn't entirely yours.",
        "leo": "You'll need acknowledgment that might not come.",
        "virgo": "You'll notice flaws that others don't see yet.",
        "libra": "You'll be asked to choose before you feel balanced.",
        "scorpio": "Something hidden will become visible.",
        "sagittarius": "You'll feel the pull toward something new.",
        "capricorn": "Progress will feel slower than it is.",
        "aquarius": "You'll see what others are missing.",
        "pisces": "You'll absorb more than you realize."
    }
    
    rewards = {
        "aries": "Movement that comes after naming what's unresolved.",
        "taurus": "Patience that isn't stubbornness in disguise.",
        "gemini": "Focus that stays long enough to land.",
        "cancer": "Protection that doesn't turn into control.",
        "leo": "Contribution that doesn't require recognition.",
        "virgo": "Help that doesn't feel like criticism.",
        "libra": "Decisions made without consensus.",
        "scorpio": "Truth that isn't delivered as a weapon.",
        "sagittarius": "Commitment that doesn't feel like limitation.",
        "capricorn": "Rest that doesn't feel like failure.",
        "aquarius": "Connection that doesn't require conformity.",
        "pisces": "Boundaries that don't feel like abandonment."
    }
    
    backfires = {
        "aries": "Forcing a decision just to stop the tension.",
        "taurus": "Refusing change just because it wasn't your idea.",
        "gemini": "Gathering more info when you already know enough.",
        "cancer": "Taking on emotional labor no one asked for.",
        "leo": "Performing when presence was enough.",
        "virgo": "Fixing things before understanding them.",
        "libra": "Saying yes when you meant 'let me think'.",
        "scorpio": "Testing people who've already proven themselves.",
        "sagittarius": "Committing to escape rather than growth.",
        "capricorn": "Working when rest was the productive move.",
        "aquarius": "Analyzing feelings instead of feeling them.",
        "pisces": "Disappearing when staying was the work."
    }
    
    moves = {
        "aries": "Wait one more beat before committing.",
        "taurus": "Let one thing change without friction.",
        "gemini": "Decide with what you know now.",
        "cancer": "Put down one thing that wasn't yours.",
        "leo": "Do one thing invisibly.",
        "virgo": "Leave one thing imperfect.",
        "libra": "Choose without asking anyone else.",
        "scorpio": "Trust before you have proof.",
        "sagittarius": "Stay 10% longer than comfortable.",
        "capricorn": "Stop before you're finished.",
        "aquarius": "Feel before you analyze.",
        "pisces": "Say no to something that feels like yours."
    }
    
    return {
        "todays_truth": today_truths.get(sun, "Something familiar will show up again."),
        "what_rewards": rewards.get(sun, "Awareness before action."),
        "what_backfires": backfires.get(sun, "Running the pattern on autopilot."),
        "one_move": moves.get(sun, "Pause before repeating.")
    }


# =============================================================================
# MAIN COMPUTE FUNCTION
# =============================================================================

def compute_astrology_insight_first(
    sun_sign: str,
    moon_sign: str,
    rising_sign: str,
    chart_data: Optional[Dict] = None,
    transit_data: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Compute the complete Astrology Insight First structure.
    
    Returns V1 structure:
    1. continuation
    2. core_truth
    3. echo
    4. how_this_shows_up
    5. when_this_backfires
    6. genius
    7. what_this_costs
    8. one_shift
    9. why_showing_up (proof layer - for collapsible)
    10. astrology_details (raw data - for collapsible)
    11. today (today tab content)
    """
    sun = (sun_sign or "aries").lower()
    moon = (moon_sign or "aries").lower()
    rising = (rising_sign or "aries").lower()
    
    # Generate all layers
    continuation = generate_continuation_line()
    core_truth = generate_core_truth(sun, moon, rising)
    echo = generate_echo_line()
    cross_link = generate_cross_link_line()
    how_shows_up = generate_how_this_shows_up(sun, moon)
    when_backfires = generate_when_backfires(sun)
    genius = generate_genius_line(sun)
    costs = generate_costs(sun)
    one_shift = generate_one_shift(sun)
    today = generate_today_insight(sun)
    
    # Build proof layer (collapsible)
    why_showing_up = {
        "summary": f"This pattern gets stronger when pressure hits before clarity lands. Your current timing is amplifying the {sun.title()} tendency to {SUN_BEHAVIORS.get(sun, ['move'])[0].lower()}.",
        "emphasis": f"Current emphasis: {sun.title()} Sun patterns",
        "area": "Main life area activated: identity / direction",
        "pressure": "Current pressure: recognition before resolution"
    }
    
    # Build raw astrology details (collapsible)
    astrology_details = {
        "sun": f"{sun.title()} Sun",
        "moon": f"{moon.title()} Moon", 
        "rising": f"{rising.title()} Rising"
    }
    
    # Add chart data if available
    if chart_data:
        planets = chart_data.get("planets", {})
        for planet, data in planets.items():
            if planet not in ["Sun", "Moon"]:
                sign = data.get("sign", "Unknown")
                astrology_details[planet.lower()] = f"{sign} {planet}"
    
    return {
        "success": True,
        # V1 Structure: Continuation → Core → Echo → Cross Link → Memory → Shows → Backfires → Genius → Cost → Shift
        "continuation": continuation,
        "core_truth": core_truth,
        "echo": echo,
        "cross_link": cross_link,
        # MEMORY layer (V1) - Placeholder, filled by API when real history exists
        # Structure: { memory_line, recurrence_count, last_seen_at, memory_state }
        "memory": None,  # Will be populated with real data via get_pattern_memory_v1
        "how_this_shows_up": how_shows_up,
        "when_this_backfires": when_backfires,
        "genius": genius,
        "what_this_costs": costs,
        "one_shift": one_shift,
        # Collapsible proof layers
        "why_showing_up": why_showing_up,
        "astrology_details": astrology_details,
        # Today tab
        "today": today,
        # Core placements for reference
        "core_placements": {
            "sun": sun.title(),
            "moon": moon.title(),
            "rising": rising.title()
        }
    }
