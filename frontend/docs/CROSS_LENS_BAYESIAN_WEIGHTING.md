# Cross-Lens Bayesian Weighting System

## Overview

A soft-prior weighting layer where Astrology and Human Design signals can gently nudge Enneagram probabilities without overriding the primary Enneagram result. This implements Bayesian influence—not deterministic mapping.

---

## 1. Core Principles

### 1.1 Hierarchy of Authority

```
PRIMARY SIGNAL: Enneagram Assessment (Deep or Short)
     │
     ▼
SOFT PRIORS: Astrology + Human Design (Optional, Bounded)
     │
     ▼
FINAL OUTPUT: Adjusted Probabilities (Renormalized)
```

### 1.2 Non-Negotiable Rules

| Rule | Description |
|------|-------------|
| **Enneagram Primacy** | Enneagram signal is never overridden |
| **No Type Flipping** | A high-confidence Enneagram result cannot be changed |
| **Bounded Influence** | Maximum ±0.05 per type, ≤0.10 total redistribution |
| **Probabilistic Only** | No hard mappings (e.g., "Saturn = Type 6") |
| **Transparency Required** | All adjustments must be logged with rationale |
| **Soft Language** | No causal or authoritative framing in outputs |

---

## 2. Eligibility Conditions

Cross-lens weighting may **only** apply when ALL of the following are true:

### 2.1 Condition Matrix

| Condition | Threshold | Rationale |
|-----------|-----------|-----------|
| Enneagram confidence tier | `low` OR `moderate` | High confidence = no adjustment needed |
| Top-2 probability gap | `≤ 0.12` | Only adjust when genuinely ambiguous |
| Assessment depth | `deep` OR `longitudinal_signals = true` | Require sufficient Enneagram data |
| Cross-lens data exists | At least one lens has valid signals | Cannot adjust without priors |

### 2.2 Eligibility Check Logic

```python
def is_cross_lens_eligible(enneagram_result, cross_lens_data):
    # Condition 1: Confidence must be low or moderate
    if enneagram_result.confidence_tier == 'high':
        return False, "High confidence - no adjustment allowed"
    
    # Condition 2: Top-2 gap must be within proximity window
    top_probs = sorted(enneagram_result.type_probabilities.values(), reverse=True)
    top_2_gap = top_probs[0] - top_probs[1]
    if top_2_gap > 0.12:
        return False, f"Top-2 gap ({top_2_gap:.2f}) exceeds threshold (0.12)"
    
    # Condition 3: Assessment depth requirement
    has_deep = enneagram_result.assessment_depth == 'deep'
    has_longitudinal = cross_lens_data.get('longitudinal_signals', False)
    if not (has_deep or has_longitudinal):
        return False, "Insufficient assessment depth"
    
    # Condition 4: Cross-lens data must exist
    has_astro = cross_lens_data.get('astrology') is not None
    has_hd = cross_lens_data.get('human_design') is not None
    if not (has_astro or has_hd):
        return False, "No cross-lens data available"
    
    return True, "Eligible for cross-lens adjustment"
```

### 2.3 Eligibility Decision Tree

```
┌─────────────────────────────────────────────────────────┐
│             Is Enneagram confidence HIGH?               │
└─────────────────────────────────────────────────────────┘
                          │
              ┌───────────┴───────────┐
              │ YES                   │ NO
              ▼                       ▼
    ┌─────────────────┐    ┌──────────────────────────────┐
    │ NO ADJUSTMENT   │    │ Is top-2 gap ≤ 0.12?        │
    │ Return raw      │    └──────────────────────────────┘
    └─────────────────┘                   │
                               ┌──────────┴──────────┐
                               │ YES                 │ NO
                               ▼                     ▼
                    ┌────────────────┐    ┌─────────────────┐
                    │ Has deep       │    │ NO ADJUSTMENT   │
                    │ assessment OR  │    │ Gap too large   │
                    │ longitudinal?  │    └─────────────────┘
                    └────────────────┘
                               │
                    ┌──────────┴──────────┐
                    │ YES                 │ NO
                    ▼                     ▼
         ┌────────────────┐    ┌─────────────────┐
         │ Has cross-lens │    │ NO ADJUSTMENT   │
         │ data?          │    │ Insufficient    │
         └────────────────┘    │ depth           │
                    │          └─────────────────┘
         ┌──────────┴──────────┐
         │ YES                 │ NO
         ▼                     ▼
┌─────────────────┐    ┌─────────────────┐
│ APPLY CROSS-    │    │ NO ADJUSTMENT   │
│ LENS WEIGHTING  │    │ No priors       │
└─────────────────┘    └─────────────────┘
```

