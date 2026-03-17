"""
Pattern Archetype Engine v0.1

Transforms structured pattern signals into named archetypes with:
- Clear narrative synthesis
- Evidence-based explanation
- Current relevance

Design principles:
- Grounded, not mystical
- Specific, not vague
- Emotionally precise
- Evidence-based
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
from collections import Counter

logger = logging.getLogger(__name__)

# =============================================================================
# ARCHETYPE LIBRARY (v0.1)
# =============================================================================

ARCHETYPE_LIBRARY = {
    "phoenix": {
        "id": "phoenix",
        "name": "Phoenix",
        "icon": "🔥",
        "description": "A pattern of breakdown, reinvention, and stronger re-emergence.",
        "short_description": "Rise through transformation",
        "signals": {
            "lifeline": ["turning point", "career", "restart", "transition", "transformation", "crisis", "rebuild", "new beginning"],
            "patterns": ["recurring", "growth_transformation", "identity_direction"],
            "journal": ["reinvent", "restart", "burnout", "fresh start", "new chapter", "rebuild", "start over"],
            "lunar": ["release", "decision", "pivot", "change", "transform"]
        },
        "narrative_template": {
            "summary": "You appear to move through cycles of build, rupture, and reinvention. What others might see as setbacks, you transform into fuel for rebuilding stronger.",
            "why_patterns": [
                "High-impact turning points have reshaped your direction multiple times",
                "Periods of pressure or crisis often precede significant new beginnings",
                "Recent reflections echo earlier reinvention themes"
            ],
            "current_expression": "This pattern may be showing up in how you approach current transitions—not as endings, but as opportunities to rebuild with more clarity.",
            "reflection_question": "What are you ready to release in order to rebuild more intentionally?"
        }
    },
    
    "builder_under_pressure": {
        "id": "builder_under_pressure",
        "name": "Builder Under Pressure",
        "icon": "🏗️",
        "description": "Growth through challenge. You build your strongest foundations when facing difficulty.",
        "short_description": "Strength through challenge",
        "signals": {
            "lifeline": ["challenge", "achievement", "career", "work", "professional", "milestone", "pressure"],
            "patterns": ["expression_action", "pressure_stress", "work_purpose"],
            "journal": ["pressure", "stress", "build", "achieve", "work", "challenge", "push through"],
            "lunar": ["tension", "effort", "commitment", "push"]
        },
        "narrative_template": {
            "summary": "You tend to create your most meaningful structures when under pressure. Challenge doesn't break you—it focuses you.",
            "why_patterns": [
                "Major achievements in your timeline often follow periods of intensity",
                "Your career or work signals show building through difficulty",
                "Stress patterns correlate with eventual breakthroughs"
            ],
            "current_expression": "Right now, any pressure you're feeling might be the necessary friction that shapes something lasting.",
            "reflection_question": "What structure are you being called to build, even when conditions feel difficult?"
        }
    },
    
    "reinventor": {
        "id": "reinventor",
        "name": "The Reinventor",
        "icon": "🔄",
        "description": "Multiple identity shifts across life. You regularly shed old versions of yourself.",
        "short_description": "Serial self-transformation",
        "signals": {
            "lifeline": ["identity", "transformation", "move", "relocation", "career", "change", "new", "different"],
            "patterns": ["identity_direction", "growth_transformation"],
            "journal": ["change", "different", "new version", "who I am", "becoming", "evolve"],
            "lunar": ["identity", "change", "who", "becoming"]
        },
        "narrative_template": {
            "summary": "You've lived multiple lives within this one. Each major shift wasn't about abandoning yourself—it was about becoming more yourself.",
            "why_patterns": [
                "Your lifeline shows distinct chapters with different focuses",
                "Identity and direction signals are consistently active",
                "Recent reflections touch on themes of personal evolution"
            ],
            "current_expression": "You may be in the early stages of another reinvention, even if you can't fully see what's forming yet.",
            "reflection_question": "What version of yourself is trying to emerge right now?"
        }
    },
    
    "seeker": {
        "id": "seeker",
        "name": "The Seeker",
        "icon": "🧭",
        "description": "Driven by exploration and the search for meaning. Always moving toward something.",
        "short_description": "Exploration and meaning",
        "signals": {
            "lifeline": ["move", "travel", "education", "learning", "new", "exploration", "search"],
            "patterns": ["mind_meaning", "identity_direction"],
            "journal": ["searching", "wondering", "meaning", "purpose", "why", "explore", "discover"],
            "lunar": ["question", "explore", "meaning", "purpose", "direction"]
        },
        "narrative_template": {
            "summary": "Your life pattern shows a consistent pull toward exploration—whether geographical, intellectual, or spiritual. You seek rather than settle.",
            "why_patterns": [
                "Movement and change appear frequently in your timeline",
                "Learning and growth signals are strongly present",
                "Reflections often touch on questions of meaning and direction"
            ],
            "current_expression": "What you're currently exploring may feel like restlessness, but it's actually your natural pattern of growth through seeking.",
            "reflection_question": "What question are you truly trying to answer right now?"
        }
    },
    
    "stabilizer": {
        "id": "stabilizer",
        "name": "The Stabilizer",
        "icon": "⚓",
        "description": "Creating consistency and grounding. You build foundations others can rely on.",
        "short_description": "Grounding through consistency",
        "signals": {
            "lifeline": ["family", "home", "relationship", "marriage", "stability", "steady", "consistent"],
            "patterns": ["relationships_boundaries", "emotional_landscape"],
            "journal": ["stable", "ground", "secure", "home", "foundation", "steady", "reliable"],
            "lunar": ["steady", "consistent", "ground", "security"]
        },
        "narrative_template": {
            "summary": "You create stability not by avoiding change, but by being the grounding force through it. Others often rely on your consistency.",
            "why_patterns": [
                "Relationship and home signals show a pattern of building foundations",
                "Your emotional landscape tends toward steadiness",
                "Your timeline shows commitment to long-term structures"
            ],
            "current_expression": "Your current stability isn't stagnation—it's the foundation that makes other growth possible.",
            "reflection_question": "What foundation have you built that you might be undervaluing?"
        }
    },
    
    "protector": {
        "id": "protector",
        "name": "The Protector",
        "icon": "🛡️",
        "description": "Driven by responsibility and care. You carry weight so others don't have to.",
        "short_description": "Responsibility and care",
        "signals": {
            "lifeline": ["family", "responsibility", "care", "duty", "support", "protect", "children"],
            "patterns": ["relationships_boundaries", "pressure_stress"],
            "journal": ["responsible", "care", "protect", "others", "duty", "support", "help"],
            "lunar": ["responsibility", "others", "care", "protect"]
        },
        "narrative_template": {
            "summary": "You take on responsibility naturally—often more than your share. Protecting and supporting others is woven into how you move through life.",
            "why_patterns": [
                "Family and responsibility signals appear throughout your timeline",
                "Your patterns show consistent care for others' wellbeing",
                "Reflections often center on duty and support themes"
            ],
            "current_expression": "The weight you're currently carrying might need to be redistributed—protection doesn't require self-sacrifice.",
            "reflection_question": "What would it look like to protect yourself as fiercely as you protect others?"
        }
    },
    
    "breakthrough_artist": {
        "id": "breakthrough_artist",
        "name": "Breakthrough Artist",
        "icon": "💫",
        "description": "Creative and expressive cycles. Periods of intense creation followed by integration.",
        "short_description": "Creative expression cycles",
        "signals": {
            "lifeline": ["creative", "expression", "art", "project", "achievement", "breakthrough", "launch"],
            "patterns": ["expression_action", "timing_readiness"],
            "journal": ["create", "express", "make", "build", "breakthrough", "inspired", "flow"],
            "lunar": ["create", "express", "flow", "inspiration", "emergence"]
        },
        "narrative_template": {
            "summary": "Your life moves in creative cycles—periods of intense expression followed by quieter integration. Your breakthroughs come through making, not just thinking.",
            "why_patterns": [
                "Expression and action signals cluster around significant life moments",
                "Your timeline shows bursts of creative or productive energy",
                "Reflections often touch on creation and emergence themes"
            ],
            "current_expression": "You may be in either a building phase or an integration phase—both are part of your natural creative rhythm.",
            "reflection_question": "What is waiting to be expressed that you've been holding back?"
        }
    },
    
    "threshold_walker": {
        "id": "threshold_walker",
        "name": "Threshold Walker",
        "icon": "🚪",
        "description": "Drawn to major life transitions. You navigate liminal spaces with unusual comfort.",
        "short_description": "Navigator of transitions",
        "signals": {
            "lifeline": ["transition", "turning point", "milestone", "major", "life change", "threshold", "between"],
            "patterns": ["growth_transformation", "timing_readiness"],
            "journal": ["transition", "between", "crossing", "threshold", "next phase", "change"],
            "lunar": ["transition", "threshold", "crossing", "between", "phase"]
        },
        "narrative_template": {
            "summary": "You're comfortable in doorways—the spaces between what was and what's coming. Many people rush through transitions; you know how to be in them.",
            "why_patterns": [
                "Major life transitions appear regularly in your timeline",
                "Your patterns show active engagement with change rather than resistance",
                "Recent reflections suggest you may be in or approaching a threshold"
            ],
            "current_expression": "If you're feeling 'between' right now, that's not a problem to solve—it's your natural territory.",
            "reflection_question": "What threshold are you standing at that you haven't fully acknowledged?"
        }
    },
    
    "expansion_through_disruption": {
        "id": "expansion_through_disruption",
        "name": "Expansion Through Disruption",
        "icon": "⚡",
        "description": "Growth comes through unexpected changes. Disruption opens doors you couldn't have planned.",
        "short_description": "Growth through the unexpected",
        "signals": {
            "lifeline": ["unexpected", "crisis", "disruption", "surprise", "sudden", "unplanned", "shock"],
            "patterns": ["growth_transformation", "pressure_stress"],
            "journal": ["unexpected", "surprised", "didn't plan", "sudden", "disruption", "change"],
            "lunar": ["unexpected", "surprise", "shift", "disruption"]
        },
        "narrative_template": {
            "summary": "Your most significant growth has often come through unexpected disruption. What seemed like chaos at the time created openings you couldn't have planned.",
            "why_patterns": [
                "Key turning points in your timeline were often unplanned",
                "Disruption patterns correlate with expansion in your signals",
                "Reflections show you've learned to work with rather than against change"
            ],
            "current_expression": "Any current disruption might be less random than it seems—it could be creating space for something that couldn't fit before.",
            "reflection_question": "What opportunity might be hiding inside your current disruption?"
        }
    },
    
    "quiet_endurer": {
        "id": "quiet_endurer",
        "name": "The Quiet Endurer",
        "icon": "🌱",
        "description": "Strength through persistence. You outlast rather than overpower.",
        "short_description": "Persistence and resilience",
        "signals": {
            "lifeline": ["persistent", "steady", "long-term", "endure", "continue", "patience", "gradual"],
            "patterns": ["emotional_landscape", "relationships_boundaries"],
            "journal": ["patience", "persist", "continue", "keep going", "endure", "steady", "wait"],
            "lunar": ["patience", "waiting", "persistence", "steady", "continue"]
        },
        "narrative_template": {
            "summary": "You don't force outcomes—you outlast obstacles. Your strength is in persistence rather than dramatic action.",
            "why_patterns": [
                "Your timeline shows gradual building rather than sudden leaps",
                "Emotional stability signals suggest deep resilience",
                "Reflections often touch on patience and persistence themes"
            ],
            "current_expression": "What feels slow right now might actually be exactly the pace your pattern requires for lasting results.",
            "reflection_question": "Where is your persistence already paying off in ways you haven't noticed?"
        }
    },
    
    "weaver": {
        "id": "weaver",
        "name": "The Weaver",
        "icon": "🕸️",
        "description": "Creating connections and patterns. You see and build relationships between disparate elements.",
        "short_description": "Connection and synthesis",
        "signals": {
            "lifeline": ["relationship", "connect", "network", "community", "bridge", "bring together"],
            "patterns": ["relationships_boundaries", "expression_action"],
            "journal": ["connect", "relationship", "together", "bridge", "link", "weave", "synthesis"],
            "lunar": ["connection", "relationship", "together", "bridge"]
        },
        "narrative_template": {
            "summary": "You naturally see connections others miss. Your life pattern shows building bridges—between people, ideas, or worlds that seemed separate.",
            "why_patterns": [
                "Relationship signals appear consistently across your timeline",
                "Your patterns show synthesis and connection-making",
                "Reflections often touch on bringing things or people together"
            ],
            "current_expression": "The connections you're making right now might seem small, but they could be part of a larger pattern you'll see later.",
            "reflection_question": "What disparate elements in your life are asking to be connected?"
        }
    },
    
    "emergence_keeper": {
        "id": "emergence_keeper",
        "name": "Emergence Keeper",
        "icon": "🌅",
        "description": "Present at beginnings. You often find yourself at the start of new things.",
        "short_description": "Present at new beginnings",
        "signals": {
            "lifeline": ["new", "start", "beginning", "first", "launch", "initiate", "pioneer"],
            "patterns": ["expression_action", "timing_readiness"],
            "journal": ["new beginning", "start", "first", "emergence", "dawn", "initiate"],
            "lunar": ["new", "beginning", "start", "emergence", "initiate"]
        },
        "narrative_template": {
            "summary": "You have an affinity for beginnings. New projects, new relationships, new chapters—you're drawn to what's just starting to emerge.",
            "why_patterns": [
                "Your timeline shows you at the start of many significant ventures",
                "Timing and expression signals suggest sensitivity to emergence",
                "Reflections often center on new beginnings and fresh starts"
            ],
            "current_expression": "Something new may be trying to emerge through you right now. Your pattern suggests you know how to receive it.",
            "reflection_question": "What new beginning is asking for your attention?"
        }
    }
}


# =============================================================================
# SIGNAL WEIGHTS
# =============================================================================

SIGNAL_WEIGHTS = {
    "lifeline": 3,
    "journal": 3,
    "patterns": 2,
    "lunar": 1
}


# =============================================================================
# ARCHETYPE SCORING ENGINE
# =============================================================================

def score_archetypes(
    lifeline_events: List[dict] = None,
    pattern_domains: List[dict] = None,
    signals: List[dict] = None,
    journal_entries: List[dict] = None,
    lunar_reflections: List[dict] = None
) -> List[Dict[str, Any]]:
    """
    Score all archetypes based on user data.
    
    Args:
        lifeline_events: Lifeline events from user's timeline
        pattern_domains: Active pattern domains with signals
        signals: Aggregated pattern signals
        journal_entries: Journal entries
        lunar_reflections: Lunar decision journal entries
    
    Returns:
        List of archetypes with scores, sorted by score descending
    """
    archetype_scores = {}
    
    # Initialize scores
    for arch_id in ARCHETYPE_LIBRARY:
        archetype_scores[arch_id] = {
            "raw_score": 0,
            "matches": {
                "lifeline": [],
                "patterns": [],
                "journal": [],
                "lunar": []
            }
        }
    
    # Score from Lifeline events
    if lifeline_events:
        for event in lifeline_events:
            event_text = f"{event.get('title', '')} {event.get('description', '')} {event.get('category', '')}".lower()
            
            for arch_id, archetype in ARCHETYPE_LIBRARY.items():
                for signal in archetype["signals"].get("lifeline", []):
                    if signal.lower() in event_text:
                        archetype_scores[arch_id]["raw_score"] += SIGNAL_WEIGHTS["lifeline"]
                        archetype_scores[arch_id]["matches"]["lifeline"].append(signal)
    
    # Score from pattern domains
    if pattern_domains:
        for domain in pattern_domains:
            domain_id = domain.get("category_id") or domain.get("domain", "")
            strength = domain.get("signal_strength", "present")
            
            for arch_id, archetype in ARCHETYPE_LIBRARY.items():
                for pattern_signal in archetype["signals"].get("patterns", []):
                    if pattern_signal.lower() in domain_id.lower():
                        weight = SIGNAL_WEIGHTS["patterns"]
                        # Boost for strong signals
                        if strength in ["recurring", "strong"]:
                            weight *= 1.5
                        archetype_scores[arch_id]["raw_score"] += weight
                        archetype_scores[arch_id]["matches"]["patterns"].append(domain_id)
    
    # Score from aggregated signals
    if signals:
        for signal in signals:
            signal_text = f"{signal.get('preview', '')} {' '.join(signal.get('tags', []))}".lower()
            source_type = signal.get("source_type", "").lower()
            
            for arch_id, archetype in ARCHETYPE_LIBRARY.items():
                # Check pattern signals
                for pattern_signal in archetype["signals"].get("patterns", []):
                    if pattern_signal.lower() in signal_text:
                        archetype_scores[arch_id]["raw_score"] += SIGNAL_WEIGHTS["patterns"]
                        archetype_scores[arch_id]["matches"]["patterns"].append(signal.get("preview", "")[:30])
    
    # Score from journal entries
    if journal_entries:
        for entry in journal_entries:
            entry_text = f"{entry.get('content', '')} {entry.get('mood', '')} {' '.join(entry.get('topics', []))}".lower()
            
            for arch_id, archetype in ARCHETYPE_LIBRARY.items():
                for signal in archetype["signals"].get("journal", []):
                    if signal.lower() in entry_text:
                        archetype_scores[arch_id]["raw_score"] += SIGNAL_WEIGHTS["journal"]
                        archetype_scores[arch_id]["matches"]["journal"].append(signal)
    
    # Score from lunar reflections
    if lunar_reflections:
        for reflection in lunar_reflections:
            reflection_text = f"{reflection.get('content', '')} {reflection.get('insight', '')}".lower()
            
            for arch_id, archetype in ARCHETYPE_LIBRARY.items():
                for signal in archetype["signals"].get("lunar", []):
                    if signal.lower() in reflection_text:
                        archetype_scores[arch_id]["raw_score"] += SIGNAL_WEIGHTS["lunar"]
                        archetype_scores[arch_id]["matches"]["lunar"].append(signal)
    
    # Normalize scores and build result
    max_score = max((s["raw_score"] for s in archetype_scores.values()), default=1)
    if max_score == 0:
        max_score = 1
    
    results = []
    for arch_id, score_data in archetype_scores.items():
        archetype = ARCHETYPE_LIBRARY[arch_id]
        normalized_score = round(score_data["raw_score"] / max_score, 2)
        
        # Count unique evidence sources
        evidence_count = sum(len(set(m)) for m in score_data["matches"].values())
        
        results.append({
            "archetype_id": arch_id,
            "archetype": archetype["name"],
            "icon": archetype["icon"],
            "description": archetype["description"],
            "short_description": archetype["short_description"],
            "score": normalized_score,
            "raw_score": score_data["raw_score"],
            "evidence_count": evidence_count,
            "matches": {
                k: list(set(v))[:3] for k, v in score_data["matches"].items()
            }
        })
    
    # Sort by score descending
    results.sort(key=lambda x: (-x["score"], -x["evidence_count"]))
    
    return results


def get_primary_archetypes(scored_archetypes: List[dict]) -> Tuple[Optional[dict], Optional[dict], float]:
    """
    Get primary and secondary archetypes with confidence score.
    
    Args:
        scored_archetypes: List of scored archetypes
    
    Returns:
        Tuple of (primary, secondary, confidence)
    """
    if not scored_archetypes:
        return None, None, 0.0
    
    primary = scored_archetypes[0] if scored_archetypes else None
    secondary = scored_archetypes[1] if len(scored_archetypes) > 1 else None
    
    # Calculate confidence based on:
    # 1. How much higher primary is than secondary
    # 2. Absolute score of primary
    # 3. Evidence count
    if primary:
        score_gap = primary["score"] - (secondary["score"] if secondary else 0)
        evidence_factor = min(1.0, primary["evidence_count"] / 10)
        confidence = (primary["score"] * 0.5 + score_gap * 0.3 + evidence_factor * 0.2)
        confidence = round(min(1.0, confidence), 2)
    else:
        confidence = 0.0
    
    return primary, secondary, confidence


# =============================================================================
# NARRATIVE GENERATION
# =============================================================================

def generate_archetype_narrative(
    archetype_id: str,
    user_data: Dict[str, Any],
    scored_archetype: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate personalized narrative for an archetype.
    
    Args:
        archetype_id: ID of the archetype
        user_data: User's data (lifeline events, signals, etc.)
        scored_archetype: The scored archetype with matches
    
    Returns:
        Narrative dictionary with headline, summary, why_patterns, etc.
    """
    archetype = ARCHETYPE_LIBRARY.get(archetype_id)
    if not archetype:
        return None
    
    template = archetype["narrative_template"]
    matches = scored_archetype.get("matches", {})
    
    # Build evidence-based "why this pattern" list
    why_patterns = []
    
    # Check lifeline matches
    lifeline_matches = matches.get("lifeline", [])
    if lifeline_matches:
        themes = ", ".join(lifeline_matches[:2])
        why_patterns.append(f"Your life story shows clear {themes} themes")
    
    # Check pattern domain matches
    pattern_matches = matches.get("patterns", [])
    if pattern_matches:
        domains = [p.replace("_", " ").title() for p in pattern_matches[:2]]
        if domains:
            why_patterns.append(f"Active patterns in: {', '.join(domains)}")
    
    # Check journal/lunar matches
    reflection_matches = matches.get("journal", []) + matches.get("lunar", [])
    if reflection_matches:
        themes = ", ".join(list(set(reflection_matches))[:2])
        why_patterns.append(f"Recent reflections echo these themes: {themes}")
    
    # Use template patterns if we don't have enough evidence
    if len(why_patterns) < 2:
        why_patterns.extend(template["why_patterns"][:3 - len(why_patterns)])
    
    # Generate current expression based on active signals
    current_expression = template["current_expression"]
    
    # Check for recent activity indicators
    lifeline_events = user_data.get("lifeline_events", [])
    if lifeline_events:
        recent_years = [e.get("year") for e in lifeline_events if e.get("year")]
        if recent_years:
            latest_year = max(recent_years)
            current_year = datetime.now().year
            if current_year - latest_year <= 3:
                current_expression = f"Recent events in your Lifeline suggest this pattern may be actively expressing itself. {template['current_expression']}"
    
    return {
        "headline": f"A {archetype['name']} Pattern",
        "icon": archetype["icon"],
        "summary": template["summary"],
        "short_description": archetype["short_description"],
        "why_this_pattern": why_patterns[:3],
        "current_expression": current_expression,
        "reflection_question": template["reflection_question"],
        "evidence_sources": {
            "lifeline": len(matches.get("lifeline", [])),
            "patterns": len(matches.get("patterns", [])),
            "journal": len(matches.get("journal", [])),
            "lunar": len(matches.get("lunar", []))
        }
    }


