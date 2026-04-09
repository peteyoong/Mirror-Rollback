"""
Tension Engine V1.0 - Real-Time Tension Resolution System

CORE PRINCIPLE:
Mirror is NOT a lens aggregator.
Mirror is a REAL-TIME TENSION ENGINE.

This engine:
1. Extracts standardized signals from each lens
2. Clusters similar tensions
3. Scores dominance (Pattern Memory weighted highest)
4. Resolves to ONE dominant tension
5. Generates sharp, immediate language

DOMINANCE WEIGHTS:
- Pattern Memory: 0.45 (highest)
- Cross-lens agreement: 0.25
- Intensity: 0.15
- Recency: 0.15

DOMAINS: action, decision, emotion, relationship, control

OUTPUT: One tension, one moment, one truth.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import hashlib
import random

logger = logging.getLogger(__name__)


# =============================================================================
# TENSION SIGNAL DATA STRUCTURE
# =============================================================================

@dataclass
class TensionSignal:
    """Standardized signal from any lens."""
    tension: str           # e.g. "hesitating before acting"
    direction: str         # e.g. "push vs hold"
    intensity: float       # 0.0 - 1.0
    confidence: float      # 0.0 - 1.0
    domain: str            # action, decision, emotion, relationship, control
    source: str            # pattern_memory, astrology, human_design, bazi, enneagram
    raw_data: Dict = None  # Original lens data for evidence


# =============================================================================
# TENSION CLUSTERS - Map similar tensions to unified directions
# =============================================================================

TENSION_CLUSTERS = {
    "push_vs_hold": {
        "label": "Push vs Hold",
        "keywords": [
            "hesitating", "waiting", "holding back", "not moving", "stuck",
            "momentum blocked", "waiting for clarity", "afraid to act",
            "paralysis", "overthinking", "stalling", "delay", "caution"
        ],
        "domain": "action"
    },
    "control_vs_flow": {
        "label": "Control vs Flow",
        "keywords": [
            "controlling", "micromanaging", "gripping", "forcing", "rigid",
            "need certainty", "perfectionism", "can't let go", "overplanning",
            "resistance", "fighting", "not surrendering"
        ],
        "domain": "control"
    },
    "precision_vs_progress": {
        "label": "Precision vs Progress",
        "keywords": [
            "perfectionist", "refining", "polishing", "not shipping",
            "too careful", "over-editing", "never ready", "detail obsessed",
            "quality over speed", "afraid of mistakes"
        ],
        "domain": "action"
    },
    "visible_vs_hidden": {
        "label": "Visible vs Hidden",
        "keywords": [
            "hiding", "not showing up", "staying small", "avoiding exposure",
            "fear of being seen", "withdrawing", "protective", "private",
            "not sharing", "keeping back"
        ],
        "domain": "relationship"
    },
    "logic_vs_instinct": {
        "label": "Logic vs Instinct",
        "keywords": [
            "overthinking", "analyzing", "ignoring gut", "rationalizing",
            "head vs heart", "second-guessing", "not trusting", "doubt",
            "need proof", "dismissing feelings"
        ],
        "domain": "decision"
    },
    "self_vs_others": {
        "label": "Self vs Others",
        "keywords": [
            "people pleasing", "boundaries", "saying yes", "overgiving",
            "resentment building", "losing self", "accommodating",
            "neglecting needs", "conflict avoidance"
        ],
        "domain": "relationship"
    },
    "rest_vs_push": {
        "label": "Rest vs Push",
        "keywords": [
            "exhaustion", "burnout", "forcing energy", "not resting",
            "pushing through", "ignoring fatigue", "overdoing",
            "can't stop", "productivity addiction"
        ],
        "domain": "action"
    },
    "clarity_vs_chaos": {
        "label": "Clarity vs Chaos",
        "keywords": [
            "confused", "unclear", "overwhelmed", "too many options",
            "scattered", "no direction", "lost", "spinning",
            "can't decide", "fog"
        ],
        "domain": "decision"
    },
    "trust_vs_doubt": {
        "label": "Trust vs Doubt",
        "keywords": [
            "doubting", "questioning", "suspicious", "not believing",
            "second-guessing others", "paranoid", "skeptical",
            "waiting for proof", "defensive"
        ],
        "domain": "emotion"
    },
    "expression_vs_suppression": {
        "label": "Expression vs Suppression",
        "keywords": [
            "holding back words", "not speaking up", "swallowing feelings",
            "unexpressed", "bottled up", "silent", "contained",
            "afraid to say", "keeping peace"
        ],
        "domain": "emotion"
    }
}


# =============================================================================
# ENERGY TITLES - Short punchy labels
# =============================================================================

ENERGY_TITLES = {
    "push_vs_hold": [
        "Still Hesitating",
        "Not Moving Yet",
        "Waiting Again",
        "Holding the Line",
        "Something Wants to Move"
    ],
    "control_vs_flow": [
        "Gripping Too Tight",
        "Trying to Control",
        "Not Letting Go",
        "Forcing It",
        "Fighting the Current"
    ],
    "precision_vs_progress": [
        "Still Refining",
        "Not Ready Yet",
        "Almost Perfect",
        "One More Edit",
        "Never Quite Done"
    ],
    "visible_vs_hidden": [
        "Staying Small",
        "Hiding Again",
        "Not Showing Up",
        "Keeping Back",
        "Behind the Curtain"
    ],
    "logic_vs_instinct": [
        "Overthinking It",
        "In Your Head",
        "Ignoring the Gut",
        "Too Much Analysis",
        "Not Trusting"
    ],
    "self_vs_others": [
        "Giving Too Much",
        "Losing Yourself",
        "Saying Yes Again",
        "Boundary Blur",
        "Their Needs First"
    ],
    "rest_vs_push": [
        "Running Empty",
        "Pushing Through",
        "Not Stopping",
        "Forcing Energy",
        "Past the Limit"
    ],
    "clarity_vs_chaos": [
        "Still Unclear",
        "Spinning",
        "Too Many Options",
        "No Direction",
        "In the Fog"
    ],
    "trust_vs_doubt": [
        "Doubting Again",
        "Questioning Everything",
        "Waiting for Proof",
        "Not Believing",
        "On Guard"
    ],
    "expression_vs_suppression": [
        "Holding Back",
        "Words Stuck",
        "Not Saying It",
        "Swallowing It",
        "Keeping Quiet"
    ]
}


# =============================================================================
# MOMENT LANGUAGE TEMPLATES - Sharp, second-person, no soft language
# =============================================================================

MOMENT_TEMPLATES = {
    "push_vs_hold": [
        "You're hesitating again — and you know it.",
        "Part of you wants to move. Part of you is holding back.",
        "You're back here again.",
        "The opening is there. You're not taking it.",
        "You're waiting for certainty that isn't coming."
    ],
    "control_vs_flow": [
        "You're trying to control something that wants to move.",
        "You're gripping when you need to let go.",
        "The harder you hold, the more it slips.",
        "You're forcing something that needs space.",
        "Control isn't working right now."
    ],
    "precision_vs_progress": [
        "You're polishing something that needs to ship.",
        "Good enough shipped beats perfect never did.",
        "You're hiding behind quality.",
        "The refining is the stalling.",
        "Done is the goal. Perfect is the trap."
    ],
    "visible_vs_hidden": [
        "You're making yourself small again.",
        "Part of you wants to be seen. Part of you is hiding.",
        "You're protecting yourself from exposure.",
        "The world can't respond to what it can't see.",
        "You're holding back what wants to come forward."
    ],
    "logic_vs_instinct": [
        "You already know. You're just not trusting it.",
        "Your gut said something. Your head overruled it.",
        "You're analyzing when you need to act.",
        "The answer is there. You're looking past it.",
        "More data won't help. You have enough."
    ],
    "self_vs_others": [
        "You're giving more than you have.",
        "Their needs are louder than yours right now.",
        "You said yes when you meant no.",
        "The resentment is building.",
        "You're losing yourself in someone else's story."
    ],
    "rest_vs_push": [
        "You're running on fumes.",
        "Your body is asking for something your mind won't give.",
        "Pushing harder isn't the answer right now.",
        "You're past the point of productive.",
        "The tank is empty. You're still driving."
    ],
    "clarity_vs_chaos": [
        "You don't know what to do next.",
        "Too many options. No clear path.",
        "The fog is real. Don't pretend it isn't.",
        "You're spinning without landing.",
        "Clarity isn't coming from more thinking."
    ],
    "trust_vs_doubt": [
        "You're questioning something you used to believe.",
        "Doubt has moved in. It's not leaving easily.",
        "You're waiting for proof that won't arrive.",
        "The suspicion is running the show.",
        "Trust is hard right now."
    ],
    "expression_vs_suppression": [
        "There's something you're not saying.",
        "The words are there. You're holding them back.",
        "You're keeping the peace at your own expense.",
        "What's unsaid is building pressure.",
        "You're swallowing what needs to come out."
    ]
}


# =============================================================================
# SUPPORTING LINES - One sentence reinforcements
# =============================================================================

SUPPORTING_LINES = {
    "recurring": [
        "Same situation. Different day.",
        "You've seen this before.",
        "This isn't new.",
        "It's a pattern. Not a surprise.",
        "Here again."
    ],
    "intensity_high": [
        "It's louder than usual.",
        "This one has weight.",
        "Pay attention to this.",
        "Something is building.",
        "Don't ignore this."
    ],
    "intensity_low": [
        "Subtle, but present.",
        "Just under the surface.",
        "Barely visible. Still real.",
        "Quiet signal.",
        "Easy to miss. Worth noticing."
    ],
    "cross_lens": [
        "Multiple signals pointing here.",
        "Everything is pointing the same direction.",
        "Not just one source.",
        "Converging.",
        "Hard to argue with."
    ]
}


# =============================================================================
# MICRO-SHIFTS - One action sentence
# =============================================================================

MICRO_SHIFTS = {
    "push_vs_hold": [
        "Move before you feel ready.",
        "Take one step. Any step.",
        "Do the smallest version.",
        "Start before you're sure.",
        "Act first. Adjust after."
    ],
    "control_vs_flow": [
        "Let one thing go.",
        "Stop managing for an hour.",
        "See what happens if you don't intervene.",
        "Release the grip on one thing.",
        "Allow it to unfold."
    ],
    "precision_vs_progress": [
        "Ship it at 80%.",
        "Send it imperfect.",
        "Let it be seen before it's perfect.",
        "Done today beats perfect next week.",
        "Release the last revision."
    ],
    "visible_vs_hidden": [
        "Show one thing you've been hiding.",
        "Let yourself be seen once today.",
        "Share before you're ready.",
        "Step forward instead of back.",
        "Be visible in one small way."
    ],
    "logic_vs_instinct": [
        "Trust the first answer.",
        "Act on the gut feeling.",
        "Skip the analysis. Decide.",
        "Let instinct lead once.",
        "Follow the feeling, not the logic."
    ],
    "self_vs_others": [
        "Say no once today.",
        "Put your need first in one situation.",
        "Let them figure it out.",
        "Take something back for yourself.",
        "Stop over-functioning for someone."
    ],
    "rest_vs_push": [
        "Stop one hour early.",
        "Take the break you're avoiding.",
        "Let the day end incomplete.",
        "Rest without earning it.",
        "Do less today."
    ],
    "clarity_vs_chaos": [
        "Choose one thing. Ignore the rest.",
        "Sit with the not-knowing.",
        "Stop gathering options.",
        "Commit to one direction for 24 hours.",
        "Let the fog be there."
    ],
    "trust_vs_doubt": [
        "Act as if you trusted.",
        "Give benefit of doubt once.",
        "Suspend the questioning for a day.",
        "Let something be true.",
        "Choose trust over proof."
    ],
    "expression_vs_suppression": [
        "Say one thing you've been holding.",
        "Speak before you're ready.",
        "Let it out, even imperfectly.",
        "Break the silence on one thing.",
        "Voice it. Even quietly."
    ]
}


# =============================================================================
# SIGNAL EXTRACTION FROM LENSES
# =============================================================================

async def extract_pattern_memory_signal(db, user_id: str) -> Optional[TensionSignal]:
    """Extract tension signal from Pattern Memory - HIGHEST PRIORITY."""
    try:
        from services.pattern_memory_engine import get_pattern_history
        
        # Get recent pattern history
        history = await get_pattern_history(db, user_id, days=14)
        if not history:
            logger.info(f"[TensionEngine] No pattern history for user {user_id}")
            return None
        
        # Count pattern frequencies
        pattern_counts = defaultdict(int)
        pattern_recency = {}
        
        for entry in history:
            # Look for tension or pattern_key in the entry
            tension = entry.get("primary_tension", "") or entry.get("pattern_key", "") or entry.get("tension", "")
            if tension:
                pattern_counts[tension] += 1
                entry_date = entry.get("date", "") or entry.get("created_at", "")
                if entry_date:
                    if isinstance(entry_date, datetime):
                        entry_date = entry_date.strftime("%Y-%m-%d")
                    pattern_recency[tension] = str(entry_date)[:10]
        
        if not pattern_counts:
            return None
        
        # Find most frequent pattern
        dominant_pattern = max(pattern_counts.items(), key=lambda x: x[1])
        pattern_key = dominant_pattern[0]
        frequency = dominant_pattern[1]
        
        # Calculate intensity based on frequency
        intensity = min(1.0, frequency / 5)  # 5+ occurrences = max intensity
        
        # Calculate confidence based on recency
        recent_date = pattern_recency.get(pattern_key, "")
        confidence = 0.5
        if recent_date:
            try:
                days_ago = (datetime.now(timezone.utc).date() - datetime.strptime(recent_date[:10], "%Y-%m-%d").date()).days
                if days_ago <= 1:
                    confidence = 1.0
                elif days_ago <= 3:
                    confidence = 0.85
                elif days_ago <= 7:
                    confidence = 0.7
            except:
                pass
        
        # Map to cluster
        cluster_key = _find_matching_cluster(pattern_key)
        cluster = TENSION_CLUSTERS.get(cluster_key, {})
        
        return TensionSignal(
            tension=pattern_key,
            direction=cluster.get("label", "Unknown"),
            intensity=intensity,
            confidence=confidence,
            domain=cluster.get("domain", "action"),
            source="pattern_memory",
            raw_data={
                "frequency": frequency,
                "recent_date": recent_date,
                "cluster": cluster_key
            }
        )
    except Exception as e:
        logger.error(f"[TensionEngine] Pattern memory extraction failed: {e}")
        return None


async def extract_astrology_signal(db, user_id: str) -> Optional[TensionSignal]:
    """Extract tension signal from current transits."""
    try:
        from services.daily_transit_window import scan_daily_transit_window, build_daily_theme_from_events
        
        # Get user's chart
        user = await db.users.find_one({"_id": user_id})
        if not user:
            return None
            
        # Try to get chart data
        chart = await db.astrology_charts.find_one({"user_id": user_id})
        if not chart:
            # Try to generate transit signal without natal chart
            from services.transit_signals import get_current_transit_context
            transit_ctx = get_current_transit_context()
            
            if transit_ctx and transit_ctx.get("dominant_theme"):
                tension_text = transit_ctx.get("dominant_theme", "energy shifting")
                intensity = transit_ctx.get("intensity", 0.5)
            else:
                tension_text = "momentum building"
                intensity = 0.5
        else:
            # Scan transit window with natal chart
            transit_data = scan_daily_transit_window(
                datetime.now(timezone.utc),
                chart.get("planet_positions", {}),
                chart.get("house_cusps", [])
            )
            
            if transit_data:
                theme = build_daily_theme_from_events(
                    transit_data.get("events", []),
                    transit_data.get("active_aspects", [])
                )
                tension_text = theme.get("theme", "transit activation")
                intensity = theme.get("intensity", 0.5)
            else:
                tension_text = "energy in motion"
                intensity = 0.5
        
        # Map to cluster
        cluster_key = _find_matching_cluster(tension_text)
        cluster = TENSION_CLUSTERS.get(cluster_key, {})
        
        return TensionSignal(
            tension=tension_text,
            direction=cluster.get("label", "Momentum"),
            intensity=min(1.0, intensity),
            confidence=0.7,  # Transits are reliable but less personal
            domain=cluster.get("domain", "action"),
            source="astrology",
            raw_data={
                "theme": tension_text,
                "intensity": intensity,
                "cluster": cluster_key
            }
        )
    except Exception as e:
        logger.error(f"[TensionEngine] Astrology extraction failed: {e}")
        return None


async def extract_human_design_signal(db, user_id: str) -> Optional[TensionSignal]:
    """Extract tension signal from Human Design mechanics."""
    try:
        # Get user's HD data
        user = await db.users.find_one({"_id": user_id})
        if not user:
            return None
        
        hd_type = user.get("human_design_type", "")
        authority = user.get("human_design_authority", "")
        
        if not hd_type:
            return None
        
        # Map HD type + authority to typical tensions
        HD_TYPE_TENSIONS = {
            "Manifestor": ("push_vs_hold", "The urge to initiate is meeting resistance.", 0.7),
            "Generator": ("rest_vs_push", "Energy is available, but forcing won't help.", 0.65),
            "Manifesting Generator": ("precision_vs_progress", "Moving fast, but skipping steps.", 0.7),
            "Projector": ("visible_vs_hidden", "Waiting for invitation feels like stalling.", 0.75),
            "Reflector": ("clarity_vs_chaos", "Too many inputs, not enough clarity.", 0.6),
        }
        
        AUTHORITY_TENSIONS = {
            "Emotional": ("logic_vs_instinct", "The wave hasn't settled yet.", 0.7),
            "Sacral": ("push_vs_hold", "Your body knows. Listen.", 0.65),
            "Splenic": ("trust_vs_doubt", "The instinct is there. Trust it.", 0.7),
            "Ego": ("self_vs_others", "Willpower isn't infinite.", 0.65),
            "Self-Projected": ("expression_vs_suppression", "Speak to find clarity.", 0.6),
            "Mental": ("logic_vs_instinct", "Talk it through with someone.", 0.55),
            "Lunar": ("clarity_vs_chaos", "Wait for the full cycle.", 0.5),
        }
        
        # Prefer authority tension if available
        if authority and authority in AUTHORITY_TENSIONS:
            cluster_key, tension_text, intensity = AUTHORITY_TENSIONS[authority]
        elif hd_type in HD_TYPE_TENSIONS:
            cluster_key, tension_text, intensity = HD_TYPE_TENSIONS[hd_type]
        else:
            return None
        
        cluster = TENSION_CLUSTERS.get(cluster_key, {})
        
        return TensionSignal(
            tension=tension_text,
            direction=cluster.get("label", "Inner Mechanics"),
            intensity=intensity,
            confidence=0.75,
            domain=cluster.get("domain", "decision"),
            source="human_design",
            raw_data={
                "type": hd_type,
                "authority": authority,
                "cluster": cluster_key
            }
        )
    except Exception as e:
        logger.error(f"[TensionEngine] Human Design extraction failed: {e}")
        return None


async def extract_bazi_signal(db, user_id: str) -> Optional[TensionSignal]:
    """Extract tension signal from BaZi structure + timing."""
    try:
        from services.bazi_insight_layer import generate_today_insight
        
        # Get user's BaZi data
        user = await db.users.find_one({"_id": user_id})
        if not user:
            return None
        
        bazi_chart = await db.bazi_charts.find_one({"user_id": user_id})
        if not bazi_chart:
            return None
        
        # Generate today's insight
        today_insight = generate_today_insight(bazi_chart)
        
        if not today_insight:
            return None
        
        tension_text = today_insight.get("tension", "") or today_insight.get("theme", "structural pull")
        intensity = today_insight.get("intensity", 0.5)
        
        # Map to cluster
        cluster_key = _find_matching_cluster(tension_text)
        cluster = TENSION_CLUSTERS.get(cluster_key, {})
        
        return TensionSignal(
            tension=tension_text,
            direction=cluster.get("label", "Structure"),
            intensity=min(1.0, intensity),
            confidence=0.7,
            domain=cluster.get("domain", "action"),
            source="bazi",
            raw_data={
                "insight": today_insight,
                "cluster": cluster_key
            }
        )
    except Exception as e:
        logger.error(f"[TensionEngine] BaZi extraction failed: {e}")
        return None


async def extract_enneagram_signal(db, user_id: str) -> Optional[TensionSignal]:
    """Extract tension signal from Enneagram defense pattern."""
    try:
        # Get user's enneagram type
        users = db["users"]
        user = await users.find_one({"_id": user_id})
        if not user:
            return None
        
        enneagram_type = user.get("enneagram_type")
        if not enneagram_type:
            return None
        
        # Map enneagram to typical tensions
        ENNEAGRAM_TENSIONS = {
            "1": ("control_vs_flow", "The inner critic is loud.", 0.7),
            "2": ("self_vs_others", "Giving more than you have.", 0.7),
            "3": ("visible_vs_hidden", "Performance mode activated.", 0.7),
            "4": ("expression_vs_suppression", "Feeling misunderstood.", 0.6),
            "5": ("logic_vs_instinct", "Retreating into analysis.", 0.7),
            "6": ("trust_vs_doubt", "Scanning for what could go wrong.", 0.75),
            "7": ("clarity_vs_chaos", "Scattered across too many options.", 0.65),
            "8": ("control_vs_flow", "Need to control the outcome.", 0.75),
            "9": ("push_vs_hold", "Avoiding the conflict.", 0.7),
        }
        
        type_num = str(enneagram_type).split("w")[0].strip()
        tension_data = ENNEAGRAM_TENSIONS.get(type_num)
        
        if not tension_data:
            return None
        
        cluster_key, tension_text, intensity = tension_data
        cluster = TENSION_CLUSTERS.get(cluster_key, {})
        
        return TensionSignal(
            tension=tension_text,
            direction=cluster.get("label", "Defense Pattern"),
            intensity=intensity,
            confidence=0.6,  # Enneagram is structural, less real-time
            domain=cluster.get("domain", "emotion"),
            source="enneagram",
            raw_data={
                "type": enneagram_type,
                "cluster": cluster_key
            }
        )
    except Exception as e:
        logger.error(f"[TensionEngine] Enneagram extraction failed: {e}")
        return None


# =============================================================================
# CLUSTERING AND DOMINANCE SCORING
# =============================================================================

def _find_matching_cluster(text: str) -> str:
    """Find the best matching tension cluster for a text."""
    if not text:
        return "push_vs_hold"  # Default
    
    text_lower = text.lower()
    best_match = "push_vs_hold"
    best_score = 0
    
    for cluster_key, cluster_data in TENSION_CLUSTERS.items():
        keywords = cluster_data.get("keywords", [])
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > best_score:
            best_score = score
            best_match = cluster_key
    
    return best_match


def cluster_signals(signals: List[TensionSignal]) -> Dict[str, List[TensionSignal]]:
    """Group signals by their tension cluster."""
    clusters = defaultdict(list)
    
    for signal in signals:
        cluster_key = _find_matching_cluster(signal.tension)
        clusters[cluster_key].append(signal)
    
    return dict(clusters)


def score_cluster_dominance(
    cluster_key: str,
    signals: List[TensionSignal]
) -> float:
    """
    Score dominance for a cluster using the required weights:
    - Pattern Memory: 0.45
    - Cross-lens agreement: 0.25
    - Intensity: 0.15
    - Recency: 0.15
    """
    if not signals:
        return 0.0
    
    # Pattern Memory weight (0.45)
    pattern_memory_score = 0.0
    for signal in signals:
        if signal.source == "pattern_memory":
            pattern_memory_score = signal.confidence * signal.intensity
            break
    
    # Cross-lens agreement (0.25) - more sources = higher score
    unique_sources = len(set(s.source for s in signals))
    cross_lens_score = min(1.0, unique_sources / 3)  # 3+ sources = max
    
    # Intensity (0.15) - average intensity across signals
    avg_intensity = sum(s.intensity for s in signals) / len(signals)
    
    # Recency (0.15) - highest confidence signal represents recency
    max_confidence = max(s.confidence for s in signals)
    
    # Weighted sum
    dominance = (
        0.45 * pattern_memory_score +
        0.25 * cross_lens_score +
        0.15 * avg_intensity +
        0.15 * max_confidence
    )
    
    return min(1.0, dominance)


def select_dominant_tension(
    clustered_signals: Dict[str, List[TensionSignal]]
) -> Tuple[str, List[TensionSignal], float]:
    """
    Select ONE dominant tension cluster.
    Returns: (cluster_key, signals, dominance_score)
    """
    if not clustered_signals:
        return "push_vs_hold", [], 0.0
    
    scored_clusters = []
    
    for cluster_key, signals in clustered_signals.items():
        score = score_cluster_dominance(cluster_key, signals)
        scored_clusters.append((cluster_key, signals, score))
    
    # Sort by dominance score descending
    scored_clusters.sort(key=lambda x: x[2], reverse=True)
    
    # Return the highest scoring cluster
    return scored_clusters[0]


# =============================================================================
# LANGUAGE GENERATION
# =============================================================================

def generate_energy_title(cluster_key: str, seed: int = None) -> str:
    """Generate a short, punchy energy title."""
    titles = ENERGY_TITLES.get(cluster_key, ["Something Happening"])
    if seed is None:
        seed = int(datetime.now(timezone.utc).timestamp())
    return titles[seed % len(titles)]


def generate_moment(cluster_key: str, seed: int = None) -> str:
    """Generate the sharp moment statement."""
    templates = MOMENT_TEMPLATES.get(cluster_key, ["You're in the middle of something."])
    if seed is None:
        seed = int(datetime.now(timezone.utc).timestamp())
    return templates[seed % len(templates)]


def generate_supporting_line(
    signals: List[TensionSignal],
    dominance_score: float,
    seed: int = None
) -> str:
    """Generate the supporting line based on signal characteristics."""
    if seed is None:
        seed = int(datetime.now(timezone.utc).timestamp())
    
    # Check for Pattern Memory presence (recurring)
    has_pattern_memory = any(s.source == "pattern_memory" for s in signals)
    
    # Check cross-lens agreement
    unique_sources = len(set(s.source for s in signals))
    
    # Check intensity
    avg_intensity = sum(s.intensity for s in signals) / len(signals) if signals else 0.5
    
    if has_pattern_memory:
        lines = SUPPORTING_LINES["recurring"]
    elif unique_sources >= 3:
        lines = SUPPORTING_LINES["cross_lens"]
    elif avg_intensity > 0.7:
        lines = SUPPORTING_LINES["intensity_high"]
    else:
        lines = SUPPORTING_LINES["intensity_low"]
    
    return lines[seed % len(lines)]


def generate_micro_shift(cluster_key: str, seed: int = None) -> str:
    """Generate the micro-shift action."""
    shifts = MICRO_SHIFTS.get(cluster_key, ["Do one small thing differently."])
    if seed is None:
        seed = int(datetime.now(timezone.utc).timestamp())
    return shifts[seed % len(shifts)]


def generate_drivers(signals: List[TensionSignal]) -> List[Dict[str, str]]:
    """Generate the bullet-point driver evidence."""
    drivers = []
    
    for signal in signals:
        if signal.source == "pattern_memory":
            freq = signal.raw_data.get("frequency", 0) if signal.raw_data else 0
            text = f"This has shown up {freq} times recently." if freq > 0 else "This pattern keeps returning."
        elif signal.source == "astrology":
            text = "Momentum is rising, but your system is resisting it."
        elif signal.source == "human_design":
            text = "You're waiting for certainty before acting."
        elif signal.source == "bazi":
            text = "Precision is slowing movement."
        elif signal.source == "enneagram":
            text = "Control feels safer than exposure."
        else:
            text = signal.tension
        
        drivers.append({
            "source": signal.source,
            "text": text
        })
    
    return drivers


def generate_driver_synthesis(cluster_key: str, signals: List[TensionSignal]) -> str:
    """Generate the 1-2 line synthesis of what's driving this."""
    SYNTHESIS_TEMPLATES = {
        "push_vs_hold": "You're ready to move — but not trusting the move.",
        "control_vs_flow": "You're managing instead of allowing.",
        "precision_vs_progress": "You're perfecting instead of completing.",
        "visible_vs_hidden": "You want to be seen — but you're making yourself invisible.",
        "logic_vs_instinct": "You know the answer. You're just not accepting it.",
        "self_vs_others": "You're giving what you need for yourself.",
        "rest_vs_push": "Your body is asking. Your mind is refusing.",
        "clarity_vs_chaos": "You're looking for clarity in more thinking.",
        "trust_vs_doubt": "You're waiting for certainty that won't arrive.",
        "expression_vs_suppression": "The words are ready. You're not letting them out.",
    }
    
    return SYNTHESIS_TEMPLATES.get(cluster_key, "Something is happening beneath the surface.")


