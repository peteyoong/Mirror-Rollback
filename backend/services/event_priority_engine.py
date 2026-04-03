"""Event Priority Engine V1.0 - Transit Salience System

CORE RULE: Major celestial events MUST dominate theme generation.
If Full Moon is happening, user MUST feel: "Oh — THAT'S why everything feels heightened"

PRIORITY TIERS:
- Tier 1 (DOMINANT): Full Moon, New Moon, Eclipses, exact hits to Sun/Moon/ASC/MC
- Tier 2 (STRONG): Jupiter/Saturn/Pluto aspects, tight orbs (<2°)
- Tier 3 (SUPPORTING): Minor aspects, wider orbs, fast-moving transits

OUTPUT HIERARCHY:
1. Main Event (Full Moon / New Moon / Eclipse)
2. Supporting transits
3. Personal interaction
4. Felt experience
5. Action
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# PRIORITY TIER DEFINITIONS
# =============================================================================

class PriorityTier(str, Enum):
    TIER_1_DOMINANT = "tier_1_dominant"
    TIER_2_STRONG = "tier_2_strong"
    TIER_3_SUPPORTING = "tier_3_supporting"


@dataclass
class PrioritizedEvent:
    """A prioritized celestial event with salience score."""
    event_type: str  # "full_moon", "new_moon", "eclipse_solar", etc.
    tier: PriorityTier
    salience: float  # 0-1, how dominant this event is
    sign: Optional[str]  # Zodiac sign if applicable
    explicit_name: str  # "Full Moon in Libra", "New Moon in Aries"
    headline: str  # User-facing headline
    what_it_means: str  # Behavioral translation
    felt_texture: List[str]  # Concrete felt experiences
    action: str  # What to do
    days_until: int  # Days until/since exact
    is_exact: bool  # True if within 24h window


# =============================================================================
# TIER 1: DOMINANT EVENTS (MUST GENERATE THEME)
# =============================================================================

TIER_1_EVENTS = {
    "full_moon", "new_moon", 
    "eclipse_solar", "eclipse_lunar",
    "sun_exact", "moon_exact", "asc_exact", "mc_exact"
}

# Full Moon themed content by zodiac sign
FULL_MOON_BY_SIGN = {
    "Aries": {
        "headline": "Full Moon in Aries — Peak Urgency",
        "what_it_means": "Everything feels urgent. The impulse to act is peaking.",
        "felt_texture": [
            "Restlessness that won't settle until something moves",
            "Irritability with anyone who slows you down",
            "The body wants to DO something, even if the mind doesn't know what",
        ],
        "action": "Move one thing forward — but don't burn bridges in the heat",
        "theme_line": "The urge to act is real. But the clarity about WHERE to act may be 24 hours behind."
    },
    "Taurus": {
        "headline": "Full Moon in Taurus — Peak Stubbornness",
        "what_it_means": "You're digging in. Something feels non-negotiable.",
        "felt_texture": [
            "Physical tension when asked to compromise",
            "Needing comfort that no one else can give you right now",
            "The body wants to hold onto what feels safe",
        ],
        "action": "Notice what you're gripping — and ask if it's worth the tension",
        "theme_line": "You're holding something tightly. Ask if it's security — or just fear of change."
    },
    "Gemini": {
        "headline": "Full Moon in Gemini — Peak Mental Noise",
        "what_it_means": "The mind is LOUD. Too many options, not enough clarity.",
        "felt_texture": [
            "Overthinking every possible scenario",
            "Starting conversations you can't finish",
            "Scattered energy — wanting to do everything at once",
        ],
        "action": "Write it down. Get it out of your head and onto paper.",
        "theme_line": "The noise is real. But the answer won't come from more thinking — it'll come from less."
    },
    "Cancer": {
        "headline": "Full Moon in Cancer — Peak Emotional Intensity",
        "what_it_means": "Feelings are at maximum. Old needs are surfacing.",
        "felt_texture": [
            "Wanting to be held but not wanting to ask",
            "Old family patterns suddenly feeling fresh",
            "Tears for no obvious reason",
        ],
        "action": "Let yourself feel it without needing to fix it",
        "theme_line": "The feelings are real. But they're not all about today — some are from way back."
    },
    "Leo": {
        "headline": "Full Moon in Leo — Peak Need for Recognition",
        "what_it_means": "You want to be SEEN. The need for appreciation is peaking.",
        "felt_texture": [
            "Frustration when your efforts go unacknowledged",
            "Wanting to perform, even when exhausted",
            "Pride colliding with vulnerability",
        ],
        "action": "Acknowledge yourself first — don't wait for others",
        "theme_line": "The need to be seen is valid. But if you're performing for approval, you'll stay hungry."
    },
    "Virgo": {
        "headline": "Full Moon in Virgo — Peak Self-Criticism",
        "what_it_means": "You're seeing every flaw. The perfectionist is running the show.",
        "felt_texture": [
            "Finding fault in everything — including yourself",
            "Anxiety about things being 'good enough'",
            "The urge to fix everything at once",
        ],
        "action": "Name three things that are working — before touching what's broken",
        "theme_line": "You're seeing clearly. But clarity isn't the same as judgment."
    },
    "Libra": {
        "headline": "Full Moon in Libra — Peak Relationship Tension",
        "what_it_means": "Something in your relationships is coming to a head.",
        "felt_texture": [
            "Wanting harmony but feeling the imbalance",
            "Resentment you've been swallowing",
            "The other person's needs feeling heavy",
        ],
        "action": "Say what you've been editing. The peace you're keeping isn't peaceful.",
        "theme_line": "Balance isn't about keeping everyone happy. It's about naming the truth."
    },
    "Scorpio": {
        "headline": "Full Moon in Scorpio — Peak Intensity",
        "what_it_means": "Deep feelings are surfacing. Something wants to be transformed.",
        "felt_texture": [
            "Intensity in small moments",
            "Obsessive thoughts circling",
            "Old wounds suddenly fresh",
        ],
        "action": "Let something die that's already gone. Stop resuscitating it.",
        "theme_line": "This intensity is here to clear something. But you have to let go first."
    },
    "Sagittarius": {
        "headline": "Full Moon in Sagittarius — Peak Restlessness",
        "what_it_means": "You want OUT. The walls feel too close.",
        "felt_texture": [
            "Boredom with everything familiar",
            "Wanting to escape responsibilities",
            "Big promises without follow-through",
        ],
        "action": "Expand your perspective before expanding your commitments",
        "theme_line": "The restlessness is pointing at something. But running won't fix what needs facing."
    },
    "Capricorn": {
        "headline": "Full Moon in Capricorn — Peak Pressure",
        "what_it_means": "The weight of responsibility is peaking. Something has to give.",
        "felt_texture": [
            "Exhaustion that rest doesn't fix",
            "The urge to push through anyway",
            "Guilt when you stop working",
        ],
        "action": "Put something down. You're carrying weight that isn't yours.",
        "theme_line": "Success without rest isn't sustainable. Something needs to be released."
    },
    "Aquarius": {
        "headline": "Full Moon in Aquarius — Peak Detachment",
        "what_it_means": "You're distancing from your own feelings. Something is being intellectualized.",
        "felt_texture": [
            "Analyzing feelings instead of feeling them",
            "Wanting to fix systems instead of sitting with discomfort",
            "Feeling alien even around familiar people",
        ],
        "action": "Drop into your body. The answer isn't in your head.",
        "theme_line": "You're smart enough to explain away your feelings. But that's not the same as processing them."
    },
    "Pisces": {
        "headline": "Full Moon in Pisces — Peak Sensitivity",
        "what_it_means": "Boundaries are dissolving. You're feeling everything.",
        "felt_texture": [
            "Not knowing what's yours vs what you're absorbing",
            "Dreams more vivid than usual",
            "Wanting to escape into anything but reality",
        ],
        "action": "Ground yourself physically before making any decisions",
        "theme_line": "What you're feeling may not be entirely yours. Discern before you react."
    },
}

# New Moon themed content by zodiac sign
NEW_MOON_BY_SIGN = {
    "Aries": {
        "headline": "New Moon in Aries — Fresh Start Energy",
        "what_it_means": "Something new wants to begin. A fresh impulse is forming.",
        "felt_texture": [
            "Excitement without clarity on direction",
            "Wanting to start something but not knowing what",
            "Energy rising with nowhere to go yet",
        ],
        "action": "Plant a seed — don't expect the harvest yet",
        "theme_line": "The energy to begin is here. But the clarity about WHAT will take a few days."
    },
    "Taurus": {
        "headline": "New Moon in Taurus — Grounding a New Foundation",
        "what_it_means": "Something solid is taking root. A new stability is forming.",
        "felt_texture": [
            "Craving simplicity and stillness",
            "Wanting to build something lasting",
            "Body asking for rest before action",
        ],
        "action": "Decide what you actually value — then build from there",
        "theme_line": "This is slow-building energy. Trust the pace."
    },
    "Gemini": {
        "headline": "New Moon in Gemini — New Ideas Forming",
        "what_it_means": "A new perspective is emerging. Mental clarity coming.",
        "felt_texture": [
            "Curiosity returning after feeling stuck",
            "Multiple ideas competing for attention",
            "Wanting to learn something new",
        ],
        "action": "Follow your curiosity — don't commit to the first answer",
        "theme_line": "The answers are coming. Stay curious, not conclusive."
    },
    "Cancer": {
        "headline": "New Moon in Cancer — Emotional Reset",
        "what_it_means": "A new emotional chapter is beginning. Home and security in focus.",
        "felt_texture": [
            "Wanting to nest and withdraw",
            "Needs feeling raw and exposed",
            "Old patterns asking to be seen differently",
        ],
        "action": "Create safety before taking external action",
        "theme_line": "Let yourself feel what you need — without apologizing for it."
    },
    "Leo": {
        "headline": "New Moon in Leo — Creative Rebirth",
        "what_it_means": "New creative energy is forming. A fresh expression wants to emerge.",
        "felt_texture": [
            "Wanting to be seen for something new",
            "Creative urges without clear output yet",
            "Heart opening after feeling closed",
        ],
        "action": "Create something just for yourself — before performing it for others",
        "theme_line": "The spark is returning. Don't rush to show it off."
    },
    "Virgo": {
        "headline": "New Moon in Virgo — New Systems Forming",
        "what_it_means": "A better approach is emerging. Health and routine in focus.",
        "felt_texture": [
            "Wanting to reorganize everything",
            "Small improvements suddenly feeling possible",
            "Body asking for different care",
        ],
        "action": "Start one new habit — not ten",
        "theme_line": "The small changes matter more than the big plans right now."
    },
    "Libra": {
        "headline": "New Moon in Libra — New Relationship Chapter",
        "what_it_means": "Something is shifting in how you relate. Balance being recalibrated.",
        "felt_texture": [
            "Wanting harmony you haven't been feeling",
            "Relationships asking for a reset",
            "Compromise feeling more possible",
        ],
        "action": "Have the conversation you've been avoiding — gently",
        "theme_line": "A new kind of balance is possible. But it requires honesty first."
    },
    "Scorpio": {
        "headline": "New Moon in Scorpio — Deep Reset",
        "what_it_means": "Something is transforming from the inside. A rebirth is seeding.",
        "felt_texture": [
            "Intensity without clear direction",
            "Old patterns surfacing to be released",
            "Power dynamics in focus",
        ],
        "action": "Let something go completely before adding anything new",
        "theme_line": "This is death-and-rebirth energy. Don't skip the death part."
    },
    "Sagittarius": {
        "headline": "New Moon in Sagittarius — New Vision Forming",
        "what_it_means": "A bigger picture is emerging. New beliefs taking shape.",
        "felt_texture": [
            "Optimism returning after doubt",
            "Wanting to learn or travel or expand",
            "Old beliefs feeling outdated",
        ],
        "action": "Update your vision before updating your plans",
        "theme_line": "What you believed last year might not be what you believe now. That's growth."
    },
    "Capricorn": {
        "headline": "New Moon in Capricorn — New Ambition Forming",
        "what_it_means": "A new goal is crystallizing. Structure being rebuilt.",
        "felt_texture": [
            "Wanting to achieve something concrete",
            "Old goals feeling irrelevant",
            "Ready to do the work — but not sure on what",
        ],
        "action": "Define success differently than you used to",
        "theme_line": "The ambition is returning. But aim it at what actually matters to you now."
    },
    "Aquarius": {
        "headline": "New Moon in Aquarius — New Vision for the Future",
        "what_it_means": "Something unconventional is calling. Change is seeding.",
        "felt_texture": [
            "Feeling different from the crowd",
            "Wanting to break patterns",
            "Future-focused thinking",
        ],
        "action": "Honor what makes you different — don't suppress it",
        "theme_line": "The future wants something new from you. Stop trying to fit the old mold."
    },
    "Pisces": {
        "headline": "New Moon in Pisces — Spiritual Reset",
        "what_it_means": "Something is dissolving to make space. Intuition heightening.",
        "felt_texture": [
            "Dreams feeling significant",
            "Boundaries blurring",
            "Old patterns losing their grip",
        ],
        "action": "Trust your intuition more than your logic right now",
        "theme_line": "Something is ending so something new can form. You don't have to understand it yet."
    },
}

# Eclipse specific content
ECLIPSE_CONTENT = {
    "solar": {
        "headline_template": "{type} Solar Eclipse — Portal Event",
        "what_it_means": "This is not a normal day. A major life chapter is shifting.",
        "felt_texture": [
            "Sense that something irreversible is happening",
            "Old identity patterns falling away",
            "Feeling destabilized but also liberated",
        ],
        "action": "Don't force decisions. Let the eclipse energy move through first.",
        "theme_line": "What changes during an eclipse doesn't change back. Let it happen."
    },
    "lunar": {
        "headline_template": "{type} Lunar Eclipse — Emotional Release",
        "what_it_means": "Deep emotional material is being illuminated and released.",
        "felt_texture": [
            "Old feelings surfacing without warning",
            "Relationships showing hidden dynamics",
            "What you've suppressed demanding attention",
        ],
        "action": "Let the emotions move through. Don't try to control the release.",
        "theme_line": "What surfaces now was always there. Now it can finally leave."
    },
}


# =============================================================================
# TIER 2: STRONG DRIVERS
# =============================================================================

TIER_2_PLANETS = {"Jupiter", "Saturn", "Pluto", "Uranus", "Neptune"}
TIER_2_ORB_THRESHOLD = 2.0  # degrees - tight aspects


# =============================================================================
# MOON SIGN CALCULATION (Approximate)
# =============================================================================

def get_moon_sign_approximate(dt: datetime) -> str:
    """
    Get approximate moon sign based on lunar cycle position.
    Uses the known new moon positions as reference.
    """
    # Known new moon dates and their signs for 2025-2026
    # This is a simplified lookup - in production, use swisseph
    new_moon_signs = [
        (datetime(2025, 1, 29, tzinfo=timezone.utc), "Aquarius"),
        (datetime(2025, 2, 28, tzinfo=timezone.utc), "Pisces"),
        (datetime(2025, 3, 29, tzinfo=timezone.utc), "Aries"),
        (datetime(2025, 4, 27, tzinfo=timezone.utc), "Taurus"),
        (datetime(2025, 5, 27, tzinfo=timezone.utc), "Gemini"),
        (datetime(2025, 6, 25, tzinfo=timezone.utc), "Cancer"),
        (datetime(2025, 7, 24, tzinfo=timezone.utc), "Leo"),
        (datetime(2025, 8, 23, tzinfo=timezone.utc), "Virgo"),
        (datetime(2025, 9, 21, tzinfo=timezone.utc), "Libra"),
        (datetime(2025, 10, 21, tzinfo=timezone.utc), "Scorpio"),
        (datetime(2025, 11, 20, tzinfo=timezone.utc), "Sagittarius"),
        (datetime(2025, 12, 20, tzinfo=timezone.utc), "Capricorn"),
        (datetime(2026, 1, 18, tzinfo=timezone.utc), "Capricorn"),
        (datetime(2026, 2, 17, tzinfo=timezone.utc), "Aquarius"),
        (datetime(2026, 3, 19, tzinfo=timezone.utc), "Pisces"),
        (datetime(2026, 4, 17, tzinfo=timezone.utc), "Aries"),
        (datetime(2026, 5, 16, tzinfo=timezone.utc), "Taurus"),
        (datetime(2026, 6, 15, tzinfo=timezone.utc), "Gemini"),
        (datetime(2026, 7, 14, tzinfo=timezone.utc), "Cancer"),
        (datetime(2026, 8, 12, tzinfo=timezone.utc), "Leo"),
        (datetime(2026, 9, 11, tzinfo=timezone.utc), "Virgo"),
        (datetime(2026, 10, 10, tzinfo=timezone.utc), "Libra"),
        (datetime(2026, 11, 9, tzinfo=timezone.utc), "Scorpio"),
        (datetime(2026, 12, 8, tzinfo=timezone.utc), "Sagittarius"),
    ]
    
    # Zodiac signs in order
    ZODIAC = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
              "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    
    # Find the most recent new moon
    closest_nm = None
    closest_sign = "Aries"
    
    for nm_date, nm_sign in new_moon_signs:
        if nm_date <= dt:
            closest_nm = nm_date
            closest_sign = nm_sign
    
    if not closest_nm:
        return "Aries"
    
    # Calculate days since new moon
    days_since = (dt - closest_nm).total_seconds() / 86400
    
    # Moon moves ~13° per day, changes sign every ~2.5 days
    signs_moved = int(days_since / 2.5)
    
    current_idx = ZODIAC.index(closest_sign)
    new_idx = (current_idx + signs_moved) % 12
    
    return ZODIAC[new_idx]


def get_full_moon_sign(new_moon_sign: str) -> str:
    """Full moon is opposite the new moon sign."""
    ZODIAC = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
              "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    
    idx = ZODIAC.index(new_moon_sign)
    opposite_idx = (idx + 6) % 12
    return ZODIAC[opposite_idx]


# =============================================================================
# MAIN PRIORITY ENGINE
# =============================================================================

def classify_transit_tier(
    transit: Dict[str, Any],
    moon_data: Dict[str, Any],
    eclipse_data: Dict[str, Any]
) -> PriorityTier:
    """
    Classify a transit into priority tiers.
    
    Tier 1: Full Moon, New Moon, Eclipses, exact hits to Sun/Moon/ASC/MC
    Tier 2: Jupiter/Saturn/Pluto aspects, tight orbs (<2°)
    Tier 3: Everything else
    """
    planet = transit.get("planet", "")
    natal_planet = transit.get("natal_planet", "")
    orb = transit.get("orb", 8.0)
    
    # Tier 1: Check for dominant events
    if moon_data.get("is_full_moon") or moon_data.get("is_new_moon"):
        return PriorityTier.TIER_1_DOMINANT
    
    if eclipse_data.get("in_eclipse_season") and eclipse_data.get("days_until", 30) <= 3:
        return PriorityTier.TIER_1_DOMINANT
    
    # Exact hits to personal points
    if natal_planet in ["Sun", "Moon", "Ascendant", "MC", "Midheaven"] and orb <= 2:
        return PriorityTier.TIER_1_DOMINANT
    
    # Tier 2: Strong drivers
    if planet in TIER_2_PLANETS or natal_planet in TIER_2_PLANETS:
        return PriorityTier.TIER_2_STRONG
    
    if orb <= TIER_2_ORB_THRESHOLD:
        return PriorityTier.TIER_2_STRONG
    
    # Tier 3: Supporting
    return PriorityTier.TIER_3_SUPPORTING


def detect_dominant_event(
    moon_data: Dict[str, Any],
    eclipse_data: Dict[str, Any],
    dt: Optional[datetime] = None
) -> Optional[PrioritizedEvent]:
    """
    Detect if a Tier 1 dominant event is active.
    Returns the event with full contextual data for theme generation.
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    
    # Check for eclipse (highest priority)
    if eclipse_data.get("in_eclipse_season"):
        days_until = eclipse_data.get("days_until", 30)
        if abs(days_until) <= 3:
            eclipse_type = eclipse_data.get("eclipse_type", "solar")
            eclipse_name = eclipse_data.get("eclipse_name", "Eclipse")
            content = ECLIPSE_CONTENT.get(eclipse_type, ECLIPSE_CONTENT["solar"])
            
            return PrioritizedEvent(
                event_type=f"eclipse_{eclipse_type}",
                tier=PriorityTier.TIER_1_DOMINANT,
                salience=0.98,
                sign=get_moon_sign_approximate(dt),
                explicit_name=f"{eclipse_name}",
                headline=content["headline_template"].format(type=eclipse_name.split()[0]),
                what_it_means=content["what_it_means"],
                felt_texture=content["felt_texture"],
                action=content["action"],
                days_until=int(days_until),
                is_exact=abs(days_until) < 1
            )
    
    # Check for Full Moon
    if moon_data.get("is_full_moon") or (moon_data.get("days_to_full", 30) <= 1.5 and moon_data.get("phase_name") in ["Waxing Gibbous", "Full Moon"]):
        moon_sign = get_moon_sign_approximate(dt)
        content = FULL_MOON_BY_SIGN.get(moon_sign, FULL_MOON_BY_SIGN["Aries"])
        
        days_to_full = moon_data.get("days_to_full", 0)
        is_exact = moon_data.get("is_full_moon", False) or days_to_full <= 0.5
        
        return PrioritizedEvent(
            event_type="full_moon",
            tier=PriorityTier.TIER_1_DOMINANT,
            salience=0.95 if is_exact else 0.88,
            sign=moon_sign,
            explicit_name=f"Full Moon in {moon_sign}",
            headline=content["headline"],
            what_it_means=content["what_it_means"],
            felt_texture=content["felt_texture"],
            action=content["action"],
            days_until=int(days_to_full) if days_to_full > 0 else 0,
            is_exact=is_exact
        )
    
    # Check for New Moon
    if moon_data.get("is_new_moon") or moon_data.get("cycle_days", 30) <= 1.5:
        moon_sign = get_moon_sign_approximate(dt)
        content = NEW_MOON_BY_SIGN.get(moon_sign, NEW_MOON_BY_SIGN["Aries"])
        
        cycle_days = moon_data.get("cycle_days", 0)
        is_exact = moon_data.get("is_new_moon", False) or cycle_days <= 0.5
        
        return PrioritizedEvent(
            event_type="new_moon",
            tier=PriorityTier.TIER_1_DOMINANT,
            salience=0.93 if is_exact else 0.85,
            sign=moon_sign,
            explicit_name=f"New Moon in {moon_sign}",
            headline=content["headline"],
            what_it_means=content["what_it_means"],
            felt_texture=content["felt_texture"],
            action=content["action"],
            days_until=0,
            is_exact=is_exact
        )
    
    # Check for approaching Full Moon (within 3 days)
    days_to_full = moon_data.get("days_to_full", 30)
    if days_to_full <= 3:
        # Calculate what sign the moon will be in at full moon
        # Full moon is roughly days_to_full days away
        future_dt = dt + __import__('datetime').timedelta(days=days_to_full)
        moon_sign = get_moon_sign_approximate(future_dt)
        content = FULL_MOON_BY_SIGN.get(moon_sign, FULL_MOON_BY_SIGN["Aries"])
        
        return PrioritizedEvent(
            event_type="full_moon_approaching",
            tier=PriorityTier.TIER_1_DOMINANT,
            salience=0.80 - (days_to_full * 0.05),  # Decreases as we get further away
            sign=moon_sign,
            explicit_name=f"Full Moon in {moon_sign} approaching",
            headline=f"Full Moon in {moon_sign} in {int(days_to_full)} day{'s' if days_to_full > 1 else ''}",
            what_it_means=f"Intensity is building toward a peak. {content['what_it_means']}",
            felt_texture=[f"Building toward: {ft}" for ft in content["felt_texture"][:2]],
            action=f"Prepare: {content['action']}",
            days_until=int(days_to_full),
            is_exact=False
        )
    
    return None


