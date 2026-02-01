# Interpretation Layer v1 (Non-deterministic)

**Status:** PLANNING - NOT YET IMPLEMENTED  
**Document Created:** 2025-06  
**Depends On:** Deterministic Computation Core (mirror-deterministic-v1)

---

## Overview

The Interpretation Layer sits DOWNSTREAM of the frozen deterministic core.
It transforms raw computational facts into user-facing narratives while
preserving Project Mirror's philosophy of non-prescriptive self-reflection.

```
┌─────────────────────────────────────┐
│  DETERMINISTIC CORE (FROZEN)        │
│  mirror-deterministic-v1            │
│                                     │
│  Output: Raw facts only             │
│  - Positions, types, gates          │
│  - No meanings attached             │
└──────────────┬──────────────────────┘
               │
               │ IMMUTABLE INPUT
               ▼
┌─────────────────────────────────────┐
│  INTERPRETATION LAYER v1            │  ← THIS DOCUMENT
│  (Non-deterministic)                │
│                                     │
│  Output: User-facing narratives     │
│  - Reflective questions             │
│  - Pattern observations             │
│  - Framework-appropriate language   │
└─────────────────────────────────────┘
```

---

## Core Constraints

### 1. Immutable Input
- Deterministic output is READ-ONLY
- Never modify, reinterpret, or "correct" computed values
- If values seem wrong, fix the deterministic layer (with tests)

### 2. Tone Adaptation by Consciousness Level
- Lower levels: Grounding, concrete, present-focused
- Mid levels: Exploratory, pattern-recognition
- Higher levels: Abstract, interconnected, paradox-tolerant
- Never condescend or "spiritually bypass"

### 3. Language Guardrails
**FORBIDDEN:**
- "You ARE a [type]" → Use "Your chart shows [type]"
- "You WILL experience..." → Use "This pattern may invite..."
- "You SHOULD..." → Use "You might explore..."
- "This MEANS..." → Use "One lens sees this as..."
- Definitive predictions about relationships, career, health

**ENCOURAGED:**
- Questions that invite self-reflection
- "Some people with this pattern notice..."
- "This is one way to look at..."
- "What resonates for you?"

### 4. User Sovereignty
- User is the authority on their own experience
- Frameworks are LENSES, not TRUTH
- Always leave room for "this doesn't fit me"
- Never override user's self-knowledge with chart data

---

## Architectural Notes

### Input Contract
```python
# Interpretation layer receives:
{
    "deterministic_data": { ... },  # From frozen core
    "user_context": {
        "consciousness_indicators": [...],
        "journal_themes": [...],
        "stated_preferences": [...]
    },
    "request_type": "mirror" | "lens_exploration" | "chatbot"
}
```

### Output Contract
```python
# Interpretation layer produces:
{
    "narrative": "...",
    "tone_level": "grounding" | "exploratory" | "integrative",
    "framework_attribution": "astrology" | "human_design" | None,
    "sovereignty_reminder": True | False
}
```

### Screen-Specific Rules

| Screen | Framework Terms Allowed | Tone |
|--------|------------------------|------|
| Mirror | NO | Reflective, framework-agnostic |
| Lenses | YES (attributed) | Educational, exploratory |
| Chatbot | Context-dependent | Adaptive to user lead |

---

## Open Questions (For Future Design)

1. How to handle contradictions between frameworks?
2. Should user be able to "mute" specific frameworks?
3. How to gracefully degrade if deterministic data is missing?
4. Caching strategy for generated narratives?

---

## Implementation NOT Started

This document is for planning only.
Do not implement until:
- [ ] Deterministic core is stable (✅ done)
- [ ] Regression tests are passing (✅ done)
- [ ] Product alignment on tone guidelines
- [ ] AI prompt templates reviewed

---

*This file is part of Project Mirror's architecture documentation.*
