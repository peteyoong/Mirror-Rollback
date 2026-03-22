/**
 * Dominant Truth Service
 * Master Layer Integration - Cross-Surface Reuse
 * 
 * This is the SINGLE SOURCE OF TRUTH for the daily dominant pattern.
 * Used by: Home, Mirror Chat, Journal, Lifeline
 */

import {
  getDominantTruth,
  buildCollapsedInsights,
  buildLifeChapterAnalysis,
  buildAspectPatternAnalysis,
} from './astrology/astrologyInterpreter';

import {
  FullChartData,
  Timeframe,
  DominantTruth,
  DominantTruthNarrative,
  CollapsedInsights,
} from './astrology/astrologyTypes';

import api from './api';

// ============================================
// TYPES
// ============================================

export interface DailyDominantTruth {
  headline: string;
  core: string;
  lifeArea: string;
  mistake: string;
  question: string;
  confidence: number;
  recognitionLine: string | null;
  timeframeContext: string;
  dominantTheme: string;
  supportingThemes: string[];
  hasChapterAlignment: boolean;
  hasPatternAlignment: boolean;
}

export interface DominantTruthContext {
  // For Home - minimal
  homeHeadline: string;
  homeSupportingLine: string | null;
  
  // For Chat - system context
  chatSystemContext: string;
  chatTopChip: string;
  
  // For Journal - prefill
  journalTitle: string;
  journalPrefill: string;
  
  // For Lifeline - optional tag
  lifelineTag: string;
  
  // Full data
  full: DailyDominantTruth | null;
}

// Cache for the current day
let cachedTruth: {
  userId: string;
  date: string;
  truth: DominantTruthContext | null;
} | null = null;

// ============================================
// MAIN SERVICE FUNCTION
// ============================================

/**
 * Get the daily dominant truth for a user
 * This is the primary entry point for all surfaces
 */
export async function getDailyDominantTruth(
  userId: string,
  timeframe: Timeframe = 'today'
): Promise<DominantTruthContext | null> {
  const today = new Date().toISOString().split('T')[0];
  
  // Check cache
  if (cachedTruth?.userId === userId && cachedTruth?.date === today && cachedTruth?.truth) {
    return cachedTruth.truth;
  }
  
  try {
    // Fetch chart data
    const response = await api.get(`/astrology/chart/${userId}`);
    const chartData: FullChartData = response.data;
    
    if (!chartData?.success) {
      return null;
    }
    
    // Build analysis
    const chapterAnalysis = buildLifeChapterAnalysis(chartData);
    const patternAnalysis = buildAspectPatternAnalysis(chartData);
    
    // Get dominant truth
    const dominantTruth = getDominantTruth(chartData, chapterAnalysis, patternAnalysis, timeframe);
    
    if (!dominantTruth) {
      // No dominant truth detected - return null context
      cachedTruth = { userId, date: today, truth: null };
      return null;
    }
    
    // Build narrative
    const collapsedInsights = buildCollapsedInsights(chartData, chapterAnalysis, patternAnalysis, timeframe);
    const narrative = collapsedInsights.narrative;
    
    if (!narrative) {
      cachedTruth = { userId, date: today, truth: null };
      return null;
    }
    
    // Build full daily truth
    const full: DailyDominantTruth = {
      headline: narrative.headline,
      core: narrative.coreTruth,
      lifeArea: dominantTruth.lifeArea,
      mistake: narrative.whatGoesWrong,
      question: narrative.question,
      confidence: dominantTruth.confidenceScore,
      recognitionLine: narrative.recognitionLine,
      timeframeContext: narrative.timeframeContext,
      dominantTheme: dominantTruth.dominantTheme,
      supportingThemes: dominantTruth.supportingThemes,
      hasChapterAlignment: !!dominantTruth.chapterType,
      hasPatternAlignment: !!dominantTruth.patternType,
    };
    
    // Build context for each surface
    const context: DominantTruthContext = {
      // HOME: headline only, skimmable
      homeHeadline: narrative.headline,
      homeSupportingLine: dominantTruth.confidenceScore >= 70 
        ? narrative.recognitionLine 
        : null,
      
      // CHAT: full context for system prompt
      chatSystemContext: buildChatSystemContext(full),
      chatTopChip: `Today's pattern: ${truncateHeadline(narrative.headline, 40)}`,
      
      // JOURNAL: prefill with headline + question
      journalTitle: 'Something to look at',
      journalPrefill: buildJournalPrefill(full),
      
      // LIFELINE: optional tag
      lifelineTag: `Connected to: ${truncateHeadline(narrative.headline, 30)}`,
      
      // Full data for detailed views
      full,
    };
    
    // Cache
    cachedTruth = { userId, date: today, truth: context };
    
    return context;
  } catch (error) {
    console.error('[DominantTruthService] Error fetching:', error);
    return null;
  }
}

