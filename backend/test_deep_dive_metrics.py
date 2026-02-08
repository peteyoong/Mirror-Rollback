#!/usr/bin/env python3
"""
Deep Dive Truncation Test Script with Enhanced Diagnostics
===========================================================
Tests all deep dive endpoints and reports detailed metrics.

Usage: 
    python test_deep_dive_metrics.py [user_id]
    python test_deep_dive_metrics.py --regression   # Run regression assertions
"""

import asyncio
import sys
import json
import os
from datetime import datetime

# Load environment
from dotenv import load_dotenv
load_dotenv()

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

# Test configuration
LENS_ENDPOINTS = [
    ("astrology", "Astrology / True Sidereal"),
    ("human-design", "Human Design"),
    ("numerology", "Numerology"),
]

# Minimum thresholds for "good" content
MIN_SECTION_WORDS = 100
MIN_SECTION_CHARS = 500
MIN_TOTAL_CHARS = {
    "astrology": 2500,
    "human-design": 4000,
    "numerology": 1500
}

def analyze_response(lens: str, data: dict) -> dict:
    """Analyze a deep dive response and return metrics."""
    metrics = {
        "lens": lens,
        "success": data.get("success", True),
        "sections_count": 0,
        "total_chars": 0,
        "total_words": 0,
        "sections": [],
        "truncated_sections": [],
        "short_sections": [],
        "debug_stamp": {}
    }
    
    # Extract debug stamp info (enhanced)
    debug_stamp = data.get("debug_stamp", {})
    metrics["debug_stamp"] = {
        "source": debug_stamp.get("source", "unknown"),
        "fallback_reason": debug_stamp.get("fallback_reason", "NONE"),
        "llm_attempted": debug_stamp.get("llm_attempted", False),
        "llm_error": debug_stamp.get("llm_error"),
        "cache_hit": debug_stamp.get("cache_hit", False),
        "fallback_used": debug_stamp.get("fallback_used", False),
        "computed_fields_present": debug_stamp.get("computed_fields_present", []),
        "computed_fields_missing": debug_stamp.get("computed_fields_missing", []),
        "section_generation_trace": debug_stamp.get("section_generation_trace", []),
    }
    
    sections = data.get("sections", [])
    metrics["sections_count"] = len(sections)
    
    for i, section in enumerate(sections):
        label = section.get("label", f"Section {i+1}")
        body = section.get("body", "")
        
        char_count = len(body)
        word_count = len(body.split())
        truncated = body.endswith("...") or body.endswith("…")
        short = word_count < MIN_SECTION_WORDS
        
        section_info = {
            "index": i + 1,
            "label": label[:40],
            "chars": char_count,
            "words": word_count,
            "truncated": truncated,
            "short": short,
        }
        
        metrics["sections"].append(section_info)
        metrics["total_chars"] += char_count
        metrics["total_words"] += word_count
        
        if truncated:
            metrics["truncated_sections"].append(label[:30])
        if short:
            metrics["short_sections"].append(label[:30])
    
    return metrics

