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
    
    # 6. Store raw signals for pattern-specific explanation generation
    # (explainable signals will be generated AFTER pattern is known)
    
    return signals


def generate_signals_by_source(
    signals: Dict[str, Any], 
    pattern: Dict[str, Any]
) -> Dict[str, List[str]]:
    """
    Generate specific, pattern-tied signal explanations grouped by source.
    
    Rules:
    - Signals must explain WHY this specific pattern was selected
    - Specific, human-readable, grounded, observational
    - NOT generic, NOT surveillance-like
    - Group by source: journal, mirror_chat, lifeline, timing
    - Omit sources with no meaningful signals
    """
    signals_by_source = {}
    
    pattern_title = pattern.get("title", "")
    what_you_may_be = pattern.get("what_you_may_be", "")
    challenges = pattern.get("challenge", [])
    
    # Extract key behavioral indicators from the pattern
    pattern_keywords = extract_pattern_keywords(what_you_may_be, challenges)
    
    # =========================================================================
    # JOURNAL SIGNALS
    # =========================================================================
    journal_entries = signals.get("journal_entries", [])
    journal_signals = []
    
    if journal_entries:
        # Analyze journal content for pattern-specific signals
        for entry in journal_entries[:5]:
            content = entry.get("content", "").lower()
            themes = entry.get("themes", [])
            
            # Check for emotional decision-making patterns
            if any(kw in content for kw in ["decide", "decision", "choice", "choosing", "should i"]):
                if any(kw in content for kw in ["feel", "feeling", "emotion", "mood"]):
                    journal_signals.append(
                        "You described trying to make important decisions while your emotional state was shifting"
                    )
                    break
            
            # Check for self-doubt / second-guessing
            if any(kw in content for kw in ["doubt", "second-guess", "unsure", "wonder if", "maybe i shouldn't"]):
                journal_signals.append(
                    "Your recent reflections show a pattern of second-guessing after emotional intensity"
                )
                break
            
            # Check for control patterns
            if any(kw in content for kw in ["control", "handle", "manage", "keep it together", "stay strong"]):
                journal_signals.append(
                    "You described staying functional by focusing on what needs to be handled"
                )
                break
            
            # Check for avoidance patterns
            if any(kw in content for kw in ["avoid", "ignore", "push down", "not think about", "later"]):
                journal_signals.append(
                    "Your writing suggests setting aside certain feelings to focus on action"
                )
                break
        
        # Theme-based signals
        all_themes = []
        for entry in journal_entries[:3]:
            all_themes.extend(entry.get("themes", []))
        
        if all_themes:
            unique_themes = list(set(all_themes))[:3]
            theme_str = ", ".join(t.lower() for t in unique_themes[:2])
            
            # Make theme signal pattern-specific
            if any(t.lower() in ["fear", "anxiety", "worry"] for t in unique_themes):
                journal_signals.append(
                    f"Your entries touched on {theme_str}, which may be feeding this anticipatory pattern"
                )
            elif any(t.lower() in ["anger", "frustration", "resentment"] for t in unique_themes):
                journal_signals.append(
                    f"Your reflections on {theme_str} suggest energy being held rather than expressed"
                )
            elif any(t.lower() in ["sadness", "grief", "loss"] for t in unique_themes):
                journal_signals.append(
                    f"Your writing about {theme_str} indicates something being processed beneath the surface"
                )
            elif len(unique_themes) >= 2:
                journal_signals.append(
                    f"Your journal explored {theme_str}, themes that connect to this pattern"
                )
        
        # Recency and intensity signals
        if len(journal_entries) >= 3:
            journal_signals.append(
                "The frequency of your recent entries suggests this is actively on your mind"
            )
    
    if journal_signals:
        signals_by_source["journal"] = journal_signals[:2]  # Max 2 per source
    
    # =========================================================================
    # MIRROR CHAT SIGNALS
    # =========================================================================
    chat_messages = signals.get("chat_messages", [])
    chat_signals = []
    
    if chat_messages:
        all_chat_content = " ".join([m.get("content", "") for m in chat_messages[:10]]).lower()
        
        # Check for urgency vs self-monitoring
        has_urgency = any(kw in all_chat_content for kw in ["need to", "have to", "must", "quickly", "now"])
        has_monitoring = any(kw in all_chat_content for kw in ["i notice", "i think", "maybe", "i wonder", "probably"])
        
        if has_urgency and has_monitoring:
            chat_signals.append(
                "In your reflections, you moved between urgency and self-monitoring, suggesting difficulty trusting your inner timing"
            )
        elif has_urgency:
            chat_signals.append(
                "Your conversations carried a sense of needing to resolve or act, even when sitting with it might help"
            )
        elif has_monitoring:
            chat_signals.append(
                "You showed a pattern of observing yourself carefully, which can be strength or self-doubt depending on context"
            )
        
        # Check for relational patterns
        if any(kw in all_chat_content for kw in ["they", "them", "other people", "everyone", "nobody"]):
            if any(kw in all_chat_content for kw in ["understand", "see", "notice", "realize"]):
                chat_signals.append(
                    "You reflected on how others perceive or respond to you, suggesting relational weight in this pattern"
                )
        
        # Check for repeated themes across messages
        if len(chat_messages) >= 3:
            # Simple theme recurrence check
            first_half = " ".join([m.get("content", "") for m in chat_messages[:len(chat_messages)//2]]).lower()
            second_half = " ".join([m.get("content", "") for m in chat_messages[len(chat_messages)//2:]]).lower()
            
            recurring_words = ["work", "relationship", "family", "money", "health", "future", "past"]
            for word in recurring_words:
                if word in first_half and word in second_half:
                    chat_signals.append(
                        f"You returned to {word} multiple times, suggesting it's central to what's unfolding"
                    )
                    break
    
    if chat_signals:
        signals_by_source["mirror_chat"] = chat_signals[:2]
    
    # =========================================================================
    # LIFELINE SIGNALS
    # =========================================================================
    lifeline_events = signals.get("lifeline_events", [])
    lifeline_signals = []
    
    if lifeline_events:
        # Check for recurring emotional patterns
        emotional_tones = [e.get("emotional_tone", "") for e in lifeline_events if e.get("emotional_tone")]
        
        if len(emotional_tones) >= 2:
            # Count tone occurrences
            tone_counts = {}
            for tone in emotional_tones:
                tone_counts[tone] = tone_counts.get(tone, 0) + 1
            
            most_common_tone = max(tone_counts, key=tone_counts.get) if tone_counts else None
            
            if most_common_tone and tone_counts[most_common_tone] >= 2:
                lifeline_signals.append(
                    f"Your lifeline shows this is not a one-off reaction—{most_common_tone} appears across multiple life events"
                )
        
        # Check for pattern of events
        if len(lifeline_events) >= 3:
            lifeline_signals.append(
                "The shape of your lifeline suggests this pattern has roots in how you've navigated pressure before"
            )
        
        # Check for recent significant events
        recent_events = [e for e in lifeline_events[:3] if e.get("title")]
        if recent_events:
            event_titles = [e.get("title", "") for e in recent_events[:2]]
            if event_titles:
                lifeline_signals.append(
                    "Recent life events may be reactivating a familiar response pattern"
                )
    
    if lifeline_signals:
        signals_by_source["lifeline"] = lifeline_signals[:2]
    
    # =========================================================================
    # TIMING SIGNALS (if available)
    # =========================================================================
    timing_signals = []
    emotional_tones = signals.get("emotional_tones", [])
    
    # Generate timing-based signals based on detected emotional state
    if emotional_tones:
        if "fear" in emotional_tones or "confusion" in emotional_tones:
            timing_signals.append(
                "Current signals suggest a period of heightened sensitivity, which may be amplifying this pattern"
            )
        elif "sadness" in emotional_tones:
            timing_signals.append(
                "This may be a period where loss or transition is asking for attention rather than resolution"
            )
        elif "anger" in emotional_tones:
            timing_signals.append(
                "Current energy suggests something pressing for expression or boundary-setting"
            )
    
    # Add general timing context if signals are weak but pattern is present
    if not timing_signals and signals.get("signal_strength") == "weak":
        timing_signals.append(
            "Even without strong recent signals, this pattern may be quietly active beneath the surface"
        )
    
    if timing_signals:
        signals_by_source["timing"] = timing_signals[:1]  # Max 1 timing signal
    
    return signals_by_source


def extract_pattern_keywords(what_you_may_be: str, challenges: List[str]) -> List[str]:
    """Extract key behavioral keywords from pattern description."""
    keywords = []
    
    text = (what_you_may_be + " " + " ".join(challenges)).lower()
    
    # Behavioral patterns to detect
    behavioral_patterns = [
        "anticipat", "prepar", "brace", "expect",  # Anticipation
        "control", "manage", "handle", "function",  # Control
        "avoid", "withdraw", "shut down", "pull away",  # Avoidance
        "repeat", "again", "pattern", "same",  # Recurrence
        "other", "they", "people", "relationship",  # Relational
        "decide", "choice", "option", "direction",  # Decision
        "feel", "emotion", "mood", "react",  # Emotional
    ]
    
    for pattern in behavioral_patterns:
        if pattern in text:
            keywords.append(pattern)
    
    return keywords


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
                # Generate pattern-specific signals by source
                signals_by_source = generate_signals_by_source(signals, cached["pattern"])
                return {
                    "pattern": cached["pattern"],
                    "cached": True,
                    "generated_at": cached["generated_at"],
                    "signal_strength": cached.get("signal_strength", "weak"),
                    "signals_by_source": signals_by_source
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
        
        # Generate pattern-specific signals by source
        signals_by_source = generate_signals_by_source(signals, pattern)
        
        return {
            "pattern": pattern,
            "cached": False,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "signal_strength": signals["signal_strength"],
            "signals_by_source": signals_by_source
        }
        
    except Exception as e:
        logger.error(f"[PatternMirror] LLM error: {e}")
        return get_fallback_pattern(signals)


def get_fallback_pattern(signals: Dict[str, Any]) -> Dict[str, Any]:
    """Return a safe fallback pattern when LLM fails or data is weak."""
    
    # Select fallback based on detected emotional tones
    tones = signals.get("emotional_tones", [])
    
    # Define fallback patterns
    if "fear" in tones or "anxiety" in tones:
        pattern = {
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
        }
    elif "anger" in tones or "frustration" in tones:
        pattern = {
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
        }
    elif "sadness" in tones or "grief" in tones:
        pattern = {
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
        }
    else:
        # Default fallback for weak/no signals
        pattern = {
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
        }
    
    # Generate pattern-specific signals by source
    signals_by_source = generate_signals_by_source(signals, pattern)
    
    return {
        "pattern": pattern,
        "cached": False,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "signal_strength": signals.get("signal_strength", "weak"),
        "signals_by_source": signals_by_source,
        "fallback": True
    }
