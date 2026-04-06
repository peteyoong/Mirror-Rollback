"""
Numerology Compute Service
===========================

DETERMINISTIC COMPUTATION LAYER
===============================
This service provides pure, deterministic numerology calculations.
No LLM involved. All outputs are reproducible and transparent.

COMPUTE ≠ SURFACED ≠ INTERPRETED

Systems:
1. Pythagorean (Western) - Name-based calculations
2. Lo Shu (Vedic) - Birth date digit distribution

Author: Mirror System
"""

from datetime import datetime
from typing import Dict, List, Optional, Any


# =============================================================================
# PYTHAGOREAN LETTER VALUES (Western Numerology)
# =============================================================================

PYTHAGOREAN_VALUES = {
    'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8, 'I': 9,
    'J': 1, 'K': 2, 'L': 3, 'M': 4, 'N': 5, 'O': 6, 'P': 7, 'Q': 8, 'R': 9,
    'S': 1, 'T': 2, 'U': 3, 'V': 4, 'W': 5, 'X': 6, 'Y': 7, 'Z': 8
}

VOWELS = set('AEIOU')


# =============================================================================
# CORE REDUCTION FUNCTION
# =============================================================================

def reduce_to_single_digit(number: int, allow_master: bool = True) -> int:
    """Reduce number to single digit (or master number 11, 22, 33)"""
    while number > 9:
        if allow_master and number in [11, 22, 33]:
            return number
        number = sum(int(digit) for digit in str(number))
    return number


# =============================================================================
# PYTHAGOREAN CALCULATIONS
# =============================================================================

def compute_life_path(birth_date: datetime) -> int:
    """
    Calculate Life Path number from birth date.
    
    Method: Add all digits of birth date and reduce.
    """
    day = birth_date.day
    month = birth_date.month
    year = birth_date.year
    
    # Reduce each component
    day_sum = reduce_to_single_digit(day)
    month_sum = reduce_to_single_digit(month)
    year_sum = reduce_to_single_digit(sum(int(d) for d in str(year)))
    
    # Combine and reduce
    total = day_sum + month_sum + year_sum
    return reduce_to_single_digit(total)


def compute_expression(full_name: str) -> int:
    """
    Calculate Expression/Destiny number from full name.
    
    Method: Sum all letters using Pythagorean values.
    """
    total = 0
    for char in full_name.upper():
        if char.isalpha():
            total += PYTHAGOREAN_VALUES.get(char, 0)
    return reduce_to_single_digit(total)


def compute_soul_urge(full_name: str) -> int:
    """
    Calculate Soul Urge/Heart's Desire number.
    
    Method: Sum vowels only using Pythagorean values.
    """
    total = 0
    for char in full_name.upper():
        if char in VOWELS:
            total += PYTHAGOREAN_VALUES.get(char, 0)
    return reduce_to_single_digit(total)


def compute_personality(full_name: str) -> int:
    """
    Calculate Personality number.
    
    Method: Sum consonants only using Pythagorean values.
    """
    total = 0
    for char in full_name.upper():
        if char.isalpha() and char not in VOWELS:
            total += PYTHAGOREAN_VALUES.get(char, 0)
    return reduce_to_single_digit(total)


def compute_name_breakdown(full_name: str) -> List[Dict[str, Any]]:
    """
    Generate letter-by-letter breakdown showing Pythagorean values.
    
    Returns list of {letter, value} for each letter in the name.
    """
    breakdown = []
    for char in full_name.upper():
        if char.isalpha():
            breakdown.append({
                "letter": char,
                "value": PYTHAGOREAN_VALUES.get(char, 0)
            })
        elif char == ' ':
            breakdown.append({
                "letter": " ",
                "value": None  # Space marker
            })
    return breakdown


# =============================================================================
# LO SHU GRID COMPUTATION (Vedic)
# =============================================================================

