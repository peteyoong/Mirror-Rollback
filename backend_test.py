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

class ProjectMirrorTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.user_id = None
        self.test_results = []
        
    def log_result(self, test_name, success, message, response_data=None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        if response_data:
            result["response"] = response_data
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
    def test_auth_register(self):
        """Test user registration"""
        test_email = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
        test_data = {
            "email": test_email,
            "password": "securepassword123",
            "name": "Test User"
        }
        
        try:
            response = requests.post(f"{self.base_url}/auth/register", json=test_data)
            
            if response.status_code == 200:
                data = response.json()
                if "token" in data and "user" in data:
                    self.token = data["token"]
                    self.user_id = data["user"]["id"]
                    self.log_result("Auth Register", True, f"User registered successfully with ID: {self.user_id}")
                    return True
                else:
                    self.log_result("Auth Register", False, "Missing token or user in response", data)
                    return False
            else:
                self.log_result("Auth Register", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Auth Register", False, f"Exception: {str(e)}")
            return False
    
    def test_auth_login(self):
        """Test user login with existing credentials"""
        # First register a user for login test
        test_email = f"logintest_{uuid.uuid4().hex[:8]}@example.com"
        register_data = {
            "email": test_email,
            "password": "loginpassword123",
            "name": "Login Test User"
        }
        
        try:
            # Register user first
            reg_response = requests.post(f"{self.base_url}/auth/register", json=register_data)
            if reg_response.status_code != 200:
                self.log_result("Auth Login", False, "Failed to register user for login test")
                return False
            
            # Now test login
            login_data = {
                "email": test_email,
                "password": "loginpassword123"
            }
            
            response = requests.post(f"{self.base_url}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                if "token" in data and "user" in data:
                    # Update token for subsequent tests if this is our main test user
                    if not self.token:
                        self.token = data["token"]
                        self.user_id = data["user"]["id"]
                    self.log_result("Auth Login", True, "Login successful")
                    return True
                else:
                    self.log_result("Auth Login", False, "Missing token or user in response", data)
                    return False
            else:
                self.log_result("Auth Login", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Auth Login", False, f"Exception: {str(e)}")
            return False
    
    def test_auth_me(self):
        """Test get current user endpoint"""
        if not self.token:
            self.log_result("Auth Me", False, "No token available for authentication")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.base_url}/auth/me", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "id" in data and "email" in data and "name" in data:
                    self.log_result("Auth Me", True, f"User info retrieved: {data['email']}")
                    return True
                else:
                    self.log_result("Auth Me", False, "Missing required fields in user response", data)
                    return False
            else:
                self.log_result("Auth Me", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Auth Me", False, f"Exception: {str(e)}")
            return False
    
    def test_onboarding_complete(self):
        """Test onboarding completion"""
        if not self.token:
            self.log_result("Onboarding Complete", False, "No token available for authentication")
            return False
            
        onboarding_data = {
            "relationship_with_self": "I'm learning to be more compassionate with myself",
            "reflection_style": "I prefer quiet contemplation and writing",
            "desired_depth": "I want to go deep but at my own pace",
            "uncertainty_relationship": "I'm learning to be comfortable with not knowing",
            "intention": "I want to develop a stronger relationship with myself"
        }
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.post(f"{self.base_url}/onboarding/complete", json=onboarding_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log_result("Onboarding Complete", True, "Onboarding completed successfully")
                    return True
                else:
                    self.log_result("Onboarding Complete", False, "Success field not true in response", data)
                    return False
            else:
                self.log_result("Onboarding Complete", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Onboarding Complete", False, f"Exception: {str(e)}")
            return False
    
    def test_mirror_today(self):
        """Test daily mirror content"""
        if not self.token:
            self.log_result("Mirror Today", False, "No token available for authentication")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.base_url}/mirror/today", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["id", "insight", "reflection_question", "another_perspective", "closing_line", "date"]
                if all(field in data for field in required_fields):
                    self.log_result("Mirror Today", True, f"Mirror content retrieved for date: {data['date']}")
                    return True
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_result("Mirror Today", False, f"Missing required fields: {missing}", data)
                    return False
            else:
                self.log_result("Mirror Today", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Mirror Today", False, f"Exception: {str(e)}")
            return False
    
    def test_journal_crud(self):
        """Test full journal CRUD operations"""
        if not self.token:
            self.log_result("Journal CRUD", False, "No token available for authentication")
            return False
            
        headers = {"Authorization": f"Bearer {self.token}"}
        entry_id = None
        
        try:
            # Test CREATE
            create_data = {"content": "This is a test journal entry about my reflections today."}
            response = requests.post(f"{self.base_url}/journal", json=create_data, headers=headers)
            
            if response.status_code != 200:
                self.log_result("Journal CREATE", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            entry_data = response.json()
            entry_id = entry_data.get("id")
            if not entry_id:
                self.log_result("Journal CREATE", False, "No entry ID in create response", entry_data)
                return False
                
            self.log_result("Journal CREATE", True, f"Entry created with ID: {entry_id}")
            
            # Test READ (list)
            response = requests.get(f"{self.base_url}/journal", headers=headers)
            if response.status_code != 200:
                self.log_result("Journal READ (list)", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            entries = response.json()
            if not isinstance(entries, list):
                self.log_result("Journal READ (list)", False, "Response is not a list", entries)
                return False
                
            self.log_result("Journal READ (list)", True, f"Retrieved {len(entries)} journal entries")
            
            # Test READ (single)
            response = requests.get(f"{self.base_url}/journal/{entry_id}", headers=headers)
            if response.status_code != 200:
                self.log_result("Journal READ (single)", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            single_entry = response.json()
            if single_entry.get("id") != entry_id:
                self.log_result("Journal READ (single)", False, "Entry ID mismatch", single_entry)
                return False
                
            self.log_result("Journal READ (single)", True, f"Retrieved entry: {entry_id}")
            
            # Test UPDATE
            update_data = {"content": "This is an updated test journal entry with new reflections."}
            response = requests.put(f"{self.base_url}/journal/{entry_id}", json=update_data, headers=headers)
            
            if response.status_code != 200:
                self.log_result("Journal UPDATE", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            updated_entry = response.json()
            if updated_entry.get("content") != update_data["content"]:
                self.log_result("Journal UPDATE", False, "Content not updated correctly", updated_entry)
                return False
                
            self.log_result("Journal UPDATE", True, f"Entry updated: {entry_id}")
            
            # Test DELETE
            response = requests.delete(f"{self.base_url}/journal/{entry_id}", headers=headers)
            if response.status_code != 200:
                self.log_result("Journal DELETE", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            delete_result = response.json()
            if not delete_result.get("success"):
                self.log_result("Journal DELETE", False, "Success field not true", delete_result)
                return False
                
            self.log_result("Journal DELETE", True, f"Entry deleted: {entry_id}")
            
            # Verify deletion
            response = requests.get(f"{self.base_url}/journal/{entry_id}", headers=headers)
            if response.status_code != 404:
                self.log_result("Journal DELETE (verify)", False, f"Entry still exists after deletion: {response.status_code}")
                return False
                
            self.log_result("Journal DELETE (verify)", True, "Entry confirmed deleted")
            
            return True
            
        except Exception as e:
            self.log_result("Journal CRUD", False, f"Exception: {str(e)}")
            return False
    
    def test_lenses_list(self):
        """Test lenses list endpoint"""
        if not self.token:
            self.log_result("Lenses List", False, "No token available for authentication")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.base_url}/lenses", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    # Check first lens has required fields
                    first_lens = data[0]
                    required_fields = ["id", "title", "icon", "summary"]
                    if all(field in first_lens for field in required_fields):
                        self.log_result("Lenses List", True, f"Retrieved {len(data)} lenses")
                        return True
                    else:
                        missing = [f for f in required_fields if f not in first_lens]
                        self.log_result("Lenses List", False, f"Missing required fields in lens: {missing}", first_lens)
                        return False
                else:
                    self.log_result("Lenses List", False, "Empty or invalid lenses list", data)
                    return False
            else:
                self.log_result("Lenses List", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Lenses List", False, f"Exception: {str(e)}")
            return False
    
    def test_lenses_detail(self):
        """Test lens detail endpoint"""
        if not self.token:
            self.log_result("Lenses Detail", False, "No token available for authentication")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            
            # Test with known lens ID
            lens_id = "inner-observer"
            response = requests.get(f"{self.base_url}/lenses/{lens_id}", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["id", "title", "icon", "summary", "deep_dive"]
                if all(field in data for field in required_fields):
                    # Check deep_dive structure
                    deep_dive = data["deep_dive"]
                    deep_dive_fields = ["description", "practices", "invitation"]
                    if all(field in deep_dive for field in deep_dive_fields):
                        self.log_result("Lenses Detail", True, f"Retrieved lens detail: {data['title']}")
                        return True
                    else:
                        missing = [f for f in deep_dive_fields if f not in deep_dive]
                        self.log_result("Lenses Detail", False, f"Missing deep_dive fields: {missing}", data)
                        return False
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_result("Lenses Detail", False, f"Missing required fields: {missing}", data)
                    return False
            else:
                self.log_result("Lenses Detail", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Lenses Detail", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all backend API tests"""
        print(f"🚀 Starting Project Mirror Backend API Tests")
        print(f"📍 Base URL: {self.base_url}")
        print("=" * 60)
        
        # Test sequence following the review request
        tests = [
            ("Auth Register", self.test_auth_register),
            ("Auth Login", self.test_auth_login),
            ("Auth Me", self.test_auth_me),
            ("Onboarding Complete", self.test_onboarding_complete),
            ("Mirror Today", self.test_mirror_today),
            ("Journal CRUD", self.test_journal_crud),
            ("Lenses List", self.test_lenses_list),
            ("Lenses Detail", self.test_lenses_detail),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🧪 Running {test_name}...")
            if test_func():
                passed += 1
        
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed!")
        else:
            print(f"⚠️  {total - passed} tests failed")
            
        return passed == total

if __name__ == "__main__":
    tester = ProjectMirrorTester()
    success = tester.run_all_tests()
    
    # Print detailed results
    print("\n📋 Detailed Test Results:")
    for result in tester.test_results:
        status = "✅" if result["success"] else "❌"
        print(f"{status} {result['test']}: {result['message']}")
    
    exit(0 if success else 1)