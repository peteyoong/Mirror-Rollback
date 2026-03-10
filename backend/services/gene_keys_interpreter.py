"""Gene Keys Interpretation Service

Provides interpretive layer for Gene Keys based on Human Design gate/line data.
This service does NOT compute anything - it only provides interpretation.

The deterministic compute is done in /calculations/gene_keys.py.
This service adds the Shadow/Gift/Siddhi meaning layer and template-based interpretations.
"""

from typing import Optional, TypedDict, List
from data.gene_keys_data import GENE_KEYS, GeneKeyData, is_gene_key_available


class GeneKeyInterpretation(TypedDict):
    """Full Gene Key interpretation response."""
    gene_key: int
    line: int
    shadow: str
    gift: str
    siddhi: str
    available: bool
    message: Optional[str]


class SphereInterpretation(TypedDict):
    """Detailed interpretation for a single sphere."""
    sphere_name: str
    gene_key: int
    line: int
    shadow: str
    gift: str
    siddhi: str
    what_this_means: str
    your_challenge: str
    your_higher_expression: str
    practical_tips: str
    remember: str


class ActivationSequenceResponse(TypedDict):
    """Full Activation Sequence response."""
    sequence_name: str
    spheres: List[SphereInterpretation]


# =============================================================================
# TEMPLATE-BASED INTERPRETATIONS
# =============================================================================
# These templates provide practical, reflective guidance based on sphere context.
# Tone: warm, non-deterministic, behaviorally specific, not guru-like.

