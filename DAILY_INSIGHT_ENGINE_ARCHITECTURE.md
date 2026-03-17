# Daily Insight Engine - Architecture Plan

## Document Status
**Version:** 1.0  
**Author:** E1 Agent  
**Created:** 2026-03-17  
**Status:** AWAITING APPROVAL

---

## 1. CURRENT STATE ANALYSIS

### A. How Home Screen Insights Are Currently Generated

The current home screen insight system uses a **Daily Keystone** architecture:

**Endpoint:** `GET /api/mirror/home/{user_id}`

**Current Flow:**
```
User Request → Template Selection → Deterministic Keystone → Optional Enrichments → Response
```

**Key Functions (in `/app/backend/server.py`):**

| Function | Lines | Purpose |
|----------|-------|---------|
| `generate_deterministic_keystone()` | 7427-7520 | Selects template based on HD type or astrology element |
| `generate_personal_echo()` | 5905-6010 | Matches lifeline events to pattern themes |
| `generate_cause_layer()` | 6107-6300 | Cross-lens synthesis (BaZi, patterns, lifeline) |
| `generate_decision_replay()` | 6941-7100 | Historical pattern recurrence |
| `detect_pattern_phase()` | 6575-6700 | Lifecycle phase detection |
| `generate_decision_awareness()` | 7100-7200 | Decision style prompt |

**Current Template Selection Logic:**
1. If user has Human Design → use type-based template (generator, projector, manifestor, reflector)
2. Else if user has astrology → use element-based template (fire, earth, air, water)
3. Else → default template

**Current Output Structure:**
```json
{
  "date": "2026-03-17",
  "title": "The Familiar Pull",
  "keystone": "There may be a tension between...",
  "reflect_question": "What are you almost ready to do?",
  "micro_affirmation": "Hesitation isn't always fear...",
  "personal_echo": "Your Lifeline shows career transitions in 2018, 2021...",
  "cause_layer": "This pattern may connect to your BaZi Wood element...",
  "decision_replay": "A similar moment appeared in 2019...",
  "pattern_phase_line": "Phase 3 of 5: Integration",
  "decision_awareness_prompt": "Your style tends toward..."
}
```

**Problems with Current System:**
1. ❌ Template-driven, not signal-driven - same person gets same type of insight regardless of today's state
2. ❌ No weighting of lived signals vs framework signals
3. ❌ Enrichments are additive layers, not synthesized into one insight
4. ❌ No detection of which pattern is most relevant TODAY
5. ❌ Multiple unrelated outputs instead of ONE coherent insight

---

### B. What Signals Are Currently Available

#### Signal Sources in Codebase:

| Signal Type | File Location | Weight | Status |
|-------------|---------------|--------|--------|
| **LIVED-STATE SIGNALS** ||||
| Journal Entries | `db.journal` | 3 | ✅ Active |
| Mirror Chat (saved insights) | `db.mirror_insights` | 2 | ✅ Active |
| Lunar Reflections | `db.lunar_journal` | 2 | ✅ Active |
| **REPEATING PATTERN SIGNALS** ||||
| Lifeline Events | `db.lifeline_events` | 3 | ✅ Active |
| **TIMING SIGNALS** ||||
| Lunar Cycle | `services/lunar_cycle.py` | 1 | ✅ Active |
| Planetary Transits | `services/pattern_graph.py` | 0.5 | ✅ Active |
| **BASE PATTERN SIGNALS** ||||
| Human Design (type, centers, gates) | `db.charts.human_design` | 1 | ✅ Active |
| Gene Keys | `db.charts.gene_keys` | 1 | ✅ Active |
| Enneagram | `db.enneagram_results` | 1 | ✅ Active |
| Numerology | `calculations/numerology.py` | 1 | ✅ Active |
| Astrology (natal) | `db.charts.astrology` | 1 | ✅ Active |
| BaZi | `db.charts.bazi` | 1 | ✅ Active |

