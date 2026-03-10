"""Gene Keys Interpretive Data

This module contains the Shadow/Gift/Siddhi meanings for Gene Keys.
Gene Keys use the same gate numbers and line numbers as Human Design.

Gene Key = Gate Number
Gene Key Line = Gate Line

This is an INTERPRETATION LAYER on top of Human Design deterministic data.
All 64 Gene Keys with canonical Shadow/Gift/Siddhi names and pattern keywords.
"""

from typing import TypedDict, Optional, List


class GeneKeyData(TypedDict):
    """Gene Key interpretive data structure with pattern keywords."""
    gene_key: int
    shadow: str
    gift: str
    siddhi: str
    shadow_keywords: List[str]
    gift_keywords: List[str]


# Complete 64 Gene Keys with canonical Shadow -> Gift -> Siddhi and pattern keywords
GENE_KEYS: dict[int, GeneKeyData] = {
    1: {
        "gene_key": 1,
        "shadow": "Entropy",
        "gift": "Freshness",
        "siddhi": "Beauty",
        "shadow_keywords": ["stale", "stuck", "repetitive", "bored", "same old", "going through motions", "lifeless"],
        "gift_keywords": ["fresh", "new perspective", "creative", "original", "inspired", "alive", "beginning"]
    },
    2: {
        "gene_key": 2,
        "shadow": "Dislocation",
        "gift": "Orientation",
        "siddhi": "Unity",
        "shadow_keywords": ["lost", "directionless", "disconnected", "out of place", "don't belong", "displaced"],
        "gift_keywords": ["direction", "purpose", "aligned", "centered", "grounded", "knowing where I'm going"]
    },
    3: {
        "gene_key": 3,
        "shadow": "Chaos",
        "gift": "Innovation",
        "siddhi": "Innocence",
        "shadow_keywords": ["chaotic", "messy", "overwhelming", "disorder", "confused", "scattered", "turbulent"],
        "gift_keywords": ["innovative", "new solution", "creative approach", "breakthrough", "fresh idea"]
    },
    4: {
        "gene_key": 4,
        "shadow": "Intolerance",
        "gift": "Understanding",
        "siddhi": "Forgiveness",
        "shadow_keywords": ["judgmental", "intolerant", "critical", "narrow-minded", "can't stand", "irritated by"],
        "gift_keywords": ["understanding", "empathy", "seeing their perspective", "compassion", "accepting"]
    },
    5: {
        "gene_key": 5,
        "shadow": "Impatience",
        "gift": "Patience",
        "siddhi": "Timelessness",
        "shadow_keywords": ["rushed", "impatient", "pressure", "frustrated", "hurry", "not fast enough", "waiting is hard"],
        "gift_keywords": ["patient", "waiting", "timing", "allowing", "trusting the process", "steady pace", "unhurried"]
    },
    6: {
        "gene_key": 6,
        "shadow": "Conflict",
        "gift": "Diplomacy",
        "siddhi": "Peace",
        "shadow_keywords": ["conflict", "fighting", "arguing", "tension", "disagreement", "hostile", "adversarial"],
        "gift_keywords": ["diplomatic", "peaceful", "harmonious", "mediating", "finding common ground", "resolving"]
    },
    7: {
        "gene_key": 7,
        "shadow": "Division",
        "gift": "Guidance",
        "siddhi": "Virtue",
        "shadow_keywords": ["divided", "split", "us vs them", "polarized", "taking sides", "fragmented"],
        "gift_keywords": ["guiding", "leading", "direction", "mentoring", "showing the way", "unifying"]
    },
    8: {
        "gene_key": 8,
        "shadow": "Mediocrity",
        "gift": "Style",
        "siddhi": "Exquisiteness",
        "shadow_keywords": ["mediocre", "average", "ordinary", "settling", "not good enough", "bland", "uninspired"],
        "gift_keywords": ["unique style", "authentic expression", "standing out", "distinctive", "original voice"]
    },
    9: {
        "gene_key": 9,
        "shadow": "Inertia",
        "gift": "Determination",
        "siddhi": "Invincibility",
        "shadow_keywords": ["stuck", "inertia", "can't move", "stagnant", "paralyzed", "no momentum", "resistance"],
        "gift_keywords": ["determined", "focused", "persistent", "committed", "pushing through", "dedicated"]
    },
    10: {
        "gene_key": 10,
        "shadow": "Self-Obsession",
        "gift": "Naturalness",
        "siddhi": "Being",
        "shadow_keywords": ["self-absorbed", "self-conscious", "overthinking myself", "ego", "narcissistic", "preoccupied with self"],
        "gift_keywords": ["natural", "authentic", "being myself", "comfortable in my skin", "effortless", "at ease"]
    },
    11: {
        "gene_key": 11,
        "shadow": "Obscurity",
        "gift": "Idealism",
        "siddhi": "Light",
        "shadow_keywords": ["unclear", "obscure", "foggy", "confused", "in the dark", "can't see", "vague"],
        "gift_keywords": ["clear vision", "idealistic", "seeing possibility", "hopeful", "bright", "optimistic"]
    },
    12: {
        "gene_key": 12,
        "shadow": "Vanity",
        "gift": "Discrimination",
        "siddhi": "Purity",
        "shadow_keywords": ["vain", "superficial", "image-focused", "appearance", "showing off", "pretentious"],
        "gift_keywords": ["discerning", "refined taste", "selective", "quality-focused", "pure intention"]
    },
    13: {
        "gene_key": 13,
        "shadow": "Discord",
        "gift": "Discernment",
        "siddhi": "Empathy",
        "shadow_keywords": ["discord", "disharmony", "not listening", "misunderstanding", "out of sync", "clashing"],
        "gift_keywords": ["listening", "discerning", "understanding", "attuned", "empathetic", "hearing"]
    },
    14: {
        "gene_key": 14,
        "shadow": "Compromise",
        "gift": "Competence",
        "siddhi": "Bounteousness",
        "shadow_keywords": ["compromising", "settling", "not enough", "sacrificing", "giving up", "lacking"],
        "gift_keywords": ["competent", "capable", "skilled", "resourceful", "abundant", "thriving"]
    },
    15: {
        "gene_key": 15,
        "shadow": "Dullness",
        "gift": "Magnetism",
        "siddhi": "Florescence",
        "shadow_keywords": ["dull", "boring", "flat", "uninteresting", "lifeless", "mundane", "gray"],
        "gift_keywords": ["magnetic", "attractive", "charismatic", "vibrant", "alive", "flourishing"]
    },
    16: {
        "gene_key": 16,
        "shadow": "Indifference",
        "gift": "Versatility",
        "siddhi": "Mastery",
        "shadow_keywords": ["indifferent", "apathetic", "don't care", "unmotivated", "bored", "disengaged"],
        "gift_keywords": ["versatile", "adaptable", "skilled", "multi-talented", "engaged", "enthusiastic"]
    },
    17: {
        "gene_key": 17,
        "shadow": "Opinion",
        "gift": "Far-Sightedness",
        "siddhi": "Omniscience",
        "shadow_keywords": ["opinionated", "rigid thinking", "my way", "closed-minded", "stubborn", "fixed views"],
        "gift_keywords": ["far-sighted", "visionary", "seeing ahead", "perspective", "open-minded", "wise"]
    },
    18: {
        "gene_key": 18,
        "shadow": "Judgement",
        "gift": "Integrity",
        "siddhi": "Perfection",
        "shadow_keywords": ["judgmental", "critical", "fault-finding", "harsh", "condemning", "perfectionist"],
        "gift_keywords": ["integrity", "honest", "authentic", "principled", "correcting with love", "improving"]
    },
    19: {
        "gene_key": 19,
        "shadow": "Co-Dependence",
        "gift": "Sensitivity",
        "siddhi": "Sacrifice",
        "shadow_keywords": ["co-dependent", "needy", "clingy", "can't be alone", "dependent", "attached"],
        "gift_keywords": ["sensitive", "attuned", "caring", "responsive", "aware of needs", "nurturing"]
    },
    20: {
        "gene_key": 20,
        "shadow": "Superficiality",
        "gift": "Self-Assurance",
        "siddhi": "Presence",
        "shadow_keywords": ["superficial", "shallow", "surface level", "pretending", "fake", "not real"],
        "gift_keywords": ["present", "grounded", "self-assured", "confident", "authentic", "here now"]
    },
    21: {
        "gene_key": 21,
        "shadow": "Control",
        "gift": "Authority",
        "siddhi": "Valour",
        "shadow_keywords": ["controlling", "dominating", "manipulating", "forcing", "power struggle", "grip"],
        "gift_keywords": ["authoritative", "leading", "empowering", "decisive", "courageous", "strong"]
    },
    22: {
        "gene_key": 22,
        "shadow": "Dishonour",
        "gift": "Graciousness",
        "siddhi": "Grace",
        "shadow_keywords": ["dishonoring", "disrespectful", "rude", "tactless", "ungracious", "harsh"],
        "gift_keywords": ["gracious", "elegant", "respectful", "dignified", "honoring", "kind"]
    },
    23: {
        "gene_key": 23,
        "shadow": "Complexity",
        "gift": "Simplicity",
        "siddhi": "Quintessence",
        "shadow_keywords": ["complicated", "complex", "overthinking", "convoluted", "too much", "confused"],
        "gift_keywords": ["simple", "clear", "straightforward", "essential", "distilled", "pure"]
    },
    24: {
        "gene_key": 24,
        "shadow": "Addiction",
        "gift": "Invention",
        "siddhi": "Silence",
        "shadow_keywords": ["addicted", "obsessed", "compulsive", "can't stop", "craving", "hooked", "dependent"],
        "gift_keywords": ["inventive", "creative", "breakthrough", "silence", "stillness", "clarity"]
    },
    25: {
        "gene_key": 25,
        "shadow": "Constriction",
        "gift": "Acceptance",
        "siddhi": "Universal Love",
        "shadow_keywords": ["constricted", "tight", "closed off", "resistant", "rejecting", "narrow"],
        "gift_keywords": ["accepting", "open", "allowing", "embracing", "loving", "welcoming"]
    },
    26: {
        "gene_key": 26,
        "shadow": "Pride",
        "gift": "Artfulness",
        "siddhi": "Invisibility",
        "shadow_keywords": ["prideful", "arrogant", "ego", "boastful", "superior", "showing off"],
        "gift_keywords": ["artful", "skillful", "humble", "crafty", "strategic", "wise"]
    },
    27: {
        "gene_key": 27,
        "shadow": "Selfishness",
        "gift": "Altruism",
        "siddhi": "Selflessness",
        "shadow_keywords": ["selfish", "self-centered", "only thinking of myself", "taking", "greedy"],
        "gift_keywords": ["giving", "caring", "nurturing", "altruistic", "generous", "selfless"]
    },
    28: {
        "gene_key": 28,
        "shadow": "Purposelessness",
        "gift": "Totality",
        "siddhi": "Immortality",
        "shadow_keywords": ["purposeless", "meaningless", "why bother", "pointless", "empty", "no reason"],
        "gift_keywords": ["purposeful", "meaningful", "fully committed", "total", "alive", "engaged"]
    },
    29: {
        "gene_key": 29,
        "shadow": "Half-Heartedness",
        "gift": "Commitment",
        "siddhi": "Devotion",
        "shadow_keywords": ["half-hearted", "uncommitted", "hesitant", "wishy-washy", "unsure", "lukewarm"],
        "gift_keywords": ["committed", "devoted", "all in", "dedicated", "wholehearted", "yes"]
    },
    30: {
        "gene_key": 30,
        "shadow": "Desire",
        "gift": "Lightness",
        "siddhi": "Rapture",
        "shadow_keywords": ["craving", "wanting", "needing", "grasping", "attached", "longing", "hungry"],
        "gift_keywords": ["light", "free", "playful", "accepting", "content", "joyful", "easy"]
    },
    31: {
        "gene_key": 31,
        "shadow": "Arrogance",
        "gift": "Leadership",
        "siddhi": "Humility",
        "shadow_keywords": ["arrogant", "superior", "condescending", "know-it-all", "dismissive", "proud"],
        "gift_keywords": ["leading", "humble", "serving", "guiding", "responsible", "mature"]
    },
    32: {
        "gene_key": 32,
        "shadow": "Failure",
        "gift": "Preservation",
        "siddhi": "Veneration",
        "shadow_keywords": ["failing", "failure", "not good enough", "losing", "inadequate", "defeated"],
        "gift_keywords": ["preserving", "sustaining", "protecting", "maintaining", "successful", "enduring"]
    },
    33: {
        "gene_key": 33,
        "shadow": "Forgetting",
        "gift": "Mindfulness",
        "siddhi": "Revelation",
        "shadow_keywords": ["forgetting", "unconscious", "unaware", "spacing out", "lost", "not remembering"],
        "gift_keywords": ["mindful", "aware", "present", "remembering", "conscious", "attentive"]
    },
    34: {
        "gene_key": 34,
        "shadow": "Force",
        "gift": "Strength",
        "siddhi": "Majesty",
        "shadow_keywords": ["forcing", "pushing", "aggressive", "bullying", "overpowering", "brutal"],
        "gift_keywords": ["strong", "powerful", "dignified", "majestic", "capable", "confident"]
    },
    35: {
        "gene_key": 35,
        "shadow": "Hunger",
        "gift": "Adventure",
        "siddhi": "Boundlessness",
        "shadow_keywords": ["hungry", "restless", "never enough", "searching", "unsatisfied", "craving experience"],
        "gift_keywords": ["adventurous", "exploring", "curious", "open", "experiencing", "alive"]
    },
    36: {
        "gene_key": 36,
        "shadow": "Turbulence",
        "gift": "Humanity",
        "siddhi": "Compassion",
        "shadow_keywords": ["turbulent", "emotional storm", "crisis", "upheaval", "chaotic feelings", "unstable"],
        "gift_keywords": ["compassionate", "human", "feeling", "empathetic", "caring", "connected"]
    },
    37: {
        "gene_key": 37,
        "shadow": "Weakness",
        "gift": "Equality",
        "siddhi": "Tenderness",
        "shadow_keywords": ["weak", "powerless", "inferior", "helpless", "inadequate", "small"],
        "gift_keywords": ["equal", "balanced", "fair", "tender", "gentle", "strong in softness"]
    },
    38: {
        "gene_key": 38,
        "shadow": "Struggle",
        "gift": "Perseverance",
        "siddhi": "Honour",
        "shadow_keywords": ["struggling", "fighting", "hard", "difficult", "battling", "effortful"],
        "gift_keywords": ["persevering", "persistent", "enduring", "honorable", "determined", "steady"]
    },
    39: {
        "gene_key": 39,
        "shadow": "Provocation",
        "gift": "Dynamism",
        "siddhi": "Liberation",
        "shadow_keywords": ["provoking", "irritating", "triggering", "annoying", "stirring up", "agitating"],
        "gift_keywords": ["dynamic", "energizing", "catalyzing", "freeing", "liberating", "alive"]
    },
    40: {
        "gene_key": 40,
        "shadow": "Exhaustion",
        "gift": "Resolve",
        "siddhi": "Divine Will",
        "shadow_keywords": ["exhausted", "burned out", "depleted", "tired", "drained", "no energy"],
        "gift_keywords": ["resolved", "determined", "clear will", "rested", "balanced", "renewed"]
    },
    41: {
        "gene_key": 41,
        "shadow": "Fantasy",
        "gift": "Anticipation",
        "siddhi": "Emanation",
        "shadow_keywords": ["fantasizing", "dreaming", "escapist", "unrealistic", "lost in imagination", "avoiding"],
        "gift_keywords": ["anticipating", "excited", "hopeful", "imaginative", "creative", "visionary"]
    },
    42: {
        "gene_key": 42,
        "shadow": "Expectation",
        "gift": "Detachment",
        "siddhi": "Celebration",
        "shadow_keywords": ["expecting", "disappointed", "should be", "wanting specific outcome", "attached"],
        "gift_keywords": ["detached", "accepting", "celebrating", "letting go", "free", "open"]
    },
    43: {
        "gene_key": 43,
        "shadow": "Deafness",
        "gift": "Insight",
        "siddhi": "Epiphany",
        "shadow_keywords": ["not hearing", "deaf to", "blocked", "closed", "missing", "ignoring"],
        "gift_keywords": ["insightful", "hearing", "understanding", "clarity", "breakthrough", "aha"]
    },
    44: {
        "gene_key": 44,
        "shadow": "Interference",
        "gift": "Teamwork",
        "siddhi": "Synarchy",
        "shadow_keywords": ["interfering", "meddling", "controlling", "disrupting", "blocking", "getting in the way"],
        "gift_keywords": ["teamwork", "collaborating", "supporting", "synergy", "together", "cooperative"]
    },
    45: {
        "gene_key": 45,
        "shadow": "Dominance",
        "gift": "Synergy",
        "siddhi": "Communion",
        "shadow_keywords": ["dominating", "controlling", "power over", "hierarchical", "superior", "ruling"],
        "gift_keywords": ["synergistic", "collaborative", "communal", "together", "sharing", "unified"]
    },
    46: {
        "gene_key": 46,
        "shadow": "Seriousness",
        "gift": "Delight",
        "siddhi": "Ecstasy",
        "shadow_keywords": ["serious", "heavy", "grave", "no fun", "tense", "burdened", "weighed down"],
        "gift_keywords": ["delightful", "light", "joyful", "playful", "pleasurable", "ecstatic"]
    },
    47: {
        "gene_key": 47,
        "shadow": "Oppression",
        "gift": "Transmutation",
        "siddhi": "Transfiguration",
        "shadow_keywords": ["oppressed", "stuck", "trapped", "heavy", "burdened", "suffering", "dark"],
        "gift_keywords": ["transmuting", "transforming", "alchemizing", "shifting", "freeing", "changing"]
    },
    48: {
        "gene_key": 48,
        "shadow": "Inadequacy",
        "gift": "Resourcefulness",
        "siddhi": "Wisdom",
        "shadow_keywords": ["inadequate", "not enough", "lacking", "unprepared", "incompetent", "deficient"],
        "gift_keywords": ["resourceful", "capable", "wise", "prepared", "skilled", "sufficient"]
    },
    49: {
        "gene_key": 49,
        "shadow": "Reaction",
        "gift": "Revolution",
        "siddhi": "Rebirth",
        "shadow_keywords": ["reactive", "triggered", "defensive", "knee-jerk", "emotional reaction", "volatile"],
        "gift_keywords": ["revolutionary", "transformative", "renewing", "changing", "evolving", "reborn"]
    },
    50: {
        "gene_key": 50,
        "shadow": "Corruption",
        "gift": "Equilibrium",
        "siddhi": "Harmony",
        "shadow_keywords": ["corrupted", "compromised", "out of balance", "distorted", "toxic", "polluted"],
        "gift_keywords": ["balanced", "equilibrium", "harmonious", "fair", "just", "pure"]
    },
    51: {
        "gene_key": 51,
        "shadow": "Agitation",
        "gift": "Initiative",
        "siddhi": "Awakening",
        "shadow_keywords": ["agitated", "restless", "anxious", "nervous", "unsettled", "disturbed"],
        "gift_keywords": ["initiating", "starting", "brave", "pioneering", "awakening", "bold"]
    },
    52: {
        "gene_key": 52,
        "shadow": "Stress",
        "gift": "Restraint",
        "siddhi": "Stillness",
        "shadow_keywords": ["stressed", "tense", "anxious", "pressure", "overwhelmed", "wound up"],
        "gift_keywords": ["restrained", "still", "calm", "peaceful", "centered", "at ease"]
    },
    53: {
        "gene_key": 53,
        "shadow": "Immaturity",
        "gift": "Expansion",
        "siddhi": "Superabundance",
        "shadow_keywords": ["immature", "childish", "naive", "undeveloped", "not ready", "green"],
        "gift_keywords": ["expanding", "growing", "maturing", "developing", "abundant", "flourishing"]
    },
    54: {
        "gene_key": 54,
        "shadow": "Greed",
        "gift": "Aspiration",
        "siddhi": "Ascension",
        "shadow_keywords": ["greedy", "grasping", "hoarding", "never enough", "wanting more", "accumulating"],
        "gift_keywords": ["aspiring", "ambitious", "rising", "growing", "reaching", "elevating"]
    },
    55: {
        "gene_key": 55,
        "shadow": "Victimisation",
        "gift": "Freedom",
        "siddhi": "Freedom",
        "shadow_keywords": ["victim", "helpless", "powerless", "poor me", "blaming", "suffering"],
        "gift_keywords": ["free", "empowered", "liberated", "choosing", "sovereign", "independent"]
    },
    56: {
        "gene_key": 56,
        "shadow": "Distraction",
        "gift": "Enrichment",
        "siddhi": "Intoxication",
        "shadow_keywords": ["distracted", "scattered", "unfocused", "lost", "wandering", "fragmented"],
        "gift_keywords": ["enriching", "focused", "meaningful", "present", "engaged", "attentive"]
    },
    57: {
        "gene_key": 57,
        "shadow": "Unease",
        "gift": "Intuition",
        "siddhi": "Clarity",
        "shadow_keywords": ["uneasy", "anxious", "worried", "fearful", "nervous", "uncertain"],
        "gift_keywords": ["intuitive", "clear", "knowing", "trusting", "sensing", "aware"]
    },
    58: {
        "gene_key": 58,
        "shadow": "Dissatisfaction",
        "gift": "Vitality",
        "siddhi": "Bliss",
        "shadow_keywords": ["dissatisfied", "unhappy", "complaining", "critical", "unfulfilled", "wanting"],
        "gift_keywords": ["vital", "alive", "joyful", "satisfied", "energized", "blissful"]
    },
    59: {
        "gene_key": 59,
        "shadow": "Dishonesty",
        "gift": "Intimacy",
        "siddhi": "Transparency",
        "shadow_keywords": ["dishonest", "hiding", "secretive", "lying", "closed", "guarded"],
        "gift_keywords": ["intimate", "honest", "open", "transparent", "vulnerable", "authentic"]
    },
    60: {
        "gene_key": 60,
        "shadow": "Limitation",
        "gift": "Realism",
        "siddhi": "Justice",
        "shadow_keywords": ["limited", "restricted", "trapped", "stuck", "can't", "impossible"],
        "gift_keywords": ["realistic", "practical", "accepting limits", "working with what is", "just"]
    },
    61: {
        "gene_key": 61,
        "shadow": "Psychosis",
        "gift": "Inspiration",
        "siddhi": "Sanctity",
        "shadow_keywords": ["mental pressure", "obsessive thoughts", "spiraling", "overwhelmed mentally", "crazy"],
        "gift_keywords": ["inspired", "creative", "visionary", "sacred", "clear mind", "channeling"]
    },
    62: {
        "gene_key": 62,
        "shadow": "Intellect",
        "gift": "Precision",
        "siddhi": "Impeccability",
        "shadow_keywords": ["over-intellectual", "too mental", "analyzing", "in my head", "detached"],
        "gift_keywords": ["precise", "clear", "accurate", "articulate", "effective", "impeccable"]
    },
    63: {
        "gene_key": 63,
        "shadow": "Doubt",
        "gift": "Inquiry",
        "siddhi": "Truth",
        "shadow_keywords": ["doubting", "uncertain", "questioning", "skeptical", "unsure", "second-guessing"],
        "gift_keywords": ["inquiring", "curious", "seeking truth", "questioning wisely", "open", "exploring"]
    },
    64: {
        "gene_key": 64,
        "shadow": "Confusion",
        "gift": "Imagination",
        "siddhi": "Illumination",
        "shadow_keywords": ["confused", "overwhelmed", "too many thoughts", "unclear", "foggy", "lost"],
        "gift_keywords": ["imaginative", "creative", "visionary", "clear", "illuminated", "inspired"]
    }
}


def get_gene_key_data(gate: int) -> Optional[GeneKeyData]:
    """Get Gene Key data for a specific gate number.
    
    Args:
        gate: The gate number (1-64), same as Gene Key number
    
    Returns:
        GeneKeyData if found, None otherwise
    """
    return GENE_KEYS.get(gate)


def is_gene_key_available(gate: int) -> bool:
    """Check if Gene Key interpretation is available for a gate."""
    return gate in GENE_KEYS


def get_all_gene_keys() -> dict[int, GeneKeyData]:
    """Get all Gene Keys data."""
    return GENE_KEYS
