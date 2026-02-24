"""
Enneagram Assessment V3 - Adaptive Assessment Engine
=====================================================

A 90-question adaptive Enneagram assessment with 4 phases:
1. TRIAD LOCK (20 questions) -> Fear/Shame/Anger
2. CORE TYPE (12-15 questions) -> Specific type within triad
3. WING & SUBTYPE (22 questions) -> Wing and instinctual stacking
4. VALIDATION (0-15 questions) -> Mistyping checks

Target: 85%+ accuracy, 15-25 min completion time
Result format: "4w5 sx/sp" (type + wing + subtype)
"""

import uuid
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTS
# =============================================================================

SESSION_TTL_SECONDS = 2 * 60 * 60  # 2 hours

# Triad lock thresholds
TRIAD_LOCK_THRESHOLD = 45  # Lock if top triad >= 45%
TRIAD_LOCK_THRESHOLD_STRESSED = 60  # Raised threshold when stress detected
TRIAD_CONFIDENCE_MIN = 40  # If confidence < 40%, add clarifying questions
TRIAD_MIN_QUESTIONS = 15  # Minimum questions before allowing early lock

# Core type thresholds (Phase 2)
CORE_TYPE_LOCK_THRESHOLD = 50  # Lock if top type >= 50%
CORE_TYPE_CONFIDENCE_THRESHOLD = 70  # High confidence threshold for early lock
CORE_TYPE_MIN_QUESTIONS = 8  # Minimum questions before allowing early type lock

# Stress detection thresholds (Phase 4)
STRESS_SURVIVAL_THRESHOLD = 4  # If survival mode score >= 4, user may be in stress
STRESS_INDICATOR_THRESHOLD = 4  # If stress indicator >= 4, specific stress pattern detected
VALIDATION_CONFIDENCE_BOOST = 10  # Confidence boost if user validates type match
VALIDATION_CONFIDENCE_PENALTY = -15  # Confidence penalty if user rejects calculated type

# =============================================================================
# ENUMS
# =============================================================================

class Phase(str, Enum):
    TRIAD = "triad"
    CORE = "core"
    WING_SUBTYPE = "wing_subtype"
    VALIDATION = "validation"
    DONE = "done"

class Triad(str, Enum):
    FEAR = "fear"     # Types 5, 6, 7
    SHAME = "shame"   # Types 2, 3, 4
    ANGER = "anger"   # Types 8, 9, 1

class QuestionType(str, Enum):
    LIKERT = "likert"
    SINGLE = "single"
    RANKING = "ranking"

# Triad to types mapping
TRIAD_TYPES = {
    Triad.FEAR: [5, 6, 7],
    Triad.SHAME: [2, 3, 4],
    Triad.ANGER: [8, 9, 1],
}

# Type to triad mapping
TYPE_TO_TRIAD = {
    5: Triad.FEAR, 6: Triad.FEAR, 7: Triad.FEAR,
    2: Triad.SHAME, 3: Triad.SHAME, 4: Triad.SHAME,
    8: Triad.ANGER, 9: Triad.ANGER, 1: Triad.ANGER,
}

# Wing adjacencies
WING_ADJACENTS = {
    1: (9, 2), 2: (1, 3), 3: (2, 4), 4: (3, 5),
    5: (4, 6), 6: (5, 7), 7: (6, 8), 8: (7, 9), 9: (8, 1),
}

# Common mistypings to validate
MISTYPE_PAIRS = [
    (5, 9), (6, 2), (7, 3), (4, 9), (1, 6), (8, 1)
]

# =============================================================================
# PHASE 1 QUESTION BANK (TRIAD LOCK - 20 questions)
# =============================================================================

PHASE1_QUESTIONS = [
    # Fear Triad (F1-F7)
    {
        "id": "F1",
        "phase": 1,
        "triad": "fear",
        "type": "single",
        "question": "At work, when facing a project with many unknowns, your first instinct is to:",
        "options": [
            {"value": 5, "text": "Research extensively before acting—you need to understand before proceeding"},
            {"value": 4, "text": "Create a detailed plan with contingencies for various scenarios"},
            {"value": 3, "text": "Dive in and figure it out as you go—you trust your ability to adapt"},
            {"value": 2, "text": "Focus on what excites you about the project and build momentum"},
            {"value": 1, "text": "Wait for clearer direction from leadership"},
        ],
        "weight": 1.0,
        "reverse_scored": False,
    },
    {
        "id": "F2",
        "phase": 1,
        "triad": "fear",
        "type": "likert",
        "question": "I often find myself anticipating what could go wrong before it happens.",
        "options": [
            {"value": 5, "text": "Strongly agree—this is my default mode"},
            {"value": 4, "text": "Agree—I do this frequently"},
            {"value": 3, "text": "Neutral—depends on the situation"},
            {"value": 2, "text": "Disagree—I tend to be optimistic"},
            {"value": 1, "text": "Strongly disagree—I live in the present"},
        ],
        "weight": 1.0,
        "reverse_scored": False,
    },
    {
        "id": "F3",
        "phase": 1,
        "triad": "fear",
        "type": "single",
        "question": "When I'm stressed or anxious, I tend to:",
        "options": [
            {"value": 5, "text": "Withdraw and research/analyze to understand the problem"},
            {"value": 4, "text": "Seek trusted opinions and gather multiple perspectives"},
            {"value": 3, "text": "Look for distractions and positive reframes"},
            {"value": 2, "text": "Focus on practical action steps"},
            {"value": 1, "text": "Reach out for emotional support"},
        ],
        "weight": 1.0,
        "reverse_scored": False,
    },
    {
        "id": "F4",
        "phase": 1,
        "triad": "fear",
        "type": "single",
        "question": "My mind often feels:",
        "options": [
            {"value": 5, "text": "Like a constantly running analysis machine—I can't easily turn it off"},
            {"value": 4, "text": "Like it's scanning for threats and possibilities simultaneously"},
            {"value": 3, "text": "Like it jumps between exciting ideas and future possibilities"},
            {"value": 2, "text": "Focused on relationships and how others perceive me"},
            {"value": 1, "text": "Focused on what's happening in my body and immediate environment"},
        ],
        "weight": 1.0,
        "reverse_scored": False,
    },
    {
        "id": "F5",
        "phase": 1,
        "triad": "fear",
        "type": "single",
        "question": "When making significant decisions, I typically:",
        "options": [
            {"value": 5, "text": "Need extensive time to gather information and analyze"},
            {"value": 4, "text": "Need to consult trusted sources and feel certain"},
            {"value": 3, "text": "Make them quickly to keep options open and avoid missing out"},
            {"value": 2, "text": "Consider how the decision affects my image/relationships"},
            {"value": 1, "text": "Go with my gut instinct"},
        ],
        "weight": 1.0,
        "reverse_scored": False,
    },
    {
        "id": "F6",
        "phase": 1,
        "triad": "fear",
        "type": "single",
        "question": "Being seen as incompetent or uninformed is:",
        "options": [
            {"value": 5, "text": "One of my deepest fears—I must be competent"},
            {"value": 4, "text": "A significant concern—I need to be prepared"},
            {"value": 3, "text": "Uncomfortable but I'd rather be seen as incompetent than trapped"},
            {"value": 2, "text": "Less important than being seen as unlovable or unsuccessful"},
            {"value": 1, "text": "Not my primary concern"},
        ],
        "weight": 1.0,
        "reverse_scored": False,
    },
    {
        "id": "F7",
        "phase": 1,
        "triad": "fear",
        "type": "likert",
        "question": "I rarely experience anxiety about future events.",
        "options": [
            {"value": 5, "text": "Strongly disagree—I'm often anxious about the future"},
            {"value": 4, "text": "Disagree—I worry more than I'd like"},
            {"value": 3, "text": "Neutral—sometimes yes, sometimes no"},
            {"value": 2, "text": "Agree—I tend to stay present"},
            {"value": 1, "text": "Strongly agree—the future doesn't worry me"},
        ],
        "weight": 1.0,
        "reverse_scored": True,  # REVERSE SCORED
    },
    
    # Shame Triad (S1-S7)
    {
        "id": "S1",
        "phase": 1,
        "triad": "shame",
        "type": "single",
        "question": "When I think about 'who I am,' I most often:",
        "options": [
            {"value": 5, "text": "Feel like I'm different from others—searching for my authentic self"},
            {"value": 4, "text": "Think about my achievements and how I'm perceived"},
            {"value": 3, "text": "Consider my relationships and who needs me"},
            {"value": 2, "text": "Focus on my principles and values"},
            {"value": 1, "text": "Don't think about it much—I just am"},
        ],
        "weight": 1.0,
        "reverse_scored": False,
    },
    {
        "id": "S2",
        "phase": 1,
        "triad": "shame",
        "type": "single",
        "question": "When I fail at something publicly, I feel:",
        "options": [
            {"value": 5, "text": "Deep shame—it affects my sense of worth significantly"},
            {"value": 4, "text": "Exposed and misunderstood—like no one sees the real me"},
            {"value": 3, "text": "Worried about disappointing others and losing connection"},
            {"value": 2, "text": "Motivated to fix it and do better"},
            {"value": 1, "text": "Annoyed but move on quickly"},
        ],
        "weight": 1.0,
        "reverse_scored": False,
    },
    {
        "id": "S3",
        "phase": 1,
        "triad": "shame",
        "type": "likert",
        "question": "I often adjust how I present myself based on who I'm with.",
        "options": [
            {"value": 5, "text": "Strongly agree—I adapt to be effective and successful"},
            {"value": 4, "text": "Agree—I want to be helpful and needed in each situation"},
            {"value": 3, "text": "Somewhat—I want to be seen as authentic but also understood"},
            {"value": 2, "text": "Rarely—I present consistently"},
            {"value": 1, "text": "Never—I am who I am"},
        ],
        "weight": 1.0,
        "reverse_scored": False,
    },
    {
        "id": "S4",
        "phase": 1,
        "triad": "shame",
        "type": "single",
        "question": "My emotional experience tends to be:",
        "options": [
            {"value": 5, "text": "Intense and complex—I feel things deeply"},
            {"value": 4, "text": "Attuned to others—I feel what they're feeling"},
            {"value": 3, "text": "Focused and efficient—I process emotions quickly"},
            {"value": 2, "text": "Steady and contained"},
            {"value": 1, "text": "Calm—I don't experience strong emotions often"},
        ],
        "weight": 1.0,
        "reverse_scored": False,
    },
    {
        "id": "S5",
        "phase": 1,
        "triad": "shame",
        "type": "single",
        "question": "The idea of living an ordinary, unremarkable life:",
        "options": [
            {"value": 5, "text": "Feels like a tragedy—I need to be uniquely myself"},
            {"value": 4, "text": "Feels like failure—I need to achieve and be recognized"},
            {"value": 3, "text": "Feels empty—I need to matter to others"},
            {"value": 2, "text": "Is fine as long as I'm doing what's right"},
            {"value": 1, "text": "Sounds peaceful and appealing"},
        ],
        "weight": 1.0,
        "reverse_scored": False,
    },
    {
        "id": "S6",
        "phase": 1,
        "triad": "shame",
        "type": "likert",
        "question": "I need attention and recognition from others.",
        "options": [
            {"value": 5, "text": "Strongly agree—I need to be seen as successful"},
            {"value": 4, "text": "Agree—I need to be seen and understood for who I am"},
            {"value": 3, "text": "Agree—I need to feel appreciated and valued"},
            {"value": 2, "text": "Neutral—it's nice but not essential"},
            {"value": 1, "text": "Disagree—I prefer to avoid attention"},
        ],
        "weight": 1.0,
        "reverse_scored": False,
    },
    {
        "id": "S7",
        "phase": 1,
        "triad": "shame",
        "type": "single",
        "question": "As a child, I was often described as:",
        "options": [
            {"value": 5, "text": "Sensitive, creative, different, or 'marching to my own drum'"},
            {"value": 4, "text": "High-achieving, impressive, or 'a natural leader'"},
            {"value": 3, "text": "Helpful, sweet, or 'such a good helper'"},
            {"value": 2, "text": "Responsible, serious, or 'mature for my age'"},
            {"value": 1, "text": "Easygoing, agreeable, or 'no trouble at all'"},
        ],
        "weight": 1.0,
        "reverse_scored": False,
    },
    
    # Anger Triad (A1-A6)
    {
        "id": "A1",
        "phase": 1,
        "triad": "anger",
        "type": "single",
        "question": "I am aware of feeling angry:",
        "options": [
            {"value": 5, "text": "Frequently—I express it directly"},
            {"value": 4, "text": "Often—but I try to contain it as inappropriate"},
            {"value": 3, "text": "Rarely—I tend to go numb or avoid conflict"},
            {"value": 2, "text": "Only when boundaries are seriously violated"},
            {"value": 1, "text": "Almost never—anger isn't my primary emotion"},
        ],
        "weight": 1.0,
        "reverse_scored": False,
    },
    {
        "id": "A2",
        "phase": 1,
        "triad": "anger",
        "type": "single",
        "question": "In group situations, I prefer to:",
        "options": [
            {"value": 5, "text": "Be in charge and direct the action"},
            {"value": 4, "text": "Ensure things are done correctly and fairly"},
            {"value": 3, "text": "Go with the flow and avoid rocking the boat"},
            {"value": 2, "text": "Contribute my expertise"},
            {"value": 1, "text": "Observe and participate as needed"},
        ],
        "weight": 1.0,
        "reverse_scored": False,
    },
    {
        "id": "A3",
        "phase": 1,
        "triad": "anger",
        "type": "single",
        "question": "When people don't follow agreed-upon rules:",
        "options": [
            {"value": 5, "text": "I feel angry and want to correct them"},
            {"value": 4, "text": "I feel contempt and may confront them"},
            {"value": 3, "text": "I feel annoyed but usually let it go"},
            {"value": 2, "text": "I analyze why they're not following the rules"},
            {"value": 1, "text": "I don't pay much attention to rules"},
        ],
        "weight": 1.0,
        "reverse_scored": False,
    },
    {
        "id": "A4",
        "phase": 1,
        "triad": "anger",
        "type": "likert",
        "question": "I have a strong inner critic that judges my actions.",
        "options": [
            {"value": 5, "text": "Strongly agree—I'm constantly evaluating myself"},
            {"value": 4, "text": "Somewhat—but I mostly ignore it"},
            {"value": 3, "text": "Not really—I tend to avoid self-judgment"},
            {"value": 2, "text": "I critique my competence, not my morality"},
            {"value": 1, "text": "I don't have a strong inner critic"},
        ],
        "weight": 1.0,
        "reverse_scored": False,
    },
    {
        "id": "A5",
        "phase": 1,
        "triad": "anger",
        "type": "single",
        "question": "When someone challenges me directly:",
        "options": [
            {"value": 5, "text": "I meet the challenge head-on"},
            {"value": 4, "text": "I defend my position with logic and principles"},
            {"value": 3, "text": "I try to find common ground or withdraw"},
            {"value": 2, "text": "I analyze their motivations"},
            {"value": 1, "text": "I worry about the relationship"},
        ],
        "weight": 1.0,
        "reverse_scored": False,
    },
    {
        "id": "A6",
        "phase": 1,
        "triad": "anger",
        "type": "likert",
        "question": "I am generally aware of my physical sensations and gut feelings.",
        "options": [
            {"value": 5, "text": "Strongly agree—I live in my body"},
            {"value": 4, "text": "Agree—I'm generally grounded"},
            {"value": 3, "text": "Somewhat—but I'm often tense"},
            {"value": 2, "text": "Not really—I'm more in my head"},
            {"value": 1, "text": "Rarely—I ignore physical sensations"},
        ],
        "weight": 1.0,
        "reverse_scored": False,
    },
]