---

## 3. Bayesian Weighting Logic

### 3.1 Conceptual Model

We treat cross-lens signals as **soft evidence** that updates our belief distribution over Enneagram types. This is NOT classical Bayesian inference with explicit likelihood functions—it's a bounded, additive adjustment inspired by Bayesian principles.

```
P_adjusted(type) = P_enneagram(type) + Δ_astrology(type) + Δ_hd(type)
```

Where:
- `P_enneagram(type)` = Raw Enneagram probability
- `Δ_astrology(type)` = Astrology-derived adjustment (bounded)
- `Δ_hd(type)` = Human Design-derived adjustment (bounded)

### 3.2 Signal-to-Type Affinity Mappings

These are **soft affinities**, not deterministic mappings. Each signal has a probability-weighted influence on multiple types.

#### Astrology Signal Affinities

| Signal | Affinity Distribution | Notes |
|--------|----------------------|-------|
| Saturn dominance | 6: +0.6, 1: +0.3, 4: +0.1 | Security, structure, melancholy |
| Jupiter dominance | 7: +0.5, 3: +0.3, 9: +0.2 | Expansion, optimism, ease |
| Mars dominance | 8: +0.6, 3: +0.2, 1: +0.2 | Assertion, drive, anger |
| Moon-Saturn hard aspect | 6: +0.4, 4: +0.4, 5: +0.2 | Emotional caution, withdrawal |
| Moon-Jupiter aspect | 7: +0.4, 2: +0.3, 9: +0.3 | Emotional expansiveness |
| Heavy mutable emphasis | 7: +0.4, 6: +0.3, 3: +0.3 | Adaptability, anxiety |
| Heavy fixed emphasis | 8: +0.3, 4: +0.3, 1: +0.2, 5: +0.2 | Stubbornness, depth |
| Angular planets (ASC/MC) | 3: +0.4, 8: +0.3, 1: +0.3 | Visibility, drive |
| 12th house emphasis | 9: +0.4, 4: +0.3, 5: +0.3 | Withdrawal, dissolution |
| 8th house emphasis | 4: +0.4, 8: +0.3, 5: +0.3 | Depth, intensity |

#### Human Design Signal Affinities

| Signal | Affinity Distribution | Notes |
|--------|----------------------|-------|
| Defined Head + Ajna | 5: +0.5, 6: +0.3, 1: +0.2 | Mental certainty, analysis |
| Undefined Head + Ajna | 7: +0.4, 9: +0.3, 6: +0.3 | Mental openness/anxiety |
| Defined Root | 3: +0.4, 8: +0.3, 1: +0.3 | Pressure handling, drive |
| Undefined Root | 9: +0.4, 7: +0.3, 4: +0.3 | Pressure sensitivity |
| Emotional Authority | 4: +0.5, 2: +0.3, 6: +0.2 | Emotional processing |
| Splenic Authority | 8: +0.4, 6: +0.3, 1: +0.3 | Instinctive response |
| Sacral Authority | 9: +0.4, 2: +0.3, 3: +0.3 | Gut response |
| Manifestor Type | 8: +0.6, 3: +0.2, 1: +0.2 | Initiating energy |
| Generator Type | 9: +0.4, 2: +0.3, 3: +0.3 | Responding energy |
| Projector Type | 5: +0.4, 4: +0.3, 2: +0.3 | Guiding, waiting |
| Reflector Type | 9: +0.6, 4: +0.2, 7: +0.2 | Sampling, reflecting |
| Defined Solar Plexus | 4: +0.4, 2: +0.3, 8: +0.3 | Emotional definition |
| Undefined Solar Plexus | 9: +0.4, 7: +0.3, 5: +0.3 | Emotional openness |