def compute_lo_shu(birth_date: datetime) -> Dict[str, Any]:
    """
    Compute Lo Shu Grid from birth date.
    
    The Lo Shu Grid is a 3x3 magic square showing presence/absence of numbers 1-9.
    Numbers are derived from birth date digits (excluding 0).
    
    Standard Lo Shu Grid positions:
    4 | 9 | 2
    3 | 5 | 7
    8 | 1 | 6
    
    Returns:
        {
            "digit_counts": {"1": count, "2": count, ...},
            "grid": [[4 or null, 9 or null, 2 or null], ...],
            "missing_numbers": [list of missing 1-9],
            "present_numbers": [list of present 1-9]
        }
    """
    # Extract all digits from birth date (DD/MM/YYYY format)
    date_str = birth_date.strftime('%d%m%Y')
    
    # Count occurrences of each digit 1-9 (EXCLUDE 0 per requirements)
    digit_counts = {str(i): 0 for i in range(1, 10)}
    for d in date_str:
        if d != '0' and d in digit_counts:
            digit_counts[d] += 1
    
    # Identify missing and present numbers
    missing_numbers = [i for i in range(1, 10) if digit_counts[str(i)] == 0]
    present_numbers = [i for i in range(1, 10) if digit_counts[str(i)] > 0]
    
    # Standard Lo Shu grid template (magic square arrangement)
    lo_shu_template = [[4, 9, 2], [3, 5, 7], [8, 1, 6]]
    
    # Build grid with null for missing numbers
    grid = []
    for row in lo_shu_template:
        grid_row = []
        for num in row:
            if digit_counts[str(num)] > 0:
                grid_row.append(num)
            else:
                grid_row.append(None)  # Missing number
        grid.append(grid_row)
    
    return {
        "digit_counts": digit_counts,
        "grid": grid,
        "missing_numbers": missing_numbers,
        "present_numbers": present_numbers
    }


# =============================================================================
# MISSING NUMBER TENSIONS (Behavioral Mapping)
# =============================================================================

MISSING_NUMBER_TENSIONS = {
    1: {
        "label": "Self-initiation gap",
        "behavioral": "You may wait for external permission to begin",
        "tension": "Starting alone can feel uncomfortable"
    },
    2: {
        "label": "Translation difficulty",
        "behavioral": "People don't always follow what feels obvious to you",
        "tension": "Bridging your inner knowing to others takes extra effort"
    },
    3: {
        "label": "Expression gap",
        "behavioral": "You may hold insight without fully expressing it",
        "tension": "What you know doesn't always make it into words"
    },
    4: {
        "label": "Grounding difficulty",
        "behavioral": "Sustained routines can feel draining rather than stabilizing",
        "tension": "Building lasting structures requires conscious effort"
    },
    5: {
        "label": "Adaptability gap",
        "behavioral": "You may get stuck between options when change is needed",
        "tension": "Flexibility doesn't come automatically"
    },
    6: {
        "label": "Responsibility resistance",
        "behavioral": "Domestic duties may feel like interruptions",
        "tension": "Care-taking energy doesn't flow naturally"
    },
    7: {
        "label": "Internal processing gap",
        "behavioral": "You may act before fully analyzing",
        "tension": "Deep reflection requires deliberate space"
    },
    8: {
        "label": "Material focus gap",
        "behavioral": "Results and outcomes may get less attention",
        "tension": "Power dynamics might not register until too late"
    },
    9: {
        "label": "Completion difficulty",
        "behavioral": "Letting go of what's finished can take longer",
        "tension": "Endings don't feel natural"
    }
}


def get_tensions_from_missing(missing_numbers: List[int]) -> List[Dict[str, str]]:
    """
    Map missing numbers to behavioral tensions.
    
    Returns list of tension objects for display.
    """
    tensions = []
    for num in missing_numbers:
        if num in MISSING_NUMBER_TENSIONS:
            tension = MISSING_NUMBER_TENSIONS[num].copy()
            tension["number"] = num
            tensions.append(tension)
    return tensions


# =============================================================================
# MIRROR SYNTHESIS (Behavioral Pattern Combination)
# =============================================================================

LIFE_PATH_BEHAVIORS = {
    1: "You move quickly on what you see",
    2: "You feel the undercurrents before they surface",
    3: "You process by expressing — silence feels stuck",
    4: "You build steadily and value what lasts",
    5: "You sense when something needs to change",
    6: "You take on responsibility, even uninvited",
    7: "You analyze before committing",
    8: "You track power and results instinctively",
    9: "You see the larger arc others miss",
    11: "You catch signals before they become visible",
    22: "You think in structures that span years",
    33: "You absorb what others carry"
}

