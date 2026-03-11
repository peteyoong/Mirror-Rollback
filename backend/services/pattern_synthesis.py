"""Pattern Synthesis Service

Generates reflective synthesis paragraphs for recurring pattern categories.
Uses LLM with strict tone guidelines - reflective, never deterministic.

Philosophy:
- "Mirror not guru" - suggest, don't prescribe
- Tentative phrasing: "may be", "might", "could"
- Never predictive or deterministic
- Maximum 2 sentences
"""

import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Template fallbacks when LLM fails
FALLBACK_TEMPLATES = {
    "energy_vitality": "A theme around energy and vitality may be appearing again. You might notice when your energy feels alive versus when it feels depleted.",
    "emotional_landscape": "Something around your emotional experience could be surfacing. You might experiment with noticing how your inner weather shifts.",
    "identity_direction": "A question about identity or direction may be emerging. You might observe what feels true about yourself in this moment.",
    "mind_meaning": "A pattern around thinking and meaning may be present. You might notice what questions keep returning.",
    "expression_action": "A theme around expression or action could be appearing. You might experiment with noticing when words or actions want to move through you.",
    "relationships_boundaries": "Something around connection or boundaries may be surfacing. You might observe where you feel drawn closer or need more space.",
    "growth_transformation": "A pattern around change or growth may be present. You might notice what feels ready to shift."
}


def get_fallback_synthesis(category_id: str) -> str:
    """Get deterministic fallback synthesis for a category."""
    return FALLBACK_TEMPLATES.get(
        category_id,
        "A recurring pattern may be emerging. You might experiment with noticing how this theme shows up."
    )


async def generate_pattern_synthesis(
    category_id: str,
    category_name: str,
    matched_signals: List[Dict[str, Any]],
    matched_sources: List[str]
) -> str:
    """Generate a reflective synthesis paragraph for a recurring pattern.
    
    Uses LLM to create a short, reflective synthesis that helps users
    see their pattern more clearly without being prescriptive.
    
    Args:
        category_id: Internal category identifier
        category_name: Human-readable category name
        matched_signals: List of matched signal objects
        matched_sources: List of source names (e.g., "gene_keys", "human_design")
    
    Returns:
        1-2 sentence reflective synthesis paragraph
    """
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')
        if not EMERGENT_LLM_KEY:
            logger.warning("[PatternSynthesis] No LLM key, using fallback")
            return get_fallback_synthesis(category_id)
        
        # Build context from signals
        signal_labels = [s.get("label", "") for s in matched_signals[:5]]
        sources_str = ", ".join(matched_sources)
        signals_str = "; ".join(signal_labels)
        
        # Build prompt
        system_prompt = """You are a reflective assistant that helps users notice patterns in their inner life.

CRITICAL TONE RULES:
- Be reflective, never deterministic
- Never be predictive or certain
- Avoid "you are" language
- Use tentative phrasing: "may be noticing", "could be surfacing", "might experiment with"
- Never sound like a guru or authority
- Keep it warm but not sentimental
- Maximum 2 sentences
- No emojis or formatting

Example good outputs:
- "A theme around energy and commitments may be appearing again. You might experiment with noticing when your energy feels most alive versus when it feels depleted."
- "Something around how you express yourself could be surfacing. You might observe when words want to come through and when silence feels right."
- "A pattern around boundaries and connection may be present. You might notice where you feel drawn closer versus where you need space."

Example bad outputs (DO NOT):
- "Your energy is depleted because you're not honoring your needs."
- "This pattern shows you need to work on your boundaries."
- "The universe is telling you to rest."
"""

        user_prompt = f"""Generate a reflective synthesis for a user whose "{category_name}" pattern is recurring.

Signals detected: {signals_str}
Sources: {sources_str}

Write 1-2 sentences that help them notice this pattern without being prescriptive.
Do not explain what the signals mean.
Just reflect the theme back gently and suggest an experiment."""

        # Call LLM
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            model="gpt-4o-mini"
        )
        
        response = await chat.send_async([
            UserMessage(content=f"{system_prompt}\n\n{user_prompt}")
        ])
        
        synthesis = response.content.strip() if hasattr(response, 'content') else str(response).strip()
        
        # Validate response
        if len(synthesis) < 20 or len(synthesis) > 500:
            logger.warning(f"[PatternSynthesis] Invalid response length: {len(synthesis)}")
            return get_fallback_synthesis(category_id)
        
        # Check for forbidden patterns
        forbidden = ["you are", "you need to", "you must", "the universe", "your destiny"]
        for phrase in forbidden:
            if phrase.lower() in synthesis.lower():
                logger.warning(f"[PatternSynthesis] Forbidden phrase detected: {phrase}")
                return get_fallback_synthesis(category_id)
        
        logger.info(f"[PatternSynthesis] Generated synthesis for {category_name}")
        return synthesis
        
    except Exception as e:
        logger.error(f"[PatternSynthesis] LLM error: {e}")
        return get_fallback_synthesis(category_id)


def generate_pattern_synthesis_sync(
    category_id: str,
    category_name: str,
    matched_signals: List[Dict[str, Any]],
    matched_sources: List[str]
) -> str:
    """Synchronous wrapper for pattern synthesis generation.
    
    Falls back to template if async isn't available.
    """
    import asyncio
    
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Can't run async in existing loop, use fallback
            return get_fallback_synthesis(category_id)
        return loop.run_until_complete(
            generate_pattern_synthesis(
                category_id, category_name, matched_signals, matched_sources
            )
        )
    except Exception as e:
        logger.error(f"[PatternSynthesis] Sync wrapper error: {e}")
        return get_fallback_synthesis(category_id)