# =============================================================================
# STRESS/STATE DETECTION QUESTIONS (inserted in Phase 1)
# =============================================================================
# These questions detect if user is in stress/survival mode, which may distort results.
# Inserted after question 5 in the interleaved order to catch early distortion.

STRESS_DETECTION_QUESTIONS = [
    {
        "id": "STRESS-1",
        "phase": 1,
        "type": "stress_detection",
        "stress_type": "survival",
        "question": "I feel like I'm operating in survival or crisis mode right now.",
        "options": [
            {"value": 5, "text": "Strongly agree—I'm in crisis/survival mode"},
            {"value": 4, "text": "Agree—I'm definitely stressed"},
            {"value": 3, "text": "Somewhat—a bit more stressed than usual"},
            {"value": 2, "text": "Disagree—I'm managing okay"},
            {"value": 1, "text": "Strongly disagree—I feel centered"},
        ],
        "weight": 1.0,
    },
    {
        "id": "STRESS-7",
        "phase": 1,
        "type": "stress_detection",
        "stress_type": "type_7_indicator",
        "target_triad": "fear",
        "question": "I'm seeking distractions and exciting possibilities to avoid pain or discomfort.",
        "options": [
            {"value": 5, "text": "Strongly agree—I'm avoiding through distraction"},
            {"value": 4, "text": "Agree—I notice this pattern"},
            {"value": 3, "text": "Somewhat—occasionally"},
            {"value": 2, "text": "Disagree—I face things directly"},
            {"value": 1, "text": "Strongly disagree—not at all"},
        ],
        "weight": 1.0,
    },
    {
        "id": "STRESS-5",
        "phase": 1,
        "type": "stress_detection",
        "stress_type": "type_5_indicator",
        "target_triad": "fear",
        "question": "I'm withdrawing to analyze and conserve my energy.",
        "options": [
            {"value": 5, "text": "Strongly agree—I'm retreating to think"},
            {"value": 4, "text": "Agree—I'm pulling back"},
            {"value": 3, "text": "Somewhat—more than usual"},
            {"value": 2, "text": "Disagree—I'm staying engaged"},
            {"value": 1, "text": "Strongly disagree—I'm very active"},
        ],
        "weight": 1.0,
    },
    {
        "id": "STRESS-1T",
        "phase": 1,
        "type": "stress_detection",
        "stress_type": "type_1_indicator",
        "target_triad": "anger",
        "question": "I'm pushing myself hard to maintain control and order.",
        "options": [
            {"value": 5, "text": "Strongly agree—I'm rigidly controlling everything"},
            {"value": 4, "text": "Agree—I'm more controlling than usual"},
            {"value": 3, "text": "Somewhat—a bit more structured"},
            {"value": 2, "text": "Disagree—I'm fairly relaxed"},
            {"value": 1, "text": "Strongly disagree—I'm going with the flow"},
        ],
        "weight": 1.0,
    },
]

# Stress type to triad mapping (for conflict detection)
STRESS_TYPE_TRIAD_MAP = {
    "type_7_indicator": "fear",
    "type_5_indicator": "fear",
    "type_1_indicator": "anger",
}

# =============================================================================
# PHASE 4: VALIDATION QUESTIONS
# =============================================================================
# Presented after Phase 3, before final results. User ranks type descriptions
# to validate or adjust the calculated result.

TYPE_DESCRIPTIONS = {
    1: {
        "name": "The Reformer",
        "description": "Principled, purposeful, self-controlled. You have a strong sense of right and wrong, often feeling a responsibility to improve things. Your inner critic is persistent, driving you toward integrity and excellence.",
    },
    2: {
        "name": "The Helper",
        "description": "Caring, interpersonal, generous. You feel most alive when connecting with and helping others. You intuitively sense what people need and often put others' needs before your own.",
    },
    3: {
        "name": "The Achiever",
        "description": "Adaptive, driven, image-conscious. You're motivated by success and recognition, naturally adapting to achieve goals. You measure your worth through accomplishments and how others perceive you.",
    },
    4: {
        "name": "The Individualist",
        "description": "Expressive, dramatic, self-absorbed. You experience emotions intensely and seek authentic self-expression. You often feel fundamentally different from others and search for your true identity.",
    },
    5: {
        "name": "The Investigator",
        "description": "Perceptive, innovative, isolated. You approach life through observation and analysis, valuing knowledge and competence. You conserve energy and maintain privacy to protect your inner resources.",
    },
    6: {
        "name": "The Loyalist",
        "description": "Committed, security-oriented, anxious. You seek guidance and certainty in an uncertain world. Your loyalty runs deep once committed, though you may doubt and test those you trust.",
    },
    7: {
        "name": "The Enthusiast",
        "description": "Spontaneous, versatile, scattered. You pursue pleasure and possibilities to avoid pain and limitation. Your mind races ahead to exciting futures, and you resist being pinned down.",
    },
    8: {
        "name": "The Challenger",
        "description": "Self-confident, decisive, confrontational. You assert control over your environment and protect yourself from vulnerability. You respect strength and directness in yourself and others.",
    },
    9: {
        "name": "The Peacemaker",
        "description": "Receptive, reassuring, complacent. You seek inner and outer peace, often merging with others' agendas to avoid conflict. You may struggle to know your own priorities and assert your presence.",
    },
}

PHASE4_VALIDATION_QUESTIONS = [
    {
        "id": "VAL-1",
        "phase": 4,
        "type": "validation_ranking",
        "question": "Which description feels most like your CORE self—not how you act under stress, but who you've been since childhood?",
        "instruction": "Review these descriptions and select the one that resonates most deeply with your fundamental nature.",
    },
    {
        "id": "VAL-2",
        "phase": 4,
        "type": "validation_confirm",
        "question": "Looking at your result, does this feel accurate to your core self?",
        "options": [
            {"value": 5, "text": "Yes, this is definitely me"},
            {"value": 4, "text": "Mostly yes, with some reservations"},
            {"value": 3, "text": "Unsure—could be me or not"},
            {"value": 2, "text": "Mostly no—something feels off"},
            {"value": 1, "text": "No, this doesn't feel like me at all"},
        ],
    },
]

# =============================================================================
# PHASE 2 QUESTION BANK (CORE TYPE - Fear Triad Only for MVP)
# =============================================================================
# After triad is locked, these questions differentiate between types within
# the locked triad. Currently only Fear triad (5, 6, 7) is implemented.

PHASE2_FEAR_QUESTIONS = [
    # Type 5 - The Investigator (F5-1 to F5-4)
    {
        "id": "F5-1",
        "phase": 2,
        "triad": "fear",
        "target_type": 5,
        "type": "likert",
        "question": "I need extensive time alone to recharge and process my thoughts.",
        "options": [
            {"value": 5, "text": "Strongly agree—solitude is essential for me"},
            {"value": 4, "text": "Agree—I need significant alone time"},
            {"value": 3, "text": "Neutral—I'm flexible about it"},
            {"value": 2, "text": "Disagree—I prefer being with others"},
            {"value": 1, "text": "Strongly disagree—I rarely need alone time"},
        ],
        "weight": 1.0,
    },
    {
        "id": "F5-2",
        "phase": 2,
        "triad": "fear",
        "target_type": 5,
        "type": "likert",
        "question": "I prefer observing before participating in group situations.",
        "options": [
            {"value": 5, "text": "Strongly agree—I always observe first"},
            {"value": 4, "text": "Agree—I usually hang back initially"},
            {"value": 3, "text": "Neutral—depends on the situation"},
            {"value": 2, "text": "Disagree—I tend to jump in"},
            {"value": 1, "text": "Strongly disagree—I dive right in"},
        ],
        "weight": 1.0,
    },
    {
        "id": "F5-3",
        "phase": 2,
        "triad": "fear",
        "target_type": 5,
        "type": "likert",
        "question": "I feel drained when people demand too much of my energy or attention.",
        "options": [
            {"value": 5, "text": "Strongly agree—demands exhaust me quickly"},
            {"value": 4, "text": "Agree—I'm protective of my energy"},
            {"value": 3, "text": "Neutral—I manage it okay"},
            {"value": 2, "text": "Disagree—I have energy to spare"},
            {"value": 1, "text": "Strongly disagree—I thrive on engagement"},
        ],
        "weight": 1.0,
    },
    {
        "id": "F5-4",
        "phase": 2,
        "triad": "fear",
        "target_type": 5,
        "type": "likert",
        "question": "I collect knowledge and resources to feel prepared and self-sufficient.",
        "options": [
            {"value": 5, "text": "Strongly agree—I stockpile knowledge"},
            {"value": 4, "text": "Agree—I like feeling prepared"},
            {"value": 3, "text": "Neutral—I'm somewhat this way"},
            {"value": 2, "text": "Disagree—I wing it more often"},
            {"value": 1, "text": "Strongly disagree—I prefer to improvise"},
        ],
        "weight": 1.0,
    },
    
    # Type 6 - The Loyalist (F6-1 to F6-4)
    {
        "id": "F6-1",
        "phase": 2,
        "triad": "fear",
        "target_type": 6,
        "type": "likert",
        "question": "I naturally scan for what could go wrong in any situation.",
        "options": [
            {"value": 5, "text": "Strongly agree—I'm always scanning for risks"},
            {"value": 4, "text": "Agree—I notice potential problems easily"},
            {"value": 3, "text": "Neutral—sometimes I do"},
            {"value": 2, "text": "Disagree—I'm usually optimistic"},
            {"value": 1, "text": "Strongly disagree—I rarely think about risks"},
        ],
        "weight": 1.0,
    },
    {
        "id": "F6-2",
        "phase": 2,
        "triad": "fear",
        "target_type": 6,
        "type": "likert",
        "question": "I value trusted authorities and clear guidelines to feel secure.",
        "options": [
            {"value": 5, "text": "Strongly agree—I need structure and guidance"},
            {"value": 4, "text": "Agree—clear guidelines help me"},
            {"value": 3, "text": "Neutral—I can go either way"},
            {"value": 2, "text": "Disagree—I prefer making my own rules"},
            {"value": 1, "text": "Strongly disagree—I resist authority"},
        ],
        "weight": 1.0,
    },
    {
        "id": "F6-3",
        "phase": 2,
        "triad": "fear",
        "target_type": 6,
        "type": "likert",
        "question": "My loyalty runs deep once I've committed to someone or something.",
        "options": [
            {"value": 5, "text": "Strongly agree—I'm fiercely loyal"},
            {"value": 4, "text": "Agree—I'm very committed once in"},
            {"value": 3, "text": "Neutral—I'm moderately loyal"},
            {"value": 2, "text": "Disagree—I keep my options open"},
            {"value": 1, "text": "Strongly disagree—I stay flexible"},
        ],
        "weight": 1.0,
    },
    {
        "id": "F6-4",
        "phase": 2,
        "triad": "fear",
        "target_type": 6,
        "type": "likert",
        "question": "I can swing between seeking support and pushing against authority.",
        "options": [
            {"value": 5, "text": "Strongly agree—I'm often torn between the two"},
            {"value": 4, "text": "Agree—I experience this ambivalence"},
            {"value": 3, "text": "Neutral—occasionally"},
            {"value": 2, "text": "Disagree—I'm pretty consistent"},
            {"value": 1, "text": "Strongly disagree—I don't relate to this"},
        ],
        "weight": 1.0,
    },
    
    # Type 7 - The Enthusiast (F7-1 to F7-4)
    {
        "id": "F7-1",
        "phase": 2,
        "triad": "fear",
        "target_type": 7,
        "type": "likert",
        "question": "I keep my options open to avoid feeling trapped or limited.",
        "options": [
            {"value": 5, "text": "Strongly agree—commitment feels constraining"},
            {"value": 4, "text": "Agree—I like having options"},
            {"value": 3, "text": "Neutral—depends on the situation"},
            {"value": 2, "text": "Disagree—I'm comfortable committing"},
            {"value": 1, "text": "Strongly disagree—I prefer certainty"},
        ],
        "weight": 1.0,
    },
    {
        "id": "F7-2",
        "phase": 2,
        "triad": "fear",
        "target_type": 7,
        "type": "likert",
        "question": "I naturally reframe negatives into positives or opportunities.",
        "options": [
            {"value": 5, "text": "Strongly agree—I'm a natural optimist"},
            {"value": 4, "text": "Agree—I look for silver linings"},
            {"value": 3, "text": "Neutral—sometimes I do"},
            {"value": 2, "text": "Disagree—I tend to be realistic"},
            {"value": 1, "text": "Strongly disagree—I focus on problems"},
        ],
        "weight": 1.0,
    },
    {
        "id": "F7-3",
        "phase": 2,
        "triad": "fear",
        "target_type": 7,
        "type": "likert",
        "question": "I seek variety and novelty to stay engaged and excited.",
        "options": [
            {"value": 5, "text": "Strongly agree—I need constant stimulation"},
            {"value": 4, "text": "Agree—variety keeps me interested"},
            {"value": 3, "text": "Neutral—I'm okay with some routine"},
            {"value": 2, "text": "Disagree—I like consistency"},
            {"value": 1, "text": "Strongly disagree—I prefer routine"},
        ],
        "weight": 1.0,
    },
    {
        "id": "F7-4",
        "phase": 2,
        "triad": "fear",
        "target_type": 7,
        "type": "likert",
        "question": "FOMO drives me to pack my schedule with experiences.",
        "options": [
            {"value": 5, "text": "Strongly agree—I hate missing out"},
            {"value": 4, "text": "Agree—I try to fit in a lot"},
            {"value": 3, "text": "Neutral—sometimes"},
            {"value": 2, "text": "Disagree—I'm selective about activities"},
            {"value": 1, "text": "Strongly disagree—I prefer a calm schedule"},
        ],
        "weight": 1.0,
    },
    
    # Fear Triad Differentiation (FD-1 to FD-4)
    # These are special differential questions - selecting an option strongly
    # boosts that type and suppresses the others
    {
        "id": "FD-1",
        "phase": 2,
        "triad": "fear",
        "type": "differential",
        "question": "When stressed, I tend to:",
        "options": [
            {"value": 5, "type_boost": 5, "text": "Withdraw into my inner world to think and analyze"},
            {"value": 6, "type_boost": 6, "text": "Seek reassurance from trusted people or systems"},
            {"value": 7, "type_boost": 7, "text": "Pursue distractions and plan exciting escapes"},
        ],
        "weight": 2.0,  # Higher weight for differential questions
    },
    {
        "id": "FD-2",
        "phase": 2,
        "triad": "fear",
        "type": "differential",
        "question": "My core fear is being:",
        "options": [
            {"value": 5, "type_boost": 5, "text": "Incompetent, useless, or incapable"},
            {"value": 6, "type_boost": 6, "text": "Unsupported, without guidance, or abandoned"},
            {"value": 7, "type_boost": 7, "text": "Deprived, trapped in pain, or limited"},
        ],
        "weight": 2.0,
    },
    {
        "id": "FD-3",
        "phase": 2,
        "triad": "fear",
        "type": "differential",
        "question": "Under pressure, I become:",
        "options": [
            {"value": 5, "type_boost": 5, "text": "Hyper-analytical, detached, and withdrawn"},
            {"value": 6, "type_boost": 6, "text": "Reactive, doubting, and seeking certainty"},
            {"value": 7, "type_boost": 7, "text": "Impulsive, scattered, and escapist"},
        ],
        "weight": 2.0,
    },
    {
        "id": "FD-4",
        "phase": 2,
        "triad": "fear",
        "type": "differential",
        "question": "I recharge by:",
        "options": [
            {"value": 5, "type_boost": 5, "text": "Being alone with my projects and interests"},
            {"value": 6, "type_boost": 6, "text": "Being with trusted people who make me feel secure"},
            {"value": 7, "type_boost": 7, "text": "Planning exciting future possibilities"},
        ],
        "weight": 2.0,
    },
]

