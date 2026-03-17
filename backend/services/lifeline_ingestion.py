"""
Lifeline Ingestion Service

A proper 3-layer pipeline for lifeline data:
1. Import Source Registry - tracks uploaded files
2. Imported Candidate Moments - raw parsed events with source tracking
3. Canonical Lifeline Events - deduplicated, merged final timeline

This replaces the old direct-to-timeline approach that caused duplicates.
"""

import logging
import hashlib
import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
from collections import defaultdict
from difflib import SequenceMatcher
from bson import ObjectId

logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTS
# =============================================================================

# Duplicate detection thresholds
TITLE_SIMILARITY_THRESHOLD = 0.7  # 70% title similarity for likely match
TITLE_EXACT_THRESHOLD = 0.9       # 90% for exact match
YEAR_TOLERANCE = 1                # Allow ±1 year for duplicate detection
DESCRIPTION_OVERLAP_THRESHOLD = 0.5  # 50% description overlap

# Import statuses
IMPORT_STATUS_NEW = "new"
IMPORT_STATUS_MATCHED = "matched"
IMPORT_STATUS_DUPLICATE = "duplicate"
IMPORT_STATUS_MERGED = "merged"
IMPORT_STATUS_IGNORED = "ignored"
IMPORT_STATUS_REVIEWED = "reviewed"

# Source statuses
SOURCE_STATUS_UPLOADED = "uploaded"
SOURCE_STATUS_PARSED = "parsed"
SOURCE_STATUS_REVIEWED = "reviewed"
SOURCE_STATUS_MERGED = "merged"
SOURCE_STATUS_FAILED = "failed"

# Source types
SOURCE_TYPE_SPREADSHEET = "spreadsheet"
SOURCE_TYPE_PPTX = "pptx"
SOURCE_TYPE_MANUAL = "manual"
SOURCE_TYPE_PDF = "pdf"
SOURCE_TYPE_IMAGE = "image"
SOURCE_TYPE_CSV = "csv"

