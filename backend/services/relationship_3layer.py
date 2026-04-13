"""
Relationship Insight Engine V5 — 3-Layer Architecture
======================================================

Layer 1 = STORY (Synthesis) — emotional, concise, no technical language
Layer 2 = PATTERNS (Behaviors) — "this is exactly what happens"
Layer 3 = SIGNALS (Proof) — "how does it know this??"

This wraps the existing relationship_insight_engine logic into
the new 3-layer output. It does NOT rewrite Human Design logic.
"""

import logging
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


# =============================================================================
# STORY TEMPLATES — Emotional synthesis, no system names
# =============================================================================

STORY_TEMPLATES = {
    ("initiator", "reflector"): {
        "headlines": [
            "One of you reaches. The other deepens what arrives.",
            "This relationship moves between starting and landing.",
            "You create openings. They complete them — if you let them.",
        ],
        "summaries": [
            "There's a pull between forward motion and depth here. You bring energy, they bring stillness. The tension between those two forces is what makes this connection real — and sometimes frustrating.",
            "This connection has a rhythm to it: one moves, the other receives. The friction isn't about who's right — it's about different speeds trying to find the same moment.",
        ],
    },
    ("reflector", "initiator"): {
        "headlines": [
            "They bring motion. You bring depth.",
            "This relationship draws things out of you that wouldn't surface alone.",
            "You hold still. They keep reaching. That's the dynamic.",
        ],
        "summaries": [
            "Without their push, you'd stay internal. Their energy draws out your response — and sometimes that feels like pressure, even when it's a gift.",
            "This connection challenges your pace. They move before you're ready, and something about that friction is exactly what pulls the real you to the surface.",
        ],
    },
    ("momentum_carrier", "attunement_holder"): {
        "headlines": [
            "Force meets awareness here.",
            "You carry energy forward. They sense what that energy creates.",
            "This relationship is a constant negotiation between speed and sensing.",
        ],
        "summaries": [
            "You build by moving. They build by feeling. Neither is wrong, but the gap between your speeds creates real friction — and real growth.",
            "This connection slows you down enough to notice what you'd miss. That's uncomfortable, and it's exactly what makes it valuable.",
        ],
    },
    ("attunement_holder", "momentum_carrier"): {
        "headlines": [
            "They move. You sense. The gap is the connection.",
            "This relationship teaches you that sensing can happen while moving.",
            "You read the room. They change it. That's the dance.",
        ],
        "summaries": [
            "Their force gives you something to work with. Your sensing gives their momentum direction. The friction is about timing — theirs is faster than yours.",
            "This connection asks you to move before you've finished reading. That's uncomfortable — and it's where the growth lives.",
        ],
    },
    ("certainty_seeker", "sensor"): {
        "headlines": [
            "You need to know. They need to feel.",
            "Facts meet impressions in this connection.",
            "This relationship lives in the gap between clarity and intuition.",
        ],
        "summaries": [
            "You seek ground. They trust what can't be named. That difference creates tension — and also a wider field of knowing than either of you has alone.",
            "This connection challenges what 'knowing' means. Their sensing reaches places your certainty can't — and your structure gives form to what they feel.",
        ],
    },
    ("sensor", "certainty_seeker"): {
        "headlines": [
            "They ground what you feel into something real.",
            "This connection turns impressions into action.",
            "You feel it. They name it. That's the gift.",
        ],
        "summaries": [
            "Without them, your sensing stays private. Their directness gives your impressions shape and weight. The friction is about translation — theirs is literal, yours is felt.",
            "This relationship asks you to make the invisible visible. Their structure meets your texture, and together you cover more territory than either could alone.",
        ],
    },
    ("expresser", "absorber"): {
        "headlines": [
            "You show what you feel. They hold what they hold.",
            "This connection doesn't match in kind — and that's its power.",
            "Visibility meets depth here. It's intense by design.",
        ],
        "summaries": [
            "What you express lands somewhere real in them. It's not mirrored back — it's received at a depth most people can't reach. That can feel like silence, but it's actually the opposite.",
            "This relationship challenges you to show without needing matching. Their stillness isn't absence — it's absorption. What you give disappears into something larger.",
        ],
    },
    ("absorber", "expresser"): {
        "headlines": [
            "They model showing. You model receiving.",
            "This connection draws out what you hold.",
            "Your small expressions carry more weight here than anywhere else.",
        ],
        "summaries": [
            "Their visibility invites yours. Not by demanding it, but by modeling what it looks like to let the inside out. Your small signals mean more to them than your silence.",
            "This connection asks for surface. Not everything — just something. One honest signal from you changes the entire dynamic.",
        ],
    },
    ("action_taker", "atmospheric_reader"): {
        "headlines": [
            "You change the room. They read what you've changed.",
            "Action meets perception in this connection.",
            "This relationship shows you what you can't see about your own impact.",
        ],
        "summaries": [
            "You act. They perceive the consequences. Without them, you'd never know what your motion actually creates. The friction is about pace — you move before they've finished reading.",
            "This connection gives your action a mirror. Their perception catches what your momentum misses, and that feedback loop is what makes this dynamic powerful.",
        ],
    },
    ("atmospheric_reader", "action_taker"): {
        "headlines": [
            "They create change. You perceive what change creates.",
            "This connection teaches you that reading can follow action.",
            "You sense. They move. The room is never the same twice.",
        ],
        "summaries": [
            "Their action gives you something to read. Without their motion, you'd be sensing a static room. The friction is that they change the field before you've finished perceiving it.",
            "This relationship challenges your timing. Sometimes the action comes first and the sensing follows — and that's okay.",
        ],
    },
    ("container", "porous"): {
        "headlines": [
            "You hold edges. They blur them.",
            "Structure meets permeability in this connection.",
            "This relationship lives at the boundary between holding and flowing.",
        ],
        "summaries": [
            "Your steadiness gives them ground. Their openness softens your edges. The tension is real: you protect what they absorb, and neither way is wrong.",
            "This connection asks you to open a door in what you've been protecting. Not tear down walls — just let something through.",
        ],
    },
    ("porous", "container"): {
        "headlines": [
            "They hold steady. You feel everything.",
            "This connection gives you something to push against.",
            "Boundaries aren't disconnection — that's what this teaches.",
        ],
        "summaries": [
            "Their structure isn't rejection. It's something you can lean on without falling through. This relationship teaches you that edges can be safe.",
            "This connection challenges your porosity. Their containment models something you need — not to become, but to borrow when you need ground.",
        ],
    },
}

