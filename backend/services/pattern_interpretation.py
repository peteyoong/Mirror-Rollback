"""Pattern Interpretation Service

Generates rich, cached pattern interpretations for the 7 Mirror domains.
Each interpretation follows the standardized Mirror Language Structure:
- What may be happening: Observable pattern or situation
- How this may feel: Emotional/experiential context
- What to notice: Specific observation prompt
- Reflection question: Single clear self-inquiry prompt

Also includes:
- Challenge: Common ways this can become difficult
- Genius: The strength or gift embedded in this pattern
- Practical Experiments: 3-4 reflective suggestions

Philosophy (aligned with Mirror):
- Grounded, reflective tone
- Non-deterministic language
- Tentative phrasing: "may", "might", "could"
- Never prescriptive or identity-defining
- Concrete behavioral language (not vague spiritual terms)
"""

import os
import json
import logging
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from services.mirror_language import (
    clean_interpretation_text,
    validate_language,
    get_reflection_question,
    get_domain_interpretation,
    DOMAIN_TEMPLATES
)

logger = logging.getLogger(__name__)

# Cache TTL - interpretations become stale after 7 days
INTERPRETATION_CACHE_TTL_DAYS = 7


def generate_cache_key(user_id: str, domain_id: str, signal_hash: str) -> str:
    """Generate a unique cache key for pattern interpretation."""
    combined = f"{user_id}:{domain_id}:{signal_hash}"
    return hashlib.md5(combined.encode()).hexdigest()


def compute_signal_hash(matched_signals: List[Dict[str, Any]], signal_strength: str) -> str:
    """Compute a hash of the signals to detect staleness."""
    signal_labels = sorted([s.get("label", "") for s in matched_signals])
    signal_str = "|".join(signal_labels) + f"|{signal_strength}"
    return hashlib.md5(signal_str.encode()).hexdigest()[:12]


def is_interpretation_stale(
    cached: Dict[str, Any],
    current_signal_hash: str,
    ttl_days: int = INTERPRETATION_CACHE_TTL_DAYS
) -> bool:
    """Check if cached interpretation is stale."""
    if not cached:
        return True
    
    # Check signal hash - if signals changed, interpretation is stale
    if cached.get("signal_hash") != current_signal_hash:
        logger.debug("[PatternInterpretation] Signal hash mismatch - stale")
        return True
    
    # Check TTL
    created_at_str = cached.get("created_at")
    if not created_at_str:
        return True
    
    try:
        created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
        age = datetime.now(timezone.utc) - created_at
        if age.days >= ttl_days:
            logger.debug(f"[PatternInterpretation] Cache expired after {age.days} days")
            return True
    except Exception as e:
        logger.warning(f"[PatternInterpretation] Error parsing cached date: {e}")
        return True
    
    return False


