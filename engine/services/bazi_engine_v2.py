"""
BaZi (Four Pillars of Destiny) Engine V2 - Stable v1.1

A sovereign lens calculation engine for Four Pillars of Destiny.

Features:
- Structured response shape for Mirror UI
- Ten Gods weighted analysis (frequency + seasonal + position)
- Timing calculations (Today/Month/Year)
- Element interaction logic with Ten God override
- Mirror language interpretations
- Deep Dive: Day Master strength, favorable elements, behavioral patterns
- Life Pattern detection

Cross-Lens Architecture (v1.1):
- Outputs `pattern_domains` for future cross-lens synthesis
- Domains: self, relationships, work, stress, growth, timing
- NO forced mapping to other frameworks (HD, Enneagram, Numerology)
- Each lens remains sovereign
- Future synthesis can identify repeated themes WITHOUT equivalence rules

Calculation Methods:
- Classical Zi Ping (Four Pillars) backbone
- Ten Gods weighted scoring
- Element relationship + Ten God combined interaction model

@version 1.1
@date 2026-03-18
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple, List
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# FUNDAMENTAL CONSTANTS (from original engine)
# =============================================================================

HEAVENLY_STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
HEAVENLY_STEMS_PINYIN = ["Jia", "Yi", "Bing", "Ding", "Wu", "Ji", "Geng", "Xin", "Ren", "Gui"]

EARTHLY_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
EARTHLY_BRANCHES_PINYIN = ["Zi", "Chou", "Yin", "Mao", "Chen", "Si", "Wu", "Wei", "Shen", "You", "Xu", "Hai"]

# Animal mapping with emoji
BRANCH_ANIMALS = {
    "子": {"name": "Rat", "emoji": "🐀"},
    "丑": {"name": "Ox", "emoji": "🐂"},
    "寅": {"name": "Tiger", "emoji": "🐅"},
    "卯": {"name": "Rabbit", "emoji": "🐰"},
    "辰": {"name": "Dragon", "emoji": "🐲"},
    "巳": {"name": "Snake", "emoji": "🐍"},
    "午": {"name": "Horse", "emoji": "🐴"},
    "未": {"name": "Goat", "emoji": "🐐"},
    "申": {"name": "Monkey", "emoji": "🐒"},
    "酉": {"name": "Rooster", "emoji": "🐓"},
    "戌": {"name": "Dog", "emoji": "🐕"},
    "亥": {"name": "Pig", "emoji": "🐷"}
}

# Simple animal name lookup (for backward compat)
BRANCH_ANIMAL_NAMES = {k: v["name"] for k, v in BRANCH_ANIMALS.items()}

# Element mappings
STEM_ELEMENTS = {
    "甲": "Wood", "乙": "Wood", "丙": "Fire", "丁": "Fire",
    "戊": "Earth", "己": "Earth", "庚": "Metal", "辛": "Metal",
    "壬": "Water", "癸": "Water"
}

STEM_POLARITY = {
    "甲": "Yang", "乙": "Yin", "丙": "Yang", "丁": "Yin",
    "戊": "Yang", "己": "Yin", "庚": "Yang", "辛": "Yin",
    "壬": "Yang", "癸": "Yin"
}

BRANCH_ELEMENTS = {
    "子": "Water", "丑": "Earth", "寅": "Wood", "卯": "Wood",
    "辰": "Earth", "巳": "Fire", "午": "Fire", "未": "Earth",
    "申": "Metal", "酉": "Metal", "戌": "Earth", "亥": "Water"
}

BRANCH_HIDDEN_STEMS = {
    "子": ["癸"],
    "丑": ["己", "癸", "辛"],
    "寅": ["甲", "丙", "戊"],
    "卯": ["乙"],
    "辰": ["戊", "乙", "癸"],
    "巳": ["丙", "庚", "戊"],
    "午": ["丁", "己"],
    "未": ["己", "丁", "乙"],
    "申": ["庚", "壬", "戊"],
    "酉": ["辛"],
    "戌": ["戊", "辛", "丁"],
    "亥": ["壬", "甲"]
}

# Element cycles
ELEMENT_PRODUCES = {"Wood": "Fire", "Fire": "Earth", "Earth": "Metal", "Metal": "Water", "Water": "Wood"}
ELEMENT_CONTROLS = {"Wood": "Earth", "Fire": "Metal", "Earth": "Water", "Metal": "Wood", "Water": "Fire"}
ELEMENT_PRODUCED_BY = {v: k for k, v in ELEMENT_PRODUCES.items()}
ELEMENT_CONTROLLED_BY = {v: k for k, v in ELEMENT_CONTROLS.items()}

# Hour to branch mapping
HOUR_TO_BRANCH_INDEX = {
    23: 0, 0: 0, 1: 1, 2: 1, 3: 2, 4: 2, 5: 3, 6: 3,
    7: 4, 8: 4, 9: 5, 10: 5, 11: 6, 12: 6, 13: 7, 14: 7,
    15: 8, 16: 8, 17: 9, 18: 9, 19: 10, 20: 10, 21: 11, 22: 11
}

# Solar terms for month calculation
SOLAR_TERMS_APPROX = {
    1: (2, 4), 2: (3, 6), 3: (4, 5), 4: (5, 6),
    5: (6, 6), 6: (7, 7), 7: (8, 8), 8: (9, 8),
    9: (10, 8), 10: (11, 7), 11: (12, 7), 12: (1, 6),
}

# =============================================================================
# TEN GODS SYSTEM
# =============================================================================

TEN_GODS_MAP = {
    ("same", "same"): "companion",
    ("same", "different"): "rob_wealth",
    ("I_produce", "same"): "eating_god",
    ("I_produce", "different"): "hurting_officer",
    ("I_control", "same"): "indirect_wealth",
    ("I_control", "different"): "direct_wealth",
    ("controls_me", "same"): "seven_killings",
    ("controls_me", "different"): "direct_officer",
    ("produces_me", "same"): "indirect_seal",
    ("produces_me", "different"): "direct_seal",
}

# Ten Gods categories for summary
TEN_GODS_CATEGORIES = {
    "resource": ["direct_seal", "indirect_seal"],
    "output": ["eating_god", "hurting_officer"],
    "wealth": ["direct_wealth", "indirect_wealth"],
    "officer": ["direct_officer", "seven_killings"],
    "companion": ["companion", "rob_wealth"],
}

TEN_GODS_DISPLAY = {
    "companion": {"name": "Companion", "chinese": "比肩"},
    "rob_wealth": {"name": "Competitor", "chinese": "劫财"},
    "eating_god": {"name": "Output", "chinese": "食神"},
    "hurting_officer": {"name": "Expression", "chinese": "伤官"},
    "indirect_wealth": {"name": "Opportunity", "chinese": "偏财"},
    "direct_wealth": {"name": "Stability", "chinese": "正财"},
    "seven_killings": {"name": "Power", "chinese": "七杀"},
    "direct_officer": {"name": "Structure", "chinese": "正官"},
    "indirect_seal": {"name": "Insight", "chinese": "偏印"},
    "direct_seal": {"name": "Resource", "chinese": "正印"},
}

# Position weights for Ten Gods scoring
POSITION_WEIGHTS = {
    "month_branch": 3.0,  # Highest - career/outer world
    "month_stem": 2.5,
    "day_branch": 2.0,    # Self/partnerships
    "year_stem": 1.5,
    "year_branch": 1.5,
    "hour_stem": 1.0,
    "hour_branch": 1.0,
}

# Seasonal strength by element
SEASON_ELEMENT_STRENGTH = {
    "spring": {"Wood": 1.5, "Fire": 1.2, "Water": 0.8, "Metal": 0.6, "Earth": 1.0},
    "summer": {"Fire": 1.5, "Earth": 1.2, "Wood": 0.8, "Water": 0.6, "Metal": 1.0},
    "late_summer": {"Earth": 1.5, "Metal": 1.2, "Fire": 0.8, "Wood": 0.6, "Water": 1.0},
    "autumn": {"Metal": 1.5, "Water": 1.2, "Earth": 0.8, "Fire": 0.6, "Wood": 1.0},
    "winter": {"Water": 1.5, "Wood": 1.2, "Metal": 0.8, "Earth": 0.6, "Fire": 1.0},
}

# =============================================================================
# DAY MASTER KEYWORDS & DESCRIPTIONS (Mirror Language - UPGRADED)
# =============================================================================

DAY_MASTER_PROFILES = {
    ("Wood", "Yang"): {
        "keywords": ["initiative", "growth", "leadership"],
        "wow_line": "You don't wait for permission — you move first and figure it out later.",
        "description": "You push through obstacles that stop others. You start things. You lead by moving, not by planning.",
        "strength_strong": "Your drive is powerful and accessible. The work: knowing when to pause and let others catch up.",
        "strength_weak": "You see the path forward but feel blocked from taking it. The work: building support before the sprint.",
        "why_pattern": "Strong Wood creates forward momentum. Your chart generates natural leadership energy that makes inaction uncomfortable.",
    },
    ("Wood", "Yin"): {
        "keywords": ["adaptability", "persistence", "connection"],
        "wow_line": "You grow around obstacles that stop others cold.",
        "description": "You find ways through resistance that others can't see. You persist quietly, bending without breaking.",
        "strength_strong": "Your flexibility is genuine strength. The work: not avoiding confrontation when it's actually needed.",
        "strength_weak": "You get swayed too easily. The work: finding your root before trying to grow.",
        "why_pattern": "Yin Wood adapts to survive. Your chart emphasizes connection and persistence over force.",
    },
    ("Fire", "Yang"): {
        "keywords": ["clarity", "warmth", "visibility"],
        "wow_line": "You light up rooms without trying — and notice when others dim.",
        "description": "You illuminate situations. You draw attention naturally. You see clearly and connect warmly.",
        "strength_strong": "Your presence fills space. The work: sustaining without burning out or needing constant fuel.",
        "strength_weak": "Your inner light struggles to express outward. The work: finding safe spaces where you can actually shine.",
        "why_pattern": "Yang Fire radiates outward. Your chart generates visibility and clarity that makes hiding uncomfortable.",
    },
    ("Fire", "Yin"): {
        "keywords": ["nurturing warmth", "steady light", "patience"],
        "wow_line": "You're the candle that stays lit when the bonfire burns out.",
        "description": "Your warmth is consistent, not dramatic. You nurture through steady presence, not grand gestures.",
        "strength_strong": "Your steady warmth is reliable. The work: not dimming yourself to make others comfortable.",
        "strength_weak": "Your inner light flickers. The work: protecting your energy sources before they run dry.",
        "why_pattern": "Yin Fire sustains through consistency. Your chart values endurance over intensity.",
    },
    ("Earth", "Yang"): {
        "keywords": ["stability", "reliability", "containment"],
        "wow_line": "You're the mountain people lean on when everything else shakes.",
        "description": "You hold space that others can't. You're solid when others crumble. You contain what would overflow.",
        "strength_strong": "Your stability is real and others sense it. The work: not becoming so solid you can't move.",
        "strength_weak": "You want to be the ground but feel unsteady yourself. The work: building your foundation first.",
        "why_pattern": "Yang Earth provides structure. Your chart generates stability that makes chaos uncomfortable.",
    },
    ("Earth", "Yin"): {
        "keywords": ["nurturing", "receptivity", "cultivation"],
        "wow_line": "You grow what you touch — sometimes at the cost of yourself.",
        "description": "You create conditions for others to flourish. You receive, process, and make things fertile.",
        "strength_strong": "Your nurturing capacity is powerful. The work: not over-giving until you're depleted.",
        "strength_weak": "You want to help but feel empty. The work: learning to receive as much as you give.",
        "why_pattern": "Yin Earth cultivates growth in others. Your chart emphasizes support over self-assertion.",
    },
    ("Metal", "Yang"): {
        "keywords": ["decisiveness", "standards", "boundaries"],
        "wow_line": "You cut through confusion that paralyzes others — sometimes too quickly.",
        "description": "You see what matters and what doesn't. You decide when others deliberate. You hold standards others avoid.",
        "strength_strong": "Your discernment is sharp and fast. The work: not becoming rigid or expecting others to match you.",
        "strength_weak": "You see what needs cutting but can't pull the trigger. The work: trusting your judgment enough to act.",
        "why_pattern": "Yang Metal creates clarity through elimination. Your chart generates decisiveness that makes ambiguity uncomfortable.",
    },
    ("Metal", "Yin"): {
        "keywords": ["precision", "discernment", "refinement"],
        "wow_line": "You don't move fast — you move right. And you notice when others don't.",
        "description": "You catch details others miss. You hold yourself to precise internal standards. You prefer less but better.",
        "strength_strong": "Your precision is a gift. The work: not letting high standards become self-criticism.",
        "strength_weak": "You crave precision but feel scattered. The work: creating small pockets of order to anchor yourself.",
        "why_pattern": "Yin Metal refines through attention to detail. Your chart generates quality consciousness that makes sloppiness painful.",
    },
    ("Water", "Yang"): {
        "keywords": ["momentum", "adaptability", "courage"],
        "wow_line": "You flow around obstacles that stop others — and sometimes can't stop yourself.",
        "description": "You adapt while maintaining momentum. You face the unknown with less fear than most.",
        "strength_strong": "Your adaptability and momentum are powerful. The work: knowing when to stop rather than always moving.",
        "strength_weak": "You feel stuck in still waters. The work: finding what creates natural movement for you.",
        "why_pattern": "Yang Water moves through obstacles. Your chart generates forward flow that makes stagnation uncomfortable.",
    },
    ("Water", "Yin"): {
        "keywords": ["depth", "reflection", "intuition"],
        "wow_line": "You understand things before you can explain them — and sometimes before you should.",
        "description": "You perceive undercurrents others miss. You know things before you have words for them.",
        "strength_strong": "Your depth and intuition are accessible. The work: not getting lost in inner waters.",
        "strength_weak": "You feel disconnected from your intuition. The work: creating stillness so you can hear yourself.",
        "why_pattern": "Yin Water perceives through stillness. Your chart generates intuitive knowing that makes surface living unsatisfying.",
    },
}

# =============================================================================
# DEEP DIVE: TEN GODS BEHAVIORAL TEMPLATES (UPGRADED)
# =============================================================================

TEN_GODS_BEHAVIORAL = {
    "resource": {
        "category": "resource",
        "label": "Resource / Seal",
        "wow_line": "You trust your own thinking more than other people's urgency.",
        "behavioral_high": "You slow down to understand before acting — which creates delays when speed matters. You process internally, research thoroughly, and prepare carefully.",
        "behavioral_low": "You jump without enough preparation. Building a stronger foundation of knowledge and support helps.",
        "stress_pattern": "Under pressure, you retreat into analysis mode — researching more, deciding less, waiting for certainty that never comes.",
        "others_experience": "People see you as thoughtful but slow. They come to you for wisdom but get frustrated waiting for action.",
        "risk": "Overthinking becomes avoidance. You gather more information instead of making the call.",
        "insight": "You understand before doing",
        "tension": "This delays necessary action",
        "action": "Set a decision deadline before you start researching",
        "why_pattern": "Strong Resource energy supports your Day Master, making you process and analyze before acting. This creates wisdom but also hesitation.",
        "go_deeper": "Resource (印星) represents support, learning, and protection. High Resource creates a tendency to seek understanding before commitment. The risk is analysis paralysis.",
    },
    "output": {
        "category": "output",
        "label": "Output / Expression",
        "wow_line": "You create to exist — holding back feels like suffocating.",
        "behavioral_high": "You express, create, and put things into the world constantly. Ideas demand to become visible through you.",
        "behavioral_low": "Expression feels blocked or unsafe. Finding trusted outlets for creativity matters.",
        "stress_pattern": "Under pressure, you over-express — talking too much, creating chaotically, becoming provocative to force a reaction.",
        "others_experience": "People see you as creative and expressive. They find you inspiring but exhausting.",
        "risk": "Energy scatters across too many outputs. You express before thinking through consequences.",
        "insight": "You create to process",
        "tension": "This scatters your focus",
        "action": "Complete one thing before starting another",
        "why_pattern": "Strong Output energy drains from your Day Master into creation. This makes expression necessary but potentially depleting.",
        "go_deeper": "Output (食傷) represents expression, creativity, and talent. High Output drives creation but can exhaust the self if not managed.",
    },
    "wealth": {
        "category": "wealth",
        "label": "Wealth / Execution",
        "wow_line": "You measure progress in results, not intentions — and get impatient with people who don't.",
        "behavioral_high": "You focus on results and practical outcomes. Getting things done, managing resources, and seeing tangible progress drives you.",
        "behavioral_low": "Practical execution drains you. Delegating or simplifying what you're managing helps.",
        "stress_pattern": "Under pressure, you become controlling — managing, organizing, directing — at the expense of other values.",
        "others_experience": "People see you as capable and results-oriented. They rely on you but find you focused on outcomes over relationships.",
        "risk": "Productivity becomes the only value. You lose sight of why results matter.",
        "insight": "You execute to feel secure",
        "tension": "This makes you impatient with process",
        "action": "Ask what outcome actually matters before optimizing",
        "why_pattern": "Strong Wealth energy means your Day Master controls resources effectively. This creates capability but also restlessness without progress.",
        "go_deeper": "Wealth (財星) represents what you control and manage. High Wealth creates results-orientation but can become obsessive about productivity.",
    },
    "officer": {
        "category": "officer",
        "label": "Officer / Structure",
        "wow_line": "You feel responsible for things that aren't your job — and resent when others don't.",
        "behavioral_high": "You have a strong relationship with structure, rules, and responsibility. You take on duties naturally and feel the weight of expectations.",
        "behavioral_low": "Structure feels oppressive rather than supportive. Creating your own frameworks helps.",
        "stress_pattern": "Under pressure, you become rigid, over-responsible, or feel trapped by obligations you didn't choose.",
        "others_experience": "People see you as responsible and trustworthy. They rely on you heavily, taking your dependability for granted.",
        "risk": "You over-identify with duty. Personal needs get sacrificed for perceived obligations.",
        "insight": "You structure to feel safe",
        "tension": "This makes you rigid under pressure",
        "action": "Distinguish duties you chose from duties you inherited",
        "why_pattern": "Strong Officer energy controls your Day Master through structure. This creates reliability but also pressure and rigidity.",
        "go_deeper": "Officer (官星) represents external authority, structure, and pressure. High Officer creates responsibility but can feel like constant obligation.",
    },
    "companion": {
        "category": "companion",
        "label": "Companion / Self",
        "wow_line": "You compete with yourself more than anyone else — and still rarely win.",
        "behavioral_high": "You have strong independence and self-reliance. Peer relationships come easily, though you notice competition more than collaboration.",
        "behavioral_low": "You struggle with isolation or finding your tribe. Building genuine peer connections helps.",
        "stress_pattern": "Under pressure, you become competitive — comparing yourself to others, feeling threatened by their success.",
        "others_experience": "People see you as confident and self-sufficient. They admire your independence but find it hard to help you.",
        "risk": "You isolate or compete when collaboration would serve better. You resist help.",
        "insight": "You rely on yourself first",
        "tension": "This isolates you from support",
        "action": "Ask for help before you need it",
        "why_pattern": "Strong Companion energy means your Day Master has peer support. This creates independence but also isolation and competition.",
        "go_deeper": "Companion (比劫) represents self and peers. High Companion creates self-reliance but can become isolation or rivalry.",
    },
}

# =============================================================================
# HIDDEN STEM MEANINGS (UPGRADED - BEHAVIORAL)
# =============================================================================

HIDDEN_STEM_MEANINGS = {
    "甲": {
        "name": "Hidden Wood (Jia)",
        "description": "An underlying drive to grow, initiate, or push forward that operates beneath your conscious awareness.",
        "behavioral": "You make sudden moves when you feel stuck. Under pressure, you push forward even when patience would serve better.",
        "shows_up": "Impatience with stagnation, unexpected bursts of initiative, frustration when growth feels blocked.",
    },
    "乙": {
        "name": "Hidden Wood (Yi)",
        "description": "A subtle adaptability or networking instinct operating beneath the surface.",
        "behavioral": "You find alternative routes instinctively. When blocked, you bend rather than break — sometimes avoiding necessary confrontation.",
        "shows_up": "Quiet persistence, relationship-building without trying, flexibility that can look like inconsistency.",
    },
    "丙": {
        "name": "Hidden Fire (Bing)",
        "description": "An inner warmth or desire for visibility that doesn't always show externally.",
        "behavioral": "You notice when you're not being seen. You draw attention in unexpected moments, even when you don't intend to.",
        "shows_up": "Sudden clarity about situations, unexpected warmth toward others, frustration when overlooked.",
    },
    "丁": {
        "name": "Hidden Fire (Ding)",
        "description": "A quiet nurturing warmth or steady illumination working in the background.",
        "behavioral": "You provide consistent support without fanfare. You're the candle that stays lit when others burn out.",
        "shows_up": "Patient teaching, steady encouragement, warmth that emerges in crisis rather than celebration.",
    },
    "戊": {
        "name": "Hidden Earth (Wu)",
        "description": "An underlying need for stability or containment that influences decisions.",
        "behavioral": "You create structure when things feel chaotic. You become the solid ground for others, sometimes at your own expense.",
        "shows_up": "Taking responsibility during uncertainty, preference for reliable over exciting, resistance to sudden change.",
    },
    "己": {
        "name": "Hidden Earth (Ji)",
        "description": "A subtle nurturing quality or desire to support growth operating beneath awareness.",
        "behavioral": "You cultivate others' potential without realizing it. You process and transform what others give you.",
        "shows_up": "Being the one people come to, absorbing others' stress, growing what you touch.",
    },
    "庚": {
        "name": "Hidden Metal (Geng)",
        "description": "An underlying decisiveness or critical faculty that emerges under pressure.",
        "behavioral": "You make fast judgments under pressure. You become sharply critical when things don't meet standards you didn't know you had.",
        "shows_up": "Snap decisions in crisis, unexpected harshness, sudden clarity about what needs cutting.",
    },
    "辛": {
        "name": "Hidden Metal (Xin)",
        "description": "A subtle precision or refinement instinct influencing choices without being obvious.",
        "behavioral": "You notice quality differences others miss. You hold internal standards you rarely articulate but always feel.",
        "shows_up": "Preference for quality over quantity, noticing imperfections, silent disappointment with sloppiness.",
    },
    "壬": {
        "name": "Hidden Water (Ren)",
        "description": "An underlying adaptability or willingness to flow that isn't consciously accessed.",
        "behavioral": "You navigate around obstacles instinctively. You face the unknown with less fear than you realize.",
        "shows_up": "Unexpected courage in uncertainty, flowing around blockers, momentum that builds without planning.",
    },
    "癸": {
        "name": "Hidden Water (Gui)",
        "description": "A deep intuitive perception or reflective quality operating beneath the surface.",
        "behavioral": "You know things before you can explain them. You perceive undercurrents others miss entirely.",
        "shows_up": "Accurate gut feelings, sensing what's not being said, understanding before explanation.",
    },
}

# =============================================================================
# DEEP DIVE: LIFE PATTERN TEMPLATES BY DAY MASTER (UPGRADED)
# =============================================================================

LIFE_PATTERN_TEMPLATES = {
    ("Wood", "Yang"): {
        "core_drive": "To initiate, grow, and lead forward motion",
        "wow_line": "You don't wait for permission — you move first.",
        "default_mode": "You push through obstacles and start things. You're the one who says 'let's go' when others are still planning.",
        "under_pressure": "You become forceful, impatient, and bulldoze through situations that require finesse. Your drive intensifies but judgment narrows.",
        "growth_direction": "Learning to pause, delegate, and trust others' timelines. Fire channels your energy; Metal refines it.",
        "why_pattern": "Strong Yang Wood creates relentless forward momentum. Your chart is built for initiation, making inaction feel like failure.",
    },
    ("Wood", "Yin"): {
        "core_drive": "To adapt, connect, and find ways through",
        "wow_line": "You grow around obstacles that stop others cold.",
        "default_mode": "You bend rather than break. You find alternative routes and build networks. Growth happens sideways as much as upward.",
        "under_pressure": "You become overly accommodating, losing your direction while adapting to everyone else's. Flexibility becomes indecision.",
        "growth_direction": "Building a stronger center that bends but doesn't break. Fire helps you express; Water helps you trust your flow.",
        "why_pattern": "Yin Wood survives through adaptation. Your chart emphasizes connection and persistence over direct force.",
    },
    ("Fire", "Yang"): {
        "core_drive": "To illuminate, inspire, and be seen",
        "wow_line": "You light up rooms without trying — and notice when others dim.",
        "default_mode": "You draw attention and clarify situations naturally. Your presence fills space. You end up leading even when you don't try.",
        "under_pressure": "You burn hot and fast — dramatic reactions, visibility at all costs, exhaustion from sustaining high energy.",
        "growth_direction": "Learning to sustain rather than blaze. Wood feeds you constructively; Earth keeps you from burning out.",
        "why_pattern": "Yang Fire radiates outward. Your chart generates visibility and warmth that makes hiding feel wrong.",
    },
    ("Fire", "Yin"): {
        "core_drive": "To nurture warmth and maintain steady light",
        "wow_line": "You're the candle that stays lit when the bonfire burns out.",
        "default_mode": "You provide consistent warmth rather than dramatic heat. You nurture through steady presence.",
        "under_pressure": "You dim yourself to make others comfortable, or flicker erratically when your fuel runs low.",
        "growth_direction": "Trusting that your light is needed, even when it feels small. Wood supports you; Earth grounds you.",
        "why_pattern": "Yin Fire sustains through consistency. Your chart values endurance and quiet illumination over spectacle.",
    },
    ("Earth", "Yang"): {
        "core_drive": "To stabilize, contain, and provide solid ground",
        "wow_line": "You're the mountain people lean on when everything else shakes.",
        "default_mode": "You hold space that others can't. You're solid when others crumble. Stability comes naturally.",
        "under_pressure": "You become immovable, stubborn, or weighted down by everything you're carrying. Stability becomes rigidity.",
        "growth_direction": "Learning that flexibility is not weakness. Metal helps you refine; Fire helps you transform what's stuck.",
        "why_pattern": "Yang Earth provides structure. Your chart generates stability that makes chaos uncomfortable.",
    },
    ("Earth", "Yin"): {
        "core_drive": "To nurture, support, and cultivate growth in others",
        "wow_line": "You grow what you touch — sometimes at the cost of yourself.",
        "default_mode": "You create conditions for things to flourish. You receive, process, and make fertile. Others grow in your presence.",
        "under_pressure": "You over-give, lose yourself in others' needs, or feel depleted by constant nurturing without receiving.",
        "growth_direction": "Learning to receive as much as you give. Metal helps you set boundaries; Water helps you restore.",
        "why_pattern": "Yin Earth cultivates growth in others. Your chart emphasizes support and receptivity over self-assertion.",
    },
    ("Metal", "Yang"): {
        "core_drive": "To decide, cut through, and hold standards",
        "wow_line": "You cut through confusion that paralyzes others — sometimes too quickly.",
        "default_mode": "You see what matters and what doesn't. You decide when others deliberate. You hold standards others avoid.",
        "under_pressure": "You become harsh, judgmental, or rigidly attached to being right. Clarity becomes coldness.",
        "growth_direction": "Learning that not everything needs cutting. Water softens you; Earth gives patience.",
        "why_pattern": "Yang Metal eliminates to clarify. Your chart generates decisiveness that makes ambiguity uncomfortable.",
    },
    ("Metal", "Yin"): {
        "core_drive": "To refine, perfect, and notice what others miss",
        "wow_line": "You don't move fast — you move right. And you notice when others don't.",
        "default_mode": "You see the small things. Quality matters more than quantity. You prefer less but better.",
        "under_pressure": "You become overly critical — of yourself first, then others. Precision becomes perfectionism.",
        "growth_direction": "Learning that 'good enough' is sometimes perfect. Water helps you flow; Fire helps you express without judgment.",
        "why_pattern": "Yin Metal refines through attention. Your chart generates quality consciousness that makes sloppiness painful.",
    },
    ("Water", "Yang"): {
        "core_drive": "To move, adapt, and face the unknown",
        "wow_line": "You flow around obstacles that stop others — and sometimes can't stop yourself.",
        "default_mode": "You navigate around obstacles rather than through them. You're comfortable with uncertainty that paralyzes others.",
        "under_pressure": "You become scattered, always moving but never arriving, or reckless in the face of danger.",
        "growth_direction": "Learning when to stop flowing and take root. Wood gives you direction; Earth gives stability.",
        "why_pattern": "Yang Water moves through obstacles. Your chart generates forward flow that makes stagnation unbearable.",
    },
    ("Water", "Yin"): {
        "core_drive": "To understand depths and trust intuition",
        "wow_line": "You understand things before you can explain them — and sometimes before you should.",
        "default_mode": "You perceive undercurrents. You understand things before you can explain them. Stillness reveals what movement hides.",
        "under_pressure": "You withdraw into inner depths, becoming hard to reach, or lose yourself in reflection without action.",
        "growth_direction": "Learning to surface and share what you know. Wood helps you grow outward; Fire helps you express.",
        "why_pattern": "Yin Water perceives through stillness. Your chart generates intuitive knowing that makes surface living unsatisfying.",
    },
}

# =============================================================================
# PILLAR MEANING LABELS
# =============================================================================

PILLAR_MEANINGS = {
    "year": {
        "label": "Roots",
        "description": "Early life, family patterns, and inherited tendencies"
    },
    "month": {
        "label": "Work",
        "description": "Career, outer world, how you're seen professionally"
    },
    "day": {
        "label": "Self",
        "description": "Core identity, partnerships, how you naturally operate"
    },
    "hour": {
        "label": "Inner World",
        "description": "Inner life, later years, private self"
    },
}

# =============================================================================
# TIMING INTERACTION DESCRIPTIONS (Mirror Language)
# =============================================================================

TIMING_DESCRIPTIONS = {
    "today": {
        "supporting": {
            "resource": "A good day for learning, receiving support, or letting yourself be helped.",
            "output": "Energy may flow toward expression and creation. Good for putting things out there.",
            "companion": "Collaboration feels easier today. Working alongside others may be energizing.",
            "wealth": "Practical matters may click into place. Good for getting things done.",
        },
        "pressure": {
            "officer": "You may feel more observed or held to expectations. Structure may feel tight.",
            "seven_killings": "Pressure may feel more intense today. Pick your battles carefully.",
            "controls": "Something may be pushing against your natural flow. Notice where you feel resistance.",
        },
        "mixed": {
            "default": "Mixed signals today—some support, some friction. Stay flexible.",
        }
    },
    "month": {
        "supporting": {
            "resource": "This month may favor learning, receiving guidance, or deepening understanding.",
            "output": "Expression and visibility may be heightened. Good for putting work out there.",
            "companion": "Collaborations and peer connections may be fruitful this month.",
            "wealth": "Practical execution may be favored. Good for making progress on tangible goals.",
        },
        "pressure": {
            "officer": "This month may bring increased expectations or responsibility.",
            "seven_killings": "Pressure may be running higher. Pace yourself and prioritize.",
            "controls": "Some resistance to your natural rhythm. Adaptation may be required.",
        },
        "mixed": {
            "default": "This month holds both opportunity and challenge. Selective focus helps.",
        }
    },
    "year": {
        "supporting": {
            "resource": "This year favors growth, learning, and building foundations.",
            "output": "A year where what you create may find more visibility and impact.",
            "companion": "Relationships and collaborations may be particularly significant this year.",
            "wealth": "Practical accomplishments may be more accessible. Good for execution.",
        },
        "pressure": {
            "officer": "This year may ask more of you—more structure, more responsibility.",
            "seven_killings": "A year of intensity. Transformative but demanding.",
            "controls": "Some of your natural tendencies may meet resistance. Growth through adaptation.",
        },
        "mixed": {
            "default": "A year of both expansion and consolidation. Balance matters.",
        }
    }
}

# =============================================================================
# CORE CALCULATION FUNCTIONS
# =============================================================================

def get_chinese_year(dt: datetime) -> int:
    """Get Chinese year, accounting for Start of Spring (~Feb 4)."""
    year = dt.year
    if dt < datetime(year, 2, 4):
        year -= 1
    return year

def get_bazi_month(dt: datetime) -> int:
    """Get BaZi month number based on solar terms."""
    month, day = dt.month, dt.day
    for bazi_month, (solar_month, solar_day) in SOLAR_TERMS_APPROX.items():
        if month == solar_month:
            if day >= solar_day:
                return bazi_month
            else:
                return (bazi_month - 2) % 12 + 1
    # Fallback
    month_map = {1: 12, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 7, 9: 8, 10: 9, 11: 10, 12: 11}
    return month_map.get(month, 1)

def get_season(bazi_month: int) -> str:
    """Get season from BaZi month."""
    if bazi_month in [1, 2, 3]:
        return "spring"
    elif bazi_month in [4, 5, 6]:
        return "summer"
    elif bazi_month == 6:  # Actually late summer is month 6
        return "late_summer"
    elif bazi_month in [7, 8, 9]:
        return "autumn"
    else:
        return "winter"

def calculate_year_pillar(year: int) -> Tuple[str, str, int, int]:
    """Calculate Year Pillar. Reference: 1984 = Jia Zi."""
    offset = year - 1984
    stem_idx = offset % 10
    branch_idx = offset % 12
    return HEAVENLY_STEMS[stem_idx], EARTHLY_BRANCHES[branch_idx], stem_idx, branch_idx

def calculate_month_pillar(year_stem_idx: int, bazi_month: int) -> Tuple[str, str, int, int]:
    """Calculate Month Pillar using Five Tigers Escape formula."""
    branch_idx = (bazi_month + 1) % 12
    year_stem_base = year_stem_idx % 5
    first_month_stem_map = {0: 2, 1: 4, 2: 6, 3: 8, 4: 0}
    stem_idx = (first_month_stem_map[year_stem_base] + bazi_month - 1) % 10
    return HEAVENLY_STEMS[stem_idx], EARTHLY_BRANCHES[branch_idx], stem_idx, branch_idx

def calculate_day_pillar(dt: datetime) -> Tuple[str, str, int, int]:
    """Calculate Day Pillar. Reference: Jan 1, 1900 = Jia Xu."""
    reference = datetime(1900, 1, 1)
    days_diff = (dt - reference).days
    stem_idx = days_diff % 10
    branch_idx = (10 + days_diff) % 12
    return HEAVENLY_STEMS[stem_idx], EARTHLY_BRANCHES[branch_idx], stem_idx, branch_idx

def calculate_hour_pillar(day_stem_idx: int, hour: int) -> Tuple[str, str, int, int]:
    """Calculate Hour Pillar using Five Rats Escape formula."""
    branch_idx = HOUR_TO_BRANCH_INDEX.get(hour, 0)
    day_stem_base = day_stem_idx % 5
    first_hour_stem_map = {0: 0, 1: 2, 2: 4, 3: 6, 4: 8}
    stem_idx = (first_hour_stem_map[day_stem_base] + branch_idx) % 10
    return HEAVENLY_STEMS[stem_idx], EARTHLY_BRANCHES[branch_idx], stem_idx, branch_idx

def parse_birth_time(time_str: Optional[str]) -> Optional[Tuple[int, int]]:
    """Parse birth time string into (hour, minute)."""
    if not time_str:
        return None
    import re
    time_str = time_str.strip().lower()
    
    # Try HH:MM
    match = re.match(r'^(\d{1,2}):(\d{2})(?::\d{2})?$', time_str)
    if match:
        return int(match.group(1)), int(match.group(2))
    
    # Try 12-hour with am/pm
    match = re.match(r'^(\d{1,2}):(\d{2})\s*(am|pm)$', time_str)
    if match:
        hour, minute, period = int(match.group(1)), int(match.group(2)), match.group(3)
        if period == 'pm' and hour != 12:
            hour += 12
        elif period == 'am' and hour == 12:
            hour = 0
        return hour, minute
    
    return None

# =============================================================================
# TEN GODS CALCULATION
# =============================================================================

def get_ten_god(day_master_stem: str, target_stem: str) -> str:
    """Calculate Ten God relationship between Day Master and target stem."""
    if target_stem == day_master_stem:
        return "companion"
    
    dm_element = STEM_ELEMENTS[day_master_stem]
    dm_polarity = STEM_POLARITY[day_master_stem]
    target_element = STEM_ELEMENTS[target_stem]
    target_polarity = STEM_POLARITY[target_stem]
    
    polarity_match = "same" if dm_polarity == target_polarity else "different"
    
    if target_element == dm_element:
        relationship = "same"
    elif ELEMENT_PRODUCES[dm_element] == target_element:
        relationship = "I_produce"
    elif ELEMENT_CONTROLS[dm_element] == target_element:
        relationship = "I_control"
    elif ELEMENT_CONTROLS[target_element] == dm_element:
        relationship = "controls_me"
    elif ELEMENT_PRODUCES[target_element] == dm_element:
        relationship = "produces_me"
    else:
        return "companion"  # fallback
    
    return TEN_GODS_MAP.get((relationship, polarity_match), "companion")

def calculate_ten_gods_weighted(day_master_stem: str, pillars: Dict, season: str) -> Dict[str, Any]:
    """
    Calculate Ten Gods with weighted scoring.
    
    Weights:
    - Position: month_branch > day_branch > year/hour
    - Seasonal strength of the element
    - Frequency
    """
    dm_element = STEM_ELEMENTS[day_master_stem]
    season_strengths = SEASON_ELEMENT_STRENGTH.get(season, SEASON_ELEMENT_STRENGTH["spring"])
    
    ten_gods_scores = {}
    ten_gods_present = set()
    position_ten_gods = {}
    
    # Process each position
    positions = [
        ("year_stem", pillars["year"]["stem"]),
        ("year_branch", pillars["year"]["branch"]),
        ("month_stem", pillars["month"]["stem"]),
        ("month_branch", pillars["month"]["branch"]),
        ("day_branch", pillars["day"]["branch"]),  # Day stem is Self
        ("hour_stem", pillars["hour"]["stem"]),
        ("hour_branch", pillars["hour"]["branch"]),
    ]
    
    for position, char in positions:
        # Get element from stem or branch
        if "stem" in position:
            element = STEM_ELEMENTS.get(char)
            ten_god = get_ten_god(day_master_stem, char)
        else:
            element = BRANCH_ELEMENTS.get(char)
            # For branch, use main hidden stem
            hidden = BRANCH_HIDDEN_STEMS.get(char, [])
            if hidden:
                ten_god = get_ten_god(day_master_stem, hidden[0])
            else:
                continue
        
        if not element:
            continue
        
        # Calculate weight
        position_weight = POSITION_WEIGHTS.get(position, 1.0)
        seasonal_weight = season_strengths.get(element, 1.0)
        total_weight = position_weight * seasonal_weight
        
        # Accumulate score
        if ten_god not in ten_gods_scores:
            ten_gods_scores[ten_god] = 0
        ten_gods_scores[ten_god] += total_weight
        ten_gods_present.add(ten_god)
        
        # Track position
        position_ten_gods[position] = {
            "ten_god": ten_god,
            "element": element,
            "weight": total_weight
        }
    
    # Sort by score for dominant
    sorted_gods = sorted(ten_gods_scores.items(), key=lambda x: x[1], reverse=True)
    dominant = [g[0] for g in sorted_gods[:2]] if sorted_gods else []
    
    # Map to categories
    categories_present = set()
    for god in ten_gods_present:
        for cat, members in TEN_GODS_CATEGORIES.items():
            if god in members:
                categories_present.add(cat)
    
    return {
        "dominant": dominant,
        "present": list(ten_gods_present),
        "categories_present": list(categories_present),
        "scores": ten_gods_scores,
        "by_position": position_ten_gods,
    }

# =============================================================================
# ELEMENT ANALYSIS
# =============================================================================

def calculate_elements(pillars: Dict) -> Dict[str, float]:
    """Calculate Five Elements distribution with proper weighting."""
    elements = {"Wood": 0, "Fire": 0, "Earth": 0, "Metal": 0, "Water": 0}
    
    for pillar_name, pillar in pillars.items():
        stem = pillar["stem"]
        branch = pillar["branch"]
        
        # Stem weight: 1.0
        stem_elem = STEM_ELEMENTS.get(stem)
        if stem_elem:
            elements[stem_elem] += 1.0
        
        # Branch main element: 0.5
        branch_elem = BRANCH_ELEMENTS.get(branch)
        if branch_elem:
            elements[branch_elem] += 0.5
        
        # Hidden stems: 0.3 each
        for hidden in BRANCH_HIDDEN_STEMS.get(branch, []):
            hidden_elem = STEM_ELEMENTS.get(hidden)
            if hidden_elem:
                elements[hidden_elem] += 0.3
    
    return {k: round(v, 1) for k, v in elements.items()}

def analyze_elements(elements: Dict[str, float], day_master_element: str) -> Dict[str, Any]:
    """Analyze element balance relative to Day Master."""
    total = sum(elements.values())
    sorted_elems = sorted(elements.items(), key=lambda x: x[1], reverse=True)
    
    dominant = [e[0] for e in sorted_elems[:2] if e[1] > total * 0.2]
    weak = [e[0] for e in sorted_elems if e[1] < total * 0.1]
    
    # Supporting elements: what produces DM + same as DM
    supporting = [day_master_element]
    for elem, produces in ELEMENT_PRODUCES.items():
        if produces == day_master_element:
            supporting.append(elem)
    
    # Balancing elements: what DM needs more of (weak elements that help)
    balancing = weak if weak else []
    
    # Day Master strength
    dm_score = elements.get(day_master_element, 0)
    producer = ELEMENT_PRODUCED_BY.get(day_master_element)
    support_score = dm_score + (elements.get(producer, 0) if producer else 0)
    is_strong = support_score >= total * 0.4
    
    return {
        "dominant": dominant,
        "weak": weak,
        "supporting": supporting,
        "balancing": balancing,
        "day_master_strength": "strong" if is_strong else "weak",
        "percentages": {k: round(v / total * 100, 1) if total > 0 else 0 for k, v in elements.items()},
    }

# =============================================================================
# TIMING CALCULATIONS
# =============================================================================

def calculate_current_pillar(dt: datetime) -> Dict[str, Any]:
    """Calculate pillar for a given date (used for today/month/year)."""
    chinese_year = get_chinese_year(dt)
    bazi_month = get_bazi_month(dt)
    
    year_stem, year_branch, year_stem_idx, year_branch_idx = calculate_year_pillar(chinese_year)
    month_stem, month_branch, month_stem_idx, month_branch_idx = calculate_month_pillar(year_stem_idx, bazi_month)
    day_stem, day_branch, day_stem_idx, day_branch_idx = calculate_day_pillar(dt)
    
    return {
        "day": {
            "stem": day_stem,
            "stem_pinyin": HEAVENLY_STEMS_PINYIN[day_stem_idx],
            "branch": day_branch,
            "branch_pinyin": EARTHLY_BRANCHES_PINYIN[day_branch_idx],
            "element": STEM_ELEMENTS[day_stem],
            "animal": BRANCH_ANIMALS[day_branch],
        },
        "month": {
            "stem": month_stem,
            "stem_pinyin": HEAVENLY_STEMS_PINYIN[month_stem_idx],
            "branch": month_branch,
            "branch_pinyin": EARTHLY_BRANCHES_PINYIN[month_branch_idx],
            "element": STEM_ELEMENTS[month_stem],
            "animal": BRANCH_ANIMALS[month_branch],
        },
        "year": {
            "stem": year_stem,
            "stem_pinyin": HEAVENLY_STEMS_PINYIN[year_stem_idx],
            "branch": year_branch,
            "branch_pinyin": EARTHLY_BRANCHES_PINYIN[year_branch_idx],
            "element": STEM_ELEMENTS[year_stem],
            "animal": BRANCH_ANIMALS[year_branch],
        },
    }

def calculate_timing_interaction(
    day_master_stem: str,
    current_stem: str,
    period: str  # "today", "month", "year"
) -> Dict[str, Any]:
    """
    Calculate interaction between Day Master and a timing pillar.
    Uses combined model: Element relationship + Ten God (Ten God primary).
    """
    dm_element = STEM_ELEMENTS[day_master_stem]
    current_element = STEM_ELEMENTS[current_stem]
    ten_god = get_ten_god(day_master_stem, current_stem)
    
    # Layer 1: Element relationship
    element_relation = "neutral"
    if ELEMENT_PRODUCES[current_element] == dm_element:
        element_relation = "produces"  # Current produces DM = support
    elif current_element == dm_element:
        element_relation = "same"  # Reinforce
    elif ELEMENT_CONTROLS[current_element] == dm_element:
        element_relation = "controls"  # Current controls DM = pressure
    elif ELEMENT_PRODUCES[dm_element] == current_element:
        element_relation = "drains"  # DM produces current = output/drain
    
    # Layer 2: Ten God interpretation (PRIMARY)
    ten_god_quality = "neutral"
    if ten_god in ["direct_seal", "indirect_seal"]:
        ten_god_quality = "supporting"  # Resource
    elif ten_god in ["eating_god", "hurting_officer"]:
        ten_god_quality = "output"  # Expression
    elif ten_god in ["direct_wealth", "indirect_wealth"]:
        ten_god_quality = "execution"  # Wealth/results
    elif ten_god in ["direct_officer", "seven_killings"]:
        ten_god_quality = "pressure"  # Officer/pressure
    elif ten_god in ["companion", "rob_wealth"]:
        ten_god_quality = "peer"  # Collaboration/competition
    
    # Final interaction type (Ten God overrides element when conflicting)
    if ten_god_quality == "pressure":
        interaction = "pressure"
    elif ten_god_quality in ["supporting", "output", "execution"]:
        interaction = "supporting"
    elif ten_god_quality == "peer":
        # Peers can be mixed
        interaction = "mixed" if ten_god == "rob_wealth" else "supporting"
    else:
        # Fall back to element
        if element_relation in ["produces", "same"]:
            interaction = "supporting"
        elif element_relation == "controls":
            interaction = "pressure"
        else:
            interaction = "mixed"
    
    # Get description
    descriptions = TIMING_DESCRIPTIONS.get(period, TIMING_DESCRIPTIONS["today"])
    desc_category = descriptions.get(interaction, descriptions.get("mixed", {}))
    
    # Find best matching description
    description = ""
    for category in TEN_GODS_CATEGORIES:
        if ten_god in TEN_GODS_CATEGORIES.get(category, []):
            description = desc_category.get(category, desc_category.get("default", ""))
            break
    if not description:
        description = desc_category.get("default", desc_category.get("controls", ""))
    
    return {
        "ten_god": ten_god,
        "ten_god_name": TEN_GODS_DISPLAY.get(ten_god, {}).get("name", ten_god),
        "element": current_element,
        "element_relation": element_relation,
        "interaction": interaction,
        "description": description,
    }

# =============================================================================
# DEEP DIVE CALCULATIONS
# =============================================================================

def calculate_day_master_analysis(
    day_master_element: str,
    day_master_polarity: str,
    elements: Dict[str, float],
    element_analysis: Dict,
    season: str,
    pillars: Dict
) -> Dict[str, Any]:
    """
    Calculate detailed Day Master analysis for Deep Dive.
    
    Returns strength reasoning, implications, and behavioral interpretation.
    """
    strength = element_analysis["day_master_strength"]
    producer = ELEMENT_PRODUCED_BY.get(day_master_element)
    controller = ELEMENT_CONTROLLED_BY.get(day_master_element)
    drainer = ELEMENT_PRODUCES.get(day_master_element)
    
    # Build reasoning
    reasoning = []
    
    # Season influence
    season_strength = SEASON_ELEMENT_STRENGTH.get(season, {})
    dm_seasonal = season_strength.get(day_master_element, 1.0)
    if dm_seasonal >= 1.3:
        reasoning.append(f"Born in {season} - your element ({day_master_element}) is naturally strong this season")
    elif dm_seasonal <= 0.7:
        reasoning.append(f"Born in {season} - your element ({day_master_element}) is naturally weaker this season")
    else:
        reasoning.append(f"Born in {season} - moderate seasonal support for {day_master_element}")
    
    # Support from producer element
    producer_score = elements.get(producer, 0) if producer else 0
    if producer_score >= 2.0:
        reasoning.append(f"Strongly supported by {producer} (your resource element)")
    elif producer_score >= 1.0:
        reasoning.append(f"Moderately supported by {producer}")
    else:
        reasoning.append(f"Limited support from {producer} (your resource element)")
    
    # Same element presence
    same_score = elements.get(day_master_element, 0)
    if same_score >= 2.5:
        reasoning.append(f"High presence of {day_master_element} in your chart reinforces your core")
    
    # Drain/control factors
    drainer_score = elements.get(drainer, 0) if drainer else 0
    controller_score = elements.get(controller, 0) if controller else 0
    
    if drainer_score >= 2.0:
        reasoning.append(f"Drained by strong {drainer} presence (output/expression pulls from your reserves)")
    if controller_score >= 2.0:
        reasoning.append(f"Challenged by strong {controller} presence (pressure/structure demands adaptation)")
    
    # Determine real strength with nuance
    total = sum(elements.values())
    dm_support = same_score + producer_score
    dm_challenge = drainer_score + controller_score
    
    if dm_support >= total * 0.45:
        strength_real = "strong"
    elif dm_support <= total * 0.25:
        strength_real = "weak"
    else:
        strength_real = "balanced"
    
    # Behavioral implication
    profile = DAY_MASTER_PROFILES.get((day_master_element, day_master_polarity), {})
    if strength_real == "strong":
        implication = profile.get("strength_strong", "Your core energy is robust and accessible.")
    elif strength_real == "weak":
        implication = profile.get("strength_weak", "Your core energy may need conscious cultivation.")
    else:
        implication = f"You have a balanced {day_master_element} Day Master. Your core is neither over nor under-supported, allowing flexibility in how you express it."
    
    return {
        "strength_real": strength_real,
        "reasoning": reasoning,
        "implication": implication,
    }

def calculate_favorable_elements(
    day_master_element: str,
    strength: str,
    elements: Dict[str, float]
) -> Tuple[List[str], List[str]]:
    """
    Calculate favorable and unfavorable elements based on Day Master strength.
    
    Classical BaZi: Strong DM needs draining/controlling; Weak DM needs support.
    """
    producer = ELEMENT_PRODUCED_BY.get(day_master_element)
    controller = ELEMENT_CONTROLLED_BY.get(day_master_element)
    drainer = ELEMENT_PRODUCES.get(day_master_element)
    controlled = ELEMENT_CONTROLS.get(day_master_element)
    
    if strength == "strong":
        # Strong DM benefits from being drained (output) and controlled (structure)
        favorable = [drainer, controlled]
        # Too much support can create stagnation
        unfavorable = [producer, day_master_element]
    else:
        # Weak DM benefits from support and same element
        favorable = [producer, day_master_element]
        # Draining and controlling weaken further
        unfavorable = [drainer, controller]
    
    # Filter None values
    favorable = [e for e in favorable if e]
    unfavorable = [e for e in unfavorable if e]
    
    return favorable, unfavorable

def calculate_ten_gods_detailed(
    day_master_stem: str,
    pillars: Dict,
    ten_gods_summary: Dict,
    season: str
) -> List[Dict[str, Any]]:
    """
    Calculate detailed Ten Gods analysis for Deep Dive.
    
    Returns behavioral expressions, risks, and stress patterns for each present category.
    """
    detailed = []
    dm_element = STEM_ELEMENTS[day_master_stem]
    
    # Get categories present with their positions
    category_positions = {cat: [] for cat in TEN_GODS_CATEGORIES.keys()}
    
    positions = [
        ("year", pillars["year"]["stem"]),
        ("month", pillars["month"]["stem"]),
        ("hour", pillars["hour"]["stem"]),
    ]
    
    for pos_name, stem in positions:
        if stem == day_master_stem:
            continue
        ten_god = get_ten_god(day_master_stem, stem)
        for cat, members in TEN_GODS_CATEGORIES.items():
            if ten_god in members:
                category_positions[cat].append(pos_name)
    
    # Also check hidden stems in month branch (highest weight)
    for hidden in pillars["month"].get("hidden_stems", []):
        ten_god = get_ten_god(day_master_stem, hidden)
        for cat, members in TEN_GODS_CATEGORIES.items():
            if ten_god in members and "month (hidden)" not in category_positions[cat]:
                category_positions[cat].append("month (hidden)")
    
    # Build detailed for present categories
    scores = ten_gods_summary.get("scores", {})
    
    for category in ten_gods_summary.get("categories_present", []):
        if category not in TEN_GODS_BEHAVIORAL:
            continue
        
        template = TEN_GODS_BEHAVIORAL[category]
        positions_list = category_positions.get(category, [])
        
        # Determine strength based on score
        cat_score = sum(scores.get(g, 0) for g in TEN_GODS_CATEGORIES.get(category, []))
        if cat_score >= 4.0:
            strength = "high"
            behavioral = template["behavioral_high"]
        elif cat_score >= 2.0:
            strength = "moderate"
            behavioral = template["behavioral_high"]  # Use high template but note moderate
        else:
            strength = "low"
            behavioral = template["behavioral_low"]
        
        detailed.append({
            "name": category,
            "label": template["label"],
            "wow_line": template.get("wow_line", ""),
            "strength": strength,
            "present_in": positions_list,
            "behavioral_expression": behavioral,
            "stress_pattern": template["stress_pattern"],
            "others_experience": template["others_experience"],
            "risk": template["risk"],
            "insight": template["insight"],
            "tension": template["tension"],
            "action": template["action"],
            "why_pattern": template.get("why_pattern", ""),
            "go_deeper": template.get("go_deeper", ""),
        })
    
    # Sort by strength (high first)
    strength_order = {"high": 0, "moderate": 1, "low": 2}
    detailed.sort(key=lambda x: strength_order.get(x["strength"], 3))
    
    return detailed

def calculate_hidden_dynamics(pillars: Dict, day_master_stem: str) -> List[Dict[str, Any]]:
    """
    Calculate hidden dynamics from branch hidden stems.
    
    Focus on the most significant hidden influences.
    """
    dynamics = []
    
    pillar_order = [
        ("month", "Month Pillar (Work/Career)"),
        ("day", "Day Pillar (Self/Partnerships)"),
        ("year", "Year Pillar (Roots/Family)"),
        ("hour", "Hour Pillar (Inner World)"),
    ]
    
    for pillar_key, pillar_label in pillar_order:
        pillar = pillars[pillar_key]
        hidden_stems = pillar.get("hidden_stems", [])
        
        if not hidden_stems:
            continue
        
        # Focus on the main hidden stem (first one is usually most significant)
        main_hidden = hidden_stems[0]
        main_hidden_pinyin = HEAVENLY_STEMS_PINYIN[HEAVENLY_STEMS.index(main_hidden)]
        
        # Skip if it's the same as day master
        if main_hidden == day_master_stem:
            continue
        
        hidden_data = HIDDEN_STEM_MEANINGS.get(main_hidden, {})
        if isinstance(hidden_data, str):
            # Old format - convert to new
            meaning = hidden_data
            behavioral = ""
            shows_up = ""
        else:
            meaning = hidden_data.get("description", f"Hidden {STEM_ELEMENTS.get(main_hidden, 'element')} influence")
            behavioral = hidden_data.get("behavioral", "")
            shows_up = hidden_data.get("shows_up", "")
        
        # Get the Ten God relationship for more context
        ten_god = get_ten_god(day_master_stem, main_hidden)
        ten_god_name = TEN_GODS_DISPLAY.get(ten_god, {}).get("name", ten_god)
        
        dynamics.append({
            "pillar": pillar_key,
            "pillar_label": pillar_label,
            "hidden_stem": main_hidden,
            "hidden_stem_pinyin": main_hidden_pinyin,
            "element": STEM_ELEMENTS.get(main_hidden),
            "ten_god": ten_god_name,
            "meaning": meaning,
            "behavioral": behavioral,
            "shows_up": shows_up,
        })
    
    return dynamics[:3]  # Limit to top 3 most significant

def calculate_life_pattern(day_master_element: str, day_master_polarity: str, favorable: List[str]) -> Dict[str, Any]:
    """
    Generate the Life Pattern section for Deep Dive.
    """
    template = LIFE_PATTERN_TEMPLATES.get(
        (day_master_element, day_master_polarity),
        LIFE_PATTERN_TEMPLATES[("Earth", "Yin")]  # fallback
    )
    
    # Customize growth direction with favorable elements
    growth_direction = template["growth_direction"]
    if favorable:
        favorable_names = ", ".join(favorable)
        growth_direction = f"{template['growth_direction']} Currently, {favorable_names} would help balance your chart."
    
    return {
        "core_drive": template["core_drive"],
        "wow_line": template.get("wow_line", ""),
        "default_mode": template["default_mode"],
        "under_pressure": template["under_pressure"],
        "growth_direction": growth_direction,
        "why_pattern": template.get("why_pattern", ""),
    }

# =============================================================================
# PATTERN DOMAINS - NORMALIZED OUTPUT FOR CROSS-LENS SYNTHESIS
# =============================================================================

def generate_pattern_domains(
    day_master: Dict,
    dm_element: str,
    dm_polarity: str,
    strength: str,
    ten_gods_detailed: List[Dict],
    ten_gods_summary: Dict,
    element_analysis: Dict,
    life_pattern: Dict,
    timing: Optional[Dict],
    favorable_elements: List[str],
) -> Dict[str, List[Dict]]:
    """
    Generate normalized pattern domains for cross-lens synthesis.
    
    These are internal normalized outputs, NOT user-facing replacements.
    Each domain contains patterns from BaZi logic that can later be
    compared with patterns from Human Design, Enneagram, Numerology, etc.
    
    The future synthesis layer can identify repeated themes WITHOUT
    forcing direct framework equivalences.
    
    Domain structure:
    - self: identity, standards, inner style
    - relationships: friction, support, bonding style
    - work: execution, leadership, responsibility, pace
    - stress: pressure pattern, shadow behavior
    - growth: balancing direction, useful elements, developmental edge
    - timing: today / month / year activation themes
    """
    
    domains = {
        "self": [],
        "relationships": [],
        "work": [],
        "stress": [],
        "growth": [],
        "timing": [],
    }
    
    # =========================================================================
    # SELF DOMAIN - Identity, standards, inner style
    # =========================================================================
    
    dm_profile = DAY_MASTER_PROFILES.get((dm_element, dm_polarity), {})
    
    # Core identity from Day Master
    domains["self"].append({
        "pattern": f"{dm_element} {dm_polarity} Day Master",
        "theme": dm_profile.get("keywords", [])[0] if dm_profile.get("keywords") else "identity",
        "insight": dm_profile.get("wow_line", ""),
        "source": "bazi_day_master",
        "confidence": 0.9,
    })
    
    # Strength impacts self-expression
    if strength == "strong":
        domains["self"].append({
            "pattern": "Strong Day Master",
            "theme": "self-expression",
            "insight": "Natural energy to express identity openly. The work is tempering force with receptivity.",
            "source": "bazi_day_master_strength",
            "confidence": 0.85,
        })
    else:
        domains["self"].append({
            "pattern": "Weak Day Master",
            "theme": "seeking support",
            "insight": "Identity benefits from external support and validation. The work is building inner foundation.",
            "source": "bazi_day_master_strength",
            "confidence": 0.85,
        })
    
    # =========================================================================
    # RELATIONSHIPS DOMAIN - Friction, support, bonding style
    # =========================================================================
    
    # Companion/Self energy indicates relationship style
    companion_present = any(g["name"] == "companion" for g in ten_gods_detailed)
    officer_present = any(g["name"] == "officer" for g in ten_gods_detailed)
    
    if companion_present:
        domains["relationships"].append({
            "pattern": "Companion energy present",
            "theme": "independence in relationships",
            "insight": "Tends toward self-reliance in partnerships. May resist help or compete with peers.",
            "source": "bazi_ten_gods",
            "confidence": 0.8,
        })
    
    if officer_present:
        domains["relationships"].append({
            "pattern": "Officer energy present",
            "theme": "structure in relationships",
            "insight": "Experiences relationships through duty and responsibility. May feel over-obligated.",
            "source": "bazi_ten_gods",
            "confidence": 0.8,
        })
    
    # Element interaction style
    if dm_element == "Metal":
        domains["relationships"].append({
            "pattern": "Metal Day Master relationship style",
            "theme": "standards and boundaries",
            "insight": "High standards in relationships. Values quality over quantity in connections.",
            "source": "bazi_element",
            "confidence": 0.75,
        })
    elif dm_element == "Water":
        domains["relationships"].append({
            "pattern": "Water Day Master relationship style",
            "theme": "adaptability and depth",
            "insight": "Flows around relationship obstacles. Seeks depth over surface connection.",
            "source": "bazi_element",
            "confidence": 0.75,
        })
    elif dm_element == "Fire":
        domains["relationships"].append({
            "pattern": "Fire Day Master relationship style",
            "theme": "warmth and visibility",
            "insight": "Natural warmth in connections. May need to be seen and appreciated.",
            "source": "bazi_element",
            "confidence": 0.75,
        })
    
    # =========================================================================
    # WORK DOMAIN - Execution, leadership, responsibility, pace
    # =========================================================================
    
    # Wealth (execution) energy
    wealth_god = next((g for g in ten_gods_detailed if g["name"] == "wealth"), None)
    if wealth_god:
        domains["work"].append({
            "pattern": "Wealth/Execution energy",
            "theme": "results orientation",
            "insight": wealth_god.get("insight", "Focus on results and practical outcomes."),
            "source": "bazi_ten_gods",
            "confidence": 0.85,
        })
    
    # Resource (preparation) energy
    resource_god = next((g for g in ten_gods_detailed if g["name"] == "resource"), None)
    if resource_god:
        domains["work"].append({
            "pattern": "Resource/Seal energy",
            "theme": "preparation and analysis",
            "insight": resource_god.get("insight", "Processes and prepares before acting."),
            "source": "bazi_ten_gods",
            "confidence": 0.85,
        })
    
    # Output (creation) energy
    output_god = next((g for g in ten_gods_detailed if g["name"] == "output"), None)
    if output_god:
        domains["work"].append({
            "pattern": "Output/Expression energy",
            "theme": "creative expression",
            "insight": output_god.get("insight", "Creates and expresses to process."),
            "source": "bazi_ten_gods",
            "confidence": 0.85,
        })
    
    # =========================================================================
    # STRESS DOMAIN - Pressure pattern, shadow behavior
    # =========================================================================
    
    # Extract stress patterns from Ten Gods
    for god in ten_gods_detailed:
        if god.get("stress_pattern"):
            domains["stress"].append({
                "pattern": f"{god['name']} stress pattern",
                "theme": god.get("name", "pressure"),
                "insight": god["stress_pattern"],
                "source": "bazi_ten_gods",
                "confidence": 0.8,
            })
    
    # Day Master strength stress
    if strength == "strong":
        domains["stress"].append({
            "pattern": "Strong Day Master under pressure",
            "theme": "over-assertion",
            "insight": "Under stress, may become rigid, controlling, or dismissive of others' input.",
            "source": "bazi_day_master_strength",
            "confidence": 0.75,
        })
    else:
        domains["stress"].append({
            "pattern": "Weak Day Master under pressure",
            "theme": "withdrawal",
            "insight": "Under stress, may withdraw, seek excessive validation, or feel overwhelmed.",
            "source": "bazi_day_master_strength",
            "confidence": 0.75,
        })
    
    # =========================================================================
    # GROWTH DOMAIN - Balancing direction, useful elements, developmental edge
    # =========================================================================
    
    # Balancing elements
    for elem in element_analysis.get("balancing", []):
        domains["growth"].append({
            "pattern": f"Balancing with {elem}",
            "theme": "element cultivation",
            "insight": f"Activating {elem} energy supports balance and growth.",
            "source": "bazi_element_analysis",
            "confidence": 0.8,
        })
    
    # Favorable elements for growth
    for elem in favorable_elements[:2]:  # Top 2
        domains["growth"].append({
            "pattern": f"Favorable element: {elem}",
            "theme": "supportive energy",
            "insight": f"{elem} energy naturally supports your Day Master.",
            "source": "bazi_favorable_elements",
            "confidence": 0.85,
        })
    
    # Life pattern developmental edge
    if life_pattern:
        domains["growth"].append({
            "pattern": life_pattern.get("pattern_name", "Life Pattern"),
            "theme": "core drive",
            "insight": life_pattern.get("core_drive", ""),
            "source": "bazi_life_pattern",
            "confidence": 0.9,
        })
    
    # =========================================================================
    # TIMING DOMAIN - Today / month / year activation themes
    # =========================================================================
    
    if timing:
        for period_key, period_data in timing.items():
            if period_data:
                theme = period_data.get("theme", "")
                reflection = period_data.get("reflection", "")
                
                if theme:
                    domains["timing"].append({
                        "pattern": f"{period_key.capitalize()} timing: {theme}",
                        "theme": theme.lower() if theme else "activation",
                        "insight": reflection or f"Current {period_key} energy activating.",
                        "source": f"bazi_timing_{period_key}",
                        "confidence": 0.7,
                        "period": period_key,
                    })
    
    return domains


# =============================================================================
# STRUCTURE SUMMARY
# =============================================================================

def calculate_structure_summary(pillars: Dict, bazi_month: int, elements: Dict, analysis: Dict) -> Dict[str, Any]:
    """Generate structure summary for the chart."""
    season = get_season(bazi_month)
    
    # Climate description
    season_elements = {
        "spring": "Wood rising, Fire emerging",
        "summer": "Fire at peak, Earth consolidating",
        "late_summer": "Earth stable, Metal forming",
        "autumn": "Metal sharp, Water gathering",
        "winter": "Water deep, Wood resting",
    }
    
    return {
        "season": season,
        "climate": season_elements.get(season, "Transitional energy"),
        "supporting_elements": analysis["supporting"],
        "balancing_elements": analysis["balancing"],
    }

# =============================================================================
# MAIN COMPUTATION FUNCTION
# =============================================================================

def compute_bazi_chart_v2(
    birth_date,
    birth_time: Optional[str] = None,
    timezone: Optional[str] = None,
    include_timing: bool = True
) -> Dict[str, Any]:
    """
    Compute complete BaZi chart with V2 structure.
    
    Returns the new response shape with:
    - day_master (with keywords, strength, description)
    - pillars (with hidden_stems, animal emoji)
    - elements (with dominant, weak, supporting, balancing)
    - ten_gods_summary (weighted analysis)
    - structure_summary (season, climate)
    - timing (today, month, year interactions)
    """
    # Parse date/time
    if isinstance(birth_date, datetime):
        dt = birth_date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif isinstance(birth_date, str):
        for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d"]:
            try:
                dt = datetime.strptime(birth_date, fmt).replace(hour=0, minute=0, second=0, microsecond=0)
                break
            except ValueError:
                continue
        else:
            raise ValueError(f"Could not parse date: {birth_date}")
    else:
        raise ValueError(f"Unsupported birth_date type: {type(birth_date)}")
    
    # Apply birth time
    time_parts = parse_birth_time(birth_time)
    if time_parts:
        dt = dt.replace(hour=time_parts[0], minute=time_parts[1])
    else:
        dt = dt.replace(hour=12, minute=0)
    
    # Calculate pillars
    chinese_year = get_chinese_year(dt)
    bazi_month = get_bazi_month(dt)
    season = get_season(bazi_month)
    
    year_stem, year_branch, year_stem_idx, year_branch_idx = calculate_year_pillar(chinese_year)
    month_stem, month_branch, month_stem_idx, month_branch_idx = calculate_month_pillar(year_stem_idx, bazi_month)
    day_stem, day_branch, day_stem_idx, day_branch_idx = calculate_day_pillar(dt)
    hour_stem, hour_branch, hour_stem_idx, hour_branch_idx = calculate_hour_pillar(day_stem_idx, dt.hour)
    
    # Build pillars structure
    def build_pillar(stem, branch, stem_idx, branch_idx, pillar_type):
        animal_data = BRANCH_ANIMALS[branch]
        meaning = PILLAR_MEANINGS[pillar_type]
        return {
            "stem": stem,
            "stem_pinyin": HEAVENLY_STEMS_PINYIN[stem_idx],
            "branch": branch,
            "branch_pinyin": EARTHLY_BRANCHES_PINYIN[branch_idx],
            "animal": f"{animal_data['emoji']} {animal_data['name']}",
            "animal_name": animal_data['name'],
            "animal_emoji": animal_data['emoji'],
            "hidden_stems": BRANCH_HIDDEN_STEMS.get(branch, []),
            "hidden_stems_pinyin": [HEAVENLY_STEMS_PINYIN[HEAVENLY_STEMS.index(s)] for s in BRANCH_HIDDEN_STEMS.get(branch, [])],
            "stem_element": STEM_ELEMENTS[stem],
            "branch_element": BRANCH_ELEMENTS[branch],
            "meaning_label": meaning["label"],
            "meaning_description": meaning["description"],
        }
    
    pillars = {
        "year": build_pillar(year_stem, year_branch, year_stem_idx, year_branch_idx, "year"),
        "month": build_pillar(month_stem, month_branch, month_stem_idx, month_branch_idx, "month"),
        "day": build_pillar(day_stem, day_branch, day_stem_idx, day_branch_idx, "day"),
        "hour": build_pillar(hour_stem, hour_branch, hour_stem_idx, hour_branch_idx, "hour"),
    }
    
    # Day Master
    dm_element = STEM_ELEMENTS[day_stem]
    dm_polarity = STEM_POLARITY[day_stem]
    dm_profile = DAY_MASTER_PROFILES.get((dm_element, dm_polarity), DAY_MASTER_PROFILES[("Earth", "Yin")])
    
    # Elements analysis
    elements = calculate_elements(pillars)
    element_analysis = analyze_elements(elements, dm_element)
    
    # Day Master strength description
    strength = element_analysis["day_master_strength"]
    strength_desc = dm_profile.get(f"strength_{strength}", dm_profile["description"])
    
    day_master = {
        "stem": day_stem,
        "stem_pinyin": HEAVENLY_STEMS_PINYIN[day_stem_idx],
        "element": dm_element,
        "polarity": dm_polarity,
        "strength": strength,
        "keywords": dm_profile["keywords"],
        "description": dm_profile["description"],
        "strength_description": strength_desc,
        "wow_line": dm_profile.get("wow_line", ""),
        "why_pattern": dm_profile.get("why_pattern", ""),
    }
    
    # Ten Gods weighted analysis
    ten_gods_summary = calculate_ten_gods_weighted(day_stem, pillars, season)
    
    # Structure summary
    structure_summary = calculate_structure_summary(pillars, bazi_month, elements, element_analysis)
    
    # Build response
    chart = {
        "day_master": day_master,
        "pillars": pillars,
        "elements": {
            "wood": elements["Wood"],
            "fire": elements["Fire"],
            "earth": elements["Earth"],
            "metal": elements["Metal"],
            "water": elements["Water"],
            "dominant": element_analysis["dominant"],
            "weak": element_analysis["weak"],
            "supporting": element_analysis["supporting"],
            "balancing": element_analysis["balancing"],
        },
        "ten_gods_summary": {
            "dominant": [TEN_GODS_DISPLAY.get(g, {}).get("name", g) for g in ten_gods_summary["dominant"]],
            "dominant_raw": ten_gods_summary["dominant"],
            "present": [TEN_GODS_DISPLAY.get(g, {}).get("name", g) for g in ten_gods_summary["present"]],
            "present_raw": ten_gods_summary["present"],
            "categories": ten_gods_summary["categories_present"],
        },
        "structure_summary": structure_summary,
        "birth_data": {
            "date": str(birth_date),
            "time": birth_time or "12:00",
            "timezone": timezone,
            "chinese_year": chinese_year,
            "bazi_month": bazi_month,
        },
        "calculation_version": "2.0",
    }
    
    # Timing calculations
    if include_timing:
        now = datetime.now()
        current_pillars = calculate_current_pillar(now)
        
        timing = {
            "today": {
                "pillar": f"{current_pillars['day']['stem_pinyin']}-{current_pillars['day']['branch_pinyin']}",
                "stem": current_pillars["day"]["stem"],
                "branch": current_pillars["day"]["branch"],
                "element": current_pillars["day"]["element"],
                "animal": current_pillars["day"]["animal"],
                **calculate_timing_interaction(day_stem, current_pillars["day"]["stem"], "today"),
            },
            "month": {
                "pillar": f"{current_pillars['month']['stem_pinyin']}-{current_pillars['month']['branch_pinyin']}",
                "stem": current_pillars["month"]["stem"],
                "branch": current_pillars["month"]["branch"],
                "element": current_pillars["month"]["element"],
                "animal": current_pillars["month"]["animal"],
                **calculate_timing_interaction(day_stem, current_pillars["month"]["stem"], "month"),
            },
            "year": {
                "pillar": f"{current_pillars['year']['stem_pinyin']}-{current_pillars['year']['branch_pinyin']}",
                "stem": current_pillars["year"]["stem"],
                "branch": current_pillars["year"]["branch"],
                "element": current_pillars["year"]["element"],
                "animal": current_pillars["year"]["animal"],
                **calculate_timing_interaction(day_stem, current_pillars["year"]["stem"], "year"),
            },
        }
        chart["timing"] = timing
    
    # =================================================================
    # DEEP DIVE CALCULATIONS
    # =================================================================
    
    # Day Master detailed analysis
    day_master_analysis = calculate_day_master_analysis(
        dm_element, dm_polarity, elements, element_analysis, season, pillars
    )
    
    # Favorable/unfavorable elements
    favorable, unfavorable = calculate_favorable_elements(
        dm_element, strength, elements
    )
    
    # Ten Gods detailed behavioral analysis
    ten_gods_detailed = calculate_ten_gods_detailed(
        day_stem, pillars, ten_gods_summary, season
    )
    
    # Hidden dynamics
    hidden_dynamics = calculate_hidden_dynamics(pillars, day_stem)
    
    # Life pattern
    life_pattern = calculate_life_pattern(dm_element, dm_polarity, favorable)
    
    # Add Deep Dive section to chart
    chart["deep_dive"] = {
        "day_master_analysis": day_master_analysis,
        "favorable_elements": favorable,
        "unfavorable_elements": unfavorable,
        "ten_gods_detailed": ten_gods_detailed,
        "hidden_dynamics": hidden_dynamics,
        "life_pattern": life_pattern,
    }
    
    # =================================================================
    # PATTERN DOMAINS - NORMALIZED OUTPUT FOR CROSS-LENS SYNTHESIS
    # =================================================================
    # These are internal normalized outputs for future synthesis.
    # NOT user-facing replacements for BaZi language.
    # Each lens (HD, Enneagram, Numerology) will populate the same buckets.
    # This enables pattern comparison WITHOUT forced metaphysical mapping.
    
    chart["pattern_domains"] = generate_pattern_domains(
        day_master=day_master,
        dm_element=dm_element,
        dm_polarity=dm_polarity,
        strength=strength,
        ten_gods_detailed=ten_gods_detailed,
        ten_gods_summary=ten_gods_summary,
        element_analysis=element_analysis,
        life_pattern=life_pattern,
        timing=chart.get("timing"),
        favorable_elements=favorable,
    )
    
    logger.info(f"[BaZi V2] Computed chart: Day Master = {day_master['stem_pinyin']} {dm_element} ({strength})")
    
    return chart


# =============================================================================
# LEGACY COMPATIBILITY WRAPPER
# =============================================================================

def compute_bazi_chart_legacy_compat(
    birth_date,
    birth_time: Optional[str] = None,
    timezone: Optional[str] = None
) -> Dict[str, Any]:
    """
    Wrapper to maintain backward compatibility with original response shape.
    """
    v2_chart = compute_bazi_chart_v2(birth_date, birth_time, timezone, include_timing=False)
    
    # Transform to legacy format
    pillars_legacy = {}
    for key, pillar in v2_chart["pillars"].items():
        pillars_legacy[f"{key}_pillar"] = {
            "stem": pillar["stem"],
            "stem_pinyin": pillar["stem_pinyin"],
            "branch": pillar["branch"],
            "branch_pinyin": pillar["branch_pinyin"],
            "animal": pillar["animal_name"],
            "stem_element": pillar["stem_element"],
            "branch_element": pillar["branch_element"],
        }
    
    return {
        "birth_data": v2_chart["birth_data"],
        "pillars": pillars_legacy,
        "day_master": {
            "stem": v2_chart["day_master"]["stem"],
            "stem_pinyin": v2_chart["day_master"]["stem_pinyin"],
            "element": v2_chart["day_master"]["element"],
            "polarity": v2_chart["day_master"]["polarity"],
        },
        "five_elements": {
            "Wood": v2_chart["elements"]["wood"],
            "Fire": v2_chart["elements"]["fire"],
            "Earth": v2_chart["elements"]["earth"],
            "Metal": v2_chart["elements"]["metal"],
            "Water": v2_chart["elements"]["water"],
        },
        "element_analysis": {
            "dominant_element": v2_chart["elements"]["dominant"][0] if v2_chart["elements"]["dominant"] else "Earth",
            "weak_element": v2_chart["elements"]["weak"][0] if v2_chart["elements"]["weak"] else "Fire",
            "element_percentages": {},
            "day_master_strength": v2_chart["day_master"]["strength"].capitalize(),
            "supporting_elements": v2_chart["elements"]["supporting"],
            "balance_status": "Moderately Balanced",
        },
        "ten_gods": {
            "year_pillar_stem": "",
            "month_pillar_stem": "",
            "day_pillar_stem": "Self (Day Master)",
            "hour_pillar_stem": "",
        },
        "summary": {
            "day_master_description": f"{v2_chart['day_master']['stem_pinyin']} {v2_chart['day_master']['element']} ({v2_chart['day_master']['polarity']})",
            "dominant_element": v2_chart["elements"]["dominant"][0] if v2_chart["elements"]["dominant"] else "Earth",
            "weak_element": v2_chart["elements"]["weak"][0] if v2_chart["elements"]["weak"] else "Fire",
            "balance_status": "Moderately Balanced",
            "day_master_strength": v2_chart["day_master"]["strength"].capitalize(),
            "supporting_elements": v2_chart["elements"]["supporting"],
        },
        "calculation_version": "2.0-compat",
    }