# Default story for unmapped pairs
DEFAULT_STORY = {
    "headlines": [
        "Something real is happening between you two.",
        "This connection activates a dynamic that's worth paying attention to.",
        "There's a reason this relationship keeps pulling you in.",
    ],
    "summaries": [
        "This relationship pulls you into depth and intensity quickly. It doesn't stay surface-level — it activates something real between you.",
        "There's a dynamic here that's bigger than either of you expected. It's not always comfortable, but it's always honest.",
    ],
}


# =============================================================================
# PATTERN TEMPLATES — Observable behaviors, real-life dynamics
# =============================================================================

PATTERN_TEMPLATES = {
    ("initiator", "reflector"): {
        "what_happens": [
            "One of you starts conversations, plans, or decisions — the other needs time to land before responding",
            "You move at different speeds, and the gap between them creates a recurring tension",
            "The one who moves first often feels like they're pulling. The one who responds feels like they're being rushed",
            "There's a rhythm of reaching and retreating that plays out in decisions, plans, and emotional moments",
        ],
        "tensions": [
            "Initiation gets misread as pressure. Reflection gets misread as disinterest",
            "When one person adds to a topic before the other has responded, the space gets crowded",
            "Silence after a bid for connection can feel like rejection — even when it's just processing",
        ],
        "gifts": [
            "They show you what your forward motion misses — the things that only become visible in stillness",
            "You pull things out of them that wouldn't surface without your reaching",
            "Together, you cover both the start and the landing — most connections only do one",
        ],
    },
    ("reflector", "initiator"): {
        "what_happens": [
            "They bring ideas, plans, or energy — you need a moment before you can meet it",
            "You process internally before responding, which can feel like delay to them",
            "Their energy draws out your response, but on a timeline that doesn't always match",
            "You often have something valuable to add — but the moment has passed by the time you're ready",
        ],
        "tensions": [
            "Their speed can crowd your thinking, making it harder to respond authentically",
            "You may hold back not because you don't care, but because the response isn't fully formed yet",
            "Their follow-up questions can feel like interrogation when you're still forming your first answer",
        ],
        "gifts": [
            "Their energy pulls you forward into expression you wouldn't choose on your own",
            "You give depth to everything they start — what they initiate, you complete",
            "Your stillness teaches them that some things don't need to be rushed",
        ],
    },
    ("momentum_carrier", "attunement_holder"): {
        "what_happens": [
            "You tend to build through doing, while they build through sensing — and the pace difference is constant",
            "Decisions happen at different speeds between you: yours is action, theirs is calibration",
            "You may feel slowed down. They may feel steamrolled. Both experiences are valid",
            "The friction isn't about disagreement — it's about different operating speeds",
        ],
        "tensions": [
            "Your momentum can override what they're sensing, causing them to withdraw",
            "Their need to attune before acting can feel like hesitation or passivity to you",
            "When you push through what they're reading, trust erodes — even when the action is right",
        ],
        "gifts": [
            "They catch nuance your momentum would miss — the thing you didn't see because you were moving",
            "You give their sensing something to work with — without your force, nothing would move",
            "Together you create informed momentum — force with feeling",
        ],
    },
    ("attunement_holder", "momentum_carrier"): {
        "what_happens": [
            "They carry energy forward and you sense what that energy creates — a constant feedback loop",
            "You adjust to their pace, but it often feels like chasing",
            "Your sensing is valuable, but it operates on a slower timeline than their action",
            "You often know what needs adjustment, but by the time you articulate it, the moment has passed",
        ],
        "tensions": [
            "Their speed can overwhelm your sensing, making it hard to articulate what you're picking up",
            "You may withdraw when the pace gets too fast, which reads as disengagement",
            "Your timing intelligence gets overridden by their urgency",
        ],
        "gifts": [
            "Their force gives you something concrete to shape — without their action, your sensing has no object",
            "You give their momentum direction and awareness",
            "Your presence reminds them that awareness is part of action, not opposed to it",
        ],
    },
}