# Fallback templates when LLM is unavailable - now using standardized structure
FALLBACK_INTERPRETATIONS = {
    "energy_vitality": {
        "what_happening": "You may be feeling a persistent pull on your energy—either too much demand or not enough outlet.",
        "how_feels": "This can show up as restlessness, fatigue, or a sense of running on empty.",
        "what_notice": "Notice what activities leave you feeling more alive versus depleted.",
        "story": "There may be days when energy flows easily, and days when it feels scarce. This pattern often emerges around questions of pace, sustainability, and what truly nourishes you.",
        "pattern": "The dynamic here involves how life force moves through you—when it rises, when it depletes, and what conditions seem to influence the ebb and flow.",
        "challenge": "A common difficulty is pushing through when rest is needed, or over-committing to prove vitality when the body signals otherwise.",
        "genius": "The gift embedded here is a deep attunement to your own rhythms. When honored, this sensitivity becomes a compass for sustainable living.",
        "experiments": [
            "Notice when your energy naturally peaks and dips throughout the day",
            "Experiment with doing less on one day this week and observe what shifts",
            "Track what activities leave you feeling more alive versus depleted",
            "Try pausing before commitments to check in with your actual capacity"
        ]
    },
    "emotional_landscape": {
        "what_happening": "A familiar emotional pattern may be surfacing—something that keeps returning.",
        "how_feels": "This can feel like being caught in a loop, or like the same feeling finding different triggers.",
        "what_notice": "Notice what situation keeps activating this emotional response.",
        "story": "Emotions may move through you like weather—sometimes clear, sometimes stormy, sometimes still. This pattern often appears when feelings are asking for attention or integration.",
        "pattern": "The dynamic here involves the texture of your inner emotional life—how feelings arise, how they're processed, and how they inform your experience.",
        "challenge": "A common difficulty is either over-identifying with emotions or suppressing them entirely, losing the wisdom they carry.",
        "genius": "The gift embedded here is emotional depth and sensitivity. When honored, this becomes a rich source of intuition and empathy.",
        "experiments": [
            "Name the emotion you're experiencing right now without trying to change it",
            "Notice which emotions feel most familiar and which feel foreign",
            "Experiment with sitting with an uncomfortable feeling for two minutes",
            "Track what triggered your strongest emotional response today"
        ]
    },
    "relationships_connection": {
        "what_happening": "Something in your relational world keeps asking for attention.",
        "how_feels": "This might show up as tension, longing, or a persistent question about connection.",
        "what_notice": "Notice which relationship or dynamic keeps coming to mind.",
        "story": "Connection may feel layered right now—some relationships pulling closer, others asking for space. This pattern often emerges when something in your relational world is shifting.",
        "pattern": "The dynamic here involves how you connect, how you maintain boundaries, and what you need from others versus what you offer.",
        "challenge": "A common difficulty is either merging too completely or isolating too defensively, losing the balance that allows genuine intimacy.",
        "genius": "The gift embedded here is relational awareness—a capacity to sense what connections need and to navigate complexity with care.",
        "experiments": [
            "Reach out to someone you've been thinking about but haven't contacted",
            "Notice one relationship where you're holding back something true",
            "Experiment with asking for something you need instead of hinting",
            "Observe how you feel after different social interactions today"
        ]
    },
    "work_purpose": {
        "what_happening": "Questions about work or purpose keep surfacing.",
        "how_feels": "This might feel like restlessness, dissatisfaction, or a pull toward something more meaningful.",
        "what_notice": "Notice what kind of contribution feels important to you right now.",
        "story": "The question of contribution may feel alive—what's worth doing, what matters, what you're building. This pattern often emerges when alignment between effort and meaning needs attention.",
        "pattern": "The dynamic here involves the gap (or harmony) between what you spend energy on and what actually matters to you.",
        "challenge": "A common difficulty is either over-identifying with productivity or losing touch with what makes effort feel meaningful.",
        "genius": "The gift embedded here is a capacity for purposeful work—when aligned, your effort carries genuine intention.",
        "experiments": [
            "Identify one task that feels genuinely meaningful and do it first today",
            "Notice where your work energy flows naturally without forcing",
            "Ask yourself: 'What would I still do even if no one noticed?'",
            "Experiment with doing one thing slowly and thoroughly instead of quickly"
        ]
    },
    "growth_transformation": {
        "what_happening": "Something in you may be ready for change.",
        "how_feels": "This can feel like pressure, anticipation, or discomfort with the status quo.",
        "what_notice": "Notice what part of your life feels too small or outdated.",
        "story": "Something in you may be ready to shift—an old pattern loosening, a new possibility emerging. Growth often feels uncomfortable precisely because it's real.",
        "pattern": "The dynamic here involves the tension between what was and what's becoming—the discomfort of transformation.",
        "challenge": "A common difficulty is either forcing change before it's ready or resisting it so hard that pressure builds.",
        "genius": "The gift embedded here is the capacity for genuine transformation—not just surface change but real evolution.",
        "experiments": [
            "Identify one habit or pattern that no longer serves you",
            "Notice what you're resisting that might be ready to shift",
            "Ask yourself: 'What am I afraid will happen if I change?'",
            "Experiment with doing one familiar thing in a completely different way"
        ]
    },
    "intuition_inner_knowing": {
        "what_happening": "Your inner knowing may be trying to get your attention.",
        "how_feels": "This can show up as a persistent sense that something is off, or a quiet certainty you keep ignoring.",
        "what_notice": "Notice what your gut has been telling you that you haven't acted on.",
        "story": "There may be a quieter voice trying to reach you—not loud like thought, more like a persistent sense of something important. Intuition often speaks when we slow down enough to notice.",
        "pattern": "The dynamic here involves the relationship between thinking and knowing—how you access deeper intelligence beyond analysis.",
        "challenge": "A common difficulty is dismissing intuition as irrational, or conversely, confusing wishful thinking for genuine knowing.",
        "genius": "The gift embedded here is direct knowing—access to insight that doesn't require deliberation.",
        "experiments": [
            "Before making a decision today, pause and notice your first instinct",
            "Track a hunch you have and see how it plays out",
            "Ask yourself a question and notice the immediate body response",
            "Experiment with following a quiet inner prompt without analyzing it first"
        ]
    },
    "identity_expression": {
        "what_happening": "Questions about who you are or how you express yourself keep returning.",
        "how_feels": "This might feel like uncertainty, a desire for authenticity, or friction between inner and outer selves.",
        "what_notice": "Notice where you feel most like yourself, and where you feel constrained.",
        "story": "The question of who you are may feel present—not an identity crisis, but a quiet inquiry. This pattern often emerges when authentic expression wants more space.",
        "pattern": "The dynamic here involves the alignment between inner experience and outer presentation—how fully you allow yourself to be seen.",
        "challenge": "A common difficulty is either hiding behind a constructed persona or oversharing without discernment.",
        "genius": "The gift embedded here is authentic presence—the capacity to show up as who you actually are.",
        "experiments": [
            "Notice one way you're performing today instead of just being",
            "Share something true about yourself that you usually keep private",
            "Ask yourself: 'Where am I pretending to be different than I am?'",
            "Experiment with dropping one small mask for one hour"
        ]
    },
}

