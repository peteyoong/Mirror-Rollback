"""Pattern Mirror Engine V1
=====================================

Generates a single, resonant pattern mirror based on user signals.

This is NOT a personality report. This is a REAL-TIME PATTERN MIRROR.

Structure:
- What you may be (current pattern)
- What's your challenge (shadow behaviors)
- What's your genius (expanded expression + optional archetype)
- Practical ways to think about it (micro shifts)

Language Rules:
- NO identity statements ("you are...")
- ALWAYS use "you may be..."
- NO spiritual jargon (energy, vibration, alignment)
- NO vague phrases ("something is shifting", "you are being called")
- Use real-life, grounded language
- Must pass "EO/YPO clarity test" → instantly understandable
"""

import os
import json
import logging
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ============================================================================
# PATTERN MIRROR OUTPUT CONTRACT
# ============================================================================

PATTERN_OUTPUT_SCHEMA = {
    "pattern": {
        "title": "string",
        "what_you_may_be": "string",
        "challenge": ["string", "string"],
        "genius": {
            "description": "string",
            "archetype": "string (optional)"
        },
        "micro_shifts": ["string", "string"]
    }
}

# ============================================================================
# ARCHETYPES (used only in genius section)
# ============================================================================

ARCHETYPES = {
    "phoenix": "The Phoenix — the ability to move through difficulty and rebuild with awareness and intention.",
    "witness": "The Witness — the capacity to observe without reacting, creating space for clarity.",
    "bridge": "The Bridge — the skill of connecting disconnected parts, within yourself or between others.",
    "anchor": "The Anchor — the ability to stay grounded when others lose their footing.",
    "catalyst": "The Catalyst — the natural ability to spark change in yourself and situations.",
    "gardener": "The Gardener — patience with slow growth and trust in unseen progress.",
    "truthsayer": "The Truthsayer — the courage to name what others avoid.",
    "navigator": "The Navigator — the ability to find direction when the path is unclear.",
}

# ============================================================================
# SIGNAL AGGREGATION
# ============================================================================

