# Longitudinal Pattern Accumulation Architecture

## Overview

A V1-safe longitudinal layer that accumulates evidence from reflections, journals, and assessments to improve Enneagram type and wing clarity over time. This layer NEVER violates P0-P4 frozen semantics.

**V1 Contract Compliance:** This layer is additive only. It cannot change scoring logic, adjustment caps, or narrative templates.

---

## 1. V1 Safety Constraints

### 1.1 What Longitudinal Layer CAN Do

✅ Store derived evidence signals (never raw text)
✅ Compute stability scores over time
✅ Compute a confidence modifier (upshift/downshift hint)
✅ Influence tie-breaking when types are close
✅ Recommend "take deep assessment" when uncertainty persists
✅ Help wing state evolve from `not_clear` → `leaning` → `dominant`

### 1.2 What Longitudinal Layer CANNOT Do

❌ Change Enneagram scoring logic
❌ Override high-confidence Enneagram results
❌ Exceed adjustment bounds (±0.05 per type, ≤0.10 total)
❌ Store raw user text
❌ Modify P0-P4 narrative templates
❌ Force type changes

### 1.3 V1 Contract Invariants (Inherited)

| Invariant | Status |
|-----------|--------|
| High-confidence lock | **ABSOLUTE** — longitudinal cannot flip |
| Max per-type adjustment | ±0.05 (same as cross-lens) |
| Max total redistribution | ≤0.10 (same as cross-lens) |
| Wing display states | `dominant`, `leaning`, `balanced`, `not_clear` only |

---

## 2. Longitudinal Input Signals

### 2.1 Signal Sources

| Source | Signal Types | Storage |
|--------|--------------|---------|
| Reflection Chat | themes, tension, state | Derived only |
| Journal Entries | tags, sentiment, stress markers | Derived only |
| Enneagram Short | type probabilities | Full |
| Enneagram Deep | probabilities + wing | Full |
| Behavioral Meta | usage frequency, recurrence | Aggregated only |

### 2.2 Signal Extraction Rules

**From Reflection Chat:**
```
- Extract: dominant themes (max 3)
- Extract: tension level (low/medium/high)
- Extract: inferred_state (already exists)
- DO NOT store: raw user text
- Derive: type_affinities based on theme-to-type mapping
```

**From Journal Entries:**
```
- Extract: tags/themes (user-selected or derived)
- Extract: sentiment polarity (positive/negative/neutral)
- Extract: stress markers (present/absent)
- DO NOT store: raw entry text
- Derive: avoidance_style based on theme patterns
```

**From Assessments:**
```
- Store: full type probabilities
- Store: wing state
- Store: confidence tier
- These are the primary evidence source
```

---

## 3. Evidence Signal Data Model

### 3.1 Evidence Event Schema

```typescript
interface LongitudinalEvidenceEvent {
  // Identity
  event_id: string;           // UUID
  user_id: string;            // User reference
  created_at: string;         // ISO8601
  
  // Source metadata
  source: 'reflection_chat' | 'journal' | 'enneagram_short' | 'enneagram_deep';
  source_id?: string;         // Reference to source record (optional)
  
  // Derived signals
  signals: {
    // Type affinities: small nudges per event (bounded)
    type_affinities: {
      [type: string]: number;  // Range: -0.03 to +0.03 per type
    };
    
    // Wing affinities (for core type's adjacent wings)
    wing_affinities: {
      [wing: string]: number;  // Range: -0.03 to +0.03
    };
    
    // Behavioral pattern indicators
    stress_style: 
      | 'vigilance'      // Type 6 pattern
      | 'reframing'      // Type 7 pattern
      | 'withdrawal'     // Type 5/4/9 pattern
      | 'control'        // Type 8/1 pattern
      | 'merging'        // Type 2/9 pattern
      | 'achieving'      // Type 3 pattern
      | 'other'
      | null;
    
    avoidance_style:
      | 'uncertainty'    // Type 6
      | 'pain'           // Type 7
      | 'conflict'       // Type 9
      | 'limitation'     // Type 7/8
      | 'intensity'      // Type 5
      | 'rejection'      // Type 2/3
      | 'ordinariness'   // Type 4
      | 'weakness'       // Type 8
      | 'imperfection'   // Type 1
      | 'other'
      | null;
    
    // Signal confidence (how strong this evidence is)
    confidence_hint: number;  // 0.0 - 1.0
  };
  
  // Validation
  v1_compliant: true;         // Always true for V1
}
```

