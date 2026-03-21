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
                
                return {
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
    
    # STEP 2: Aggregate user signals
    signals = await aggregate_user_signals(db, user_id)
    
    # STEP 2b: Compute signal clustering (V3)
    cluster_data = cluster_signal_themes(signals)
    
    # STEP 3: Select best pattern using SIGNALS-FIRST scoring with clustering (V3)
    selected_pattern_id, scores, v3_data = select_best_pattern(signals, transit_themes, cluster_data)
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
    
    # STEP 12: Compute debug data and selection_debug (V3 enhanced)
    signal_only_ranking = compute_signal_only_ranking(signals, transit_themes)
    final_ranking = scores.get("top_candidates", [])
    timing_impact = determine_timing_impact(signal_only_ranking, final_ranking, selected_pattern_id)
    
    # Selection debug - V3 enhanced with clustering data
    selection_debug = {
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
    }
    
    debug_data = {
        "signal_only_top3": signal_only_ranking[:3],
        "final_top3": final_ranking[:3],
        "timing_impact": timing_impact,
        "fallback_mode": fallback_mode,
        "signal_strength": signals["signal_strength"],
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
                    "signal_strength": signals["signal_strength"],
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "pattern_id": selected_pattern_id,
                    "scores": scores,
                    "personal_activations": personal_activations,
                    "unified_narrative": unified_narrative,
                    "pattern_evidence": pattern_evidence,
                }
            },
            upsert=True
        )
    except Exception as e:
        logger.warning(f"[PatternMirror] Cache write failed: {e}")
    
    # V3 RESPONSE: Three-layer structure with clustering and archetypal resonance
    return {
        # ===== V3 LAYERED STRUCTURE =====
        "pattern_card_v3": {
            "personal_pattern_core": personal_pattern_core,
            "timing_amplifier": timing_amplifier,
            "archetypal_resonance": archetypal_resonance,
            "evidence_panel": evidence_panel,
            "selection_debug": selection_debug,
        },
        
        # ===== V3 NARRATIVE =====
        "narrative": v3_narrative,
        
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
        "signal_strength": signals["signal_strength"],
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
