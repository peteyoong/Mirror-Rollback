/**
 * HomeV2 - Restructured Home Tab Layout
 * 
 * Phase 1: Structural Reset Only
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
import { Typography } from '../constants/typography';
import { Spacing } from '../constants/spacing';
import { useAppStore } from '../store';
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

// Format timestamp for display
const formatTimestamp = (isoString: string): string => {
  try {
    const date = new Date(isoString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  } catch {
    return isoString;
  }
};

// Extract themes from transit key points
const extractThemes = (keyPoints: string[]): string[] => {
  // Take first 2-3 key points and extract key themes
  const themes: string[] = [];
  
  if (keyPoints && keyPoints.length > 0) {
    // Extract key thematic words from first 2 key points
    keyPoints.slice(0, 2).forEach(point => {
      // Look for common astrological themes
      const lowerPoint = point.toLowerCase();
      if (lowerPoint.includes('communication') || lowerPoint.includes('express')) {
        themes.push('Communication');
      } else if (lowerPoint.includes('relationship') || lowerPoint.includes('connection')) {
        themes.push('Relationships');
      } else if (lowerPoint.includes('work') || lowerPoint.includes('career') || lowerPoint.includes('professional')) {
        themes.push('Work & Purpose');
      } else if (lowerPoint.includes('emotion') || lowerPoint.includes('feeling') || lowerPoint.includes('inner')) {
        themes.push('Inner State');
      } else if (lowerPoint.includes('change') || lowerPoint.includes('transform')) {
        themes.push('Transformation');
      } else if (lowerPoint.includes('rest') || lowerPoint.includes('peace') || lowerPoint.includes('calm')) {
        themes.push('Rest & Restoration');
      } else if (lowerPoint.includes('growth') || lowerPoint.includes('expand') || lowerPoint.includes('learn')) {
        themes.push('Growth');
      } else if (lowerPoint.includes('health') || lowerPoint.includes('body') || lowerPoint.includes('energy')) {
        themes.push('Health & Body');
      }
    });
  }
  
  // If no themes extracted, use fallback
  if (themes.length === 0) {
    return ['Presence', 'Awareness'];
  }
  
  // Dedupe and limit to 3
  return [...new Set(themes)].slice(0, 3);
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
    router.push('/(tabs)/lens?tab=astrology');
  }, [router]);
  
  // Derive headline: Use transit headline or keystone
  const primaryHeadline = transitInsight?.headline 
    || keystone?.keystone 
    || 'Something in you brought you here today.';
  
  // Derive timestamp from transit or current time
  const timestamp = transitInsight?.meta?.timestamp_utc 
    ? formatTimestamp(transitInsight.meta.timestamp_utc)
    : formatTimestamp(new Date().toISOString());
  
  // Derive themes from transit key points or focus context
  const themes = transitInsight?.key_points 
    ? extractThemes(transitInsight.key_points)
    : dailyFocus?.context 
      ? [dailyFocus.context]
      : ['Presence'];
  
  // Get single reflection question
  const reflectionQuestion = transitInsight?.reflect?.[0] 
    || keystone?.reflect_question 
    || 'What feels most present right now?';
  
  // Derive current chapter from slowest transit or first key point
  const currentChapterHeadline = transitInsight?.key_points?.[0]
    || 'A season of noticing what wants your attention.';
  
  const currentChapterBody = transitInsight?.key_points?.[1]
    || 'The slower currents are inviting you to look at what usually moves too fast to see.';
  
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
        <SectionLabel marginBottom={Spacing.md}>TODAY</SectionLabel>
        
        {/* Primary Headline - large text, single sentence */}
        <Text style={styles.primaryHeadline}>
          {primaryHeadline}
        </Text>
        
        {/* Micro anchor */}
        <View style={styles.microAnchor}>
          <Text style={styles.anchorTimestamp}>As of: {timestamp}</Text>
          <Text style={styles.anchorThemes}>
            Active themes: {themes.join(', ')}
          </Text>
        </View>
        
        {/* Single reflection question */}
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
        <SectionLabel marginBottom={Spacing.sm}>YOUR CURRENT CHAPTER</SectionLabel>
        
        {/* Chapter Headline - 1 sentence */}
        <Text style={styles.chapterHeadline}>
          {currentChapterHeadline}
        </Text>
        
        {/* Short paragraph - max 3 lines */}
        <Text style={styles.chapterBody} numberOfLines={3}>
          {currentChapterBody}
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
  },
  loadingContainer: {
    paddingVertical: Spacing.xxl,
    alignItems: 'center',
    gap: Spacing.sm,
  },
  loadingText: {
    fontSize: 13,
    color: Colors.textTertiary,
    opacity: 0.6,
  },
  
  // ============================================
  // TODAY SECTION
  // ============================================
  todaySection: {
    paddingBottom: Spacing.xl,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.06)',
    marginBottom: Spacing.xl,
  },
  primaryHeadline: {
    fontSize: 22,
    fontWeight: '300',
    color: Colors.text,
    lineHeight: 32,
    marginBottom: Spacing.md,
  },
  microAnchor: {
    marginBottom: Spacing.lg,
  },
  anchorTimestamp: {
    fontSize: 11,
    color: Colors.textTertiary,
    opacity: 0.5,
    marginBottom: 4,
  },
  anchorThemes: {
    fontSize: 11,
    color: Colors.textTertiary,
    opacity: 0.5,
  },
  reflectionQuestion: {
    fontSize: 16,
    fontWeight: '400',
    fontStyle: 'italic',
    color: Colors.textSecondary,
    lineHeight: 24,
    marginBottom: Spacing.lg,
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
  // YOUR CURRENT CHAPTER SECTION
  // ============================================
  chapterSection: {
    paddingBottom: Spacing.lg,
  },
  chapterHeadline: {
    fontSize: 16,
    fontWeight: '400',
    color: Colors.text,
    lineHeight: 24,
    marginBottom: Spacing.sm,
  },
  chapterBody: {
    fontSize: 14,
    fontWeight: '400',
    color: Colors.textSecondary,
    lineHeight: 22,
    marginBottom: Spacing.md,
  },
  timelineLink: {
    paddingVertical: Spacing.xs,
  },
  timelineLinkText: {
    fontSize: 13,
    color: Colors.accent,
    fontWeight: '400',
  },
  
  // Debug
  debugStamp: {
    fontSize: 9,
    color: Colors.textTertiary,
    opacity: 0.3,
    textAlign: 'center',
    marginTop: Spacing.lg,
    fontFamily: 'monospace',
  },
});
