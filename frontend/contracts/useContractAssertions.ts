/**
 * V1 Contract Runtime Assertions
 * 
 * Provides hooks for runtime validation that log violations in DEBUG_MIRROR mode.
 * These assertions never crash the app - they only log warnings for debugging.
 * 
 * Usage:
 *   import { useContractAssertions } from '@/contracts/useContractAssertions';
 *   
 *   const { assertWingDisplay, assertNarrative } = useContractAssertions();
 *   assertWingDisplay(wingState);
 */

import { useCallback, useMemo } from 'react';
import {
  MIRROR_V1_CONTRACT_VERSION,
  validateWingDisplay,
  validateHighConfidenceLock,
  validateProbabilitySum,
  validateCrossLensEligibility,
  validateAdjustmentBounds,
  validateNarrativeLanguage,
  validateUncertaintyVisibility,
  validateAgencyPreservation,
  validateV1Contract,
  ContractViolation,
  FullValidationInput,
  logContractViolation,
} from './v1IntegrityContract';

// ============================================
// DEBUG MODE CHECK
// ============================================

const IS_DEBUG = process.env.EXPO_PUBLIC_DEBUG_MIRROR === 'true';

// ============================================
// ASSERTION RESULT TYPE
// ============================================

export interface AssertionResult {
  passed: boolean;
  violations: ContractViolation[];
  contractVersion: string;
}

// ============================================
// HOOK: useContractAssertions
// ============================================

export function useContractAssertions() {
  
  /**
   * Assert wing display is valid
   */
  const assertWingDisplay = useCallback((wingState: string | null | undefined): AssertionResult => {
    const violation = validateWingDisplay(wingState);
    
    if (violation && IS_DEBUG) {
      logContractViolation(violation);
    }
    
    return {
      passed: violation === null,
      violations: violation ? [violation] : [],
      contractVersion: MIRROR_V1_CONTRACT_VERSION,
    };
  }, []);
  
  /**
   * Assert high confidence results are not being altered
   */
  const assertHighConfidenceLock = useCallback((
    confidenceTier: string,
    adjustmentApplied: boolean
  ): AssertionResult => {
    const violation = validateHighConfidenceLock(confidenceTier, adjustmentApplied);
    
    if (violation && IS_DEBUG) {
      logContractViolation(violation);
    }
    
    return {
      passed: violation === null,
      violations: violation ? [violation] : [],
      contractVersion: MIRROR_V1_CONTRACT_VERSION,
    };
  }, []);
  
  /**
   * Assert narrative language is safe
   */
  const assertNarrativeLanguage = useCallback((narrativeText: string): AssertionResult => {
    const violations = validateNarrativeLanguage(narrativeText);
    
    if (IS_DEBUG) {
      for (const violation of violations) {
        logContractViolation(violation);
      }
    }
    
    return {
      passed: violations.length === 0,
      violations,
      contractVersion: MIRROR_V1_CONTRACT_VERSION,
    };
  }, []);
  
  /**
   * Assert reflection prompt preserves agency
   */
  const assertAgencyPreservation = useCallback((reflectionPrompt: string): AssertionResult => {
    const violation = validateAgencyPreservation(reflectionPrompt);
    
    if (violation && IS_DEBUG) {
      logContractViolation(violation);
    }
    
    return {
      passed: violation === null,
      violations: violation ? [violation] : [],
      contractVersion: MIRROR_V1_CONTRACT_VERSION,
    };
  }, []);
  
  /**
   * Assert cross-lens adjustment eligibility
   */
  const assertCrossLensEligibility = useCallback((
    confidenceTier: string,
    top2Gap: number,
    assessmentDepth: string,
    longitudinalSignals: boolean,
    adjustmentApplied: boolean
  ): AssertionResult => {
    const violation = validateCrossLensEligibility(
      confidenceTier,
      top2Gap,
      assessmentDepth,
      longitudinalSignals,
      adjustmentApplied
    );
    
    if (violation && IS_DEBUG) {
      logContractViolation(violation);
    }
    
    return {
      passed: violation === null,
      violations: violation ? [violation] : [],
      contractVersion: MIRROR_V1_CONTRACT_VERSION,
    };
  }, []);
  
  /**
   * Assert adjustment bounds
   */
  const assertAdjustmentBounds = useCallback((
    adjustments: Record<string, number>
  ): AssertionResult => {
    const violations = validateAdjustmentBounds(adjustments);
    
    if (IS_DEBUG) {
      for (const violation of violations) {
        logContractViolation(violation);
      }
    }
    
    return {
      passed: violations.length === 0,
      violations,
      contractVersion: MIRROR_V1_CONTRACT_VERSION,
    };
  }, []);
  
  /**
   * Full contract validation
   */
  const assertFullContract = useCallback((input: FullValidationInput): AssertionResult => {
    const result = validateV1Contract(input);
    
    if (IS_DEBUG) {
      for (const violation of result.violations) {
        logContractViolation(violation);
      }
      
      if (!result.valid) {
        console.error(
          `🚨 [CONTRACT] V1 Integrity Contract violated (${result.violations.filter(v => v.severity === 'critical').length} critical)`
        );
      }
    }
    
    return {
      passed: result.valid,
      violations: result.violations,
      contractVersion: result.contractVersion,
    };
  }, []);
  
  return useMemo(() => ({
    // Individual assertions
    assertWingDisplay,
    assertHighConfidenceLock,
    assertNarrativeLanguage,
    assertAgencyPreservation,
    assertCrossLensEligibility,
    assertAdjustmentBounds,
    
    // Full validation
    assertFullContract,
    
    // Contract info
    contractVersion: MIRROR_V1_CONTRACT_VERSION,
    isDebugMode: IS_DEBUG,
  }), [
    assertWingDisplay,
    assertHighConfidenceLock,
    assertNarrativeLanguage,
    assertAgencyPreservation,
    assertCrossLensEligibility,
    assertAdjustmentBounds,
    assertFullContract,
  ]);
}

