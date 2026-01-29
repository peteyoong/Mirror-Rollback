#!/usr/bin/env python3
"""
Backend API Testing for Project Mirror - Lens Chat APIs
Focus: Testing the new Lens Chat functionality
"""

import requests
import json
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from frontend env
BACKEND_URL = os.getenv('EXPO_PUBLIC_BACKEND_URL', 'http://localhost:8001')
BASE_URL = f"{BACKEND_URL}/api"

print(f"Testing backend at: {BASE_URL}")

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def assert_test(self, condition, test_name, error_msg=""):
        if condition:
            print(f"✅ {test_name}")
            self.passed += 1
        else:
            print(f"❌ {test_name}: {error_msg}")
            self.failed += 1
            self.errors.append(f"{test_name}: {error_msg}")
    
    def print_summary(self):
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY: {self.passed} passed, {self.failed} failed")
        if self.errors:
            print(f"\nFAILED TESTS:")
            for error in self.errors:
                print(f"  - {error}")
        print(f"{'='*60}")

def test_lens_chat_apis():
    """Test the new Lens Chat APIs"""
    results = TestResults()
    
    # Test data
    test_email = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
    test_password = "testpassword123"
    test_name = "Test User"
    
    # Valid lens IDs from the backend code
    valid_lens_ids = [
        "true-sidereal-astrology",
        "human-design", 
        "numerology",
        "levels-of-consciousness"
    ]
    
    jwt_token = None
    
    try:
        # 1. Register a new test user
        print("\n1. Testing User Registration...")
        register_data = {
            "email": test_email,
            "password": test_password,
            "name": test_name
        }
        
        response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
        results.assert_test(
            response.status_code == 200,
            "User registration",
            f"Status: {response.status_code}, Response: {response.text}"
        )
        
        if response.status_code == 200:
            register_result = response.json()
            jwt_token = register_result.get("token")
            results.assert_test(
                jwt_token is not None,
                "JWT token received",
                "No token in registration response"
            )
        
        if not jwt_token:
            print("❌ Cannot continue without JWT token")
            return results
        
        headers = {"Authorization": f"Bearer {jwt_token}"}
        
        # 2. Complete onboarding (so chatbot has context)
        print("\n2. Testing Onboarding Completion...")
        onboarding_data = {
            "relationship_with_self": "I'm learning to be more compassionate with myself and understand my patterns better.",
            "reflection_style": "I prefer deep contemplation and looking for patterns in my experiences.",
            "desired_depth": "deep",
            "uncertainty_relationship": "I'm learning to be more comfortable with not knowing and see it as space for growth.",
            "intention": "I want to develop greater self-awareness and find clarity in my life direction."
        }
        
        response = requests.post(f"{BASE_URL}/onboarding/complete", json=onboarding_data, headers=headers)
        results.assert_test(
            response.status_code == 200,
            "Onboarding completion",
            f"Status: {response.status_code}, Response: {response.text}"
        )
        
        # 3. Test Lens Chat APIs for each valid lens
        for lens_id in valid_lens_ids:
            print(f"\n3. Testing Lens Chat APIs for '{lens_id}'...")
            
            # 3a. GET chat history (should be empty initially)
            print(f"  3a. Getting initial chat history for {lens_id}...")
            response = requests.get(f"{BASE_URL}/lenses/{lens_id}/chat", headers=headers)
            results.assert_test(
                response.status_code == 200,
                f"GET chat history for {lens_id}",
                f"Status: {response.status_code}, Response: {response.text}"
            )
            
            if response.status_code == 200:
                chat_history = response.json()
                results.assert_test(
                    isinstance(chat_history, list),
                    f"Chat history is list for {lens_id}",
                    f"Expected list, got: {type(chat_history)}"
                )
                results.assert_test(
                    len(chat_history) == 0,
                    f"Initial chat history empty for {lens_id}",
                    f"Expected empty list, got {len(chat_history)} messages"
                )
            
            # 3b. POST a message and verify AI response
            print(f"  3b. Sending message to {lens_id}...")
            test_messages = {
                "true-sidereal-astrology": "What is True Sidereal Astrology and how is it different from regular astrology?",
                "human-design": "What is Human Design and how can it help with self-understanding?",
                "numerology": "How does numerology work and what can it tell me about myself?",
                "levels-of-consciousness": "What are levels of consciousness and how do they relate to personal growth?"
            }
            
            message_data = {"message": test_messages[lens_id]}
            response = requests.post(f"{BASE_URL}/lenses/{lens_id}/chat", json=message_data, headers=headers)
            results.assert_test(
                response.status_code == 200,
                f"POST message to {lens_id}",
                f"Status: {response.status_code}, Response: {response.text}"
            )
            
            if response.status_code == 200:
                chat_response = response.json()
                results.assert_test(
                    isinstance(chat_response, list),
                    f"Chat response is list for {lens_id}",
                    f"Expected list, got: {type(chat_response)}"
                )
                
                if isinstance(chat_response, list):
                    results.assert_test(
                        len(chat_response) == 2,
                        f"Chat response has 2 messages for {lens_id}",
                        f"Expected 2 messages (user + assistant), got {len(chat_response)}"
                    )
                    
                    if len(chat_response) >= 2:
                        user_msg = chat_response[0]
                        assistant_msg = chat_response[1]
                        
                        # Verify user message structure
                        required_fields = ["id", "lens_key", "role", "message_text", "created_at"]
                        for field in required_fields:
                            results.assert_test(
                                field in user_msg,
                                f"User message has {field} for {lens_id}",
                                f"Missing field: {field}"
                            )
                        
                        results.assert_test(
                            user_msg.get("role") == "user",
                            f"User message role correct for {lens_id}",
                            f"Expected 'user', got: {user_msg.get('role')}"
                        )
                        
                        results.assert_test(
                            user_msg.get("message_text") == test_messages[lens_id],
                            f"User message text correct for {lens_id}",
                            f"Message text mismatch"
                        )
                        
                        # Verify assistant message structure
                        for field in required_fields:
                            results.assert_test(
                                field in assistant_msg,
                                f"Assistant message has {field} for {lens_id}",
                                f"Missing field: {field}"
                            )
                        
                        results.assert_test(
                            assistant_msg.get("role") == "assistant",
                            f"Assistant message role correct for {lens_id}",
                            f"Expected 'assistant', got: {assistant_msg.get('role')}"
                        )
                        
                        # Verify AI response is substantive (not just error message)
                        assistant_text = assistant_msg.get("message_text", "")
                        results.assert_test(
                            len(assistant_text) > 50,
                            f"Assistant response is substantive for {lens_id}",
                            f"Response too short ({len(assistant_text)} chars): {assistant_text[:100]}..."
                        )
                        
                        # Check that response doesn't contain error indicators
                        error_indicators = ["unable to respond", "try again later", "error", "failed"]
                        has_error = any(indicator in assistant_text.lower() for indicator in error_indicators)
                        results.assert_test(
                            not has_error,
                            f"Assistant response not an error for {lens_id}",
                            f"Response contains error indicators: {assistant_text[:200]}..."
                        )
            
            # 3c. GET chat history again (should show messages now)
            print(f"  3c. Getting updated chat history for {lens_id}...")
            response = requests.get(f"{BASE_URL}/lenses/{lens_id}/chat", headers=headers)
            results.assert_test(
                response.status_code == 200,
                f"GET updated chat history for {lens_id}",
                f"Status: {response.status_code}, Response: {response.text}"
            )
            
            if response.status_code == 200:
                updated_history = response.json()
                results.assert_test(
                    len(updated_history) == 2,
                    f"Updated chat history has 2 messages for {lens_id}",
                    f"Expected 2 messages, got {len(updated_history)}"
                )
            
            # 3d. DELETE chat history and verify it's cleared
            print(f"  3d. Clearing chat history for {lens_id}...")
            response = requests.delete(f"{BASE_URL}/lenses/{lens_id}/chat", headers=headers)
            results.assert_test(
                response.status_code == 200,
                f"DELETE chat history for {lens_id}",
                f"Status: {response.status_code}, Response: {response.text}"
            )
            
            # 3e. Verify chat history is now empty
            print(f"  3e. Verifying chat history cleared for {lens_id}...")
            response = requests.get(f"{BASE_URL}/lenses/{lens_id}/chat", headers=headers)
            if response.status_code == 200:
                cleared_history = response.json()
                results.assert_test(
                    len(cleared_history) == 0,
                    f"Chat history cleared for {lens_id}",
                    f"Expected empty list, got {len(cleared_history)} messages"
                )
        
        # 4. Test invalid lens ID returns 404
        print("\n4. Testing invalid lens ID...")
        invalid_lens_id = "invalid-lens-id"
        response = requests.get(f"{BASE_URL}/lenses/{invalid_lens_id}/chat", headers=headers)
        results.assert_test(
            response.status_code == 404,
            "Invalid lens ID returns 404",
            f"Expected 404, got: {response.status_code}"
        )
        
        # Test POST with invalid lens ID
        message_data = {"message": "Test message"}
        response = requests.post(f"{BASE_URL}/lenses/{invalid_lens_id}/chat", json=message_data, headers=headers)
        results.assert_test(
            response.status_code == 404,
            "POST to invalid lens ID returns 404",
            f"Expected 404, got: {response.status_code}"
        )
        
        # Test DELETE with invalid lens ID
        response = requests.delete(f"{BASE_URL}/lenses/{invalid_lens_id}/chat", headers=headers)
        results.assert_test(
            response.status_code == 404,
            "DELETE invalid lens ID returns 404",
            f"Expected 404, got: {response.status_code}"
        )
        
        # 5. Test authentication required
        print("\n5. Testing authentication requirements...")
        no_auth_headers = {}
        
        response = requests.get(f"{BASE_URL}/lenses/human-design/chat", headers=no_auth_headers)
        results.assert_test(
            response.status_code == 403,
            "GET chat requires authentication",
            f"Expected 403, got: {response.status_code}"
        )
        
        message_data = {"message": "Test"}
        response = requests.post(f"{BASE_URL}/lenses/human-design/chat", json=message_data, headers=no_auth_headers)
        results.assert_test(
            response.status_code == 403,
            "POST chat requires authentication", 
            f"Expected 403, got: {response.status_code}"
        )
        
        response = requests.delete(f"{BASE_URL}/lenses/human-design/chat", headers=no_auth_headers)
        results.assert_test(
            response.status_code == 403,
            "DELETE chat requires authentication",
            f"Expected 403, got: {response.status_code}"
        )
        
    except Exception as e:
        print(f"❌ Test execution error: {str(e)}")
        results.errors.append(f"Test execution error: {str(e)}")
        results.failed += 1
    
    return results

if __name__ == "__main__":
    print("🧪 Starting Lens Chat API Tests...")
    print(f"Backend URL: {BASE_URL}")
    
    results = test_lens_chat_apis()
    results.print_summary()
    
    if results.failed > 0:
        exit(1)
    else:
        print("\n🎉 All tests passed!")
        exit(0)