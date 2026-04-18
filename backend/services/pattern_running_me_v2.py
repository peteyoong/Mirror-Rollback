"""
Pattern Running Me V2 — data contract + storage.
=================================================

Replaces the older "Share Forum Update" flow. The new flow has 4 steps:

  1. TITLE             — one-line summary, max 80 chars
  2. EMOTIONS          — pick up to 3 from a fixed vocabulary of 10
  3. STORY             — free-form, "what happened, as it happened"
  4. GUIDED REFLECTION — three prompts that appear after the user starts
                         typing the story:
                           a) "What does this say about you?"
                           b) "Why does this matter to you?"
                           c) "How is this affecting you?"

The submitted payload feeds three downstream engines:
  - Pattern Memory Engine
  - Forum Field Engine (aggregates)
  - Future Home insights

Persistence: `pattern_running_me_v2` collection.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


ALLOWED_EMOTIONS: List[str] = [
    "Frustrated",
    "Anxious",
    "Overwhelmed",
    "Pressured",
    "Avoidant",
    "Disconnected",
    "Conflicted",
    "Energized",
    "Clear",
    "Hopeful",
]


class PatternReflection(BaseModel):
    meaning: str = Field("", description="What does this say about you?")
    importance: str = Field("", description="Why does this matter to you?")
    impact: str = Field("", description="How is this affecting you?")


class PatternRunningMePayload(BaseModel):
    title: str = Field(..., min_length=1, max_length=80)
    emotions: List[str] = Field(..., min_length=1, max_length=3)
    story: str = Field(..., min_length=1, max_length=5000)
    reflection: PatternReflection = Field(default_factory=PatternReflection)
    forum_id: Optional[str] = None
    visibility: str = Field(
        "private",
        description="'private' = only visible to the author; 'forum' = visible to the forum",
    )

    @field_validator("emotions")
    @classmethod
    def _validate_emotions(cls, v: List[str]) -> List[str]:
        cleaned: List[str] = []
        seen = set()
        for e in v:
            e = (e or "").strip()
            if not e:
                continue
            # Allow case-insensitive match against the allowed vocab
            canonical = next((a for a in ALLOWED_EMOTIONS if a.lower() == e.lower()), None)
            if canonical is None:
                raise ValueError(f"Unknown emotion: {e}. Allowed: {ALLOWED_EMOTIONS}")
            if canonical in seen:
                continue
            cleaned.append(canonical)
            seen.add(canonical)
        if not cleaned:
            raise ValueError("At least one emotion is required")
        if len(cleaned) > 3:
            cleaned = cleaned[:3]
        return cleaned


def build_storage_document(
    user_id: str,
    payload: PatternRunningMePayload,
) -> Dict[str, Any]:
    """Normalise a payload into the document persisted in Mongo."""
    now = datetime.now(timezone.utc)
    return {
        "user_id": str(user_id),
        "forum_id": payload.forum_id,
        "visibility": payload.visibility,
        "title": payload.title.strip(),
        "emotions": payload.emotions,
        "story": payload.story.strip(),
        "reflection": {
            "meaning": (payload.reflection.meaning or "").strip(),
            "importance": (payload.reflection.importance or "").strip(),
            "impact": (payload.reflection.impact or "").strip(),
        },
        "created_at": now,
        "updated_at": now,
        "schema_version": "v2",
    }


def build_pattern_memory_signal(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Project the stored doc into the flat structure that Pattern Memory
    Engine consumes. Keeps the memory layer thin and decoupled.
    """
    return {
        "source": "pattern_running_me_v2",
        "user_id": doc.get("user_id"),
        "forum_id": doc.get("forum_id"),
        "summary": doc.get("title"),
        "emotions": doc.get("emotions") or [],
        "story": doc.get("story"),
        "reflection": doc.get("reflection") or {},
        "ts": doc.get("created_at"),
    }


def build_forum_field_signal(doc: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    If the entry is scoped to a forum, emit a signal for the Forum Field
    Engine aggregator. Returns None for private entries.
    """
    if not doc.get("forum_id") or doc.get("visibility") != "forum":
        return None
    return {
        "type": "pattern_update",
        "forum_id": doc["forum_id"],
        "user_id": doc["user_id"],
        "emotions": doc.get("emotions") or [],
        "title": doc.get("title"),
        "impact": (doc.get("reflection") or {}).get("impact"),
        "ts": doc.get("created_at"),
    }