async def aggregate_user_signals(
    db: AsyncIOMotorDatabase,
    user_id: str,
    days: int = 7
) -> Dict[str, Any]:
    """Aggregate signals from journal, mirror chat, and lifeline."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    signals = {
        "journal_entries": [],
        "chat_messages": [],
        "lifeline_events": [],
        "emotional_tones": [],
        "signal_strength": "weak",
    }
    
    # 1. Fetch recent journal entries
    try:
        journal_cursor = db.journal.find({
            "user_id": user_id,
            "created_at": {"$gte": cutoff}
        }).sort("created_at", -1).limit(10)
        
        async for entry in journal_cursor:
            signals["journal_entries"].append({
                "content": entry.get("content", ""),
                "themes": entry.get("themes", []),
                "created_at": entry.get("created_at", datetime.now(timezone.utc)).isoformat()
            })
    except Exception as e:
        logger.warning(f"[PatternMirror] Failed to fetch journal: {e}")
    
    # 2. Fetch recent mirror chat messages (user messages only)
    try:
        chat_cursor = db.mirror_chat.find({
            "user_id": user_id,
            "role": "user",
            "timestamp": {"$gte": cutoff}
        }).sort("timestamp", -1).limit(20)
        
        async for msg in chat_cursor:
            signals["chat_messages"].append({
                "content": msg.get("content", ""),
                "timestamp": msg.get("timestamp", datetime.now(timezone.utc)).isoformat()
            })
    except Exception as e:
        logger.warning(f"[PatternMirror] Failed to fetch chat: {e}")
    
    # 3. Fetch recent lifeline events
    try:
        lifeline_cursor = db.lifeline_events.find({
            "user_id": user_id,
        }).sort("event_date", -1).limit(10)
        
        async for event in lifeline_cursor:
            signals["lifeline_events"].append({
                "title": event.get("title", ""),
                "description": event.get("description", ""),
                "emotional_tone": event.get("emotional_tone", "neutral"),
                "event_date": str(event.get("event_date", ""))
            })
    except Exception as e:
        logger.warning(f"[PatternMirror] Failed to fetch lifeline: {e}")
    
    # 4. Detect emotional tones from content
    all_content = " ".join([
        e["content"] for e in signals["journal_entries"]
    ] + [
        m["content"] for m in signals["chat_messages"]
    ])
    
    emotional_keywords = {
        "fear": ["afraid", "scared", "anxious", "worry", "nervous", "panic", "dread"],
        "shame": ["ashamed", "embarrassed", "guilty", "worthless", "inadequate", "failure"],
        "anger": ["angry", "frustrated", "resentful", "irritated", "annoyed", "furious"],
        "sadness": ["sad", "depressed", "lonely", "hopeless", "grief", "loss"],
        "joy": ["happy", "excited", "grateful", "content", "peaceful", "hopeful"],
        "confusion": ["confused", "lost", "uncertain", "stuck", "unclear", "indecisive"],
    }
    
    content_lower = all_content.lower()
    detected_tones = []
    for tone, keywords in emotional_keywords.items():
        if any(kw in content_lower for kw in keywords):
            detected_tones.append(tone)
    
    signals["emotional_tones"] = detected_tones
    
    # 5. Calculate signal strength
    total_signals = (
        len(signals["journal_entries"]) + 
        len(signals["chat_messages"]) + 
        len(signals["lifeline_events"])
    )
    
    if total_signals >= 10:
        signals["signal_strength"] = "strong"
    elif total_signals >= 3:
        signals["signal_strength"] = "moderate"
    else:
        signals["signal_strength"] = "weak"
    
    # 6. Generate human-readable signal explanations (max 5)
    signals["explainable_signals"] = generate_explainable_signals(signals)
    
    return signals


def generate_explainable_signals(signals: Dict[str, Any]) -> List[str]:
    """
    Generate human-readable signal explanations.
    
    Rules:
    - Max 3-5 signals
    - Summarized, human-readable
    - No raw logs, timestamps, or IDs
    - Use phrasing like "You described...", "You noted...", "Your recent entries suggest..."
    """
    explanations = []
    
    # From journal entries
    journal_entries = signals.get("journal_entries", [])
    if journal_entries:
        # Get themes from entries
        all_themes = []
        for entry in journal_entries[:3]:
            themes = entry.get("themes", [])
            all_themes.extend(themes)
        
        if all_themes:
            unique_themes = list(set(all_themes))[:3]
            if len(unique_themes) == 1:
                explanations.append(f"Your recent reflections touched on {unique_themes[0].lower()}")
            elif len(unique_themes) >= 2:
                explanations.append(f"Your journal entries explored themes of {', '.join(t.lower() for t in unique_themes[:2])}")
        
        # Content-based signal
        if len(journal_entries) >= 2:
            explanations.append(f"You've been writing consistently over the past few days")
        elif len(journal_entries) == 1:
            content_preview = journal_entries[0].get("content", "")[:50]
            if content_preview:
                explanations.append(f"You recently described what's been on your mind")
    
    # From chat messages
    chat_messages = signals.get("chat_messages", [])
    if chat_messages:
        if len(chat_messages) >= 5:
            explanations.append("You've been actively reflecting in conversations")
        elif len(chat_messages) >= 2:
            explanations.append("Your recent conversations revealed recurring themes")
        elif len(chat_messages) == 1:
            explanations.append("You shared something significant in a recent reflection")
    
    # From lifeline events
    lifeline_events = signals.get("lifeline_events", [])
    if lifeline_events:
        # Look for emotional tones in events
        emotional_events = [e for e in lifeline_events if e.get("emotional_tone") and e.get("emotional_tone") != "neutral"]
        
        if emotional_events:
            tones = list(set(e.get("emotional_tone", "") for e in emotional_events[:3]))
            if tones:
                explanations.append(f"Your life events carry emotional weight worth noticing")
        
        if len(lifeline_events) >= 3:
            explanations.append("Your lifeline shows patterns across multiple experiences")
    
    # From emotional tones detected
    emotional_tones = signals.get("emotional_tones", [])
    if emotional_tones:
        tone_map = {
            "fear": "a sense of anticipation or worry",
            "shame": "self-questioning moments",
            "anger": "moments of frustration",
            "sadness": "processing something difficult",
            "joy": "hopeful or grateful moments",
            "confusion": "uncertainty about direction",
        }
        
        for tone in emotional_tones[:2]:
            if tone in tone_map:
                explanations.append(f"Your words suggest {tone_map[tone]}")
                break
    
    # If no signals, provide a gentle fallback
    if not explanations:
        explanations.append("This pattern is based on general awareness prompts")
    
    # Limit to max 5, unique
    seen = set()
    unique_explanations = []
    for exp in explanations:
        if exp not in seen:
            seen.add(exp)
            unique_explanations.append(exp)
            if len(unique_explanations) >= 5:
                break
    
    return unique_explanations


# ============================================================================
# LLM PROMPT FOR PATTERN GENERATION
# ============================================================================

PATTERN_GENERATION_PROMPT = '''You are the Pattern Mirror engine inside Project Mirror.

Your task is to generate a SINGLE, RESONANT pattern based on the user's recent signals.

This is NOT a personality report.
This is a REAL-TIME PATTERN MIRROR.

=== LANGUAGE RULES (CRITICAL) ===

1. NO identity statements ("you are...", "you're someone who...")
2. ALWAYS use "You may be..." framing
3. NO spiritual jargon:
   - FORBIDDEN: energy, vibration, alignment, universe, manifest, divine, cosmic, ascension
4. NO vague phrases:
   - FORBIDDEN: "something is shifting", "you are being called", "trust the process"
5. Use REAL-LIFE, GROUNDED language
6. Must pass "EO/YPO clarity test" → an executive should understand it instantly

=== OUTPUT STRUCTURE ===

1. WHAT YOU MAY BE (Current Pattern)
   - 1-2 sentences max
   - Present tense
   - Situational (NOT identity)
   - Start with "You may be..."
   - Must feel immediately recognizable

2. WHAT'S YOUR CHALLENGE (Shadow Expression)
   - 2-4 bullet points
   - Concrete behaviors
   - Observable reactions
   - No abstraction

3. WHAT'S YOUR GENIUS (Expanded Expression)
   - First line: expanded potential (same pattern, higher expression)
   - Optional: include archetype name
   - No hype language
   - Grounded and believable

4. PRACTICAL WAYS TO THINK ABOUT IT (Micro Shifts)
   - 1-2 short prompts max
   - NOT advice
   - NOT coaching
   - Just awareness triggers

=== USER SIGNALS ===

{user_signals}

=== EMOTIONAL TONES DETECTED ===
{emotional_tones}

=== SIGNAL STRENGTH: {signal_strength} ===

If signal strength is weak, generate a safe but still relatable pattern.
Do NOT overfit to limited data.

=== OUTPUT FORMAT (JSON) ===

Return ONLY valid JSON matching this exact structure:

{{
  "pattern": {{
    "title": "Brief 2-4 word title",
    "what_you_may_be": "You may be [present tense situation/behavior]...",
    "challenge": [
      "concrete behavior 1",
      "concrete behavior 2"
    ],
    "genius": {{
      "description": "At its best, this same pattern becomes: [expanded expression]",
      "archetype": "The [Name] (optional, can be null)"
    }},
    "micro_shifts": [
      "Try noticing [specific awareness trigger]",
      "Ask: [one clear question]"
    ]
  }}
}}

=== SUCCESS CRITERIA ===

User reaction should be:
1. "That's exactly what I do"
2. "I didn't realize that"
3. "I can see another way"

If it feels generic → FAIL
If it feels like a personality report → FAIL
If it hits emotionally → PASS
'''


# ============================================================================
# PATTERN GENERATION
# ============================================================================

async def generate_pattern_mirror(
    db: AsyncIOMotorDatabase,
    user_id: str,
    force_refresh: bool = False
) -> Dict[str, Any]:
    """Generate a pattern mirror for the user."""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')
    
    # Check cache first (unless force refresh)
    if not force_refresh:
        try:
            cached = await db.pattern_mirror_cache.find_one({
                "user_id": user_id,
                "date": datetime.now(timezone.utc).strftime('%Y-%m-%d')
            })
            if cached:
                logger.info(f"[PatternMirror] Cache hit for user {user_id}")
                # Regenerate signals for cached response (signals are dynamic)
                signals = await aggregate_user_signals(db, user_id)
                return {
                    "pattern": cached["pattern"],
                    "cached": True,
                    "generated_at": cached["generated_at"],
                    "signal_strength": cached.get("signal_strength", "weak"),
                    "signals": signals.get("explainable_signals", [])
                }
        except Exception as e:
            logger.warning(f"[PatternMirror] Cache check failed: {e}")
    
    # Aggregate signals
    signals = await aggregate_user_signals(db, user_id)
    
    # Format signals for prompt
    signal_text = ""
    
    if signals["journal_entries"]:
        signal_text += "\n\nRECENT JOURNAL ENTRIES:\n"
        for i, entry in enumerate(signals["journal_entries"][:5], 1):
            signal_text += f"{i}. \"{entry['content'][:200]}...\" ({entry['created_at'][:10]})\n"
    
    if signals["chat_messages"]:
        signal_text += "\n\nRECENT CHAT MESSAGES:\n"
        for i, msg in enumerate(signals["chat_messages"][:5], 1):
            signal_text += f"{i}. \"{msg['content'][:150]}...\"\n"
    
    if signals["lifeline_events"]:
        signal_text += "\n\nLIFELINE EVENTS:\n"
        for i, event in enumerate(signals["lifeline_events"][:3], 1):
            signal_text += f"{i}. {event['title']} - {event.get('description', '')[:100]}\n"
    
    if not signal_text:
        signal_text = "No recent signals available. Generate a relatable general pattern."
    
    emotional_tones = ", ".join(signals["emotional_tones"]) if signals["emotional_tones"] else "None clearly detected"
    
    # Build prompt
    prompt = PATTERN_GENERATION_PROMPT.format(
        user_signals=signal_text,
        emotional_tones=emotional_tones,
        signal_strength=signals["signal_strength"]
    )
    
    # Generate with LLM
    try:
        if not EMERGENT_LLM_KEY:
            logger.warning("[PatternMirror] No LLM key, using fallback")
            return get_fallback_pattern(signals)
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"pattern_mirror_{user_id}_{datetime.now().timestamp()}",
            system_message="You are the Pattern Mirror engine. Return ONLY valid JSON."
        )
        chat.with_model("openai", "gpt-5.2")
        
        response = await chat.send_message(UserMessage(text=prompt))
        
        # Parse response
        response_text = response.strip()
        
        # Try to extract JSON from response
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        try:
            pattern_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"[PatternMirror] JSON parse error: {e}")
            logger.error(f"[PatternMirror] Raw response: {response_text[:500]}")
            return get_fallback_pattern(signals)
        
        # Validate structure
        if "pattern" not in pattern_data:
            logger.error("[PatternMirror] Missing 'pattern' key")
            return get_fallback_pattern(signals)
        
        pattern = pattern_data["pattern"]
        
        # Ensure required fields
        required_fields = ["title", "what_you_may_be", "challenge", "genius", "micro_shifts"]
        for field in required_fields:
            if field not in pattern:
                logger.error(f"[PatternMirror] Missing field: {field}")
                return get_fallback_pattern(signals)
        
        # Cache the result
        try:
            await db.pattern_mirror_cache.update_one(
                {"user_id": user_id, "date": datetime.now(timezone.utc).strftime('%Y-%m-%d')},
                {
                    "$set": {
                        "pattern": pattern,
                        "signal_strength": signals["signal_strength"],
                        "generated_at": datetime.now(timezone.utc).isoformat()
                    }
                },
                upsert=True
            )
        except Exception as e:
            logger.warning(f"[PatternMirror] Cache write failed: {e}")
        
        return {
            "pattern": pattern,
            "cached": False,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "signal_strength": signals["signal_strength"],
            "signals": signals.get("explainable_signals", [])
        }
        
    except Exception as e:
        logger.error(f"[PatternMirror] LLM error: {e}")
        return get_fallback_pattern(signals)


def get_fallback_pattern(signals: Dict[str, Any]) -> Dict[str, Any]:
    """Return a safe fallback pattern when LLM fails or data is weak."""
    
    # Get explainable signals
    explainable = signals.get("explainable_signals", ["This pattern is based on general awareness prompts"])
    
    # Select fallback based on detected emotional tones
    tones = signals.get("emotional_tones", [])
    
    if "fear" in tones or "anxiety" in tones:
        return {
            "pattern": {
                "title": "Anticipating Impact",
                "what_you_may_be": "You may be anticipating discomfort before it's present, preparing yourself for impact instead of staying with what's real.",
                "challenge": [
                    "assuming the worst quickly",
                    "bracing for reactions that haven't happened",
                    "running scenarios instead of staying present"
                ],
                "genius": {
                    "description": "At its best, this same pattern becomes the ability to prepare thoughtfully without being consumed by what-ifs.",
                    "archetype": "The Navigator"
                },
                "micro_shifts": [
                    "Try noticing the moment before you brace.",
                    "Ask: What is actually happening vs what I'm imagining?"
                ]
            },
            "cached": False,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "signal_strength": signals.get("signal_strength", "weak"),
            "signals": explainable,
            "fallback": True
        }
    
    elif "anger" in tones or "frustration" in tones:
        return {
            "pattern": {
                "title": "Holding the Line",
                "what_you_may_be": "You may be holding firm on something that matters to you, but the effort of holding is starting to wear.",
                "challenge": [
                    "repeating points that aren't landing",
                    "feeling unheard or dismissed",
                    "carrying tension in the body"
                ],
                "genius": {
                    "description": "At its best, this same pattern becomes the courage to name what needs naming without attachment to being received.",
                    "archetype": "The Truthsayer"
                },
                "micro_shifts": [
                    "Try noticing where the tension lives in your body.",
                    "Ask: What would it mean to let this go?"
                ]
            },
            "cached": False,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "signal_strength": signals.get("signal_strength", "weak"),
            "signals": explainable,
            "fallback": True
        }
    
    elif "sadness" in tones or "grief" in tones:
        return {
            "pattern": {
                "title": "Moving Through",
                "what_you_may_be": "You may be processing something that needed to end, even if you didn't choose the ending.",
                "challenge": [
                    "replaying what could have been different",
                    "withdrawing when connection might help",
                    "minimizing what you're actually feeling"
                ],
                "genius": {
                    "description": "At its best, this same pattern becomes the ability to honor what was while making space for what's next.",
                    "archetype": "The Phoenix"
                },
                "micro_shifts": [
                    "Try naming what you're actually grieving.",
                    "Ask: What part of this am I ready to set down?"
                ]
            },
            "cached": False,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "signal_strength": signals.get("signal_strength", "weak"),
            "signals": explainable,
            "fallback": True
        }
    
    # Default fallback for weak/no signals
    return {
        "pattern": {
            "title": "Something's Here",
            "what_you_may_be": "You may be noticing something you can't quite name yet—a pull, a tension, or a question that keeps returning.",
            "challenge": [
                "dismissing subtle signals",
                "waiting for clarity before acting",
                "outsourcing your knowing to others"
            ],
            "genius": {
                "description": "At its best, this same pattern becomes the ability to trust incomplete information and move with it.",
                "archetype": "The Witness"
            },
            "micro_shifts": [
                "Try noticing what keeps coming back to mind.",
                "Ask: What would I do if I trusted what I already know?"
            ]
        },
        "cached": False,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "signal_strength": signals.get("signal_strength", "weak"),
        "signals": explainable,
        "fallback": True
    }