### 3.3 Adjustment Calculation

```python
def calculate_adjustment(signal_type, signal_name, signal_strength, affinity_map):
    """
    Calculate bounded adjustment for a single signal.
    
    Args:
        signal_type: 'astrology' or 'human_design'
        signal_name: e.g., 'saturn_dominance'
        signal_strength: 0.0-1.0 (how strong the signal is in the chart)
        affinity_map: Dict of type -> affinity weight
    
    Returns:
        Dict of type -> adjustment delta
    """
    MAX_SIGNAL_CONTRIBUTION = 0.025  # Each signal can contribute max ±0.025
    
    adjustments = {}
    for enneagram_type, affinity in affinity_map.items():
        # Raw adjustment = signal_strength × affinity × max_contribution
        raw_delta = signal_strength * affinity * MAX_SIGNAL_CONTRIBUTION
        adjustments[enneagram_type] = raw_delta
    
    # Zero-sum: positive adjustments must be balanced by negative elsewhere
    total_positive = sum(d for d in adjustments.values() if d > 0)
    if total_positive > 0:
        # Distribute negative adjustment across non-favored types
        non_favored = [t for t in range(1, 10) if t not in adjustments or adjustments.get(t, 0) <= 0]
        neg_per_type = -total_positive / len(non_favored) if non_favored else 0
        for t in non_favored:
            adjustments[t] = adjustments.get(t, 0) + neg_per_type
    
    return adjustments
```

### 3.4 Aggregation and Bounding

```python
def aggregate_adjustments(astro_adjustments, hd_adjustments):
    """
    Combine all adjustments with strict bounding.
    """
    MAX_PER_TYPE = 0.05
    MAX_TOTAL = 0.10
    
    combined = {}
    for t in range(1, 10):
        raw = astro_adjustments.get(t, 0) + hd_adjustments.get(t, 0)
        # Bound per-type adjustment
        combined[t] = max(-MAX_PER_TYPE, min(MAX_PER_TYPE, raw))
    
    # Check total redistribution
    total_movement = sum(abs(d) for d in combined.values()) / 2  # Divide by 2 because zero-sum
    if total_movement > MAX_TOTAL:
        # Scale down all adjustments proportionally
        scale_factor = MAX_TOTAL / total_movement
        combined = {t: d * scale_factor for t, d in combined.items()}
    
    return combined
```

### 3.5 Final Probability Calculation

```python
def apply_cross_lens_weighting(enneagram_probs, combined_adjustments):
    """
    Apply adjustments and renormalize.
    """
    adjusted = {}
    for t in range(1, 10):
        t_str = str(t)
        base = enneagram_probs.get(t_str, 0)
        delta = combined_adjustments.get(t, 0)
        # Ensure non-negative
        adjusted[t_str] = max(0.001, base + delta)  # Floor at 0.001
    
    # Renormalize to sum to 1.0
    total = sum(adjusted.values())
    adjusted = {t: p / total for t, p in adjusted.items()}
    
    return adjusted
```

---

## 4. Formal Constraints

### 4.1 Hard Constraints (NEVER VIOLATED)

| Constraint | Value | Enforcement |
|------------|-------|-------------|
| `MAX_ADJUSTMENT_PER_TYPE` | ±0.05 | Clipped at calculation |
| `MAX_TOTAL_REDISTRIBUTION` | 0.10 | Scaled down if exceeded |
| `HIGH_CONFIDENCE_LOCKED` | true | No adjustment when confidence = high |
| `TOP_2_GAP_THRESHOLD` | 0.12 | Skip adjustment if gap > 0.12 |
| `MIN_PROBABILITY_FLOOR` | 0.001 | No type goes to zero |
| `PROBABILITY_SUM` | 1.0 | Always renormalized |

### 4.2 Soft Constraints (Guidelines)

