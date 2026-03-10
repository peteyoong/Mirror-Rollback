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
# These templates provide consistent, practical, reflective guidance
# based on the sphere and Gene Key qualities. No LLM generation.

SPHERE_TEMPLATES = {
    "Life's Work": {
        "what_this_means": "Your Life's Work sphere represents the core theme of your vocation—how you're designed to contribute to the world. This isn't about a specific job, but rather the underlying energy and quality you bring to whatever you do. The Gene Key {gene_key} suggests that your work in life involves navigating the spectrum from {shadow} toward {gift}.",
        "your_challenge": "The shadow of {shadow} may show up in your work life as a pattern you unconsciously fall into, especially under stress. You might notice this in moments of doubt, frustration, or when you feel your contributions aren't valued. This isn't a flaw to fix—it's a signal pointing toward where your gift wants to emerge.",
        "your_higher_expression": "When you're aligned with your Life's Work, the gift of {gift} naturally flows through what you do. This isn't something to force or perform—it emerges when you're engaged with work that genuinely calls to you. Others may recognize this quality in you before you do.",
        "practical_tips": "Notice when {shadow} patterns arise in your work. Instead of fighting them, get curious. What would {gift} look like in this situation? You might experiment with small moments of bringing more {gift} into your daily tasks—not as a goal, but as an exploration.",
        "remember": "Your Life's Work isn't something you find—it's something you uncover by paying attention to what naturally engages you. The journey from {shadow} to {gift} is itself the work."
    },
    "Evolution": {
        "what_this_means": "Your Evolution sphere represents your path of growth and learning in this lifetime. Gene Key {gene_key} suggests that your evolution involves transforming {shadow} into {gift}. This isn't about becoming someone different—it's about becoming more fully yourself.",
        "your_challenge": "The shadow of {shadow} may appear as an ongoing challenge in your life—a pattern that keeps showing up in different forms. Rather than seeing this as a problem to solve, consider it as the raw material for your evolution. This challenge is pointing you somewhere.",
        "your_higher_expression": "As you evolve, the gift of {gift} becomes more accessible. This doesn't mean the shadow disappears—it means you develop a different relationship with it. You might notice yourself responding to old triggers with new awareness.",
        "practical_tips": "Track the moments when {shadow} shows up. What situations trigger it? What does it feel like in your body? The more familiar you become with this pattern, the more choice you have in how you respond. Consider: what would {gift} feel like as a response?",
        "remember": "Evolution isn't linear. You may cycle through {shadow} and {gift} many times. Each cycle brings deeper understanding. Trust the process."
    },
    "Radiance": {
        "what_this_means": "Your Radiance sphere represents what you naturally emanate when you're not trying to be anything. Gene Key {gene_key} suggests that your authentic radiance emerges as you integrate the journey from {shadow} through {gift}. This is the quality that draws others to you without effort.",
        "your_challenge": "The shadow of {shadow} can dim your natural radiance, often through unconscious patterns of self-protection or trying too hard. When you notice yourself contracted, forcing, or performing, you may be in the shadow expression of this sphere.",
        "your_higher_expression": "True radiance isn't something you do—it's what happens when you stop trying. The gift of {gift} shines through you naturally when you're at ease with yourself. Others sense this as an attractive quality, though you may not even notice it.",
        "practical_tips": "Notice the difference between trying to radiate something and simply being present. When do you feel most naturally yourself? Those are the moments when your radiance is active. Practice allowing rather than performing.",
        "remember": "You don't need to work on your radiance. It's already there. The work is in removing the barriers—the shadow patterns—that block it from naturally expressing."
    },
    "Purpose": {
        "what_this_means": "Your Purpose sphere represents the deeper reason behind your life journey. Gene Key {gene_key} suggests that your purpose involves the alchemical transformation from {shadow} to {gift}, ultimately touching {siddhi}. This isn't a destination—it's a direction that gives meaning to everything else.",
        "your_challenge": "The shadow of {shadow} can create a sense of purposelessness or misdirection when you're identified with it. You might question whether you're on the right path, or feel disconnected from deeper meaning. These moments of doubt are actually invitations to look deeper.",
        "your_higher_expression": "When you're connected to your purpose, the gift of {gift} infuses your actions with meaning. You don't need to know the grand plan—you simply feel aligned. This sense of rightness comes not from achieving goals, but from living in integrity with your nature.",
        "practical_tips": "Purpose isn't found through thinking—it's felt. Notice the activities, relationships, and moments that give you a sense of meaning. What do they have in common? How does {gift} show up in those moments?",
        "remember": "Your purpose isn't something to figure out intellectually. It reveals itself through living. The transformation from {shadow} to {gift} IS your purpose in action."
    },
    # =========================================================================
    # VENUS SEQUENCE SPHERES
    # =========================================================================
    "Attraction": {
        "what_this_means": "Your Attraction sphere reveals the energetic signature that draws relationships and experiences into your life. Gene Key {gene_key} suggests that what you attract is shaped by the dance between {shadow} and {gift}. This isn't about manipulation—it's about understanding the invisible forces at play in your relational field.",
        "your_challenge": "The shadow of {shadow} can create unconscious patterns in what you attract. You might notice recurring themes in relationships or situations that feel 'fated' but frustrating. These patterns aren't punishment—they're mirrors showing you where transformation wants to happen.",
        "your_higher_expression": "When operating from {gift}, your attraction field shifts. You begin drawing in relationships and experiences that support your growth rather than replaying old patterns. This happens naturally as you become more conscious of your own energy.",
        "practical_tips": "Pay attention to what keeps showing up in your life—especially in relationships. What's the common thread? Instead of trying to change what you attract, explore how {gift} might already be emerging in these situations.",
        "remember": "You are always attracting what matches your frequency. The path from {shadow} to {gift} changes not just you, but the entire field of what becomes possible in your relationships."
    },
    "IQ": {
        "what_this_means": "Your IQ sphere in the Venus Sequence represents your mental intelligence—how you process, analyze, and communicate in relationships. Gene Key {gene_key} shapes your cognitive style, moving between {shadow} and {gift}. This isn't about being 'smart'—it's about how your mind serves or sabotages connection.",
        "your_challenge": "The shadow of {shadow} can manifest as mental patterns that create distance in relationships—overthinking, analyzing others, or using intellect as a shield. You might catch yourself in your head when your heart is needed.",
        "your_higher_expression": "The gift of {gift} transforms your mental intelligence into a bridge for deeper connection. Your thoughts become clearer, your communication more precise, and your mind becomes an ally rather than an obstacle to intimacy.",
        "practical_tips": "Notice when your mind takes over in relationships. What triggers analytical mode? Experiment with dropping from your head into your heart mid-conversation. What would {gift} sound like if you spoke from that place?",
        "remember": "Your mind is a tool, not your identity. The journey from {shadow} to {gift} is about putting your intelligence in service of love rather than protection."
    },
    "EQ": {
        "what_this_means": "Your EQ sphere represents your emotional intelligence—the capacity to feel, process, and navigate the emotional currents in relationships. Gene Key {gene_key} colors your emotional landscape with the spectrum from {shadow} to {gift}. This sphere reveals how you handle the waves of feeling that relationships inevitably bring.",
        "your_challenge": "The shadow of {shadow} can distort your emotional responses—either through suppression, projection, or getting lost in emotional storms. You might notice patterns of reactivity or numbness that create distance from those you love.",
        "your_higher_expression": "The gift of {gift} brings emotional mastery—not control, but the ability to ride emotional waves without being capsized by them. From this place, your emotions become a source of wisdom and connection rather than chaos.",
        "practical_tips": "Track your emotional patterns in relationships. Where does {shadow} show up? What does it feel like in your body? Practice staying present with difficult emotions rather than reacting or withdrawing.",
        "remember": "Emotional intelligence isn't about having 'good' emotions. It's about having a wise relationship with all emotions. The path from {shadow} to {gift} is walked one feeling at a time."
    },
    "SQ": {
        "what_this_means": "Your SQ sphere represents your spiritual intelligence—your capacity for depth, meaning, and transcendence in relationships. Gene Key {gene_key} influences how you access the sacred dimension of love, moving between {shadow} and {gift}. This sphere connects your relationships to something larger than personal satisfaction.",
        "your_challenge": "The shadow of {shadow} can either close you off from spiritual connection or create spiritual bypassing—using transcendent concepts to avoid real intimacy. You might notice a tendency to either dismiss the sacred or hide in it.",
        "your_higher_expression": "The gift of {gift} brings genuine spiritual depth to your relationships. This isn't about shared beliefs—it's about the capacity to touch something holy in the space between you and another. Love becomes a gateway to the infinite.",
        "practical_tips": "Consider what 'spiritual' means in your relationships. Is it abstract or embodied? How might {gift} show up in everyday moments with those you love? Look for the sacred in the ordinary.",
        "remember": "Spiritual intelligence in relationships isn't about perfection or transcendence—it's about presence. The journey from {shadow} to {gift} deepens your capacity to be truly here with another."
    },
    "Core": {
        "what_this_means": "Your Core sphere represents the deepest wound and highest potential in your relational life. Gene Key {gene_key} reveals the {shadow} that you've carried, often from early life, and the {gift} that emerges as you heal. This is the most tender and powerful sphere of the Venus Sequence.",
        "your_challenge": "The shadow of {shadow} connects to your deepest vulnerability—the place where love has wounded you. This isn't something to 'get over' but something to integrate. You might notice this pattern echoing through your most significant relationships.",
        "your_higher_expression": "The gift of {gift} emerges precisely from your core wound. As you bring consciousness to this tender place, it becomes the source of your greatest capacity for love. Your wound becomes your medicine.",
        "practical_tips": "This sphere asks for gentleness. What is your earliest memory of {shadow}? How does it show up in your current relationships? The path isn't to fix this wound but to hold it with compassion.",
        "remember": "Your core wound is not your shame—it's your initiation. The transformation from {shadow} to {gift} at this level changes everything. Go slowly. Be kind to yourself."
    },
    # =========================================================================
    # PEARL SEQUENCE SPHERES
    # =========================================================================
    "Vocation": {
        "what_this_means": "Your Vocation sphere in the Pearl Sequence represents the work you're here to do in the world—not as a job title, but as a calling that emerges from your unique genius. Gene Key {gene_key} shapes how you offer your gifts, moving between {shadow} and {gift}. This is where your inner work meets outer contribution.",
        "your_challenge": "The shadow of {shadow} can distort your relationship with work—either through over-identification with achievement or through hiding your gifts from the world. You might notice patterns of burnout, undervaluing yourself, or working in ways that don't align with your nature.",
        "your_higher_expression": "The gift of {gift} transforms your work into genuine service. When operating from this frequency, work becomes effortless—not because it's easy, but because it flows from who you truly are. You find yourself doing what you love and being valued for it.",
        "practical_tips": "Notice where {shadow} shows up in your work life. What would change if you approached your vocation from {gift} instead? Consider: what work would you do even if no one paid you? That's closer to your true vocation.",
        "remember": "Your vocation isn't found—it's uncovered by removing the layers of conditioning about what you 'should' do. The path from {shadow} to {gift} reveals what you're actually here to offer."
    },
    "Culture": {
        "what_this_means": "Your Culture sphere represents the environment and community where your gifts can flourish. Gene Key {gene_key} influences what kind of culture you thrive in and what you contribute to collective spaces. The journey from {shadow} to {gift} shapes how you relate to groups, organizations, and society.",
        "your_challenge": "The shadow of {shadow} can create friction with collective environments—either through conforming too much and losing yourself, or through rebelling in ways that isolate you. You might notice patterns of not fitting in or compromising your authenticity to belong.",
        "your_higher_expression": "The gift of {gift} allows you to find or create cultures where you genuinely belong. From this frequency, you contribute something unique to the collective while remaining true to yourself. You become a cultural catalyst.",
        "practical_tips": "What environments bring out the worst in you? What environments bring out your best? The difference often relates to {shadow} and {gift}. Consider what kind of culture would support your vocation.",
        "remember": "You don't have to fit into existing cultures—you can help create new ones. The transformation from {shadow} to {gift} makes you a builder of the environments your gifts need to flourish."
    },
    "Brand": {
        "what_this_means": "Your Brand sphere represents the essence of how you're perceived in the world—your reputation, your unique signature, the quality people associate with you. Gene Key {gene_key} shapes your natural brand, moving between the shadow of {shadow} and the gift of {gift}. This is about authenticity, not marketing.",
        "your_challenge": "The shadow of {shadow} can create a gap between how you present yourself and who you truly are. You might notice patterns of hiding, performing, or being misunderstood. The challenge is to let your authentic frequency be seen.",
        "your_higher_expression": "The gift of {gift} is your true brand—the quality that naturally emanates when you're being yourself. When operating from this frequency, you attract the right opportunities and relationships without forcing or pretending.",
        "practical_tips": "How do others describe you? How do you want to be known? Notice the gap. What would it take to let {gift} be more visible in how you show up? Authentic branding is about revealing, not constructing.",
        "remember": "Your real brand already exists—it's the frequency you naturally broadcast. The journey from {shadow} to {gift} is about getting out of your own way so your true essence can be recognized."
    },
    "Pearl": {
        "what_this_means": "Your Pearl sphere represents the culmination of the Pearl Sequence—the point where your inner transformation becomes outer prosperity. Gene Key {gene_key} reveals how abundance flows to you when you align with your true nature. The path from {shadow} to {gift} unlocks genuine prosperity.",
        "your_challenge": "The shadow of {shadow} can block the flow of prosperity in your life—through beliefs about scarcity, unworthiness, or the relationship between money and spirituality. You might notice patterns of struggle, feast-and-famine cycles, or discomfort with receiving.",
        "your_higher_expression": "The gift of {gift} opens the channels of abundance. This isn't about manifesting or manipulating reality—it's about removing the internal blocks that prevent natural prosperity from flowing. From this frequency, you receive in proportion to what you give.",
        "practical_tips": "What is your relationship with prosperity? Where does {shadow} show up in your beliefs about money, success, or receiving? The Pearl isn't about wanting more—it's about opening to what's already trying to flow to you.",
        "remember": "Prosperity is a natural side effect of alignment. The transformation from {shadow} to {gift} doesn't make you wealthy—it removes what's been blocking your natural abundance. The Pearl emerges from the friction of life itself."
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


def get_available_gene_keys() -> list[int]:
    """Get list of Gene Key numbers that have interpretation data."""
    return list(GENE_KEYS.keys())
