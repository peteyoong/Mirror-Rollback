#!/usr/bin/env python3
"""
V9 Language System Validation Script

This script tests whether all pattern types have full V9 language coverage:
1. PATTERN_WHY_NOW - pattern-specific "why now" explanations
2. friction_map - specific friction statements  
3. practical_map - actionable suggestions
4. NATURAL_TITLES - human-readable titles

A pattern is considered V9-complete if it has entries in all relevant maps.
"""

import sys
sys.path.insert(0, '/app/backend')

from services.pattern_mirror import PATTERN_TEMPLATES

# Define the V9 language maps (copied from pattern_mirror.py for validation)
# These are the patterns with explicit V9 coverage

# V9 COMPLETE: All 16 content patterns have WHY_NOW entries
PATTERN_WHY_NOW_KEYS = {
    # Relational patterns
    "relational_reopening",
    "heart_thaw",
    "safe_intimacy_returning",
    "relational_weight",
    "reconnection_window",
    # Emotional patterns
    "somethings_here",
    "emotional_wave_riding",
    "moving_through",
    "emotional_integration",
    # Threshold/identity patterns
    "threshold_standing",
    "expansion_resistance",
    "anticipating_impact",
    # Behavioral patterns
    "duty_over_self",
    "over_functioning_hero",
    "inner_critic_override",
    "holding_the_line",
    # Opening/positive patterns
    "grounded_presence",
    "renewal_after_distance",
}

FRICTION_MAP_KEYS = {
    # Relational patterns
    "relational_reopening",
    "heart_thaw",
    "safe_intimacy_returning",
    "relational_weight",
    "reconnection_window",
    # Emotional patterns
    "somethings_here",
    "emotional_wave_riding",
    "moving_through",
    "emotional_integration",
    # Threshold/identity patterns
    "threshold_standing",
    "expansion_resistance",
    "anticipating_impact",
    # Behavioral patterns
    "duty_over_self",
    "over_functioning_hero",
    "inner_critic_override",
    "waiting_for_permission",
    "perfectionist_paralysis",
    "avoidant_autopilot",
    "control_grip",
    "boundary_blur",
    "people_pleasing_loop",
    "holding_the_line",
    "closed_door_syndrome",
    # Opening/positive patterns
    "grounded_presence",
    "renewal_after_distance",
}

# V9 COMPLETE: All 16 content patterns have PRACTICAL entries
PRACTICAL_MAP_KEYS = {
    # Relational patterns
    "relational_reopening",
    "heart_thaw",
    "safe_intimacy_returning",
    "relational_weight",
    "reconnection_window",
    # Emotional patterns
    "somethings_here",
    "emotional_wave_riding",
    "moving_through",
    "emotional_integration",
    # Threshold/identity patterns
    "threshold_standing",
    "expansion_resistance",
    "anticipating_impact",
    # Behavioral patterns
    "duty_over_self",
    "over_functioning_hero",
    "inner_critic_override",
    "waiting_for_permission",
    "perfectionist_paralysis",
    "emotional_flooding",
    "avoidant_autopilot",
    "control_grip",
    "boundary_blur",
    "people_pleasing_loop",
    "holding_the_line",
    "closed_door_syndrome",
    # Opening/positive patterns
    "grounded_presence",
    "renewal_after_distance",
}

# V9 COMPLETE: All 16 content patterns have NATURAL_TITLES
NATURAL_TITLES_KEYS = {
    # Relational patterns
    "Relational Reopening",
    "Heart Thaw",
    "Safe Intimacy Returning",
    "Relational Weight",
    "Reconnection Window",
    # Emotional patterns
    "Something's Here",
    "Emotional Wave Riding",
    "Moving Through",
    "Emotional Integration",
    # Threshold/identity patterns
    "Standing at Threshold",
    "Expansion Resistance",
    "Anticipating Impact",
    # Behavioral patterns
    "Duty Over Self",
    "Over-Functioning Hero",
    "Inner Critic Override",
    "Waiting for Permission",
    "Holding the Line",
    # Opening/positive patterns
    "Grounded Presence",
    "Renewal After Distance",
}

