# Enneagram Deep Assessment Architecture

## Overview

A two-phase Enneagram assessment system designed to improve type and wing accuracy, especially for commonly confused pairs, while maintaining Project Mirror's reflective, non-diagnostic philosophy.

---

## 1. Assessment Structure

### Phase 1 — Short Entry Assessment (EXISTING)
- **Duration**: 8-12 minutes
- **Questions**: ~30
- **Output**: Core type hypothesis, wing (may be null), low/moderate confidence
- **Purpose**: Initial pattern recognition, surface-level type indication

### Phase 2 — Deep Enneagram Assessment (NEW)
- **Duration**: 15-20 minutes
- **Questions**: 45 questions (9 sections × 5 questions each)
- **Trigger**: Explicit opt-in after Phase 1 results
- **Purpose**: Discriminate between commonly confused types, increase confidence

---

## 2. Section Architecture

### 2.1 Section Distribution

| Section | Focus | Questions | Primary Pairs |
|---------|-------|-----------|---------------|
| 1 | Fear Response & Security | 5 | 6↔7, 6↔9 |
| 2 | Achievement & Image | 5 | 3↔7, 3↔8 |
| 3 | Withdrawal & Intensity | 5 | 4↔5, 5↔9 |
| 4 | Control & Autonomy | 5 | 8↔1, 8↔2 |
| 5 | Anxiety & Optimism | 5 | 6↔7, 7↔9 |
| 6 | Identity & Authenticity | 5 | 4↔3, 4↔9 |
| 7 | Authority & Trust | 5 | 6↔8, 1↔6 |
| 8 | Connection & Independence | 5 | 2↔9, 5↔8 |
| 9 | Stress Patterns | 5 | All types (validation) |

### 2.2 Question Type Mix Per Section

Each section contains:
- 2 Forced Choice questions
- 2 Likert Scale questions  
- 1 Ranked Preference question

**Total Mix (45 questions)**:
- 18 Forced Choice (40%)
- 18 Likert Scale (40%)
- 9 Ranked Preference (20%)

---

## 3. Type-Pair Discrimination Strategy

### 3.1 Primary Confusion Pairs (High Priority)

#### 6 ↔ 7 (Anxiety vs. Avoidance of Anxiety)
- **Core Distinction**: Sixes lean into anxiety to manage it; Sevens reframe away from it
- **Question Focus**: 
  - Response to uncertainty
  - Planning vs. spontaneity under stress
  - Relationship with worst-case thinking

#### 6 ↔ 9 (Vigilance vs. Numbing)
- **Core Distinction**: Sixes scan for threat; Nines avoid noticing threat
- **Question Focus**:
  - Conflict engagement style
  - Response to external pressure
  - Inner vs. outer focus of anxiety

#### 3 ↔ 7 (Achievement vs. Experience)
- **Core Distinction**: Threes achieve to prove worth; Sevens achieve for stimulation
- **Question Focus**:
  - Motivation for accomplishment
  - Response to failure
  - Image vs. freedom orientation

#### 4 ↔ 5 (Emotional Depth vs. Intellectual Depth)
- **Core Distinction**: Fours process through feeling; Fives process through thinking
- **Question Focus**:
  - Response to overwhelm
  - Identity relationship with emotions
  - Withdrawal motivation

#### 8 ↔ 1 (Gut Assertion vs. Gut Control)
- **Core Distinction**: Eights assert to protect; Ones control to perfect
- **Question Focus**:
  - Relationship with anger expression
  - Response to injustice
  - Need for control vs. need for correctness

### 3.2 Secondary Confusion Pairs (Medium Priority)

- 3 ↔ 8 (Power through image vs. power through force)
- 7 ↔ 9 (Active avoidance vs. passive avoidance)
- 4 ↔ 9 (Longing vs. contentment)
- 2 ↔ 9 (Merging to help vs. merging to avoid)
- 1 ↔ 6 (Internal critic vs. external authority)

---

## 4. Question Design Specifications

### 4.1 Forced Choice Format

