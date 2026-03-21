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
from typing import Dict, List, Optional, Any, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from dotenv import load_dotenv


# ============================================================================
# PERSONALIZED TRANSIT TARGETING - Venus Sequence Mapping
# ============================================================================

# Map timing themes to Venus Sequence targets
THEME_TO_VENUS_TARGETS = {
    # Challenge/Neutral themes
    "emotional_sensitivity": ["eq", "sq"],
    "clarity_vs_confusion": ["iq", "core"],
    "pressure": ["core", "iq"],
    "urgency": ["purpose", "core"],
    "transition_threshold": ["core", "purpose"],
    "reset_cycle": ["core", "eq"],
    "relational_sensitivity": ["sq", "attraction"],
    "identity_shift": ["core", "purpose"],
    "expansion": ["purpose", "attraction"],
    "contraction": ["core", "iq"],
    
    # Positive/Opening themes
    "relational_harmony": ["sq", "attraction"],
    "emotional_openness": ["eq", "sq"],
    "receptivity": ["attraction", "sq"],
    "renewal_cycle": ["core", "eq"],
    "reconnection_window": ["sq", "attraction"],
    "softening_phase": ["eq", "attraction"],
    "integration_phase": ["iq", "core"],
    "grounded_stability": ["core", "iq"],
}

# Human-readable descriptions for Venus Sequence spheres (NO Gene Key numbers)
VENUS_SPHERE_DESCRIPTIONS = {
    "core": {
        "name": "core stability",
        "description": "how you hold your ground and sense of self",
        "shadow": "where pressure can destabilize",
        "gift": "where groundedness emerges",
    },
    "eq": {
        "name": "emotional intelligence",
        "description": "how you relate to expectations and emotional clarity",
        "shadow": "where emotions can overwhelm discernment",
        "gift": "where emotional wisdom becomes available",
    },
    "sq": {
        "name": "relational intelligence",
        "description": "how you show up in connection with others",
        "shadow": "where relating can feel effortful",
        "gift": "where intimacy and ease become possible",
    },
    "iq": {
        "name": "mental clarity",
        "description": "how you process and make sense of things",
        "shadow": "where thinking can loop or confuse",
        "gift": "where insight and understanding arrive",
    },
    "attraction": {
        "name": "what draws others to you",
        "description": "the quality that naturally invites connection",
        "shadow": "where self-presentation can feel forced",
        "gift": "where authentic magnetism emerges",
    },
    "purpose": {
        "name": "your sense of direction",
        "description": "what gives meaning to your efforts",
        "shadow": "where purpose can feel unclear",
        "gift": "where alignment with direction emerges",
    },
}


def compute_personal_activations(
    user_profile: Optional[Dict[str, Any]],
    active_themes: List[str],
    transit_score: float
) -> List[Dict[str, Any]]:
    """
    Map timing themes to user's Gene Keys Venus Sequence.
    
    Returns top 2 activated spheres with scores.
    NO Gene Key numbers in output - only sphere descriptions.
    """
    # Default Venus Sequence if not available
    default_venus = {
        "core": 1,
        "eq": 2,
        "sq": 3,
        "iq": 4,
        "attraction": 5,
        "purpose": 6,
    }
    
    # Get user's Venus Sequence
    venus = default_venus
    if user_profile:
        gene_keys = user_profile.get("gene_keys", {})
        if gene_keys and "venus_sequence" in gene_keys:
            venus = gene_keys.get("venus_sequence", default_venus)
    
    # Calculate activation scores for each sphere
    scores = {k: 0.0 for k in venus.keys()}
    
    for theme in active_themes:
        targets = THEME_TO_VENUS_TARGETS.get(theme, [])
        for target in targets:
            if target in scores:
                # Weight by theme position (first themes are strongest)
                theme_index = active_themes.index(theme) if theme in active_themes else 0
                weight = 1.0 - (theme_index * 0.15)  # Decay by position
                scores[target] += transit_score * weight
    
    # Sort by score and take top 2
    sorted_targets = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:2]
    
    # Build activations with descriptions (NO Gene Key numbers)
    activations = []
    for target, score in sorted_targets:
        if score > 0:
            sphere_info = VENUS_SPHERE_DESCRIPTIONS.get(target, {})
            activations.append({
                "target": target,
                "gene_key": venus.get(target, 0),  # Internal use only
                "score": round(score, 2),
                "name": sphere_info.get("name", target),
                "description": sphere_info.get("description", ""),
            })
    
    return activations


# ============================================================================
# UNIFIED NARRATIVE BUILDER
# ============================================================================

def build_unified_narrative(
    pattern: Dict[str, Any],
    signals_by_source: Dict[str, List[str]],
    timing_context: List[str],
    activations: List[Dict[str, Any]],
    active_themes: List[str]
) -> str:
    """
    Build a SINGLE unified narrative that combines:
    - Pattern recognition (what you may be)
    - Timing context (what's happening now)
    - Personal activation (where it's touching you)
    
    Rules:
    - No astrology terms
    - No "Gene Key 41"
    - No jargon
    - Must feel like a single coherent reflection
    """
    parts = []
    
    # Part 1: Pattern sentence (from "what_you_may_be")
    what_you_may_be = pattern.get("what_you_may_be", "")
    if what_you_may_be:
        parts.append(what_you_may_be)
    
    # Part 2: Timing sentence (grounded, not mystical)
    timing_sentence = build_timing_sentence(timing_context, active_themes)
    if timing_sentence:
        parts.append(timing_sentence)
    
    # Part 3: Activation sentence (personalized, no jargon)
    if activations:
        activation_sentence = build_activation_sentence(activations)
        if activation_sentence:
            parts.append(activation_sentence)
    
    # Join with double newlines for readability
    return "\n\n".join(parts)


def build_timing_sentence(
    timing_context: List[str],
    active_themes: List[str]
) -> str:
    """
    Build a grounded timing sentence.
    
    Style:
    "Right now, [timing condition], which can make [pattern feeling]."
    """
    if not timing_context and not active_themes:
        return ""
    
    # Map themes to timing phrases
    theme_phrases = {
        "emotional_sensitivity": "emotional sensitivity may be higher than usual",
        "clarity_vs_confusion": "mental clarity may come and go",
        "pressure": "pressure may feel more present than usual",
        "transition_threshold": "you may be at a threshold between phases",
        "reset_cycle": "a natural reset may be underway",
        "relational_sensitivity": "relational sensitivity may be heightened",
        "relational_harmony": "connection may feel more available",
        "emotional_openness": "emotional openness may feel more accessible",
        "softening_phase": "defenses may be naturally softening",
        "renewal_cycle": "new energy may be present",
        "expansion": "a sense of expansion may be available",
        "receptivity": "receptivity may be heightened",
    }
    
    # Get primary timing phrase
    timing_phrase = None
    for theme in active_themes[:2]:
        if theme in theme_phrases:
            timing_phrase = theme_phrases[theme]
            break
    
    if not timing_phrase and timing_context:
        # Fallback to first timing context, cleaned up
        timing_phrase = timing_context[0].lower()
        if timing_phrase.startswith("this may"):
            timing_phrase = timing_phrase[9:]  # Remove "This may"
    
    if not timing_phrase:
        return ""
    
    # Build the sentence
    # Determine if opening or challenge energy
    opening_themes = ["relational_harmony", "emotional_openness", "receptivity",
                      "renewal_cycle", "softening_phase", "expansion"]
    
    is_opening = any(t in active_themes for t in opening_themes)
    
    if is_opening:
        effect_clause = "which can make openness feel both inviting and uncertain"
    else:
        effect_clause = "which can make this pattern feel more present"
    
    return f"Right now, {timing_phrase}, {effect_clause}."


def build_activation_sentence(
    activations: List[Dict[str, Any]]
) -> str:
    """
    Build a personal activation sentence.
    
    Style:
    "This may be touching [sphere description] — where [shadow/gift dynamic]."
    
    NO Gene Key numbers. NO jargon.
    """
    if not activations:
        return ""
    
    # Get primary activation
    primary = activations[0]
    target = primary.get("target", "")
    name = primary.get("name", target)
    description = primary.get("description", "")
    
    # Build sphere-specific endings
    sphere_endings = {
        "core": "where it's easy to feel destabilized, but also where groundedness can emerge",
        "eq": "where it's easy to respond to what you feel, but harder to tell what is actually true",
        "sq": "where showing up in connection can feel effortful, but also where intimacy becomes possible",
        "iq": "where thinking can loop, but also where clarity can arrive",
        "attraction": "where self-presentation can feel forced, but also where authenticity wants to emerge",
        "purpose": "where direction can feel unclear, but also where meaning becomes visible",
    }
    
    ending = sphere_endings.get(target, "where something wants your attention")
    
    # Build the sentence
    if description:
        return f"This may be touching {description} — {ending}."
    else:
        return f"This may be touching {name} — {ending}."

load_dotenv()

logger = logging.getLogger(__name__)


# ============================================================================
# USER PROFILE HELPER
# ============================================================================

async def get_user_profile(db: AsyncIOMotorDatabase, user_id: str) -> Optional[Dict[str, Any]]:
    """Fetch user profile including Gene Keys data for personalized activations."""
    try:
        from bson import ObjectId
        # Try with string first
        user = await db.users.find_one({"_id": user_id})
        if not user:
            # Try with ObjectId
            try:
                user = await db.users.find_one({"_id": ObjectId(user_id)})
            except:
                pass
        return user
    except Exception as e:
        logger.warning(f"[PatternMirror] Failed to fetch user profile: {e}")
        return None


# ============================================================================
# V2: SIGNALS-FIRST RESPONSE STRUCTURE
# ============================================================================

def build_personal_pattern_layer(
    pattern: Dict[str, Any],
    signals: Dict[str, Any],
    pattern_evidence: Dict[str, Any],
    scores: Dict[str, float]
) -> Dict[str, Any]:
    """
    Build the PERSONAL_PATTERN layer of the response.
    
    This represents what was derived from personal signals:
    - journal
    - mirror chat
    - lifeline
    
    This is the PRIMARY truth of the homepage.
    """
    return {
        "selected_pattern_id": pattern_evidence.get("pattern_id", "unknown"),
        "selected_pattern_title": pattern.get("title", ""),
        "selected_pattern_summary": pattern.get("what_you_may_be", ""),
        "primary_signal_sources": pattern_evidence.get("contributing_sources", []),
        "primary_signal_evidence": pattern_evidence.get("matched_evidence", {}),
        "signal_strength": signals.get("signal_strength", "weak"),
        "signal_score": round(scores.get("signal", 0), 3),
    }


def build_timing_amplifier_layer(
    transit_themes: Any,
    scores: Dict[str, float],
    timing_context: List[str]
) -> Dict[str, Any]:
    """
    Build the TIMING_AMPLIFIER layer of the response.
    
    This represents contextual timing that may amplify or modulate:
    - lunar phase
    - seasonal context
    - transit themes
    
    This is SECONDARY to personal signals.
    """
    fallback_mode = scores.get("fallback_mode", False)
    
    # Determine timing role
    if fallback_mode:
        timing_role = "fallback"  # Timing is driving because personal data is sparse
    else:
        timing_role = "amplifier"  # Timing is only amplifying personal signals
    
    return {
        "active_timing_themes": transit_themes.active_themes[:3] if transit_themes else [],
        "timing_summary": timing_context[0] if timing_context else None,
        "transit_score": round(scores.get("transit", 0), 3),
        "timing_role": timing_role,
        "lunar_phase": transit_themes.lunar_phase if transit_themes else None,
        "seasonal_context": transit_themes.seasonal_context if transit_themes else None,
    }


def build_signals_first_narrative(
    pattern: Dict[str, Any],
    pattern_evidence: Dict[str, Any],
    timing_context: List[str],
    active_themes: List[str],
    fallback_mode: bool = False
) -> Dict[str, Any]:
    """
    Build the narrative in SIGNALS-FIRST order:
    
    1. Main pattern title
    2. Main pattern explanation (from personal signals)
    3. Optional timing note (amplification only)
    4. Evidence summary
    
    Timing does NOT author the main narrative.
    """
    # A. Main pattern explanation (purely from pattern template, selected by signals)
    main_explanation = pattern.get("what_you_may_be", "")
    
    # B. Optional timing note (ONLY if not fallback mode)
    timing_note = None
    if not fallback_mode and active_themes:
        # Build a subtle timing amplification note
        timing_note = _build_timing_amplification_note(active_themes, timing_context)
    
    # C. Evidence summary sentence
    evidence_summary = _build_evidence_summary(pattern_evidence)
    
    return {
        "main_explanation": main_explanation,
        "timing_note": timing_note,
        "evidence_summary": evidence_summary,
        # Combined narrative for backwards compatibility
        "combined": _combine_narrative_parts(main_explanation, timing_note, evidence_summary)
    }


def _build_timing_amplification_note(
    active_themes: List[str],
    timing_context: List[str]
) -> Optional[str]:
    """
    Build a SHORT timing amplification note.
    
    Style: "This may feel more present right now because [timing context]."
    
    NOT: Blended into main explanation
    """
    # Map themes to short amplification phrases
    amplification_phrases = {
        "emotional_sensitivity": "emotional sensitivity may be heightened",
        "transition_threshold": "you may be at a threshold moment",
        "reset_cycle": "a natural reset cycle may be underway",
        "renewal_cycle": "renewal energy is present",
        "relational_harmony": "relational conditions are supportive",
        "emotional_openness": "emotional openness feels more available",
        "softening_phase": "a softening is naturally occurring",
        "expansion": "expansion energy is present",
        "pressure": "pressure may be intensifying things",
        "urgency": "urgency may be amplifying this",
    }
    
    # Get the most relevant timing phrase
    timing_phrase = None
    for theme in active_themes[:2]:
        if theme in amplification_phrases:
            timing_phrase = amplification_phrases[theme]
            break
    
    if not timing_phrase and timing_context:
        # Use first timing context, cleaned up
        ctx = timing_context[0]
        if ctx.lower().startswith("this may be"):
            timing_phrase = ctx[12:].strip()  # Remove "This may be "
        else:
            timing_phrase = ctx.lower()
    
    if timing_phrase:
        return f"This may feel more present right now because {timing_phrase}."
    
    return None


def _build_evidence_summary(pattern_evidence: Dict[str, Any]) -> Optional[str]:
    """
    Build a brief evidence summary.
    
    Style: "This pattern emerged from [sources]."
    """
    sources = pattern_evidence.get("contributing_sources", [])
    
    if not sources:
        return None
    
    source_names = {
        "journal": "your recent journal entries",
        "mirror_chat": "your Mirror conversations",
        "lifeline": "your lifeline events",
    }
    
    readable_sources = [source_names.get(s, s) for s in sources if s in source_names]
    
    if not readable_sources:
        return None
    
    if len(readable_sources) == 1:
        return f"This pattern emerged from {readable_sources[0]}."
    elif len(readable_sources) == 2:
        return f"This pattern emerged from {readable_sources[0]} and {readable_sources[1]}."
    else:
        return f"This pattern emerged from {', '.join(readable_sources[:-1])}, and {readable_sources[-1]}."


def _combine_narrative_parts(
    main_explanation: str,
    timing_note: Optional[str],
    evidence_summary: Optional[str]
) -> str:
    """Combine narrative parts for backwards compatibility."""
    parts = [main_explanation]
    if timing_note:
        parts.append(timing_note)
    if evidence_summary:
        parts.append(evidence_summary)
    return "\n\n".join(parts)


