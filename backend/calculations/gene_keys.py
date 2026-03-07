"""Gene Keys Sequence Computation

===============================================================================
DETERMINISTIC COMPUTATION CORE - FROZEN
===============================================================================
This file is part of Project Mirror's deterministic computation core.
Outputs must remain stable across versions.
Do NOT modify without updating regression tests and bumping computation_version.

Current version: gk_sidereal_v1
Derived from: Human Design planetary positions (hd_sidereal_v1)

FROZEN: 2025-03-07 - All benchmarks passed (Jay, Melissa, Pete)
===============================================================================

Gene Keys sequences are deterministically derived from Human Design chart data.
Each sequence position maps to a specific planet from either the personality
(conscious/birth) or design (unconscious/88° before birth) chart.

Sequences:
- Purpose Arc: lifes_work, evolution, radiance, purpose
- Love Arc: attraction, iq, eq, sq, core_wound
- Prosperity Arc: brand, culture, vocation, pearl
"""

from typing import Dict, Any, List


# Gene Keys version (frozen)
GENE_KEYS_VERSION = "gk_sidereal_v1"


# =============================================================================
# SEQUENCE DEFINITIONS (FROZEN)
# =============================================================================
# Each sequence position maps to: (planet_name, chart_type)
# chart_type: "personality" (conscious/birth) or "design" (unconscious)

SEQUENCE_DEFINITIONS = {
    # Purpose Arc
    "lifes_work": ("Sun", "personality"),
    "evolution": ("Earth", "personality"),
    "radiance": ("Sun", "design"),
    "purpose": ("Earth", "design"),
    
    # Love Arc
    "attraction": ("Venus", "design"),
    "iq": ("Mercury", "personality"),
    "eq": ("Venus", "personality"),
    "sq": ("Moon", "design"),
    "core_wound": ("Mars", "design"),
    
    # Prosperity Arc
    "brand": ("Sun", "personality"),  # Same as lifes_work
    "culture": ("Jupiter", "design"),
    "vocation": ("Mars", "design"),  # Same as core_wound
    "pearl": ("Jupiter", "personality"),
}


# Arc groupings for structured output
PURPOSE_ARC = ["lifes_work", "evolution", "radiance", "purpose"]
LOVE_ARC = ["attraction", "iq", "eq", "sq", "core_wound"]
PROSPERITY_ARC = ["brand", "culture", "vocation", "pearl"]


def get_gene_keys_sequences(hd_chart: Dict[str, Any]) -> Dict[str, Any]:
    """Derive Gene Keys sequences from Human Design chart data.
    
    This is a deterministic computation - same HD input always produces
    same Gene Keys output. No interpretation or randomness involved.
    
    Args:
        hd_chart: Human Design chart from get_human_design_chart()
                  Must contain 'personality_data' and 'design_data' keys
    
    Returns:
        Dict with:
        - gene_keys_version: Version string
        - purpose_arc: Dict of purpose sequence positions
        - love_arc: Dict of love sequence positions
        - prosperity_arc: Dict of prosperity sequence positions
        - all_sequences: Flat dict of all positions
        
        Each position contains:
        - gate: int (1-64)
        - line: int (1-6)
        - source_planet: str (e.g., "Sun", "Venus")
        - source_chart: str ("personality" or "design")
    """
    # Extract personality and design data from HD chart
    personality_data = hd_chart.get('personality_data', {})
    design_data = hd_chart.get('design_data', {})
    
    if not personality_data or not design_data:
        raise ValueError("HD chart must contain personality_data and design_data")
    
    # Build all sequences
    all_sequences = {}
    
    for position_name, (planet, chart_type) in SEQUENCE_DEFINITIONS.items():
        # Get the correct chart data
        chart_data = personality_data if chart_type == "personality" else design_data
        
        # Get planet data
        planet_data = chart_data.get(planet)
        if not planet_data:
            raise ValueError(f"Missing planet data for {planet} in {chart_type} chart")
        
        gate_info = planet_data.get('gate', {})
        
        all_sequences[position_name] = {
            "gate": gate_info.get('gate'),
            "line": gate_info.get('line'),
            "source_planet": planet,
            "source_chart": chart_type,
        }
    
    # Build arc groupings
    purpose_arc = {k: all_sequences[k] for k in PURPOSE_ARC}
    love_arc = {k: all_sequences[k] for k in LOVE_ARC}
    prosperity_arc = {k: all_sequences[k] for k in PROSPERITY_ARC}
    
    return {
        "gene_keys_version": GENE_KEYS_VERSION,
        "purpose_arc": purpose_arc,
        "love_arc": love_arc,
        "prosperity_arc": prosperity_arc,
        "all_sequences": all_sequences,
    }


def get_gene_keys_from_birth(
    birth_datetime,
    lat: float,
    lon: float,
    sidereal_settings: Dict = None
) -> Dict[str, Any]:
    """Convenience function to compute Gene Keys directly from birth data.
    
    This computes the HD chart first, then derives Gene Keys sequences.
    
    Args:
        birth_datetime: UTC datetime of birth
        lat: Latitude
        lon: Longitude
        sidereal_settings: Optional sidereal configuration
    
    Returns:
        Dict with Gene Keys sequences plus HD metadata
    """
    from calculations.human_design import get_human_design_chart
    
    # Get HD chart (includes personality_data and design_data)
    hd_chart = get_human_design_chart(birth_datetime, lat, lon, sidereal_settings)
    
    # Derive Gene Keys
    gk_sequences = get_gene_keys_sequences(hd_chart)
    
    # Add HD metadata for reference
    gk_sequences["hd_metadata"] = {
        "computation_version": hd_chart.get("computation_version"),
        "astronomy_version": hd_chart.get("astronomy_version"),
        "human_design_version": hd_chart.get("human_design_version"),
        "profile": hd_chart.get("profile"),
        "type": hd_chart.get("type"),
    }
    
    return gk_sequences


# =============================================================================
# VALIDATION
# =============================================================================

def validate_gene_keys_output(gk_data: Dict[str, Any]) -> List[str]:
    """Validate Gene Keys output structure and values.
    
    Args:
        gk_data: Output from get_gene_keys_sequences()
    
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    # Check version
    if gk_data.get("gene_keys_version") != GENE_KEYS_VERSION:
        errors.append(f"Invalid version: {gk_data.get('gene_keys_version')}")
    
    # Check all sequences exist
    all_sequences = gk_data.get("all_sequences", {})
    for position in SEQUENCE_DEFINITIONS.keys():
        if position not in all_sequences:
            errors.append(f"Missing sequence position: {position}")
            continue
        
        pos_data = all_sequences[position]
        
        # Check gate (1-64)
        gate = pos_data.get("gate")
        if not isinstance(gate, int) or gate < 1 or gate > 64:
            errors.append(f"{position}: Invalid gate {gate}")
        
        # Check line (1-6)
        line = pos_data.get("line")
        if not isinstance(line, int) or line < 1 or line > 6:
            errors.append(f"{position}: Invalid line {line}")
        
        # Check source_planet
        expected_planet = SEQUENCE_DEFINITIONS[position][0]
        if pos_data.get("source_planet") != expected_planet:
            errors.append(f"{position}: Wrong planet {pos_data.get('source_planet')}, expected {expected_planet}")
        
        # Check source_chart
        expected_chart = SEQUENCE_DEFINITIONS[position][1]
        if pos_data.get("source_chart") != expected_chart:
            errors.append(f"{position}: Wrong chart {pos_data.get('source_chart')}, expected {expected_chart}")
    
    return errors
