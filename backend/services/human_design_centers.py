"""Human Design Centers Interpretation Service

Provides reflective, template-based interpretations for the 9 Human Design centers.
Uses the same Mirror tone as Gene Keys - practical, warm, non-deterministic.

This service does NOT compute anything - it only provides interpretation.
The deterministic center computation is done in /calculations/human_design.py.
"""

from typing import List, Dict, Any, TypedDict


# =============================================================================
# GATE-TO-CENTER MAPPING
# =============================================================================
# Maps each of the 64 gates to their corresponding center

GATE_TO_CENTER = {
    # HEAD CENTER - Gates of inspiration and pressure to think
    64: "Head", 61: "Head", 63: "Head",
    
    # AJNA CENTER - Gates of mental processing and conceptualization
    47: "Ajna", 24: "Ajna", 4: "Ajna", 17: "Ajna", 43: "Ajna", 11: "Ajna",
    
    # THROAT CENTER - Gates of expression and manifestation
    62: "Throat", 23: "Throat", 56: "Throat", 35: "Throat", 12: "Throat",
    45: "Throat", 33: "Throat", 8: "Throat", 31: "Throat", 20: "Throat", 16: "Throat",
    
    # G CENTER (Identity) - Gates of identity, direction, and love
    7: "G Center", 1: "G Center", 13: "G Center", 25: "G Center", 46: "G Center",
    2: "G Center", 15: "G Center", 10: "G Center",
    
    # EGO / HEART CENTER - Gates of willpower and material resources
    21: "Ego", 51: "Ego", 26: "Ego", 40: "Ego",
    
    # SOLAR PLEXUS CENTER - Gates of emotional awareness
    36: "Solar Plexus", 22: "Solar Plexus", 37: "Solar Plexus", 6: "Solar Plexus",
    49: "Solar Plexus", 55: "Solar Plexus", 30: "Solar Plexus",
    
    # SACRAL CENTER - Gates of life force and work capacity
    5: "Sacral", 14: "Sacral", 29: "Sacral", 59: "Sacral", 9: "Sacral",
    3: "Sacral", 42: "Sacral", 27: "Sacral", 34: "Sacral",
    
    # SPLEEN CENTER - Gates of instinct and survival awareness
    48: "Spleen", 57: "Spleen", 44: "Spleen", 50: "Spleen", 32: "Spleen", 28: "Spleen", 18: "Spleen",
    
    # ROOT CENTER - Gates of pressure and adrenaline
    58: "Root", 38: "Root", 54: "Root", 53: "Root", 60: "Root", 52: "Root",
    19: "Root", 39: "Root", 41: "Root",
}

# Center display names for UI
CENTER_DISPLAY_NAMES = {
    "Head": "Head",
    "Ajna": "Ajna (Mind)",
    "Throat": "Throat",
    "G Center": "G / Identity",
    "Ego": "Heart / Ego",
    "Solar Plexus": "Solar Plexus",
    "Sacral": "Sacral",
    "Spleen": "Spleen",
    "Root": "Root"
}

# Center themes - plain language description
CENTER_THEMES = {
    "Head": ["inspiration", "mental pressure", "questions"],
    "Ajna": ["thinking patterns", "conceptualization", "opinions"],
    "Throat": ["expression", "communication", "action"],
    "G Center": ["identity", "direction", "sense of self"],
    "Ego": ["willpower", "commitment", "material resources"],
    "Solar Plexus": ["emotions", "feelings", "emotional waves"],
    "Sacral": ["life force", "work energy", "vitality"],
    "Spleen": ["instinct", "intuition", "survival awareness"],
    "Root": ["pressure", "drive", "adrenaline"]
}


class CenterInterpretation(TypedDict):
    """Full interpretation for a single center."""
    center_name: str
    display_name: str
    defined: bool
    gates_present: List[int]
    themes: List[str]
    what_this_means: str
    your_challenge: str
    your_genius: str
    practical_experiments: List[str]
    remember: str


# =============================================================================
# TEMPLATE-BASED INTERPRETATIONS
# =============================================================================
# Separate templates for defined vs undefined states

