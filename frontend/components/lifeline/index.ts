/**
 * Lifeline Components Index
 * 
 * Export all lifeline components for easy importing.
 */

export { default as LifelineTimeline } from './LifelineTimeline';
export { default as LifelineEventCard, type LifelineEvent } from './LifelineEventCard';
export { default as LifelineEventEditor } from './LifelineEventEditor';
export { default as LifelineEmptyState } from './LifelineEmptyState';
export { default as LifelineInlineOnboarding } from './LifelineInlineOnboarding';
export { default as LifelinePatterns, type LifelinePatternsData, type PatternInsight } from './LifelinePatterns';
export { default as LifelinePatternSynthesisCard } from './LifelinePatternSynthesisCard';
export { default as LifelineGapPrompt, type GapPromptData } from './LifelineGapPrompt';
export { default as TimeDistanceTimeline } from './TimeDistanceTimeline';
export { default as LifelineAddMenu } from './LifelineAddMenu';
export { default as LifelineFramingCard } from './LifelineFramingCard';
export { default as LifelineMiniMap } from './LifelineMiniMap';
export { default as LifelineStarterPrompts } from './LifelineStarterPrompts';
export { 
  default as MemoryEchoPrompt, 
  type MemoryEchoData, 
  type EarlierMomentPrefill,
  generateEchoData,
  canShowEcho,
  resetEchoCount,
} from './MemoryEchoPrompt';
export {
  StormBadge,
  StormHighlight,
  StormModal,
  IntensePeriods,
  detectPatternStorms,
  getStormForEvent,
  isFirstEventInStorm,
  type PatternStorm,
} from './PatternStorm';
export {
  ResonanceMarker,
  ResonanceModal,
  ResonanceInline,
  ChartResonanceSection,
  type ChartResonance,
  type PatternResonanceSummary,
} from './ChartResonance';
