"""
Enneagram Deep Assessment Engine for Project Mirror
====================================================

A single-sitting (20-30 min) Enneagram assessment that identifies:
- Core type (1-9)
- Wing (adjacent type)
- Instinctual stacking (sp/so/sx)

Key Principles:
- User answers ALWAYS determine type (hidden validation never overrides)
- Hidden validation (HD/Astro) only adjusts confidence or triggers more questions
- Deterministic question bank with scoring (no LLM-generated scoring questions)
- Non-prescriptive Mirror language

Stage Flow:
1. CENTER (12 items) -> Determine Head/Heart/Gut
2. CORE (18 items for detected center) -> Narrow to top types
3. DIFFERENTIATORS (up to 6, conditional) -> Separate close types
4. WING (8 items) -> Determine wing preference
5. INSTINCT (8 items) -> Determine instinctual stacking
6. CONSISTENCY (6 items) -> Validate reliability
"""

import uuid
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import math
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTS
# =============================================================================

SESSION_TTL_SECONDS = 2 * 60 * 60  # 2 hours
GAP_THRESHOLD = 8  # Points gap below which differentiators are triggered
INST_DELTA_THRESHOLD = 4  # Instinct delta below which secondary is uncertain
COHERENCE_THRESHOLD = 0.35  # Below this, require differentiators regardless of gap
WING_BALANCED_DELTA = 3  # If wing scores within this delta, consider balanced

# =============================================================================
# ENUMS
# =============================================================================

class Stage(str, Enum):
    CENTER = "center"
    CORE = "core"
    DIFF = "diff"
    WING = "wing"
    INSTINCT = "instinct"
    CONSISTENCY = "consistency"
    DONE = "done"

class QuestionFormat(str, Enum):
    LIKERT = "likert"
    FORCED = "forced"

class ConfidenceTier(str, Enum):
    HIGH = "high"
    MODERATE = "moderate"
    EXPLORATORY = "exploratory"

class Reliability(str, Enum):
    STABLE = "stable"
    MIXED = "mixed"
    LOW = "low"

# =============================================================================
# QUESTION BANK
# =============================================================================
# Each question has:
# - id: unique identifier
# - stage: which stage it belongs to
# - prompt: the question text (Mirror language - descriptive, not prescriptive)
# - format: "likert" (1-5 scale) or "forced" (A/B choice)
# - options: for forced format, the choice options
# - scoring: targets and weights for scoring

# -----------------------------------------------------------------------------
# CENTER ITEMS (12 questions)
# Determines Head (5,6,7), Heart (2,3,4), or Gut (8,9,1) center
# -----------------------------------------------------------------------------

CENTER_ITEMS = [
    {
        "id": "C01",
        "stage": "center",
        "prompt": "When facing uncertainty, I tend to analyze the situation thoroughly before acting.",
        "format": "likert",
        "scoring": {"targets": [{"center": "head", "weight": 1}]}
    },
    {
        "id": "C02",
        "stage": "center",
        "prompt": "I often notice how situations affect my sense of connection with others.",
        "format": "likert",
        "scoring": {"targets": [{"center": "heart", "weight": 1}]}
    },
    {
        "id": "C03",
        "stage": "center",
        "prompt": "I have strong gut reactions that I trust to guide my decisions.",
        "format": "likert",
        "scoring": {"targets": [{"center": "gut", "weight": 1}]}
    },
    {
        "id": "C04",
        "stage": "center",
        "prompt": "I spend significant time thinking through possibilities and scenarios.",
        "format": "likert",
        "scoring": {"targets": [{"center": "head", "weight": 1}]}
    },
    {
        "id": "C05",
        "stage": "center",
        "prompt": "How others perceive me matters significantly in how I feel about myself.",
        "format": "likert",
        "scoring": {"targets": [{"center": "heart", "weight": 1}]}
    },
    {
        "id": "C06",
        "stage": "center",
        "prompt": "I tend to act decisively based on what feels right in the moment.",
        "format": "likert",
        "scoring": {"targets": [{"center": "gut", "weight": 1}]}
    },
    {
        "id": "C07",
        "stage": "center",
        "prompt": "When stressed, my mind races with questions and concerns about what might happen.",
        "format": "likert",
        "scoring": {"targets": [{"center": "head", "weight": 1}]}
    },
    {
        "id": "C08",
        "stage": "center",
        "prompt": "I am highly attuned to the emotional atmosphere in a room.",
        "format": "likert",
        "scoring": {"targets": [{"center": "heart", "weight": 1}]}
    },
    {
        "id": "C09",
        "stage": "center",
        "prompt": "I experience frustration or anger more readily than fear or sadness.",
        "format": "likert",
        "scoring": {"targets": [{"center": "gut", "weight": 1}]}
    },
    {
        "id": "C10",
        "stage": "center",
        "prompt": "When something is wrong, which response feels most familiar?",
        "format": "forced",
        "options": {
            "A": "I analyze what went wrong and consider different approaches",
            "B": "I feel concerned about how this affects my relationships",
            "C": "I want to take action to fix or change the situation",
            "allow_both": False,
            "allow_neither": True
        },
        "scoring": {
            "targets": [
                {"choice": "A", "center": "head", "weight": 4},
                {"choice": "B", "center": "heart", "weight": 4},
                {"choice": "C", "center": "gut", "weight": 4}
            ]
        }
    },
    {
        "id": "C11",
        "stage": "center",
        "prompt": "In a crisis, my first instinct is to:",
        "format": "forced",
        "options": {
            "A": "Step back and assess the situation thoroughly",
            "B": "Connect with others and gauge how everyone is feeling",
            "C": "Take charge and do what needs to be done",
            "allow_both": False,
            "allow_neither": True
        },
        "scoring": {
            "targets": [
                {"choice": "A", "center": "head", "weight": 4},
                {"choice": "B", "center": "heart", "weight": 4},
                {"choice": "C", "center": "gut", "weight": 4}
            ]
        }
    },
    {
        "id": "C12",
        "stage": "center",
        "prompt": "The emotion I tend to struggle with most is:",
        "format": "forced",
        "options": {
            "A": "Fear and anxiety about the future",
            "B": "Shame or concern about my worth and image",
            "C": "Anger or frustration about how things are",
            "allow_both": False,
            "allow_neither": True
        },
        "scoring": {
            "targets": [
                {"choice": "A", "center": "head", "weight": 4},
                {"choice": "B", "center": "heart", "weight": 4},
                {"choice": "C", "center": "gut", "weight": 4}
            ]
        }
    }
]

# -----------------------------------------------------------------------------
# CORE TYPE POOLS (18 questions per center, 6 per type)
# -----------------------------------------------------------------------------