| Guideline | Value | Purpose |
|-----------|-------|---------|
| `MAX_SIGNAL_CONTRIBUTION` | 0.025 | Single signal limited impact |
| `SIGNAL_STRENGTH_THRESHOLD` | 0.3 | Ignore weak signals |
| `CONCORDANCE_BONUS` | 1.2× | Slight boost when lenses agree |

### 4.3 Constraint Enforcement Order

1. Check eligibility conditions → Skip if not met
2. Calculate individual signal adjustments → Bound each
3. Aggregate adjustments → Apply per-type bounds
4. Check total redistribution → Scale if needed
5. Apply to base probabilities → Floor at minimum
6. Renormalize → Sum to 1.0

---

## 5. JSON Contract

### 5.1 Input Contract: Cross-Lens Data

```json
{
  "$schema": "CrossLensInput",
  "user_id": "uuid",
  
  "astrology": {
    "available": true,
    "signals": [
      {
        "name": "saturn_dominance",
        "strength": 0.75,
        "description": "Saturn conjunct MC, square Moon"
      },
      {
        "name": "heavy_mutable_emphasis",
        "strength": 0.60,
        "description": "Sun, Mercury, Mars in mutable signs"
      }
    ],
    "computed_at": "ISO8601"
  },
  
  "human_design": {
    "available": true,
    "signals": [
      {
        "name": "defined_head_ajna",
        "strength": 1.0,
        "description": "Both Head and Ajna centers defined"
      },
      {
        "name": "emotional_authority",
        "strength": 1.0,
        "description": "Solar Plexus authority"
      }
    ],
    "type": "Generator",
    "authority": "Emotional",
    "computed_at": "ISO8601"
  },
  
  "longitudinal_signals": false
}
```

### 5.2 Output Contract: Adjustment Result

```json
{
  "$schema": "CrossLensAdjustmentResult",
  "user_id": "uuid",
  "computed_at": "ISO8601",
  
  "eligibility": {
    "eligible": true,
    "confidence_tier": "moderate",
    "top_2_gap": 0.08,
    "assessment_depth": "deep",
    "cross_lens_sources": ["astrology", "human_design"]
  },
  
  "enneagram_raw": {
    "type_probabilities": {
      "1": 0.05,
      "2": 0.04,
      "3": 0.08,
      "4": 0.09,
      "5": 0.06,
      "6": 0.32,
      "7": 0.24,
      "8": 0.05,
      "9": 0.07
    },
    "top_types": [
      { "type": 6, "probability": 0.32 },
      { "type": 7, "probability": 0.24 }
    ],
    "confidence_tier": "moderate"
  },
  
  "adjustment_applied": true,
  
  "adjustment_details": {
    "astrology_adjustments": {
      "1": 0.008,
      "4": 0.003,
      "6": 0.022,
      "7": -0.015,
      "other": "..."
    },
    "human_design_adjustments": {
      "4": 0.012,
      "5": 0.010,
      "6": 0.008,
      "other": "..."
    },
    "combined_adjustments": {
      "1": 0.008,
      "4": 0.015,
      "5": 0.010,
      "6": 0.030,
      "7": -0.020,
      "other": "..."
    },
    "total_redistribution": 0.083
  },
  
  "enneagram_adjusted": {
    "type_probabilities": {
      "1": 0.058,
      "2": 0.035,
      "3": 0.073,
      "4": 0.105,
      "5": 0.070,
      "6": 0.350,
      "7": 0.220,
      "8": 0.042,
      "9": 0.047
    },
    "top_types": [
      { "type": 6, "probability": 0.35 },
      { "type": 7, "probability": 0.22 }
    ],
    "confidence_tier": "moderate"
  },
  
  "adjustment_sources": ["astrology", "human_design"],
  
  "adjustment_rationale": [
    "Saturn-emphasized profile gently supports security-oriented patterns (Type 6).",
    "Defined Head/Ajna centers align with analytical tendencies.",
    "Emotional Authority resonates with depth-seeking patterns."
  ],
  
  "narrative_hint": "Multiple lenses point in a similar direction, though this remains exploratory.",
  
  "metadata": {
    "version": "1.0",
    "constraints_applied": {
      "per_type_bounded": true,
      "total_redistribution_bounded": true,
      "renormalized": true
    }
  }
}
```