// ============================================
// STANDALONE ASSERTION FUNCTIONS
// ============================================

/**
 * Standalone assertion for use outside React components
 */
export function assertContractInvariant(
  invariantName: string,
  validator: () => ContractViolation | null
): boolean {
  const violation = validator();
  
  if (violation && IS_DEBUG) {
    logContractViolation(violation);
  }
  
  return violation === null;
}

/**
 * Assert and log full Enneagram result
 */
export function assertEnneagramResult(result: {
  wingState: string | null;
  confidenceTier: string;
  typeProbabilities: Record<string, number>;
  adjustmentApplied: boolean;
}): AssertionResult {
  const violations: ContractViolation[] = [];
  
  const wingViolation = validateWingDisplay(result.wingState);
  if (wingViolation) violations.push(wingViolation);
  
  const highConfViolation = validateHighConfidenceLock(
    result.confidenceTier,
    result.adjustmentApplied
  );
  if (highConfViolation) violations.push(highConfViolation);
  
  const probViolation = validateProbabilitySum(result.typeProbabilities);
  if (probViolation) violations.push(probViolation);
  
  if (IS_DEBUG) {
    for (const violation of violations) {
      logContractViolation(violation);
    }
  }
  
  return {
    passed: violations.filter(v => v.severity === 'critical').length === 0,
    violations,
    contractVersion: MIRROR_V1_CONTRACT_VERSION,
  };
}

/**
 * Assert narrative output
 */
export function assertNarrativeOutput(narrative: {
  patternSummary: string;
  confidenceFraming: string | null;
  crossLensContext: string | null;
  reflectionPrompt: string;
  confidenceTier: string;
  uncertaintyVisible: boolean;
  adjustmentApplied: boolean;
}): AssertionResult {
  const violations: ContractViolation[] = [];
  
  // Check all narrative text
  const fullText = [
    narrative.patternSummary,
    narrative.confidenceFraming,
    narrative.crossLensContext,
    narrative.reflectionPrompt,
  ].filter(Boolean).join(' ');
  
  violations.push(...validateNarrativeLanguage(fullText));
  
  // Check uncertainty visibility
  const uncertaintyViolation = validateUncertaintyVisibility(
    narrative.confidenceTier,
    narrative.uncertaintyVisible,
    narrative.confidenceFraming
  );
  if (uncertaintyViolation) violations.push(uncertaintyViolation);
  
  // Check agency in reflection prompt
  const agencyViolation = validateAgencyPreservation(narrative.reflectionPrompt);
  if (agencyViolation) violations.push(agencyViolation);
  
  if (IS_DEBUG) {
    for (const violation of violations) {
      logContractViolation(violation);
    }
  }
  
  return {
    passed: violations.filter(v => v.severity === 'critical').length === 0,
    violations,
    contractVersion: MIRROR_V1_CONTRACT_VERSION,
  };
}
