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
# TRANSIT-COMPATIBLE PATTERN TEMPLATES
# ============================================================================

PATTERN_TEMPLATES = {
    "emotional_wave_riding": {
        "title": "Emotional Wave Riding",
        "timing_compatibility": ["emotional_sensitivity", "clarity_vs_confusion", "transition_threshold"],
        "signal_keywords": ["feel", "emotion", "mood", "overwhelm", "intense", "react"],
        "what_you_may_be": "You may be experiencing emotions that arrive in waves—intense one moment, settled the next—making it hard to trust what you're actually feeling.",
        "challenge": [
            "questioning your reactions after the fact",
            "waiting for stability before trusting yourself",
            "second-guessing decisions made during emotional peaks"
        ],
        "genius": {
            "description": "At its best, this same pattern becomes the ability to ride emotional waves without being capsized by them.",
            "archetype": "The Navigator"
        },
        "micro_shifts": [
            "Try noticing the wave without needing to name it immediately.",
            "Ask: Can I trust this feeling even if it changes tomorrow?"
        ]
    },
    "anticipating_impact": {
        "title": "Anticipating Impact",
        "timing_compatibility": ["pressure", "urgency", "emotional_sensitivity"],
        "signal_keywords": ["worry", "anxious", "afraid", "brace", "prepare", "expect"],
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
    "duty_over_self": {
        "title": "Duty Over Self",
        "timing_compatibility": ["pressure", "contraction", "relational_sensitivity"],
        "signal_keywords": ["handle", "manage", "control", "responsible", "keep it together", "strong"],
        "what_you_may_be": "You may be staying highly functional through major life changes by focusing on what needs to be handled next—work, logistics, and being reliable for others—while keeping your own reactions tightly contained.",
        "challenge": [
            "postponing your own processing indefinitely",
            "interpreting your needs as inconveniences",
            "measuring self-worth by how much you absorb without complaint"
        ],
        "genius": {
            "description": "At its best, this same pattern becomes the capacity to remain steady under pressure while staying connected to what you actually need.",
            "archetype": "The Anchor"
        },
        "micro_shifts": [
            "Try noticing when you move into 'handle it' mode before you're asked.",
            "Ask: What am I trying to keep from becoming inconvenient—and for whom?"
        ]
    },
    "threshold_standing": {
        "title": "Standing at Threshold",
        "timing_compatibility": ["transition_threshold", "identity_shift", "reset_cycle"],
        "signal_keywords": ["decide", "choice", "direction", "change", "crossroads", "stuck"],
        "what_you_may_be": "You may be standing at a decision point that feels larger than the specific choice—as if what you decide will set a direction you can't easily undo.",
        "challenge": [
            "waiting for certainty before moving",
            "analyzing options instead of sensing what's right",
            "looking for permission from outside sources"
        ],
        "genius": {
            "description": "At its best, this same pattern becomes the ability to step through thresholds without needing to see the entire path first.",
            "archetype": "The Navigator"
        },
        "micro_shifts": [
            "Try noticing which direction your body leans when you stop thinking.",
            "Ask: What do I already know that I'm pretending not to?"
        ]
    },
    "holding_the_line": {
        "title": "Holding the Line",
        "timing_compatibility": ["pressure", "urgency", "relational_sensitivity"],
        "signal_keywords": ["angry", "frustrated", "resentful", "unfair", "boundaries", "enough"],
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
    "moving_through": {
        "title": "Moving Through",
        "timing_compatibility": ["reset_cycle", "emotional_sensitivity", "contraction"],
        "signal_keywords": ["sad", "loss", "grief", "ending", "goodbye", "letting go"],
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
    "expansion_resistance": {
        "title": "Expansion Resistance",
        "timing_compatibility": ["expansion", "identity_shift", "transition_threshold"],
        "signal_keywords": ["opportunity", "growth", "fear", "ready", "big", "next level"],
        "what_you_may_be": "You may be standing at the edge of something bigger than you've allowed yourself before—and noticing the part of you that wants to pull back.",
        "challenge": [
            "finding reasons why now isn't the right time",
            "focusing on what could go wrong",
            "self-editing before you've even started"
        ],
        "genius": {
            "description": "At its best, this same pattern becomes the wisdom to discern true readiness from premature expansion.",
            "archetype": "The Gardener"
        },
        "micro_shifts": [
            "Try noticing what your resistance is protecting.",
            "Ask: What would I do if I trusted I could handle what comes next?"
        ]
    },
    "somethings_here": {
        "title": "Something's Here",
        "timing_compatibility": ["clarity_vs_confusion", "emotional_sensitivity", "transition_threshold"],
        "signal_keywords": ["sense", "feeling", "notice", "something", "can't explain", "intuition"],
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
    "relational_weight": {
        "title": "Relational Weight",
        "timing_compatibility": ["relational_sensitivity", "emotional_sensitivity", "pressure"],
        "signal_keywords": ["relationship", "they", "them", "others", "connection", "distance"],
        "pattern_type": "challenge",
        "what_you_may_be": "You may be carrying the weight of a relationship dynamic that feels unresolved—something unspoken, misaligned, or in need of attention.",
        "challenge": [
            "over-functioning to keep peace",
            "interpreting silence as rejection",
            "avoiding direct conversation to prevent conflict"
        ],
        "genius": {
            "description": "At its best, this same pattern becomes the capacity to hold relational complexity without needing immediate resolution.",
            "archetype": "The Bridge"
        },
        "micro_shifts": [
            "Try noticing what you're hoping they'll say first.",
            "Ask: What would I want them to know if I weren't afraid of the response?"
        ]
    },
    
    # =========================================================================
    # POSITIVE / OPENING PATTERNS (NEW)
    # =========================================================================
    
    "relational_reopening": {
        "title": "Relational Reopening",
        "timing_compatibility": ["relational_harmony", "reconnection_window", "emotional_openness", "softening_phase"],
        "signal_keywords": ["close", "connect", "open", "together", "warmth", "love", "trust", "repair", "reconnect"],
        "pattern_type": "opening",
        "what_you_may_be": "You may be allowing warmth back in where there was distance—reconnecting with someone, or with a part of yourself that was guarded.",
        "challenge": [
            "doubting if openness will last",
            "holding back fully in case it doesn't",
            "overanalyzing a good moment"
        ],
        "genius": {
            "description": "At its best, this same pattern becomes the ability to receive connection without needing to control it.",
            "archetype": "The Bridge"
        },
        "micro_shifts": [
            "Try letting this moment be enough without needing more proof.",
            "Ask: What if I trusted this opening?"
        ]
    },
    "heart_thaw": {
        "title": "Heart Thaw",
        "timing_compatibility": ["emotional_openness", "softening_phase", "receptivity", "relational_harmony"],
        "signal_keywords": ["soft", "vulnerable", "open", "feel", "heart", "tender", "safe", "receive"],
        "pattern_type": "opening",
        "what_you_may_be": "You may be softening in places that were guarded—allowing yourself to feel more fully, or to be seen more honestly.",
        "challenge": [
            "bracing for the vulnerability to backfire",
            "questioning if it's safe to stay open",
            "retreating at the first hint of discomfort"
        ],
        "genius": {
            "description": "At its best, this same pattern becomes the capacity to stay open even when it feels unfamiliar.",
            "archetype": "The Witness"
        },
        "micro_shifts": [
            "Try staying with the softness a little longer before protecting.",
            "Ask: What becomes possible if I let myself be seen here?"
        ]
    },
    "safe_intimacy_returning": {
        "title": "Safe Intimacy Returning",
        "timing_compatibility": ["relational_harmony", "receptivity", "softening_phase", "reconnection_window"],
        "signal_keywords": ["intimate", "close", "safe", "trust", "connection", "together", "partner", "loved"],
        "pattern_type": "opening",
        "what_you_may_be": "You may be experiencing a return of safety in closeness—a sense that it's okay to let someone in, or to be truly present with another.",
        "challenge": [
            "waiting for something to go wrong",
            "testing the connection instead of receiving it",
            "numbing the good to protect from future loss"
        ],
        "genius": {
            "description": "At its best, this same pattern becomes the ability to be fully present in intimacy without needing guarantees.",
            "archetype": "The Anchor"
        },
        "micro_shifts": [
            "Try noticing where your body feels the safety.",
            "Ask: What if this is exactly what it seems?"
        ]
    },
    "reconnection_window": {
        "title": "Reconnection Window",
        "timing_compatibility": ["reconnection_window", "relational_harmony", "renewal_cycle", "softening_phase"],
        "signal_keywords": ["reconnect", "repair", "bridge", "heal", "return", "restore", "mend", "again"],
        "pattern_type": "opening",
        "what_you_may_be": "You may be sensing an opening—a window where repair, reconnection, or reconciliation feels more possible than before.",
        "challenge": [
            "overthinking the right way to approach",
            "waiting for the other person to move first",
            "dismissing the opening as unlikely to work"
        ],
        "genius": {
            "description": "At its best, this same pattern becomes the courage to reach out when the moment is present.",
            "archetype": "The Bridge"
        },
        "micro_shifts": [
            "Try noticing what small step feels available.",
            "Ask: What do I have to lose by trying?"
        ]
    },
    "renewal_after_distance": {
        "title": "Renewal After Distance",
        "timing_compatibility": ["renewal_cycle", "reconnection_window", "expansion", "relational_harmony"],
        "signal_keywords": ["new", "fresh", "start", "again", "return", "begin", "renewed", "different"],
        "pattern_type": "opening",
        "what_you_may_be": "You may be entering a new phase in something that felt stuck or distant—a relationship, a project, or a part of yourself that's waking up again.",
        "challenge": [
            "doubting if the change is real",
            "bringing old expectations into the new phase",
            "rushing past the renewal instead of inhabiting it"
        ],
        "genius": {
            "description": "At its best, this same pattern becomes the ability to begin again with fresh eyes.",
            "archetype": "The Phoenix"
        },
        "micro_shifts": [
            "Try meeting this moment as if you don't already know how it ends.",
            "Ask: What wants to be different this time?"
        ]
    },
    "grounded_presence": {
        "title": "Grounded Presence",
        "timing_compatibility": ["grounded_stability", "integration_phase", "receptivity", "emotional_openness"],
        "signal_keywords": ["grounded", "present", "calm", "stable", "centered", "clear", "settled", "peace"],
        "pattern_type": "opening",
        "what_you_may_be": "You may be experiencing a sense of stability—a groundedness that doesn't require fixing, only inhabiting.",
        "challenge": [
            "distrusting calm as the quiet before a storm",
            "filling silence with activity",
            "looking for what's wrong instead of resting in what's right"
        ],
        "genius": {
            "description": "At its best, this same pattern becomes the capacity to rest in presence without needing to do.",
            "archetype": "The Anchor"
        },
        "micro_shifts": [
            "Try letting this steadiness be true.",
            "Ask: What if there's nothing to fix right now?"
        ]
    },
    "emotional_integration": {
        "title": "Emotional Integration",
        "timing_compatibility": ["integration_phase", "emotional_openness", "renewal_cycle", "grounded_stability"],
        "signal_keywords": ["whole", "together", "integrate", "make sense", "coming together", "clarity", "understand"],
        "pattern_type": "opening",
        "what_you_may_be": "You may be experiencing something clicking into place—pieces that were scattered beginning to make sense, emotions that were confusing starting to integrate.",
        "challenge": [
            "rushing to name it before it fully forms",
            "doubting the integration will hold",
            "needing to explain it to others too soon"
        ],
        "genius": {
            "description": "At its best, this same pattern becomes the ability to let understanding arrive in its own time.",
            "archetype": "The Witness"
        },
        "micro_shifts": [
            "Try letting the pieces settle without forcing a conclusion.",
            "Ask: What's becoming clearer without effort?"
        ]
    },
}


# ============================================================================
# POSITIVE SIGNAL VOCABULARY
# ============================================================================

POSITIVE_SIGNAL_KEYWORDS = {
    "relational_openness": ["open", "close", "connect", "together", "near", "with"],
    "emotional_softening": ["soft", "gentle", "tender", "ease", "relax", "let go"],
    "vulnerability_access": ["vulnerable", "honest", "real", "true", "show", "reveal"],
    "intimacy_activation": ["intimate", "close", "deep", "meaningful", "present"],
    "trust_returning": ["trust", "safe", "believe", "faith", "reliable"],
    "warmth": ["warm", "love", "care", "affection", "kind", "gentle"],
    "connection": ["connect", "bond", "link", "together", "us", "we"],
    "safety_in_contact": ["safe", "comfortable", "okay", "alright", "secure"],
    "emotional_regulation": ["calm", "steady", "balanced", "regulated", "centered"],
    "grounded_presence": ["grounded", "present", "here", "now", "stable", "rooted"],
    "mutual_recognition": ["see", "seen", "understood", "known", "recognized"],
    "repair_in_progress": ["repair", "fix", "mend", "heal", "restore", "reconcile"],
    "reconnection": ["reconnect", "return", "back", "again", "resume", "renew"],
    "expansion": ["grow", "expand", "open", "more", "possibility", "opportunity"],
    "relief_after_tension": ["relief", "release", "exhale", "finally", "over", "done"],
    "receiving": ["receive", "accept", "allow", "let in", "take in"],
    "heart_opening": ["heart", "love", "open", "feel", "moved", "touched"],
    "stability_after_fluctuation": ["stable", "steady", "consistent", "settled", "even"],
}


# ============================================================================
# TRANSIT-FIRST PATTERN SCORING
# ============================================================================

def score_pattern_transit_alignment(
    pattern_id: str,
    active_themes: List[str],
    theme_intensity: Dict[str, float]
) -> float:
    """
    Score how well a pattern aligns with current transit themes.
    
    Returns: 0.0 to 1.0
    """
    template = PATTERN_TEMPLATES.get(pattern_id)
    if not template:
        return 0.0
    
    compatible_themes = template.get("timing_compatibility", [])
    if not compatible_themes:
        return 0.3  # Neutral score for patterns without timing rules
    
    # Calculate alignment score
    matching_themes = [t for t in compatible_themes if t in active_themes]
    
    if not matching_themes:
        return 0.0  # No alignment = reject pattern
    
    # Base score from match ratio
    base_score = len(matching_themes) / len(compatible_themes)
    
    # Weight by intensity of matching themes
    intensity_boost = 0
    for theme in matching_themes:
        intensity_boost += theme_intensity.get(theme, 0.3)
    
    intensity_boost = intensity_boost / len(matching_themes) if matching_themes else 0
    
    # Final score: base + intensity boost
    final_score = (base_score * 0.6) + (intensity_boost * 0.4)
    
    return min(1.0, final_score)


def score_pattern_signal_alignment(
    pattern_id: str,
    signals: Dict[str, Any]
) -> float:
    """
    Score how well a pattern matches user signals.
    
    Returns: 0.0 to 1.0
    """
    template = PATTERN_TEMPLATES.get(pattern_id)
    if not template:
        return 0.0
    
    signal_keywords = template.get("signal_keywords", [])
    if not signal_keywords:
        return 0.5  # Neutral score
    
    # Collect all text from signals
    all_text = ""
    
    for entry in signals.get("journal_entries", []):
        all_text += " " + entry.get("content", "")
        all_text += " " + " ".join(entry.get("themes", []))
    
    for msg in signals.get("chat_messages", []):
        all_text += " " + msg.get("content", "")
    
    for event in signals.get("lifeline_events", []):
        all_text += " " + (event.get("title", "") or "")
        all_text += " " + (event.get("description", "") or "")
        all_text += " " + (event.get("emotional_tone", "") or "")
    
    all_text = all_text.lower()
    
    # Count keyword matches
    matches = sum(1 for kw in signal_keywords if kw in all_text)
    
    # Score based on match ratio
    if matches == 0:
        return 0.1  # Minimal score if no keyword matches
    
    score = min(1.0, matches / (len(signal_keywords) * 0.5))
    
    # Boost for emotional tone alignment
    emotional_tones = signals.get("emotional_tones", [])
    if emotional_tones:
        tone_boost = 0.1  # Small boost for having detected emotions
        score = min(1.0, score + tone_boost)
    
    return score


def detect_dominant_energy_state(signals: Dict[str, Any]) -> str:
    """
    Detect if user signals indicate OPENING vs CHALLENGE energy.
    
    Returns: "opening", "challenge", or "neutral"
    """
    all_text = ""
    
    for entry in signals.get("journal_entries", []):
        all_text += " " + (entry.get("content", "") or "")
    
    for msg in signals.get("chat_messages", []):
        all_text += " " + (msg.get("content", "") or "")
    
    all_text = all_text.lower()
    
    # Count positive/opening signals
    opening_count = 0
    for signal_name, keywords in POSITIVE_SIGNAL_KEYWORDS.items():
        for kw in keywords:
            if kw in all_text:
                opening_count += 1
                break
    
    # Count challenge signals
    challenge_keywords = [
        "afraid", "scared", "anxious", "worry", "stressed", "overwhelm",
        "angry", "frustrated", "resentful", "stuck", "lost", "confused",
        "sad", "depressed", "lonely", "hurt", "rejected", "abandoned",
        "ashamed", "guilty", "doubt", "uncertain", "pressured", "drained"
    ]
    
    challenge_count = sum(1 for kw in challenge_keywords if kw in all_text)
    
    # Determine dominant state
    if opening_count >= 3 and opening_count > challenge_count * 1.5:
        return "opening"
    elif challenge_count >= 3 and challenge_count > opening_count * 1.5:
        return "challenge"
    else:
        return "neutral"


def select_best_pattern(
    signals: Dict[str, Any],
    transit_themes: Any  # TransitThemes dataclass
) -> tuple[str, Dict[str, float]]:
    """
    Select the best pattern using transit-first logic with POSITIVE/OPENING support.
    
    Final Score = (signal_score × 0.5) + (transit_score × 0.5)
    
    CRITICAL: 
    - Patterns with transit_score < 0.2 are REJECTED
    - If dominant energy is "opening", challenge patterns are penalized
    - If dominant energy is "challenge", opening patterns are penalized
    """
    from services.transit_theme_engine import TIMING_THEMES
    
    scores = {}
    
    # Detect dominant energy state from user signals
    dominant_energy = detect_dominant_energy_state(signals)
    logger.info(f"[PatternSelect] Dominant energy: {dominant_energy}")
    
    # Check if transit themes favor opening
    opening_transit_themes = ["relational_harmony", "emotional_openness", "receptivity", 
                              "renewal_cycle", "reconnection_window", "softening_phase",
                              "integration_phase", "grounded_stability", "expansion"]
    
    transit_favors_opening = any(t in transit_themes.active_themes for t in opening_transit_themes)
    
    for pattern_id, template in PATTERN_TEMPLATES.items():
        # Calculate transit alignment score (CRITICAL)
        transit_score = score_pattern_transit_alignment(
            pattern_id,
            transit_themes.active_themes,
            transit_themes.theme_intensity
        )
        
        # REJECT patterns that don't align with timing
        if transit_score < 0.2:
            logger.debug(f"[PatternSelect] {pattern_id} REJECTED - transit_score={transit_score:.2f}")
            continue
        
        # Calculate signal alignment score
        signal_score = score_pattern_signal_alignment(pattern_id, signals)
        
        # Get pattern type (opening vs challenge)
        pattern_type = template.get("pattern_type", "challenge")
        
        # Apply energy state adjustments
        energy_modifier = 1.0
        
        if dominant_energy == "opening":
            if pattern_type == "opening":
                energy_modifier = 1.3  # Boost opening patterns
            elif pattern_type == "challenge":
                energy_modifier = 0.6  # Penalize challenge patterns heavily
        
        elif dominant_energy == "challenge":
            if pattern_type == "challenge":
                energy_modifier = 1.2  # Boost challenge patterns
            elif pattern_type == "opening":
                energy_modifier = 0.7  # Penalize opening patterns
        
        # If transit favors opening, give extra boost to opening patterns
        if transit_favors_opening and pattern_type == "opening":
            energy_modifier *= 1.15
        
        # Final weighted score: 50/50 split for more transit influence
        base_score = (signal_score * 0.5) + (transit_score * 0.5)
        final_score = base_score * energy_modifier
        
        scores[pattern_id] = {
            "final": final_score,
            "signal": signal_score,
            "transit": transit_score,
            "pattern_type": pattern_type,
            "energy_modifier": energy_modifier,
        }
        
        logger.debug(
            f"[PatternSelect] {pattern_id} ({pattern_type}): "
            f"final={final_score:.2f}, signal={signal_score:.2f}, transit={transit_score:.2f}, "
            f"modifier={energy_modifier:.2f}"
        )
    
    # Select highest scoring pattern
    if not scores:
        # Fallback: no patterns matched timing - use most general pattern
        logger.warning("[PatternSelect] No patterns matched timing, using fallback")
        return "somethings_here", {"final": 0.3, "signal": 0.3, "transit": 0.3, "pattern_type": "neutral"}
    
    best_pattern = max(scores.keys(), key=lambda k: scores[k]["final"])
    return best_pattern, scores[best_pattern]

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
    - INCLUDES positive/opening signal detection
    """
    signals_by_source = {}
    
    pattern_title = pattern.get("title", "")
    what_you_may_be = pattern.get("what_you_may_be", "")
    challenges = pattern.get("challenge", [])
    
    # Detect if this is an opening pattern
    is_opening_pattern = any(word in what_you_may_be.lower() for word in 
        ["warmth", "opening", "softening", "reconnect", "closeness", "safe", "trust", "receiving"])
    
    # Extract key behavioral indicators from the pattern
    pattern_keywords = extract_pattern_keywords(what_you_may_be, challenges)
    
    # =========================================================================
    # JOURNAL SIGNALS
    # =========================================================================
    journal_entries = signals.get("journal_entries", [])
    journal_signals = []
    
    if journal_entries:
        # Analyze journal content for pattern-specific signals
        all_content = " ".join([e.get("content", "") for e in journal_entries[:5]]).lower()
        
        # === POSITIVE / OPENING SIGNALS ===
        if is_opening_pattern:
            # Check for connection/closeness signals
            if any(kw in all_content for kw in ["close", "connect", "together", "warmth", "love"]):
                journal_signals.append(
                    "You described moments of closeness and openness in connection"
                )
            
            # Check for softening/vulnerability signals
            if any(kw in all_content for kw in ["soft", "vulnerable", "open", "honest", "real"]):
                journal_signals.append(
                    "Your writing shows a willingness to be seen or to soften"
                )
            
            # Check for trust/safety signals
            if any(kw in all_content for kw in ["trust", "safe", "secure", "believe", "faith"]):
                journal_signals.append(
                    "You reflected on trust or safety in relationship"
                )
            
            # Check for repair/reconnection signals
            if any(kw in all_content for kw in ["repair", "reconnect", "heal", "mend", "return"]):
                journal_signals.append(
                    "You described movement toward repair or reconnection"
                )
            
            # Check for receiving signals
            if any(kw in all_content for kw in ["receive", "accept", "allow", "let in"]):
                journal_signals.append(
                    "You wrote about openness to receiving"
                )
        
        # === CHALLENGE SIGNALS (existing) ===
        else:
            for entry in journal_entries[:5]:
                content = entry.get("content", "").lower()
                
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
    """
    Generate a pattern mirror for the user using TRANSIT-FIRST logic.
    
    Scoring:
    - Final Score = (signal_score × 0.6) + (transit_score × 0.4)
    - Patterns with transit_score < 0.2 are REJECTED
    """
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    from services.transit_theme_engine import (
        compute_transit_themes,
        generate_timing_context,
        generate_timing_signals
    )
    
    EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')
    
    # STEP 1: Compute current transit themes (CRITICAL - drives pattern selection)
    transit_themes = compute_transit_themes()
    logger.info(f"[PatternMirror] Transit themes: {transit_themes.active_themes}")
    
    # Check cache first (unless force refresh)
    if not force_refresh:
        try:
            cached = await db.pattern_mirror_cache.find_one({
                "user_id": user_id,
                "date": datetime.now(timezone.utc).strftime('%Y-%m-%d')
            })
            if cached:
                logger.info(f"[PatternMirror] Cache hit for user {user_id}")
                # Regenerate dynamic elements for cached response
                signals = await aggregate_user_signals(db, user_id)
                signals_by_source = generate_signals_by_source(signals, cached["pattern"])
                
                # ALWAYS add timing signals (transit_score from cache or default)
                cached_transit_score = cached.get("scores", {}).get("transit", 0.4)
                timing_signals = generate_timing_signals(transit_themes, cached_transit_score)
                if timing_signals:
                    signals_by_source["timing"] = timing_signals
                
                # Generate timing context
                timing_context = generate_timing_context(transit_themes)
                
                return {
                    "pattern": cached["pattern"],
                    "cached": True,
                    "generated_at": cached["generated_at"],
                    "signal_strength": cached.get("signal_strength", "weak"),
                    "signals_by_source": signals_by_source,
                    "timing_context": timing_context,
                    "active_themes": transit_themes.active_themes[:3]
                }
        except Exception as e:
            logger.warning(f"[PatternMirror] Cache check failed: {e}")
    
    # STEP 2: Aggregate user signals
    signals = await aggregate_user_signals(db, user_id)
    
    # STEP 3: Select best pattern using TRANSIT-FIRST scoring
    selected_pattern_id, scores = select_best_pattern(signals, transit_themes)
    logger.info(
        f"[PatternMirror] Selected: {selected_pattern_id} "
        f"(final={scores['final']:.2f}, signal={scores['signal']:.2f}, transit={scores['transit']:.2f})"
    )
    
    # STEP 4: Get pattern template
    template = PATTERN_TEMPLATES.get(selected_pattern_id)
    
    if template:
        # Use template directly (no LLM needed for V1)
        pattern = {
            "title": template["title"],
            "what_you_may_be": template["what_you_may_be"],
            "challenge": template["challenge"],
            "genius": template["genius"],
            "micro_shifts": template["micro_shifts"]
        }
    else:
        # Fallback to LLM generation
        pattern = await _generate_pattern_with_llm(
            signals, transit_themes, EMERGENT_LLM_KEY, user_id
        )
    
    if not pattern:
        return get_fallback_pattern(signals, transit_themes)
    
    # STEP 5: Generate signals by source
    signals_by_source = generate_signals_by_source(signals, pattern)
    
    # STEP 6: ALWAYS add timing signals (pass transit score for priority rule)
    transit_score = scores.get("transit", 0.0)
    timing_signals = generate_timing_signals(transit_themes, transit_score)
    if timing_signals:
        signals_by_source["timing"] = timing_signals
    
    # STEP 7: Generate timing context
    timing_context = generate_timing_context(transit_themes)
    
    # STEP 8: Cache the result
    try:
        await db.pattern_mirror_cache.update_one(
            {"user_id": user_id, "date": datetime.now(timezone.utc).strftime('%Y-%m-%d')},
            {
                "$set": {
                    "pattern": pattern,
                    "signal_strength": signals["signal_strength"],
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "pattern_id": selected_pattern_id,
                    "scores": scores,
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
        "signals_by_source": signals_by_source,
        "timing_context": timing_context,
        "active_themes": transit_themes.active_themes[:3],
        "scores": scores
    }


async def _generate_pattern_with_llm(
    signals: Dict[str, Any],
    transit_themes: Any,
    api_key: str,
    user_id: str
) -> Optional[Dict[str, Any]]:
    """Generate pattern using LLM when template doesn't match."""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    if not api_key:
        return None
    
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
        signal_text = "No recent signals available."
    
    # Add transit context to prompt
    transit_context = f"\n\nCURRENT TIMING THEMES: {', '.join(transit_themes.active_themes[:3])}"
    transit_context += f"\nLunar phase: {transit_themes.lunar_phase}"
    transit_context += f"\nSeasonal context: {transit_themes.seasonal_context}"
    
    emotional_tones = ", ".join(signals["emotional_tones"]) if signals["emotional_tones"] else "None clearly detected"
    
    prompt = PATTERN_GENERATION_PROMPT.format(
        user_signals=signal_text + transit_context,
        emotional_tones=emotional_tones,
        signal_strength=signals["signal_strength"]
    )
    
    try:
        chat = LlmChat(
            api_key=api_key,
            session_id=f"pattern_mirror_{user_id}_{datetime.now().timestamp()}",
            system_message="You are the Pattern Mirror engine. Return ONLY valid JSON."
        )
        chat.with_model("openai", "gpt-5.2")
        
        response = await chat.send_message(UserMessage(text=prompt))
        response_text = response.strip()
        
        # Parse JSON
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        pattern_data = json.loads(response_text.strip())
        
        if "pattern" in pattern_data:
            return pattern_data["pattern"]
        return None
        
    except Exception as e:
        logger.error(f"[PatternMirror] LLM generation failed: {e}")
        return None


def get_fallback_pattern(signals: Dict[str, Any], transit_themes: Any = None) -> Dict[str, Any]:
    """Return a safe fallback pattern when no pattern matches timing."""
    from services.transit_theme_engine import (
        compute_transit_themes,
        generate_timing_context,
        generate_timing_signals
    )
    
    # If no transit themes provided, compute them
    if transit_themes is None:
        transit_themes = compute_transit_themes()
    
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
    
    # ALWAYS add timing signals (use default transit_score for fallback)
    timing_signals = generate_timing_signals(transit_themes, 0.3)
    if timing_signals:
        signals_by_source["timing"] = timing_signals
    
    # Generate timing context
    timing_context = generate_timing_context(transit_themes)
    
    return {
        "pattern": pattern,
        "cached": False,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "signal_strength": signals.get("signal_strength", "weak"),
        "signals_by_source": signals_by_source,
        "timing_context": timing_context,
        "active_themes": transit_themes.active_themes[:3],
        "fallback": True
    }
