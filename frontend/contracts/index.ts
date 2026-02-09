/**
 * Project Mirror V1 Contracts Module
 * 
 * Exports all contract-related functionality for V1 integrity enforcement.
 * 
 * FROZEN: Version 1.0.0
 */

// Contract constants and validators
export {
  // Version
  MIRROR_V1_CONTRACT_VERSION,
  MIRROR_V1_CONTRACT_FROZEN,
  
  // Thresholds
  ENNEAGRAM_INVARIANTS,
  CROSS_LENS_INVARIANTS,
  NARRATIVE_INVARIANTS,
  
  // Types
  type WingState,
  type ConfidenceTier,
  type ContractViolation,
  type ContractValidationResult,
  type FullValidationInput,
  
  // Section A validators
  validateWingDisplay,
  validateHighConfidenceLock,
  validateProbabilitySum,
  
  // Section B validators
  validateCrossLensEligibility,
  validateAdjustmentBounds,
  validateRawPreservation,
  
  // Section C validators
  validateNarrativeLanguage,
  validateUncertaintyVisibility,
  validateTimeBoundLanguage,
  validateAgencyPreservation,
  validateCrossLensContextPresence,
  
  // Full validation
  validateV1Contract,
  
  // Debug logging
  logContractViolation,
  assertContract,
} from './v1IntegrityContract';

// React hooks
export {
  useContractAssertions,
  type AssertionResult,
  
  // Standalone functions
  assertContractInvariant,
  assertEnneagramResult,
  assertNarrativeOutput,
} from './useContractAssertions';
