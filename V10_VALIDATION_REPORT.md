# V10.4 Live Validation Report
## Date: March 21, 2026

---

## EXECUTIVE SUMMARY

**Status: ❌ NOT READY FOR PRODUCTION**

V10.4 validation across 15 cards revealed **13 cards with quality issues (87%)**. Major problems detected that require a quality pass before deployment.

---

## KEY FINDINGS

### 1. Confidence Distribution is Skewed

| Confidence | Count | Percentage |
|------------|-------|------------|
| HIGH | 1 | 7% |
| MEDIUM | 0 | 0% |
| LOW | 14 | 93% |

**Problem:** The system is defaulting to LOW confidence even for HIGH signal profiles (clear warmth + growth, clear grief processing). This defeats the purpose of confidence-aware expression.

**Root Cause:** The frame scoring mechanism appears to not be weighting signals strongly enough, resulting in tight margins between top candidates and defaulting to LOW confidence.

### 2. Failure Type Breakdown

| Failure Type | Count | % of Cards |
|--------------|-------|------------|
| WEAK PRACTICAL | 9 | 60% |
| VAGUE PHRASE | 6 | 40% |
| REPETITIVE | 2 | 13% |
| GENERIC DERIVATION | 1 | 7% |

### 3. Specific Issues

#### A. WEAK PRACTICAL GUIDANCE (Critical - 9 cards)

The practical suggestions use soft language ("Notice", "Ask yourself") instead of actionable verbs ("Try", "Do", "Take").

**Examples of weak practicals:**
- "Notice one small moment of connection today without evaluating it."
- "Notice both: where you feel ready, and where you're hesitating."

**What's needed:** More directive language for HIGH confidence scenarios.

#### B. VAGUE PHRASES (High - 6 cards)

"Something is" appears frequently, violating the language rules that prohibit vague phrases.

**Examples:**
- "Something is stirring: momentum toward action..."
- "Something you've been holding is ready to move..."

#### C. REPETITIVE PATTERNS (Medium - 2 cards)

Words like "holding", "testing", "whether" repeat 3+ times across card sections.

#### D. FALSE CERTAINTY MISMATCH (High - 5 cards)

HIGH signal profiles received LOW confidence output:
- Card #1 (high_warmth_growth): Correctly got HIGH
- Card #2 (high_grief_processing): Expected HIGH, got LOW
- Card #3 (high_pressure_overwhelm): Expected HIGH, got LOW
- Card #14 (high_warmth_growth): Expected HIGH, got LOW

### 4. Section Coherence Analysis

**POSITIVE:** Sections generally follow the selected frame. When `edge_of_action` is selected, all sections speak to readiness and movement.

**NEGATIVE:** Dual-frame expressions sometimes create awkward constructions:
- "There's a pull toward self-protection, even as something is being held back that wants to move.."
- Note the double period and awkward phrasing.

---

## FLAGGED FAILURES

### Card #2 - Moving Through (HIGH: Clear Grief Processing)
- **False Certainty:** Expected HIGH confidence, got LOW
- **Repetitive:** "holding" appears 3 times
- **Vague:** Contains "Something is stirring"

### Card #5 - Relational Weight (LOW: Neutral & Sparse)
- **Generic Derivation:** No signal matches, pattern-only
- **Vague:** Contains "Something is stirring"
- **Weak Practical:** Only "Notice" verb

### Card #15 - Heart Thaw (MIXED: Hope + Fear)
- **Highly Repetitive:** "testing" (3x), "whether" (3x), "small" (3x)
- **Disconnected:** Core insight and Why Now are IDENTICAL

---

## ROOT CAUSE ANALYSIS

### 1. Signal Extraction Too Weak

The signal extraction is returning low values (0.4-0.6) even for clearly emotional journal entries:
- "I feel grateful and hopeful" → warmth: 1.0 ✓
- "I miss them deeply. The loss feels heavier today." → grief: 0.4 ✗

The grief signal should be much higher given the clear emotional content.

### 2. Confidence Thresholds Too Narrow

Current thresholds appear to be:
- HIGH: margin > 2.0
- MEDIUM: margin 1.0-2.0
- LOW: margin < 1.0