# Old fallback interpretations for legacy domain IDs
LEGACY_FALLBACK_INTERPRETATIONS = {
    "identity_direction": {
        "story": "Questions about who you are and where you're going may be surfacing. This pattern often appears at crossroads, transitions, or when something about your current path feels uncertain.",
        "pattern": "The dynamic here involves the relationship between self-concept and life direction—how your sense of identity shapes your choices and vice versa.",
        "challenge": "A common difficulty is either rigid attachment to a fixed identity or feeling lost without external validation of who you should be.",
        "genius": "The gift embedded here is the capacity for authentic self-definition. When honored, this becomes a compass that guides meaningful decisions.",
        "experiments": [
            "Complete the sentence: 'Right now, I am someone who...'",
            "Notice when you feel most yourself versus when you feel like you're performing",
            "Experiment with saying 'I don't know' when asked about your plans",
            "Identify one area where you're waiting for permission to be who you already are"
        ]
    },
    "mind_meaning": {
        "story": "The mind may be active with questions, analysis, or a search for understanding. This pattern often emerges when something is asking to be comprehended or when mental activity becomes pronounced.",
        "pattern": "The dynamic here involves how you make sense of experience—through thinking, questioning, analyzing, and meaning-making.",
        "challenge": "A common difficulty is overthinking as a way to avoid feeling, or seeking certainty in places where ambiguity is unavoidable.",
        "genius": "The gift embedded here is intellectual depth and curiosity. When honored, this becomes a tool for insight and understanding.",
        "experiments": [
            "Notice one thought loop that keeps returning and gently name it",
            "Experiment with not solving a problem for one full day",
            "Ask yourself: 'What am I trying to understand right now?'",
            "Try writing down your thoughts for 5 minutes without editing"
        ]
    },
    "expression_action": {
        "story": "Something may be wanting to be expressed, created, or acted upon. This pattern often appears when creativity is stirring or when action feels either urgent or blocked.",
        "pattern": "The dynamic here involves how inner impulses become outer expression—through words, creativity, movement, or decisive action.",
        "challenge": "A common difficulty is either acting impulsively without discernment or suppressing expression until it builds into pressure.",
        "genius": "The gift embedded here is creative and expressive capacity. When honored, this becomes a channel for bringing something new into the world.",
        "experiments": [
            "Notice what wants to be expressed but hasn't found its form yet",
            "Experiment with creating something small with no plan for it",
            "Track when you censor yourself and what you were about to say",
            "Try one small action on something you've been putting off"
        ]
    },
    "relationships_boundaries": {
        "story": "Themes around connection, closeness, or boundaries may be present. This pattern often appears when relationships are in focus—whether through intimacy, conflict, or questions of belonging.",
        "pattern": "The dynamic here involves the space between self and other—how you connect, where you draw lines, and how relationships shape your experience.",
        "challenge": "A common difficulty is either merging with others and losing yourself, or maintaining such strong boundaries that connection becomes difficult.",
        "genius": "The gift embedded here is relational intelligence. When honored, this becomes the capacity for deep, authentic connection while maintaining a clear sense of self.",
        "experiments": [
            "Notice where you automatically say 'yes' when you mean 'maybe'",
            "Experiment with expressing one need you normally keep quiet about",
            "Track which relationships energize you versus deplete you",
            "Try taking 5 minutes of solitude before responding to a request"
        ]
    },
    "growth_transformation": {
        "story": "Something may be shifting, ending, or beginning. This pattern often emerges during periods of change, when old ways of being are giving way to something new.",
        "pattern": "The dynamic here involves the process of change itself—how growth happens, what resists transformation, and what supports it.",
        "challenge": "A common difficulty is either rushing transformation or resisting change so strongly that growth becomes painful.",
        "genius": "The gift embedded here is the capacity for renewal. When honored, this becomes an ability to move through transitions with wisdom and resilience.",
        "experiments": [
            "Identify one thing you're ready to release, even slightly",
            "Notice what feels like it's dying and what feels like it's being born",
            "Experiment with welcoming rather than resisting an uncomfortable change",
            "Ask yourself: 'What version of me is trying to emerge?'"
        ]
    }
}