DEFINED_TEMPLATES = {
    "Head": {
        "what_this_means": "You get caught in questions that won't let go—ideas arrive uninvited and stay until you've turned them over enough times. This mental activity comes from within you, not absorbed from others.",
        "your_challenge": "The challenge is managing the constant stream of inspiration. You might feel pressure to chase every interesting question or idea. Learning which inspirations are truly yours to follow versus just mental noise takes practice.",
        "your_genius": "You have a reliable source of inspiration that others can draw from. There's a consistency to what fascinates you that, over time, becomes a resource. You're less likely to be confused by other people's mental agendas.",
        "practical_experiments": [
            "Notice which questions keep returning over weeks or months - these may be genuinely yours.",
            "Try writing down inspirations without immediately acting on them. See which ones still feel alive after a few days.",
            "When you feel mental pressure, pause and ask: 'Is this mine to solve, or am I just processing?'"
        ],
        "remember": "Not every inspiration requires action. Your consistent mental activity is a feature, not a problem to fix."
    },
    "Ajna": {
        "what_this_means": "You tend to lock into a way of thinking—and once it makes sense to you, you stick with it. Changing your mind takes real evidence, not just someone else's opinion. Your mind works in a particular way that doesn't shift based on who you're around.",
        "your_challenge": "This can create mental rigidity. You might find it hard to see other perspectives or get stuck in thought loops. There can also be pressure to have opinions about everything, even when you don't actually need one.",
        "your_genius": "Your consistent thinking style means you can offer reliable perspectives. Others may value your mental clarity because it doesn't waver. You can process information without being overly influenced by how others think about it.",
        "practical_experiments": [
            "Notice when you're defending an opinion out of habit versus genuine conviction.",
            "Practice saying 'I haven't formed a view on that yet' and notice how it feels.",
            "When someone thinks differently, try mapping their logic before disagreeing."
        ],
        "remember": "Your mind is designed to be consistent, but consistency isn't the same as certainty. Your opinions can evolve while your thinking style stays stable."
    },
    "Throat": {
        "what_this_means": "You speak or act in consistent patterns—your voice has a recognizable style. When you have something to say, it comes out. Words, actions, or creative output tend to flow from you in ways others can recognize.",
        "your_challenge": "There can be pressure to speak or act even when it's not the right moment. You might talk over others or feel the need to fill silence. The consistency of your expression can also mean repeating patterns that no longer serve you.",
        "your_genius": "You have reliable communication abilities. You can express yourself clearly and consistently. Others likely recognize your voice or style. When properly channeled, this is a powerful capacity for manifesting ideas into reality.",
        "practical_experiments": [
            "Practice letting silence exist in conversations without filling it.",
            "Notice the difference between speaking because you have something to say versus speaking from habit.",
            "Try different modes of expression (writing, art, movement) to see what channels feel most natural."
        ],
        "remember": "Your voice is consistent, but timing matters. The same words land differently when offered at the right moment versus pushed out from pressure."
    },
    "G Center": {
        "what_this_means": "You usually have a strong sense of direction—you know who you are at your core, even if external circumstances change. There's a consistency to your identity that others may recognize and orient around.",
        "your_challenge": "This can create rigidity around identity or direction. You might struggle to change course even when it's appropriate, or become attached to being a particular way. The consistency can also make it hard to understand people who feel less certain about who they are.",
        "your_genius": "Your stable identity is a gift. You can hold a sense of self that doesn't collapse under pressure or change with every passing influence. Others often find this grounding. Your direction, once clear, tends to remain reliable.",
        "practical_experiments": [
            "Notice whether your sense of direction comes from genuine knowing or from resistance to uncertainty.",
            "Practice being curious about people who seem less certain about their identity - what might they see that you don't?",
            "When you feel lost, pause before forcing a direction. Sometimes 'lost' is part of finding a truer path."
        ],
        "remember": "Your identity is stable, but it can still grow. Consistency doesn't mean being exactly the same person forever - it means having a continuous thread through change."
    },
    "Ego": {
        "what_this_means": "You can push through when you've committed to something—willpower is available. You can make commitments and follow through. There's a steadiness to your capacity for effort that others may rely on.",
        "your_challenge": "This can push you to prove yourself constantly or make promises you shouldn't. The will is always available, so you might overuse it—working when rest is needed, competing when cooperation would serve better. Worth can become too tied to achievement.",
        "your_genius": "Your consistent willpower is valuable. When you commit to something, you have the resources to follow through. You can push through difficulty when it genuinely matters. Others often trust your word because you have the capacity to back it up.",
        "practical_experiments": [
            "Before making a commitment, ask: 'Is this mine to do, or am I just proving I can?'",
            "Notice when willpower is serving you versus depleting you. The capacity is always there, but it's not always appropriate to use.",
            "Practice resting even when you could keep going. See what happens to your effectiveness."
        ],
        "remember": "Having willpower doesn't mean every situation calls for it. Your heart is designed to work hard, but it's also designed to rest."
    },
    "Solar Plexus": {
        "what_this_means": "You feel things in waves—your emotional state rises and falls in patterns that belong to you. Clarity doesn't come immediately; it arrives after the wave has moved through. You bring an emotional atmosphere into spaces you enter.",
        "your_challenge": "Living with emotional waves means no feeling state is permanent—the highs will pass, and so will the lows. The challenge is not making decisions in either extreme. There can also be pressure to explain or justify your moods when they don't have logical causes.",
        "your_genius": "Your emotional depth is a form of intelligence. The waves bring richness, creativity, and the capacity for profound connection. When you give yourself time to ride through the wave, your clarity is often more complete than purely mental analysis.",
        "practical_experiments": [
            "Track your emotional rhythms for a few weeks. Notice if there are patterns (daily, weekly, monthly).",
            "Practice saying 'I'm not sure yet' when asked for decisions during emotional highs or lows.",
            "When you feel certain in an emotional peak, write it down and revisit it in a different mood."
        ],
        "remember": "Your waves are yours - you don't need to explain them or wait for them to stop. Riding them skillfully is different from controlling them."
    },
    "Sacral": {
        "what_this_means": "You have consistent energy for work that engages you—when it's right, you can go and go. There's a generator quality to your system. Your vitality comes from within when you're doing work that lights you up.",
        "your_challenge": "This can lead to overwork. Because the energy is always there, you might not notice when you've gone past healthy limits. You could also get stuck in work that depletes you because you can technically keep going. Learning to honor 'no' signals is crucial.",
        "your_genius": "Your sustainable energy is a gift. When properly matched to work that lights you up, you can create, build, and sustain in ways others can't. The key is listening to your gut response—the 'uh-huh' (yes) or 'un-un' (no)—about what's correct to engage.",
        "practical_experiments": [
            "Pay attention to your gut response when opportunities arise. Does your energy rise or drop?",
            "Notice the difference between tasks that build your energy versus tasks that drain it, even if both get done.",
            "Practice stopping before you're exhausted. See what happens to your overall output."
        ],
        "remember": "Your energy regenerates through correct engagement, not just rest. The right work feeds you; the wrong work empties you even while you're doing it."
    },
    "Spleen": {
        "what_this_means": "You get quiet, instant signals about what's safe or healthy—a knowing that arrives in the moment and doesn't repeat. Your body tends to give you subtle awareness about safety, health, and timing that speaks softly and only once.",
        "your_challenge": "This awareness is subtle and doesn't repeat itself. The challenge is learning to hear and trust these quiet signals before the mind overrides them. You might also project a false sense of safety onto others, assuming they have the same instinctual awareness.",
        "your_genius": "Your consistent access to instinct is a survival gift. When you learn to hear its quiet voice, you can navigate in real-time with a kind of knowing that doesn't require analysis. Health, timing, and safety awareness become reliable resources.",
        "practical_experiments": [
            "Practice noticing your first, instantaneous response before your mind starts analyzing.",
            "When your body says 'no' to something, honor it - even if you can't explain why.",
            "Pay attention to what your body does around different people and environments. It's giving you data."
        ],
        "remember": "Your instinct speaks in whispers, not shouts. Learning to hear it requires slowing down the mind enough to notice what the body already knows."
    },
    "Root": {
        "what_this_means": "You handle pressure without being destabilized by it—stress arrives, but it doesn't throw you off. You experience stress and drive in your own rhythm, rather than absorbing it from external sources. There's a steadiness to how you handle urgency.",
        "your_challenge": "This can create addiction to pressure. Because you have consistent access to adrenaline, you might create stress even when it's not necessary, or struggle to fully relax. The drive is always there, which can make it hard to stop.",
        "your_genius": "Your consistent relationship with pressure means you can handle stress without being destabilized by it. You can work under deadlines and navigate urgency from a grounded place. Others may find your steadiness under pressure reassuring.",
        "practical_experiments": [
            "Notice when you're creating artificial urgency. Is the deadline real, or are you manufacturing pressure?",
            "Practice genuine rest - not 'productive rest' - and notice what arises.",
            "When external pressure hits, pause and notice whether it actually affects your internal state."
        ],
        "remember": "Your drive is yours, but it doesn't need to run constantly. The same engine that powers you through difficulty needs maintenance and downtime."
    }
}