EXPRESSION_BEHAVIORS = {
    1: "and present as someone who leads",
    2: "and come across as collaborative",
    3: "and appear naturally expressive",
    4: "and seem methodical to others",
    5: "and appear adaptable, sometimes restless",
    6: "and present as caring and responsible",
    7: "and come across as thoughtful, reserved",
    8: "and appear capable and driven",
    9: "and seem warm and broad-minded",
    11: "and appear inspired, visionary",
    22: "and present as masterful, ambitious",
    33: "and come across as nurturing, wise"
}

SOUL_URGE_BEHAVIORS = {
    1: "You want independence and space to move",
    2: "You want connection and harmony",
    3: "You want expression and lightness",
    4: "You want stability and order",
    5: "You want freedom and new experience",
    6: "You want to nurture and be needed",
    7: "You want understanding and solitude",
    8: "You want achievement and recognition",
    9: "You want meaning and completion",
    11: "You want spiritual insight",
    22: "You want to build something lasting",
    33: "You want to heal and guide"
}


def generate_pattern_synthesis(
    life_path: int,
    expression: Optional[int],
    soul_urge: Optional[int],
    missing_numbers: List[int]
) -> Dict[str, Any]:
    """
    Generate behavioral synthesis combining all pattern elements.
    
    This is the "HOW THIS PATTERN PLAYS OUT" section.
    No mystical language. Grounded behavioral observations.
    """
    lines = []
    
    # Life path behavior
    if life_path in LIFE_PATH_BEHAVIORS:
        line = LIFE_PATH_BEHAVIORS[life_path]
        if expression and expression in EXPRESSION_BEHAVIORS:
            line += f" {EXPRESSION_BEHAVIORS[expression]}"
        lines.append(line)
    
    # Soul urge
    if soul_urge and soul_urge in SOUL_URGE_BEHAVIORS:
        lines.append(SOUL_URGE_BEHAVIORS[soul_urge])
    
    # Missing number consequence
    if missing_numbers:
        missing_labels = []
        for num in missing_numbers[:3]:  # Top 3 missing
            if num in MISSING_NUMBER_TENSIONS:
                missing_labels.append(MISSING_NUMBER_TENSIONS[num]["label"].lower())
        
        if missing_labels:
            missing_str = " and ".join(missing_labels[:2])
            lines.append(f"But {missing_str} don't come naturally")
    
    # Consequence line
    consequence = generate_consequence_line(life_path, missing_numbers)
    if consequence:
        lines.append(consequence)
    
    return {
        "lines": lines,
        "summary": " ".join(lines)
    }