def generate_true_evidence(
    signals: Dict[str, Any],
    pattern_id: str,
    pattern: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate TRUE evidence that shows what actually matched.
    
    This is NOT post-hoc rationalization.
    This shows the ACTUAL signal matches that led to pattern selection.
    
    Returns:
    {
        "pattern_id": str,
        "contributing_sources": ["journal", "lifeline", ...],
        "matched_evidence": {
            "journal": [{"text": "...", "matched_keyword": "...", "strength": "high"}],
            "lifeline": [...],
            "mirror_chat": [...]
        },
        "total_matches": int,
        "primary_source": str (source with most matches)
    }
    """
    evidence = {
        "pattern_id": pattern_id,
        "contributing_sources": [],
        "matched_evidence": {},
        "total_matches": 0,
        "primary_source": None,
    }
    
    # Get pattern keywords
    template = PATTERN_TEMPLATES.get(pattern_id, {})
    signal_keywords = template.get("signal_keywords", [])
    what_you_may_be = pattern.get("what_you_may_be", "").lower()
    
    # Additional keywords from pattern description
    pattern_words = ["feel", "emotion", "decide", "trust", "control", "close", "open", 
                     "connect", "fear", "doubt", "wait", "stuck", "resist", "avoid"]
    all_keywords = list(set(signal_keywords + [w for w in pattern_words if w in what_you_may_be]))
    
    source_match_counts = {}
    
    # Check JOURNAL
    journal_matches = []
    for entry in signals.get("journal_entries", [])[:5]:
        content = entry.get("content", "").lower()
        for kw in all_keywords:
            if kw in content:
                journal_matches.append({
                    "text": entry.get("content", "")[:100] + "...",
                    "matched_keyword": kw,
                    "strength": "high" if content.count(kw) > 1 else "moderate",
                    "date": entry.get("created_at", "")[:10] if entry.get("created_at") else None
                })
                break  # One match per entry
    
    if journal_matches:
        evidence["matched_evidence"]["journal"] = journal_matches[:3]
        evidence["contributing_sources"].append("journal")
        source_match_counts["journal"] = len(journal_matches)
    
    # Check MIRROR CHAT
    chat_matches = []
    for msg in signals.get("chat_messages", [])[:10]:
        content = msg.get("content", "").lower()
        for kw in all_keywords:
            if kw in content:
                chat_matches.append({
                    "text": msg.get("content", "")[:80] + "...",
                    "matched_keyword": kw,
                    "strength": "moderate",
                })
                break
    
    if chat_matches:
        evidence["matched_evidence"]["mirror_chat"] = chat_matches[:3]
        evidence["contributing_sources"].append("mirror_chat")
        source_match_counts["mirror_chat"] = len(chat_matches)
    
    # Check LIFELINE
    lifeline_matches = []
    for event in signals.get("lifeline_events", [])[:10]:
        title = (event.get("title") or "").lower()
        desc = (event.get("description") or "").lower()
        combined = f"{title} {desc}"
        
        for kw in all_keywords:
            if kw in combined:
                lifeline_matches.append({
                    "text": event.get("title", ""),
                    "matched_keyword": kw,
                    "strength": "high" if event.get("emotional_tone") else "moderate",
                    "emotional_tone": event.get("emotional_tone"),
                })
                break
    
    if lifeline_matches:
        evidence["matched_evidence"]["lifeline"] = lifeline_matches[:3]
        evidence["contributing_sources"].append("lifeline")
        source_match_counts["lifeline"] = len(lifeline_matches)
    
    # Calculate totals
    evidence["total_matches"] = sum(source_match_counts.values())
    
    if source_match_counts:
        evidence["primary_source"] = max(source_match_counts, key=source_match_counts.get)
    
    return evidence


def compute_signal_only_ranking(
    signals: Dict[str, Any],
    transit_themes: Any
) -> List[Dict[str, Any]]:
    """
    Compute pattern ranking by SIGNAL SCORE ONLY (ignoring transit).
    
    Used for debug output to show what would have been selected
    without transit influence.
    """
    from services.transit_theme_engine import TIMING_THEMES
    
    signal_rankings = []
    
    for pattern_id, template in PATTERN_TEMPLATES.items():
        signal_score = score_pattern_signal_alignment(pattern_id, signals)
        
        signal_rankings.append({
            "pattern_id": pattern_id,
            "signal_score": round(signal_score, 3),
            "title": template.get("title", "")
        })
    
    # Sort by signal score descending
    signal_rankings.sort(key=lambda x: x["signal_score"], reverse=True)
    
    return signal_rankings[:5]  # Top 5


def determine_timing_impact(
    signal_only_top: List[Dict[str, Any]],
    final_top: List[Dict[str, Any]],
    selected_pattern_id: str
) -> Dict[str, Any]:
    """
    Determine whether timing changed the winner or only amplified it.
    """
    signal_winner = signal_only_top[0]["pattern_id"] if signal_only_top else None
    final_winner = final_top[0]["pattern_id"] if final_top else selected_pattern_id
    
    if signal_winner == final_winner:
        timing_changed_winner = False
        impact_description = "Timing amplified the signal-selected pattern"
    else:
        timing_changed_winner = True
        impact_description = f"Timing changed selection from '{signal_winner}' to '{final_winner}'"
    
    return {
        "timing_changed_winner": timing_changed_winner,
        "signal_only_winner": signal_winner,
        "final_winner": final_winner,
        "impact_description": impact_description
    }


# ============================================================================
# V3: MULTI-SIGNAL CLUSTERING ENGINE
# ============================================================================

# Theme categories for clustering
THEME_CATEGORIES = {
    "relational": ["connect", "partner", "relationship", "love", "trust", "intimacy", "close", 
                   "warmth", "openness", "vulnerable", "heart", "bond", "attachment", "safe"],
    "emotional": ["feel", "emotion", "sad", "angry", "fear", "joy", "anxious", "overwhelm",
                  "sensitive", "mood", "cry", "hurt", "pain", "healing", "grief"],
    "behavioral": ["decide", "control", "resist", "avoid", "stuck", "wait", "act", "move",
                   "change", "habit", "pattern", "cycle", "repeat", "stop", "start"],
    "identity": ["who", "self", "purpose", "direction", "lost", "confused", "meaning",
                 "growth", "change", "becoming", "identity", "role", "calling"],
    "pressure": ["pressure", "stress", "deadline", "urgent", "overwhelm", "busy", "tired",
                 "exhausted", "burden", "responsibility", "must", "should", "need"],
}

# Map pattern_ids to theme categories
PATTERN_TO_THEME_CATEGORY = {
    "relational_reopening": "relational",
    "heart_thaw": "relational",
    "safe_intimacy_returning": "relational",
    "somethings_here": "emotional",
    "threshold_standing": "behavioral",
    "closed_door_syndrome": "relational",
    "over_functioning_hero": "behavioral",
    "inner_critic_override": "identity",
    "waiting_for_permission": "behavioral",
    "perfectionist_paralysis": "behavioral",
    "emotional_flooding": "emotional",
    "avoidant_autopilot": "behavioral",
    "control_grip": "behavioral",
    "boundary_blur": "relational",
    "people_pleasing_loop": "relational",
}


# ============================================================================
# V10: CONTEXT-AWARE LANGUAGE GENERATION LAYER
# ============================================================================
# This layer transforms static pattern templates into dynamic, signal-responsive
# language. Maps remain as fallback/baseline, but outputs adapt to user signals.
#
# Core shift: pattern → fixed string  >>>  pattern + signals → generated sentence
# ============================================================================

# Note: Uses hashlib and datetime already imported at top of file

# --- SIGNAL TONE DETECTION ---
# Keywords that indicate emotional/behavioral tones in user signals

SIGNAL_TONE_MARKERS = {
    # Hesitation / caution tones
    "hesitation": ["but", "though", "not sure", "maybe", "wonder", "afraid", "scared", 
                   "worry", "uncertain", "hesitant", "cautious", "careful", "nervous"],
    
    # Warmth / opening tones
    "warmth": ["grateful", "thankful", "love", "appreciate", "glad", "happy", "warm",
               "close", "connected", "open", "ready", "excited", "hopeful"],
    
    # Clarity / insight tones
    "clarity": ["realize", "understand", "see now", "clear", "obvious", "finally",
                "makes sense", "figured", "know", "aware", "recognize", "notice"],
    
    # Confusion / overwhelm tones
    "confusion": ["confused", "overwhelmed", "lost", "stuck", "don't know", "unclear",
                  "fog", "can't see", "mixed", "torn", "scattered", "messy"],
    
    # Pressure / urgency tones
    "pressure": ["must", "have to", "need to", "should", "deadline", "urgent", 
                 "pressure", "stress", "overwhelm", "too much", "can't keep up"],
    
    # Resistance / guardedness tones
    "resistance": ["don't want", "can't", "won't", "refuse", "no", "stop", "protect",
                   "guard", "wall", "shield", "defensive", "closed", "shut"],
    
    # Grief / loss tones
    "grief": ["miss", "lost", "gone", "ending", "goodbye", "grief", "sad", "mourn",
              "letting go", "was", "used to", "before"],
    
    # Growth / momentum tones
    "growth": ["growing", "learning", "changing", "becoming", "evolving", "shifting",
               "moving", "progress", "forward", "new", "different", "transform"],
}

# --- LIFELINE PATTERN DETECTION ---
# Patterns observable in lifeline/history that inform language

LIFELINE_PATTERNS = {
    "delayed_action": ["waited", "took time", "finally", "after", "eventually"],
    "repeated_cycles": ["again", "same", "pattern", "before", "always", "every time"],
    "breakthrough_moments": ["first time", "never before", "breakthrough", "finally did"],
    "relational_themes": ["relationship", "partner", "friend", "family", "they", "we"],
    "identity_shifts": ["became", "changed", "no longer", "used to be", "now I"],
}

# --- CONTEXTUAL MODIFIERS ---
# Phrases that can be appended based on detected tones

CONTEXTUAL_MODIFIERS = {
    "hesitation": [
        ", even if part of you is still cautious",
        ", though something may still feel uncertain",
        "—even with the hesitation that's also present",
        ", while honoring the part that isn't fully sure yet",
    ],
    "warmth": [
        ", and there's a softness present that supports this",
        "—something in you is already moving toward this",
        ", with a readiness that wasn't there before",
        ", and you may feel more open to it than expected",
    ],
    "clarity": [
        ", and you may already sense what this is about",
        "—something is becoming clearer",
        ", with a recognition that feels familiar",
        ", and the knowing may already be present",
    ],
    "confusion": [
        ", even when clarity feels hard to find",
        "—the not-knowing is part of it right now",
        ", even in the middle of the fog",
        ", and that's okay while things settle",
    ],
    "pressure": [
        ", especially under current pressures",
        "—the intensity you're feeling makes sense",
        ", and the urgency may be amplifying this",
        ", even when everything feels like too much",
    ],
    "resistance": [
        ", even with the part of you that wants to step back",
        "—the guardedness makes sense given what you've experienced",
        ", while respecting your need to protect",
        ", honoring what the resistance might be telling you",
    ],
    "grief": [
        ", even as you're processing what's been lost",
        "—the weight of what's ending is real",
        ", while holding space for what was",
        ", and grief may be part of what's moving through",
    ],
    "growth": [
        ", and something new is genuinely emerging",
        "—you're not the same as you were",
        ", and the change is real, even if subtle",
        ", with momentum that's building",
    ],
}

# --- SENTENCE VARIATION STRUCTURES ---
# Different ways to begin similar sentences (for variation)

SENTENCE_OPENERS = {
    "timing": [
        "Current timing may be",
        "Right now, conditions may be",
        "This moment seems to be",
        "Something about now is",
        "The present moment may be",
    ],
    "personal": [
        "Something in you may be",
        "Part of you might be",
        "You may be finding yourself",
        "There's a sense that you're",
        "You might be noticing",
    ],
    "observation": [
        "What's showing up is",
        "What seems present is",
        "What's emerging is",
        "What may be true is",
        "What's becoming visible is",
    ],
    "invitation": [
        "Try noticing",
        "See if you can",
        "Consider",
        "Let yourself",
        "Give yourself permission to",
    ],
}

# --- VERB VARIATIONS ---
# Synonyms for common verbs to add natural variation

VERB_VARIATIONS = {
    "notice": ["notice", "observe", "see", "recognize", "sense"],
    "allow": ["allow", "let", "permit", "give space for", "make room for"],
    "try": ["try", "experiment with", "see what happens if you", "explore"],
    "stay": ["stay", "remain", "linger", "rest", "settle"],
    "soften": ["soften", "ease", "relax", "release", "loosen"],
}


# ============================================================================
# V10.1: STRUCTURAL VARIATION SYSTEM
# ============================================================================
# Instead of always using the same base sentence with modifiers,
# select fundamentally different sentence structures based on signal patterns.
#
# Core shift: base_sentence + modifier  >>>  signal-driven sentence selection
# ============================================================================

# --- SIGNAL COMBINATION TYPES ---
# Named combinations that map to specific structural choices

SIGNAL_COMBINATIONS = {
    "grief_resistance": ["grief", "resistance"],
    "growth_confusion": ["growth", "confusion"],
    "warmth_hesitation": ["warmth", "hesitation"],
    "clarity_pressure": ["clarity", "pressure"],
    "grief_growth": ["grief", "growth"],
    "hesitation_confusion": ["hesitation", "confusion"],
    "warmth_clarity": ["warmth", "clarity"],
    "pressure_resistance": ["pressure", "resistance"],
}


# ============================================================================
# V10.2: CROSS-SECTION COHERENCE SYSTEM
# ============================================================================
# Ensures all sections of a Mirror card follow the SAME underlying frame
# and feel like one coherent narrative, not separately generated sections.
#
# Core shift: independent section generation >>> shared "thought frame" per card
# ============================================================================

# --- FRAME TYPES ---
# Each frame type represents a coherent conceptual lens that guides all sections.
# Frames are selected based on signal patterns and then passed to all generators.

FRAME_TYPES = {
    # --- Action-oriented frames ---
    "edge_of_action": {
        "description": "Standing at the verge of doing something different",
        "tone": "present, forward-leaning, embodied",
        "metaphors": ["edge", "step", "threshold", "brink", "verge"],
        "signal_affinities": ["growth", "clarity"],
    },
    "testing_the_waters": {
        "description": "Tentatively exploring whether something is safe",
        "tone": "cautious, curious, protective",
        "metaphors": ["testing", "checking", "watching", "feeling out"],
        "signal_affinities": ["hesitation", "warmth"],
    },
    
    # --- Protection-oriented frames ---
    "walls_questioning": {
        "description": "Defenses reconsidering their necessity",
        "tone": "guarded but curious, self-protective",
        "metaphors": ["walls", "shields", "armor", "guard", "protection"],
        "signal_affinities": ["resistance", "hesitation"],
    },
    "grief_underneath": {
        "description": "Loss or grief driving current experience",
        "tone": "tender, heavy, honoring what was",
        "metaphors": ["holding", "loss", "weight", "what was", "letting go"],
        "signal_affinities": ["grief", "resistance"],
    },
    
    # --- Emergence frames ---
    "something_surfacing": {
        "description": "Something unnamed is becoming visible",
        "tone": "quiet, attentive, pre-verbal",
        "metaphors": ["surfacing", "emerging", "rising", "appearing", "showing"],
        "signal_affinities": ["confusion", "warmth"],
    },
    "clarity_arriving": {
        "description": "Understanding is becoming available",
        "tone": "clear, grounded, recognizing",
        "metaphors": ["seeing", "knowing", "recognizing", "clear", "obvious"],
        "signal_affinities": ["clarity", "growth"],
    },
    
    # --- Pattern frames ---
    "here_again": {
        "description": "Recognizing a familiar pattern returning",
        "tone": "aware, weary but wise, pattern-seeing",
        "metaphors": ["again", "before", "pattern", "cycle", "familiar"],
        "signal_affinities": ["repeated_cycles"],
    },
    "something_different": {
        "description": "This time might be different",
        "tone": "hopeful, aware of past, open to change",
        "metaphors": ["different", "this time", "new", "shift", "change"],
        "signal_affinities": ["growth", "repeated_cycles"],
    },
    
    # --- Pressure frames ---
    "pressing_forward": {
        "description": "External or internal pressure to move",
        "tone": "urgent, compressed, demanding",
        "metaphors": ["pressing", "pushing", "must", "now", "time"],
        "signal_affinities": ["pressure", "clarity"],
    },
    "weight_carried": {
        "description": "Bearing too much, running low",
        "tone": "heavy, depleted, acknowledging limits",
        "metaphors": ["weight", "carrying", "heavy", "full", "too much"],
        "signal_affinities": ["pressure", "grief"],
    },
    
    # --- Movement frames ---
    "ready_to_release": {
        "description": "Something held is ready to move",
        "tone": "releasing, allowing, surrendering",
        "metaphors": ["release", "let go", "move through", "flow", "out"],
        "signal_affinities": ["growth", "grief"],
    },
    "holding_back": {
        "description": "Something wants to move but is being contained",
        "tone": "constrained, full, containing",
        "metaphors": ["holding", "back", "in", "contained", "stopped"],
        "signal_affinities": ["resistance", "pressure"],
    },
}

# --- FRAME MAPPING ---
# Maps each structure's "framing" field to a coherent frame_type
# This ensures that when we select a structure, we get its frame_type

FRAMING_TO_FRAME_TYPE = {
    # Opening/action framings
    "opening": "edge_of_action",
    "pull": "edge_of_action",
    "readiness": "edge_of_action",
    "small_moment": "edge_of_action",
    "small_step": "edge_of_action",
    
    # Testing/cautious framings
    "testing": "testing_the_waters",
    "between": "testing_the_waters",
    "uncertainty": "testing_the_waters",
    "naming_fear": "testing_the_waters",
    
    # Protection framings
    "protection": "walls_questioning",
    "self_protection": "walls_questioning",
    "proof_seeking": "walls_questioning",
    "certainty_seeking": "walls_questioning",
    "staying": "walls_questioning",
    "risk": "walls_questioning",
    
    # Grief framings
    "grief_aware": "grief_underneath",
    "after_loss": "grief_underneath",
    "grief_tinged": "grief_underneath",
    "betrayal_fear": "grief_underneath",
    "grief_honoring": "grief_underneath",
    "fear": "grief_underneath",
    "permission": "grief_underneath",
    
    # Emergence framings
    "emergence": "something_surfacing",
    "fog": "something_surfacing",
    "unwilled": "something_surfacing",
    "body": "something_surfacing",
    "body_knowing": "something_surfacing",
    "curiosity": "something_surfacing",
    
    # Clarity framings
    "recognition": "clarity_arriving",
    "decision": "clarity_arriving",
    "unavoidable": "clarity_arriving",
    "knowing": "clarity_arriving",
    "naming": "clarity_arriving",
    "receiving": "clarity_arriving",
    "questioning": "clarity_arriving",
    
    # Pattern framings
    "pattern": "here_again",
    "pattern_recognition": "here_again",
    "pattern_awareness": "here_again",
    "pattern_breaking": "something_different",
    
    # Pressure framings
    "timing": "pressing_forward",
    "pressure": "pressing_forward",
    "pressure_aware": "pressing_forward",
    "urgency": "pressing_forward",
    "control": "pressing_forward",
    "perfectionism": "pressing_forward",
    "honesty": "pressing_forward",
    
    # Weight framings
    "weight": "weight_carried",
    "depletion": "weight_carried",
    "imbalance": "weight_carried",
    "guilt": "weight_carried",
    "identity": "weight_carried",
    "worthiness": "weight_carried",
    "good_enough": "weight_carried",
    "not_doing": "weight_carried",
    "asking": "weight_carried",
    "rest": "weight_carried",
    "saying_no": "weight_carried",
    "priority": "weight_carried",
    
    # Release framings
    "release": "ready_to_release",
    "transition": "ready_to_release",
    "softening": "ready_to_release",
    "unguarded": "ready_to_release",
    "witnessing": "ready_to_release",
    "expression": "ready_to_release",
    
    # Holding framings
    "containment": "holding_back",
    "minimizing": "holding_back",
    "rushing": "holding_back",
    "pacing": "holding_back",
    "avoidance": "holding_back",
    "dismissing": "holding_back",
    "loss_aversion": "holding_back",
    "believing": "holding_back",
    "bargaining": "holding_back",
    "pausing": "holding_back",
    "thanking": "holding_back",
    "automatic": "holding_back",
}

# --- FRAME-COMPATIBLE FRAMINGS ---
# For each frame_type, list which structural framings are compatible
# Used to filter structure selection in subsequent sections

FRAME_COMPATIBLE_FRAMINGS = {
    "edge_of_action": [
        "opening", "pull", "readiness", "small_moment", "small_step",
        "receiving", "timing", "decision", "questioning", "honesty",
    ],
    "testing_the_waters": [
        "testing", "between", "uncertainty", "naming_fear",
        "staying", "small_moment", "body_knowing", "curiosity",
    ],
    "walls_questioning": [
        "protection", "self_protection", "proof_seeking", "certainty_seeking",
        "staying", "risk", "control", "timing",
    ],
    "grief_underneath": [
        "grief_aware", "after_loss", "grief_tinged", "betrayal_fear",
        "grief_honoring", "fear", "permission", "containment", "loss_aversion",
    ],
    "something_surfacing": [
        "emergence", "fog", "unwilled", "body", "body_knowing",
        "curiosity", "naming_fear", "pacing",
    ],
    "clarity_arriving": [
        "recognition", "decision", "unavoidable", "knowing", "naming",
        "receiving", "questioning", "witnessing",
    ],
    "here_again": [
        "pattern", "pattern_recognition", "pattern_awareness",
        "identity", "automatic", "guilt",
    ],
    "something_different": [
        "pattern_breaking", "transition", "opening", "small_step",
        "different", "questioning",
    ],
    "pressing_forward": [
        "timing", "pressure", "pressure_aware", "urgency", "control",
        "perfectionism", "honesty", "decision", "naming",
    ],
    "weight_carried": [
        "weight", "depletion", "imbalance", "guilt", "identity",
        "worthiness", "good_enough", "not_doing", "asking", "rest",
        "saying_no", "priority",
    ],
    "ready_to_release": [
        "release", "transition", "softening", "unguarded",
        "witnessing", "expression", "permission", "pacing",
    ],
    "holding_back": [
        "containment", "minimizing", "rushing", "pacing", "avoidance",
        "dismissing", "loss_aversion", "believing", "bargaining",
        "pausing", "thanking", "automatic",
    ],
}


# ============================================================================
# V10.3: COMPETITIVE FRAME RANKING SYSTEM
# ============================================================================
# Instead of just selecting a compatible frame, rank all candidate frames
# to find the MOST TRUTHFUL one based on signal strength and context.
#
# Core shift: compatible frame selection >>> competitive frame ranking
# ============================================================================

# V10.5: QUALITY CALIBRATION CONSTANTS
# ============================================================================
# Tuned thresholds and scoring weights to produce meaningful confidence 
# distribution across high/medium/low signal scenarios.
#
# Key changes from V10.4:
# - Stronger primary signal weights (+4.0 for strong, +3.0 for moderate)
# - Adjusted confidence thresholds (HIGH > 1.5, MEDIUM > 0.5)
# - Reduced over-penalization from conflicting signals
# - Bonus for reinforcing signal pairs increased
# ============================================================================

V105_CONFIDENCE_THRESHOLDS = {
    "high": 1.5,     # Margin > 1.5 = HIGH confidence (was 2.0)
    "medium": 0.5,   # Margin > 0.5 = MEDIUM confidence (was 1.0)
    # Below 0.5 = LOW confidence
}

V105_SCORING_WEIGHTS = {
    "primary_strong": 4.0,      # Tone > 0.5 (was 3.0)
    "primary_moderate": 3.0,    # Tone > 0.25 (was 2.0)
    "secondary_strong": 2.0,    # (was 1.5)
    "secondary_moderate": 1.5,  # (was 1.0)
    "negative_strong": -1.5,    # (was -2.0) - reduced penalty
    "negative_moderate": -0.5,  # (was -1.0) - reduced penalty
    "lifeline_strong": 2.5,     # (was 2.0)
    "lifeline_moderate": 2.0,   # (was 1.5)
    "pattern_strong": 2.5,      # (was 2.0)
    "pattern_moderate": 1.5,    # (was 1.0)
    "pattern_weak": -0.5,       # (was -1.0) - reduced penalty
    "reinforcing_pair": 1.5,    # (was 1.0) - increased bonus
    "conflicting_pair": -0.25,  # (was -0.5) - reduced penalty
}

V105_TONE_THRESHOLDS = {
    "strong": 0.5,   # Tone value >= 0.5 is strong (was 0.4)
    "moderate": 0.25, # Tone value >= 0.25 is moderate (was 0.2)
}

# --- FRAME SIGNAL AFFINITIES ---
# Primary and secondary signal affinities for each frame, with weights

FRAME_SIGNAL_WEIGHTS = {
    "edge_of_action": {
        "primary": ["growth", "warmth"],        # Strong positive indicators
        "secondary": ["clarity"],               # Supporting indicators
        "negative": ["grief", "resistance"],    # Conflicting signals
    },
    "testing_the_waters": {
        "primary": ["hesitation", "warmth"],
        "secondary": ["confusion"],
        "negative": ["clarity", "pressure"],
    },
    "walls_questioning": {
        "primary": ["resistance", "hesitation"],
        "secondary": ["grief"],
        "negative": ["warmth", "growth"],
    },
    "grief_underneath": {
        "primary": ["grief"],
        "secondary": ["resistance", "confusion"],
        "negative": ["growth", "clarity"],
    },
    "something_surfacing": {
        "primary": ["confusion"],
        "secondary": ["warmth", "hesitation"],
        "negative": ["clarity", "pressure"],
    },
    "clarity_arriving": {
        "primary": ["clarity"],
        "secondary": ["growth", "warmth"],
        "negative": ["confusion"],
    },
    "here_again": {
        "primary": ["repeated_cycles"],
        "secondary": ["hesitation", "resistance"],
        "negative": [],
    },
    "something_different": {
        "primary": ["repeated_cycles", "growth"],
        "secondary": ["warmth", "clarity"],
        "negative": ["resistance"],
    },
    "pressing_forward": {
        "primary": ["pressure"],
        "secondary": ["clarity"],
        "negative": ["hesitation", "confusion"],
    },
    "weight_carried": {
        "primary": ["pressure", "grief"],
        "secondary": ["resistance"],
        "negative": ["warmth", "growth"],
    },
    "ready_to_release": {
        "primary": ["growth", "grief"],
        "secondary": ["warmth", "clarity"],
        "negative": ["resistance"],
    },
    "holding_back": {
        "primary": ["resistance"],
        "secondary": ["pressure", "confusion"],
        "negative": ["growth", "clarity"],
    },
}

# --- PATTERN ARCHETYPE AFFINITIES ---
# Some patterns naturally align with certain frames

PATTERN_FRAME_AFFINITIES = {
    "relational_reopening": {
        "strong": ["edge_of_action", "testing_the_waters", "walls_questioning"],
        "moderate": ["grief_underneath", "here_again"],
        "weak": ["pressing_forward", "weight_carried"],
    },
    "threshold_standing": {
        "strong": ["edge_of_action", "clarity_arriving", "here_again"],
        "moderate": ["testing_the_waters", "something_different"],
        "weak": ["something_surfacing"],
    },
    "over_functioning_hero": {
        "strong": ["weight_carried", "pressing_forward"],
        "moderate": ["holding_back", "here_again"],
        "weak": ["edge_of_action", "ready_to_release"],
    },
    "somethings_here": {
        "strong": ["something_surfacing", "clarity_arriving"],
        "moderate": ["testing_the_waters"],
        "weak": ["pressing_forward", "weight_carried"],
    },
    "moving_through": {
        "strong": ["ready_to_release", "grief_underneath"],
        "moderate": ["holding_back", "something_surfacing"],
        "weak": ["edge_of_action", "pressing_forward"],
    },
    "heart_thaw": {
        "strong": ["testing_the_waters", "ready_to_release", "walls_questioning"],
        "moderate": ["edge_of_action", "grief_underneath"],
        "weak": ["pressing_forward"],
    },
    "inner_critic_override": {
        "strong": ["holding_back", "something_surfacing"],
        "moderate": ["walls_questioning", "here_again"],
        "weak": ["edge_of_action", "ready_to_release"],
    },
    "duty_over_self": {
        "strong": ["weight_carried", "holding_back"],
        "moderate": ["here_again", "pressing_forward"],
        "weak": ["ready_to_release", "edge_of_action"],
    },
    "safe_intimacy_returning": {
        "strong": ["testing_the_waters", "edge_of_action"],
        "moderate": ["walls_questioning", "grief_underneath"],
        "weak": ["pressing_forward"],
    },
    "expansion_resistance": {
        "strong": ["holding_back", "walls_questioning"],
        "moderate": ["testing_the_waters", "here_again"],
        "weak": ["ready_to_release"],
    },
}

# --- SIGNAL CONSISTENCY PAIRS ---
# Signals that reinforce each other (consistency bonus)

REINFORCING_SIGNAL_PAIRS = [
    ("grief", "resistance"),       # Grief often creates protective resistance
    ("warmth", "growth"),          # Warmth supports growth
    ("clarity", "growth"),         # Clarity enables growth
    ("pressure", "confusion"),     # Pressure can create confusion
    ("hesitation", "confusion"),   # Hesitation often comes with confusion
    ("resistance", "hesitation"),  # Resistance manifests as hesitation
]

# Signals that conflict (consistency penalty)
CONFLICTING_SIGNAL_PAIRS = [
    ("warmth", "resistance"),      # Warmth and resistance are opposites
    ("clarity", "confusion"),      # Can't have both
    ("growth", "holding_back"),    # Growth vs holding back
    ("grief", "warmth"),           # Grief dampens warmth (though can coexist)
]


def score_frame(
    frame_type: str,
    tones: Dict[str, float],
    lifeline_patterns: List[str],
    pattern_id: str,
    transit_themes: Any = None,
    debug: bool = False
) -> Dict[str, Any]:
    """
    Calculate a competitive score for a frame based on signal strength and context.
    
    V10.5 CALIBRATED SCORING:
    - +4.0 per strong primary signal match (tone >= 0.5)
    - +3.0 per moderate primary signal match (tone >= 0.25)
    - +2.0 per strong secondary signal match (tone >= 0.5)
    - +1.5 per moderate secondary signal match (tone >= 0.25)
    - -1.5 per strong negative signal (tone >= 0.5) [reduced from -2.0]
    - -0.5 per moderate negative signal (tone >= 0.25) [reduced from -1.0]
    - +2.5 if lifeline pattern strongly supports frame
    - +2.5 if pattern archetype strongly aligns
    - +1.5 if pattern archetype moderately aligns
    - -0.5 if pattern archetype weakly aligns [reduced from -1.0]
    - +1.5 per reinforcing signal pair present [increased from 1.0]
    - -0.25 per conflicting signal pair present [reduced from -0.5]
    
    Returns dict with score breakdown for debugging.
    """
    # Use V10.5 calibrated weights
    W = V105_SCORING_WEIGHTS
    T = V105_TONE_THRESHOLDS
    
    weights = FRAME_SIGNAL_WEIGHTS.get(frame_type, {})
    primary_signals = weights.get("primary", [])
    secondary_signals = weights.get("secondary", [])
    negative_signals = weights.get("negative", [])
    
    score = 0.0
    breakdown = {
        "frame_type": frame_type,
        "primary_matches": [],
        "secondary_matches": [],
        "negative_matches": [],
        "lifeline_bonus": 0,
        "pattern_alignment": 0,
        "consistency_bonus": 0,
        "total_score": 0,
    }
    
    # --- Primary signal scoring (V10.5) ---
    for signal in primary_signals:
        tone_value = tones.get(signal, 0)
        # Special handling for repeated_cycles (comes from lifeline_patterns)
        if signal == "repeated_cycles" and "repeated_cycles" in lifeline_patterns:
            tone_value = 0.7  # Treat as strong signal (increased from 0.6)
        
        if tone_value >= T["strong"]:
            score += W["primary_strong"]
            breakdown["primary_matches"].append((signal, tone_value, W["primary_strong"]))
        elif tone_value >= T["moderate"]:
            score += W["primary_moderate"]
            breakdown["primary_matches"].append((signal, tone_value, W["primary_moderate"]))
    
    # --- Secondary signal scoring (V10.5) ---
    for signal in secondary_signals:
        tone_value = tones.get(signal, 0)
        if signal == "repeated_cycles" and "repeated_cycles" in lifeline_patterns:
            tone_value = 0.7
        
        if tone_value >= T["strong"]:
            score += W["secondary_strong"]
            breakdown["secondary_matches"].append((signal, tone_value, W["secondary_strong"]))
        elif tone_value >= T["moderate"]:
            score += W["secondary_moderate"]
            breakdown["secondary_matches"].append((signal, tone_value, W["secondary_moderate"]))
    
    # --- Negative signal scoring (V10.5 - reduced penalties) ---
    for signal in negative_signals:
        tone_value = tones.get(signal, 0)
        if tone_value >= T["strong"]:
            score += W["negative_strong"]  # Negative value
            breakdown["negative_matches"].append((signal, tone_value, W["negative_strong"]))
        elif tone_value >= T["moderate"]:
            score += W["negative_moderate"]  # Negative value
            breakdown["negative_matches"].append((signal, tone_value, W["negative_moderate"]))
    
    # --- Lifeline pattern support (V10.5 - increased bonuses) ---
    if "repeated_cycles" in lifeline_patterns:
        if frame_type in ["here_again", "something_different"]:
            score += W["lifeline_strong"]
            breakdown["lifeline_bonus"] = W["lifeline_strong"]
    
    # Check for other lifeline patterns that support frames
    if "delayed_action" in lifeline_patterns:
        if frame_type in ["holding_back", "testing_the_waters"]:
            score += W["lifeline_moderate"]
            breakdown["lifeline_bonus"] += W["lifeline_moderate"]
    
    if "breakthrough_moments" in lifeline_patterns:
        if frame_type in ["edge_of_action", "something_different", "clarity_arriving"]:
            score += W["lifeline_moderate"]
            breakdown["lifeline_bonus"] += W["lifeline_moderate"]
    
    # --- Pattern archetype alignment (V10.5) ---
    affinities = PATTERN_FRAME_AFFINITIES.get(pattern_id, {})
    if frame_type in affinities.get("strong", []):
        score += W["pattern_strong"]
        breakdown["pattern_alignment"] = W["pattern_strong"]
    elif frame_type in affinities.get("moderate", []):
        score += W["pattern_moderate"]
        breakdown["pattern_alignment"] = W["pattern_moderate"]
    elif frame_type in affinities.get("weak", []):
        score += W["pattern_weak"]  # Negative value
        breakdown["pattern_alignment"] = W["pattern_weak"]
    
    # --- Signal consistency scoring (V10.5) ---
    active_signals = [s for s, v in tones.items() if v >= T["moderate"]]
    if "repeated_cycles" in lifeline_patterns:
        active_signals.append("repeated_cycles")
    
    # Reinforcing pairs bonus (increased)
    for pair in REINFORCING_SIGNAL_PAIRS:
        if pair[0] in active_signals and pair[1] in active_signals:
            score += W["reinforcing_pair"]
            breakdown["consistency_bonus"] += W["reinforcing_pair"]
    
    # Conflicting pairs penalty (reduced)
    for pair in CONFLICTING_SIGNAL_PAIRS:
        if pair[0] in active_signals and pair[1] in active_signals:
            score += W["conflicting_pair"]  # Negative value
            breakdown["consistency_bonus"] += W["conflicting_pair"]
    
    breakdown["total_score"] = round(score, 2)
    
    return breakdown


def rank_candidate_frames(
    pattern_id: str,
    tones: Dict[str, float],
    lifeline_patterns: List[str],
    transit_themes: Any = None,
    debug: bool = False
) -> List[Dict[str, Any]]:
    """
    Rank all candidate frames by score to find the most truthful one.
    
    Returns list of frame scores, sorted by total_score descending.
    """
    all_frames = list(FRAME_TYPES.keys())
    scored_frames = []
    
    for frame_type in all_frames:
        score_breakdown = score_frame(
            frame_type,
            tones,
            lifeline_patterns,
            pattern_id,
            transit_themes,
            debug
        )
        scored_frames.append(score_breakdown)
    
    # Sort by total score descending
    scored_frames.sort(key=lambda x: x["total_score"], reverse=True)
    
    return scored_frames


def select_best_frame(
    pattern_id: str,
    tones: Dict[str, float],
    lifeline_patterns: List[str],
    selected_framing: str = "",
    transit_themes: Any = None,
    debug: bool = False
) -> Tuple[str, Dict[str, Any]]:
    """
    Select the BEST frame using competitive ranking.
    
    Returns (best_frame_type, debug_info).
    
    V10.5 CALIBRATED THRESHOLDS:
    Debug info includes:
    - all_candidates: ranked list of all frame scores
    - winner: the selected frame
    - margin: score difference from second place
    - confidence: "high" if margin > 1.5, "medium" if > 0.5, "low" otherwise
    """
    # Get ranked frames
    ranked_frames = rank_candidate_frames(
        pattern_id,
        tones,
        lifeline_patterns,
        transit_themes,
        debug
    )
    
    # Select winner
    winner = ranked_frames[0]
    runner_up = ranked_frames[1] if len(ranked_frames) > 1 else None
    
    # Calculate margin and confidence using V10.5 calibrated thresholds
    margin = winner["total_score"] - (runner_up["total_score"] if runner_up else 0)
    
    THRESHOLDS = V105_CONFIDENCE_THRESHOLDS
    if margin > THRESHOLDS["high"]:
        confidence = "high"
    elif margin > THRESHOLDS["medium"]:
        confidence = "medium"
    else:
        confidence = "low"
    
    # If confidence is low and we have a selected_framing, use it as tiebreaker
    if confidence == "low" and selected_framing:
        framing_frame = FRAMING_TO_FRAME_TYPE.get(selected_framing, "")
        if framing_frame:
            # Boost the frame that matches the selected framing
            for frame_data in ranked_frames:
                if frame_data["frame_type"] == framing_frame:
                    # If it's close to the winner, prefer the framing-matched frame
                    if winner["total_score"] - frame_data["total_score"] < 1.5:
                        winner = frame_data
                        confidence = "framing_tiebreak"
                    break
    
    debug_info = {
        "all_candidates": ranked_frames[:5] if debug else [],  # Top 5 only for brevity
        "winner": winner,
        "runner_up": runner_up,
        "margin": round(margin, 2),
        "confidence": confidence,
    }
    
    return (winner["frame_type"], debug_info)


# ============================================================================
# V10.4: CONFIDENCE-AWARE EXPRESSION SYSTEM
# ============================================================================
# Adapts language tone and certainty based on frame ranking confidence.
# HIGH = direct, MEDIUM = softened, LOW = dual-frame/ambiguous
#
# Core insight: Confidence shapes EXPRESSION, not just selection.
# ============================================================================

# V10.5: BANNED VAGUE PHRASES
# ============================================================================
# These phrases should be avoided or replaced with more concrete language.
# Used for validation and automatic replacement.
# ============================================================================

V105_BANNED_PHRASES = [
    "something is stirring",
    "something is present",
    "something is moving",
    "something wants to",
    "something in the air",
    "something is shifting",
    "the universe",
    "energy is",
    "vibration",
    "alignment",
    "being called",
]

V105_PHRASE_REPLACEMENTS = {
    "something is stirring": "you may be sensing",
    "something is present": "there's a feeling present",
    "something is moving": "a shift is underway",
    "something wants to": "part of you wants to",
}

# --- HEDGING LANGUAGE BY CONFIDENCE ---

CONFIDENCE_HEDGES = {
    "high": {
        # Direct, clear statements - minimal hedging
        "prefixes": ["", "", ""],  # Often no prefix needed
        "connectors": ["is", "are", "feels"],
        "modals": [""],  # No modal needed
    },
    "medium": {
        # Light softening
        "prefixes": ["Something in you ", "Part of you ", "There's a sense that "],
        "connectors": ["may be", "seems to be", "might be"],
        "modals": ["may ", "might ", "could "],
    },
    "low": {
        # Acknowledge duality - these are used differently
        "prefixes": ["Part of you ", "Something in you ", "There's a pull "],
        "connectors": ["may be", "seems to be", "could be"],
        "modals": ["may ", "might ", ""],
    },
}

# --- DUAL-FRAME TEMPLATES ---
# Used when confidence is LOW to express both winning and runner-up frames
# V10.5: Removed vague phrases like "Something is stirring"

DUAL_FRAME_TEMPLATES = {
    # Core insight templates - combine two tendencies
    "core_insight": [
        "Part of you {frame1_verb}, while another part {frame2_verb}.",
        "There's a pull toward {frame1_noun}, even as {frame2_clause}.",
        "You may be {frame1_gerund}—and at the same time, {frame2_gerund}.",
        "{frame1_sentence} And yet, {frame2_sentence_lower}",
    ],
    # Why now templates - V10.5: replaced vague "Something is stirring"
    "why_now": [
        "This may be surfacing because {frame1_reason}—though {frame2_reason} is also present.",
        "You may be sensing both {frame1_short} and {frame2_short}.",
        "The timing seems to be highlighting both {frame1_noun} and {frame2_noun}.",
    ],
    # Friction templates
    "friction": [
        "You may be pulled between {frame1_friction} and {frame2_friction}.",
        "Part of the difficulty is {frame1_friction}, while also {frame2_friction}.",
        "The friction may be coming from {frame1_source}—but also from {frame2_source}.",
    ],
    # Practical templates - V10.5: made more actionable
    "practical": [
        "Try noticing both: {frame1_action}, and {frame2_action}.",
        "Pause to hold both: {frame1_practice} while also {frame2_practice}.",
        "Give space to {frame1_need}—without abandoning {frame2_need}.",
    ],
}

# --- FRAME EXPRESSION COMPONENTS ---
# Language components for each frame used in dual-frame expressions

FRAME_EXPRESSION_COMPONENTS = {
    "edge_of_action": {
        "verb": "is ready to move forward",
        "noun": "action",
        "gerund": "stepping toward something new",
        "sentence": "Something in you is ready to take a step.",
        "reason": "readiness is building",
        "short": "momentum toward action",
        "friction": "wanting to act before you're certain",
        "source": "the pull to move",
        "action": "where you feel ready",
        "practice": "letting yourself step forward",
        "need": "the readiness",
    },
    "testing_the_waters": {
        "verb": "wants to check if this is safe",
        "noun": "caution",
        "gerund": "checking if it's okay to proceed",
        "sentence": "Part of you is checking if this is safe.",
        "reason": "you're checking the ground before stepping",
        "short": "careful exploration",
        "friction": "needing more certainty first",
        "source": "wanting to be sure",
        "action": "where you're hesitating",
        "practice": "noticing what you're cautious about",
        "need": "the hesitation",
    },
    "walls_questioning": {
        "verb": "is reconsidering its defenses",
        "noun": "self-protection",
        "gerund": "questioning whether the walls are still needed",
        "sentence": "The walls you built may be asking if they're still necessary.",
        "reason": "old protections are being reconsidered",
        "short": "walls becoming uncertain",
        "friction": "keeping your guard up out of habit",
        "source": "the need to stay protected",
        "action": "where you're guarding",
        "practice": "noticing what you're protecting",
        "need": "the protection",
    },
    "grief_underneath": {
        "verb": "is holding something lost",
        "noun": "grief",
        "gerund": "carrying what's been lost",
        "sentence": "There's grief underneath this—something missing.",
        "reason": "loss is still present",
        "short": "unprocessed grief",
        "friction": "not wanting to feel the loss fully",
        "source": "what's been lost",
        "action": "what you're mourning",
        "practice": "honoring what was",
        "need": "the grief",
    },
    "something_surfacing": {
        "verb": "is sensing something emerging",
        "noun": "emergence",
        "gerund": "sensing what's not yet named",
        "sentence": "A feeling is surfacing that doesn't have a name yet.",
        "reason": "an unnamed feeling is becoming visible",
        "short": "an emerging awareness",
        "friction": "not being able to name it clearly",
        "source": "the unknown",
        "action": "what's trying to surface",
        "practice": "staying with the unnamed",
        "need": "the emergence",
    },
    "clarity_arriving": {
        "verb": "is starting to see clearly",
        "noun": "clarity",
        "gerund": "recognizing what's been true",
        "sentence": "A clarity is arriving that wasn't there before.",
        "reason": "understanding is arriving",
        "short": "growing clarity",
        "friction": "knowing but not acting yet",
        "source": "what you now see",
        "action": "what's becoming clear",
        "practice": "trusting what you now know",
        "need": "the clarity",
    },
    "here_again": {
        "verb": "recognizes this territory",
        "noun": "the familiar pattern",
        "gerund": "recognizing you've been here before",
        "sentence": "You've been here before—this feels familiar.",
        "reason": "a known pattern is returning",
        "short": "pattern recognition",
        "friction": "doing what you've always done",
        "source": "repeating what hasn't worked",
        "action": "what's familiar",
        "practice": "noticing what you usually do",
        "need": "the awareness of repetition",
    },
    "something_different": {
        "verb": "senses this time could be different",
        "noun": "possibility of change",
        "gerund": "feeling that something could shift",
        "sentence": "This time might be different.",
        "reason": "something new is possible",
        "short": "hope for change",
        "friction": "not trusting that change is real",
        "source": "doubt about whether it will last",
        "action": "what could change",
        "practice": "trying something new",
        "need": "the possibility",
    },
    "pressing_forward": {
        "verb": "feels the urgency to move",
        "noun": "pressure",
        "gerund": "feeling pushed to act now",
        "sentence": "There's pressure to move—time feels limited.",
        "reason": "urgency is building",
        "short": "pressing momentum",
        "friction": "rushing before you're ready",
        "source": "the urgency",
        "action": "what feels urgent",
        "practice": "distinguishing real urgency from anxiety",
        "need": "the pressure",
    },
    "weight_carried": {
        "verb": "is carrying too much",
        "noun": "the weight",
        "gerund": "bearing more than your share",
        "sentence": "You may be carrying more than you realize.",
        "reason": "the load has become heavy",
        "short": "accumulated weight",
        "friction": "not putting it down",
        "source": "what you're holding",
        "action": "what you're carrying",
        "practice": "noticing the weight",
        "need": "the burden",
    },
    "ready_to_release": {
        "verb": "is ready to let something go",
        "noun": "release",
        "gerund": "feeling ready to let go",
        "sentence": "Something you've been holding may be ready to move.",
        "reason": "release is becoming possible",
        "short": "readiness to release",
        "friction": "holding on past when it's needed",
        "source": "fear of letting go",
        "action": "what's ready to move",
        "practice": "allowing release",
        "need": "the letting go",
    },
    "holding_back": {
        "verb": "is containing what wants to move",
        "noun": "containment",
        "gerund": "holding back what wants to come out",
        "sentence": "You may be holding back what wants to move.",
        "reason": "containment is becoming harder",
        "short": "held-back expression",
        "friction": "not letting it out",
        "source": "what's being suppressed",
        "action": "what you're containing",
        "practice": "noticing what's held back",
        "need": "the containment",
    },
}


def apply_confidence_expression(
    text: str,
    confidence: str,
    section: str = "general"
) -> str:
    """
    Adjust text expression based on confidence level.
    
    HIGH: Keep as-is (direct)
    MEDIUM: Add light softening if not already present
    LOW: Text should already be dual-frame, just ensure softening
    """
    if confidence == "high":
        # Direct expression - no changes needed
        return text
    
    if confidence in ["medium", "low", "framing_tiebreak"]:
        # Check if text already has softening language
        soft_indicators = [
            "may ", "might ", "could ", "seems ", "perhaps",
            "part of you", "something in you", "there's a sense",
            "you may be", "it's possible"
        ]
        
        text_lower = text.lower()
        has_softening = any(indicator in text_lower for indicator in soft_indicators)
        
        if has_softening:
            return text
        
        # Add light softening for medium confidence
        # Only modify if the sentence starts with a definitive statement
        if text[0].isupper() and not text.startswith(("Part", "Something", "There", "You may", "It seems")):
            # Convert to softer phrasing
            if text.startswith("You "):
                text = "You may " + text[4].lower() + text[5:]
            elif text.startswith("The "):
                text = "It seems like the " + text[4].lower() + text[5:]
            elif text.startswith("A "):
                text = "There may be a " + text[2].lower() + text[3:]
        
        return text
    
    return text


def generate_dual_frame_insight(
    pattern_id: str,
    winner_frame: str,
    runner_up_frame: str,
    section: str,
    user_id: str = ""
) -> str:
    """
    Generate a dual-frame expression for LOW confidence situations.
    
    Combines the winning and runner-up frames to express ambiguity.
    """
    winner_components = FRAME_EXPRESSION_COMPONENTS.get(winner_frame, {})
    runner_up_components = FRAME_EXPRESSION_COMPONENTS.get(runner_up_frame, {})
    
    if not winner_components or not runner_up_components:
        return ""  # Can't generate dual-frame without components
    
    templates = DUAL_FRAME_TEMPLATES.get(section, DUAL_FRAME_TEMPLATES.get("core_insight", []))
    
    if not templates:
        return ""
    
    # Select template deterministically
    idx = get_deterministic_variation_index(pattern_id, user_id, f"dual_{section}") % len(templates)
    template = templates[idx]
    
    # Fill in template with frame components
    try:
        if section == "core_insight":
            result = template.format(
                frame1_verb=winner_components.get("verb", ""),
                frame2_verb=runner_up_components.get("verb", ""),
                frame1_noun=winner_components.get("noun", ""),
                frame2_clause=runner_up_components.get("sentence", "").lower(),
                frame1_gerund=winner_components.get("gerund", ""),
                frame2_gerund=runner_up_components.get("gerund", ""),
                frame1_sentence=winner_components.get("sentence", ""),
                frame2_sentence_lower=runner_up_components.get("sentence", "").lower() if runner_up_components.get("sentence") else "",
            )
        elif section == "why_now":
            result = template.format(
                frame1_reason=winner_components.get("reason", ""),
                frame2_reason=runner_up_components.get("reason", ""),
                frame1_short=winner_components.get("short", ""),
                frame2_short=runner_up_components.get("short", ""),
                frame1_noun=winner_components.get("noun", ""),
                frame2_noun=runner_up_components.get("noun", ""),
            )
        elif section == "friction":
            result = template.format(
                frame1_friction=winner_components.get("friction", ""),
                frame2_friction=runner_up_components.get("friction", ""),
                frame1_source=winner_components.get("source", ""),
                frame2_source=runner_up_components.get("source", ""),
            )
        elif section == "practical":
            result = template.format(
                frame1_action=winner_components.get("action", ""),
                frame2_action=runner_up_components.get("action", ""),
                frame1_practice=winner_components.get("practice", ""),
                frame2_practice=runner_up_components.get("practice", ""),
                frame1_need=winner_components.get("need", ""),
                frame2_need=runner_up_components.get("need", ""),
            )
        else:
            result = ""
        
        return result
    except KeyError:
        return ""


def should_use_dual_frame(confidence: str, margin: float) -> bool:
    """
    Determine if we should use dual-frame expression.
    
    Use dual-frame when:
    - Confidence is LOW
    - Margin is very small (< 0.5)
    - Both frames are genuinely relevant
    """
    if confidence == "low" and margin < 1.0:
        return True
    return False


def determine_frame_type(
    pattern_id: str,
    active_signals: List[str],
    selected_framing: str
) -> str:
    """
    Determine the frame_type for this card based on the selected core insight framing.
    
    This frame_type will be passed to all subsequent section generators
    to ensure cross-section coherence.
    """
    # First, try to map from the selected framing
    if selected_framing in FRAMING_TO_FRAME_TYPE:
        return FRAMING_TO_FRAME_TYPE[selected_framing]
    
    # Fallback: determine frame_type from dominant signals
    if "repeated_cycles" in active_signals:
        if "growth" in active_signals:
            return "something_different"
        return "here_again"
    
    if "grief" in active_signals:
        if "growth" in active_signals:
            return "ready_to_release"
        return "grief_underneath"
    
    if "resistance" in active_signals:
        if "pressure" in active_signals:
            return "holding_back"
        return "walls_questioning"
    
    if "clarity" in active_signals:
        if "pressure" in active_signals:
            return "pressing_forward"
        return "clarity_arriving"
    
    if "warmth" in active_signals or "growth" in active_signals:
        return "edge_of_action"
    
    if "confusion" in active_signals or "hesitation" in active_signals:
        return "testing_the_waters"
    
    # Default
    return "something_surfacing"


def select_structure_with_frame(
    structures_config: Dict[str, Any],
    pattern_id: str,
    active_signals: List[str],
    frame_type: str,
    user_id: str = "",
    section: str = ""
) -> Tuple[str, str]:
    """
    Select the best sentence structure that is COMPATIBLE with the given frame_type.
    
    Returns (selected_text, selected_framing).
    Prioritizes structures whose framing is compatible with the frame_type.
    """
    config = structures_config.get(pattern_id, {})
    structures = config.get("structures", [])
    default_text = config.get("default", "")
    
    if not structures:
        return (default_text, "default")
    
    # Get compatible framings for this frame_type
    compatible_framings = FRAME_COMPATIBLE_FRAMINGS.get(frame_type, [])
    
    # Score each structure by affinity match AND frame compatibility
    scored_structures = []
    for struct in structures:
        affinities = struct.get("affinities", [])
        framing = struct.get("framing", "")
        
        # Base score from signal affinity match
        affinity_score = sum(1 for sig in active_signals if sig in affinities)
        
        # Bonus for repeated_cycles match
        if "repeated_cycles" in active_signals and "repeated_cycles" in affinities:
            affinity_score += 0.5
        
        # Frame compatibility bonus (prioritize structures that match our frame)
        frame_bonus = 2.0 if framing in compatible_framings else 0.0
        
        total_score = affinity_score + frame_bonus
        scored_structures.append((struct, total_score, affinity_score))
    
    # Sort by total score (highest first)
    scored_structures.sort(key=lambda x: x[1], reverse=True)
    
    # If top scorer has meaningful score, use it
    if scored_structures[0][1] > 0:
        top_score = scored_structures[0][1]
        tied_structures = [s for s, score, _ in scored_structures if score == top_score]
        
        if len(tied_structures) > 1:
            idx = get_deterministic_variation_index(pattern_id, user_id, section) % len(tied_structures)
            selected = tied_structures[idx]
        else:
            selected = tied_structures[0]
        
        return (selected["text"], selected.get("framing", "default"))
    
    # No good match - use deterministic selection with frame preference
    # First try frame-compatible structures
    frame_compatible = [s for s in structures if s.get("framing", "") in compatible_framings]
    if frame_compatible:
        idx = get_deterministic_variation_index(pattern_id, user_id, section) % len(frame_compatible)
        selected = frame_compatible[idx]
        return (selected["text"], selected.get("framing", "default"))
    
    # Fallback to any structure
    idx = get_deterministic_variation_index(pattern_id, user_id, section) % len(structures)
    selected = structures[idx]
    return (selected["text"], selected.get("framing", "default"))


# --- STRUCTURAL SENTENCE PATTERNS ---
# Multiple base structures per pattern, tagged with signal affinities
# Format: { pattern_id: { "structures": [ { "text": ..., "affinities": [...], "framing": ... } ] } }

WHY_NOW_STRUCTURES = {
    "relational_reopening": {
        "structures": [
            {
                "framing": "opening",
                "affinities": ["warmth", "growth"],
                "text": "Something in you may be becoming more willing to let connection back in.",
            },
            {
                "framing": "protection",
                "affinities": ["hesitation", "resistance"],
                "text": "The walls you've built may be asking whether they're still needed.",
            },
            {
                "framing": "grief_aware",
                "affinities": ["grief"],
                "text": "Even while holding what's been lost, something in you is reaching toward connection.",
            },
            {
                "framing": "timing",
                "affinities": ["clarity", "pressure"],
                "text": "The question of closeness is pressing now—not because you've answered it, but because it won't wait.",
            },
            {
                "framing": "pattern_recognition",
                "affinities": ["repeated_cycles"],
                "text": "You've been here before—at the edge of letting someone in. This time something feels different.",
            },
        ],
        "default": "Current timing may be making openness feel more possible.",
    },
    "threshold_standing": {
        "structures": [
            {
                "framing": "decision",
                "affinities": ["clarity", "pressure"],
                "text": "A decision is becoming unavoidable—not because you're ready, but because the moment is.",
            },
            {
                "framing": "between",
                "affinities": ["confusion", "hesitation"],
                "text": "You're standing between what was and what could be, and neither feels fully real yet.",
            },
            {
                "framing": "readiness",
                "affinities": ["warmth", "growth"],
                "text": "Something in you knows it's time to move—even if the path isn't fully visible.",
            },
            {
                "framing": "resistance_aware",
                "affinities": ["resistance", "grief"],
                "text": "Part of you is holding back, and that hesitation might be worth listening to.",
            },
            {
                "framing": "pattern_recognition",
                "affinities": ["repeated_cycles"],
                "text": "This threshold feels familiar. You've stood here before, but you're not the same person now.",
            },
        ],
        "default": "Current timing may be highlighting a threshold.",
    },
    "over_functioning_hero": {
        "structures": [
            {
                "framing": "weight",
                "affinities": ["pressure", "grief"],
                "text": "The weight of carrying so much is becoming harder to ignore.",
            },
            {
                "framing": "questioning",
                "affinities": ["clarity", "growth"],
                "text": "You're starting to wonder whether all this holding is actually yours to do.",
            },
            {
                "framing": "depletion",
                "affinities": ["confusion", "resistance"],
                "text": "Something is running low—not just energy, but the willingness to keep going this way.",
            },
            {
                "framing": "identity",
                "affinities": ["warmth", "hesitation"],
                "text": "Being the one who holds things together has felt like who you are. Now you're not so sure.",
            },
            {
                "framing": "pattern_recognition",
                "affinities": ["repeated_cycles"],
                "text": "You've done this before—carried more than your share. And here you are again.",
            },
        ],
        "default": "Current pressures may be revealing where you're overextended.",
    },
    "somethings_here": {
        "structures": [
            {
                "framing": "emergence",
                "affinities": ["warmth", "growth"],
                "text": "Something is present that wasn't there before—still forming, not yet named.",
            },
            {
                "framing": "uncertainty",
                "affinities": ["confusion", "hesitation"],
                "text": "There's something here you can't quite see clearly yet, but you feel it.",
            },
            {
                "framing": "recognition",
                "affinities": ["clarity"],
                "text": "You're noticing something that's been there awhile—it just became visible.",
            },
            {
                "framing": "grief_tinged",
                "affinities": ["grief", "resistance"],
                "text": "Something is surfacing that you may have been avoiding. It's here now.",
            },
            {
                "framing": "pressure_aware",
                "affinities": ["pressure"],
                "text": "Under the noise and demands, something quieter is trying to get your attention.",
            },
        ],
        "default": "Current timing may be bringing something into focus.",
    },
    "moving_through": {
        "structures": [
            {
                "framing": "release",
                "affinities": ["growth", "warmth"],
                "text": "Something you've been holding is ready to move through you.",
            },
            {
                "framing": "containment",
                "affinities": ["grief", "resistance"],
                "text": "You might be holding more than you've let yourself feel.",
            },
            {
                "framing": "transition",
                "affinities": ["confusion", "hesitation"],
                "text": "Something is shifting, even if you can't fully name it yet.",
            },
            {
                "framing": "pattern_recognition",
                "affinities": ["repeated_cycles"],
                "text": "This feels like a moment where something wants to move, but hasn't before.",
            },
            {
                "framing": "pressure_aware",
                "affinities": ["pressure", "clarity"],
                "text": "What's been building can't stay contained much longer. Something needs to move.",
            },
        ],
        "default": "Timing may be supporting release or completion.",
    },
    "heart_thaw": {
        "structures": [
            {
                "framing": "softening",
                "affinities": ["warmth", "growth"],
                "text": "Walls that have been up are starting to soften—not all at once, but noticeably.",
            },
            {
                "framing": "testing",
                "affinities": ["hesitation", "resistance"],
                "text": "You're checking if it's safe to feel again, one careful moment at a time.",
            },
            {
                "framing": "grief_aware",
                "affinities": ["grief"],
                "text": "The heart that closed to protect itself is wondering if it's time to open.",
            },
            {
                "framing": "pressure",
                "affinities": ["pressure", "clarity"],
                "text": "Warmth is pressing against the walls—not forcing, but persistent.",
            },
            {
                "framing": "confusion",
                "affinities": ["confusion"],
                "text": "You're not sure if you're ready, but a thaw is happening anyway.",
            },
        ],
        "default": "Conditions may be supporting a quiet softening.",
    },
    "inner_critic_override": {
        "structures": [
            {
                "framing": "volume",
                "affinities": ["pressure", "confusion"],
                "text": "The critical voice is louder than usual—drowning out other signals.",
            },
            {
                "framing": "questioning",
                "affinities": ["clarity", "growth"],
                "text": "You're starting to notice the inner critic as a voice, not a truth.",
            },
            {
                "framing": "protection",
                "affinities": ["resistance", "hesitation"],
                "text": "The harsh self-talk might be trying to protect you from something scarier.",
            },
            {
                "framing": "grief_aware",
                "affinities": ["grief", "warmth"],
                "text": "The critic speaks loudest when something tender is trying to emerge.",
            },
            {
                "framing": "pattern_recognition",
                "affinities": ["repeated_cycles"],
                "text": "You've heard this voice before. It says the same things every time you get close to something real.",
            },
        ],
        "default": "Timing may be amplifying self-judgment.",
    },
    "duty_over_self": {
        "structures": [
            {
                "framing": "imbalance",
                "affinities": ["pressure", "clarity"],
                "text": "The gap between what you're giving and what you're receiving is becoming visible.",
            },
            {
                "framing": "questioning",
                "affinities": ["growth", "warmth"],
                "text": "You're starting to wonder where you fit on your own priority list.",
            },
            {
                "framing": "depletion",
                "affinities": ["grief", "resistance"],
                "text": "Giving has become so automatic that you've forgotten what it's like to receive.",
            },
            {
                "framing": "confusion",
                "affinities": ["confusion", "hesitation"],
                "text": "You're not sure anymore where responsibility ends and self-abandonment begins.",
            },
            {
                "framing": "pattern_recognition",
                "affinities": ["repeated_cycles"],
                "text": "This isn't the first time you've put yourself last. But it might be the first time you've noticed.",
            },
        ],
        "default": "Current pressures may be highlighting where you put yourself last.",
    },
}

FRICTION_STRUCTURES = {
    "relational_reopening": {
        "structures": [
            {
                "framing": "proof_seeking",
                "affinities": ["hesitation", "resistance"],
                "text": "Part of you may still want proof that openness is safe before committing to it.",
            },
            {
                "framing": "self_protection",
                "affinities": ["grief", "resistance"],
                "text": "The part of you that got hurt before is watching carefully, ready to retreat.",
            },
            {
                "framing": "control",
                "affinities": ["pressure", "clarity"],
                "text": "You may be trying to control the terms of reconnection rather than letting it unfold.",
            },
            {
                "framing": "worthiness",
                "affinities": ["warmth", "confusion"],
                "text": "A quiet voice may be asking whether you deserve the connection you're being offered.",
            },
            {
                "framing": "timing",
                "affinities": ["growth"],
                "text": "You might be second-guessing the timing, even when the readiness is real.",
            },
        ],
        "default": "Part of you may still want proof that openness is safe.",
    },
    "threshold_standing": {
        "structures": [
            {
                "framing": "certainty_seeking",
                "affinities": ["hesitation", "confusion"],
                "text": "You may be waiting for a certainty that won't come until after you've moved.",
            },
            {
                "framing": "loss_aversion",
                "affinities": ["grief", "resistance"],
                "text": "What you'd leave behind may feel more real than what you'd step into.",
            },
            {
                "framing": "perfectionism",
                "affinities": ["pressure", "clarity"],
                "text": "You might be looking for the perfect moment to step forward—and it doesn't exist.",
            },
            {
                "framing": "identity",
                "affinities": ["growth", "warmth"],
                "text": "Part of you may be wondering who you'll be on the other side of this decision.",
            },
            {
                "framing": "pattern_awareness",
                "affinities": ["repeated_cycles"],
                "text": "You may be afraid of choosing wrong again, like you feel you have before.",
            },
        ],
        "default": "You may still be waiting for certainty before stepping forward.",
    },
    "over_functioning_hero": {
        "structures": [
            {
                "framing": "identity",
                "affinities": ["warmth", "confusion"],
                "text": "Not doing might feel like not being—like you'll disappear without the role.",
            },
            {
                "framing": "guilt",
                "affinities": ["grief", "hesitation"],
                "text": "Resting may feel like abandoning the people who count on you.",
            },
            {
                "framing": "control",
                "affinities": ["pressure", "resistance"],
                "text": "Letting go of control may feel more dangerous than burning out.",
            },
            {
                "framing": "worthiness",
                "affinities": ["growth", "clarity"],
                "text": "Part of you may believe you only deserve rest after everything is handled.",
            },
            {
                "framing": "pattern_awareness",
                "affinities": ["repeated_cycles"],
                "text": "You know this pattern, but knowing it hasn't been enough to stop it.",
            },
        ],
        "default": "You might find it hard to rest when there's still something you could do.",
    },
    "somethings_here": {
        "structures": [
            {
                "framing": "avoidance",
                "affinities": ["resistance", "grief"],
                "text": "You might be keeping this feeling at arm's length, afraid of what it means.",
            },
            {
                "framing": "naming_fear",
                "affinities": ["hesitation", "confusion"],
                "text": "Naming it might make it real in a way you're not ready for.",
            },
            {
                "framing": "rushing",
                "affinities": ["pressure", "clarity"],
                "text": "You may want to understand it before it's ready to be understood.",
            },
            {
                "framing": "dismissing",
                "affinities": ["warmth", "growth"],
                "text": "Part of you may be tempted to dismiss this as nothing important.",
            },
            {
                "framing": "pattern_awareness",
                "affinities": ["repeated_cycles"],
                "text": "You've felt this before and ignored it. Part of you wants to do that again.",
            },
        ],
        "default": "You might be resisting naming it too soon.",
    },
    "moving_through": {
        "structures": [
            {
                "framing": "minimizing",
                "affinities": ["resistance", "pressure"],
                "text": "Part of you may be minimizing what you're actually grieving.",
            },
            {
                "framing": "rushing",
                "affinities": ["growth", "clarity"],
                "text": "You might be trying to rush through the feeling instead of letting it move at its own pace.",
            },
            {
                "framing": "containment",
                "affinities": ["hesitation", "confusion"],
                "text": "You may be holding back tears, words, or truth that want to come out.",
            },
            {
                "framing": "fear",
                "affinities": ["grief", "warmth"],
                "text": "You might be afraid that feeling it fully will overwhelm you.",
            },
            {
                "framing": "pattern_awareness",
                "affinities": ["repeated_cycles"],
                "text": "You've held this before. The question is whether you're ready to let it go this time.",
            },
        ],
        "default": "Part of you may be minimizing what you're actually grieving.",
    },
    "heart_thaw": {
        "structures": [
            {
                "framing": "testing",
                "affinities": ["hesitation", "resistance"],
                "text": "Part of you may still be checking if softening is worth the risk.",
            },
            {
                "framing": "betrayal_fear",
                "affinities": ["grief"],
                "text": "Opening again might feel like betraying the pain that closed you in the first place.",
            },
            {
                "framing": "control",
                "affinities": ["pressure", "clarity"],
                "text": "You might be trying to control the pace of thawing rather than letting it happen.",
            },
            {
                "framing": "worthiness",
                "affinities": ["warmth", "confusion"],
                "text": "A part of you may wonder if you deserve the warmth that's becoming available.",
            },
            {
                "framing": "identity",
                "affinities": ["growth"],
                "text": "Being guarded has become who you are. Softening feels like losing yourself.",
            },
        ],
        "default": "Part of you may still be uncertain if softening is worth the risk.",
    },
    "inner_critic_override": {
        "structures": [
            {
                "framing": "believing",
                "affinities": ["pressure", "confusion"],
                "text": "The voice is loud enough that part of you believes it's telling the truth.",
            },
            {
                "framing": "protection",
                "affinities": ["resistance", "grief"],
                "text": "Silencing the critic might feel dangerous—like removing a guard you've relied on.",
            },
            {
                "framing": "identity",
                "affinities": ["hesitation"],
                "text": "Part of you may have come to see the harsh voice as the only honest one inside you.",
            },
            {
                "framing": "bargaining",
                "affinities": ["warmth", "growth"],
                "text": "You might be negotiating with the critic instead of questioning its authority.",
            },
            {
                "framing": "pattern_awareness",
                "affinities": ["repeated_cycles", "clarity"],
                "text": "You know this voice. You've fought it before. And here it is again.",
            },
        ],
        "default": "You may be dismissing your own knowing before it has room to land.",
    },
    "duty_over_self": {
        "structures": [
            {
                "framing": "guilt",
                "affinities": ["warmth", "hesitation"],
                "text": "Putting yourself on the list may feel selfish, even when you know it isn't.",
            },
            {
                "framing": "identity",
                "affinities": ["grief", "resistance"],
                "text": "Taking care of others has become who you are. Stopping might feel like disappearing.",
            },
            {
                "framing": "urgency",
                "affinities": ["pressure"],
                "text": "There's always something more urgent than your own needs, and there always will be.",
            },
            {
                "framing": "worthiness",
                "affinities": ["confusion", "growth"],
                "text": "Part of you may feel you haven't earned the right to rest yet.",
            },
            {
                "framing": "pattern_awareness",
                "affinities": ["repeated_cycles", "clarity"],
                "text": "You've told yourself 'just this once' so many times it's become a pattern.",
            },
        ],
        "default": "You might be putting your own needs at the end of the list again.",
    },
}

PRACTICAL_STRUCTURES = {
    "relational_reopening": {
        "structures": [
            {
                "framing": "small_moment",
                "affinities": ["hesitation", "warmth"],
                "text": "Try letting one moment of connection land without analyzing it.",
            },
            {
                "framing": "staying",
                "affinities": ["resistance", "grief"],
                "text": "When you feel the urge to pull back, pause and stay one beat longer.",
            },
            {
                "framing": "receiving",
                "affinities": ["growth", "clarity"],
                "text": "Let yourself receive one thing today—a compliment, help, or kindness—without deflecting.",
            },
            {
                "framing": "honesty",
                "affinities": ["pressure", "confusion"],
                "text": "Tell someone one true thing about how you're feeling, even if it's small.",
            },
            {
                "framing": "pattern_breaking",
                "affinities": ["repeated_cycles"],
                "text": "Do one thing differently than you did last time. This time might be different.",
            },
        ],
        "default": "Let yourself receive one moment of connection without immediately evaluating it.",
    },
    "threshold_standing": {
        "structures": [
            {
                "framing": "body_knowing",
                "affinities": ["warmth", "hesitation"],
                "text": "Ask your body what it already knows about this choice, before your mind weighs in.",
            },
            {
                "framing": "small_step",
                "affinities": ["resistance", "confusion"],
                "text": "Take one step in the direction that scares you—small enough to be reversible.",
            },
            {
                "framing": "naming",
                "affinities": ["clarity", "pressure"],
                "text": "Write down what you're actually afraid of losing by moving forward.",
            },
            {
                "framing": "grief_honoring",
                "affinities": ["grief", "growth"],
                "text": "Say goodbye to what you're leaving behind, even as you go.",
            },
            {
                "framing": "pattern_breaking",
                "affinities": ["repeated_cycles"],
                "text": "Ask yourself: what would I do differently this time? Then try it.",
            },
        ],
        "default": "Take one small action in the direction your body is already leaning.",
    },
    "over_functioning_hero": {
        "structures": [
            {
                "framing": "good_enough",
                "affinities": ["pressure", "growth"],
                "text": "Let one thing be good enough today. Don't fix it further.",
            },
            {
                "framing": "not_doing",
                "affinities": ["hesitation", "confusion"],
                "text": "Drop one thing you usually would do. See what happens when you don't catch it.",
            },
            {
                "framing": "asking",
                "affinities": ["warmth", "resistance"],
                "text": "Ask for help with one thing today, even if you could do it yourself.",
            },
            {
                "framing": "rest",
                "affinities": ["grief", "clarity"],
                "text": "Rest before you're exhausted. Just once. See how it feels.",
            },
            {
                "framing": "pattern_breaking",
                "affinities": ["repeated_cycles"],
                "text": "Let something fall that you'd usually catch. Watch what actually happens.",
            },
        ],
        "default": "Let one thing be good enough today. Don't fix it further.",
    },
    "somethings_here": {
        "structures": [
            {
                "framing": "naming",
                "affinities": ["hesitation", "clarity"],
                "text": "Write down one feeling you notice right now, even if it's incomplete.",
            },
            {
                "framing": "staying",
                "affinities": ["resistance", "grief"],
                "text": "Sit with the feeling for one minute. Don't try to change or understand it yet.",
            },
            {
                "framing": "curiosity",
                "affinities": ["warmth", "growth"],
                "text": "Ask the feeling what it wants you to know. Listen without judging.",
            },
            {
                "framing": "body",
                "affinities": ["confusion", "pressure"],
                "text": "Put your hand where in your body this feeling lives. Just locate it.",
            },
            {
                "framing": "pattern_awareness",
                "affinities": ["repeated_cycles"],
                "text": "Ask yourself: when have I felt this before? What was true then?",
            },
        ],
        "default": "Write down one feeling you notice right now, even if it's incomplete.",
    },
    "moving_through": {
        "structures": [
            {
                "framing": "permission",
                "affinities": ["grief", "warmth"],
                "text": "Say out loud: I give myself permission to feel what's actually here.",
            },
            {
                "framing": "expression",
                "affinities": ["resistance", "pressure"],
                "text": "Let it out somehow—tears, words, movement. Don't hold it in one more day.",
            },
            {
                "framing": "pacing",
                "affinities": ["hesitation", "confusion"],
                "text": "Let the feeling move at its own pace. You don't have to rush the release.",
            },
            {
                "framing": "witnessing",
                "affinities": ["clarity", "growth"],
                "text": "Tell one person what you're going through. Let them witness it.",
            },
            {
                "framing": "pattern_breaking",
                "affinities": ["repeated_cycles"],
                "text": "This time, feel it all the way through. Don't stop at comfortable.",
            },
        ],
        "default": "Say out loud: I give myself permission to feel what's actually here.",
    },
    "heart_thaw": {
        "structures": [
            {
                "framing": "unguarded",
                "affinities": ["warmth", "growth"],
                "text": "Say one unguarded thought today without rushing to protect it.",
            },
            {
                "framing": "risk",
                "affinities": ["hesitation", "resistance"],
                "text": "Let yourself be seen in one small way you usually hide.",
            },
            {
                "framing": "receiving",
                "affinities": ["grief", "clarity"],
                "text": "Accept warmth from someone today without explaining why you don't deserve it.",
            },
            {
                "framing": "softening",
                "affinities": ["pressure", "confusion"],
                "text": "When you catch yourself hardening, pause and take one slow breath.",
            },
            {
                "framing": "pattern_breaking",
                "affinities": ["repeated_cycles"],
                "text": "Do one soft thing you stopped doing when you built the walls.",
            },
        ],
        "default": "Allow yourself one unguarded thought today without rushing to protect it.",
    },
    "inner_critic_override": {
        "structures": [
            {
                "framing": "friend_voice",
                "affinities": ["warmth", "clarity"],
                "text": "Notice what you'd say to a friend in your situation—and say it to yourself.",
            },
            {
                "framing": "questioning",
                "affinities": ["growth", "pressure"],
                "text": "Ask the critical voice: whose voice is this really? When did I first hear it?",
            },
            {
                "framing": "pausing",
                "affinities": ["hesitation", "confusion"],
                "text": "When the critic speaks, pause before believing it. Just pause.",
            },
            {
                "framing": "thanking",
                "affinities": ["grief", "resistance"],
                "text": "Thank the critic for trying to protect you, then do what you were going to do anyway.",
            },
            {
                "framing": "pattern_breaking",
                "affinities": ["repeated_cycles"],
                "text": "This time, don't argue with the voice. Just don't obey it.",
            },
        ],
        "default": "Notice what you'd say to a friend in your situation—and say it to yourself.",
    },
    "duty_over_self": {
        "structures": [
            {
                "framing": "list",
                "affinities": ["clarity", "growth"],
                "text": "Put one of your own needs on the list today, even if it's small.",
            },
            {
                "framing": "saying_no",
                "affinities": ["hesitation", "resistance"],
                "text": "Say no to one thing today that you would usually say yes to.",
            },
            {
                "framing": "receiving",
                "affinities": ["warmth", "grief"],
                "text": "Let someone do something for you without reciprocating immediately.",
            },
            {
                "framing": "priority",
                "affinities": ["pressure", "confusion"],
                "text": "Before saying yes, ask: what am I saying no to by doing this?",
            },
            {
                "framing": "pattern_breaking",
                "affinities": ["repeated_cycles"],
                "text": "Do one thing for yourself first today. Just once. See if the world ends.",
            },
        ],
        "default": "Put one of your own needs on the list today, even if it's small.",
    },
}

CORE_INSIGHT_STRUCTURES = {
    "relational_reopening": {
        "structures": [
            {
                "framing": "pull",
                "affinities": ["warmth", "growth"],
                "text": "Something in you is reaching toward connection—not because it's safe, but because it's real.",
            },
            {
                "framing": "testing",
                "affinities": ["hesitation", "resistance"],
                "text": "You're standing at the edge of letting someone in, testing whether you can.",
            },
            {
                "framing": "after_loss",
                "affinities": ["grief"],
                "text": "After closing for good reasons, something in you is asking whether it's time to open again.",
            },
            {
                "framing": "choice",
                "affinities": ["clarity", "pressure"],
                "text": "The question isn't whether to connect, but whether you'll let yourself.",
            },
            {
                "framing": "pattern",
                "affinities": ["repeated_cycles", "confusion"],
                "text": "You've been here before—at the threshold of closeness. Something is different now.",
            },
        ],
        "default": "Something in you may be becoming more willing to let connection back in.",
    },
    "threshold_standing": {
        "structures": [
            {
                "framing": "unavoidable",
                "affinities": ["clarity", "pressure"],
                "text": "A decision is becoming unavoidable—not because you're ready, but because the moment is.",
            },
            {
                "framing": "between",
                "affinities": ["confusion", "hesitation"],
                "text": "You're standing between what was and what might be, belonging fully to neither.",
            },
            {
                "framing": "knowing",
                "affinities": ["warmth", "growth"],
                "text": "Part of you already knows which way to go. The rest of you is catching up.",
            },
            {
                "framing": "grief_aware",
                "affinities": ["grief", "resistance"],
                "text": "Moving forward means leaving something behind. You're grieving before you've even gone.",
            },
            {
                "framing": "pattern",
                "affinities": ["repeated_cycles"],
                "text": "You've stood at this kind of threshold before. This time you know more.",
            },
        ],
        "default": "You may be standing at a decision point—not because the answer is clear, but because the question has become unavoidable.",
    },
    "over_functioning_hero": {
        "structures": [
            {
                "framing": "weight",
                "affinities": ["pressure", "grief"],
                "text": "You've been carrying more than your share—and the weight is starting to show.",
            },
            {
                "framing": "questioning",
                "affinities": ["clarity", "growth"],
                "text": "You're starting to wonder if all this holding is actually helping.",
            },
            {
                "framing": "identity",
                "affinities": ["warmth", "confusion"],
                "text": "Being the one who holds things together has felt like who you are. Now you're not so sure.",
            },
            {
                "framing": "depletion",
                "affinities": ["resistance", "hesitation"],
                "text": "The tank is running low, and filling it keeps getting postponed.",
            },
            {
                "framing": "pattern",
                "affinities": ["repeated_cycles"],
                "text": "You've done this before—carried until you couldn't. Here you are again.",
            },
        ],
        "default": "You may be carrying more than your share—doing the work others could do.",
    },
    "somethings_here": {
        "structures": [
            {
                "framing": "emergence",
                "affinities": ["warmth", "growth"],
                "text": "A feeling is present that wasn't before—still forming, not yet named, but real.",
            },
            {
                "framing": "fog",
                "affinities": ["confusion", "hesitation"],
                "text": "There's a feeling here you can't quite see clearly yet, but you sense it.",
            },
            {
                "framing": "recognition",
                "affinities": ["clarity"],
                "text": "You're noticing a feeling that's been there awhile. It just became impossible to ignore.",
            },
            {
                "framing": "avoided",
                "affinities": ["grief", "resistance"],
                "text": "A feeling you've been avoiding is making itself known.",
            },
            {
                "framing": "underneath",
                "affinities": ["pressure"],
                "text": "Under everything else, a quieter feeling is asking for your attention.",
            },
        ],
        "default": "A feeling is present that wasn't before—an awareness, a shift.",
    },
    "moving_through": {
        "structures": [
            {
                "framing": "release",
                "affinities": ["growth", "clarity"],
                "text": "Something you've been holding is ready to move through you—not to be solved, but to be felt.",
            },
            {
                "framing": "containment",
                "affinities": ["grief", "resistance"],
                "text": "You might be holding more than you've let yourself feel.",
            },
            {
                "framing": "transition",
                "affinities": ["confusion", "hesitation"],
                "text": "Something is shifting. You can feel it moving even if you can't name it.",
            },
            {
                "framing": "pressure",
                "affinities": ["pressure", "warmth"],
                "text": "What's been building can't stay contained much longer.",
            },
            {
                "framing": "pattern",
                "affinities": ["repeated_cycles"],
                "text": "This feeling has come before, and you've held it back. This time it wants to move.",
            },
        ],
        "default": "Something you've been holding is ready to move through you.",
    },
    "heart_thaw": {
        "structures": [
            {
                "framing": "softening",
                "affinities": ["warmth", "growth"],
                "text": "The walls you built to protect yourself are starting to soften.",
            },
            {
                "framing": "testing",
                "affinities": ["hesitation", "resistance"],
                "text": "You're checking if it's safe to feel again, one careful moment at a time.",
            },
            {
                "framing": "grief_aware",
                "affinities": ["grief"],
                "text": "The heart that closed to survive is wondering if it's time to open.",
            },
            {
                "framing": "unwilled",
                "affinities": ["confusion", "clarity"],
                "text": "A thaw is happening, even if you didn't plan it.",
            },
            {
                "framing": "pressure",
                "affinities": ["pressure"],
                "text": "Warmth is pressing against the walls—not forcing, but persistent.",
            },
        ],
        "default": "Walls that have been up are starting to soften.",
    },
    "inner_critic_override": {
        "structures": [
            {
                "framing": "volume",
                "affinities": ["pressure", "confusion"],
                "text": "The critical voice inside is louder than usual, drowning out other signals.",
            },
            {
                "framing": "questioning",
                "affinities": ["clarity", "growth"],
                "text": "You're starting to notice the inner critic as a voice, not a truth.",
            },
            {
                "framing": "protection",
                "affinities": ["resistance", "hesitation"],
                "text": "The harsh self-talk might be trying to protect you from something scarier.",
            },
            {
                "framing": "tender",
                "affinities": ["warmth", "grief"],
                "text": "The critic speaks loudest when something tender is trying to emerge.",
            },
            {
                "framing": "pattern",
                "affinities": ["repeated_cycles"],
                "text": "This voice has visited before. It says the same things every time you get close.",
            },
        ],
        "default": "Self-critical voices are louder right now, asking to be worked with.",
    },
    "duty_over_self": {
        "structures": [
            {
                "framing": "visibility",
                "affinities": ["clarity", "pressure"],
                "text": "The gap between what you give and what you receive is becoming impossible to ignore.",
            },
            {
                "framing": "questioning",
                "affinities": ["growth", "warmth"],
                "text": "You're starting to wonder where you fit on your own priority list.",
            },
            {
                "framing": "automatic",
                "affinities": ["confusion", "hesitation"],
                "text": "Giving has become so automatic that you've forgotten what it's like to receive.",
            },
            {
                "framing": "depletion",
                "affinities": ["grief", "resistance"],
                "text": "You've been running on empty, and the tank isn't refilling.",
            },
            {
                "framing": "pattern",
                "affinities": ["repeated_cycles"],
                "text": "This isn't the first time you've put yourself last. But it might be the first time you've noticed.",
            },
        ],
        "default": "The gap between what you're giving and what you're receiving is becoming visible.",
    },
}


def get_dominant_signal_combination(tones: Dict[str, float], lifeline_patterns: List[str]) -> Tuple[str, List[str]]:
    """
    Determine the dominant signal combination from detected tones and lifeline patterns.
    
    Returns: (combination_name, list_of_active_signals)
    """
    # Get tones above threshold
    active_tones = [tone for tone, score in tones.items() if score >= 0.3]
    
    # Add lifeline patterns as pseudo-tones
    if "repeated_cycles" in lifeline_patterns:
        active_tones.append("repeated_cycles")
    
    if not active_tones:
        return ("baseline", [])
    
    # Check for specific named combinations
    for combo_name, combo_tones in SIGNAL_COMBINATIONS.items():
        if all(t in active_tones for t in combo_tones):
            return (combo_name, active_tones)
    
    # No named combination - return the strongest signals
    sorted_tones = sorted(
        [(t, tones.get(t, 0.5 if t == "repeated_cycles" else 0)) for t in active_tones],
        key=lambda x: x[1],
        reverse=True
    )
    
    top_signals = [t[0] for t in sorted_tones[:2]]
    combo_name = "_".join(top_signals) if len(top_signals) > 1 else top_signals[0]
    
    return (combo_name, active_tones)


def select_structure(
    structures_config: Dict[str, Any],
    pattern_id: str,
    active_signals: List[str],
    user_id: str = "",
    section: str = ""
) -> str:
    """
    Select the best sentence structure based on signal affinities.
    
    Returns the selected structure text, or default if no match.
    """
    config = structures_config.get(pattern_id, {})
    structures = config.get("structures", [])
    default_text = config.get("default", "")
    
    if not structures:
        return default_text
    
    # Score each structure by affinity match
    scored_structures = []
    for struct in structures:
        affinities = struct.get("affinities", [])
        # Count how many of the user's active signals match this structure's affinities
        match_count = sum(1 for sig in active_signals if sig in affinities)
        # Bonus for repeated_cycles match (pattern recognition framings are valuable)
        if "repeated_cycles" in active_signals and "repeated_cycles" in affinities:
            match_count += 0.5
        scored_structures.append((struct, match_count))
    
    # Sort by match count (highest first)
    scored_structures.sort(key=lambda x: x[1], reverse=True)
    
    # If top scorer has matches, use it
    if scored_structures[0][1] > 0:
        # If there are ties, use deterministic selection among tied structures
        top_score = scored_structures[0][1]
        tied_structures = [s for s, score in scored_structures if score == top_score]
        
        if len(tied_structures) > 1:
            # Deterministic selection among ties
            idx = get_deterministic_variation_index(pattern_id, user_id, section) % len(tied_structures)
            return tied_structures[idx]["text"]
        else:
            return tied_structures[0]["text"]
    
    # No affinity matches - use deterministic selection for variation
    idx = get_deterministic_variation_index(pattern_id, user_id, section) % len(structures)
    return structures[idx]["text"]


def extract_signal_tones(signals_extended: Dict[str, Any]) -> Dict[str, float]:
    """
    Analyze signals to detect emotional/behavioral tones.
    
    V10.5 CALIBRATION:
    - Increased sensitivity: 2 matches = 0.5 (strong threshold)
    - Better normalization to produce meaningful differentiation
    - Each match contributes 0.25 (capped at 1.0)
    
    Returns dict of tone -> strength (0-1) based on keyword matches.
    """
    tones = {tone: 0.0 for tone in SIGNAL_TONE_MARKERS}
    
    # Gather all signal text
    all_text = []
    
    # Journal (most weighted - recent personal reflection)
    memory = signals_extended.get("memory", signals_extended)
    for entry in memory.get("journal_entries", []):
        content = entry.get("content", "")
        all_text.append(content.lower())
    
    # Chat (medium weighted)
    for msg in memory.get("chat_messages", []):
        content = msg.get("content", "")
        all_text.append(content.lower())
    
    # Lifeline (lower weighted for immediate tone)
    for event in memory.get("lifeline_events", []):
        title = event.get("title", "") or ""
        desc = event.get("description", "") or ""
        all_text.append(f"{title} {desc}".lower())
    
    combined_text = " ".join(all_text)
    
    if not combined_text:
        return tones
    
    # V10.5: More sensitive matching - count unique marker matches
    # Each unique marker match contributes 0.25 to the tone score
    for tone, markers in SIGNAL_TONE_MARKERS.items():
        matches = sum(1 for marker in markers if marker in combined_text)
        # V10.5: 2 matches = 0.5 (strong), 4 matches = 1.0 (max)
        tones[tone] = min(1.0, matches * 0.25)
    
    return tones


def extract_lifeline_patterns(signals_extended: Dict[str, Any]) -> List[str]:
    """
    Detect patterns in lifeline events that can inform language.
    
    Returns list of detected pattern types.
    """
    detected = []
    
    memory = signals_extended.get("memory", signals_extended)
    lifeline_events = memory.get("lifeline_events", [])
    
    # Combine lifeline text
    lifeline_text = " ".join([
        f"{e.get('title', '')} {e.get('description', '')}" 
        for e in lifeline_events
    ]).lower()
    
    if not lifeline_text:
        return detected
    
    # Check for patterns
    for pattern_name, markers in LIFELINE_PATTERNS.items():
        if any(marker in lifeline_text for marker in markers):
            detected.append(pattern_name)
    
    return detected


def get_deterministic_variation_index(pattern_id: str, user_id: str = "", section: str = "") -> int:
    """
    Generate a stable variation index based on pattern, user, and date.
    
    This ensures:
    - Same user + pattern + day = same variation (consistency)
    - Different days = different variations (freshness)
    - Different users = different variations (personalization)
    """
    today = datetime.now().strftime("%Y-%m-%d")
    seed = f"{pattern_id}:{user_id}:{today}:{section}"
    hash_val = int(hashlib.md5(seed.encode()).hexdigest(), 16)
    return hash_val


def select_variation(options: List[str], pattern_id: str, user_id: str = "", section: str = "") -> str:
    """
    Select a variation from options using deterministic randomness.
    """
    if not options:
        return ""
    idx = get_deterministic_variation_index(pattern_id, user_id, section) % len(options)
    return options[idx]


def apply_contextual_modifier(
    base_text: str, 
    tones: Dict[str, float], 
    pattern_id: str,
    user_id: str = "",
    threshold: float = 0.3
) -> str:
    """
    Append a contextual modifier to base text based on detected tones.
    
    Only applies modifier if a tone is above threshold.
    Prioritizes strongest detected tone.
    """
    # Find strongest tone above threshold
    strongest_tone = None
    strongest_score = 0
    
    for tone, score in tones.items():
        if score >= threshold and score > strongest_score:
            strongest_tone = tone
            strongest_score = score
    
    if not strongest_tone or strongest_tone not in CONTEXTUAL_MODIFIERS:
        return base_text
    
    # Select a modifier deterministically
    modifiers = CONTEXTUAL_MODIFIERS[strongest_tone]
    modifier = select_variation(modifiers, pattern_id, user_id, f"modifier_{strongest_tone}")
    
    # Ensure base text doesn't already end with similar phrasing
    base_lower = base_text.lower()
    if any(m[:20].lower() in base_lower for m in modifiers):
        return base_text
    
    # Clean up base text ending
    base_text = base_text.rstrip(".")
    
    return f"{base_text}{modifier}."


def vary_sentence_opener(base_text: str, opener_type: str, pattern_id: str, user_id: str = "") -> str:
    """
    Replace standard sentence openers with varied alternatives.
    
    V10: SIMPLIFIED - This function now only applies variation when it's safe.
    The primary personalization comes from contextual modifiers, not opener variations.
    Disabled aggressive opener replacement to maintain grammatical correctness.
    """
    # V10: Disable sentence opener variations for now
    # The contextual modifiers provide sufficient personalization
    # without risking grammatical errors
    return base_text


def generate_why_now(
    pattern_id: str,
    pattern: Dict[str, Any],
    signals_extended: Dict[str, Any],
    cluster_data: Dict[str, Any],
    transit_themes: Any,
    base_maps: Dict[str, Dict[str, str]],
    user_id: str = "",
    frame_type: str = "",
    confidence: str = "medium",
    runner_up_frame: str = "",
    margin: float = 1.0
) -> str:
    """
    V10.4: Generate context-aware "why now" explanation with CONFIDENCE-AWARE EXPRESSION.
    
    1. Extract signal tones and lifeline patterns
    2. Select structure COMPATIBLE with the frame_type (if provided)
    3. Apply confidence-aware expression (dual-frame for LOW)
    """
    # Extract signal tones and lifeline patterns
    tones = extract_signal_tones(signals_extended)
    lifeline_patterns = extract_lifeline_patterns(signals_extended)
    
    # Get dominant signal combination
    combo_name, active_signals = get_dominant_signal_combination(tones, lifeline_patterns)
    
    # V10.4: Check for dual-frame expression on LOW confidence
    if should_use_dual_frame(confidence, margin) and runner_up_frame:
        dual_text = generate_dual_frame_insight(
            pattern_id,
            frame_type,
            runner_up_frame,
            "why_now",
            user_id
        )
        if dual_text:
            return dual_text
    
    # V10.2: Select structure with frame compatibility
    if pattern_id in WHY_NOW_STRUCTURES and active_signals:
        if frame_type:
            # Use frame-aware selection
            base_text, _ = select_structure_with_frame(
                WHY_NOW_STRUCTURES,
                pattern_id,
                active_signals,
                frame_type,
                user_id,
                "why_now"
            )
        else:
            # Fallback to original selection
            base_text = select_structure(
                WHY_NOW_STRUCTURES,
                pattern_id,
                active_signals,
                user_id,
                "why_now"
            )
    else:
        # Fallback to old map-based selection
        source_diversity = cluster_data.get("source_diversity_score", 0)
        evidence_count = cluster_data.get("total_evidence_count", 0)
        
        if evidence_count >= 3 and source_diversity >= 0.5:
            level = "high"
        elif evidence_count >= 2:
            level = "medium"
        else:
            level = "low"
        
        pattern_map = base_maps.get(pattern_id, {})
        if pattern_map:
            base_text = pattern_map.get(level, pattern_map.get("low", ""))
        else:
            base_text = "Current timing may be bringing this pattern into focus."
        
        if not base_text:
            base_text = "Current timing may be bringing this pattern into focus."
    
    # V10.4: Apply confidence-aware expression
    base_text = apply_confidence_expression(base_text, confidence, "why_now")
    
    # V10.1: Apply contextual modifier as SECONDARY layer (only if strong signal)
    enhanced_text = apply_contextual_modifier(base_text, tones, pattern_id, user_id, threshold=0.5)
    
    return enhanced_text


def generate_friction(
    pattern_id: str,
    pattern: Dict[str, Any],
    signals_extended: Dict[str, Any],
    cluster_data: Dict[str, Any],
    base_map: Dict[str, str],
    user_id: str = "",
    frame_type: str = "",
    confidence: str = "medium",
    runner_up_frame: str = "",
    margin: float = 1.0
) -> str:
    """
    V10.4: Generate context-aware friction statement with CONFIDENCE-AWARE EXPRESSION.
    
    1. Extract signal tones and lifeline patterns
    2. Select structure COMPATIBLE with the frame_type (if provided)
    3. Apply confidence-aware expression (dual-frame for LOW)
    """
    # Extract signal tones and lifeline patterns
    tones = extract_signal_tones(signals_extended)
    lifeline_patterns = extract_lifeline_patterns(signals_extended)
    
    # Get dominant signal combination
    combo_name, active_signals = get_dominant_signal_combination(tones, lifeline_patterns)
    
    # V10.4: Check for dual-frame expression on LOW confidence
    if should_use_dual_frame(confidence, margin) and runner_up_frame:
        dual_text = generate_dual_frame_insight(
            pattern_id,
            frame_type,
            runner_up_frame,
            "friction",
            user_id
        )
        if dual_text:
            return dual_text
    
    # V10.2: Select structure with frame compatibility
    if pattern_id in FRICTION_STRUCTURES and active_signals:
        if frame_type:
            # Use frame-aware selection
            base_text, _ = select_structure_with_frame(
                FRICTION_STRUCTURES,
                pattern_id,
                active_signals,
                frame_type,
                user_id,
                "friction"
            )
        else:
            # Fallback to original selection
            base_text = select_structure(
                FRICTION_STRUCTURES,
                pattern_id,
                active_signals,
                user_id,
                "friction"
            )
    elif pattern_id in FRICTION_STRUCTURES:
        # No active signals - use default from structures
        base_text = FRICTION_STRUCTURES[pattern_id].get("default", "")
    else:
        # Fallback to old map-based selection
        base_text = base_map.get(pattern_id, "")
        
        if not base_text:
            challenge = pattern.get("challenge", [])
            if challenge:
                base_text = f"You may notice a pull toward {challenge[0].lower()}."
            else:
                base_text = "You may be waiting for the right moment instead of trusting this one."
    
    # V10.4: Apply confidence-aware expression
    base_text = apply_confidence_expression(base_text, confidence, "friction")
    
    # V10.1: Modifiers only applied as secondary enhancement for very strong signals
    if tones.get("warmth", 0) > 0.6 or tones.get("growth", 0) > 0.6:
        softeners = [
            "Even with the progress you're making, ",
            "Alongside the opening, ",
        ]
        softener = select_variation(softeners, pattern_id, user_id, "friction_softener")
        if not base_text.startswith("Even") and not base_text.startswith("Alongside"):
            base_text = softener + base_text[0].lower() + base_text[1:]
    
    return base_text


def generate_practical(
    pattern_id: str,
    pattern: Dict[str, Any],
    signals_extended: Dict[str, Any],
    cluster_data: Dict[str, Any],
    base_map: Dict[str, str],
    user_id: str = "",
    frame_type: str = "",
    confidence: str = "medium",
    runner_up_frame: str = "",
    margin: float = 1.0
) -> str:
    """
    V10.4: Generate context-aware practical suggestion with CONFIDENCE-AWARE EXPRESSION.
    
    1. Extract signal tones and lifeline patterns
    2. Select structure COMPATIBLE with the frame_type (if provided)
    3. Apply confidence-aware expression (dual-frame for LOW)
    """
    # Extract signal tones and lifeline patterns
    tones = extract_signal_tones(signals_extended)
    lifeline_patterns = extract_lifeline_patterns(signals_extended)
    
    # Get dominant signal combination
    combo_name, active_signals = get_dominant_signal_combination(tones, lifeline_patterns)
    
    # V10.4: Check for dual-frame expression on LOW confidence
    if should_use_dual_frame(confidence, margin) and runner_up_frame:
        dual_text = generate_dual_frame_insight(
            pattern_id,
            frame_type,
            runner_up_frame,
            "practical",
            user_id
        )
        if dual_text:
            return dual_text
    
    # V10.2: Select structure with frame compatibility
    if pattern_id in PRACTICAL_STRUCTURES and active_signals:
        if frame_type:
            # Use frame-aware selection
            base_text, _ = select_structure_with_frame(
                PRACTICAL_STRUCTURES,
                pattern_id,
                active_signals,
                frame_type,
                user_id,
                "practical"
            )
        else:
            # Fallback to original selection
            base_text = select_structure(
                PRACTICAL_STRUCTURES,
                pattern_id,
                active_signals,
                user_id,
                "practical"
            )
    elif pattern_id in PRACTICAL_STRUCTURES:
        # No active signals - use default from structures
        base_text = PRACTICAL_STRUCTURES[pattern_id].get("default", "")
    else:
        # Fallback to old map-based selection
        base_text = base_map.get(pattern_id, "")
        
        if not base_text:
            micro_shifts = pattern.get("micro_shifts", [])
            if micro_shifts:
                base_text = micro_shifts[0]
            else:
                base_text = "Notice what already feels true and give it a moment of your attention."
    
    # V10.4: Apply confidence-aware expression
    base_text = apply_confidence_expression(base_text, confidence, "practical")
    
    # V10.1: For repeated_cycles, add pattern-breaking encouragement if not already in structure
    if "repeated_cycles" in lifeline_patterns:
        if "pattern_breaking" not in base_text.lower() and "this time" not in base_text.lower():
            enders = [
                " This time might be different.",
                " You've been here before—but you're not the same.",
            ]
            ender = select_variation(enders, pattern_id, user_id, "practical_cycle_ender")
            base_text = base_text.rstrip(".") + "." + ender
    
    # V10.1: For very strong hesitation, add gentler framing if not already present
    if tones.get("hesitation", 0) > 0.5:
        gentlers = ["Start small: ", "Just for today, "]
        if not any(base_text.startswith(g) for g in gentlers):
            gentler = select_variation(gentlers, pattern_id, user_id, "practical_gentler")
            base_text = gentler + base_text[0].lower() + base_text[1:]
    
    return base_text


def generate_core_insight(
    pattern_id: str,
    pattern: Dict[str, Any],
    signals_extended: Dict[str, Any],
    user_id: str = "",
    debug: bool = False
) -> Tuple[str, str, Dict[str, Any]]:
    """
    V10.4: Generate context-aware core insight with CONFIDENCE-AWARE EXPRESSION.
    
    Returns (insight_text, frame_type, debug_info) so that:
    - frame_type can be passed to subsequent section generators
    - debug_info shows frame selection reasoning (for dev)
    - Expression adapts to confidence level:
      - HIGH: direct statements
      - MEDIUM: light softening
      - LOW: dual-frame expression combining top 2 frames
    """
    # Extract signal tones and lifeline patterns
    tones = extract_signal_tones(signals_extended)
    lifeline_patterns = extract_lifeline_patterns(signals_extended)
    
    # Get dominant signal combination
    combo_name, active_signals = get_dominant_signal_combination(tones, lifeline_patterns)
    
    # V10.3: Use competitive frame ranking to select the BEST frame
    best_frame, frame_debug = select_best_frame(
        pattern_id,
        tones,
        lifeline_patterns,
        "",  # No pre-selected framing - let the ranking decide
        None,  # transit_themes
        debug
    )
    
    confidence = frame_debug.get("confidence", "medium")
    margin = frame_debug.get("margin", 1.0)
    runner_up = frame_debug.get("runner_up", {})
    runner_up_frame = runner_up.get("frame_type", "") if runner_up else ""
    
    # V10.4: Check if we should use dual-frame expression for LOW confidence
    if should_use_dual_frame(confidence, margin) and runner_up_frame:
        dual_text = generate_dual_frame_insight(
            pattern_id,
            best_frame,
            runner_up_frame,
            "core_insight",
            user_id
        )
        if dual_text:
            # Successfully generated dual-frame expression
            frame_debug["expression_mode"] = "dual_frame"
            return (dual_text, best_frame, frame_debug)
    
    # V10.3: Select structure compatible with the competitively-selected frame
    if pattern_id in CORE_INSIGHT_STRUCTURES and active_signals:
        text, framing = select_structure_with_frame(
            CORE_INSIGHT_STRUCTURES,
            pattern_id,
            active_signals,
            best_frame,  # Use the competitively-ranked frame
            user_id,
            "core_insight"
        )
        # V10.4: Apply confidence-aware expression
        text = apply_confidence_expression(text, confidence, "core_insight")
        frame_debug["expression_mode"] = f"single_frame_{confidence}"
        return (text, best_frame, frame_debug)
    elif pattern_id in CORE_INSIGHT_STRUCTURES:
        # No active signals - use default
        default_text = CORE_INSIGHT_STRUCTURES[pattern_id].get(
            "default",
            pattern.get("summary", "A feeling is present that deserves your attention.")
        )
        frame_debug["expression_mode"] = "default"
        return (default_text, "something_surfacing", frame_debug)
    else:
        # Pattern not in structures - use pattern summary
        frame_debug["expression_mode"] = "fallback"
        return (
            pattern.get("summary", "A feeling is present that deserves your attention."),
            "something_surfacing",
            frame_debug
        )


def cluster_signal_themes(signals: Dict[str, Any]) -> Dict[str, Any]:
    """
    Cluster signals across sources to find dominant themes.
    
    Returns:
    {
        "theme_counts": {"relational": 5, "emotional": 3, ...},
        "dominant_theme": "relational",
        "source_distribution": {"journal": 3, "chat": 2, "lifeline": 1},
        "total_evidence_count": 6,
        "source_diversity_score": 0.8,  # 0-1, higher = more diverse
        "repetition_score": 0.6,  # 0-1, higher = more repeated themes
        "matched_themes_by_source": {...}
    }
    """
    theme_counts = {cat: 0 for cat in THEME_CATEGORIES}
    source_distribution = {"journal": 0, "chat": 0, "lifeline": 0}
    matched_themes_by_source = {"journal": [], "chat": [], "lifeline": []}
    
    # Process journal entries
    for entry in signals.get("journal_entries", []):
        content = entry.get("content", "").lower()
        entry_themes = []
        for category, keywords in THEME_CATEGORIES.items():
            matches = [kw for kw in keywords if kw in content]
            if matches:
                theme_counts[category] += len(matches)
                entry_themes.extend(matches)
        if entry_themes:
            source_distribution["journal"] += 1
            matched_themes_by_source["journal"].append({
                "text": entry.get("content", "")[:80],
                "themes": entry_themes[:3]
            })
    
    # Process chat messages
    for msg in signals.get("chat_messages", []):
        content = msg.get("content", "").lower()
        msg_themes = []
        for category, keywords in THEME_CATEGORIES.items():
            matches = [kw for kw in keywords if kw in content]
            if matches:
                theme_counts[category] += len(matches)
                msg_themes.extend(matches)
        if msg_themes:
            source_distribution["chat"] += 1
            matched_themes_by_source["chat"].append({
                "text": msg.get("content", "")[:60],
                "themes": msg_themes[:3]
            })
    
    # Process lifeline events
    for event in signals.get("lifeline_events", []):
        title = (event.get("title") or "").lower()
        desc = (event.get("description") or "").lower()
        combined = f"{title} {desc}"
        event_themes = []
        for category, keywords in THEME_CATEGORIES.items():
            matches = [kw for kw in keywords if kw in combined]
            if matches:
                theme_counts[category] += len(matches)
                event_themes.extend(matches)
        if event_themes:
            source_distribution["lifeline"] += 1
            matched_themes_by_source["lifeline"].append({
                "text": event.get("title", ""),
                "themes": event_themes[:3]
            })
    
    # Calculate metrics
    total_evidence = sum(source_distribution.values())
    active_sources = sum(1 for v in source_distribution.values() if v > 0)
    
    # Source diversity: 0-1, higher = more diverse
    source_diversity_score = active_sources / 3.0 if total_evidence > 0 else 0
    
    # Repetition score: based on how concentrated themes are
    total_theme_hits = sum(theme_counts.values())
    if total_theme_hits > 0:
        max_theme_count = max(theme_counts.values())
        repetition_score = max_theme_count / total_theme_hits
    else:
        repetition_score = 0
    
    # Find dominant theme
    dominant_theme = max(theme_counts, key=theme_counts.get) if total_theme_hits > 0 else None
    
    return {
        "theme_counts": theme_counts,
        "dominant_theme": dominant_theme,
        "source_distribution": source_distribution,
        "total_evidence_count": total_evidence,
        "source_diversity_score": round(source_diversity_score, 2),
        "repetition_score": round(repetition_score, 2),
        "matched_themes_by_source": matched_themes_by_source,
    }


def score_pattern_with_clustering(
    pattern_id: str,
    signals: Dict[str, Any],
    cluster_data: Dict[str, Any]
) -> Dict[str, float]:
    """
    Score a pattern using multi-signal clustering.
    
    Factors:
    - Base signal alignment (keyword matching)
    - Theme category alignment (does pattern match dominant theme?)
    - Evidence count weight (more evidence = higher score)
    - Source diversity weight (multi-source support = higher score)
    - Repetition weight (repeated themes = higher score)
    """
    # Base signal score (existing logic)
    base_score = score_pattern_signal_alignment(pattern_id, signals)
    
    # Theme category alignment
    pattern_category = PATTERN_TO_THEME_CATEGORY.get(pattern_id)
    dominant_theme = cluster_data.get("dominant_theme")
    
    theme_alignment = 0.0
    if pattern_category and dominant_theme and pattern_category == dominant_theme:
        theme_alignment = 0.3  # Boost for matching dominant theme
    
    # Evidence count weight (logarithmic to prevent runaway scores)
    evidence_count = cluster_data.get("total_evidence_count", 0)
    evidence_weight = min(0.2, evidence_count * 0.05)  # Max 0.2 bonus
    
    # Source diversity weight
    diversity_score = cluster_data.get("source_diversity_score", 0)
    diversity_weight = diversity_score * 0.15  # Max 0.15 bonus
    
    # Repetition weight (theme concentration)
    repetition_score = cluster_data.get("repetition_score", 0)
    repetition_weight = repetition_score * 0.1  # Max 0.1 bonus
    
    # Calculate clustered score
    clustered_score = base_score + theme_alignment + evidence_weight + diversity_weight + repetition_weight
    
    return {
        "base_score": round(base_score, 3),
        "theme_alignment": round(theme_alignment, 3),
        "evidence_weight": round(evidence_weight, 3),
        "diversity_weight": round(diversity_weight, 3),
        "repetition_weight": round(repetition_weight, 3),
        "clustered_score": round(clustered_score, 3),
    }


def compute_archetypal_resonance(
    pattern_id: str,
    pattern: Dict[str, Any],
    user_profile: Optional[Dict[str, Any]],
    cluster_data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Compute archetypal resonance from existing lens data.
    
    Uses Gene Keys Venus Sequence if available.
    Does NOT add natal transit contact logic.
    
    Returns:
    {
        "primary_archetype_label": "The Heart Opener",
        "supporting_archetypes": ["Receptivity", "Trust"],
        "source_lens": "gene_keys",
        "resonance_summary": "Your Venus sequence suggests..."
    }
    """
    if not user_profile:
        return None
    
    # Check for Gene Keys Venus data
    gene_keys = user_profile.get("gene_keys", {})
    venus_sequence = gene_keys.get("venus_sequence", {})
    
    if not venus_sequence:
        return None
    
    # Map pattern categories to Venus spheres
    pattern_category = PATTERN_TO_THEME_CATEGORY.get(pattern_id)
    dominant_theme = cluster_data.get("dominant_theme")
    
    # Venus sphere relevance mapping
    sphere_to_archetype = {
        "attraction": {"label": "The Attractor", "themes": ["relational", "identity"]},
        "iq": {"label": "The Mind Holder", "themes": ["behavioral", "identity"]},
        "eq": {"label": "The Heart Opener", "themes": ["emotional", "relational"]},
        "sq": {"label": "The Soul Bridge", "themes": ["relational", "identity"]},
        "core": {"label": "The Core Self", "themes": ["identity", "emotional"]},
        "purpose": {"label": "The Purpose Finder", "themes": ["identity", "behavioral"]},
    }
    
    # Find relevant sphere based on pattern/dominant theme
    relevant_sphere = None
    relevant_archetype = None
    
    for sphere, data in sphere_to_archetype.items():
        if pattern_category in data["themes"] or dominant_theme in data["themes"]:
            sphere_data = venus_sequence.get(sphere, {})
            if sphere_data:
                relevant_sphere = sphere
                relevant_archetype = data["label"]
                break
    
    if not relevant_sphere:
        return None
    
    # Get Gene Key data for this sphere
    sphere_data = venus_sequence.get(relevant_sphere, {})
    gene_key_num = sphere_data.get("gene_key")
    sphere_name = sphere_data.get("name", "")
    
    # Build resonance summary
    if gene_key_num and pattern_category == "relational":
        resonance_summary = f"Your {relevant_sphere.upper()} sphere ({sphere_name}) may be resonating with this pattern."
    elif gene_key_num:
        resonance_summary = f"Gene Key {gene_key_num} in your {relevant_sphere.upper()} sphere adds depth to this pattern."
    else:
        resonance_summary = None
    
    # Build supporting archetypes from other relevant spheres
    supporting = []
    for sphere, data in sphere_to_archetype.items():
        if sphere != relevant_sphere and (pattern_category in data["themes"] or dominant_theme in data["themes"]):
            sphere_data = venus_sequence.get(sphere, {})
            if sphere_data:
                supporting.append(data["label"])
    
    return {
        "primary_archetype_label": relevant_archetype,
        "supporting_archetypes": supporting[:2],
        "source_lens": "gene_keys",
        "gene_key": gene_key_num,
        "sphere": relevant_sphere,
        "resonance_summary": resonance_summary,
    }


def build_personal_pattern_core(
    pattern: Dict[str, Any],
    pattern_id: str,
    cluster_data: Dict[str, Any],
    cluster_scores: Dict[str, float],
    signals: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Build the PERSONAL_PATTERN_CORE layer for V3 response.
    
    Based on clustered multi-signal evidence, not single entry.
    """
    # Determine source mix
    source_dist = cluster_data.get("source_distribution", {})
    active_sources = [s for s, count in source_dist.items() if count > 0]
    
    # Calculate confidence based on evidence strength
    evidence_count = cluster_data.get("total_evidence_count", 0)
    diversity = cluster_data.get("source_diversity_score", 0)
    repetition = cluster_data.get("repetition_score", 0)
    
    if evidence_count >= 5 and diversity >= 0.6:
        confidence = "high"
    elif evidence_count >= 3 or diversity >= 0.3:
        confidence = "moderate"
    else:
        confidence = "low"
    
    return {
        "title": pattern.get("title", ""),
        "summary": pattern.get("what_you_may_be", ""),
        "pattern_domain": cluster_data.get("dominant_theme", "general"),
        "source_mix": active_sources,
        "evidence_count": evidence_count,
        "supporting_entries_count": sum(source_dist.values()),
        "confidence": confidence,
        "cluster_scores": cluster_scores,
    }


def build_evidence_panel_v3(
    signals: Dict[str, Any],
    cluster_data: Dict[str, Any],
    pattern: Dict[str, Any],
    pattern_id: str
) -> Dict[str, Any]:
    """
    Build structured evidence panel for V3 response.
    
    Shows evidence by source with contribution strength.
    """
    source_sections = []
    
    # Build journal section
    journal_evidence = cluster_data.get("matched_themes_by_source", {}).get("journal", [])
    if journal_evidence:
        source_sections.append({
            "source_name": "journal",
            "contribution_strength": "high" if len(journal_evidence) >= 2 else "moderate",
            "matched_themes": list(set([t for e in journal_evidence for t in e.get("themes", [])])),
            "sample_snippets": [e.get("text", "") for e in journal_evidence[:2]],
            "entry_count": len(journal_evidence),
        })
    
    # Build chat section
    chat_evidence = cluster_data.get("matched_themes_by_source", {}).get("chat", [])
    if chat_evidence:
        source_sections.append({
            "source_name": "mirror_chat",
            "contribution_strength": "moderate" if len(chat_evidence) >= 2 else "light",
            "matched_themes": list(set([t for e in chat_evidence for t in e.get("themes", [])])),
            "sample_snippets": [e.get("text", "") for e in chat_evidence[:2]],
            "entry_count": len(chat_evidence),
        })
    
    # Build lifeline section
    lifeline_evidence = cluster_data.get("matched_themes_by_source", {}).get("lifeline", [])
    if lifeline_evidence:
        source_sections.append({
            "source_name": "lifeline",
            "contribution_strength": "moderate" if len(lifeline_evidence) >= 2 else "light",
            "matched_themes": list(set([t for e in lifeline_evidence for t in e.get("themes", [])])),
            "sample_snippets": [e.get("text", "") for e in lifeline_evidence[:2]],
            "entry_count": len(lifeline_evidence),
        })
    
    # Build summary line
    total = cluster_data.get("total_evidence_count", 0)
    sources = [s["source_name"] for s in source_sections]
    if len(sources) == 1:
        summary_line = f"This pattern emerged from {total} signal(s) in your {sources[0]}."
    elif len(sources) == 2:
        summary_line = f"This pattern emerged from {total} signals across your {sources[0]} and {sources[1]}."
    elif len(sources) >= 3:
        summary_line = f"This pattern emerged from {total} signals across {len(sources)} sources."
    else:
        summary_line = "This pattern is based on current timing context."
    
    return {
        "summary_line": summary_line,
        "source_sections": source_sections,
        "total_evidence_count": total,
        "source_count": len(source_sections),
    }


def build_v3_narrative(
    personal_core: Dict[str, Any],
    timing_amplifier: Dict[str, Any],
    archetypal_resonance: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Build V3 narrative with clear separation of layers.
    
    Order:
    A. Main title = personal pattern core title
    B. Main explanation = personal pattern core summary
    C. Timing note = why it may feel stronger now
    D. Archetypal note = what deeper pattern this resembles
    E. Evidence summary = what this is based on
    """
    # A + B: Main content from personal core
    main_explanation = personal_core.get("summary", "")
    
    # C: Timing note
    timing_note = None
    if timing_amplifier.get("timing_summary"):
        timing_note = f"This may feel stronger right now because {timing_amplifier['timing_summary'].lower()}"
        # Clean up double "may be"
        timing_note = timing_note.replace("because may be", "because")
    
    # D: Archetypal note
    archetypal_note = None
    if archetypal_resonance and archetypal_resonance.get("resonance_summary"):
        archetypal_note = archetypal_resonance["resonance_summary"]
    
    # E: Evidence reference (handled separately in evidence_panel)
    
    return {
        "main_explanation": main_explanation,
        "timing_note": timing_note,
        "archetypal_note": archetypal_note,
        "combined": _combine_v3_narrative(main_explanation, timing_note, archetypal_note),
    }


def _combine_v3_narrative(
    main: str,
    timing: Optional[str],
    archetypal: Optional[str]
) -> str:
    """Combine V3 narrative parts into single text for backwards compatibility."""
    parts = [main]
    if timing:
        parts.append(timing)
    if archetypal:
        parts.append(archetypal)
    return "\n\n".join(parts)


# ============================================================================
# V4: TWO-TIMESCALE MEMORY MODEL
# ============================================================================

# Daily angle facets that can be derived from core patterns
DAILY_FACETS = {
    "relational": [
        {"tag": "trust", "label": "Trust & Safety", "desc": "What feels safe to open to"},
        {"tag": "receiving", "label": "Receiving", "desc": "What you're allowing in"},
        {"tag": "boundaries", "label": "Boundaries", "desc": "What needs protecting"},
        {"tag": "reopening", "label": "Reopening", "desc": "What's thawing or reconnecting"},
        {"tag": "vulnerability", "label": "Vulnerability", "desc": "Where you feel exposed"},
    ],
    "emotional": [
        {"tag": "processing", "label": "Processing", "desc": "What emotions are moving"},
        {"tag": "holding", "label": "Holding Space", "desc": "What needs gentle attention"},
        {"tag": "releasing", "label": "Releasing", "desc": "What's ready to let go"},
        {"tag": "feeling", "label": "Feeling", "desc": "What's present right now"},
        {"tag": "sensitivity", "label": "Sensitivity", "desc": "What's heightened"},
    ],
    "behavioral": [
        {"tag": "deciding", "label": "Deciding", "desc": "What's waiting for clarity"},
        {"tag": "acting", "label": "Taking Action", "desc": "What's ready to move"},
        {"tag": "pausing", "label": "Pausing", "desc": "What needs stillness"},
        {"tag": "resisting", "label": "Resistance", "desc": "What you're pushing against"},
        {"tag": "waiting", "label": "Waiting", "desc": "What's in limbo"},
    ],
    "identity": [
        {"tag": "questioning", "label": "Questioning", "desc": "What identity is shifting"},
        {"tag": "becoming", "label": "Becoming", "desc": "What's emerging"},
        {"tag": "letting_go", "label": "Letting Go", "desc": "What role is ending"},
        {"tag": "finding", "label": "Finding", "desc": "What's clarifying"},
        {"tag": "integrating", "label": "Integrating", "desc": "What's coming together"},
    ],
    "pressure": [
        {"tag": "managing", "label": "Managing Load", "desc": "What feels heavy"},
        {"tag": "delegating", "label": "Delegating", "desc": "What can be shared"},
        {"tag": "resting", "label": "Resting", "desc": "What needs recovery"},
        {"tag": "pushing", "label": "Pushing Through", "desc": "What requires effort"},
        {"tag": "accepting", "label": "Accepting Limits", "desc": "What can't change now"},
    ],
}

# Timing themes mapped to facet preferences
TIMING_TO_FACET_PREFERENCE = {
    "renewal_cycle": ["reopening", "releasing", "becoming"],
    "reset_cycle": ["releasing", "letting_go", "deciding"],
    "emotional_sensitivity": ["sensitivity", "feeling", "processing"],
    "emotional_openness": ["receiving", "trust", "vulnerability"],
    "relational_harmony": ["reopening", "receiving", "trust"],
    "transition_threshold": ["deciding", "questioning", "becoming"],
    "pressure": ["managing", "pushing", "accepting"],
    "identity_shift": ["questioning", "becoming", "finding"],
    "expansion": ["acting", "becoming", "receiving"],
    "contraction": ["pausing", "holding", "resting"],
    "softening_phase": ["receiving", "trust", "reopening"],
    "integration_phase": ["integrating", "finding", "processing"],
}


async def aggregate_user_signals_extended(
    db: AsyncIOMotorDatabase,
    user_id: str,
    recent_days: int = 7,
    memory_days: int = 60
) -> Dict[str, Any]:
    """
    Aggregate signals with two timescales:
    - Recent: last 7 days (for daily freshness)
    - Memory: last 60 days (for core pattern stability)
    
    Memory policy:
    - Journal: recency matters strongly (exponential decay)
    - Chat: recency matters moderately
    - Lifeline: persistent with lower daily weight
    """
    recent_cutoff = datetime.now(timezone.utc) - timedelta(days=recent_days)
    memory_cutoff = datetime.now(timezone.utc) - timedelta(days=memory_days)
    
    signals = {
        "recent": {
            "journal_entries": [],
            "chat_messages": [],
            "lifeline_events": [],
        },
        "memory": {
            "journal_entries": [],
            "chat_messages": [],
            "lifeline_events": [],
        },
        "signal_strength": "weak",
        "memory_window_days": memory_days,
    }
    
    # 1. Fetch journal entries with recency tracking
    try:
        # Fetch all recent entries, filter in Python to handle date format issues
        journal_cursor = db.journal.find({
            "user_id": user_id
        }).sort("created_at", -1).limit(30)
        
        async for entry in journal_cursor:
            created_at = entry.get("created_at")
            
            # Handle both datetime and string formats
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except:
                    created_at = datetime.now(timezone.utc) - timedelta(days=30)  # Default to 30 days ago
            elif isinstance(created_at, datetime):
                pass  # Already datetime
            else:
                created_at = datetime.now(timezone.utc) - timedelta(days=30)
            
            # Ensure timezone aware
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            
            entry_data = {
                "content": entry.get("content", ""),
                "themes": entry.get("themes", []),
                "created_at": created_at,
            }
            
            # Add to memory if within memory window (compare both as aware)
            memory_cutoff_aware = memory_cutoff if memory_cutoff.tzinfo else memory_cutoff.replace(tzinfo=timezone.utc)
            recent_cutoff_aware = recent_cutoff if recent_cutoff.tzinfo else recent_cutoff.replace(tzinfo=timezone.utc)
            
            if created_at >= memory_cutoff_aware:
                signals["memory"]["journal_entries"].append(entry_data)
            
            # Also add to recent if within recent window
            if created_at >= recent_cutoff_aware:
                signals["recent"]["journal_entries"].append(entry_data)
                
    except Exception as e:
        logger.warning(f"[PatternMirror] Failed to fetch journal (extended): {e}")
    
    # 2. Fetch chat messages
    try:
        chat_cursor = db.mirror_chat.find({
            "user_id": user_id,
            "role": "user",
            "timestamp": {"$gte": memory_cutoff}
        }).sort("timestamp", -1).limit(30)
        
        async for msg in chat_cursor:
            msg_data = {
                "content": msg.get("content", ""),
                "timestamp": msg.get("timestamp", datetime.now(timezone.utc)),
            }
            
            signals["memory"]["chat_messages"].append(msg_data)
            
            if msg_data["timestamp"] >= recent_cutoff:
                signals["recent"]["chat_messages"].append(msg_data)
                
    except Exception as e:
        logger.warning(f"[PatternMirror] Failed to fetch chat (extended): {e}")
    
    # 3. Fetch lifeline events (all, since they're persistent)
    try:
        lifeline_cursor = db.lifeline_events.find({
            "user_id": user_id,
        }).sort("event_date", -1).limit(20)
        
        async for event in lifeline_cursor:
            event_data = {
                "title": event.get("title", ""),
                "description": event.get("description", ""),
                "emotional_tone": event.get("emotional_tone", "neutral"),
                "event_date": event.get("event_date"),
            }
            
            # Lifeline goes to memory (persistent)
            signals["memory"]["lifeline_events"].append(event_data)
            # Also add recent lifeline if relevant
            signals["recent"]["lifeline_events"].append(event_data)
                
    except Exception as e:
        logger.warning(f"[PatternMirror] Failed to fetch lifeline (extended): {e}")
    
    # 4. Calculate signal strength
    recent_count = (len(signals["recent"]["journal_entries"]) + 
                    len(signals["recent"]["chat_messages"]))
    memory_count = (len(signals["memory"]["journal_entries"]) + 
                    len(signals["memory"]["chat_messages"]) +
                    len(signals["memory"]["lifeline_events"]))
    
    if recent_count >= 3:
        signals["signal_strength"] = "strong"
    elif recent_count >= 1 or memory_count >= 5:
        signals["signal_strength"] = "moderate"
    else:
        signals["signal_strength"] = "weak"
    
    return signals


def build_core_pattern_memory(
    signals: Dict[str, Any],
    cluster_data: Dict[str, Any],
    pattern: Dict[str, Any],
    pattern_id: str,
    cluster_scores: Dict[str, float]
) -> Dict[str, Any]:
    """
    Build CORE PATTERN MEMORY from the wider rolling window.
    
    This answers: "What broader personal pattern has been showing up lately?"
    
    This layer should be relatively stable across days.
    """
    memory = signals.get("memory", signals)  # Fallback to full signals if no memory key
    
    # Count entries in memory window
    journal_count = len(memory.get("journal_entries", []))
    chat_count = len(memory.get("chat_messages", []))
    lifeline_count = len(memory.get("lifeline_events", []))
    total_entries = journal_count + chat_count + lifeline_count
    
    # Determine source mix
    source_mix = []
    if journal_count > 0:
        source_mix.append("journal")
    if chat_count > 0:
        source_mix.append("mirror_chat")
    if lifeline_count > 0:
        source_mix.append("lifeline")
    
    # Extract recurring themes from cluster data
    theme_counts = cluster_data.get("theme_counts", {})
    recurring_themes = [t for t, c in sorted(theme_counts.items(), key=lambda x: -x[1]) if c >= 2][:3]
    
    # Calculate confidence
    evidence_count = cluster_data.get("total_evidence_count", 0)
    diversity = cluster_data.get("source_diversity_score", 0)
    
    if evidence_count >= 5 and diversity >= 0.5:
        confidence = "high"
    elif evidence_count >= 3 or diversity >= 0.3:
        confidence = "moderate"
    else:
        confidence = "low"
    
    return {
        "title": pattern.get("title", ""),
        "summary": pattern.get("what_you_may_be", ""),
        "domain": cluster_data.get("dominant_theme", "general"),
        "confidence": confidence,
        "source_mix": source_mix,
        "evidence_count": evidence_count,
        "supporting_entries_count": total_entries,
        "recurring_themes": recurring_themes,
        "memory_window_days": signals.get("memory_window_days", 60),
        "cluster_scores": cluster_scores,
    }


def select_daily_angle(
    core_pattern_memory: Dict[str, Any],
    transit_themes: Any,
    recent_signals: Dict[str, Any],
    archetypal_resonance: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Select the DAILY ANGLE - what facet of the core pattern is active today.
    
    This answers: "What facet of the broader pattern is most alive today?"
    
    Influenced by:
    - Current timing themes
    - Recent personal signals
    - Existing lens resonance
    """
    core_domain = core_pattern_memory.get("domain", "general")
    core_title = core_pattern_memory.get("title", "")
    core_summary = core_pattern_memory.get("summary", "")
    
    # Get available facets for this domain
    available_facets = DAILY_FACETS.get(core_domain, DAILY_FACETS.get("emotional", []))
    
    # Score facets based on timing preferences
    active_themes = transit_themes.active_themes if transit_themes else []
    
    facet_scores = {}
    for facet in available_facets:
        score = 0.0
        tag = facet["tag"]
        
        # Check timing preference
        for theme in active_themes:
            if theme in TIMING_TO_FACET_PREFERENCE:
                if tag in TIMING_TO_FACET_PREFERENCE[theme]:
                    score += 0.3
        
        # Check recent signals for facet keywords
        recent_content = " ".join([
            e.get("content", "") for e in recent_signals.get("journal_entries", [])
        ] + [
            m.get("content", "") for m in recent_signals.get("chat_messages", [])
        ]).lower()
        
        facet_keywords = {
            "trust": ["trust", "safe", "secure"],
            "receiving": ["receive", "accept", "let in", "allow"],
            "boundaries": ["boundary", "protect", "no", "limit"],
            "reopening": ["reopen", "reconnect", "thaw", "warm"],
            "vulnerability": ["vulnerable", "exposed", "open"],
            "processing": ["process", "working through", "figuring"],
            "releasing": ["release", "let go", "free"],
            "deciding": ["decide", "choice", "unclear", "which"],
            "waiting": ["wait", "limbo", "uncertain"],
            "questioning": ["who am i", "purpose", "meaning"],
        }
        
        if tag in facet_keywords:
            for kw in facet_keywords[tag]:
                if kw in recent_content:
                    score += 0.2
        
        # Archetypal boost if resonance matches facet
        if archetypal_resonance:
            ar_label = (archetypal_resonance.get("primary_archetype_label") or "").lower()
            if tag in ar_label or facet["label"].lower() in ar_label:
                score += 0.15
        
        facet_scores[tag] = score
    
    # Select highest scoring facet, or default to first
    if facet_scores:
        selected_tag = max(facet_scores, key=facet_scores.get)
        selected_facet = next((f for f in available_facets if f["tag"] == selected_tag), available_facets[0])
    else:
        selected_facet = available_facets[0] if available_facets else {"tag": "general", "label": "Today", "desc": ""}
    
    # Build daily angle summary
    # V9: Create more natural, human-readable titles
    angle_title = _build_natural_title(core_title, selected_facet)
    
    # Generate angle summary based on core + facet
    angle_summary = _generate_angle_summary(core_summary, selected_facet, transit_themes)
    
    # Determine freshness reason
    if facet_scores.get(selected_facet["tag"], 0) > 0.3:
        freshness_reason = "timing and recent signals align on this facet"
    elif active_themes:
        freshness_reason = f"current timing themes ({', '.join(active_themes[:2])}) highlight this facet"
    else:
        freshness_reason = "this facet naturally surfaces from your recent patterns"
    
    return {
        "angle_title": angle_title,
        "angle_summary": angle_summary,
        "facet_tag": selected_facet["tag"],
        "facet_label": selected_facet["label"],
        "facet_desc": selected_facet["desc"],
        "related_core_pattern": core_title,
        "derived_from_core_pattern": True,
        "daily_facet_tags": [selected_facet["tag"]] + [f["tag"] for f in available_facets[:2] if f["tag"] != selected_facet["tag"]],
        "freshness_reason": freshness_reason,
        "facet_scores": {k: round(v, 2) for k, v in facet_scores.items()},
    }


def _build_natural_title(core_title: str, facet: Dict[str, Any]) -> str:
    """
    V9: Build more natural, human-readable titles.
    
    Avoid awkward "Label: Label" constructions.
    Create titles that feel like natural phrases.
    """
    facet_tag = facet.get("tag", "")
    
    # V9: Natural title mappings by pattern + facet combination
    # Pattern titles mapped to more readable versions
    NATURAL_TITLES = {
        # Relational patterns
        "Relational Reopening": {
            "trust": "Opening Back Up",
            "reopening": "Letting Connection In Again",
            "deciding": "A Decision to Reopen",
            "receiving": "Becoming Ready to Receive",
            "general": "Connection Becoming Possible",
            "_default": "Opening Back Up",
        },
        "Heart Thaw": {
            "softening": "Softening Again",
            "trust": "Beginning to Trust",
            "vulnerability": "Letting Walls Down",
            "processing": "Thawing Out",
            "_default": "A Quiet Thaw",
        },
        "Safe Intimacy Returning": {
            "trust": "Safety Returning",
            "receiving": "Letting Closeness In",
            "boundaries": "Finding Safe Ground",
            "_default": "Closeness Becoming Safer",
        },
        "Relational Weight": {
            "processing": "Carrying Relational Weight",
            "boundaries": "Something Unspoken",
            "_default": "Something Needs Attention",
        },
        # Emotional patterns
        "Something's Here": {
            "emerging": "Something Is Stirring",
            "processing": "Noticing What's Here",
            "trust": "Trusting What's Arriving",
            "_default": "Something Wants Attention",
        },
        "Emotional Wave Riding": {
            "processing": "Riding the Wave",
            "holding": "Holding Steady",
            "releasing": "Letting It Move",
            "_default": "Moving Through Waves",
        },
        "Moving Through": {
            "processing": "Moving Through Loss",
            "releasing": "Letting Go",
            "grief": "Honoring What Was",
            "_default": "Moving Through",
        },
        # Threshold/decision patterns
        "Standing at Threshold": {
            "deciding": "Standing at a Choice",
            "trust": "Ready to Step Forward",
            "releasing": "Releasing the Old",
            "_default": "At a Threshold",
        },
        "Expansion Resistance": {
            "fear": "Noticing the Pull Back",
            "growth": "Something Bigger Calling",
            "_default": "At the Edge of More",
        },
        "Anticipating Impact": {
            "anxiety": "Bracing for What's Next",
            "processing": "Preparing for Impact",
            "_default": "Getting Ahead of Yourself",
        },
        # Behavioral patterns
        "Duty Over Self": {
            "boundaries": "Carrying Too Much",
            "processing": "Noticing the Weight",
            "_default": "Putting Others First",
        },
        "Over-Functioning Hero": {
            "boundaries": "Carrying Too Much",
            "releasing": "Learning to Put It Down",
            "processing": "Noticing the Weight",
            "_default": "Doing Too Much",
        },
        "Inner Critic Override": {
            "processing": "The Inner Critic Is Loud",
            "softening": "Finding Self-Compassion",
            "_default": "Working with the Critic",
        },
        "Waiting for Permission": {
            "deciding": "Ready Without Permission",
            "trust": "Learning to Trust Yourself",
            "_default": "Not Needing Permission",
        },
        "Holding the Line": {
            "boundaries": "Holding Your Ground",
            "processing": "Staying Firm",
            "_default": "Holding Something Important",
        },
        # === Opening/positive patterns ===
        "Reconnection Window": {
            "reaching": "Reaching Out",
            "repair": "Time to Mend",
            "trust": "A Window to Reconnect",
            "_default": "An Opening for Reconnection",
        },
        "Renewal After Distance": {
            "beginning": "Starting Fresh",
            "trust": "Trying Again",
            "receiving": "Letting in the New",
            "_default": "Something Renewed",
        },
        "Grounded Presence": {
            "stability": "Resting in Stability",
            "calm": "Settled for Now",
            "trust": "Trusting the Calm",
            "_default": "Grounded and Present",
        },
        "Emotional Integration": {
            "clarity": "Things Coming Together",
            "processing": "Making Sense of It",
            "understanding": "Pieces Falling into Place",
            "_default": "Integration Happening",
        },
    }
    
    # Try to find a natural title
    if core_title in NATURAL_TITLES:
        pattern_titles = NATURAL_TITLES[core_title]
        # Look for facet-specific title
        if facet_tag in pattern_titles:
            return pattern_titles[facet_tag]
        # Use default for this pattern
        if "_default" in pattern_titles:
            return pattern_titles["_default"]
    
    # Fallback: Use core title alone (cleaner than "Title: Facet")
    return core_title


def _generate_angle_summary(
    core_summary: str,
    facet: Dict[str, Any],
    transit_themes: Any
) -> str:
    """Generate a daily angle summary that combines core pattern with today's facet."""
    facet_tag = facet["tag"]
    facet_label = facet["label"]
    
    # Template-based angle summaries
    angle_templates = {
        "trust": "Today the question may be about trust—what feels safe enough to open to, and what still needs more care.",
        "receiving": "Today you may be noticing what you're willing to receive—where you're letting things in, and where you're still guarded.",
        "boundaries": "Today the edge between self and other may be asking for attention—what needs protecting, what can soften.",
        "reopening": "Today something that was distant may be wanting to come closer—a slow thaw, a gentle reconnection.",
        "vulnerability": "Today what feels exposed may be more present—the tender places that want care.",
        "processing": "Today emotions may be moving—not to be fixed, just witnessed.",
        "holding": "Today something may need gentle attention—held without needing to change.",
        "releasing": "Today something may be ready to let go—a weight that's been carried long enough.",
        "deciding": "Today a decision may be quietly surfacing—not rushing, just becoming clearer.",
        "waiting": "Today the in-between space may feel more present—uncertainty asking for patience.",
        "questioning": "Today questions about direction or identity may feel louder—who you're becoming.",
        "becoming": "Today something new may be emerging—slowly, in its own time.",
    }
    
    if facet_tag in angle_templates:
        return angle_templates[facet_tag]
    
    # Fallback: derive from core summary
    return f"Today the {facet_label.lower()} aspect of this pattern may be more alive: {facet['desc'].lower()}."


def build_evidence_panel_v4(
    signals: Dict[str, Any],
    cluster_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Build evidence panel showing clustered support, not just one snippet.
    
    V4 improvements:
    - Shows multiple snippets per source (max 3)
    - Includes snippet_count and evidence_weight per source
    - Clearly indicates when only one entry exists
    """
    source_sections = []
    memory = signals.get("memory", signals)
    
    # Single entry dominance detection
    single_entry_dominated = False
    why_single_dominated = None
    
    # Build journal section
    journal_entries = memory.get("journal_entries", [])
    if journal_entries:
        # Get matched themes from cluster data
        journal_evidence = cluster_data.get("matched_themes_by_source", {}).get("journal", [])
        matched_themes = list(set([t for e in journal_evidence for t in e.get("themes", [])]))[:5]
        
        # Calculate evidence weight (higher for more entries)
        evidence_weight = min(1.0, len(journal_entries) * 0.2)
        
        source_sections.append({
            "source_name": "journal",
            "contribution_strength": "high" if len(journal_entries) >= 2 else "moderate",
            "matched_themes": matched_themes,
            "snippet_count": len(journal_entries),
            "sample_snippets": [
                {"text": e.get("content", "")[:100], "date": str(e.get("created_at", ""))[:10]}
                for e in journal_entries[:3]
            ],
            "evidence_weight": round(evidence_weight, 2),
        })
        
        if len(journal_entries) == 1 and len(memory.get("chat_messages", [])) == 0:
            single_entry_dominated = True
            why_single_dominated = "Only one journal entry in memory window"
    
    # Build chat section
    chat_messages = memory.get("chat_messages", [])
    if chat_messages:
        chat_evidence = cluster_data.get("matched_themes_by_source", {}).get("chat", [])
        matched_themes = list(set([t for e in chat_evidence for t in e.get("themes", [])]))[:5]
        
        evidence_weight = min(0.8, len(chat_messages) * 0.15)
        
        source_sections.append({
            "source_name": "mirror_chat",
            "contribution_strength": "moderate" if len(chat_messages) >= 2 else "light",
            "matched_themes": matched_themes,
            "snippet_count": len(chat_messages),
            "sample_snippets": [
                {"text": m.get("content", "")[:80], "date": str(m.get("timestamp", ""))[:10]}
                for m in chat_messages[:3]
            ],
            "evidence_weight": round(evidence_weight, 2),
        })
    
    # Build lifeline section
    lifeline_events = memory.get("lifeline_events", [])
    if lifeline_events:
        lifeline_evidence = cluster_data.get("matched_themes_by_source", {}).get("lifeline", [])
        matched_themes = list(set([t for e in lifeline_evidence for t in e.get("themes", [])]))[:5]
        
        evidence_weight = min(0.6, len(lifeline_events) * 0.1)
        
        source_sections.append({
            "source_name": "lifeline",
            "contribution_strength": "moderate" if len(lifeline_events) >= 3 else "light",
            "matched_themes": matched_themes,
            "snippet_count": len(lifeline_events),
            "sample_snippets": [
                {"text": e.get("title", ""), "emotional_tone": e.get("emotional_tone")}
                for e in lifeline_events[:3]
            ],
            "evidence_weight": round(evidence_weight, 2),
        })
    
    # Build summary line
    total_snippets = sum(s["snippet_count"] for s in source_sections)
    sources = [s["source_name"] for s in source_sections]
    
    if single_entry_dominated:
        summary_line = f"Based primarily on a recent journal entry."
    elif total_snippets == 1:
        summary_line = f"Based on one signal in your {sources[0] if sources else 'recent activity'}."
    elif len(sources) == 1:
        summary_line = f"This pattern emerged from {total_snippets} entries in your {sources[0]}."
    elif len(sources) == 2:
        summary_line = f"This pattern emerged from {total_snippets} signals across your {sources[0]} and {sources[1]}."
    else:
        summary_line = f"This pattern emerged from {total_snippets} signals across {len(sources)} sources."
    
    return {
        "summary_line": summary_line,
        "source_sections": source_sections,
        "total_snippet_count": total_snippets,
        "source_count": len(source_sections),
        "single_entry_dominated": single_entry_dominated,
        "why_single_dominated": why_single_dominated,
        "snippet_count_by_source": {s["source_name"]: s["snippet_count"] for s in source_sections},
    }


def build_v4_narrative(
    core_memory: Dict[str, Any],
    daily_angle: Dict[str, Any],
    timing_amplifier: Dict[str, Any],
    archetypal_resonance: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Build V4 narrative with two-timescale model.
    
    Order:
    A. Card title = DAILY ANGLE title
    B. Main paragraph = DAILY ANGLE summary
    C. Sub-line = "This seems connected to a broader pattern of …"
    D. Timing note = "This may feel stronger now because …"
    E. Archetypal note (optional)
    """
    # A: Title
    title = daily_angle.get("angle_title", core_memory.get("title", ""))
    
    # B: Main paragraph
    main_paragraph = daily_angle.get("angle_summary", "")
    
    # C: Connection to core
    core_title = core_memory.get("title", "")
    core_domain = core_memory.get("domain", "")
    
    if core_domain and core_title:
        core_connection = f"This seems connected to a broader pattern of {core_domain} themes you've been exploring—{core_title.lower()}."
    else:
        core_connection = None
    
    # D: Timing note
    timing_note = None
    if timing_amplifier.get("timing_summary"):
        timing_note = f"This may feel stronger right now because {timing_amplifier['timing_summary'].lower()}"
        timing_note = timing_note.replace("because may be", "because").rstrip(".")
    
    # E: Archetypal note
    archetypal_note = None
    if archetypal_resonance and archetypal_resonance.get("resonance_summary"):
        archetypal_note = archetypal_resonance["resonance_summary"]
    
    return {
        "title": title,
        "main_paragraph": main_paragraph,
        "core_connection": core_connection,
        "timing_note": timing_note,
        "archetypal_note": archetypal_note,
        "combined": _combine_v4_narrative(main_paragraph, core_connection, timing_note),
    }


def _combine_v4_narrative(
    main: str,
    core_connection: Optional[str],
    timing: Optional[str]
) -> str:
    """Combine V4 narrative parts."""
    parts = [main]
    if core_connection:
        parts.append(core_connection)
    if timing:
        parts.append(timing)
    return "\n\n".join(parts)


# ============================================================================
# V5: TWO-LAYER MIRROR OUTPUT STRUCTURE
# ============================================================================
# 
# Implements the new output format:
# A. CORE PATTERN (always visible) - One sharp sentence
# B. WHY THIS MAY BE SHOWING UP - 1-2 sentences on timing/activation  
# C. HOW THIS WAS DERIVED (collapsible) - Cross-lens proof
#
# Language Rules:
# - NO jargon (avoid "Gate 22", "Resource element" unless simplified)
# - Use directional language: "moving toward", "shifting from → to", etc.
# - Only include lenses that meaningfully contribute
# ============================================================================

# Cross-lens translation templates (plain English, no jargon)
LENS_SIGNAL_TRANSLATIONS = {
    "astrology": {
        "new_moon": "A new cycle is beginning—endings and fresh starts overlapping",
        "full_moon": "Things are reaching a peak—what's been building is now visible", 
        "waning": "Energy is moving inward—time to process rather than push",
        "waxing": "Energy is building—momentum gathering toward something",
        "emotional_sensitivity": "Emotional sensitivity is heightened right now",
        "transition_threshold": "You're at a threshold—one phase ending, another beginning",
        "reset_cycle": "A natural reset is underway—clearing to make room",
        "renewal_cycle": "Renewal energy is present—something wants to grow",
        "pressure": "Pressure is building—decisions or tensions coming to a head",
        "expansion": "Expansion is available—conditions support reaching outward",
        "contraction": "Energy is contracting—pulling inward for consolidation",
        "relational_harmony": "Relational conditions are supportive right now",
        "relational_sensitivity": "Relational sensitivity is heightened",
        "softening_phase": "A natural softening is occurring—defenses relaxing",
        "integration_phase": "Integration is happening—pieces coming together",
    },
    "human_design": {
        "defined_head": "Mental activity may feel more constant—processing is active",
        "defined_ajna": "Mental certainty may feel stronger—fixed perspectives present",
        "defined_throat": "Expression and communication feel more available",
        "defined_g_center": "Sense of direction feels more stable",
        "defined_heart": "Willpower and commitment feel more accessible",
        "defined_sacral": "Energy for work and response feels consistent",
        "defined_spleen": "Instincts and intuition are speaking clearly",
        "defined_solar_plexus": "Emotional waves are moving—clarity comes with time",
        "defined_root": "Pressure to act or complete is present",
        "undefined_centers": "You may be absorbing energy from your environment",
        "generator": "Waiting for response before acting serves you",
        "projector": "Waiting for recognition and invitation matters now",
        "manifestor": "Initiating energy is available—inform before acting",
        "reflector": "Taking time before decisions is especially important",
    },
    "bazi": {
        "wood_dominant": "Growth energy is strong—expansion and new beginnings",
        "fire_dominant": "Transformation energy is active—passion and visibility",
        "earth_dominant": "Stability energy is present—grounding and consolidation",
        "metal_dominant": "Refinement energy is active—cutting away what doesn't serve",
        "water_dominant": "Wisdom and flow energy present—adaptability serves you",
        "wood_weak": "Growth energy may feel harder to access—patience with progress",
        "fire_weak": "Passion and drive may feel lower—rest supports recovery",
        "earth_weak": "Stability may feel harder to find—seek grounding",
        "metal_weak": "Clarity and boundaries may need extra attention",
        "water_weak": "Going with the flow may feel challenging—structure helps",
        "energy_shifting": "Energy is shifting from one mode to another",
        "seasonal_alignment": "Current season supports this pattern",
        "element_clash": "Conflicting energies present—inner tension is normal",
    },
    "lifeline": {
        "pattern_repeating": "This pattern has appeared before in your life",
        "similar_themes": "Similar themes show up across multiple experiences",
        "emotional_echo": "Emotional tone matches previous significant moments",
        "relationship_pattern": "Relational patterns from your history are echoing",
        "growth_edge": "This touches a growth edge you've been working on",
        "unresolved_thread": "An unresolved thread from your past is active",
    },
}


def build_two_layer_mirror_output(
    pattern: Dict[str, Any],
    pattern_id: str,
    core_pattern_memory: Dict[str, Any],
    daily_angle: Dict[str, Any],
    timing_amplifier: Dict[str, Any],
    cluster_data: Dict[str, Any],
    signals_extended: Dict[str, Any],
    transit_themes: Any,
    user_profile: Optional[Dict[str, Any]] = None,
    bazi_chart: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Build the V10 Three-Layer Mirror Output structure with CONTEXT-AWARE LANGUAGE.
    
    V10 Upgrade: Language now adapts to user signals instead of using static templates.
    
    Layer A: CORE PATTERN (always visible)
    - One sharp, behaviorally meaningful sentence
    
    Layer B: WHY THIS MAY BE SHOWING UP (always visible)
    - 1-2 sentences explaining timing/activation (context-aware)
    
    Layer C: HOW THIS WAS DERIVED (collapsible)
    - Structured cross-lens proof with plain language translations
    - Only includes lenses that meaningfully contributed
    
    Layer D: WHERE THE FRICTION MAY BE (always visible)
    - 1 short sentence describing likely tension/hesitation/blind spot (context-aware)
    
    Layer E: WHAT TO DO WITH IT (always visible)
    - 1 short practical reflection or action sentence (context-aware)
    """
    # Get user_id for deterministic variation
    user_id = ""
    if user_profile:
        user_id = str(user_profile.get("_id", ""))
    
    # ===== LAYER A: CORE PATTERN (one sharp sentence) =====
    # Extract the core insight from daily angle or pattern summary
    core_summary = daily_angle.get("angle_summary", "")
    core_title = daily_angle.get("angle_title", pattern.get("title", ""))
    
    # Simplify to one sharp sentence if needed
    core_insight = _extract_sharp_insight(core_summary, pattern)
    
    # ===== LAYER B: WHY THIS MAY BE SHOWING UP =====
    # V10: Context-aware explanation using signal tones
    why_showing_up = _build_why_showing_up_v10(
        pattern_id,
        pattern,
        signals_extended,
        cluster_data,
        timing_amplifier,
        transit_themes,
        daily_angle,
        user_id
    )
    
    # ===== LAYER C: HOW THIS WAS DERIVED (cross-lens proof) =====
    # Build structured derivation from each contributing lens
    cross_lens_derivation = _build_cross_lens_derivation(
        transit_themes,
        cluster_data,
        signals_extended,
        user_profile,
        bazi_chart,
        pattern_id
    )
    
    # ===== LAYER D: WHERE THE FRICTION MAY BE =====
    # V10: Context-aware friction using signal tones
    friction = _build_friction_layer_v10(pattern, pattern_id, signals_extended, cluster_data, user_id)
    
    # ===== LAYER E: WHAT TO DO WITH IT =====
    # V10: Context-aware practical using signal tones and lifeline patterns
    practical = _build_practical_layer_v10(pattern, pattern_id, signals_extended, cluster_data, user_id)
    
    return {
        "core_insight": {
            "title": core_title,
            "text": core_insight,
        },
        "why_showing_up": {
            "text": why_showing_up,
            "is_timing_driven": timing_amplifier.get("timing_role") == "fallback",
        },
        "cross_lens_derivation": cross_lens_derivation,
        # V6 NEW: Usefulness layers
        "friction": {
            "text": friction,
        },
        "practical": {
            "text": practical,
        },
        "display_config": {
            "core_always_visible": True,
            "why_always_visible": True,
            "derivation_collapsed_by_default": True,
            "derivation_label": "How this was derived",
            "friction_always_visible": True,
            "practical_always_visible": True,
        }
    }


def _build_friction_layer(pattern: Dict[str, Any], pattern_id: str) -> str:
    """
    V9: Build the friction layer - one short, sharp sentence.
    
    Describes the likely tension, hesitation, or blind spot.
    Tighter and more emotionally true.
    """
    # V9: Polished, tighter friction statements - EXPANDED COVERAGE
    friction_map = {
        # === Relational patterns ===
        "relational_reopening": "Part of you may still want proof that openness is safe.",
        "heart_thaw": "Part of you may still be testing whether softening is worth the risk.",
        "safe_intimacy_returning": "You might hesitate to fully arrive, in case the safety shifts.",
        "relational_weight": "Part of you may be carrying more of this than you need to.",
        "reconnection_window": "You might be overthinking the right way to reach out.",
        
        # === Emotional patterns ===
        "somethings_here": "You might be resisting naming it too soon.",
        "emotional_wave_riding": "You might want to fast-forward through the feeling instead of riding it.",
        "moving_through": "Part of you may be minimizing what you're actually grieving.",
        "emotional_integration": "You might be rushing to make sense of it before it's ready.",
        
        # === Threshold/identity patterns ===
        "threshold_standing": "You may still be waiting for certainty before stepping forward.",
        "expansion_resistance": "Part of you may be finding reasons why now isn't the right time.",
        "anticipating_impact": "You might be bracing for something that hasn't happened yet.",
        
        # === Behavioral patterns ===
        "duty_over_self": "You might be putting your own needs at the end of the list again.",
        "over_functioning_hero": "You might find it hard to rest when there's still something you could do.",
        "inner_critic_override": "You may be dismissing your own knowing before it has room to land.",
        "waiting_for_permission": "You might be looking outside for permission you already have.",
        "perfectionist_paralysis": "You may be telling yourself it's not ready when it might be.",
        "avoidant_autopilot": "Part of you may be subtly steering away from what feels too close.",
        "control_grip": "You may be tightening your hold on things that need room to breathe.",
        "boundary_blur": "You might feel pulled between your needs and what others expect.",
        "people_pleasing_loop": "You may be adjusting to fit others before checking what you want.",
        "holding_the_line": "You might be repeating yourself in ways that aren't landing.",
        "closed_door_syndrome": "Part of you may be scanning for reasons to step back.",
        
        # === Opening/positive patterns ===
        "grounded_presence": "You might be distrusting the calm, waiting for something to go wrong.",
        "renewal_after_distance": "You might bring old expectations into what wants to be new.",
    }
    
    if pattern_id in friction_map:
        return friction_map[pattern_id]
    
    # Fallback: use first challenge, polished
    challenge = pattern.get("challenge", [])
    if challenge and len(challenge) > 0:
        first_challenge = challenge[0].lower()
        return f"You may notice a pull toward {first_challenge}."
    
    return "You may be waiting for the right moment instead of trusting this one."


def _build_practical_layer(pattern: Dict[str, Any], pattern_id: str) -> str:
    """
    Build the V6 practical layer - one short actionable sentence.
    
    This should be a simple, useful, concrete suggestion the user can actually do.
    """
    # Pattern-specific practical suggestions (concise, one sentence)
    # V9: COMPLETE COVERAGE - all 16 content patterns have specific practical advice
    practical_map = {
        # === Relational patterns ===
        "relational_reopening": "Let yourself notice one small moment of connection without immediately evaluating it.",
        "heart_thaw": "Allow yourself one unguarded thought today without rushing to protect it.",
        "safe_intimacy_returning": "Notice where you already feel safe, even if it's just for a moment.",
        "relational_weight": "Name one thing you've been carrying that isn't yours to hold alone.",
        "reconnection_window": "Send one small signal today—a text, a question—without needing to control the response.",
        
        # === Emotional patterns ===
        "somethings_here": "Name one feeling you notice right now, even if it's incomplete.",
        "emotional_wave_riding": "Let one wave of feeling pass through without trying to stop it or figure it out.",
        "moving_through": "Give yourself permission to feel what's actually here, not what you think you should feel.",
        "emotional_integration": "Notice one thing that's starting to make sense, even if the whole picture isn't clear.",
        
        # === Threshold/identity patterns ===
        "threshold_standing": "Let yourself notice what already feels true before asking for more proof.",
        "expansion_resistance": "Take one small step toward the thing you're resisting—just to see what happens.",
        "anticipating_impact": "Ask yourself: what is actually happening right now, not what might happen?",
        
        # === Behavioral patterns ===
        "duty_over_self": "Put one of your own needs on the list today, even if it's small.",
        "over_functioning_hero": "Let one thing be good enough today without fixing it further.",
        "inner_critic_override": "Notice what you'd say to a friend in your situation—and say it to yourself.",
        "waiting_for_permission": "Ask yourself what you'd do if you already had permission.",
        "perfectionist_paralysis": "Choose one thing that's ready and let it be done.",
        "emotional_flooding": "Give the feeling a name and one minute of your attention without acting on it.",
        "avoidant_autopilot": "Notice where you're steering away—and pause there for a breath.",
        "control_grip": "Release your grip on one small thing today and notice what happens.",
        "boundary_blur": "Check in with what you actually want before saying yes.",
        "people_pleasing_loop": "Before adjusting, ask: what would I choose if no one were watching?",
        "holding_the_line": "Notice where you're holding tension and let your body soften, even slightly.",
        "closed_door_syndrome": "Try staying present one beat longer than your instinct to retreat.",
        
        # === Opening/positive patterns ===
        "grounded_presence": "Let yourself rest in what's stable right now—no need to look for trouble.",
        "renewal_after_distance": "Meet this moment fresh, without assuming it will repeat the past.",
    }
    
    # Get pattern-specific practical or generate from micro_shifts
    if pattern_id in practical_map:
        return practical_map[pattern_id]
    
    # Fallback: use first micro_shift, simplified
    micro_shifts = pattern.get("micro_shifts", [])
    if micro_shifts and len(micro_shifts) > 0:
        first_shift = micro_shifts[0]
        if first_shift:
            return first_shift
    
    return "Notice what already feels true and give it a moment of your attention."


# ============================================================================
# V10: CONTEXT-AWARE LAYER BUILDERS
# ============================================================================
# These functions replace static map lookups with context-aware generation
# that adapts to user signals while using maps as fallback/baseline.
# ============================================================================

def _build_why_showing_up_v10(
    pattern_id: str,
    pattern: Dict[str, Any],
    signals_extended: Dict[str, Any],
    cluster_data: Dict[str, Any],
    timing_amplifier: Dict[str, Any],
    transit_themes: Any,
    daily_angle: Dict[str, Any],
    user_id: str = ""
) -> str:
    """
    V10: Build context-aware "why now" explanation.
    
    Uses base maps as scaffold, layers signal-responsive modifications.
    Two users with same pattern but different signals get different outputs.
    """
    # V10: Base maps for "why now" explanations (fallback)
    PATTERN_WHY_NOW = {
        # === Relational patterns ===
        "relational_reopening": {
            "high": "Something in you may be becoming more willing to let connection back in.",
            "medium": "Momentum is building around connection—readiness is growing.",
            "low": "Current timing may be making openness feel more possible.",
        },
        "heart_thaw": {
            "high": "Walls that have been up are starting to soften.",
            "medium": "Something is thawing—defensiveness is loosening.",
            "low": "Conditions may be supporting a quiet softening.",
        },
        "safe_intimacy_returning": {
            "high": "Safety in closeness is becoming more accessible again.",
            "medium": "The conditions for safe connection are improving.",
            "low": "Timing may be supporting a return to closeness.",
        },
        "relational_weight": {
            "high": "A relationship dynamic you've been carrying is pressing for attention.",
            "medium": "Something unspoken may be ready to surface.",
            "low": "Current timing may be highlighting what's been held too long.",
        },
        "reconnection_window": {
            "high": "An opening for repair or reconnection is becoming visible.",
            "medium": "Conditions seem more favorable for reaching out.",
            "low": "Timing may be supporting a gentle move toward connection.",
        },
        # === Emotional patterns ===
        "somethings_here": {
            "high": "Something has been stirring and is now ready to be noticed.",
            "medium": "An awareness is emerging—something wants attention.",
            "low": "Current timing may be bringing something into focus.",
        },
        "emotional_wave_riding": {
            "high": "Emotional waves are moving through with more intensity right now.",
            "medium": "Feelings may be arriving faster than you can process them.",
            "low": "Current timing may be amplifying emotional fluctuations.",
        },
        "moving_through": {
            "high": "Something you've been holding is ready to move through you.",
            "medium": "Processing something old may feel more available now.",
            "low": "Timing may be supporting release or completion.",
        },
        "emotional_integration": {
            "high": "Pieces that felt separate are starting to come together.",
            "medium": "Something about your experience is becoming clearer.",
            "low": "Integration may be happening quietly beneath the surface.",
        },
        # === Threshold/identity patterns ===
        "threshold_standing": {
            "high": "You're at a decision point, and multiple signals are converging on it.",
            "medium": "A choice is becoming more present—the moment feels ripe.",
            "low": "Current timing may be highlighting a threshold.",
        },
        "expansion_resistance": {
            "high": "Something bigger is calling, and the resistance to it is becoming clearer.",
            "medium": "Growth pressure is building—the pull and the hesitation are both present.",
            "low": "Timing may be revealing where expansion feels risky.",
        },
        "anticipating_impact": {
            "high": "Future concerns are pressing more heavily than usual.",
            "medium": "Your mind may be running ahead of present reality.",
            "low": "Current timing may be amplifying anticipatory tension.",
        },
        # === Behavioral patterns ===
        "duty_over_self": {
            "high": "The gap between what you're giving and what you're receiving is becoming visible.",
            "medium": "Self-sacrifice patterns may be surfacing for attention.",
            "low": "Current pressures may be highlighting where you put yourself last.",
        },
        "over_functioning_hero": {
            "high": "The weight of carrying so much is becoming harder to ignore.",
            "medium": "Something about your current load is asking for attention.",
            "low": "Current pressures may be revealing where you're overextended.",
        },
        "inner_critic_override": {
            "high": "Self-critical voices are louder right now, asking to be worked with.",
            "medium": "Your inner critic may be more active than usual.",
            "low": "Timing may be amplifying self-judgment.",
        },
        "holding_the_line": {
            "high": "Something you've been firm about is being tested again.",
            "medium": "A boundary or position you hold may need reinforcement.",
            "low": "Current timing may be highlighting where you're holding firm.",
        },
        # === Opening/positive patterns ===
        "grounded_presence": {
            "high": "A sense of stability is genuinely available right now.",
            "medium": "Groundedness feels more accessible than usual.",
            "low": "Conditions may be supporting a moment of stillness.",
        },
        "renewal_after_distance": {
            "high": "Something that felt stuck or distant is opening again.",
            "medium": "Fresh energy is entering where things felt stale.",
            "low": "Timing may be supporting a new beginning.",
        },
    }
    
    # V10: Apply context-aware enhancements
    # The generate_why_now function uses PATTERN_WHY_NOW as base map
    # and layers signal-responsive modifications on top
    return generate_why_now(
        pattern_id,
        pattern,
        signals_extended,
        cluster_data,
        transit_themes,
        PATTERN_WHY_NOW,
        user_id
    )


def _build_friction_layer_v10(
    pattern: Dict[str, Any], 
    pattern_id: str,
    signals_extended: Dict[str, Any],
    cluster_data: Dict[str, Any],
    user_id: str = ""
) -> str:
    """
    V10: Build context-aware friction statement.
    
    Uses base map as scaffold, layers signal-responsive modifications.
    Adapts based on user's detected emotional/behavioral tones.
    """
    # V10: Base friction map (fallback)
    friction_map = {
        # === Relational patterns ===
        "relational_reopening": "Part of you may still want proof that openness is safe.",
        "heart_thaw": "Part of you may still be testing whether softening is worth the risk.",
        "safe_intimacy_returning": "You might hesitate to fully arrive, in case the safety shifts.",
        "relational_weight": "Part of you may be carrying more of this than you need to.",
        "reconnection_window": "You might be overthinking the right way to reach out.",
        # === Emotional patterns ===
        "somethings_here": "You might be resisting naming it too soon.",
        "emotional_wave_riding": "You might want to fast-forward through the feeling instead of riding it.",
        "moving_through": "Part of you may be minimizing what you're actually grieving.",
        "emotional_integration": "You might be rushing to make sense of it before it's ready.",
        # === Threshold/identity patterns ===
        "threshold_standing": "You may still be waiting for certainty before stepping forward.",
        "expansion_resistance": "Part of you may be finding reasons why now isn't the right time.",
        "anticipating_impact": "You might be bracing for something that hasn't happened yet.",
        # === Behavioral patterns ===
        "duty_over_self": "You might be putting your own needs at the end of the list again.",
        "over_functioning_hero": "You might find it hard to rest when there's still something you could do.",
        "inner_critic_override": "You may be dismissing your own knowing before it has room to land.",
        "waiting_for_permission": "You might be looking outside for permission you already have.",
        "perfectionist_paralysis": "You may be telling yourself it's not ready when it might be.",
        "avoidant_autopilot": "Part of you may be subtly steering away from what feels too close.",
        "control_grip": "You may be tightening your hold on things that need room to breathe.",
        "boundary_blur": "You might feel pulled between your needs and what others expect.",
        "people_pleasing_loop": "You may be adjusting to fit others before checking what you want.",
        "holding_the_line": "You might be repeating yourself in ways that aren't landing.",
        "closed_door_syndrome": "Part of you may be scanning for reasons to step back.",
        # === Opening/positive patterns ===
        "grounded_presence": "You might be distrusting the calm, waiting for something to go wrong.",
        "renewal_after_distance": "You might bring old expectations into what wants to be new.",
    }
    
    # V10: Apply context-aware generation
    return generate_friction(
        pattern_id,
        pattern,
        signals_extended,
        cluster_data,
        friction_map,
        user_id
    )


def _build_practical_layer_v10(
    pattern: Dict[str, Any], 
    pattern_id: str,
    signals_extended: Dict[str, Any],
    cluster_data: Dict[str, Any],
    user_id: str = ""
) -> str:
    """
    V10: Build context-aware practical suggestion.
    
    Uses base map as scaffold, layers signal-responsive modifications.
    Adapts based on user's detected tones and lifeline patterns.
    """
    # V10: Base practical map (fallback)
    practical_map = {
        # === Relational patterns ===
        "relational_reopening": "Let yourself notice one small moment of connection without immediately evaluating it.",
        "heart_thaw": "Allow yourself one unguarded thought today without rushing to protect it.",
        "safe_intimacy_returning": "Notice where you already feel safe, even if it's just for a moment.",
        "relational_weight": "Name one thing you've been carrying that isn't yours to hold alone.",
        "reconnection_window": "Send one small signal today—a text, a question—without needing to control the response.",
        # === Emotional patterns ===
        "somethings_here": "Name one feeling you notice right now, even if it's incomplete.",
        "emotional_wave_riding": "Let one wave of feeling pass through without trying to stop it or figure it out.",
        "moving_through": "Give yourself permission to feel what's actually here, not what you think you should feel.",
        "emotional_integration": "Notice one thing that's starting to make sense, even if the whole picture isn't clear.",
        # === Threshold/identity patterns ===
        "threshold_standing": "Let yourself notice what already feels true before asking for more proof.",
        "expansion_resistance": "Take one small step toward the thing you're resisting—just to see what happens.",
        "anticipating_impact": "Ask yourself: what is actually happening right now, not what might happen?",
        # === Behavioral patterns ===
        "duty_over_self": "Put one of your own needs on the list today, even if it's small.",
        "over_functioning_hero": "Let one thing be good enough today without fixing it further.",
        "inner_critic_override": "Notice what you'd say to a friend in your situation—and say it to yourself.",
        "waiting_for_permission": "Ask yourself what you'd do if you already had permission.",
        "perfectionist_paralysis": "Choose one thing that's ready and let it be done.",
        "emotional_flooding": "Give the feeling a name and one minute of your attention without acting on it.",
        "avoidant_autopilot": "Notice where you're steering away—and pause there for a breath.",
        "control_grip": "Release your grip on one small thing today and notice what happens.",
        "boundary_blur": "Check in with what you actually want before saying yes.",
        "people_pleasing_loop": "Before adjusting, ask: what would I choose if no one were watching?",
        "holding_the_line": "Notice where you're holding tension and let your body soften, even slightly.",
        "closed_door_syndrome": "Try staying present one beat longer than your instinct to retreat.",
        # === Opening/positive patterns ===
        "grounded_presence": "Let yourself rest in what's stable right now—no need to look for trouble.",
        "renewal_after_distance": "Meet this moment fresh, without assuming it will repeat the past.",
    }
    
    # V10: Apply context-aware generation
    return generate_practical(
        pattern_id,
        pattern,
        signals_extended,
        cluster_data,
        practical_map,
        user_id
    )


def _extract_sharp_insight(angle_summary: str, pattern: Dict[str, Any]) -> str:
    """
    Extract or generate one sharp, behaviorally meaningful sentence.
    
    Must be:
    - Human, clear, behaviorally meaningful
    - Not abstract or mystical
    """
    # If angle_summary is already short enough, use it
    if angle_summary and len(angle_summary) < 120:
        # Clean up if needed
        insight = angle_summary.strip()
        if insight.endswith("."):
            return insight
        return insight + "."
    
    # If too long, take first sentence
    if angle_summary:
        sentences = angle_summary.split(".")
        if sentences:
            first = sentences[0].strip()
            if first and len(first) > 20:
                return first + "."
    
    # Fallback to pattern's what_you_may_be, simplified
    what_you_may_be = pattern.get("what_you_may_be", "")
    if what_you_may_be:
        sentences = what_you_may_be.split(".")
        if sentences:
            first = sentences[0].strip()
            if first:
                return first + "."
    
    return "A pattern is showing up that may deserve your attention."


def _build_why_showing_up(
    timing_amplifier: Dict[str, Any],
    transit_themes: Any,
    cluster_data: Dict[str, Any],
    daily_angle: Dict[str, Any],
    pattern_id: str = ""
) -> str:
    """
    V9: Build a specific, human explanation for WHY this pattern is showing up NOW.
    
    Keep this concise but meaningful. Don't repeat derivation details.
    """
    # Get evidence-based signals
    source_diversity = cluster_data.get("source_diversity_score", 0)
    evidence_count = cluster_data.get("total_evidence_count", 0)
    dominant_theme = cluster_data.get("dominant_theme", "")
    
    # V9: Pattern-specific "why now" explanations
    # COMPLETE COVERAGE - all 16 content patterns have specific "why now" entries
    PATTERN_WHY_NOW = {
        # === Relational patterns ===
        "relational_reopening": {
            "high": "Something in you may be becoming more willing to let connection back in.",
            "medium": "Momentum is building around connection—readiness is growing.",
            "low": "Current timing may be making openness feel more possible.",
        },
        "heart_thaw": {
            "high": "Walls that have been up are starting to soften.",
            "medium": "Something is thawing—defensiveness is loosening.",
            "low": "Conditions may be supporting a quiet softening.",
        },
        "safe_intimacy_returning": {
            "high": "Safety in closeness is becoming more accessible again.",
            "medium": "The conditions for safe connection are improving.",
            "low": "Timing may be supporting a return to closeness.",
        },
        "relational_weight": {
            "high": "A relationship dynamic you've been carrying is pressing for attention.",
            "medium": "Something unspoken may be ready to surface.",
            "low": "Current timing may be highlighting what's been held too long.",
        },
        "reconnection_window": {
            "high": "An opening for repair or reconnection is becoming visible.",
            "medium": "Conditions seem more favorable for reaching out.",
            "low": "Timing may be supporting a gentle move toward connection.",
        },
        
        # === Emotional patterns ===
        "somethings_here": {
            "high": "Something has been stirring and is now ready to be noticed.",
            "medium": "An awareness is emerging—something wants attention.",
            "low": "Current timing may be bringing something into focus.",
        },
        "emotional_wave_riding": {
            "high": "Emotional waves are moving through with more intensity right now.",
            "medium": "Feelings may be arriving faster than you can process them.",
            "low": "Current timing may be amplifying emotional fluctuations.",
        },
        "moving_through": {
            "high": "Something you've been holding is ready to move through you.",
            "medium": "Processing something old may feel more available now.",
            "low": "Timing may be supporting release or completion.",
        },
        "emotional_integration": {
            "high": "Pieces that felt separate are starting to come together.",
            "medium": "Something about your experience is becoming clearer.",
            "low": "Integration may be happening quietly beneath the surface.",
        },
        
        # === Threshold/identity patterns ===
        "threshold_standing": {
            "high": "You're at a decision point, and multiple signals are converging on it.",
            "medium": "A choice is becoming more present—the moment feels ripe.",
            "low": "Current timing may be highlighting a threshold.",
        },
        "expansion_resistance": {
            "high": "Something bigger is calling, and the resistance to it is becoming clearer.",
            "medium": "Growth pressure is building—the pull and the hesitation are both present.",
            "low": "Timing may be revealing where expansion feels risky.",
        },
        "anticipating_impact": {
            "high": "Future concerns are pressing more heavily than usual.",
            "medium": "Your mind may be running ahead of present reality.",
            "low": "Current timing may be amplifying anticipatory tension.",
        },
        
        # === Behavioral patterns ===
        "duty_over_self": {
            "high": "The gap between what you're giving and what you're receiving is becoming visible.",
            "medium": "Self-sacrifice patterns may be surfacing for attention.",
            "low": "Current pressures may be highlighting where you put yourself last.",
        },
        "over_functioning_hero": {
            "high": "The weight of carrying so much is becoming harder to ignore.",
            "medium": "Something about your current load is asking for attention.",
            "low": "Current pressures may be revealing where you're overextended.",
        },
        "inner_critic_override": {
            "high": "Self-critical voices are louder right now, asking to be worked with.",
            "medium": "Your inner critic may be more active than usual.",
            "low": "Timing may be amplifying self-judgment.",
        },
        "holding_the_line": {
            "high": "Something you've been firm about is being tested again.",
            "medium": "A boundary or position you hold may need reinforcement.",
            "low": "Current timing may be highlighting where you're holding firm.",
        },
        
        # === Opening/positive patterns ===
        "grounded_presence": {
            "high": "A sense of stability is genuinely available right now.",
            "medium": "Groundedness feels more accessible than usual.",
            "low": "Conditions may be supporting a moment of stillness.",
        },
        "renewal_after_distance": {
            "high": "Something that felt stuck or distant is opening again.",
            "medium": "Fresh energy is entering where things felt stale.",
            "low": "Timing may be supporting a new beginning.",
        },
    }
    
    # Determine evidence level
    if evidence_count >= 3 and source_diversity >= 0.5:
        level = "high"
    elif evidence_count >= 2:
        level = "medium"
    else:
        level = "low"
    
    # Try pattern-specific explanation first
    if pattern_id in PATTERN_WHY_NOW:
        return PATTERN_WHY_NOW[pattern_id].get(level, PATTERN_WHY_NOW[pattern_id]["low"])
    
    # V9: Fallback based on dominant theme
    theme_why_now = {
        "relational": {
            "high": "Connection and closeness are becoming more present in your awareness.",
            "medium": "Something around relationships is asking for attention.",
            "low": "Current timing may be highlighting relational themes.",
        },
        "emotional": {
            "high": "Emotional material is moving and wants to be witnessed.",
            "medium": "Feelings are surfacing that may have been waiting.",
            "low": "Current timing may be bringing emotions into focus.",
        },
        "behavioral": {
            "high": "Patterns in how you respond are becoming visible.",
            "medium": "Something about how you're operating is asking for notice.",
            "low": "Current timing may be revealing habitual patterns.",
        },
        "identity": {
            "high": "Questions of direction and purpose are pressing for attention.",
            "medium": "Something about your sense of self is shifting.",
            "low": "Current timing may be highlighting identity questions.",
        },
    }
    
    if dominant_theme in theme_why_now:
        return theme_why_now[dominant_theme].get(level, theme_why_now[dominant_theme]["low"])
    
    # Generic fallback (still specific enough to add value)
    if level == "high":
        return "Multiple signals—your reflections and current timing—point to this moment as significant."
    elif level == "medium":
        return "Something in your recent experience is activating this theme."
    else:
        return "Current timing may be bringing this pattern into focus."


def _build_cross_lens_derivation(
    transit_themes: Any,
    cluster_data: Dict[str, Any],
    signals_extended: Dict[str, Any],
    user_profile: Optional[Dict[str, Any]],
    bazi_chart: Optional[Dict[str, Any]],
    pattern_id: str
) -> Dict[str, Any]:
    """
    Build structured cross-lens derivation showing convergence.
    
    V6: Enhanced to include Journal derivation and be more inclusive.
    
    Format per lens:
    Lens Name → plain language signal
    
    Only includes lenses that meaningfully contributed.
    """
    derivations = []
    debug_info = {"candidates": [], "included": [], "excluded": []}
    
    # 1. JOURNAL lens (NEW in V6 - check first since it's most personal)
    journal_signal = _get_journal_derivation(signals_extended, cluster_data, pattern_id)
    debug_info["candidates"].append({"lens": "Journal", "signal": journal_signal})
    if journal_signal:
        derivations.append({
            "lens": "Journal",
            "signal": journal_signal,
            "contributed": True,
        })
        debug_info["included"].append("Journal")
    else:
        debug_info["excluded"].append({"lens": "Journal", "reason": "no matching entries"})
    
    # 2. LIFELINE lens (from user's lifeline events)
    lifeline_signal = _get_lifeline_derivation(signals_extended, cluster_data, pattern_id)
    debug_info["candidates"].append({"lens": "Lifeline", "signal": lifeline_signal})
    if lifeline_signal:
        derivations.append({
            "lens": "Lifeline",
            "signal": lifeline_signal,
            "contributed": True,
        })
        debug_info["included"].append("Lifeline")
    else:
        debug_info["excluded"].append({"lens": "Lifeline", "reason": "no lifeline events or matches"})
    
    # 3. ASTROLOGY lens (timing context) - V8: Now pattern-specific with max 2 drivers
    astrology_data = _get_astrology_derivation(transit_themes, pattern_id)
    debug_info["candidates"].append({"lens": "Astrology", "data": astrology_data})
    
    if astrology_data:
        # V7: Astrology now returns a dict with signal, drivers, etc.
        if isinstance(astrology_data, dict):
            astrology_signal = astrology_data.get("signal", "")
            astrology_drivers = astrology_data.get("drivers", [])
            derivations.append({
                "lens": "Astrology",
                "signal": astrology_signal,
                "drivers": astrology_drivers,  # V7: Include individual drivers
                "driver_count": len(astrology_drivers),
                "contributed": True,
            })
        else:
            # Fallback for old string format
            derivations.append({
                "lens": "Astrology",
                "signal": astrology_data,
                "contributed": True,
            })
        debug_info["included"].append("Astrology")
    else:
        debug_info["excluded"].append({"lens": "Astrology", "reason": "no transit themes"})
    
    # 4. HUMAN DESIGN lens (if user has HD data)
    hd_signal = _get_human_design_derivation(user_profile, pattern_id)
    debug_info["candidates"].append({"lens": "Human Design", "signal": hd_signal})
    if hd_signal:
        derivations.append({
            "lens": "Human Design",
            "signal": hd_signal,
            "contributed": True,
        })
        debug_info["included"].append("Human Design")
    else:
        debug_info["excluded"].append({"lens": "Human Design", "reason": "no HD data in profile"})
    
    # 5. BAZI lens (if user has BaZi data)
    bazi_signal = _get_bazi_derivation(bazi_chart, user_profile)
    debug_info["candidates"].append({"lens": "BaZi", "signal": bazi_signal})
    if bazi_signal:
        derivations.append({
            "lens": "BaZi",
            "signal": bazi_signal,
            "contributed": True,
        })
        debug_info["included"].append("BaZi")
    else:
        debug_info["excluded"].append({"lens": "BaZi", "reason": "no BaZi chart data"})
    
    # Calculate convergence
    contributing_count = len([d for d in derivations if d.get("contributed")])
    
    # Log debug info
    print(f"[CrossLensDerivation] Candidates: {len(debug_info['candidates'])}")
    print(f"[CrossLensDerivation] Included: {debug_info['included']}")
    print(f"[CrossLensDerivation] Excluded: {[e['lens'] for e in debug_info['excluded']]}")
    
    return {
        "lenses": derivations,
        "convergence_count": contributing_count,
        "shows_convergence": contributing_count >= 2,
        "convergence_note": f"{contributing_count} system{'s' if contributing_count != 1 else ''} point{'s' if contributing_count == 1 else ''} to this theme" if contributing_count > 0 else None,
        "debug": debug_info,
    }
    contributing_count = len([d for d in derivations if d.get("contributed")])
    
    return {
        "lenses": derivations,
        "convergence_count": contributing_count,
        "shows_convergence": contributing_count >= 2,
        "convergence_note": f"{contributing_count} system{'s' if contributing_count != 1 else ''} point{'s' if contributing_count == 1 else ''} to this theme" if contributing_count > 0 else None,
    }


def _get_astrology_derivation(transit_themes: Any, pattern_id: str = "") -> Optional[Dict[str, Any]]:
    """
    Get Astrology derivation with ACTUAL transit drivers (not generic summaries).
    
    V8: Tighter filtering, max 2 drivers, pattern-specific relevance.
    
    Returns:
        Dict with:
        - signal: The combined plain English sentence
        - drivers: List of individual driver objects (max 2)
        - raw_indicators: The raw indicator keys for debugging
    """
    if not transit_themes:
        return None
    
    # Get raw indicators from transit themes
    raw_indicators = transit_themes.raw_indicators if hasattr(transit_themes, 'raw_indicators') else []
    lunar_phase = transit_themes.lunar_phase if hasattr(transit_themes, 'lunar_phase') else None
    
    # V8: Pattern-specific driver relevance mapping
    # Different patterns benefit from different timing contexts
    PATTERN_TIMING_RELEVANCE = {
        "relational_reopening": ["venus_active", "new_moon", "waxing_crescent"],
        "heart_thaw": ["venus_active", "new_moon", "waning_moon"],
        "threshold_standing": ["first_quarter", "equinox_window", "saturn_active"],
        "somethings_here": ["waxing_crescent", "mercury_active", "new_moon"],
        "safe_intimacy_returning": ["venus_active", "waxing_moon", "cancer_season"],
        "over_functioning_hero": ["mars_active", "first_quarter", "saturn_active"],
        "inner_critic_override": ["mercury_active", "waning_moon", "saturn_active"],
        "emotional_flooding": ["full_moon", "water_season", "neptune_active"],
        "avoidant_autopilot": ["mars_active", "mercury_retrograde", "waning_crescent"],
    }
    
    # V9: More specific, pattern-contextual driver translations
    # These explain WHY the timing matters for THIS pattern
    DRIVER_TRANSLATIONS = {
        # === LUNAR (most actionable) ===
        "new_moon": "New moon timing supports fresh starts—a good moment to begin something",
        "full_moon": "Full moon brings things to the surface—what's been building becomes visible",
        "waxing_crescent": "Waxing moon supports small forward steps—momentum is available",
        "waning_crescent": "Waning moon supports release—easier to let go of what's finished",
        "first_quarter": "First quarter moon brings decision energy—a natural crossroads",
        "last_quarter": "Last quarter moon supports reflection—time to assess what's working",
        "waxing_moon": "Moon is waxing—energy for forward motion is building",
        "waning_moon": "Moon is waning—energy favors completion over initiation",
        
        # === PLANETARY (only high-impact) ===
        "mercury_active": "Mercury timing supports clarity—easier to see and name things",
        "venus_active": "Venus timing brings warmth—connection feels more available",
        "mars_active": "Mars timing adds activation—easier to act on what you know",
        "saturn_active": "Saturn timing brings seriousness—commitments feel weightier",
        
        # === SPECIAL WINDOWS (only if truly active) ===
        "equinox_window": "Equinox marks a balance point—transitions feel more natural",
        "solstice_window": "Solstice marks a turning point—thresholds are highlighted",
        "eclipse_window": "Eclipse window creates revelation—hidden things surface",
        "mercury_retrograde": "Mercury retrograde invites review—better for reflection than action",
    }
    
    drivers = []
    
    # V8: Get pattern-relevant timing keys
    relevant_keys = PATTERN_TIMING_RELEVANCE.get(pattern_id, [])
    
    # 1. Check lunar phase FIRST (always relevant, max 1 lunar)
    if lunar_phase:
        lunar_key = lunar_phase.lower().replace(" ", "_")
        if lunar_key in DRIVER_TRANSLATIONS:
            is_relevant = not relevant_keys or lunar_key in relevant_keys
            drivers.append({
                "key": lunar_key,
                "text": DRIVER_TRANSLATIONS[lunar_key],
                "category": "lunar",
                "priority": 1 if is_relevant else 2,
                "relevance": "high" if is_relevant else "medium",
            })
    
    # 2. Check special windows (only include if actually active)
    special_windows = ["eclipse_window", "equinox_window", "solstice_window", "mercury_retrograde"]
    for window in special_windows:
        if window in raw_indicators and window in DRIVER_TRANSLATIONS:
            is_relevant = not relevant_keys or window in relevant_keys
            drivers.append({
                "key": window,
                "text": DRIVER_TRANSLATIONS[window],
                "category": "special",
                "priority": 1 if is_relevant else 3,
                "relevance": "high" if is_relevant else "low",
            })
    
    # 3. Check planetary (only if relevant to pattern)
    planetary_indicators = ["mercury_active", "venus_active", "mars_active", "saturn_active"]
    for indicator in planetary_indicators:
        if indicator in raw_indicators and indicator in DRIVER_TRANSLATIONS:
            is_relevant = not relevant_keys or indicator in relevant_keys
            if is_relevant:  # V8: Only include planetary if pattern-relevant
                drivers.append({
                    "key": indicator,
                    "text": DRIVER_TRANSLATIONS[indicator],
                    "category": "planetary",
                    "priority": 2,
                    "relevance": "high",
                })
    
    # If no drivers found, return None
    if not drivers:
        return None
    
    # V8: Sort by priority AND relevance, take max 2
    drivers.sort(key=lambda d: (d["priority"], 0 if d.get("relevance") == "high" else 1))
    
    # V8: Filter out low-relevance drivers if we have high-relevance ones
    high_relevance = [d for d in drivers if d.get("relevance") == "high"]
    if high_relevance:
        top_drivers = high_relevance[:2]
    else:
        top_drivers = drivers[:2]  # Max 2 drivers
    
    # Build combined signal (simpler when only 1-2 drivers)
    if len(top_drivers) == 1:
        combined_signal = top_drivers[0]["text"]
    else:
        combined_signal = f"{top_drivers[0]['text']}. {top_drivers[1]['text']}"
    
    return {
        "signal": combined_signal,
        "drivers": top_drivers,
        "raw_indicators": raw_indicators[:5],  # Limit for debugging
        "driver_count": len(top_drivers),
    }


def _get_human_design_derivation(
    user_profile: Optional[Dict[str, Any]], 
    pattern_id: str
) -> Optional[str]:
    """Get plain-language Human Design signal."""
    if not user_profile:
        return None
    
    # Check for HD data in profile
    hd_data = user_profile.get("human_design", {})
    if not hd_data:
        return None
    
    translations = LENS_SIGNAL_TRANSLATIONS.get("human_design", {})
    
    # Check for type-based signal
    hd_type = hd_data.get("type", "").lower()
    if hd_type and hd_type in translations:
        return translations[hd_type]
    
    # Check for defined centers relevant to pattern
    defined_centers = hd_data.get("defined_centers", [])
    
    # Map pattern domains to relevant centers
    pattern_center_relevance = {
        "emotional": ["solar_plexus", "heart"],
        "relational": ["g_center", "solar_plexus", "heart"],
        "behavioral": ["sacral", "root", "spleen"],
        "identity": ["g_center", "head", "ajna"],
        "pressure": ["root", "head"],
    }
    
    # Find relevant center signal
    for center in defined_centers:
        key = f"defined_{center.lower().replace(' ', '_')}"
        if key in translations:
            return translations[key]
    
    return None


def _get_bazi_derivation(
    bazi_chart: Optional[Dict[str, Any]],
    user_profile: Optional[Dict[str, Any]]
) -> Optional[str]:
    """Get plain-language BaZi signal."""
    # Try to get BaZi from chart or profile
    if not bazi_chart and user_profile:
        bazi_chart = user_profile.get("bazi_chart", {})
    
    if not bazi_chart:
        return None
    
    translations = LENS_SIGNAL_TRANSLATIONS.get("bazi", {})
    
    # Check element analysis
    element_analysis = bazi_chart.get("element_analysis", {})
    
    if element_analysis:
        dominant = element_analysis.get("dominant_element", "").lower()
        weak = element_analysis.get("weak_element", "").lower()
        
        # Check for dominant element signal
        dominant_key = f"{dominant}_dominant"
        if dominant_key in translations:
            return translations[dominant_key]
        
        # Check for weak element signal
        weak_key = f"{weak}_weak"
        if weak_key in translations:
            return translations[weak_key]
    
    # Check for general energy signal
    day_master = bazi_chart.get("day_master", {})
    if day_master:
        element = day_master.get("element", "").lower()
        element_key = f"{element}_dominant"
        if element_key in translations:
            return f"Your {element.title()} nature supports this pattern"
    
    return None


def _get_lifeline_derivation(
    signals_extended: Dict[str, Any],
    cluster_data: Dict[str, Any],
    pattern_id: str = ""
) -> Optional[str]:
    """
    Get specific, pattern-based Lifeline derivation (V8).
    
    Lifeline = repeated life patterns - should feel like recognition of history.
    """
    translations = LENS_SIGNAL_TRANSLATIONS.get("lifeline", {})
    
    # Check for lifeline evidence in cluster data
    lifeline_evidence = cluster_data.get("matched_themes_by_source", {}).get("lifeline", [])
    
    # Also check signals_extended memory
    memory = signals_extended.get("memory", {})
    lifeline_events = memory.get("lifeline_events", [])
    
    if not lifeline_evidence and not lifeline_events:
        return None
    
    # V8: Analyze lifeline event themes if available
    event_themes = []
    event_periods = []
    for event in lifeline_events[:5]:  # Look at recent significant events
        if isinstance(event, dict):
            title = event.get("title", "").lower()
            description = event.get("description", "").lower()
            combined = f"{title} {description}"
            
            # Extract recurring life themes
            if any(w in combined for w in ["relationship", "love", "partner", "connect"]):
                event_themes.append("relationships")
            if any(w in combined for w in ["career", "work", "job", "project"]):
                event_themes.append("work")
            if any(w in combined for w in ["move", "change", "transition", "shift"]):
                event_themes.append("transitions")
            if any(w in combined for w in ["loss", "end", "grief", "goodbye"]):
                event_themes.append("endings")
            if any(w in combined for w in ["begin", "start", "new", "first"]):
                event_themes.append("beginnings")
            if any(w in combined for w in ["realiz", "clarity", "understand", "insight"]):
                event_themes.append("insights")
            if any(w in combined for w in ["wait", "hesitat", "uncertain", "unsure"]):
                event_themes.append("waiting")
    
    # V8: Pattern-specific lifeline signals
    pattern_lifeline_phrases = {
        "relational_reopening": "Similar moments of opening up have preceded important connections before",
        "heart_thaw": "Past softening moments have often led to meaningful change",
        "threshold_standing": "You've stood at thresholds like this before—usually just before clarity arrived",
        "somethings_here": "This quiet sense of emergence has shown up before significant shifts",
        "safe_intimacy_returning": "Safety returning echoes earlier periods when walls came down",
        "over_functioning_hero": "This pattern of carrying too much has appeared before—often before a needed boundary",
        "inner_critic_override": "Your inner critic has surfaced at growth edges before",
        "emotional_flooding": "Strong emotional waves have preceded breakthroughs in your history",
        "avoidant_autopilot": "This pattern of stepping back resembles earlier protective responses",
    }
    
    # Try pattern-specific phrase first
    if pattern_id in pattern_lifeline_phrases and (lifeline_evidence or lifeline_events):
        return pattern_lifeline_phrases[pattern_id]
    
    # Check for pattern repetition score
    repetition_score = cluster_data.get("repetition_score", 0)
    
    if repetition_score >= 0.5:
        return "This theme has appeared at key turning points in your life before"
    
    # V8: Build specific signal from detected themes
    unique_themes = list(dict.fromkeys(event_themes))
    if unique_themes:
        theme_phrases = {
            "relationships": "relationship shifts",
            "work": "work or purpose questions",
            "transitions": "major transitions",
            "endings": "necessary endings",
            "beginnings": "fresh starts",
            "insights": "moments of clarity",
            "waiting": "periods of waiting",
        }
        detected = [theme_phrases.get(t) for t in unique_themes[:2] if t in theme_phrases]
        if detected:
            return f"Your lifeline shows this pattern often emerges around {detected[0]}"
    
    # Check for multiple lifeline matches
    if len(lifeline_evidence) >= 2:
        return "Multiple life experiences echo this theme"
    
    # If we have lifeline events but no explicit matches
    if lifeline_events and len(lifeline_events) > 0:
        return "Your life history contains echoes of this moment"
    
    return None


def _get_journal_derivation(
    signals_extended: Dict[str, Any],
    cluster_data: Dict[str, Any],
    pattern_id: str
) -> Optional[str]:
    """
    Get specific, content-based Journal derivation (V8).
    
    Journal = current inner experience - should feel personal and specific.
    """
    # Check for journal evidence in cluster data
    journal_evidence = cluster_data.get("matched_themes_by_source", {}).get("journal", [])
    
    # Also check signals_extended memory
    memory = signals_extended.get("memory", {})
    journal_entries = memory.get("journal_entries", [])
    
    # Get dominant theme and matched keywords from cluster data
    dominant_theme = cluster_data.get("dominant_theme", "")
    matched_keywords = cluster_data.get("matched_keywords", [])
    
    if not journal_evidence and not journal_entries:
        return None
    
    # V8: Extract actual themes/keywords from entries if available
    entry_themes = []
    for entry in journal_entries[:3]:  # Look at last 3 entries
        content = entry.get("content", "").lower() if isinstance(entry, dict) else str(entry).lower()
        # Extract emotional signals
        if any(w in content for w in ["open", "opening", "warmth", "warm"]):
            entry_themes.append("openness")
        if any(w in content for w in ["connect", "connection", "close", "closer"]):
            entry_themes.append("connection")
        if any(w in content for w in ["uncertain", "unsure", "hesitant", "cautious"]):
            entry_themes.append("hesitation")
        if any(w in content for w in ["clear", "clarity", "see", "understand"]):
            entry_themes.append("clarity")
        if any(w in content for w in ["feel", "feeling", "emotion", "emotional"]):
            entry_themes.append("emotion")
        if any(w in content for w in ["decide", "decision", "choice", "choosing"]):
            entry_themes.append("decision")
        if any(w in content for w in ["trust", "trusting", "faith", "believe"]):
            entry_themes.append("trust")
        if any(w in content for w in ["let go", "release", "letting go", "surrender"]):
            entry_themes.append("release")
    
    # Deduplicate themes
    unique_themes = list(dict.fromkeys(entry_themes))
    
    # V8: Generate specific signal based on detected themes
    journal_count = len(journal_evidence) if journal_evidence else len(journal_entries)
    
    if unique_themes:
        # Build specific signal from detected themes
        theme_phrases = {
            "openness": "warmth and openness",
            "connection": "a pull toward connection",
            "hesitation": "some caution or hesitation",
            "clarity": "growing clarity",
            "emotion": "emotional processing",
            "decision": "decisions taking shape",
            "trust": "questions around trust",
            "release": "readiness to let go",
        }
        
        detected_phrases = [theme_phrases.get(t) for t in unique_themes[:3] if t in theme_phrases]
        
        if len(detected_phrases) >= 2:
            return f"Recent writing points to {detected_phrases[0]} alongside {detected_phrases[1]}"
        elif detected_phrases:
            return f"Recent writing reflects {detected_phrases[0]}"
    
    # V8: Pattern-specific fallbacks
    pattern_journal_phrases = {
        "relational_reopening": "Recent entries touch on connection and the possibility of opening up",
        "heart_thaw": "Recent writing reflects softening and emotional availability",
        "threshold_standing": "Recent entries show awareness of standing at a decision point",
        "somethings_here": "Recent writing captures a sense of something emerging",
        "safe_intimacy_returning": "Recent entries explore safety and closeness",
        "over_functioning_hero": "Recent writing touches on doing too much or carrying others",
        "inner_critic_override": "Recent entries show self-critical thoughts surfacing",
        "emotional_flooding": "Recent writing reflects strong emotions moving through",
    }
    
    if pattern_id in pattern_journal_phrases:
        return pattern_journal_phrases[pattern_id]
    
    # Generic but still specific fallback
    if journal_count >= 3:
        return "Your recent writing repeatedly explores themes that align with this"
    elif journal_count >= 1:
        return "Something in recent writing touches on this theme"
    
    return None


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
    transit_themes: Any,  # TransitThemes dataclass
    cluster_data: Optional[Dict[str, Any]] = None
) -> tuple[str, Dict[str, float], Dict[str, Any]]:
    """
    Select the best pattern using SIGNALS-FIRST logic with V3 clustering.
    
    ARCHITECTURE (V3 - Multi-Signal Clustering):
    - Personal signals (journal, chat, lifeline) drive pattern selection
    - Multi-signal clustering weights patterns with broader evidence
    - Transit acts as amplifier/modulator, NOT gatekeeper
    - No hard transit gate - all patterns remain eligible
    
    V3 Scoring Factors:
    - Base signal alignment (keyword matching)
    - Theme category alignment (dominant theme match)
    - Evidence count weight (more evidence = higher score)
    - Source diversity weight (multi-source = higher score)
    - Repetition weight (repeated themes = higher score)
    - Transit amplification (secondary)
    
    Returns: (pattern_id, scores_dict, cluster_scores_dict)
    """
    from services.transit_theme_engine import TIMING_THEMES
    
    scores = {}
    cluster_scores_all = {}
    signal_strength = signals.get("signal_strength", "weak")
    
    # Compute cluster data if not provided
    if cluster_data is None:
        cluster_data = cluster_signal_themes(signals)
    
    # Determine if we're in fallback mode (sparse personal data)
    fallback_mode = signal_strength == "weak"
    
    # Detect dominant energy state from user signals
    dominant_energy = detect_dominant_energy_state(signals)
    
    logger.info(
        f"[PatternSelect] Mode: {'FALLBACK' if fallback_mode else 'NORMAL'}, "
        f"signal_strength={signal_strength}, dominant_energy={dominant_energy}, "
        f"dominant_theme={cluster_data.get('dominant_theme')}, "
        f"evidence_count={cluster_data.get('total_evidence_count')}"
    )
    
    # Check if transit themes favor opening
    opening_transit_themes = ["relational_harmony", "emotional_openness", "receptivity", 
                              "renewal_cycle", "reconnection_window", "softening_phase",
                              "integration_phase", "grounded_stability", "expansion"]
    
    transit_favors_opening = any(t in transit_themes.active_themes for t in opening_transit_themes)
    
    for pattern_id, template in PATTERN_TEMPLATES.items():
        # Calculate transit alignment score
        transit_score = score_pattern_transit_alignment(
            pattern_id,
            transit_themes.active_themes,
            transit_themes.theme_intensity
        )
        
        # V3: Calculate clustered signal score
        cluster_scores = score_pattern_with_clustering(pattern_id, signals, cluster_data)
        clustered_signal_score = cluster_scores["clustered_score"]
        cluster_scores_all[pattern_id] = cluster_scores
        
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
        
        # If transit favors opening, give modest boost to opening patterns
        if transit_favors_opening and pattern_type == "opening":
            energy_modifier *= 1.1  # Reduced from 1.15 - transit should modulate, not dominate
        
        # V3: SIGNALS-FIRST WEIGHTING with clustered score
        if fallback_mode:
            # Fallback: transit drives when personal data is sparse
            base_score = (clustered_signal_score * 0.30) + (transit_score * 0.70)
        else:
            # Normal: personal signals drive selection
            base_score = (clustered_signal_score * 0.75) + (transit_score * 0.25)
        
        final_score = base_score * energy_modifier
        
        scores[pattern_id] = {
            "final": final_score,
            "signal": clustered_signal_score,
            "base_signal": cluster_scores["base_score"],
            "transit": transit_score,
            "pattern_type": pattern_type,
            "energy_modifier": energy_modifier,
            "fallback_mode": fallback_mode,
            "signal_strength": signal_strength,
            "cluster_bonuses": {
                "theme_alignment": cluster_scores["theme_alignment"],
                "evidence_weight": cluster_scores["evidence_weight"],
                "diversity_weight": cluster_scores["diversity_weight"],
                "repetition_weight": cluster_scores["repetition_weight"],
            }
        }
        
        logger.debug(
            f"[PatternSelect] {pattern_id} ({pattern_type}): "
            f"final={final_score:.2f}, clustered_signal={clustered_signal_score:.2f}, transit={transit_score:.2f}, "
            f"modifier={energy_modifier:.2f}, mode={'fallback' if fallback_mode else 'normal'}"
        )
    
    # Select highest scoring pattern
    if not scores:
        # Fallback: no patterns evaluated (should not happen)
        logger.warning("[PatternSelect] No patterns scored, using fallback")
        return "somethings_here", {
            "final": 0.3, "signal": 0.3, "transit": 0.3, 
            "pattern_type": "neutral", "fallback_mode": True, "signal_strength": "weak"
        }
    
    # Get top 3 candidates for debug output
    sorted_patterns = sorted(scores.items(), key=lambda x: x[1]["final"], reverse=True)
    top_3_candidates = sorted_patterns[:3]
    
    logger.info(
        f"[PatternSelect] Top 3 candidates: "
        f"{[(p, round(s['final'], 3), round(s['signal'], 3), round(s['transit'], 3)) for p, s in top_3_candidates]}"
    )
    
    best_pattern = sorted_patterns[0][0]
    best_scores = scores[best_pattern]
    
    # Add top_candidates to return for debugging
    best_scores["top_candidates"] = [
        {"pattern_id": p, "final": round(s["final"], 3), "signal": round(s["signal"], 3), "transit": round(s["transit"], 3)}
        for p, s in top_3_candidates
    ]
    
    # V3: Return cluster data for the selected pattern
    best_cluster_scores = cluster_scores_all.get(best_pattern, {})
    
    return best_pattern, best_scores, {"cluster_data": cluster_data, "cluster_scores": best_cluster_scores}

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
    Generate a pattern mirror for the user using SIGNALS-FIRST logic (V2).
    
    V2 ARCHITECTURE:
    - Personal signals (journal, chat, lifeline) DRIVE pattern selection
    - Transit acts as AMPLIFIER only, not gatekeeper
    - Response clearly separates personal_pattern from timing_amplifier
    
    Scoring (V2):
    - Normal mode: signal=0.75, transit=0.25
    - Fallback mode (weak signals): signal=0.30, transit=0.70
    - No hard transit gate
    
    Response Structure (V2):
    - personal_pattern: what came from personal signals
    - timing_amplifier: what came from transit/timing
    - narrative: signals-first narrative structure
    - evidence: true evidence showing actual matches
    - debug: diagnostic data for validation
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
                cached_scores = cached.get("scores", {})
                cached_transit_score = cached_scores.get("transit", 0.4)
                timing_signals = generate_timing_signals(transit_themes, cached_transit_score)
                if timing_signals:
                    signals_by_source["timing"] = timing_signals
                
                # Generate timing context
                timing_context = generate_timing_context(transit_themes)
                
                # Compute personal activations for cached pattern
                user_profile = await get_user_profile(db, user_id)
                personal_activations = compute_personal_activations(
                    user_profile,
                    transit_themes.active_themes,
                    cached_transit_score
                )
                
                # Build unified narrative for cached pattern
                unified_narrative = cached.get("unified_narrative") or build_unified_narrative(
                    cached["pattern"],
                    signals_by_source,
                    timing_context,
                    personal_activations,
                    transit_themes.active_themes
                )
                
                # V2: Generate layered response for cached pattern
                cached_pattern_id = cached.get("pattern_id", "unknown")
                pattern_evidence = cached.get("pattern_evidence") or generate_true_evidence(
                    signals, cached_pattern_id, cached["pattern"]
                )
                
                fallback_mode = cached_scores.get("fallback_mode", False)
                signals_first_narrative = build_signals_first_narrative(
                    cached["pattern"],
                    pattern_evidence,
                    timing_context,
                    transit_themes.active_themes,
                    fallback_mode
                )
                
                personal_pattern = build_personal_pattern_layer(
                    cached["pattern"], signals, pattern_evidence, cached_scores
                )
                
                timing_amplifier = build_timing_amplifier_layer(
                    transit_themes, cached_scores, timing_context
                )
                
                # V5: Build two-layer output for cached response too
                cached_two_layer = build_two_layer_mirror_output(
                    pattern=cached["pattern"],
                    pattern_id=cached_pattern_id,
                    core_pattern_memory=cached.get("core_pattern_memory", {
                        "pattern_id": cached_pattern_id,
                        "pattern_title": cached["pattern"].get("title", ""),
                        "persistence_score": 0.7,
                        "memory_window_days": 60,
                    }),
                    daily_angle=cached.get("daily_angle", {
                        "angle_title": cached["pattern"].get("title", ""),
                        "angle_summary": cached["pattern"].get("what_you_may_be", ""),
                    }),
                    timing_amplifier=timing_amplifier,
                    cluster_data=cached.get("cluster_data", {}),
                    signals_extended={"memory": signals},
                    transit_themes=transit_themes,
                    user_profile=user_profile,
                    bazi_chart=None
                )
                
                return {
                    # ===== V5 TWO-LAYER OUTPUT =====
                    "two_layer_output": cached_two_layer,
                    
                    # ===== V2 LAYERED STRUCTURE =====
                    "personal_pattern": personal_pattern,
                    "timing_amplifier": timing_amplifier,
                    "narrative": signals_first_narrative,
                    "evidence": pattern_evidence,
                    
                    # ===== LEGACY FIELDS =====
                    "pattern": cached["pattern"],
                    "pattern_id": cached_pattern_id,
                    "cached": True,
                    "generated_at": cached["generated_at"],
                    "signal_strength": cached.get("signal_strength", "weak"),
                    "signals_by_source": signals_by_source,
                    "timing_context": timing_context,
                    "active_themes": transit_themes.active_themes[:3],
                    "scores": cached_scores,
                    "personal_activations": personal_activations,
                    "unified_narrative": unified_narrative,
                }
        except Exception as e:
            logger.warning(f"[PatternMirror] Cache check failed: {e}")
    
    # STEP 2: Aggregate user signals (V4: extended with two timescales)
    signals_extended = await aggregate_user_signals_extended(db, user_id, recent_days=7, memory_days=60)
    
    # Also get regular signals for backwards compatibility
    signals = await aggregate_user_signals(db, user_id)
    
    # STEP 2b: Compute signal clustering (V3/V4) using memory window
    # Build combined signals for clustering
    memory_signals = {
        "journal_entries": signals_extended.get("memory", {}).get("journal_entries", []),
        "chat_messages": signals_extended.get("memory", {}).get("chat_messages", []),
        "lifeline_events": signals_extended.get("memory", {}).get("lifeline_events", []),
        "signal_strength": signals_extended.get("signal_strength", "weak"),
    }
    cluster_data = cluster_signal_themes(memory_signals)
    
    # STEP 3: Select best pattern using SIGNALS-FIRST scoring with clustering (V3)
    selected_pattern_id, scores, v3_data = select_best_pattern(memory_signals, transit_themes, cluster_data)
    logger.info(
        f"[PatternMirror] Selected: {selected_pattern_id} "
        f"(final={scores['final']:.2f}, signal={scores['signal']:.2f}, transit={scores['transit']:.2f}, "
        f"mode={'fallback' if scores.get('fallback_mode') else 'normal'}, "
        f"evidence_count={cluster_data.get('total_evidence_count')}, "
        f"dominant_theme={cluster_data.get('dominant_theme')})"
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
    
    # STEP 5: Generate TRUE evidence (actual matches, not post-hoc)
    pattern_evidence = generate_true_evidence(signals, selected_pattern_id, pattern)
    
    # STEP 6: Generate signals by source (legacy, for backwards compatibility)
    signals_by_source = generate_signals_by_source(signals, pattern)
    
    # STEP 7: ALWAYS add timing signals (pass transit score for priority rule)
    transit_score = scores.get("transit", 0.0)
    timing_signals = generate_timing_signals(transit_themes, transit_score)
    if timing_signals:
        signals_by_source["timing"] = timing_signals
    
    # STEP 8: Generate timing context
    timing_context = generate_timing_context(transit_themes)
    
    # STEP 9: Compute personal activations (Venus Sequence mapping)
    user_profile = await get_user_profile(db, user_id)
    personal_activations = compute_personal_activations(
        user_profile,
        transit_themes.active_themes,
        transit_score
    )
    
    # STEP 10: Build SIGNALS-FIRST NARRATIVE (V2)
    fallback_mode = scores.get("fallback_mode", False)
    signals_first_narrative = build_signals_first_narrative(
        pattern,
        pattern_evidence,
        timing_context,
        transit_themes.active_themes,
        fallback_mode
    )
    
    # STEP 10b: Build legacy unified narrative (for backwards compatibility)
    unified_narrative = build_unified_narrative(
        pattern,
        signals_by_source,
        timing_context,
        personal_activations,
        transit_themes.active_themes
    )
    
    # STEP 11: Build V3 layered response structure
    
    # V3: Build personal pattern core using clustering
    cluster_scores = v3_data.get("cluster_scores", {})
    personal_pattern_core = build_personal_pattern_core(
        pattern, selected_pattern_id, cluster_data, cluster_scores, signals
    )
    
    # V3: Timing amplifier (enhanced)
    timing_amplifier = build_timing_amplifier_layer(
        transit_themes, scores, timing_context
    )
    # Add contribution level based on timing role
    timing_amplifier["contribution_level"] = "secondary" if not fallback_mode else "primary"
    timing_amplifier["top_timing_factors"] = transit_themes.active_themes[:3]
    
    # V3: Compute archetypal resonance from Gene Keys
    user_profile = await get_user_profile(db, user_id)
    archetypal_resonance = compute_archetypal_resonance(
        selected_pattern_id, pattern, user_profile, cluster_data
    )
    
    # V3: Build evidence panel
    evidence_panel = build_evidence_panel_v3(signals, cluster_data, pattern, selected_pattern_id)
    
    # V3: Build narrative with all layers
    v3_narrative = build_v3_narrative(personal_pattern_core, timing_amplifier, archetypal_resonance)
    
    # Legacy personal_pattern (for backwards compatibility)
    personal_pattern = build_personal_pattern_layer(
        pattern, signals, pattern_evidence, scores
    )
    
    # STEP 12: Compute debug data and selection_debug (V3/V4 enhanced)
    signal_only_ranking = compute_signal_only_ranking(memory_signals, transit_themes)
    final_ranking = scores.get("top_candidates", [])
    timing_impact = determine_timing_impact(signal_only_ranking, final_ranking, selected_pattern_id)
    
    # V4: Build core pattern memory and daily angle
    core_pattern_memory = build_core_pattern_memory(
        signals_extended, cluster_data, pattern, selected_pattern_id, cluster_scores
    )
    
    # V4: Select daily angle based on core + timing
    recent_signals = signals_extended.get("recent", {})
    daily_angle = select_daily_angle(
        core_pattern_memory, transit_themes, recent_signals, archetypal_resonance
    )
    
    # V4: Build evidence panel with multiple snippets
    evidence_panel_v4 = build_evidence_panel_v4(signals_extended, cluster_data)
    
    # V4: Build narrative with two-timescale model
    v4_narrative = build_v4_narrative(
        core_pattern_memory, daily_angle, timing_amplifier, archetypal_resonance
    )
    
    # V5: Build two-layer mirror output (Insight + Cross-Lens Proof)
    two_layer_output = build_two_layer_mirror_output(
        pattern=pattern,
        pattern_id=selected_pattern_id,
        core_pattern_memory=core_pattern_memory,
        daily_angle=daily_angle,
        timing_amplifier=timing_amplifier,
        cluster_data=cluster_data,
        signals_extended=signals_extended,
        transit_themes=transit_themes,
        user_profile=user_profile,
        bazi_chart=None  # Will be populated if available
    )
    
    # Selection debug - V4 enhanced with two-timescale data
    selection_debug = {
        "top_core_candidates_by_memory_score": signal_only_ranking[:3],
        "selected_core_pattern": core_pattern_memory.get("title"),
        "selected_daily_angle": daily_angle.get("angle_title"),
        "timing_influence_on_daily_angle": daily_angle.get("facet_scores", {}),
        "top_candidates_by_personal_score": signal_only_ranking[:3],
        "top_candidates_by_final_score": final_ranking[:3],
        "source_diversity_score": cluster_data.get("source_diversity_score", 0),
        "repetition_score": cluster_data.get("repetition_score", 0),
        "evidence_count": cluster_data.get("total_evidence_count", 0),
        "dominant_theme": cluster_data.get("dominant_theme"),
        "fallback_mode": fallback_mode,
        "timing_changed_rank": timing_impact.get("timing_changed_winner", False),
        "archetypal_resonance_used": archetypal_resonance is not None,
        "cluster_bonuses": scores.get("cluster_bonuses", {}),
        "snippet_count_by_source": evidence_panel_v4.get("snippet_count_by_source", {}),
        "did_single_entry_dominate": evidence_panel_v4.get("single_entry_dominated", False),
        "why_single_entry_dominated": evidence_panel_v4.get("why_single_dominated"),
        "memory_window_days": signals_extended.get("memory_window_days", 60),
    }
    
    debug_data = {
        "signal_only_top3": signal_only_ranking[:3],
        "final_top3": final_ranking[:3],
        "timing_impact": timing_impact,
        "fallback_mode": fallback_mode,
        "signal_strength": signals_extended.get("signal_strength", "weak"),
        "cluster_data": {
            "theme_counts": cluster_data.get("theme_counts", {}),
            "source_distribution": cluster_data.get("source_distribution", {}),
        },
    }
    
    # STEP 13: Cache the result
    try:
        await db.pattern_mirror_cache.update_one(
            {"user_id": user_id, "date": datetime.now(timezone.utc).strftime('%Y-%m-%d')},
            {
                "$set": {
                    "pattern": pattern,
                    "signal_strength": signals_extended.get("signal_strength", "weak"),
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "pattern_id": selected_pattern_id,
                    "scores": scores,
                    "personal_activations": personal_activations,
                    "unified_narrative": unified_narrative,
                    "pattern_evidence": pattern_evidence,
                    "core_pattern_memory": core_pattern_memory,
                    "daily_angle": daily_angle,
                }
            },
            upsert=True
        )
    except Exception as e:
        logger.warning(f"[PatternMirror] Cache write failed: {e}")
    
    # V4 RESPONSE: Two-timescale structure with core memory and daily angle
    return {
        # ===== V5 TWO-LAYER MIRROR OUTPUT =====
        "two_layer_output": two_layer_output,
        
        # ===== V4 LAYERED STRUCTURE =====
        "pattern_card_v4": {
            "core_pattern_memory": core_pattern_memory,
            "daily_angle": daily_angle,
            "timing_amplifier": timing_amplifier,
            "archetypal_resonance": archetypal_resonance,
            "evidence_panel": evidence_panel_v4,
            "selection_debug": selection_debug,
        },
        
        # ===== V4 NARRATIVE =====
        "narrative": v4_narrative,
        
        # ===== V3 COMPATIBILITY =====
        "pattern_card_v3": {
            "personal_pattern_core": personal_pattern_core,
            "timing_amplifier": timing_amplifier,
            "archetypal_resonance": archetypal_resonance,
            "evidence_panel": evidence_panel,
            "selection_debug": selection_debug,
        },
        
        # ===== V2 COMPATIBILITY =====
        "personal_pattern": personal_pattern,
        "timing_amplifier": timing_amplifier,
        "evidence": pattern_evidence,
        "selection_debug": selection_debug,
        "debug": debug_data,
        
        # ===== LEGACY FIELDS (backwards compatibility) =====
        "pattern": pattern,
        "pattern_id": selected_pattern_id,
        "cached": False,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "signal_strength": signals_extended.get("signal_strength", "weak"),
        "signals_by_source": signals_by_source,
        "timing_context": timing_context,
        "active_themes": transit_themes.active_themes[:3],
        "scores": scores,
        "personal_activations": personal_activations,
        "unified_narrative": unified_narrative,
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