#### Current Aggregation (pattern_graph.py):

The `aggregate_pattern_graph()` function (lines 1869-2132) already:
- Aggregates signals from all sources
- Maps them to 7 pattern domains
- Calculates weighted scores
- Detects tensions between domains

**Current 7 Domains (PATTERN_CATEGORIES):**
1. `energy_vitality` - Energy & Vitality
2. `emotional_landscape` - Emotional Landscape
3. `identity_direction` - Identity & Direction
4. `mind_meaning` - Mind & Meaning
5. `expression_action` - Expression & Action
6. `relationships_boundaries` - Relationships & Boundaries
7. `growth_transformation` - Growth & Transformation

**Current Signal Weights (pattern_graph.py:24-34):**
```python
SIGNAL_WEIGHTS = {
    "lifeline": 3,              # Highest - direct life experience
    "journal": 3,               # Highest - direct user reflection
    "mirror_chat": 2,           # High - user-initiated conversation
    "gene_keys": 1,             # Framework-based
    "human_design_centers": 1,  # Framework-based
    "human_design_gates": 1,    # Framework-based
    "human_design": 1,          # Legacy source name
    "enneagram": 1,             # Framework-based - invisible contributor
    "astrology_transit": 0.5,   # Timing layer - amplifies existing patterns only
}
```

---

## 2. PROPOSED ARCHITECTURE

### 3-Layer Design Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          LAYER 1: SIGNAL INPUTS                         │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │
│  │ Lived-State  │ │   Timing     │ │    Base      │ │  Repeating   │    │
│  │   Signals    │ │   Signals    │ │   Patterns   │ │   Patterns   │    │
│  │  (weight:3)  │ │ (weight:1.5) │ │ (weight:1.5) │ │ (weight:2.5) │    │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    LAYER 2: PATTERN AGGREGATION ENGINE                  │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ 1. Normalize signals → 7 domains                                  │   │
│  │ 2. Score each domain (weighted by source)                        │   │
│  │ 3. Detect tensions between domains                               │   │
│  │ 4. Check for recurrence (lifeline historical match)              │   │
│  │ 5. Apply Reflector lunar boost (if applicable)                   │   │
│  │ 6. SELECT PRIMARY PATTERN (one, not many)                        │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     LAYER 3: INTERPRETATION LAYER                       │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ Pattern → Structured Insight:                                     │   │
│  │   • title (pattern name)                                         │   │
│  │   • what_happening (descriptive, present-tense)                  │   │
│  │   • why_feels (emotional grounding)                              │   │
│  │   • watch_for (behavioral flag)                                  │   │
│  │   • better_move (non-prescriptive suggestion)                    │   │
│  │   • interrupt (anti-pattern awareness)                           │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### LAYER 1: Signal Inputs (Detailed)

#### A. Lived-State Signals (HIGHEST WEIGHT: 3.0)
**Source:** Real user activity in last 7-30 days

| Signal Source | Collection | How to Extract | Domain Mapping |
|---------------|------------|----------------|----------------|
| Journal Entries | `db.journal` | Keyword matching + `source_domain` metadata | Direct domain mapping or NLP keywords |
| Mirror Chat Insights | `db.mirror_insights` | `domains` field (explicit) | Direct domain mapping |
| Lunar Reflections | `db.lunar_journal` | Content keywords | Domain keywords |

**Extraction Function:** `aggregate_journal_signals()` (pattern_graph.py:541-624)  
**Extraction Function:** `aggregate_mirror_chat_signals()` (pattern_graph.py:1320-1383)

#### B. Timing Signals (WEIGHT: 1.5)
**Source:** Current planetary/lunar positions