def generate_consequence_line(life_path: int, missing_numbers: List[int]) -> str:
    """Generate the consequence/result line based on pattern."""
    
    # Premium consequence phrasing - specific to pattern combinations
    consequences = {
        # Life Path 1 combinations
        (1, 2): "The result: you move faster than others can follow, and the gap becomes isolating.",
        (1, 4): "The result: strong starts without sustained follow-through—momentum fades when structure is required.",
        (1, 5): "The result: clarity of direction meets inflexibility—when plans fail, recovery is slow.",
        (1, 3): "The result: action without articulation—you do but don't explain.",
        
        # Life Path 2 combinations
        (2, 1): "The result: you sense what's needed but hesitate to initiate—awareness without action.",
        (2, 3): "The result: you feel everything but struggle to voice it—insight stays internal.",
        (2, 4): "The result: intuition without structure—you know but can't systematize.",
        
        # Life Path 3 combinations  
        (3, 7): "The result: words arrive before understanding—expression outruns depth.",
        (3, 4): "The result: creative impulse without sustained execution—ideas scatter.",
        (3, 2): "The result: expression without reception—you speak but don't hear.",
        
        # Life Path 4 combinations
        (4, 5): "The result: solid foundations but rigid response to change—stability becomes stagnation.",
        (4, 3): "The result: structure without spark—systems that work but don't inspire.",
        (4, 2): "The result: method without connection—process that excludes.",
        
        # Life Path 5 combinations
        (5, 4): "The result: constant motion without lasting structure—freedom becomes fragmentation.",
        (5, 2): "The result: restless change meets disconnection—movement without relational anchoring.",
        (5, 3): "The result: experience without expression—life lived but not shared.",
        
        # Life Path 6 combinations
        (6, 1): "The result: responsibility without self-direction—you wait for others to need you.",
        (6, 5): "The result: commitment that becomes confinement—care that can't adapt.",
        (6, 2): "The result: giving without receiving signals—care that misreads the room.",
        
        # Life Path 7 combinations
        (7, 3): "The result: deep knowing without clear expression—insight that can't translate.",
        (7, 1): "The result: understanding without initiative—you analyze but don't act.",
        (7, 2): "The result: solitary wisdom—truth that remains unshared.",
        
        # Life Path 8 combinations
        (8, 2): "The result: drive for results without relational attunement—success that isolates.",
        (8, 6): "The result: power focus without nurturing—achievement that neglects care.",
        (8, 3): "The result: material success without creative expression—wealth without meaning.",
        
        # Life Path 9 combinations
        (9, 4): "The result: broad vision without grounded execution—ideals that don't materialize.",
        (9, 1): "The result: completion without new beginnings—endings that don't lead anywhere.",
        (9, 2): "The result: universal compassion without personal connection—loving humanity but not people.",
        
        # Master Number combinations
        (11, 4): "The result: visionary clarity outpaces practical building—you see far but bridge-building frustrates.",
        (11, 2): "The result: heightened sensitivity without integration—awareness becomes overwhelm.",
        (11, 3): "The result: receiving signals but not transmitting—vision trapped inside.",
        (22, 5): "The result: master building meets inflexibility—grand structures that can't adapt.",
        (22, 3): "The result: vast ambition without voice—plans that can't be communicated.",
        (22, 2): "The result: building empires without bridges—creation that excludes.",
        (33, 1): "The result: deep compassion without self-assertion—healing others while neglecting self.",
        (33, 7): "The result: nurturing presence without analytical boundary—absorbing what should be observed.",
        (33, 3): "The result: feeling everything but expressing little—wisdom that stays silent.",
        (33, 5): "The result: stable healing presence that can't evolve—care that becomes calcified.",
    }
    
    for missing in missing_numbers[:2]:
        key = (life_path if life_path <= 9 else life_path, missing)
        if key in consequences:
            return consequences[key]
    
    # Improved generic fallback - still premium
    if missing_numbers:
        return f"The result: what comes naturally ({life_path}) exceeds what must be built ({missing_numbers[0]})—strength outpaces support."
    
    return "The result: the pattern amplifies what's easy while revealing what requires conscious effort."


# =============================================================================
# PATTERN INTERRUPT GENERATOR (Real-time behavioral layer)
# =============================================================================

# Trigger conditions by Life Path
LIFE_PATH_TRIGGERS: Dict[int, List[str]] = {
    1: [
        "You're about to make a decision and notice others hesitating",
        "Someone asks for your input but you've already moved past the question",
        "A meeting or conversation feels too slow and you want to cut through it",
    ],
    2: [
        "You sense tension in a room but no one has named it yet",
        "Someone's words don't match what you're picking up from them",
        "You're about to accommodate when part of you wants to push back",
    ],
    3: [
        "You're mid-sentence and notice you haven't finished your last thought",
        "An idea excites you and you want to share it immediately",
        "Silence in a conversation makes you want to fill the space",
    ],
    4: [
        "Someone suggests changing a plan you've already committed to",
        "A system you built isn't being followed the way you designed it",
        "You notice something isn't 'right' but others seem unbothered",
    ],
    5: [
        "You feel stuck in a routine that used to work",
        "A commitment starts to feel like a cage",
        "You're considering a change just because the current option feels stale",
    ],
    6: [
        "Someone has a problem and you immediately feel responsible for solving it",
        "You're about to say yes when you haven't been asked",
        "You notice yourself adjusting to make someone else more comfortable",
    ],
    7: [
        "You're asked to decide before you've had time to think",
        "Your gut says something but your mind hasn't caught up",
        "A conversation feels too surface-level to engage with",
    ],
    8: [
        "You're tracking the outcome of a situation before it's finished",
        "Someone's approach feels inefficient and you want to correct it",
        "You notice you're calculating what you'll get from an interaction",
    ],
    9: [
        "You're already seeing the end of something that just started",
        "A situation feels like something you've already resolved internally",
        "You're detaching from something others are still attached to",
    ],
    11: [
        "You're sensing something invisible to others and they're not seeing it",
        "Your intuition is firing but you can't explain why",
        "You feel overwhelmed by signals others seem immune to",
    ],
    22: [
        "The vision in your head doesn't match what's being built",
        "You're frustrated that others can't see what you see",
        "A project feels too small for what you know is possible",
    ],
    33: [
        "You're absorbing someone's emotional state without meaning to",
        "You feel responsible for healing something that isn't yours",
        "Your compassion is extending beyond your capacity",
    ],
}

