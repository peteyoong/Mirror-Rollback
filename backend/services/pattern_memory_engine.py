"""Pattern Memory Engine V4 - Psychological Continuity

Makes Mirror feel continuous, not daily-reset.
User should feel: "You've been here before."

CORE:
1. Generate pattern_signature for each diagnosis
2. Store rolling history (30-60 days)
3. Detect repetition (NEW, RETURNING, RECURRING)
4. Inject memory language into diagnosis

NOT analytics - psychological continuity.
The win: "Damn... I really am doing this again."
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple
import hashlib
import re

logger = logging.getLogger(__name__)


# =============================================================================
# PATTERN MEMORY CLASSIFICATION
# =============================================================================

class PatternMemoryState:
    NEW_PATTERN = "new_pattern"
    RETURNING_PATTERN = "returning_pattern"  # Seen in last 7-14 days
    RECURRING_PATTERN = "recurring_pattern"  # Seen multiple times over longer window


# =============================================================================
# MEMORY LANGUAGE - Recognition phrases, not tracking
# =============================================================================

RETURNING_PHRASES = [
    "You've been here recently.",
    "This isn't the first time this has come up.",
    "You were here a few days ago.",
    "This showed up before—and it's back.",
]

RECURRING_PHRASES = [
    "You keep coming back to this.",
    "This pattern doesn't resolve because something in it hasn't changed yet.",
    "You've circled back to this more than once.",
    "This keeps surfacing. That's not random.",
    "You've been here before. More than once.",
]

CROSS_LENS_PHRASES = [
    "This is showing up in more than one place right now.",
    "Multiple parts of your chart are pointing at the same thing.",
    "This isn't just one signal—it's echoing across your system.",
]


# =============================================================================
# PATTERN SIGNATURE GENERATION
# =============================================================================

def generate_pattern_signature(
    primary_tension: str,
    lens_source: str,
    key_drivers: List[str],
    secondary_tension: Optional[str] = None
) -> str:
    """
    Generate a pattern signature for matching across days.
    
    Format: tension__source__driver1_driver2_...
    
    Example: "urgency_vs_readiness__human_design__gate35"
    """
    # Normalize tension
    tension_clean = primary_tension.lower().strip()
    tension_clean = re.sub(r'[^a-z0-9_]', '_', tension_clean)
    tension_clean = re.sub(r'_+', '_', tension_clean).strip('_')
    
    # Normalize lens source
    lens_clean = lens_source.lower().strip()
    lens_clean = re.sub(r'[^a-z0-9_]', '_', lens_clean)
    
    # Normalize drivers
    drivers_clean = []
    for driver in key_drivers[:3]:  # Max 3 drivers
        d = str(driver).lower().strip()
        d = re.sub(r'[^a-z0-9_]', '_', d)
        d = re.sub(r'_+', '_', d).strip('_')
        if d:
            drivers_clean.append(d)
    
    # Build signature
    parts = [tension_clean, lens_clean]
    if drivers_clean:
        parts.append('_'.join(drivers_clean))
    
    return '__'.join(parts)


def generate_tension_hash(primary_tension: str, secondary_tension: Optional[str] = None) -> str:
    """
    Generate a short hash for quick tension matching.
    Used for partial matches across lenses.
    """
    content = primary_tension.lower()
    if secondary_tension:
        content += f"|{secondary_tension.lower()}"
    
    return hashlib.md5(content.encode()).hexdigest()[:8]


# =============================================================================
# DATABASE OPERATIONS
# =============================================================================

async def store_pattern_memory(
    db,
    user_id: str,
    date_str: str,
    pattern_signature: str,
    tension_hash: str,
    diagnosis_title: str,
    primary_tension: str,
    lens_source: str,
    key_drivers: List[str]
):
    """Store a pattern in the user's memory history."""
    try:
        await db.pattern_memory.update_one(
            {"user_id": user_id, "date": date_str},
            {"$set": {
                "user_id": user_id,
                "date": date_str,
                "pattern_signature": pattern_signature,
                "tension_hash": tension_hash,
                "diagnosis_title": diagnosis_title,
                "primary_tension": primary_tension,
                "lens_source": lens_source,
                "key_drivers": key_drivers,
                "stored_at": datetime.now(timezone.utc).isoformat()
            }},
            upsert=True
        )
        logger.info(f"[PatternMemory] Stored pattern for {user_id[:8]}: {pattern_signature[:30]}...")
    except Exception as e:
        logger.error(f"[PatternMemory] Store error: {e}")


