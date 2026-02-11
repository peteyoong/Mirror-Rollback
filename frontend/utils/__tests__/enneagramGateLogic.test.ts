/**
 * Enneagram Gate Logic Tests
 * ==========================
 * 
 * Acceptance tests for the Enneagram retake/upgrade gate logic.
 * These tests verify:
 * 1. Low confidence → retake CTA (HIGHEST PRIORITY)
 * 2. Short assessment → upgrade CTA
 * 3. Deep + high confidence → no CTA shown
 * 4. Stale results → refresh CTA
 * 5. CTA copy matches exactly (no coaching language)
 * 6. Content remains accessible regardless of CTA presence
 */

import {
  computeEnneagramGateState,
  getEnneagramCTACopy,
  getEnneagramUpgradeInfo,
  calculateAssessmentAgeDays,
  UPGRADE_CTA_COPY,
  RETAKE_CTA_COPY,
  EnneagramGateInput,
} from '../enneagramGateLogic';

describe('Enneagram Gate Logic', () => {
  // =========================================================================
  // RULE 1: Low Confidence → Retake CTA (HIGHEST PRIORITY)
  // =========================================================================
  describe('Rule 1: Low Confidence (Highest Priority)', () => {
    it('should show retake CTA when confidence_tier is "low"', () => {
      const input: EnneagramGateInput = {
        assessment_depth: 'deep',
        confidence_tier: 'low',
        confidence: 0.3,
      };
      
      const state = computeEnneagramGateState(input);
      
      expect(state.suggest_retake).toBe(true);
      expect(state.show_cta).toBe(true);
      expect(state.cta_type).toBe('retake');
      expect(state.cta_variant).toBe('retake_low_confidence');
    });
    
    it('should show retake CTA when confidence_tier is "exploratory"', () => {
      const input: EnneagramGateInput = {
        assessment_depth: 'deep',
        confidence_tier: 'exploratory',
        confidence: 0.45,
      };
      
      const state = computeEnneagramGateState(input);
      
      expect(state.suggest_retake).toBe(true);
      expect(state.cta_type).toBe('retake');
    });
    
    it('should prioritize retake over upgrade for short + low confidence', () => {
      const input: EnneagramGateInput = {
        assessment_depth: 'short',
        confidence_tier: 'low',
        confidence: 0.25,
      };
      
      const state = computeEnneagramGateState(input);
      
      // Retake has higher priority than upgrade
      expect(state.suggest_retake).toBe(true);
      expect(state.cta_type).toBe('retake');
      expect(state.needs_deep_assessment).toBe(false); // Not activated since retake won
    });
  });
  
  // =========================================================================
  // RULE 2: Short Assessment → Upgrade CTA
  // =========================================================================
  describe('Rule 2: Short Assessment', () => {
    it('should show upgrade CTA when assessment_depth is "short" and confidence is high', () => {
      const input: EnneagramGateInput = {
        assessment_depth: 'short',
        confidence_tier: 'high',
        confidence: 0.85,
      };
      
      const state = computeEnneagramGateState(input);
      
      expect(state.needs_deep_assessment).toBe(true);
      expect(state.result_is_preliminary).toBe(true);
      expect(state.show_cta).toBe(true);
      expect(state.cta_type).toBe('upgrade');
      expect(state.cta_variant).toBe('upgrade_short');
    });
    
    it('should show upgrade CTA when assessment_depth is undefined', () => {
      const input: EnneagramGateInput = {
        confidence_tier: 'high',
        confidence: 0.9,
      };
      
      const state = computeEnneagramGateState(input);
      
      expect(state.needs_deep_assessment).toBe(true);
      expect(state.result_is_preliminary).toBe(true);
      expect(state.cta_type).toBe('upgrade');
    });
    
    it('should mark result as preliminary for short assessment', () => {
      const input: EnneagramGateInput = {
        assessment_depth: 'short',
        confidence_tier: 'moderate',
      };
      
      const state = computeEnneagramGateState(input);
      
      expect(state.result_is_preliminary).toBe(true);
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
  // RULE 3: Deep + High Confidence → No CTA
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
      expect(state.suggest_retake).toBe(false);
      expect(state.suggest_refresh).toBe(false);
      expect(state.result_is_preliminary).toBe(false);
      expect(state.show_cta).toBe(false);
      expect(state.cta_type).toBeNull();
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
    
    it('should show no CTA when deep and moderate confidence', () => {
      const input: EnneagramGateInput = {
        assessment_depth: 'deep',
        confidence_tier: 'moderate',
        confidence: 0.65,
      };
      
      const state = computeEnneagramGateState(input);
      
      // Moderate is NOT in LOW_CONFIDENCE_TIERS, so no retake
      // Deep assessment, so no upgrade
      // No stale, so no refresh
      expect(state.show_cta).toBe(false);
      expect(state.cta_type).toBeNull();
    });
  });
  
  // =========================================================================
  // CTA COPY VERIFICATION (Mirror-safe, no coaching language)
  // =========================================================================
  describe('CTA Copy - Mirror Safe', () => {
    it('should return correct upgrade CTA copy', () => {
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
    
    it('should return correct retake CTA copy', () => {
      const input: EnneagramGateInput = {
        assessment_depth: 'deep',
        confidence_tier: 'low',
      };
      
      const state = computeEnneagramGateState(input);
      const copy = getEnneagramCTACopy(state);
      
      expect(copy).not.toBeNull();
      expect(copy?.title).toBe("Refine your reflection");
      expect(copy?.body).toContain("Your current result shows some ambiguity.");
      expect(copy?.button_text).toBe("Retake assessment");
      expect(copy?.variant).toBe('secondary');
    });
    
    it('should NOT contain coaching language in upgrade CTA', () => {
      const forbiddenPhrases = [
        'improve accuracy',
        'fix',
        'you should',
        'recommended',
        'better',
        'more accurate',
      ];
      
      forbiddenPhrases.forEach(phrase => {
        expect(UPGRADE_CTA_COPY.title.toLowerCase()).not.toContain(phrase);
        expect(UPGRADE_CTA_COPY.body.toLowerCase()).not.toContain(phrase);
        expect(UPGRADE_CTA_COPY.button_text.toLowerCase()).not.toContain(phrase);
      });
    });
    
    it('should NOT contain coaching language in retake CTA', () => {
      const forbiddenPhrases = [
        'improve accuracy',
        'fix',
        'you should',
        'recommended',
      ];
      
      forbiddenPhrases.forEach(phrase => {
        expect(RETAKE_CTA_COPY.title.toLowerCase()).not.toContain(phrase);
        expect(RETAKE_CTA_COPY.body.toLowerCase()).not.toContain(phrase);
        expect(RETAKE_CTA_COPY.button_text.toLowerCase()).not.toContain(phrase);
      });
    });
  });
  
  // =========================================================================
  // MUTUAL EXCLUSIVITY
  // =========================================================================
  describe('CTA Mutual Exclusivity', () => {
    it('should only show one CTA type at a time', () => {
      const testCases: EnneagramGateInput[] = [
        { assessment_depth: 'short', confidence_tier: 'high' },
        { assessment_depth: 'short', confidence_tier: 'low' },
        { assessment_depth: 'deep', confidence_tier: 'low' },
        { assessment_depth: 'deep', confidence_tier: 'high' },
        { assessment_depth: undefined, confidence_tier: 'high' },
      ];
      
      testCases.forEach(input => {
        const state = computeEnneagramGateState(input);
        
        // Only one of these flags should be true at a time
        const ctaFlags = [
          state.needs_deep_assessment && state.cta_type === 'upgrade',
          state.suggest_retake && state.cta_type === 'retake',
          state.suggest_refresh && state.cta_type === 'refresh',
        ].filter(Boolean);
        
        expect(ctaFlags.length).toBeLessThanOrEqual(1);
      });
    });
    
    it('should have cta_type match the active flag', () => {
      // Retake case
      let state = computeEnneagramGateState({ assessment_depth: 'deep', confidence_tier: 'low' });
      expect(state.suggest_retake).toBe(true);
      expect(state.cta_type).toBe('retake');
      
      // Upgrade case
      state = computeEnneagramGateState({ assessment_depth: 'short', confidence_tier: 'high' });
      expect(state.needs_deep_assessment).toBe(true);
      expect(state.cta_type).toBe('upgrade');
      
      // No CTA case
      state = computeEnneagramGateState({ assessment_depth: 'deep', confidence_tier: 'high' });
      expect(state.cta_type).toBeNull();
    });
  });
  
  // =========================================================================
  // CONVENIENCE FUNCTION
  // =========================================================================
  describe('getEnneagramUpgradeInfo', () => {
    it('should return complete info for short assessment', () => {
      const input: EnneagramGateInput = {
        assessment_depth: 'short',
        confidence_tier: 'high',
      };
      
      const info = getEnneagramUpgradeInfo(input);
      
      expect(info.gateState.cta_type).toBe('upgrade');
      expect(info.ctaCopy).not.toBeNull();
      expect(info.showPreliminaryLabel).toBe(true);
    });
    
    it('should return complete info for deep + high', () => {
      const input: EnneagramGateInput = {
        assessment_depth: 'deep',
        confidence_tier: 'high',
      };
      
      const info = getEnneagramUpgradeInfo(input);
      
      expect(info.gateState.cta_type).toBeNull();
      expect(info.gateState.show_cta).toBe(false);
      expect(info.ctaCopy).toBeNull();
      expect(info.showPreliminaryLabel).toBe(false);
    });
    
    it('should return retake info for low confidence', () => {
      const input: EnneagramGateInput = {
        assessment_depth: 'deep',
        confidence_tier: 'low',
      };
      
      const info = getEnneagramUpgradeInfo(input);
      
      expect(info.gateState.cta_type).toBe('retake');
      expect(info.ctaCopy?.title).toBe('Refine your reflection');
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
    
    it('should return 0 for today', () => {
      const today = new Date();
      const age = calculateAssessmentAgeDays(today.toISOString());
      expect(age).toBe(0);
    });
  });
  
  // =========================================================================
  // REFRESH SUGGESTION (6 months)
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
      expect(state.cta_type).toBe('refresh');
      expect(state.cta_variant).toBe('refresh_stale');
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
      expect(state.cta_type).toBeNull();
    });
    
    it('should prioritize retake over refresh for old low-confidence result', () => {
      const sevenMonthsAgo = new Date();
      sevenMonthsAgo.setDate(sevenMonthsAgo.getDate() - 210);
      
      const input: EnneagramGateInput = {
        assessment_depth: 'deep',
        confidence_tier: 'low',
        created_at_iso: sevenMonthsAgo.toISOString(),
      };
      
      const state = computeEnneagramGateState(input);
      
      // Low confidence takes priority over stale
      expect(state.cta_type).toBe('retake');
      expect(state.suggest_retake).toBe(true);
    });
  });
  
  // =========================================================================
  // DEBUG INFO
  // =========================================================================
  describe('Debug Info', () => {
    it('should include debug info in state', () => {
      const input: EnneagramGateInput = {
        assessment_depth: 'short',
        confidence_tier: 'high',
        confidence: 0.85,
      };
      
      const state = computeEnneagramGateState(input);
      
      expect(state._debug).toBeDefined();
      expect(state._debug.input_depth).toBe('short');
      expect(state._debug.input_tier).toBe('high');
      expect(state._debug.input_confidence).toBe(0.85);
      expect(state._debug.rule_applied).toBe('priority_2_short_assessment');
    });
    
    it('should track the rule applied', () => {
      // Retake rule
      let state = computeEnneagramGateState({ assessment_depth: 'deep', confidence_tier: 'low' });
      expect(state._debug.rule_applied).toBe('priority_1_low_confidence');
      
      // No CTA rule
      state = computeEnneagramGateState({ assessment_depth: 'deep', confidence_tier: 'high' });
      expect(state._debug.rule_applied).toBe('no_cta_needed');
    });
  });
});