def get_fallback_interpretation(domain_id: str) -> Dict[str, Any]:
    """Get fallback interpretation when LLM is unavailable.
    
    Now returns the standardized Mirror Language Structure.
    """
    base = FALLBACK_INTERPRETATIONS.get(domain_id)
    if not base:
        # Check legacy fallbacks
        base = LEGACY_FALLBACK_INTERPRETATIONS.get(domain_id, {
            "what_happening": "A pattern may be emerging in this area of your life.",
            "how_feels": "You might notice what feels familiar about this theme.",
            "what_notice": "Notice when this theme appears in your daily life.",
            "story": "A pattern may be emerging in this area of your life. You might notice what feels familiar about this theme.",
            "pattern": "The dynamic here involves recurring themes that may be asking for your attention.",
            "challenge": "A common difficulty is not seeing the pattern clearly while you're inside of it.",
            "genius": "The gift embedded here may only become visible when you stop trying to fix it.",
            "experiments": [
                "Notice when this theme appears in your daily life",
                "Experiment with observing rather than solving",
                "Track what triggers this pattern to intensify",
                "Try naming the pattern out loud when you catch it"
            ]
        })
    
    # Ensure all required fields are present
    return {
        "what_happening": base.get("what_happening", base.get("story", "")[:100] + "..." if len(base.get("story", "")) > 100 else base.get("story", "")),
        "how_feels": base.get("how_feels", ""),
        "what_notice": base.get("what_notice", ""),
        "story": base.get("story", ""),
        "pattern": base.get("pattern", ""),
        "challenge": base.get("challenge", ""),
        "genius": base.get("genius", ""),
        "experiments": base.get("experiments", [])
    }