# =============================================================================
# MAIN ENGINE FUNCTION
# =============================================================================

async def generate_tension_moment(db, user_id: str) -> Dict[str, Any]:
    """
    Main function: Generate the Home tension moment.
    
    Returns the complete API response with:
    - tension_label
    - energy_title
    - moment
    - supporting_line
    - micro_shift
    - drivers
    - driver_synthesis
    - confidence
    - intensity
    - fallback_used
    """
    logger.info(f"[TensionEngine] Generating tension for user {user_id}")
    
    # Collect signals from all lenses (prioritize Pattern Memory, Astrology, HD)
    signals = []
    
    # Pattern Memory - HIGHEST PRIORITY
    pm_signal = await extract_pattern_memory_signal(db, user_id)
    if pm_signal:
        signals.append(pm_signal)
        logger.info(f"[TensionEngine] Pattern Memory signal: {pm_signal.tension}")
    
    # Astrology
    astro_signal = await extract_astrology_signal(db, user_id)
    if astro_signal:
        signals.append(astro_signal)
        logger.info(f"[TensionEngine] Astrology signal: {astro_signal.tension}")
    
    # Human Design
    hd_signal = await extract_human_design_signal(db, user_id)
    if hd_signal:
        signals.append(hd_signal)
        logger.info(f"[TensionEngine] Human Design signal: {hd_signal.tension}")
    
    # BaZi (secondary priority)
    bazi_signal = await extract_bazi_signal(db, user_id)
    if bazi_signal:
        signals.append(bazi_signal)
        logger.info(f"[TensionEngine] BaZi signal: {bazi_signal.tension}")
    
    # Enneagram (secondary priority)
    enneagram_signal = await extract_enneagram_signal(db, user_id)
    if enneagram_signal:
        signals.append(enneagram_signal)
        logger.info(f"[TensionEngine] Enneagram signal: {enneagram_signal.tension}")
    
    # Handle no signals case
    if not signals:
        logger.warning(f"[TensionEngine] No signals extracted for user {user_id}")
        return {
            "tension_label": "Unclear",
            "energy_title": "Something Building",
            "moment": "Something is building, but not fully clear yet.",
            "supporting_line": "Stay with it.",
            "micro_shift": "Notice what's happening without naming it.",
            "drivers": [],
            "driver_synthesis": "The signal is forming.",
            "confidence": 0.3,
            "intensity": 0.4,
            "fallback_used": True
        }
    
    # Cluster signals
    clustered = cluster_signals(signals)
    logger.info(f"[TensionEngine] Clustered into {len(clustered)} groups")
    
    # Select dominant tension
    dominant_cluster, dominant_signals, dominance_score = select_dominant_tension(clustered)
    logger.info(f"[TensionEngine] Dominant: {dominant_cluster} (score: {dominance_score:.2f})")
    
    # Generate seed for variety (changes daily)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    seed = int(hashlib.md5(f"{user_id}:{date_str}".encode()).hexdigest()[:8], 16)
    
    # Generate language
    cluster_info = TENSION_CLUSTERS.get(dominant_cluster, {})
    tension_label = cluster_info.get("label", "Tension")
    
    energy_title = generate_energy_title(dominant_cluster, seed)
    moment = generate_moment(dominant_cluster, seed)
    supporting_line = generate_supporting_line(dominant_signals, dominance_score, seed)
    micro_shift = generate_micro_shift(dominant_cluster, seed)
    drivers = generate_drivers(dominant_signals)
    driver_synthesis = generate_driver_synthesis(dominant_cluster, dominant_signals)
    
    # Calculate overall confidence and intensity
    avg_confidence = sum(s.confidence for s in dominant_signals) / len(dominant_signals)
    avg_intensity = sum(s.intensity for s in dominant_signals) / len(dominant_signals)
    
    return {
        "tension_label": tension_label,
        "energy_title": energy_title,
        "moment": moment,
        "supporting_line": supporting_line,
        "micro_shift": micro_shift,
        "drivers": drivers,
        "driver_synthesis": driver_synthesis,
        "confidence": round(avg_confidence, 2),
        "intensity": round(avg_intensity, 2),
        "fallback_used": False,
        "debug": {
            "cluster": dominant_cluster,
            "dominance_score": round(dominance_score, 2),
            "signal_count": len(signals),
            "signals_used": [s.source for s in dominant_signals]
        }
    }
