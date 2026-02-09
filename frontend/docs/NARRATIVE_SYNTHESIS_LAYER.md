# Narrative Synthesis Layer Architecture

## Overview

The Narrative Synthesis Layer translates computed Enneagram results into human-readable reflection. It is **interpretive only** — no computation happens here. Its purpose is to explain patterns while preserving uncertainty and user sovereignty.

---

## 1. Core Philosophy

### What This Layer Does
- **Reflects** patterns back to the user
- **Surfaces** uncertainty honestly
- **Integrates** cross-lens signals gently
- **Preserves** user sovereignty and agency

### What This Layer Never Does
- **Declares** identity ("You are a Type 6")
- **Implies** permanence ("You will always...")
- **Diagnoses** ("This means you have...")
- **Prescribes** ("You should...")
- **Confirms** ("This proves...")

### The Mirror Principle
> "The narrative is a mirror, not a verdict. It shows patterns — the user decides what they mean."

---

## 2. Input Contract

The Narrative Synthesis Layer accepts a single object:

```typescript
interface NarrativeInput {
  // Core Enneagram data
  enneagram_raw: {
    type_probabilities: TypeProbabilities;
    top_types: { type: number; probability: number }[];
    confidence_tier: 'low' | 'moderate' | 'high';
  };
  
  // Cross-lens adjusted (null if not applied)
  enneagram_adjusted: {
    type_probabilities: TypeProbabilities;
    top_types: { type: number; probability: number }[];
    confidence_tier: 'low' | 'moderate' | 'high';
  } | null;
  
  // Result metadata
  confidence_tier: 'low' | 'moderate' | 'high';
  wing_state: 'dominant' | 'leaning' | 'balanced' | 'not_clear';
  inferred_core: number;
  inferred_wing: number | null;
  
  // Cross-lens context
  adjustment_applied: boolean;
  adjustment_rationale: string[];
  adjustment_sources: ('astrology' | 'human_design')[];
  
  // Assessment context
  assessment_depth: 'short' | 'deep';
  longitudinal_signals: boolean;
  
  // Optional: Close-call data
  close_call: boolean;
  close_call_types?: number[];
}
```

---

## 3. Output Contract

```typescript
interface NarrativeOutput {
  narrative: {
    pattern_summary: string;      // Section 1: What stands out
    confidence_framing: string;   // Section 2: How settled vs exploratory
    cross_lens_context: string | null;  // Section 3: Other lens context (conditional)
    reflection_prompt: string;    // Section 4: Open-ended cue
  };
  
  // Meta-information
  narrative_style: 'exploratory' | 'grounded' | 'settled';
  uncertainty_visible: boolean;
  
  // For debugging/transparency
  template_used: string;
  input_scenario: string;
}
```

### Narrative Style Mapping

| Confidence | Assessment | Cross-Lens | Style |
|------------|------------|------------|-------|
| Low | Short | — | `exploratory` |
| Low | Deep | — | `exploratory` |
| Moderate | Short | No | `grounded` |
| Moderate | Deep | No | `grounded` |
| Moderate | Deep | Yes | `grounded` |
| High | Any | — | `settled` |

---

## 4. Four-Section Narrative Structure

### Section 1: Pattern Summary

**Purpose:** Name what stands out, based on Enneagram results.

**Rules:**
- Use primary type name, not number alone
- Reference motivation or core pattern, not behavior
- Use tentative language ("seems to", "appears to")
- Keep to 1-2 sentences

**Template Structure:**
```
"A pattern around [CORE_THEME] seems to stand out in your responses. 
This suggests [MOTIVATION_HINT] may be a recurring theme."
```

**Core Themes by Type:**
| Type | Core Theme |
|------|------------|
| 1 | improvement and getting things right |
| 2 | connection and being needed |
| 3 | achievement and recognition |
| 4 | depth and authentic self-expression |
| 5 | understanding and preserving energy |
| 6 | security and anticipating what's ahead |
| 7 | possibility and staying engaged |
| 8 | strength and maintaining autonomy |
| 9 | peace and avoiding disruption |

---