SPHERE_TEMPLATES = {
    # =========================================================================
    # ACTIVATION SEQUENCE - Self-discovery & core stability
    # =========================================================================
    "Life's Work": {
        "what_this_means": "This sphere highlights a theme that tends to show up in how you engage with work and contribution. Gene Key {gene_key} suggests a particular tension between {shadow} and {gift}—not as a problem to solve, but as a creative friction that shapes what you offer. You may notice this dynamic playing out in your career, projects, or how you spend your energy.",
        "your_challenge": "When stressed or off-center, {shadow} may surface in your work life. This could look like certain habitual reactions, avoidance patterns, or ways you undermine yourself professionally. Rather than fighting this, it helps to simply notice: \"Ah, there's that {shadow} pattern again.\" Recognition is the first step.",
        "your_higher_expression": "The gift of {gift} often emerges naturally when you're doing work that genuinely interests you. You might notice it in moments of flow, when effort feels less effortful. Others may comment on this quality in you—it's often more visible to them than to yourself.",
        "practical_tips": "• Keep a brief log this week: when does {shadow} show up at work? What triggers it?\n• Ask a trusted colleague: \"What do you see as my natural strength?\" Compare to {gift}.\n• Try one small experiment: approach a routine task with curiosity rather than obligation.\n• Notice what work makes time disappear—that's a clue.",
        "remember": "Work patterns evolve slowly. Small awareness shifts matter more than dramatic changes."
    },
    "Evolution": {
        "what_this_means": "This sphere points to a recurring growth edge in your life—a place where you keep learning the same lesson in new forms. Gene Key {gene_key} suggests that {shadow} and {gift} represent two sides of something you're integrating over time. This isn't about fixing yourself; it's about developing a more skillful relationship with this particular pattern.",
        "your_challenge": "The shadow of {shadow} likely feels familiar—you've probably met it many times. It may show up as a recurring frustration, a pattern others have pointed out, or something you notice in hindsight. The challenge isn't to eliminate it but to catch it earlier and respond differently.",
        "your_higher_expression": "As you become more familiar with this pattern, {gift} becomes more accessible. This looks less like achieving something and more like having options where you previously felt stuck. You might notice yourself pausing before reacting, or choosing a different response.",
        "practical_tips": "• Identify one recent situation where {shadow} showed up. What happened just before?\n• What would {gift} have looked like in that moment? Be specific.\n• Set a gentle reminder to check in with yourself midday: \"How am I doing with this pattern today?\"\n• Share this growth edge with someone you trust—accountability helps.",
        "remember": "Growth isn't linear. Recognizing an old pattern is itself progress, even if you still fall into it."
    },
    "Radiance": {
        "what_this_means": "This sphere reflects something about your natural presence—the quality you emanate when you're relaxed and not performing. Gene Key {gene_key} suggests that {shadow} can obscure this, while {gift} represents what naturally shines through when you're at ease. This isn't something to cultivate so much as to stop blocking.",
        "your_challenge": "The shadow of {shadow} may show up as self-consciousness, contraction, or efforting. You might notice it when you're trying to make a certain impression, or when you feel observed and judged. In these moments, your natural presence gets covered over by protective patterns.",
        "your_higher_expression": "The gift of {gift} tends to appear when you forget yourself—in moments of genuine engagement, play, or deep conversation. Others often perceive this quality in you more clearly than you do. It's less about doing something and more about allowing.",
        "practical_tips": "• Notice when you feel most \"yourself\" this week. What conditions support that?\n• Identify one situation where you tend to perform or try hard. Can you approach it differently?\n• Ask someone close to you: \"When do I seem most relaxed and present?\"\n• Practice doing less in one interaction today—see what happens.",
        "remember": "You can't force presence. The work is noticing what gets in the way."
    },
    "Purpose": {
        "what_this_means": "This sphere relates to a sense of direction or meaning—not a specific destination, but a quality that makes some paths feel more aligned than others. Gene Key {gene_key} suggests that moving from {shadow} toward {gift} is itself meaningful, regardless of external outcomes. Purpose here is more verb than noun.",
        "your_challenge": "The shadow of {shadow} can create feelings of being lost, questioning your direction, or wondering if anything matters. These experiences aren't signs you've failed—they're natural parts of the journey. The challenge is staying curious rather than collapsing into despair or false certainty.",
        "your_higher_expression": "When connected to {gift}, you may feel a quiet sense of rightness—not excitement necessarily, but alignment. This often shows up in ordinary moments rather than dramatic ones. You know it by the absence of inner conflict rather than the presence of fireworks.",
        "practical_tips": "• Reflect: when did you last feel a sense of quiet rightness? What were you doing?\n• What activities leave you feeling slightly more whole afterward?\n• Notice what you're drawn to when you have unstructured time.\n• Try asking \"Is this aligned?\" before one decision this week—feel for the answer rather than thinking it.",
        "remember": "Purpose is felt, not figured out. Trust the small signals."
    },
    # =========================================================================
    # VENUS SEQUENCE - Relationships & emotional patterns
    # =========================================================================
    "Attraction": {
        "what_this_means": "This sphere highlights patterns in what you tend to draw into your life, particularly in relationships. Gene Key {gene_key} suggests that {shadow} and {gift} create different kinds of attraction fields. This isn't about blame—it's about noticing how your inner state shapes what shows up around you.",
        "your_challenge": "The shadow of {shadow} may correlate with attracting certain difficult patterns—relationships that feel familiar but frustrating, or situations that keep repeating. These aren't cosmic punishments; they're feedback about something that wants attention in you.",
        "your_higher_expression": "When operating more from {gift}, you may notice a shift in what comes your way—not necessarily different people, but different dynamics with them. Connections feel more nourishing, less draining. This shift happens gradually as you change internally.",
        "practical_tips": "• Review your last few significant connections. What themes repeat?\n• Where in your life does {shadow} feel most active right now?\n• Experiment: for one week, act as if {gift} were already more present. Notice any shifts.\n• What would you like to attract more of? What inner shift might support that?",
        "remember": "What you attract often mirrors what you're working on internally. The pattern can shift."
    },
    "IQ": {
        "what_this_means": "This sphere reflects how your mental processes show up in close relationships—how you think about others, communicate, and use your mind in intimate contexts. Gene Key {gene_key} suggests that {shadow} represents ways your intellect can create distance, while {gift} shows how it can serve connection.",
        "your_challenge": "The shadow of {shadow} might appear as overthinking relationships, analyzing partners, creating mental narratives that keep you safe but separate, or communicating in ways that miss the emotional point. You might catch yourself \"in your head\" when presence is needed.",
        "your_higher_expression": "The gift of {gift} represents your mind in service of connection—clear communication, helpful insight, and the ability to understand complexity without getting lost in it. Your intelligence becomes a bridge rather than a barrier.",
        "practical_tips": "• Notice one conversation this week where you went into analysis mode. What triggered it?\n• Practice pausing before responding: take a breath, feel your body, then speak.\n• Ask a partner or close friend: \"Do I sometimes seem distant or in my head?\" Listen without defending.\n• Try expressing one thing you're feeling before explaining what you're thinking.",
        "remember": "Your mind is valuable. The question is whether it's serving connection or substituting for it."
    },
    "EQ": {
        "what_this_means": "This sphere reflects your emotional patterns in relationships—how you experience, express, and navigate feelings with others. Gene Key {gene_key} suggests that {shadow} represents emotional reactivity or avoidance, while {gift} represents emotional wisdom and capacity.",
        "your_challenge": "The shadow of {shadow} might show up as emotional flooding, withdrawal, projection onto others, or difficulty sitting with uncomfortable feelings. You may notice certain triggers that reliably pull you off-center, or patterns your partners have named.",
        "your_higher_expression": "The gift of {gift} appears as emotional resilience—not suppression, but the capacity to feel fully without being overwhelmed. This allows for deeper intimacy because you can stay present through emotional intensity.",
        "practical_tips": "• Identify your top 3 emotional triggers in relationships. What happens in your body when they're activated?\n• Practice naming emotions as they arise: \"I notice I'm feeling...\" This creates space.\n• Try staying 10 seconds longer with an uncomfortable feeling before reacting.\n• Ask: \"What does this emotion need right now?\" rather than immediately acting on it.",
        "remember": "Emotional intelligence grows through feeling, not avoiding. Each wave passed through builds capacity."
    },
    "SQ": {
        "what_this_means": "This sphere reflects the depth dimension of your relationships—the capacity for meaning, presence, and something beyond the purely personal. Gene Key {gene_key} suggests that {shadow} can either close this dimension or distort it, while {gift} represents genuine spiritual depth in connection.",
        "your_challenge": "The shadow of {shadow} might appear as spiritual bypassing (using spiritual concepts to avoid real intimacy), dismissing the deeper dimensions of love, or oscillating between skepticism and inflation. You might notice difficulty being truly present or staying grounded.",
        "your_higher_expression": "The gift of {gift} shows up as the capacity to touch something sacred in ordinary moments with another person. This isn't about beliefs but about presence—the ability to be deeply here, without agenda, allowing connection to reveal its own depth.",
        "practical_tips": "• Recall a moment of genuine depth with another person. What made it possible?\n• Notice when you use ideas or concepts to create distance from emotional intimacy.\n• Practice 3 minutes of silent presence with someone you love—no talking, no fixing, just being together.\n• Ask: \"What would it mean to bring more reverence to my close relationships?\"",
        "remember": "Depth isn't achieved through effort. It's allowed through presence and letting go of agendas."
    },
    "Core": {
        "what_this_means": "This sphere points to deep relational patterns, often connected to early experiences of love and its absence. Gene Key {gene_key} suggests that {shadow} represents tender vulnerabilities carried from the past, while {gift} represents the healing and capacity that can emerge from meeting these places with compassion.",
        "your_challenge": "The shadow of {shadow} likely connects to your deepest relational fears—places where love has felt unsafe, inadequate, or conditional. These patterns tend to be subtle and pervasive, showing up across many relationships in ways you may only partly recognize.",
        "your_higher_expression": "The gift of {gift} emerges not by transcending the wound but by integrating it. Paradoxically, your deepest vulnerability can become your greatest capacity for love—because you know what it means to need it, you can offer it more genuinely.",
        "practical_tips": "• This sphere asks for gentleness. Don't push—just notice.\n• Journal: \"My earliest experience of {shadow} in love was...\" See what surfaces.\n• Consider: how does this pattern show up in your current closest relationship?\n• Rather than trying to fix this, practice simply acknowledging: \"This is tender for me.\"",
        "remember": "Core patterns change slowly, through compassion rather than force. Go gently."
    },
    # =========================================================================
    # PEARL SEQUENCE - Vocation, contribution & prosperity
    # =========================================================================
    "Vocation": {
        "what_this_means": "This sphere reflects the kind of work that genuinely calls to you—not necessarily a job title, but an underlying quality of contribution. Gene Key {gene_key} suggests that {shadow} can distort your relationship with work, while {gift} represents what wants to come through you when you're aligned.",
        "your_challenge": "The shadow of {shadow} might show up as workaholism, avoidance of meaningful work, burnout, or doing things that feel misaligned but \"safe.\" You might notice a gap between what you do and what feels genuinely alive for you.",
        "your_higher_expression": "The gift of {gift} tends to appear when you're doing work that matters to you, regardless of external reward. There's a sense of rightness, of fitting, of time well-spent. This quality is often visible to others who benefit from what you offer.",
        "practical_tips": "• List 3 activities that feel genuinely meaningful to you. What do they have in common?\n• Where does {shadow} currently show up in your work life?\n• What would change if you made decisions based on alignment rather than just security?\n• Ask someone who knows you well: \"What work do you think suits me?\"",
        "remember": "Vocation unfolds gradually. Small alignments matter more than dramatic pivots."
    },
    "Culture": {
        "what_this_means": "This sphere reflects the environments and communities where you thrive versus struggle. Gene Key {gene_key} suggests that {shadow} represents ways you might compromise yourself to belong or rebel in ways that isolate, while {gift} represents finding or creating contexts that support your authentic contribution.",
        "your_challenge": "The shadow of {shadow} might appear as chronic not-fitting-in, over-adapting to environments that drain you, or difficulty finding your people. You may notice patterns of either disappearing in groups or setting yourself apart.",
        "your_higher_expression": "The gift of {gift} shows up when you find or create environments that genuinely support who you are. In these contexts, you contribute naturally without forcing, and belonging doesn't require self-betrayal.",
        "practical_tips": "• List the environments where you feel most alive. What do they have in common?\n• Identify one context that consistently drains you. What would it take to change or leave it?\n• What kind of culture are you trying to create through your work or presence?\n• Who are your people? If you don't know, where might you find them?",
        "remember": "You don't have to fit everywhere. Finding the right container matters."
    },
    "Brand": {
        "what_this_means": "This sphere reflects how you're perceived—your reputation, essence, and the quality others associate with you. Gene Key {gene_key} suggests that {shadow} can create a gap between your image and your truth, while {gift} represents your authentic signature when you're not performing.",
        "your_challenge": "The shadow of {shadow} might appear as hiding, over-performing, being misunderstood, or crafting an image that doesn't match who you really are. You may notice energy drain from maintaining a certain presentation.",
        "your_higher_expression": "The gift of {gift} is your natural brand—what you emanate when you're simply being yourself. When this is clear and consistent, the right opportunities and people tend to find you without forced marketing.",
        "practical_tips": "• Ask 3 people: \"What quality do you most associate with me?\" Look for patterns.\n• Where do you currently hide or over-perform? What would authenticity look like there?\n• What would you want written in a single sentence about you?\n• Notice when you feel most \"on brand\" vs. when you feel like you're pretending.",
        "remember": "Authentic presence is more effective than polished performance. Less effort, more truth."
    },
    "Pearl": {
        "what_this_means": "This sphere reflects the relationship between your inner alignment and outer prosperity—how resources, opportunities, and abundance flow (or don't) in your life. Gene Key {gene_key} suggests that {shadow} represents blocks to receiving, while {gift} represents an open channel for natural prosperity.",
        "your_challenge": "The shadow of {shadow} might show up as scarcity thinking, difficulty receiving, feast-and-famine cycles, or conflicted feelings about money and success. These patterns often have roots in deeper beliefs about worthiness or the nature of abundance.",
        "your_higher_expression": "The gift of {gift} represents prosperity as a natural flow—not grasping or manifesting, but allowing what wants to come through to actually arrive. This requires both inner alignment and practical openness to receive.",
        "practical_tips": "• Examine your beliefs about money and success. Where does {shadow} show up?\n• Practice receiving compliments, gifts, and help without deflecting—notice the discomfort.\n• What would you do if prosperity were not an issue? This reveals alignment clues.\n• Track instances of unexpected support or abundance this week. What allowed them?",
        "remember": "Prosperity often follows alignment. The blocks are usually internal."
    }
}