# Map file extensions to source types
EXT_TO_SOURCE_TYPE = {
    ".xlsx": SOURCE_TYPE_SPREADSHEET,
    ".xls": SOURCE_TYPE_SPREADSHEET,
    ".csv": SOURCE_TYPE_CSV,
    ".pptx": SOURCE_TYPE_PPTX,
    ".pdf": SOURCE_TYPE_PDF,
    ".jpg": SOURCE_TYPE_IMAGE,
    ".jpeg": SOURCE_TYPE_IMAGE,
    ".png": SOURCE_TYPE_IMAGE,
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def normalize_text(text: str) -> str:
    """Normalize text for comparison - lowercase, strip, collapse whitespace."""
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    # Remove common punctuation
    text = re.sub(r'[.,;:!?\-\'\"()\[\]]', '', text)
    return text


def compute_file_hash(file_bytes: bytes) -> str:
    """Compute SHA256 hash of file content for idempotency."""
    return hashlib.sha256(file_bytes).hexdigest()[:16]


def compute_dedupe_key(
    user_id: str,
    source_type: str,
    import_source_id: str,
    source_event_id: str,
    normalized_year: Optional[int],
    normalized_title: str
) -> str:
    """
    Compute a stable dedupe key for an imported moment.
    Used to prevent duplicate imports of the same source row/slide.
    """
    title_normalized = normalize_text(normalized_title)[:50]
    key_parts = [
        user_id[:12],
        source_type,
        import_source_id[:12] if import_source_id else "none",
        str(source_event_id),
        str(normalized_year) if normalized_year else "noyear",
        title_normalized
    ]
    key_string = "|".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()


def compute_canonical_dedupe_key(
    user_id: str,
    year: Optional[int],
    title: str
) -> str:
    """
    Compute a dedupe key for canonical events.
    Used to detect duplicates across different sources.
    """
    title_normalized = normalize_text(title)[:50]
    key_parts = [
        user_id[:12],
        str(year) if year else "noyear",
        title_normalized
    ]
    key_string = "|".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()


def calculate_title_similarity(title1: str, title2: str) -> float:
    """Calculate similarity ratio between two titles."""
    if not title1 or not title2:
        return 0.0
    t1 = normalize_text(title1)
    t2 = normalize_text(title2)
    if not t1 or not t2:
        return 0.0
    return SequenceMatcher(None, t1, t2).ratio()


def calculate_description_overlap(desc1: str, desc2: str) -> float:
    """Calculate overlap between two descriptions."""
    if not desc1 or not desc2:
        return 0.0
    d1 = normalize_text(desc1)
    d2 = normalize_text(desc2)
    if not d1 or not d2:
        return 0.0
    return SequenceMatcher(None, d1, d2).ratio()


def get_source_type_from_filename(filename: str) -> str:
    """Determine source type from filename extension."""
    import os
    ext = os.path.splitext(filename.lower())[1]
    return EXT_TO_SOURCE_TYPE.get(ext, SOURCE_TYPE_SPREADSHEET)


# =============================================================================
# IMPORT SOURCE REGISTRY
# =============================================================================

async def create_import_source(
    db,
    user_id: str,
    source_type: str,
    file_name: str,
    file_hash: Optional[str] = None,
    raw_event_count: int = 0
) -> Dict[str, Any]:
    """
    Create a new import source record.
    Returns the created source document.
    """
    now = datetime.now(timezone.utc)
    
    source_doc = {
        "user_id": user_id,
        "source_type": source_type,
        "file_name": file_name,
        "file_hash": file_hash,
        "uploaded_at": now,
        "imported_at": None,
        "status": SOURCE_STATUS_UPLOADED,
        "raw_event_count": raw_event_count,
        "candidate_event_count": 0,
        "canonical_match_count": 0,
        "duplicate_count": 0,
        "notes": None,
        "created_at": now,
        "updated_at": now,
    }
    
    result = await db.lifeline_import_sources.insert_one(source_doc)
    source_doc["_id"] = result.inserted_id
    source_doc["id"] = str(result.inserted_id)
    
    logger.info(f"[LifelineIngestion] Created import source: {file_name} for user {user_id[:8]}")
    return source_doc


async def get_import_source_by_hash(
    db,
    user_id: str,
    file_hash: str
) -> Optional[Dict[str, Any]]:
    """Check if a file with this hash was already imported."""
    return await db.lifeline_import_sources.find_one({
        "user_id": user_id,
        "file_hash": file_hash
    })


async def update_import_source_status(
    db,
    source_id: str,
    status: str,
    **kwargs
) -> bool:
    """Update import source status and counts."""
    update_doc = {
        "status": status,
        "updated_at": datetime.now(timezone.utc),
        **kwargs
    }
    
    result = await db.lifeline_import_sources.update_one(
        {"_id": ObjectId(source_id)},
        {"$set": update_doc}
    )
    return result.modified_count > 0


async def get_user_import_sources(
    db,
    user_id: str,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """Get all import sources for a user."""
    cursor = db.lifeline_import_sources.find({
        "user_id": user_id
    }).sort("uploaded_at", -1).limit(limit)
    
    sources = await cursor.to_list(length=limit)
    for s in sources:
        s["id"] = str(s["_id"])
    return sources


# =============================================================================
# IMPORTED CANDIDATE MOMENTS
# =============================================================================

async def store_imported_moment(
    db,
    user_id: str,
    import_source_id: str,
    source_type: str,
    source_event_id: str,
    raw_text: str,
    normalized_year: Optional[int],
    normalized_title: str,
    normalized_description: str,
    category: Optional[str] = None,
    tags: Optional[List[str]] = None,
    confidence: float = 0.5
) -> Dict[str, Any]:
    """
    Store an imported moment with idempotency.
    If a moment with the same dedupe_key exists, update it instead of creating duplicate.
    """
    now = datetime.now(timezone.utc)
    
    dedupe_key = compute_dedupe_key(
        user_id=user_id,
        source_type=source_type,
        import_source_id=import_source_id,
        source_event_id=source_event_id,
        normalized_year=normalized_year,
        normalized_title=normalized_title
    )
    
    # Check for existing moment with same dedupe key
    existing = await db.lifeline_imported_moments.find_one({
        "user_id": user_id,
        "dedupe_key": dedupe_key
    })
    
    moment_doc = {
        "user_id": user_id,
        "import_source_id": import_source_id,
        "source_type": source_type,
        "source_event_id": source_event_id,
        "raw_text": raw_text,
        "normalized_year": normalized_year,
        "normalized_date": None,  # Could be enhanced later
        "normalized_title": normalized_title,
        "normalized_description": normalized_description,
        "category": category,
        "tags": tags or [],
        "confidence": confidence,
        "dedupe_key": dedupe_key,
        "import_status": IMPORT_STATUS_NEW,
        "canonical_event_id": None,
        "updated_at": now,
    }
    
    if existing:
        # Update existing moment
        await db.lifeline_imported_moments.update_one(
            {"_id": existing["_id"]},
            {"$set": moment_doc}
        )
        moment_doc["_id"] = existing["_id"]
        moment_doc["id"] = str(existing["_id"])
        moment_doc["created_at"] = existing.get("created_at", now)
        logger.debug(f"[LifelineIngestion] Updated existing imported moment: {dedupe_key[:8]}")
    else:
        # Create new moment
        moment_doc["created_at"] = now
        result = await db.lifeline_imported_moments.insert_one(moment_doc)
        moment_doc["_id"] = result.inserted_id
        moment_doc["id"] = str(result.inserted_id)
        logger.debug(f"[LifelineIngestion] Created new imported moment: {dedupe_key[:8]}")
    
    return moment_doc


async def store_imported_moments_batch(
    db,
    user_id: str,
    import_source_id: str,
    source_type: str,
    events: List[Dict[str, Any]]
) -> Tuple[int, int]:
    """
    Store a batch of imported moments.
    Returns (created_count, updated_count).
    """
    created = 0
    updated = 0
    
    for idx, event in enumerate(events):
        source_event_id = event.get("source_event_id", f"row_{idx}")
        
        dedupe_key = compute_dedupe_key(
            user_id=user_id,
            source_type=source_type,
            import_source_id=import_source_id,
            source_event_id=str(source_event_id),
            normalized_year=event.get("year"),
            normalized_title=event.get("title", "")
        )
        
        existing = await db.lifeline_imported_moments.find_one({
            "user_id": user_id,
            "dedupe_key": dedupe_key
        })
        
        if existing:
            updated += 1
        else:
            created += 1
        
        await store_imported_moment(
            db=db,
            user_id=user_id,
            import_source_id=import_source_id,
            source_type=source_type,
            source_event_id=str(source_event_id),
            raw_text=event.get("description", event.get("title", "")),
            normalized_year=event.get("year"),
            normalized_title=event.get("title", ""),
            normalized_description=event.get("description", ""),
            category=event.get("category"),
            tags=event.get("tags", []),
            confidence=event.get("confidence", 0.5)
        )
    
    logger.info(f"[LifelineIngestion] Batch store: {created} created, {updated} updated")
    return created, updated


async def get_imported_moments_for_source(
    db,
    import_source_id: str
) -> List[Dict[str, Any]]:
    """Get all imported moments for a specific import source."""
    cursor = db.lifeline_imported_moments.find({
        "import_source_id": import_source_id
    }).sort("normalized_year", 1)
    
    moments = await cursor.to_list(length=500)
    for m in moments:
        m["id"] = str(m["_id"])
    return moments


async def get_user_imported_moments(
    db,
    user_id: str,
    status: Optional[str] = None,
    limit: int = 500
) -> List[Dict[str, Any]]:
    """Get imported moments for a user, optionally filtered by status."""
    query = {"user_id": user_id}
    if status:
        query["import_status"] = status
    
    cursor = db.lifeline_imported_moments.find(query).sort("normalized_year", 1).limit(limit)
    moments = await cursor.to_list(length=limit)
    for m in moments:
        m["id"] = str(m["_id"])
    return moments


async def update_imported_moment_status(
    db,
    moment_id: str,
    status: str,
    canonical_event_id: Optional[str] = None
) -> bool:
    """Update the status of an imported moment."""
    update_doc = {
        "import_status": status,
        "updated_at": datetime.now(timezone.utc)
    }
    if canonical_event_id:
        update_doc["canonical_event_id"] = canonical_event_id
    
    result = await db.lifeline_imported_moments.update_one(
        {"_id": ObjectId(moment_id)},
        {"$set": update_doc}
    )
    return result.modified_count > 0


# =============================================================================
# DUPLICATE DETECTION / CLUSTERING
# =============================================================================

async def find_duplicate_candidates(
    db,
    user_id: str,
    year: Optional[int],
    title: str,
    description: str = "",
    category: Optional[str] = None,
    exclude_event_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Find potential duplicate canonical events for a given moment.
    
    Returns:
    {
        "exact_match": event or None,
        "likely_matches": [events],
        "match_type": "exact" | "likely" | "none"
    }
    """
    result = {
        "exact_match": None,
        "likely_matches": [],
        "match_type": "none"
    }
    
    # Build query for potential matches
    query = {"user_id": user_id}
    
    # Add year range if we have a year
    if year:
        query["year"] = {"$gte": year - YEAR_TOLERANCE, "$lte": year + YEAR_TOLERANCE}
    
    # Fetch candidates
    cursor = db.lifeline_events.find(query).limit(100)
    candidates = await cursor.to_list(length=100)
    
    for candidate in candidates:
        if exclude_event_id and str(candidate["_id"]) == exclude_event_id:
            continue
        
        candidate_title = candidate.get("title", "")
        candidate_desc = candidate.get("description", "")
        candidate_year = candidate.get("year")
        
        # Calculate similarity scores
        title_sim = calculate_title_similarity(title, candidate_title)
        desc_sim = calculate_description_overlap(description, candidate_desc)
        
        # Same year bonus
        year_match = (year and candidate_year and year == candidate_year)
        
        # Same category bonus
        category_match = (category and candidate.get("category") == category)
        
        # Check for exact match
        if title_sim >= TITLE_EXACT_THRESHOLD:
            candidate["id"] = str(candidate["_id"])
            candidate["match_score"] = title_sim
            candidate["match_reason"] = "exact_title"
            result["exact_match"] = candidate
            result["match_type"] = "exact"
            logger.debug(f"[LifelineIngestion] Found exact match: {title_sim:.2f}")
            return result
        
        # Check for likely match
        if title_sim >= TITLE_SIMILARITY_THRESHOLD or (
            desc_sim >= DESCRIPTION_OVERLAP_THRESHOLD and year_match
        ):
            candidate["id"] = str(candidate["_id"])
            candidate["match_score"] = max(title_sim, desc_sim)
            candidate["match_reason"] = "similar_title" if title_sim >= TITLE_SIMILARITY_THRESHOLD else "similar_description"
            result["likely_matches"].append(candidate)
    
    if result["likely_matches"]:
        result["match_type"] = "likely"
        # Sort by match score
        result["likely_matches"].sort(key=lambda x: x.get("match_score", 0), reverse=True)
    
    return result


async def find_all_duplicate_candidates_for_user(
    db,
    user_id: str
) -> List[Dict[str, Any]]:
    """
    Find all potential duplicate groups in the user's canonical events.
    Used for cleanup/migration.
    """
    # Get all canonical events
    events = await db.lifeline_events.find({"user_id": user_id}).to_list(length=500)
    
    if len(events) < 2:
        return []
    
    duplicate_groups = []
    processed_ids = set()
    
    for i, event in enumerate(events):
        event_id = str(event["_id"])
        if event_id in processed_ids:
            continue
        
        group = [event]
        event["id"] = event_id
        
        for j, other in enumerate(events[i+1:], start=i+1):
            other_id = str(other["_id"])
            if other_id in processed_ids:
                continue
            
            # Check if these are duplicates
            title_sim = calculate_title_similarity(
                event.get("title", ""),
                other.get("title", "")
            )
            
            year_match = (
                event.get("year") and 
                other.get("year") and 
                abs(event["year"] - other["year"]) <= YEAR_TOLERANCE
            )
            
            if title_sim >= TITLE_SIMILARITY_THRESHOLD and year_match:
                other["id"] = other_id
                other["match_score"] = title_sim
                group.append(other)
                processed_ids.add(other_id)
        
        if len(group) > 1:
            duplicate_groups.append({
                "primary": group[0],
                "duplicates": group[1:],
                "count": len(group)
            })
            processed_ids.add(event_id)
    
    logger.info(f"[LifelineIngestion] Found {len(duplicate_groups)} duplicate groups for user {user_id[:8]}")
    return duplicate_groups


# =============================================================================
# CANONICAL MERGE PIPELINE
# =============================================================================

async def merge_moment_into_canonical(
    db,
    moment: Dict[str, Any],
    match_result: Dict[str, Any],
    user_action: str = "auto"  # "auto", "merge", "keep_separate", "ignore"
) -> Optional[str]:
    """
    Merge an imported moment into the canonical timeline.
    
    Returns the canonical_event_id if successful.
    """
    user_id = moment["user_id"]
    moment_id = str(moment["_id"])
    now = datetime.now(timezone.utc)
    
    # Handle based on match type and user action
    if match_result["match_type"] == "exact" and user_action != "keep_separate":
        # Exact match - attach to existing canonical event
        canonical_event = match_result["exact_match"]
        canonical_id = str(canonical_event["_id"])
        
        # Update canonical event with source ref
        source_ref = {
            "moment_id": moment_id,
            "import_source_id": moment.get("import_source_id"),
            "source_type": moment.get("source_type"),
            "added_at": now.isoformat()
        }
        
        await db.lifeline_events.update_one(
            {"_id": ObjectId(canonical_id)},
            {
                "$push": {"source_refs": source_ref},
                "$inc": {"source_count": 1},
                "$set": {"updated_at": now}
            }
        )
        
        # Update moment status
        await update_imported_moment_status(db, moment_id, IMPORT_STATUS_MATCHED, canonical_id)
        
        logger.info(f"[LifelineIngestion] Merged moment into existing canonical: {canonical_id[:8]}")
        return canonical_id
    
    elif match_result["match_type"] == "likely" and user_action == "merge":
        # User chose to merge with likely match
        canonical_event = match_result["likely_matches"][0]
        canonical_id = str(canonical_event["_id"])
        
        source_ref = {
            "moment_id": moment_id,
            "import_source_id": moment.get("import_source_id"),
            "source_type": moment.get("source_type"),
            "added_at": now.isoformat()
        }
        
        await db.lifeline_events.update_one(
            {"_id": ObjectId(canonical_id)},
            {
                "$push": {"source_refs": source_ref},
                "$inc": {"source_count": 1},
                "$set": {"updated_at": now}
            }
        )
        
        await update_imported_moment_status(db, moment_id, IMPORT_STATUS_MERGED, canonical_id)
        
        logger.info(f"[LifelineIngestion] User merged moment into canonical: {canonical_id[:8]}")
        return canonical_id
    
    elif user_action == "ignore":
        await update_imported_moment_status(db, moment_id, IMPORT_STATUS_IGNORED)
        return None
    
    else:
        # No match or keep_separate - create new canonical event
        canonical_doc = {
            "user_id": user_id,
            "title": moment.get("normalized_title"),
            "description": moment.get("normalized_description"),
            "year": moment.get("normalized_year"),
            "category": moment.get("category", "Other"),
            "tags": moment.get("tags", []),
            "emotional_tone": "neutral",
            "impact_score": 5,
            "source_refs": [{
                "moment_id": moment_id,
                "import_source_id": moment.get("import_source_id"),
                "source_type": moment.get("source_type"),
                "added_at": now.isoformat()
            }],
            "source_count": 1,
            "confidence": moment.get("confidence", 0.5),
            "created_at": now,
            "updated_at": now,
        }
        
        result = await db.lifeline_events.insert_one(canonical_doc)
        canonical_id = str(result.inserted_id)
        
        await update_imported_moment_status(db, moment_id, IMPORT_STATUS_MATCHED, canonical_id)
        
        logger.info(f"[LifelineIngestion] Created new canonical event: {canonical_id[:8]}")
        return canonical_id


async def process_import_source_to_canonical(
    db,
    import_source_id: str,
    auto_merge_exact: bool = True
) -> Dict[str, Any]:
    """
    Process all imported moments from a source into canonical events.
    
    Returns stats about the merge operation.
    """
    stats = {
        "total_moments": 0,
        "new_canonical": 0,
        "exact_matches": 0,
        "likely_matches": 0,
        "needs_review": 0,
        "errors": 0
    }
    
    # Get all moments for this source
    moments = await get_imported_moments_for_source(db, import_source_id)
    stats["total_moments"] = len(moments)
    
    if not moments:
        return stats
    
    user_id = moments[0]["user_id"]
    needs_review = []
    
    for moment in moments:
        try:
            # Find duplicates
            match_result = await find_duplicate_candidates(
                db=db,
                user_id=user_id,
                year=moment.get("normalized_year"),
                title=moment.get("normalized_title", ""),
                description=moment.get("normalized_description", ""),
                category=moment.get("category")
            )
            
            if match_result["match_type"] == "exact" and auto_merge_exact:
                await merge_moment_into_canonical(db, moment, match_result, "auto")
                stats["exact_matches"] += 1
            elif match_result["match_type"] == "likely":
                # Mark for review
                await update_imported_moment_status(
                    db, str(moment["_id"]), IMPORT_STATUS_DUPLICATE
                )
                needs_review.append({
                    "moment": moment,
                    "candidates": match_result["likely_matches"]
                })
                stats["likely_matches"] += 1
                stats["needs_review"] += 1
            else:
                # No match - create new canonical
                await merge_moment_into_canonical(db, moment, match_result, "keep_separate")
                stats["new_canonical"] += 1
                
        except Exception as e:
            logger.error(f"[LifelineIngestion] Error processing moment: {e}")
            stats["errors"] += 1
    
    # Update import source stats
    await update_import_source_status(
        db=db,
        source_id=import_source_id,
        status=SOURCE_STATUS_MERGED if stats["needs_review"] == 0 else SOURCE_STATUS_REVIEWED,
        imported_at=datetime.now(timezone.utc),
        candidate_event_count=stats["total_moments"],
        canonical_match_count=stats["exact_matches"] + stats["new_canonical"],
        duplicate_count=stats["likely_matches"]
    )
    
    logger.info(f"[LifelineIngestion] Processed source {import_source_id[:8]}: {stats}")
    return stats


# =============================================================================
# DUPLICATE MERGE OPERATIONS
# =============================================================================

async def merge_canonical_duplicates(
    db,
    primary_event_id: str,
    duplicate_event_ids: List[str]
) -> Dict[str, Any]:
    """
    Merge duplicate canonical events into one.
    Keeps the primary, deletes duplicates, transfers source refs.
    """
    now = datetime.now(timezone.utc)
    
    # Get primary event
    primary = await db.lifeline_events.find_one({"_id": ObjectId(primary_event_id)})
    if not primary:
        return {"success": False, "error": "Primary event not found"}
    
    # Collect all source refs from duplicates
    all_source_refs = primary.get("source_refs", [])
    total_merged = 0
    
    for dup_id in duplicate_event_ids:
        dup = await db.lifeline_events.find_one({"_id": ObjectId(dup_id)})
        if not dup:
            continue
        
        # Add source refs
        dup_refs = dup.get("source_refs", [])
        if dup_refs:
            all_source_refs.extend(dup_refs)
        else:
            # Create a source ref for the duplicate itself (legacy data)
            all_source_refs.append({
                "moment_id": None,
                "legacy_event_id": dup_id,
                "source_type": "legacy_merge",
                "added_at": now.isoformat()
            })
        
        # Update any imported moments that pointed to this duplicate
        await db.lifeline_imported_moments.update_many(
            {"canonical_event_id": dup_id},
            {"$set": {"canonical_event_id": primary_event_id}}
        )
        
        # Delete the duplicate
        await db.lifeline_events.delete_one({"_id": ObjectId(dup_id)})
        total_merged += 1
    
    # Update primary with all source refs
    await db.lifeline_events.update_one(
        {"_id": ObjectId(primary_event_id)},
        {
            "$set": {
                "source_refs": all_source_refs,
                "source_count": len(all_source_refs),
                "updated_at": now
            }
        }
    )
    
    logger.info(f"[LifelineIngestion] Merged {total_merged} duplicates into {primary_event_id[:8]}")
    
    return {
        "success": True,
        "primary_id": primary_event_id,
        "merged_count": total_merged,
        "total_sources": len(all_source_refs)
    }


# =============================================================================
# CLEANUP / MIGRATION
# =============================================================================

async def migrate_fix_existing_duplicates(
    db,
    user_id: str,
    dry_run: bool = True
) -> Dict[str, Any]:
    """
    Find and optionally fix existing duplicate canonical events.
    Use dry_run=True to preview changes.
    """
    duplicate_groups = await find_all_duplicate_candidates_for_user(db, user_id)
    
    result = {
        "duplicate_groups_found": len(duplicate_groups),
        "total_duplicates": sum(g["count"] - 1 for g in duplicate_groups),
        "groups": [],
        "dry_run": dry_run
    }
    
    for group in duplicate_groups:
        primary = group["primary"]
        duplicates = group["duplicates"]
        
        group_info = {
            "primary_id": primary["id"],
            "primary_title": primary.get("title", "")[:50],
            "primary_year": primary.get("year"),
            "duplicates": [
                {
                    "id": d["id"],
                    "title": d.get("title", "")[:50],
                    "year": d.get("year"),
                    "match_score": d.get("match_score", 0)
                }
                for d in duplicates
            ],
            "merged": False
        }
        
        if not dry_run:
            merge_result = await merge_canonical_duplicates(
                db,
                primary["id"],
                [d["id"] for d in duplicates]
            )
            group_info["merged"] = merge_result.get("success", False)
        
        result["groups"].append(group_info)
    
    logger.info(f"[LifelineIngestion] Migration for {user_id[:8]}: {result['duplicate_groups_found']} groups, dry_run={dry_run}")
    return result


async def ensure_canonical_event_has_source_fields(db, event_id: str) -> bool:
    """Ensure a canonical event has the new source tracking fields."""
    event = await db.lifeline_events.find_one({"_id": ObjectId(event_id)})
    if not event:
        return False
    
    needs_update = False
    update_doc = {}
    
    if "source_refs" not in event:
        update_doc["source_refs"] = []
        needs_update = True
    
    if "source_count" not in event:
        update_doc["source_count"] = len(event.get("source_refs", []))
        needs_update = True
    
    if "confidence" not in event:
        update_doc["confidence"] = 1.0  # Legacy events are assumed high confidence
        needs_update = True
    
    if needs_update:
        update_doc["updated_at"] = datetime.now(timezone.utc)
        await db.lifeline_events.update_one(
            {"_id": ObjectId(event_id)},
            {"$set": update_doc}
        )
    
    return needs_update


async def migrate_add_source_fields_to_all_events(
    db,
    user_id: str
) -> int:
    """Add source tracking fields to all existing canonical events."""
    events = await db.lifeline_events.find({"user_id": user_id}).to_list(length=500)
    
    updated = 0
    for event in events:
        if await ensure_canonical_event_has_source_fields(db, str(event["_id"])):
            updated += 1
    
    logger.info(f"[LifelineIngestion] Added source fields to {updated} events for {user_id[:8]}")
    return updated


# =============================================================================
# DEBUG / STATS
# =============================================================================

async def get_lifeline_ingestion_stats(
    db,
    user_id: str
) -> Dict[str, Any]:
    """Get comprehensive stats about a user's lifeline data."""
    # Count import sources
    source_count = await db.lifeline_import_sources.count_documents({"user_id": user_id})
    
    # Count imported moments by status
    moment_pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": "$import_status", "count": {"$sum": 1}}}
    ]
    moment_stats = await db.lifeline_imported_moments.aggregate(moment_pipeline).to_list(length=20)
    moment_by_status = {s["_id"]: s["count"] for s in moment_stats}
    
    # Count canonical events
    canonical_count = await db.lifeline_events.count_documents({"user_id": user_id})
    
    # Count events with source refs
    events_with_sources = await db.lifeline_events.count_documents({
        "user_id": user_id,
        "source_refs": {"$exists": True, "$ne": []}
    })
    
    # Find potential duplicates
    duplicate_groups = await find_all_duplicate_candidates_for_user(db, user_id)
    
    return {
        "import_sources": source_count,
        "imported_moments": {
            "total": sum(moment_by_status.values()),
            "by_status": moment_by_status
        },
        "canonical_events": canonical_count,
        "events_with_source_tracking": events_with_sources,
        "potential_duplicate_groups": len(duplicate_groups),
        "potential_duplicate_events": sum(g["count"] - 1 for g in duplicate_groups)
    }
