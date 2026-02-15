/**
 * Journal Prefill Utilities
 * 
 * Shared helpers for navigating to Journal with prefilled text from lens screens.
 * Keeps navigation logic consistent and avoids Zustand store writes from lens screens.
 */

import { Router } from 'expo-router';

/**
 * Build the prefill text for Journal entry.
 * @param question - The primary reflect question shown in the lens
 * @param continuation - Optional follow-up line (e.g., "What's one small action...")
 * @returns Combined prefill text with blank line separator if continuation exists
 */
export function buildJournalPrefill(question: string, continuation?: string): string {
  if (!question) return '';
  if (continuation && continuation.trim()) {
    return `${question.trim()}\n\n${continuation.trim()}`;
  }
  return question.trim();
}

/**
 * Navigate to Journal tab with prefilled text.
 * Uses dismissAll() first to close any modals/lens screens before switching tabs.
 * 
 * @param router - expo-router Router instance
 * @param prefill - The text to prefill in the journal input
 * @param source - The lens source (e.g., 'astrology', 'human_design', 'numerology', 'enneagram')
 */
export function goToJournalWithPrefill(
  router: Router,
  prefill: string,
  source: 'astrology' | 'human_design' | 'numerology' | 'enneagram' | string
): void {
  try {
    // Dismiss any open modals/screens first
    router.dismissAll();
  } catch (e) {
    // dismissAll may throw if no screens to dismiss - that's fine
    console.log('[JournalPrefill] No screens to dismiss');
  }
  
  // Navigate to Journal tab with prefill params
  router.push({
    pathname: '/(tabs)/journal',
    params: {
      prefill,
      source,
    },
  });
}

// Lens-specific continuation prompts
export const LENS_CONTINUATIONS: Record<string, string> = {
  astrology: "If you had to name the theme in one sentence, what would it be?",
  human_design: "Where do you feel this most in your body: yes, no, or neutral?",
  numerology: "What's one small action that would honor this pattern today?",
  enneagram: "", // Enneagram already has its own journal prompts
};
