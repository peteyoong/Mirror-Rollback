/**
 * useAdaptationCues Hook - V1
 * ===========================
 * 
 * Provides subtle visual adaptation cues based on engagement state.
 * 
 * ADAPTATION MODES:
 * - sharpen: tighter spacing, higher contrast, less padding
 * - intensify: normal spacing, stronger emphasis
 * - deepen: more breathing room, softer pacing
 * - neutral: default styling
 * 
 * DOES NOT add visible labels like "adapted" or "personalized".
 * Changes are subtle enough that user feels "this landed differently".
 */

import { useMemo } from 'react';
import { StyleSheet, TextStyle, ViewStyle } from 'react-native';

// =============================================================================
// TYPES
// =============================================================================

export type AdaptationMode = 'sharpen' | 'intensify' | 'deepen' | 'neutral';
export type FirstLineSource = 'echo' | 'snap';

export interface AdaptationResponse {
  adaptation_mode?: AdaptationMode | null;
  first_line_source?: FirstLineSource | null;
  behavior_snap?: string | null;
  engagement_state?: string | null;
}

export interface AdaptationCueStyles {
  // Hero container adjustments
  heroContainer: ViewStyle;
  // First line text adjustments
  firstLineText: TextStyle;
  // Body text adjustments
  bodyText: TextStyle;
  // Whisper line (continuity cue)
  whisperLine: TextStyle;
  // Card spacing
  cardSpacing: ViewStyle;
}

export interface AdaptationCues {
  mode: AdaptationMode;
  firstLineSource: FirstLineSource;
  styles: AdaptationCueStyles;
  showWhisper: boolean;
  whisperText: string | null;
  debugInfo: {
    mode: AdaptationMode;
    source: FirstLineSource;
    whisperShown: boolean;
  };
}

// =============================================================================
// WHISPER TEXTS (Optional continuity cues)
// =============================================================================

const WHISPER_TEXTS = {
  repeat_open: ['Back here.', 'Again.', 'Still here.'],
  returned_same_day: ['Back.', 'Again.', 'Here.'],
};

// =============================================================================
// BASE STYLES
// =============================================================================

const BASE_STYLES: AdaptationCueStyles = {
  heroContainer: {
    paddingHorizontal: 20,
    paddingVertical: 24,
  },
  firstLineText: {
    fontSize: 18,
    lineHeight: 26,
    fontWeight: '500',
    opacity: 1,
  },
  bodyText: {
    fontSize: 16,
    lineHeight: 24,
    opacity: 0.9,
  },
  whisperLine: {
    fontSize: 12,
    opacity: 0,
    marginBottom: 0,
  },
  cardSpacing: {
    marginBottom: 16,
  },
};

// =============================================================================
// ADAPTATION STYLE MODIFIERS
// =============================================================================

const SHARPEN_MODIFIERS: Partial<AdaptationCueStyles> = {
  heroContainer: {
    paddingHorizontal: 18,  // Slightly tighter
    paddingVertical: 20,    // Less padding
  },
  firstLineText: {
    fontSize: 18,
    lineHeight: 24,         // Tighter line spacing
    fontWeight: '600',      // Slightly heavier
    opacity: 1,
  },
  bodyText: {
    fontSize: 16,
    lineHeight: 22,         // Tighter
    opacity: 0.95,          // Higher contrast
  },
  whisperLine: {
    opacity: 0,
  },
  cardSpacing: {
    marginBottom: 14,       // Tighter
  },
};

const INTENSIFY_MODIFIERS: Partial<AdaptationCueStyles> = {
  heroContainer: {
    paddingHorizontal: 20,
    paddingVertical: 24,
  },
  firstLineText: {
    fontSize: 19,           // Slightly larger
    lineHeight: 26,
    fontWeight: '600',      // Stronger emphasis
    opacity: 1,
  },
  bodyText: {
    fontSize: 16,
    lineHeight: 24,
    opacity: 0.92,
  },
  whisperLine: {
    opacity: 0,
  },
  cardSpacing: {
    marginBottom: 16,
  },
};

const DEEPEN_MODIFIERS: Partial<AdaptationCueStyles> = {
  heroContainer: {
    paddingHorizontal: 22,  // More breathing room
    paddingVertical: 28,    // More padding
  },
  firstLineText: {
    fontSize: 18,
    lineHeight: 28,         // More line height
    fontWeight: '500',
    opacity: 0.95,          // Slightly softer
  },
  bodyText: {
    fontSize: 16,
    lineHeight: 26,         // More breathing room
    opacity: 0.88,          // Softer
  },
  whisperLine: {
    fontSize: 12,
    opacity: 0.4,           // Visible but subtle
    marginBottom: 8,
  },
  cardSpacing: {
    marginBottom: 18,       // More space
  },
};

// =============================================================================
// HOOK
// =============================================================================

export function useAdaptationCues(response: AdaptationResponse): AdaptationCues {
  return useMemo(() => {
    const mode: AdaptationMode = (response.adaptation_mode as AdaptationMode) || 'neutral';
    const firstLineSource: FirstLineSource = (response.first_line_source as FirstLineSource) || 'snap';
    
    // Determine if we should show whisper
    // Only show for deepen mode with echo source
    const engagementState = response.engagement_state;
    const isRepeatOrReturn = 
      engagementState === 'captured' || 
      response.behavior_snap?.toLowerCase().includes('again') ||
      response.behavior_snap?.toLowerCase().includes('back');
    
    const showWhisper = 
      mode === 'deepen' && 
      firstLineSource === 'echo' && 
      isRepeatOrReturn;
    
    // Get whisper text
    let whisperText: string | null = null;
    if (showWhisper) {
      const whispers = WHISPER_TEXTS.repeat_open;
      const dayOfYear = Math.floor(Date.now() / 86400000) % whispers.length;
      whisperText = whispers[dayOfYear];
    }
    
    // Compute styles based on mode
    let styleModifiers: Partial<AdaptationCueStyles> = {};
    
    switch (mode) {
      case 'sharpen':
        styleModifiers = SHARPEN_MODIFIERS;
        break;
      case 'intensify':
        styleModifiers = INTENSIFY_MODIFIERS;
        break;
      case 'deepen':
        styleModifiers = DEEPEN_MODIFIERS;
        break;
      default:
        styleModifiers = {};
    }
    
    // Merge base styles with modifiers
    const styles: AdaptationCueStyles = {
      heroContainer: { ...BASE_STYLES.heroContainer, ...styleModifiers.heroContainer },
      firstLineText: { ...BASE_STYLES.firstLineText, ...styleModifiers.firstLineText },
      bodyText: { ...BASE_STYLES.bodyText, ...styleModifiers.bodyText },
      whisperLine: { ...BASE_STYLES.whisperLine, ...styleModifiers.whisperLine },
      cardSpacing: { ...BASE_STYLES.cardSpacing, ...styleModifiers.cardSpacing },
    };
    
    return {
      mode,
      firstLineSource,
      styles,
      showWhisper,
      whisperText,
      debugInfo: {
        mode,
        source: firstLineSource,
        whisperShown: showWhisper,
      },
    };
  }, [
    response.adaptation_mode, 
    response.first_line_source,
    response.engagement_state,
    response.behavior_snap,
  ]);
}

// =============================================================================
// DEBUG HELPER
// =============================================================================

export function logAdaptationCues(cues: AdaptationCues): void {
  if (__DEV__ || process.env.EXPO_PUBLIC_DEBUG_MIRROR === 'true') {
    console.log('[AdaptationCues]', JSON.stringify(cues.debugInfo, null, 2));
  }
}

export default useAdaptationCues;