Even with strong signals (growth:0.8, warmth:1.0), the margin between top frames is only 1.5-2.0, resulting in LOW/MEDIUM confidence.

### 3. Dual-Frame Logic Too Aggressive

The dual-frame expression triggers at LOW confidence (margin < 1.0), but with 93% of cards falling into LOW confidence, dual-frame expressions dominate when they should be the exception.

### 4. Practical Templates Need Strength Variation

Practical suggestions don't vary based on confidence level. A HIGH confidence card should have more direct practical guidance than a LOW confidence card.

---

## RECOMMENDED FIXES

### Priority 1: Fix Signal Extraction Weights
- Increase signal detection sensitivity
- Ensure "grief", "loss", "miss" keywords yield grief signal ≥ 0.6

### Priority 2: Adjust Confidence Thresholds
- Current: HIGH requires margin > 2.0
- Proposed: HIGH requires margin > 1.5 OR strongest signal > 0.7

### Priority 3: Strengthen Practical Templates
- Add confidence-based practical selection
- HIGH confidence → "Do X", "Take Y", "Say Z"
- LOW confidence → "Notice X", "Consider Y"

### Priority 4: Remove Vague Phrases
- Search and replace "Something is" with more specific language
- Review all structures for vague phrases

### Priority 5: Add Repetition Prevention
- Track words used across sections
- Avoid repeating significant words more than 2x per card

---

## SUCCESS CRITERIA (Not Met)

| Criterion | Status |
|-----------|--------|
| Cards read like one coherent thought | ⚠️ Mostly yes, but some awkward dual-frame constructions |
| Wording feels personal, not templated | ❌ Too many vague phrases |
| Confidence appropriately shapes certainty | ❌ Almost all cards LOW confidence |
| Derivation feels specific and trustworthy | ⚠️ Good when signals present, generic when sparse |
| No repetitive/vague/over-poetic sections | ❌ Multiple failures |

---

## RECOMMENDATION

**Do NOT deploy V10.4 as the default Mirror engine yet.**

A quality pass is required to:
1. Fix confidence calibration
2. Strengthen signal extraction
3. Remove vague phrases
4. Add practical guidance variation by confidence level

Estimated effort: 2-4 hours of focused refinement.

---

## APPENDIX: Card-by-Card Results

| # | Pattern | Signal Profile | Confidence | Failures |
|---|---------|----------------|------------|----------|
| 1 | Relational Reopening | HIGH: Warmth+Growth | HIGH ✓ | WEAK PRACTICAL |
| 2 | Moving Through | HIGH: Grief | LOW ✗ | REPETITIVE, VAGUE |
| 3 | Emotional Wave Riding | HIGH: Pressure | LOW ✗ | None |
| 4 | Standing at Threshold | LOW: Minimal | LOW ✓ | WEAK PRACTICAL |
| 5 | Relational Weight | LOW: Sparse | LOW ✓ | GENERIC, VAGUE, WEAK |
| 6 | Expansion Resistance | LOW: Factual | LOW ✓ | VAGUE |
| 7 | Standing at Threshold | MIXED: Hope+Fear | LOW ✓ | WEAK PRACTICAL |
| 8 | Expansion Resistance | MIXED: Growth+Resist | LOW ✓ | VAGUE, WEAK |
| 9 | Relational Reopening | MIXED: Open+Walls | LOW ✓ | VAGUE, WEAK |
| 10 | Moving Through | MIXED: Grief+Gratitude | LOW ✓ | WEAK PRACTICAL |
| 11 | Standing at Threshold | MEDIUM: Hesitant | LOW ✗ | None |
| 12 | Emotional Wave Riding | MEDIUM: Cycles | LOW ✗ | WEAK PRACTICAL |
| 13 | Relational Weight | MEDIUM: Tension | LOW ✗ | WEAK PRACTICAL |
| 14 | Heart Thaw | HIGH: Warmth+Growth | LOW ✗ | VAGUE |
| 15 | Heart Thaw | MIXED: Hope+Fear | LOW ✓ | REPETITIVE |

✓ = Confidence matched expectation
✗ = Confidence did NOT match expectation
