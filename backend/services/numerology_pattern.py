"""
Numerology Pattern System Service

Task: Transform numerology from descriptive personality text into 
diagnostic pattern recognition system.

SYSTEM: Vedic Numerology (date-based) is the PRIMARY system.
Name-based numbers (Western) are SECONDARY - available when user adds name.

Philosophy: Pattern notation, not identity. Lens, not truth.

Provides:
- Lo Shu Grid computation (Vedic)
- Core pattern generation (sharp, confronting)
- WHERE THIS MISFIRES (real-world behavior)
- WHERE THIS COSTS YOU (energy, relationships, trust)
- ONE WAY TO BALANCE TODAY (practical action)
- Precise reflection questions
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# =============================================================================
# LO SHU GRID COMPUTATION (VEDIC - Primary System)
# =============================================================================

def compute_lo_shu_grid(birth_date: datetime) -> Dict[str, Any]:
    """
    Compute Lo Shu Grid from birth date (Vedic numerology).
    
    The Lo Shu Grid is a 3x3 grid showing presence/absence of numbers 1-9.
    Numbers are derived from the birth date digits.
    
    Grid positions:
    4 | 9 | 2
    3 | 5 | 7  
    8 | 1 | 6
    
    Returns:
        {
            'lo_shu_template': [[4,9,2],[3,5,7],[8,1,6]],
            'lo_shu_counts': {'1': 2, '8': 1, ...},
            'lo_shu_display': [["4","9","—"],["—","—","—"],["8","1 1","6"]],
            'present_numbers': {'1': 2, '8': 1, ...},
            'missing_numbers': [3, 5, 7]
        }
    """
    # Extract all digits from birth date
    date_str = birth_date.strftime('%d%m%Y')  # e.g., "01111988"
    digits = [int(d) for d in date_str if d != '0']  # Remove zeros
    
    # Count occurrences of each number 1-9
    present_numbers = {}
    for d in digits:
        if 1 <= d <= 9:
            present_numbers[str(d)] = present_numbers.get(str(d), 0) + 1
    
    # Find missing numbers
    missing_numbers = [n for n in range(1, 10) if str(n) not in present_numbers]
    
    # Standard Lo Shu grid template (positions)
    lo_shu_template = [[4, 9, 2], [3, 5, 7], [8, 1, 6]]
    
    # Build display grid with actual user data
    lo_shu_display = []
    for row in lo_shu_template:
        display_row = []
        for num in row:
            count = present_numbers.get(str(num), 0)
            if count == 0:
                display_row.append("—")
            elif count == 1:
                display_row.append(str(num))
            else:
                # Repeat the number for multiple occurrences
                display_row.append(" ".join([str(num)] * count))
        lo_shu_display.append(display_row)
    
    return {
        'lo_shu_template': lo_shu_template,
        'lo_shu_counts': present_numbers,
        'lo_shu_display': lo_shu_display,
        'present_numbers': present_numbers,
        'missing_numbers': missing_numbers
    }

# =============================================================================
# NUMBER MEANINGS FOR PATTERN GENERATION
# =============================================================================

NUMBER_CORE_MEANINGS = {
    1: {'energy': 'initiation, independence, action', 'shadow': 'isolation, domination', 'verb': 'initiates'},
    2: {'energy': 'sensitivity, partnership, processing', 'shadow': 'dependency, over-accommodation', 'verb': 'connects'},
    3: {'energy': 'expression, creativity, joy', 'shadow': 'superficiality, scattered energy', 'verb': 'expresses'},
    4: {'energy': 'stability, structure, grounding', 'shadow': 'rigidity, limitation', 'verb': 'builds'},
    5: {'energy': 'freedom, change, experience', 'shadow': 'restlessness, excess', 'verb': 'moves'},
    6: {'energy': 'responsibility, care, harmony', 'shadow': 'martyrdom, control', 'verb': 'nurtures'},
    7: {'energy': 'analysis, depth, spirituality', 'shadow': 'isolation, cynicism', 'verb': 'analyzes'},
    8: {'energy': 'power, manifestation, karma', 'shadow': 'materialism, manipulation', 'verb': 'manifests'},
    9: {'energy': 'completion, wisdom, service', 'shadow': 'martyrdom, escapism', 'verb': 'completes'},
    11: {'energy': 'intuition, inspiration, vision', 'shadow': 'anxiety, impracticality', 'verb': 'illuminates'},
    22: {'energy': 'mastery, large-scale building', 'shadow': 'overwhelm, scattered power', 'verb': 'constructs'},
    33: {'energy': 'teaching, healing, compassion', 'shadow': 'self-sacrifice, delusion', 'verb': 'heals'}
}

# =============================================================================
# CONTINUATION LAYER (V2) - Bridge from Mirror Home
# =============================================================================

import random

CONTINUATION_LINES = [
    "This is the same pattern — just from a different angle.",
    "You're seeing the same thing again, just clearer here.",
    "This connects to what showed up earlier.",
    "Same pattern. Different lens.",
    "The same signal, just louder here.",
    "What you noticed before — this is the root of it.",
    "You've already felt this. Now you're seeing where it comes from."
]

def generate_continuation_line() -> str:
    """
    Generate a short continuation line that bridges from Mirror Home.
    
    Purpose: User should feel "This is the same intelligence, just going deeper"
    NOT: "I've opened a different system"
    
    Rules:
    - Short
    - Calm
    - Matter-of-fact
    - No explanation of numerology system
    - No jargon
    """
    return random.choice(CONTINUATION_LINES)


# =============================================================================
# CROSS-LENS ECHO (V3.1) - Recognition of lived repetition
# =============================================================================

ECHO_LINES = [
    # Neutral (kept from V3)
    "This isn't new.",
    "You've felt this before.",
    "You know this one.",
    # Sharp / Lived (V3.1 upgrade)
    "You keep ending up here.",
    "You've hit this before.",
    "This is where it loops.",
    "You don't get past this — it resets.",
    "You've already been here recently.",
    "You thought you moved past this.",
    "This part again.",
    "You're back in the same spot."
]

def generate_echo_line() -> str:
    """
    Generate a short echo line that reinforces lived pattern repetition.
    
    V3.1 Purpose: User should feel "I keep ending up here"
    
    Rules:
    - 1 short line only
    - No explanation
    - No system references
    - No abstract phrasing
    - Must feel immediate and personal
    
    Tone:
    - Grounded
    - Matter-of-fact
    - Slightly confronting
    - Not dramatic, not mystical
    """
    return random.choice(ECHO_LINES)


# =============================================================================
# GENIUS LAYER - Why the pattern exists (V9 Mirror System)
# =============================================================================

LIFE_PATH_GENIUS = {
    1: "You don't wait once you feel direction. That's why you move before others are ready.",
    2: "You feel what's off before anyone says it. That's why you're already adjusting before others notice.",
    3: "You process by expressing. That's why silence feels like something's stuck.",
    4: "You see instability before it breaks. That's why you're already building walls others don't need yet.",
    5: "You feel when something's dead before it ends. That's why you're already leaving when others are still settling in.",
    6: "You sense when someone's struggling. That's why you reach before they ask.",
    7: "You notice what doesn't add up. That's why you're still analyzing when others have moved on.",
    8: "You see where the power sits. That's why you're already positioning when others are still reacting.",
    9: "You see how things end. That's why you're already grieving what hasn't finished yet.",
    11: "You catch signals others miss. That's why you're frustrated when no one else sees it coming.",
    22: "You see the larger structure. That's why small fixes feel like a waste of time.",
    33: "You absorb what others carry. That's why you're tired before you've done anything for yourself."
}

def generate_genius_line(life_path: int) -> str:
    """
    Generate the GENIUS line for V9 Mirror System integration.
    
    Rules:
    - 1-2 lines max
    - No hype, no identity statements ("you are...")
    - Must explain WHY pattern exists
    - Must feel slightly confronting
    
    Format: "[Observation]. That's why [consequence behavior]."
    """
    return LIFE_PATH_GENIUS.get(life_path, 
        "You run your pattern before you check if it's working. That's why the same results keep showing up."
    )


# =============================================================================
# WHERE THIS MISFIRES - Real-world behavior patterns
# =============================================================================

def generate_where_this_misfires(
    life_path: int,
    missing_numbers: List[int],
    present_counts: Dict[str, int]
) -> List[str]:
    """
    Generate 2-3 specific ways this pattern misfires in real life.
    
    Rules:
    - Concrete behaviors, not abstract tendencies
    - Specific situations where the pattern works against you
    - Confronting but recognizable
    """
    misfires = []
    
    # Life path misfires
    lp_misfires = {
        1: [
            "You start moving before the other person has finished talking",
            "You dismiss input that would have changed your course",
            "You push through warning signs that were trying to slow you down"
        ],
        2: [
            "You say yes when you mean maybe—and end up resenting it",
            "You absorb someone else's mood and forget what you were feeling",
            "You wait for approval that never comes"
        ],
        3: [
            "You overshare before you've fully processed what happened",
            "You scatter energy across too many interests and finish none",
            "You talk about doing the work instead of doing it"
        ],
        4: [
            "You rebuild systems that were working fine",
            "You get stuck perfecting details no one will notice",
            "You say no to opportunities that don't fit your timeline"
        ],
        5: [
            "You leave before giving something enough time to work",
            "You mistake restlessness for intuition",
            "You start over instead of solving the problem in front of you"
        ],
        6: [
            "You fix problems no one asked you to fix",
            "You sacrifice your needs to avoid difficult conversations",
            "You take responsibility for outcomes outside your control"
        ],
        7: [
            "You analyze your way out of decisions that need to be felt",
            "You reject feedback before fully hearing it",
            "You isolate when connection is what you actually need"
        ],
        8: [
            "You push through resistance that's trying to tell you something",
            "You track results at the expense of relationships",
            "You see power dynamics that weren't there"
        ],
        9: [
            "You move on before you've fully completed what you started",
            "You detach when presence is what's needed",
            "You offer wisdom when someone just wanted to be heard"
        ],
        11: [
            "You trust a vision before checking if the ground will support it",
            "You overwhelm yourself with possibilities",
            "You see what's coming but can't get others to see it with you"
        ],
        22: [
            "You build systems that are too big for the current moment",
            "You delay starting because the plan isn't perfect",
            "You exhaust yourself on projects that weren't yours to carry"
        ],
        33: [
            "You heal others at the cost of your own wellbeing",
            "You attract people who drain more than they give",
            "You teach before you've learned the lesson yourself"
        ]
    }
    
    misfires.extend(lp_misfires.get(life_path, [
        "You run the pattern on autopilot without checking if it's working",
        "You overcorrect for old wounds in situations that don't require it"
    ]))
    
    return misfires[:3]


# =============================================================================
# WHERE THIS COSTS YOU - Energy, relationships, trust
# =============================================================================

def generate_where_this_costs_you(
    life_path: int,
    missing_numbers: List[int]
) -> Dict[str, str]:
    """
    Generate specific costs for each pattern.
    
    Returns dict with:
    - energy_cost: how it drains you
    - relationship_cost: how it affects connections
    - trust_cost: how it erodes self-trust or credibility
    """
    
    costs = {
        1: {
            'energy_cost': 'Starting over repeatedly instead of building on what exists',
            'relationship_cost': 'People stop offering input because you move anyway',
            'trust_cost': 'Others learn to wait you out instead of engage'
        },
        2: {
            'energy_cost': 'Processing everyone else\'s feelings before your own',
            'relationship_cost': 'People don\'t know what you actually want',
            'trust_cost': 'Your yes loses weight because you say it too often'
        },
        3: {
            'energy_cost': 'Spinning on creative projects that never ship',
            'relationship_cost': 'People hear your plans more than your results',
            'trust_cost': 'Your excitement gets discounted because it\'s always there'
        },
        4: {
            'energy_cost': 'Maintaining structures that should be simplified or released',
            'relationship_cost': 'Others feel judged for their chaos',
            'trust_cost': 'You\'re seen as rigid even when you\'re just being careful'
        },
        5: {
            'energy_cost': 'Starting from scratch repeatedly instead of deepening',
            'relationship_cost': 'People stop investing because you might leave',
            'trust_cost': 'Your commitments carry less weight because they\'ve shifted before'
        },
        6: {
            'energy_cost': 'Carrying responsibilities that were never yours',
            'relationship_cost': 'People lean too heavily because you always catch them',
            'trust_cost': 'You\'re overlooked for your own needs because you hide them'
        },
        7: {
            'energy_cost': 'Researching past the point of usefulness',
            'relationship_cost': 'People feel analyzed rather than understood',
            'trust_cost': 'Your conclusions get dismissed because they came without emotion'
        },
        8: {
            'energy_cost': 'Fighting battles that don\'t need to be won',
            'relationship_cost': 'People feel like transactions instead of connections',
            'trust_cost': 'Your drive gets mistaken for ambition without care'
        },
        9: {
            'energy_cost': 'Holding the big picture while ignoring the details that need you',
            'relationship_cost': 'People feel you\'re already gone before you leave',
            'trust_cost': 'Your wisdom gets dismissed because it sounds detached'
        },
        11: {
            'energy_cost': 'Living in vision while neglecting practical ground',
            'relationship_cost': 'People can\'t follow where you\'re pointing',
            'trust_cost': 'Your insights get ignored because they can\'t be proven yet'
        },
        22: {
            'energy_cost': 'Building beyond your current capacity',
            'relationship_cost': 'People feel like pieces in a larger plan',
            'trust_cost': 'Your timelines lose credibility because they\'re too ambitious'
        },
        33: {
            'energy_cost': 'Giving until you\'re empty',
            'relationship_cost': 'People don\'t know when you need them to give back',
            'trust_cost': 'Your guidance gets taken for granted because it\'s always available'
        }
    }
    
    return costs.get(life_path, {
        'energy_cost': 'Running the pattern without checking if it\'s still serving you',
        'relationship_cost': 'Others can\'t meet you where you are because you hide it',
        'trust_cost': 'Self-trust erodes when the pattern keeps producing the same outcome'
    })


# =============================================================================
# ONE WAY TO BALANCE TODAY - Situational specificity with micro-references
# =============================================================================

def generate_balance_today(
    life_path: int,
    missing_numbers: List[int]
) -> str:
    """
    Generate ONE practical, grounded action for today.
    
    Rules:
    - Specific and doable
    - References real behavior patterns (the thing you've been circling)
    - Takes less than 10 minutes
    """
    
    balance_actions = {
        1: "Before you act on the thing you've been about to do — ask one person for input. Wait for their full answer before moving.",
        2: "The next time someone asks you for something, say 'I need a moment' instead of answering. Even if you already know what you want to say.",
        3: "The idea you've already talked about — do one concrete step on it before mentioning it again.",
        4: "The thing you've been wanting to fix or reorganize — let it stay imperfect for the rest of the day. Notice what happens.",
        5: "The thing you're ready to leave or move on from — stay with it 10% longer than feels comfortable. Notice what you learn.",
        6: "Someone you've been wanting to help — don't. Let them struggle. Notice how it feels to not be the one fixing it.",
        7: "The decision you've been researching — make it today using only how it feels. No more information gathering.",
        8: "The thing you're tracking or measuring progress on — do it once today without tracking. Just do it.",
        9: "The big picture you keep referencing — zoom into one specific detail instead. Give it your full attention for 10 minutes.",
        11: "The insight you've been sitting on — write down three specific steps to make it real. No more vision until it has legs.",
        22: "The bigger plan you've been perfecting — take one small action on it today. Imperfect is fine.",
        33: "The next request that comes in — say no. Even if you could easily say yes. Even if they need you."
    }
    
    return balance_actions.get(life_path, 
        "The pattern you've been running today — pause before repeating it. Ask: is this actually serving me right now?"
    )


# =============================================================================
# HOW THIS SHOWS UP TODAY - Time-aware, context-aware
# =============================================================================

def generate_today_bridge(life_path: int) -> List[str]:
    """
    Generate 2-3 specific ways this pattern shows up TODAY.
    
    Rules:
    - Present tense, current moment
    - Specific behavior, not general trait
    - Feels like "this is what I'm doing right now"
    """
    
    today_bridges = {
        1: [
            "You're already thinking about the next thing before finishing what's in front of you",
            "You've dismissed feedback today without fully hearing it",
            "You're about to move forward on something without checking if others are ready"
        ],
        2: [
            "You've already said yes to something you meant to think about first",
            "You're carrying someone else's emotional weight and calling it 'being supportive'",
            "You're waiting for a signal from someone instead of checking your own knowing"
        ],
        3: [
            "You've talked about an idea more than you've worked on it today",
            "You're juggling multiple creative threads and none of them are moving",
            "You shared something personal before you fully processed it"
        ],
        4: [
            "You're fixing something that didn't need fixing",
            "You've already spent time organizing or planning instead of doing",
            "You're resisting a change because it doesn't fit your system"
        ],
        5: [
            "You're already restless with something you just started",
            "You're considering leaving or changing something that hasn't had time to work",
            "You've mistaken boredom for a sign that you need to move on"
        ],
        6: [
            "You've taken on responsibility for something that wasn't yours to carry",
            "You're managing someone else's emotions instead of letting them feel it",
            "You've avoided a difficult conversation by just handling it yourself"
        ],
        7: [
            "You've researched past the point where it's useful today",
            "You're holding back from acting because you don't have enough information",
            "You've analyzed a feeling instead of just feeling it"
        ],
        8: [
            "You've pushed through resistance that was trying to tell you something",
            "You're tracking progress on something instead of just being in it",
            "You've noticed a power dynamic that might not actually be there"
        ],
        9: [
            "You've given advice when someone just wanted to be heard",
            "You're mentally already past something that's still happening",
            "You've detached from a detail that actually needed your attention"
        ],
        11: [
            "You've seen something others haven't — and you're frustrated they can't see it too",
            "You're living in a vision that doesn't have practical legs yet",
            "You've overwhelmed yourself with possibilities instead of picking one"
        ],
        22: [
            "You're planning something too big for the current moment",
            "You've delayed starting because the plan isn't perfect",
            "You're carrying a project that was never supposed to be yours alone"
        ],
        33: [
            "You've given to someone who hasn't given back in a while",
            "You're teaching or guiding before you've learned the lesson yourself",
            "You've attracted a conversation or request that's draining you"
        ]
    }
    
    return today_bridges.get(life_path, [
        "The pattern is running today — you just haven't noticed it yet",
        "Something you're doing today is a repeat of what you did yesterday"
    ])


# =============================================================================
# WHEN THIS GETS TRIGGERED - Context triggers
# =============================================================================

def generate_triggers(life_path: int) -> List[str]:
    """
    Generate 3-4 specific triggers that activate this pattern.
    
    Categories: pressure, urgency, social expectation, lack of processing time
    """
    
    triggers = {
        1: [
            "When someone is moving slower than you want",
            "When you feel blocked or dependent on others",
            "When there's urgency and you see a clear path forward",
            "When feedback feels like a delay tactic"
        ],
        2: [
            "When someone asks you for an answer before you've had time to feel into it",
            "When you sense emotional tension in the room",
            "When someone you care about is struggling",
            "When you're afraid saying no will damage the relationship"
        ],
        3: [
            "When you have a new idea you're excited about",
            "When you feel unheard or unseen",
            "When there's social energy and an audience",
            "When staying quiet feels like disappearing"
        ],
        4: [
            "When something feels disorganized or unstable",
            "When someone else's chaos touches your system",
            "When change is introduced without structure",
            "When you feel like things could fall apart"
        ],
        5: [
            "When you've been in one place or project too long",
            "When someone tries to pin you down or make you commit",
            "When routine starts feeling like a cage",
            "When excitement shows up somewhere new"
        ],
        6: [
            "When someone you care about is in trouble",
            "When harmony is at risk",
            "When saying no would make you feel selfish",
            "When it's easier to fix it than to have the conversation"
        ],
        7: [
            "When you're asked to decide without enough information",
            "When you feel emotionally exposed",
            "When people expect you to engage before you've processed",
            "When intuition shows up without logic to back it"
        ],
        8: [
            "When power dynamics feel unclear or shifting",
            "When you sense someone testing your authority",
            "When there's competition or scarcity",
            "When results aren't coming fast enough"
        ],
        9: [
            "When details feel tedious or irrelevant",
            "When someone is asking you to narrow your focus",
            "When closure is being forced before you're ready",
            "When you feel pressure to stay engaged when you're ready to move on"
        ],
        11: [
            "When you see something others can't see yet",
            "When you're asked to explain what you just 'know'",
            "When the practical world feels too slow for your vision",
            "When anxiety spikes without a clear cause"
        ],
        22: [
            "When you see a system that could be built better",
            "When you're handed a project that's bigger than expected",
            "When perfection feels achievable if you just had more time",
            "When others aren't meeting your standards"
        ],
        33: [
            "When someone needs you",
            "When you sense pain or struggle in another person",
            "When saying no would feel like abandonment",
            "When you believe your guidance could change an outcome"
        ]
    }
    
    return triggers.get(life_path, [
        "When pressure shows up",
        "When urgency is high",
        "When social expectations kick in",
        "When you don't have time to process"
    ])


# =============================================================================
# CORE PATTERN GENERATOR
# =============================================================================

def generate_core_pattern(
    life_path: int,
    expression: Optional[int],
    soul_urge: Optional[int],
    missing_numbers: List[int]
) -> str:
    """
    Generate a sharp, confronting core pattern statement.
    
    Format: 1-2 lines max, direct, no hedging.
    
    Examples:
    - "You are built to see quickly and move quickly—but not naturally built to stabilize or express what you see."
    - "You initiate powerfully but struggle to follow through on emotional commitments."
    """
    # Start with life path core
    pattern_parts = []
    
    # Life path strength
    if life_path == 1:
        pattern_parts.append("You initiate quickly and act decisively")
    elif life_path == 2:
        pattern_parts.append("You read emotional undercurrents that others miss")
    elif life_path == 3:
        pattern_parts.append("You communicate naturally and crave expression")
    elif life_path == 4:
        pattern_parts.append("You build steadily and value what lasts")
    elif life_path == 5:
        pattern_parts.append("You adapt rapidly and need constant movement")
    elif life_path == 6:
        pattern_parts.append("You take responsibility even when it isn't yours")
    elif life_path == 7:
        pattern_parts.append("You analyze deeply before committing to anything")
    elif life_path == 8:
        pattern_parts.append("You see power dynamics clearly and navigate them well")
    elif life_path == 9:
        pattern_parts.append("You see the larger picture that others struggle to grasp")
    elif life_path == 11:
        pattern_parts.append("You perceive things before they become visible to others")
    elif life_path == 22:
        pattern_parts.append("You think in systems and structures that span years")
    elif life_path == 33:
        pattern_parts.append("You absorb others' pain without being asked")
    else:
        pattern_parts.append("You carry a unique energetic signature")
    
    # Add missing number tension
    if missing_numbers:
        missing_str = ', '.join([str(n) for n in missing_numbers[:3]])
        
        if 3 in missing_numbers:
            pattern_parts.append("—but expressing what you know doesn't come naturally")
        elif 4 in missing_numbers:
            pattern_parts.append("—but stabilizing and grounding your insights is a struggle")
        elif 5 in missing_numbers:
            pattern_parts.append("—but adapting to rapid change feels forced")
        elif 6 in missing_numbers:
            pattern_parts.append("—but domestic harmony eludes you")
        elif 7 in missing_numbers:
            pattern_parts.append("—but deep analysis feels like work, not instinct")
        elif 2 in missing_numbers:
            pattern_parts.append("—but emotional nuance isn't your native language")
        elif 1 in missing_numbers:
            pattern_parts.append("—but initiating alone is uncomfortable")
        elif 8 in missing_numbers:
            pattern_parts.append("—but material mastery doesn't hold your attention")
        elif 9 in missing_numbers:
            pattern_parts.append("—but letting go and completing cycles is hard")
        else:
            pattern_parts.append(f"—missing {missing_str} creates gaps in your natural flow")
    
    return ''.join(pattern_parts) + '.'

# =============================================================================
# HOW THIS SHOWS UP GENERATOR
# =============================================================================

def generate_how_this_shows_up(
    life_path: int,
    expression: Optional[int],
    missing_numbers: List[int],
    present_counts: Dict[str, int]
) -> List[str]:
    """
    Generate 3-5 specific behavioral tendencies.
    
    Rules:
    - Real behavioral patterns only
    - Grounded, not absolute
    - Confronting but fair
    - Behavioral, not mystical
    """
    behaviors = []
    
    # Life path behaviors - refined to be less absolute
    lp_behaviors = {
        1: [
            "You often start projects before fully mapping them out - and frequently finish them anyway",
            "You tend to resist asking for help until you've already tried on your own",
            "Your pace of decision-making can outrun those around you"
        ],
        2: [
            "You often pick up on tension in a room before it's spoken",
            "You tend to over-explain when you sense you're being misunderstood",
            "You may give more than you receive in many relationships"
        ],
        3: [
            "You often have multiple creative threads open at once",
            "Thinking tends to happen out loud for you - talking is processing",
            "Your emotional state can visibly influence the energy around you"
        ],
        4: [
            "Chaotic environments tend to create physical discomfort for you",
            "You often create systems even when no one requests them",
            "Shortcuts that skip necessary steps tend to bother you"
        ],
        5: [
            "Routine can feel constraining even when you chose it",
            "You may leave situations before they become fully unbearable",
            "You're often drawn to people and places that challenge your current setup"
        ],
        6: [
            "You often take on other people's problems as your responsibility",
            "You may sacrifice personal needs to maintain harmony around you",
            "You can feel responsible for outcomes outside your direct control"
        ],
        7: [
            "You tend to research extensively before making commitments",
            "Processing time alone is often necessary, even for positive experiences",
            "Your own analysis usually carries more weight than outside opinions"
        ],
        8: [
            "You often notice the power dynamics in any room you enter",
            "High-stakes decisions tend to feel comfortable rather than stressful",
            "You track value and results in situations where others don't"
        ],
        9: [
            "You often see patterns that connect seemingly unrelated events",
            "Endings and transitions tend to draw your attention",
            "You may release attachments with less difficulty than most"
        ],
        11: [
            "Insights often arrive before you have language for them",
            "You may sense things unfolding before concrete evidence appears",
            "Environments that others tolerate can feel overwhelming to you"
        ],
        22: [
            "Your thinking often operates on longer timelines than those around you",
            "Small-scale solutions can feel frustrating when bigger structures are needed",
            "You tend to build frameworks - physical, organizational, or conceptual"
        ],
        33: [
            "You often absorb the emotional weight others are carrying",
            "People frequently share their struggles with you without prompting",
            "Teaching happens through your presence as much as your words"
        ]
    }
    
    behaviors.extend(lp_behaviors.get(life_path, [
        "Your patterns follow a rhythm that's distinctly yours",
        "Your life operates on a beat that doesn't match conventional timelines"
    ]))
    
    # Add missing number behaviors - softer language
    for missing in missing_numbers[:2]:
        missing_behaviors = {
            1: "Group consensus may carry more weight for you than solo conviction",
            2: "The larger pattern can grab your attention before relational nuance registers",
            3: "Articulating what you're thinking may take more effort than thinking it",
            4: "Starting strong comes naturally, but sustained maintenance can drain energy",
            5: "Familiar patterns can feel safer than necessary change, even when change would help",
            6: "Domestic responsibilities may feel like an interruption rather than a calling",
            7: "Decisions sometimes happen before deep analysis has run its course",
            8: "Value and material results may get less tracking than other priorities",
            9: "Letting go of what's complete can take longer than it needs to"
        }
        if missing in missing_behaviors:
            behaviors.append(missing_behaviors[missing])
    
    # Check for repeated numbers (emphasis) - softer
    for num_str, count in present_counts.items():
        if count >= 2:
            num = int(num_str)
            emphasis_behaviors = {
                1: "Independence is amplified - self-reliance runs strong in your pattern",
                2: "Sensitivity is heightened - you tend to feel things with extra depth",
                3: "Expressiveness is doubled - communication is a constant current",
                4: "Structure needs are intensified - chaos tolerance runs low",
                5: "The pull toward change is urgent - stability can feel like stagnation",
                6: "Responsibility runs strong - you may carry more than your share",
                7: "Analysis runs deep - thinking tends to be thorough, sometimes excessively",
                8: "Power awareness is amplified - results and outcomes stay in focus",
                9: "The big picture dominates - but so does the pull to disengage"
            }
            if num in emphasis_behaviors:
                behaviors.append(emphasis_behaviors[num])
    
    return behaviors[:5]  # Max 5 behaviors

# =============================================================================
# INTERNAL TENSION GENERATOR
# =============================================================================

def generate_internal_tensions(
    life_path: int,
    expression: Optional[int],
    soul_urge: Optional[int],
    missing_numbers: List[int],
    present_counts: Dict[str, int]
) -> List[Dict[str, str]]:
    """
    Generate 2-3 X vs Y tensions.
    
    Format:
    {
        'a': 'Fast action (1)',
        'b': 'emotional processing (2)',
        'description': 'You move before you feel—then the feelings catch up'
    }
    """
    tensions = []
    
    # Life path vs missing number tensions
    for missing in missing_numbers[:2]:
        tension_map = {
            (1, 2): {
                'a': f'Fast action ({life_path})',
                'b': f'emotional processing ({missing})',
                'description': 'You move before you feel—then the feelings catch up later'
            },
            (1, 4): {
                'a': f'Quick initiation ({life_path})',
                'b': f'stable foundation ({missing})',
                'description': 'You start quickly but building something lasting takes effort'
            },
            (2, 1): {
                'a': f'Sensitivity ({life_path})',
                'b': f'decisive action ({missing})',
                'description': 'You feel everything but acting on it does not come naturally'
            },
            (3, 7): {
                'a': f'Expression ({life_path})',
                'b': f'deep analysis ({missing})',
                'description': 'You speak before you have fully understood - wisdom lags behind words'
            },
            (5, 4): {
                'a': f'Constant movement ({life_path})',
                'b': f'stable grounding ({missing})',
                'description': 'You crave change but lack the foundation to sustain it'
            },
            (7, 3): {
                'a': f'Deep analysis ({life_path})',
                'b': f'free expression ({missing})',
                'description': 'You understand deeply but struggle to communicate what you know'
            },
            (11, 4): {
                'a': f'Vision ({life_path})',
                'b': f'practical grounding ({missing})',
                'description': 'You see far ahead but building the bridge there is frustrating'
            }
        }
        
        key = (life_path if life_path <= 9 else life_path, missing)
        if key in tension_map:
            tensions.append(tension_map[key])
        elif (missing, life_path if life_path <= 9 else life_path) in tension_map:
            tensions.append(tension_map[(missing, life_path if life_path <= 9 else life_path)])
    
    # Add expression vs soul urge tension if both present
    if expression and soul_urge and expression != soul_urge:
        exp_verb = NUMBER_CORE_MEANINGS.get(expression, {}).get('verb', 'acts')
        su_verb = NUMBER_CORE_MEANINGS.get(soul_urge, {}).get('verb', 'wants')
        
        tensions.append({
            'a': f'How you present ({expression})',
            'b': f'what you truly want ({soul_urge})',
            'description': f'The face you show {exp_verb}—but your soul {su_verb} something different'
        })
    
    # Add doubled number tension
    for num_str, count in present_counts.items():
        if count >= 2:
            num = int(num_str)
            if num in NUMBER_CORE_MEANINGS:
                meaning = NUMBER_CORE_MEANINGS[num]
                tensions.append({
                    'a': f'Amplified {meaning["energy"].split(",")[0]} ({num}×{count})',
                    'b': 'balance and moderation',
                    'description': 'This energy is doubled—making it both a gift and a blind spot'
                })
                break  # Only one doubled number tension
    
    return tensions[:3]  # Max 3 tensions

# =============================================================================
# MIRROR MOMENT GENERATOR
# =============================================================================

def generate_mirror_moment(
    life_path: int,
    tensions: List[Dict[str, str]],
    missing_numbers: List[int]
) -> str:
    """
    Generate a precise reflection question based on the pattern tensions.
    
    Not generic—must be derived from the specific tensions identified.
    """
    if tensions:
        # Use the primary tension to generate the question
        primary_tension = tensions[0]
        a = primary_tension['a'].split('(')[0].strip().lower()
        b = primary_tension['b'].split('(')[0].strip().lower()
        
        return f"Where in your life is {a} running ahead of {b}—and what would it cost to slow down?"
    
    # Fallback based on missing numbers
    if missing_numbers:
        missing = missing_numbers[0]
        missing_energy = NUMBER_CORE_MEANINGS.get(missing, {}).get('energy', 'this energy').split(',')[0]
        return f"Where are you compensating for the absence of {missing_energy}—and is it working?"
    
    # Life path fallback
    lp_energy = NUMBER_CORE_MEANINGS.get(life_path, {}).get('energy', 'your core energy').split(',')[0]
    return f"Where is your {lp_energy} serving you—and where has it become a pattern you're running on autopilot?"

# =============================================================================
# MAIN PATTERN COMPUTATION
# =============================================================================

async def compute_numerology_pattern(
    db,
    user_id: str,
    birth_date: datetime,
    full_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Compute the complete numerology pattern system for a user.
    
    System: Vedic (date-based) is PRIMARY. Western (name-based) is SECONDARY.
    
    Returns:
        {
            'life_path': int,
            'expression': int | null,
            'soul_urge': int | null,
            'personality': int | null,
            'birth_date': str,
            'has_name_numbers': bool,
            'system_explanation': str,
            'lo_shu_template': [[int]],
            'lo_shu_display': [[str]],
            'present_numbers': {str: int},
            'missing_numbers': [int],
            'core_pattern': str,
            'how_this_shows_up': [str],
            'how_this_shows_up_today': [str],  # NEW: Time-aware
            'when_this_gets_triggered': [str],  # NEW: Context triggers
            'where_this_misfires': [str],
            'where_this_costs_you': {energy_cost, relationship_cost, trust_cost},
            'balance_today': str,
            'internal_tensions': [{a, b, description}],
            'mirror_moment': str
        }
    """
    from calculations.numerology import (
        calculate_life_path,
        calculate_expression_number,
        calculate_soul_urge,
        calculate_personality_number
    )
    
    # Calculate core numbers
    life_path_result = calculate_life_path(birth_date)
    life_path = life_path_result['number']
    
    expression = None
    soul_urge = None
    personality = None
    has_name_numbers = False
    
    if full_name:
        expression_result = calculate_expression_number(full_name)
        expression = expression_result['number']
        
        soul_urge_result = calculate_soul_urge(full_name)
        soul_urge = soul_urge_result['number']
        
        personality_result = calculate_personality_number(full_name)
        personality = personality_result['number']
        has_name_numbers = True
    
    # Compute Lo Shu grid (Vedic - Primary)
    lo_shu = compute_lo_shu_grid(birth_date)
    
    # Generate pattern content
    core_pattern = generate_core_pattern(
        life_path, expression, soul_urge, lo_shu['missing_numbers']
    )
    
    how_shows_up = generate_how_this_shows_up(
        life_path, expression, lo_shu['missing_numbers'], lo_shu['present_numbers']
    )
    
    # NEW: Time-aware today bridge
    how_shows_up_today = generate_today_bridge(life_path)
    
    # NEW: Context triggers
    when_triggered = generate_triggers(life_path)
    
    # GENIUS layer (V9 Mirror System) - Why the pattern exists
    genius_line = generate_genius_line(life_path)
    
    # CONTINUATION layer (V2) - Bridge from Mirror Home
    continuation_line = generate_continuation_line()
    
    # ECHO layer (V3) - Cross-lens reinforcement
    echo_line = generate_echo_line()
    
    # Action-relevant sections
    where_misfires = generate_where_this_misfires(
        life_path, lo_shu['missing_numbers'], lo_shu['present_numbers']
    )
    
    where_costs = generate_where_this_costs_you(
        life_path, lo_shu['missing_numbers']
    )
    
    balance_today = generate_balance_today(
        life_path, lo_shu['missing_numbers']
    )
    
    internal_tensions = generate_internal_tensions(
        life_path, expression, soul_urge, 
        lo_shu['missing_numbers'], lo_shu['present_numbers']
    )
    
    mirror_moment = generate_mirror_moment(
        life_path, internal_tensions, lo_shu['missing_numbers']
    )
    
    # System explanation (Vedic-first positioning)
    system_explanation = (
        "Your core pattern comes from your birth date (Vedic numerology). "
        "Your name adds an identity layer on top of it."
    ) if not has_name_numbers else (
        "Your birth date reveals the core pattern. "
        "Your name shows how you express and refine it."
    )
    
    return {
        # CONTINUATION layer (V2) - FIRST, bridges from Mirror Home
        'continuation': continuation_line,
        # Core identifiers
        'life_path': life_path,
        'expression': expression,
        'soul_urge': soul_urge,
        'personality': personality,
        'birth_date': birth_date.isoformat(),
        'has_name_numbers': has_name_numbers,
        'system_explanation': system_explanation,
        # Lo Shu structure (Vedic - Primary System)
        'lo_shu_template': lo_shu['lo_shu_template'],
        'lo_shu_counts': lo_shu['lo_shu_counts'],
        'lo_shu_display': lo_shu['lo_shu_display'],
        # Keep these for backward compatibility
        'present_numbers': lo_shu['present_numbers'],
        'missing_numbers': lo_shu['missing_numbers'],
        # Pattern content (V3 Structure: Continuation → Core → Echo → Shows → Backfires → Genius → Cost → Shift)
        'core_pattern': core_pattern,
        # ECHO layer (V3) - Cross-lens reinforcement, goes after Core Truth
        'echo': echo_line,
        'how_this_shows_up': how_shows_up,
        # NEW: Time-aware sections
        'how_this_shows_up_today': how_shows_up_today,
        'when_this_gets_triggered': when_triggered,
        # GENIUS layer (V9) - Goes between recognition and consequence
        'genius': genius_line,
        # Action-relevant sections (consequence/cost)
        'where_this_misfires': where_misfires,
        'where_this_costs_you': where_costs,
        'balance_today': balance_today,
        # Original sections
        'internal_tensions': internal_tensions,
        'mirror_moment': mirror_moment
    }