```json
{
  "id": "deep_fc_001",
  "type": "forced_choice",
  "section": 1,
  "stem": "When facing an uncertain situation, which internal experience is more familiar?",
  "options": [
    {
      "id": "A",
      "text": "My mind runs through possible problems, preparing for what might go wrong",
      "primary_type": 6,
      "secondary_type": null,
      "weight": 1.0
    },
    {
      "id": "B",
      "text": "I focus on the possibilities and trust I'll figure it out when I get there",
      "primary_type": 7,
      "secondary_type": null,
      "weight": 1.0
    }
  ],
  "pair_focus": ["6", "7"],
  "dimension": "fear_response"
}
```

### 4.2 Likert Scale Format

```json
{
  "id": "deep_ls_001",
  "type": "likert",
  "section": 1,
  "stem": "I often find myself mentally preparing for worst-case scenarios, even when things are going well.",
  "scale": {
    "min": 1,
    "max": 5,
    "labels": ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"]
  },
  "scoring": {
    "primary_type": 6,
    "secondary_type": 1,
    "direction": "positive",
    "weight": 0.8
  },
  "pair_focus": ["6", "7"],
  "dimension": "anxiety_management"
}
```

### 4.3 Ranked Preference Format

```json
{
  "id": "deep_rp_001",
  "type": "ranked",
  "section": 1,
  "stem": "When you're stressed, rank these responses from most to least like you (1 = most like me):",
  "options": [
    {
      "id": "A",
      "text": "I seek reassurance from people I trust",
      "primary_type": 6,
      "weight_multipliers": { "rank_1": 1.0, "rank_2": 0.5, "rank_3": 0.2 }
    },
    {
      "id": "B",
      "text": "I distract myself with something enjoyable or stimulating",
      "primary_type": 7,
      "weight_multipliers": { "rank_1": 1.0, "rank_2": 0.5, "rank_3": 0.2 }
    },
    {
      "id": "C",
      "text": "I withdraw and try not to think about it",
      "primary_type": 9,
      "weight_multipliers": { "rank_1": 1.0, "rank_2": 0.5, "rank_3": 0.2 }
    }
  ],
  "pair_focus": ["6", "7", "9"],
  "dimension": "stress_response"
}
```

---

## 5. Scoring Data Model

### 5.1 Raw Response Storage

```json
{
  "assessment_id": "uuid",
  "user_id": "uuid",
  "assessment_type": "deep",
  "version": "1.0",
  "started_at": "ISO8601",
  "completed_at": "ISO8601",
  "responses": [
    {
      "question_id": "deep_fc_001",
      "question_type": "forced_choice",
      "response": "A",
      "response_time_ms": 4500,
      "section": 1
    },
    {
      "question_id": "deep_ls_001",
      "question_type": "likert",
      "response": 4,
      "response_time_ms": 3200,
      "section": 1
    },
    {
      "question_id": "deep_rp_001",
      "question_type": "ranked",
      "response": ["B", "A", "C"],
      "response_time_ms": 8100,
      "section": 1
    }
  ]
}
```

### 5.2 Scoring Output Schema