# Default behaviors by Life Path
LIFE_PATH_DEFAULTS: Dict[int, List[str]] = {
    1: [
        "Move forward without confirming alignment",
        "Assume others will catch up",
        "Skip the translation step because it feels slow",
    ],
    2: [
        "Adjust to what you're sensing rather than naming it",
        "Defer to keep the peace",
        "Absorb the tension rather than addressing it",
    ],
    3: [
        "Express before processing",
        "Fill silence with words",
        "Move to the next idea before landing the current one",
    ],
    4: [
        "Resist the change and defend the existing system",
        "Get frustrated when others don't follow the process",
        "Double down on structure when flexibility is needed",
    ],
    5: [
        "Make a change for the sake of change",
        "Exit before seeing what staying could offer",
        "Mistake restlessness for insight",
    ],
    6: [
        "Take on the problem without being asked",
        "Sacrifice your position to maintain harmony",
        "Over-function so others don't have to step up",
    ],
    7: [
        "Withdraw rather than engage at a shallow level",
        "Delay action until analysis is complete (it never is)",
        "Dismiss what can't be proven internally",
    ],
    8: [
        "Optimize for outcome before understanding the situation",
        "Correct others before building rapport",
        "Measure the value of the moment while still in it",
    ],
    9: [
        "Let go before the process is complete",
        "Detach emotionally while still physically present",
        "Assume completion when others are still invested",
    ],
    11: [
        "Overwhelm yourself by trying to process everything you sense",
        "Expect others to see what you see without explanation",
        "Retreat when the signals become too much",
    ],
    22: [
        "Push the vision harder when others don't understand",
        "Get frustrated with incremental progress",
        "Dismiss practical constraints as small thinking",
    ],
    33: [
        "Absorb what others carry without filtering",
        "Neglect your own needs to attend to others",
        "Lose your boundary in service of healing",
    ],
}

