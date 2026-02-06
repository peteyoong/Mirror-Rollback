"""
Test auto-convergence in assessment save
"""
import asyncio
import json
import httpx

async def test_save_with_convergence():
    async with httpx.AsyncClient(base_url="http://localhost:8001") as client:
        # Simulate a v2 assessment save for pete
        payload = {
            "user_id": "697f0c6abf35c0528ff06954",
            "method": "assessment_inference_v2",
            "version": "v2",
            "inferred_core": 7,
            "inferred_wing": 8,
            "confidence": 0.4946,
            "confidence_tier": "high",
            "is_close": False,
            "top_candidates": [
                {"type": 7, "probability": 0.4946},
                {"type": 8, "probability": 0.2523},
                {"type": 3, "probability": 0.0503}
            ],
            "state_calibration": {
                "energy_state": "high",
                "life_context": "expanding",
                "answer_frame": "best_self"
            },
            "debug_scores": {
                "raw_scores": {"1": 3.0, "2": 3.0, "3": 3.33, "4": 1.67, "5": 1.67, "6": 2.33, "7": 9.0, "8": 7.33, "9": 2.0},
                "z_scores": {"1": -0.28, "2": -0.28, "3": -0.15, "4": -0.82, "5": -0.82, "6": -0.55, "7": 2.14, "8": 1.46, "9": -0.69},
                "wing_scores": {"left": 2.0, "right": 7.0, "diff": 5.0},
                "mean_likert": {"1": 2.0, "2": 2.0, "3": 3.33, "4": 1.67, "5": 1.67, "6": 2.33, "7": 5.0, "8": 4.33, "9": 2.0},
                "forced_hits": {"1": 1, "2": 1, "3": 0, "4": 0, "5": 0, "6": 0, "7": 4, "8": 3, "9": 0},
                "probabilities": {"1": 0.0441, "2": 0.0441, "3": 0.0503, "4": 0.0258, "5": 0.0258, "6": 0.0336, "7": 0.4946, "8": 0.2523, "9": 0.0294},
                "wing_access": {
                    "left_type": 6,
                    "right_type": 8,
                    "left_accessible": True,
                    "right_accessible": True,
                    "dominant_wing": 8
                }
            }
        }
        
        # Save the assessment (should auto-compute convergence)
        response = await client.post("/api/enneagram/results", json=payload)
        save_result = response.json()
        print("=== SAVE RESPONSE ===")
        print(json.dumps(save_result, indent=2))
        
        # Now fetch the saved result
        response = await client.get("/api/enneagram/results/697f0c6abf35c0528ff06954")
        get_result = response.json()
        print("\n=== GET RESULT (user-facing) ===")
        print(json.dumps(get_result, indent=2, default=str)[:2500])
        
        # Fetch with debug flag
        response = await client.get("/api/enneagram/results/697f0c6abf35c0528ff06954?debug=true")
        debug_result = response.json()
        print("\n=== GET RESULT (debug=true) - convergence object ===")
        if debug_result.get("result", {}).get("convergence"):
            print(json.dumps(debug_result["result"]["convergence"], indent=2))
        else:
            print("No convergence object found")

asyncio.run(test_save_with_convergence())
