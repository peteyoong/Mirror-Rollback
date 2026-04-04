"""Relationship Insight Engine V1.0

Generates 1:1 dynamic reflections that help the user understand:
1) What is happening between them
2) What they need to shift in themselves

CRITICAL RULES:
- Always center the USER, not the other person
- Never suggest what the other person should do
- Do not blame, diagnose, or fix the other person
- Use grounded, real-life language
- Make it feel specific, relational, and slightly confronting

STRUCTURE:
1. ESSENCE - What they are / how they move (1-2 lines)
2. FRICTION - Where it clashes with you (1-2 lines)
3. TENSION - What happens between you (1-2 lines)
4. YOUR SHIFT - What YOU need to adjust (2-3 lines) - MOST IMPORTANT
5. GIFT - What unlocks if you do this well (1-2 lines)
6. TRY THIS - ONE specific action

TONE: Direct, grounded, human. Slight edge is okay.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import hashlib

logger = logging.getLogger(__name__)


# =============================================================================
# CORE DYNAMIC PATTERNS
# =============================================================================

# How different types naturally move/operate
ESSENCE_PATTERNS = {
    # Speed patterns
    "slow_processor": [
        "They take time to feel what's true before moving.",
        "They need to sit with things before they know.",
        "They process by slowing down, not speeding up.",
    ],
    "fast_mover": [
        "They move when something feels clear. They don't wait.",
        "They trust their first read and act on it.",
        "Hesitation frustrates them. Clarity comes through motion.",
    ],
    # Emotional patterns
    "emotionally_guarded": [
        "They don't show everything. That's not coldness—it's protection.",
        "They feel deeply but share selectively.",
        "You won't always know what's happening inside them.",
    ],
    "emotionally_open": [
        "They lead with how they feel. It's not a choice—it's how they're built.",
        "Their emotions are visible, even when they try to hide them.",
        "They process out loud. Silence makes things worse for them.",
    ],
    # Decision patterns
    "needs_certainty": [
        "They need to know before they move.",
        "Ambiguity makes them contract, not expand.",
        "They want the map before they walk.",
    ],
    "comfortable_with_uncertainty": [
        "They're okay not knowing. That's where they find freedom.",
        "They trust the path will clarify as they walk.",
        "Too much planning feels like a cage to them.",
    ],
    # Control patterns
    "needs_control": [
        "They need to feel like they're steering.",
        "Chaos doesn't excite them—it destabilizes them.",
        "They hold tight because loose feels dangerous.",
    ],
    "goes_with_flow": [
        "They adapt. That's their superpower and their blind spot.",
        "They don't grip—they adjust.",
        "Control isn't their comfort zone.",
    ],
    # Communication patterns
    "direct_communicator": [
        "They say what they mean. Don't read between the lines.",
        "Subtlety isn't their language.",
        "If they haven't said it, they probably haven't thought it yet.",
    ],
    "indirect_communicator": [
        "They communicate through implication, not declaration.",
        "What they don't say matters as much as what they do.",
        "You have to read the subtext with them.",
    ],
    # Conflict patterns
    "avoids_conflict": [
        "They'd rather keep peace than be right.",
        "Confrontation costs them more than it costs you.",
        "They absorb tension instead of expressing it.",
    ],
    "engages_conflict": [
        "They don't shy from friction. Sometimes they seek it.",
        "Tension clarifies things for them.",
        "They'd rather fight than fake harmony.",
    ],
}

# Friction patterns between different types
FRICTION_PATTERNS = {
    ("fast_mover", "slow_processor"): [
        "You move fast when something feels clear.\nThey slow down when something feels uncertain.",
        "Your clarity feels like pressure to them.\nTheir pause feels like resistance to you.",
    ],
    ("slow_processor", "fast_mover"): [
        "You need time to feel what's true.\nThey've already decided and moved on.",
        "Your process feels like stalling to them.\nTheir speed feels like dismissal to you.",
    ],
    ("emotionally_open", "emotionally_guarded"): [
        "You show what you feel.\nThey keep what they feel.",
        "Your openness feels like exposure to them.\nTheir reserve feels like rejection to you.",
    ],
    ("emotionally_guarded", "emotionally_open"): [
        "You protect what you feel.\nThey broadcast what they feel.",
        "Their intensity can overwhelm you.\nYour stillness can confuse them.",
    ],
    ("needs_certainty", "comfortable_with_uncertainty"): [
        "You need the plan.\nThey need the room to discover.",
        "Your structure feels like constraint to them.\nTheir openness feels like chaos to you.",
    ],
    ("comfortable_with_uncertainty", "needs_certainty"): [
        "You're okay not knowing.\nThey need to know before they can relax.",
        "Their questions feel like doubt to you.\nYour ease feels like carelessness to them.",
    ],
    ("needs_control", "goes_with_flow"): [
        "You hold the wheel.\nThey let the current carry.",
        "Your grip feels heavy to them.\nTheir looseness feels irresponsible to you.",
    ],
    ("goes_with_flow", "needs_control"): [
        "You adapt and adjust.\nThey plan and execute.",
        "Their rigidity frustrates you.\nYour flexibility worries them.",
    ],
    ("direct_communicator", "indirect_communicator"): [
        "You say it straight.\nThey imply and suggest.",
        "Your directness can land hard on them.\nTheir subtlety can feel evasive to you.",
    ],
    ("indirect_communicator", "direct_communicator"): [
        "You communicate in layers.\nThey communicate in statements.",
        "Their bluntness can feel harsh.\nYour indirectness can feel unclear.",
    ],
    ("avoids_conflict", "engages_conflict"): [
        "You keep the peace.\nThey surface the problem.",
        "Their confrontation feels aggressive to you.\nYour avoidance feels passive to them.",
    ],
    ("engages_conflict", "avoids_conflict"): [
        "You address things directly.\nThey smooth things over.",
        "Their deflection frustrates you.\nYour intensity overwhelms them.",
    ],
}

# Tension loops - what happens between you
TENSION_LOOPS = {
    ("fast_mover", "slow_processor"): [
        "The more you push for movement, the more they pull back.",
        "You speed up. They dig in. Nobody moves.",
        "Your urgency creates their resistance.",
    ],
    ("slow_processor", "fast_mover"): [
        "The more you pause, the more impatient they become.",
        "You need time. They need action. The gap widens.",
        "Your slowness triggers their frustration. Their frustration triggers your shutdown.",
    ],
    ("emotionally_open", "emotionally_guarded"): [
        "You reach. They retreat. You reach harder.",
        "Your openness asks for matching. They can't give it the way you want.",
        "The more you express, the less they show.",
    ],
    ("emotionally_guarded", "emotionally_open"): [
        "You hold back. They push in. You hold back more.",
        "Their need for connection feels like demand.",
        "Your protection triggers their pursuit.",
    ],
    ("needs_certainty", "comfortable_with_uncertainty"): [
        "You ask for plans. They offer possibilities. Neither feels heard.",
        "Your need to know meets their need to explore.",
        "The more you pin down, the more they resist commitment.",
    ],
    ("comfortable_with_uncertainty", "needs_certainty"): [
        "You stay open. They need closure. The tension builds.",
        "Your comfort with ambiguity feels like avoidance to them.",
        "They ask 'when?' You ask 'why rush?'",
    ],
    ("needs_control", "goes_with_flow"): [
        "You tighten. They loosen. Nothing sticks.",
        "Your planning meets their improvisation. Both feel unseen.",
        "The harder you grip, the more they slip away.",
    ],
    ("goes_with_flow", "needs_control"): [
        "You adapt. They direct. You lose yourself.",
        "Their structure starts to feel like your cage.",
        "You bend. They don't. Something eventually breaks.",
    ],
    ("direct_communicator", "indirect_communicator"): [
        "You say it. They hear something else.",
        "Your clarity lands as criticism. Their subtlety lands as confusion.",
        "The conversation happens on two different levels.",
    ],
    ("indirect_communicator", "direct_communicator"): [
        "You hint. They miss it. You resent them for missing it.",
        "Your meaning lives between your words. They only hear the words.",
        "You expect them to read you. They expect you to say it.",
    ],
    ("avoids_conflict", "engages_conflict"): [
        "You smooth. They dig. Nothing gets resolved.",
        "Their confrontation triggers your retreat. Your retreat triggers their frustration.",
        "They want to fight it out. You want it to just be okay.",
    ],
    ("engages_conflict", "avoids_conflict"): [
        "You surface things. They bury them. The same issue keeps returning.",
        "Your directness triggers their shutdown.",
        "You want resolution. They want peace. Neither gets what they need.",
    ],
}

# Your Shift - what the user needs to adjust
YOUR_SHIFT_PATTERNS = {
    ("fast_mover", "slow_processor"): [
        "Don't push for speed here.\nSlow just enough for them to catch what you're already sensing.\nYour pace isn't wrong—but it's not the only right pace.",
        "Let them arrive at it themselves.\nYour certainty doesn't need their immediate agreement.\nGive them the gap they need.",
    ],
    ("slow_processor", "fast_mover"): [
        "Name what you're processing, even before you've finished.\nYour silence reads as distance to them.\nLet them see the work happening, not just the result.",
        "You don't have to move their speed.\nBut you do have to signal that you're moving.",
    ],
    ("emotionally_open", "emotionally_guarded"): [
        "Your openness is a gift. But it can feel like demand.\nShow without needing matching.\nLet them come toward you at their pace.",
        "Don't interpret their quiet as rejection.\nThey're not withholding—they're protecting.\nYour job isn't to crack them open.",
    ],
    ("emotionally_guarded", "emotionally_open"): [
        "You don't have to match their intensity.\nBut give them something to hold onto.\nA little more access, not full exposure.",
        "Your protection makes sense. But it reads as distance.\nOffer one small window they didn't expect.",
    ],
    ("needs_certainty", "comfortable_with_uncertainty"): [
        "You need the map. They need the territory.\nYour planning isn't wrong—but it can suffocate.\nBuild in room for discovery.",
        "Let go of needing to know the whole shape.\nOne step at a time works here.\nYour certainty doesn't have to be theirs.",
    ],
    ("comfortable_with_uncertainty", "needs_certainty"): [
        "Your openness feels like chaos to them.\nOffer one anchor they can hold.\nYou don't have to lock everything down—just one thing.",
        "Give them a timeline. Even a rough one.\nTheir need to know isn't weakness.\nMeet them partway.",
    ],
    ("needs_control", "goes_with_flow"): [
        "Loosen your grip. Just slightly.\nYour need to steer can stall the thing you're building.\nLet them lead somewhere you didn't plan.",
        "Control isn't bad. But control of everything is exhausting.\nTrust them with one piece you usually hold.",
    ],
    ("goes_with_flow", "needs_control"): [
        "Offer more structure than you naturally would.\nYour flexibility is a gift—but it can feel like absence.\nStep into the frame they need.",
        "Take a position. Hold it.\nThey need to know where you stand.\nYour adaptability shouldn't erase you.",
    ],
    ("direct_communicator", "indirect_communicator"): [
        "Say it softer. Same truth, less force.\nYour clarity is a gift—but it can cut.\nThey need the message wrapped, not thrown.",
        "Slow your delivery. Watch their face.\nYour words land harder than you realize.\nMake room for them to receive.",
    ],
    ("indirect_communicator", "direct_communicator"): [
        "Say the thing you're implying.\nThey won't read between your lines.\nYour subtlety is invisible to them.",
        "Stop expecting them to infer.\nWhat you need, you have to name.\nClarity isn't aggression.",
    ],
    ("avoids_conflict", "engages_conflict"): [
        "The peace you're keeping isn't peaceful.\nSay the thing you're swallowing.\nYour silence is louder than you think.",
        "Conflict isn't always damage.\nSometimes it's the only way to the other side.\nStep into the friction.",
    ],
    ("engages_conflict", "avoids_conflict"): [
        "Not every issue needs to be surfaced right now.\nYour confrontation triggers their shutdown.\nLower the temperature first.",
        "Let some things settle before you address them.\nYour urgency to resolve can create more to resolve.\nPick your moments.",
    ],
}

# Gift - what unlocks if you shift
GIFT_PATTERNS = {
    ("fast_mover", "slow_processor"): [
        "When you do, their perspective sharpens your direction.",
        "Their slower pace catches what your speed would miss.",
        "You move faster together when you let them catch up first.",
    ],
    ("slow_processor", "fast_mover"): [
        "Their momentum carries you past your own hesitation.",
        "Their decisiveness cuts through your loops.",
        "Together, you move with both certainty and depth.",
    ],
    ("emotionally_open", "emotionally_guarded"): [
        "Their containment gives your expression somewhere to land.",
        "When they do open, it means something.",
        "Their steadiness becomes your anchor.",
    ],
    ("emotionally_guarded", "emotionally_open"): [
        "Their openness invites parts of you you've kept hidden.",
        "They create space for feelings you didn't know you had.",
        "Your small openings become bridges.",
    ],
    ("needs_certainty", "comfortable_with_uncertainty"): [
        "Their openness reveals paths you wouldn't have planned.",
        "Discovery becomes part of the structure.",
        "You find things together that neither would find alone.",
    ],
    ("comfortable_with_uncertainty", "needs_certainty"): [
        "Their structure gives your exploration direction.",
        "Grounding becomes freedom, not limitation.",
        "You discover more because you're not wandering aimlessly.",
    ],
    ("needs_control", "goes_with_flow"): [
        "Their flexibility shows you what you're missing by holding so tight.",
        "What you let go of creates room for something better.",
        "Their adaptation makes your plans actually work.",
    ],
    ("goes_with_flow", "needs_control"): [
        "Their structure gives your flexibility a frame.",
        "Commitment becomes clarifying, not constraining.",
        "You become more yourself with a shape to work within.",
    ],
    ("direct_communicator", "indirect_communicator"): [
        "Their nuance adds depth to your clarity.",
        "You learn to hear what isn't said.",
        "Communication becomes layered instead of flat.",
    ],
    ("indirect_communicator", "direct_communicator"): [
        "Their directness teaches you to trust your own voice.",
        "You stop hiding behind implication.",
        "What you need actually gets met.",
    ],
    ("avoids_conflict", "engages_conflict"): [
        "Real peace comes after the hard conversation.",
        "What you were protecting becomes unnecessary.",
        "Resolution actually sticks.",
    ],
    ("engages_conflict", "avoids_conflict"): [
        "Some things heal without being opened.",
        "Their peace shows you what doesn't need fighting.",
        "You save your energy for what actually matters.",
    ],
}

# Try This - one specific action
TRY_THIS_PATTERNS = {
    ("fast_mover", "slow_processor"): [
        "Before deciding, ask: 'What are you still sensing here?'",
        "Pause for 10 seconds before responding. Let them fill the space.",
        "Say: 'I'm ready to move. Where are you?'",
    ],
    ("slow_processor", "fast_mover"): [
        "Say: 'I'm still working on this. Here's where I am so far.'",
        "Give them a timeline: 'I'll have clarity by [time].'",
        "Name your process: 'I need to sit with this. I'll circle back.'",
    ],
    ("emotionally_open", "emotionally_guarded"): [
        "Share without asking for matching: 'I feel this. You don't have to respond.'",
        "Ask: 'Is there anything you're holding that you want me to know?'",
        "Offer silence after you share. Let them come to you.",
    ],
    ("emotionally_guarded", "emotionally_open"): [
        "Name one feeling you wouldn't normally share.",
        "Say: 'This is hard for me to say, but...'",
        "Ask them what they need from you emotionally. Listen without defending.",
    ],
    ("needs_certainty", "comfortable_with_uncertainty"): [
        "Ask: 'What would help you feel more free here?'",
        "Offer a loose plan instead of a tight one.",
        "Say: 'We don't have to decide everything. What's the one thing?'",
    ],
    ("comfortable_with_uncertainty", "needs_certainty"): [
        "Offer one commitment: 'Here's what I know for sure.'",
        "Give them a date or a number. Anything concrete.",
        "Ask: 'What would help you feel grounded here?'",
    ],
    ("needs_control", "goes_with_flow"): [
        "Let them make one decision you'd normally make yourself.",
        "Ask: 'What would you do if I wasn't managing this?'",
        "Say: 'I'm letting go of this one. It's yours.'",
    ],
    ("goes_with_flow", "needs_control"): [
        "Take ownership of one thing they usually control.",
        "Say: 'Here's what I think we should do.' State it clearly.",
        "Make a decision without consulting them. See what happens.",
    ],
    ("direct_communicator", "indirect_communicator"): [
        "Before speaking, ask: 'How will this land for them?'",
        "Soften your opener: 'This might come out strong, but...'",
        "Ask: 'How did that land?' after you say something important.",
    ],
    ("indirect_communicator", "direct_communicator"): [
        "Say the thing you've been implying. Out loud.",
        "Start with: 'I need to tell you something directly.'",
        "Ask yourself: 'What am I hoping they'll guess?' Then say it.",
    ],
    ("avoids_conflict", "engages_conflict"): [
        "Name one thing you've been swallowing.",
        "Say: 'There's something I've been avoiding bringing up.'",
        "Ask: 'Can we talk about the thing we've been not talking about?'",
    ],
    ("engages_conflict", "avoids_conflict"): [
        "Let one issue go unaddressed. See what happens.",
        "Say: 'I want to talk about this, but I'll wait until you're ready.'",
        "Ask: 'Is now a good time, or should we come back to this?'",
    ],
}


# =============================================================================
# TYPE DETECTION FROM PROFILE DATA
# =============================================================================

def detect_user_type(profile_data: Dict[str, Any]) -> List[str]:
    """Detect user's dominant patterns from their profile."""
    types = []
    
    # From Enneagram
    enneagram = profile_data.get("enneagram", {})
    enneagram_type = enneagram.get("type")
    
    if enneagram_type:
        type_map = {
            1: ["needs_certainty", "direct_communicator", "engages_conflict"],
            2: ["emotionally_open", "indirect_communicator", "avoids_conflict"],
            3: ["fast_mover", "direct_communicator", "needs_control"],
            4: ["slow_processor", "emotionally_open", "indirect_communicator"],
            5: ["slow_processor", "emotionally_guarded", "avoids_conflict"],
            6: ["needs_certainty", "indirect_communicator", "avoids_conflict"],
            7: ["fast_mover", "comfortable_with_uncertainty", "avoids_conflict"],
            8: ["fast_mover", "direct_communicator", "engages_conflict", "needs_control"],
            9: ["slow_processor", "avoids_conflict", "goes_with_flow"],
        }
        types.extend(type_map.get(enneagram_type, []))
    
    # From Astrology (Sun sign element)
    astrology = profile_data.get("astrology", {})
    sun_sign = astrology.get("sun_sign", "").lower()
    
    fire_signs = ["aries", "leo", "sagittarius"]
    earth_signs = ["taurus", "virgo", "capricorn"]
    air_signs = ["gemini", "libra", "aquarius"]
    water_signs = ["cancer", "scorpio", "pisces"]
    
    if sun_sign in fire_signs:
        types.extend(["fast_mover", "direct_communicator"])
    elif sun_sign in earth_signs:
        types.extend(["slow_processor", "needs_certainty"])
    elif sun_sign in air_signs:
        types.extend(["comfortable_with_uncertainty", "direct_communicator"])
    elif sun_sign in water_signs:
        types.extend(["emotionally_open", "indirect_communicator"])
    
    # Default if nothing detected
    if not types:
        types = ["fast_mover", "emotionally_open"]
    
    # Dedupe and return
    return list(set(types))