def validate_v9_coverage():
    """Check which patterns have full V9 language coverage."""
    
    print("=" * 70)
    print("V9 LANGUAGE SYSTEM VALIDATION")
    print("=" * 70)
    print()
    
    # Get actual pattern IDs from PATTERN_TEMPLATES
    actual_patterns = set(PATTERN_TEMPLATES.keys())
    
    # Filter to only content patterns (exclude lens descriptors like 'astrology', 'bazi', etc.)
    content_patterns = {
        p for p in actual_patterns 
        if p not in {'core', 'eq', 'sq', 'iq', 'attraction', 'purpose', 
                     'astrology', 'human_design', 'bazi', 'lifeline', 'pattern'}
    }
    
    print(f"Total content patterns in PATTERN_TEMPLATES: {len(content_patterns)}")
    print(f"Patterns: {sorted(content_patterns)}")
    print()
    
    # Track results
    results = {}
    missing_coverage = []
    full_coverage = []
    
    for pattern_id in sorted(content_patterns):
        template = PATTERN_TEMPLATES.get(pattern_id, {})
        title = template.get("title", pattern_id)
        
        # Check coverage in each V9 map
        has_why_now = pattern_id in PATTERN_WHY_NOW_KEYS
        has_friction = pattern_id in FRICTION_MAP_KEYS
        has_practical = pattern_id in PRACTICAL_MAP_KEYS
        has_natural_title = title in NATURAL_TITLES_KEYS
        
        # Count how many maps this pattern is in
        coverage_count = sum([has_why_now, has_friction, has_practical, has_natural_title])
        
        results[pattern_id] = {
            "title": title,
            "has_why_now": has_why_now,
            "has_friction": has_friction,
            "has_practical": has_practical,
            "has_natural_title": has_natural_title,
            "coverage_count": coverage_count,
            "coverage_pct": round(coverage_count / 4 * 100),
        }
        
        if coverage_count == 4:
            full_coverage.append(pattern_id)
        else:
            missing_coverage.append(pattern_id)
    
    # Print results
    print("-" * 70)
    print("COVERAGE BY PATTERN")
    print("-" * 70)
    
    for pattern_id, info in sorted(results.items(), key=lambda x: -x[1]["coverage_count"]):
        status = "✅" if info["coverage_count"] >= 3 else "⚠️" if info["coverage_count"] >= 2 else "❌"
        
        print(f"\n{status} {info['title']} ({pattern_id})")
        print(f"   Coverage: {info['coverage_pct']}% ({info['coverage_count']}/4)")
        
        # Show what's missing
        missing = []
        if not info["has_why_now"]:
            missing.append("PATTERN_WHY_NOW")
        if not info["has_friction"]:
            missing.append("friction_map")
        if not info["has_practical"]:
            missing.append("practical_map")
        if not info["has_natural_title"]:
            missing.append("NATURAL_TITLES")
        
        if missing:
            print(f"   Missing: {', '.join(missing)}")
    
    # Summary
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total patterns: {len(content_patterns)}")
    print(f"Full V9 coverage (4/4): {len(full_coverage)}")
    print(f"Partial coverage: {len(missing_coverage)}")
    print()
    
    if missing_coverage:
        print("PATTERNS NEEDING ATTENTION:")
        for pid in missing_coverage:
            info = results[pid]
            print(f"  - {info['title']} ({pid}): {info['coverage_pct']}% coverage")
    
    # Return success/failure
    # Consider it a pass if all patterns have at least 2 maps covered
    min_coverage = min(r["coverage_count"] for r in results.values())
    
    print()
    if min_coverage >= 2:
        print("✅ VALIDATION PASSED: All patterns have adequate V9 coverage (>=50%)")
        return True
    else:
        print("❌ VALIDATION FAILED: Some patterns have insufficient V9 coverage (<50%)")
        return False