async def get_pattern_history(
    db,
    user_id: str,
    days: int = 60
) -> List[Dict[str, Any]]:
    """Get user's pattern history for the last N days."""
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        cutoff_str = cutoff.strftime("%Y-%m-%d")
        
        history = await db.pattern_memory.find({
            "user_id": user_id,
            "date": {"$gte": cutoff_str}
        }).sort("date", -1).to_list(days)
        
        return history
    except Exception as e:
        logger.error(f"[PatternMemory] History fetch error: {e}")
        return []


# =============================================================================
# REPETITION DETECTION
# =============================================================================

def detect_pattern_repetition(
    current_signature: str,
    current_tension_hash: str,
    history: List[Dict[str, Any]],
    today_str: str
) -> Tuple[str, Dict[str, Any]]:
    """
    Detect if the current pattern is repeating.
    
    Returns:
        (memory_state, memory_details)
    """
    # Filter out today's entry
    past_entries = [h for h in history if h.get("date") != today_str]
    
    if not past_entries:
        return PatternMemoryState.NEW_PATTERN, {"match_count": 0}
    
    # Track matches
    exact_matches = []
    partial_matches = []  # Same tension, different source
    
    for entry in past_entries:
        entry_signature = entry.get("pattern_signature", "")
        entry_tension_hash = entry.get("tension_hash", "")
        
        # Exact signature match
        if entry_signature == current_signature:
            exact_matches.append(entry)
        # Partial match (same tension across lenses)
        elif entry_tension_hash == current_tension_hash:
            partial_matches.append(entry)
    
    # Classify based on match patterns
    total_matches = len(exact_matches) + len(partial_matches)
    
    if total_matches == 0:
        return PatternMemoryState.NEW_PATTERN, {"match_count": 0}
    
    # Check recency of matches
    recent_cutoff = datetime.now(timezone.utc) - timedelta(days=14)
    recent_cutoff_str = recent_cutoff.strftime("%Y-%m-%d")
    
    recent_matches = [m for m in (exact_matches + partial_matches) 
                      if m.get("date", "") >= recent_cutoff_str]
    
    # Determine classification
    if len(exact_matches) >= 2 or total_matches >= 3:
        # Multiple occurrences - RECURRING
        memory_state = PatternMemoryState.RECURRING_PATTERN
    elif recent_matches:
        # Seen recently - RETURNING
        memory_state = PatternMemoryState.RETURNING_PATTERN
    else:
        # Old match only - treat as new
        memory_state = PatternMemoryState.NEW_PATTERN
    
    # Build details
    most_recent_match = None
    if exact_matches:
        most_recent_match = exact_matches[0]
    elif partial_matches:
        most_recent_match = partial_matches[0]
    
    details = {
        "match_count": total_matches,
        "exact_matches": len(exact_matches),
        "partial_matches": len(partial_matches),
        "most_recent_date": most_recent_match.get("date") if most_recent_match else None,
        "most_recent_title": most_recent_match.get("diagnosis_title") if most_recent_match else None,
        "recent_match_count": len(recent_matches),
    }
    
    logger.info(f"[PatternMemory] Detection result: {memory_state} (exact={len(exact_matches)}, partial={len(partial_matches)})")
    
    return memory_state, details


def detect_cross_lens_memory(
    current_tension_hash: str,
    history: List[Dict[str, Any]],
    current_lens: str,
    today_str: str
) -> Tuple[bool, Optional[str]]:
    """
    Detect if the same tension is appearing across different lenses.
    
    Returns:
        (is_cross_lens, other_lens)
    """
    # Find matches with same tension but different lens
    past_entries = [h for h in history if h.get("date") != today_str]
    
    cross_lens_matches = [
        h for h in past_entries
        if h.get("tension_hash") == current_tension_hash
        and h.get("lens_source") != current_lens
    ]
    
    if cross_lens_matches:
        other_lens = cross_lens_matches[0].get("lens_source", "another lens")
        return True, other_lens
    
    return False, None


