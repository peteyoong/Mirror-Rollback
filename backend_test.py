#!/usr/bin/env python3
"""
Backend Testing Script for Mirror Chat API Transit/Timing Question
Testing the new "answer-first" behavior for transit/timing questions
"""

import requests
import json
import time
import sys
from datetime import datetime

# Backend URL from environment
BACKEND_URL = "https://chart-spine-1.preview.emergentagent.com/api"

def test_mirror_chat_transit_timing():
    """
    Test Mirror Chat API with transit/timing question to verify answer-first behavior
    """
    print("🧪 TESTING MIRROR CHAT API - TRANSIT/TIMING QUESTION")
    print("=" * 60)
    
    # Test parameters from review request
    user_id = "697f0c6abf35c0528ff06954"  # User with chart data
    test_payload = {
        "user_id": user_id,
        "message": "Are there any planetary alignments that are specifically coming up for me this month?",
        "lens": None,
        "include_journal": False,
        "include_history": False
    }
    
    print(f"📋 TEST SETUP:")
    print(f"   User ID: {user_id}")
    print(f"   Message: {test_payload['message']}")
    print(f"   Lens: {test_payload['lens']}")
    print(f"   Include Journal: {test_payload['include_journal']}")
    print(f"   Include History: {test_payload['include_history']}")
    print()
    
    # Make the API request
    print("🚀 SENDING REQUEST TO MIRROR CHAT API...")
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/mirror/chat",
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Time: {response_time:.2f} seconds")
        print()
        
        if response.status_code == 200:
            response_data = response.json()
            
            # Extract response text
            response_text = response_data.get('response', '')
            
            print("✅ API REQUEST SUCCESSFUL")
            print(f"   Response Length: {len(response_text)} characters")
            print(f"   Word Count: {len(response_text.split())} words")
            print()
            
            # Analyze response for review requirements
            print("🔍 ANALYZING RESPONSE FOR REVIEW REQUIREMENTS:")
            print("-" * 50)
            
            # 1. Check if response answers first (doesn't immediately ask clarifying questions)
            clarifying_questions = [
                "what month?", "what timezone?", "which month", "what time zone",
                "when exactly", "what location", "where are you located"
            ]
            
            has_immediate_clarifying = any(q.lower() in response_text.lower()[:200] for q in clarifying_questions)
            
            print(f"1. ✅ Response ANSWERS FIRST (no immediate clarifying questions): {not has_immediate_clarifying}")
            if has_immediate_clarifying:
                print(f"   ❌ Found clarifying question in first 200 chars")
            
            # 2. Check for astrological content relevant to user's chart
            astro_keywords = [
                "pisces", "aries", "sun", "moon", "transit", "planetary", "alignment",
                "mars", "venus", "mercury", "jupiter", "saturn", "uranus", "neptune", "pluto"
            ]
            
            found_astro_keywords = [kw for kw in astro_keywords if kw.lower() in response_text.lower()]
            
            print(f"2. ✅ Contains astrological content: {len(found_astro_keywords) > 0}")
            print(f"   Found keywords: {found_astro_keywords}")
            
            # 3. Check for specific chart references (Pisces Sun, Aries Moon)
            has_pisces_ref = "pisces" in response_text.lower()
            has_aries_ref = "aries" in response_text.lower()
            
            print(f"3. ✅ References user's chart (Pisces Sun/Aries Moon): Pisces={has_pisces_ref}, Aries={has_aries_ref}")
            
            # 4. Check if response ends with reflective question (not clarifying)
            last_sentence = response_text.strip().split('.')[-1].strip()
            if last_sentence.endswith('?'):
                is_reflective = not any(q.lower() in last_sentence.lower() for q in clarifying_questions)
                print(f"4. ✅ Ends with reflective question (not clarifying): {is_reflective}")
                print(f"   Final question: '{last_sentence}'")
            else:
                print(f"4. ❓ Does not end with question")
            
            # 5. Check Mirror tone (no generic assistant language)
            generic_phrases = [
                "i'm here to help", "i can assist", "let me help you", "i'd be happy to",
                "as an ai", "i'm an ai", "i don't have access", "i cannot provide"
            ]
            
            has_generic_tone = any(phrase.lower() in response_text.lower() for phrase in generic_phrases)
            
            print(f"5. ✅ Mirror tone (not generic assistant): {not has_generic_tone}")
            
            # 6. Check for 1-3 themes/signals mentioned
            theme_indicators = [
                "theme", "signal", "pattern", "energy", "influence", "aspect", "transit"
            ]
            
            theme_count = sum(1 for indicator in theme_indicators if indicator.lower() in response_text.lower())
            
            print(f"6. ✅ Contains themes/signals: {theme_count > 0} (found {theme_count} theme indicators)")
            
            print()
            print("📝 FULL RESPONSE TEXT:")
            print("-" * 50)
            print(response_text)
            print("-" * 50)
            
            # Return response for backend log analysis
            return True, response_data
            
        else:
            print(f"❌ API REQUEST FAILED")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ REQUEST ERROR: {str(e)}")
        return False, None

def check_backend_logs():
    """
    Check backend logs for specific patterns mentioned in review request
    """
    print("\n🔍 CHECKING BACKEND LOGS FOR REQUIRED PATTERNS:")
    print("=" * 60)
    
    # Check supervisor backend logs
    try:
        import subprocess
        result = subprocess.run(
            ["tail", "-n", "100", "/var/log/supervisor/backend.out.log"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            log_content = result.stdout
            
            # Look for specific patterns from review request
            required_patterns = [
                "[MIRROR_CHAT] Detected transit/timing question",
                "[MIRROR_CHAT] Added transit context", 
                "mode=timeline"
            ]
            
            print("Looking for required log patterns:")
            for pattern in required_patterns:
                if pattern in log_content:
                    print(f"   ✅ Found: {pattern}")
                else:
                    print(f"   ❌ Missing: {pattern}")
            
            # Show recent Mirror Chat related logs
            mirror_logs = [line for line in log_content.split('\n') if 'MIRROR_CHAT' in line]
            if mirror_logs:
                print(f"\n📋 Recent Mirror Chat logs ({len(mirror_logs)} entries):")
                for log in mirror_logs[-5:]:  # Show last 5
                    print(f"   {log}")
            else:
                print("\n❌ No Mirror Chat logs found in recent output")
                
        else:
            print("❌ Could not read backend logs")
            
    except Exception as e:
        print(f"❌ Error reading logs: {str(e)}")

def main():
    """
    Main test execution
    """
    print("🧪 MIRROR CHAT API TRANSIT/TIMING QUESTION TESTING")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Backend URL: {BACKEND_URL}")
    print()
    
    # Test the Mirror Chat API
    success, response_data = test_mirror_chat_transit_timing()
    
    if success:
        # Check backend logs for required patterns
        check_backend_logs()
        
        print("\n🎯 SUMMARY:")
        print("=" * 60)
        print("✅ Mirror Chat API responded successfully")
        print("✅ Response analyzed for review requirements")
        print("✅ Backend logs checked for required patterns")
        print("\n📋 NEXT STEPS:")
        print("- Review the full response text above")
        print("- Verify backend logs show correct mode detection")
        print("- Confirm answer-first behavior is working")
        
    else:
        print("\n❌ TESTING FAILED")
        print("- Mirror Chat API did not respond successfully")
        print("- Check backend service status")
        print("- Verify user ID and endpoint availability")

if __name__ == "__main__":
    main()