# =============================================================================
# PHASE 2: SHAME TRIAD (Types 2, 3, 4)
# =============================================================================

PHASE2_SHAME_QUESTIONS = [
    # Type 2 - The Helper (S2-1 to S2-4)
    {
        "id": "S2-1",
        "phase": 2,
        "triad": "shame",
        "target_type": 2,
        "type": "likert",
        "question": "I intuitively sense what others need and feel compelled to help.",
        "options": [
            {"value": 5, "text": "Strongly agree—I always know what people need"},
            {"value": 4, "text": "Agree—I'm very attuned to others' needs"},
            {"value": 3, "text": "Neutral—sometimes I pick up on needs"},
            {"value": 2, "text": "Disagree—I focus more on my own needs"},
            {"value": 1, "text": "Strongly disagree—I don't notice others' needs much"},
        ],
        "weight": 1.0,
    },
    {
        "id": "S2-2",
        "phase": 2,
        "triad": "shame",
        "target_type": 2,
        "type": "likert",
        "question": "Being needed and appreciated makes me feel worthy.",
        "options": [
            {"value": 5, "text": "Strongly agree—being needed is essential to my worth"},
            {"value": 4, "text": "Agree—appreciation means a lot to me"},
            {"value": 3, "text": "Neutral—it's nice but not essential"},
            {"value": 2, "text": "Disagree—my worth comes from other sources"},
            {"value": 1, "text": "Strongly disagree—I don't need to be needed"},
        ],
        "weight": 1.0,
    },
    {
        "id": "S2-3",
        "phase": 2,
        "triad": "shame",
        "target_type": 2,
        "type": "likert",
        "question": "I often put others' needs ahead of my own without realizing.",
        "options": [
            {"value": 5, "text": "Strongly agree—I neglect myself for others constantly"},
            {"value": 4, "text": "Agree—I frequently prioritize others"},
            {"value": 3, "text": "Neutral—I try to balance both"},
            {"value": 2, "text": "Disagree—I'm usually aware of my own needs"},
            {"value": 1, "text": "Strongly disagree—I put myself first"},
        ],
        "weight": 1.0,
    },
    {
        "id": "S2-4",
        "phase": 2,
        "triad": "shame",
        "target_type": 2,
        "type": "likert",
        "question": "Directly asking for what I need feels selfish or uncomfortable.",
        "options": [
            {"value": 5, "text": "Strongly agree—asking for myself feels wrong"},
            {"value": 4, "text": "Agree—I struggle to ask directly"},
            {"value": 3, "text": "Neutral—sometimes it's hard"},
            {"value": 2, "text": "Disagree—I can usually ask for what I need"},
            {"value": 1, "text": "Strongly disagree—I have no problem asking"},
        ],
        "weight": 1.0,
    },
    
    # Type 3 - The Achiever (S3-1 to S3-4)
    {
        "id": "S3-1",
        "phase": 2,
        "triad": "shame",
        "target_type": 3,
        "type": "likert",
        "question": "I adapt my image to succeed in any environment I'm in.",
        "options": [
            {"value": 5, "text": "Strongly agree—I'm a chameleon for success"},
            {"value": 4, "text": "Agree—I adjust my presentation strategically"},
            {"value": 3, "text": "Neutral—I adapt somewhat"},
            {"value": 2, "text": "Disagree—I stay fairly consistent"},
            {"value": 1, "text": "Strongly disagree—I never change who I am"},
        ],
        "weight": 1.0,
    },
    {
        "id": "S3-2",
        "phase": 2,
        "triad": "shame",
        "target_type": 3,
        "type": "likert",
        "question": "Efficiency and measurable results matter more than feelings.",
        "options": [
            {"value": 5, "text": "Strongly agree—results are what count"},
            {"value": 4, "text": "Agree—I prioritize outcomes over emotions"},
            {"value": 3, "text": "Neutral—both matter to me"},
            {"value": 2, "text": "Disagree—feelings are equally important"},
            {"value": 1, "text": "Strongly disagree—feelings come first"},
        ],
        "weight": 1.0,
    },
    {
        "id": "S3-3",
        "phase": 2,
        "triad": "shame",
        "target_type": 3,
        "type": "likert",
        "question": "I feel empty when I'm not working toward a goal.",
        "options": [
            {"value": 5, "text": "Strongly agree—I need goals to feel alive"},
            {"value": 4, "text": "Agree—I'm restless without objectives"},
            {"value": 3, "text": "Neutral—sometimes I need a break"},
            {"value": 2, "text": "Disagree—I'm fine without active goals"},
            {"value": 1, "text": "Strongly disagree—I prefer just being"},
        ],
        "weight": 1.0,
    },
    {
        "id": "S3-4",
        "phase": 2,
        "triad": "shame",
        "target_type": 3,
        "type": "likert",
        "question": "Failure or looking incompetent is unbearable to me.",
        "options": [
            {"value": 5, "text": "Strongly agree—failure is devastating"},
            {"value": 4, "text": "Agree—I avoid failure at all costs"},
            {"value": 3, "text": "Neutral—failure is uncomfortable but manageable"},
            {"value": 2, "text": "Disagree—I can handle failure okay"},
            {"value": 1, "text": "Strongly disagree—failure doesn't bother me much"},
        ],
        "weight": 1.0,
    },
    
    # Type 4 - The Individualist (S4-1 to S4-4)
    {
        "id": "S4-1",
        "phase": 2,
        "triad": "shame",
        "target_type": 4,
        "type": "likert",
        "question": "Something fundamental is missing that others seem to have.",
        "options": [
            {"value": 5, "text": "Strongly agree—I feel this deficiency deeply"},
            {"value": 4, "text": "Agree—I often feel like something's missing"},
            {"value": 3, "text": "Neutral—sometimes I feel this way"},
            {"value": 2, "text": "Disagree—I feel fairly complete"},
            {"value": 1, "text": "Strongly disagree—I don't feel lacking"},
        ],
        "weight": 1.0,
    },
    {
        "id": "S4-2",
        "phase": 2,
        "triad": "shame",
        "target_type": 4,
        "type": "likert",
        "question": "My emotional highs and lows feel more intense than most people's.",
        "options": [
            {"value": 5, "text": "Strongly agree—my emotions are exceptionally intense"},
            {"value": 4, "text": "Agree—I feel things more deeply than others"},
            {"value": 3, "text": "Neutral—my emotions seem average"},
            {"value": 2, "text": "Disagree—I'm fairly emotionally stable"},
            {"value": 1, "text": "Strongly disagree—I'm very even-keeled"},
        ],
        "weight": 1.0,
    },
    {
        "id": "S4-3",
        "phase": 2,
        "triad": "shame",
        "target_type": 4,
        "type": "likert",
        "question": "I need to feel authentic even if it creates conflict.",
        "options": [
            {"value": 5, "text": "Strongly agree—authenticity trumps harmony"},
            {"value": 4, "text": "Agree—I prioritize being real over fitting in"},
            {"value": 3, "text": "Neutral—I try to balance both"},
            {"value": 2, "text": "Disagree—I'd rather keep the peace"},
            {"value": 1, "text": "Strongly disagree—harmony is more important"},
        ],
        "weight": 1.0,
    },
    {
        "id": "S4-4",
        "phase": 2,
        "triad": "shame",
        "target_type": 4,
        "type": "likert",
        "question": "Beauty, depth, and meaning are essential to my existence.",
        "options": [
            {"value": 5, "text": "Strongly agree—life without these is unbearable"},
            {"value": 4, "text": "Agree—these are very important to me"},
            {"value": 3, "text": "Neutral—I appreciate them but don't need them"},
            {"value": 2, "text": "Disagree—I'm more practical"},
            {"value": 1, "text": "Strongly disagree—I focus on simpler things"},
        ],
        "weight": 1.0,
    },
    
    # Shame Triad Differentiation (SD-1 to SD-4)
    {
        "id": "SD-1",
        "phase": 2,
        "triad": "shame",
        "type": "differential",
        "question": "When helping others, I most need:",
        "options": [
            {"value": 2, "type_boost": 2, "text": "Gratitude and appreciation for my care"},
            {"value": 3, "type_boost": 3, "text": "Recognition for my competence and success"},
            {"value": 4, "type_boost": 4, "text": "Authentic connection and being truly seen"},
        ],
        "weight": 2.0,
    },
    {
        "id": "SD-2",
        "phase": 2,
        "triad": "shame",
        "type": "differential",
        "question": "My shame shows up most as:",
        "options": [
            {"value": 2, "type_boost": 2, "text": "Over-giving and losing myself in others' needs"},
            {"value": 3, "type_boost": 3, "text": "Over-performing and fear of being exposed as a fraud"},
            {"value": 4, "type_boost": 4, "text": "Over-identifying with emotions and feeling fundamentally flawed"},
        ],
        "weight": 2.0,
    },
    {
        "id": "SD-3",
        "phase": 2,
        "triad": "shame",
        "type": "differential",
        "question": "Under stress, I become:",
        "options": [
            {"value": 2, "type_boost": 2, "text": "Possessive, demanding, and resentful of ingratitude"},
            {"value": 3, "type_boost": 3, "text": "Deceptive, cutting corners, and obsessed with image"},
            {"value": 4, "type_boost": 4, "text": "Melancholic, withdrawn, and envious of others"},
        ],
        "weight": 2.0,
    },
    {
        "id": "SD-4",
        "phase": 2,
        "triad": "shame",
        "type": "differential",
        "question": "I seek love through:",
        "options": [
            {"value": 2, "type_boost": 2, "text": "Service and making myself indispensable"},
            {"value": 3, "type_boost": 3, "text": "Success and proving my value through achievement"},
            {"value": 4, "type_boost": 4, "text": "Uniqueness and sharing my authentic depth"},
        ],
        "weight": 2.0,
    },
]

PHASE2_ANGER_QUESTIONS = []  # Types 8, 9, 1 - To be implemented

# =============================================================================
# PHASE 2: ANGER TRIAD (Types 8, 9, 1)
# =============================================================================

