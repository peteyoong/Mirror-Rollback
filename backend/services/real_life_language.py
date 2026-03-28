"""Real-Life Language Transformation Service

Converts Human Design and Pattern system terminology into 
lived-experience, behavioral language that users instantly recognize.

RULES:
1. NEVER start with system terms (Ajna, G Center, House, Element)
2. ALWAYS start with behavior or lived experience
3. System labels go LAST (optional, secondary)

SUCCESS CRITERIA:
- User instantly recognizes themselves
- No system knowledge required
- Feels like observation, not explanation
"""

from typing import Dict, Optional, Tuple
import re


# =============================================================================
# CENTER TRANSLATIONS - Behavioral First, System Label Last
# =============================================================================

CENTER_BEHAVIORAL_TRANSLATIONS = {
    # DEFINED CENTERS - What you consistently do/are
    "Head_defined": {
        "short": "You get caught in questions that won't let go",
        "medium": "You get caught in questions that won't let go—ideas arrive uninvited and stay until you've turned them over enough times.",
        "label": "Head center defined",
    },
    "Ajna_defined": {
        "short": "You tend to lock into a way of thinking—and once it makes sense to you, you stick with it",
        "medium": "You tend to lock into a way of thinking—and once it makes sense to you, you stick with it. Changing your mind takes real evidence, not just someone else's opinion.",
        "label": "Ajna center defined",
    },
    "Throat_defined": {
        "short": "You speak or act in consistent patterns—your voice has a recognizable style",
        "medium": "You speak or act in consistent patterns—your voice has a recognizable style. When you have something to say, it comes out. The challenge is timing.",
        "label": "Throat center defined",
    },
    "G Center_defined": {
        "short": "You usually have a strong sense of direction—but that can make you slow to change course",
        "medium": "You usually have a strong sense of direction—you know who you are at your core. But that certainty can make you slow to change course, even when it might help.",
        "label": "G center defined",
    },
    "G_defined": {
        "short": "You usually have a strong sense of direction—but that can make you slow to change course",
        "medium": "You usually have a strong sense of direction—you know who you are at your core. But that certainty can make you slow to change course, even when it might help.",
        "label": "G center defined",
    },
    "Ego_defined": {
        "short": "You can push through when you've committed to something—willpower is available",
        "medium": "You can push through when you've committed to something—willpower is available. The risk is overusing it, proving yourself when you don't need to.",
        "label": "Heart/Ego center defined",
    },
    "Heart_defined": {
        "short": "You can push through when you've committed to something—willpower is available",
        "medium": "You can push through when you've committed to something—willpower is available. The risk is overusing it, proving yourself when you don't need to.",
        "label": "Heart/Ego center defined",
    },
    "Solar Plexus_defined": {
        "short": "You feel things in waves—clarity doesn't come immediately, it comes after time",
        "medium": "You feel things in waves—your emotional state rises and falls in patterns. Clarity doesn't come immediately; it arrives after the wave has moved through.",
        "label": "Solar Plexus defined",
    },
    "Sacral_defined": {
        "short": "You have consistent energy for work that engages you—when it's right, you can go and go",
        "medium": "You have consistent energy for work that engages you—when it's right, you can go and go. When it's wrong, you're depleted even while technically productive.",
        "label": "Sacral center defined",
    },
    "Spleen_defined": {
        "short": "You get quiet, instant signals about what's safe or healthy—they don't repeat",
        "medium": "You get quiet, instant signals about what's safe or healthy—a knowing that arrives in the moment and doesn't repeat. Learning to hear it before your mind overrides it takes practice.",
        "label": "Spleen center defined",
    },
    "Root_defined": {
        "short": "You handle pressure without being destabilized by it—stress is manageable",
        "medium": "You handle pressure without being destabilized by it—stress arrives, but it doesn't throw you off. The risk is becoming addicted to urgency.",
        "label": "Root center defined",
    },
    
    # UNDEFINED CENTERS - What you absorb, amplify, or experience inconsistently
    "Head_undefined": {
        "short": "You take in other people's mental pressure and sometimes mistake it for your own",
        "medium": "You take in other people's mental pressure and sometimes mistake it for your own. Their questions become urgent for you, even when they're not yours to solve.",
        "label": "Head center open",
    },
    "Ajna_undefined": {
        "short": "Your thinking shifts depending on who you're around—you can see multiple perspectives",
        "medium": "Your thinking shifts depending on who you're around—you can see multiple perspectives, but might struggle to hold a consistent view. That flexibility is a gift, not a flaw.",
        "label": "Ajna center open",
    },
    "Throat_undefined": {
        "short": "You don't always know when or how to speak—timing feels inconsistent",
        "medium": "You don't always know when or how to speak—timing feels inconsistent. You might overspeak to get attention or go quiet when you actually have something to say.",
        "label": "Throat center open",
    },
    "G Center_undefined": {
        "short": "You sometimes feel uncertain about who you are or where you're going",
        "medium": "You sometimes feel uncertain about who you are or where you're going. You pick up a sense of identity from people and places around you—which makes environment crucial.",
        "label": "G center open",
    },
    "G_undefined": {
        "short": "You sometimes feel uncertain about who you are or where you're going",
        "medium": "You sometimes feel uncertain about who you are or where you're going. You pick up a sense of identity from people and places around you—which makes environment crucial.",
        "label": "G center open",
    },
    "Ego_undefined": {
        "short": "You don't have consistent willpower—and that's not a weakness",
        "medium": "You don't have consistent willpower—and that's not a weakness. You might overcommit to prove yourself, then burn out. Learning what's actually yours to push through matters.",
        "label": "Heart/Ego center open",
    },
    "Heart_undefined": {
        "short": "You don't have consistent willpower—and that's not a weakness",
        "medium": "You don't have consistent willpower—and that's not a weakness. You might overcommit to prove yourself, then burn out. Learning what's actually yours to push through matters.",
        "label": "Heart/Ego center open",
    },
    "Solar Plexus_undefined": {
        "short": "You absorb emotions from others and feel them more intensely than they do",
        "medium": "You absorb emotions from others and feel them more intensely than they do. Conflict in the room becomes your conflict. Learning to release what isn't yours is essential.",
        "label": "Solar Plexus open",
    },
    "Sacral_undefined": {
        "short": "You don't have consistent work energy—you need to know when enough is enough",
        "medium": "You don't have consistent work energy—you can borrow it from others and go beyond healthy limits. Learning when enough is enough prevents burnout.",
        "label": "Sacral center open",
    },
    "Spleen_undefined": {
        "short": "You might hold onto things too long—jobs, relationships, habits—past their expiration",
        "medium": "You might hold onto things too long—jobs, relationships, habits—past their expiration. Security feels uncertain, so you grip what you have even when it no longer serves.",
        "label": "Spleen center open",
    },
    "Root_undefined": {
        "short": "You absorb other people's urgency and feel pressured to rush",
        "medium": "You absorb other people's urgency and feel pressured to rush. Their deadline becomes your stress. Learning to notice when the pressure isn't actually yours is freedom.",
        "label": "Root center open",
    },
}