def get_gene_key_interpretation(gate: int, line: int) -> GeneKeyInterpretation:
    """Get Gene Key interpretation for a specific gate and line.
    
    Args:
        gate: The gate number (1-64), same as Gene Key number
        line: The line number (1-6)
    
    Returns:
        GeneKeyInterpretation with shadow, gift, siddhi meanings
    """
    # Validate inputs
    if not (1 <= gate <= 64):
        return {
            "gene_key": gate,
            "line": line,
            "shadow": "",
            "gift": "",
            "siddhi": "",
            "available": False,
            "message": f"Invalid gate number: {gate}. Must be 1-64."
        }
    
    if not (1 <= line <= 6):
        return {
            "gene_key": gate,
            "line": line,
            "shadow": "",
            "gift": "",
            "siddhi": "",
            "available": False,
            "message": f"Invalid line number: {line}. Must be 1-6."
        }
    
    # Check if Gene Key data is available
    if not is_gene_key_available(gate):
        return {
            "gene_key": gate,
            "line": line,
            "shadow": "",
            "gift": "",
            "siddhi": "",
            "available": False,
            "message": f"Gene Key {gate} interpretation not yet available. Coming soon."
        }
    
    # Get the Gene Key data
    gk_data = GENE_KEYS[gate]
    
    return {
        "gene_key": gk_data["gene_key"],
        "line": line,
        "shadow": gk_data["shadow"],
        "gift": gk_data["gift"],
        "siddhi": gk_data["siddhi"],
        "available": True,
        "message": None
    }


