/**
 * HomeV2 - Restructured Home Tab Layout
 * 
 * Phase 1: Structural Reset
 * Phase 2: Resonance Calibration - Copy tightening, visual hierarchy
 * 
 * Two unified sections:
 * 1. TODAY - Primary headline, timestamp, themes, single reflection question, Reflect Now button
 * 2. YOUR CURRENT CHAPTER - Slowest transit / key point, See timeline link
 * 
 * No changes to backend logic or APIs.
 * Preserves all existing data calls.
 */

import React, { useState, useCallback, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Colors } from '../constants/colors';
import { Spacing } from '../constants/spacing';
import { DailyFocusState } from './DailyFocusCard';
import { getDailyFocus, DailyFocusResponse } from '../services/api';
import { 
  getTransitInsightNow, 
  TransitInterpretation,
} from '../services/transitService';
import { BUILD_ENV } from '../utils/buildInfo';
import AsyncStorage from '@react-native-async-storage/async-storage';
import SectionLabel from './SectionLabel';

interface HomeV2Props {
  userId: string;
  keystone: {
    reflect_question: string;
    keystone: string;
    micro_affirmation: string;
    title: string;
    date: string;
  } | null;
  isLoading: boolean;
  onFocusStateChange?: (state: DailyFocusState) => void;
}

// ============================================
// TEXT PROCESSING UTILITIES
// ============================================

// Format timestamp - simpler, just time
const formatTime = (isoString: string): string => {
  try {
    const date = new Date(isoString);
    return date.toLocaleString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    }).toLowerCase();
  } catch {
    return 'now';
  }
};

// Clean headline: Remove astrological jargon, keep first sentence only, max 140 chars
const cleanHeadline = (raw: string): string => {
  if (!raw) return 'A moment of quiet presence.';
  
  // Phrases to remove (astrological/technical language)
  const jargonPatterns = [
    /transiting\s+\w+/gi,
    /pronounced\s+polarity/gi,
    /opportunity\s+between/gi,
    /natal\s+\w+/gi,
    /\(.*?\)/g,  // Remove parenthetical explanations
    /mercury|venus|mars|jupiter|saturn|uranus|neptune|pluto|sun|moon/gi,
  ];
  
  let cleaned = raw;
  jargonPatterns.forEach(pattern => {
    cleaned = cleaned.replace(pattern, '');
  });
  
  // Clean up extra spaces
  cleaned = cleaned.replace(/\s+/g, ' ').trim();
  
  // Take first sentence only
  const firstSentence = cleaned.split(/[.!?]/)[0].trim();
  
  // Ensure it ends properly
  let result = firstSentence;
  if (result && !result.match(/[.!?]$/)) {
    result += '.';
  }
  
  // Truncate to 140 chars if needed
  if (result.length > 140) {
    result = result.substring(0, 137).trim() + '...';
  }
  
  // Fallback if too short or empty after cleaning
  if (result.length < 10) {
    return 'A quiet moment for inner reflection.';
  }
  
  return result;
};

// Extract simple themes - lowercase, max 3
const extractThemes = (keyPoints: string[]): string[] => {
  const themeMap: Record<string, string> = {
    'communication': 'communication',
    'express': 'expression',
    'relationship': 'relationships',
    'connection': 'connection',
    'work': 'work',
    'career': 'purpose',
    'professional': 'work',
    'emotion': 'feelings',
    'feeling': 'feelings',
    'inner': 'inner life',
    'change': 'change',
    'transform': 'transformation',
    'rest': 'rest',
    'peace': 'stillness',
    'calm': 'calm',
    'growth': 'growth',
    'expand': 'expansion',
    'learn': 'learning',
    'health': 'body',
    'body': 'body',
    'energy': 'energy',
    'reflect': 'reflection',
    'notice': 'awareness',
    'attention': 'attention',
    'depth': 'depth',
    'identity': 'identity',
    'structure': 'structure',
  };
  
  const themes: string[] = [];
  
  if (keyPoints && keyPoints.length > 0) {
    keyPoints.slice(0, 3).forEach(point => {
      const lowerPoint = point.toLowerCase();
      for (const [keyword, theme] of Object.entries(themeMap)) {
        if (lowerPoint.includes(keyword) && !themes.includes(theme)) {
          themes.push(theme);
          break;
        }
      }
    });
  }
  
  // Fallback themes
  if (themes.length === 0) {
    return ['presence', 'reflection'];
  }
  
  return themes.slice(0, 3);
};

