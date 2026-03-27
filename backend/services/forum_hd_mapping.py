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
    Generate a human-readable interpretation of the mapping between two people.
    """
    
    if not completed_channels:
        # No completed channels - return a soft interpretation
        return {
            "member_name": member_name,
            "headline": "Connection may rely more on conscious effort",
            "description": "You don't have automatic energetic completions with this person. That's not bad—it means your connection is built through awareness and intention rather than unconscious energetic pull.",
            "what_works": "Clear communication, intentional time together, shared interests",
            "what_to_watch": "Don't force connection. Some relationships work through words, not energy.",
            "why_this_happens": [],
            "channel_count": 0,
            "strength_score": 0,
        }
    
    # Sort by priority (could be weighted by channel importance)
    # For now, just use count
    channel_count = len(completed_channels)
    
    # Generate headline based on strongest channel
    primary_channel = completed_channels[0]
    channel_interp = CHANNEL_INTERPRETATIONS.get(
        primary_channel["channel_id"],
        CHANNEL_INTERPRETATIONS["default"]
    )
    
    # Build combined interpretation
    if channel_count == 1:
        headline = channel_interp["headline"]
        description = channel_interp["description"]
    elif channel_count == 2:
        headline = f"Strong natural momentum between you"
        themes = [c["relational"] for c in completed_channels[:2]]
        description = f"You complete each other in {themes[0]} and {themes[1]}. This creates real energetic pull."
    else:
        headline = f"Multiple natural completions between you"
        description = f"You have {channel_count} electromagnetic connections. There's significant energetic interplay here that can feel both exciting and intense."
    
    # Build what works and what to watch
    what_works_parts = [channel_interp["what_works"]]
    what_to_watch_parts = [channel_interp["what_to_watch"]]
    
    for c in completed_channels[1:3]:  # Add up to 2 more
        c_interp = CHANNEL_INTERPRETATIONS.get(c["channel_id"], CHANNEL_INTERPRETATIONS["default"])
        if c_interp["what_works"] not in what_works_parts:
            what_works_parts.append(c_interp["what_works"].split(",")[0].strip())
        if c_interp["what_to_watch"] not in what_to_watch_parts:
            what_to_watch_parts.append(c_interp["what_to_watch"].split(".")[0].strip())
    
    # Build why_this_happens for detail view
    why_this_happens = []
    for c in completed_channels:
        why_this_happens.append({
            "channel": c["channel_id"],
            "name": c["name"],
            "theme": c["theme"],
            "your_gate": c["gate_a"],
            "their_gate": c["gate_b"],
        })
    
    return {
        "member_name": member_name,
        "headline": headline,
        "description": description,
        "what_works": ", ".join(what_works_parts[:3]),
        "what_to_watch": ". ".join(what_to_watch_parts[:2]) + ".",
        "why_this_happens": why_this_happens,
        "channel_count": channel_count,
        "strength_score": min(channel_count * 20 + 10, 100),  # Score for sorting
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
