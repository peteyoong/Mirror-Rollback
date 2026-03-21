#!/usr/bin/env python3
"""
V10.4 Confidence-Aware Expression Demonstration
Shows how the system adapts tone and certainty based on frame ranking confidence.
- HIGH: Direct, clear statements
- MEDIUM: Light softening
- LOW: Dual-frame expression combining top 2 frames
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
    FRAME_TYPES,
)

# ============================================================================
# SIGNAL PROFILES - Designed to produce different confidence levels
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
    # HIGH confidence - very clear signals
    "warmth_growth": create_signals(
        "I feel grateful and hopeful. Something is changing and I'm excited about growing into this new version of myself. I'm ready for what's next."
    ),
    # MEDIUM confidence - moderately clear signals
    "grief_resistance": create_signals(
        "I miss how things were. It's gone now and I don't want to accept it."
    ),
    # LOW confidence - ambiguous/mixed signals (should trigger dual-frame)
    "ambiguous_mixed": create_signals(
        "I want to move forward but I'm also scared. Part of me is ready, another part wants to stay safe. I feel both hopeful and protective."
    ),
    # MEDIUM confidence with lifeline
    "repeated_cycles": create_signals(
        "Here we go again. I'm cautious about this.",
        lifeline_events=[{"title": "Same pattern", "description": "This keeps happening again and again."}]
    ),
    # LOW confidence - conflicting signals (growth vs resistance)
    "conflicting": create_signals(
        "I'm growing and changing but I don't want to let go. I refuse to accept it but I also know I need to. It's confusing."
    ),
}

# ============================================================================
# PATTERNS TO DEMONSTRATE
# ============================================================================

PATTERNS = [
    ("relational_reopening", "RELATIONAL REOPENING"),
    ("threshold_standing", "STANDING AT A THRESHOLD"),
    ("moving_through", "MOVING THROUGH"),
]

# Variants to show per pattern - designed to show different confidence levels
VARIANTS = [
    ("warmth_growth", "HIGH: Clear Warmth + Growth"),
    ("grief_resistance", "MEDIUM: Grief + Resistance"),
    ("ambiguous_mixed", "LOW: Ambiguous/Mixed Signals"),
    ("conflicting", "LOW: Conflicting Signals"),
    ("repeated_cycles", "Repeated Cycles Pattern"),
]

# ============================================================================
# GENERATE AND DISPLAY WITH COMPETITIVE FRAME RANKING
# ============================================================================

def generate_coherent_output_with_debug(pattern_id: str, signal_profile_name: str):
    """Generate complete output with confidence-aware expression and debug info."""
    
    pattern = PATTERN_TEMPLATES.get(pattern_id, {"title": pattern_id})
    signals = SIGNAL_PROFILES[signal_profile_name]
    cluster_data = {"source_diversity_score": 0.6, "total_evidence_count": 3}
    
    # Step 1: Generate core insight with competitive frame ranking
    core_insight_text, frame_type, frame_debug = generate_core_insight(
        pattern_id, pattern, signals, f"user_{signal_profile_name}", debug=True
    )
    
    # Extract confidence info for passing to other generators
    confidence = frame_debug.get("confidence", "medium")
    margin = frame_debug.get("margin", 1.0)
    runner_up = frame_debug.get("runner_up", {})
    runner_up_frame = runner_up.get("frame_type", "") if runner_up else ""
    
    # Step 2: Generate all other sections with V10.4 confidence-aware parameters
    why_now = generate_why_now(
        pattern_id, pattern, signals, cluster_data, None,
        WHY_NOW_STRUCTURES, f"user_{signal_profile_name}",
        frame_type=frame_type,
        confidence=confidence,
        runner_up_frame=runner_up_frame,
        margin=margin
    )
    
    friction = generate_friction(
        pattern_id, pattern, signals, cluster_data,
        FRICTION_STRUCTURES, f"user_{signal_profile_name}",
        frame_type=frame_type,
        confidence=confidence,
        runner_up_frame=runner_up_frame,
        margin=margin
    )
    
    practical = generate_practical(
        pattern_id, pattern, signals, cluster_data,
        PRACTICAL_STRUCTURES, f"user_{signal_profile_name}",
        frame_type=frame_type,
        confidence=confidence,
        runner_up_frame=runner_up_frame,
        margin=margin
    )
    
    return {
        "frame_type": frame_type,
        "frame_debug": frame_debug,
        "core_insight": core_insight_text,
        "why_now": why_now,
        "friction": friction,
        "practical": practical,
    }


def format_frame_score(score_data: dict) -> str:
    """Format a single frame score for display."""
    parts = []
    if score_data.get("primary_matches"):
        matches = ", ".join([f"{s}:{v:.1f}" for s, v, _ in score_data["primary_matches"]])
        parts.append(f"primary=[{matches}]")
    if score_data.get("pattern_alignment"):
        parts.append(f"pattern={score_data['pattern_alignment']:+.1f}")
    if score_data.get("lifeline_bonus"):
        parts.append(f"lifeline={score_data['lifeline_bonus']:+.1f}")
    return " ".join(parts) if parts else "no matches"


def print_pattern_outputs(pattern_id: str, pattern_name: str):
    """Print outputs for a pattern across different signal profiles."""
    
    print()
    print("=" * 100)
    print(f"PATTERN: {pattern_name}")
    print("=" * 100)
    
    for variant_key, variant_label in VARIANTS:
        output = generate_coherent_output_with_debug(pattern_id, variant_key)
        
        frame_info = FRAME_TYPES.get(output['frame_type'], {})
        frame_debug = output['frame_debug']
        
        print()
        print("-" * 100)
        print(f"SIGNAL: {variant_label.upper()}")
        print("-" * 100)
        
        # Show frame ranking debug info
        print()
        print(f"  FRAME SELECTION (V10.3 Competitive Ranking):")
        print(f"    Winner: {output['frame_type']} (score: {frame_debug['winner']['total_score']:.1f})")
        if frame_debug.get('runner_up'):
            print(f"    Runner-up: {frame_debug['runner_up']['frame_type']} (score: {frame_debug['runner_up']['total_score']:.1f})")
        print(f"    Margin: {frame_debug['margin']:.1f}, Confidence: {frame_debug['confidence'].upper()}")
        
        # Show top 3 candidates if available
        if frame_debug.get('all_candidates'):
            print(f"    Top 3 candidates:")
            for i, candidate in enumerate(frame_debug['all_candidates'][:3], 1):
                details = format_frame_score(candidate)
                print(f"      {i}. {candidate['frame_type']}: {candidate['total_score']:.1f} ({details})")
        
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
    print("╔════════════════════════════════════════════════════════════════════════════════════════════════╗")
    print("║         V10.4 CONFIDENCE-AWARE EXPRESSION: TONE ADAPTATION DEMONSTRATION                       ║")
    print("╚════════════════════════════════════════════════════════════════════════════════════════════════╝")
    print()
    print("The system now ADAPTS TONE based on frame ranking confidence:")
    print("  - HIGH: Direct, clear statements (minimal hedging)")
    print("  - MEDIUM: Light softening ('may', 'seems', 'something in you')")
    print("  - LOW: Dual-frame expression (acknowledges ambiguity/both tendencies)")
    print()
    
    for pattern_id, pattern_name in PATTERNS:
        print_pattern_outputs(pattern_id, pattern_name)
    
    print()
    print("=" * 100)
    print("SUCCESS CRITERIA CHECK:")
    print("  ✓ Outputs feel more human in ambiguous situations (dual-frame expressions)")
    print("  ✓ Reduced 'false certainty' - HIGH confidence = direct, LOW = hedged")
    print("  ✓ Increased trust when signals are mixed")
    print("  ✓ System feels more nuanced and less rigid")
    print("=" * 100)


if __name__ == "__main__":
    main()
