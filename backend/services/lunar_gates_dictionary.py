"""
Reflector Lunar Gates Dictionary - Task 50

Complete 64-gate dictionary for Reflector lunar gate mapping.
Each gate includes Mirror-aligned language for reflection.

Tone: observational, spacious, psychologically clear, non-deterministic
"""

from typing import Dict, Any

# =============================================================================
# GATE DICTIONARY
# =============================================================================

# All 64 Human Design gates with Reflector-focused interpretations
# Each entry: gate_number -> {title, theme, center, reflection, question}

LUNAR_GATES: Dict[int, Dict[str, Any]] = {
    1: {
        "title": "Self-Expression",
        "theme": "creative expression, uniqueness, contribution",
        "center": "G Center (Identity)",
        "reflection": "Today may invite awareness of your authentic creative expression and what wants to emerge through you.",
        "question": "What feels ready to be expressed in your own unique way?"
    },
    2: {
        "title": "The Direction of Self",
        "theme": "receptivity, direction, magnetic attraction",
        "center": "G Center (Identity)",
        "reflection": "This gate may highlight your relationship with direction and how you receive guidance about where to go.",
        "question": "What direction seems to be calling to you right now?"
    },
    3: {
        "title": "Ordering",
        "theme": "innovation, mutation, ordering chaos",
        "center": "Sacral",
        "reflection": "Today could bring attention to beginnings and how you navigate the chaos of new starts.",
        "question": "What new beginning might be asking for your patience?"
    },
    4: {
        "title": "Formulization",
        "theme": "mental answers, logical solutions, certainty",
        "center": "Ajna (Mind)",
        "reflection": "This gate may highlight your relationship with mental certainty and the search for answers.",
        "question": "Where might uncertainty be inviting you to stay curious rather than conclude?"
    },
    5: {
        "title": "Fixed Rhythms",
        "theme": "natural rhythms, patience, timing",
        "center": "Sacral",
        "reflection": "Today may bring awareness to your natural rhythms and the patience required for right timing.",
        "question": "What rhythm feels most natural to you today?"
    },
    6: {
        "title": "Friction",
        "theme": "emotional intimacy, conflict resolution, pH balance",
        "center": "Solar Plexus (Emotional)",
        "reflection": "This gate may highlight the friction points in your relationships and how intimacy emerges from tension.",
        "question": "What friction in your life might be leading toward deeper connection?"
    },
    7: {
        "title": "The Role of Self",
        "theme": "leadership, influence, roles",
        "center": "G Center (Identity)",
        "reflection": "Today could bring awareness to the roles you play and your relationship with leading or influencing others.",
        "question": "What role feels most authentic for you right now?"
    },
    8: {
        "title": "Contribution",
        "theme": "individual contribution, making a difference",
        "center": "Throat",
        "reflection": "This gate may highlight your desire to contribute something meaningful and unique to the world.",
        "question": "What contribution wants to be expressed through you?"
    },
    9: {
        "title": "Focus",
        "theme": "concentration, determination, details",
        "center": "Sacral",
        "reflection": "Today may invite attention to focus and the energy required for concentrating on details.",
        "question": "What deserves your concentrated attention right now?"
    },
    10: {
        "title": "Behavior of Self",
        "theme": "self-love, authenticity, behavior",
        "center": "G Center (Identity)",
        "reflection": "This gate may highlight your relationship with self-love and living authentically.",
        "question": "What behavior feels most true to who you really are?"
    },
    11: {
        "title": "Ideas",
        "theme": "ideas, peace, harmony",
        "center": "Ajna (Mind)",
        "reflection": "Today could bring a flow of ideas and awareness of your relationship with mental stimulation.",
        "question": "Which ideas feel worth pursuing and which are simply passing through?"
    },
    12: {
        "title": "Caution",
        "theme": "articulation, caution, social expression",
        "center": "Throat",
        "reflection": "This gate may highlight the care required in expressing yourself and knowing when to speak.",
        "question": "What might be gained by pausing before expressing yourself today?"
    },
    13: {
        "title": "The Listener",
        "theme": "listening, secrets, narrative",
        "center": "G Center (Identity)",
        "reflection": "Today may invite awareness of listening and the stories you hold, both your own and others'.",
        "question": "What story wants to be heard today?"
    },
    14: {
        "title": "Power Skills",
        "theme": "resources, wealth, empowerment",
        "center": "Sacral",
        "reflection": "This gate may highlight your relationship with resources and the skills that create empowerment.",
        "question": "What resources or skills feel available to you right now?"
    },
    15: {
        "title": "Extremes",
        "theme": "humanity, rhythms, extremes",
        "center": "G Center (Identity)",
        "reflection": "Today could bring awareness to the extremes in human behavior and your own rhythmic patterns.",
        "question": "Where might balance be found between the extremes you notice?"
    },
    16: {
        "title": "Skills",
        "theme": "enthusiasm, skills, identification",
        "center": "Throat",
        "reflection": "This gate may highlight your relationship with skills and the enthusiasm that drives mastery.",
        "question": "What skill or talent wants more expression today?"
    },
    17: {
        "title": "Opinions",
        "theme": "opinions, logic, organization",
        "center": "Ajna (Mind)",
        "reflection": "Today may bring awareness to opinions – both your own and others' – and how they organize understanding.",
        "question": "What opinions might be worth holding lightly today?"
    },
    18: {
        "title": "Correction",
        "theme": "judgment, correction, patterns",
        "center": "Spleen",
        "reflection": "This gate may highlight your ability to see what needs correction and your relationship with judgment.",
        "question": "What pattern seems ready for correction, and what deserves acceptance as it is?"
    },
    19: {
        "title": "Wanting",
        "theme": "sensitivity, needs, approach",
        "center": "Root",
        "reflection": "Today could bring awareness to wants and needs, and how you approach getting them met.",
        "question": "What need feels most present for you right now?"
    },
    20: {
        "title": "The Now",
        "theme": "presence, contemplation, recognition",
        "center": "Throat",
        "reflection": "This gate may highlight the power of presence and recognition in the current moment.",
        "question": "What becomes visible when you pause and notice the present moment?"
    },
    21: {
        "title": "The Hunter/Huntress",
        "theme": "control, willpower, resources",
        "center": "Heart/Will",
        "reflection": "Today may bring awareness to your relationship with control and the will to pursue what you want.",
        "question": "Where might releasing control create more ease than holding on?"
    },
    22: {
        "title": "Openness",
        "theme": "grace, emotional openness, charm",
        "center": "Solar Plexus (Emotional)",
        "reflection": "This gate may highlight how open or guarded you feel in emotional expression.",
        "question": "What feels ready to be expressed today, and what still wants space?"
    },
    23: {
        "title": "Assimilation",
        "theme": "simplicity, explanation, genetic insight",
        "center": "Throat",
        "reflection": "Today could bring awareness to simplifying complex things and sharing understanding.",
        "question": "What insight wants to be shared in simple terms?"
    },
    24: {
        "title": "Rationalization",
        "theme": "returning, revisiting, mental review",
        "center": "Ajna (Mind)",
        "reflection": "This gate may highlight the mind's tendency to return and review, seeking understanding.",
        "question": "What thought or situation keeps returning for your attention?"
    },
    25: {
        "title": "Innocence",
        "theme": "universal love, innocence, spirit",
        "center": "G Center (Identity)",
        "reflection": "Today may invite connection with innocence and unconditional love for life itself.",
        "question": "Where might more innocence or openness serve you today?"
    },
    26: {
        "title": "The Egoist",
        "theme": "accumulation, influence, memory",
        "center": "Heart/Will",
        "reflection": "This gate may highlight your relationship with achievement, accumulation, and making an impression.",
        "question": "What achievement or recognition matters most to you right now?"
    },
    27: {
        "title": "Nourishment",
        "theme": "caring, nourishment, responsibility",
        "center": "Sacral",
        "reflection": "Today could bring awareness to nourishment – what you give, what you receive, and what truly sustains.",
        "question": "What needs nourishing in your life right now?"
    },
    28: {
        "title": "The Game Player",
        "theme": "struggle, purpose, risk",
        "center": "Spleen",
        "reflection": "This gate may highlight your relationship with struggle, purpose, and what feels worth the risk.",
        "question": "What feels worth struggling for, and what might be released?"
    },
    29: {
        "title": "Perseverance",
        "theme": "saying yes, commitment, devotion",
        "center": "Sacral",
        "reflection": "Today may bring awareness to commitment and what you truly have energy for.",
        "question": "What feels right to commit to, and what might need reconsideration?"
    },
    30: {
        "title": "Feelings",
        "theme": "desire, fates, recognition of feelings",
        "center": "Solar Plexus (Emotional)",
        "reflection": "This gate may highlight the power of desire and the recognition of your emotional experiences.",
        "question": "What desire feels most alive in you today?"
    },
    31: {
        "title": "Leading",
        "theme": "influence, leading, democracy",
        "center": "Throat",
        "reflection": "Today could bring awareness to influence and your relationship with leading others.",
        "question": "Where might your influence be naturally requested?"
    },
    32: {
        "title": "Continuity",
        "theme": "duration, instinct, transformation",
        "center": "Spleen",
        "reflection": "This gate may highlight the instinct for what has lasting value and can endure.",
        "question": "What feels worth preserving for the long term?"
    },
    33: {
        "title": "Privacy",
        "theme": "retreat, reflection, remembering",
        "center": "Throat",
        "reflection": "Today may invite retreat and the privacy needed to process and remember.",
        "question": "What might be gained by withdrawing to reflect?"
    },
    34: {
        "title": "Power",
        "theme": "pure power, individual empowerment, response",
        "center": "Sacral",
        "reflection": "This gate may highlight raw power and energy available when responded to correctly.",
        "question": "What is your energy naturally responding to today?"
    },
    35: {
        "title": "Change",
        "theme": "experience, change, progress",
        "center": "Throat",
        "reflection": "Today could bring awareness to the desire for new experiences and the nature of change.",
        "question": "What new experience is calling to you?"
    },
    36: {
        "title": "Crisis",
        "theme": "exploration, inexperience, emotional transition",
        "center": "Solar Plexus (Emotional)",
        "reflection": "This gate may highlight emotional transitions and learning through new territory.",
        "question": "What emotional territory feels unfamiliar yet worth exploring?"
    },
    37: {
        "title": "Friendship",
        "theme": "family, community, agreements",
        "center": "Solar Plexus (Emotional)",
        "reflection": "Today may bring awareness to community bonds and the agreements that sustain belonging.",
        "question": "What agreements in your relationships might need attention?"
    },
    38: {
        "title": "The Fighter",
        "theme": "opposition, stubbornness, purpose",
        "center": "Root",
        "reflection": "This gate may highlight what you stand for and your capacity to fight for meaning.",
        "question": "What feels worth standing firm for?"
    },
    39: {
        "title": "Provocation",
        "theme": "provocation, spirit, emotional response",
        "center": "Root",
        "reflection": "Today could bring awareness to what provokes you and the spirit that emerges in response.",
        "question": "What is provoking a response in you, and what might it be revealing?"
    },
    40: {
        "title": "Aloneness",
        "theme": "aloneness, willpower, rest",
        "center": "Heart/Will",
        "reflection": "This gate may highlight the need for aloneness and the rest that restores will.",
        "question": "What kind of rest or solitude would serve you today?"
    },
    41: {
        "title": "Contraction",
        "theme": "fantasy, start codon, imagination",
        "center": "Root",
        "reflection": "Today may bring awareness to new fantasies and imaginings that want to become real.",
        "question": "What fantasy or dream feels ready to take its first step?"
    },
    42: {
        "title": "Growth",
        "theme": "completion, finishing, growth",
        "center": "Sacral",
        "reflection": "This gate may highlight cycles coming to completion and the growth that emerges from finishing.",
        "question": "What feels ready to be completed in your life?"
    },
    43: {
        "title": "Insight",
        "theme": "breakthrough, insight, mental uniqueness",
        "center": "Ajna (Mind)",
        "reflection": "Today could bring sudden insights and unique mental perspectives.",
        "question": "What breakthrough insight might be emerging?"
    },
    44: {
        "title": "Alertness",
        "theme": "patterns, instinct, alertness to the past",
        "center": "Spleen",
        "reflection": "This gate may highlight your ability to recognize patterns from the past.",
        "question": "What pattern from the past seems relevant to today?"
    },
    45: {
        "title": "The Gatherer",
        "theme": "gathering, distribution, dominion",
        "center": "Throat",
        "reflection": "Today may bring awareness to gathering and sharing resources within community.",
        "question": "What do you have to gather or share with your tribe?"
    },
    46: {
        "title": "Determination",
        "theme": "body, serendipity, love of body",
        "center": "G Center (Identity)",
        "reflection": "This gate may highlight your relationship with your body and the serendipity of physical existence.",
        "question": "What is your body telling you today?"
    },
    47: {
        "title": "Realization",
        "theme": "oppression, realization, making sense",
        "center": "Ajna (Mind)",
        "reflection": "Today could bring the pressure of making sense of abstract experiences.",
        "question": "What experience is waiting to become understanding?"
    },
    48: {
        "title": "Depth",
        "theme": "depth, solution, talent",
        "center": "Spleen",
        "reflection": "This gate may highlight the depth of your talents and the fear of inadequacy.",
        "question": "Where might you be underestimating your own depth?"
    },
    49: {
        "title": "Principles",
        "theme": "revolution, principles, rejection/acceptance",
        "center": "Solar Plexus (Emotional)",
        "reflection": "Today may bring awareness to principles and what you accept or reject emotionally.",
        "question": "What principle feels most important to honor today?"
    },
    50: {
        "title": "Values",
        "theme": "values, responsibility, laws",
        "center": "Spleen",
        "reflection": "This gate may highlight your core values and sense of responsibility to preserve what matters.",
        "question": "What values are you being called to uphold?"
    },
    51: {
        "title": "Shock",
        "theme": "initiative, shock, arousing spirit",
        "center": "Heart/Will",
        "reflection": "Today could bring unexpected experiences that awaken spirit and initiative.",
        "question": "What shock or surprise might be an invitation rather than a disruption?"
    },
    52: {
        "title": "Stillness",
        "theme": "inaction, stillness, mountain",
        "center": "Root",
        "reflection": "This gate may highlight the power of stillness and knowing when not to act.",
        "question": "Where might stillness serve you more than action?"
    },
    53: {
        "title": "Beginnings",
        "theme": "development, pressure to begin, cycles",
        "center": "Root",
        "reflection": "Today may bring the pressure to start something new and awareness of developmental cycles.",
        "question": "What new cycle is pressing to begin?"
    },
    54: {
        "title": "Ambition",
        "theme": "drive, ambition, transformation through effort",
        "center": "Root",
        "reflection": "This gate may highlight ambition and the drive to rise through effort.",
        "question": "What are you driven to achieve or transform?"
    },
    55: {
        "title": "Spirit",
        "theme": "abundance, spirit, emotional melancholy",
        "center": "Solar Plexus (Emotional)",
        "reflection": "Today could bring awareness to spirit, abundance, and the depths of emotional experience.",
        "question": "What does abundance mean to you in this moment?"
    },
    56: {
        "title": "Stimulation",
        "theme": "storytelling, stimulation, travel",
        "center": "Throat",
        "reflection": "This gate may highlight the desire to stimulate through stories and ideas.",
        "question": "What story wants to be told or explored?"
    },
    57: {
        "title": "Intuition",
        "theme": "intuitive clarity, survival, now",
        "center": "Spleen",
        "reflection": "Today may bring heightened intuition and present-moment awareness.",
        "question": "What is your intuition telling you right now?"
    },
    58: {
        "title": "Vitality",
        "theme": "joy, vitality, correction",
        "center": "Root",
        "reflection": "This gate may highlight the pressure to improve and the joy of vitality.",
        "question": "What brings you vital joy?"
    },
    59: {
        "title": "Sexuality",
        "theme": "intimacy, genetics, breaking barriers",
        "center": "Sacral",
        "reflection": "Today could bring awareness to intimacy and the barriers that keep connection at bay.",
        "question": "What barrier to intimacy might be ready to dissolve?"
    },
    60: {
        "title": "Limitation",
        "theme": "acceptance, limitation, transcendence",
        "center": "Root",
        "reflection": "This gate may highlight limitations and the potential for transcendence within constraints.",
        "question": "What limitation might actually contain hidden freedom?"
    },
    61: {
        "title": "Mystery",
        "theme": "inner truth, mystery, inspiration",
        "center": "Head",
        "reflection": "Today may bring the pressure of mystery and the search for inner truth.",
        "question": "What mystery is pulling at your awareness?"
    },
    62: {
        "title": "Details",
        "theme": "precision, details, expression of facts",
        "center": "Throat",
        "reflection": "This gate may highlight attention to details and the precision of expression.",
        "question": "What details deserve your careful attention today?"
    },
    63: {
        "title": "Doubt",
        "theme": "doubt, logic, questioning",
        "center": "Head",
        "reflection": "Today could bring healthy doubt and the logical questioning that leads to understanding.",
        "question": "What doubt might be protecting you from premature conclusions?"
    },
    64: {
        "title": "Confusion",
        "theme": "completion, confusion before clarity, transition",
        "center": "Head",
        "reflection": "This gate may highlight the confusion that precedes clarity and mental completion.",
        "question": "What confusion might be the doorway to a new understanding?"
    },
}


def get_gate_data(gate_number: int) -> Dict[str, Any]:
    """
    Get the complete data for a specific gate.
    
    Returns dictionary with title, theme, center, reflection, question.
    Falls back to generic data if gate not found.
    """
    if gate_number in LUNAR_GATES:
        return {
            "gate": gate_number,
            **LUNAR_GATES[gate_number]
        }
    else:
        # Fallback for any missing gates
        return {
            "gate": gate_number,
            "title": f"Gate {gate_number}",
            "theme": "awareness, presence, possibility",
            "center": "Unknown",
            "reflection": f"Gate {gate_number} is active in the Moon today, inviting you to notice what arises.",
            "question": "What awareness is this gate bringing to your day?"
        }


def get_all_gates() -> Dict[int, Dict[str, Any]]:
    """Return the complete gate dictionary."""
    return LUNAR_GATES
