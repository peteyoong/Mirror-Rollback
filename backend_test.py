#!/usr/bin/env python3

import requests
import json
import sys
from datetime import datetime

# Backend URL from frontend/.env
BACKEND_URL = "https://experience-controls.preview.emergentagent.com/api"

def test_pattern_signals_endpoint():
    """
    Test the updated Pattern Signals endpoint for evidence-driven, pattern-linked content
    
    Requirements to verify:
    1. ASTROLOGY signals should be pattern-linked, not generic
    2. HUMAN DESIGN signals should link to user's type/authority and current pattern
    3. PATTERN HISTORY signals should include behavioral examples
    4. SYNTHESIS should feel like a conclusion, not summary
    """
    
    print("🧪 TESTING UPDATED PATTERN SIGNALS ENDPOINT")
    print("=" * 60)
    
    # Test user ID from review request
    user_id = "697f0c6abf35c0528ff06954"
    endpoint = f"{BACKEND_URL}/pattern-signals/{user_id}"
    
    print(f"📍 Testing endpoint: GET {endpoint}")
    print(f"🕐 Test time: {datetime.now().isoformat()}")
    print()
    
    try:
        # Make the API request
        response = requests.get(endpoint, timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"⏱️  Response Time: {response.elapsed.total_seconds():.2f} seconds")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200 OK, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
        # Parse JSON response
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            print(f"❌ FAILED: Invalid JSON response - {e}")
            return False
            
        print(f"📄 Response size: {len(response.text)} characters")
        print()
        
        # Verify response structure
        required_fields = ['summary', 'signals', 'synthesis', 'confidence']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            print(f"❌ FAILED: Missing required fields: {missing_fields}")
            return False
            
        print("✅ Response structure validation PASSED")
        print()
        
        # Test 1: ASTROLOGY signals validation
        print("🔍 TEST 1: ASTROLOGY SIGNALS VALIDATION")
        print("-" * 40)
        
        astrology_signals = data.get('signals', {}).get('astrology', [])
        print(f"Found {len(astrology_signals)} astrology signals")
        
        astrology_passed = True
        for i, signal in enumerate(astrology_signals):
            print(f"\nSignal {i+1}:")
            print(f"  Label: {signal.get('label', 'N/A')}")
            print(f"  Meaning: {signal.get('meaning', 'N/A')[:100]}...")
            
            meaning = signal.get('meaning', '').lower()
            
            # Check for generic language (should NOT contain)
            generic_phrases = [
                "subtle planetary movements are stirring patterns beneath the surface",
                "planetary movements are stirring",
                "stirring patterns beneath"
            ]
            
            has_generic = any(phrase in meaning for phrase in generic_phrases)
            if has_generic:
                print(f"  ❌ Contains generic language")
                astrology_passed = False
            else:
                print(f"  ✅ No generic language detected")
                
            # Check for pattern-linked language (should contain)
            pattern_keywords = ["pause", "stall", "pattern", "timing relates", "how this"]
            has_pattern_link = any(keyword in meaning for keyword in pattern_keywords)
            
            if has_pattern_link:
                print(f"  ✅ Contains pattern-linked language")
            else:
                print(f"  ❌ Missing pattern-linked language")
                astrology_passed = False
        
        print(f"\n🎯 ASTROLOGY SIGNALS: {'✅ PASSED' if astrology_passed else '❌ FAILED'}")
        print()
        
        # Test 2: HUMAN DESIGN signals validation
        print("🔍 TEST 2: HUMAN DESIGN SIGNALS VALIDATION")
        print("-" * 40)
        
        human_design_signals = data.get('signals', {}).get('human_design', [])
        print(f"Found {len(human_design_signals)} human design signals")
        
        human_design_passed = True
        for i, signal in enumerate(human_design_signals):
            print(f"\nSignal {i+1}:")
            print(f"  Label: {signal.get('label', 'N/A')}")
            print(f"  Meaning: {signal.get('meaning', 'N/A')[:100]}...")
            
            meaning = signal.get('meaning', '').lower()
            label = signal.get('label', '').lower()
            
            # Check for type/authority linkage (in both meaning and label)
            type_authority_keywords = ["type", "authority", "design", "manifestor", "generator", "projector", "reflector", "emotional", "sacral", "splenic"]
            has_type_authority = any(keyword in meaning for keyword in type_authority_keywords) or any(keyword in label for keyword in type_authority_keywords)
            
            if has_type_authority:
                print(f"  ✅ Links to user's type/authority")
            else:
                print(f"  ❌ Missing type/authority linkage")
                human_design_passed = False
                
            # Check for pattern connection
            pattern_connection = ["stall", "pause", "pattern", "current", "relates to"]
            has_pattern_connection = any(keyword in meaning for keyword in pattern_connection)
            
            if has_pattern_connection:
                print(f"  ✅ Explains how design relates to current pattern")
            else:
                print(f"  ❌ Missing pattern connection")
                human_design_passed = False
        
        print(f"\n🎯 HUMAN DESIGN SIGNALS: {'✅ PASSED' if human_design_passed else '❌ FAILED'}")
        print()
        
        # Test 3: PATTERN HISTORY signals validation
        print("🔍 TEST 3: PATTERN HISTORY SIGNALS VALIDATION")
        print("-" * 40)
        
        pattern_history_signals = data.get('signals', {}).get('pattern_history', [])
        print(f"Found {len(pattern_history_signals)} pattern history signals")
        
        pattern_history_passed = True
        for i, signal in enumerate(pattern_history_signals):
            print(f"\nSignal {i+1}:")
            print(f"  Label: {signal.get('label', 'N/A')}")
            print(f"  Meaning: {signal.get('meaning', 'N/A')[:100]}...")
            
            meaning = signal.get('meaning', '').lower()
            label = signal.get('label', '').lower()
            
            # Check for generic "appeared X times" language (should NOT contain)
            generic_history = ["appeared", "times recently"] 
            has_generic_history = all(phrase in label for phrase in generic_history)
            
            if has_generic_history:
                print(f"  ❌ Contains generic 'appeared X times' language")
                pattern_history_passed = False
            else:
                print(f"  ✅ No generic frequency language")
                
            # Check for behavioral examples or pattern-shaped descriptions
            behavioral_keywords = ["behavior", "example", "pattern", "repetition", "context", "you", "this time"]
            has_behavioral = any(keyword in meaning for keyword in behavioral_keywords)
            
            if has_behavioral:
                print(f"  ✅ Contains behavioral examples or pattern descriptions")
            else:
                print(f"  ❌ Missing behavioral examples")
                pattern_history_passed = False
        
        print(f"\n🎯 PATTERN HISTORY SIGNALS: {'✅ PASSED' if pattern_history_passed else '❌ FAILED'}")
        print()
        
        # Test 4: SYNTHESIS validation
        print("🔍 TEST 4: SYNTHESIS VALIDATION")
        print("-" * 40)
        
        synthesis = data.get('synthesis', '')
        print(f"Synthesis: {synthesis[:200]}...")
        
        synthesis_passed = True
        synthesis_lower = synthesis.lower()
        
        # Check for generic "signals are converging" language (should NOT contain)
        generic_synthesis = ["signals are converging", "converging", "pointing to"]
        has_generic_synthesis = any(phrase in synthesis_lower for phrase in generic_synthesis)
        
        if has_generic_synthesis:
            print(f"  ❌ Contains generic 'signals converging' language")
            synthesis_passed = False
        else:
            print(f"  ✅ No generic convergence language")
            
        # Check for conclusion-like language
        conclusion_keywords = ["therefore", "this means", "conclusion", "result", "because", "so", "thus"]
        has_conclusion = any(keyword in synthesis_lower for keyword in conclusion_keywords)
        
        if has_conclusion:
            print(f"  ✅ Feels like a conclusion")
        else:
            print(f"  ❌ Doesn't feel like a conclusion")
            synthesis_passed = False
            
        # Check for multi-source linking
        source_linking = ["astrology", "human design", "pattern", "history", "together", "combined"]
        has_source_linking = sum(1 for keyword in source_linking if keyword in synthesis_lower) >= 2
        
        if has_source_linking:
            print(f"  ✅ Links multiple sources")
        else:
            print(f"  ❌ Missing multi-source linking")
            synthesis_passed = False
        
        print(f"\n🎯 SYNTHESIS: {'✅ PASSED' if synthesis_passed else '❌ FAILED'}")
        print()
        
        # Overall results
        all_tests_passed = astrology_passed and human_design_passed and pattern_history_passed and synthesis_passed
        
        print("=" * 60)
        print("📊 FINAL TEST RESULTS:")
        print(f"  Astrology Signals: {'✅ PASSED' if astrology_passed else '❌ FAILED'}")
        print(f"  Human Design Signals: {'✅ PASSED' if human_design_passed else '❌ FAILED'}")
        print(f"  Pattern History Signals: {'✅ PASSED' if pattern_history_passed else '❌ FAILED'}")
        print(f"  Synthesis: {'✅ PASSED' if synthesis_passed else '❌ FAILED'}")
        print()
        print(f"🎉 OVERALL RESULT: {'✅ ALL TESTS PASSED' if all_tests_passed else '❌ SOME TESTS FAILED'}")
        
        # Print full response for debugging
        print("\n" + "=" * 60)
        print("📄 FULL RESPONSE FOR DEBUGGING:")
        print(json.dumps(data, indent=2))
        
        return all_tests_passed
        
    except requests.exceptions.RequestException as e:
        print(f"❌ FAILED: Request error - {e}")
        return False
    except Exception as e:
        print(f"❌ FAILED: Unexpected error - {e}")
        return False

if __name__ == "__main__":
    success = test_pattern_signals_endpoint()
    sys.exit(0 if success else 1)