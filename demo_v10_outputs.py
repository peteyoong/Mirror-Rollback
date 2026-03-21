#!/usr/bin/env python3
"""
V10.1 Structural Variation Language Demonstration
Shows how different signal combinations produce FUNDAMENTALLY DIFFERENT
sentence structures, not just modified versions of the same base sentence.
"""

import sys
sys.path.insert(0, '/app/backend')

from services.pattern_mirror import (
    generate_why_now,
    generate_friction,
    generate_practical,
    generate_core_insight,
    PATTERN_TEMPLATES,
    WHY_NOW_STRUCTURES,
    FRICTION_STRUCTURES,
    PRACTICAL_STRUCTURES,
    CORE_INSIGHT_STRUCTURES,
)

# ============================================================================
# SIGNAL PROFILES - Different emotional combinations
# ============================================================================

def create_signals(journal_text: str, lifeline_events: list = None):
    return {
        "memory": {
            "journal_entries": [{"content": journal_text}] if journal_text else [],
            "chat_messages": [],
            "lifeline_events": lifeline_events or [],
        }
    }

SIGNAL_PROFILES = {
    "warmth_growth": create_signals(
        "I feel grateful and hopeful. Something is changing and I'm excited about growing into this new version of myself."
    ),
    "hesitation_resistance": create_signals(
        "I'm not sure about this. Maybe I shouldn't do it. I don't want to get hurt again. I need to protect myself."
    ),
    "grief_resistance": create_signals(
        "I miss how things were. It's gone now and I don't want to accept it. I refuse to let go of what we had."
    ),
    "clarity_pressure": create_signals(
        "I finally understand what's happening. It's so clear now. But there's so much pressure and I have to figure this out urgently."
    ),
    "confusion_hesitation": create_signals(
        "I'm confused about what to do. Everything feels mixed up. Maybe I should wait. I'm not sure."
    ),
    "repeated_cycles": create_signals(
        "Here we go again. I'm cautious about this.",
        lifeline_events=[{"title": "Same pattern", "description": "This keeps happening again and again, the same way every time."}]
    ),
    "baseline": create_signals(""),
}

# ============================================================================
# PATTERNS TO DEMONSTRATE
# ============================================================================

PATTERNS = [
    ("relational_reopening", "RELATIONAL REOPENING"),
    ("threshold_standing", "STANDING AT A THRESHOLD"),
    ("over_functioning_hero", "THE OVER-FUNCTIONING HERO"),
    ("somethings_here", "SOMETHING'S HERE"),
    ("moving_through", "MOVING THROUGH"),
]

# Variants to show per pattern
VARIANTS = [
    ("warmth_growth", "Warmth + Growth"),
    ("hesitation_resistance", "Hesitation + Resistance"),
    ("grief_resistance", "Grief + Resistance"),
    ("clarity_pressure", "Clarity + Pressure"),
    ("repeated_cycles", "Repeated Cycles"),
    ("baseline", "Baseline (no signals)"),
]

# ============================================================================
# GENERATE AND DISPLAY
# ============================================================================

def generate_full_output(pattern_id: str, signal_profile_name: str):
    """Generate complete output for a pattern + signal combination."""
    
    pattern = PATTERN_TEMPLATES.get(pattern_id, {"title": pattern_id})
    signals = SIGNAL_PROFILES[signal_profile_name]
    cluster_data = {"source_diversity_score": 0.6, "total_evidence_count": 3}
    
    # Generate each section using structural variation
    core_insight = generate_core_insight(pattern_id, pattern, signals, f"user_{signal_profile_name}")
    
    why_now = generate_why_now(
        pattern_id, pattern, signals, cluster_data, None,
        WHY_NOW_STRUCTURES, f"user_{signal_profile_name}"
    )
    
    friction = generate_friction(
        pattern_id, pattern, signals, cluster_data,
        FRICTION_STRUCTURES, f"user_{signal_profile_name}"
    )
    
    practical = generate_practical(
        pattern_id, pattern, signals, cluster_data,
        PRACTICAL_STRUCTURES, f"user_{signal_profile_name}"
    )
    
    return {
        "core_insight": core_insight,
        "why_now": why_now,
        "friction": friction,
        "practical": practical,
    }


def print_pattern_outputs(pattern_id: str, pattern_name: str):
    """Print outputs for a pattern across different signal profiles."""
    
    print()
    print("=" * 90)
    print(f"PATTERN: {pattern_name}")
    print("=" * 90)
    
    for variant_key, variant_label in VARIANTS:
        output = generate_full_output(pattern_id, variant_key)
        
        print()
        print("-" * 90)
        print(f"SIGNAL: {variant_label.upper()}")
        print("-" * 90)
        print()
        print(f"  CORE INSIGHT:")
        print(f"    \"{output['core_insight']}\"")
        print()
        print(f"  WHY NOW:")
        print(f"    \"{output['why_now']}\"")
        print()
        print(f"  FRICTION:")
        print(f"    \"{output['friction']}\"")
        print()
        print(f"  PRACTICAL:")
        print(f"    \"{output['practical']}\"")


def main():
    print()
    print("╔════════════════════════════════════════════════════════════════════════════════════════╗")
    print("║         V10.1 STRUCTURAL VARIATION: SIDE-BY-SIDE OUTPUT DEMONSTRATION                  ║")
    print("╚════════════════════════════════════════════════════════════════════════════════════════╝")
    print()
    print("Each pattern generates FUNDAMENTALLY DIFFERENT sentences based on signal combinations.")
    print("This is NOT just 'same sentence + suffix'. The entire framing changes.")
    print()
    
    for pattern_id, pattern_name in PATTERNS:
        print_pattern_outputs(pattern_id, pattern_name)
    
    print()
    print("=" * 90)
    print("END OF V10.1 STRUCTURAL VARIATION DEMONSTRATION")
    print("=" * 90)


if __name__ == "__main__":
    main()
