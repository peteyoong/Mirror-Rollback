#!/usr/bin/env python3
"""
Backend Testing Script for Human Design Variables with Planetary Longitude Data
Testing the review request scenarios for Human Design Variables computation.
"""

import requests
import json
import sys
from typing import Dict, Any, List

# Backend URL from environment
BACKEND_URL = "https://lens-bridge-app.preview.emergentagent.com/api"

def test_human_design_mechanics_endpoint(user_id: str, expected_environment: str = None) -> Dict[str, Any]:
    """Test the Human Design mechanics endpoint for a specific user."""
    print(f"\n🧪 Testing GET /api/human-design/mechanics/{user_id}")
    
    try:
        response = requests.get(f"{BACKEND_URL}/human-design/mechanics/{user_id}", timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ ERROR: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return {"success": False, "error": f"HTTP {response.status_code}"}
        
        data = response.json()
        
        # Check if variables exist
        variables = data.get("variables")
        print(f"Variables: {variables}")
        
        if variables is None:
            print("⚠️  Variables is null - no planetary longitude data available")
            return {"success": True, "variables": None, "has_longitude_data": False}
        
        # Validate variables structure
        required_components = ["environment", "determination", "cognition", "motivation"]
        missing_components = []
        
        for component in required_components:
            if component not in variables:
                missing_components.append(component)
        
        if missing_components:
            print(f"❌ Missing components: {missing_components}")
            return {"success": False, "error": f"Missing components: {missing_components}"}
        
        # Check environment type
        environment = variables.get("environment", {})
        environment_type = environment.get("type")
        print(f"Environment type: {environment_type}")
        
        if expected_environment and environment_type != expected_environment:
            print(f"❌ Expected environment '{expected_environment}', got '{environment_type}'")
            return {"success": False, "error": f"Environment mismatch: expected {expected_environment}, got {environment_type}"}
        
        # Validate each component structure
        for component_name in required_components:
            component = variables[component_name]
            required_fields = ["type", "description", "arrow"]
            
            for field in required_fields:
                if field not in component:
                    print(f"❌ Component '{component_name}' missing field '{field}'")
                    return {"success": False, "error": f"Component {component_name} missing {field}"}
            
            # Validate arrow direction
            arrow = component.get("arrow")
            if arrow not in ["left", "right"]:
                print(f"❌ Invalid arrow direction '{arrow}' for component '{component_name}'")
                return {"success": False, "error": f"Invalid arrow direction: {arrow}"}
        
        print("✅ All variables components validated successfully")
        return {
            "success": True, 
            "variables": variables, 
            "has_longitude_data": True,
            "environment_type": environment_type
        }
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return {"success": False, "error": str(e)}
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        return {"success": False, "error": f"JSON decode error: {e}"}

def test_recompute_endpoint(user_id: str) -> Dict[str, Any]:
    """Test the Human Design recompute endpoint."""
    print(f"\n🔄 Testing POST /api/human-design/recompute/{user_id}")
    
    try:
        response = requests.post(f"{BACKEND_URL}/human-design/recompute/{user_id}", timeout=60)
        print(f"Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ ERROR: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return {"success": False, "error": f"HTTP {response.status_code}"}
        
        data = response.json()
        print(f"Response keys: {list(data.keys())}")
        
        # Check status
        status = data.get("status")
        print(f"Status: {status}")
        
        if status not in ["success", "skipped"]:
            print(f"❌ Invalid status: {status}")
            return {"success": False, "error": f"Invalid status: {status}"}
        
        # Check for variables and planetary_longitudes
        has_variables = "variables" in data
        has_planetary_longitudes = "planetary_longitudes" in data
        
        print(f"Has variables: {has_variables}")
        print(f"Has planetary_longitudes: {has_planetary_longitudes}")
        
        if status == "success":
            if not has_variables:
                print("⚠️  Success status but no variables in response")
            if not has_planetary_longitudes:
                print("⚠️  Success status but no planetary_longitudes in response")
        
        return {
            "success": True,
            "status": status,
            "has_variables": has_variables,
            "has_planetary_longitudes": has_planetary_longitudes,
            "data": data
        }
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return {"success": False, "error": str(e)}
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        return {"success": False, "error": f"JSON decode error: {e}"}

def validate_planetary_longitudes(planetary_longitudes: Dict[str, Any]) -> Dict[str, Any]:
    """Validate the planetary_longitudes structure."""
    print(f"\n🌍 Validating planetary_longitudes structure")
    
    required_sections = ["personality", "design"]
    required_planets = [
        "sun", "earth", "moon", "mercury", "venus", "mars", 
        "jupiter", "saturn", "uranus", "neptune", "pluto", 
        "north_node", "south_node"
    ]
    
    errors = []
    
    for section in required_sections:
        if section not in planetary_longitudes:
            errors.append(f"Missing section: {section}")
            continue
        
        section_data = planetary_longitudes[section]
        print(f"Section '{section}' has {len(section_data)} planets")
        
        for planet in required_planets:
            if planet not in section_data:
                errors.append(f"Missing planet '{planet}' in section '{section}'")
            else:
                planet_data = section_data[planet]
                # Check if planet has longitude data
                if "longitude" not in planet_data:
                    errors.append(f"Planet '{planet}' in section '{section}' missing longitude")
    
    if errors:
        print(f"❌ Validation errors: {errors}")
        return {"success": False, "errors": errors}
    
    print("✅ Planetary longitudes structure validated successfully")
    return {"success": True}

def main():
    """Main testing function."""
    print("🚀 Starting Human Design Variables with Planetary Longitude Data Testing")
    print(f"Backend URL: {BACKEND_URL}")
    
    test_results = []
    
    # Test 1: Reflector user - expected environment = "valleys"
    print("\n" + "="*80)
    print("TEST 1: Reflector User (697f795f1a7a96aa35e283a3)")
    print("Expected: variables.environment.type = 'valleys'")
    print("="*80)
    
    result1 = test_human_design_mechanics_endpoint("697f795f1a7a96aa35e283a3", "valleys")
    test_results.append(("Reflector User Variables", result1))
    
    # Test 2: peter@test.com - expected environment = "mountains"  
    print("\n" + "="*80)
    print("TEST 2: Peter User (6971c81f2b40fd5ef501d375)")
    print("Expected: variables.environment.type = 'mountains'")
    print("="*80)
    
    result2 = test_human_design_mechanics_endpoint("6971c81f2b40fd5ef501d375", "mountains")
    test_results.append(("Peter User Variables", result2))
    
    # If variables are null, try recompute endpoint
    if (result1.get("variables") is None or result2.get("variables") is None):
        print("\n" + "="*80)
        print("VARIABLES ARE NULL - TESTING RECOMPUTE ENDPOINT")
        print("="*80)
        
        # Test recompute for both users
        print("\nTesting recompute for Reflector user...")
        recompute1 = test_recompute_endpoint("697f795f1a7a96aa35e283a3")
        test_results.append(("Reflector Recompute", recompute1))
        
        print("\nTesting recompute for Peter user...")
        recompute2 = test_recompute_endpoint("6971c81f2b40fd5ef501d375")
        test_results.append(("Peter Recompute", recompute2))
        
        # If recompute was successful, validate planetary_longitudes
        if recompute1.get("has_planetary_longitudes"):
            planetary_longitudes = recompute1["data"].get("planetary_longitudes")
            if planetary_longitudes:
                validation1 = validate_planetary_longitudes(planetary_longitudes)
                test_results.append(("Reflector Planetary Longitudes Validation", validation1))
        
        if recompute2.get("has_planetary_longitudes"):
            planetary_longitudes = recompute2["data"].get("planetary_longitudes")
            if planetary_longitudes:
                validation2 = validate_planetary_longitudes(planetary_longitudes)
                test_results.append(("Peter Planetary Longitudes Validation", validation2))
        
        # Re-test mechanics endpoints after recompute
        print("\n" + "="*80)
        print("RE-TESTING MECHANICS ENDPOINTS AFTER RECOMPUTE")
        print("="*80)
        
        result1_after = test_human_design_mechanics_endpoint("697f795f1a7a96aa35e283a3", "valleys")
        test_results.append(("Reflector User Variables (After Recompute)", result1_after))
        
        result2_after = test_human_design_mechanics_endpoint("6971c81f2b40fd5ef501d375", "mountains")
        test_results.append(("Peter User Variables (After Recompute)", result2_after))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = 0
    failed = 0
    
    for test_name, result in test_results:
        if result.get("success"):
            print(f"✅ {test_name}: PASSED")
            passed += 1
        else:
            print(f"❌ {test_name}: FAILED - {result.get('error', 'Unknown error')}")
            failed += 1
    
    print(f"\nTotal Tests: {len(test_results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/len(test_results)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {failed} TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())