def get_sphere_interpretation(
    sphere_name: str,
    gene_key: int,
    line: int
) -> SphereInterpretation:
    """Generate template-based interpretation for a specific sphere.
    
    Args:
        sphere_name: Name of the sphere (Life's Work, Evolution, Radiance, Purpose)
        gene_key: The Gene Key number (1-64)
        line: The line number (1-6)
    
    Returns:
        SphereInterpretation with full template-based content
    """
    # Get Gene Key data
    gk_data = GENE_KEYS.get(gene_key, {
        "gene_key": gene_key,
        "shadow": "Unknown",
        "gift": "Unknown",
        "siddhi": "Unknown"
    })
    
    shadow = gk_data.get("shadow", "Unknown")
    gift = gk_data.get("gift", "Unknown")
    siddhi = gk_data.get("siddhi", "Unknown")
    
    # Get sphere template (fallback to Life's Work if not found)
    template = SPHERE_TEMPLATES.get(sphere_name, SPHERE_TEMPLATES["Life's Work"])
    
    # Fill in templates
    format_vars = {
        "gene_key": gene_key,
        "line": line,
        "shadow": shadow,
        "gift": gift,
        "siddhi": siddhi,
        "sphere_name": sphere_name
    }
    
    return {
        "sphere_name": sphere_name,
        "gene_key": gene_key,
        "line": line,
        "shadow": shadow,
        "gift": gift,
        "siddhi": siddhi,
        "what_this_means": template["what_this_means"].format(**format_vars),
        "your_challenge": template["your_challenge"].format(**format_vars),
        "your_higher_expression": template["your_higher_expression"].format(**format_vars),
        "practical_tips": template["practical_tips"].format(**format_vars),
        "remember": template["remember"].format(**format_vars)
    }