# =============================================================================
# AUTHORITY TRANSLATIONS - Behavioral First
# =============================================================================

AUTHORITY_BEHAVIORAL_TRANSLATIONS = {
    "Emotional": {
        "short": "You feel things in waves—clarity doesn't come immediately, it comes after time",
        "medium": "You feel things in waves. Big decisions need time to settle—not because you're uncertain, but because your clarity arrives after the emotional wave has moved through.",
        "process": "Wait. Ride the wave. The answer becomes clear when the intensity fades.",
        "label": "Emotional Authority",
    },
    "Sacral": {
        "short": "Your gut responds instantly—an 'uh-huh' yes or 'un-un' no that you feel in your body",
        "medium": "Your gut responds instantly—you feel a rise of energy toward something or a contraction away. That body response is more reliable than your reasoning.",
        "process": "Notice your body's immediate response. Yes feels like expansion. No feels like contraction.",
        "label": "Sacral Authority",
    },
    "Splenic": {
        "short": "You get quiet, instant knowing about what's right—it speaks once and doesn't repeat",
        "medium": "You get quiet, instant knowing about what's right—a subtle signal that speaks once, in the moment, and doesn't repeat. Learning to hear it before your mind overrides it is key.",
        "process": "Trust the first hit. The body knows before the mind catches up.",
        "label": "Splenic Authority",
    },
    "Ego": {
        "short": "You know through what you're willing to commit to—if the will is there, it's right",
        "medium": "You know through what you're willing to commit to. If your heart says 'I will' or 'I want,' that's your signal. If the willpower isn't there, don't force it.",
        "process": "Check: Is the commitment there? Is this something you actually want to give yourself to?",
        "label": "Ego/Heart Authority",
    },
    "Self-Projected": {
        "short": "You find clarity by talking things through—hearing your own voice reveals what's true",
        "medium": "You find clarity by talking things through—not to get advice, but to hear yourself. Your voice reveals your direction when you speak without filtering.",
        "process": "Talk it out. Let someone listen without advising. Your truth emerges as you speak.",
        "label": "Self-Projected Authority",
    },
    "Mental": {
        "short": "You need to talk through decisions with trusted others—not for their opinion, but for your clarity",
        "medium": "You need to talk through decisions with trusted others—not for their opinion, but because bouncing ideas off them helps you hear what's right for you.",
        "process": "Find the right sounding boards. Notice what feels true as you talk.",
        "label": "Mental/Environmental Authority",
    },
    "Lunar": {
        "short": "Big decisions need a full moon cycle—about 28 days—to become clear",
        "medium": "Big decisions need a full moon cycle to become clear. You experience life differently throughout the month, and rushing decisions means missing important data.",
        "process": "Give it time. A full lunar cycle. Notice how your perspective shifts as the month moves.",
        "label": "Lunar Authority",
    },
    "None": {
        "short": "Your clarity comes from environment and experience—not a single inner signal",
        "medium": "Your clarity emerges from being in the right environment and processing experience over time. There's no single 'authority' signal—it's more diffuse.",
        "process": "Notice what environments feel right. Let clarity emerge rather than forcing it.",
        "label": "No Inner Authority",
    },
}


