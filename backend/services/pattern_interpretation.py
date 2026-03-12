"""Pattern Interpretation Service

Generates rich, cached pattern interpretations for the 7 Mirror domains.
Each interpretation includes:
- Story: Short narrative of what the pattern may feel like
- Pattern: Explanation of the underlying dynamic
- Challenge: Common ways this can become difficult or limiting
- Genius: The strength or gift embedded in this pattern
- Practical Experiments: 3-4 reflective suggestions or behavioral experiments

Philosophy (aligned with Mirror):
- Grounded, reflective tone
- Non-deterministic language
- Tentative phrasing: "may", "might", "could"
- Never prescriptive or identity-defining
"""

import os
import json
import logging
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List

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


# Fallback templates when LLM is unavailable
FALLBACK_INTERPRETATIONS = {
    "energy_vitality": {
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
    """Get fallback interpretation when LLM is unavailable."""
    return FALLBACK_INTERPRETATIONS.get(domain_id, {
        "story": "A pattern may be emerging in this area of your life. You might notice what feels familiar about this theme.",
        "pattern": "The dynamic here involves recurring themes that may be asking for your attention.",
        "challenge": "A common difficulty is not seeing the pattern clearly while you're inside of it.",
        "genius": "The gift embedded here may only become visible when you stop trying to fix it.",
        "experiments": [
            "Notice when this theme appears in your daily life",
            "Experiment with observing rather than solving",
            "Track what triggers this pattern to intensify"
        ]
    })


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
            session_id=f"pattern_interpretation_{domain_id}"
        )
        chat.with_model("openai", "gpt-4o-mini")
        
        response = await chat.send_message(
            UserMessage(text=f"{system_prompt}\n\n{user_prompt}")
        )
        
        response_text = response.strip() if isinstance(response, str) else str(response).strip()
        
        # Clean up response - remove markdown code blocks if present
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            # Remove first line (```json) and last line (```)
            lines = [l for l in lines if not l.startswith("```")]
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