def detect_other_type(other_profile: Dict[str, Any], relationship_context: str = "") -> List[str]:
    """Detect other person's type from their profile or context."""
    types = []
    
    # Try to detect from profile first
    if other_profile:
        types = detect_user_type(other_profile)
    
    # Override/supplement from context keywords
    context_lower = relationship_context.lower()
    
    if any(w in context_lower for w in ["slow", "takes time", "careful", "hesitant"]):
        types.append("slow_processor")
    if any(w in context_lower for w in ["fast", "quick", "decisive", "impulsive"]):
        types.append("fast_mover")
    if any(w in context_lower for w in ["closed", "guarded", "quiet", "reserved"]):
        types.append("emotionally_guarded")
    if any(w in context_lower for w in ["emotional", "sensitive", "expressive"]):
        types.append("emotionally_open")
    if any(w in context_lower for w in ["controlling", "needs control", "rigid"]):
        types.append("needs_control")
    if any(w in context_lower for w in ["flexible", "easygoing", "adaptable"]):
        types.append("goes_with_flow")
    if any(w in context_lower for w in ["direct", "blunt", "straightforward"]):
        types.append("direct_communicator")
    if any(w in context_lower for w in ["indirect", "subtle", "hints"]):
        types.append("indirect_communicator")
    if any(w in context_lower for w in ["avoids conflict", "peacekeeper", "non-confrontational"]):
        types.append("avoids_conflict")
    if any(w in context_lower for w in ["confrontational", "direct about problems"]):
        types.append("engages_conflict")
    
    # Default
    if not types:
        types = ["slow_processor", "emotionally_guarded"]
    
    return list(set(types))


