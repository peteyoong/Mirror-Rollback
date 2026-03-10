"""Gene Keys Interpretation Service

Provides interpretive layer for Gene Keys based on Human Design gate/line data.
This service does NOT compute anything - it only provides interpretation.

The deterministic compute is done in /calculations/gene_keys.py.
This service adds the Shadow/Gift/Siddhi meaning layer.
"""

from typing import Optional, TypedDict
from data.gene_keys_data import GENE_KEYS, GeneKeyData, is_gene_key_available


class GeneKeyInterpretation(TypedDict):
    """Full Gene Key interpretation response."""
    gene_key: int
    line: int
    shadow: str
    gift: str
    siddhi: str
    available: bool
    message: Optional[str]


def get_gene_key_interpretation(gate: int, line: int) -> GeneKeyInterpretation:
    """Get Gene Key interpretation for a specific gate and line.
    
    Args:
        gate: The gate number (1-64), same as Gene Key number
        line: The line number (1-6)
    
    Returns:
        GeneKeyInterpretation with shadow, gift, siddhi meanings
    """
    # Validate inputs
    if not (1 <= gate <= 64):
        return {
            "gene_key": gate,
            "line": line,
            "shadow": "",
            "gift": "",
            "siddhi": "",
            "available": False,
            "message": f"Invalid gate number: {gate}. Must be 1-64."
        }
    
    if not (1 <= line <= 6):
        return {
            "gene_key": gate,
            "line": line,
            "shadow": "",
            "gift": "",
            "siddhi": "",
            "available": False,
            "message": f"Invalid line number: {line}. Must be 1-6."
        }
    
    # Check if Gene Key data is available
    if not is_gene_key_available(gate):
        return {
            "gene_key": gate,
            "line": line,
            "shadow": "",
            "gift": "",
            "siddhi": "",
            "available": False,
            "message": f"Gene Key {gate} interpretation not yet available. Coming soon."
        }
    
    # Get the Gene Key data
    gk_data = GENE_KEYS[gate]
    
    return {
        "gene_key": gk_data["gene_key"],
        "line": line,
        "shadow": gk_data["shadow"],
        "gift": gk_data["gift"],
        "siddhi": gk_data["siddhi"],
        "available": True,
        "message": None
    }


def get_available_gene_keys() -> list[int]:
    """Get list of Gene Key numbers that have interpretation data."""
    return list(GENE_KEYS.keys())
