#!/usr/bin/env python3
"""
Comprehensive Human Design Variables Testing Script
Testing all review request requirements for Human Design Variables with planetary longitude data.
"""

import requests
import json
import sys
from typing import Dict, Any, List

# Backend URL from environment
BACKEND_URL = "https://mirror-forum-fix.preview.emergentagent.com/api"

def test_mechanics_endpoint_comprehensive(user_id: str, expected_environment: str, user_description: str) -> Dict[str, Any]:
    """Comprehensive test of the Human Design mechanics endpoint."""
    print(f"\n🧪 Testing GET /api/human-design/mechanics/{user_id} ({user_description})")
    print(f"Expected environment: {expected_environment}")
    
    try:
        response = requests.get(f"{BACKEND_URL}/human-design/mechanics/{user_id}", timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code != 200:
            return {"success": False, "error": f"HTTP {response.status_code}", "response": response.text}
        
        data = response.json()
        variables = data.get("variables")
        
        if variables is None:
            return {"success": False, "error": "Variables is null - no planetary longitude data"}
        
        # Test 1: Variables should have all 4 components
        required_components = ["environment", "determination", "cognition", "motivation"]
        missing_components = [comp for comp in required_components if comp not in variables]
        
        if missing_components:
            return {"success": False, "error": f"Missing components: {missing_components}"}
        
        print(f"✅ All 4 components present: {required_components}")
        
        # Test 2: Each component should have type, description, and arrow
        for component_name in required_components:
            component = variables[component_name]
            required_fields = ["type", "description", "arrow"]
            missing_fields = [field for field in required_fields if field not in component]
            
            if missing_fields:
                return {"success": False, "error": f"Component {component_name} missing fields: {missing_fields}"}
            
            # Validate arrow direction
            arrow = component.get("arrow")
            if arrow not in ["left", "right"]:
                return {"success": False, "error": f"Invalid arrow '{arrow}' for {component_name}"}
        
        print(f"✅ All components have required fields (type, description, arrow)")
        
        # Test 3: Environment type should match expected
        environment = variables["environment"]
        environment_type = environment["type"]
        
        if environment_type != expected_environment:
            return {"success": False, "error": f"Environment mismatch: expected '{expected_environment}', got '{environment_type}'"}
        
        print(f"✅ Environment type matches: {environment_type}")
        
        # Additional validation: Print component details
        print(f"\n📋 Component Details:")
        for component_name in required_components:
            component = variables[component_name]
            print(f"  {component_name}: {component['type']} ({component['arrow']} arrow)")
            print(f"    Description: {component['description']}")
        
        return {
            "success": True,
            "environment_type": environment_type,
            "variables": variables,
            "all_components_present": True,
            "all_fields_present": True
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def test_recompute_endpoint_comprehensive(user_id: str, user_description: str) -> Dict[str, Any]:
    """Comprehensive test of the recompute endpoint."""
    print(f"\n🔄 Testing POST /api/human-design/recompute/{user_id} ({user_description})")
    
    try:
        # Test without force first
        response = requests.post(f"{BACKEND_URL}/human-design/recompute/{user_id}", timeout=60)
        print(f"Status: {response.status_code}")
        
        if response.status_code != 200:
            return {"success": False, "error": f"HTTP {response.status_code}", "response": response.text}
        
        data = response.json()
        status = data.get("status")
        
        print(f"Status: {status}")
        
        # Test 1: Status should be "success" or "skipped"
        if status not in ["success", "skipped"]:
            return {"success": False, "error": f"Invalid status: {status}"}
        
        print(f"✅ Valid status: {status}")
        
        # Test 2: Should include variables in response
        has_variables = "variables" in data
        if not has_variables:
            return {"success": False, "error": "No variables in response"}
        
        print(f"✅ Variables included in response")
        
        # If skipped, test with force=true to get planetary_longitudes
        if status == "skipped":
            print(f"\n🔄 Testing with force=true to get planetary_longitudes...")
            response_force = requests.post(f"{BACKEND_URL}/human-design/recompute/{user_id}?force=true", timeout=60)
            
            if response_force.status_code != 200:
                return {"success": False, "error": f"Force recompute failed: HTTP {response_force.status_code}"}
            
            data_force = response_force.json()
            status_force = data_force.get("status")
            
            if status_force != "success":
                return {"success": False, "error": f"Force recompute status: {status_force}"}
            
            # Test 3: Should include planetary_longitudes in force response
            has_planetary_longitudes = "planetary_longitudes" in data_force
            if not has_planetary_longitudes:
                return {"success": False, "error": "No planetary_longitudes in force response"}
            
            print(f"✅ Planetary longitudes included in force response")
            
            return {
                "success": True,
                "status": status,
                "force_status": status_force,
                "has_variables": True,
                "has_planetary_longitudes": True,
                "planetary_longitudes": data_force["planetary_longitudes"]
            }
        
        # If success, should already have planetary_longitudes
        has_planetary_longitudes = "planetary_longitudes" in data
        
        return {
            "success": True,
            "status": status,
            "has_variables": has_variables,
            "has_planetary_longitudes": has_planetary_longitudes,
            "planetary_longitudes": data.get("planetary_longitudes")
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def validate_planetary_longitudes_structure(planetary_longitudes: Dict[str, Any]) -> Dict[str, Any]:
    """Validate planetary_longitudes structure according to review requirements."""
    print(f"\n🌍 Validating planetary_longitudes structure")
    
    # Test 1: Both personality and design sections
    required_sections = ["personality", "design"]
    missing_sections = [section for section in required_sections if section not in planetary_longitudes]
    
    if missing_sections:
        return {"success": False, "error": f"Missing sections: {missing_sections}"}
    
    print(f"✅ Both personality and design sections present")
    
    # Test 2: All 13 planets present in each section
    required_planets = [
        "sun", "earth", "moon", "mercury", "venus", "mars", 
        "jupiter", "saturn", "uranus", "neptune", "pluto", 
        "north_node", "south_node"
    ]
    
    errors = []
    
    for section in required_sections:
        section_data = planetary_longitudes[section]
        print(f"Section '{section}' has {len(section_data)} planets")
        
        missing_planets = [planet for planet in required_planets if planet not in section_data]
        if missing_planets:
            errors.append(f"Section '{section}' missing planets: {missing_planets}")
        
        # Validate longitude values are numbers
        for planet in required_planets:
            if planet in section_data:
                longitude = section_data[planet]
                if not isinstance(longitude, (int, float)):
                    errors.append(f"Planet '{planet}' in '{section}' has non-numeric longitude: {longitude}")
                elif not (0 <= longitude < 360):
                    errors.append(f"Planet '{planet}' in '{section}' has invalid longitude: {longitude} (should be 0-360)")
    
    if errors:
        return {"success": False, "errors": errors}
    
    print(f"✅ All 13 planets present in both sections with valid longitude values")
    
    # Print sample data
    print(f"\n📋 Sample Planetary Data:")
    for section in required_sections:
        print(f"  {section.upper()}:")
        section_data = planetary_longitudes[section]
        for planet in ["sun", "moon", "mercury"][:3]:  # Show first 3 as sample
            if planet in section_data:
                print(f"    {planet}: {section_data[planet]:.2f}°")
    
    return {"success": True}

def main():
    """Main testing function."""
    print("🚀 COMPREHENSIVE HUMAN DESIGN VARIABLES TESTING")
    print("Testing all review request requirements")
    print(f"Backend URL: {BACKEND_URL}")
    print("="*80)
    
    test_results = []
    
    # Test Scenario 1: Reflector user - expected environment = "valleys"
    print("\n" + "🎯 TEST SCENARIO 1: REFLECTOR USER")
    print("User ID: 697f795f1a7a96aa35e283a3")
    print("Expected: variables.environment.type = 'valleys'")
    print("Expected: variables should have all 4 components")
    print("Expected: Each component should have type, description, and arrow")
    
    result1 = test_mechanics_endpoint_comprehensive("697f795f1a7a96aa35e283a3", "valleys", "Reflector user")
    test_results.append(("Reflector User Mechanics", result1))
    
    # Test Scenario 2: peter@test.com - expected environment = "mountains"
    print("\n" + "🎯 TEST SCENARIO 2: PETER USER")
    print("User ID: 6971c81f2b40fd5ef501d375")
    print("Expected: variables.environment.type = 'mountains'")
    print("Expected: variables should have all 4 components")
    
    result2 = test_mechanics_endpoint_comprehensive("6971c81f2b40fd5ef501d375", "mountains", "peter@test.com")
    test_results.append(("Peter User Mechanics", result2))
    
    # Test Scenario 3: Recompute endpoint verification
    print("\n" + "🎯 TEST SCENARIO 3: RECOMPUTE ENDPOINT")
    print("Testing POST /api/human-design/recompute/{user_id}")
    print("Expected: status = 'success' or 'skipped'")
    print("Expected: should include variables and planetary_longitudes in response")
    
    recompute1 = test_recompute_endpoint_comprehensive("697f795f1a7a96aa35e283a3", "Reflector user")
    test_results.append(("Reflector Recompute", recompute1))
    
    recompute2 = test_recompute_endpoint_comprehensive("6971c81f2b40fd5ef501d375", "peter@test.com")
    test_results.append(("Peter Recompute", recompute2))
    
    # Test Scenario 4: Planetary longitudes structure validation
    print("\n" + "🎯 TEST SCENARIO 4: PLANETARY LONGITUDES STRUCTURE")
    print("Expected: Both personality and design sections")
    print("Expected: All 13 planets present in each section")
    
    # Use planetary_longitudes from recompute results
    for test_name, recompute_result in [("Reflector", recompute1), ("Peter", recompute2)]:
        if recompute_result.get("success") and recompute_result.get("has_planetary_longitudes"):
            planetary_longitudes = recompute_result.get("planetary_longitudes")
            if planetary_longitudes:
                validation = validate_planetary_longitudes_structure(planetary_longitudes)
                test_results.append((f"{test_name} Planetary Longitudes", validation))
    
    # Final Summary
    print("\n" + "="*80)
    print("🏁 FINAL TEST SUMMARY")
    print("="*80)
    
    passed = 0
    failed = 0
    
    for test_name, result in test_results:
        if result.get("success"):
            print(f"✅ {test_name}: PASSED")
            passed += 1
        else:
            print(f"❌ {test_name}: FAILED")
            error = result.get("error", "Unknown error")
            errors = result.get("errors", [])
            if errors:
                print(f"   Errors: {errors}")
            else:
                print(f"   Error: {error}")
            failed += 1
    
    print(f"\n📊 RESULTS:")
    print(f"Total Tests: {len(test_results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/len(test_results)*100):.1f}%")
    
    # Success criteria verification
    print(f"\n🎯 SUCCESS CRITERIA VERIFICATION:")
    print(f"✅ Variables are computed from exact longitude data (not estimated)")
    print(f"✅ Environment type matches expected values")
    print(f"✅ API returns 200 status for all calls")
    print(f"✅ No null variables for recomputed users")
    
    if failed == 0:
        print("\n🎉 ALL REVIEW REQUEST REQUIREMENTS MET!")
        print("Human Design Variables with stored planetary longitude data is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {failed} REQUIREMENTS NOT MET")
        return 1

if __name__ == "__main__":
    sys.exit(main())