# =============================================================================
# TYPE TRANSLATIONS - Behavioral First
# =============================================================================

TYPE_BEHAVIORAL_TRANSLATIONS = {
    "Manifestor": {
        "short": "You're wired to initiate—to start things before others are ready",
        "medium": "You're wired to initiate—to start things before others are ready. The world responds to your impact, but it can also resist if you don't inform people before you act.",
        "challenge": "You might move before others can catch up, creating resistance or confusion",
        "gift": "Starting things, catalyzing change, moving energy that was stuck",
        "label": "Manifestor",
    },
    "Generator": {
        "short": "You have sustainable energy when you're doing work that genuinely engages you",
        "medium": "You have sustainable energy when you're doing work that genuinely engages you. The key is responding to what life brings rather than initiating from your head.",
        "challenge": "You might say yes when your gut says no, or initiate instead of waiting to respond",
        "gift": "Sustaining effort, building things over time, mastery through commitment",
        "label": "Generator",
    },
    "Manifesting Generator": {
        "short": "You move fast when engaged—but skipping steps creates cleanup work later",
        "medium": "You move fast when engaged—efficient, multi-tracking, capable of doing in moments what takes others hours. But skipping steps creates cleanup work later.",
        "challenge": "Impatience with process, skipping necessary steps, starting before you've fully responded",
        "gift": "Speed, efficiency, doing multiple things simultaneously, finding shortcuts",
        "label": "Manifesting Generator",
    },
    "Projector": {
        "short": "You see how things could work better—but sharing that without invitation creates bitterness",
        "medium": "You see how things could work better—systems, people, processes. But sharing that insight without being invited creates resentment, both from others and in yourself.",
        "challenge": "Offering guidance when it wasn't asked for, working too hard, bitterness from not being seen",
        "gift": "Seeing what others miss, guiding energy efficiently, understanding systems",
        "label": "Projector",
    },
    "Reflector": {
        "short": "You mirror your environment—what you feel often belongs to the people and places around you",
        "medium": "You mirror your environment—what you feel often belongs to the people and places around you. This makes you a sensitive reader of spaces, but requires careful environment selection.",
        "challenge": "Taking on what doesn't belong to you, moving too fast, absorbing dysfunction",
        "gift": "Reading environments accurately, sensing what's healthy or unhealthy in a space",
        "label": "Reflector",
    },
}


# =============================================================================
# PATTERN HEADLINE REPLACEMENTS
# =============================================================================

# Replace generic "The Pause" with specific behavioral variants
PAUSE_VARIANTS = {
    "moving_before_settled": {
        "headline": "You're moving before it's settled",
        "subtext": "The push is there. The ground isn't.",
    },
    "waiting_external": {
        "headline": "You're waiting on something outside you",
        "subtext": "But the hold might be internal.",
    },
    "unsure_pushing": {
        "headline": "You're unsure—but still pushing",
        "subtext": "Something hasn't clicked, and you know it.",
    },
    "avoiding_known": {
        "headline": "You're avoiding something you already know",
        "subtext": "The pause isn't confusion. It's protection.",
    },
}


