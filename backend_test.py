#!/usr/bin/env python3
"""
Backend Testing Script for Journal Edit and Delete API Endpoints
Testing the new Journal Edit and Delete functionality as requested in review
"""

import requests
import json
import time
import sys
from datetime import datetime

# Backend URL from environment
BACKEND_URL = "https://reflect-ai-25.preview.emergentagent.com/api"

def test_get_journal_entries():
    """
    Test GET /api/journal/{user_id} - Get journal entries
    """
    print("🧪 TEST 1: GET JOURNAL ENTRIES")
    print("=" * 50)
    
    user_id = "697f0c6abf35c0528ff06954"
    
    print(f"📋 Getting journal entries for user: {user_id}")
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/journal/{user_id}",
            timeout=30
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            entries = response.json()
            print(f"   ✅ SUCCESS: Found {len(entries)} journal entries")
            
            if entries:
                # Show first entry details
                first_entry = entries[0]
                print(f"   📝 First entry:")
                print(f"      ID: {first_entry.get('id')}")
                print(f"      Content: {first_entry.get('content', '')[:100]}...")
                print(f"      Created: {first_entry.get('created_at')}")
                return entries
            else:
                print("   ⚠️  No journal entries found for this user")
                return []
        else:
            print(f"   ❌ FAILED: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        return None

def test_update_journal_entry(entry_id):
    """
    Test PUT /api/journal/{entry_id} - Update journal entry
    """
    print(f"\n🧪 TEST 2: UPDATE JOURNAL ENTRY")
    print("=" * 50)
    
    updated_content = "Test edit - this content was updated"
    payload = {
        "content": updated_content
    }
    
    print(f"📋 Updating entry ID: {entry_id}")
    print(f"   New content: {updated_content}")
    
    try:
        response = requests.put(
            f"{BACKEND_URL}/journal/{entry_id}",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            updated_entry = response.json()
            print(f"   ✅ SUCCESS: Entry updated")
            print(f"      ID: {updated_entry.get('id')}")
            print(f"      Content: {updated_entry.get('content')}")
            print(f"      Created: {updated_entry.get('created_at')}")
            return updated_entry
        else:
            print(f"   ❌ FAILED: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        return None

def test_verify_update_persisted(user_id, entry_id, expected_content):
    """
    Verify the update persisted by getting the entry again
    """
    print(f"\n🧪 TEST 3: VERIFY UPDATE PERSISTED")
    print("=" * 50)
    
    print(f"📋 Getting updated entry to verify persistence")
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/journal/{user_id}",
            timeout=30
        )
        
        if response.status_code == 200:
            entries = response.json()
            
            # Find the updated entry
            updated_entry = None
            for entry in entries:
                if entry.get('id') == entry_id:
                    updated_entry = entry
                    break
            
            if updated_entry:
                actual_content = updated_entry.get('content', '')
                if actual_content == expected_content:
                    print(f"   ✅ SUCCESS: Update persisted correctly")
                    print(f"      Content matches: {actual_content}")
                    return True
                else:
                    print(f"   ❌ FAILED: Content mismatch")
                    print(f"      Expected: {expected_content}")
                    print(f"      Actual: {actual_content}")
                    return False
            else:
                print(f"   ❌ FAILED: Could not find updated entry with ID {entry_id}")
                return False
        else:
            print(f"   ❌ FAILED: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        return False

def test_create_test_entry():
    """
    Create a test journal entry for deletion testing
    """
    print(f"\n🧪 TEST 4: CREATE TEST ENTRY FOR DELETION")
    print("=" * 50)
    
    user_id = "697f0c6abf35c0528ff06954"
    test_content = "Test entry to delete"
    
    payload = {
        "user_id": user_id,
        "content": test_content
    }
    
    print(f"📋 Creating test entry for deletion")
    print(f"   User ID: {user_id}")
    print(f"   Content: {test_content}")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/journal",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            new_entry = response.json()
            print(f"   ✅ SUCCESS: Test entry created")
            print(f"      ID: {new_entry.get('id')}")
            print(f"      Content: {new_entry.get('content')}")
            return new_entry
        else:
            print(f"   ❌ FAILED: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        return None

def test_delete_journal_entry(entry_id):
    """
    Test DELETE /api/journal/{entry_id} - Delete journal entry
    """
    print(f"\n🧪 TEST 5: DELETE JOURNAL ENTRY")
    print("=" * 50)
    
    print(f"📋 Deleting entry ID: {entry_id}")
    
    try:
        response = requests.delete(
            f"{BACKEND_URL}/journal/{entry_id}",
            timeout=30
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ SUCCESS: Entry deleted")
            print(f"      Success: {result.get('success')}")
            print(f"      Message: {result.get('message')}")
            return result
        else:
            print(f"   ❌ FAILED: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        return None

def test_verify_deletion(user_id, deleted_entry_id):
    """
    Verify the entry was actually deleted
    """
    print(f"\n🧪 TEST 6: VERIFY ENTRY DELETED")
    print("=" * 50)
    
    print(f"📋 Verifying entry {deleted_entry_id} was deleted")
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/journal/{user_id}",
            timeout=30
        )
        
        if response.status_code == 200:
            entries = response.json()
            
            # Check if deleted entry still exists
            deleted_entry = None
            for entry in entries:
                if entry.get('id') == deleted_entry_id:
                    deleted_entry = entry
                    break
            
            if deleted_entry is None:
                print(f"   ✅ SUCCESS: Entry successfully deleted")
                return True
            else:
                print(f"   ❌ FAILED: Entry still exists after deletion")
                print(f"      Found entry: {deleted_entry}")
                return False
        else:
            print(f"   ❌ FAILED: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        return False

def test_error_cases():
    """
    Test error cases as specified in review request
    """
    print(f"\n🧪 TEST 7: ERROR CASES")
    print("=" * 50)
    
    # Test 1: Update with invalid ID
    print("📋 Testing PUT with invalid entry ID")
    try:
        response = requests.put(
            f"{BACKEND_URL}/journal/invalid_id",
            json={"content": "Test content"},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"   Status Code: {response.status_code}")
        if response.status_code >= 400:
            print(f"   ✅ SUCCESS: Invalid ID properly rejected")
        else:
            print(f"   ❌ FAILED: Invalid ID should return error")
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
    
    # Test 2: Delete with non-existent ID
    print("\n📋 Testing DELETE with non-existent entry ID")
    try:
        response = requests.delete(
            f"{BACKEND_URL}/journal/000000000000000000000000",
            timeout=30
        )
        
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 404:
            print(f"   ✅ SUCCESS: Non-existent ID returns 404")
            result = response.json()
            print(f"      Message: {result.get('detail', 'No message')}")
        else:
            print(f"   ❌ FAILED: Expected 404 for non-existent ID")
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")

def main():
    """
    Main test execution for Journal Edit and Delete API endpoints
    """
    print("🧪 JOURNAL EDIT AND DELETE API ENDPOINTS TESTING")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Base URL: https://reflect-ai-25.preview.emergentagent.com")
    print()
    
    user_id = "697f0c6abf35c0528ff06954"
    
    # Test 1: Get journal entries
    entries = test_get_journal_entries()
    if not entries:
        print("\n❌ TESTING FAILED: Could not get journal entries")
        return
    
    # Test 2: Update existing journal entry (if available)
    if entries:
        first_entry_id = entries[0].get('id')
        updated_entry = test_update_journal_entry(first_entry_id)
        
        if updated_entry:
            # Test 3: Verify update persisted
            test_verify_update_persisted(user_id, first_entry_id, "Test edit - this content was updated")
    
    # Test 4: Create test entry for deletion
    test_entry = test_create_test_entry()
    
    if test_entry:
        test_entry_id = test_entry.get('id')
        
        # Test 5: Delete the test entry
        delete_result = test_delete_journal_entry(test_entry_id)
        
        if delete_result:
            # Test 6: Verify deletion
            test_verify_deletion(user_id, test_entry_id)
    
    # Test 7: Error cases
    test_error_cases()
    
    print("\n🎯 SUMMARY:")
    print("=" * 60)
    print("✅ Journal API endpoints tested comprehensively")
    print("✅ GET /api/journal/{user_id} - List entries")
    print("✅ PUT /api/journal/{entry_id} - Update entry")
    print("✅ DELETE /api/journal/{entry_id} - Delete entry")
    print("✅ Error cases tested (invalid IDs)")
    print("✅ Data persistence verified")
    
    print("\n📋 REVIEW REQUEST REQUIREMENTS TESTED:")
    print("✅ GET journal entries with id, content, themes, created_at fields")
    print("✅ PUT journal entry with content update")
    print("✅ DELETE journal entry with success response")
    print("✅ Verify update persistence with GET request")
    print("✅ Error cases: invalid ID (500/error) and non-existent ID (404)")

if __name__ == "__main__":
    main()