### 3.2 Storage Plan

**Backend (MongoDB):**
```javascript
// Collection: longitudinal_evidence
{
  _id: ObjectId,
  user_id: ObjectId,
  created_at: ISODate,
  source: String,
  source_id: ObjectId | null,
  signals: {
    type_affinities: Object,
    wing_affinities: Object,
    stress_style: String | null,
    avoidance_style: String | null,
    confidence_hint: Number
  },
  // Index on user_id + created_at for efficient queries
}

// Indexes
db.longitudinal_evidence.createIndex({ user_id: 1, created_at: -1 })
db.longitudinal_evidence.createIndex({ user_id: 1, source: 1 })
```

### 3.3 Signal Bounds (CRITICAL)

| Parameter | Bound | Rationale |
|-----------|-------|-----------|
| Max type_affinity per event | ±0.03 | Prevents single event from dominating |
| Max wing_affinity per event | ±0.03 | Same rationale |
| Max total type redistribution per event | 0.06 | Sum of absolute values |
| confidence_hint range | 0.0 - 1.0 | Normalized |

---

## 4. Theme-to-Type Mapping

### 4.1 Reflection Theme Affinities

```typescript
const THEME_TYPE_AFFINITIES: Record<string, Record<string, number>> = {
  // Security/Trust themes
  'trust': { '6': 0.025, '9': 0.01 },
  'safety': { '6': 0.03, '5': 0.01 },
  'loyalty': { '6': 0.025, '2': 0.015 },
  'doubt': { '6': 0.03, '4': 0.01 },
  
  // Achievement themes
  'success': { '3': 0.03, '8': 0.01 },
  'recognition': { '3': 0.025, '2': 0.015 },
  'efficiency': { '3': 0.02, '1': 0.02 },
  'image': { '3': 0.03 },
  
  // Connection themes
  'helping': { '2': 0.03, '9': 0.01 },
  'relationships': { '2': 0.02, '6': 0.01, '9': 0.01 },
  'being_needed': { '2': 0.03 },
  
  // Depth/Authenticity themes
  'authenticity': { '4': 0.03, '5': 0.01 },
  'meaning': { '4': 0.025, '5': 0.015 },
  'uniqueness': { '4': 0.03 },
  'longing': { '4': 0.025, '9': 0.015 },
  
  // Knowledge/Understanding themes
  'understanding': { '5': 0.03, '6': 0.01 },
  'observation': { '5': 0.025, '9': 0.015 },
  'privacy': { '5': 0.03 },
  'competence': { '5': 0.02, '3': 0.02 },
  
  // Possibility/Freedom themes
  'freedom': { '7': 0.03, '8': 0.01 },
  'options': { '7': 0.025, '6': 0.015 },
  'excitement': { '7': 0.03 },
  'future': { '7': 0.025, '3': 0.015 },
  
  // Strength/Control themes
  'control': { '8': 0.03, '1': 0.01 },
  'strength': { '8': 0.025, '3': 0.015 },
  'justice': { '8': 0.02, '1': 0.02 },
  'autonomy': { '8': 0.03, '5': 0.01 },
  
  // Peace/Harmony themes
  'peace': { '9': 0.03, '2': 0.01 },
  'harmony': { '9': 0.025, '2': 0.015 },
  'stability': { '9': 0.02, '6': 0.02 },
  'comfort': { '9': 0.025, '7': 0.015 },
  
  // Integrity/Improvement themes
  'improvement': { '1': 0.03, '3': 0.01 },
  'integrity': { '1': 0.025, '6': 0.015 },
  'responsibility': { '1': 0.02, '6': 0.02 },
  'standards': { '1': 0.03 },
};
```

### 4.2 Stress/Avoidance Pattern Mapping