/**
 * Clear cache (call when user logs out or data changes)
 */
export function clearDominantTruthCache(): void {
  cachedTruth = null;
}

// ============================================
// HELPER FUNCTIONS
// ============================================

/**
 * Build system context for Mirror Chat
 */
function buildChatSystemContext(truth: DailyDominantTruth): string {
  return `
CURRENT DOMINANT PATTERN (from astrology transits):
Headline: ${truth.headline}
Core insight: ${truth.core}
Life area: ${truth.lifeArea}
Common mistake: ${truth.mistake}
Reflection question: ${truth.question}
Confidence: ${truth.confidence}%

GUIDANCE:
- The user may or may not be aware of this pattern
- If relevant to their question, gently connect back to this pattern
- Do NOT force the connection - only mention if it naturally relates
- If they ask about something unrelated, respond to their actual question
- Use this as background context, not a script to follow
`.trim();
}

/**
 * Build journal prefill content
 */
function buildJournalPrefill(truth: DailyDominantTruth): string {
  return `${truth.headline}

${truth.question}

`;
}

/**
 * Truncate headline for chips/tags
 */
function truncateHeadline(headline: string, maxLength: number): string {
  if (headline.length <= maxLength) return headline;
  return headline.substring(0, maxLength - 3) + '...';
}

// ============================================
// SURFACE-SPECIFIC HOOKS
// ============================================

/**
 * Get Home-specific data (headline only)
 */
export async function getDominantTruthForHome(userId: string): Promise<{
  headline: string;
  supportingLine: string | null;
  hasPattern: boolean;
} | null> {
  const context = await getDailyDominantTruth(userId, 'today');
  if (!context) return null;
  
  return {
    headline: context.homeHeadline,
    supportingLine: context.homeSupportingLine,
    hasPattern: true,
  };
}

/**
 * Get Chat-specific data (system context + chip)
 */
export async function getDominantTruthForChat(userId: string): Promise<{
  systemContext: string;
  topChip: string;
  hasPattern: boolean;
} | null> {
  const context = await getDailyDominantTruth(userId, 'today');
  if (!context) return null;
  
  return {
    systemContext: context.chatSystemContext,
    topChip: context.chatTopChip,
    hasPattern: true,
  };
}

/**
 * Get Journal-specific data (prefill)
 */
export async function getDominantTruthForJournal(userId: string): Promise<{
  title: string;
  prefill: string;
  question: string;
  hasPattern: boolean;
} | null> {
  const context = await getDailyDominantTruth(userId, 'today');
  if (!context || !context.full) return null;
  
  return {
    title: context.journalTitle,
    prefill: context.journalPrefill,
    question: context.full.question,
    hasPattern: true,
  };
}

/**
 * Get Lifeline-specific data (optional tag)
 */
export async function getDominantTruthForLifeline(userId: string): Promise<{
  suggestedTag: string;
  headline: string;
  hasPattern: boolean;
} | null> {
  const context = await getDailyDominantTruth(userId, 'today');
  if (!context || !context.full) return null;
  
  return {
    suggestedTag: context.lifelineTag,
    headline: context.full.headline,
    hasPattern: true,
  };
}

/**
 * Get full dominant truth data (for Today tab and detailed views)
 */
export async function getFullDominantTruth(
  userId: string,
  timeframe: Timeframe = 'today'
): Promise<DailyDominantTruth | null> {
  const context = await getDailyDominantTruth(userId, timeframe);
  return context?.full || null;
}
