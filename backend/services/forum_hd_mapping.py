"""
Forum HD Mapping Service
========================

Computes "How they map to me" using Human Design channel-completion logic.
Returns human-readable interpretations, not raw HD data.

For two people:
1. Get their active HD gates (design + personality)
2. Find completed channels between them (electromagnetic connections)
3. Generate relational interpretations

"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


# HD Channel definitions with relational themes
HD_CHANNELS = {
    "1-8": {
        "name": "Inspiration",
        "theme": "creative direction, self-expression, leading through example",
        "relational": "creative momentum",
    },
    "2-14": {
        "name": "The Beat",
        "theme": "being called, higher power direction, natural response",
        "relational": "shared calling",
    },
    "3-60": {
        "name": "Mutation",
        "theme": "innovation, accepting limits, new beginnings",
        "relational": "navigating change together",
    },
    "4-63": {
        "name": "Logic",
        "theme": "mental pressure, doubt leading to answers, problem-solving",
        "relational": "thinking through things together",
    },
    "5-15": {
        "name": "Rhythm",
        "theme": "universal timing, natural flow, accepting life's rhythms",
        "relational": "shared flow and timing",
    },
    "6-59": {
        "name": "Intimacy",
        "theme": "emotional bonding, reproduction, breaking barriers",
        "relational": "deep emotional connection",
    },
    "7-31": {
        "name": "The Alpha",
        "theme": "leadership for the future, democratic influence",
        "relational": "natural leadership dynamic",
    },
    "9-52": {
        "name": "Concentration",
        "theme": "focused attention, stillness, determination",
        "relational": "grounding each other",
    },
    "10-20": {
        "name": "Awakening",
        "theme": "authentic expression, being yourself in the moment",
        "relational": "mutual authenticity",
    },
    "10-34": {
        "name": "Exploration",
        "theme": "following conviction, empowered self-direction",
        "relational": "independent connection",
    },
    "10-57": {
        "name": "Perfected Form",
        "theme": "intuitive self-love, survival through authenticity",
        "relational": "intuitive understanding",
    },
    "11-56": {
        "name": "Curiosity",
        "theme": "seeking and sharing experiences, stimulation",
        "relational": "shared curiosity",
    },
    "12-22": {
        "name": "Openness",
        "theme": "social emotional expression, mood and charm",
        "relational": "emotional expression together",
    },
    "13-33": {
        "name": "The Prodigal",
        "theme": "witnessing and sharing experiences, listener and storyteller",
        "relational": "deep listening",
    },
    "16-48": {
        "name": "The Wavelength",
        "theme": "talent expression, depth mastery, skill development",
        "relational": "appreciating each other's depth",
    },
    "17-62": {
        "name": "Acceptance",
        "theme": "organizational thinking, detail and pattern",
        "relational": "thinking things through",
    },
    "18-58": {
        "name": "Judgment",
        "theme": "correction, perfection drive, improving what exists",
        "relational": "growth through feedback",
    },
    "19-49": {
        "name": "Synthesis",
        "theme": "tribal needs, revolution, sensitivity to belonging",
        "relational": "shared values and boundaries",
    },
    "20-34": {
        "name": "Charisma",
        "theme": "busy-ness, thought into action, immediate response",
        "relational": "active energy together",
    },
    "20-57": {
        "name": "The Brainwave",
        "theme": "intuitive knowing in the now, penetrating awareness",
        "relational": "intuitive understanding",
    },
    "21-45": {
        "name": "The Money Line",
        "theme": "materialism, control, willpower for resources",
        "relational": "resource dynamics",
    },
    "23-43": {
        "name": "Structuring",
        "theme": "genius insight, individual knowing, unique perspective",
        "relational": "unique ideas together",
    },
    "24-61": {
        "name": "Awareness",
        "theme": "mental pressure, knowing through mystery, inspiration",
        "relational": "shared inspiration",
    },
    "25-51": {
        "name": "Initiation",
        "theme": "competitive spirit, initiating others, shock and spirit",
        "relational": "challenging each other",
    },
    "26-44": {
        "name": "Surrender",
        "theme": "transmitter, influence through memory and pattern",
        "relational": "influence dynamics",
    },
    "27-50": {
        "name": "Preservation",
        "theme": "nurturing, values, taking care of what matters",
        "relational": "mutual care",
    },
    "28-38": {
        "name": "Struggle",
        "theme": "stubbornness, individual purpose, fighting for meaning",
        "relational": "purpose alignment",
    },
    "29-46": {
        "name": "Discovery",
        "theme": "commitment, embodiment, saying yes to experience",
        "relational": "shared commitment",
    },
    "30-41": {
        "name": "Recognition",
        "theme": "feeling pressure, desire, new emotional experiences",
        "relational": "emotional exploration",
    },
    "32-54": {
        "name": "Transformation",
        "theme": "ambition, transformation, drive for improvement",
        "relational": "growth together",
    },
    "34-57": {
        "name": "Power",
        "theme": "intuitive power, survival energy, in-the-moment response",
        "relational": "instinctive trust",
    },
    "35-36": {
        "name": "Transitoriness",
        "theme": "emotional adventure, seeking new experiences",
        "relational": "adventure together",
    },
    "37-40": {
        "name": "Community",
        "theme": "bargains, loyalty, agreements and expectations",
        "relational": "trust and agreements",
    },
    "39-55": {
        "name": "Emoting",
        "theme": "emotional spirit, provocation, melancholy and abundance",
        "relational": "emotional depth",
    },
    "42-53": {
        "name": "Maturation",
        "theme": "cyclic growth, beginning and completing",
        "relational": "completing together",
    },
    "47-64": {
        "name": "Abstraction",
        "theme": "mental processing, making sense of confusion",
        "relational": "making sense together",
    },
}


# Interpretation templates for different channel types
CHANNEL_INTERPRETATIONS = {
    # High-connection channels
    "37-40": {
        "headline": "You naturally create strong agreements with each other",
        "description": "There's a real sense of loyalty and mutual backing here. Things may feel solid quickly.",
        "what_works": "Trust, mutual support, shared commitment",
        "what_to_watch": "Make expectations explicit. Don't assume alignment means agreement.",
    },
    "6-59": {
        "headline": "Deep emotional intimacy flows between you",
        "description": "There's potential for profound emotional bonding. Barriers tend to dissolve.",
        "what_works": "Vulnerability, emotional honesty, presence",
        "what_to_watch": "Maintain healthy boundaries. Intensity needs space too.",
    },
    "10-20": {
        "headline": "You encourage each other's authenticity",
        "description": "When together, you both feel more permission to be yourselves in the moment.",
        "what_works": "Honest expression, being present, supporting truth",
        "what_to_watch": "Don't confuse authenticity with always agreeing. Different truths can coexist.",
    },
    "13-33": {
        "headline": "You're natural witnesses for each other",
        "description": "One speaks, the other deeply listens. Stories matter here.",
        "what_works": "Deep listening, sharing experiences, holding space",
        "what_to_watch": "Balance who speaks and who listens. Both roles need time.",
    },
    "27-50": {
        "headline": "You naturally care for what matters to each other",
        "description": "There's mutual nurturing here—a sense of looking after shared values.",
        "what_works": "Nurturing, protecting what matters, shared responsibility",
        "what_to_watch": "Don't over-give. Check that care flows both ways.",
    },
    # Default for channels without specific interpretation
    "default": {
        "headline": "There's a natural energetic completion between you",
        "description": "Something clicks when you're together that neither of you has alone.",
        "what_works": "Presence, allowing the dynamic to unfold naturally",
        "what_to_watch": "Notice what emerges. Some completions bring intensity that needs awareness.",
    },
}


def get_user_gates(user_data: Dict[str, Any], chart_data: Dict[str, Any] = None) -> List[int]:
    """
    Extract all active gates from a user's Human Design data.
    Prioritizes chart_data if available (from charts collection).
    """
    gates = set()
    
    # Primary source: charts collection data
    if chart_data:
        hd = chart_data.get("human_design", {})
        
        # Active gates (computed list)
        active_gates = hd.get("active_gates", [])
        for g in active_gates:
            if isinstance(g, int):
                gates.add(g)
            elif isinstance(g, str):
                try:
                    gates.add(int(g))
                except:
                    pass
        
        # Extract from personality/design sections as backup
        for section in ["personality", "design"]:
            section_data = hd.get(section, {})
            if isinstance(section_data, dict):
                for planet_data in section_data.values():
                    if isinstance(planet_data, dict):
                        gate_info = planet_data.get("gate", {})
                        if isinstance(gate_info, dict):
                            gate_num = gate_info.get("gate")
                            if gate_num:
                                gates.add(int(gate_num))
        
        # Also check defined_channels
        channels = hd.get("defined_channels", [])
        for c in channels:
            if isinstance(c, dict):
                g1 = c.get("gate1")
                g2 = c.get("gate2")
                if g1:
                    gates.add(int(g1))
                if g2:
                    gates.add(int(g2))
    
    # Fallback: user data
    if not gates:
        hd_data = user_data.get("human_design", {})
        
        # Try different HD data formats from user
        if "gates" in hd_data:
            gate_list = hd_data.get("gates", [])
            if isinstance(gate_list, list):
                for g in gate_list:
                    if isinstance(g, dict):
                        gate_num = g.get("gate", g.get("number"))
                        if gate_num:
                            gates.add(int(gate_num))
                    elif isinstance(g, (int, str)):
                        try:
                            gates.add(int(g))
                        except:
                            pass
    
    return list(gates)


def find_completed_channels(gates_a: List[int], gates_b: List[int]) -> List[Dict[str, Any]]:
    """
    Find channels completed between two people.
    A channel is completed when one person has one gate and the other has the partner gate.
    """
    completed = []
    
    gates_a_set = set(gates_a)
    gates_b_set = set(gates_b)
    
    for channel_key, channel_data in HD_CHANNELS.items():
        gate_1, gate_2 = [int(g) for g in channel_key.split("-")]
        
        # Check if channel is completed between A and B
        # Case 1: A has gate_1, B has gate_2
        if gate_1 in gates_a_set and gate_2 in gates_b_set:
            completed.append({
                "channel_id": channel_key,
                "name": channel_data["name"],
                "theme": channel_data["theme"],
                "relational": channel_data.get("relational", "connection"),
                "gate_a": gate_1,
                "gate_b": gate_2,
            })
        # Case 2: A has gate_2, B has gate_1
        elif gate_2 in gates_a_set and gate_1 in gates_b_set:
            completed.append({
                "channel_id": channel_key,
                "name": channel_data["name"],
                "theme": channel_data["theme"],
                "relational": channel_data.get("relational", "connection"),
                "gate_a": gate_2,
                "gate_b": gate_1,
            })
    
    return completed


def generate_mapping_interpretation(
    current_user_name: str,
    member_name: str,
    completed_channels: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Generate 3-LAYER relationship interpretation.
    
    Layer 1: STORY (emotional hook)
    Layer 2: PATTERNS (behavioral recognition)
    Layer 3: SIGNALS (HD proof + placeholders)
    """
    
    if not completed_channels:
        return {
            "member_name": member_name,
            "story": {
                "headline": "Your connection runs on intention, not automatic pull.",
                "summary": "You don't have energetic completions pulling you together unconsciously. That means what exists between you is built — through choice, presence, and attention. That's not less real. It's just different.",
            },
            "patterns": {
                "what_happens": [
                    "Connection requires more conscious effort — it doesn't just flow automatically",
                    "You may notice periods of natural distance that aren't about disconnection",
                ],
                "tensions": [
                    "One of you may feel like they're doing more work to maintain the connection",
                ],
                "gifts": [
                    "What you build together is fully yours — not driven by unconscious energetic pull",
                ],
            },
            "signals": {
                "human_design": [],
                "astrology": [],
                "bazi": [],
                "enneagram": [],
                "numerology": [],
            },
            "channel_count": 0,
            "strength_score": 0,
        }
    
    channel_count = len(completed_channels)
    
    # =========================================================================
    # LAYER 1: STORY — Emotional, sharp, specific to connection type
    # =========================================================================
    
    # Categorize connection themes
    themes = [c["relational"] for c in completed_channels]
    channel_ids = [c["channel_id"] for c in completed_channels]
    
    # Check for specific powerful combos
    has_intimacy = "6-59" in channel_ids
    has_community = "37-40" in channel_ids
    has_authenticity = "10-20" in channel_ids
    has_power = "34-57" in channel_ids
    has_listening = "13-33" in channel_ids
    has_money = "21-45" in channel_ids
    has_adventure = "35-36" in channel_ids
    
    if channel_count >= 4:
        if has_intimacy and has_community:
            story_headline = "This connection runs deep and wide — it touches both your emotional core and your sense of belonging."
            story_summary = f"With {channel_count} active channels between you, this isn't a surface-level dynamic. You complete each other in ways that create real pull — the kind where silence feels full and distance feels temporary."
        elif has_intimacy:
            story_headline = "There's an intensity here that most connections don't reach."
            story_summary = f"You have {channel_count} energetic completions pulling you together. The intimacy channel means barriers dissolve faster than usual between you. That's powerful — and sometimes overwhelming."
        else:
            story_headline = "You don't just connect — you activate each other."
            story_summary = f"With {channel_count} electromagnetic completions, your presence changes something in each other. This is a connection that runs on energy, not just words."
    elif channel_count == 3:
        story_headline = "There's a triangulation of energy here that creates real depth."
        story_summary = "Three connection points means this dynamic has range — it touches different parts of your life and creates a pull that's hard to ignore."
    elif channel_count == 2:
        story_headline = "Two clear lines of energy run between you."
        story_summary = "This isn't a single-note connection. You complete each other in two distinct ways, which means the dynamic has both depth and texture."
    else:
        # Single channel — use specific interpretation
        primary = completed_channels[0]
        ch_data = CHANNEL_INTERPRETATIONS.get(primary["channel_id"], CHANNEL_INTERPRETATIONS["default"])
        story_headline = ch_data["headline"]
        story_summary = ch_data["description"]
    
    # =========================================================================
    # LAYER 2: PATTERNS — Behavioral, "this is EXACTLY what happens"
    # =========================================================================
    
    what_happens = []
    tensions = []
    gifts = []
    
    # Generate behavioral patterns based on actual channels
    for c in completed_channels:
        cid = c["channel_id"]
        rel = c["relational"]
        
        # What happens — observable behaviors
        WHAT_HAPPENS_MAP = {
            "6-59": "You tend to bypass each other's emotional walls faster than either of you expected",
            "37-40": "There's an unspoken agreement between you — a sense of loyalty that formed before you discussed it",
            "10-20": "When you're together, you both become more openly yourselves — less filtering, more truth",
            "13-33": "One of you speaks while the other deeply absorbs — and the listener often sees more than the speaker realizes",
            "27-50": "You naturally look out for what matters to each other — sometimes before being asked",
            "21-45": "Money, resources, or control dynamics surface between you — not always comfortably",
            "35-36": "You pull each other toward new experiences — sometimes before either of you is ready",
            "5-15": "Your natural rhythms and timing sync up in ways that feel effortless",
            "34-57": "There's an instinctive trust between you that doesn't need explanation",
            "32-54": "You push each other to grow — sometimes gently, sometimes through friction",
            "39-55": "Emotions run deep and unpredictable between you — rich but not always comfortable",
            "28-38": "You challenge each other's sense of purpose — which can feel like pressure or liberation",
        }
        
        if cid in WHAT_HAPPENS_MAP:
            what_happens.append(WHAT_HAPPENS_MAP[cid])
        else:
            what_happens.append(f"There's a natural completion in {rel} that creates pull between you")
        
        # Tensions — where friction shows up
        TENSION_MAP = {
            "6-59": "The emotional depth can feel overwhelming — one of you may pull back when it gets too close",
            "37-40": "Unspoken expectations can build up — what feels 'agreed' may not actually be shared",
            "10-20": "Raw authenticity can accidentally land as bluntness — timing matters",
            "21-45": "Control or resource dynamics may create a power imbalance if not named",
            "35-36": "The drive for novelty can destabilize what's already working",
            "32-54": "Growth-pushing can feel like criticism if the intention isn't clear",
            "39-55": "Emotional provocation — one of you may trigger deep feelings in the other without meaning to",
        }
        
        if cid in TENSION_MAP:
            tensions.append(TENSION_MAP[cid])
        
        # Gifts — how you help each other grow
        GIFT_MAP = {
            "6-59": f"{member_name} helps you access emotional depth you'd normally protect",
            "37-40": f"Together you create a sense of belonging that neither of you has alone",
            "10-20": f"{member_name} gives you permission to be more authentically yourself",
            "13-33": f"One of you holds space that allows the other to process and release",
            "27-50": f"You protect and nurture what matters to each other — without being asked",
            "5-15": f"Your shared rhythm creates a container of ease that other relationships don't have",
            "34-57": f"There's an instinctive safety between you that allows faster trust",
            "35-36": f"{member_name} pulls you toward experiences you'd avoid alone — and that expands you",
        }
        
        if cid in GIFT_MAP:
            gifts.append(GIFT_MAP[cid])
    
    # Ensure minimum content
    if not what_happens:
        what_happens = [f"There's a natural energetic pull between you that activates when you're together"]
    if not tensions:
        tensions = ["The intensity of the connection can create pressure if expectations aren't aligned"]
    if not gifts:
        gifts = [f"Together you access something neither of you has alone — that's the gift of completion"]
    
    # Limit to best items
    what_happens = what_happens[:4]
    tensions = tensions[:3]
    gifts = gifts[:3]
    
    # =========================================================================
    # LAYER 3: SIGNALS — HD channels as proof + placeholders
    # =========================================================================
    
    # Build HD signals with 1-line plain language translations
    hd_signals = []
    for c in completed_channels:
        cid = c["channel_id"]
        
        # Plain language translation per channel
        TRANSLATION_MAP = {
            "5-15": "Your natural rhythms align — you feel 'in sync' without trying",
            "6-59": "You break through each other's emotional walls naturally",
            "21-45": "Resources, money, or control become a live wire between you",
            "35-36": "You push each other toward adventure and new emotional territory",
            "37-40": "Loyalty and mutual agreements form fast — and feel binding",
            "10-20": "You give each other permission to be more real",
            "13-33": "Deep listening flows naturally — one speaks, the other truly hears",
            "27-50": "You instinctively protect what matters to each other",
            "34-57": "There's a gut-level trust that doesn't need words",
            "32-54": "You drive each other toward growth — sometimes uncomfortably",
            "39-55": "Emotions run deeper and more unpredictably between you",
            "28-38": "You challenge each other's sense of meaning and purpose",
            "18-58": "You push each other toward improvement — through honest feedback",
            "12-22": "Emotional expression between you is amplified — moods are shared",
        }
        
        translation = TRANSLATION_MAP.get(cid, f"Energy flows between your {c['relational']} — this shapes how you interact")
        
        hd_signals.append({
            "channel": cid,
            "name": f"Channel of {c['name']}",
            "theme": c["theme"],
            "translation": translation,
            "your_gate": c["gate_a"],
            "their_gate": c["gate_b"],
        })
    
    return {
        "member_name": member_name,
        # V2 3-LAYER STRUCTURE
        "story": {
            "headline": story_headline,
            "summary": story_summary,
        },
        "patterns": {
            "what_happens": what_happens,
            "tensions": tensions,
            "gifts": gifts,
        },
        "signals": {
            "human_design": hd_signals,
            "astrology": [],
            "bazi": [],
            "enneagram": [],
            "numerology": [],
        },
        # BACKWARD COMPAT (old fields still available)
        "headline": story_headline,
        "description": story_summary,
        "what_works": ", ".join(gifts[:2]) if gifts else "Presence, allowing the dynamic to unfold naturally",
        "what_to_watch": ". ".join(tensions[:2]) if tensions else "Notice what emerges. Some completions bring intensity that needs awareness.",
        "why_this_happens": hd_signals,
        "channel_count": channel_count,
        "strength_score": min(channel_count * 20 + 10, 100),
    }