# Interrupt actions by missing number (primary driver)
MISSING_NUMBER_INTERRUPTS: Dict[int, Dict[str, Any]] = {
    1: {
        "actions": [
            "Name what you want before naming what others need",
            "Start one thing without waiting for permission",
            "Say 'I'll take the first step' out loud",
        ],
        "why_works": "You're building the initiation muscle that doesn't come naturally. Starting creates clarity.",
        "watch_for": "Watch for waiting for permission that won't come."
    },
    2: {
        "actions": [
            "Ask: 'Does this land for you?' before moving on",
            "Pause and name what you're sensing: 'I'm noticing...'",
            "Check alignment with one person before proceeding",
        ],
        "why_works": "You're skipping the translation step. Others aren't tracking what's obvious to you.",
        "watch_for": "Watch for assuming others see what feels obvious to you."
    },
    3: {
        "actions": [
            "Say one sentence that captures what you're holding",
            "Finish this phrase out loud: 'What I haven't said is...'",
            "Share the incomplete version rather than waiting for perfection",
        ],
        "why_works": "Expression is how insight becomes real. What stays inside doesn't count.",
        "watch_for": "Watch for holding insight without saying it."
    },
    4: {
        "actions": [
            "Write down one next step before doing anything else",
            "Ask: 'What structure would make this sustainable?'",
            "Commit to finishing before starting something new",
        ],
        "why_works": "You're strong at starting but weak at sustaining. Structure is the bridge.",
        "watch_for": "Watch for starting without a plan to sustain."
    },
    5: {
        "actions": [
            "Name two options and pick one in 10 seconds",
            "Ask: 'What would adapting look like here?'",
            "Make a small change instead of a big one",
        ],
        "why_works": "You get stuck because flexibility doesn't come naturally. Small pivots build the muscle.",
        "watch_for": "Watch for staying stuck when a small pivot would help."
    },
    6: {
        "actions": [
            "Ask: 'Is this mine to carry?' before acting",
            "Offer support without attaching to outcome",
            "Let one thing be imperfect without fixing it",
        ],
        "why_works": "You over-function to feel useful. Restraint is the intervention.",
        "watch_for": "Watch for taking on what isn't yours to carry."
    },
    7: {
        "actions": [
            "Take 30 seconds to sit with the question before responding",
            "Ask yourself: 'What do I actually know here?'",
            "Name the gap between what you sense and what you've proven",
        ],
        "why_works": "You act before processing. The pause creates depth that surface speed misses.",
        "watch_for": "Watch for moving before you've fully understood."
    },
    8: {
        "actions": [
            "Name the concrete outcome you're tracking",
            "Ask: 'What result would make this worth it?'",
            "Notice what you're measuring and why",
        ],
        "why_works": "You avoid the material dimension. Naming the stakes grounds you.",
        "watch_for": "Watch for ignoring results until consequences arrive."
    },
    9: {
        "actions": [
            "Ask: 'What am I ready to release here?'",
            "Name what's ending rather than just feeling it",
            "Let one thing be finished before starting the next",
        ],
        "why_works": "Endings pile up when you don't mark them. Naming creates closure.",
        "watch_for": "Watch for dragging what's finished into what's next."
    },
}

def generate_pattern_interrupt(
    life_path: int,
    expression: Optional[int],
    soul_urge: Optional[int],
    missing_numbers: List[int]
) -> Dict[str, Any]:
    """
    Generate real-time pattern interrupt content.
    
    This is NOT reflection or journaling.
    This is a real-time pattern interrupt layer.
    
    Structure:
    - trigger_conditions: situations where pattern activates
    - default_behavior: what user tends to do automatically
    - interrupt_actions: 2-3 actions under 30 seconds
    - why_this_works: mechanism explanation
    """
    
    # Get triggers based on Life Path
    lp_key = life_path if life_path in LIFE_PATH_TRIGGERS else (life_path % 9 or 9)
    triggers = LIFE_PATH_TRIGGERS.get(lp_key, LIFE_PATH_TRIGGERS[1])
    
    # Get default behaviors based on Life Path
    defaults = LIFE_PATH_DEFAULTS.get(lp_key, LIFE_PATH_DEFAULTS[1])
    
    # Get interrupt actions based on primary missing number
    primary_missing = missing_numbers[0] if missing_numbers else 2  # Default to 2 (translation)
    interrupt_data = MISSING_NUMBER_INTERRUPTS.get(primary_missing, MISSING_NUMBER_INTERRUPTS[2])
    
    # Refine trigger language based on Expression if available
    refined_triggers = triggers.copy()
    if expression:
        # Expression affects how triggers manifest externally
        if expression in [1, 8]:  # Leadership/Power expressions
            refined_triggers[0] = refined_triggers[0].replace("notice others", "see others falling behind")
        elif expression in [2, 6]:  # Collaborative/Caring expressions
            refined_triggers[0] = refined_triggers[0].replace("notice others", "feel others struggling to keep up")
    
    # Refine why_works based on Soul Urge if available
    why_works = interrupt_data["why_works"]
    if soul_urge:
        if soul_urge == 3:  # Soul Urge for expression
            why_works += " Your soul wants to express—give it an outlet."
        elif soul_urge == 7:  # Soul Urge for understanding
            why_works += " Your soul wants depth—the pause honors that."
        elif soul_urge == 1:  # Soul Urge for independence
            why_works += " Your soul wants to lead—this lets you lead yourself first."
    
    return {
        "trigger_conditions": refined_triggers,
        "default_behavior": defaults[:3],  # Max 3
        "interrupt_actions": interrupt_data["actions"],
        "why_this_works": why_works,
        "primary_driver": f"Missing {primary_missing}",
        "mechanism": get_interrupt_mechanism(primary_missing),
    }


