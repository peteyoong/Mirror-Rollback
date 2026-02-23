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
TRIAD_CONFIDENCE_MIN = 40  # If confidence < 40%, add clarifying questions
TRIAD_MIN_QUESTIONS = 15  # Minimum questions before allowing early lock

# Core type thresholds (Phase 2)
CORE_TYPE_LOCK_THRESHOLD = 50  # Lock if top type >= 50%
CORE_TYPE_CONFIDENCE_THRESHOLD = 70  # High confidence threshold for early lock
CORE_TYPE_MIN_QUESTIONS = 8  # Minimum questions before allowing early type lock

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

# Placeholder for Shame and Anger triad questions (to be implemented)
PHASE2_SHAME_QUESTIONS = []  # Types 2, 3, 4
PHASE2_ANGER_QUESTIONS = []  # Types 8, 9, 1

# Combine all Phase 2 questions
PHASE2_QUESTIONS = PHASE2_FEAR_QUESTIONS + PHASE2_SHAME_QUESTIONS + PHASE2_ANGER_QUESTIONS

# Build question lookup for all phases
QUESTION_BY_ID = {q["id"]: q for q in PHASE1_QUESTIONS}
QUESTION_BY_ID.update({q["id"]: q for q in PHASE2_QUESTIONS})

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
    """
    question = QUESTION_BY_ID.get(question_id)
    if not question:
        raise ValueError(f"Unknown question ID: {question_id}")
    
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
    - Top triad >= TRIAD_LOCK_THRESHOLD (45%)
    
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
    
    # Check if we can lock
    if top_pct >= TRIAD_LOCK_THRESHOLD:
        return True, top_triad, confidence
    
    return False, None, confidence

def get_next_phase1_question(session: dict) -> Optional[dict]:
    """Get the next Phase 1 question to ask."""
    asked = set(session["asked_question_ids"])
    
    for q in PHASE1_QUESTIONS:
        if q["id"] not in asked:
            return q
    
    return None

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
        response_value: The selected option value (1-5)
    
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
    
    # Check phase completion
    if session["phase"] == Phase.TRIAD.value:
        return await handle_phase1_completion_async(session)
    
    # For now, return done if not in Phase 1
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
        
        # Update session in MongoDB
        await update_v3_session_async(session["session_id"], {
            "triad_locked": locked_triad,
            "triad_confidence": confidence,
            "phase": Phase.CORE.value,
            "phase_number": 2,
            "triad_scores": session["triad_scores"],
            "answers": session["answers"],
            "asked_question_ids": session["asked_question_ids"],
        })
        
        # Return Phase 1 complete result (Phase 2 not yet implemented)
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
            "message": f"Triad locked: {locked_triad.title()} ({confidence:.0f}% confidence). Phase 2 coming soon.",
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
    "Phase",
    "Triad",
    "TRIAD_TYPES",
]