### 5.3 Eligibility-Blocked Output

When cross-lens adjustment is not allowed:

```json
{
  "$schema": "CrossLensAdjustmentResult",
  "user_id": "uuid",
  "computed_at": "ISO8601",
  
  "eligibility": {
    "eligible": false,
    "reason": "High confidence - no adjustment allowed",
    "confidence_tier": "high",
    "top_2_gap": 0.18,
    "assessment_depth": "deep"
  },
  
  "enneagram_raw": { "..." },
  
  "adjustment_applied": false,
  "enneagram_adjusted": null,
  "adjustment_sources": [],
  "adjustment_rationale": [],
  
  "narrative_hint": null
}
```

---

## 6. Example Scenarios

### 6.1 Scenario A: Close 6 vs 7, Saturn + Defined Head

**Input State:**
- Enneagram: Type 6 (32%) vs Type 7 (28%), confidence = moderate
- Astrology: Saturn conjunct MC (strength 0.8), Moon-Saturn square (strength 0.7)
- Human Design: Defined Head + Ajna (strength 1.0), Generator type

**Eligibility Check:**
- ✅ Confidence = moderate (not high)
- ✅ Top-2 gap = 0.04 (≤ 0.12)
- ✅ Assessment depth = deep
- ✅ Cross-lens data available

**Adjustment Calculation:**

| Signal | Type 6 Δ | Type 7 Δ | Type 5 Δ | Others |
|--------|----------|----------|----------|--------|
| Saturn dominance (0.8) | +0.012 | -0.003 | +0.002 | ... |
| Moon-Saturn (0.7) | +0.007 | -0.002 | +0.004 | ... |
| Defined Head/Ajna (1.0) | +0.008 | -0.002 | +0.013 | ... |
| Generator type (1.0) | -0.002 | -0.002 | -0.002 | +0.01 to 9 |
| **Combined** | **+0.025** | **-0.009** | **+0.017** | ... |

**Result:**
```json
{
  "before": { "6": 0.32, "7": 0.28, "5": 0.08 },
  "after":  { "6": 0.345, "7": 0.271, "5": 0.097 },
  "adjustment_rationale": [
    "Saturn-emphasized profile gently supports security-oriented patterns.",
    "Defined mental centers align with analytical, questioning tendencies."
  ]
}
```

**Outcome:** Type 6 lead strengthened slightly (32% → 34.5%), gap widens from 4% to 7.4%.

---

### 6.2 Scenario B: Close 4 vs 5, Emotional Authority + Moon-Saturn

**Input State:**
- Enneagram: Type 4 (29%) vs Type 5 (27%), confidence = low
- Astrology: Moon-Saturn opposition (strength 0.9), 8th house stellium (strength 0.7)
- Human Design: Emotional Authority (strength 1.0), Projector type

**Eligibility Check:**
- ✅ Confidence = low
- ✅ Top-2 gap = 0.02 (≤ 0.12)
- ✅ Deep assessment
- ✅ Both lenses available

**Adjustment Calculation:**

| Signal | Type 4 Δ | Type 5 Δ | Type 6 Δ | Others |
|--------|----------|----------|----------|--------|
| Moon-Saturn (0.9) | +0.009 | +0.005 | +0.009 | ... |
| 8th house (0.7) | +0.007 | +0.005 | -0.002 | ... |
| Emotional Authority (1.0) | +0.013 | -0.003 | +0.005 | ... |
| Projector type (1.0) | +0.008 | +0.010 | -0.002 | ... |
| **Combined** | **+0.037** | **+0.017** | **+0.010** | ... |

**Bounding Applied:** Type 4 adjustment capped at +0.05

**Result:**
```json
{
  "before": { "4": 0.29, "5": 0.27, "6": 0.12 },
  "after":  { "4": 0.327, "5": 0.287, "6": 0.130 },
  "adjustment_rationale": [
    "Moon-Saturn aspect supports depth-seeking patterns.",
    "Emotional Authority aligns with feeling-centered processing.",
    "Projector energy resonates with withdrawal themes."
  ]
}
```