```typescript
const STRESS_TYPE_AFFINITIES: Record<string, Record<string, number>> = {
  'vigilance': { '6': 0.025 },
  'reframing': { '7': 0.025 },
  'withdrawal': { '5': 0.02, '4': 0.015, '9': 0.01 },
  'control': { '8': 0.02, '1': 0.015 },
  'merging': { '2': 0.02, '9': 0.015 },
  'achieving': { '3': 0.025 },
};

const AVOIDANCE_TYPE_AFFINITIES: Record<string, Record<string, number>> = {
  'uncertainty': { '6': 0.025 },
  'pain': { '7': 0.025 },
  'conflict': { '9': 0.025 },
  'limitation': { '7': 0.015, '8': 0.015 },
  'intensity': { '5': 0.025 },
  'rejection': { '2': 0.015, '3': 0.015 },
  'ordinariness': { '4': 0.025 },
  'weakness': { '8': 0.025 },
  'imperfection': { '1': 0.025 },
};
```

---

## 5. Aggregation Logic

### 5.1 Aggregator Input

```typescript
interface AggregatorInput {
  user_id: string;
  evidence_events: LongitudinalEvidenceEvent[];
  current_enneagram_result: {
    inferred_core: number;
    inferred_wing: number | null;
    confidence_tier: 'low' | 'moderate' | 'high';
    wing_state: 'dominant' | 'leaning' | 'balanced' | 'not_clear';
    type_probabilities: Record<string, number>;
  };
  config: AggregatorConfig;
}

interface AggregatorConfig {
  // Time windows
  recent_window_days: number;      // Default: 30
  stability_window_events: number; // Default: 10
  
  // Thresholds
  stability_high_threshold: number;    // Default: 0.75
  stability_low_threshold: number;     // Default: 0.55
  top1_dominance_threshold: number;    // Default: 0.70
  wing_clarity_threshold: number;      // Default: 0.65
  
  // Bounds (V1-inherited)
  max_total_adjustment: number;        // Default: 0.10
  max_per_type_adjustment: number;     // Default: 0.05
}
```

### 5.2 Stability Score Calculation

```python
def calculate_type_stability(events: List[Evidence], config: Config) -> float:
    """
    Calculate how consistent the top type has been over recent events.
    Returns 0.0 (unstable) to 1.0 (very stable).
    """
    if len(events) < 3:
        return 0.0  # Insufficient data
    
    # Get top type from each event
    top_types = []
    for event in events[-config.stability_window_events:]:
        affinities = event.signals.type_affinities
        if affinities:
            top = max(affinities.keys(), key=lambda k: affinities[k])
            top_types.append(top)
    
    if not top_types:
        return 0.0
    
    # Calculate mode (most frequent top type)
    mode_type = Counter(top_types).most_common(1)[0][0]
    mode_count = Counter(top_types)[mode_type]
    
    # Base stability = frequency of mode
    base_stability = mode_count / len(top_types)
    
    # Apply recency weighting (recent events count more)
    recency_weights = [0.5 + 0.5 * (i / len(top_types)) for i in range(len(top_types))]
    weighted_matches = sum(
        w for t, w in zip(top_types, recency_weights) if t == mode_type
    )
    weighted_total = sum(recency_weights)
    recency_weighted_stability = weighted_matches / weighted_total
    
    # Combine (60% recency-weighted, 40% raw)
    return 0.6 * recency_weighted_stability + 0.4 * base_stability


def calculate_wing_stability(
    events: List[Evidence], 
    core_type: int,
    config: Config
) -> float:
    """
    Calculate how consistent wing signals have been.
    """
    if len(events) < 3:
        return 0.0
    
    wing_left = core_type - 1 if core_type > 1 else 9
    wing_right = core_type + 1 if core_type < 9 else 1
    
    wing_scores = {'left': [], 'right': []}
    
    for event in events[-config.stability_window_events:]:
        affinities = event.signals.wing_affinities
        if affinities:
            wing_scores['left'].append(affinities.get(str(wing_left), 0))
            wing_scores['right'].append(affinities.get(str(wing_right), 0))
    
    if not wing_scores['left'] or not wing_scores['right']:
        return 0.0
    
    avg_left = sum(wing_scores['left']) / len(wing_scores['left'])
    avg_right = sum(wing_scores['right']) / len(wing_scores['right'])
    
    # Stability = how clearly one wing dominates
    total = abs(avg_left) + abs(avg_right)
    if total < 0.001:
        return 0.0
    
    dominance = abs(avg_left - avg_right) / total
    
    # Scale to 0-1
    return min(1.0, dominance * 1.5)
```

