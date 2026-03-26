#!/usr/bin/env python3

import requests
import json
import sys
from datetime import datetime

# Backend URL configuration
BACKEND_URL = "https://experience-controls.preview.emergentagent.com/api"

def test_pattern_diagnosis_unified_timing():
    """
    Test the unified timing intelligence in the pattern diagnosis endpoint.
    
    Requirements:
    1. evidence.timing.summary should reference actual transits
    2. evidence.timing.implication should be pattern-specific
    3. Check for BaZi evidence if present
    4. Verify real astrology, not generic summaries
    """
    
    print("🧪 TESTING: Pattern Diagnosis Unified Timing Intelligence")
    print("=" * 70)
    
    # Test endpoint
    user_id = "697f0c6abf35c0528ff06954"
    endpoint = f"{BACKEND_URL}/pattern-diagnosis/{user_id}?force_refresh=true"
    
    print(f"📍 Endpoint: GET {endpoint}")
    print(f"🕐 Test Time: {datetime.now().isoformat()}")
    print()
    
    try:
        # Make the API request
        print("🔄 Making API request...")
        response = requests.get(endpoint, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"⏱️  Response Time: {response.elapsed.total_seconds():.2f} seconds")
        
        if response.status_code != 200:
            print(f"❌ ERROR: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
        # Parse JSON response
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            print(f"❌ ERROR: Invalid JSON response: {e}")
            return False
            
        print("✅ Valid JSON response received")
        print()
        
        # Test 1: Check evidence.timing.summary for actual transits
        print("🔍 TEST 1: evidence.timing.summary - Actual Transit References")
        print("-" * 50)
        
        if 'evidence' not in data:
            print("❌ ERROR: 'evidence' field missing from response")
            return False
            
        if 'timing' not in data['evidence']:
            print("❌ ERROR: 'evidence.timing' field missing from response")
            return False
            
        timing_evidence = data['evidence']['timing']
        
        if 'summary' not in timing_evidence:
            print("❌ ERROR: 'evidence.timing.summary' field missing")
            return False
            
        timing_summary = timing_evidence['summary']
        print(f"📝 Timing Summary: {timing_summary}")
        
        # Check for actual transit references
        transit_keywords = [
            'jupiter', 'saturn', 'uranus', 'neptune', 'pluto', 'mars', 'venus',
            'square', 'opposition', 'conjunction', 'trine', 'sextile',
            'transit', 'transits'
        ]
        
        found_transits = []
        for keyword in transit_keywords:
            if keyword.lower() in timing_summary.lower():
                found_transits.append(keyword)
                
        if found_transits:
            print(f"✅ Found transit keywords: {found_transits}")
        else:
            print("⚠️  No specific transit keywords found")
            
        # Check for "the sky is quiet" - should NOT be present when real transits exist
        if "sky is quiet" in timing_summary.lower():
            print("❌ ERROR: Found 'the sky is quiet' - should show real transits instead")
            return False
        else:
            print("✅ No 'sky is quiet' language found")
            
        # Check for transit intensity
        intensity_keywords = ['low', 'moderate', 'high', 'intensity']
        found_intensity = []
        for keyword in intensity_keywords:
            if keyword.lower() in timing_summary.lower():
                found_intensity.append(keyword)
                
        if found_intensity:
            print(f"✅ Found intensity indicators: {found_intensity}")
        else:
            print("⚠️  No intensity indicators found")
            
        # Check for transit types
        transit_types = ['expansion', 'constraint', 'disruption', 'transformation', 'threshold']
        found_types = []
        for transit_type in transit_types:
            if transit_type.lower() in timing_summary.lower():
                found_types.append(transit_type)
                
        if found_types:
            print(f"✅ Found transit types: {found_types}")
        else:
            print("⚠️  No specific transit types found")
            
        print()
        
        # Test 2: Check evidence.timing.implication for pattern-specific content
        print("🔍 TEST 2: evidence.timing.implication - Pattern-Specific Content")
        print("-" * 50)
        
        if 'implication' not in timing_evidence:
            print("❌ ERROR: 'evidence.timing.implication' field missing")
            return False
            
        timing_implication = timing_evidence['implication']
        print(f"📝 Timing Implication: {timing_implication}")
        
        # Check for pattern-specific references (should link to "The Pause")
        pattern_keywords = ['pause', 'threshold', 'decision', 'choice', 'moment']
        found_pattern_refs = []
        for keyword in pattern_keywords:
            if keyword.lower() in timing_implication.lower():
                found_pattern_refs.append(keyword)
                
        if found_pattern_refs:
            print(f"✅ Found pattern-specific references: {found_pattern_refs}")
        else:
            print("⚠️  No pattern-specific references found")
            
        # Check that it's NOT generic timing language
        generic_phrases = [
            'this is a good time', 'the stars suggest', 'planetary energy',
            'cosmic influence', 'universal timing'
        ]
        found_generic = []
        for phrase in generic_phrases:
            if phrase.lower() in timing_implication.lower():
                found_generic.append(phrase)
                
        if found_generic:
            print(f"⚠️  Found generic language: {found_generic}")
        else:
            print("✅ No generic timing language found")
            
        print()
        
        # Test 3: Check for BaZi evidence if present
        print("🔍 TEST 3: BaZi Evidence Check")
        print("-" * 50)
        
        if 'bazi' in data['evidence']:
            bazi_evidence = data['evidence']['bazi']
            print(f"✅ BaZi evidence found")
            print(f"📝 BaZi Evidence: {json.dumps(bazi_evidence, indent=2)}")
        else:
            print("ℹ️  No BaZi evidence present (optional)")
            
        print()
        
        # Test 4: Overall response quality - real astrology vs generic
        print("🔍 TEST 4: Overall Response Quality - Real Astrology")
        print("-" * 50)
        
        # Check for specific astrological elements
        astro_elements = [
            'moon', 'sun', 'mercury', 'venus', 'mars', 'jupiter', 'saturn',
            'uranus', 'neptune', 'pluto', 'ascendant', 'midheaven',
            'house', 'houses', 'sign', 'degree', 'aspect'
        ]
        
        full_response = json.dumps(data).lower()
        found_astro = []
        for element in astro_elements:
            if element in full_response:
                found_astro.append(element)
                
        if len(found_astro) >= 3:
            print(f"✅ Rich astrological content found: {found_astro[:10]}...")
        else:
            print(f"⚠️  Limited astrological content: {found_astro}")
            
        # Check response structure
        required_fields = ['pattern_title', 'constitution', 'evidence', 'full_diagnosis']
        missing_fields = []
        for field in required_fields:
            if field not in data:
                missing_fields.append(field)
                
        if missing_fields:
            print(f"❌ ERROR: Missing required fields: {missing_fields}")
            return False
        else:
            print("✅ All required response fields present")
            
        print()
        
        # Additional test: Check if real transit data is available
        print("🔍 ADDITIONAL TEST: Real Transit Data Availability")
        print("-" * 50)
        
        try:
            chart_response = requests.get(f"{BACKEND_URL}/astrology/chart/{user_id}", timeout=10)
            if chart_response.status_code == 200:
                chart_data = chart_response.json()
                transit_aspects = chart_data.get('transits', {}).get('transit_to_natal_aspects', [])
                print(f"✅ Chart API accessible: {len(transit_aspects)} transit aspects available")
                
                if transit_aspects:
                    sample_transit = transit_aspects[0]
                    print(f"📝 Sample transit: {sample_transit.get('transit_point')} {sample_transit.get('aspect_type')} {sample_transit.get('natal_point')} (strength: {sample_transit.get('strength_score', 0):.3f})")
                    
                    # Check for major transits
                    major_transits = []
                    for t in transit_aspects[:5]:  # Check top 5
                        if t.get('strength_score', 0) > 0.5:
                            major_transits.append(f"{t.get('transit_point')} {t.get('aspect_type')} {t.get('natal_point')}")
                    
                    if major_transits:
                        print(f"✅ Major transits found: {major_transits}")
                        print("❌ CRITICAL ISSUE: Real transit data exists but not showing in timing evidence!")
                        print("🔧 DIAGNOSIS: Pattern diagnosis endpoint not accessing chart API transit data")
                    else:
                        print("ℹ️  No major transits (strength > 0.5) currently active")
                else:
                    print("ℹ️  No transit aspects in chart data")
            else:
                print(f"⚠️  Chart API not accessible: {chart_response.status_code}")
        except Exception as e:
            print(f"⚠️  Could not check chart API: {e}")
        
        print()
        
        # Summary
        print("📊 TEST SUMMARY")
        print("=" * 70)
        print("✅ Pattern Diagnosis endpoint accessible")
        print("✅ Valid JSON response structure")
        print("✅ Timing evidence present with summary and implication")
        print("✅ No 'sky is quiet' generic language")
        
        if found_transits:
            print("✅ Actual transit references found")
        else:
            print("❌ No actual transit references found (BaZi data shown instead)")
            
        if found_intensity:
            print("✅ Transit intensity indicators present")
        else:
            print("❌ No transit intensity indicators found")
            
        if found_pattern_refs:
            print("✅ Pattern-specific implications present")
        else:
            print("❌ No pattern-specific references found")
            
        if len(found_astro) >= 3:
            print("✅ Rich astrological content confirmed")
        else:
            print("❌ Limited astrological content")
            
        print()
        
        # Determine overall success
        critical_issues = []
        if not found_transits:
            critical_issues.append("No actual transit references in timing evidence")
        if not found_intensity:
            critical_issues.append("No transit intensity indicators")
        if not found_pattern_refs:
            critical_issues.append("No pattern-specific implications")
            
        if critical_issues:
            print("❌ CRITICAL ISSUES FOUND:")
            for issue in critical_issues:
                print(f"   • {issue}")
            print()
            print("🔧 RECOMMENDATION: Fix transit data integration in pattern diagnosis endpoint")
            return False
        else:
            print("🎉 UNIFIED TIMING INTELLIGENCE TEST COMPLETED SUCCESSFULLY")
            return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR: Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_pattern_diagnosis_unified_timing()
    sys.exit(0 if success else 1)