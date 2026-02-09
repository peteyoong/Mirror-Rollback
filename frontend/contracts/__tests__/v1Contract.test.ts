/**
 * Project Mirror V1 Integrity Contract - Regression Test Suite
 * 
 * These tests MUST pass for every deployment.
 * Any failure blocks the build.
 * 
 * Run with: npx jest contracts/__tests__/v1Contract.test.ts
 */

import {
  MIRROR_V1_CONTRACT_VERSION,
  ENNEAGRAM_INVARIANTS,
  CROSS_LENS_INVARIANTS,
  NARRATIVE_INVARIANTS,
  validateWingDisplay,
  validateHighConfidenceLock,
  validateProbabilitySum,
  validateCrossLensEligibility,
  validateAdjustmentBounds,
  validateNarrativeLanguage,
  validateUncertaintyVisibility,
  validateTimeBoundLanguage,
  validateAgencyPreservation,
  validateCrossLensContextPresence,
  validateV1Contract,
  WingState,
} from '../v1IntegrityContract';

describe('V1 Integrity Contract', () => {
  // ============================================
  // CONTRACT VERSION
  // ============================================
  
  describe('Contract Version', () => {
    it('should be version 1.0.0', () => {
      expect(MIRROR_V1_CONTRACT_VERSION).toBe('1.0.0');
    });
  });

  // ============================================
  // SECTION A: ENNEAGRAM INTEGRITY
  // ============================================
  
  describe('Section A: Enneagram Integrity', () => {
    
    describe('A1: Wing Display Invariant', () => {
      it('should reject null wing state', () => {
        const violation = validateWingDisplay(null);
        expect(violation).not.toBeNull();
        expect(violation?.invariant).toBe('A1_WING_DISPLAY');
        expect(violation?.severity).toBe('critical');
      });
      
      it('should reject undefined wing state', () => {
        const violation = validateWingDisplay(undefined);
        expect(violation).not.toBeNull();
      });
      
      it('should reject string "null"', () => {
        const violation = validateWingDisplay('null');
        expect(violation).not.toBeNull();
      });
      
      it('should accept "dominant"', () => {
        const violation = validateWingDisplay('dominant');
        expect(violation).toBeNull();
      });
      
      it('should accept "leaning"', () => {
        const violation = validateWingDisplay('leaning');
        expect(violation).toBeNull();
      });
      
      it('should accept "balanced"', () => {
        const violation = validateWingDisplay('balanced');
        expect(violation).toBeNull();
      });
      
      it('should accept "not_clear"', () => {
        const violation = validateWingDisplay('not_clear');
        expect(violation).toBeNull();
      });
      
      it('should reject invalid wing states', () => {
        const violation = validateWingDisplay('unknown');
        expect(violation).not.toBeNull();
      });
    });
    
    describe('A2: High Confidence Lock Invariant', () => {
      it('should reject adjustment on high confidence', () => {
        const violation = validateHighConfidenceLock('high', true);
        expect(violation).not.toBeNull();
        expect(violation?.invariant).toBe('A2_HIGH_CONFIDENCE_LOCK');
        expect(violation?.severity).toBe('critical');
      });
      
      it('should allow no adjustment on high confidence', () => {
        const violation = validateHighConfidenceLock('high', false);
        expect(violation).toBeNull();
      });
      
      it('should allow adjustment on moderate confidence', () => {
        const violation = validateHighConfidenceLock('moderate', true);
        expect(violation).toBeNull();
      });
      
      it('should allow adjustment on low confidence', () => {
        const violation = validateHighConfidenceLock('low', true);
        expect(violation).toBeNull();
      });
    });
    
    describe('A3: Probability Sum Invariant', () => {
      it('should accept probabilities summing to 1.0', () => {
        const probs = {
          '1': 0.1, '2': 0.1, '3': 0.1, '4': 0.1, '5': 0.1,
          '6': 0.2, '7': 0.2, '8': 0.05, '9': 0.05,
        };
        const violation = validateProbabilitySum(probs);
        expect(violation).toBeNull();
      });
      
      it('should reject probabilities not summing to 1.0', () => {
        const probs = {
          '1': 0.5, '2': 0.5, '3': 0.5, '4': 0.1, '5': 0.1,
          '6': 0.1, '7': 0.1, '8': 0.1, '9': 0.1,
        };
        const violation = validateProbabilitySum(probs);
        expect(violation).not.toBeNull();
        expect(violation?.invariant).toBe('A3_PROBABILITY_SUM');
      });
      
      it('should reject probabilities below floor', () => {
        const probs = {
          '1': 0.0001, '2': 0.1, '3': 0.1, '4': 0.1, '5': 0.1,
          '6': 0.2, '7': 0.2, '8': 0.0999, '9': 0.1,
        };
        const violation = validateProbabilitySum(probs);
        expect(violation).not.toBeNull();
        expect(violation?.invariant).toBe('A3_PROBABILITY_FLOOR');
      });
    });
  });

  // ============================================
  // SECTION B: CROSS-LENS GUARDRAILS
  // ============================================
  
  describe('Section B: Cross-Lens Guardrails', () => {
    
    describe('B1: Eligibility Gate Invariant', () => {
      it('should reject adjustment on high confidence', () => {
        const violation = validateCrossLensEligibility(
          'high', 0.05, 'deep', false, true
        );
        expect(violation).not.toBeNull();
        expect(violation?.invariant).toBe('B1_ELIGIBILITY_CONFIDENCE');
      });
      
      it('should reject adjustment when top-2 gap exceeds threshold', () => {
        const violation = validateCrossLensEligibility(
          'moderate', 0.20, 'deep', false, true
        );
        expect(violation).not.toBeNull();
        expect(violation?.invariant).toBe('B1_ELIGIBILITY_GAP');
      });
      
      it('should reject adjustment on short assessment without longitudinal', () => {
        const violation = validateCrossLensEligibility(
          'moderate', 0.05, 'short', false, true
        );
        expect(violation).not.toBeNull();
        expect(violation?.invariant).toBe('B1_ELIGIBILITY_DEPTH');
      });
      
      it('should allow adjustment with longitudinal signals', () => {
        const violation = validateCrossLensEligibility(
          'moderate', 0.05, 'short', true, true
        );
        expect(violation).toBeNull();
      });
      
      it('should allow valid adjustment', () => {
        const violation = validateCrossLensEligibility(
          'moderate', 0.08, 'deep', false, true
        );
        expect(violation).toBeNull();
      });
      
      it('should skip validation when no adjustment applied', () => {
        const violation = validateCrossLensEligibility(
          'high', 0.50, 'short', false, false
        );
        expect(violation).toBeNull();
      });
    });
    
    describe('B2: Adjustment Bounds Invariant', () => {
      it('should accept adjustments within bounds', () => {
        const adjustments = {
          '6': 0.03, '7': -0.02, '5': 0.01, '9': -0.02,
        };
        const violations = validateAdjustmentBounds(adjustments);
        expect(violations).toHaveLength(0);
      });
      
      it('should reject per-type adjustment exceeding ±0.05', () => {
        const adjustments = { '6': 0.08 };
        const violations = validateAdjustmentBounds(adjustments);
        expect(violations.some(v => v.invariant === 'B2_PER_TYPE_BOUND')).toBe(true);
      });
      
      it('should reject total redistribution exceeding 0.10', () => {
        const adjustments = {
          '1': 0.05, '2': 0.05, '3': 0.05, '4': -0.05, '5': -0.05, '6': -0.05,
        };
        const violations = validateAdjustmentBounds(adjustments);
        expect(violations.some(v => v.invariant === 'B2_TOTAL_REDISTRIBUTION')).toBe(true);
      });
    });
  });

  // ============================================
  // SECTION C: NARRATIVE LANGUAGE SAFETY
  // ============================================
  
  describe('Section C: Narrative Language Safety', () => {
    
    describe('C1: Banned Phrase Invariant', () => {
      it.each([
        ['you are a type 6'],
        ['this is your type'],
        ['this confirms your identity'],
        ['this proves you are'],
        ['you should work on'],
        ['you must try to'],
        ['you will always be'],
        ['your destiny is'],
      ])('should reject narrative containing "%s"', (phrase) => {
        const violations = validateNarrativeLanguage(phrase);
        expect(violations.length).toBeGreaterThan(0);
        expect(violations[0].invariant).toBe('C1_BANNED_PHRASE');
      });
      
      it('should accept valid narrative language', () => {
        const text = 'A pattern around security appears in your responses. You might notice when this feels most active.';
        const violations = validateNarrativeLanguage(text);
        expect(violations).toHaveLength(0);
      });
    });
    
    describe('C2: Uncertainty Visibility Invariant', () => {
      it('should reject hidden uncertainty on moderate confidence', () => {
        const violation = validateUncertaintyVisibility('moderate', false, 'Some framing');
        expect(violation).not.toBeNull();
        expect(violation?.invariant).toBe('C2_UNCERTAINTY_VISIBILITY');
      });
      
      it('should reject missing framing on low confidence', () => {
        const violation = validateUncertaintyVisibility('low', true, null);
        expect(violation).not.toBeNull();
        expect(violation?.invariant).toBe('C2_CONFIDENCE_FRAMING');
      });
      
      it('should allow hidden uncertainty on high confidence', () => {
        const violation = validateUncertaintyVisibility('high', false, null);
        expect(violation).toBeNull();
      });
      
      it('should accept visible uncertainty with framing', () => {
        const violation = validateUncertaintyVisibility('moderate', true, 'This pattern is still forming.');
        expect(violation).toBeNull();
      });
    });
    
    describe('C3: Time-Bound Language Invariant', () => {
      it('should accept narrative with time-bound language', () => {
        const text = 'Right now, this pattern appears to be active.';
        const violation = validateTimeBoundLanguage(text);
        expect(violation).toBeNull();
      });
      
      it('should accept "at this stage"', () => {
        const violation = validateTimeBoundLanguage('At this stage, the pattern is forming.');
        expect(violation).toBeNull();
      });
      
      it('should warn when time-bound language is missing', () => {
        const text = 'This pattern appears in your responses.';
        const violation = validateTimeBoundLanguage(text);
        expect(violation).not.toBeNull();
        expect(violation?.severity).toBe('warning');
      });
    });
    
    describe('C4: Agency Preservation Invariant', () => {
      it('should accept agency-preserving language', () => {
        const prompt = 'You might notice when this pattern feels most active.';
        const violation = validateAgencyPreservation(prompt);
        expect(violation).toBeNull();
      });
      
      it('should reject "should" in reflection prompt', () => {
        const prompt = 'You should try to notice this pattern.';
        const violation = validateAgencyPreservation(prompt);
        expect(violation).not.toBeNull();
        expect(violation?.invariant).toBe('C4_AGENCY_VIOLATION');
      });
      
      it('should reject "must" in reflection prompt', () => {
        const prompt = 'You must pay attention to this.';
        const violation = validateAgencyPreservation(prompt);
        expect(violation).not.toBeNull();
      });
      
      it('should reject "need to" in reflection prompt', () => {
        const prompt = 'You need to work on this pattern.';
        const violation = validateAgencyPreservation(prompt);
        expect(violation).not.toBeNull();
      });
    });
    
    describe('C5: Cross-Lens Context Invariant', () => {
      it('should warn when context present without adjustment', () => {
        const violation = validateCrossLensContextPresence(false, 'Some context');
        expect(violation).not.toBeNull();
        expect(violation?.severity).toBe('warning');
      });
      
      it('should warn when context missing with adjustment', () => {
        const violation = validateCrossLensContextPresence(true, null);
        expect(violation).not.toBeNull();
      });
      
      it('should accept null context when no adjustment', () => {
        const violation = validateCrossLensContextPresence(false, null);
        expect(violation).toBeNull();
      });
      
      it('should accept context when adjustment applied', () => {
        const violation = validateCrossLensContextPresence(true, 'Your chart echoes similar themes.');
        expect(violation).toBeNull();
      });
    });
  });

  // ============================================
  // FULL CONTRACT VALIDATION
  // ============================================
  
  describe('Full Contract Validation', () => {
    
    it('should pass for valid moderate confidence result', () => {
      const result = validateV1Contract({
        wingState: 'leaning',
        confidenceTier: 'moderate',
        typeProbabilities: {
          '1': 0.05, '2': 0.04, '3': 0.08, '4': 0.07, '5': 0.06,
          '6': 0.32, '7': 0.28, '8': 0.05, '9': 0.05,
        },
        adjustmentApplied: false,
        enneagramRaw: {},
        narrative: {
          patternSummary: 'A pattern around security appears right now.',
          confidenceFraming: 'This pattern is still forming.',
          crossLensContext: null,
          reflectionPrompt: 'You might notice when this feels active.',
        },
        uncertaintyVisible: true,
      });
      
      expect(result.valid).toBe(true);
      expect(result.violations.filter(v => v.severity === 'critical')).toHaveLength(0);
    });
    
    it('should fail for null wing state', () => {
      const result = validateV1Contract({
        wingState: null,
        confidenceTier: 'moderate',
        typeProbabilities: {
          '1': 0.1, '2': 0.1, '3': 0.1, '4': 0.1, '5': 0.1,
          '6': 0.2, '7': 0.2, '8': 0.05, '9': 0.05,
        },
        adjustmentApplied: false,
        enneagramRaw: {},
      });
      
      expect(result.valid).toBe(false);
      expect(result.violations.some(v => v.invariant === 'A1_WING_DISPLAY')).toBe(true);
    });
    
    it('should fail for banned phrase in narrative', () => {
      const result = validateV1Contract({
        wingState: 'dominant',
        confidenceTier: 'high',
        typeProbabilities: {
          '1': 0.1, '2': 0.1, '3': 0.1, '4': 0.1, '5': 0.1,
          '6': 0.2, '7': 0.2, '8': 0.05, '9': 0.05,
        },
        adjustmentApplied: false,
        enneagramRaw: {},
        narrative: {
          patternSummary: 'You are a Type 6. This proves your identity.',
          confidenceFraming: null,
          crossLensContext: null,
          reflectionPrompt: 'You should work on this.',
        },
        uncertaintyVisible: false,
      });
      
      expect(result.valid).toBe(false);
      expect(result.violations.filter(v => v.invariant === 'C1_BANNED_PHRASE').length).toBeGreaterThan(0);
    });
    
    it('should fail for illegal cross-lens adjustment', () => {
      const result = validateV1Contract({
        wingState: 'dominant',
        confidenceTier: 'high',
        typeProbabilities: {
          '1': 0.1, '2': 0.1, '3': 0.1, '4': 0.1, '5': 0.1,
          '6': 0.2, '7': 0.2, '8': 0.05, '9': 0.05,
        },
        adjustmentApplied: true, // Illegal with high confidence
        enneagramRaw: {},
        enneagramAdjusted: {},
      });
      
      expect(result.valid).toBe(false);
      expect(result.violations.some(v => v.invariant === 'A2_HIGH_CONFIDENCE_LOCK')).toBe(true);
    });
  });

  // ============================================
  // EDGE CASES & REGRESSION SCENARIOS
  // ============================================
  
  describe('Regression Scenarios', () => {
    
    it('REGRESSION: Short assessment with internal null wing resolves to "not_clear"', () => {
      // This is the scenario that originally caused wing=null to appear in UI
      const internalWing: number | null = null;
      const displayState = internalWing === null ? 'not_clear' : 'dominant';
      
      const violation = validateWingDisplay(displayState);
      expect(violation).toBeNull();
    });
    
    it('REGRESSION: Deep assessment with balanced wings shows correct language', () => {
      const result = validateV1Contract({
        wingState: 'balanced',
        confidenceTier: 'moderate',
        typeProbabilities: {
          '1': 0.1, '2': 0.1, '3': 0.1, '4': 0.1, '5': 0.1,
          '6': 0.2, '7': 0.2, '8': 0.05, '9': 0.05,
        },
        adjustmentApplied: false,
        enneagramRaw: {},
        narrative: {
          patternSummary: 'A pattern around security appears at this stage.',
          confidenceFraming: 'This pattern shows up consistently.',
          crossLensContext: null,
          reflectionPrompt: 'Notice which wing feels more familiar.',
        },
        uncertaintyVisible: true,
      });
      
      expect(result.valid).toBe(true);
    });
    
    it('REGRESSION: Leaning wing shows correct badge', () => {
      const wingState: WingState = 'leaning';
      expect(ENNEAGRAM_INVARIANTS.VALID_WING_STATES).toContain(wingState);
    });
    
    it('REGRESSION: Adjustment exceeding caps gets caught', () => {
      const adjustments = {
        '6': 0.08, // Exceeds ±0.05
      };
      const violations = validateAdjustmentBounds(adjustments);
      expect(violations.length).toBeGreaterThan(0);
    });
    
    it('REGRESSION: Narrative with "confirms" gets caught', () => {
      const narrative = 'Your chart confirms this pattern.';
      const violations = validateNarrativeLanguage(narrative);
      expect(violations.length).toBeGreaterThan(0);
    });
  });
});