def print_metrics(metrics: dict):
    """Print metrics in a readable format."""
    ds = metrics["debug_stamp"]
    
    print(f"\n{'='*70}")
    print(f"📊 {metrics['lens'].upper()} DEEP DIVE METRICS")
    print(f"{'='*70}")
    
    # Overall status
    status_emoji = "✅" if metrics["success"] else "❌"
    print(f"\nStatus: {status_emoji} {'Success' if metrics['success'] else 'Failed'}")
    
    # Source and diagnostics
    source = ds.get("source", "unknown")
    fallback_reason = ds.get("fallback_reason", "NONE")
    llm_attempted = ds.get("llm_attempted", False)
    
    print(f"\n🔍 DIAGNOSTICS:")
    print(f"   Source: {source}")
    print(f"   Fallback Reason: {fallback_reason}")
    print(f"   LLM Attempted: {'YES' if llm_attempted else 'NO'}")
    print(f"   Cache Hit: {'YES' if ds.get('cache_hit') else 'NO'}")
    print(f"   Fallback Used: {'YES' if ds.get('fallback_used') else 'NO'}")
    
    # LLM error if present
    llm_error = ds.get("llm_error")
    if llm_error:
        print(f"   LLM Error Type: {llm_error.get('type', 'unknown')}")
        print(f"   LLM Error Message: {llm_error.get('message', 'N/A')[:100]}")
    
    # Computed fields
    fields_present = ds.get("computed_fields_present", [])
    fields_missing = ds.get("computed_fields_missing", [])
    if fields_present:
        print(f"   Computed Fields Present: {', '.join(fields_present)}")
    if fields_missing:
        print(f"   ⚠️ Computed Fields Missing: {', '.join(fields_missing)}")
    
    # Content totals
    min_chars = MIN_TOTAL_CHARS.get(metrics['lens'].lower().replace(' / true sidereal', '').replace(' ', '-'), 2000)
    total_ok = metrics["total_chars"] >= min_chars
    print(f"\n📈 TOTALS:")
    print(f"   Sections: {metrics['sections_count']}")
    print(f"   Characters: {metrics['total_chars']:,} {'✓' if total_ok else f'⚠️ LOW (min: {min_chars})'}")
    print(f"   Words: {metrics['total_words']:,}")
    
    # Per-section breakdown
    print(f"\n📝 SECTIONS:")
    for s in metrics["sections"]:
        status = ""
        if s["truncated"]:
            status += "⛔TRUNC "
        if s["short"]:
            status += "⚠️SHORT "
        if not status:
            status = "✓"
        
        print(f"   {s['index']}. {s['label']:<40} | {s['chars']:>5}c / {s['words']:>4}w | {status}")
    
    # Section generation trace (if DEBUG_MIRROR is enabled)
    section_traces = ds.get("section_generation_trace", [])
    if section_traces:
        print(f"\n🔬 SECTION GENERATION TRACE:")
        for trace in section_traces:
            trace_status = trace.get("status", "unknown")
            trace_source = trace.get("source", "unknown")
            trace_reason = trace.get("reason")
            section_id = trace.get("section_id", "unknown")[:30]
            
            status_icon = "✓" if trace_status == "ok" else "⚠️" if trace_status == "skipped" else "❌"
            reason_str = f" ({trace_reason})" if trace_reason else ""
            print(f"   {status_icon} {section_id}: {trace_status} via {trace_source}{reason_str}")
    
    # Issues summary
    if metrics["truncated_sections"] or metrics["short_sections"]:
        print(f"\n⚠️  ISSUES DETECTED:")
        if metrics["truncated_sections"]:
            print(f"   Truncated: {', '.join(metrics['truncated_sections'])}")
        if metrics["short_sections"]:
            print(f"   Short (<{MIN_SECTION_WORDS}w): {', '.join(metrics['short_sections'])}")
    else:
        print(f"\n✅ No issues detected!")
    
    return metrics

async def test_deep_dive(user_id: str, lens: str) -> dict:
    """Test a single deep dive endpoint via HTTP."""
    import httpx
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        url = f"http://localhost:8001/api/{lens}/deep-dive/{user_id}"
        print(f"\n🔄 Testing {lens}... ({url})")
        
        try:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                return analyze_response(lens, data)
            else:
                print(f"   ❌ HTTP {response.status_code}: {response.text[:100]}")
                return {"lens": lens, "success": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:100]}")
            return {"lens": lens, "success": False, "error": str(e)[:100]}

async def find_test_user() -> str:
    """Find a user with complete data for testing."""
    from motor.motor_asyncio import AsyncIOMotorClient
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Find a user with a chart
    user = await db.users.find_one({"charts": {"$exists": True}})
    if user:
        return str(user["_id"])
    
    # Fall back to any user
    user = await db.users.find_one({})
    if user:
        return str(user["_id"])
    
    return None