// Clean chapter headline: max 110 chars, one sentence, grounded
const cleanChapterHeadline = (raw: string): string => {
  if (!raw) return 'A season of noticing what wants attention.';
  
  // If the raw text has astrological jargon that will leave fragments, use fallback
  const hasHeavyJargon = /transiting\s+(mercury|venus|mars|jupiter|saturn|sun|moon)/i.test(raw) ||
    /natal\s+(mercury|venus|mars|jupiter|saturn|pluto)/i.test(raw) ||
    /polarity\s+between/i.test(raw);
  
  if (hasHeavyJargon) {
    // Extract the meaningful part after common patterns
    const meaningfulPatterns = [
      /you may notice\s+(.+)/i,
      /this invites\s+(.+)/i,
      /there's an?\s+(.+)/i,
      /notice\s+(.+)/i,
    ];
    
    for (const pattern of meaningfulPatterns) {
      const match = raw.match(pattern);
      if (match && match[1] && match[1].length > 15) {
        const extracted = match[1].trim();
        const firstSentence = extracted.split(/[.!?]/)[0].trim();
        if (firstSentence.length > 15) {
          return (firstSentence.charAt(0).toUpperCase() + firstSentence.slice(1) + '.').substring(0, 110);
        }
      }
    }
    
    return 'A season of noticing what wants attention.';
  }
  
  // Clean up without heavy stripping
  let cleaned = raw
    .replace(/\(.*?\)/g, '')
    .replace(/\s+/g, ' ')
    .trim();
  
  // Take first sentence
  const firstSentence = cleaned.split(/[.!?]/)[0].trim();
  let result = firstSentence;
  
  if (result && !result.match(/[.!?]$/)) {
    result += '.';
  }
  
  // Truncate to 110 chars
  if (result.length > 110) {
    result = result.substring(0, 107).trim() + '...';
  }
  
  if (result.length < 15) {
    return 'A season of noticing what wants attention.';
  }
  
  return result;
};

// Clean chapter body: remove filler, grounded tone, max ~180 chars
const cleanChapterBody = (raw: string): string => {
  if (!raw) return 'Take your time with what\'s emerging.';
  
  // Remove mystical/filler phrases
  const fillerPatterns = [
    /this isn't about.*?—/gi,
    /it's about recalibration/gi,
    /the cosmos.*?/gi,
    /transiting\s+\w+/gi,
    /natal\s+\w+/gi,
    /\(.*?\)/g,
    /mercury|venus|mars|jupiter|saturn|uranus|neptune|pluto/gi,
  ];
  
  let cleaned = raw;
  fillerPatterns.forEach(pattern => {
    cleaned = cleaned.replace(pattern, '');
  });
  
  cleaned = cleaned.replace(/\s+/g, ' ').trim();
  
  // Truncate for 3 lines (~180 chars)
  if (cleaned.length > 180) {
    cleaned = cleaned.substring(0, 177).trim() + '...';
  }
  
  if (cleaned.length < 10) {
    return 'Take your time with what\'s emerging.';
  }
  
  return cleaned;
};

// Clean reflection question: remove preface, just the question
const cleanReflectionQuestion = (raw: string): string => {
  if (!raw) return 'What feels present right now?';
  
  // Remove common prefixes
  let cleaned = raw
    .replace(/^reflect:\s*/i, '')
    .replace(/^question:\s*/i, '')
    .replace(/^consider:\s*/i, '')
    .trim();
  
  // Ensure it ends with ?
  if (cleaned && !cleaned.endsWith('?')) {
    cleaned += '?';
  }
  
  return cleaned || 'What feels present right now?';
};

const DISMISS_KEY_PREFIX = 'daily_focus_dismissed_';