def get_interrupt_mechanism(missing_number: int) -> str:
    """Get the core mechanism being addressed by the interrupt."""
    mechanisms = {
        1: "self-initiation",
        2: "alignment / translation",
        3: "expression",
        4: "structure / sustainability",
        5: "adaptability / movement",
        6: "responsibility boundaries",
        7: "reflection / processing",
        8: "material grounding",
        9: "completion / release",
    }
    return mechanisms.get(missing_number, "pattern awareness")


def generate_daily_watch_for(missing_numbers: List[int]) -> str:
    """
    Generate a single short 'watch for' cue for daily use.
    
    Under 14 words. No mystical language. Immediately usable.
    Derived from the interrupt logic.
    """
    if not missing_numbers:
        return "Watch for patterns running without your awareness."
    
    primary_missing = missing_numbers[0]
    interrupt_data = MISSING_NUMBER_INTERRUPTS.get(primary_missing, MISSING_NUMBER_INTERRUPTS[2])
    return interrupt_data.get("watch_for", "Watch for the pattern running on autopilot.")


# =============================================================================
# MAIN COMPUTE FUNCTION
# =============================================================================

def compute_numerology_deterministic(
    birth_date: datetime,
    full_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Compute complete deterministic numerology profile.
    
    This is the canonical compute function that returns:
    - Input data
    - Pythagorean calculations (name-based)
    - Lo Shu grid (date-based)
    
    NO LLM. NO interpretation. Pure computation.
    
    Args:
        birth_date: User's birth date
        full_name: User's full birth name (optional)
    
    Returns:
        Complete deterministic numerology payload
    """
    
    # === PYTHAGOREAN (Name-based) ===
    life_path = compute_life_path(birth_date)
    
    pythagorean = {
        "life_path": life_path,
        "expression": None,
        "soul_urge": None,
        "personality": None,
        "name_breakdown": None
    }
    
    if full_name and full_name.strip():
        pythagorean["expression"] = compute_expression(full_name)
        pythagorean["soul_urge"] = compute_soul_urge(full_name)
        pythagorean["personality"] = compute_personality(full_name)
        pythagorean["name_breakdown"] = compute_name_breakdown(full_name)
    
    # === LO SHU (Date-based) ===
    lo_shu = compute_lo_shu(birth_date)
    
    # === TENSIONS (Behavioral mapping) ===
    tensions = get_tensions_from_missing(lo_shu["missing_numbers"])
    
    # === PATTERN SYNTHESIS (Behavioral interpretation) ===
    synthesis = generate_pattern_synthesis(
        life_path=life_path,
        expression=pythagorean["expression"],
        soul_urge=pythagorean["soul_urge"],
        missing_numbers=lo_shu["missing_numbers"]
    )
    
    # === PATTERN INTERRUPT (Real-time behavioral layer) ===
    pattern_interrupt = generate_pattern_interrupt(
        life_path=life_path,
        expression=pythagorean["expression"],
        soul_urge=pythagorean["soul_urge"],
        missing_numbers=lo_shu["missing_numbers"]
    )
    
    # === DAILY WATCH FOR (Lightweight bridge cue) ===
    daily_watch_for = generate_daily_watch_for(lo_shu["missing_numbers"])
    
    return {
        "input": {
            "full_name": full_name,
            "birth_date": birth_date.strftime('%Y-%m-%d')
        },
        "pythagorean": pythagorean,
        "lo_shu": lo_shu,
        "tensions": tensions,
        "synthesis": synthesis,
        "pattern_interrupt": pattern_interrupt,
        "daily_watch_for": daily_watch_for,
        "computation_version": "mirror-numerology-v2",
        "computed_at": datetime.now().isoformat()
    }