PHASE2_ANGER_QUESTIONS = [
    # Type 8 - The Challenger (A8-1 to A8-4)
    {
        "id": "A8-1",
        "phase": 2,
        "triad": "anger",
        "target_type": 8,
        "type": "likert",
        "question": "I naturally take charge when others hesitate or avoid conflict.",
        "options": [
            {"value": 5, "text": "Strongly agree—I step up to lead immediately"},
            {"value": 4, "text": "Agree—I often take charge in uncertain situations"},
            {"value": 3, "text": "Neutral—sometimes I do, sometimes I don't"},
            {"value": 2, "text": "Disagree—I prefer to let others lead"},
            {"value": 1, "text": "Strongly disagree—I avoid taking charge"},
        ],
        "weight": 1.0,
    },
    {
        "id": "A8-2",
        "phase": 2,
        "triad": "anger",
        "target_type": 8,
        "type": "likert",
        "question": "Being controlled or vulnerable feels like a threat to my existence.",
        "options": [
            {"value": 5, "text": "Strongly agree—I cannot tolerate being controlled"},
            {"value": 4, "text": "Agree—vulnerability and control feel dangerous"},
            {"value": 3, "text": "Neutral—it depends on the situation"},
            {"value": 2, "text": "Disagree—I'm okay with some vulnerability"},
            {"value": 1, "text": "Strongly disagree—vulnerability doesn't threaten me"},
        ],
        "weight": 1.0,
    },
    {
        "id": "A8-3",
        "phase": 2,
        "triad": "anger",
        "target_type": 8,
        "type": "likert",
        "question": "I respect people who stand their ground, even against me.",
        "options": [
            {"value": 5, "text": "Strongly agree—I deeply respect strength and pushback"},
            {"value": 4, "text": "Agree—I admire people who hold firm"},
            {"value": 3, "text": "Neutral—it depends on the context"},
            {"value": 2, "text": "Disagree—I prefer people who compromise"},
            {"value": 1, "text": "Strongly disagree—standing ground against me is wrong"},
        ],
        "weight": 1.0,
    },
    {
        "id": "A8-4",
        "phase": 2,
        "triad": "anger",
        "target_type": 8,
        "type": "likert",
        "question": "My anger is immediate and direct - I express it, then move on.",
        "options": [
            {"value": 5, "text": "Strongly agree—I express anger directly, then it's done"},
            {"value": 4, "text": "Agree—I tend to be upfront with my anger"},
            {"value": 3, "text": "Neutral—sometimes direct, sometimes not"},
            {"value": 2, "text": "Disagree—I hold back or suppress anger"},
            {"value": 1, "text": "Strongly disagree—I rarely express anger directly"},
        ],
        "weight": 1.0,
    },
    
    # Type 9 - The Peacemaker (A9-1 to A9-4)
    {
        "id": "A9-1",
        "phase": 2,
        "triad": "anger",
        "target_type": 9,
        "type": "likert",
        "question": "I merge with others' agendas to avoid tension or separation.",
        "options": [
            {"value": 5, "text": "Strongly agree—I lose myself in others' priorities"},
            {"value": 4, "text": "Agree—I often go along to keep peace"},
            {"value": 3, "text": "Neutral—sometimes I merge, sometimes I don't"},
            {"value": 2, "text": "Disagree—I maintain my own agenda"},
            {"value": 1, "text": "Strongly disagree—I never merge with others"},
        ],
        "weight": 1.0,
    },
    {
        "id": "A9-2",
        "phase": 2,
        "triad": "anger",
        "target_type": 9,
        "type": "likert",
        "question": "My anger is so slow-burning I often don't realize I'm angry until later.",
        "options": [
            {"value": 5, "text": "Strongly agree—anger creeps up on me gradually"},
            {"value": 4, "text": "Agree—I often realize my anger after the fact"},
            {"value": 3, "text": "Neutral—sometimes I notice it, sometimes I don't"},
            {"value": 2, "text": "Disagree—I'm usually aware of my anger"},
            {"value": 1, "text": "Strongly disagree—I always know when I'm angry"},
        ],
        "weight": 1.0,
    },
    {
        "id": "A9-3",
        "phase": 2,
        "triad": "anger",
        "target_type": 9,
        "type": "likert",
        "question": "Having someone else decide is often easier than knowing my own preference.",
        "options": [
            {"value": 5, "text": "Strongly agree—I struggle to know what I want"},
            {"value": 4, "text": "Agree—I often defer to others' choices"},
            {"value": 3, "text": "Neutral—depends on the decision"},
            {"value": 2, "text": "Disagree—I usually know what I want"},
            {"value": 1, "text": "Strongly disagree—I always know my preferences"},
        ],
        "weight": 1.0,
    },
    {
        "id": "A9-4",
        "phase": 2,
        "triad": "anger",
        "target_type": 9,
        "type": "likert",
        "question": "Inner peace and harmony matter more than being right.",
        "options": [
            {"value": 5, "text": "Strongly agree—peace is more important than winning"},
            {"value": 4, "text": "Agree—I prioritize harmony over being correct"},
            {"value": 3, "text": "Neutral—both matter to me"},
            {"value": 2, "text": "Disagree—being right is important"},
            {"value": 1, "text": "Strongly disagree—being right matters most"},
        ],
        "weight": 1.0,
    },
    
    # Type 1 - The Reformer (A1-1 to A1-4)
    {
        "id": "A1-1",
        "phase": 2,
        "triad": "anger",
        "target_type": 1,
        "type": "likert",
        "question": "There's a right way to do things, and I feel compelled to correct errors.",
        "options": [
            {"value": 5, "text": "Strongly agree—I must correct things that are wrong"},
            {"value": 4, "text": "Agree—I notice and want to fix errors"},
            {"value": 3, "text": "Neutral—sometimes I notice, sometimes I let it go"},
            {"value": 2, "text": "Disagree—I'm not focused on correctness"},
            {"value": 1, "text": "Strongly disagree—there's no single right way"},
        ],
        "weight": 1.0,
    },
    {
        "id": "A1-2",
        "phase": 2,
        "triad": "anger",
        "target_type": 1,
        "type": "likert",
        "question": "My inner critic is relentless - I hold myself to impossibly high standards.",
        "options": [
            {"value": 5, "text": "Strongly agree—I'm my own harshest judge"},
            {"value": 4, "text": "Agree—I have very high standards for myself"},
            {"value": 3, "text": "Neutral—I'm moderately self-critical"},
            {"value": 2, "text": "Disagree—I'm fairly easy on myself"},
            {"value": 1, "text": "Strongly disagree—I don't have an inner critic"},
        ],
        "weight": 1.0,
    },
    {
        "id": "A1-3",
        "phase": 2,
        "triad": "anger",
        "target_type": 1,
        "type": "likert",
        "question": "Righteous anger about injustice or incompetence drives me to action.",
        "options": [
            {"value": 5, "text": "Strongly agree—injustice triggers strong action in me"},
            {"value": 4, "text": "Agree—I feel compelled to address unfairness"},
            {"value": 3, "text": "Neutral—sometimes it motivates me"},
            {"value": 2, "text": "Disagree—I don't get that worked up"},
            {"value": 1, "text": "Strongly disagree—injustice doesn't affect me much"},
        ],
        "weight": 1.0,
    },
    {
        "id": "A1-4",
        "phase": 2,
        "triad": "anger",
        "target_type": 1,
        "type": "likert",
        "question": "I restrain my impulses because they might be wrong or imperfect.",
        "options": [
            {"value": 5, "text": "Strongly agree—I tightly control my impulses"},
            {"value": 4, "text": "Agree—I often hold back from acting on impulse"},
            {"value": 3, "text": "Neutral—sometimes I restrain, sometimes not"},
            {"value": 2, "text": "Disagree—I'm fairly impulsive"},
            {"value": 1, "text": "Strongly disagree—I act on my impulses freely"},
        ],
        "weight": 1.0,
    },
    
    # Anger Triad Differentiation (AD-1 to AD-4)
    {
        "id": "AD-1",
        "phase": 2,
        "triad": "anger",
        "type": "differential",
        "question": "My anger is:",
        "options": [
            {"value": 8, "type_boost": 8, "text": "Explosive and direct - I confront immediately"},
            {"value": 9, "type_boost": 9, "text": "Suppressed and slow - it builds until it erupts"},
            {"value": 1, "type_boost": 1, "text": "Channeled and controlled - I redirect it into improvement"},
        ],
        "weight": 2.0,
    },
    {
        "id": "AD-2",
        "phase": 2,
        "triad": "anger",
        "type": "differential",
        "question": "I maintain control by:",
        "options": [
            {"value": 8, "type_boost": 8, "text": "Dominating - I take charge to protect myself and others"},
            {"value": 9, "type_boost": 9, "text": "Avoiding - I sidestep conflict to maintain peace"},
            {"value": 1, "type_boost": 1, "text": "Perfecting - I follow rules and standards meticulously"},
        ],
        "weight": 2.0,
    },
    {
        "id": "AD-3",
        "phase": 2,
        "triad": "anger",
        "type": "differential",
        "question": "Under stress, I become:",
        "options": [
            {"value": 8, "type_boost": 8, "text": "Confrontational - I push harder and fight back"},
            {"value": 9, "type_boost": 9, "text": "Dissociated - I numb out and withdraw"},
            {"value": 1, "type_boost": 1, "text": "Rigid and critical - I become more judgmental"},
        ],
        "weight": 2.0,
    },
    {
        "id": "AD-4",
        "phase": 2,
        "triad": "anger",
        "type": "differential",
        "question": "I seek autonomy through:",
        "options": [
            {"value": 8, "type_boost": 8, "text": "Strength - I become powerful to protect my freedom"},
            {"value": 9, "type_boost": 9, "text": "Harmony - I create peace to avoid being disturbed"},
            {"value": 1, "type_boost": 1, "text": "Integrity - I become correct to justify my position"},
        ],
        "weight": 2.0,
    },
]

# Combine all Phase 2 questions
PHASE2_QUESTIONS = PHASE2_FEAR_QUESTIONS + PHASE2_SHAME_QUESTIONS + PHASE2_ANGER_QUESTIONS

# =============================================================================
# PHASE 3 QUESTION BANK (WINGS & SUBTYPE)
# =============================================================================
# Wing questions: 2 per type (compare adjacent types)
# Subtype questions: 3 per type (SP, SO, SX instincts)

# Wing adjacencies for reference
# 1: (9, 2), 2: (1, 3), 3: (2, 4), 4: (3, 5),
# 5: (4, 6), 6: (5, 7), 7: (6, 8), 8: (7, 9), 9: (8, 1)

PHASE3_WING_QUESTIONS = {
    # Type 1 Wings (9w1 or 1w2)
    1: [
        {
            "id": "W1-1",
            "phase": 3,
            "core_type": 1,
            "type": "wing_comparison",
            "question": "In my pursuit of improvement, I more often:",
            "options": [
                {"value": 9, "wing": 9, "text": "Maintain inner calm and see multiple perspectives before acting"},
                {"value": 2, "wing": 2, "text": "Focus on helping others improve along with myself"},
            ],
            "weight": 1.5,
        },
        {
            "id": "W1-2",
            "phase": 3,
            "core_type": 1,
            "type": "wing_comparison",
            "question": "When I notice something wrong, I tend to:",
            "options": [
                {"value": 9, "wing": 9, "text": "Consider if it's worth the conflict to address it"},
                {"value": 2, "wing": 2, "text": "Feel compelled to help fix it for everyone's benefit"},
            ],
            "weight": 1.5,
        },
    ],
    # Type 2 Wings (1w2 or 2w3)
    2: [
        {
            "id": "W2-1",
            "phase": 3,
            "core_type": 2,
            "type": "wing_comparison",
            "question": "When helping others, I'm more motivated by:",
            "options": [
                {"value": 1, "wing": 1, "text": "Doing what's right and proper for them"},
                {"value": 3, "wing": 3, "text": "Being seen as successful and valuable in their eyes"},
            ],
            "weight": 1.5,
        },
        {
            "id": "W2-2",
            "phase": 3,
            "core_type": 2,
            "type": "wing_comparison",
            "question": "I express my caring nature by:",
            "options": [
                {"value": 1, "wing": 1, "text": "Offering principled advice and moral support"},
                {"value": 3, "wing": 3, "text": "Adapting to be whatever they need me to be"},
            ],
            "weight": 1.5,
        },
    ],
    # Type 3 Wings (2w3 or 3w4)
    3: [
        {
            "id": "W3-1",
            "phase": 3,
            "core_type": 3,
            "type": "wing_comparison",
            "question": "My drive for success is more connected to:",
            "options": [
                {"value": 2, "wing": 2, "text": "Being loved and appreciated by others"},
                {"value": 4, "wing": 4, "text": "Creating something unique and meaningful"},
            ],
            "weight": 1.5,
        },
        {
            "id": "W3-2",
            "phase": 3,
            "core_type": 3,
            "type": "wing_comparison",
            "question": "When achieving goals, I prefer:",
            "options": [
                {"value": 2, "wing": 2, "text": "Collaborative success that helps everyone"},
                {"value": 4, "wing": 4, "text": "Standing out as distinctively accomplished"},
            ],
            "weight": 1.5,
        },
    ],
    # Type 4 Wings (3w4 or 4w5)
    4: [
        {
            "id": "W4-1",
            "phase": 3,
            "core_type": 4,
            "type": "wing_comparison",
            "question": "I express my individuality more through:",
            "options": [
                {"value": 3, "wing": 3, "text": "Polished presentation and notable achievements"},
                {"value": 5, "wing": 5, "text": "Deep knowledge and intellectual uniqueness"},
            ],
            "weight": 1.5,
        },
        {
            "id": "W4-2",
            "phase": 3,
            "core_type": 4,
            "type": "wing_comparison",
            "question": "When feeling misunderstood, I tend to:",
            "options": [
                {"value": 3, "wing": 3, "text": "Work harder to show my value to others"},
                {"value": 5, "wing": 5, "text": "Retreat into my own world of ideas and feelings"},
            ],
            "weight": 1.5,
        },
    ],
    # Type 5 Wings (4w5 or 5w6)
    5: [
        {
            "id": "W5-1",
            "phase": 3,
            "core_type": 5,
            "type": "wing_comparison",
            "question": "My intellectual pursuits are more driven by:",
            "options": [
                {"value": 4, "wing": 4, "text": "Finding unique, creative insights others miss"},
                {"value": 6, "wing": 6, "text": "Building reliable systems and solving practical problems"},
            ],
            "weight": 1.5,
        },
        {
            "id": "W5-2",
            "phase": 3,
            "core_type": 5,
            "type": "wing_comparison",
            "question": "I relate to being described as:",
            "options": [
                {"value": 4, "wing": 4, "text": "The withdrawn, creative iconoclast"},
                {"value": 6, "wing": 6, "text": "The analytical troubleshooter"},
            ],
            "weight": 1.5,
        },
    ],
    # Type 6 Wings (5w6 or 6w7)
    6: [
        {
            "id": "W6-1",
            "phase": 3,
            "core_type": 6,
            "type": "wing_comparison",
            "question": "When facing uncertainty, I more often:",
            "options": [
                {"value": 5, "wing": 5, "text": "Withdraw to analyze and research thoroughly"},
                {"value": 7, "wing": 7, "text": "Stay active and look for positive possibilities"},
            ],
            "weight": 1.5,
        },
        {
            "id": "W6-2",
            "phase": 3,
            "core_type": 6,
            "type": "wing_comparison",
            "question": "My approach to building security involves:",
            "options": [
                {"value": 5, "wing": 5, "text": "Accumulating knowledge and becoming self-sufficient"},
                {"value": 7, "wing": 7, "text": "Creating alliances and keeping spirits high"},
            ],
            "weight": 1.5,
        },
    ],
    # Type 7 Wings (6w7 or 7w8)
    7: [
        {
            "id": "W7-1",
            "phase": 3,
            "core_type": 7,
            "type": "wing_comparison",
            "question": "My enthusiasm is more characterized by:",
            "options": [
                {"value": 6, "wing": 6, "text": "Loyal commitment to people and shared adventures"},
                {"value": 8, "wing": 8, "text": "Bold action and making things happen"},
            ],
            "weight": 1.5,
        },
        {
            "id": "W7-2",
            "phase": 3,
            "core_type": 7,
            "type": "wing_comparison",
            "question": "When pursuing experiences, I'm more:",
            "options": [
                {"value": 6, "wing": 6, "text": "Thoughtful about risks and loyal to companions"},
                {"value": 8, "wing": 8, "text": "Assertive and willing to push boundaries"},
            ],
            "weight": 1.5,
        },
    ],
    # Type 8 Wings (7w8 or 8w9)
    8: [
        {
            "id": "W8-1",
            "phase": 3,
            "core_type": 8,
            "type": "wing_comparison",
            "question": "My strength shows up more as:",
            "options": [
                {"value": 7, "wing": 7, "text": "Energetic leadership with enthusiasm"},
                {"value": 9, "wing": 9, "text": "Grounded power with patience"},
            ],
            "weight": 1.5,
        },
        {
            "id": "W8-2",
            "phase": 3,
            "core_type": 8,
            "type": "wing_comparison",
            "question": "When asserting myself, I tend to be:",
            "options": [
                {"value": 7, "wing": 7, "text": "Quick, direct, and adventurous"},
                {"value": 9, "wing": 9, "text": "Steady, receptive, and diplomatic when needed"},
            ],
            "weight": 1.5,
        },
    ],
    # Type 9 Wings (8w9 or 9w1)
    9: [
        {
            "id": "W9-1",
            "phase": 3,
            "core_type": 9,
            "type": "wing_comparison",
            "question": "My peaceful nature is balanced by:",
            "options": [
                {"value": 8, "wing": 8, "text": "A hidden strength and occasional intensity"},
                {"value": 1, "wing": 1, "text": "A sense of purpose and quiet principles"},
            ],
            "weight": 1.5,
        },
        {
            "id": "W9-2",
            "phase": 3,
            "core_type": 9,
            "type": "wing_comparison",
            "question": "When I do take action, it's more likely to be:",
            "options": [
                {"value": 8, "wing": 8, "text": "Bold and protective of those I care about"},
                {"value": 1, "wing": 1, "text": "Methodical and aligned with my values"},
            ],
            "weight": 1.5,
        },
    ],
}