CORE_POOLS = {
    "head": [
        # Type 5 questions (6)
        {
            "id": "H5_01",
            "stage": "core",
            "prompt": "I often prefer to observe situations before participating in them.",
            "format": "likert",
            "scoring": {"targets": [{"type": 5, "weight": 1}]}
        },
        {
            "id": "H5_02",
            "stage": "core",
            "prompt": "I feel drained by too much social interaction and need significant time alone to recharge.",
            "format": "likert",
            "scoring": {"targets": [{"type": 5, "weight": 1}]}
        },
        {
            "id": "H5_03",
            "stage": "core",
            "prompt": "Knowledge and competence feel essential to my sense of security.",
            "format": "likert",
            "scoring": {"targets": [{"type": 5, "weight": 1}]}
        },
        {
            "id": "H5_04",
            "stage": "core",
            "prompt": "I tend to detach emotionally to think more clearly about problems.",
            "format": "likert",
            "scoring": {"targets": [{"type": 5, "weight": 1}]}
        },
        {
            "id": "H5_05",
            "stage": "core",
            "prompt": "I guard my time, energy, and resources carefully.",
            "format": "likert",
            "scoring": {"targets": [{"type": 5, "weight": 1}]}
        },
        {
            "id": "H5_06",
            "stage": "core",
            "prompt": "I prefer depth of understanding over breadth of experience.",
            "format": "likert",
            "scoring": {"targets": [{"type": 5, "weight": 1}]}
        },
        # Type 6 questions (6)
        {
            "id": "H6_01",
            "stage": "core",
            "prompt": "I often anticipate what could go wrong in order to prepare for it.",
            "format": "likert",
            "scoring": {"targets": [{"type": 6, "weight": 1}]}
        },
        {
            "id": "H6_02",
            "stage": "core",
            "prompt": "Loyalty and trustworthiness are among my most important values.",
            "format": "likert",
            "scoring": {"targets": [{"type": 6, "weight": 1}]}
        },
        {
            "id": "H6_03",
            "stage": "core",
            "prompt": "I question authority but also seek reliable guidance and support.",
            "format": "likert",
            "scoring": {"targets": [{"type": 6, "weight": 1}]}
        },
        {
            "id": "H6_04",
            "stage": "core",
            "prompt": "I often doubt my own decisions and seek reassurance from others.",
            "format": "likert",
            "scoring": {"targets": [{"type": 6, "weight": 1}]}
        },
        {
            "id": "H6_05",
            "stage": "core",
            "prompt": "I am vigilant about potential threats or dangers in my environment.",
            "format": "likert",
            "scoring": {"targets": [{"type": 6, "weight": 1}]}
        },
        {
            "id": "H6_06",
            "stage": "core",
            "prompt": "I value commitment and show up reliably for the people and causes I believe in.",
            "format": "likert",
            "scoring": {"targets": [{"type": 6, "weight": 1}]}
        },
        # Type 7 questions (6)
        {
            "id": "H7_01",
            "stage": "core",
            "prompt": "I tend to look for the positive possibilities in any situation.",
            "format": "likert",
            "scoring": {"targets": [{"type": 7, "weight": 1}]}
        },
        {
            "id": "H7_02",
            "stage": "core",
            "prompt": "I struggle with commitments that might limit my options or freedom.",
            "format": "likert",
            "scoring": {"targets": [{"type": 7, "weight": 1}]}
        },
        {
            "id": "H7_03",
            "stage": "core",
            "prompt": "I reframe painful experiences quickly, looking for what I can learn or enjoy.",
            "format": "likert",
            "scoring": {"targets": [{"type": 7, "weight": 1}]}
        },
        {
            "id": "H7_04",
            "stage": "core",
            "prompt": "I get excited about new ideas and possibilities, sometimes more than follow-through.",
            "format": "likert",
            "scoring": {"targets": [{"type": 7, "weight": 1}]}
        },
        {
            "id": "H7_05",
            "stage": "core",
            "prompt": "I avoid or minimize feelings of pain, sadness, or limitation.",
            "format": "likert",
            "scoring": {"targets": [{"type": 7, "weight": 1}]}
        },
        {
            "id": "H7_06",
            "stage": "core",
            "prompt": "I am energized by variety, stimulation, and new experiences.",
            "format": "likert",
            "scoring": {"targets": [{"type": 7, "weight": 1}]}
        }
    ],
    "heart": [
        # Type 2 questions (6)
        {
            "id": "HT2_01",
            "stage": "core",
            "prompt": "I often sense what others need before they express it.",
            "format": "likert",
            "scoring": {"targets": [{"type": 2, "weight": 1}]}
        },
        {
            "id": "HT2_02",
            "stage": "core",
            "prompt": "Helping others makes me feel valuable and connected.",
            "format": "likert",
            "scoring": {"targets": [{"type": 2, "weight": 1}]}
        },
        {
            "id": "HT2_03",
            "stage": "core",
            "prompt": "I sometimes feel hurt when my help isn't appreciated or reciprocated.",
            "format": "likert",
            "scoring": {"targets": [{"type": 2, "weight": 1}]}
        },
        {
            "id": "HT2_04",
            "stage": "core",
            "prompt": "I find it easier to identify others' feelings than my own needs.",
            "format": "likert",
            "scoring": {"targets": [{"type": 2, "weight": 1}]}
        },
        {
            "id": "HT2_05",
            "stage": "core",
            "prompt": "I adapt my personality to connect with different people.",
            "format": "likert",
            "scoring": {"targets": [{"type": 2, "weight": 1}]}
        },
        {
            "id": "HT2_06",
            "stage": "core",
            "prompt": "Being needed by others is important to my sense of self-worth.",
            "format": "likert",
            "scoring": {"targets": [{"type": 2, "weight": 1}]}
        },
        # Type 3 questions (6)
        {
            "id": "HT3_01",
            "stage": "core",
            "prompt": "I am driven to achieve and often measure myself by my accomplishments.",
            "format": "likert",
            "scoring": {"targets": [{"type": 3, "weight": 1}]}
        },
        {
            "id": "HT3_02",
            "stage": "core",
            "prompt": "I naturally adapt my presentation to succeed in different contexts.",
            "format": "likert",
            "scoring": {"targets": [{"type": 3, "weight": 1}]}
        },
        {
            "id": "HT3_03",
            "stage": "core",
            "prompt": "Failure or appearing unsuccessful is deeply uncomfortable for me.",
            "format": "likert",
            "scoring": {"targets": [{"type": 3, "weight": 1}]}
        },
        {
            "id": "HT3_04",
            "stage": "core",
            "prompt": "I am efficient and goal-oriented, preferring action over reflection.",
            "format": "likert",
            "scoring": {"targets": [{"type": 3, "weight": 1}]}
        },
        {
            "id": "HT3_05",
            "stage": "core",
            "prompt": "I sometimes lose touch with my genuine feelings in pursuit of success.",
            "format": "likert",
            "scoring": {"targets": [{"type": 3, "weight": 1}]}
        },
        {
            "id": "HT3_06",
            "stage": "core",
            "prompt": "Recognition and admiration from others motivate me significantly.",
            "format": "likert",
            "scoring": {"targets": [{"type": 3, "weight": 1}]}
        },
        # Type 4 questions (6)
        {
            "id": "HT4_01",
            "stage": "core",
            "prompt": "I feel fundamentally different from others in ways that are hard to explain.",
            "format": "likert",
            "scoring": {"targets": [{"type": 4, "weight": 1}]}
        },
        {
            "id": "HT4_02",
            "stage": "core",
            "prompt": "Authenticity and depth are more important to me than fitting in.",
            "format": "likert",
            "scoring": {"targets": [{"type": 4, "weight": 1}]}
        },
        {
            "id": "HT4_03",
            "stage": "core",
            "prompt": "I am drawn to what's missing or unavailable rather than what's present.",
            "format": "likert",
            "scoring": {"targets": [{"type": 4, "weight": 1}]}
        },
        {
            "id": "HT4_04",
            "stage": "core",
            "prompt": "Melancholy and longing are familiar emotional states for me.",
            "format": "likert",
            "scoring": {"targets": [{"type": 4, "weight": 1}]}
        },
        {
            "id": "HT4_05",
            "stage": "core",
            "prompt": "I express my individuality through creative or aesthetic choices.",
            "format": "likert",
            "scoring": {"targets": [{"type": 4, "weight": 1}]}
        },
        {
            "id": "HT4_06",
            "stage": "core",
            "prompt": "I sometimes envy what others seem to have that I feel I lack.",
            "format": "likert",
            "scoring": {"targets": [{"type": 4, "weight": 1}]}
        }
    ],
    "gut": [
        # Type 8 questions (6)
        {
            "id": "G8_01",
            "stage": "core",
            "prompt": "I naturally take charge in situations that need leadership.",
            "format": "likert",
            "scoring": {"targets": [{"type": 8, "weight": 1}]}
        },
        {
            "id": "G8_02",
            "stage": "core",
            "prompt": "I value directness and dislike when people are indirect or manipulative.",
            "format": "likert",
            "scoring": {"targets": [{"type": 8, "weight": 1}]}
        },
        {
            "id": "G8_03",
            "stage": "core",
            "prompt": "I protect those I care about and stand up against injustice.",
            "format": "likert",
            "scoring": {"targets": [{"type": 8, "weight": 1}]}
        },
        {
            "id": "G8_04",
            "stage": "core",
            "prompt": "Showing vulnerability feels risky and uncomfortable to me.",
            "format": "likert",
            "scoring": {"targets": [{"type": 8, "weight": 1}]}
        },
        {
            "id": "G8_05",
            "stage": "core",
            "prompt": "I have strong opinions and express them confidently.",
            "format": "likert",
            "scoring": {"targets": [{"type": 8, "weight": 1}]}
        },
        {
            "id": "G8_06",
            "stage": "core",
            "prompt": "Being controlled or dominated by others is intolerable to me.",
            "format": "likert",
            "scoring": {"targets": [{"type": 8, "weight": 1}]}
        },
        # Type 9 questions (6)
        {
            "id": "G9_01",
            "stage": "core",
            "prompt": "I tend to go along with others to maintain harmony and avoid conflict.",
            "format": "likert",
            "scoring": {"targets": [{"type": 9, "weight": 1}]}
        },
        {
            "id": "G9_02",
            "stage": "core",
            "prompt": "I can see and appreciate multiple perspectives, even opposing ones.",
            "format": "likert",
            "scoring": {"targets": [{"type": 9, "weight": 1}]}
        },
        {
            "id": "G9_03",
            "stage": "core",
            "prompt": "I sometimes lose touch with my own priorities while attending to others.",
            "format": "likert",
            "scoring": {"targets": [{"type": 9, "weight": 1}]}
        },
        {
            "id": "G9_04",
            "stage": "core",
            "prompt": "I prefer routine and comfort over disruption and change.",
            "format": "likert",
            "scoring": {"targets": [{"type": 9, "weight": 1}]}
        },
        {
            "id": "G9_05",
            "stage": "core",
            "prompt": "My anger tends to come out indirectly, as stubbornness or passive resistance.",
            "format": "likert",
            "scoring": {"targets": [{"type": 9, "weight": 1}]}
        },
        {
            "id": "G9_06",
            "stage": "core",
            "prompt": "I sometimes numb out or distract myself to avoid uncomfortable feelings.",
            "format": "likert",
            "scoring": {"targets": [{"type": 9, "weight": 1}]}
        },
        # Type 1 questions (6)
        {
            "id": "G1_01",
            "stage": "core",
            "prompt": "I have a strong sense of right and wrong that guides my actions.",
            "format": "likert",
            "scoring": {"targets": [{"type": 1, "weight": 1}]}
        },
        {
            "id": "G1_02",
            "stage": "core",
            "prompt": "I notice errors and imperfections that others often miss.",
            "format": "likert",
            "scoring": {"targets": [{"type": 1, "weight": 1}]}
        },
        {
            "id": "G1_03",
            "stage": "core",
            "prompt": "I am harder on myself than others typically are on me.",
            "format": "likert",
            "scoring": {"targets": [{"type": 1, "weight": 1}]}
        },
        {
            "id": "G1_04",
            "stage": "core",
            "prompt": "I feel responsible for improving myself and the world around me.",
            "format": "likert",
            "scoring": {"targets": [{"type": 1, "weight": 1}]}
        },
        {
            "id": "G1_05",
            "stage": "core",
            "prompt": "I suppress my anger because expressing it feels wrong or dangerous.",
            "format": "likert",
            "scoring": {"targets": [{"type": 1, "weight": 1}]}
        },
        {
            "id": "G1_06",
            "stage": "core",
            "prompt": "I hold myself to high standards and feel frustrated when I fall short.",
            "format": "likert",
            "scoring": {"targets": [{"type": 1, "weight": 1}]}
        }
    ]
}