# =============================================================================
# MEMORY LANGUAGE INJECTION
# =============================================================================

def get_memory_prefix(
    memory_state: str,
    memory_details: Dict[str, Any],
    is_cross_lens: bool = False,
    user_id: str = ""
) -> Optional[str]:
    """
    Get the memory recognition phrase to inject into diagnosis.
    
    Returns None if no memory phrase should be added.
    """
    if memory_state == PatternMemoryState.NEW_PATTERN:
        return None
    
    # Generate deterministic but varied selection
    seed = f"{user_id}:{datetime.now(timezone.utc).strftime('%Y%m%d')}"
    seed_hash = int(hashlib.md5(seed.encode()).hexdigest()[:8], 16)
    
    # Select phrase based on state
    if memory_state == PatternMemoryState.RECURRING_PATTERN:
        phrases = RECURRING_PHRASES
    else:
        phrases = RETURNING_PHRASES
    
    phrase_idx = seed_hash % len(phrases)
    prefix = phrases[phrase_idx]
    
    # Add cross-lens note if applicable
    if is_cross_lens and memory_state in [PatternMemoryState.RECURRING_PATTERN, PatternMemoryState.RETURNING_PATTERN]:
        cross_idx = seed_hash % len(CROSS_LENS_PHRASES)
        prefix += f" {CROSS_LENS_PHRASES[cross_idx]}"
    
    return prefix


def inject_memory_into_diagnosis(
    diagnosis: Dict[str, Any],
    memory_state: str,
    memory_details: Dict[str, Any],
    memory_prefix: Optional[str]
) -> Dict[str, Any]:
    """
    Inject memory language into the diagnosis.
    Modifies the diagnosis in place and returns it.
    """
    if not memory_prefix:
        # No memory to inject
        diagnosis["pattern_memory"] = {
            "state": memory_state,
            "is_new": True,
        }
        return diagnosis
    
    # Inject prefix into body
    original_body = diagnosis.get("body", "")
    if original_body:
        # Add memory line before the main body
        diagnosis["body"] = f"{memory_prefix}\n\n{original_body}"
    
    # Add memory metadata
    diagnosis["pattern_memory"] = {
        "state": memory_state,
        "is_new": False,
        "match_count": memory_details.get("match_count", 0),
        "most_recent_date": memory_details.get("most_recent_date"),
        "memory_prefix": memory_prefix,
    }
    
    return diagnosis


# =============================================================================
# MAIN MEMORY ENGINE INTERFACE
# =============================================================================