# Subtype/Instinct questions (generic for all types)
PHASE3_SUBTYPE_QUESTIONS = [
    {
        "id": "SP-1",
        "phase": 3,
        "type": "subtype",
        "instinct": "sp",
        "question": "My core concerns in life center around:",
        "options": [
            {"value": 5, "text": "Strongly agree—security, health, comfort, and practical resources"},
            {"value": 4, "text": "Agree—these are very important to me"},
            {"value": 3, "text": "Neutral—somewhat important"},
            {"value": 2, "text": "Disagree—not my primary focus"},
            {"value": 1, "text": "Strongly disagree—rarely think about these"},
        ],
        "weight": 1.0,
    },
    {
        "id": "SP-2",
        "phase": 3,
        "type": "subtype",
        "instinct": "sp",
        "question": "I spend significant mental energy on:",
        "options": [
            {"value": 5, "text": "Strongly agree—maintaining my physical wellbeing and material stability"},
            {"value": 4, "text": "Agree—I'm quite attentive to these"},
            {"value": 3, "text": "Neutral—a moderate amount"},
            {"value": 2, "text": "Disagree—less than most people"},
            {"value": 1, "text": "Strongly disagree—hardly any"},
        ],
        "weight": 1.0,
    },
    {
        "id": "SO-1",
        "phase": 3,
        "type": "subtype",
        "instinct": "so",
        "question": "I'm highly attuned to:",
        "options": [
            {"value": 5, "text": "Strongly agree—group dynamics, social status, and community belonging"},
            {"value": 4, "text": "Agree—I pay close attention to social contexts"},
            {"value": 3, "text": "Neutral—somewhat aware"},
            {"value": 2, "text": "Disagree—not my focus"},
            {"value": 1, "text": "Strongly disagree—I largely ignore social dynamics"},
        ],
        "weight": 1.0,
    },
    {
        "id": "SO-2",
        "phase": 3,
        "type": "subtype",
        "instinct": "so",
        "question": "My sense of identity is strongly shaped by:",
        "options": [
            {"value": 5, "text": "Strongly agree—my role in groups and contribution to community"},
            {"value": 4, "text": "Agree—group membership matters a lot to me"},
            {"value": 3, "text": "Neutral—somewhat"},
            {"value": 2, "text": "Disagree—I'm more independent"},
            {"value": 1, "text": "Strongly disagree—I define myself individually"},
        ],
        "weight": 1.0,
    },
    {
        "id": "SX-1",
        "phase": 3,
        "type": "subtype",
        "instinct": "sx",
        "question": "I'm drawn to and energized by:",
        "options": [
            {"value": 5, "text": "Strongly agree—intense one-on-one connections and passionate experiences"},
            {"value": 4, "text": "Agree—I seek depth and intensity"},
            {"value": 3, "text": "Neutral—sometimes"},
            {"value": 2, "text": "Disagree—I prefer calmer connections"},
            {"value": 1, "text": "Strongly disagree—intensity drains me"},
        ],
        "weight": 1.0,
    },
    {
        "id": "SX-2",
        "phase": 3,
        "type": "subtype",
        "instinct": "sx",
        "question": "In relationships, I prioritize:",
        "options": [
            {"value": 5, "text": "Strongly agree—chemistry, attraction, and deep merging"},
            {"value": 4, "text": "Agree—intimate connection is essential"},
            {"value": 3, "text": "Neutral—it's one factor among many"},
            {"value": 2, "text": "Disagree—I value other qualities more"},
            {"value": 1, "text": "Strongly disagree—I prefer distance and independence"},
        ],
        "weight": 1.0,
    },
]

# Build combined question list for Phase 3
def get_phase3_questions_for_type(core_type: int) -> list:
    """Get all Phase 3 questions for a specific core type."""
    questions = []
    # Add wing questions for this type
    if core_type in PHASE3_WING_QUESTIONS:
        questions.extend(PHASE3_WING_QUESTIONS[core_type])
    # Add subtype questions (same for all types)
    questions.extend(PHASE3_SUBTYPE_QUESTIONS)
    return questions

# Build question lookup for all phases
QUESTION_BY_ID = {q["id"]: q for q in PHASE1_QUESTIONS}
QUESTION_BY_ID.update({q["id"]: q for q in PHASE2_QUESTIONS})
# Add stress detection questions
for q in STRESS_DETECTION_QUESTIONS:
    QUESTION_BY_ID[q["id"]] = q
# Add Phase 3 wing questions
for type_questions in PHASE3_WING_QUESTIONS.values():
    for q in type_questions:
        QUESTION_BY_ID[q["id"]] = q
# Add Phase 3 subtype questions
for q in PHASE3_SUBTYPE_QUESTIONS:
    QUESTION_BY_ID[q["id"]] = q
# Add Phase 4 validation questions
for q in PHASE4_VALIDATION_QUESTIONS:
    QUESTION_BY_ID[q["id"]] = q

# =============================================================================
# SESSION MANAGEMENT (MongoDB-backed for persistence across restarts)
# =============================================================================

# MongoDB collection name for V3 sessions
V3_SESSIONS_COLLECTION = "enneagram_v3_sessions"

# Global database reference (will be set by server.py)
_db = None

def set_v3_db(db):
    """Set the MongoDB database reference. Called from server.py startup."""
    global _db
    _db = db
    logger.info("[V3Assessment] Database reference set")

async def create_v3_session_async(user_id: str) -> dict:
    """Create a new V3 assessment session in MongoDB."""
    global _db
    if _db is None:
        raise RuntimeError("Database not initialized. Call set_v3_db() first.")
    
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    
    session = {
        "session_id": session_id,
        "user_id": user_id,
        "version": "v3",
        "phase": Phase.TRIAD.value,
        "phase_number": 1,
        
        # Question tracking
        "asked_question_ids": [],
        "current_question_index": 0,
        "answers": {},  # question_id -> response value
        
        # Triad scores (Phase 1)
        "triad_scores": {
            "fear": 0,
            "shame": 0,
            "anger": 0,
        },
        "triad_locked": None,  # Will be "fear", "shame", or "anger"
        "triad_confidence": 0.0,
        
        # Type scores (Phase 2)
        "type_scores": {str(i): 0 for i in range(1, 10)},  # Use string keys for MongoDB
        "core_type_locked": None,
        "core_type_confidence": 0.0,
        
        # Wing scores (Phase 3)
        "wing_scores": {"left": 0, "right": 0},
        "wing_result": None,  # Will be a number or "balanced"
        
        # Subtype scores (Phase 3)
        "subtype_scores": {"sp": 0, "sx": 0, "so": 0},
        "subtype_stack": [],  # e.g., ["sx", "sp", "so"]
        
        # Validation (Phase 4)
        "validation_flags": [],  # Potential mistypings to check
        "validation_confidence": 0.0,
        
        # Stress detection (Phase 4)
        "stress_scores": {
            "survival": 0,           # General survival/crisis mode score
            "type_7_indicator": 0,   # Seeking distractions (7 stress)
            "type_5_indicator": 0,   # Withdrawing/analyzing (5 stress)
            "type_1_indicator": 0,   # Controlling/ordering (1 stress)
        },
        "stress_detected": False,    # True if survival >= 4 AND conflict detected
        "stress_warning": None,      # Warning message if stress affects results
        "stress_conflict_triad": None,  # Triad that conflicts with stress pattern
        
        # User validation (after Phase 3)
        "user_validation_type": None,  # Type user selected as most resonant
        "user_validation_score": None,  # 1-5 confidence in calculated result
        "validation_adjustment": 0,     # Confidence adjustment from validation
        
        # Final result
        "final_result": None,  # Will be populated when done
        
        # Timestamps
        "created_at": now,
        "updated_at": now,
        "expires_at": now.timestamp() + SESSION_TTL_SECONDS,
    }
    
    # Insert into MongoDB
    await _db[V3_SESSIONS_COLLECTION].insert_one(session)
    logger.info(f"[V3Assessment] Created session {session_id} in MongoDB")
    
    return session

async def get_v3_session_async(session_id: str) -> Optional[dict]:
    """Get session by ID from MongoDB, checking expiration."""
    global _db
    if _db is None:
        return None
    
    session = await _db[V3_SESSIONS_COLLECTION].find_one({"session_id": session_id})
    if not session:
        return None
    
    # Check expiration
    if time.time() > session.get("expires_at", 0):
        await _db[V3_SESSIONS_COLLECTION].delete_one({"session_id": session_id})
        return None
    
    return session

async def update_v3_session_async(session_id: str, updates: dict) -> Optional[dict]:
    """Update session in MongoDB."""
    global _db
    if _db is None:
        return None
    
    session = await get_v3_session_async(session_id)
    if not session:
        return None
    
    # Add updated timestamp
    updates["updated_at"] = datetime.now(timezone.utc)
    
    # Update in MongoDB
    await _db[V3_SESSIONS_COLLECTION].update_one(
        {"session_id": session_id},
        {"$set": updates}
    )
    
    # Return updated session
    session.update(updates)
    return session

# Synchronous wrappers for backward compatibility (used by scoring functions)
def create_v3_session(user_id: str) -> dict:
    """Sync wrapper - DO NOT USE. Use create_v3_session_async instead."""
    raise NotImplementedError("Use create_v3_session_async instead")

def get_v3_session(session_id: str) -> Optional[dict]:
    """Sync wrapper - DO NOT USE. Use get_v3_session_async instead."""
    raise NotImplementedError("Use get_v3_session_async instead")

def update_v3_session(session_id: str, updates: dict) -> Optional[dict]:
    """Sync wrapper - DO NOT USE. Use update_v3_session_async instead."""
    raise NotImplementedError("Use update_v3_session_async instead")

# =============================================================================
# SCORING FUNCTIONS (Phase 1)
# =============================================================================

def score_phase1_answer(session: dict, question_id: str, response_value: int) -> dict:
    """
    Score a Phase 1 (Triad Lock) answer.
    
    Scoring logic:
    - Fear questions (F1-F7): High values (4-5) indicate Fear triad
    - Shame questions (S1-S7): High values (4-5) indicate Shame triad
    - Anger questions (A1-A6): High values (4-5) indicate Anger triad
    - F7 is reverse-scored (high original value = low fear indication)
    - STRESS-* questions: Track stress state for validation
    """
    question = QUESTION_BY_ID.get(question_id)
    if not question:
        raise ValueError(f"Unknown question ID: {question_id}")
    
    # Handle stress detection questions
    if question.get("type") == "stress_detection":
        return score_stress_question(session, question, response_value)
    
    # Get the triad this question measures
    triad = question.get("triad")
    if not triad:
        return session
    
    # Handle reverse scoring
    score = response_value
    if question.get("reverse_scored"):
        score = 6 - response_value  # Reverse: 5->1, 4->2, 3->3, 2->4, 1->5
    
    # Apply weight
    weight = question.get("weight", 1.0)
    weighted_score = score * weight
    
    # Add to triad score
    session["triad_scores"][triad] += weighted_score
    
    return session

def score_stress_question(session: dict, question: dict, response_value: int) -> dict:
    """
    Score a stress detection question.
    
    Updates stress_scores dict and checks for stress/triad conflicts.
    """
    stress_type = question.get("stress_type")
    if not stress_type:
        return session
    
    # Initialize stress_scores if not present
    if "stress_scores" not in session:
        session["stress_scores"] = {
            "survival": 0,
            "type_7_indicator": 0,
            "type_5_indicator": 0,
            "type_1_indicator": 0,
        }
    
    # Store the stress score
    session["stress_scores"][stress_type] = response_value
    
    # Check for stress state after all stress questions answered
    detect_stress_state(session)
    
    return session

def detect_stress_state(session: dict) -> None:
    """
    Analyze stress scores to detect if user is in stress state.
    
    If survival mode >= 4 AND a stress indicator conflicts with emerging triad:
    - Set stress_detected = True
    - Raise triad lock threshold
    - Add warning message
    """
    stress_scores = session.get("stress_scores", {})
    survival_score = stress_scores.get("survival", 0)
    
    # Only trigger if in survival mode
    if survival_score < STRESS_SURVIVAL_THRESHOLD:
        session["stress_detected"] = False
        session["stress_warning"] = None
        return
    
    # Check for conflicting stress indicators
    # If user shows Fear triad stress indicators but emerging triad is different
    percentages = calculate_triad_percentages(session)
    top_triad = max(percentages, key=percentages.get)
    
    # Detect specific stress patterns
    type_7_indicator = stress_scores.get("type_7_indicator", 0)
    type_5_indicator = stress_scores.get("type_5_indicator", 0)
    type_1_indicator = stress_scores.get("type_1_indicator", 0)
    
    conflict_detected = False
    conflict_triad = None
    
    # Type 7 stress (seeking distractions) -> Fear triad behavior
    if type_7_indicator >= STRESS_INDICATOR_THRESHOLD and top_triad != "fear":
        conflict_detected = True
        conflict_triad = "fear"
    
    # Type 5 stress (withdrawing) -> Fear triad behavior
    if type_5_indicator >= STRESS_INDICATOR_THRESHOLD and top_triad != "fear":
        conflict_detected = True
        conflict_triad = "fear"
    
    # Type 1 stress (controlling) -> Anger triad behavior
    if type_1_indicator >= STRESS_INDICATOR_THRESHOLD and top_triad != "anger":
        conflict_detected = True
        conflict_triad = "anger"
    
    session["stress_detected"] = conflict_detected
    session["stress_conflict_triad"] = conflict_triad
    
    if conflict_detected:
        session["stress_warning"] = (
            "You appear to be in a stress state. Your results may reflect current coping "
            "patterns rather than your core type. Consider retaking when not under stress."
        )
        logger.info(f"[V3Assessment] Stress detected: survival={survival_score}, conflict_triad={conflict_triad}")
    else:
        session["stress_warning"] = None