### 5.3 Confidence Modifier Calculation

```python
def calculate_confidence_modifier(
    events: List[Evidence],
    current_result: EnneagramResult,
    type_stability: float,
    config: Config
) -> Tuple[str, str]:
    """
    Determine if confidence should shift.
    Returns: (modifier, recommended_next_step)
    
    modifier: 'none' | 'upshift' | 'downshift'
    recommended_next_step: 'none' | 'take_deep_assessment' | 'keep_observing'
    """
    # CRITICAL: Never modify high confidence
    if current_result.confidence_tier == 'high':
        return ('none', 'none')
    
    # Get recent events
    recent = [e for e in events if is_within_days(e.created_at, 30)]
    
    if len(recent) < 5:
        return ('none', 'keep_observing')
    
    # Calculate top-1 frequency
    top1_count = sum(
        1 for e in recent 
        if get_top_type(e.signals.type_affinities) == current_result.inferred_core
    )
    top1_frequency = top1_count / len(recent)
    
    # Upshift conditions (all must be met)
    if (
        type_stability >= config.stability_high_threshold and
        top1_frequency >= config.top1_dominance_threshold and
        len(recent) >= 10
    ):
        # Can upshift: low → moderate, or moderate → high
        return ('upshift', 'none')
    
    # Downshift conditions
    if type_stability < config.stability_low_threshold:
        # Recommend more data
        if current_result.assessment_depth == 'short':
            return ('none', 'take_deep_assessment')
        else:
            return ('downshift', 'keep_observing')
    
    return ('none', 'none')
```

### 5.4 Top Types Over Time

```python
def calculate_top_types_over_time(
    events: List[Evidence],
    config: Config
) -> List[Dict]:
    """
    Calculate frequency distribution of top types over time.
    """
    if not events:
        return []
    
    recent = [e for e in events if is_within_days(e.created_at, config.recent_window_days)]
    
    if not recent:
        return []
    
    # Aggregate type affinities
    type_totals = defaultdict(float)
    
    for event in recent:
        affinities = event.signals.type_affinities
        for type_num, affinity in affinities.items():
            type_totals[type_num] += affinity
    
    # Normalize to shares
    total = sum(type_totals.values())
    if total < 0.001:
        return []
    
    shares = [
        {'type': int(t), 'share': round(v / total, 3)}
        for t, v in type_totals.items()
    ]
    
    # Sort by share descending
    shares.sort(key=lambda x: x['share'], reverse=True)
    
    return shares[:3]  # Top 3 only
```

---

## 6. Longitudinal Adjustment Logic (V1-Bounded)

### 6.1 Adjustment Calculation

```python
def calculate_longitudinal_adjustment(
    events: List[Evidence],
    current_probabilities: Dict[str, float],
    config: Config
) -> Dict[str, float]:
    """
    Calculate bounded probability adjustments from longitudinal data.
    
    CRITICAL: Must respect V1 bounds:
    - Max per-type: ±0.05
    - Max total: ≤0.10
    """
    if len(events) < 5:
        return {}  # Insufficient data
    
    recent = [e for e in events if is_within_days(e.created_at, 30)]
    
    if len(recent) < 3:
        return {}
    
    # Aggregate affinities with recency weighting
    adjustments = defaultdict(float)
    
    for i, event in enumerate(recent):
        recency_weight = 0.5 + 0.5 * (i / len(recent))
        
        for type_num, affinity in event.signals.type_affinities.items():
            adjustments[type_num] += affinity * recency_weight * 0.1  # Damped
    
    # Apply per-type bounds
    bounded = {}
    for type_num, adj in adjustments.items():
        bounded[type_num] = max(-config.max_per_type_adjustment,
                                min(config.max_per_type_adjustment, adj))
    
    # Check total redistribution
    total_redistribution = sum(abs(v) for v in bounded.values()) / 2
    
    if total_redistribution > config.max_total_adjustment:
        # Scale down proportionally
        scale = config.max_total_adjustment / total_redistribution
        bounded = {k: v * scale for k, v in bounded.items()}
    
    return bounded
```