# =============================================================================
# MAIN GENERATOR
# =============================================================================

def generate_relationship_insight(
    user_profile: Dict[str, Any],
    other_profile: Optional[Dict[str, Any]] = None,
    other_name: str = "them",
    relationship_type: str = "relationship",  # relationship, friendship, family, work
    relationship_context: str = "",  # User-provided context about the dynamic
    seed: str = ""
) -> Dict[str, Any]:
    """
    Generate a 1:1 relationship insight.
    
    Centered on USER, not the other person.
    Helps user understand what's happening and what to shift.
    """
    
    # Generate seed for deterministic output
    if not seed:
        seed = f"{user_profile.get('user_id', '')}:{other_name}:{datetime.now().strftime('%Y-%m-%d')}"
    seed_hash = int(hashlib.md5(seed.encode()).hexdigest()[:8], 16)
    
    # Detect types
    user_types = detect_user_type(user_profile)
    other_types = detect_other_type(other_profile or {}, relationship_context)
    
    # Find primary dynamic pair
    # Pick the most contrasting pair for interesting friction
    dynamic_pair = None
    for u_type in user_types:
        for o_type in other_types:
            if (u_type, o_type) in FRICTION_PATTERNS:
                dynamic_pair = (u_type, o_type)
                break
        if dynamic_pair:
            break
    
    # Fallback to first available
    if not dynamic_pair:
        dynamic_pair = (user_types[0], other_types[0])
    
    user_type, other_type = dynamic_pair
    
    # Select content
    def select(patterns: dict, key: tuple, fallback_key: str = None) -> str:
        options = patterns.get(key, patterns.get(fallback_key, ["Content not available"]))
        if isinstance(options, list):
            return options[seed_hash % len(options)]
        return options
    
    # Generate sections
    essence = select(ESSENCE_PATTERNS, other_type, "slow_processor")
    friction = select(FRICTION_PATTERNS, dynamic_pair, ("fast_mover", "slow_processor"))
    tension = select(TENSION_LOOPS, dynamic_pair, ("fast_mover", "slow_processor"))
    your_shift = select(YOUR_SHIFT_PATTERNS, dynamic_pair, ("fast_mover", "slow_processor"))
    gift = select(GIFT_PATTERNS, dynamic_pair, ("fast_mover", "slow_processor"))
    try_this = select(TRY_THIS_PATTERNS, dynamic_pair, ("fast_mover", "slow_processor"))
    
    return {
        "success": True,
        "version": "v1.0",
        "other_name": other_name,
        "relationship_type": relationship_type,
        
        # The 6-section structure
        "essence": essence,
        "friction": friction,
        "tension": tension,
        "your_shift": your_shift,
        "gift": gift,
        "try_this": try_this,
        
        # Metadata
        "dynamic_pair": {
            "user_type": user_type,
            "other_type": other_type,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# =============================================================================
# API HELPERS
# =============================================================================

async def get_relationship_insight(
    db,
    user_id: str,
    other_user_id: Optional[str] = None,
    other_name: str = "them",
    relationship_type: str = "relationship",
    relationship_context: str = ""
) -> Dict[str, Any]:
    """
    Get relationship insight from database profiles.
    """
    try:
        # Get user profile
        user = await db.users.find_one({"_id": user_id})
        user_profile = {
            "user_id": user_id,
            "enneagram": user.get("enneagram", {}) if user else {},
            "astrology": user.get("astrology", {}) if user else {},
        }
        
        # Get other profile if available
        other_profile = None
        if other_user_id:
            other = await db.users.find_one({"_id": other_user_id})
            if other:
                other_profile = {
                    "user_id": other_user_id,
                    "enneagram": other.get("enneagram", {}),
                    "astrology": other.get("astrology", {}),
                }
        
        return generate_relationship_insight(
            user_profile=user_profile,
            other_profile=other_profile,
            other_name=other_name,
            relationship_type=relationship_type,
            relationship_context=relationship_context,
        )
        
    except Exception as e:
        logger.error(f"[RelationshipInsight] Error: {e}")
        return {
            "success": False,
            "error": str(e),
        }