def calculate_triad_percentages(session: dict) -> dict:
    """Calculate percentage for each triad based on current scores."""
    fear = session["triad_scores"]["fear"]
    shame = session["triad_scores"]["shame"]
    anger = session["triad_scores"]["anger"]
    
    total = fear + shame + anger
    if total == 0:
        return {"fear": 0, "shame": 0, "anger": 0}
    
    return {
        "fear": round((fear / total) * 100, 1),
        "shame": round((shame / total) * 100, 1),
        "anger": round((anger / total) * 100, 1),
    }

def check_triad_lock(session: dict) -> Tuple[bool, Optional[str], float]:
    """
    Check if we can lock the triad.
    
    Requirements for early lock:
    - At least TRIAD_MIN_QUESTIONS answered (15)
    - Top triad >= TRIAD_LOCK_THRESHOLD (45%) OR TRIAD_LOCK_THRESHOLD_STRESSED (60%) if stress detected
    
    Returns:
        (is_locked, locked_triad, confidence)
    """
    percentages = calculate_triad_percentages(session)
    
    # Find the top triad
    sorted_triads = sorted(percentages.items(), key=lambda x: x[1], reverse=True)
    top_triad, top_pct = sorted_triads[0]
    second_triad, second_pct = sorted_triads[1]
    
    # Calculate confidence as the gap between top and second
    confidence = (top_pct - second_pct) * 2  # Double the gap for confidence
    confidence = min(confidence, 100)  # Cap at 100
    
    # Check minimum questions answered before allowing early lock
    questions_answered = len(session.get("asked_question_ids", []))
    if questions_answered < TRIAD_MIN_QUESTIONS:
        return False, None, confidence
    
    # Use raised threshold if stress detected
    stress_detected = session.get("stress_detected", False)
    threshold = TRIAD_LOCK_THRESHOLD_STRESSED if stress_detected else TRIAD_LOCK_THRESHOLD
    
    # Check if we can lock
    if top_pct >= threshold:
        return True, top_triad, confidence
    
    return False, None, confidence

def get_next_phase1_question(session: dict) -> Optional[dict]:
    """
    Get the next Phase 1 question to ask.
    
    IMPORTANT: Questions are interleaved across triads to ensure fair representation
    before any early triad lock decision. This prevents bias towards triads whose
    questions appear first in the question bank.
    
    Interleaving pattern: Fear -> Shame -> Anger -> Fear -> Shame -> Anger -> ...
    
    Stress detection questions are inserted after question 5.
    """
    asked = set(session.get("asked_question_ids", []))
    questions_answered = len(asked)
    
    # Insert stress detection questions after the 5th question
    # This gives us some triad data before asking about stress state
    if questions_answered >= 5:
        stress_remaining = [q for q in STRESS_DETECTION_QUESTIONS if q["id"] not in asked]
        if stress_remaining:
            return stress_remaining[0]
    
    # Group questions by triad
    fear_questions = [q for q in PHASE1_QUESTIONS if q["triad"] == "fear" and q["id"] not in asked]
    shame_questions = [q for q in PHASE1_QUESTIONS if q["triad"] == "shame" and q["id"] not in asked]
    anger_questions = [q for q in PHASE1_QUESTIONS if q["triad"] == "anger" and q["id"] not in asked]
    
    # Interleave: pick from the triad with the most unanswered questions relative to total
    # This ensures balanced coverage
    # Note: triads variable is informational - actual logic uses proportions below
    
    # Calculate how many questions have been asked from each triad
    asked_fear = 7 - len(fear_questions)
    asked_shame = 7 - len(shame_questions)
    asked_anger = 6 - len(anger_questions)
    
    # Pick from the triad that has been asked the least (proportionally)
    # to ensure fair coverage
    proportions = [
        ("fear", asked_fear / 7, fear_questions),
        ("shame", asked_shame / 7, shame_questions),
        ("anger", asked_anger / 6, anger_questions),
    ]
    
    # Sort by proportion asked (ascending) - pick from least asked triad
    proportions.sort(key=lambda x: x[1])
    
    for triad_name, proportion, questions in proportions:
        if questions:
            return questions[0]
    
    return None

# =============================================================================
# PHASE 2 SCORING FUNCTIONS (Core Type - Fear Triad)
# =============================================================================

def score_phase2_answer(session: dict, question_id: str, response_value: int) -> dict:
    """
    Score a Phase 2 (Core Type) answer.
    
    Scoring logic:
    - Likert questions (F5-x, F6-x, F7-x): Score adds to that type
    - Differential questions (FD-x): Selected option strongly boosts that type
    """
    question = QUESTION_BY_ID.get(question_id)
    if not question:
        raise ValueError(f"Unknown question ID: {question_id}")
    
    # Ensure type_scores exists
    if "type_scores" not in session:
        session["type_scores"] = {str(i): 0 for i in range(1, 10)}
    
    weight = question.get("weight", 1.0)
    q_type = question.get("type")
    
    if q_type == "differential":
        # Differential question: response_value IS the type to boost
        # The value is 5, 6, or 7 for Fear triad differential questions
        type_to_boost = str(response_value)
        
        # Strong boost for selected type
        session["type_scores"][type_to_boost] = session["type_scores"].get(type_to_boost, 0) + (5 * weight)
        
        # Slight suppression for non-selected types in the triad
        triad_types = TRIAD_TYPES.get(Triad(session.get("triad_locked", "fear")), [5, 6, 7])
        for t in triad_types:
            if str(t) != type_to_boost:
                session["type_scores"][str(t)] = session["type_scores"].get(str(t), 0) + 1
    else:
        # Likert question: Add weighted score to target type
        target_type = str(question.get("target_type"))
        if target_type:
            weighted_score = response_value * weight
            session["type_scores"][target_type] = session["type_scores"].get(target_type, 0) + weighted_score
    
    return session

def calculate_type_percentages(session: dict, triad: str) -> dict:
    """Calculate percentage for each type within a triad."""
    triad_types = TRIAD_TYPES.get(Triad(triad), [])
    type_scores = session.get("type_scores", {})
    
    # Get scores for types in this triad
    scores = {str(t): type_scores.get(str(t), 0) for t in triad_types}
    total = sum(scores.values())
    
    if total == 0:
        # Equal distribution if no scores yet
        return {str(t): round(100 / len(triad_types), 1) for t in triad_types}
    
    return {t: round((s / total) * 100, 1) for t, s in scores.items()}

def check_core_type_lock(session: dict) -> Tuple[bool, Optional[int], float]:
    """
    Check if we can lock the core type.
    
    Requirements for early lock:
    - At least CORE_TYPE_MIN_QUESTIONS Phase 2 questions answered (8)
    - Confidence > CORE_TYPE_CONFIDENCE_THRESHOLD (70%)
    
    Returns:
        (is_locked, locked_type, confidence)
    """
    triad_locked = session.get("triad_locked")
    if not triad_locked:
        return False, None, 0
    
    percentages = calculate_type_percentages(session, triad_locked)
    
    # Find the top type
    sorted_types = sorted(percentages.items(), key=lambda x: x[1], reverse=True)
    top_type, top_pct = sorted_types[0]
    second_pct = sorted_types[1][1] if len(sorted_types) > 1 else 0
    
    # Calculate confidence based on lead over second type
    confidence = top_pct - second_pct
    if confidence > 30:
        confidence = min(confidence * 2.5, 100)  # Strong lead = high confidence
    else:
        confidence = min(confidence * 2, 80)  # Moderate lead = moderate confidence
    
    # Count Phase 2 questions answered
    asked = session.get("asked_question_ids", [])
    phase2_answered = sum(1 for q_id in asked if q_id in [q["id"] for q in PHASE2_QUESTIONS])
    
    if phase2_answered < CORE_TYPE_MIN_QUESTIONS:
        return False, None, confidence
    
    # Check if we have high enough confidence for early lock
    if confidence >= CORE_TYPE_CONFIDENCE_THRESHOLD:
        return True, int(top_type), confidence
    
    return False, None, confidence

def get_next_phase2_question(session: dict) -> Optional[dict]:
    """Get the next Phase 2 question based on locked triad."""
    asked = set(session.get("asked_question_ids", []))
    triad_locked = session.get("triad_locked")
    
    if not triad_locked:
        return None
    
    # Get Phase 2 questions for this triad
    if triad_locked == "fear":
        questions = PHASE2_FEAR_QUESTIONS
    elif triad_locked == "shame":
        questions = PHASE2_SHAME_QUESTIONS
    elif triad_locked == "anger":
        questions = PHASE2_ANGER_QUESTIONS
    else:
        return None
    
    for q in questions:
        if q["id"] not in asked:
            return q
    
    return None

# =============================================================================
# PHASE 3 SCORING FUNCTIONS (Wings & Subtype)
# =============================================================================

def score_phase3_answer(session: dict, question_id: str, response_value: int) -> dict:
    """
    Score a Phase 3 (Wing & Subtype) answer.
    
    Scoring logic:
    - Wing comparison questions: response_value IS the wing type selected
    - Subtype questions: Likert scale (1-5) adds to that instinct
    """
    question = QUESTION_BY_ID.get(question_id)
    if not question:
        raise ValueError(f"Unknown question ID: {question_id}")
    
    q_type = question.get("type")
    weight = question.get("weight", 1.0)
    
    if q_type == "wing_comparison":
        # Wing comparison: response_value IS the wing type (e.g., 4 or 6 for Type 5)
        core_type = session.get("core_type_locked")
        if core_type and core_type in WING_ADJACENTS:
            left_wing, right_wing = WING_ADJACENTS[core_type]
            
            # Ensure wing_scores exists
            if "wing_scores" not in session:
                session["wing_scores"] = {"left": 0, "right": 0}
            
            if response_value == left_wing:
                session["wing_scores"]["left"] += (3 * weight)
            elif response_value == right_wing:
                session["wing_scores"]["right"] += (3 * weight)
    
    elif q_type == "subtype":
        # Subtype question: Add score to the instinct
        instinct = question.get("instinct")  # "sp", "so", or "sx"
        if instinct:
            if "subtype_scores" not in session:
                session["subtype_scores"] = {"sp": 0, "so": 0, "sx": 0}
            session["subtype_scores"][instinct] += (response_value * weight)
    
    return session

def calculate_wing_result(session: dict) -> Tuple[Optional[int], float, str]:
    """
    Calculate the wing result based on wing scores.
    
    Returns:
        (wing_number, confidence, status)
        status is "locked", "balanced", or "inconclusive"
    """
    core_type = session.get("core_type_locked")
    if not core_type or core_type not in WING_ADJACENTS:
        return None, 0, "inconclusive"
    
    left_wing, right_wing = WING_ADJACENTS[core_type]
    wing_scores = session.get("wing_scores", {"left": 0, "right": 0})
    
    left_score = wing_scores.get("left", 0)
    right_score = wing_scores.get("right", 0)
    total = left_score + right_score
    
    if total == 0:
        return None, 0, "inconclusive"
    
    # Calculate percentages
    left_pct = (left_score / total) * 100
    right_pct = (right_score / total) * 100
    
    # Determine wing
    gap = abs(left_pct - right_pct)
    
    if gap < 20:  # Very close - balanced wings
        return None, gap, "balanced"
    elif left_pct > right_pct:
        confidence = min(gap * 2, 100)
        return left_wing, confidence, "locked"
    else:
        confidence = min(gap * 2, 100)
        return right_wing, confidence, "locked"

def calculate_subtype_stack(session: dict) -> Tuple[list, dict]:
    """
    Calculate the instinctual stack based on subtype scores.
    
    Returns:
        (stack_list, score_dict)
        stack_list e.g., ["sx", "sp", "so"]
        score_dict e.g., {"sp": 3.5, "so": 2.1, "sx": 4.2}
    """
    subtype_scores = session.get("subtype_scores", {"sp": 0, "so": 0, "sx": 0})
    
    # Normalize scores
    total = sum(subtype_scores.values())
    if total == 0:
        return ["sp", "so", "sx"], {"sp": 0, "so": 0, "sx": 0}
    
    normalized = {k: round((v / total) * 5, 1) for k, v in subtype_scores.items()}
    
    # Sort by score (descending)
    sorted_instincts = sorted(normalized.items(), key=lambda x: x[1], reverse=True)
    stack = [item[0] for item in sorted_instincts]
    
    return stack, normalized

def get_next_phase3_question(session: dict) -> Optional[dict]:
    """Get the next Phase 3 question based on locked core type."""
    asked = set(session.get("asked_question_ids", []))
    core_type = session.get("core_type_locked")
    
    if not core_type:
        return None
    
    # Get Phase 3 questions for this type
    questions = get_phase3_questions_for_type(core_type)
    
    for q in questions:
        if q["id"] not in asked:
            return q
    
    return None