def prioritize_transits(
    transits: List[Dict[str, Any]],
    moon_data: Dict[str, Any],
    eclipse_data: Dict[str, Any]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Sort transits into priority tiers.
    
    Returns:
        {
            "tier_1": [...],  # Dominant events
            "tier_2": [...],  # Strong drivers
            "tier_3": [...],  # Supporting signals
        }
    """
    result = {
        "tier_1": [],
        "tier_2": [],
        "tier_3": [],
    }
    
    for transit in transits:
        tier = classify_transit_tier(transit, moon_data, eclipse_data)
        transit["priority_tier"] = tier.value
        
        if tier == PriorityTier.TIER_1_DOMINANT:
            result["tier_1"].append(transit)
        elif tier == PriorityTier.TIER_2_STRONG:
            result["tier_2"].append(transit)
        else:
            result["tier_3"].append(transit)
    
    return result


def generate_event_priority_output(
    dominant_event: Optional[PrioritizedEvent],
    prioritized_transits: Dict[str, List[Dict[str, Any]]],
    timeframe: str = "today"
) -> Dict[str, Any]:
    """
    Generate the prioritized output structure.
    
    If Tier 1 event exists → theme MUST derive from it.
    
    OUTPUT HIERARCHY:
    1. Main Event (Full Moon / New Moon / Eclipse)
    2. Supporting transits
    3. Personal interaction
    4. Felt experience
    5. Action
    """
    if dominant_event:
        # TIER 1 ACTIVE — Theme derives from dominant event
        timeframe_modifier = ""
        if timeframe == "week":
            timeframe_modifier = " This energy colors the entire week."
        elif timeframe == "month":
            timeframe_modifier = " This is a key moment in your month's arc."
        
        return {
            "has_dominant_event": True,
            "dominant_event": {
                "type": dominant_event.event_type,
                "explicit_name": dominant_event.explicit_name,
                "sign": dominant_event.sign,
                "is_exact": dominant_event.is_exact,
                "days_until": dominant_event.days_until,
                "salience": dominant_event.salience,
            },
            "main_event": {
                "headline": dominant_event.headline,
                "what_it_means": dominant_event.what_it_means + timeframe_modifier,
            },
            "supporting_transits": prioritized_transits.get("tier_2", [])[:3],
            "felt_texture": dominant_event.felt_texture,
            "action": dominant_event.action,
            "tier_summary": {
                "tier_1_count": 1,
                "tier_2_count": len(prioritized_transits.get("tier_2", [])),
                "tier_3_count": len(prioritized_transits.get("tier_3", [])),
            }
        }
    else:
        # No dominant event — use Tier 2 drivers or default
        tier_2 = prioritized_transits.get("tier_2", [])
        
        if tier_2:
            # Use strongest Tier 2 transit as theme source
            primary = tier_2[0]
            return {
                "has_dominant_event": False,
                "dominant_event": None,
                "main_event": {
                    "headline": f"{primary.get('planet', 'Transit')} Energy Active",
                    "what_it_means": f"Strong {primary.get('planet', 'planetary')} influence shaping today.",
                },
                "supporting_transits": tier_2[1:4],
                "felt_texture": [],
                "action": "Stay responsive to the energy without forcing outcomes.",
                "tier_summary": {
                    "tier_1_count": 0,
                    "tier_2_count": len(tier_2),
                    "tier_3_count": len(prioritized_transits.get("tier_3", [])),
                }
            }
        else:
            # Quiet day — Tier 3 only
            return {
                "has_dominant_event": False,
                "dominant_event": None,
                "main_event": {
                    "headline": "Subtle Shifts",
                    "what_it_means": "No major events dominating. Smaller adjustments matter.",
                },
                "supporting_transits": prioritized_transits.get("tier_3", [])[:3],
                "felt_texture": [],
                "action": "Notice the small signals. They're preparing you for what's next.",
                "tier_summary": {
                    "tier_1_count": 0,
                    "tier_2_count": 0,
                    "tier_3_count": len(prioritized_transits.get("tier_3", [])),
                }
            }


# =============================================================================
# PUBLIC API
# =============================================================================

def compute_event_priority(
    transits: List[Dict[str, Any]],
    moon_data: Dict[str, Any],
    eclipse_data: Dict[str, Any],
    timeframe: str = "today",
    dt: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Main entry point: Compute event priority for Astrology Today.
    
    CRITICAL: If Tier 1 event exists, theme MUST derive from it.
    
    Args:
        transits: List of transit aspects
        moon_data: Moon phase data from field_signals
        eclipse_data: Eclipse data from field_signals
        timeframe: "today" | "week" | "month"
        dt: Datetime for calculation (defaults to now)
        
    Returns:
        Complete prioritized output structure
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    
    # Step 1: Detect dominant Tier 1 event
    dominant_event = detect_dominant_event(moon_data, eclipse_data, dt)
    
    # Step 2: Prioritize all transits
    prioritized_transits = prioritize_transits(transits, moon_data, eclipse_data)
    
    # Step 3: Generate output structure
    output = generate_event_priority_output(dominant_event, prioritized_transits, timeframe)
    
    # Add metadata
    output["computed_at"] = dt.isoformat()
    output["timeframe"] = timeframe
    output["moon_phase"] = moon_data.get("phase_name", "Unknown")
    output["days_to_full"] = moon_data.get("days_to_full", 0)
    output["days_to_new"] = moon_data.get("days_to_new", 0)
    
    logger.info(f"[EventPriority] Dominant event: {dominant_event.event_type if dominant_event else 'None'}, "
                f"Tier counts: T1={output['tier_summary']['tier_1_count']}, "
                f"T2={output['tier_summary']['tier_2_count']}, "
                f"T3={output['tier_summary']['tier_3_count']}")
    
    return output
