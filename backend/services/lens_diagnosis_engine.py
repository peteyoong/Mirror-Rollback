"""Lens Diagnosis Engine - Diagnosis Layer for Astrology & Human Design Today

Matches the Home diagnosis standard:
1. Diagnosis Title (short, tension-based)
2. Diagnosis Body (what's happening, where tension is, why now feels difficult)
3. Bridge Line (normalize experience)
4. Likely Misstep (what user will do wrong)
5. Better Move (grounded, non-preachy action)

V1: Initial implementation with HD gates + Gene Keys integration
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
import hashlib

logger = logging.getLogger(__name__)


# =============================================================================
# GENE KEY MAPPINGS - Gate Number = Gene Key Number (1:1 mapping)
# =============================================================================

# Import Gene Keys data
try:
    from data.gene_keys_data import GENE_KEYS
except ImportError:
    GENE_KEYS = {}


def get_gene_key_for_gate(gate_number: int) -> Dict[str, Any]:
    """
    Get Gene Key data for a gate number.
    Gate number = Gene Key number (1:1 mapping).
    """
    return GENE_KEYS.get(gate_number, {
        "gene_key": gate_number,
        "shadow": "Unknown",
        "gift": "Unknown",
        "siddhi": "Unknown",
        "shadow_keywords": [],
        "gift_keywords": [],
    })


# =============================================================================
# HD CENTER TENSION MAPPINGS
# =============================================================================

HD_CENTER_TENSIONS = {
    "Head": {
        "defined_tension": "pressure to figure things out",
        "undefined_tension": "getting lost in others' questions",
        "amplified_state": "mental overwhelm, can't stop thinking",
        "diagnosis_angle": "The mind wants answers. But not all questions need solving today.",
    },
    "Ajna": {
        "defined_tension": "stuck in one way of seeing",
        "undefined_tension": "pulled between too many perspectives",
        "amplified_state": "analysis paralysis, conceptual fog",
        "diagnosis_angle": "You're trying to think your way to certainty. That's not where it lives.",
    },
    "Throat": {
        "defined_tension": "pressure to express before ready",
        "undefined_tension": "speaking things that aren't yours",
        "amplified_state": "urge to say something, anything",
        "diagnosis_angle": "There's something you want to say or do. The question is timing.",
    },
    "G/Identity": {
        "defined_tension": "fixed sense of direction that feels limiting",
        "undefined_tension": "no clear sense of self or direction",
        "amplified_state": "identity confusion, who am I questions",
        "diagnosis_angle": "Who you are isn't in question. What you do next is.",
    },
    "Heart/Ego": {
        "defined_tension": "pressure to prove willpower",
        "undefined_tension": "over-promising to prove worth",
        "amplified_state": "pushing beyond capacity, willpower depletion",
        "diagnosis_angle": "You're trying to prove something. But to whom?",
    },
    "Sacral": {
        "defined_tension": "energy without direction",
        "undefined_tension": "not knowing when to stop",
        "amplified_state": "energy surge with no clear outlet",
        "diagnosis_angle": "There's energy available. The question is whether it has a real home.",
    },
    "Solar Plexus": {
        "defined_tension": "emotional waves distorting clarity",
        "undefined_tension": "absorbing others' emotions as your own",
        "amplified_state": "emotional intensity, highs and lows",
        "diagnosis_angle": "What you're feeling is real. But it may not be the whole truth.",
    },
    "Spleen": {
        "defined_tension": "instincts that don't translate to words",
        "undefined_tension": "holding onto things past their time",
        "amplified_state": "survival alertness, fear signals",
        "diagnosis_angle": "Something feels off. Trust it—but don't act from fear alone.",
    },
    "Root": {
        "defined_tension": "constant pressure to act",
        "undefined_tension": "absorbing external urgency",
        "amplified_state": "stress, adrenaline, can't relax",
        "diagnosis_angle": "The pressure is real. But the timeline might not be.",
    },
}


# =============================================================================
# HD TYPE TENSION PATTERNS
# =============================================================================

HD_TYPE_TENSIONS = {
    "Generator": {
        "core_tension": "waiting vs forcing",
        "shadow_pattern": "saying yes to keep momentum, even when gut says no",
        "misstep": "initiating before the response comes",
        "wise_move": "wait for the gut pull before committing",
    },
    "Manifesting Generator": {
        "core_tension": "speed vs correctness",
        "shadow_pattern": "moving so fast you skip the response check",
        "misstep": "changing direction without informing others",
        "wise_move": "respond first, then move—and let people know when you pivot",
    },
    "Projector": {
        "core_tension": "seeing vs being seen",
        "shadow_pattern": "offering guidance before being invited",
        "misstep": "giving advice nobody asked for",
        "wise_move": "wait for recognition before sharing what you see",
    },
    "Manifestor": {
        "core_tension": "impact vs isolation",
        "shadow_pattern": "moving without informing, creating resistance",
        "misstep": "acting without letting others know what's coming",
        "wise_move": "inform before you act—not for permission, for flow",
    },
    "Reflector": {
        "core_tension": "sampling vs deciding",
        "shadow_pattern": "deciding too fast, before the full picture forms",
        "misstep": "making permanent choices on temporary feelings",
        "wise_move": "wait. big decisions need a full lunar cycle",
    },
}


# =============================================================================
# HD AUTHORITY TENSION PATTERNS
# =============================================================================

HD_AUTHORITY_TENSIONS = {
    "Emotional": {
        "timing_pattern": "clarity comes in waves, not instantly",
        "shadow_pattern": "deciding at emotional peaks or valleys",
        "diagnosis_hint": "You feel strongly. But strong isn't the same as clear.",
    },
    "Sacral": {
        "timing_pattern": "body responds in the moment",
        "shadow_pattern": "overriding gut response with logic",
        "diagnosis_hint": "Your body knows. The question is whether you're listening.",
    },
    "Splenic": {
        "timing_pattern": "instant knowing, once only",
        "shadow_pattern": "second-guessing the first hit",
        "diagnosis_hint": "You knew immediately. Everything after is doubt.",
    },
    "Ego": {
        "timing_pattern": "heart commitment or nothing",
        "shadow_pattern": "promising what heart doesn't want",
        "diagnosis_hint": "If your heart's not in it, you can't sustain it.",
    },
    "Self-Projected": {
        "timing_pattern": "clarity through speaking",
        "shadow_pattern": "thinking without talking it through",
        "diagnosis_hint": "You won't know until you hear yourself say it.",
    },
    "Mental": {
        "timing_pattern": "clarity through trusted sounding boards",
        "shadow_pattern": "deciding alone without external input",
        "diagnosis_hint": "Talk to someone you trust. Not for their answer—for yours.",
    },
    "Lunar": {
        "timing_pattern": "full cycle needed for major decisions",
        "shadow_pattern": "rushing to certainty too fast",
        "diagnosis_hint": "This needs more time than feels comfortable.",
    },
}


# =============================================================================
# GATE-BASED DIAGNOSIS TEMPLATES
# =============================================================================

def build_gate_diagnosis(
    gate_number: int,
    is_natal: bool,
    is_transit: bool,
    center: str,
    user_id: str,
    date_str: str
) -> Dict[str, Any]:
    """
    Build a diagnosis entry for a specific gate.
    """
    gene_key = get_gene_key_for_gate(gate_number)
    
    shadow = gene_key.get("shadow", "Unknown")
    gift = gene_key.get("gift", "Unknown")
    
    # Determine activation type
    if is_natal and is_transit:
        activation_type = "double_activated"
        intensity = "high"
    elif is_transit:
        activation_type = "transit"
        intensity = "medium"
    else:
        activation_type = "natal"
        intensity = "base"
    
    return {
        "gate": gate_number,
        "gene_key": gate_number,
        "shadow": shadow,
        "gift": gift,
        "center": center,
        "activation_type": activation_type,
        "intensity": intensity,
        "is_natal": is_natal,
        "is_transit": is_transit,
    }


# =============================================================================
# MAIN HD DIAGNOSIS GENERATOR
# =============================================================================

async def generate_hd_today_diagnosis(
    db,
    user_id: str,
    hd_data: Dict[str, Any],
    active_gates: List[int],
    transit_gates: List[int],
    defined_centers: List[str],
    undefined_centers: List[str]
) -> Dict[str, Any]:
    """
    Generate Human Design Today diagnosis following Home standard.
    
    Returns diagnosis with:
    - title (tension-based)
    - body (what's happening internally)
    - bridge (normalize experience)
    - misstep (what user will do wrong)
    - better_move (grounded action)
    - active_signals (collapsible)
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    hd_type = hd_data.get("type", "Generator")
    authority = hd_data.get("authority", "Sacral")
    
    # Normalize authority for lookup
    authority_key = authority.split()[0] if authority else "Sacral"
    if "emotional" in authority.lower():
        authority_key = "Emotional"
    elif "sacral" in authority.lower():
        authority_key = "Sacral"
    elif "splenic" in authority.lower():
        authority_key = "Splenic"
    elif "ego" in authority.lower() or "heart" in authority.lower():
        authority_key = "Ego"
    elif "self" in authority.lower():
        authority_key = "Self-Projected"
    elif "mental" in authority.lower() or "environment" in authority.lower():
        authority_key = "Mental"
    elif "lunar" in authority.lower() or "moon" in authority.lower():
        authority_key = "Lunar"
    
    # Get type and authority tensions
    type_tension = HD_TYPE_TENSIONS.get(hd_type, HD_TYPE_TENSIONS["Generator"])
    auth_tension = HD_AUTHORITY_TENSIONS.get(authority_key, HD_AUTHORITY_TENSIONS["Sacral"])
    
    # Build gate diagnoses
    gate_diagnoses = []
    for gate in active_gates[:5]:  # Top 5 most relevant
        is_transit = gate in transit_gates
        is_natal = gate in active_gates and gate not in transit_gates
        
        # Determine center (simplified mapping)
        center = get_center_for_gate(gate)
        
        diagnosis = build_gate_diagnosis(
            gate_number=gate,
            is_natal=is_natal,
            is_transit=is_transit,
            center=center,
            user_id=user_id,
            date_str=today
        )
        gate_diagnoses.append(diagnosis)
    
    # Find dominant tension from gates
    dominant_gate = gate_diagnoses[0] if gate_diagnoses else None
    
    # Build the diagnosis
    if dominant_gate:
        shadow = dominant_gate["shadow"]
        gift = dominant_gate["gift"]
        center = dominant_gate["center"]
        center_tension = HD_CENTER_TENSIONS.get(center, HD_CENTER_TENSIONS["Sacral"])
        
        # Create tension-based title
        title = f"Between {shadow} and {gift}"
        
        # Create body that describes internal experience
        body = f"{center_tension['diagnosis_angle']} Today, Gate {dominant_gate['gate']} is active—the tension between {shadow.lower()} and {gift.lower()}. {auth_tension['diagnosis_hint']}"
        
        # Bridge line normalizes
        bridge = f"This is your design working, not failing. The {shadow.lower()} feeling is real—but so is the {gift.lower()} waiting on the other side."
        
        # Misstep based on type
        misstep = type_tension["misstep"]
        
        # Better move based on type
        better_move = type_tension["wise_move"]
    else:
        # Fallback when no specific gate data
        title = "Something Is Processing"
        body = f"{auth_tension['diagnosis_hint']} {type_tension['shadow_pattern'].capitalize()}—that's the pattern to watch today."
        bridge = "This is how your design works. Not a problem to fix."
        misstep = type_tension["misstep"]
        better_move = type_tension["wise_move"]
    
    # Build signals for collapsible section
    signals = {
        "active_gates": [
            {
                "gate": g["gate"],
                "shadow": g["shadow"],
                "gift": g["gift"],
                "center": g["center"],
                "activation": g["activation_type"],
            }
            for g in gate_diagnoses
        ],
        "defined_centers": defined_centers,
        "undefined_centers": undefined_centers,
        "type": hd_type,
        "authority": authority,
    }
    
    return {
        "success": True,
        "lens": "human_design",
        "date": today,
        "title": title,
        "body": body,
        "bridge": bridge,
        "misstep": misstep,
        "better_move": better_move,
        "signals": signals,
        "debug": {
            "dominant_gate": dominant_gate["gate"] if dominant_gate else None,
            "type_tension": type_tension["core_tension"],
            "authority_key": authority_key,
            "gate_count": len(gate_diagnoses),
        }
    }


def get_center_for_gate(gate: int) -> str:
    """
    Map gate number to its center.
    Simplified mapping based on HD gate-center relationships.
    """
    # Head Center gates
    if gate in [64, 61, 63]:
        return "Head"
    # Ajna Center gates
    if gate in [47, 24, 4, 17, 43, 11]:
        return "Ajna"
    # Throat Center gates
    if gate in [62, 23, 56, 35, 12, 45, 33, 8, 31, 20, 16]:
        return "Throat"
    # G/Identity Center gates
    if gate in [7, 1, 13, 25, 46, 2, 15, 10]:
        return "G/Identity"
    # Heart/Ego Center gates
    if gate in [21, 40, 26, 51]:
        return "Heart/Ego"
    # Sacral Center gates
    if gate in [5, 14, 29, 59, 9, 3, 42, 27, 34]:
        return "Sacral"
    # Solar Plexus Center gates
    if gate in [6, 37, 22, 36, 30, 55, 49]:
        return "Solar Plexus"
    # Spleen Center gates
    if gate in [48, 57, 44, 50, 32, 28, 18]:
        return "Spleen"
    # Root Center gates
    if gate in [58, 38, 54, 53, 60, 52, 19, 39, 41]:
        return "Root"
    
    return "Sacral"  # Default


# =============================================================================
# ASTROLOGY DIAGNOSIS GENERATOR
# =============================================================================

ASTRO_TRANSIT_TENSIONS = {
    "Sun": {
        "theme": "identity and vitality",
        "tension": "who you're being vs who you think you should be",
        "diagnosis_angle": "Something about how you're showing up feels off. Or too on.",
    },
    "Moon": {
        "theme": "emotional needs and security",
        "tension": "what you need vs what you're getting",
        "diagnosis_angle": "There's an emotional undertow today. It's real, but it's moving.",
    },
    "Mercury": {
        "theme": "mind and communication",
        "tension": "what you're thinking vs what you're saying",
        "diagnosis_angle": "Your mind is active. The question is whether it's helping or spinning.",
    },
    "Venus": {
        "theme": "values and connection",
        "tension": "what you want vs what you're settling for",
        "diagnosis_angle": "Something about what you value or desire is in focus.",
    },
    "Mars": {
        "theme": "drive and assertion",
        "tension": "pushing forward vs knowing when to hold",
        "diagnosis_angle": "There's energy to act. The question is whether it's the right action.",
    },
    "Jupiter": {
        "theme": "growth and meaning",
        "tension": "expansion vs overreach",
        "diagnosis_angle": "Something wants to grow. But growth has a right size.",
    },
    "Saturn": {
        "theme": "structure and responsibility",
        "tension": "what's required vs what feels heavy",
        "diagnosis_angle": "There's a weight here. It's not punishment—it's material.",
    },
    "Uranus": {
        "theme": "change and liberation",
        "tension": "freedom vs stability",
        "diagnosis_angle": "Something wants to break free. Or break apart.",
    },
    "Neptune": {
        "theme": "dreams and illusion",
        "tension": "vision vs confusion",
        "diagnosis_angle": "The edges are blurry. That's not always bad, but it's not always trustworthy either.",
    },
    "Pluto": {
        "theme": "power and transformation",
        "tension": "control vs surrender",
        "diagnosis_angle": "Something is transforming. You don't get to skip that process.",
    },
}


ASTRO_HOUSE_MEANINGS = {
    1: {"life_area": "self and presence", "shows_up": "how you show up"},
    2: {"life_area": "resources and security", "shows_up": "money, worth, what you have"},
    3: {"life_area": "mind and communication", "shows_up": "conversations, learning, siblings"},
    4: {"life_area": "home and roots", "shows_up": "family, where you feel safe"},
    5: {"life_area": "creativity and pleasure", "shows_up": "fun, romance, self-expression"},
    6: {"life_area": "work and health", "shows_up": "daily routines, service, body"},
    7: {"life_area": "relationships", "shows_up": "partnerships, one-on-one dynamics"},
    8: {"life_area": "depth and shared resources", "shows_up": "intimacy, other people's money, loss"},
    9: {"life_area": "expansion and belief", "shows_up": "travel, philosophy, what you believe"},
    10: {"life_area": "career and public role", "shows_up": "reputation, ambition, authority"},
    11: {"life_area": "community and future", "shows_up": "groups, hopes, where you're headed"},
    12: {"life_area": "hidden and unconscious", "shows_up": "what's beneath the surface, solitude"},
}


async def generate_astro_today_diagnosis(
    db,
    user_id: str,
    chart_data: Dict[str, Any],
    transits: List[Dict[str, Any]],
    active_houses: List[int]
) -> Dict[str, Any]:
    """
    Generate Astrology Today diagnosis following Home standard.
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Find the most significant transit
    dominant_transit = None
    for transit in transits[:5]:
        planet = transit.get("planet", "")
        if planet in ASTRO_TRANSIT_TENSIONS:
            dominant_transit = transit
            break
    
    if not dominant_transit and transits:
        dominant_transit = transits[0]
    
    # Get primary house activation
    primary_house = active_houses[0] if active_houses else 1
    house_meaning = ASTRO_HOUSE_MEANINGS.get(primary_house, ASTRO_HOUSE_MEANINGS[1])
    
    if dominant_transit:
        planet = dominant_transit.get("planet", "Moon")
        aspect = dominant_transit.get("aspect", "conjunction")
        natal_planet = dominant_transit.get("natal_planet", "")
        
        planet_tension = ASTRO_TRANSIT_TENSIONS.get(planet, ASTRO_TRANSIT_TENSIONS["Moon"])
        
        # Build diagnosis
        title = f"{planet_tension['theme'].title()} in Motion"
        
        body = f"{planet_tension['diagnosis_angle']} This lands in your {house_meaning['life_area']}—{house_meaning['shows_up']}. The tension: {planet_tension['tension']}."
        
        bridge = "This transit is passing through. What it stirs up is yours to work with."
        
        misstep = f"reacting to the {planet_tension['theme']} pressure before understanding what it's asking"
        
        better_move = f"notice what's activated in your {house_meaning['life_area']}. let it be information before it becomes action."
    else:
        # Fallback
        title = "Something Is Shifting"
        body = f"The sky is active in your {house_meaning['life_area']}. Something about {house_meaning['shows_up']} wants attention."
        bridge = "Not all transits feel dramatic. Sometimes it's just a nudge."
        misstep = "ignoring the subtle signals"
        better_move = "pay attention to what keeps coming up"
    
    # Build signals for collapsible
    signals = {
        "transits": [
            {
                "planet": t.get("planet"),
                "aspect": t.get("aspect"),
                "natal_planet": t.get("natal_planet"),
                "house": t.get("house"),
            }
            for t in transits[:5]
        ],
        "active_houses": active_houses[:3],
        "house_meanings": [
            {
                "house": h,
                "area": ASTRO_HOUSE_MEANINGS.get(h, {}).get("life_area", ""),
            }
            for h in active_houses[:3]
        ],
    }
    
    return {
        "success": True,
        "lens": "astrology",
        "date": today,
        "title": title,
        "body": body,
        "bridge": bridge,
        "misstep": misstep,
        "better_move": better_move,
        "signals": signals,
        "debug": {
            "dominant_planet": dominant_transit.get("planet") if dominant_transit else None,
            "primary_house": primary_house,
            "transit_count": len(transits),
        }
    }
