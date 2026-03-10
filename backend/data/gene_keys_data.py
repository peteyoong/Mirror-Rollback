"""Gene Keys Interpretive Data

This module contains the Shadow/Gift/Siddhi meanings for Gene Keys.
Gene Keys use the same gate numbers and line numbers as Human Design.

Gene Key = Gate Number
Gene Key Line = Gate Line

This is an INTERPRETATION LAYER on top of Human Design deterministic data.
All 64 Gene Keys with canonical Shadow/Gift/Siddhi names.
"""

from typing import TypedDict, Optional


class GeneKeyData(TypedDict):
    """Gene Key interpretive data structure."""
    gene_key: int
    shadow: str
    gift: str
    siddhi: str


# Complete 64 Gene Keys with canonical Shadow -> Gift -> Siddhi
GENE_KEYS: dict[int, GeneKeyData] = {
    1: {
        "gene_key": 1,
        "shadow": "Entropy",
        "gift": "Freshness",
        "siddhi": "Beauty"
    },
    2: {
        "gene_key": 2,
        "shadow": "Dislocation",
        "gift": "Orientation",
        "siddhi": "Unity"
    },
    3: {
        "gene_key": 3,
        "shadow": "Chaos",
        "gift": "Innovation",
        "siddhi": "Innocence"
    },
    4: {
        "gene_key": 4,
        "shadow": "Intolerance",
        "gift": "Understanding",
        "siddhi": "Forgiveness"
    },
    5: {
        "gene_key": 5,
        "shadow": "Impatience",
        "gift": "Patience",
        "siddhi": "Timelessness"
    },
    6: {
        "gene_key": 6,
        "shadow": "Conflict",
        "gift": "Diplomacy",
        "siddhi": "Peace"
    },
    7: {
        "gene_key": 7,
        "shadow": "Division",
        "gift": "Guidance",
        "siddhi": "Virtue"
    },
    8: {
        "gene_key": 8,
        "shadow": "Mediocrity",
        "gift": "Style",
        "siddhi": "Exquisiteness"
    },
    9: {
        "gene_key": 9,
        "shadow": "Inertia",
        "gift": "Determination",
        "siddhi": "Invincibility"
    },
    10: {
        "gene_key": 10,
        "shadow": "Self-Obsession",
        "gift": "Naturalness",
        "siddhi": "Being"
    },
    11: {
        "gene_key": 11,
        "shadow": "Obscurity",
        "gift": "Idealism",
        "siddhi": "Light"
    },
    12: {
        "gene_key": 12,
        "shadow": "Vanity",
        "gift": "Discrimination",
        "siddhi": "Purity"
    },
    13: {
        "gene_key": 13,
        "shadow": "Discord",
        "gift": "Discernment",
        "siddhi": "Empathy"
    },
    14: {
        "gene_key": 14,
        "shadow": "Compromise",
        "gift": "Competence",
        "siddhi": "Bounteousness"
    },
    15: {
        "gene_key": 15,
        "shadow": "Dullness",
        "gift": "Magnetism",
        "siddhi": "Florescence"
    },
    16: {
        "gene_key": 16,
        "shadow": "Indifference",
        "gift": "Versatility",
        "siddhi": "Mastery"
    },
    17: {
        "gene_key": 17,
        "shadow": "Opinion",
        "gift": "Far-Sightedness",
        "siddhi": "Omniscience"
    },
    18: {
        "gene_key": 18,
        "shadow": "Judgement",
        "gift": "Integrity",
        "siddhi": "Perfection"
    },
    19: {
        "gene_key": 19,
        "shadow": "Co-Dependence",
        "gift": "Sensitivity",
        "siddhi": "Sacrifice"
    },
    20: {
        "gene_key": 20,
        "shadow": "Superficiality",
        "gift": "Self-Assurance",
        "siddhi": "Presence"
    },
    21: {
        "gene_key": 21,
        "shadow": "Control",
        "gift": "Authority",
        "siddhi": "Valour"
    },
    22: {
        "gene_key": 22,
        "shadow": "Dishonour",
        "gift": "Graciousness",
        "siddhi": "Grace"
    },
    23: {
        "gene_key": 23,
        "shadow": "Complexity",
        "gift": "Simplicity",
        "siddhi": "Quintessence"
    },
    24: {
        "gene_key": 24,
        "shadow": "Addiction",
        "gift": "Invention",
        "siddhi": "Silence"
    },
    25: {
        "gene_key": 25,
        "shadow": "Constriction",
        "gift": "Acceptance",
        "siddhi": "Universal Love"
    },
    26: {
        "gene_key": 26,
        "shadow": "Pride",
        "gift": "Artfulness",
        "siddhi": "Invisibility"
    },
    27: {
        "gene_key": 27,
        "shadow": "Selfishness",
        "gift": "Altruism",
        "siddhi": "Selflessness"
    },
    28: {
        "gene_key": 28,
        "shadow": "Purposelessness",
        "gift": "Totality",
        "siddhi": "Immortality"
    },
    29: {
        "gene_key": 29,
        "shadow": "Half-Heartedness",
        "gift": "Commitment",
        "siddhi": "Devotion"
    },
    30: {
        "gene_key": 30,
        "shadow": "Desire",
        "gift": "Lightness",
        "siddhi": "Rapture"
    },
    31: {
        "gene_key": 31,
        "shadow": "Arrogance",
        "gift": "Leadership",
        "siddhi": "Humility"
    },
    32: {
        "gene_key": 32,
        "shadow": "Failure",
        "gift": "Preservation",
        "siddhi": "Veneration"
    },
    33: {
        "gene_key": 33,
        "shadow": "Forgetting",
        "gift": "Mindfulness",
        "siddhi": "Revelation"
    },
    34: {
        "gene_key": 34,
        "shadow": "Force",
        "gift": "Strength",
        "siddhi": "Majesty"
    },
    35: {
        "gene_key": 35,
        "shadow": "Hunger",
        "gift": "Adventure",
        "siddhi": "Boundlessness"
    },
    36: {
        "gene_key": 36,
        "shadow": "Turbulence",
        "gift": "Humanity",
        "siddhi": "Compassion"
    },
    37: {
        "gene_key": 37,
        "shadow": "Weakness",
        "gift": "Equality",
        "siddhi": "Tenderness"
    },
    38: {
        "gene_key": 38,
        "shadow": "Struggle",
        "gift": "Perseverance",
        "siddhi": "Honour"
    },
    39: {
        "gene_key": 39,
        "shadow": "Provocation",
        "gift": "Dynamism",
        "siddhi": "Liberation"
    },
    40: {
        "gene_key": 40,
        "shadow": "Exhaustion",
        "gift": "Resolve",
        "siddhi": "Divine Will"
    },
    41: {
        "gene_key": 41,
        "shadow": "Fantasy",
        "gift": "Anticipation",
        "siddhi": "Emanation"
    },
    42: {
        "gene_key": 42,
        "shadow": "Expectation",
        "gift": "Detachment",
        "siddhi": "Celebration"
    },
    43: {
        "gene_key": 43,
        "shadow": "Deafness",
        "gift": "Insight",
        "siddhi": "Epiphany"
    },
    44: {
        "gene_key": 44,
        "shadow": "Interference",
        "gift": "Teamwork",
        "siddhi": "Synarchy"
    },
    45: {
        "gene_key": 45,
        "shadow": "Dominance",
        "gift": "Synergy",
        "siddhi": "Communion"
    },
    46: {
        "gene_key": 46,
        "shadow": "Seriousness",
        "gift": "Delight",
        "siddhi": "Ecstasy"
    },
    47: {
        "gene_key": 47,
        "shadow": "Oppression",
        "gift": "Transmutation",
        "siddhi": "Transfiguration"
    },
    48: {
        "gene_key": 48,
        "shadow": "Inadequacy",
        "gift": "Resourcefulness",
        "siddhi": "Wisdom"
    },
    49: {
        "gene_key": 49,
        "shadow": "Reaction",
        "gift": "Revolution",
        "siddhi": "Rebirth"
    },
    50: {
        "gene_key": 50,
        "shadow": "Corruption",
        "gift": "Equilibrium",
        "siddhi": "Harmony"
    },
    51: {
        "gene_key": 51,
        "shadow": "Agitation",
        "gift": "Initiative",
        "siddhi": "Awakening"
    },
    52: {
        "gene_key": 52,
        "shadow": "Stress",
        "gift": "Restraint",
        "siddhi": "Stillness"
    },
    53: {
        "gene_key": 53,
        "shadow": "Immaturity",
        "gift": "Expansion",
        "siddhi": "Superabundance"
    },
    54: {
        "gene_key": 54,
        "shadow": "Greed",
        "gift": "Aspiration",
        "siddhi": "Ascension"
    },
    55: {
        "gene_key": 55,
        "shadow": "Victimisation",
        "gift": "Freedom",
        "siddhi": "Freedom"
    },
    56: {
        "gene_key": 56,
        "shadow": "Distraction",
        "gift": "Enrichment",
        "siddhi": "Intoxication"
    },
    57: {
        "gene_key": 57,
        "shadow": "Unease",
        "gift": "Intuition",
        "siddhi": "Clarity"
    },
    58: {
        "gene_key": 58,
        "shadow": "Dissatisfaction",
        "gift": "Vitality",
        "siddhi": "Bliss"
    },
    59: {
        "gene_key": 59,
        "shadow": "Dishonesty",
        "gift": "Intimacy",
        "siddhi": "Transparency"
    },
    60: {
        "gene_key": 60,
        "shadow": "Limitation",
        "gift": "Realism",
        "siddhi": "Justice"
    },
    61: {
        "gene_key": 61,
        "shadow": "Psychosis",
        "gift": "Inspiration",
        "siddhi": "Sanctity"
    },
    62: {
        "gene_key": 62,
        "shadow": "Intellect",
        "gift": "Precision",
        "siddhi": "Impeccability"
    },
    63: {
        "gene_key": 63,
        "shadow": "Doubt",
        "gift": "Inquiry",
        "siddhi": "Truth"
    },
    64: {
        "gene_key": 64,
        "shadow": "Confusion",
        "gift": "Imagination",
        "siddhi": "Illumination"
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