# =============================================================================
# MAIN API FUNCTION
# =============================================================================

async def get_user_archetype(
    db,
    user_id: str
) -> Dict[str, Any]:
    """
    Get archetype analysis for a user.
    
    Args:
        db: Database connection
        user_id: User ID
    
    Returns:
        Complete archetype analysis with primary/secondary archetypes and narratives
    """
    logger.info(f"[Archetype] Computing archetype for user {user_id}")
    
    # Fetch user data
    lifeline_events = []
    try:
        lifeline_events = await db.lifeline_events.find(
            {"user_id": user_id}
        ).sort("year", -1).limit(50).to_list(50)
    except Exception as e:
        logger.debug(f"[Archetype] Could not load lifeline: {e}")
    
    # Fetch pattern domains from pattern graph
    pattern_domains = []
    try:
        from services.pattern_graph import aggregate_pattern_graph
        graph = aggregate_pattern_graph(lifeline_events=lifeline_events)
        pattern_domains = graph.get("categories", [])
    except Exception as e:
        logger.debug(f"[Archetype] Could not load pattern graph: {e}")
    
    # Fetch aggregated signals
    signals = []
    try:
        from services.pattern_engine import get_user_pattern_signals
        signals = await get_user_pattern_signals(db, user_id, limit=100)
    except Exception as e:
        logger.debug(f"[Archetype] Could not load signals: {e}")
    
    # Fetch journal entries
    journal_entries = []
    try:
        journal_entries = await db.journal.find(
            {"user_id": user_id}
        ).sort("timestamp", -1).limit(20).to_list(20)
    except Exception as e:
        logger.debug(f"[Archetype] Could not load journal: {e}")
    
    # Fetch lunar reflections
    lunar_reflections = []
    try:
        lunar_reflections = await db.lunar_journal.find(
            {"user_id": user_id}
        ).sort("created_at", -1).limit(30).to_list(30)
    except Exception as e:
        logger.debug(f"[Archetype] Could not load lunar: {e}")
    
    # Score archetypes
    scored_archetypes = score_archetypes(
        lifeline_events=lifeline_events,
        pattern_domains=pattern_domains,
        signals=signals,
        journal_entries=journal_entries,
        lunar_reflections=lunar_reflections
    )
    
    # Get primary and secondary
    primary, secondary, confidence = get_primary_archetypes(scored_archetypes)
    
    # Build user data for narrative generation
    user_data = {
        "lifeline_events": lifeline_events,
        "pattern_domains": pattern_domains,
        "signals": signals,
        "journal_entries": journal_entries,
        "lunar_reflections": lunar_reflections
    }
    
    # Generate narratives
    primary_narrative = None
    secondary_narrative = None
    
    if primary:
        primary_narrative = generate_archetype_narrative(
            primary["archetype_id"],
            user_data,
            primary
        )
    
    if secondary and secondary["score"] >= 0.5:  # Only include if strong enough
        secondary_narrative = generate_archetype_narrative(
            secondary["archetype_id"],
            user_data,
            secondary
        )
    
    # Build response
    result = {
        "success": True,
        "user_id": user_id,
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "confidence": confidence,
        "data_available": {
            "lifeline_events": len(lifeline_events),
            "pattern_domains": len(pattern_domains),
            "signals": len(signals),
            "journal_entries": len(journal_entries),
            "lunar_reflections": len(lunar_reflections)
        }
    }
    
    if primary_narrative:
        result["primary_archetype"] = {
            "id": primary["archetype_id"],
            "name": primary["archetype"],
            "icon": primary["icon"],
            "score": primary["score"],
            "evidence_count": primary["evidence_count"],
            "narrative": primary_narrative
        }
    
    if secondary_narrative:
        result["secondary_archetype"] = {
            "id": secondary["archetype_id"],
            "name": secondary["archetype"],
            "icon": secondary["icon"],
            "score": secondary["score"],
            "evidence_count": secondary["evidence_count"],
            "narrative": secondary_narrative
        }
    
    # Include top 5 scored archetypes for debugging/insight
    result["all_scores"] = [
        {
            "id": a["archetype_id"],
            "name": a["archetype"],
            "score": a["score"]
        }
        for a in scored_archetypes[:5]
    ]
    
    logger.info(f"[Archetype] Computed archetype for user {user_id}: {primary['archetype'] if primary else 'None'} (confidence: {confidence})")
    
    return result