# Map pattern states to specific pause variants
def get_pause_variant(context: dict) -> dict:
    """
    Select the most appropriate pause variant based on context.
    
    Context can include:
    - authority: HD authority type
    - defined_centers: list of defined centers
    - recent_behavior: what user has been doing
    - exposure_state: first, repeated, persistent, engaged
    """
    authority = context.get("authority", "").lower()
    exposure_state = context.get("exposure_state", "first_exposure")
    # defined_centers can be used for future center-specific pause variants
    _ = context.get("defined_centers", [])
    
    # First exposure - usually "moving before settled"
    if exposure_state == "first_exposure":
        return PAUSE_VARIANTS["moving_before_settled"]
    
    # Emotional authority and repeated = waiting on something external (the wave)
    if "emotional" in authority and exposure_state == "repeated_exposure":
        return PAUSE_VARIANTS["waiting_external"]
    
    # Persistent pattern = avoiding something known
    if exposure_state in ["persistent_pattern", "engaged_pattern"]:
        return PAUSE_VARIANTS["avoiding_known"]
    
    # Default to unsure but pushing
    return PAUSE_VARIANTS["unsure_pushing"]


# =============================================================================
# MAIN TRANSFORMATION FUNCTIONS
# =============================================================================

def transform_center_description(
    center_name: str, 
    is_defined: bool,
    length: str = "short"
) -> str:
    """
    Transform a center reference to behavioral language.
    
    Args:
        center_name: Name of the center (e.g., "Ajna", "G Center")
        is_defined: Whether the center is defined or undefined
        length: "short" or "medium" for description length
        
    Returns:
        Behavioral description that starts with lived experience
    """
    status = "defined" if is_defined else "undefined"
    key = f"{center_name}_{status}"
    
    translation = CENTER_BEHAVIORAL_TRANSLATIONS.get(key)
    if not translation:
        # Fallback for unknown centers
        if is_defined:
            return f"You have consistent access to {center_name.lower()} energy"
        else:
            return f"You experience {center_name.lower()} energy inconsistently, absorbing it from others"
    
    return translation.get(length, translation.get("short", ""))


def transform_authority_description(
    authority: str,
    length: str = "short"
) -> str:
    """
    Transform authority to behavioral language.
    
    Args:
        authority: Authority type (e.g., "Emotional", "Sacral")
        length: "short" or "medium" for description length
        
    Returns:
        Behavioral description that starts with lived experience
    """
    # Normalize authority name
    authority_key = authority
    for key in AUTHORITY_BEHAVIORAL_TRANSLATIONS:
        if key.lower() in authority.lower():
            authority_key = key
            break
    
    translation = AUTHORITY_BEHAVIORAL_TRANSLATIONS.get(authority_key)
    if not translation:
        return f"Your clarity emerges through {authority.lower()}"
    
    return translation.get(length, translation.get("short", ""))


def transform_type_description(
    hd_type: str,
    length: str = "short"
) -> str:
    """
    Transform HD type to behavioral language.
    
    Args:
        hd_type: Type (e.g., "Generator", "Projector")
        length: "short" or "medium" for description length
        
    Returns:
        Behavioral description that starts with lived experience
    """
    translation = TYPE_BEHAVIORAL_TRANSLATIONS.get(hd_type)
    if not translation:
        return "Your natural operating mode shapes how you engage with the world"
    
    return translation.get(length, translation.get("short", ""))


def transform_system_text(text: str) -> str:
    """
    Transform any text containing system terminology to behavioral language.
    Replaces system terms with behavioral equivalents inline.
    
    Args:
        text: Text that may contain HD/astrology terminology
        
    Returns:
        Text with system terms replaced by behavioral language
    """
    if not text:
        return text
    
    # Pattern replacements for common system-first phrasings
    replacements = [
        # Authority patterns
        (r"Your Emotional Authority", "You feel things in waves"),
        (r"With Emotional Authority,?", "Because clarity comes after time for you,"),
        (r"Emotional Authority means", "For you, clarity comes in waves—"),
        (r"Your Sacral Authority", "Your gut response"),
        (r"With Sacral Authority,?", "Because your gut knows instantly,"),
        (r"Your Splenic Authority", "Your instant knowing"),
        (r"With Splenic Authority,?", "Because you get quiet signals that speak once,"),
        
        # Center patterns  
        (r"Your Ajna (center )?is defined", "You tend to lock into a way of thinking"),
        (r"Your G Center is defined", "You have a strong sense of direction"),
        (r"Your Solar Plexus is defined", "You feel things in waves"),
        (r"Your Sacral (center )?is defined", "You have consistent work energy"),
        (r"Your Spleen (center )?is defined", "You get quiet, instant signals"),
        (r"Your Root (center )?is defined", "You handle pressure without being destabilized"),
        (r"Your Throat (center )?is defined", "You speak in consistent patterns"),
        (r"Your Head (center )?is defined", "You get caught in questions that won't let go"),
        (r"Your Heart/Ego (center )?is defined", "You can push through when committed"),
        
        # Open center patterns
        (r"Your Ajna (center )?is (open|undefined)", "Your thinking shifts depending on who you're around"),
        (r"Your G Center is (open|undefined)", "You sometimes feel uncertain about direction"),
        (r"Your Solar Plexus is (open|undefined)", "You absorb emotions from others"),
        (r"Your Sacral (center )?is (open|undefined)", "Your work energy is inconsistent"),
        (r"Your Spleen (center )?is (open|undefined)", "You might hold onto things past their time"),
        (r"Your Root (center )?is (open|undefined)", "You absorb other people's urgency"),
        
        # Type patterns
        (r"As a Generator,?", "With sustainable energy for work you love,"),
        (r"As a Projector,?", "Seeing how things could work better,"),
        (r"As a Manifestor,?", "Wired to initiate before others are ready,"),
        (r"As a Manifesting Generator,?", "Moving fast when engaged,"),
        (r"As a Reflector,?", "Mirroring your environment,"),
    ]
    
    result = text
    for pattern, replacement in replacements:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    
    return result