def build_final_result(session: dict) -> dict:
    """Build the final assessment result object."""
    core_type = session.get("core_type_locked")
    triad = session.get("triad_locked")
    
    # Get wing result
    wing, wing_confidence, wing_status = calculate_wing_result(session)
    
    # Get subtype stack
    subtype_stack, instinct_scores = calculate_subtype_stack(session)
    
    # Build full type string (e.g., "5w4 sx/sp")
    if wing_status == "balanced":
        wing_str = "w"  # Just "w" for balanced
        full_type_string = f"{core_type}w (balanced)"
    else:
        wing_str = f"w{wing}" if wing else ""
        full_type_string = f"{core_type}{wing_str}"
    
    # Add subtype to full string
    if len(subtype_stack) >= 2:
        full_type_string += f" {subtype_stack[0]}/{subtype_stack[1]}"
    
    # Calculate overall confidence
    triad_conf = session.get("triad_confidence", 0)
    type_conf = session.get("core_type_confidence", 0)
    overall_confidence = (triad_conf * 0.3) + (type_conf * 0.4) + (wing_confidence * 0.15) + 15  # +15 for completed
    overall_confidence = min(overall_confidence, 100)
    
    return {
        "core_type": core_type,
        "core_type_name": {
            1: "The Reformer", 2: "The Helper", 3: "The Achiever",
            4: "The Individualist", 5: "The Investigator", 6: "The Loyalist",
            7: "The Enthusiast", 8: "The Challenger", 9: "The Peacemaker"
        }.get(core_type, f"Type {core_type}"),
        "wing": wing if wing_status == "locked" else "balanced",
        "wing_status": wing_status,
        "wing_confidence": round(wing_confidence, 1),
        "triad": triad,
        "dominant_instinct": subtype_stack[0] if subtype_stack else None,
        "secondary_instinct": subtype_stack[1] if len(subtype_stack) > 1 else None,
        "instinct_stack": subtype_stack,
        "instinct_scores": instinct_scores,
        "full_type_string": full_type_string,
        "confidence_percentage": round(overall_confidence, 1),
        "assessment_version": "v3",
    }

# =============================================================================
# MAIN API FUNCTIONS (Async for MongoDB)
# =============================================================================

async def start_v3_assessment_async(user_id: str) -> dict:
    """
    Start a new V3 assessment session.
    
    Returns:
        Session data with first question
    """
    session = await create_v3_session_async(user_id)
    
    # Get first question
    first_question = get_next_phase1_question(session)
    
    return {
        "session_id": session["session_id"],
        "phase": session["phase"],
        "phase_number": session["phase_number"],
        "phase_label": "Discovering your triad...",
        "question": format_question_for_api(first_question),
        "progress": {
            "current": 1,
            "estimated_total": 45,  # Rough estimate
            "section": "Testing your core center...",
        },
    }

async def submit_v3_answer_async(session_id: str, question_id: str, response_value: int) -> dict:
    """
    Submit an answer and get the next question or result.
    
    Args:
        session_id: The assessment session ID
        question_id: The question being answered
        response_value: The selected option value (1-5 for likert, type number for differential)
    
    Returns:
        Next question or final result
    """
    session = await get_v3_session_async(session_id)
    if not session:
        raise ValueError("Session not found or expired")
    
    # Check for duplicate answer
    if question_id in session.get("answers", {}):
        logger.warning(f"Duplicate answer for {question_id}, skipping")
    else:
        # Record the answer
        if "answers" not in session:
            session["answers"] = {}
        session["answers"][question_id] = response_value
        
        if "asked_question_ids" not in session:
            session["asked_question_ids"] = []
        session["asked_question_ids"].append(question_id)
        
        # Score based on current phase
        if session["phase"] == Phase.TRIAD.value:
            score_phase1_answer(session, question_id, response_value)
        elif session["phase"] == Phase.CORE.value:
            score_phase2_answer(session, question_id, response_value)
        elif session["phase"] == Phase.WING_SUBTYPE.value:
            score_phase3_answer(session, question_id, response_value)
        elif session["phase"] == Phase.VALIDATION.value:
            score_phase4_answer(session, question_id, response_value)
    
    # Handle phase completion
    if session["phase"] == Phase.TRIAD.value:
        return await handle_phase1_completion_async(session)
    elif session["phase"] == Phase.CORE.value:
        return await handle_phase2_completion_async(session)
    elif session["phase"] == Phase.WING_SUBTYPE.value:
        return await handle_phase3_completion_async(session)
    elif session["phase"] == Phase.VALIDATION.value:
        return await handle_phase4_completion_async(session)
    
    # For phases not yet implemented
    return {"status": "done", "message": "Phase not yet implemented"}

async def handle_phase1_completion_async(session: dict) -> dict:
    """Handle Phase 1 (Triad Lock) completion logic."""
    
    # Check if all Phase 1 questions are answered
    phase1_ids = {q["id"] for q in PHASE1_QUESTIONS}
    answered_ids = set(session.get("asked_question_ids", []))
    answered_phase1 = answered_ids.intersection(phase1_ids)
    
    # Try to lock triad
    is_locked, locked_triad, confidence = check_triad_lock(session)
    
    # If all questions answered, force lock to top triad
    all_answered = len(answered_phase1) >= len(PHASE1_QUESTIONS)
    
    if is_locked or all_answered:
        if not is_locked:
            # Force lock to top triad
            percentages = calculate_triad_percentages(session)
            sorted_triads = sorted(percentages.items(), key=lambda x: x[1], reverse=True)
            locked_triad = sorted_triads[0][0]
            confidence = (sorted_triads[0][1] - sorted_triads[1][1]) * 2
        
        # Update session for Phase 2
        session["triad_locked"] = locked_triad
        session["triad_confidence"] = confidence
        session["phase"] = Phase.CORE.value
        session["phase_number"] = 2
        
        # Update in MongoDB
        await update_v3_session_async(session["session_id"], {
            "triad_locked": locked_triad,
            "triad_confidence": confidence,
            "phase": Phase.CORE.value,
            "phase_number": 2,
            "triad_scores": session["triad_scores"],
            "stress_scores": session.get("stress_scores", {}),
            "stress_detected": session.get("stress_detected", False),
            "stress_warning": session.get("stress_warning"),
            "stress_conflict_triad": session.get("stress_conflict_triad"),
            "answers": session["answers"],
            "asked_question_ids": session["asked_question_ids"],
        })
        
        # Get first Phase 2 question (if available for this triad)
        first_phase2_question = get_next_phase2_question(session)
        
        if first_phase2_question:
            # Transition to Phase 2 with first question
            total_answered = len(session.get("asked_question_ids", []))
            return {
                "status": "continue",
                "phase_transition": True,
                "phase_completed": 1,
                "phase_result": {
                    "triad_locked": locked_triad,
                    "triad_confidence": confidence,
                    "triad_percentages": calculate_triad_percentages(session),
                    "types_in_triad": TRIAD_TYPES[Triad(locked_triad)],
                },
                "session_id": session["session_id"],
                "phase": Phase.CORE.value,
                "phase_number": 2,
                "phase_label": f"Narrowing down your type in the {locked_triad.title()} triad...",
                "question": format_question_for_api(first_phase2_question),
                "progress": {
                    "current": total_answered + 1,
                    "estimated_total": 45,
                    "section": f"Testing types {', '.join(map(str, TRIAD_TYPES[Triad(locked_triad)]))}...",
                    "confidence_hint": "Phase 2 begins - refining your type...",
                },
            }
        else:
            # No Phase 2 questions for this triad (Shame/Anger not implemented yet)
            return {
                "status": "phase_complete",
                "phase_completed": 1,
                "phase_result": {
                    "triad_locked": locked_triad,
                    "triad_confidence": confidence,
                    "triad_percentages": calculate_triad_percentages(session),
                    "types_in_triad": TRIAD_TYPES[Triad(locked_triad)],
                },
                "next_phase": 2,
                "message": f"Triad locked: {locked_triad.title()} ({confidence:.0f}% confidence). Phase 2 not yet implemented for this triad.",
            }
    
    # Get next question
    next_question = get_next_phase1_question(session)
    if not next_question:
        # Should not happen, but handle gracefully
        return {"status": "error", "message": "No more Phase 1 questions"}
    
    # Update session in MongoDB
    await update_v3_session_async(session["session_id"], {
        "triad_scores": session["triad_scores"],
        "answers": session["answers"],
        "asked_question_ids": session["asked_question_ids"],
    })
    
    answered_count = len(answered_phase1)
    
    return {
        "status": "continue",
        "session_id": session["session_id"],
        "phase": session["phase"],
        "phase_number": session["phase_number"],
        "phase_label": "Discovering your triad...",
        "question": format_question_for_api(next_question),
        "progress": {
            "current": answered_count + 1,
            "estimated_total": 45,
            "section": "Testing your core center...",
            "confidence_hint": get_confidence_hint(session),
        },
    }

async def handle_phase2_completion_async(session: dict) -> dict:
    """Handle Phase 2 (Core Type) completion logic."""
    
    triad_locked = session.get("triad_locked")
    if not triad_locked:
        return {"status": "error", "message": "Triad not locked - cannot process Phase 2"}
    
    # Get Phase 2 questions for this triad
    if triad_locked == "fear":
        phase2_questions = PHASE2_FEAR_QUESTIONS
    elif triad_locked == "shame":
        phase2_questions = PHASE2_SHAME_QUESTIONS
    elif triad_locked == "anger":
        phase2_questions = PHASE2_ANGER_QUESTIONS
    else:
        phase2_questions = []
    
    # Count Phase 2 questions answered
    phase2_ids = {q["id"] for q in phase2_questions}
    answered_ids = set(session.get("asked_question_ids", []))
    answered_phase2 = answered_ids.intersection(phase2_ids)
    
    # Try to lock core type
    is_locked, locked_type, confidence = check_core_type_lock(session)
    
    # Check if all Phase 2 questions answered
    all_answered = len(answered_phase2) >= len(phase2_questions)
    
    if is_locked or all_answered:
        if not is_locked:
            # Force lock to top type
            percentages = calculate_type_percentages(session, triad_locked)
            sorted_types = sorted(percentages.items(), key=lambda x: x[1], reverse=True)
            locked_type = int(sorted_types[0][0])
            confidence = sorted_types[0][1] - sorted_types[1][1]
        
        # Determine if confidence is sufficient or needs warning
        low_confidence = confidence < 50
        
        # Update session
        session["core_type_locked"] = locked_type
        session["core_type_confidence"] = confidence
        session["phase"] = Phase.WING_SUBTYPE.value
        session["phase_number"] = 3
        
        await update_v3_session_async(session["session_id"], {
            "core_type_locked": locked_type,
            "core_type_confidence": confidence,
            "phase": Phase.WING_SUBTYPE.value,
            "phase_number": 3,
            "type_scores": session.get("type_scores", {}),
            "answers": session["answers"],
            "asked_question_ids": session["asked_question_ids"],
        })
        
        # Get first Phase 3 question (if available for this type)
        first_phase3_question = get_next_phase3_question(session)
        
        if first_phase3_question:
            # Transition to Phase 3 with first question
            total_answered = len(session.get("asked_question_ids", []))
            
            result = {
                "status": "continue",
                "phase_transition": True,
                "phase_completed": 2,
                "phase_result": {
                    "core_type_locked": locked_type,
                    "core_type_confidence": round(confidence, 1),
                    "type_percentages": calculate_type_percentages(session, triad_locked),
                    "triad": triad_locked,
                },
                "session_id": session["session_id"],
                "phase": Phase.WING_SUBTYPE.value,
                "phase_number": 3,
                "phase_label": "Determining your wing and instincts...",
                "question": format_question_for_api(first_phase3_question),
                "progress": {
                    "current": total_answered + 1,
                    "estimated_total": 45,
                    "section": f"Type {locked_type} - Wings & Subtypes",
                    "confidence_hint": "Almost there! Final phase...",
                },
            }
            
            if low_confidence:
                result["warning"] = "Low type confidence - results may be less accurate"
            
            return result
        else:
            # No Phase 3 questions (shouldn't happen)
            result = {
                "status": "phase_complete",
                "phase_completed": 2,
                "phase_result": {
                    "core_type_locked": locked_type,
                    "core_type_confidence": round(confidence, 1),
                    "type_percentages": calculate_type_percentages(session, triad_locked),
                    "triad": triad_locked,
                },
                "next_phase": 3,
                "message": f"Core type identified: Type {locked_type} ({confidence:.0f}% confidence). Phase 3 not available.",
            }
            
            if low_confidence:
                result["warning"] = "Low confidence - consider retaking with more reflective answers"
            
            return result
    
    # Get next Phase 2 question
    next_question = get_next_phase2_question(session)
    if not next_question:
        # Should not happen, but handle gracefully
        return {"status": "error", "message": "No more Phase 2 questions"}
    
    # Update session in MongoDB
    await update_v3_session_async(session["session_id"], {
        "type_scores": session.get("type_scores", {}),
        "answers": session["answers"],
        "asked_question_ids": session["asked_question_ids"],
    })
    
    total_answered = len(session.get("asked_question_ids", []))
    type_percentages = calculate_type_percentages(session, triad_locked)
    
    # Build confidence hint based on current type scores
    sorted_types = sorted(type_percentages.items(), key=lambda x: x[1], reverse=True)
    if len(sorted_types) >= 2:
        gap = sorted_types[0][1] - sorted_types[1][1]
        if gap > 20:
            hint = f"Type {sorted_types[0][0]} is emerging as your likely type..."
        elif gap > 10:
            hint = "A pattern is forming..."
        else:
            hint = "Still gathering data to differentiate..."
    else:
        hint = "Analyzing your responses..."
    
    return {
        "status": "continue",
        "session_id": session["session_id"],
        "phase": session["phase"],
        "phase_number": session["phase_number"],
        "phase_label": f"Narrowing down your type in the {triad_locked.title()} triad...",
        "question": format_question_for_api(next_question),
        "progress": {
            "current": total_answered + 1,
            "estimated_total": 45,
            "section": f"Testing types {', '.join(map(str, TRIAD_TYPES[Triad(triad_locked)]))}...",
            "confidence_hint": hint,
        },
    }