| Signal Source | File | How to Extract |
|---------------|------|----------------|
| Lunar Cycle Phase | `services/lunar_cycle.py` | `calculate_lunar_cycle_info()` |
| Moon Gate (for Reflectors) | `services/lunar_cycle.py` | `get_current_moon_gate()` |
| Planetary Transits | `pattern_graph.py` | `calculate_current_planetary_positions()` + `map_transits_to_domains()` |

**Timing signals AMPLIFY existing patterns, they don't create new ones.**

#### C. Base Pattern Signals (WEIGHT: 1.5)
**Source:** User's computed frameworks (static or slow-changing)

| Signal Source | Collection/Function | Domain Mapping |
|---------------|---------------------|----------------|
| Human Design Type | `charts.human_design.type` | Type-specific behavior tendencies |
| Human Design Centers | `charts.human_design.centers` | `HD_CENTER_CATEGORY_MAP` |
| Human Design Gates | `charts.human_design.gates` | `HD_GATE_CATEGORY_MAP` |
| Gene Keys | `charts.gene_keys.all_spheres` | `GENE_KEY_CATEGORY_MAP` |
| Enneagram | `enneagram_results.inferred_core` | `ENNEAGRAM_DOMAIN_MAPPING` |
| Numerology | `users.numerology_full_name` / birth_date | Life Path, Personal Year/Month |
| BaZi | `charts.bazi.day_master_element` | `ELEMENT_DOMAIN_MAP` |

#### D. Repeating Pattern Signals (WEIGHT: 2.5)
**Source:** Historical life patterns

| Signal Source | Collection | How to Extract |
|---------------|------------|----------------|
| Lifeline Events | `db.lifeline_events` | `aggregate_lifeline_signals()` |
| Category Recurrence | Count events by category | Flag if ≥3 events in same category |
| Temporal Clusters | Events grouped by decade | Flag if ≥3 events in same decade |
| High-Impact Events | `impact_score >= 7` | Include in recurrence detection |

---

### LAYER 2: Pattern Aggregation Engine

#### Domain Model (7 Unified Domains)
Using existing `PATTERN_CATEGORIES` from pattern_graph.py:

| Domain ID | Display Name | What It Tracks |
|-----------|--------------|----------------|
| `energy_vitality` | Action / Momentum | Pacing, burnout, vitality, drive |
| `emotional_landscape` | Emotional Landscape | Feelings, waves, mood states |
| `identity_direction` | Identity / Expression | Self-concept, direction, becoming |
| `mind_meaning` | Clarity / Decision | Thinking, confusion, sense-making |
| `expression_action` | Expression & Action | Voice, communication, creative output |
| `relationships_boundaries` | Relationship / Boundaries | Connection, limits, intimacy |
| `growth_transformation` | Stability / Safety + Growth | Security, change, transition |

#### Scoring System

**Phase 1 Weights (updated from current):**
```python
INSIGHT_SIGNAL_WEIGHTS = {
    # Lived-State (highest - reality anchor)
    "journal": 3.0,
    "mirror_chat": 3.0,
    "lunar_reflection": 2.5,
    
    # Repeating Patterns (high - historical validation)
    "lifeline": 2.5,
    "lifeline_recurrence": 3.0,  # Bonus for repeated category
    
    # Timing (medium - amplification layer)
    "lunar_cycle": 1.5,
    "transit": 1.0,
    
    # Base Patterns (medium - structural constraint)
    "human_design": 1.5,
    "gene_keys": 1.0,
    "enneagram": 1.0,
    "numerology": 1.0,
    "bazi": 1.0,
}
```

#### Tension Detection
Reuse existing `detect_pattern_tensions()` from pattern_graph.py (lines 2135-2184).

Returns tensions like:
- "energy_vitality vs relationships_boundaries" → "Tension between energy and connection"
- "expression_action vs emotional_landscape" → "Tension between what you're feeling and expressing"

#### Recurrence Detection
**New function needed:** `detect_pattern_recurrence()`