def get_behavioral_opening(
    pattern_type: str,
    authority: str = None,
    defined_centers: list = None,
    exposure_state: str = "first_exposure"
) -> dict:
    """
    Generate a behavioral opening for pattern diagnosis.
    Returns headline and opening that start with lived experience.
    
    Args:
        pattern_type: Type of pattern (stall, push_pull, expression, etc.)
        authority: User's HD authority
        defined_centers: List of user's defined centers
        exposure_state: How many times user has seen this pattern
        
    Returns:
        Dict with 'headline' and 'opening' keys
    """
    context = {
        "authority": authority or "",
        "defined_centers": defined_centers or [],
        "exposure_state": exposure_state,
    }
    
    if pattern_type == "stall":
        variant = get_pause_variant(context)
        return {
            "headline": variant["headline"],
            "opening": variant["subtext"],
        }
    
    # Other pattern types keep their existing structure but ensure behavioral opening
    pattern_openings = {
        "push_pull": {
            "headline": "You're pulled in two directions",
            "opening": "Both feel real. The tension isn't confusion—it's two truths competing.",
        },
        "expression": {
            "headline": "There's something you're not saying",
            "opening": "It's sitting in you. The silence isn't peace—it's pressure.",
        },
        "overextension": {
            "headline": "You've taken on more than you should",
            "opening": "You know it. But you keep going anyway.",
        },
        "timing": {
            "headline": "The timing feels off",
            "opening": "Something in you says wait. Something else says move. Neither wins.",
        },
    }
    
    return pattern_openings.get(pattern_type, {
        "headline": "Something's emerging",
        "opening": "A pattern you've felt before. A tension asking for attention.",
    })


# =============================================================================
# HELPER FUNCTIONS FOR INTEGRATION
# =============================================================================

def format_center_with_behavior(center_name: str, is_defined: bool) -> str:
    """
    Format a center description with behavior first, label second.
    
    Example output:
    "You tend to lock into a way of thinking (Ajna defined)"
    """
    behavior = transform_center_description(center_name, is_defined, "short")
    key = f"{center_name}_{'defined' if is_defined else 'undefined'}"
    translation = CENTER_BEHAVIORAL_TRANSLATIONS.get(key, {})
    label = translation.get("label", f"{center_name} {'defined' if is_defined else 'open'}")
    
    return f"{behavior} ({label})"


def format_authority_with_behavior(authority: str) -> str:
    """
    Format authority description with behavior first, label second.
    
    Example output:
    "You feel things in waves—clarity comes after time (Emotional Authority)"
    """
    behavior = transform_authority_description(authority, "short")
    
    # Get label
    for key, translation in AUTHORITY_BEHAVIORAL_TRANSLATIONS.items():
        if key.lower() in authority.lower():
            label = translation.get("label", authority)
            return f"{behavior} ({label})"
    
    return f"{behavior} ({authority})"


def format_type_with_behavior(hd_type: str) -> str:
    """
    Format type description with behavior first, label second.
    
    Example output:
    "You have sustainable energy for work that engages you (Generator)"
    """
    behavior = transform_type_description(hd_type, "short")
    translation = TYPE_BEHAVIORAL_TRANSLATIONS.get(hd_type, {})
    label = translation.get("label", hd_type)
    
    return f"{behavior} ({label})"