# -----------------------------------------------------------------------------
# DIFFERENTIATORS (9 questions for separating close types)
# -----------------------------------------------------------------------------

DIFFERENTIATORS = [
    # 5 vs 6 differentiator
    {
        "id": "D_5v6_01",
        "stage": "diff",
        "prompt": "When facing uncertainty, I:",
        "format": "forced",
        "options": {
            "A": "Withdraw to gather more information and understand the situation",
            "B": "Seek support from trusted people or systems while remaining vigilant",
            "allow_both": True,
            "allow_neither": True
        },
        "scoring": {
            "targets": [
                {"choice": "A", "type": 5, "weight": 4},
                {"choice": "B", "type": 6, "weight": 4}
            ]
        },
        "separates": [5, 6]
    },
    # 6 vs 7 differentiator
    {
        "id": "D_6v7_01",
        "stage": "diff",
        "prompt": "My relationship with fear is:",
        "format": "forced",
        "options": {
            "A": "I face it head-on, preparing for potential problems",
            "B": "I avoid or reframe it, focusing on positive possibilities",
            "allow_both": True,
            "allow_neither": True
        },
        "scoring": {
            "targets": [
                {"choice": "A", "type": 6, "weight": 4},
                {"choice": "B", "type": 7, "weight": 4}
            ]
        },
        "separates": [6, 7]
    },
    # 2 vs 3 differentiator
    {
        "id": "D_2v3_01",
        "stage": "diff",
        "prompt": "What drives my actions more:",
        "format": "forced",
        "options": {
            "A": "Being needed and appreciated by others",
            "B": "Being successful and admired for achievements",
            "allow_both": True,
            "allow_neither": True
        },
        "scoring": {
            "targets": [
                {"choice": "A", "type": 2, "weight": 4},
                {"choice": "B", "type": 3, "weight": 4}
            ]
        },
        "separates": [2, 3]
    },
    # 3 vs 4 differentiator
    {
        "id": "D_3v4_01",
        "stage": "diff",
        "prompt": "In terms of identity:",
        "format": "forced",
        "options": {
            "A": "I adapt to succeed in different contexts",
            "B": "I emphasize what makes me unique and different",
            "allow_both": True,
            "allow_neither": True
        },
        "scoring": {
            "targets": [
                {"choice": "A", "type": 3, "weight": 4},
                {"choice": "B", "type": 4, "weight": 4}
            ]
        },
        "separates": [3, 4]
    },
    # 8 vs 9 differentiator
    {
        "id": "D_8v9_01",
        "stage": "diff",
        "prompt": "When conflict arises:",
        "format": "forced",
        "options": {
            "A": "I confront it directly, even if it creates tension",
            "B": "I try to minimize it and restore peace",
            "allow_both": True,
            "allow_neither": True
        },
        "scoring": {
            "targets": [
                {"choice": "A", "type": 8, "weight": 4},
                {"choice": "B", "type": 9, "weight": 4}
            ]
        },
        "separates": [8, 9]
    },
    # 9 vs 1 differentiator
    {
        "id": "D_9v1_01",
        "stage": "diff",
        "prompt": "My relationship with anger is:",
        "format": "forced",
        "options": {
            "A": "I tend to suppress it and avoid confrontation",
            "B": "I feel it as resentment when standards aren't met",
            "allow_both": True,
            "allow_neither": True
        },
        "scoring": {
            "targets": [
                {"choice": "A", "type": 9, "weight": 4},
                {"choice": "B", "type": 1, "weight": 4}
            ]
        },
        "separates": [9, 1]
    },
    # 1 vs 8 differentiator
    {
        "id": "D_1v8_01",
        "stage": "diff",
        "prompt": "I assert myself because:",
        "format": "forced",
        "options": {
            "A": "It's the right thing to do - principles matter",
            "B": "I refuse to be controlled or dominated",
            "allow_both": True,
            "allow_neither": True
        },
        "scoring": {
            "targets": [
                {"choice": "A", "type": 1, "weight": 4},
                {"choice": "B", "type": 8, "weight": 4}
            ]
        },
        "separates": [1, 8]
    },
    # 4 vs 5 differentiator
    {
        "id": "D_4v5_01",
        "stage": "diff",
        "prompt": "I withdraw because:",
        "format": "forced",
        "options": {
            "A": "I feel misunderstood and need to process my emotions",
            "B": "I need to conserve energy and think independently",
            "allow_both": True,
            "allow_neither": True
        },
        "scoring": {
            "targets": [
                {"choice": "A", "type": 4, "weight": 4},
                {"choice": "B", "type": 5, "weight": 4}
            ]
        },
        "separates": [4, 5]
    },
    # 2 vs 9 differentiator (common mistype)
    {
        "id": "D_2v9_01",
        "stage": "diff",
        "prompt": "I focus on others because:",
        "format": "forced",
        "options": {
            "A": "I want to be important and needed in their lives",
            "B": "It's easier than focusing on my own priorities",
            "allow_both": True,
            "allow_neither": True
        },
        "scoring": {
            "targets": [
                {"choice": "A", "type": 2, "weight": 4},
                {"choice": "B", "type": 9, "weight": 4}
            ]
        },
        "separates": [2, 9]
    }
]

# -----------------------------------------------------------------------------
# WING POOLS (12 questions per type, ask 8)
# -----------------------------------------------------------------------------