def check_actual_implementation():
    """
    Actually check the implementation in pattern_mirror.py
    by looking at what's really in the code.
    """
    print()
    print("=" * 70)
    print("CHECKING ACTUAL IMPLEMENTATION")
    print("=" * 70)
    
    # Import and check the actual maps from pattern_mirror.py
    # Since the maps are defined inside functions, we need to check differently
    
    import re
    
    with open('/app/backend/services/pattern_mirror.py', 'r') as f:
        content = f.read()
    
    # Extract PATTERN_WHY_NOW keys - needs to handle nested dicts
    # Pattern: "pattern_name": { ... "high": ..., "medium": ..., "low": ... },
    why_now_start = content.find('PATTERN_WHY_NOW = {')
    if why_now_start != -1:
        # Find the matching closing brace
        brace_count = 0
        end_pos = why_now_start
        for i, char in enumerate(content[why_now_start:]):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_pos = why_now_start + i + 1
                    break
        
        why_now_content = content[why_now_start:end_pos]
        # Extract top-level keys (pattern_ids) - they're followed by ": {"
        actual_why_now_keys = set(re.findall(r'"([a-z_]+)":\s*\{', why_now_content))
        print(f"\nActual PATTERN_WHY_NOW keys ({len(actual_why_now_keys)}):")
        for k in sorted(actual_why_now_keys):
            print(f"  - {k}")
    else:
        actual_why_now_keys = set()
        print("\n⚠️ Could not find PATTERN_WHY_NOW")
    
    # Extract friction_map keys
    friction_match = re.search(r'friction_map = \{([^}]+)\}', content, re.DOTALL)
    if friction_match:
        friction_content = friction_match.group(1)
        actual_friction_keys = set(re.findall(r'"([a-z_]+)":', friction_content))
        print(f"\nActual friction_map keys ({len(actual_friction_keys)}):")
        for k in sorted(actual_friction_keys):
            print(f"  - {k}")
    else:
        actual_friction_keys = set()
        print("\n⚠️ Could not extract friction_map")
    
    # Extract practical_map keys - handle multi-line with categories
    practical_start = content.find('practical_map = {')
    if practical_start != -1:
        # Find closing brace
        brace_count = 0
        end_pos = practical_start
        for i, char in enumerate(content[practical_start:]):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_pos = practical_start + i + 1
                    break
        
        practical_content = content[practical_start:end_pos]
        actual_practical_keys = set(re.findall(r'"([a-z_]+)":', practical_content))
        print(f"\nActual practical_map keys ({len(actual_practical_keys)}):")
        for k in sorted(actual_practical_keys):
            print(f"  - {k}")
    else:
        actual_practical_keys = set()
        print("\n⚠️ Could not extract practical_map")
    
    # Get content patterns
    actual_patterns = set(PATTERN_TEMPLATES.keys())
    content_patterns = {
        p for p in actual_patterns 
        if p not in {'core', 'eq', 'sq', 'iq', 'attraction', 'purpose', 
                     'astrology', 'human_design', 'bazi', 'lifeline', 'pattern'}
    }
    
    # Check gaps
    print()
    print("-" * 70)
    print("GAP ANALYSIS")
    print("-" * 70)
    
    missing_why_now = content_patterns - actual_why_now_keys
    missing_friction = content_patterns - actual_friction_keys
    missing_practical = content_patterns - actual_practical_keys
    
    if missing_why_now:
        print(f"\n❌ Missing from PATTERN_WHY_NOW ({len(missing_why_now)}):")
        for p in sorted(missing_why_now):
            print(f"   - {p}")
    else:
        print("\n✅ PATTERN_WHY_NOW: All patterns covered")
    
    if missing_friction:
        print(f"\n❌ Missing from friction_map ({len(missing_friction)}):")
        for p in sorted(missing_friction):
            print(f"   - {p}")
    else:
        print("\n✅ friction_map: All patterns covered")
    
    if missing_practical:
        print(f"\n❌ Missing from practical_map ({len(missing_practical)}):")
        for p in sorted(missing_practical):
            print(f"   - {p}")
    else:
        print("\n✅ practical_map: All patterns covered")
    
    # Overall result
    total_gaps = len(missing_why_now) + len(missing_friction) + len(missing_practical)
    print()
    print("=" * 70)
    if total_gaps == 0:
        print("✅ ALL V9 LANGUAGE MAPS HAVE COMPLETE COVERAGE")
        return True
    else:
        print(f"❌ TOTAL GAPS: {total_gaps} entries needed")
        return False


if __name__ == "__main__":
    # Run validation
    validate_v9_coverage()
    
    # Check actual implementation
    success = check_actual_implementation()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
