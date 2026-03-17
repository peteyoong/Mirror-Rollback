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
# ARCHETYPE LIBRARY (v0.2 - Compressed & Precise)
# =============================================================================

ARCHETYPE_LIBRARY = {
    "phoenix": {
        "id": "phoenix",
        "name": "Phoenix",
        "icon": "🔥",
        "description": "You build. Something breaks. You rebuild stronger.",
        "short_description": "Breakdown → rebuild",
        "signals": {
            "lifeline": ["turning point", "career", "restart", "transition", "transformation", "crisis", "rebuild", "new beginning"],
            "patterns": ["recurring", "growth_transformation", "identity_direction"],
            "journal": ["reinvent", "restart", "burnout", "fresh start", "new chapter", "rebuild", "start over"],
            "lunar": ["release", "decision", "pivot", "change", "transform"]
        },
        "narrative_template": {
            "summary": "You don't grow steadily. You grow when something breaks. Your biggest leaps forward come after collapse—not despite it, but because of it.",
            "contrast": "Others fear losing what they've built. You know destruction clears the way for something better.",
            "how_this_shows_up": [
                "In work: Career restarts, industry pivots, burning boats",
                "In relationships: Ending what no longer fits, even when hard",
                "In decisions: Choosing transformation over comfortable stagnation"
            ],
            "why_patterns": [
                "Multiple major turning points have reshaped your direction",
                "Crisis precedes your biggest growth periods",
                "Your reflections keep returning to themes of starting over"
            ],
            "current_expression": "If something feels like it's falling apart right now, you've been here before. You know how this goes.",
            "reflection_question": "What are you refusing to let die that needs to?"
        }
    },
    
    "builder_under_pressure": {
        "id": "builder_under_pressure",
        "name": "Builder Under Pressure",
        "icon": "🏗️",
        "description": "Difficulty doesn't break you. It builds you.",
        "short_description": "Strength through challenge",
        "signals": {
            "lifeline": ["challenge", "achievement", "career", "work", "professional", "milestone", "pressure"],
            "patterns": ["expression_action", "pressure_stress", "work_purpose"],
            "journal": ["pressure", "stress", "build", "achieve", "work", "challenge", "push through"],
            "lunar": ["tension", "effort", "commitment", "push"]
        },
        "narrative_template": {
            "summary": "You create your strongest work under pressure. Comfort makes you lazy. Challenge makes you sharp.",
            "contrast": "Others crumble under weight. You use it to build foundations.",
            "how_this_shows_up": [
                "In work: Deadlines and constraints improve your output",
                "In relationships: You step up when others need you most",
                "In decisions: You commit hardest when stakes are highest"
            ],
            "why_patterns": [
                "Your biggest achievements follow periods of intensity",
                "Stress and breakthrough cluster together in your timeline",
                "You keep choosing harder paths over easier ones"
            ],
            "current_expression": "The pressure you feel right now isn't breaking you. It's shaping you.",
            "reflection_question": "What are you building that only pressure can forge?"
        }
    },
    
    "reinventor": {
        "id": "reinventor",
        "name": "The Reinventor",
        "icon": "🔄",
        "description": "You've been many people. Each one was real.",
        "short_description": "Serial transformation",
        "signals": {
            "lifeline": ["identity", "transformation", "move", "relocation", "career", "change", "new", "different"],
            "patterns": ["identity_direction", "growth_transformation"],
            "journal": ["change", "different", "new version", "who I am", "becoming", "evolve"],
            "lunar": ["identity", "change", "who", "becoming"]
        },
        "narrative_template": {
            "summary": "You've lived multiple lives in one. Shedding old identities isn't loss—it's how you become more yourself.",
            "contrast": "Others cling to who they were. You keep asking who you're becoming.",
            "how_this_shows_up": [
                "In work: Career pivots that confuse others but feel right to you",
                "In relationships: Outgrowing connections that no longer fit",
                "In decisions: Choosing unknown futures over known limitations"
            ],
            "why_patterns": [
                "Your timeline shows distinct chapters, not continuous storyline",
                "Identity signals are consistently high",
                "You've made 'who am I now' a recurring question"
            ],
            "current_expression": "Something in you is shifting again. Trust it. You've done this before.",
            "reflection_question": "Who are you becoming that you haven't admitted yet?"
        }
    },
    
    "seeker": {
        "id": "seeker",
        "name": "The Seeker",
        "icon": "🧭",
        "description": "You'd rather search than settle.",
        "short_description": "Exploration over arrival",
        "signals": {
            "lifeline": ["move", "travel", "education", "learning", "new", "exploration", "search"],
            "patterns": ["mind_meaning", "identity_direction"],
            "journal": ["searching", "wondering", "meaning", "purpose", "why", "explore", "discover"],
            "lunar": ["question", "explore", "meaning", "purpose", "direction"]
        },
        "narrative_template": {
            "summary": "You're pulled toward questions, not answers. The search itself is the point. Settling feels like dying slowly.",
            "contrast": "Others need destinations. You need horizons.",
            "how_this_shows_up": [
                "In work: Learning new fields, exploring possibilities",
                "In relationships: Drawn to depth and novelty",
                "In decisions: Choosing growth over security"
            ],
            "why_patterns": [
                "Movement and change run through your timeline",
                "Learning signals stay consistently strong",
                "Your reflections circle questions of meaning"
            ],
            "current_expression": "That restlessness you feel? It's not a problem. It's your compass.",
            "reflection_question": "What question are you avoiding by staying busy?"
        }
    },
    
    "stabilizer": {
        "id": "stabilizer",
        "name": "The Stabilizer",
        "icon": "⚓",
        "description": "You're the ground others stand on.",
        "short_description": "Steady through chaos",
        "signals": {
            "lifeline": ["family", "home", "relationship", "marriage", "stability", "steady", "consistent"],
            "patterns": ["relationships_boundaries", "emotional_landscape"],
            "journal": ["stable", "ground", "secure", "home", "foundation", "steady", "reliable"],
            "lunar": ["steady", "consistent", "ground", "security"]
        },
        "narrative_template": {
            "summary": "You create steadiness. Not by avoiding change—by being what doesn't change. Others orbit around your consistency.",
            "contrast": "Others chase excitement. You create foundations.",
            "how_this_shows_up": [
                "In work: Reliable, long-term commitments",
                "In relationships: The one people lean on",
                "In decisions: Choosing what lasts over what excites"
            ],
            "why_patterns": [
                "Home and relationship themes dominate your timeline",
                "You've built structures others depend on",
                "Emotional steadiness signals run deep"
            ],
            "current_expression": "Your steadiness isn't boring. It's rare. Don't undervalue it.",
            "reflection_question": "What would fall apart if you stopped holding it together?"
        }
    },
    
    "protector": {
        "id": "protector",
        "name": "The Protector",
        "icon": "🛡️",
        "description": "You carry weight so others don't have to.",
        "short_description": "Responsibility first",
        "signals": {
            "lifeline": ["family", "responsibility", "care", "duty", "support", "protect", "children"],
            "patterns": ["relationships_boundaries", "pressure_stress"],
            "journal": ["responsible", "care", "protect", "others", "duty", "support", "help"],
            "lunar": ["responsibility", "others", "care", "protect"]
        },
        "narrative_template": {
            "summary": "You take responsibility—often more than your share. Protecting others is woven into how you exist.",
            "contrast": "Others protect themselves first. You protect others first.",
            "how_this_shows_up": [
                "In work: Taking on what others can't or won't",
                "In relationships: Being the strong one",
                "In decisions: Considering others' needs before your own"
            ],
            "why_patterns": [
                "Family and duty signals run through your timeline",
                "You carry more than anyone asks you to",
                "Sacrifice patterns cluster around those you love"
            ],
            "current_expression": "The weight you're carrying right now—is it yours to carry?",
            "reflection_question": "What would happen if you protected yourself as fiercely as you protect others?"
        }
    },
    
    "breakthrough_artist": {
        "id": "breakthrough_artist",
        "name": "Breakthrough Artist",
        "icon": "💫",
        "description": "You create in bursts. Then you rest. Then you burst again.",
        "short_description": "Creative cycles",
        "signals": {
            "lifeline": ["creative", "expression", "art", "project", "achievement", "breakthrough", "launch"],
            "patterns": ["expression_action", "timing_readiness"],
            "journal": ["create", "express", "make", "build", "breakthrough", "inspired", "flow"],
            "lunar": ["create", "express", "flow", "inspiration", "emergence"]
        },
        "narrative_template": {
            "summary": "You work in cycles—intense creation, then quiet integration. Your breakthroughs come through making, not thinking.",
            "contrast": "Others produce steadily. You explode, rest, explode.",
            "how_this_shows_up": [
                "In work: Projects with intense bursts of energy",
                "In relationships: Deep connection then needed space",
                "In decisions: Acting when inspiration strikes"
            ],
            "why_patterns": [
                "Your achievements cluster in time",
                "Creative expression signals spike and calm",
                "Your best work follows periods of incubation"
            ],
            "current_expression": "Quiet phase? Building. Intense phase? Trust it.",
            "reflection_question": "What's ready to emerge that you've been holding back?"
        }
    },
    
    "threshold_walker": {
        "id": "threshold_walker",
        "name": "Threshold Walker",
        "icon": "🚪",
        "description": "You're comfortable in doorways. Others rush through—you know how to be in them.",
        "short_description": "Navigator of between",
        "signals": {
            "lifeline": ["transition", "turning point", "milestone", "major", "life change", "threshold", "between"],
            "patterns": ["growth_transformation", "timing_readiness"],
            "journal": ["transition", "between", "crossing", "threshold", "next phase", "change"],
            "lunar": ["transition", "threshold", "crossing", "between", "phase"]
        },
        "narrative_template": {
            "summary": "You navigate liminal spaces. While others panic at 'between', you've learned to be there—because you've been there before.",
            "contrast": "Others fear uncertainty. You've made it familiar territory.",
            "how_this_shows_up": [
                "In work: Handling transitions others avoid",
                "In relationships: Staying present during hard changes",
                "In decisions: Trusting timing over forcing outcomes"
            ],
            "why_patterns": [
                "Transitions cluster throughout your timeline",
                "You engage with change rather than resist it",
                "Your reflections show comfort with uncertainty"
            ],
            "current_expression": "Feeling 'between' right now? That's not limbo. That's your territory.",
            "reflection_question": "What threshold are you standing at that you haven't fully acknowledged?"
        }
    },
    
    "expansion_through_disruption": {
        "id": "expansion_through_disruption",
        "name": "Expansion Through Disruption",
        "icon": "⚡",
        "description": "Your biggest growth comes from what you didn't plan.",
        "short_description": "Growth via chaos",
        "signals": {
            "lifeline": ["unexpected", "crisis", "disruption", "surprise", "sudden", "unplanned", "shock"],
            "patterns": ["growth_transformation", "pressure_stress"],
            "journal": ["unexpected", "surprised", "didn't plan", "sudden", "disruption", "change"],
            "lunar": ["unexpected", "surprise", "shift", "disruption"]
        },
        "narrative_template": {
            "summary": "Your most significant growth comes uninvited. Disruption opens doors you couldn't have planned. Chaos becomes compass.",
            "contrast": "Others plan growth. Growth plans you.",
            "how_this_shows_up": [
                "In work: Pivots forced by circumstance that led somewhere better",
                "In relationships: Unexpected connections that changed everything",
                "In decisions: Choosing to work with surprise rather than against it"
            ],
            "why_patterns": [
                "Key turning points were unplanned",
                "Disruption and expansion correlate in your signals",
                "You've learned to ride chaos rather than fight it"
            ],
            "current_expression": "Current disruption? Less random than it seems.",
            "reflection_question": "What opportunity is hiding inside what just broke?"
        }
    },
    
    "quiet_endurer": {
        "id": "quiet_endurer",
        "name": "The Quiet Endurer",
        "icon": "🌱",
        "description": "You outlast. You don't overpower.",
        "short_description": "Persistence over force",
        "signals": {
            "lifeline": ["persistent", "steady", "long-term", "endure", "continue", "patience", "gradual"],
            "patterns": ["emotional_landscape", "relationships_boundaries"],
            "journal": ["patience", "persist", "continue", "keep going", "endure", "steady", "wait"],
            "lunar": ["patience", "waiting", "persistence", "steady", "continue"]
        },
        "narrative_template": {
            "summary": "You don't force outcomes. You outlast obstacles. Your strength is quiet—but it's deeper than most.",
            "contrast": "Others push through walls. You wait for them to crumble.",
            "how_this_shows_up": [
                "In work: Long games that others abandon",
                "In relationships: Staying when others would leave",
                "In decisions: Trusting slow over fast"
            ],
            "why_patterns": [
                "Gradual building shows throughout your timeline",
                "Emotional steadiness runs deep",
                "Your patience has already paid off more than you've noticed"
            ],
            "current_expression": "What feels slow right now is exactly the pace this needs.",
            "reflection_question": "Where is your persistence already paying off without recognition?"
        }
    },
    
    "weaver": {
        "id": "weaver",
        "name": "The Weaver",
        "icon": "🕸️",
        "description": "You see connections others miss.",
        "short_description": "Pattern connector",
        "signals": {
            "lifeline": ["relationship", "connect", "network", "community", "bridge", "bring together"],
            "patterns": ["relationships_boundaries", "expression_action"],
            "journal": ["connect", "relationship", "together", "bridge", "link", "weave", "synthesis"],
            "lunar": ["connection", "relationship", "together", "bridge"]
        },
        "narrative_template": {
            "summary": "You naturally see how separate things connect. Your life pattern shows building bridges—between people, ideas, or worlds that seemed unrelated.",
            "contrast": "Others see categories. You see relationships.",
            "how_this_shows_up": [
                "In work: Bringing different fields together",
                "In relationships: Being the connector in your circles",
                "In decisions: Synthesizing rather than choosing"
            ],
            "why_patterns": [
                "Connection-making runs through your timeline",
                "Relationship signals stay consistently active",
                "You've linked things others kept separate"
            ],
            "current_expression": "Those connections forming right now? They're part of a larger pattern.",
            "reflection_question": "What disconnected parts of your life are asking to be woven together?"
        }
    },
    
    "emergence_keeper": {
        "id": "emergence_keeper",
        "name": "Emergence Keeper",
        "icon": "🌅",
        "description": "You're drawn to beginnings. You know how to receive what's trying to start.",
        "short_description": "Midwife of new things",
        "signals": {
            "lifeline": ["new", "start", "beginning", "first", "launch", "initiate", "pioneer"],
            "patterns": ["expression_action", "timing_readiness"],
            "journal": ["new beginning", "start", "first", "emergence", "dawn", "initiate"],
            "lunar": ["new", "beginning", "start", "emergence", "initiate"]
        },
        "narrative_template": {
            "summary": "You have an affinity for beginnings. New projects, relationships, chapters—you sense what's trying to emerge before others do.",
            "contrast": "Others finish things. You start them.",
            "how_this_shows_up": [
                "In work: Launching initiatives others continue",
                "In relationships: Sensing new connections before they solidify",
                "In decisions: Recognizing dawn before sunrise"
            ],
            "why_patterns": [
                "Your timeline shows you present at many beginnings",
                "Emergence signals stay consistently active",
                "You often start what others carry forward"
            ],
            "current_expression": "Something new is trying to begin. You can feel it. Trust that.",
            "reflection_question": "What new beginning is asking for your attention that you keep postponing?"
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