def _generate_wing_items(type_num: int, left_wing: int, right_wing: int) -> List[dict]:
    """Generate wing questions for a given type."""
    # Template questions that compare wing directions
    base_prompts = [
        ("When making decisions, I lean more toward {left_trait} than {right_trait}.", "left"),
        ("In groups, I tend to be more {right_trait} than {left_trait}.", "right"),
        ("My approach to problems is more {left_trait}.", "left"),
        ("I relate to others in a more {right_trait} way.", "right"),
        ("My energy style is more {left_trait} than {right_trait}.", "left"),
        ("I express myself in a more {right_trait} manner.", "right"),
        ("Under stress, I become more {left_trait}.", "left"),
        ("In my free time, I am more {right_trait}.", "right"),
        ("My thinking style is more {left_trait}.", "left"),
        ("My emotional expression is more {right_trait}.", "right"),
        ("I handle conflict in a more {left_trait} way.", "left"),
        ("My social style is more {right_trait}.", "right"),
    ]
    
    # Wing trait descriptions
    wing_traits = {
        1: {"trait": "principled and self-controlled", "short": "principled"},
        2: {"trait": "caring and people-oriented", "short": "warm"},
        3: {"trait": "driven and image-conscious", "short": "ambitious"},
        4: {"trait": "introspective and individualistic", "short": "introspective"},
        5: {"trait": "analytical and detached", "short": "analytical"},
        6: {"trait": "loyal and security-focused", "short": "cautious"},
        7: {"trait": "enthusiastic and spontaneous", "short": "spontaneous"},
        8: {"trait": "assertive and confrontational", "short": "assertive"},
        9: {"trait": "easygoing and harmonious", "short": "peaceful"},
    }
    
    items = []
    for i, (template, direction) in enumerate(base_prompts):
        left_trait = wing_traits[left_wing]["short"]
        right_trait = wing_traits[right_wing]["short"]
        
        prompt = template.format(left_trait=left_trait, right_trait=right_trait)
        
        items.append({
            "id": f"W{type_num}_{i+1:02d}",
            "stage": "wing",
            "prompt": prompt,
            "format": "likert",
            "scoring": {
                "targets": [
                    {"wing": "left" if direction == "left" else "right", "weight": 1}
                ]
            }
        })
    
    return items

# Pre-generate wing pools for all types
WING_POOLS = {
    1: _generate_wing_items(1, 9, 2),  # 1w9 vs 1w2
    2: _generate_wing_items(2, 1, 3),  # 2w1 vs 2w3
    3: _generate_wing_items(3, 2, 4),  # 3w2 vs 3w4
    4: _generate_wing_items(4, 3, 5),  # 4w3 vs 4w5
    5: _generate_wing_items(5, 4, 6),  # 5w4 vs 5w6
    6: _generate_wing_items(6, 5, 7),  # 6w5 vs 6w7
    7: _generate_wing_items(7, 6, 8),  # 7w6 vs 7w8
    8: _generate_wing_items(8, 7, 9),  # 8w7 vs 8w9
    9: _generate_wing_items(9, 8, 1),  # 9w8 vs 9w1
}

# Wing adjacency map
WING_ADJACENTS = {
    1: (9, 2),
    2: (1, 3),
    3: (2, 4),
    4: (3, 5),
    5: (4, 6),
    6: (5, 7),
    7: (6, 8),
    8: (7, 9),
    9: (8, 1),
}

# -----------------------------------------------------------------------------
# INSTINCT POOL (12 questions, ask 8)
# -----------------------------------------------------------------------------

INSTINCT_POOL = [
    {
        "id": "I_01",
        "stage": "instinct",
        "prompt": "I prioritize physical comfort, health, and having enough resources.",
        "format": "likert",
        "scoring": {"targets": [{"instinct": "sp", "weight": 1}]}
    },
    {
        "id": "I_02",
        "stage": "instinct",
        "prompt": "I focus on my place within groups and how I contribute to community.",
        "format": "likert",
        "scoring": {"targets": [{"instinct": "so", "weight": 1}]}
    },
    {
        "id": "I_03",
        "stage": "instinct",
        "prompt": "I seek intense, intimate connections with specific individuals.",
        "format": "likert",
        "scoring": {"targets": [{"instinct": "sx", "weight": 1}]}
    },
    {
        "id": "I_04",
        "stage": "instinct",
        "prompt": "Security and stability in my environment matter deeply to me.",
        "format": "likert",
        "scoring": {"targets": [{"instinct": "sp", "weight": 1}]}
    },
    {
        "id": "I_05",
        "stage": "instinct",
        "prompt": "Social status and my role in the broader community are important.",
        "format": "likert",
        "scoring": {"targets": [{"instinct": "so", "weight": 1}]}
    },
    {
        "id": "I_06",
        "stage": "instinct",
        "prompt": "I am drawn to experiences of chemistry and attraction.",
        "format": "likert",
        "scoring": {"targets": [{"instinct": "sx", "weight": 1}]}
    },
    {
        "id": "I_07",
        "stage": "instinct",
        "prompt": "I am most concerned with self-preservation and practical needs.",
        "format": "likert",
        "scoring": {"targets": [{"instinct": "sp", "weight": 1}]}
    },
    {
        "id": "I_08",
        "stage": "instinct",
        "prompt": "I think about social dynamics and group belonging frequently.",
        "format": "likert",
        "scoring": {"targets": [{"instinct": "so", "weight": 1}]}
    },
    {
        "id": "I_09",
        "stage": "instinct",
        "prompt": "Deep one-on-one bonds are more important than broad social networks.",
        "format": "likert",
        "scoring": {"targets": [{"instinct": "sx", "weight": 1}]}
    },
    {
        "id": "I_10",
        "stage": "instinct",
        "prompt": "What energy focus feels most natural to you?",
        "format": "forced",
        "options": {
            "A": "Managing my personal well-being and resources",
            "B": "Navigating social hierarchies and community roles",
            "C": "Creating intense connections with select individuals",
            "allow_both": False,
            "allow_neither": True
        },
        "scoring": {
            "targets": [
                {"choice": "A", "instinct": "sp", "weight": 4},
                {"choice": "B", "instinct": "so", "weight": 4},
                {"choice": "C", "instinct": "sx", "weight": 4}
            ]
        }
    },
    {
        "id": "I_11",
        "stage": "instinct",
        "prompt": "What matters most in your relationships?",
        "format": "forced",
        "options": {
            "A": "Practical support and shared stability",
            "B": "Shared values and social connection",
            "C": "Depth, intensity, and mutual transformation",
            "allow_both": False,
            "allow_neither": True
        },
        "scoring": {
            "targets": [
                {"choice": "A", "instinct": "sp", "weight": 4},
                {"choice": "B", "instinct": "so", "weight": 4},
                {"choice": "C", "instinct": "sx", "weight": 4}
            ]
        }
    },
    {
        "id": "I_12",
        "stage": "instinct",
        "prompt": "What do you fear losing most?",
        "format": "forced",
        "options": {
            "A": "Security, health, or resources",
            "B": "Social standing or group belonging",
            "C": "A deep connection or sense of aliveness",
            "allow_both": False,
            "allow_neither": True
        },
        "scoring": {
            "targets": [
                {"choice": "A", "instinct": "sp", "weight": 4},
                {"choice": "B", "instinct": "so", "weight": 4},
                {"choice": "C", "instinct": "sx", "weight": 4}
            ]
        }
    }
]

# -----------------------------------------------------------------------------
# CONSISTENCY POOL (4 questions: 2 duplicates, 2 contradictions)
# NOTE: Removed explicit "select Agree" and "captures patterns" integrity checks
# Reliability is now tracked via silent checks (response time, straightlining)
# -----------------------------------------------------------------------------