```python
def detect_pattern_recurrence(
    primary_domain: str,
    lifeline_events: List[dict],
    historical_tensions: List[dict]  # from past daily insights
) -> Optional[dict]:
    """
    Check if today's pattern matches historical patterns.
    
    Returns:
        {
            "is_recurring": bool,
            "recurrence_count": int,
            "matching_years": List[int],
            "matching_events": List[str],
            "confidence": float
        }
    """
```

#### Reflector-Specific Logic
**Condition:** If `human_design.type == "Reflector"`

**Adjustments:**
1. Boost `lunar_cycle` weight from 1.5 → 3.0
2. Include Moon Gate as additional signal
3. Add lunar phase context to interpretation
4. Do NOT produce fluffy "Reflector special" language

---

### LAYER 3: Interpretation Layer

#### Pattern → Insight Mapping

Create a library of **pattern templates** that map to interpretations:

**Example Pattern Library:**
```python
PATTERN_TEMPLATES = {
    "high_drive_low_signal": {
        "trigger": {
            "primary_domain": "expression_action",
            "primary_score": ">= 5",
            "secondary_domain": "mind_meaning",
            "secondary_score": "<= 3",
            "tension": True
        },
        "title": "High Drive, Low Signal",
        "what_happening": "You're ready to move, but the direction isn't clear yet.",
        "why_feels": "The energy is there. The clarity isn't keeping pace.",
        "watch_for": "Starting things to escape the discomfort of not knowing.",
        "better_move": "Name what you're waiting to understand before acting.",
        "interrupt": "If you catch yourself doing busy work—pause and ask what you're avoiding."
    },
    "fast_start_delayed_feedback": {
        "trigger": {
            "primary_domain": "expression_action",
            "timing_signal": "mars_transit",
            "tension_with": "relationships_boundaries"
        },
        "title": "Fast Start, Delayed Feedback",
        "what_happening": "You're moving quickly. Others aren't responding at the same speed.",
        "why_feels": "Your pace is natural for you. It may feel frustrating waiting for others to catch up.",
        "watch_for": "Interpreting silence as rejection.",
        "better_move": "Give it one more day before following up.",
        "interrupt": "If you're refreshing your inbox repeatedly—walk away for an hour."
    },
    "emotional_noise_low_clarity": {
        "trigger": {
            "primary_domain": "emotional_landscape",
            "primary_score": ">= 6",
            "secondary_domain": "mind_meaning",
            "secondary_score": "<= 2"
        },
        "title": "Emotional Noise, Low Clarity",
        "what_happening": "Feelings are running high. Thinking isn't keeping pace.",
        "why_feels": "You're processing something that doesn't have words yet.",
        "watch_for": "Making decisions while the wave is still moving.",
        "better_move": "Let feelings pass before deciding anything permanent.",
        "interrupt": "If someone asks 'what's wrong' and you snap—that's the signal to pause."
    },
    "pattern_returning_control": {
        "trigger": {
            "recurrence": True,
            "recurrence_theme": "control"
        },
        "title": "Pattern Returning: Control Under Pressure",
        "what_happening": "A familiar response is showing up again. You've been here before.",
        "why_feels": "When things feel uncertain, control feels like the only option.",
        "watch_for": "Tightening your grip on things you can't actually control.",
        "better_move": "Name what you're actually afraid of losing.",
        "interrupt": "If you catch yourself micromanaging—that's the pattern talking."
    }
}
```

#### Tone Rules (Non-Negotiable)
1. **No astrology/mystical language** - No "Mars is pushing you" or "the Moon invites"
2. **No prescriptive advice** - No "you should" or "you need to"
3. **Direct, behavioral language** - Observable, present-tense
4. **Mirror voice** - Reflective, grounded, warm
5. **One insight, not multiple** - Choose the strongest signal

---