UNDEFINED_TEMPLATES = {
    "Head": {
        "what_this_means": "You take in other people's mental pressure and sometimes mistake it for your own. Their questions become urgent for you, even when they're not yours to solve. You might experience different ideas depending on who you're around.",
        "your_challenge": "Without consistent pressure of your own, you might feel confused about which questions are actually yours to answer. You could chase other people's inspirations thinking they're your own, or feel overwhelmed in mentally active environments.",
        "your_genius": "You can sample and understand many different types of inspiration. You can recognize truly interesting questions from the mundane. Over time, you develop wisdom about what's actually worth thinking about.",
        "practical_experiments": [
            "Notice how your mental activity changes in different environments or around different people.",
            "When inspired by an idea, ask: 'Would I still care about this if I were alone?'",
            "Practice letting go of questions that don't stay with you after leaving certain people or places."
        ],
        "remember": "Not having your own fixed mental pressure is a gift for understanding how different minds work. You don't need to hold onto every inspiration that passes through."
    },
    "Ajna": {
        "what_this_means": "Your thinking shifts depending on who you're around—you can see multiple perspectives, but might struggle to hold a consistent view. That flexibility is a gift, not a flaw. Your mental processing adapts to context rather than staying fixed.",
        "your_challenge": "Without a fixed way of thinking, you might feel pressure to have certainty you don't actually have, or get confused about what you really believe. You could adopt others' opinions without realizing they're not your own.",
        "your_genius": "Your mental flexibility allows you to understand many different perspectives. You can process information in ways that match the context rather than forcing everything through one filter. This gives you potential wisdom about the nature of certainty itself.",
        "practical_experiments": [
            "Notice when your opinions change based on who you're talking to. Is this flexibility or people-pleasing?",
            "Practice saying 'I see it differently in different contexts' instead of forcing one answer.",
            "After leaving a strong personality, check in: which thoughts were theirs, which are yours?"
        ],
        "remember": "Your mind is designed to be flexible, not fixated. Wisdom comes from experiencing many ways of thinking, not from pretending to have one true opinion."
    },
    "Throat": {
        "what_this_means": "You don't always know when or how to speak—timing feels inconsistent. You might overspeak to get attention or go quiet when you actually have something to say. Your voice and expression may vary depending on context.",
        "your_challenge": "Without consistent throat energy, you might struggle to be heard or feel pressure to speak even when you have nothing to say. You could try to force expression, or conversely, remain silent even when you do have something to contribute.",
        "your_genius": "You have the ability to communicate in many different styles. You can adapt your expression to the situation. Over time, you develop wisdom about when speaking actually matters versus when silence is more powerful.",
        "practical_experiments": [
            "Notice how your communication style changes in different settings. Which feels most authentic?",
            "Practice being comfortable with not speaking when you don't have something genuine to say.",
            "When you do speak, notice whether people seem to hear you. Timing and context may matter more for you."
        ],
        "remember": "Your voice doesn't need to be consistent to be powerful. Sometimes the flexibility to express differently in different contexts is the gift."
    },
    "G Center": {
        "what_this_means": "You sometimes feel uncertain about who you are or where you're going. You pick up a sense of identity from people and places around you—which makes environment crucial. This isn't instability; it's openness to finding yourself through experience.",
        "your_challenge": "Without a fixed identity center, you might feel lost or uncertain about who you are or where you're going. You could attach to others' identities, or become chameleon-like in ways that feel inauthentic. Finding yourself may seem like an ongoing project.",
        "your_genius": "Your openness in identity allows you to understand many different ways of being. You can try on different directions without being locked into one. Over time, you develop wisdom about the nature of identity itself—recognizing who others truly are.",
        "practical_experiments": [
            "Notice how your sense of self changes in different places and with different people.",
            "Instead of asking 'Who am I?', try asking 'Who am I in this context, right now?'",
            "Pay attention to which environments and people make you feel more like yourself."
        ],
        "remember": "Your identity is designed to be fluid. This doesn't mean you lack a self—it means your self is discovered through experience rather than fixed from birth."
    },
    "Ego": {
        "what_this_means": "You don't have consistent willpower—and that's not a weakness. You might overcommit to prove yourself, then burn out. Learning what's actually yours to push through matters more than trying to match others' determination.",
        "your_challenge": "Without fixed willpower, you might overcompensate by making promises you can't keep, or pushing yourself with borrowed will. You could become obsessed with proving your worth, or conversely, feel powerless around people with strong will.",
        "your_genius": "You have the ability to recognize true worthiness in others and yourself without needing external proof. You can let go of the proving game entirely. Over time, you develop wisdom about when willpower is actually needed versus when it's ego.",
        "practical_experiments": [
            "Notice when you're pushing with borrowed willpower versus genuine capacity.",
            "Practice not promising things to prove yourself. See how it feels to say 'I'm not sure I can commit to that.'",
            "Around very driven people, check: is this your will or are you amplifying theirs?"
        ],
        "remember": "You don't need to prove your worth. Your value isn't dependent on willpower or achievement. Learning when NOT to push can be your superpower."
    },
    "Solar Plexus": {
        "what_this_means": "You absorb emotions from others and feel them more intensely than they do. Conflict in the room becomes your conflict. Learning to release what isn't yours is essential. Your own emotional baseline is actually more neutral than it might seem.",
        "your_challenge": "Without a fixed emotional wave, you might struggle to distinguish your feelings from others'. You could avoid emotional environments entirely, or become overwhelmed in them. There can be a tendency to absorb emotional energy that isn't yours to process.",
        "your_genius": "You have deep empathy and the ability to sense emotional undercurrents others miss. You can read the emotional atmosphere of any room. Over time, you develop wisdom about emotions themselves—seeing the waves without drowning in them.",
        "practical_experiments": [
            "After leaving emotional environments, check in: which feelings were yours?",
            "Practice being in emotional spaces without trying to fix or absorb the feelings.",
            "Notice your baseline emotional state when alone. This is closer to your authentic emotional tone."
        ],
        "remember": "Feeling others' emotions deeply is a gift, not a burden. The skill is learning to feel without taking responsibility for emotions that aren't yours."
    },
    "Sacral": {
        "what_this_means": "You don't have consistent work energy—you need to know when enough is enough. You can borrow it from others and go beyond healthy limits. Learning when enough is enough prevents burnout. This is not a deficiency; it's a different design.",
        "your_challenge": "Without fixed sacral energy, you might push yourself based on borrowed life force, leading to deep exhaustion. You could compare yourself to people with consistent work capacity and feel inadequate. Learning your actual sustainable rhythm is essential.",
        "your_genius": "You have the ability to know when enough is enough—not just for yourself, but in general. You can see when others are overworking. Over time, you develop wisdom about the nature of life force and sustainable effort.",
        "practical_experiments": [
            "Track your energy through the day. When do you have it, and where did it come from?",
            "Practice stopping before you're exhausted. Your signal comes later, so you need to stop earlier.",
            "Notice how your energy changes around different people. Some will energize you; some will deplete you."
        ],
        "remember": "You're not designed for sustained work output like sacral beings. Your wisdom is about efficiency and knowing when to stop—not about matching their endurance."
    },
    "Spleen": {
        "what_this_means": "You might hold onto things too long—jobs, relationships, habits—past their expiration. Security feels uncertain, so you grip what you have even when it no longer serves. This can make you highly attuned to health and survival themes.",
        "your_challenge": "Without fixed splenic awareness, you might hold onto things (people, situations, habits) past their healthy expiration because letting go feels unsafe. You could also ignore genuine danger signals or become overly fearful.",
        "your_genius": "You have potential mastery over fear and health awareness. You can sense what's unhealthy in ways others miss. Over time, you develop wisdom about the nature of safety itself—knowing what's truly dangerous versus what just feels scary.",
        "practical_experiments": [
            "Notice what you're holding onto that may have outlived its usefulness.",
            "When fear arises, ask: is this a genuine signal or amplified anxiety from the environment?",
            "Pay attention to your health awareness—you may pick up on things before they become obvious."
        ],
        "remember": "Your relationship with fear and survival is an ongoing education. The goal isn't to eliminate fear but to develop wisdom about when it's a real signal."
    },
    "Root": {
        "what_this_means": "You absorb other people's urgency and feel pressured to rush. Their deadline becomes your stress. Learning to notice when the pressure isn't actually yours is freedom. Your own natural rhythm may be less driven than you think.",
        "your_challenge": "Without fixed root pressure, you might become addicted to others' urgency or feel chronically stressed in fast-paced environments. You could also try to match the pace of pressured people, burning out in the process.",
        "your_genius": "You have the ability to recognize when pressure is real versus manufactured. You can see the hamster wheel others are running on. Over time, you develop wisdom about the nature of stress and healthy pacing.",
        "practical_experiments": [
            "Notice how your sense of urgency changes in different environments.",
            "When you feel pressured, ask: is this deadline real, or am I absorbing someone else's stress?",
            "Practice doing things at your natural pace when possible. See how the quality changes."
        ],
        "remember": "You're not designed to run on constant pressure. Your gift is recognizing when urgency is artificial—both for yourself and others."
    }
}