def get_activation_sequence(
    personality_sun_gate: int,
    personality_sun_line: int,
    personality_earth_gate: int,
    personality_earth_line: int,
    design_sun_gate: int,
    design_sun_line: int,
    design_earth_gate: int,
    design_earth_line: int
) -> ActivationSequenceResponse:
    """Build the complete Activation Sequence from HD planetary data.
    
    Activation Sequence mapping:
    - Life's Work = Personality Sun
    - Evolution = Personality Earth
    - Radiance = Design Sun
    - Purpose = Design Earth
    
    Args:
        personality_sun_gate/line: Conscious Sun placement
        personality_earth_gate/line: Conscious Earth placement
        design_sun_gate/line: Unconscious Sun placement
        design_earth_gate/line: Unconscious Earth placement
    
    Returns:
        ActivationSequenceResponse with all 4 spheres
    """
    spheres = [
        get_sphere_interpretation("Life's Work", personality_sun_gate, personality_sun_line),
        get_sphere_interpretation("Evolution", personality_earth_gate, personality_earth_line),
        get_sphere_interpretation("Radiance", design_sun_gate, design_sun_line),
        get_sphere_interpretation("Purpose", design_earth_gate, design_earth_line),
    ]
    
    return {
        "sequence_name": "Activation Sequence",
        "spheres": spheres
    }


