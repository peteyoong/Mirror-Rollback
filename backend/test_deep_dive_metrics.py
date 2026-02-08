#!/usr/bin/env python3
"""
Deep Dive Truncation Test Script
================================
Tests all deep dive endpoints and reports content metrics.
Run this script to identify truncation issues.

Usage: python test_deep_dive_metrics.py [user_id]
"""

import asyncio
import sys
import json
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

# Load environment
from dotenv import load_dotenv
load_dotenv()

mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']

# Test configuration
LENS_ENDPOINTS = [
    ("astrology", "Astrology / True Sidereal"),
    ("human_design", "Human Design"),
    ("numerology", "Numerology"),
]

# Minimum thresholds for "good" content
MIN_SECTION_WORDS = 100
MIN_SECTION_CHARS = 500
MIN_TOTAL_CHARS = 3000

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
        "fallback_used": False,
        "cached": False,
        "source": "unknown"
    }
    
    # Extract debug stamp info
    debug_stamp = data.get("debug_stamp", {})
    metrics["fallback_used"] = debug_stamp.get("fallback_used", False)
    metrics["cached"] = debug_stamp.get("cached", False)
    metrics["source"] = debug_stamp.get("source", "unknown")
    
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
            "first_50": body[:50] if body else "",
            "last_30": body[-30:] if body else ""
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
    print(f"\n{'='*60}")
    print(f"📊 {metrics['lens'].upper()} DEEP DIVE METRICS")
    print(f"{'='*60}")
    
    # Overall status
    status_emoji = "✅" if metrics["success"] else "❌"
    print(f"\nStatus: {status_emoji} {'Success' if metrics['success'] else 'Failed'}")
    print(f"Source: {metrics['source']} | Fallback: {'YES' if metrics['fallback_used'] else 'NO'} | Cached: {'YES' if metrics['cached'] else 'NO'}")
    
    # Content totals
    total_ok = metrics["total_chars"] >= MIN_TOTAL_CHARS
    print(f"\n📈 TOTALS:")
    print(f"   Sections: {metrics['sections_count']}")
    print(f"   Characters: {metrics['total_chars']:,} {'✓' if total_ok else '⚠️ LOW'}")
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
    """Test a single deep dive endpoint via direct database and cache lookup."""
    import httpx
    
    # Use httpx to call the API
    async with httpx.AsyncClient(timeout=120.0) as client:
        url = f"http://localhost:8001/api/{lens.replace('_', '-')}/deep-dive/{user_id}"
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
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Find a user with a chart
    user = await db.users.find_one({"charts": {"$exists": True}})
    if user:
        return str(user["_id"])
    
    # Fall back to any user
    user = await db.users.find_one({})
    if user:
        return str(user["_id"])
    
    return None

async def main():
    """Run all deep dive tests."""
    print("\n" + "="*60)
    print("🔍 DEEP DIVE TRUNCATION TEST")
    print("="*60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Get user ID
    if len(sys.argv) > 1:
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
        metrics = await test_deep_dive(user_id, lens_key.replace("_", "-"))
        metrics["lens"] = lens_name
        print_metrics(metrics)
        all_metrics.append(metrics)
    
    # Summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    
    total_issues = 0
    for m in all_metrics:
        issues = len(m.get("truncated_sections", [])) + len(m.get("short_sections", []))
        total_issues += issues
        status = "✅" if issues == 0 else f"⚠️ {issues} issues"
        fallback = " (FALLBACK)" if m.get("fallback_used") else ""
        print(f"   {m['lens']:<25} | {m.get('total_chars', 0):>6}c | {status}{fallback}")
    
    print(f"\nTotal issues: {total_issues}")
    
    if total_issues == 0:
        print("\n✅ ALL DEEP DIVES PASS CONTENT CHECKS!")
    else:
        print("\n⚠️  Some deep dives have content issues. Review above for details.")
    
    return all_metrics

if __name__ == "__main__":
    asyncio.run(main())