def run_regression_assertions(all_metrics: list) -> dict:
    """
    Regression test assertions:
    - When LLM is configured, source should ideally be LLM (but JSON_TRUNCATED is expected)
    - Total chars should exceed minimum thresholds
    """
    results = {
        "timestamp": datetime.now().isoformat(),
        "llm_configured": bool(EMERGENT_LLM_KEY),
        "tests": [],
        "passed": 0,
        "failed": 0
    }
    
    for m in all_metrics:
        lens = m.get("lens", "unknown")
        ds = m.get("debug_stamp", {})
        
        # Test 1: LLM was attempted when configured
        llm_attempted = ds.get("llm_attempted", False)
        if EMERGENT_LLM_KEY:
            test_result = {
                "name": f"{lens}_llm_attempted",
                "passed": llm_attempted,
                "expected": "llm_attempted=True when key configured",
                "actual": f"llm_attempted={llm_attempted}"
            }
            results["tests"].append(test_result)
            if llm_attempted:
                results["passed"] += 1
            else:
                results["failed"] += 1
        
        # Test 2: Minimum character threshold met
        min_chars = MIN_TOTAL_CHARS.get(lens.lower().replace(' / true sidereal', '').replace(' ', '-'), 2000)
        total_chars = m.get("total_chars", 0)
        chars_ok = total_chars >= min_chars
        
        test_result = {
            "name": f"{lens}_min_chars",
            "passed": chars_ok,
            "expected": f"total_chars >= {min_chars}",
            "actual": f"total_chars = {total_chars}"
        }
        results["tests"].append(test_result)
        if chars_ok:
            results["passed"] += 1
        else:
            results["failed"] += 1
        
        # Test 3: Check fallback reason is documented
        source = ds.get("source", "unknown")
        fallback_reason = ds.get("fallback_reason", "unknown")
        
        if source == "FALLBACK":
            reason_documented = fallback_reason != "NONE" and fallback_reason != "unknown"
            test_result = {
                "name": f"{lens}_fallback_reason_documented",
                "passed": reason_documented,
                "expected": "fallback_reason documented when source=FALLBACK",
                "actual": f"fallback_reason={fallback_reason}"
            }
            results["tests"].append(test_result)
            if reason_documented:
                results["passed"] += 1
            else:
                results["failed"] += 1
    
    return results

async def main():
    """Run all deep dive tests."""
    is_regression = "--regression" in sys.argv
    
    print("\n" + "="*70)
    print("🔍 DEEP DIVE TRUNCATION TEST WITH DIAGNOSTICS")
    print("="*70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"LLM Key Configured: {'YES' if EMERGENT_LLM_KEY else 'NO'}")
    print(f"DEBUG_MIRROR: {os.environ.get('DEBUG_MIRROR', 'false')}")
    
    # Get user ID
    if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        user_id = sys.argv[1]
    else:
        user_id = await find_test_user()
        if not user_id:
            print("❌ No test user found in database!")
            return
    
    print(f"User ID: {user_id}")
    
    # Test each lens
    all_metrics = []
    for lens_key, lens_name in LENS_ENDPOINTS:
        metrics = await test_deep_dive(user_id, lens_key)
        metrics["lens"] = lens_name
        print_metrics(metrics)
        all_metrics.append(metrics)
    
    # Summary
    print("\n" + "="*70)
    print("📊 SUMMARY")
    print("="*70)
    
    total_issues = 0
    for m in all_metrics:
        ds = m.get("debug_stamp", {})
        issues = len(m.get("truncated_sections", [])) + len(m.get("short_sections", []))
        total_issues += issues
        
        source = ds.get("source", "?")
        fallback_reason = ds.get("fallback_reason", "")
        reason_str = f" ({fallback_reason})" if fallback_reason and fallback_reason != "NONE" else ""
        status = "✅" if issues == 0 else f"⚠️ {issues} issues"
        
        print(f"   {m['lens']:<25} | {m.get('total_chars', 0):>6}c | {source:>8}{reason_str:<20} | {status}")
    
    print(f"\nTotal issues: {total_issues}")
    
    # Run regression assertions if requested
    if is_regression:
        print("\n" + "="*70)
        print("🧪 REGRESSION TEST RESULTS")
        print("="*70)
        
        regression_results = run_regression_assertions(all_metrics)
        
        for test in regression_results["tests"]:
            icon = "✅" if test["passed"] else "❌"
            print(f"   {icon} {test['name']}: {test['actual']}")
        
        print(f"\nPassed: {regression_results['passed']} / {regression_results['passed'] + regression_results['failed']}")
        
        if regression_results["failed"] > 0:
            print("\n❌ REGRESSION TESTS FAILED")
            return 1
        else:
            print("\n✅ ALL REGRESSION TESTS PASSED")
            return 0
    
    if total_issues == 0:
        print("\n✅ ALL DEEP DIVES PASS CONTENT CHECKS!")
    else:
        print("\n⚠️  Some deep dives have content issues. Review above for details.")
    
    return all_metrics

if __name__ == "__main__":
    result = asyncio.run(main())
    if isinstance(result, int):
        sys.exit(result)