class VenusSequenceResponse(TypedDict):
    """Full Venus Sequence response."""
    sequence_name: str
    spheres: List[SphereInterpretation]


def get_venus_sequence(
    design_moon_gate: int,
    design_moon_line: int,
    personality_mercury_gate: int,
    personality_mercury_line: int,
    design_mercury_gate: int,
    design_mercury_line: int,
    design_venus_gate: int,
    design_venus_line: int,
    personality_mars_gate: int,
    personality_mars_line: int
) -> VenusSequenceResponse:
    """Build the complete Venus Sequence from HD planetary data.
    
    Venus Sequence mapping (relationships & emotional intelligence):
    - Attraction = Design Moon (what you unconsciously attract)
    - IQ = Personality Mercury (mental intelligence in relationships)
    - EQ = Design Mercury (emotional intelligence)
    - SQ = Design Venus (spiritual intelligence in love)
    - Core = Personality Mars (deepest wound and potential in relationships)
    
    Args:
        design_moon_gate/line: Unconscious Moon placement
        personality_mercury_gate/line: Conscious Mercury placement
        design_mercury_gate/line: Unconscious Mercury placement
        design_venus_gate/line: Unconscious Venus placement
        personality_mars_gate/line: Conscious Mars placement
    
    Returns:
        VenusSequenceResponse with all 5 spheres
    """
    spheres = [
        get_sphere_interpretation("Attraction", design_moon_gate, design_moon_line),
        get_sphere_interpretation("IQ", personality_mercury_gate, personality_mercury_line),
        get_sphere_interpretation("EQ", design_mercury_gate, design_mercury_line),
        get_sphere_interpretation("SQ", design_venus_gate, design_venus_line),
        get_sphere_interpretation("Core", personality_mars_gate, personality_mars_line),
    ]
    
    return {
        "sequence_name": "Venus Sequence",
        "spheres": spheres
    }


class PearlSequenceResponse(TypedDict):
    """Full Pearl Sequence response."""
    sequence_name: str
    spheres: List[SphereInterpretation]


def get_pearl_sequence(
    design_mars_gate: int,
    design_mars_line: int,
    personality_jupiter_gate: int,
    personality_jupiter_line: int,
    personality_sun_gate: int,
    personality_sun_line: int,
    design_jupiter_gate: int,
    design_jupiter_line: int
) -> PearlSequenceResponse:
    """Build the complete Pearl Sequence from HD planetary data.
    
    Pearl Sequence mapping (prosperity & material world):
    - Vocation = Design Mars (the work you're here to do)
    - Culture = Personality Jupiter (the environment where you thrive)
    - Brand = Personality Sun (your authentic signature in the world)
    - Pearl = Design Jupiter (where prosperity flows from alignment)
    
    Args:
        design_mars_gate/line: Unconscious Mars placement
        personality_jupiter_gate/line: Conscious Jupiter placement
        personality_sun_gate/line: Conscious Sun placement
        design_jupiter_gate/line: Unconscious Jupiter placement
    
    Returns:
        PearlSequenceResponse with all 4 spheres
    """
    spheres = [
        get_sphere_interpretation("Vocation", design_mars_gate, design_mars_line),
        get_sphere_interpretation("Culture", personality_jupiter_gate, personality_jupiter_line),
        get_sphere_interpretation("Brand", personality_sun_gate, personality_sun_line),
        get_sphere_interpretation("Pearl", design_jupiter_gate, design_jupiter_line),
    ]
    
    return {
        "sequence_name": "Pearl Sequence",
        "spheres": spheres
    }