### 6.2 Wing Evolution Logic

```python
def evolve_wing_state(
    current_wing_state: str,
    current_wing: Optional[int],
    wing_stability: float,
    wing_affinities: Dict[str, float],
    core_type: int,
    config: Config
) -> Tuple[str, Optional[int]]:
    """
    Evolve wing state based on longitudinal evidence.
    
    Allowed transitions:
    - not_clear → leaning (if stability crosses threshold)
    - leaning → dominant (if stability is very high)
    - dominant stays dominant
    - balanced stays balanced (until one clearly wins)
    """
    wing_left = core_type - 1 if core_type > 1 else 9
    wing_right = core_type + 1 if core_type < 9 else 1
    
    left_total = wing_affinities.get(str(wing_left), 0)
    right_total = wing_affinities.get(str(wing_right), 0)
    
    # Determine dominant wing from longitudinal data
    if abs(left_total - right_total) < 0.02:
        longitudinal_wing = None  # Still unclear
    else:
        longitudinal_wing = wing_left if left_total > right_total else wing_right
    
    # Evolution rules
    if current_wing_state == 'not_clear':
        if wing_stability >= config.wing_clarity_threshold and longitudinal_wing:
            return ('leaning', longitudinal_wing)
        return ('not_clear', None)
    
    if current_wing_state == 'leaning':
        if wing_stability >= 0.85 and longitudinal_wing == current_wing:
            return ('dominant', current_wing)
        return ('leaning', current_wing or longitudinal_wing)
    
    if current_wing_state == 'balanced':
        if wing_stability >= config.wing_clarity_threshold:
            return ('leaning', longitudinal_wing)
        return ('balanced', None)
    
    # dominant stays dominant
    return (current_wing_state, current_wing)
```

---

## 7. Output Contract

### 7.1 Longitudinal Summary Schema

```typescript
interface LongitudinalSummary {
  // Feature flag
  enabled: boolean;
  
  // Stability metrics
  type_stability: number;          // 0.0 - 1.0
  wing_stability: number;          // 0.0 - 1.0
  
  // Evidence volume
  evidence_volume: {
    total: number;                 // All-time count
    last_30_days: number;          // Recent count
    sources: {
      reflection_chat: number;
      journal: number;
      enneagram_short: number;
      enneagram_deep: number;
    };
  };
  
  // Type trends
  top_types_over_time: Array<{
    type: number;
    share: number;                 // 0.0 - 1.0
  }>;
  
  // Modifiers
  confidence_modifier: 'none' | 'upshift' | 'downshift';
  
  // Recommendations
  recommended_next_step: 'none' | 'take_deep_assessment' | 'keep_observing';
  
  // Adjustment data (for debugging, not UI)
  adjustments?: {
    type_adjustments: Record<string, number>;
    total_redistribution: number;
    v1_bounded: boolean;
  };
  
  // Metadata
  computed_at: string;             // ISO8601
  evidence_window_days: number;
}
```

### 7.2 Combined Result Integration

```typescript
interface EnneagramResultWithLongitudinal {
  // Existing V1 fields (unchanged)
  inferred_core: number;
  inferred_wing: number | null;
  confidence_tier: 'low' | 'moderate' | 'high';
  wing_state: 'dominant' | 'leaning' | 'balanced' | 'not_clear';
  type_probabilities: Record<string, number>;
  
  // V1 cross-lens (unchanged)
  cross_lens?: CrossLensAdjustmentResult;
  
  // NEW: Longitudinal (additive)
  longitudinal?: LongitudinalSummary;
  
  // Final adjusted (if applicable)
  effective_confidence_tier: 'low' | 'moderate' | 'high';
  effective_wing_state: 'dominant' | 'leaning' | 'balanced' | 'not_clear';
}
```

---

## 8. Confidence Evolution Rules (Deterministic)

### 8.1 Upshift Rules

