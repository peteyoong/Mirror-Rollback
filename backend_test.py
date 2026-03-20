#!/usr/bin/env python3
"""Backend Test Script for Pattern Mirror V1 API Endpoints
==========================================================

Test the new Pattern Mirror V1 backend endpoints:
1. GET /api/patterns/{user_id}
2. POST /api/patterns/generate

Expected response structure and language rules validation.
"""

import asyncio
import httpx
import json
from datetime import datetime
from typing import Dict, Any, List

# Backend URL from frontend/.env
BASE_URL = "https://narrative-enneagram.preview.emergentagent.com/api"

class PatternMirrorTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_results = []
    
    async def close(self):
        await self.client.aclose()
    
    def log_test_result(self, test_name: str, success: bool, message: str, details: Dict = None):
        """Log test result for reporting"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self.test_results.append(result)
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {message}")
        if details:
            print(f"   Details: {json.dumps(details, indent=2)}")
    
    def validate_response_structure(self, data: Dict[str, Any]) -> tuple[bool, str]:
        """Validate the Pattern Mirror response structure"""
        try:
            # Check top-level required fields
            required_top_fields = ["pattern", "cached", "generated_at", "signal_strength"]
            for field in required_top_fields:
                if field not in data:
                    return False, f"Missing top-level field: {field}"
            
            # Validate pattern object
            pattern = data["pattern"]
            required_pattern_fields = ["title", "what_you_may_be", "challenge", "genius", "micro_shifts"]
            for field in required_pattern_fields:
                if field not in pattern:
                    return False, f"Missing pattern field: {field}"
            
            # Validate pattern field types
            if not isinstance(pattern["title"], str):
                return False, "pattern.title must be string"
            
            if not isinstance(pattern["what_you_may_be"], str):
                return False, "pattern.what_you_may_be must be string"
            
            if not isinstance(pattern["challenge"], list):
                return False, "pattern.challenge must be array"
            
            if not isinstance(pattern["genius"], dict):
                return False, "pattern.genius must be object"
            
            if not isinstance(pattern["micro_shifts"], list):
                return False, "pattern.micro_shifts must be array"
            
            # Validate genius object
            genius = pattern["genius"]
            if "description" not in genius:
                return False, "Missing pattern.genius.description"
            
            if not isinstance(genius["description"], str):
                return False, "pattern.genius.description must be string"
            
            # archetype is optional
            if "archetype" in genius and not isinstance(genius["archetype"], str):
                return False, "pattern.genius.archetype must be string if present"
            
            # Validate signal_strength
            valid_signal_strengths = ["weak", "moderate", "strong"]
            if data["signal_strength"] not in valid_signal_strengths:
                return False, f"signal_strength must be one of: {valid_signal_strengths}"
            
            # Validate cached is boolean
            if not isinstance(data["cached"], bool):
                return False, "cached must be boolean"
            
            # Validate generated_at is string (ISO timestamp)
            if not isinstance(data["generated_at"], str):
                return False, "generated_at must be string"
            
            return True, "Response structure valid"
            
        except Exception as e:
            return False, f"Structure validation error: {str(e)}"
    
    def validate_language_rules(self, data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate language rules according to review request"""
        issues = []
        pattern = data["pattern"]
        
        # Rule 1: what_you_may_be should start with "You may be..."
        what_you_may_be = pattern["what_you_may_be"]
        if not what_you_may_be.lower().startswith("you may be"):
            issues.append(f"what_you_may_be should start with 'You may be...' but starts with: '{what_you_may_be[:50]}...'")
        
        # Rule 2: No spiritual jargon (energy, vibration, alignment)
        forbidden_words = ["energy", "vibration", "alignment"]
        all_text = json.dumps(pattern).lower()
        
        for word in forbidden_words:
            if word in all_text:
                issues.append(f"Found forbidden spiritual jargon word: '{word}'")
        
        # Rule 3: Check for vague phrases
        vague_phrases = ["something is shifting", "you are being called", "energy is"]
        for phrase in vague_phrases:
            if phrase.lower() in all_text:
                issues.append(f"Found vague phrase: '{phrase}'")
        
        return len(issues) == 0, issues
    
    async def test_get_patterns_endpoint(self, user_id: str):
        """Test GET /api/patterns/{user_id} endpoint"""
        try:
            url = f"{BASE_URL}/patterns/{user_id}"
            response = await self.client.get(url)
            
            if response.status_code != 200:
                self.log_test_result(
                    "GET /api/patterns/{user_id}",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"url": url, "status": response.status_code}
                )
                return None
            
            data = response.json()
            
            # Validate structure
            structure_valid, structure_msg = self.validate_response_structure(data)
            if not structure_valid:
                self.log_test_result(
                    "GET /api/patterns/{user_id} - Structure",
                    False,
                    structure_msg,
                    {"response": data}
                )
                return None
            
            # Validate language rules
            language_valid, language_issues = self.validate_language_rules(data)
            if not language_valid:
                self.log_test_result(
                    "GET /api/patterns/{user_id} - Language Rules",
                    False,
                    f"Language rule violations: {'; '.join(language_issues)}",
                    {"violations": language_issues}
                )
            else:
                self.log_test_result(
                    "GET /api/patterns/{user_id} - Language Rules",
                    True,
                    "All language rules passed"
                )
            
            self.log_test_result(
                "GET /api/patterns/{user_id}",
                True,
                f"Response received with {data['signal_strength']} signal strength",
                {
                    "title": data["pattern"]["title"],
                    "what_you_may_be": data["pattern"]["what_you_may_be"][:100] + "..." if len(data["pattern"]["what_you_may_be"]) > 100 else data["pattern"]["what_you_may_be"],
                    "signal_strength": data["signal_strength"],
                    "cached": data["cached"]
                }
            )
            
            return data
            
        except Exception as e:
            self.log_test_result(
                "GET /api/patterns/{user_id}",
                False,
                f"Exception: {str(e)}",
                {"error": str(e)}
            )
            return None
    
    async def test_post_patterns_generate_endpoint(self, user_id: str):
        """Test POST /api/patterns/generate endpoint"""
        try:
            url = f"{BASE_URL}/patterns/generate"
            payload = {
                "user_id": user_id,
                "force_refresh": False
            }
            
            response = await self.client.post(url, json=payload)
            
            if response.status_code != 200:
                self.log_test_result(
                    "POST /api/patterns/generate",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"url": url, "payload": payload, "status": response.status_code}
                )
                return None
            
            data = response.json()
            
            # Validate structure
            structure_valid, structure_msg = self.validate_response_structure(data)
            if not structure_valid:
                self.log_test_result(
                    "POST /api/patterns/generate - Structure",
                    False,
                    structure_msg,
                    {"response": data}
                )
                return None
            
            # Validate language rules
            language_valid, language_issues = self.validate_language_rules(data)
            if not language_valid:
                self.log_test_result(
                    "POST /api/patterns/generate - Language Rules",
                    False,
                    f"Language rule violations: {'; '.join(language_issues)}",
                    {"violations": language_issues}
                )
            else:
                self.log_test_result(
                    "POST /api/patterns/generate - Language Rules",
                    True,
                    "All language rules passed"
                )
            
            self.log_test_result(
                "POST /api/patterns/generate",
                True,
                f"Response received with {data['signal_strength']} signal strength",
                {
                    "title": data["pattern"]["title"],
                    "what_you_may_be": data["pattern"]["what_you_may_be"][:100] + "..." if len(data["pattern"]["what_you_may_be"]) > 100 else data["pattern"]["what_you_may_be"],
                    "signal_strength": data["signal_strength"],
                    "cached": data["cached"]
                }
            )
            
            return data
            
        except Exception as e:
            self.log_test_result(
                "POST /api/patterns/generate",
                False,
                f"Exception: {str(e)}",
                {"error": str(e)}
            )
            return None
    
    async def test_response_consistency(self, get_data: Dict, post_data: Dict):
        """Test that GET and POST return consistent results"""
        try:
            # For cached results, they should be identical
            if get_data["cached"] and post_data["cached"]:
                if get_data["pattern"]["title"] == post_data["pattern"]["title"]:
                    self.log_test_result(
                        "GET/POST Response Consistency",
                        True,
                        "Cached responses are consistent"
                    )
                else:
                    self.log_test_result(
                        "GET/POST Response Consistency", 
                        False,
                        "Cached responses differ",
                        {
                            "get_title": get_data["pattern"]["title"],
                            "post_title": post_data["pattern"]["title"]
                        }
                    )
            else:
                self.log_test_result(
                    "GET/POST Response Consistency",
                    True,
                    "Both endpoints return valid patterns (may differ if not cached)"
                )
                
        except Exception as e:
            self.log_test_result(
                "GET/POST Response Consistency",
                False,
                f"Exception: {str(e)}"
            )
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("PATTERN MIRROR V1 API TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for r in self.test_results if r["success"])
        total = len(self.test_results)
        
        print(f"Tests Passed: {passed}/{total}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed < total:
            print("\nFAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"❌ {result['test']}: {result['message']}")
        
        print(f"\nAll tests completed at {datetime.now().isoformat()}")

async def main():
    """Main test execution"""
    print("PATTERN MIRROR V1 BACKEND API TESTING")
    print("="*50)
    print(f"Testing against: {BASE_URL}")
    print(f"Test User ID: test_user_123")
    print()
    
    tester = PatternMirrorTester()
    
    try:
        user_id = "test_user_123"
        
        # Test GET endpoint
        print("1. Testing GET /api/patterns/{user_id}...")
        get_data = await tester.test_get_patterns_endpoint(user_id)
        
        print("\n2. Testing POST /api/patterns/generate...")
        post_data = await tester.test_post_patterns_generate_endpoint(user_id)
        
        # Test consistency if both succeeded
        if get_data and post_data:
            print("\n3. Testing response consistency...")
            await tester.test_response_consistency(get_data, post_data)
        
        # Test force refresh to ensure non-cached works correctly
        print("\n4. Testing GET with force_refresh=true...")
        refresh_url = f"{BASE_URL}/patterns/{user_id}?force_refresh=true"
        try:
            response = await tester.client.get(refresh_url)
            if response.status_code == 200:
                refresh_data = response.json()
                structure_valid, structure_msg = tester.validate_response_structure(refresh_data)
                language_valid, language_issues = tester.validate_language_rules(refresh_data)
                
                if structure_valid and language_valid:
                    tester.log_test_result(
                        "GET /api/patterns/{user_id}?force_refresh=true",
                        True,
                        f"Force refresh successful, signal_strength: {refresh_data['signal_strength']}, cached: {refresh_data['cached']}"
                    )
                else:
                    tester.log_test_result(
                        "GET /api/patterns/{user_id}?force_refresh=true",
                        False,
                        f"Structure: {structure_msg}, Language issues: {language_issues}"
                    )
            else:
                tester.log_test_result(
                    "GET /api/patterns/{user_id}?force_refresh=true",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
        except Exception as e:
            tester.log_test_result(
                "GET /api/patterns/{user_id}?force_refresh=true",
                False,
                f"Exception: {str(e)}"
            )
        
        # Print summary
        tester.print_summary()
        
    finally:
        await tester.close()

if __name__ == "__main__":
    asyncio.run(main())