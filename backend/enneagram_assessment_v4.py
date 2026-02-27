"""
Enneagram Assessment V4 - Ground-up Rebuild
============================================
108-question assessment (12 per type) with weighted scoring,
consistency checks, and gaming detection.

Version: 4.0.0
Author: Project Mirror Team
"""

import logging
import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTS & CONFIGURATION
# =============================================================================

# Scoring weights
SCORING_WEIGHTS = {
    "primary": 1.0,       # 100% for primary type match
    "wing": 0.20,         # 20% for adjacent wing types
    "stress_growth": 0.10, # 10% for stress/growth lines
    "same_triad": 0.05,   # 5% for same triad types
}

# Enneagram type relationships
TYPE_WINGS = {
    1: [9, 2], 2: [1, 3], 3: [2, 4], 4: [3, 5], 5: [4, 6],
    6: [5, 7], 7: [6, 8], 8: [7, 9], 9: [8, 1]
}

TYPE_STRESS_GROWTH = {
    1: {"stress": 4, "growth": 7},
    2: {"stress": 8, "growth": 4},
    3: {"stress": 9, "growth": 6},
    4: {"stress": 2, "growth": 1},
    5: {"stress": 7, "growth": 8},
    6: {"stress": 3, "growth": 9},
    7: {"stress": 1, "growth": 5},
    8: {"stress": 5, "growth": 2},
    9: {"stress": 6, "growth": 3},
}

TYPE_TRIADS = {
    "body": [8, 9, 1],    # Gut/Instinctive triad
    "heart": [2, 3, 4],   # Feeling triad
    "head": [5, 6, 7],    # Thinking triad
}

TRIAD_FOR_TYPE = {
    8: "body", 9: "body", 1: "body",
    2: "heart", 3: "heart", 4: "heart",
    5: "head", 6: "head", 7: "head",
}

# Gaming detection thresholds
MIN_RESPONSE_TIME_MS = 2000   # Minimum 2 seconds per question
MAX_RESPONSE_TIME_MS = 60000  # Maximum 60 seconds per question
CONTRADICTION_THRESHOLD = 2   # Max difference for reverse-coded pairs

# Session configuration
SESSION_TTL_HOURS = 24
QUESTIONS_PER_BATCH = 12

# =============================================================================
# TYPE DESCRIPTIONS
# =============================================================================

TYPE_DESCRIPTIONS = {
    1: {
        "name": "The Reformer",
        "core_desire": "To be good, right, and ethical",
        "core_fear": "Being corrupt, evil, or defective",
        "brief": "Principled, purposeful, self-controlled, and perfectionistic"
    },
    2: {
        "name": "The Helper",
        "core_desire": "To be loved and needed",
        "core_fear": "Being unwanted or unworthy of love",
        "brief": "Generous, demonstrative, people-pleasing, and possessive"
    },
    3: {
        "name": "The Achiever",
        "core_desire": "To be valuable and worthwhile",
        "core_fear": "Being worthless or without value",
        "brief": "Adaptable, excelling, driven, and image-conscious"
    },
    4: {
        "name": "The Individualist",
        "core_desire": "To find their identity and significance",
        "core_fear": "Having no identity or personal significance",
        "brief": "Expressive, dramatic, self-absorbed, and temperamental"
    },
    5: {
        "name": "The Investigator",
        "core_desire": "To be capable and competent",
        "core_fear": "Being useless, incompetent, or overwhelmed",
        "brief": "Perceptive, innovative, secretive, and isolated"
    },
    6: {
        "name": "The Loyalist",
        "core_desire": "To have security and support",
        "core_fear": "Being without support or guidance",
        "brief": "Engaging, responsible, anxious, and suspicious"
    },
    7: {
        "name": "The Enthusiast",
        "core_desire": "To be satisfied and content",
        "core_fear": "Being deprived or trapped in pain",
        "brief": "Spontaneous, versatile, acquisitive, and scattered"
    },
    8: {
        "name": "The Challenger",
        "core_desire": "To protect themselves and control their destiny",
        "core_fear": "Being harmed or controlled by others",
        "brief": "Self-confident, decisive, willful, and confrontational"
    },
    9: {
        "name": "The Peacemaker",
        "core_desire": "To have inner stability and peace of mind",
        "core_fear": "Loss, separation, and fragmentation",
        "brief": "Receptive, reassuring, complacent, and resigned"
    },
}

# =============================================================================
# QUESTION BANK - 42 QUESTIONS (36 + 6 VALIDATION)
# =============================================================================