async def handle_phase3_completion_async(session: dict) -> dict:
    """Handle Phase 3 (Wing & Subtype) completion logic."""
    
    core_type = session.get("core_type_locked")
    if not core_type:
        return {"status": "error", "message": "Core type not locked - cannot process Phase 3"}
    
    # Get Phase 3 questions for this type
    phase3_questions = get_phase3_questions_for_type(core_type)
    
    # Count Phase 3 questions answered
    phase3_ids = {q["id"] for q in phase3_questions}
    answered_ids = set(session.get("asked_question_ids", []))
    answered_phase3 = answered_ids.intersection(phase3_ids)
    
    # Check if all Phase 3 questions answered
    all_answered = len(answered_phase3) >= len(phase3_questions)
    
    if all_answered:
        # Check if we need Phase 4 validation
        stress_detected = session.get("stress_detected", False)
        
        if stress_detected:
            # Transition to Phase 4 validation
            session["phase"] = Phase.VALIDATION.value
            session["phase_number"] = 4
            
            await update_v3_session_async(session["session_id"], {
                "phase": Phase.VALIDATION.value,
                "phase_number": 4,
                "wing_scores": session.get("wing_scores", {}),
                "subtype_scores": session.get("subtype_scores", {}),
                "answers": session["answers"],
                "asked_question_ids": session["asked_question_ids"],
            })
            
            # Build preliminary result for validation
            prelim_result = build_final_result(session)
            
            # Get top 3 candidate types for validation
            type_scores = session.get("type_scores", {})
            sorted_types = sorted(type_scores.items(), key=lambda x: float(x[1]), reverse=True)
            top_3_types = [int(t[0]) for t in sorted_types[:3] if float(t[1]) > 0]
            if core_type not in top_3_types:
                top_3_types.insert(0, core_type)
            top_3_types = top_3_types[:3]
            
            # Build validation question with type descriptions
            validation_options = []
            for t in top_3_types:
                desc = TYPE_DESCRIPTIONS.get(t, {})
                validation_options.append({
                    "value": t,
                    "name": desc.get("name", f"Type {t}"),
                    "description": desc.get("description", ""),
                })
            
            return {
                "status": "continue",
                "phase_transition": True,
                "phase_completed": 3,
                "session_id": session["session_id"],
                "phase": Phase.VALIDATION.value,
                "phase_number": 4,
                "phase_label": "Validating your result...",
                "stress_warning": session.get("stress_warning"),
                "preliminary_result": prelim_result,
                "question": {
                    "id": "VAL-1",
                    "phase": 4,
                    "type": "validation_ranking",
                    "question": "Which description feels most like your CORE self—not how you act under stress, but who you've been since childhood?",
                    "options": validation_options,
                },
                "progress": {
                    "current": len(session.get("asked_question_ids", [])) + 1,
                    "estimated_total": len(session.get("asked_question_ids", [])) + 2,
                    "section": "Validating your type...",
                    "confidence_hint": "Please review these descriptions carefully.",
                },
            }
        
        # No stress detected - complete assessment normally
        final_result = build_final_result(session)
        
        # Update session to done
        session["phase"] = Phase.DONE.value
        session["phase_number"] = 4
        session["final_result"] = final_result
        
        await update_v3_session_async(session["session_id"], {
            "phase": Phase.DONE.value,
            "phase_number": 4,
            "wing_scores": session.get("wing_scores", {}),
            "subtype_scores": session.get("subtype_scores", {}),
            "final_result": final_result,
            "answers": session["answers"],
            "asked_question_ids": session["asked_question_ids"],
        })
        
        return {
            "status": "done",
            "phase_completed": 3,
            "final_result": final_result,
            "message": f"Assessment complete! You are a {final_result['full_type_string']}",
        }
    
    # Get next Phase 3 question
    next_question = get_next_phase3_question(session)
    if not next_question:
        # Should not happen, but handle gracefully
        return {"status": "error", "message": "No more Phase 3 questions"}
    
    # Update session in MongoDB
    await update_v3_session_async(session["session_id"], {
        "wing_scores": session.get("wing_scores", {}),
        "subtype_scores": session.get("subtype_scores", {}),
        "answers": session["answers"],
        "asked_question_ids": session["asked_question_ids"],
    })
    
    total_answered = len(session.get("asked_question_ids", []))
    
    # Determine hint based on progress
    wing_scores = session.get("wing_scores", {"left": 0, "right": 0})
    subtype_scores = session.get("subtype_scores", {"sp": 0, "so": 0, "sx": 0})
    
    if sum(wing_scores.values()) > 0 or sum(subtype_scores.values()) > 0:
        hint = "Refining your wing and instincts..."
    else:
        hint = "Determining your wing preference..."
    
    return {
        "status": "continue",
        "session_id": session["session_id"],
        "phase": session["phase"],
        "phase_number": session["phase_number"],
        "phase_label": "Determining your wing and instincts...",
        "question": format_question_for_api(next_question),
        "progress": {
            "current": total_answered + 1,
            "estimated_total": 45,
            "section": f"Type {core_type} - Wings & Subtypes",
            "confidence_hint": hint,
        },
    }

async def get_v3_session_status_async(session_id: str) -> dict:
    """Get current status of a V3 assessment session."""
    session = await get_v3_session_async(session_id)
    if not session:
        return {"found": False, "error": "Session not found or expired"}
    
    created_at = session.get("created_at")
    updated_at = session.get("updated_at")
    
    return {
        "found": True,
        "session_id": session["session_id"],
        "user_id": session["user_id"],
        "phase": session["phase"],
        "phase_number": session["phase_number"],
        "questions_answered": len(session.get("asked_question_ids", [])),
        "triad_locked": session.get("triad_locked"),
        "triad_percentages": calculate_triad_percentages(session),
        "core_type_locked": session.get("core_type_locked"),
        "created_at": created_at.isoformat() if hasattr(created_at, 'isoformat') else str(created_at),
        "updated_at": updated_at.isoformat() if hasattr(updated_at, 'isoformat') else str(updated_at),
    }

async def resume_v3_assessment_async(session_id: str) -> dict:
    """Resume an existing V3 assessment session."""
    session = await get_v3_session_async(session_id)
    if not session:
        return {"error": "Session not found or expired", "can_resume": False}
    
    # Get next question based on current phase
    if session["phase"] == Phase.TRIAD.value:
        next_question = get_next_phase1_question(session)
        if not next_question:
            # All Phase 1 questions answered, trigger completion check
            return await handle_phase1_completion_async(session)
        
        answered_count = len(session.get("asked_question_ids", []))
        
        return {
            "can_resume": True,
            "session_id": session["session_id"],
            "phase": session["phase"],
            "phase_number": session["phase_number"],
            "phase_label": "Discovering your triad...",
            "question": format_question_for_api(next_question),
            "progress": {
                "current": answered_count + 1,
                "estimated_total": 45,
                "section": "Testing your core center...",
                "confidence_hint": get_confidence_hint(session),
            },
        }
    
    return {"can_resume": False, "message": "Phase not yet implemented"}


# Legacy sync function aliases (for backward compatibility in exports)
def start_v3_assessment(user_id: str) -> dict:
    """DEPRECATED: Use start_v3_assessment_async instead."""
    raise NotImplementedError("Use start_v3_assessment_async - called from async endpoint")

def submit_v3_answer(session_id: str, question_id: str, response_value: int) -> dict:
    """DEPRECATED: Use submit_v3_answer_async instead."""
    raise NotImplementedError("Use submit_v3_answer_async - called from async endpoint")

def get_v3_session_status(session_id: str) -> dict:
    """DEPRECATED: Use get_v3_session_status_async instead."""
    raise NotImplementedError("Use get_v3_session_status_async - called from async endpoint")

def resume_v3_assessment(session_id: str) -> dict:
    """DEPRECATED: Use resume_v3_assessment_async instead."""
    raise NotImplementedError("Use resume_v3_assessment_async - called from async endpoint")

# =============================================================================
# PHASE 4 SCORING AND COMPLETION
# =============================================================================

def score_phase4_answer(session: dict, question_id: str, response_value: int) -> dict:
    """
    Score a Phase 4 (Validation) answer.
    
    VAL-1: User's selection of which type description resonates most
    VAL-2: User's confidence in the calculated result (1-5)
    """
    question = QUESTION_BY_ID.get(question_id)
    if not question:
        return session
    
    if question_id == "VAL-1":
        # User selected a type as most resonant
        session["user_validation_type"] = response_value
    elif question_id == "VAL-2":
        # User rated confidence in result
        session["user_validation_score"] = response_value
    
    return session

async def handle_phase4_completion_async(session: dict) -> dict:
    """Handle Phase 4 (Validation) completion logic."""
    
    val_1_answered = "VAL-1" in session.get("answers", {})
    val_2_answered = "VAL-2" in session.get("answers", {})
    
    # Check if VAL-1 answered but not VAL-2
    if val_1_answered and not val_2_answered:
        # Ask the confirmation question
        return {
            "status": "continue",
            "session_id": session["session_id"],
            "phase": Phase.VALIDATION.value,
            "phase_number": 4,
            "phase_label": "Final validation...",
            "question": {
                "id": "VAL-2",
                "phase": 4,
                "type": "validation_confirm",
                "question": "Looking at your calculated result, does this feel accurate to your core self?",
                "options": [
                    {"value": 5, "text": "Yes, this is definitely me"},
                    {"value": 4, "text": "Mostly yes, with some reservations"},
                    {"value": 3, "text": "Unsure—could be me or not"},
                    {"value": 2, "text": "Mostly no—something feels off"},
                    {"value": 1, "text": "No, this doesn't feel like me at all"},
                ],
            },
            "progress": {
                "current": len(session.get("asked_question_ids", [])) + 1,
                "estimated_total": len(session.get("asked_question_ids", [])) + 1,
                "section": "Validating your type...",
                "confidence_hint": "Your input helps ensure accuracy.",
            },
        }
    
    # Both questions answered - calculate final result with adjustments
    if val_1_answered and val_2_answered:
        user_type = session.get("user_validation_type")
        user_score = session.get("user_validation_score", 3)
        core_type = session.get("core_type_locked")
        
        # Calculate confidence adjustment
        confidence_adjustment = 0
        retest_suggestion = None
        
        if user_type == core_type:
            # User validated the calculated type
            if user_score >= 4:
                confidence_adjustment = VALIDATION_CONFIDENCE_BOOST
            elif user_score <= 2:
                # User says it doesn't feel right despite matching
                confidence_adjustment = VALIDATION_CONFIDENCE_PENALTY // 2
                retest_suggestion = "Consider retaking when not under stress for more clarity."
        else:
            # User selected a different type as more resonant
            confidence_adjustment = VALIDATION_CONFIDENCE_PENALTY
            retest_suggestion = "Your validation suggests a different type. Consider retaking when not under stress."
        
        session["validation_adjustment"] = confidence_adjustment
        
        # Build final result with adjustments
        final_result = build_final_result(session)
        
        # Apply validation adjustment to confidence
        original_confidence = final_result.get("confidence_percentage", 50)
        adjusted_confidence = max(10, min(100, original_confidence + confidence_adjustment))
        final_result["confidence_percentage"] = adjusted_confidence
        final_result["validation_adjustment"] = confidence_adjustment
        
        if retest_suggestion:
            final_result["retest_suggestion"] = retest_suggestion
        
        if session.get("stress_warning"):
            final_result["stress_warning"] = session["stress_warning"]
        
        # Update session to done
        session["phase"] = Phase.DONE.value
        session["final_result"] = final_result
        
        await update_v3_session_async(session["session_id"], {
            "phase": Phase.DONE.value,
            "user_validation_type": user_type,
            "user_validation_score": user_score,
            "validation_adjustment": confidence_adjustment,
            "final_result": final_result,
            "answers": session["answers"],
            "asked_question_ids": session["asked_question_ids"],
        })
        
        return {
            "status": "done",
            "phase_completed": 4,
            "final_result": final_result,
            "validation_applied": True,
            "message": f"Assessment complete! You are a {final_result['full_type_string']}",
        }
    
    # Should not reach here, but handle gracefully
    return {"status": "error", "message": "Validation phase incomplete"}

async def validate_v3_result_async(session_id: str, user_selected_type: int, confidence_score: int) -> dict:
    """
    API endpoint handler for POST /api/enneagram/v3/validate
    
    Allows user to validate their result directly without going through the question flow.
    
    Args:
        session_id: The assessment session ID
        user_selected_type: The type the user feels most represents them (1-9)
        confidence_score: How confident they are in the calculated result (1-5)
    
    Returns:
        Adjusted final result with validation applied
    """
    session = await get_v3_session_async(session_id)
    if not session:
        raise ValueError("Session not found or expired")
    
    if session["phase"] not in [Phase.VALIDATION.value, Phase.DONE.value]:
        raise ValueError("Session not ready for validation - complete Phase 3 first")
    
    # Apply validation
    session["user_validation_type"] = user_selected_type
    session["user_validation_score"] = confidence_score
    session["answers"]["VAL-1"] = user_selected_type
    session["answers"]["VAL-2"] = confidence_score
    
    core_type = session.get("core_type_locked")
    
    # Calculate confidence adjustment
    confidence_adjustment = 0
    retest_suggestion = None
    
    if user_selected_type == core_type:
        if confidence_score >= 4:
            confidence_adjustment = VALIDATION_CONFIDENCE_BOOST
        elif confidence_score <= 2:
            confidence_adjustment = VALIDATION_CONFIDENCE_PENALTY // 2
            retest_suggestion = "Consider retaking when not under stress for more clarity."
    else:
        confidence_adjustment = VALIDATION_CONFIDENCE_PENALTY
        retest_suggestion = "Your validation suggests a different type. Consider retaking when not under stress."
    
    session["validation_adjustment"] = confidence_adjustment
    
    # Build final result with adjustments
    final_result = build_final_result(session)
    
    original_confidence = final_result.get("confidence_percentage", 50)
    adjusted_confidence = max(10, min(100, original_confidence + confidence_adjustment))
    final_result["confidence_percentage"] = adjusted_confidence
    final_result["validation_adjustment"] = confidence_adjustment
    
    if retest_suggestion:
        final_result["retest_suggestion"] = retest_suggestion
    
    if session.get("stress_warning"):
        final_result["stress_warning"] = session["stress_warning"]
    
    # Update session
    session["phase"] = Phase.DONE.value
    session["final_result"] = final_result
    
    await update_v3_session_async(session_id, {
        "phase": Phase.DONE.value,
        "user_validation_type": user_selected_type,
        "user_validation_score": confidence_score,
        "validation_adjustment": confidence_adjustment,
        "final_result": final_result,
        "answers": session["answers"],
    })
    
    return {
        "status": "done",
        "validation_applied": True,
        "final_result": final_result,
        "message": f"Validation applied. You are a {final_result['full_type_string']}",
    }

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def format_question_for_api(question: dict) -> dict:
    """Format a question for API response."""
    return {
        "id": question["id"],
        "phase": question["phase"],
        "type": question["type"],
        "question": question["question"],
        "options": question["options"],
    }

def get_confidence_hint(session: dict) -> str:
    """Get a hint about current confidence level."""
    percentages = calculate_triad_percentages(session)
    sorted_triads = sorted(percentages.items(), key=lambda x: x[1], reverse=True)
    
    if len(sorted_triads) < 2:
        return "Just getting started..."
    
    top_pct, second_pct = sorted_triads[0][1], sorted_triads[1][1]
    gap = top_pct - second_pct
    
    if gap > 20:
        return "A clear pattern is emerging..."
    elif gap > 10:
        return "We're getting a clearer picture..."
    else:
        return "Still gathering your responses..."

# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "start_v3_assessment",
    "submit_v3_answer",
    "get_v3_session_status",
    "resume_v3_assessment",
    "validate_v3_result_async",
    "Phase",
    "Triad",
    "TRIAD_TYPES",
    "TYPE_DESCRIPTIONS",
]