def get_gates_for_center(center_name: str, active_gates: List[int]) -> List[int]:
    """Get which gates from active_gates belong to a specific center."""
    return [gate for gate in active_gates if GATE_TO_CENTER.get(gate) == center_name]


def get_center_interpretation(
    center_name: str,
    defined: bool,
    active_gates: List[int]
) -> CenterInterpretation:
    """Generate interpretation for a single center.
    
    Args:
        center_name: Internal center name (e.g., "G Center")
        defined: Whether the center is defined
        active_gates: List of all user's active gates
    
    Returns:
        CenterInterpretation with full template-based content
    """
    # Get gates present in this center
    gates_present = get_gates_for_center(center_name, active_gates)
    
    # Get display name and themes
    display_name = CENTER_DISPLAY_NAMES.get(center_name, center_name)
    themes = CENTER_THEMES.get(center_name, [])
    
    # Select appropriate template
    template = DEFINED_TEMPLATES.get(center_name) if defined else UNDEFINED_TEMPLATES.get(center_name)
    
    if not template:
        # Fallback for any missing templates
        template = {
            "what_this_means": f"Your {display_name} center is {'defined' if defined else 'undefined'}.",
            "your_challenge": "Understanding this center takes time and experimentation.",
            "your_genius": "Every center configuration has its gifts.",
            "practical_experiments": ["Observe how this center shows up in your life."],
            "remember": "Your design is perfect as it is."
        }
    
    return {
        "center_name": center_name,
        "display_name": display_name,
        "defined": defined,
        "gates_present": gates_present,
        "themes": themes,
        "what_this_means": template["what_this_means"],
        "your_challenge": template["your_challenge"],
        "your_genius": template["your_genius"],
        "practical_experiments": template["practical_experiments"],
        "remember": template["remember"]
    }


def build_centers_profile(
    defined_centers: List[str],
    undefined_centers: List[str],
    active_gates: List[int]
) -> List[CenterInterpretation]:
    """Build complete centers profile with interpretations for all 9 centers.
    
    Args:
        defined_centers: List of defined center names from HD computation
        undefined_centers: List of undefined center names from HD computation
        active_gates: List of all active gates from HD computation
    
    Returns:
        List of CenterInterpretation for all 9 centers in standard order
    """
    # Standard center order for display
    center_order = [
        "Head", "Ajna", "Throat", "G Center", "Ego",
        "Solar Plexus", "Sacral", "Spleen", "Root"
    ]
    
    defined_set = set(defined_centers)
    
    centers = []
    for center_name in center_order:
        is_defined = center_name in defined_set
        interpretation = get_center_interpretation(
            center_name=center_name,
            defined=is_defined,
            active_gates=active_gates
        )
        centers.append(interpretation)
    
    return centers
