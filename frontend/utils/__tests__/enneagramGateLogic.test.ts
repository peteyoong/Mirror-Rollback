/**
 * Enneagram Gate Logic Tests
 * ==========================
 * 
 * Acceptance tests for the Enneagram retake/upgrade gate logic.
 * These tests verify:
 * 1. Short assessment → primary CTA shown
 * 2. Deep + moderate confidence → secondary CTA shown
 * 3. Deep + high confidence → no CTA shown
 * 4. CTA copy matches exactly (no coaching language)
 * 5. Content remains accessible regardless of CTA presence
 */

import {
  computeEnneagramGateState,
  getEnneagramCTACopy,
  getEnneagramUpgradeInfo,
  calculateAssessmentAgeDays,
  PRIMARY_CTA_COPY,
  SECONDARY_CTA_COPY,
  EnneagramGateInput,
} from '../enneagramGateLogic';

describe('Enneagram Gate Logic', () => {
  // =========================================================================
  // RULE 1: Short assessment → Primary CTA
  // =========================================================================
  describe('Rule 1: Short Assessment', () => {
    it('should show primary CTA when assessment_depth is "short"', () => {
      const input: EnneagramGateInput = {
        assessment_depth: 'short',
        confidence_tier: 'high',
        confidence: 0.85,
      };
      
      const state = computeEnneagramGateState(input);
      
      expect(state.needs_deep_assessment).toBe(true);
      expect(state.result_is_preliminary).toBe(true);
      expect(state.show_primary_cta).toBe(true);
      expect(state.show_secondary_cta).toBe(false);
    });
    
    it('should show primary CTA when assessment_depth is undefined', () => {
      const input: EnneagramGateInput = {
        confidence_tier: 'high',
        confidence: 0.9,
      };
      
      const state = computeEnneagramGateState(input);
      
      expect(state.needs_deep_assessment).toBe(true);
      expect(state.result_is_preliminary).toBe(true);
      expect(state.show_primary_cta).toBe(true);
    });
    
    it('should mark result as preliminary for short assessment', () => {
      const input: EnneagramGateInput = {
        assessment_depth: 'short',
        confidence_tier: 'moderate',
      };
      
      const state = computeEnneagramGateState(input);
      
      expect(state.result_is_preliminary).toBe(true);
    });
  });
  
  // =========================================================================
  // RULE 2: Deep + Non-high confidence → Secondary CTA
  // =========================================================================
  describe('Rule 2: Deep + Non-High Confidence', () => {
    it('should show secondary CTA when deep but moderate confidence', () => {
      const input: EnneagramGateInput = {
        assessment_depth: 'deep',
        confidence_tier: 'moderate',
        confidence: 0.6,
      };
      
      const state = computeEnneagramGateState(input);
      
      expect(state.needs_deep_assessment).toBe(false);
      expect(state.suggest_deep_assessment).toBe(true);
      expect(state.result_is_preliminary).toBe(false);
      expect(state.show_primary_cta).toBe(false);
      expect(state.show_secondary_cta).toBe(true);
    });
    
    it('should show secondary CTA when deep but exploratory confidence', () => {
      const input: EnneagramGateInput = {
        assessment_depth: 'deep',
        confidence_tier: 'exploratory',
        confidence: 0.45,
      };
      
      const state = computeEnneagramGateState(input);
      
      expect(state.suggest_deep_assessment).toBe(true);
      expect(state.show_secondary_cta).toBe(true);
    });
    
    it('should show secondary CTA when deep but low confidence', () => {
      const input: EnneagramGateInput = {
        assessment_depth: 'deep',
        confidence_tier: 'low',
        confidence: 0.3,
      };
      
      const state = computeEnneagramGateState(input);
      
      expect(state.suggest_deep_assessment).toBe(true);
      expect(state.show_secondary_cta).toBe(true);
    });
    
    it('should NOT mark result as preliminary for deep assessment', () => {
      const input: EnneagramGateInput = {
        assessment_depth: 'deep',
        confidence_tier: 'moderate',
      };
      
      const state = computeEnneagramGateState(input);
      
      expect(state.result_is_preliminary).toBe(false);
    });
  });
  
  // =========================================================================
  // RULE 3: Deep + High confidence → No CTA
  // =========================================================================
  describe('Rule 3: Deep + High Confidence', () => {
    it('should show no CTA when deep and high confidence', () => {
      const input: EnneagramGateInput = {
        assessment_depth: 'deep',
        confidence_tier: 'high',
        confidence: 0.85,
      };
      
      const state = computeEnneagramGateState(input);
      
      expect(state.needs_deep_assessment).toBe(false);
      expect(state.suggest_deep_assessment).toBe(false);
      expect(state.result_is_preliminary).toBe(false);
      expect(state.show_primary_cta).toBe(false);
      expect(state.show_secondary_cta).toBe(false);
    });
    
    it('should return null CTA copy when no CTA needed', () => {
      const input: EnneagramGateInput = {
        assessment_depth: 'deep',
        confidence_tier: 'high',
        confidence: 0.9,
      };
      
      const state = computeEnneagramGateState(input);
      const copy = getEnneagramCTACopy(state);
      
      expect(copy).toBeNull();
    });
  });
  
  // =========================================================================
  // CTA COPY VERIFICATION (Mirror-safe, no coaching language)
  // =========================================================================
  describe('CTA Copy - Mirror Safe', () => {
    it('should return correct primary CTA copy', () => {
      const input: EnneagramGateInput = {
        assessment_depth: 'short',
        confidence_tier: 'high',
      };
      
      const state = computeEnneagramGateState(input);
      const copy = getEnneagramCTACopy(state);
      
      expect(copy).not.toBeNull();
      expect(copy?.title).toBe("Want a clearer mirror?");
      expect(copy?.body).toContain("This view is based on a shorter Enneagram assessment.");
      expect(copy?.button_text).toBe("Take the deeper assessment");
      expect(copy?.variant).toBe('primary');
    });
    
    it('should return correct secondary CTA copy', () => {
      const input: EnneagramGateInput = {
        assessment_depth: 'deep',
        confidence_tier: 'moderate',
      };
      
      const state = computeEnneagramGateState(input);
      const copy = getEnneagramCTACopy(state);
      
      expect(copy).not.toBeNull();
      expect(copy?.title).toBe("Refine this view");
      expect(copy?.body).toContain("This result is valid");
      expect(copy?.button_text).toBe("Explore a deeper assessment");
      expect(copy?.variant).toBe('secondary');
    });
    
    it('should NOT contain coaching language in primary CTA', () => {
      const forbiddenPhrases = [
        'improve accuracy',
        'fix',
        'you should',
        'recommended',
        'better',
        'more accurate',
      ];
      
      forbiddenPhrases.forEach(phrase => {
        expect(PRIMARY_CTA_COPY.title.toLowerCase()).not.toContain(phrase);
        expect(PRIMARY_CTA_COPY.body.toLowerCase()).not.toContain(phrase);
        expect(PRIMARY_CTA_COPY.button_text.toLowerCase()).not.toContain(phrase);
      });
    });
    
    it('should NOT contain coaching language in secondary CTA', () => {
      const forbiddenPhrases = [
        'improve accuracy',
        'fix',
        'you should',
        'recommended',
      ];
      
      forbiddenPhrases.forEach(phrase => {
        expect(SECONDARY_CTA_COPY.title.toLowerCase()).not.toContain(phrase);
        expect(SECONDARY_CTA_COPY.body.toLowerCase()).not.toContain(phrase);
        expect(SECONDARY_CTA_COPY.button_text.toLowerCase()).not.toContain(phrase);
      });
    });
  });
  
  // =========================================================================
  // MUTUAL EXCLUSIVITY
  // =========================================================================
  describe('CTA Mutual Exclusivity', () => {
    it('should never show both primary and secondary CTA', () => {
      const testCases: EnneagramGateInput[] = [
        { assessment_depth: 'short', confidence_tier: 'high' },
        { assessment_depth: 'short', confidence_tier: 'moderate' },
        { assessment_depth: 'deep', confidence_tier: 'moderate' },
        { assessment_depth: 'deep', confidence_tier: 'high' },
        { assessment_depth: undefined, confidence_tier: 'high' },
      ];
      
      testCases.forEach(input => {
        const state = computeEnneagramGateState(input);
        
        // XOR: only one can be true, or both false
        expect(state.show_primary_cta && state.show_secondary_cta).toBe(false);
      });
    });
  });
  
  // =========================================================================
  // CONVENIENCE FUNCTION
  // =========================================================================
  describe('getEnneagramUpgradeInfo', () => {
    it('should return complete info for short assessment', () => {
      const input: EnneagramGateInput = {
        assessment_depth: 'short',
        confidence_tier: 'moderate',
      };
      
      const info = getEnneagramUpgradeInfo(input);
      
      expect(info.gateState.show_primary_cta).toBe(true);
      expect(info.ctaCopy).not.toBeNull();
      expect(info.showPreliminaryLabel).toBe(true);
    });
    
    it('should return complete info for deep + high', () => {
      const input: EnneagramGateInput = {
        assessment_depth: 'deep',
        confidence_tier: 'high',
      };
      
      const info = getEnneagramUpgradeInfo(input);
      
      expect(info.gateState.show_primary_cta).toBe(false);
      expect(info.gateState.show_secondary_cta).toBe(false);
      expect(info.ctaCopy).toBeNull();
      expect(info.showPreliminaryLabel).toBe(false);
    });
  });
  
  // =========================================================================
  // AGE CALCULATION
  // =========================================================================
  describe('Assessment Age Calculation', () => {
    it('should return null for undefined created_at_iso', () => {
      expect(calculateAssessmentAgeDays(undefined)).toBeNull();
    });
    
    it('should return null for invalid date string', () => {
      expect(calculateAssessmentAgeDays('not-a-date')).toBeNull();
    });
    
    it('should calculate correct age for recent date', () => {
      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);
      
      const age = calculateAssessmentAgeDays(yesterday.toISOString());
      expect(age).toBe(1);
    });
  });
  
  // =========================================================================
  // REFRESH SUGGESTION (Optional feature)
  // =========================================================================
  describe('Refresh Suggestion (6 months)', () => {
    it('should suggest refresh for old deep + high confidence result', () => {
      const sevenMonthsAgo = new Date();
      sevenMonthsAgo.setDate(sevenMonthsAgo.getDate() - 210);
      
      const input: EnneagramGateInput = {
        assessment_depth: 'deep',
        confidence_tier: 'high',
        confidence: 0.9,
        created_at_iso: sevenMonthsAgo.toISOString(),
      };
      
      const state = computeEnneagramGateState(input);
      
      expect(state.suggest_refresh).toBe(true);
      expect(state.show_secondary_cta).toBe(true);
    });
    
    it('should NOT suggest refresh for recent result', () => {
      const oneMonthAgo = new Date();
      oneMonthAgo.setDate(oneMonthAgo.getDate() - 30);
      
      const input: EnneagramGateInput = {
        assessment_depth: 'deep',
        confidence_tier: 'high',
        created_at_iso: oneMonthAgo.toISOString(),
      };
      
      const state = computeEnneagramGateState(input);
      
      expect(state.suggest_refresh).toBe(false);
      expect(state.show_secondary_cta).toBe(false);
    });
  });
});