## 3. DATA FLOW (End-to-End)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API REQUEST                                     │
│                    GET /api/daily-insight/{user_id}                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          LAYER 1: COLLECT SIGNALS                           │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. Fetch lived-state signals:                                               │
│    • db.journal.find({user_id}, last 30 days)                              │
│    • db.mirror_insights.find({user_id}, last 30 days)                      │
│    • db.lunar_journal.find({user_id}, last 30 days)                        │
│                                                                             │
│ 2. Fetch timing signals:                                                    │
│    • calculate_lunar_cycle_info()                                          │
│    • calculate_current_planetary_positions()                                │
│    • if Reflector: get_current_moon_gate()                                 │
│                                                                             │
│ 3. Fetch base pattern signals:                                              │
│    • db.charts.find_one({user_id}) → HD, Gene Keys, BaZi, Astrology        │
│    • db.enneagram_results.find_one({user_id})                              │
│    • get_numerology_cycles(user)                                           │
│                                                                             │
│ 4. Fetch repeating pattern signals:                                         │
│    • db.lifeline_events.find({user_id})                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LAYER 2: AGGREGATE & SCORE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. Normalize all signals → 7 domains                                        │
│    • Use existing aggregate_*_signals() functions                          │
│                                                                             │
│ 2. Calculate domain scores (weighted):                                      │
│    domain_scores = {                                                        │
│      "energy_vitality": 4.5,                                               │
│      "expression_action": 7.2,  ← PRIMARY (highest)                        │
│      "mind_meaning": 2.1,                                                  │
│      ...                                                                   │
│    }                                                                        │
│                                                                             │
│ 3. Detect tension:                                                          │
│    primary_tension = detect_pattern_tensions(categories)[0]                 │
│    → "expression_action vs mind_meaning"                                   │
│                                                                             │
│ 4. Check recurrence:                                                        │
│    recurrence = detect_pattern_recurrence(primary_domain, lifeline)         │
│    → {is_recurring: true, matching_years: [2018, 2021]}                    │
│                                                                             │
│ 5. Apply Reflector boost (if applicable):                                   │
│    if is_reflector: boost lunar_cycle weight                               │
│                                                                             │
│ 6. SELECT PRIMARY PATTERN:                                                  │
│    primary_pattern = {                                                      │
│      domain: "expression_action",                                          │
│      score: 7.2,                                                           │
│      tension: "expression_action vs mind_meaning",                         │
│      recurrence: {is_recurring: true, years: [2018, 2021]},                │
│      signal_sources: ["journal", "transit", "human_design"],               │
│      confidence: "medium"                                                  │
│    }                                                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LAYER 3: INTERPRET → STRUCTURED OUTPUT                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. Match pattern → template:                                                │
│    template = match_pattern_to_template(primary_pattern)                    │
│    → "high_drive_low_signal" or "pattern_returning_control"                │
│                                                                             │
│ 2. Personalize template with user context:                                  │
│    • Inject recurrence years                                               │
│    • Adjust language based on confidence                                   │
│    • Add Reflector lunar context if applicable                             │
│                                                                             │
│ 3. Generate structured insight:                                             │
│    {                                                                        │
│      "title": "High Drive, Low Signal",                                    │
│      "what_happening": "...",                                              │
│      "why_feels": "...",                                                   │
│      "watch_for": "...",                                                   │
│      "better_move": "...",                                                 │
│      "interrupt": "..."                                                    │
│    }                                                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API RESPONSE                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│ {                                                                           │
│   "pattern_id": "high_drive_low_signal_20260317",                          │
│   "title": "High Drive, Low Signal",                                        │
│   "primary_domain": "expression_action",                                    │
│   "secondary_domain": "mind_meaning",                                       │
│   "tension": "expression_action vs mind_meaning",                           │
│   "confidence": "medium",                                                   │
│   "signal_sources": ["journal", "transit", "human_design"],                │
│   "what_happening": "You're ready to move, but the direction isn't clear.", │
│   "why_feels": "The energy is there. The clarity isn't keeping pace.",      │
│   "watch_for": "Starting things to escape the discomfort of not knowing.",  │
│   "better_move": "Name what you're waiting to understand before acting.",   │
│   "interrupt": "If busy work starts—pause and ask what you're avoiding.",   │
│   "debug": {                                                                │
│     "source_scores": {                                                      │
│       "journal": 4.5, "human_design": 1.5, "transit": 1.2                  │
│     },                                                                      │
│     "domain_scores": {                                                      │
│       "expression_action": 7.2, "mind_meaning": 2.1, ...                   │
│     },                                                                      │
│     "recurrence_matches": [{"year": 2018, "event": "Career pivot"}],        │
│     "selected_reason": "expression_action highest (7.2) with tension"       │
│   }                                                                         │
│ }                                                                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND RENDER                                    │
│                      <HomeInsightCard insight={...} />                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. MINIMAL VIABLE IMPLEMENTATION (Phased)