| From | To | Conditions (ALL must be true) |
|------|-----|-------------------------------|
| `low` | `moderate` | type_stability ≥ 0.65, top1_frequency ≥ 0.60, evidence_volume.last_30_days ≥ 5 |
| `moderate` | `high` | type_stability ≥ 0.75, top1_frequency ≥ 0.70, evidence_volume.last_30_days ≥ 10, assessment_depth = 'deep' |

### 8.2 Downshift Rules

| From | To | Conditions |
|------|-----|------------|
| `moderate` | `low` | type_stability < 0.45 AND top1_frequency < 0.50 |
| ❌ `high` | `moderate` | **NEVER** — high confidence is locked |

### 8.3 Wing Evolution Rules

| From | To | Conditions |
|------|-----|------------|
| `not_clear` | `leaning` | wing_stability ≥ 0.65, one wing has ≥60% of signals |
| `leaning` | `dominant` | wing_stability ≥ 0.85, same wing dominant for ≥10 events |
| `balanced` | `leaning` | wing_stability ≥ 0.70, clear winner emerges |

### 8.4 Recommendation Rules

| Condition | Recommendation |
|-----------|----------------|
| confidence = low, evidence < 5 | `keep_observing` |
| confidence = low, evidence ≥ 10, stability < 0.55 | `take_deep_assessment` |
| confidence = moderate, type keeps alternating | `take_deep_assessment` |
| confidence = moderate, stability high | `none` |
| confidence = high | `none` |

---

## 9. API Endpoints

### 9.1 Record Evidence

```
POST /api/longitudinal/evidence
{
  "user_id": "uuid",
  "source": "reflection_chat",
  "source_id": "optional_ref",
  "signals": {
    "type_affinities": { "6": 0.02, "7": 0.01 },
    "wing_affinities": { "5": 0.01 },
    "stress_style": "vigilance",
    "avoidance_style": null,
    "confidence_hint": 0.6
  }
}
```

### 9.2 Get Longitudinal Summary

```
GET /api/longitudinal/summary/{user_id}

Response:
{
  "enabled": true,
  "type_stability": 0.78,
  "wing_stability": 0.62,
  "evidence_volume": { ... },
  "top_types_over_time": [ ... ],
  "confidence_modifier": "none",
  "recommended_next_step": "none"
}
```

### 9.3 Get Enriched Enneagram Result

```
GET /api/enneagram/results/{user_id}?include_longitudinal=true

Response:
{
  // Standard V1 result
  "inferred_core": 6,
  "inferred_wing": 5,
  "confidence_tier": "moderate",
  "wing_state": "leaning",
  
  // Longitudinal enrichment
  "longitudinal": {
    "enabled": true,
    "type_stability": 0.78,
    "confidence_modifier": "upshift",
    "recommended_next_step": "none"
  },
  
  // Effective values (after longitudinal)
  "effective_confidence_tier": "high",
  "effective_wing_state": "leaning"
}
```

---

## 10. V1 Contract Compliance Checklist

| Requirement | Status |
|-------------|--------|
| No change to Enneagram scoring logic | ✅ |
| No change to cross-lens eligibility | ✅ |
| No change to adjustment caps | ✅ (inherits ±0.05, ≤0.10) |
| No change to narrative templates | ✅ |
| High confidence lock respected | ✅ |
| No raw text storage | ✅ |
| Additive layer only | ✅ |

---

## Appendix A: Default Configuration

```typescript
const DEFAULT_LONGITUDINAL_CONFIG: AggregatorConfig = {
  // Time windows
  recent_window_days: 30,
  stability_window_events: 10,
  
  // Thresholds
  stability_high_threshold: 0.75,
  stability_low_threshold: 0.55,
  top1_dominance_threshold: 0.70,
  wing_clarity_threshold: 0.65,
  
  // V1-inherited bounds
  max_total_adjustment: 0.10,
  max_per_type_adjustment: 0.05,
};
```

## Appendix B: Evidence Source Weights

| Source | Base Weight | Rationale |
|--------|-------------|-----------|
| `enneagram_deep` | 1.0 | Most reliable |
| `enneagram_short` | 0.7 | Less comprehensive |
| `reflection_chat` | 0.5 | Indirect signal |
| `journal` | 0.4 | Least structured |
