#!/usr/bin/env python3
"""
Backend Testing for Birth Time Handling Feature - STAGING Environment
Testing birth_time and birth_time_known fields in user creation and retrieval
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

# Base URL for staging environment
BASE_URL = "https://cachebuster-2.preview.emergentagent.com/api"

class BackendTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: Dict[str, Any]):
        """Log test results"""
        result = {
            'test_name': test_name,
            'success': success,
            'timestamp': datetime.now().isoformat(),
            'details': details
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"\n{status} {test_name}")
        if details.get('error'):
            print(f"   Error: {details['error']}")
        if details.get('response_data'):
            print(f"   Response: {json.dumps(details['response_data'], indent=2)}")
        
    def test_birth_time_unknown(self):
        """TEST: Create User with Unknown Birth Time"""
        print("\n" + "="*60)
        print("TEST: Create User with Unknown Birth Time")
        print("="*60)
        
        # Generate unique timestamp for test emails
        timestamp = int(time.time())
        
        test_payload = {
            "name": "Sarah Chen",
            "email": f"sarah.chen.{timestamp}@test.com",
            "birth_date": "1990-01-15",
            "birth_time": None,
            "birth_time_known": False,
            "city": "Kuala Lumpur",
            "country": "Malaysia",
            "timezone": "Asia/Kuala_Lumpur",
            "latitude": 3.139,
            "longitude": 101.6869
        }
        
        try:
            response = self.session.post(f"{self.base_url}/users", 
                                       json=test_payload, 
                                       timeout=15)
            
            details = {
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'payload': test_payload,
                'response_data': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            }
            
            if response.status_code == 200:
                data = response.json()
                
                # Check birth_time and birth_time_known fields
                birth_time_checks = {
                    'birth_time_is_null': data.get('birth_time') is None,
                    'birth_time_known_is_false': data.get('birth_time_known') is False,
                    'has_user_id': 'id' in data and data['id'] is not None
                }
                
                details['validation_checks'] = birth_time_checks
                details['birth_time_value'] = data.get('birth_time')
                details['birth_time_known_value'] = data.get('birth_time_known')
                details['user_id'] = data.get('id')
                
                # Store user ID for retrieval test
                if data.get('id'):
                    self.unknown_time_user_id = data.get('id')
                
                success = all(birth_time_checks.values())
                
                if not success:
                    details['error'] = f"Expected birth_time=null, birth_time_known=false, got birth_time={data.get('birth_time')}, birth_time_known={data.get('birth_time_known')}"
                    
            else:
                success = False
                details['error'] = f"Expected 200, got {response.status_code}"
                
            self.log_test("Create User with Unknown Birth Time", success, details)
            return success
            
        except Exception as e:
            details = {'error': str(e), 'payload': test_payload}
            self.log_test("Create User with Unknown Birth Time", False, details)
            return False

    def test_birth_time_known(self):
        """TEST: Create User with Known Birth Time (24h format)"""
        print("\n" + "="*60)
        print("TEST: Create User with Known Birth Time (24h format)")
        print("="*60)
        
        # Generate unique timestamp for test emails
        timestamp = int(time.time())
        
        test_payload = {
            "name": "Marcus Tan",
            "email": f"marcus.tan.{timestamp}@test.com",
            "birth_date": "1990-01-15",
            "birth_time": "19:30",
            "birth_time_known": True,
            "city": "Singapore",
            "country": "Singapore",
            "timezone": "Asia/Singapore",
            "latitude": 1.3521,
            "longitude": 103.8198
        }
        
        try:
            response = self.session.post(f"{self.base_url}/users", 
                                       json=test_payload, 
                                       timeout=15)
            
            details = {
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'payload': test_payload,
                'response_data': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            }
            
            if response.status_code == 200:
                data = response.json()
                
                # Check birth_time and birth_time_known fields
                birth_time_checks = {
                    'birth_time_is_1930': data.get('birth_time') == "19:30",
                    'birth_time_known_is_true': data.get('birth_time_known') is True,
                    'has_user_id': 'id' in data and data['id'] is not None
                }
                
                details['validation_checks'] = birth_time_checks
                details['birth_time_value'] = data.get('birth_time')
                details['birth_time_known_value'] = data.get('birth_time_known')
                details['user_id'] = data.get('id')
                
                success = all(birth_time_checks.values())
                
                if not success:
                    details['error'] = f"Expected birth_time='19:30', birth_time_known=true, got birth_time={data.get('birth_time')}, birth_time_known={data.get('birth_time_known')}"
                    
            else:
                success = False
                details['error'] = f"Expected 200, got {response.status_code}"
                
            self.log_test("Create User with Known Birth Time", success, details)
            return success
            
        except Exception as e:
            details = {'error': str(e), 'payload': test_payload}
            self.log_test("Create User with Known Birth Time", False, details)
            return False

    def test_user_retrieval_birth_time_known(self):
        """TEST: Get User - Should return birth_time_known"""
        print("\n" + "="*60)
        print("TEST: Get User - Should return birth_time_known")
        print("="*60)
        
        if not hasattr(self, 'unknown_time_user_id') or not self.unknown_time_user_id:
            details = {'error': 'No user ID from unknown birth time test to retrieve'}
            self.log_test("Get User - birth_time_known field", False, details)
            return False
            
        try:
            response = self.session.get(f"{self.base_url}/users/{self.unknown_time_user_id}", timeout=10)
            
            details = {
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'user_id': self.unknown_time_user_id,
                'response_data': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            }
            
            if response.status_code == 200:
                data = response.json()
                
                # Check that birth_time_known field is present and correct
                retrieval_checks = {
                    'has_birth_time_known_field': 'birth_time_known' in data,
                    'birth_time_known_is_false': data.get('birth_time_known') is False,
                    'birth_time_is_null': data.get('birth_time') is None
                }
                
                details['validation_checks'] = retrieval_checks
                details['birth_time_known_value'] = data.get('birth_time_known')
                details['birth_time_value'] = data.get('birth_time')
                
                success = all(retrieval_checks.values())
                
                if not success:
                    details['error'] = f"Expected birth_time_known=false in response, got {data.get('birth_time_known')}"
                    
            else:
                success = False
                details['error'] = f"Expected 200, got {response.status_code}"
                
            self.log_test("Get User - birth_time_known field", success, details)
            return success
            
        except Exception as e:
            details = {'error': str(e), 'user_id': self.unknown_time_user_id}
            self.log_test("Get User - birth_time_known field", False, details)
            return False

    def test_invalid_time_format(self):
        """TEST: Validate 24h Time Format (Invalid)"""
        print("\n" + "="*60)
        print("TEST: Validate 24h Time Format (Invalid)")
        print("="*60)
        
        # Generate unique timestamp for test emails
        timestamp = int(time.time())
        
        test_payload = {
            "name": "Emma Wilson",
            "email": f"emma.wilson.{timestamp}@test.com",
            "birth_date": "1990-01-15",
            "birth_time": "25:00",  # Invalid time
            "birth_time_known": True,
            "city": "London",
            "country": "United Kingdom",
            "timezone": "Europe/London"
        }
        
        try:
            response = self.session.post(f"{self.base_url}/users", 
                                       json=test_payload, 
                                       timeout=15)
            
            details = {
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'payload': test_payload,
                'response_data': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            }
            
            if response.status_code == 400:
                data = response.json()
                
                # Check for VALIDATION_ERROR
                validation_checks = {
                    'is_validation_error': data.get('error') == 'VALIDATION_ERROR',
                    'has_error_field': 'error' in data,
                    'is_json_response': response.headers.get('content-type', '').startswith('application/json')
                }
                
                details['validation_checks'] = validation_checks
                details['error_value'] = data.get('error')
                details['message_value'] = data.get('message')
                
                success = all(validation_checks.values())
                
                if not success:
                    details['error'] = f"Expected VALIDATION_ERROR, got {data.get('error')}"
                    
            else:
                success = False
                details['error'] = f"Expected 400 validation error, got {response.status_code}"
                
            self.log_test("Validate Invalid Time Format", success, details)
            return success
            
        except Exception as e:
            details = {'error': str(e), 'payload': test_payload}
            self.log_test("Validate Invalid Time Format", False, details)
            return False
        """TEST 2: Verify Backend Health"""
        print("\n" + "="*60)
        print("TEST 2: Backend Health Check")
        print("="*60)
        
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            
            details = {
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'response_data': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            }
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_checks = {
                    'env_is_staging': data.get('env') == 'staging',
                    'db_type_present': 'db_type' in data and data['db_type'] is not None,
                    'build_version_present': 'build_version' in data and data['build_version'] is not None
                }
                
                details['validation_checks'] = required_checks
                details['env_value'] = data.get('env')
                details['db_type_value'] = data.get('db_type')
                details['build_version_value'] = data.get('build_version')
                
                all_checks_pass = all(required_checks.values())
                
                self.log_test("Backend Health Check", all_checks_pass, details)
                return all_checks_pass
            else:
                details['error'] = f"Unexpected status code: {response.status_code}"
                self.log_test("Backend Health Check", False, details)
                return False
                
        except Exception as e:
            details = {'error': str(e)}
            self.log_test("Backend Health Check", False, details)
            return False

    def test_backend_health(self):
        """TEST: Health Check - Should return env: 'staging'"""
        print("\n" + "="*60)
        print("TEST: Health Check")
        print("="*60)
        
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            
            details = {
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'response_data': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            }
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                health_checks = {
                    'env_is_staging': data.get('env') == 'staging',
                    'has_status': 'status' in data,
                    'has_timestamp': 'timestamp_utc' in data or 'timestamp' in data
                }
                
                details['validation_checks'] = health_checks
                details['env_value'] = data.get('env')
                details['status_value'] = data.get('status')
                
                success = all(health_checks.values())
                
                if not success:
                    details['error'] = f"Expected env='staging', got {data.get('env')}"
                    
            else:
                success = False
                details['error'] = f"Expected 200, got {response.status_code}"
                
            self.log_test("Health Check", success, details)
            return success
            
        except Exception as e:
            details = {'error': str(e)}
            self.log_test("Health Check", False, details)
            return False
    
    def test_user_creation_valid(self):
        """TEST 1a: Create user with valid data"""
        print("\n" + "="*60)
        print("TEST 1a: User Creation - Valid Data")
        print("="*60)
        
        # Create unique email with timestamp
        timestamp = int(time.time())
        test_payload = {
            "name": "Test User P0",
            "email": f"unique-test-{timestamp}@example.com",
            "birth_date": "1990-01-15",
            "birth_time": "10:30",
            "city": "Kuala Lumpur",
            "country": "Malaysia",
            "timezone": "Asia/Kuala_Lumpur",
            "latitude": 3.139,
            "longitude": 101.6869
        }
        
        try:
            response = self.session.post(f"{self.base_url}/users", 
                                       json=test_payload, 
                                       timeout=15)
            
            details = {
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'payload': test_payload,
                'response_data': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            }
            
            success = response.status_code == 200
            if success:
                data = response.json()
                # Store email for duplicate test
                self.test_email = test_payload['email']
                details['user_created'] = True
                details['user_id'] = data.get('user', {}).get('id') if isinstance(data.get('user'), dict) else None
            else:
                details['error'] = f"Expected 200, got {response.status_code}"
                
            self.log_test("User Creation - Valid Data", success, details)
            return success
            
        except Exception as e:
            details = {'error': str(e), 'payload': test_payload}
            self.log_test("User Creation - Valid Data", False, details)
            return False
    
    def test_user_creation_duplicate_email(self):
        """TEST 1b: Create user with duplicate email"""
        print("\n" + "="*60)
        print("TEST 1b: User Creation - Duplicate Email")
        print("="*60)
        
        if not hasattr(self, 'test_email'):
            print("   Skipping: No test email from previous test")
            return False
            
        # Use the same email from the previous test
        test_payload = {
            "name": "Duplicate Test User",
            "email": self.test_email,  # Same email as before
            "birth_date": "1985-05-20",
            "birth_time": "14:15",
            "city": "Singapore",
            "country": "Singapore",
            "timezone": "Asia/Singapore",
            "latitude": 1.3521,
            "longitude": 103.8198
        }
        
        try:
            response = self.session.post(f"{self.base_url}/users", 
                                       json=test_payload, 
                                       timeout=15)
            
            details = {
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'payload': test_payload,
                'response_data': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            }
            
            if response.status_code == 400:
                data = response.json()
                
                # Check for required error structure
                required_fields = {
                    'error_present': 'error' in data,
                    'message_present': 'message' in data,
                    'field_present': 'field' in data,
                    'error_is_validation': data.get('error') == 'VALIDATION_ERROR',
                    'field_is_email': data.get('field') == 'email',
                    'message_contains_registered': 'already registered' in data.get('message', '').lower()
                }
                
                details['validation_checks'] = required_fields
                details['error_value'] = data.get('error')
                details['message_value'] = data.get('message')
                details['field_value'] = data.get('field')
                
                success = all(required_fields.values())
                
                if not success:
                    details['error'] = "Response structure doesn't match expected validation error format"
                    
            else:
                success = False
                details['error'] = f"Expected 400 status code, got {response.status_code}"
                
            self.log_test("User Creation - Duplicate Email", success, details)
            return success
            
        except Exception as e:
            details = {'error': str(e), 'payload': test_payload}
            self.log_test("User Creation - Duplicate Email", False, details)
            return False
    
    def test_user_creation_invalid_timezone(self):
        """TEST 1c: Create user with invalid timezone"""
        print("\n" + "="*60)
        print("TEST 1c: User Creation - Invalid Timezone")
        print("="*60)
        
        # Create unique email with timestamp
        timestamp = int(time.time())
        test_payload = {
            "name": "Invalid Timezone User",
            "email": f"invalid-tz-test-{timestamp}@example.com",
            "birth_date": "1992-03-10",
            "birth_time": "09:45",
            "city": "London",
            "country": "United Kingdom",
            "timezone": "Invalid/Timezone",  # Invalid timezone
            "latitude": 51.5074,
            "longitude": -0.1278
        }
        
        try:
            response = self.session.post(f"{self.base_url}/users", 
                                       json=test_payload, 
                                       timeout=15)
            
            details = {
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'payload': test_payload,
                'response_data': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            }
            
            # Should return 400 with validation error
            if response.status_code == 400:
                data = response.json()
                
                # Check that it's a proper JSON validation error (not 520)
                validation_checks = {
                    'is_json_response': response.headers.get('content-type', '').startswith('application/json'),
                    'has_error_field': 'error' in data,
                    'not_520_error': response.status_code != 520
                }
                
                details['validation_checks'] = validation_checks
                success = all(validation_checks.values())
                
                if not success:
                    details['error'] = "Response is not proper JSON validation error"
                    
            else:
                success = False
                details['error'] = f"Expected 400 status code for invalid timezone, got {response.status_code}"
                
            self.log_test("User Creation - Invalid Timezone", success, details)
            return success
            
        except Exception as e:
            details = {'error': str(e), 'payload': test_payload}
            self.log_test("User Creation - Invalid Timezone", False, details)
            return False
    
    def run_all_tests(self):
        """Run all Birth Time handling tests"""
        print("="*80)
        print("BACKEND BIRTH TIME HANDLING TESTING - STAGING ENVIRONMENT")
        print("="*80)
        print(f"Base URL: {self.base_url}")
        print(f"Test Start Time: {datetime.now().isoformat()}")
        
        # Run Birth Time handling tests in order
        test_results = []
        
        # Birth Time Tests
        test_results.append(self.test_birth_time_unknown())
        test_results.append(self.test_birth_time_known())
        test_results.append(self.test_user_retrieval_birth_time_known())
        test_results.append(self.test_invalid_time_format())
        test_results.append(self.test_backend_health())
        
        # Summary
        print("\n" + "="*80)
        print("BIRTH TIME HANDLING TEST SUMMARY")
        print("="*80)
        
        passed = sum(test_results)
        total = len(test_results)
        
        print(f"Tests Passed: {passed}/{total}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("🎉 ALL BIRTH TIME HANDLING TESTS PASSED")
        else:
            print("⚠️  SOME BIRTH TIME HANDLING TESTS FAILED")
            
        # Detailed results
        print("\nDetailed Results:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"  {status} {result['test_name']}")
            if not result['success'] and result['details'].get('error'):
                print(f"     Error: {result['details']['error']}")
        
        return passed == total

def main():
    """Main test execution"""
    tester = BackendTester()
    success = tester.run_all_tests()
    
    if success:
        print(f"\n✅ All P0 fixes verified successfully in STAGING environment")
        exit(0)
    else:
        print(f"\n❌ Some P0 fixes failed verification")
        exit(1)

if __name__ == "__main__":
    main()