export default function HomeV2({ 
  userId, 
  keystone, 
  isLoading,
  onFocusStateChange,
}: HomeV2Props) {
  const router = useRouter();
  const isStaging = BUILD_ENV === 'staging' || BUILD_ENV === 'preview';
  
  // Transit insight state
  const [transitInsight, setTransitInsight] = useState<TransitInterpretation | null>(null);
  const [transitLoading, setTransitLoading] = useState(true);
  const [transitError, setTransitError] = useState<string | null>(null);
  
  // Daily focus state (for context)
  const [dailyFocus, setDailyFocus] = useState<DailyFocusResponse | null>(null);
  const [focusDismissed, setFocusDismissed] = useState(false);
  
  // Get today's date string for dismiss key
  const getTodayKey = useCallback(() => {
    const today = new Date().toISOString().split('T')[0];
    return `${DISMISS_KEY_PREFIX}${userId}_${today}`;
  }, [userId]);
  
  // Fetch transit insight
  useEffect(() => {
    const fetchTransit = async () => {
      if (!userId) {
        setTransitLoading(false);
        return;
      }
      
      setTransitLoading(true);
      setTransitError(null);
      
      try {
        const data = await getTransitInsightNow(userId);
        setTransitInsight(data);
      } catch (err: any) {
        console.error('[HomeV2] Transit fetch error:', err);
        if (err?.response?.status === 404) {
          setTransitError('Chart not found');
        } else {
          setTransitError('Unable to load transits');
        }
      } finally {
        setTransitLoading(false);
      }
    };
    
    fetchTransit();
  }, [userId]);
  
  // Fetch daily focus for context
  useEffect(() => {
    const fetchFocus = async () => {
      if (!userId) return;
      
      try {
        // Check if dismissed for today
        const dismissedValue = await AsyncStorage.getItem(getTodayKey());
        if (dismissedValue === 'true') {
          setFocusDismissed(true);
          if (onFocusStateChange) {
            onFocusStateChange({
              isLoading: false,
              isDismissed: true,
              hasContext: false,
              context: null,
              ambientLine: null,
            });
          }
          return;
        }
        
        const focus = await getDailyFocus(userId);
        setDailyFocus(focus);
        
        if (onFocusStateChange) {
          onFocusStateChange({
            isLoading: false,
            isDismissed: false,
            hasContext: !!focus?.context,
            context: focus?.context || null,
            ambientLine: focus?.ambient_line || null,
          });
        }
      } catch (err) {
        console.error('[HomeV2] Daily focus fetch error:', err);
        if (onFocusStateChange) {
          onFocusStateChange({
            isLoading: false,
            isDismissed: false,
            hasContext: false,
            context: null,
            ambientLine: null,
          });
        }
      }
    };
    
    fetchFocus();
  }, [userId, getTodayKey, onFocusStateChange]);
  
  // Handle Reflect Now button
  const handleReflectNow = useCallback(() => {
    const navParams = new URLSearchParams();
    if (dailyFocus?.context) {
      navParams.set('context', dailyFocus.context);
    }
    if (focusDismissed) {
      navParams.set('dismissed', 'true');
    }
    router.push(`/reflection-chat?${navParams.toString()}`);
  }, [router, dailyFocus?.context, focusDismissed]);
  
  // Handle See Timeline link
  const handleSeeTimeline = useCallback(() => {
    router.push('/(tabs)/lenses?tab=astrology');
  }, [router]);
  
  // ============================================
  // DERIVED CONTENT (with cleaning)
  // ============================================
  
  // Headline: cleaned, max 140 chars, single sentence
  const rawHeadline = transitInsight?.headline || keystone?.keystone || '';
  const primaryHeadline = cleanHeadline(rawHeadline);
  
  // Timestamp: just time
  const timestamp = transitInsight?.meta?.timestamp_utc 
    ? formatTime(transitInsight.meta.timestamp_utc)
    : formatTime(new Date().toISOString());
  
  // Themes: max 3, lowercase
  const themes = transitInsight?.key_points 
    ? extractThemes(transitInsight.key_points)
    : dailyFocus?.context 
      ? [dailyFocus.context.toLowerCase()]
      : ['presence'];
  
  // Reflection question: cleaned, no preface
  const rawQuestion = transitInsight?.reflect?.[0] || keystone?.reflect_question || '';
  const reflectionQuestion = cleanReflectionQuestion(rawQuestion);
  
  // Chapter headline: max 110 chars, one sentence
  const rawChapterHeadline = transitInsight?.key_points?.[0] || '';
  const chapterHeadline = cleanChapterHeadline(rawChapterHeadline);
  
  // Chapter body: max 3 lines, grounded
  const rawChapterBody = transitInsight?.key_points?.[1] || '';
  const chapterBody = cleanChapterBody(rawChapterBody);
  
  // Combined loading state
  const showLoading = isLoading || transitLoading;
  
  if (showLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="small" color={Colors.textTertiary} />
        <Text style={styles.loadingText}>Loading your day...</Text>
      </View>
    );
  }
  
  return (
    <View style={styles.container}>
      {/* ============================================ */}
      {/* SECTION 1: TODAY */}
      {/* ============================================ */}
      <View style={styles.todaySection}>
        <SectionLabel marginBottom={Spacing.sm}>TODAY</SectionLabel>
        
        {/* Primary Headline - larger, more breathing room */}
        <Text style={styles.primaryHeadline}>
          {primaryHeadline}
        </Text>
        
        {/* Micro anchor - simplified two lines */}
        <View style={styles.microAnchor}>
          <Text style={styles.anchorTime}>As of {timestamp}</Text>
          <Text style={styles.anchorThemes}>
            Active: {themes.join(' • ')}
          </Text>
        </View>
        
        {/* Single reflection question - more space above */}
        <Text style={styles.reflectionQuestion}>
          {reflectionQuestion}
        </Text>
        
        {/* Primary Button: Reflect Now */}
        <TouchableOpacity 
          style={styles.reflectButton}
          onPress={handleReflectNow}
          activeOpacity={0.7}
        >
          <Text style={styles.reflectButtonText}>Reflect Now</Text>
        </TouchableOpacity>
      </View>
      
      {/* ============================================ */}
      {/* SECTION 2: YOUR CURRENT CHAPTER */}
      {/* ============================================ */}
      <View style={styles.chapterSection}>
        <SectionLabel marginBottom={Spacing.md}>YOUR CURRENT CHAPTER</SectionLabel>
        
        {/* Chapter Headline - max 110 chars */}
        <Text style={styles.chapterHeadline}>
          {chapterHeadline}
        </Text>
        
        {/* Short paragraph - max 3 lines */}
        <Text style={styles.chapterBody} numberOfLines={3}>
          {chapterBody}
        </Text>
        
        {/* See timeline link */}
        <TouchableOpacity 
          style={styles.timelineLink}
          onPress={handleSeeTimeline}
          activeOpacity={0.6}
        >
          <Text style={styles.timelineLinkText}>See timeline →</Text>
        </TouchableOpacity>
      </View>
      
      {/* Debug: Build stamp (staging only) */}
      {isStaging && (
        <Text style={styles.debugStamp}>
          HomeV2 • {BUILD_ENV}
        </Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingTop: Spacing.sm,
  },
  loadingContainer: {
    paddingVertical: Spacing.xxxl,
    alignItems: 'center',
    gap: Spacing.sm,
  },
  loadingText: {
    fontSize: 13,
    color: Colors.textTertiary,
    opacity: 0.5,
  },
  
  // ============================================
  // TODAY SECTION - Visual dominance
  // ============================================
  todaySection: {
    paddingTop: Spacing.md,
    paddingBottom: Spacing.xxl,
    marginBottom: Spacing.xl,
  },
  primaryHeadline: {
    fontSize: 24,
    fontWeight: '300',
    color: Colors.text,
    lineHeight: 36,
    marginTop: Spacing.md,
    marginBottom: Spacing.lg,
    letterSpacing: 0.2,
  },
  microAnchor: {
    marginBottom: Spacing.xl,
    gap: 6,
  },
  anchorTime: {
    fontSize: 11,
    color: Colors.textTertiary,
    opacity: 0.45,
    letterSpacing: 0.3,
  },
  anchorThemes: {
    fontSize: 11,
    color: Colors.textTertiary,
    opacity: 0.35,
    letterSpacing: 0.3,
  },
  reflectionQuestion: {
    fontSize: 17,
    fontWeight: '400',
    fontStyle: 'italic',
    color: Colors.textSecondary,
    lineHeight: 26,
    marginTop: Spacing.sm,
    marginBottom: Spacing.xl,
  },
  reflectButton: {
    backgroundColor: Colors.accent,
    paddingVertical: 14,
    paddingHorizontal: Spacing.lg,
    borderRadius: 8,
    alignItems: 'center',
    alignSelf: 'flex-start',
  },
  reflectButtonText: {
    fontSize: 15,
    fontWeight: '500',
    color: Colors.background,
    letterSpacing: 0.3,
  },
  
  // ============================================
  // YOUR CURRENT CHAPTER - Secondary, important
  // ============================================
  chapterSection: {
    paddingTop: Spacing.lg,
    paddingBottom: Spacing.xl,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.04)',
  },
  chapterHeadline: {
    fontSize: 15,
    fontWeight: '400',
    color: Colors.text,
    lineHeight: 23,
    marginBottom: Spacing.sm,
  },
  chapterBody: {
    fontSize: 14,
    fontWeight: '400',
    color: Colors.textSecondary,
    lineHeight: 22,
    marginBottom: Spacing.md,
    opacity: 0.8,
  },
  timelineLink: {
    paddingVertical: Spacing.xs,
    marginTop: Spacing.xs,
  },
  timelineLinkText: {
    fontSize: 13,
    color: Colors.accent,
    fontWeight: '400',
    letterSpacing: 0.2,
  },
  
  // Debug
  debugStamp: {
    fontSize: 9,
    color: Colors.textTertiary,
    opacity: 0.2,
    textAlign: 'center',
    marginTop: Spacing.xl,
    fontFamily: 'monospace',
  },
});