**Outcome:** Type 4 slightly strengthened, but 4 vs 5 remains close. Narrative acknowledges ambiguity.

---

### 6.3 Scenario C: High Confidence - No Adjustment

**Input State:**
- Enneagram: Type 8 (52%) vs Type 3 (18%), confidence = high
- Astrology: Mars dominance (strength 0.9)
- Human Design: Manifestor type (strength 1.0)

**Eligibility Check:**
- ❌ Confidence = high → **BLOCKED**

**Result:**
```json
{
  "adjustment_applied": false,
  "reason": "High confidence - no adjustment allowed",
  "enneagram_adjusted": null,
  "narrative_hint": null
}
```

**Outcome:** Despite strong cross-lens signals supporting Type 8, no adjustment is made because Enneagram confidence is already high.

---

## 7. Disallowed Behaviors (EXPLICIT)

### 7.1 NEVER Do These

| Behavior | Why Disallowed |
|----------|----------------|
| **Hard-map a signal to a type** | "Saturn = Type 6" is forbidden. All mappings are probabilistic. |
| **Flip a high-confidence result** | If Enneagram says Type 3 with high confidence, cross-lens cannot change it. |
| **Exceed ±0.05 per type** | Even if signals strongly agree, per-type cap is absolute. |
| **Exceed 0.10 total redistribution** | Total movement is bounded regardless of signal count. |
| **Use causal language** | "Your astrology confirms..." is forbidden. |
| **Use authoritative language** | "This proves..." is forbidden. |
| **Make a type probability zero** | Floor is 0.001; no type is eliminated. |
| **Override Enneagram with cross-lens** | Cross-lens nudges; it never replaces. |
| **Apply to short assessment alone** | Must have deep assessment OR longitudinal signals. |
| **Apply when gap > 0.12** | Only adjust genuinely ambiguous cases. |

### 7.2 Rationale Text Restrictions

**Allowed phrases:**
- "gently supports"
- "aligns with"
- "resonates with"
- "points in a similar direction"
- "suggests themes of"

**Forbidden phrases:**
- "confirms"
- "proves"
- "determines"
- "means you are"
- "shows that your type is"
- "your chart says"

---

## 8. Language Templates

### 8.1 When Cross-Lens Supports Top Type

> "Multiple perspectives point in a similar direction. Your assessment suggests [Type X] patterns, and other lenses gently support this theme—though all of these remain exploratory."

### 8.2 When Cross-Lens Is Mixed

> "Different lenses highlight different facets. Your Enneagram assessment leans toward [Type X], while other perspectives illuminate additional patterns. This complexity is normal and often meaningful."

### 8.3 When Cross-Lens Was Not Applied

> "Your Enneagram result carries sufficient clarity that additional weighting wasn't applied. The patterns speak for themselves."

---

## 9. Implementation Notes

### 9.1 Signal Extraction

Astrology signals should be extracted from the user's natal chart data (already computed). Human Design signals should be extracted from the user's bodygraph (already computed).

### 9.2 Caching

- Cross-lens adjustments can be cached per user (invalidate on new assessment)
- Signal strength values are static per chart (no recalculation needed)

### 9.3 Logging

All adjustments must be logged for:
- Debugging and validation
- Potential future weight tuning
- Transparency if user requests

### 9.4 Version Control

The weighting system must be versioned. If weights change, old results should be queryable with original weights.

---

## 10. Out of Scope

| Item | Status |
|------|--------|
| UI changes | Not in this prompt |
| Final copy for narratives | Not in this prompt |
| Actual weight values (tuned) | Placeholders only |
| Production tuning | Future phase |
| A/B testing framework | Future phase |

---

## Appendix A: Signal Affinity Reference

See `/app/backend/data/cross_lens_affinities.json` for full affinity mappings.

## Appendix B: Constraint Configuration

See `/app/backend/config/cross_lens_constraints.json` for tunable thresholds.
