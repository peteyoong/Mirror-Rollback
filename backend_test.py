#!/usr/bin/env python3

import requests
import json
import sys
from datetime import datetime

# Backend URL configuration
BACKEND_URL = "https://experience-controls.preview.emergentagent.com/api"

def test_upgraded_astrology_evidence():
    """
    Test the upgraded astrology evidence in the pattern diagnosis endpoint.
    
    Review Request Requirements:
    1. Evidence.timing.summary should include:
       - Specific transit type (forcing, pause_review, threshold, overreach_risk, opening, closure, ripening, neutral)
       - Moon context (sign, phase)
       - NOT generic language like "the sky is quiet"
    
    2. Evidence.timing.implication should:
       - Be pattern-specific (referencing "The Pause" or stall pattern)
       - Explain HOW the transit relates to the pattern
       - NOT be a generic timing description
    
    3. Look for evidence of real transit hierarchy:
       - Moon sign and phase mentioned
       - Transit type clearly stated
       - Pattern-specific interpretation
    """
    
    print("🧪 TESTING UPGRADED ASTROLOGY EVIDENCE IN PATTERN DIAGNOSIS ENDPOINT")
    print("=" * 80)
    
    # Test endpoint
    user_id = "697f0c6abf35c0528ff06954"
    endpoint = f"{BACKEND_URL}/pattern-diagnosis/{user_id}?force_refresh=true"
    
    print(f"📍 Testing endpoint: {endpoint}")
    print(f"🕐 Test time: {datetime.now().isoformat()}")
    print()
    
    try:
        # Make the API request
        print("📡 Making API request...")
        response = requests.get(endpoint, timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"⏱️  Response Time: {response.elapsed.total_seconds():.2f}s")
        
        if response.status_code != 200:
            print(f"❌ ERROR: Expected status 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        # Parse JSON response
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            print(f"❌ ERROR: Failed to parse JSON response: {e}")
            print(f"Raw response: {response.text[:500]}...")
            return False
        
        print("✅ Successfully received JSON response")
        print()
        
        # Test 1: Verify evidence structure exists
        print("🔍 TEST 1: EVIDENCE STRUCTURE VERIFICATION")
        print("-" * 50)
        
        if 'evidence' not in data:
            print("❌ ERROR: 'evidence' field missing from response")
            return False
        
        evidence = data['evidence']
        
        if 'timing' not in evidence:
            print("❌ ERROR: 'evidence.timing' field missing from response")
            return False
        
        timing_evidence = evidence['timing']
        
        if 'summary' not in timing_evidence:
            print("❌ ERROR: 'evidence.timing.summary' field missing from response")
            return False
        
        if 'implication' not in timing_evidence:
            print("❌ ERROR: 'evidence.timing.implication' field missing from response")
            return False
        
        print("✅ Evidence structure verified: evidence.timing.summary and evidence.timing.implication present")
        print()
        
        # Test 2: Analyze timing summary for upgraded content
        print("🔍 TEST 2: TIMING SUMMARY UPGRADE VERIFICATION")
        print("-" * 50)
        
        timing_summary = timing_evidence['summary']
        print(f"📝 Timing Summary: {timing_summary}")
        print()
        
        # Check for specific transit types
        transit_types = [
            'forcing', 'pause_review', 'threshold', 'overreach_risk', 
            'opening', 'closure', 'ripening', 'neutral'
        ]
        
        found_transit_type = None
        for transit_type in transit_types:
            if transit_type in timing_summary.lower():
                found_transit_type = transit_type
                break
        
        if found_transit_type:
            print(f"✅ Specific transit type found: '{found_transit_type}'")
        else:
            print("❌ ERROR: No specific transit type found in timing summary")
            print(f"Expected one of: {', '.join(transit_types)}")
        
        # Check for Moon context (sign, phase)
        moon_indicators = ['moon', 'lunar', 'new moon', 'full moon', 'waxing', 'waning']
        moon_signs = [
            'aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo',
            'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces'
        ]
        
        found_moon_context = False
        found_moon_sign = None
        
        timing_summary_lower = timing_summary.lower()
        
        for indicator in moon_indicators:
            if indicator in timing_summary_lower:
                found_moon_context = True
                break
        
        for sign in moon_signs:
            if sign in timing_summary_lower:
                found_moon_sign = sign
                break
        
        if found_moon_context:
            print(f"✅ Moon context found in timing summary")
            if found_moon_sign:
                print(f"✅ Moon sign mentioned: '{found_moon_sign}'")
        else:
            print("❌ ERROR: No Moon context found in timing summary")
        
        # Check for generic language (should NOT be present)
        generic_phrases = ['the sky is quiet', 'sky is quiet', 'quiet sky']
        found_generic = False
        
        for phrase in generic_phrases:
            if phrase in timing_summary.lower():
                found_generic = True
                print(f"❌ ERROR: Generic language found: '{phrase}'")
                break
        
        if not found_generic:
            print("✅ No generic language detected in timing summary")
        
        print()
        
        # Test 3: Analyze timing implication for pattern-specific content
        print("🔍 TEST 3: TIMING IMPLICATION PATTERN-SPECIFIC VERIFICATION")
        print("-" * 50)
        
        timing_implication = timing_evidence['implication']
        print(f"📝 Timing Implication: {timing_implication}")
        print()
        
        # Check for pattern-specific references
        pattern_references = ['the pause', 'stall pattern', 'pause pattern', 'stall', 'pause']
        found_pattern_ref = False
        
        timing_implication_lower = timing_implication.lower()
        
        for ref in pattern_references:
            if ref in timing_implication_lower:
                found_pattern_ref = True
                print(f"✅ Pattern-specific reference found: '{ref}'")
                break
        
        if not found_pattern_ref:
            print("❌ ERROR: No pattern-specific reference found in timing implication")
            print(f"Expected references to: {', '.join(pattern_references)}")
        
        # Check for HOW the transit relates to the pattern
        relationship_indicators = [
            'relates to', 'connects to', 'influences', 'affects', 'impacts',
            'supports', 'reinforces', 'amplifies', 'triggers', 'activates'
        ]
        
        found_relationship = False
        for indicator in relationship_indicators:
            if indicator in timing_implication_lower:
                found_relationship = True
                print(f"✅ Transit-pattern relationship explanation found: '{indicator}'")
                break
        
        if not found_relationship:
            print("⚠️  WARNING: No clear transit-pattern relationship explanation found")
        
        # Check that it's NOT a generic timing description
        generic_timing_phrases = [
            'timing is important', 'good time to', 'time for', 'timing suggests',
            'now is the time', 'timing indicates'
        ]
        
        found_generic_timing = False
        for phrase in generic_timing_phrases:
            if phrase in timing_implication_lower:
                found_generic_timing = True
                print(f"❌ ERROR: Generic timing language found: '{phrase}'")
                break
        
        if not found_generic_timing:
            print("✅ No generic timing language detected in implication")
        
        print()
        
        # Test 4: Overall transit hierarchy evidence
        print("🔍 TEST 4: REAL TRANSIT HIERARCHY EVIDENCE")
        print("-" * 50)
        
        hierarchy_score = 0
        
        if found_transit_type:
            hierarchy_score += 1
            print(f"✅ Transit type clearly stated: {found_transit_type}")
        
        if found_moon_context:
            hierarchy_score += 1
            print(f"✅ Moon context mentioned")
        
        if found_moon_sign:
            hierarchy_score += 1
            print(f"✅ Moon sign specified: {found_moon_sign}")
        
        if found_pattern_ref:
            hierarchy_score += 1
            print(f"✅ Pattern-specific interpretation present")
        
        print(f"📊 Transit Hierarchy Score: {hierarchy_score}/4")
        
        if hierarchy_score >= 3:
            print("✅ Strong evidence of real transit hierarchy")
        elif hierarchy_score >= 2:
            print("⚠️  Moderate evidence of transit hierarchy")
        else:
            print("❌ Weak evidence of transit hierarchy")
        
        print()
        
        # Test 5: Additional verification
        print("🔍 TEST 5: ADDITIONAL VERIFICATION")
        print("-" * 50)
        
        # Check response size and completeness
        response_size = len(json.dumps(data))
        print(f"📏 Response size: {response_size} characters")
        
        # Check for other evidence types
        other_evidence_types = ['design', 'history']
        for evidence_type in other_evidence_types:
            if evidence_type in evidence:
                print(f"✅ {evidence_type.title()} evidence present")
            else:
                print(f"⚠️  {evidence_type.title()} evidence missing")
        
        # Check for core diagnosis fields
        core_fields = ['what_is_happening', 'why_it_is_happening', 'what_kind_of_moment', 'what_would_be_wise']
        for field in core_fields:
            if field in data:
                print(f"✅ Core field present: {field}")
            else:
                print(f"❌ Core field missing: {field}")
        
        print()
        
        # Final assessment
        print("🎯 FINAL ASSESSMENT")
        print("=" * 50)
        
        all_tests_passed = True
        
        # Critical requirements check
        if not found_transit_type:
            print("❌ CRITICAL: No specific transit type found")
            all_tests_passed = False
        
        if not found_moon_context:
            print("❌ CRITICAL: No Moon context found")
            all_tests_passed = False
        
        if found_generic:
            print("❌ CRITICAL: Generic language still present")
            all_tests_passed = False
        
        if not found_pattern_ref:
            print("❌ CRITICAL: No pattern-specific reference in implication")
            all_tests_passed = False
        
        if all_tests_passed:
            print("🎉 ALL CRITICAL REQUIREMENTS MET")
            print("✅ Astrology evidence has been successfully upgraded")
            print("✅ Timing summary includes specific transit type and Moon context")
            print("✅ Timing implication is pattern-specific")
            print("✅ No generic language detected")
            print("✅ Real transit hierarchy evidence present")
        else:
            print("❌ SOME CRITICAL REQUIREMENTS NOT MET")
            print("⚠️  Astrology evidence upgrade may be incomplete")
        
        return all_tests_passed
        
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR: Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 STARTING UPGRADED ASTROLOGY EVIDENCE TESTING")
    print(f"🕐 Test started at: {datetime.now().isoformat()}")
    print()
    
    success = test_upgraded_astrology_evidence()
    
    print()
    print("📋 TEST SUMMARY")
    print("=" * 50)
    
    if success:
        print("✅ TESTING COMPLETED SUCCESSFULLY")
        print("🎯 All requirements verified")
        sys.exit(0)
    else:
        print("❌ TESTING FAILED")
        print("⚠️  Some requirements not met")
        sys.exit(1)