def get_available_gene_keys() -> list[int]:
    """Get list of Gene Key numbers that have interpretation data."""
    return list(GENE_KEYS.keys())


# =============================================================================
# GENE KEYS PROFILE - Unified access to all sequences
# =============================================================================

class SphereSummary(TypedDict):
    """Compact sphere data for the all_spheres array."""
    sphere_name: str
    sequence: str
    gene_key: int
    line: int
    shadow: str
    gift: str
    siddhi: str


class GeneKeysProfile(TypedDict):
    """Complete Gene Keys profile with all sequences."""
    activation_sequence: ActivationSequenceResponse
    venus_sequence: VenusSequenceResponse
    pearl_sequence: PearlSequenceResponse
    all_spheres: List[SphereSummary]


def build_gene_keys_profile(
    # Activation Sequence planets
    personality_sun_gate: int,
    personality_sun_line: int,
    personality_earth_gate: int,
    personality_earth_line: int,
    design_sun_gate: int,
    design_sun_line: int,
    design_earth_gate: int,
    design_earth_line: int,
    # Venus Sequence planets
    design_moon_gate: int,
    design_moon_line: int,
    personality_mercury_gate: int,
    personality_mercury_line: int,
    design_mercury_gate: int,
    design_mercury_line: int,
    design_venus_gate: int,
    design_venus_line: int,
    personality_mars_gate: int,
    personality_mars_line: int,
    # Pearl Sequence planets
    design_mars_gate: int,
    design_mars_line: int,
    personality_jupiter_gate: int,
    personality_jupiter_line: int,
    design_jupiter_gate: int,
    design_jupiter_line: int,
) -> GeneKeysProfile:
    """Build complete Gene Keys profile from all planetary data.
    
    This function builds all three sequences from a single set of planetary
    data, avoiding multiple HD computations.
    
    Returns:
        GeneKeysProfile with activation, venus, pearl sequences and flattened spheres
    """
    # Build Activation Sequence
    activation = get_activation_sequence(
        personality_sun_gate, personality_sun_line,
        personality_earth_gate, personality_earth_line,
        design_sun_gate, design_sun_line,
        design_earth_gate, design_earth_line
    )
    
    # Build Venus Sequence
    venus = get_venus_sequence(
        design_moon_gate, design_moon_line,
        personality_mercury_gate, personality_mercury_line,
        design_mercury_gate, design_mercury_line,
        design_venus_gate, design_venus_line,
        personality_mars_gate, personality_mars_line
    )
    
    # Build Pearl Sequence (Note: Brand uses personality_sun, same as Life's Work)
    pearl = get_pearl_sequence(
        design_mars_gate, design_mars_line,
        personality_jupiter_gate, personality_jupiter_line,
        personality_sun_gate, personality_sun_line,  # Brand = Personality Sun
        design_jupiter_gate, design_jupiter_line
    )
    
    # Flatten all spheres with sequence attribution
    all_spheres: List[SphereSummary] = []
    
    for sphere in activation["spheres"]:
        all_spheres.append({
            "sphere_name": sphere["sphere_name"],
            "sequence": "Activation",
            "gene_key": sphere["gene_key"],
            "line": sphere["line"],
            "shadow": sphere["shadow"],
            "gift": sphere["gift"],
            "siddhi": sphere["siddhi"]
        })
    
    for sphere in venus["spheres"]:
        all_spheres.append({
            "sphere_name": sphere["sphere_name"],
            "sequence": "Venus",
            "gene_key": sphere["gene_key"],
            "line": sphere["line"],
            "shadow": sphere["shadow"],
            "gift": sphere["gift"],
            "siddhi": sphere["siddhi"]
        })
    
    for sphere in pearl["spheres"]:
        all_spheres.append({
            "sphere_name": sphere["sphere_name"],
            "sequence": "Pearl",
            "gene_key": sphere["gene_key"],
            "line": sphere["line"],
            "shadow": sphere["shadow"],
            "gift": sphere["gift"],
            "siddhi": sphere["siddhi"]
        })
    
    return {
        "activation_sequence": activation,
        "venus_sequence": venus,
        "pearl_sequence": pearl,
        "all_spheres": all_spheres
    }