# Default patterns for unmapped pairs
DEFAULT_PATTERNS = {
    "what_happens": [
        "You tend to approach situations from fundamentally different angles — and that creates a dynamic",
        "There's a recurring dance between how each of you processes decisions and emotions",
        "One of you leads in certain areas while the other leads in others — and those domains shift",
        "The way you communicate doesn't always align, which creates both friction and depth",
    ],
    "tensions": [
        "Different processing speeds or styles can be misread as lack of care or respect",
        "What feels natural to one person can feel like pressure or absence to the other",
        "The gap between your operating modes is where most of the friction lives",
    ],
    "gifts": [
        "They activate something in you that wouldn't surface in any other connection",
        "You offer them a perspective or quality they can't access alone",
        "Together, you cover a wider range of human experience than either could separately",
    ],
}


def generate_3layer_insight(
    user_type: str,
    other_type: str,
    other_name: str,
    deep_content: Dict[str, Any],
    seed_hash: int,
    hd_signals: Optional[List[Dict]] = None,
    astro_signals: Optional[Dict] = None,
    bazi_signals: Optional[Dict] = None,
    enneagram_signals: Optional[Dict] = None,
    numerology_signals: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Generate the 3-layer relationship insight structure.
    
    Layer 1 = Story (synthesis)
    Layer 2 = Patterns (behaviors)
    Layer 3 = Signals (proof)
    """
    
    pair_key = (user_type, other_type)
    
    # =========================================================================
    # LAYER 1: STORY
    # =========================================================================
    story_template = STORY_TEMPLATES.get(pair_key, DEFAULT_STORY)
    headlines = story_template["headlines"]
    summaries = story_template["summaries"]
    
    story = {
        "headline": headlines[seed_hash % len(headlines)],
        "summary": summaries[seed_hash % len(summaries)],
    }
    
    # =========================================================================
    # LAYER 2: PATTERNS
    # =========================================================================
    pattern_template = PATTERN_TEMPLATES.get(pair_key)
    
    if not pattern_template:
        # Build from existing deep_content
        what_happens = []
        tensions_list = []
        gifts_list = []
        
        # Extract from friction/tension/gift text
        if deep_content.get("friction"):
            for line in deep_content["friction"].split("\n"):
                line = line.strip()
                if line:
                    what_happens.append(line)
        
        if deep_content.get("tension"):
            for line in deep_content["tension"].split("\n"):
                line = line.strip()
                if line:
                    tensions_list.append(line)
        
        if deep_content.get("gift"):
            for line in deep_content["gift"].split("\n"):
                line = line.strip()
                if line:
                    gifts_list.append(line)
        
        # Fallback
        if not what_happens:
            what_happens = DEFAULT_PATTERNS["what_happens"]
        if not tensions_list:
            tensions_list = DEFAULT_PATTERNS["tensions"]
        if not gifts_list:
            gifts_list = DEFAULT_PATTERNS["gifts"]
        
        pattern_template = {
            "what_happens": what_happens[:5],
            "tensions": tensions_list[:3],
            "gifts": gifts_list[:3],
        }
    
    # Select subset for variety
    wh = pattern_template["what_happens"]
    start = seed_hash % max(1, len(wh) - 2)
    selected_wh = wh[start:start + 4] if len(wh) > 3 else wh[:4]
    
    tn = pattern_template["tensions"]
    selected_tn = tn[:3]
    
    gf = pattern_template["gifts"]
    selected_gf = gf[:3]
    
    patterns = {
        "what_happens": selected_wh,
        "tensions": selected_tn,
        "gifts": selected_gf,
    }
    
    # =========================================================================
    # LAYER 3: SIGNALS (proof layer)
    # =========================================================================
    signals = {
        "human_design": hd_signals or [],
        "astrology": astro_signals or {"attraction": [], "tension": [], "growth": []},
        "bazi": bazi_signals or {"strengthens": [], "drains": [], "activates_growth": []},
        "enneagram": enneagram_signals or {"gift_to_them": [], "gift_to_you": []},
        "numerology": numerology_signals or {"complementarity": [], "missing_traits": []},
    }
    
    return {
        "success": True,
        "version": "v5_3layer",
        "other_name": other_name,
        "story": story,
        "patterns": patterns,
        "signals": signals,
        "dynamic": {
            "user_type": user_type,
            "other_type": other_type,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