```json
{
  "assessment_id": "uuid",
  "user_id": "uuid",
  "assessment_depth": "deep",
  "computed_at": "ISO8601",
  
  "type_probabilities": {
    "1": 0.05,
    "2": 0.04,
    "3": 0.08,
    "4": 0.07,
    "5": 0.06,
    "6": 0.32,
    "7": 0.29,
    "8": 0.05,
    "9": 0.04
  },
  
  "top_types": [
    { "type": 6, "probability": 0.32 },
    { "type": 7, "probability": 0.29 }
  ],
  
  "type_discrimination": {
    "6_vs_7": {
      "leaning": 6,
      "confidence": 0.53,
      "key_differentiators": ["fear_response", "uncertainty_management"]
    },
    "6_vs_9": {
      "leaning": 6,
      "confidence": 0.71,
      "key_differentiators": ["vigilance", "conflict_engagement"]
    }
  },
  
  "confidence": {
    "tier": "moderate",
    "score": 0.58,
    "factors": {
      "response_consistency": 0.72,
      "pair_discrimination": 0.61,
      "top_type_separation": 0.03
    }
  },
  
  "wing_analysis": {
    "core_type": 6,
    "adjacent_types": [5, 7],
    "wing_scores": {
      "5": 0.41,
      "7": 0.38
    },
    "wing_state": "leaning",
    "inferred_wing": 5,
    "wing_confidence": 0.52
  },
  
  "integration_with_phase1": {
    "phase1_top_type": 7,
    "phase1_confidence": 0.45,
    "type_shift": true,
    "shift_explanation": "Deep assessment revealed stronger 6 patterns under stress scenarios"
  },
  
  "metadata": {
    "questions_answered": 45,
    "avg_response_time_ms": 4200,
    "sections_completed": 9,
    "flagged_inconsistencies": []
  }
}
```

### 5.3 Combined Result Schema (Phase 1 + Phase 2)

```json
{
  "user_id": "uuid",
  "assessment_complete": true,
  
  "final_result": {
    "inferred_core": 6,
    "inferred_wing": 5,
    "wing_state": "leaning",
    "confidence_tier": "moderate",
    "confidence_score": 0.58,
    "assessment_depth": "deep"
  },
  
  "type_probabilities": {
    "1": 0.05, "2": 0.04, "3": 0.08, "4": 0.07, "5": 0.06,
    "6": 0.32, "7": 0.29, "8": 0.05, "9": 0.04
  },
  
  "top_candidates": [
    { "type": 6, "probability": 0.32, "name": "The Loyalist" },
    { "type": 7, "probability": 0.29, "name": "The Enthusiast" }
  ],
  
  "close_call": true,
  "close_call_types": [6, 7],
  
  "display": {
    "type_label": "Type 6 — leaning toward Wing 5",
    "type_name": "The Loyalist",
    "confidence_badge": "Exploratory",
    "helper_text": "One adjacent pattern appears slightly stronger, though not yet decisive."
  },
  
  "phase_data": {
    "phase1": { /* short assessment result */ },
    "phase2": { /* deep assessment result */ }
  }
}
```

---

## 6. UX Flow Outline

### 6.1 Entry Point (After Phase 1 Results)

```
┌─────────────────────────────────────────────────┐
│                                                 │
│  Your initial pattern suggests Type 7           │
│  Confidence: Low                                │
│                                                 │
│  ─────────────────────────────────────────────  │
│                                                 │
│  📍 Want a clearer mirror?                      │
│                                                 │
│  Some patterns take time to distinguish.        │
│  A deeper exploration can help clarify          │
│  what's driving your responses.                 │
│                                                 │
│  Duration: ~15-20 minutes                       │
│  No right answers. No diagnosis.                │
│  Just clearer seeing.                           │
│                                                 │
│  ┌─────────────────────────────────────────┐   │
│  │       Explore More Deeply               │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
│           Maybe Later                           │
│                                                 │
└─────────────────────────────────────────────────┘
```

### 6.2 Deep Assessment Flow

```
[Intro Screen]
    │
    ▼
[State Calibration] (same as Phase 1)
    - Energy level
    - Life context
    - Answer frame
    │
    ▼
[Section 1: Fear & Security] ────────────────────┐
    │                                            │
    ▼                                            │
[Section 2: Achievement & Image]                 │
    │                                            │
    ▼                                            │  Progress
[Section 3: Withdrawal & Intensity]              │  indicator
    │                                            │  shows time
    ▼                                            │  remaining
[Section 4: Control & Autonomy]                  │  (not %)
    │                                            │
    ▼                                            │
[Section 5: Anxiety & Optimism]                  │
    │                                            │
    ▼                                            │
[Section 6: Identity & Authenticity]             │
    │                                            │
    ▼                                            │
[Section 7: Authority & Trust]                   │
    │                                            │
    ▼                                            │
[Section 8: Connection & Independence]           │
    │                                            │
    ▼                                            │
[Section 9: Stress Patterns]─────────────────────┘
    │
    ▼
[Processing Screen]
    "Integrating your responses..."
    │
    ▼
[Combined Results Screen]
    - Updated type probabilities
    - Refined wing inference
    - New confidence level
    - Comparison with Phase 1
```