async def process_pattern_memory(
    db,
    user_id: str,
    diagnosis: Dict[str, Any],
    primary_tension: str,
    lens_source: str,
    key_drivers: List[str],
    diagnosis_title: str,
    secondary_tension: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main entry point for Pattern Memory Engine.
    
    1. Generates pattern signature
    2. Fetches history
    3. Detects repetition
    4. Injects memory language
    5. Stores current pattern
    
    Returns modified diagnosis with memory data.
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Generate signatures
    pattern_signature = generate_pattern_signature(
        primary_tension=primary_tension,
        lens_source=lens_source,
        key_drivers=key_drivers,
        secondary_tension=secondary_tension
    )
    
    tension_hash = generate_tension_hash(primary_tension, secondary_tension)
    
    # Get history
    history = await get_pattern_history(db, user_id, days=60)
    
    # Detect repetition
    memory_state, memory_details = detect_pattern_repetition(
        current_signature=pattern_signature,
        current_tension_hash=tension_hash,
        history=history,
        today_str=today
    )
    
    # Detect cross-lens memory
    is_cross_lens, other_lens = detect_cross_lens_memory(
        current_tension_hash=tension_hash,
        history=history,
        current_lens=lens_source,
        today_str=today
    )
    
    if is_cross_lens:
        memory_details["is_cross_lens"] = True
        memory_details["other_lens"] = other_lens
    
    # Get memory prefix
    memory_prefix = get_memory_prefix(
        memory_state=memory_state,
        memory_details=memory_details,
        is_cross_lens=is_cross_lens,
        user_id=user_id
    )
    
    # Inject memory into diagnosis
    diagnosis = inject_memory_into_diagnosis(
        diagnosis=diagnosis,
        memory_state=memory_state,
        memory_details=memory_details,
        memory_prefix=memory_prefix
    )
    
    # Store current pattern
    await store_pattern_memory(
        db=db,
        user_id=user_id,
        date_str=today,
        pattern_signature=pattern_signature,
        tension_hash=tension_hash,
        diagnosis_title=diagnosis_title,
        primary_tension=primary_tension,
        lens_source=lens_source,
        key_drivers=key_drivers
    )
    
    # Add signature to diagnosis for debugging
    diagnosis["debug"] = diagnosis.get("debug", {})
    diagnosis["debug"]["pattern_memory"] = {
        "signature": pattern_signature,
        "tension_hash": tension_hash,
        "memory_state": memory_state,
        "match_count": memory_details.get("match_count", 0),
        "is_cross_lens": is_cross_lens,
        "history_entries": len(history),
    }
    
    logger.info(f"[PatternMemory] Processed for {user_id[:8]}: state={memory_state}, matches={memory_details.get('match_count', 0)}")
    
    return diagnosis


# =============================================================================
# HOME OVERRIDE CHECK - For recurring patterns
# =============================================================================

async def should_override_home_with_memory(
    db,
    user_id: str
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Check if Home should be overridden with a recurring pattern.
    
    Returns:
        (should_override, recurring_pattern_info)
    """
    history = await get_pattern_history(db, user_id, days=30)
    
    if len(history) < 3:
        return False, None
    
    # Count signature occurrences
    signature_counts = {}
    for entry in history:
        sig = entry.get("pattern_signature", "")
        if sig:
            if sig not in signature_counts:
                signature_counts[sig] = []
            signature_counts[sig].append(entry)
    
    # Find recurring patterns (3+ occurrences)
    recurring_patterns = [
        (sig, entries) for sig, entries in signature_counts.items()
        if len(entries) >= 3
    ]
    
    if not recurring_patterns:
        return False, None
    
    # Get the most frequent recurring pattern
    most_frequent = max(recurring_patterns, key=lambda x: len(x[1]))
    sig, entries = most_frequent
    
    # Check if it appeared recently (last 7 days)
    recent_cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    recent_cutoff_str = recent_cutoff.strftime("%Y-%m-%d")
    
    recent_entries = [e for e in entries if e.get("date", "") >= recent_cutoff_str]
    
    if not recent_entries:
        return False, None
    
    # This is a recurring pattern that showed up recently
    most_recent = entries[0]
    
    return True, {
        "pattern_signature": sig,
        "occurrence_count": len(entries),
        "primary_tension": most_recent.get("primary_tension"),
        "diagnosis_title": most_recent.get("diagnosis_title"),
        "lens_source": most_recent.get("lens_source"),
        "most_recent_date": most_recent.get("date"),
    }


# =============================================================================
# HOME MEMORY OVERRIDE - Special Home diagnosis for recurring patterns
# =============================================================================

def generate_home_memory_override(recurring_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a special Home diagnosis that acknowledges recurring pattern.
    """
    tension = recurring_info.get("primary_tension", "this tension")
    occurrences = recurring_info.get("occurrence_count", 3)
    
    # Build recognition-focused diagnosis
    title = "You're Back Here Again"
    
    body = f"This isn't new. You've been circling this pattern—{tension.lower()}—and it keeps coming back because something hasn't shifted yet. "
    body += "That's not failure. That's the pattern asking to be seen more clearly."
    
    bridge = "The repetition isn't random. What you haven't resolved keeps returning until you do."
    
    misstep = "ignoring it because it feels familiar"
    
    better_move = "Instead of pushing past it, ask: what about this am I not yet willing to see?"
    
    return {
        "title": title,
        "body": body,
        "bridge": bridge,
        "misstep": misstep,
        "better_move": better_move,
        "pattern_memory": {
            "state": PatternMemoryState.RECURRING_PATTERN,
            "is_override": True,
            "occurrence_count": occurrences,
            "primary_tension": tension,
        },
        "debug": {
            "source": "home_memory_override",
            "recurring_info": recurring_info,
        }
    }
