"""
Engagement Loop Validation Script
==================================

Validates that the engagement adaptation loop is working cleanly:
1. Event quality check - duplicates, missing events, ordering
2. Adaptation trigger check - state/mode/source validation
3. Session trace review - readable session traces
4. Early impact metrics - bounce/skim/capture rates

Run: python3 /app/backend/scripts/validate_engagement_loop.py
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import os

# =============================================================================
# DATABASE CONNECTION
# =============================================================================

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")


async def get_db():
    client = AsyncIOMotorClient(MONGO_URL)
    return client[DB_NAME], client


# =============================================================================
# TASK 1: EVENT QUALITY CHECK
# =============================================================================

async def check_event_quality(db):
    print("\n" + "=" * 60)
    print("TASK 1: EVENT QUALITY CHECK")
    print("=" * 60)
    
    sessions = await db["home_engagement_sessions"].find().sort("created_at", -1).to_list(100)
    actions_doc = await db["user_recent_actions"].find().to_list(100)
    
    issues = []
    
    # Check 1: Duplicate session IDs
    session_ids = [s.get("session_id") for s in sessions]
    duplicates = [sid for sid in set(session_ids) if session_ids.count(sid) > 1]
    if duplicates:
        issues.append(f"DUPLICATE SESSION IDs: {duplicates}")
    else:
        print("[OK] No duplicate session IDs")
    
    # Check 2: Impossible durations
    for s in sessions:
        time_on_home = s.get("time_on_home", 0)
        if time_on_home < 0:
            issues.append(f"NEGATIVE DURATION: session={s.get('session_id')}, duration={time_on_home}")
        elif time_on_home > 3600:  # More than 1 hour
            issues.append(f"SUSPICIOUSLY LONG DURATION: session={s.get('session_id')}, duration={time_on_home}")
    
    if not any("DURATION" in i for i in issues):
        print("[OK] All durations within reasonable bounds")
    
    # Check 3: Missing close events (sessions without closed_from_home)
    unclosed = [s for s in sessions if not s.get("closed_from_home")]
    if unclosed:
        issues.append(f"UNCLOSED SESSIONS: {len(unclosed)}")
    else:
        print("[OK] All sessions properly closed")
    
    # Check 4: Event ordering in recent_actions
    for doc in actions_doc:
        actions = doc.get("actions", [])
        timestamps = []
        for a in actions:
            ts = a.get("timestamp")
            if ts:
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                timestamps.append(ts)
        
        # Check if timestamps are in descending order (newest first)
        if timestamps != sorted(timestamps, reverse=True):
            issues.append(f"OUT OF ORDER ACTIONS for user {doc.get('user_id', 'unknown')[:8]}")
    
    if not any("ORDER" in i for i in issues):
        print("[OK] Action timestamps in correct order")
    
    # Summary
    print(f"\nTotal sessions analyzed: {len(sessions)}")
    print(f"Total action docs: {len(actions_doc)}")
    
    if issues:
        print(f"\n[ISSUES FOUND: {len(issues)}]")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n[ALL CHECKS PASSED]")
    
    return issues


# =============================================================================
# TASK 2: ADAPTATION TRIGGER CHECK
# =============================================================================

async def check_adaptation_triggers(db):
    print("\n" + "=" * 60)
    print("TASK 2: ADAPTATION TRIGGER CHECK")
    print("=" * 60)
    
    # Get user engagement states
    states = await db["user_engagement_state"].find().to_list(100)
    actions = await db["user_recent_actions"].find().to_list(100)
    
    print(f"\nUsers with engagement state: {len(states)}")
    
    for state in states:
        user_id = state.get("user_id", "unknown")[:8]
        eng_state = state.get("last_engagement_state", "unknown")
        bounces = state.get("consecutive_bounces", 0)
        skims = state.get("consecutive_skims", 0)
        last_at = state.get("last_engagement_at")
        
        # Expected adaptation mode
        if eng_state == "bounced":
            expected_mode = "sharpen"
        elif eng_state == "skimmed":
            expected_mode = "intensify"
        elif eng_state == "captured":
            expected_mode = "deepen"
        else:
            expected_mode = "neutral"
        
        print(f"\nUser {user_id}:")
        print(f"  engagement_state: {eng_state}")
        print(f"  consecutive_bounces: {bounces}")
        print(f"  consecutive_skims: {skims}")
        print(f"  expected_adaptation_mode: {expected_mode}")
        print(f"  last_engagement_at: {last_at}")
    
    # Check recent actions
    print(f"\nUsers with recent actions: {len(actions)}")
    
    for action_doc in actions:
        user_id = action_doc.get("user_id", "unknown")[:8]
        action_list = action_doc.get("actions", [])
        action_types = [a.get("action_type") for a in action_list]
        
        # Expected first_line_source based on actions
        echo_triggering_actions = [
            "chat_no_send", "repeat_open", "lens_exit_fast", 
            "exited_quickly", "chat_sent"
        ]
        has_echo_action = any(a in echo_triggering_actions for a in action_types)
        expected_source = "echo" if has_echo_action else "snap"
        
        print(f"\nUser {user_id}:")
        print(f"  recent_action_types: {action_types}")
        print(f"  expected_first_line_source: {expected_source}")


# =============================================================================
# TASK 3: SESSION TRACE REVIEW
# =============================================================================

async def create_session_traces(db):
    print("\n" + "=" * 60)
    print("TASK 3: SESSION TRACE REVIEW")
    print("=" * 60)
    
    sessions = await db["home_engagement_sessions"].find().sort("created_at", 1).to_list(100)
    
    if not sessions:
        print("\nNo sessions to trace.")
        return
    
    # Group by user
    user_sessions = defaultdict(list)
    for s in sessions:
        user_sessions[s.get("user_id", "unknown")].append(s)
    
    print(f"\nFound {len(sessions)} sessions across {len(user_sessions)} users")
    
    trace_count = 0
    for user_id, user_sess in user_sessions.items():
        if trace_count >= 5:
            break
        
        print(f"\n{'─' * 50}")
        print(f"USER: {user_id[:8]}...")
        print(f"{'─' * 50}")
        
        prev_state = None
        for i, s in enumerate(user_sess[:10]):  # Max 10 sessions per user
            session_id = s.get("session_id", "unknown")[:20]
            time_on = s.get("time_on_home", 0)
            state = s.get("engagement_state", "unknown")
            created = s.get("created_at")
            pattern = s.get("pattern_shown", "N/A")
            snap = s.get("behavior_snap_shown", "N/A")
            
            print(f"\n  Session {i+1}: {session_id}")
            print(f"  ├─ time_on_home: {time_on:.1f}s")
            print(f"  ├─ engagement_state: {state}")
            if pattern and pattern != "N/A":
                print(f"  ├─ pattern_shown: {pattern}")
            if snap and snap != "N/A":
                print(f"  ├─ behavior_snap: {snap}")
            
            # Show adaptation expectation for next session
            if state == "bounced":
                print(f"  └─ NEXT SESSION: expect adaptation_mode=sharpen")
            elif state == "skimmed":
                print(f"  └─ NEXT SESSION: expect adaptation_mode=intensify")
            elif state == "captured":
                print(f"  └─ NEXT SESSION: expect adaptation_mode=deepen")
            
            prev_state = state
        
        trace_count += 1


# =============================================================================
# TASK 4: EARLY IMPACT METRICS
# =============================================================================

async def compute_impact_metrics(db):
    print("\n" + "=" * 60)
    print("TASK 4: EARLY IMPACT METRICS")
    print("=" * 60)
    
    sessions = await db["home_engagement_sessions"].find().to_list(1000)
    
    if not sessions:
        print("\nNo sessions for metrics.")
        return
    
    # Count engagement states
    state_counts = defaultdict(int)
    for s in sessions:
        state = s.get("engagement_state", "unknown")
        state_counts[state] += 1
    
    total = len(sessions)
    
    print(f"\n=== ENGAGEMENT STATE DISTRIBUTION ===")
    print(f"Total sessions: {total}")
    for state, count in sorted(state_counts.items()):
        pct = (count / total) * 100 if total > 0 else 0
        bar = "█" * int(pct / 5)
        print(f"  {state:12} : {count:4} ({pct:5.1f}%) {bar}")
    
    # Bounce rate
    bounce_rate = (state_counts.get("bounced", 0) / total) * 100 if total > 0 else 0
    skim_rate = (state_counts.get("skimmed", 0) / total) * 100 if total > 0 else 0
    capture_rate = (state_counts.get("captured", 0) / total) * 100 if total > 0 else 0
    
    print(f"\n=== KEY RATES ===")
    print(f"  Bounce rate:  {bounce_rate:.1f}%")
    print(f"  Skim rate:    {skim_rate:.1f}%")
    print(f"  Capture rate: {capture_rate:.1f}%")
    
    # Bounce → next session analysis
    user_sessions = defaultdict(list)
    for s in sessions:
        user_sessions[s.get("user_id", "unknown")].append(s)
    
    # Sort each user's sessions by time
    for user_id in user_sessions:
        user_sessions[user_id].sort(key=lambda x: x.get("created_at", datetime.min))
    
    bounce_to_captured = 0
    bounce_to_total = 0
    skim_to_chat = 0
    skim_to_total = 0
    
    for user_id, sess_list in user_sessions.items():
        for i in range(len(sess_list) - 1):
            curr = sess_list[i]
            next_s = sess_list[i + 1]
            
            curr_state = curr.get("engagement_state")
            next_state = next_s.get("engagement_state")
            next_chat = next_s.get("entered_chat", False)
            
            if curr_state == "bounced":
                bounce_to_total += 1
                if next_state == "captured":
                    bounce_to_captured += 1
            
            if curr_state == "skimmed":
                skim_to_total += 1
                if next_chat:
                    skim_to_chat += 1
    
    print(f"\n=== ADAPTATION IMPACT ===")
    if bounce_to_total > 0:
        bounce_capture_rate = (bounce_to_captured / bounce_to_total) * 100
        print(f"  Bounce → Captured (next session): {bounce_to_captured}/{bounce_to_total} ({bounce_capture_rate:.1f}%)")
    else:
        print(f"  Bounce → Captured: No data")
    
    if skim_to_total > 0:
        skim_chat_rate = (skim_to_chat / skim_to_total) * 100
        print(f"  Skim → Chat tap (next session): {skim_to_chat}/{skim_to_total} ({skim_chat_rate:.1f}%)")
    else:
        print(f"  Skim → Chat tap: No data")
    
    # First line source distribution
    actions_docs = await db["user_recent_actions"].find().to_list(100)
    echo_count = 0
    snap_count = 0
    
    # We can infer from action types
    for doc in actions_docs:
        actions = doc.get("actions", [])
        action_types = [a.get("action_type") for a in actions]
        
        echo_actions = ["chat_no_send", "repeat_open", "lens_exit_fast", "exited_quickly", "chat_sent"]
        if any(a in echo_actions for a in action_types):
            echo_count += 1
        else:
            snap_count += 1
    
    total_users = echo_count + snap_count
    if total_users > 0:
        print(f"\n=== FIRST LINE SOURCE (inferred) ===")
        print(f"  Echo-eligible users: {echo_count}/{total_users} ({(echo_count/total_users)*100:.1f}%)")
        print(f"  Snap-only users: {snap_count}/{total_users} ({(snap_count/total_users)*100:.1f}%)")


# =============================================================================
# MAIN
# =============================================================================

async def main():
    print("=" * 60)
    print("ENGAGEMENT LOOP VALIDATION SPRINT")
    print("=" * 60)
    print(f"Database: {DB_NAME}")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    
    db, client = await get_db()
    
    try:
        await check_event_quality(db)
        await check_adaptation_triggers(db)
        await create_session_traces(db)
        await compute_impact_metrics(db)
        
        print("\n" + "=" * 60)
        print("VALIDATION COMPLETE")
        print("=" * 60)
        
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())