### Phase 1: MVP (This Implementation)
**Goal:** Replace current template-driven keystone with signal-driven daily insight

**What we build:**
1. ✅ New file: `/app/backend/services/home_insight_engine.py`
   - `collect_all_signals()` - gathers from existing sources
   - `score_domains()` - weighted scoring
   - `select_primary_pattern()` - choose one pattern
   - `generate_daily_insight()` - main orchestrator

2. ✅ New file: `/app/backend/services/interpretation_engine.py`
   - `PATTERN_TEMPLATES` - library of ~10-15 pattern templates
   - `match_pattern_to_template()` - matching logic
   - `generate_structured_insight()` - template → output

3. ✅ New endpoint: `GET /api/daily-insight/{user_id}` in server.py

4. ✅ New frontend: `/app/frontend/components/HomeInsightCard.tsx`
   - Display new structured insight format
   - Replace current keystone display

**What we DON'T build in Phase 1:**
- ❌ LLM-based interpretation (use templates)
- ❌ New NLP for journal parsing (use existing keyword matching)
- ❌ Historical tension tracking
- ❌ Complex recurrence scoring

### Phase 2: Enhanced Signals
**Goal:** Improve signal extraction quality

**What we add:**
- Better journal content analysis (beyond keywords)
- Mirror chat content parsing (beyond saved insights)
- Historical tension tracking (db storage)
- Recurrence confidence scoring refinement

### Phase 3: Advanced Features
**Goal:** Full production polish

**What we add:**
- Reflector-specific lunar weighting
- Cross-lens synthesis integration
- LLM fallback for edge cases
- Caching layer for performance

---

## 5. DEBUG / TRANSPARENCY

### Debug Payload Structure
```python
{
    "debug": {
        # What signals contributed
        "signal_counts": {
            "journal": 3,
            "mirror_chat": 1,
            "lifeline": 5,
            "human_design": 2,
            "transit": 1
        },
        
        # Raw scores per domain
        "domain_scores": {
            "expression_action": 7.2,
            "mind_meaning": 2.1,
            "emotional_landscape": 3.5,
            "energy_vitality": 4.0,
            "relationships_boundaries": 1.8,
            "identity_direction": 2.9,
            "growth_transformation": 3.2
        },
        
        # Source breakdown for primary domain
        "source_scores": {
            "journal": 4.5,
            "human_design": 1.5,
            "transit": 1.2
        },
        
        # Recurrence data
        "recurrence_matches": [
            {"year": 2018, "event": "Career pivot", "category": "Career"},
            {"year": 2021, "event": "New role", "category": "Career"}
        ],
        
        # Why this pattern was selected
        "selected_reason": "expression_action highest score (7.2) with active tension against mind_meaning (2.1)",
        
        # Template used
        "template_matched": "high_drive_low_signal",
        
        # Confidence factors
        "confidence_factors": {
            "lived_signal_presence": true,
            "signal_source_diversity": 3,
            "recurrence_detected": true,
            "tension_detected": true
        },
        
        # Reflector-specific (if applicable)
        "reflector_context": {
            "lunar_phase": "Waxing Gibbous",
            "lunar_day": 12.3,
            "moon_gate": 35,
            "lunar_weight_boost": true
        }
    }
}
```

