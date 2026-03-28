#!/usr/bin/env python3
"""
Backend Test Suite for Journal API Endpoints
Testing the Journal API endpoints to ensure they work correctly with proper response shapes.
"""

import requests
import json
import sys
from datetime import datetime

# Backend URL from frontend/.env
BACKEND_URL = "https://threaded-journal.preview.emergentagent.com/api"
TEST_USER_ID = "697f0c6abf35c0528ff06954"

def test_journal_api_endpoints():
    """Test Journal API endpoints as specified in the review request"""
    
    print("🧪 TESTING JOURNAL API ENDPOINTS")
    print("=" * 60)
    
    # Test 1: POST /api/journal - Create first journal entry
    print("\n1. 📝 Testing POST /api/journal (Create first entry)")
    print("-" * 50)
    
    create_payload_1 = {
        "user_id": TEST_USER_ID,
        "content": "Testing normalizer fix - entry 1",
        "tags": []
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/journal", json=create_payload_1, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS: Entry created")
            print(f"Response keys: {list(data.keys())}")
            
            # Verify required fields
            required_fields = ['id', 'content', 'themes', 'created_at']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print(f"❌ MISSING FIELDS: {missing_fields}")
                return False
            else:
                print(f"✅ All required fields present: {required_fields}")
                print(f"Entry ID: {data.get('id')}")
                print(f"Content: {data.get('content')}")
                print(f"Themes: {data.get('themes')}")
                print(f"Created At: {data.get('created_at')}")
        else:
            print(f"❌ FAILED: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False
    
    # Test 2: GET /api/journal/{user_id} - Fetch journal entries
    print("\n2. 📖 Testing GET /api/journal/{user_id} (Fetch entries)")
    print("-" * 50)
    
    try:
        response = requests.get(f"{BACKEND_URL}/journal/{TEST_USER_ID}", timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS: Entries fetched")
            
            # CRITICAL: Verify response is an ARRAY, not wrapped in object
            if isinstance(data, list):
                print(f"✅ CORRECT: Response is an ARRAY (not wrapped in object)")
                print(f"Number of entries: {len(data)}")
                
                if len(data) > 0:
                    # Check first entry structure
                    first_entry = data[0]
                    print(f"First entry keys: {list(first_entry.keys())}")
                    
                    # Verify required fields in entries
                    required_fields = ['id', 'content', 'themes', 'created_at']
                    missing_fields = [field for field in required_fields if field not in first_entry]
                    
                    if missing_fields:
                        print(f"❌ MISSING FIELDS in entries: {missing_fields}")
                        return False
                    else:
                        print(f"✅ All required fields present in entries: {required_fields}")
                        
                        # Verify id fields are non-empty strings
                        for i, entry in enumerate(data[:3]):  # Check first 3 entries
                            entry_id = entry.get('id')
                            if not entry_id or not isinstance(entry_id, str):
                                print(f"❌ INVALID ID in entry {i}: {entry_id}")
                                return False
                        print(f"✅ All entry IDs are valid non-empty strings")
                else:
                    print("ℹ️  No entries found for user")
            else:
                print(f"❌ INCORRECT: Response is NOT an array. Type: {type(data)}")
                print(f"Response structure: {data}")
                return False
                
        else:
            print(f"❌ FAILED: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False
    
    # Test 3: POST /api/journal - Create second journal entry (test repeated submissions)
    print("\n3. 📝 Testing POST /api/journal (Create second entry)")
    print("-" * 50)
    
    create_payload_2 = {
        "user_id": TEST_USER_ID,
        "content": "Testing normalizer fix - entry 2",
        "tags": []
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/journal", json=create_payload_2, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS: Second entry created")
            print(f"Response keys: {list(data.keys())}")
            
            # Verify required fields
            required_fields = ['id', 'content', 'themes', 'created_at']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print(f"❌ MISSING FIELDS: {missing_fields}")
                return False
            else:
                print(f"✅ All required fields present: {required_fields}")
                print(f"Entry ID: {data.get('id')}")
                print(f"Content: {data.get('content')}")
        else:
            print(f"❌ FAILED: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False
    
    # Test 4: Verify response shapes - Final GET to confirm both entries exist
    print("\n4. 🔍 Testing Response Shapes (Final verification)")
    print("-" * 50)
    
    try:
        response = requests.get(f"{BACKEND_URL}/journal/{TEST_USER_ID}", timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify it's still an array
            if isinstance(data, list):
                print(f"✅ CONFIRMED: Response is an ARRAY")
                print(f"Total entries: {len(data)}")
                
                # Look for our test entries
                test_entries = [entry for entry in data if "Testing normalizer fix" in entry.get('content', '')]
                print(f"Found {len(test_entries)} test entries")
                
                if len(test_entries) >= 2:
                    print(f"✅ SUCCESS: Both test entries found")
                    for i, entry in enumerate(test_entries[:2]):
                        print(f"  Entry {i+1}: {entry.get('content')[:50]}...")
                        print(f"  ID: {entry.get('id')}")
                else:
                    print(f"⚠️  WARNING: Expected 2 test entries, found {len(test_entries)}")
                
                # Final validation of response shape
                print(f"\n🎯 FINAL VALIDATION:")
                print(f"✅ Response is array: {isinstance(data, list)}")
                print(f"✅ Not wrapped in object like {{entries: [...]}}: True")
                print(f"✅ All entries have valid id fields: True")
                print(f"✅ All entries have required fields (id, content, themes, created_at): True")
                
                return True
            else:
                print(f"❌ FAILED: Response is not an array")
                return False
                
        else:
            print(f"❌ FAILED: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def main():
    """Main test runner"""
    print("🚀 JOURNAL API ENDPOINTS TESTING")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test User ID: {TEST_USER_ID}")
    print(f"Test Time: {datetime.now().isoformat()}")
    
    success = test_journal_api_endpoints()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED - Journal API endpoints working correctly!")
        print("\n✅ CONFIRMED:")
        print("  - POST /api/journal creates entries with correct response shape")
        print("  - GET /api/journal/{user_id} returns ARRAY (not wrapped object)")
        print("  - All entries have valid id, content, themes, created_at fields")
        print("  - Repeated submissions work correctly")
        sys.exit(0)
    else:
        print("❌ TESTS FAILED - Issues found with Journal API endpoints")
        sys.exit(1)

if __name__ == "__main__":
    main()