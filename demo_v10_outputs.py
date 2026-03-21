#!/usr/bin/env python3
"""
V10 Language Output Demonstration
Generates side-by-side examples showing how the same pattern 
produces different outputs with different signal profiles.
"""

import sys
sys.path.insert(0, '/app/backend')

from services.pattern_mirror import (
    generate_why_now,
    generate_friction,
    generate_practical,
    PATTERN_TEMPLATES,
)

# ============================================================================
# SIGNAL PROFILES
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
    "warmth_hesitation": create_signals(
        "I feel grateful and hopeful but I'm not sure if I should trust this feeling. Maybe it's too good to be true."
    ),
    "clarity_pressure": create_signals(
        "I finally understand what's been happening. It's so clear now. But there's so much pressure and I have to figure this out."
    ),
    "grief_resistance": create_signals(
        "I miss how things were. It's gone now and I don't want to accept it. I refuse to let go of what we had."
    ),
    "growth_confusion": create_signals(
        "I'm changing and becoming someone different. But I'm confused about where this is going. Everything feels mixed up."
    ),
    "repeated_cycles_hesitation": create_signals(
        "I'm not sure about this. Maybe I'm being too cautious.",
        lifeline_events=[{"title": "Here again", "description": "This same pattern keeps happening again and again"}]
    ),
    "no_signals": create_signals(""),
}

# ============================================================================
# PATTERN CONFIGURATIONS
# ============================================================================

PATTERNS_TO_TEST = {
    "relational_reopening": {
        "title": "Relational Reopening",
        "insight": "Something in you may be becoming more willing to let connection back in—not because the risk has gone away, but because the pull toward closeness has become harder to ignore.",
        "variants": ["warmth_hesitation", "grief_resistance", "no_signals"],
    },
    "threshold_standing": {
        "title": "Standing at a Threshold",
        "insight": "You may be standing at a decision point—not because the answer is clear, but because the question has become unavoidable.",
        "variants": ["clarity_pressure", "growth_confusion", "repeated_cycles_hesitation"],
    },
    "over_functioning_hero": {
        "title": "The Over-Functioning Hero",
        "insight": "You may be carrying more than your share—doing the work others could do, holding things together that aren't yours to hold.",
        "variants": ["clarity_pressure", "grief_resistance", "no_signals"],
    },
    "somethings_here": {
        "title": "Something's Here",
        "insight": "Something is present that wasn't before—a feeling, an awareness, a shift. It may not have a name yet.",
        "variants": ["warmth_hesitation", "growth_confusion", "no_signals"],
    },
    "moving_through": {
        "title": "Moving Through",
        "insight": "Something you've been holding is ready to move through you—not to be solved or fixed, but to be felt and released.",
        "variants": ["grief_resistance", "growth_confusion", "repeated_cycles_hesitation"],
    },
}

# ============================================================================
# BASE MAPS (for generation)
# ============================================================================

WHY_NOW_MAP = {
    "relational_reopening": {
        "high": "Something in you may be becoming more willing to let connection back in.",
        "medium": "Momentum is building around connection—readiness is growing.",
        "low": "Current timing may be making openness feel more possible.",
    },
    "threshold_standing": {
        "high": "You're at a decision point, and multiple signals are converging on it.",
        "medium": "A choice is becoming more present—the moment feels ripe.",
        "low": "Current timing may be highlighting a threshold.",
    },
    "over_functioning_hero": {
        "high": "The weight of carrying so much is becoming harder to ignore.",
        "medium": "Something about your current load is asking for attention.",
        "low": "Current pressures may be revealing where you're overextended.",
    },
    "somethings_here": {
        "high": "Something has been stirring and is now ready to be noticed.",
        "medium": "An awareness is emerging—something wants attention.",
        "low": "Current timing may be bringing something into focus.",
    },
    "moving_through": {
        "high": "Something you've been holding is ready to move through you.",
        "medium": "Processing something old may feel more available now.",
        "low": "Timing may be supporting release or completion.",
    },
}

FRICTION_MAP = {
    "relational_reopening": "Part of you may still want proof that openness is safe.",
    "threshold_standing": "You may still be waiting for certainty before stepping forward.",
    "over_functioning_hero": "You might find it hard to rest when there's still something you could do.",
    "somethings_here": "You might be resisting naming it too soon.",
    "moving_through": "Part of you may be minimizing what you're actually grieving.",
}

PRACTICAL_MAP = {
    "relational_reopening": "Let yourself notice one small moment of connection without immediately evaluating it.",
    "threshold_standing": "Let yourself notice what already feels true before asking for more proof.",
    "over_functioning_hero": "Let one thing be good enough today without fixing it further.",
    "somethings_here": "Name one feeling you notice right now, even if it's incomplete.",
    "moving_through": "Give yourself permission to feel what's actually here, not what you think you should feel.",
}

# ============================================================================
# GENERATE OUTPUTS
# ============================================================================

def generate_variant_output(pattern_id: str, signal_profile_name: str):
    """Generate complete output for a pattern + signal combination."""
    
    pattern = PATTERN_TEMPLATES.get(pattern_id, {"title": pattern_id})
    signals = SIGNAL_PROFILES[signal_profile_name]
    
    # Simulate high evidence for consistent base text selection
    cluster_data = {"source_diversity_score": 0.6, "total_evidence_count": 3}
    
    # Generate each layer
    why_now = generate_why_now(
        pattern_id, pattern, signals, cluster_data, None,
        WHY_NOW_MAP, f"user_{signal_profile_name}"
    )
    
    friction = generate_friction(
        pattern_id, pattern, signals, cluster_data,
        FRICTION_MAP, f"user_{signal_profile_name}"
    )
    
    practical = generate_practical(
        pattern_id, pattern, signals, cluster_data,
        PRACTICAL_MAP, f"user_{signal_profile_name}"
    )
    
    return {
        "why_now": why_now,
        "friction": friction,
        "practical": practical,
    }


def print_pattern_comparison(pattern_id: str, config: dict):
    """Print side-by-side comparison for a pattern."""
    
    print()
    print("=" * 80)
    print(f"PATTERN: {config['title'].upper()}")
    print("=" * 80)
    print()
    print(f"Core Insight: {config['insight']}")
    print()
    
    for i, variant_name in enumerate(config["variants"], 1):
        output = generate_variant_output(pattern_id, variant_name)
        
        # Format the signal profile name nicely
        profile_label = variant_name.replace("_", " + ").upper()
        if variant_name == "no_signals":
            profile_label = "BASELINE (no signals)"
        
        print("-" * 80)
        print(f"VARIANT {i}: {profile_label}")
        print("-" * 80)
        print()
        print(f"Why this may be showing up:")
        print(f"  \"{output['why_now']}\"")
        print()
        print(f"Where the friction may be:")
        print(f"  \"{output['friction']}\"")
        print()
        print(f"What to do with it:")
        print(f"  \"{output['practical']}\"")
        print()


def main():
    print()
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║          V10 CONTEXT-AWARE LANGUAGE: SIDE-BY-SIDE OUTPUT EXAMPLES            ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print()
    print("Each pattern is generated 3 times with different signal profiles.")
    print("Notice how the language adapts to the user's emotional context.")
    print()
    
    for pattern_id, config in PATTERNS_TO_TEST.items():
        print_pattern_comparison(pattern_id, config)
    
    print()
    print("=" * 80)
    print("END OF V10 LANGUAGE DEMONSTRATION")
    print("=" * 80)


if __name__ == "__main__":
    main()
