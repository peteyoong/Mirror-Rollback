"""Gene Keys Interpretive Data

This module contains the Shadow/Gift/Siddhi meanings for Gene Keys.
Gene Keys use the same gate numbers and line numbers as Human Design.

Gene Key = Gate Number
Gene Key Line = Gate Line

This is an INTERPRETATION LAYER on top of Human Design deterministic data.
"""

from typing import TypedDict, Optional


class GeneKeyData(TypedDict):
    """Gene Key interpretive data structure."""
    gene_key: int
    shadow: str
    gift: str
    siddhi: str


# Gene Keys data - Only 3 keys populated for initial scaffold
# These are the Shadow -> Gift -> Siddhi transformations
GENE_KEYS: dict[int, GeneKeyData] = {
    22: {
        "gene_key": 22,
        "shadow": "Dishonor",
        "gift": "Graciousness",
        "siddhi": "Grace"
    },
    34: {
        "gene_key": 34,
        "shadow": "Force",
        "gift": "Strength",
        "siddhi": "Majesty"
    },
    10: {
        "gene_key": 10,
        "shadow": "Self-Obsession",
        "gift": "Naturalness",
        "siddhi": "Being"
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