CONSISTENCY_POOL = [
    # Duplicate checks (should match earlier center answers)
    {
        "id": "CON_01",
        "stage": "consistency",
        "prompt": "I often think through multiple scenarios before acting.",
        "format": "likert",
        "scoring": {"targets": [{"center": "head", "weight": 1}], "check": "duplicate", "reference": "C01"}
    },
    {
        "id": "CON_02",
        "stage": "consistency",
        "prompt": "I am strongly aware of how situations make me and others feel.",
        "format": "likert",
        "scoring": {"targets": [{"center": "heart", "weight": 1}], "check": "duplicate", "reference": "C02"}
    },
    # Contradiction checks (opposite direction of earlier answers)
    {
        "id": "CON_03",
        "stage": "consistency",
        "prompt": "I rarely analyze situations - I just respond intuitively.",
        "format": "likert",
        "scoring": {"targets": [{"center": "head", "weight": -1}], "check": "contradiction", "reference": "C01"}
    },
    {
        "id": "CON_04",
        "stage": "consistency",
        "prompt": "How others see me doesn't really affect how I feel about myself.",
        "format": "likert",
        "scoring": {"targets": [{"center": "heart", "weight": -1}], "check": "contradiction", "reference": "C05"}
    },
    # NOTE: Removed CON_05 and CON_06 ("select Agree" and "captures patterns" questions)
    # These broke immersion and felt test-like. Reliability is now handled via silent checks:
    # - Response time monitoring (too-fast answers reduce confidence)
    # - Straightlining detection (excessive same-answer patterns reduce confidence)
]

# =============================================================================
# SESSION MANAGEMENT
# =============================================================================

# In-memory session store (would use Redis in production)
_sessions: Dict[str, dict] = {}

def _create_session(user_id: str) -> dict:
    """Create a new assessment session."""
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    session = {
        "session_id": session_id,
        "user_id": user_id,
        "stage": Stage.CENTER.value,
        "asked_question_ids": [],
        "answers": {},
        "center_scores": {"head": 0, "heart": 0, "gut": 0},
        "type_scores": {i: 0 for i in range(1, 10)},
        "wing_scores": {"left": 0, "right": 0},
        "instinct_scores": {"sp": 0, "so": 0, "sx": 0},
        "consistency_score": 1.0,
        "coherence_score": 1.0,
        "neither_count": 0,  # Track neither responses for confidence penalty
        # Silent reliability tracking (no user-facing questions)
        "response_times": [],  # Track per-question response times (seconds)
        "last_question_sent_at": None,  # Timestamp when last question was sent
        "answer_sequence": [],  # Track sequence of likert values for straightlining detection
        "created_at_iso": now,
        "updated_at_iso": now,
        "expires_at": time.time() + SESSION_TTL_SECONDS
    }
    
    _sessions[session_id] = session
    return session

def _get_session(session_id: str) -> Optional[dict]:
    """Get session by ID, checking expiration."""
    session = _sessions.get(session_id)
    if not session:
        return None
    
    # Check expiration
    if time.time() > session.get("expires_at", 0):
        del _sessions[session_id]
        return None
    
    return session

def _update_session(session_id: str, updates: dict) -> Optional[dict]:
    """Update session with new data."""
    session = _get_session(session_id)
    if not session:
        return None
    
    session.update(updates)
    session["updated_at_iso"] = datetime.now(timezone.utc).isoformat()
    _sessions[session_id] = session
    return session

def _cleanup_expired_sessions():
    """Remove expired sessions."""
    current_time = time.time()
    expired = [sid for sid, s in _sessions.items() if current_time > s.get("expires_at", 0)]
    for sid in expired:
        del _sessions[sid]

# =============================================================================
# SCORING FUNCTIONS
# =============================================================================

def score_likert_answer(value: int, scoring: dict, session: dict) -> dict:
    """
    Score a likert answer (1-5 scale).
    Maps 1-5 to 0-4 points and applies to targets.
    """
    points = max(0, value - 1)  # 1->0, 2->1, 3->2, 4->3, 5->4
    
    for target in scoring.get("targets", []):
        weight = target.get("weight", 1)
        actual_points = points * weight
        
        if "center" in target:
            center = target["center"]
            session["center_scores"][center] = session["center_scores"].get(center, 0) + actual_points
        
        if "type" in target:
            type_num = target["type"]
            session["type_scores"][type_num] = session["type_scores"].get(type_num, 0) + actual_points
        
        if "wing" in target:
            wing_dir = target["wing"]
            session["wing_scores"][wing_dir] = session["wing_scores"].get(wing_dir, 0) + actual_points
        
        if "instinct" in target:
            inst = target["instinct"]
            session["instinct_scores"][inst] = session["instinct_scores"].get(inst, 0) + actual_points
    
    return session

def score_forced_answer(choice: str, scoring: dict, session: dict, options: dict) -> dict:
    """
    Score a forced choice answer.
    - "A" => A_target += 4
    - "B" => B_target += 4
    - "both" => A_target += 2, B_target += 2
    - "neither" => no points, increment neither_count
    """
    if choice == "neither":
        session["neither_count"] = session.get("neither_count", 0) + 1
        return session
    
    targets = scoring.get("targets", [])
    
    if choice == "both":
        # Half points to each applicable target
        for target in targets:
            target_choice = target.get("choice")
            if target_choice in ["A", "B"]:
                apply_target_score(target, session, multiplier=0.5)
    else:
        # Full points to matching choice
        for target in targets:
            if target.get("choice") == choice:
                apply_target_score(target, session, multiplier=1.0)
    
    return session

def apply_target_score(target: dict, session: dict, multiplier: float = 1.0):
    """Apply score to the appropriate target in session."""
    weight = target.get("weight", 4) * multiplier
    
    if "center" in target:
        center = target["center"]
        session["center_scores"][center] = session["center_scores"].get(center, 0) + weight
    
    if "type" in target:
        type_num = target["type"]
        session["type_scores"][type_num] = session["type_scores"].get(type_num, 0) + weight
    
    if "wing" in target:
        wing_dir = target["wing"]
        session["wing_scores"][wing_dir] = session["wing_scores"].get(wing_dir, 0) + weight
    
    if "instinct" in target:
        inst = target["instinct"]
        session["instinct_scores"][inst] = session["instinct_scores"].get(inst, 0) + weight

def process_answer(session: dict, question_id: str, answer: dict) -> dict:
    """Process an answer and update session scores."""
    # Check for idempotency
    if question_id in session["answers"]:
        return session  # Already answered, skip
    
    # Find the question
    question = get_question_by_id(question_id)
    if not question:
        raise ValueError(f"Unknown question ID: {question_id}")
    
    # Record the answer
    session["answers"][question_id] = answer
    session["asked_question_ids"].append(question_id)
    
    # Score based on format
    scoring = question.get("scoring", {})
    options = question.get("options", {})
    
    if question["format"] == "likert":
        value = answer.get("value")
        if not isinstance(value, int) or not (1 <= value <= 5):
            raise ValueError("Likert answer must be integer 1-5")
        score_likert_answer(value, scoring, session)
    
    elif question["format"] == "forced":
        choice = answer.get("value")
        valid_choices = ["A", "B"]
        if options.get("C"):
            valid_choices.append("C")
        if options.get("allow_both", False):
            valid_choices.append("both")
        if options.get("allow_neither", False):
            valid_choices.append("neither")
        
        if choice not in valid_choices:
            raise ValueError(f"Invalid forced choice: {choice}")
        score_forced_answer(choice, scoring, session, options)
    
    return session

def get_question_by_id(question_id: str) -> Optional[dict]:
    """Find a question by its ID."""
    # Search all pools
    all_questions = []
    all_questions.extend(CENTER_ITEMS)
    for pool in CORE_POOLS.values():
        all_questions.extend(pool)
    all_questions.extend(DIFFERENTIATORS)
    for pool in WING_POOLS.values():
        all_questions.extend(pool)
    all_questions.extend(INSTINCT_POOL)
    all_questions.extend(CONSISTENCY_POOL)
    
    for q in all_questions:
        if q["id"] == question_id:
            return q
    return None

# =============================================================================
# STAGE FLOW LOGIC
# =============================================================================

def get_dominant_center(center_scores: dict) -> str:
    """Get the center with highest score."""
    return max(center_scores, key=center_scores.get)