### 6.3 Progress Indicator Design

```
┌─────────────────────────────────────────────────┐
│                                                 │
│  Section 3 of 9                                 │
│  ━━━━━━━━━●━━━━━━━━━━━━━━━━━━━━━━━━━━━━━       │
│                                                 │
│  About 12 minutes remaining                     │
│                                                 │
└─────────────────────────────────────────────────┘
```

### 6.4 Section Transition Language

Between sections, brief grounding text:

- "These next questions explore how you respond when things feel uncertain."
- "Now we'll look at patterns around achievement and recognition."
- "The following questions explore your relationship with intensity and withdrawal."

---

## 7. Philosophy Guardrails

### 7.1 Language Rules (MANDATORY)

**Never use:**
- "You are a Type X"
- "This proves..."
- "Your personality is..."
- "You should..."

**Always use:**
- "Based on this deeper exploration..."
- "The patterns suggest..."
- "You may notice..."
- "This lens offers..."

### 7.2 Result Framing Examples

**High Confidence:**
> "Based on this deeper exploration, Type 6 patterns appear most active in your responses. The Loyalist lens may offer useful insight into your relationship with security and trust."

**Moderate Confidence:**
> "Your responses show a close interplay between Type 6 and Type 7 patterns. Both lenses may offer relevant insight—many people find elements of each that resonate."

**Low Confidence:**
> "The patterns in your responses remain fluid. This isn't unusual—type clarity often emerges through lived experience rather than assessment alone."

### 7.3 Close-Call Handling

When top two types are within 5% probability:
- Present both types as valid lenses
- Offer brief description of what distinguishes them
- Invite ongoing self-observation rather than forcing a choice

---

## 8. Technical Implementation Notes

### 8.1 Database Collections

```
enneagram_deep_assessments
├── assessment_id (PK)
├── user_id (FK)
├── version
├── started_at
├── completed_at
├── responses[]
├── scoring_result
└── metadata

enneagram_combined_results
├── user_id (PK)
├── phase1_result
├── phase2_result
├── final_result
├── computed_at
└── display_config
```

### 8.2 API Endpoints (Proposed)

```
POST /api/enneagram/deep/start
  - Initializes deep assessment session
  - Returns first section questions

POST /api/enneagram/deep/respond
  - Submits response for a question
  - Returns next question or section transition

POST /api/enneagram/deep/complete
  - Finalizes assessment
  - Triggers scoring
  - Returns combined result

GET /api/enneagram/result/{user_id}
  - Returns combined result (Phase 1 + Phase 2 if available)
```

### 8.3 Frontend State Management

```typescript
interface DeepAssessmentState {
  session_id: string;
  current_section: number;
  current_question: number;
  responses: DeepAssessmentResponse[];
  started_at: string;
  estimated_time_remaining: number;
  section_intros_shown: number[];
}
```

---

## 9. Implementation Phases

### Phase A: Data Model & Questions (This Prompt)
- [x] Architecture document
- [x] JSON schemas
- [ ] Question bank (45 questions)

### Phase B: Backend Implementation
- [ ] Database models
- [ ] Scoring algorithm (placeholder weights)
- [ ] API endpoints

### Phase C: Frontend Implementation  
- [ ] Deep assessment screens
- [ ] Progress indicator
- [ ] Results integration

### Phase D: Scoring Refinement
- [ ] Weight tuning based on test data
- [ ] Validation against known types
- [ ] Confidence calibration

---

## Appendix A: Question Bank Structure

See `/app/frontend/data/deep_assessment_questions.json` for full question bank.

## Appendix B: Scoring Weight Placeholders

See `/app/backend/enneagram_deep_scoring.py` for scoring implementation (weights TBD).