async def generate_pattern_interpretation(
    domain_id: str,
    domain_name: str,
    signal_strength: str,
    matched_signals: List[Dict[str, Any]],
    matched_sources: List[str]
) -> Dict[str, Any]:
    """Generate rich pattern interpretation using LLM.
    
    Returns a dictionary with:
    - story: Short narrative
    - pattern: Underlying dynamic explanation
    - challenge: Common difficulties
    - genius: Embedded gift/strength
    - experiments: 3-4 practical suggestions
    """
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')
        if not EMERGENT_LLM_KEY:
            logger.warning("[PatternInterpretation] No LLM key, using fallback")
            return get_fallback_interpretation(domain_id)
        
        # Build context from signals
        signal_labels = [s.get("label", "") for s in matched_signals[:8]]
        sources_str = ", ".join(matched_sources) if matched_sources else "multiple sources"
        signals_str = "; ".join(signal_labels) if signal_labels else "various indicators"
        
        system_prompt = """You are a reflective assistant for Mirror, an app that helps people notice patterns in their inner life without prescribing solutions.

CRITICAL TONE:
- Grounded, not mystical
- Reflective, not deterministic
- Non-prescriptive
- Use tentative language: "may", "might", "could", "often", "sometimes"
- Never use: "you are", "you must", "the universe", "your destiny", "you need to"
- Warm but not sentimental
- Concise and scannable

You will generate a pattern interpretation with 5 sections. Each section must be SHORT and readable:

1. STORY (40-60 words): A short narrative describing what this pattern may feel like in daily life. Written in second person but tentative.

2. PATTERN (30-50 words): A brief explanation of the underlying dynamic. What's happening beneath the surface.

3. CHALLENGE (30-50 words): Common ways this pattern can become difficult or limiting. One or two specific examples.

4. GENIUS (30-50 words): The strength or gift embedded in this pattern when it's honored or integrated.

5. EXPERIMENTS (4 items, each 10-20 words): Specific, practical micro-experiments or reflection prompts. These should be actionable today.

Respond ONLY with valid JSON in this exact format:
{
  "story": "...",
  "pattern": "...",
  "challenge": "...",
  "genius": "...",
  "experiments": ["...", "...", "...", "..."]
}"""

        user_prompt = f"""Generate a pattern interpretation for the "{domain_name}" domain.

Current signal strength: {signal_strength}
Contributing signals: {signals_str}
Signal sources: {sources_str}

Remember:
- Keep each section concise and scannable
- Use tentative, non-deterministic language
- Make experiments specific and actionable
- Do not explain what signals mean - just reflect the theme"""

        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"pattern_interpretation_{domain_id}",
            system_message=system_prompt
        )
        chat.with_model("openai", "gpt-4o-mini")
        
        response = await chat.send_message(
            UserMessage(text=user_prompt)
        )
        
        response_text = response.strip() if isinstance(response, str) else str(response).strip()
        
        # Clean up response - remove markdown code blocks if present
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            # Remove first line (```json) and last line (```)
            lines = [line for line in lines if not line.startswith("```")]
            response_text = "\n".join(lines)
        
        # Parse JSON
        interpretation = json.loads(response_text)
        
        # Validate required fields
        required_fields = ["story", "pattern", "challenge", "genius", "experiments"]
        for field in required_fields:
            if field not in interpretation:
                logger.warning(f"[PatternInterpretation] Missing field: {field}")
                return get_fallback_interpretation(domain_id)
        
        # Validate experiments is a list
        if not isinstance(interpretation["experiments"], list) or len(interpretation["experiments"]) < 3:
            logger.warning("[PatternInterpretation] Invalid experiments format")
            return get_fallback_interpretation(domain_id)
        
        # Check for forbidden patterns
        forbidden = ["you are ", "you must", "the universe", "your destiny", "you need to"]
        full_text = json.dumps(interpretation).lower()
        for phrase in forbidden:
            if phrase in full_text:
                logger.warning(f"[PatternInterpretation] Forbidden phrase: {phrase}")
                return get_fallback_interpretation(domain_id)
        
        logger.info(f"[PatternInterpretation] Generated interpretation for {domain_name}")
        return interpretation
        
    except json.JSONDecodeError as e:
        logger.error(f"[PatternInterpretation] JSON parse error: {e}")
        return get_fallback_interpretation(domain_id)
    except Exception as e:
        logger.error(f"[PatternInterpretation] LLM error: {e}")
        return get_fallback_interpretation(domain_id)