def get_top_types(type_scores: dict, n: int = 2) -> List[Tuple[int, int]]:
    """Get top N types by score, returns list of (type, score) tuples."""
    sorted_types = sorted(type_scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_types[:n]

def get_top_type_gap(type_scores: dict) -> Tuple[int, int, int]:
    """Get top type, second type, and gap between them."""
    top = get_top_types(type_scores, 2)
    if len(top) < 2:
        return top[0][0], 0, top[0][1]
    return top[0][0], top[1][0], top[0][1] - top[1][1]

def get_next_question(session: dict) -> Optional[dict]:
    """Determine and return the next question based on current stage."""
    stage = Stage(session["stage"])
    asked = set(session["asked_question_ids"])
    
    if stage == Stage.CENTER:
        # Get next unanswered center item
        for q in CENTER_ITEMS:
            if q["id"] not in asked:
                return q
        # All center items done, advance to core
        session["stage"] = Stage.CORE.value
        return get_next_question(session)
    
    elif stage == Stage.CORE:
        # Determine center and get core questions for that center
        center = get_dominant_center(session["center_scores"])
        pool = CORE_POOLS.get(center, [])
        
        for q in pool:
            if q["id"] not in asked:
                return q
        
        # All core items done, check if differentiators needed
        top_type, second_type, gap = get_top_type_gap(session["type_scores"])
        
        # Check coherence score (will be computed if HD data available)
        coherence = session.get("coherence_score", 1.0)
        
        if gap < GAP_THRESHOLD or coherence < COHERENCE_THRESHOLD:
            session["stage"] = Stage.DIFF.value
            session["_diff_count"] = 0
            session["_top_types"] = (top_type, second_type)
        else:
            session["stage"] = Stage.WING.value
            session["_top_type"] = top_type
        
        return get_next_question(session)
    
    elif stage == Stage.DIFF:
        # Ask up to 6 differentiators that separate top types
        diff_count = session.get("_diff_count", 0)
        top_types = session.get("_top_types", (1, 2))
        
        if diff_count >= 6:
            # Done with differentiators
            top_type, _, _ = get_top_type_gap(session["type_scores"])
            session["stage"] = Stage.WING.value
            session["_top_type"] = top_type
            return get_next_question(session)
        
        # Find relevant differentiator
        for q in DIFFERENTIATORS:
            if q["id"] not in asked:
                separates = set(q.get("separates", []))
                if top_types[0] in separates or top_types[1] in separates:
                    session["_diff_count"] = diff_count + 1
                    return q
        
        # No more relevant differentiators
        top_type, _, _ = get_top_type_gap(session["type_scores"])
        session["stage"] = Stage.WING.value
        session["_top_type"] = top_type
        return get_next_question(session)
    
    elif stage == Stage.WING:
        top_type = session.get("_top_type")
        if not top_type:
            top_type, _, _ = get_top_type_gap(session["type_scores"])
            session["_top_type"] = top_type
        
        pool = WING_POOLS.get(top_type, [])
        wing_asked = sum(1 for q in pool if q["id"] in asked)
        
        if wing_asked >= 8:
            # Done with wing questions
            session["stage"] = Stage.INSTINCT.value
            return get_next_question(session)
        
        for q in pool:
            if q["id"] not in asked:
                return q
        
        # Fallback
        session["stage"] = Stage.INSTINCT.value
        return get_next_question(session)
    
    elif stage == Stage.INSTINCT:
        instinct_asked = sum(1 for q in INSTINCT_POOL if q["id"] in asked)
        
        if instinct_asked >= 8:
            session["stage"] = Stage.CONSISTENCY.value
            return get_next_question(session)
        
        for q in INSTINCT_POOL:
            if q["id"] not in asked:
                return q
        
        session["stage"] = Stage.CONSISTENCY.value
        return get_next_question(session)
    
    elif stage == Stage.CONSISTENCY:
        for q in CONSISTENCY_POOL:
            if q["id"] not in asked:
                return q
        
        # All done
        session["stage"] = Stage.DONE.value
        return None
    
    return None

def get_progress(session: dict) -> dict:
    """Calculate progress information."""
    stage = Stage(session["stage"])
    asked_count = len(session["asked_question_ids"])
    
    # Estimate total questions
    stage_counts = {
        Stage.CENTER: 12,
        Stage.CORE: 12 + 18,
        Stage.DIFF: 12 + 18 + 6,
        Stage.WING: 12 + 18 + 6 + 8,
        Stage.INSTINCT: 12 + 18 + 6 + 8 + 8,
        Stage.CONSISTENCY: 12 + 18 + 6 + 8 + 8 + 6,
        Stage.DONE: 12 + 18 + 6 + 8 + 8 + 6
    }
    
    # Not all stages may run (diff is conditional)
    estimated_total = stage_counts.get(Stage.CONSISTENCY, 58)
    
    return {
        "stage": stage.value,
        "questions_answered": asked_count,
        "estimated_total": estimated_total,
        "estimated_remaining": max(0, estimated_total - asked_count),
        "estimated_minutes_remaining": max(0, (estimated_total - asked_count) * 0.5)  # ~30 sec per question
    }

# =============================================================================
# HIDDEN VALIDATION (COHERENCE SCORING)
# =============================================================================

# Expected signals by type (simplified heuristics)
TYPE_EXPECTED_SIGNALS = {
    1: {"mental_focus": 0.4, "emotional_intensity": 0.3, "assertiveness": 0.7, "harmony_seeking": 0.3, "novelty_drive": 0.2},
    2: {"mental_focus": 0.3, "emotional_intensity": 0.8, "assertiveness": 0.4, "harmony_seeking": 0.7, "novelty_drive": 0.4},
    3: {"mental_focus": 0.5, "emotional_intensity": 0.5, "assertiveness": 0.7, "harmony_seeking": 0.4, "novelty_drive": 0.6},
    4: {"mental_focus": 0.6, "emotional_intensity": 0.9, "assertiveness": 0.3, "harmony_seeking": 0.3, "novelty_drive": 0.5},
    5: {"mental_focus": 0.9, "emotional_intensity": 0.2, "assertiveness": 0.2, "harmony_seeking": 0.4, "novelty_drive": 0.6},
    6: {"mental_focus": 0.8, "emotional_intensity": 0.5, "assertiveness": 0.4, "harmony_seeking": 0.6, "novelty_drive": 0.3},
    7: {"mental_focus": 0.7, "emotional_intensity": 0.4, "assertiveness": 0.6, "harmony_seeking": 0.4, "novelty_drive": 0.9},
    8: {"mental_focus": 0.4, "emotional_intensity": 0.6, "assertiveness": 0.95, "harmony_seeking": 0.1, "novelty_drive": 0.5},
    9: {"mental_focus": 0.4, "emotional_intensity": 0.3, "assertiveness": 0.2, "harmony_seeking": 0.9, "novelty_drive": 0.3},
}

def compute_coherence_score(session: dict, user_computed_data: Optional[dict] = None) -> float:
    """
    Compute coherence score from HD/Astrology data.
    
    This NEVER overrides the type determined by user answers.
    It only adjusts confidence or triggers more questions.
    """
    if not user_computed_data:
        return 1.0  # No data = assume coherent
    
    # Extract signals from computed data
    signals = derive_signals_from_computed_data(user_computed_data)
    if not signals:
        return 1.0
    
    # Get expected signals for top type
    top_type, _, _ = get_top_type_gap(session["type_scores"])
    expected = TYPE_EXPECTED_SIGNALS.get(top_type, {})
    
    if not expected:
        return 1.0
    
    # Compute similarity (simple euclidean distance normalized)
    total_diff = 0
    count = 0
    for key in expected:
        if key in signals:
            diff = abs(expected[key] - signals[key])
            total_diff += diff
            count += 1
    
    if count == 0:
        return 1.0
    
    avg_diff = total_diff / count
    coherence = max(0, 1 - avg_diff)
    
    return round(coherence, 3)

def derive_signals_from_computed_data(computed_data: dict) -> dict:
    """
    Derive simplified signals from HD/Astrology data.
    This is a lightweight heuristic layer, not a full analysis.
    """
    signals = {}
    
    # From Human Design
    hd = computed_data.get("human_design", {})
    if hd:
        hd_type = hd.get("type", "")
        authority = hd.get("authority", "")
        
        # Map HD type to signals
        if "Generator" in hd_type:
            signals["assertiveness"] = 0.5
            signals["mental_focus"] = 0.4
        elif "Projector" in hd_type:
            signals["assertiveness"] = 0.3
            signals["mental_focus"] = 0.7
        elif "Manifestor" in hd_type:
            signals["assertiveness"] = 0.9
            signals["mental_focus"] = 0.4
        elif "Reflector" in hd_type:
            signals["emotional_intensity"] = 0.6
            signals["harmony_seeking"] = 0.7
        
        # Map authority to signals
        if "Emotional" in authority:
            signals["emotional_intensity"] = 0.7
        elif "Splenic" in authority:
            signals["mental_focus"] = 0.6
        elif "Sacral" in authority:
            signals["assertiveness"] = signals.get("assertiveness", 0.5) + 0.1
    
    # From Astrology (sun/moon signs)
    astro = computed_data.get("astrology", {})
    if astro:
        planets = astro.get("planets", {})
        sun = planets.get("Sun", {})
        moon = planets.get("Moon", {})
        
        # Fire signs = assertiveness
        fire_signs = ["Aries", "Leo", "Sagittarius"]
        if sun.get("sign") in fire_signs:
            signals["assertiveness"] = signals.get("assertiveness", 0.5) + 0.15
            signals["novelty_drive"] = signals.get("novelty_drive", 0.5) + 0.1
        
        # Water signs = emotional intensity
        water_signs = ["Cancer", "Scorpio", "Pisces"]
        if moon.get("sign") in water_signs:
            signals["emotional_intensity"] = signals.get("emotional_intensity", 0.5) + 0.15
        
        # Air signs = mental focus
        air_signs = ["Gemini", "Libra", "Aquarius"]
        if sun.get("sign") in air_signs:
            signals["mental_focus"] = signals.get("mental_focus", 0.5) + 0.15
        
        # Earth signs = harmony/stability
        earth_signs = ["Taurus", "Virgo", "Capricorn"]
        if sun.get("sign") in earth_signs:
            signals["harmony_seeking"] = signals.get("harmony_seeking", 0.5) + 0.1
    
    # Clamp all signals to 0-1
    for key in signals:
        signals[key] = max(0, min(1, signals[key]))
    
    return signals

# =============================================================================
# CONSISTENCY SCORING
# =============================================================================

def compute_consistency_score(session: dict) -> Tuple[float, str]:
    """
    Compute consistency score from duplicate/contradiction checks.
    Returns (score, reliability).
    """
    answers = session["answers"]
    
    consistency_checks = []
    
    for q in CONSISTENCY_POOL:
        q_id = q["id"]
        if q_id not in answers:
            continue
        
        check_type = q.get("scoring", {}).get("check")
        answer_val = answers[q_id].get("value", 3)
        
        if check_type == "duplicate":
            ref_id = q["scoring"].get("reference")
            if ref_id and ref_id in answers:
                ref_val = answers[ref_id].get("value", 3)
                # Should be similar (within 1 point)
                diff = abs(answer_val - ref_val)
                consistency_checks.append(1 - (diff / 4))
        
        elif check_type == "contradiction":
            ref_id = q["scoring"].get("reference")
            if ref_id and ref_id in answers:
                ref_val = answers[ref_id].get("value", 3)
                # Should be opposite (sum should be ~6)
                expected_sum = 6
                actual_sum = answer_val + ref_val
                diff = abs(expected_sum - actual_sum)
                consistency_checks.append(1 - (diff / 8))
        
        elif check_type == "integrity":
            expected = q["scoring"].get("expected")
            expected_range = q["scoring"].get("expected_range")
            
            if expected is not None:
                consistency_checks.append(1.0 if answer_val == expected else 0.0)
            elif expected_range is not None:
                low, high = expected_range
                consistency_checks.append(1.0 if low <= answer_val <= high else 0.5)
    
    if not consistency_checks:
        return 1.0, Reliability.STABLE.value
    
    avg_consistency = sum(consistency_checks) / len(consistency_checks)
    
    if avg_consistency >= 0.8:
        reliability = Reliability.STABLE.value
    elif avg_consistency >= 0.5:
        reliability = Reliability.MIXED.value
    else:
        reliability = Reliability.LOW.value
    
    return round(avg_consistency, 3), reliability


# =============================================================================
# SILENT RELIABILITY CHECKS (No user-facing questions)
# =============================================================================

# Minimum response time threshold (seconds) - answers faster than this are suspicious
MIN_RESPONSE_TIME_SECONDS = 1.5

# Maximum ratio of "too fast" answers before confidence penalty kicks in
TOO_FAST_RATIO_THRESHOLD = 0.3

# Straightlining detection: if same answer appears this many times consecutively
STRAIGHTLINE_CONSECUTIVE_THRESHOLD = 5

# Straightlining detection: if same answer appears this % of total answers
STRAIGHTLINE_DOMINANCE_THRESHOLD = 0.7


def compute_response_time_penalty(session: dict) -> float:
    """
    Calculate confidence penalty based on response times.
    Returns a penalty value 0.0 to 0.15 (higher = worse reliability).
    
    Too-fast answers (< MIN_RESPONSE_TIME_SECONDS) suggest random clicking.
    """
    response_times = session.get("response_times", [])
    if len(response_times) < 5:
        return 0.0  # Not enough data
    
    too_fast_count = sum(1 for t in response_times if t < MIN_RESPONSE_TIME_SECONDS)
    too_fast_ratio = too_fast_count / len(response_times)
    
    if too_fast_ratio > TOO_FAST_RATIO_THRESHOLD:
        # Scale penalty based on how many are too fast
        excess = too_fast_ratio - TOO_FAST_RATIO_THRESHOLD
        penalty = min(0.15, excess * 0.3)  # Max 15% penalty
        return round(penalty, 3)
    
    return 0.0


def compute_straightlining_penalty(session: dict) -> float:
    """
    Calculate confidence penalty based on straightlining detection.
    Returns a penalty value 0.0 to 0.15 (higher = worse reliability).
    
    Straightlining = selecting the same answer excessively (random or disengaged).
    """
    answer_sequence = session.get("answer_sequence", [])
    if len(answer_sequence) < 10:
        return 0.0  # Not enough data
    
    # Check for consecutive same answers
    max_consecutive = 1
    current_consecutive = 1
    for i in range(1, len(answer_sequence)):
        if answer_sequence[i] == answer_sequence[i-1]:
            current_consecutive += 1
            max_consecutive = max(max_consecutive, current_consecutive)
        else:
            current_consecutive = 1
    
    # Check for dominance of a single answer value
    from collections import Counter
    counts = Counter(answer_sequence)
    most_common_count = counts.most_common(1)[0][1]
    dominance_ratio = most_common_count / len(answer_sequence)
    
    penalty = 0.0
    
    # Consecutive straightlining penalty
    if max_consecutive >= STRAIGHTLINE_CONSECUTIVE_THRESHOLD:
        penalty += 0.05 * (max_consecutive - STRAIGHTLINE_CONSECUTIVE_THRESHOLD + 1)
    
    # Dominance penalty (using same answer too much)
    if dominance_ratio > STRAIGHTLINE_DOMINANCE_THRESHOLD:
        excess = dominance_ratio - STRAIGHTLINE_DOMINANCE_THRESHOLD
        penalty += excess * 0.3
    
    return round(min(0.15, penalty), 3)


def compute_silent_reliability_score(session: dict) -> tuple[float, dict]:
    """
    Compute overall reliability score from silent checks.
    Returns (score 0.0-1.0, debug_info dict).
    
    Silent checks include:
    - Response time monitoring
    - Straightlining detection
    """
    response_time_penalty = compute_response_time_penalty(session)
    straightlining_penalty = compute_straightlining_penalty(session)
    
    total_penalty = response_time_penalty + straightlining_penalty
    reliability_score = max(0.0, 1.0 - total_penalty)
    
    debug_info = {
        "response_time_penalty": response_time_penalty,
        "straightlining_penalty": straightlining_penalty,
        "total_penalty": round(total_penalty, 3),
        "reliability_score": round(reliability_score, 3),
        "response_times_count": len(session.get("response_times", [])),
        "answer_sequence_length": len(session.get("answer_sequence", []))
    }
    
    return round(reliability_score, 3), debug_info


# =============================================================================
# RESULT COMPUTATION
# =============================================================================

def compute_results(session: dict) -> dict:
    """Compute final assessment results."""
    # Get top type
    top_type, second_type, gap = get_top_type_gap(session["type_scores"])
    
    # Determine wing
    wing_scores = session["wing_scores"]
    left_wing, right_wing = WING_ADJACENTS.get(top_type, (top_type - 1, top_type + 1))
    
    if wing_scores["left"] > wing_scores["right"] + WING_BALANCED_DELTA:
        wing = str(left_wing)
    elif wing_scores["right"] > wing_scores["left"] + WING_BALANCED_DELTA:
        wing = str(right_wing)
    elif wing_scores["left"] > 0 and wing_scores["right"] > 0:
        wing = "balanced"
    else:
        wing = str(left_wing) if wing_scores["left"] >= wing_scores["right"] else str(right_wing)
    
    # Determine instincts
    instinct_scores = session["instinct_scores"]
    sorted_instincts = sorted(instinct_scores.items(), key=lambda x: x[1], reverse=True)
    
    instinct_primary = sorted_instincts[0][0]
    instinct_secondary = None
    
    if len(sorted_instincts) >= 2:
        primary_score = sorted_instincts[0][1]
        secondary_score = sorted_instincts[1][1]
        
        if primary_score - secondary_score < INST_DELTA_THRESHOLD:
            # Too close to determine secondary with confidence
            instinct_secondary = None
        else:
            instinct_secondary = sorted_instincts[1][0]
    
    # Compute confidence
    consistency_score, reliability = compute_consistency_score(session)
    session["consistency_score"] = consistency_score
    
    # Base confidence from multiple factors
    type_gap_factor = min(1.0, gap / 20)  # Max confidence at 20+ point gap
    
    wing_clarity = abs(wing_scores["left"] - wing_scores["right"])
    wing_factor = min(1.0, wing_clarity / 10)
    
    instinct_clarity = sorted_instincts[0][1] - sorted_instincts[1][1] if len(sorted_instincts) >= 2 else 0
    instinct_factor = min(1.0, instinct_clarity / 10)
    
    # Neither penalty
    neither_penalty = min(0.2, session.get("neither_count", 0) * 0.02)
    
    # Silent reliability check (response time + straightlining)
    silent_reliability, silent_debug = compute_silent_reliability_score(session)
    
    # Compute base confidence
    base_confidence = (
        type_gap_factor * 0.4 +
        wing_factor * 0.2 +
        instinct_factor * 0.2 +
        consistency_score * 0.2
    )
    
    # Apply coherence modifier (only reduces, never increases beyond base)
    coherence = session.get("coherence_score", 1.0)
    
    # Apply silent reliability as a multiplier (0.85-1.0 range to avoid harsh penalties)
    reliability_multiplier = 0.85 + 0.15 * silent_reliability
    
    confidence = base_confidence * (0.7 + 0.3 * coherence) * reliability_multiplier - neither_penalty
    confidence = max(0.1, min(0.99, confidence))
    
    # Determine confidence tier
    if confidence >= 0.75:
        confidence_tier = ConfidenceTier.HIGH.value
    elif confidence >= 0.50:
        confidence_tier = ConfidenceTier.MODERATE.value
    else:
        confidence_tier = ConfidenceTier.EXPLORATORY.value
    
    return {
        "core_type": top_type,
        "wing": wing,
        "instinct_primary": instinct_primary,
        "instinct_secondary": instinct_secondary,
        "confidence": round(confidence, 2),
        "confidence_tier": confidence_tier,
        "assessment_depth": "deep",
        "assessment_version": "v2",  # Version marker for soft versioning
        "reliability": reliability,
        "created_at_iso": datetime.now(timezone.utc).isoformat(),
        # Debug fields
        "_debug": {
            "type_scores": session["type_scores"],
            "center_scores": session["center_scores"],
            "wing_scores": session["wing_scores"],
            "instinct_scores": session["instinct_scores"],
            "consistency_score": consistency_score,
            "coherence_score": coherence,
            "silent_reliability": silent_reliability,
            "silent_reliability_debug": silent_debug,
            "type_gap": gap,
            "questions_asked": len(session["asked_question_ids"]),
            "neither_count": session.get("neither_count", 0)
        }
    }

# =============================================================================
# PUBLIC API FUNCTIONS
# =============================================================================

def start_assessment(user_id: str, user_computed_data: Optional[dict] = None) -> dict:
    """
    Start a new deep assessment session.
    
    Args:
        user_id: User identifier
        user_computed_data: Optional computed profile data for coherence validation
    
    Returns:
        Dict with session_id, first question, and progress
    """
    _cleanup_expired_sessions()
    
    session = _create_session(user_id)
    
    # Pre-compute coherence if data available
    if user_computed_data:
        coherence = compute_coherence_score(session, user_computed_data)
        session["coherence_score"] = coherence
    
    question = get_next_question(session)
    progress = get_progress(session)
    
    # Track when question was sent for response time measurement
    session["last_question_sent_at"] = time.time()
    _update_session(session["session_id"], session)
    
    return {
        "session_id": session["session_id"],
        "question": format_question_for_response(question) if question else None,
        "progress": progress
    }

def submit_answer(
    user_id: str, 
    session_id: str, 
    question_id: str, 
    answer: dict,
    user_computed_data: Optional[dict] = None
) -> dict:
    """
    Submit an answer and get next question or results.
    
    Args:
        user_id: User identifier
        session_id: Assessment session ID
        question_id: Question being answered
        answer: Answer object with type and value
        user_computed_data: Optional computed profile data for coherence validation
    
    Returns:
        Dict with either next question or final results
    """
    session = _get_session(session_id)
    
    if not session:
        raise ValueError("Session not found or expired")
    
    if session["user_id"] != user_id:
        raise ValueError("Session does not belong to this user")
    
    # =========================================================================
    # SILENT RELIABILITY TRACKING
    # =========================================================================
    
    # Track response time (time since question was sent)
    last_sent = session.get("last_question_sent_at")
    if last_sent:
        response_time = time.time() - last_sent
        session["response_times"].append(response_time)
    
    # Track answer sequence for straightlining detection (likert answers only)
    if answer.get("type") == "likert" and "value" in answer:
        session["answer_sequence"].append(answer["value"])
    
    # Process the answer
    try:
        process_answer(session, question_id, answer)
    except ValueError as e:
        raise ValueError(f"Invalid answer: {e}")
    
    # Update coherence if we have data and moving to diff stage
    if user_computed_data and session["stage"] == Stage.CORE.value:
        coherence = compute_coherence_score(session, user_computed_data)
        session["coherence_score"] = coherence
    
    # Get next question
    question = get_next_question(session)
    
    if question:
        progress = get_progress(session)
        # Track when this question was sent for next response time measurement
        session["last_question_sent_at"] = time.time()
        _update_session(session_id, session)
        
        return {
            "session_id": session_id,
            "question": format_question_for_response(question),
            "progress": progress
        }
    else:
        # Assessment complete
        results = compute_results(session)
        session["stage"] = Stage.DONE.value
        _update_session(session_id, session)
        
        return {
            "session_id": session_id,
            "results": results
        }

def get_session_status(session_id: str) -> Optional[dict]:
    """Get current session status."""
    session = _get_session(session_id)
    if not session:
        return None
    
    return {
        "session_id": session_id,
        "user_id": session["user_id"],
        "stage": session["stage"],
        "progress": get_progress(session),
        "created_at_iso": session["created_at_iso"],
        "updated_at_iso": session["updated_at_iso"]
    }

def format_question_for_response(question: dict) -> dict:
    """Format a question for API response (exclude scoring info)."""
    formatted = {
        "id": question["id"],
        "prompt": question["prompt"],
        "format": question["format"]
    }
    
    if question["format"] == "forced":
        options = question.get("options", {})
        formatted["options"] = {
            "A": options.get("A"),
            "B": options.get("B"),
            "allow_both": options.get("allow_both", False),
            "allow_neither": options.get("allow_neither", False)
        }
        if options.get("C"):
            formatted["options"]["C"] = options["C"]
    
    return formatted

# =============================================================================
# PROFILE WRITEBACK
# =============================================================================

def format_profile_enneagram(results: dict, include_debug: bool = False) -> dict:
    """Format results for profile storage."""
    profile = {
        "core_type": results["core_type"],
        "wing": results["wing"],
        "instinct_primary": results["instinct_primary"],
        "instinct_secondary": results["instinct_secondary"],
        "confidence": results["confidence"],
        "confidence_tier": results["confidence_tier"],
        "assessment_depth": results["assessment_depth"],
        "assessment_version": results.get("assessment_version", "v2"),
        "reliability": results["reliability"],
        "created_at_iso": results["created_at_iso"]
    }
    
    if include_debug and "_debug" in results:
        profile["_debug"] = results["_debug"]
    
    return profile