### Section 2: Confidence Framing

**Purpose:** Explicitly state how settled vs exploratory the result is.

**Rules:**
- Normalize uncertainty (it's not a failure)
- Use time-bound language ("at this stage", "right now")
- Never apologize for low confidence
- Frame uncertainty as information, not limitation

**Templates by Confidence:**

**Low Confidence:**
```
"This pattern is still forming. Your responses point in this direction, 
though clarity often emerges over time rather than all at once."
```

**Moderate Confidence:**
```
"This theme appears consistently across your responses, though 
nearby patterns remain relevant. Many people find resonance 
in more than one area."
```

**High Confidence:**
```
"This pattern appears clearly and consistently across your responses. 
The signal is strong, though patterns are always lenses, not labels."
```

---

### Section 3: Cross-Lens Context (Conditional)

**Purpose:** Add context from Astrology/Human Design when adjustment was applied.

**Rules:**
- Only include if `adjustment_applied = true`
- Never name exact probabilities
- Never use causal language ("confirms", "proves")
- Position as "context" not "evidence"
- Keep brief (1-2 sentences)

**Templates:**

**Single source (astrology only):**
```
"Your birth chart echoes similar themes, adding texture 
without adding certainty."
```

**Single source (human design only):**
```
"Your Human Design configuration resonates with this pattern, 
offering another angle on the same question."
```

**Both sources:**
```
"Other lenses — your chart and design — gently point in a 
similar direction, though all of these remain exploratory."
```

**Concordance (when lenses agree strongly):**
```
"Multiple perspectives seem to converge here, which may be 
meaningful — though convergence isn't confirmation."
```

---

### Section 4: Reflection Prompt

**Purpose:** End with an open-ended reflection, never advice.

**Rules:**
- Must be observational, not instructional
- Use "might", "may", "could" — never "should"
- Invite noticing, not action
- Keep to 1 sentence

**Template Pool:**
```
- "You might notice when this pattern feels most active."
- "It may be worth observing how this shows up under pressure."
- "Consider when this theme feels most familiar — and when it doesn't."
- "Notice what resonates and what feels less true."
- "This may become clearer as you observe it in daily moments."
- "Pay attention to when this pattern serves you — and when it doesn't."
```

**Selection Logic:**
- Low confidence → Use "forming" language ("This may become clearer...")
- Moderate confidence → Use "noticing" language ("You might notice...")
- High confidence → Use "observing" language ("Pay attention to...")
- Wing unclear → Use wing-specific prompt ("Notice which adjacent pattern...")
- Close call → Use comparison prompt ("Observe which theme feels more central...")

---

## 5. Six Required Template Variants

### Variant 1: Low Confidence + Short Assessment

**Scenario:** User completed short assessment, result is tentative.

**Narrative Style:** `exploratory`

**Template:**
```json
{
  "pattern_summary": "A pattern around [CORE_THEME] seems to be emerging in your responses. At this early stage, this is more of a direction than a destination.",
  
  "confidence_framing": "This is still forming. Short assessments offer a starting point, not a conclusion — and that's exactly how they're designed. Clarity often arrives through reflection, not more questions.",
  
  "cross_lens_context": null,
  
  "reflection_prompt": "This may become clearer as you notice when this pattern shows up in your daily life."
}
```

**Tone:** Gentle, provisional, inviting further exploration.

---

### Variant 2: Moderate Confidence + Deep Assessment

**Scenario:** User completed deep assessment, result has moderate clarity.

**Narrative Style:** `grounded`

**Template:**
```json
{
  "pattern_summary": "A pattern around [CORE_THEME] stands out consistently across your responses. [TYPE_NAME] themes — [MOTIVATION_HINT] — appear to be a significant part of how you navigate the world.",
  
  "confidence_framing": "This pattern appears reliably, though it's not the only one present. Many people carry elements of nearby types, and that complexity is normal — not a sign of unclear results.",
  
  "cross_lens_context": null,
  
  "reflection_prompt": "You might notice when this pattern feels most active — and what happens when you're not in it."
}
```

**Tone:** Grounded, acknowledging complexity, not over-claiming.

---

### Variant 3: High Confidence (No Cross-Lens)

**Scenario:** Clear result from Enneagram alone, no adjustment applied.

**Narrative Style:** `settled`

**Template:**
```json
{
  "pattern_summary": "[TYPE_NAME] patterns appear clearly in your responses. The core theme — [CORE_THEME] — shows up consistently across different question types and contexts.",
  
  "confidence_framing": "This pattern appears with clarity. That doesn't make it a permanent label — all patterns are lenses, not cages — but the signal here is strong enough to work with directly.",
  
  "cross_lens_context": null,
  
  "reflection_prompt": "Pay attention to when this pattern serves you well — and when it might be worth loosening its grip."
}
```

**Tone:** Clear, confident, but still preserving agency.

---

### Variant 4: Moderate Confidence + Cross-Lens Applied

**Scenario:** Deep assessment with cross-lens adjustment.

**Narrative Style:** `grounded`

**Template:**
```json
{
  "pattern_summary": "A pattern around [CORE_THEME] emerges from your responses, with [TYPE_NAME] themes appearing most prominent. This reflects how you answered, not who you are — though the two are often related.",
  
  "confidence_framing": "This pattern appears consistently, and other lenses gently support the same direction. That convergence adds context, not certainty — multiple perspectives pointing similarly is interesting, not definitive.",
  
  "cross_lens_context": "[CROSS_LENS_CONTEXT based on adjustment_rationale]",
  
  "reflection_prompt": "Notice whether this pattern resonates in your lived experience — that's the real test, not any assessment."
}
```

**Tone:** Integrative, acknowledging multiple inputs without over-weighting them.

---

### Variant 5: Wing Not Yet Clear

**Scenario:** Core type identified but wing is unclear.

**Narrative Style:** Inherit from confidence tier.

**Additional Section (inserted after pattern_summary):**
```json
{
  "wing_context": "Your wing — the adjacent pattern that flavors your core type — isn't clearly defined yet. Both neighboring types ([WING_LEFT] and [WING_RIGHT]) may be accessible to you, or one may emerge more clearly over time. This ambiguity isn't a problem to solve; it's information about where you are right now."
}
```

**Reflection Prompt Override:**
```
"Notice which adjacent pattern — [WING_LEFT_THEME] or [WING_RIGHT_THEME] — feels more familiar in your daily life."
```

---

### Variant 6: Balanced Wings

**Scenario:** Core type clear, but both wings are equally present.

**Narrative Style:** Inherit from confidence tier.

**Additional Section (inserted after pattern_summary):**
```json
{
  "wing_context": "You show access to both wings — [WING_LEFT] and [WING_RIGHT]. Rather than defaulting to one pattern, you may draw on different adjacent energies depending on context. Balance here isn't confusion; it's range."
}
```

**Reflection Prompt Override:**
```
"Observe when you lean toward [WING_LEFT_THEME] versus [WING_RIGHT_THEME]. The choice may be more conscious than you realize."
```

---

## 6. Banned Phrases + Allowed Replacements

### Identity Declaration

| ❌ Banned | ✅ Replacement |
|-----------|---------------|
| "You are a Type 6" | "Type 6 patterns appear in your responses" |
| "This is your type" | "This pattern stands out" |
| "You're definitely..." | "This appears consistently..." |
| "Your personality is..." | "Your responses suggest..." |

### Causal / Confirmatory

| ❌ Banned | ✅ Replacement |
|-----------|---------------|
| "This confirms..." | "This is consistent with..." |
| "This proves..." | "This points toward..." |
| "Your astrology shows..." | "Your chart echoes..." |
| "Your Human Design means..." | "Your design resonates with..." |

### Prescriptive / Instructional

| ❌ Banned | ✅ Replacement |
|-----------|---------------|
| "You should..." | "You might notice..." |
| "You need to..." | "It may be worth observing..." |
| "Try to..." | "Consider whether..." |
| "Work on..." | "Pay attention to..." |

### Absolute / Permanent

| ❌ Banned | ✅ Replacement |
|-----------|---------------|
| "You will always..." | "Right now, this pattern..." |
| "You never..." | "At this stage..." |
| "This is permanent" | "This is where you are now" |
| "Your destiny..." | "This direction..." |

### Diagnostic / Clinical

| ❌ Banned | ✅ Replacement |
|-----------|---------------|
| "This means you have..." | "This suggests a pattern of..." |
| "Symptoms of..." | "Themes around..." |
| "Diagnosis" | "Observation" |
| "Treatment" | "Reflection" |

---

## 7. Language Quality Checklist

Every narrative must pass these checks:

### ✅ Required Qualities

| Quality | Test |
|---------|------|
| **Tentative** | Contains "seems", "appears", "suggests", "may" |
| **Observational** | Describes pattern, not person |
| **Time-bound** | References "right now", "at this stage", "currently" |
| **Non-instructional** | No "should", "must", "need to" |
| **Agency-preserving** | User is observer, not object |

### ❌ Automatic Failures

| Failure | Detection |
|---------|-----------|
| Identity claim | "You are", "This is your" without "pattern" |
| Causal claim | "confirms", "proves", "means" |
| Prescription | "should", "must", "need to", "try to" |
| Absolute | "always", "never", "permanent" |
| Diagnostic | "diagnosis", "treatment", "symptom" |

---

## 8. Narrative Assembly Logic

```python
def synthesize_narrative(input: NarrativeInput) -> NarrativeOutput:
    # 1. Determine scenario
    scenario = determine_scenario(input)
    
    # 2. Select base template
    template = get_template(scenario)
    
    # 3. Fill pattern summary
    pattern_summary = fill_pattern_summary(
        template.pattern_summary,
        core_type=input.inferred_core,
        confidence=input.confidence_tier
    )
    
    # 4. Fill confidence framing
    confidence_framing = fill_confidence_framing(
        template.confidence_framing,
        confidence=input.confidence_tier,
        assessment_depth=input.assessment_depth
    )
    
    # 5. Generate cross-lens context (if applicable)
    cross_lens_context = None
    if input.adjustment_applied:
        cross_lens_context = generate_cross_lens_context(
            sources=input.adjustment_sources,
            rationale=input.adjustment_rationale
        )
    
    # 6. Select reflection prompt
    reflection_prompt = select_reflection_prompt(
        confidence=input.confidence_tier,
        wing_state=input.wing_state,
        close_call=input.close_call
    )
    
    # 7. Handle wing variants
    if input.wing_state in ['not_clear', 'balanced']:
        # Insert wing context after pattern summary
        pattern_summary = insert_wing_context(
            pattern_summary,
            wing_state=input.wing_state,
            core_type=input.inferred_core
        )
        reflection_prompt = get_wing_reflection_prompt(
            wing_state=input.wing_state,
            core_type=input.inferred_core
        )
    
    # 8. Determine narrative style
    narrative_style = determine_style(input.confidence_tier, input.assessment_depth)
    
    # 9. Validate language
    validate_language([
        pattern_summary,
        confidence_framing,
        cross_lens_context,
        reflection_prompt
    ])
    
    return NarrativeOutput(
        narrative={
            "pattern_summary": pattern_summary,
            "confidence_framing": confidence_framing,
            "cross_lens_context": cross_lens_context,
            "reflection_prompt": reflection_prompt
        },
        narrative_style=narrative_style,
        uncertainty_visible=(input.confidence_tier != 'high'),
        template_used=scenario,
        input_scenario=describe_scenario(input)
    )
```

---

## 9. Complete Example Outputs

### Example 1: Moderate + Deep + Cross-Lens

**Input:**
```json
{
  "inferred_core": 6,
  "inferred_wing": 5,
  "wing_state": "leaning",
  "confidence_tier": "moderate",
  "assessment_depth": "deep",
  "adjustment_applied": true,
  "adjustment_sources": ["astrology", "human_design"],
  "adjustment_rationale": [
    "Saturn-emphasized profile supports security-oriented patterns",
    "Defined Head/Ajna aligns with analytical tendencies"
  ]
}
```

**Output:**
```json
{
  "narrative": {
    "pattern_summary": "A pattern around security and anticipating what's ahead emerges consistently in your responses. The Loyalist lens — with its focus on preparation, trust, and navigating uncertainty — appears to be a significant part of how you navigate the world.",
    
    "confidence_framing": "This pattern appears reliably across your deep assessment, though it's not the only one present. A leaning toward Wing 5 suggests analytical, observational tendencies flavor this core pattern. Many people carry elements of nearby types, and that complexity is normal.",
    
    "cross_lens_context": "Your birth chart and Human Design configuration gently echo similar themes — a Saturn emphasis and defined mental centers both resonate with vigilance and analysis. This adds context rather than certainty; multiple perspectives pointing similarly is interesting, not definitive.",
    
    "reflection_prompt": "Notice when this pattern of anticipation feels protective versus when it feels constraining. That distinction often reveals more than any assessment."
  },
  "narrative_style": "grounded",
  "uncertainty_visible": true,
  "template_used": "moderate_deep_crosslens",
  "input_scenario": "Type 6w5, moderate confidence, deep assessment, cross-lens applied"
}
```

---

### Example 2: Low + Short Assessment

**Input:**
```json
{
  "inferred_core": 7,
  "inferred_wing": null,
  "wing_state": "not_clear",
  "confidence_tier": "low",
  "assessment_depth": "short",
  "adjustment_applied": false
}
```

**Output:**
```json
{
  "narrative": {
    "pattern_summary": "A pattern around possibility and staying engaged seems to be emerging in your responses. At this early stage, this is more of a direction than a destination — Enthusiast themes are present, but not yet clearly dominant.",
    
    "confidence_framing": "This is still forming. Short assessments offer a starting point, not a conclusion — and that's exactly how they're designed. Clarity often arrives through reflection over time, not from answering more questions.",
    
    "cross_lens_context": null,
    
    "reflection_prompt": "This may become clearer as you notice when the pull toward new possibilities feels most alive — and what you might be moving away from."
  },
  "narrative_style": "exploratory",
  "uncertainty_visible": true,
  "template_used": "low_short",
  "input_scenario": "Type 7 (wing unclear), low confidence, short assessment"
}
```

---

### Example 3: High Confidence

**Input:**
```json
{
  "inferred_core": 8,
  "inferred_wing": 7,
  "wing_state": "dominant",
  "confidence_tier": "high",
  "assessment_depth": "deep",
  "adjustment_applied": false
}
```

**Output:**
```json
{
  "narrative": {
    "pattern_summary": "Challenger patterns appear clearly and consistently in your responses. The core theme — strength, autonomy, and protecting what matters — shows up across different question types and contexts. A dominant Wing 7 adds an expansive, possibility-seeking flavor to this assertive foundation.",
    
    "confidence_framing": "This pattern appears with clarity. That doesn't make it a permanent label — all patterns are lenses, not cages — but the signal here is strong enough to work with directly. The 8w7 combination is sometimes called 'The Maverick' for its blend of force and forward motion.",
    
    "cross_lens_context": null,
    
    "reflection_prompt": "Pay attention to when this pattern of strength serves you well — and when the intensity might be worth softening."
  },
  "narrative_style": "settled",
  "uncertainty_visible": false,
  "template_used": "high_any",
  "input_scenario": "Type 8w7, high confidence, deep assessment"
}
```

---

## 10. Implementation Notes

### Caching
- Templates can be cached
- Filled narratives should not be cached (personalized)

### Logging
- Log template selection rationale
- Log any language validation failures
- Track which reflection prompts resonate (future optimization)

### Versioning
- Narrative templates should be versioned
- Users should see consistent narrative for same result

### Localization
- All templates should support i18n
- Tone and cultural appropriateness varies by locale

---

## Appendix A: Full Phrase Replacement Reference

See `/app/frontend/data/narrative_phrase_replacements.json`

## Appendix B: Type Theme Glossary

See `/app/frontend/data/type_themes.json`

## Appendix C: Reflection Prompt Library

See `/app/frontend/data/reflection_prompts.json`