QUESTION_BANK = [
    # =========================================================================
    # BODY TRIAD (Types 8, 9, 1) - 12 Questions
    # =========================================================================
    
    # TYPE 8 - The Challenger (4 questions)
    {
        "id": "Q01-T8-BODY",
        "text": "When a group project falls behind schedule, you typically:",
        "primary_type": 8,
        "secondary_influence": 3,
        "triad": "body",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "options": [
            {"value": 5, "text": "Take charge immediately and delegate tasks with clear deadlines"},
            {"value": 4, "text": "Push the team harder and call out anyone slacking"},
            {"value": 3, "text": "Focus on the most critical tasks yourself"},
            {"value": 2, "text": "Try to motivate everyone while staying calm"},
            {"value": 1, "text": "Wait for someone else to step up and lead"},
        ]
    },
    {
        "id": "Q02-T8-BODY",
        "text": "When someone criticizes your work unfairly in a meeting, you:",
        "primary_type": 8,
        "secondary_influence": 6,
        "triad": "body",
        "difficulty_weight": 1.2,
        "reverse_coded": False,
        "options": [
            {"value": 5, "text": "Directly confront them and demand they explain themselves"},
            {"value": 4, "text": "Stand your ground firmly and defend your work point by point"},
            {"value": 3, "text": "Ask clarifying questions to understand their perspective"},
            {"value": 2, "text": "Let it go in the moment but address it privately later"},
            {"value": 1, "text": "Stay quiet and process your feelings afterward"},
        ]
    },
    {
        "id": "Q03-T8-BODY",
        "text": "When you discover a friend has been dishonest with you, you:",
        "primary_type": 8,
        "secondary_influence": 2,
        "triad": "body",
        "difficulty_weight": 1.1,
        "reverse_coded": False,
        "options": [
            {"value": 5, "text": "Confront them immediately and demand the truth"},
            {"value": 4, "text": "Test them with questions to see if they'll come clean"},
            {"value": 3, "text": "Distance yourself while deciding what to do"},
            {"value": 2, "text": "Give them a chance to explain before reacting"},
            {"value": 1, "text": "Avoid confrontation and quietly reassess the friendship"},
        ]
    },
    {
        "id": "Q04-T8-BODY",
        "text": "When entering a new social situation, you tend to:",
        "primary_type": 8,
        "secondary_influence": 7,
        "triad": "body",
        "difficulty_weight": 0.9,
        "reverse_coded": False,
        "options": [
            {"value": 5, "text": "Scan for who has influence and position yourself strategically"},
            {"value": 4, "text": "Make your presence known and introduce yourself confidently"},
            {"value": 3, "text": "Observe the dynamics before engaging"},
            {"value": 2, "text": "Find someone approachable and start a conversation"},
            {"value": 1, "text": "Stay on the periphery until you feel comfortable"},
        ]
    },
    
    # TYPE 9 - The Peacemaker (4 questions)
    {
        "id": "Q05-T9-BODY",
        "text": "When two friends are in conflict and both ask for your support, you:",
        "primary_type": 9,
        "secondary_influence": 2,
        "triad": "body",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "options": [
            {"value": 5, "text": "Try to see both perspectives and help them find common ground"},
            {"value": 4, "text": "Avoid taking sides and hope it resolves itself"},
            {"value": 3, "text": "Listen to both but keep your own opinion to yourself"},
            {"value": 2, "text": "Support whoever you think is more right"},
            {"value": 1, "text": "Pick a side clearly and advocate for that friend"},
        ]
    },
    {
        "id": "Q06-T9-BODY",
        "text": "When you have a free weekend with no obligations, you typically:",
        "primary_type": 9,
        "secondary_influence": 4,
        "triad": "body",
        "difficulty_weight": 0.8,
        "reverse_coded": False,
        "options": [
            {"value": 5, "text": "Go with the flow and see what happens naturally"},
            {"value": 4, "text": "Enjoy relaxing activities without much structure"},
            {"value": 3, "text": "Make loose plans but stay flexible"},
            {"value": 2, "text": "Plan a few specific activities or goals"},
            {"value": 1, "text": "Create a detailed schedule to maximize the time"},
        ]
    },
    {
        "id": "Q07-T9-BODY",
        "text": "When your partner wants to try a restaurant you're not interested in, you:",
        "primary_type": 9,
        "secondary_influence": 6,
        "triad": "body",
        "difficulty_weight": 0.9,
        "reverse_coded": False,
        "options": [
            {"value": 5, "text": "Happily agree because their happiness matters more"},
            {"value": 4, "text": "Go along with it to avoid conflict"},
            {"value": 3, "text": "Suggest a compromise or alternative"},
            {"value": 2, "text": "Express your preference but defer to them"},
            {"value": 1, "text": "Firmly state your preference and negotiate"},
        ]
    },
    {
        "id": "Q08-T9-BODY",
        "text": "When you're angry at someone close to you, you typically:",
        "primary_type": 9,
        "secondary_influence": 1,
        "triad": "body",
        "difficulty_weight": 1.2,
        "reverse_coded": False,
        "options": [
            {"value": 5, "text": "Suppress it and focus on maintaining harmony"},
            {"value": 4, "text": "Withdraw and become passive or distant"},
            {"value": 3, "text": "Wait until you've calmed down to discuss it"},
            {"value": 2, "text": "Express it indirectly through hints or tone"},
            {"value": 1, "text": "Address it directly and immediately"},
        ]
    },
    
    # TYPE 1 - The Reformer (4 questions)
    {
        "id": "Q09-T1-BODY",
        "text": "When you notice a colleague taking ethical shortcuts at work, you:",
        "primary_type": 1,
        "secondary_influence": 6,
        "triad": "body",
        "difficulty_weight": 1.1,
        "reverse_coded": False,
        "options": [
            {"value": 5, "text": "Feel compelled to address it or report it"},
            {"value": 4, "text": "Struggle internally but eventually speak up"},
            {"value": 3, "text": "Document it but wait to see if it continues"},
            {"value": 2, "text": "Focus on your own work and standards"},
            {"value": 1, "text": "Let it go—it's not your responsibility"},
        ]
    },
    {
        "id": "Q10-T1-BODY",
        "text": "When you make a mistake on an important task, you:",
        "primary_type": 1,
        "secondary_influence": 4,
        "triad": "body",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "options": [
            {"value": 5, "text": "Feel intense self-criticism and replay what went wrong"},
            {"value": 4, "text": "Immediately work to fix it and prevent future errors"},
            {"value": 3, "text": "Acknowledge it and move on after correcting it"},
            {"value": 2, "text": "Feel briefly disappointed but let it go"},
            {"value": 1, "text": "Shrug it off—mistakes happen to everyone"},
        ]
    },
    {
        "id": "Q11-T1-BODY",
        "text": "When organizing a shared living space, you tend to:",
        "primary_type": 1,
        "secondary_influence": 3,
        "triad": "body",
        "difficulty_weight": 0.8,
        "reverse_coded": False,
        "options": [
            {"value": 5, "text": "Create systems and expect everyone to follow them"},
            {"value": 4, "text": "Keep your own areas perfect, frustrated by others' mess"},
            {"value": 3, "text": "Suggest guidelines but stay flexible"},
            {"value": 2, "text": "Adapt to whatever system emerges naturally"},
            {"value": 1, "text": "Don't worry much about organization"},
        ]
    },
    {
        "id": "Q12-T1-BODY",
        "text": "When giving feedback on someone's work, you:",
        "primary_type": 1,
        "secondary_influence": 8,
        "triad": "body",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "options": [
            {"value": 5, "text": "Point out every flaw so they can improve to the right standard"},
            {"value": 4, "text": "Balance criticism with praise but focus on corrections needed"},
            {"value": 3, "text": "Highlight both strengths and areas for improvement"},
            {"value": 2, "text": "Focus mainly on positives to encourage them"},
            {"value": 1, "text": "Avoid giving critical feedback to keep things positive"},
        ]
    },
    
    # =========================================================================
    # HEART TRIAD (Types 2, 3, 4) - 12 Questions
    # =========================================================================
    
    # TYPE 2 - The Helper (4 questions)
    {
        "id": "Q13-T2-HEART",
        "text": "When a friend is going through a difficult time, you typically:",
        "primary_type": 2,
        "secondary_influence": 9,
        "triad": "heart",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "options": [
            {"value": 5, "text": "Drop everything to be there and help in any way possible"},
            {"value": 4, "text": "Reach out frequently and offer specific support"},
            {"value": 3, "text": "Check in regularly and offer help when asked"},
            {"value": 2, "text": "Send supportive messages but give them space"},
            {"value": 1, "text": "Wait for them to reach out if they need something"},
        ]
    },
    {
        "id": "Q14-T2-HEART",
        "text": "When you've done a lot for someone and they don't acknowledge it, you:",
        "primary_type": 2,
        "secondary_influence": 8,
        "triad": "heart",
        "difficulty_weight": 1.2,
        "reverse_coded": False,
        "options": [
            {"value": 5, "text": "Feel hurt and resentful, questioning if they value you"},
            {"value": 4, "text": "Drop hints about what you've done hoping they notice"},
            {"value": 3, "text": "Feel disappointed but tell yourself it doesn't matter"},
            {"value": 2, "text": "Directly ask for appreciation or acknowledgment"},
            {"value": 1, "text": "Genuinely don't need recognition—helping is enough"},
        ]
    },
    {
        "id": "Q15-T2-HEART",
        "text": "When meeting new people, you often find yourself:",
        "primary_type": 2,
        "secondary_influence": 3,
        "triad": "heart",
        "difficulty_weight": 0.9,
        "reverse_coded": False,
        "options": [
            {"value": 5, "text": "Quickly identifying what they need and how you can help"},
            {"value": 4, "text": "Being warm and making them feel welcomed and comfortable"},
            {"value": 3, "text": "Finding common interests to connect over"},
            {"value": 2, "text": "Sharing about yourself while showing interest in them"},
            {"value": 1, "text": "Staying reserved until you know them better"},
        ]
    },
    {
        "id": "Q16-T2-HEART",
        "text": "When you're overwhelmed with your own problems, you:",
        "primary_type": 2,
        "secondary_influence": 4,
        "triad": "heart",
        "difficulty_weight": 1.1,
        "reverse_coded": False,
        "options": [
            {"value": 5, "text": "Focus on helping others—it distracts from your own issues"},
            {"value": 4, "text": "Struggle to ask for help even when you need it"},
            {"value": 3, "text": "Reach out to trusted friends for support"},
            {"value": 2, "text": "Take time alone to process and recover"},
            {"value": 1, "text": "Easily ask for and accept help from others"},
        ]
    },
    
    # TYPE 3 - The Achiever (4 questions)
    {
        "id": "Q17-T3-HEART",
        "text": "When preparing for an important presentation, you focus most on:",
        "primary_type": 3,
        "secondary_influence": 1,
        "triad": "heart",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "options": [
            {"value": 5, "text": "How you'll come across and the impression you'll make"},
            {"value": 4, "text": "Achieving the best possible outcome and metrics"},
            {"value": 3, "text": "Delivering accurate, well-organized content"},
            {"value": 2, "text": "Connecting authentically with your audience"},
            {"value": 1, "text": "Just getting through it—presentations aren't your thing"},
        ]
    },
    {
        "id": "Q18-T3-HEART",
        "text": "When you fail at something publicly, your first instinct is to:",
        "primary_type": 3,
        "secondary_influence": 9,
        "triad": "heart",
        "difficulty_weight": 1.3,
        "reverse_coded": False,
        "options": [
            {"value": 5, "text": "Quickly reframe it as a learning experience to save face"},
            {"value": 4, "text": "Feel deeply embarrassed and work to recover your image"},
            {"value": 3, "text": "Analyze what went wrong to do better next time"},
            {"value": 2, "text": "Accept it openly and move on without dwelling"},
            {"value": 1, "text": "Not care much what others think about the failure"},
        ]
    },
    {
        "id": "Q19-T3-HEART",
        "text": "When your accomplishments go unrecognized at work, you:",
        "primary_type": 3,
        "secondary_influence": 8,
        "triad": "heart",
        "difficulty_weight": 1.1,
        "reverse_coded": False,
        "options": [
            {"value": 5, "text": "Find subtle ways to make your achievements visible"},
            {"value": 4, "text": "Feel frustrated and consider if you're in the right place"},
            {"value": 3, "text": "Directly ask for feedback and recognition"},
            {"value": 2, "text": "Trust that good work speaks for itself eventually"},
            {"value": 1, "text": "Don't need external validation to feel successful"},
        ]
    },
    {
        "id": "Q20-T3-HEART",
        "text": "In social situations, you often find yourself:",
        "primary_type": 3,
        "secondary_influence": 7,
        "triad": "heart",
        "difficulty_weight": 0.9,
        "reverse_coded": False,
        "options": [
            {"value": 5, "text": "Adapting your personality to fit what the group values"},
            {"value": 4, "text": "Highlighting your achievements when relevant"},
            {"value": 3, "text": "Being charming and making good impressions"},
            {"value": 2, "text": "Showing up as your authentic self regardless of context"},
            {"value": 1, "text": "Staying quiet and observing rather than performing"},
        ]
    },
    
    # TYPE 4 - The Individualist (4 questions)
    {
        "id": "Q21-T4-HEART",
        "text": "When you see others living seemingly perfect lives, you tend to:",
        "primary_type": 4,
        "secondary_influence": 2,
        "triad": "heart",
        "difficulty_weight": 1.1,
        "reverse_coded": False,
        "options": [
            {"value": 5, "text": "Feel a deep sense of longing for what's missing in your life"},
            {"value": 4, "text": "Wonder what's wrong with you that you can't have that"},
            {"value": 3, "text": "Remind yourself that appearances aren't reality"},
            {"value": 2, "text": "Feel happy for them while content with your own path"},
            {"value": 1, "text": "Not compare yourself—their life has nothing to do with yours"},
        ]
    },
    {
        "id": "Q22-T4-HEART",
        "text": "When experiencing intense emotions, you typically:",
        "primary_type": 4,
        "secondary_influence": 5,
        "triad": "heart",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "options": [
            {"value": 5, "text": "Dive deep into them—intensity feels more authentic than numbness"},
            {"value": 4, "text": "Express them creatively through art, writing, or music"},
            {"value": 3, "text": "Process them internally while maintaining composure"},
            {"value": 2, "text": "Share them with trusted people to work through them"},
            {"value": 1, "text": "Try to regulate them quickly and return to neutral"},
        ]
    },
    {
        "id": "Q23-T4-HEART",
        "text": "When you feel like no one truly understands you, you:",
        "primary_type": 4,
        "secondary_influence": 1,
        "triad": "heart",
        "difficulty_weight": 1.2,
        "reverse_coded": False,
        "options": [
            {"value": 5, "text": "Find a melancholic comfort in your unique perspective"},
            {"value": 4, "text": "Withdraw and spend time in introspection"},
            {"value": 3, "text": "Seek out people or communities who might relate"},
            {"value": 2, "text": "Express yourself more clearly to bridge the gap"},
            {"value": 1, "text": "Accept that complete understanding isn't necessary"},
        ]
    },
    {
        "id": "Q24-T4-HEART",
        "text": "When choosing how to decorate your personal space, you prioritize:",
        "primary_type": 4,
        "secondary_influence": 9,
        "triad": "heart",
        "difficulty_weight": 0.8,
        "reverse_coded": False,
        "options": [
            {"value": 5, "text": "Creating a unique aesthetic that reflects your inner world"},
            {"value": 4, "text": "Surrounding yourself with meaningful, beautiful objects"},
            {"value": 3, "text": "Balance of style and functionality"},
            {"value": 2, "text": "Comfort and practicality over aesthetics"},
            {"value": 1, "text": "Not caring much—it's just a space"},
        ]
    },
    
    # =========================================================================
    # HEAD TRIAD (Types 5, 6, 7) - 12 Questions
    # =========================================================================
    
    # TYPE 5 - The Investigator (4 questions)
    {
        "id": "Q25-T5-HEAD",
        "text": "When faced with a complex problem at work, you prefer to:",
        "primary_type": 5,
        "secondary_influence": 6,
        "triad": "head",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "options": [
            {"value": 5, "text": "Research extensively before taking any action"},
            {"value": 4, "text": "Think through all possibilities independently first"},
            {"value": 3, "text": "Gather some information then discuss with colleagues"},
            {"value": 2, "text": "Jump in and figure it out as you go"},
            {"value": 1, "text": "Delegate it to someone with more expertise"},
        ]
    },
    {
        "id": "Q26-T5-HEAD",
        "text": "When attending a large social event, you typically:",
        "primary_type": 5,
        "secondary_influence": 4,
        "triad": "head",
        "difficulty_weight": 0.9,
        "reverse_coded": False,
        "options": [
            {"value": 5, "text": "Feel drained and need alone time to recharge afterward"},
            {"value": 4, "text": "Find one or two people to have deep conversations with"},
            {"value": 3, "text": "Participate moderately then take breaks"},
            {"value": 2, "text": "Enjoy mingling and meeting new people"},
            {"value": 1, "text": "Thrive on the energy and stay until the end"},
        ]
    },
    {
        "id": "Q27-T5-HEAD",
        "text": "When someone asks for your emotional support, you:",
        "primary_type": 5,
        "secondary_influence": 9,
        "triad": "head",
        "difficulty_weight": 1.1,
        "reverse_coded": False,
        "options": [
            {"value": 5, "text": "Feel uncomfortable and try to solve the problem instead"},
            {"value": 4, "text": "Listen but struggle to express emotional warmth"},
            {"value": 3, "text": "Offer both practical help and emotional presence"},
            {"value": 2, "text": "Focus on being present and empathetic"},
            {"value": 1, "text": "Easily provide comfort and emotional connection"},
        ]
    },
    {
        "id": "Q28-T5-HEAD",
        "text": "When your personal boundaries are pushed, you tend to:",
        "primary_type": 5,
        "secondary_influence": 8,
        "triad": "head",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "options": [
            {"value": 5, "text": "Withdraw completely and cut off contact"},
            {"value": 4, "text": "Create more distance without explicit confrontation"},
            {"value": 3, "text": "Calmly communicate your boundaries"},
            {"value": 2, "text": "Accommodate somewhat while feeling uncomfortable"},
            {"value": 1, "text": "Assert yourself forcefully and immediately"},
        ]
    },
    
    # TYPE 6 - The Loyalist (4 questions)
    {
        "id": "Q29-T6-HEAD",
        "text": "When starting a new job or project, your first thoughts are often about:",
        "primary_type": 6,
        "secondary_influence": 1,
        "triad": "head",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "options": [
            {"value": 5, "text": "What could go wrong and how to prepare for it"},
            {"value": 4, "text": "Who you can trust and rely on for support"},
            {"value": 3, "text": "Understanding the expectations and guidelines"},
            {"value": 2, "text": "The opportunities and possibilities ahead"},
            {"value": 1, "text": "Excitement about the new adventure"},
        ]
    },
    {
        "id": "Q30-T6-HEAD",
        "text": "When an authority figure gives you instructions you disagree with, you:",
        "primary_type": 6,
        "secondary_influence": 8,
        "triad": "head",
        "difficulty_weight": 1.2,
        "reverse_coded": False,
        "options": [
            {"value": 5, "text": "Question them internally while outwardly complying"},
            {"value": 4, "text": "Seek clarification to understand their reasoning"},
            {"value": 3, "text": "Respectfully voice your concerns"},
            {"value": 2, "text": "Follow instructions but adapt where you can"},
            {"value": 1, "text": "Push back directly and advocate for your approach"},
        ]
    },
    {
        "id": "Q31-T6-HEAD",
        "text": "When making a significant life decision, you typically:",
        "primary_type": 6,
        "secondary_influence": 5,
        "triad": "head",
        "difficulty_weight": 1.1,
        "reverse_coded": False,
        "options": [
            {"value": 5, "text": "Consult many trusted people and weigh all perspectives"},
            {"value": 4, "text": "Overthink scenarios and struggle to commit"},
            {"value": 3, "text": "Research carefully then make a reasoned choice"},
            {"value": 2, "text": "Trust your gut and decide relatively quickly"},
            {"value": 1, "text": "Make spontaneous decisions based on what feels right"},
        ]
    },
    {
        "id": "Q32-T6-HEAD",
        "text": "When things are going smoothly in your life, you often:",
        "primary_type": 6,
        "secondary_influence": 7,
        "triad": "head",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "options": [
            {"value": 5, "text": "Wait for the other shoe to drop—something will go wrong"},
            {"value": 4, "text": "Stay vigilant and prepare for potential problems"},
            {"value": 3, "text": "Enjoy it while maintaining reasonable caution"},
            {"value": 2, "text": "Fully enjoy the good times without worry"},
            {"value": 1, "text": "Feel confident that things will continue going well"},
        ]
    },
    
    # TYPE 7 - The Enthusiast (4 questions)
    {
        "id": "Q33-T7-HEAD",
        "text": "When you have to deal with a boring but necessary task, you:",
        "primary_type": 7,
        "secondary_influence": 3,
        "triad": "head",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "options": [
            {"value": 5, "text": "Procrastinate by finding more interesting things to do"},
            {"value": 4, "text": "Rush through it to get back to enjoyable activities"},
            {"value": 3, "text": "Find ways to make it more interesting or gamify it"},
            {"value": 2, "text": "Buckle down and complete it methodically"},
            {"value": 1, "text": "Actually enjoy the structure of routine tasks"},
        ]
    },
    {
        "id": "Q34-T7-HEAD",
        "text": "When you're feeling sad or anxious, your instinct is to:",
        "primary_type": 7,
        "secondary_influence": 9,
        "triad": "head",
        "difficulty_weight": 1.2,
        "reverse_coded": False,
        "options": [
            {"value": 5, "text": "Find distractions—activities, people, or plans to look forward to"},
            {"value": 4, "text": "Reframe it positively and focus on silver linings"},
            {"value": 3, "text": "Acknowledge the feeling but not dwell on it"},
            {"value": 2, "text": "Sit with the emotion and process it fully"},
            {"value": 1, "text": "Talk about it deeply with someone you trust"},
        ]
    },
    {
        "id": "Q35-T7-HEAD",
        "text": "When planning a vacation, you prefer:",
        "primary_type": 7,
        "secondary_influence": 2,
        "triad": "head",
        "difficulty_weight": 0.8,
        "reverse_coded": False,
        "options": [
            {"value": 5, "text": "An adventure-packed itinerary with maximum experiences"},
            {"value": 4, "text": "Flexibility to explore spontaneously with loose plans"},
            {"value": 3, "text": "Balance of planned activities and free time"},
            {"value": 2, "text": "A relaxing trip with minimal scheduling"},
            {"value": 1, "text": "Detailed planning to ensure everything goes smoothly"},
        ]
    },
    {
        "id": "Q36-T7-HEAD",
        "text": "When someone shares their problems with you, you often:",
        "primary_type": 7,
        "secondary_influence": 6,
        "triad": "head",
        "difficulty_weight": 1.1,
        "reverse_coded": False,
        "options": [
            {"value": 5, "text": "Try to cheer them up and offer optimistic perspectives"},
            {"value": 4, "text": "Suggest solutions and exciting alternatives"},
            {"value": 3, "text": "Listen while gently steering toward positive outcomes"},
            {"value": 2, "text": "Focus on understanding and validating their feelings"},
            {"value": 1, "text": "Sit with them in their pain without trying to fix it"},
        ]
    },
    
    # =========================================================================
    # VALIDATION QUESTIONS (6 Reverse-Coded Pairs)
    # =========================================================================
    
    # Validation pair 1: Type 8 aggression (normal vs reverse)
    {
        "id": "V01-T8-VAL",
        "text": "When someone cuts in line in front of you, you:",
        "primary_type": 8,
        "secondary_influence": 1,
        "triad": "body",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "validation_pair": "V02-T8-VAL",
        "options": [
            {"value": 5, "text": "Call them out directly and assert your place"},
            {"value": 4, "text": "Make your displeasure known through body language"},
            {"value": 3, "text": "Feel annoyed but weigh if it's worth confronting"},
            {"value": 2, "text": "Let it go—not worth the conflict"},
            {"value": 1, "text": "Barely notice or care"},
        ]
    },
    {
        "id": "V02-T8-VAL",
        "text": "You prefer to avoid confrontation even when you've been wronged.",
        "primary_type": 8,
        "secondary_influence": 9,
        "triad": "body",
        "difficulty_weight": 1.0,
        "reverse_coded": True,
        "validation_pair": "V01-T8-VAL",
        "options": [
            {"value": 1, "text": "Strongly agree—peace is more valuable than being right"},
            {"value": 2, "text": "Somewhat agree—confrontation is uncomfortable"},
            {"value": 3, "text": "Neutral—depends on the situation"},
            {"value": 4, "text": "Somewhat disagree—I'll address it if important"},
            {"value": 5, "text": "Strongly disagree—I always stand up for myself"},
        ]
    },
    
    # Validation pair 2: Type 2 helping motivation
    {
        "id": "V03-T2-VAL",
        "text": "You feel most fulfilled when:",
        "primary_type": 2,
        "secondary_influence": 3,
        "triad": "heart",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "validation_pair": "V04-T2-VAL",
        "options": [
            {"value": 5, "text": "Others recognize how much you've helped them"},
            {"value": 4, "text": "You're making a tangible difference in someone's life"},
            {"value": 3, "text": "You're connected to people who appreciate you"},
            {"value": 2, "text": "You're achieving your personal goals"},
            {"value": 1, "text": "You have time for solitude and self-care"},
        ]
    },
    {
        "id": "V04-T2-VAL",
        "text": "Your sense of worth comes primarily from your own self-assessment, not others' opinions.",
        "primary_type": 2,
        "secondary_influence": 5,
        "triad": "heart",
        "difficulty_weight": 1.0,
        "reverse_coded": True,
        "validation_pair": "V03-T2-VAL",
        "options": [
            {"value": 1, "text": "Strongly agree—I know my worth regardless of feedback"},
            {"value": 2, "text": "Somewhat agree—though appreciation is nice"},
            {"value": 3, "text": "Neutral—both internal and external matter"},
            {"value": 4, "text": "Somewhat disagree—others' views affect me significantly"},
            {"value": 5, "text": "Strongly disagree—I need others to feel valued"},
        ]
    },
    
    # Validation pair 3: Type 5 social energy
    {
        "id": "V05-T5-VAL",
        "text": "After a day of meetings and social interaction, you:",
        "primary_type": 5,
        "secondary_influence": 4,
        "triad": "head",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "validation_pair": "V06-T5-VAL",
        "options": [
            {"value": 5, "text": "Need significant alone time to recover your energy"},
            {"value": 4, "text": "Prefer quiet activities rather than more socializing"},
            {"value": 3, "text": "Feel tired but could still see close friends"},
            {"value": 2, "text": "Feel energized and ready for more connection"},
            {"value": 1, "text": "Want to continue socializing—people energize you"},
        ]
    },
    {
        "id": "V06-T5-VAL",
        "text": "Being around people gives you more energy than being alone.",
        "primary_type": 5,
        "secondary_influence": 7,
        "triad": "head",
        "difficulty_weight": 1.0,
        "reverse_coded": True,
        "validation_pair": "V05-T5-VAL",
        "options": [
            {"value": 1, "text": "Strongly agree—people are energizing"},
            {"value": 2, "text": "Somewhat agree—with the right people"},
            {"value": 3, "text": "Neutral—depends on the context"},
            {"value": 4, "text": "Somewhat disagree—solitude often feels better"},
            {"value": 5, "text": "Strongly disagree—alone time is essential for me"},
        ]
    },
]

# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class QuestionResponse:
    question_id: str
    answer_value: int
    response_time_ms: int
    timestamp: str

@dataclass
class ConsistencyCheck:
    pair_id: str
    question_1: str
    question_2: str
    answer_1: int
    answer_2: int
    difference: int
    is_consistent: bool

@dataclass
class GamingIndicators:
    avg_response_time_ms: float
    fast_responses_count: int  # < 2 seconds
    slow_responses_count: int  # > 60 seconds
    variance_score: float
    all_same_value: bool
    randomness_score: float
    consistency_failures: int
    is_suspicious: bool
    flags: List[str]

@dataclass
class TypeScore:
    type_number: int
    raw_score: float
    normalized_percentage: float
    question_count: int

@dataclass
class AssessmentResult:
    primary_type: int
    primary_percentage: float
    secondary_type: int
    secondary_percentage: float
    suggested_wing: int
    all_scores: List[TypeScore]
    confidence_level: str  # "high", "medium", "low"
    is_unclear: bool  # True if top 2 within 10%
    gaming_indicators: GamingIndicators
    consistency_checks: List[ConsistencyCheck]

# =============================================================================
# SCORING ENGINE
# =============================================================================

class ScoringEngine:
    """Calculates type scores with weighted relationships and consistency checks."""
    
    def __init__(self):
        self.question_map = {q["id"]: q for q in QUESTION_BANK}
    
    def calculate_scores(self, responses: List[QuestionResponse]) -> Dict[int, float]:
        """Calculate raw scores for all 9 types based on responses."""
        scores = {t: 0.0 for t in range(1, 10)}
        question_counts = {t: 0 for t in range(1, 10)}
        
        for response in responses:
            question = self.question_map.get(response.question_id)
            if not question:
                continue
            
            primary_type = question["primary_type"]
            secondary_type = question.get("secondary_influence")
            answer = response.answer_value
            difficulty = question.get("difficulty_weight", 1.0)
            is_reverse = question.get("reverse_coded", False)
            
            # For reverse-coded questions, invert the score
            if is_reverse:
                answer = 6 - answer  # Converts 1->5, 2->4, 3->3, 4->2, 5->1
            
            # Primary type gets full points
            primary_points = answer * difficulty * SCORING_WEIGHTS["primary"]
            scores[primary_type] += primary_points
            question_counts[primary_type] += 1
            
            # Wing types get partial points
            for wing_type in TYPE_WINGS.get(primary_type, []):
                wing_points = answer * difficulty * SCORING_WEIGHTS["wing"]
                scores[wing_type] += wing_points
            
            # Stress/growth lines get partial points
            stress_growth = TYPE_STRESS_GROWTH.get(primary_type, {})
            for line_type in [stress_growth.get("stress"), stress_growth.get("growth")]:
                if line_type:
                    line_points = answer * difficulty * SCORING_WEIGHTS["stress_growth"]
                    scores[line_type] += line_points
            
            # Same triad types get small bonus
            triad = TRIAD_FOR_TYPE.get(primary_type)
            if triad:
                for triad_type in TYPE_TRIADS.get(triad, []):
                    if triad_type != primary_type:
                        triad_points = answer * difficulty * SCORING_WEIGHTS["same_triad"]
                        scores[triad_type] += triad_points
            
            # Secondary influence gets small bonus if present
            if secondary_type and secondary_type != primary_type:
                secondary_points = answer * difficulty * 0.05
                scores[secondary_type] += secondary_points
        
        return scores, question_counts
    
    def normalize_scores(self, raw_scores: Dict[int, float]) -> Dict[int, float]:
        """Convert raw scores to percentages (0-100)."""
        total = sum(raw_scores.values())
        if total == 0:
            return {t: 0.0 for t in range(1, 10)}
        
        return {t: (score / total) * 100 for t, score in raw_scores.items()}
    
    def get_top_types(self, normalized_scores: Dict[int, float]) -> Tuple[int, int]:
        """Return the top 2 types by score."""
        sorted_types = sorted(normalized_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_types[0][0], sorted_types[1][0]
    
    def suggest_wing(self, primary_type: int, normalized_scores: Dict[int, float]) -> int:
        """Suggest the most likely wing based on scores."""
        wings = TYPE_WINGS.get(primary_type, [])
        if not wings:
            return primary_type
        
        wing_scores = {w: normalized_scores.get(w, 0) for w in wings}
        return max(wing_scores.items(), key=lambda x: x[1])[0]
    
    def check_result_clarity(self, primary_pct: float, secondary_pct: float) -> bool:
        """Check if result is unclear (top 2 within 10%)."""
        return abs(primary_pct - secondary_pct) <= 10

# =============================================================================
# GAMING DETECTION
# =============================================================================

class GamingDetector:
    """Detects suspicious response patterns that suggest gaming or random answers."""
    
    def __init__(self):
        self.question_map = {q["id"]: q for q in QUESTION_BANK}
    
    def analyze(self, responses: List[QuestionResponse]) -> GamingIndicators:
        """Analyze responses for gaming indicators."""
        if not responses:
            return GamingIndicators(
                avg_response_time_ms=0,
                fast_responses_count=0,
                slow_responses_count=0,
                variance_score=0,
                all_same_value=False,
                randomness_score=0,
                consistency_failures=0,
                is_suspicious=False,
                flags=[]
            )
        
        flags = []
        
        # Response time analysis
        times = [r.response_time_ms for r in responses]
        avg_time = sum(times) / len(times)
        fast_count = sum(1 for t in times if t < MIN_RESPONSE_TIME_MS)
        slow_count = sum(1 for t in times if t > MAX_RESPONSE_TIME_MS)
        
        if fast_count > len(responses) * 0.3:
            flags.append("HIGH_FAST_RESPONSE_RATE")
        if slow_count > len(responses) * 0.3:
            flags.append("HIGH_SLOW_RESPONSE_RATE")
        
        # Answer variance analysis
        answers = [r.answer_value for r in responses]
        all_same = len(set(answers)) == 1
        if all_same:
            flags.append("ALL_SAME_ANSWERS")
        
        # Calculate variance (higher variance = more random)
        mean_answer = sum(answers) / len(answers)
        variance = sum((a - mean_answer) ** 2 for a in answers) / len(answers)
        
        # Randomness score: check for alternating or patterned responses
        randomness = self._calculate_randomness(answers)
        if randomness > 0.8:
            flags.append("HIGH_RANDOMNESS")
        
        # Consistency check for validation pairs
        consistency_failures = self._check_validation_pairs(responses)
        if consistency_failures > 2:
            flags.append("CONSISTENCY_FAILURES")
        
        is_suspicious = len(flags) >= 2 or all_same or consistency_failures > 2
        
        return GamingIndicators(
            avg_response_time_ms=avg_time,
            fast_responses_count=fast_count,
            slow_responses_count=slow_count,
            variance_score=variance,
            all_same_value=all_same,
            randomness_score=randomness,
            consistency_failures=consistency_failures,
            is_suspicious=is_suspicious,
            flags=flags
        )
    
    def _calculate_randomness(self, answers: List[int]) -> float:
        """Calculate how random the answer pattern appears (0-1)."""
        if len(answers) < 3:
            return 0.0
        
        # Check for sequential patterns
        alternations = 0
        for i in range(1, len(answers)):
            if answers[i] != answers[i-1]:
                alternations += 1
        
        # Perfect alternation would be suspicious
        alternation_rate = alternations / (len(answers) - 1)
        
        # Check distribution across all options
        value_counts = {}
        for a in answers:
            value_counts[a] = value_counts.get(a, 0) + 1
        
        # If all options used roughly equally, might be random
        expected_per_value = len(answers) / 5
        deviation = sum(abs(count - expected_per_value) for count in value_counts.values())
        normalized_deviation = deviation / len(answers)
        
        # Combine metrics (lower deviation + high alternation = more random)
        randomness = (1 - normalized_deviation) * 0.5 + (alternation_rate * 0.5 if alternation_rate > 0.7 else 0)
        
        return min(1.0, randomness)
    
    def _check_validation_pairs(self, responses: List[QuestionResponse]) -> int:
        """Check reverse-coded validation pairs for contradictions."""
        failures = 0
        response_map = {r.question_id: r.answer_value for r in responses}
        
        for question in QUESTION_BANK:
            pair_id = question.get("validation_pair")
            if not pair_id or question.get("reverse_coded"):
                continue
            
            q1_answer = response_map.get(question["id"])
            q2_answer = response_map.get(pair_id)
            
            if q1_answer is None or q2_answer is None:
                continue
            
            # For validation pairs, answers should correlate
            # Q1 high (5) should mean Q2 high (5) after reverse coding
            # If Q1=5 and Q2=1 (reverse coded), that's consistent
            # If Q1=5 and Q2=5 (reverse coded to 1), that's inconsistent
            difference = abs(q1_answer - q2_answer)
            if difference > CONTRADICTION_THRESHOLD:
                failures += 1
        
        return failures
    
    def get_consistency_details(self, responses: List[QuestionResponse]) -> List[ConsistencyCheck]:
        """Get detailed consistency check results."""
        checks = []
        response_map = {r.question_id: r.answer_value for r in responses}
        
        for question in QUESTION_BANK:
            pair_id = question.get("validation_pair")
            if not pair_id or question.get("reverse_coded"):
                continue
            
            q1_answer = response_map.get(question["id"])
            q2_answer = response_map.get(pair_id)
            
            if q1_answer is None or q2_answer is None:
                continue
            
            difference = abs(q1_answer - q2_answer)
            is_consistent = difference <= CONTRADICTION_THRESHOLD
            
            checks.append(ConsistencyCheck(
                pair_id=f"{question['id']}-{pair_id}",
                question_1=question["id"],
                question_2=pair_id,
                answer_1=q1_answer,
                answer_2=q2_answer,
                difference=difference,
                is_consistent=is_consistent
            ))
        
        return checks

# =============================================================================
# SESSION MANAGEMENT
# =============================================================================

class SessionManager:
    """Manages assessment sessions with persistence and resume capability."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["v4_sessions"]
        self.results_collection = db["v4_results"]
    
    async def create_session(self, user_id: str) -> Dict:
        """Create a new assessment session."""
        session_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        session = {
            "session_id": session_id,
            "user_id": user_id,
            "status": "in_progress",
            "current_question_index": 0,
            "current_section": "body",  # body -> heart -> head
            "responses": [],
            "start_time": now.isoformat(),
            "last_activity": now.isoformat(),
            "expires_at": (now + timedelta(hours=SESSION_TTL_HOURS)).isoformat(),
            "completed_sections": [],
            "created_at": now.isoformat(),
        }
        
        await self.collection.insert_one(session)
        logger.info(f"[V4Assessment] Created session {session_id} for user {user_id}")
        
        return session
    
    async def get_session(self, session_id: str) -> Optional[Dict]:
        """Retrieve a session by ID."""
        session = await self.collection.find_one({"session_id": session_id})
        if session:
            session.pop("_id", None)
        return session
    
    async def get_user_session(self, user_id: str) -> Optional[Dict]:
        """Get active session for a user."""
        now = datetime.utcnow().isoformat()
        session = await self.collection.find_one({
            "user_id": user_id,
            "status": "in_progress",
            "expires_at": {"$gt": now}
        })
        if session:
            session.pop("_id", None)
        return session
    
    async def update_session(self, session_id: str, updates: Dict) -> bool:
        """Update session with new data."""
        updates["last_activity"] = datetime.utcnow().isoformat()
        result = await self.collection.update_one(
            {"session_id": session_id},
            {"$set": updates}
        )
        return result.modified_count > 0
    
    async def add_response(self, session_id: str, response: QuestionResponse) -> bool:
        """Add a question response to the session."""
        result = await self.collection.update_one(
            {"session_id": session_id},
            {
                "$push": {"responses": asdict(response)},
                "$inc": {"current_question_index": 1},
                "$set": {"last_activity": datetime.utcnow().isoformat()}
            }
        )
        return result.modified_count > 0
    
    async def complete_session(self, session_id: str, result: AssessmentResult) -> bool:
        """Mark session as complete and store results."""
        now = datetime.utcnow().isoformat()
        
        # Update session status
        await self.collection.update_one(
            {"session_id": session_id},
            {"$set": {
                "status": "completed",
                "completed_at": now,
                "last_activity": now
            }}
        )
        
        # Store result
        result_doc = {
            "session_id": session_id,
            "primary_type": result.primary_type,
            "primary_percentage": result.primary_percentage,
            "secondary_type": result.secondary_type,
            "secondary_percentage": result.secondary_percentage,
            "suggested_wing": result.suggested_wing,
            "all_scores": [asdict(s) for s in result.all_scores],
            "confidence_level": result.confidence_level,
            "is_unclear": result.is_unclear,
            "gaming_indicators": asdict(result.gaming_indicators),
            "created_at": now
        }
        
        await self.results_collection.insert_one(result_doc)
        logger.info(f"[V4Assessment] Completed session {session_id}")
        
        return True
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        result = await self.collection.delete_one({"session_id": session_id})
        return result.deleted_count > 0

# =============================================================================
# MAIN ASSESSMENT CLASS
# =============================================================================

class EnneagramAssessmentV4:
    """Main assessment class coordinating all components."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.session_manager = SessionManager(db)
        self.scoring_engine = ScoringEngine()
        self.gaming_detector = GamingDetector()
        self.questions = QUESTION_BANK
    
    async def start_assessment(self, user_id: str) -> Dict:
        """Start a new assessment or resume existing one."""
        # Check for existing session
        existing = await self.session_manager.get_user_session(user_id)
        if existing:
            return {
                "status": "resumed",
                "session_id": existing["session_id"],
                "current_index": existing["current_question_index"],
                "total_questions": len(self.questions),
                "next_batch": self._get_question_batch(existing["current_question_index"])
            }
        
        # Create new session
        session = await self.session_manager.create_session(user_id)
        
        return {
            "status": "started",
            "session_id": session["session_id"],
            "current_index": 0,
            "total_questions": len(self.questions),
            "next_batch": self._get_question_batch(0)
        }
    
    def _get_question_batch(self, start_index: int) -> List[Dict]:
        """Get a batch of questions starting from index."""
        end_index = min(start_index + QUESTIONS_PER_BATCH, len(self.questions))
        batch = []
        
        for i in range(start_index, end_index):
            q = self.questions[i].copy()
            q["index"] = i
            # Remove internal fields from client response
            q.pop("validation_pair", None)
            batch.append(q)
        
        return batch
    
    async def submit_answer(
        self,
        session_id: str,
        question_id: str,
        answer_value: int,
        response_time_ms: int
    ) -> Dict:
        """Submit an answer and get progress/next question."""
        session = await self.session_manager.get_session(session_id)
        if not session:
            raise ValueError("Session not found")
        
        if session["status"] != "in_progress":
            raise ValueError("Session is not active")
        
        # Validate answer
        if not 1 <= answer_value <= 5:
            raise ValueError("Answer must be between 1 and 5")
        
        # Create response record
        response = QuestionResponse(
            question_id=question_id,
            answer_value=answer_value,
            response_time_ms=response_time_ms,
            timestamp=datetime.utcnow().isoformat()
        )
        
        # Save response
        await self.session_manager.add_response(session_id, response)
        
        # Get updated session
        session = await self.session_manager.get_session(session_id)
        current_index = session["current_question_index"]
        
        # Check if assessment is complete
        if current_index >= len(self.questions):
            # Calculate final results
            result = await self.calculate_results(session_id)
            return {
                "status": "completed",
                "result": self._format_result(result)
            }
        
        # Determine section progress
        section = self._get_section_for_index(current_index)
        section_progress = self._get_section_progress(current_index)
        
        return {
            "status": "in_progress",
            "current_index": current_index,
            "total_questions": len(self.questions),
            "section": section,
            "section_progress": section_progress,
            "next_batch": self._get_question_batch(current_index) if current_index % QUESTIONS_PER_BATCH == 0 else None
        }
    
    def _get_section_for_index(self, index: int) -> str:
        """Determine which section (triad) for question index."""
        if index < 12:
            return "body"
        elif index < 24:
            return "heart"
        elif index < 36:
            return "head"
        else:
            return "validation"
    
    def _get_section_progress(self, index: int) -> Dict:
        """Get progress within current section."""
        section = self._get_section_for_index(index)
        if section == "body":
            return {"section": "body", "current": index + 1, "total": 12}
        elif section == "heart":
            return {"section": "heart", "current": index - 11, "total": 12}
        elif section == "head":
            return {"section": "head", "current": index - 23, "total": 12}
        else:
            return {"section": "validation", "current": index - 35, "total": 6}
    
    async def calculate_results(self, session_id: str) -> AssessmentResult:
        """Calculate final assessment results."""
        session = await self.session_manager.get_session(session_id)
        if not session:
            raise ValueError("Session not found")
        
        # Convert stored responses to QuestionResponse objects
        responses = [
            QuestionResponse(**r) for r in session["responses"]
        ]
        
        # Calculate scores
        raw_scores, question_counts = self.scoring_engine.calculate_scores(responses)
        normalized_scores = self.scoring_engine.normalize_scores(raw_scores)
        
        # Get top types
        primary_type, secondary_type = self.scoring_engine.get_top_types(normalized_scores)
        primary_pct = normalized_scores[primary_type]
        secondary_pct = normalized_scores[secondary_type]
        
        # Check clarity
        is_unclear = self.scoring_engine.check_result_clarity(primary_pct, secondary_pct)
        
        # Suggest wing
        suggested_wing = self.scoring_engine.suggest_wing(primary_type, normalized_scores)
        
        # Gaming detection
        gaming_indicators = self.gaming_detector.analyze(responses)
        consistency_checks = self.gaming_detector.get_consistency_details(responses)
        
        # Determine confidence
        confidence = "high"
        if is_unclear or gaming_indicators.is_suspicious:
            confidence = "low"
        elif gaming_indicators.consistency_failures > 0:
            confidence = "medium"
        
        # Build type scores list
        all_scores = [
            TypeScore(
                type_number=t,
                raw_score=raw_scores[t],
                normalized_percentage=round(normalized_scores[t], 2),
                question_count=question_counts.get(t, 0)
            )
            for t in range(1, 10)
        ]
        all_scores.sort(key=lambda x: x.normalized_percentage, reverse=True)
        
        result = AssessmentResult(
            primary_type=primary_type,
            primary_percentage=round(primary_pct, 2),
            secondary_type=secondary_type,
            secondary_percentage=round(secondary_pct, 2),
            suggested_wing=suggested_wing,
            all_scores=all_scores,
            confidence_level=confidence,
            is_unclear=is_unclear,
            gaming_indicators=gaming_indicators,
            consistency_checks=consistency_checks
        )
        
        # Save result
        await self.session_manager.complete_session(session_id, result)
        
        return result
    
    def _format_result(self, result: AssessmentResult) -> Dict:
        """Format result for API response."""
        primary_desc = TYPE_DESCRIPTIONS.get(result.primary_type, {})
        secondary_desc = TYPE_DESCRIPTIONS.get(result.secondary_type, {})
        
        return {
            "primary_type": {
                "number": result.primary_type,
                "name": primary_desc.get("name", f"Type {result.primary_type}"),
                "percentage": result.primary_percentage,
                "core_desire": primary_desc.get("core_desire", ""),
                "core_fear": primary_desc.get("core_fear", ""),
                "brief": primary_desc.get("brief", "")
            },
            "secondary_type": {
                "number": result.secondary_type,
                "name": secondary_desc.get("name", f"Type {result.secondary_type}"),
                "percentage": result.secondary_percentage
            },
            "suggested_wing": result.suggested_wing,
            "full_type_string": f"{result.primary_type}w{result.suggested_wing}",
            "all_scores": [
                {
                    "type": s.type_number,
                    "name": TYPE_DESCRIPTIONS.get(s.type_number, {}).get("name", f"Type {s.type_number}"),
                    "percentage": s.normalized_percentage
                }
                for s in result.all_scores
            ],
            "confidence_level": result.confidence_level,
            "is_unclear": result.is_unclear,
            "flags": result.gaming_indicators.flags if result.gaming_indicators.is_suspicious else []
        }
    
    async def get_results(self, session_id: str) -> Optional[Dict]:
        """Get results for a completed session."""
        session = await self.session_manager.get_session(session_id)
        if not session or session["status"] != "completed":
            return None
        
        result_doc = await self.session_manager.results_collection.find_one(
            {"session_id": session_id}
        )
        if result_doc:
            result_doc.pop("_id", None)
        return result_doc
    
    async def resume_session(self, user_id: str) -> Optional[Dict]:
        """Resume an existing session for a user."""
        session = await self.session_manager.get_user_session(user_id)
        if not session:
            return None
        
        return {
            "status": "resumed",
            "session_id": session["session_id"],
            "current_index": session["current_question_index"],
            "total_questions": len(self.questions),
            "responses_count": len(session["responses"]),
            "next_batch": self._get_question_batch(session["current_question_index"])
        }

# =============================================================================
# API HELPER FUNCTIONS
# =============================================================================

def get_all_questions() -> List[Dict]:
    """Get all questions (for admin/testing)."""
    return QUESTION_BANK

def get_question_batch(start_index: int) -> List[Dict]:
    """Get a batch of questions."""
    end_index = min(start_index + QUESTIONS_PER_BATCH, len(QUESTION_BANK))
    return QUESTION_BANK[start_index:end_index]

def get_type_description(type_number: int) -> Dict:
    """Get description for a type."""
    return TYPE_DESCRIPTIONS.get(type_number, {})