---

## 6. EDGE CASES

### A. No Journal Data
**Condition:** User has never journaled

**Handling:**
1. Fall back to lifeline + framework signals
2. Reduce confidence to "low"
3. Use broader pattern templates (less behavioral specificity)
4. Add gentle prompt: "Journaling helps Mirror understand you better"

### B. Weak Signal Day
**Condition:** All domain scores < 3.0

**Handling:**
1. Use "neutral day" template
2. Title: "A Quiet Signal Day"
3. Focus on observational mode: "Nothing strong is pulling today. That can be information too."
4. Avoid forcing a pattern that isn't there

### C. Conflicting Signals
**Condition:** Multiple domains have similar high scores (e.g., 6.8, 6.5, 6.2)

**Handling:**
1. Check for tension between top 2 domains
2. If tension exists → tension-based template
3. If no tension → use highest by small margin
4. Note in debug: "Close call between X and Y"

### D. First-Time Users
**Condition:** User has completed onboarding but has no activity

**Handling:**
1. Use framework signals only (HD, astrology, numerology)
2. Reduce confidence to "low"
3. Title: "Getting to Know Your Patterns"
4. Focus on invitation language: "As you journal and reflect, Mirror will learn your patterns"

### E. Reflector Users
**Condition:** `human_design.type == "Reflector"`

**Handling:**
1. Boost lunar_cycle weight from 1.5 → 3.0
2. Include Moon Gate in signal mix
3. Add lunar context to `why_feels`: "The Moon is currently in Gate 35..."
4. Do NOT use mystical language
5. Do NOT override lived signals (journal still highest)

### F. Strong Recurrence Detected
**Condition:** `recurrence_count >= 3` and `confidence >= 0.7`

**Handling:**
1. Use recurrence-specific template
2. Title includes "Pattern Returning: X"
3. Add historical context: "You've been here in 2018, 2021..."
4. Focus on recognition, not prediction

---

## 7. FILES TO CREATE/MODIFY

### New Files
| File | Purpose |
|------|---------|
| `/app/backend/services/home_insight_engine.py` | Layer 1 & 2: Signal collection + aggregation |
| `/app/backend/services/interpretation_engine.py` | Layer 3: Pattern templates + structured output |
| `/app/frontend/components/HomeInsightCard.tsx` | New UI for daily insight |

### Modified Files
| File | Changes |
|------|---------|
| `/app/backend/server.py` | Add `GET /api/daily-insight/{user_id}` endpoint |
| `/app/frontend/app/(tabs)/index.tsx` | Replace keystone display with HomeInsightCard |

### Unchanged Files (Reused)
| File | What We Reuse |
|------|---------------|
| `/app/backend/services/pattern_graph.py` | `aggregate_*_signals()`, `detect_pattern_tensions()`, `SIGNAL_WEIGHTS` |
| `/app/backend/services/lunar_cycle.py` | `calculate_lunar_cycle_info()`, `get_current_moon_gate()` |
| `/app/backend/services/pattern_archetype.py` | Reference for archetype scoring approach |

---

## 8. APPROVAL CHECKLIST

Before implementing, please confirm:

- [ ] Architecture overview is clear
- [ ] 3-layer design makes sense
- [ ] Scoring weights are appropriate (Lived: 3, Repeating: 2.5, Timing: 1.5, Base: 1.5)
- [ ] Domain model (7 domains) is correct
- [ ] Output contract matches expectations
- [ ] Phase 1 MVP scope is appropriate
- [ ] Edge case handling is acceptable
- [ ] Debug payload provides enough transparency

---

**Ready for approval. Please confirm to proceed with implementation.**