async def get_forum_member_mappings(
    db,
    forum_id: str,
    current_user_id: str,
) -> List[Dict[str, Any]]:
    """
    Get "How they map to me" for all forum members relative to current user.
    Returns sorted list by strength/relevance.
    """
    try:
        # Get forum
        from bson import ObjectId
        forum = await db.forums.find_one({"_id": ObjectId(forum_id)})
        if not forum:
            logger.error(f"[ForumMapping] Forum {forum_id} not found")
            return []
        
        # Get current user data
        current_user = await db.users.find_one({"_id": ObjectId(current_user_id)})
        if not current_user:
            logger.error(f"[ForumMapping] Current user {current_user_id} not found")
            return []
        
        # Get current user's chart (HD data)
        current_chart = await db.charts.find_one({"user_id": current_user_id})
        current_user_gates = get_user_gates(current_user, current_chart)
        current_user_name = current_user.get("name", "You")
        
        logger.info(f"[ForumMapping] User {current_user_id[:8]} has {len(current_user_gates)} gates: {current_user_gates[:5]}...")
        
        # Get all forum members from forum_members collection
        memberships = await db.forum_members.find({
            "forum_id": forum_id,
            "status": "active"
        }).to_list(100)
        
        mappings = []
        
        for membership in memberships:
            member_id = membership.get("user_id")
            if member_id == current_user_id:
                continue  # Skip self
            
            # Get member data
            member = await db.users.find_one({"_id": ObjectId(str(member_id))})
            if not member:
                continue
            
            member_name = member.get("name", "Unknown")
            
            # Get member's chart (HD data)
            member_chart = await db.charts.find_one({"user_id": str(member_id)})
            member_gates = get_user_gates(member, member_chart)
            
            logger.info(f"[ForumMapping] Member {member_name} has {len(member_gates)} gates: {member_gates[:5]}...")
            
            # Find completed channels
            completed_channels = find_completed_channels(current_user_gates, member_gates)
            
            # Generate interpretation
            mapping = generate_mapping_interpretation(
                current_user_name=current_user_name,
                member_name=member_name,
                completed_channels=completed_channels,
            )
            mapping["member_id"] = str(member_id)
            
            mappings.append(mapping)
            
            logger.info(f"[ForumMapping] {current_user_name} ↔ {member_name}: {len(completed_channels)} channels")
        
        # Sort by strength score (most connections first)
        mappings.sort(key=lambda x: x["strength_score"], reverse=True)
        
        return mappings
        
    except Exception as e:
        logger.error(f"[ForumMapping] Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []
