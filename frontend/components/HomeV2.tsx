/**
 * HomeV2 - Restructured Home Tab Layout
 * 
 * Phase 1: Structural Reset
 * Phase 2: Resonance Calibration - Copy tightening, visual hierarchy
 * Phase 3: Deterministic Personal Resonance Layer
 * Phase 4: Resonance Precision - Multiple variants, deterministic selection
 * Phase 5: Interaction Psychology Layer - Progressive disclosure, micro motion, memory anchor
 * 
 * Two unified sections:
 * 1. TODAY - Primary headline, personal resonance, timestamp, themes, reflection question, Reflect Now button
 * 2. YOUR CURRENT CHAPTER - Slowest transit / key point, See timeline link
 * 
 * No changes to backend logic or APIs.
 * Preserves all existing data calls.
 */

import React, { useState, useCallback, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Animated,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Colors } from '../constants/colors';
import { Spacing } from '../constants/spacing';
import { useAppStore } from '../store';
import { DailyFocusState } from './DailyFocusCard';
import { getDailyFocus, DailyFocusResponse, getEnneagramResult, getJournalEntries } from '../services/api';
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
// PERSONAL RESONANCE - Phase 4: Precision
// ============================================

// Stable hash function for deterministic variant selection
// Simple djb2 hash - no external dependencies
const stableHash = (str: string): number => {
  let hash = 5381;
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) + hash) + str.charCodeAt(i);
    hash = hash & hash; // Convert to 32-bit integer
  }
  return Math.abs(hash);
};

// Get local date as YYYY-MM-DD
const getLocalDateKey = (): string => {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

// Enneagram core type mappings (1-9) - 2-3 variants each
const ENNEAGRAM_RESONANCE: Record<number, string[]> = {
  1: [
    "This may highlight your internal standards.",
    "This may surface the gap between how things are and how they should be.",
    "This may sharpen your sense of what needs correcting.",
  ],
  2: [
    "This may pull on your instinct to support others.",
    "This may highlight where giving feels easier than receiving.",
    "This may stir awareness of what you need versus what you offer.",
  ],
  3: [
    "This may touch your drive to achieve or perform.",
    "This may test whether you're moving for you or for recognition.",
    "This may highlight the difference between doing and being.",
  ],
  4: [
    "This may stir deeper emotional undercurrents.",
    "This may amplify your sense of what's missing.",
    "This may highlight the tension between ordinary and meaningful.",
  ],
  5: [
    "This may draw you inward to process privately.",
    "This may test when to stay quiet versus when to share.",
    "This may highlight your need for space before engagement.",
  ],
  6: [
    "This may activate your need for reassurance or clarity.",
    "This may surface doubt that wants to be worked through.",
    "This may test your trust in the unknown.",
  ],
  7: [
    "This may stir your urge to move on quickly.",
    "This may test your patience with slower emotions.",
    "This may highlight the pull to keep things light.",
  ],
  8: [
    "This may test how you hold control.",
    "This may surface intensity around boundaries.",
    "This may challenge you to soften without giving up power.",
  ],
  9: [
    "This may soften or blur your boundaries.",
    "This may highlight where you're merging with others' needs.",
    "This may test your ability to stay present with tension.",
  ],
};

// Human Design type mappings - 2-3 variants each
const HD_RESONANCE: Record<string, string[]> = {
  'Manifestor': [
    "This may affect how you initiate — especially if you feel resistance.",
    "This may shift how you start things when you're not fully sure yet.",
    "This may bring up friction around taking the first step.",
  ],
  'Generator': [
    "This may shift what you feel energy for — and what you don't.",
    "This may clarify what's worth saying yes to today.",
    "This may highlight where your energy is naturally pulled.",
  ],
  'Manifesting Generator': [
    "This may redirect your momentum — fast.",
    "This may shift your pace or priorities mid-stream.",
    "This may push you to adjust quickly without overthinking.",
  ],
  'Projector': [
    "This may affect how you guide — or when you hold back.",
    "This may highlight where your focus is best spent.",
    "This may nudge you to wait for the right moment to step in.",
  ],
  'Reflector': [
    "This may feel amplified by your environment today.",
    "This may make outside signals feel louder than usual.",
    "This may heighten sensitivity to people and spaces.",
  ],
};

// Domain hints - maps themes to contextual suffixes
const DOMAIN_HINTS: Record<string, string> = {
  'communication': 'in conversations',
  'expression': 'in how you express',
  'relationships': 'in relationships',
  'connection': 'in connection',
  'work': 'at work',
  'purpose': 'around purpose',
  'feelings': 'around feelings',
  'inner life': 'in your inner life',
  'change': 'around change',
  'transformation': 'in what\'s shifting',
  'rest': 'around rest',
  'stillness': 'in stillness',
  'calm': 'in finding calm',
  'growth': 'around growth',
  'expansion': 'in expansion',
  'learning': 'in learning',
  'body': 'in your body',
  'energy': 'around energy',
  'reflection': 'in reflection',
  'awareness': 'in awareness',
  'attention': 'around attention',
  'depth': 'in what\'s deeper',
  'identity': 'in how you show up',
  'structure': 'around structure',
  'presence': 'in presence',
  'home': 'at home',
};

interface UserProfile {
  enneagram?: {
    core_type?: number;
  };
  human_design?: {
    type?: string;
  };
}

/**
 * Select a variant deterministically based on userId and date.
 * Same user + same day = same variant. Different days = rotation.
 */
const selectVariant = (variants: string[], userId: string, lensKey: string): string => {
  const dateKey = getLocalDateKey();
  const hashKey = `${userId}|${dateKey}|${lensKey}|resonance`;
  const hash = stableHash(hashKey);
  const index = hash % variants.length;
  return variants[index];
};

/**
 * Append a domain hint if available and if result stays ≤120 chars.
 */
const appendDomainHint = (base: string, themes: string[]): string => {
  if (!themes || themes.length === 0) return base;
  
  // Find first matching theme
  for (const theme of themes) {
    const lowerTheme = theme.toLowerCase();
    const hint = DOMAIN_HINTS[lowerTheme];
    if (hint) {
      // Check if base already ends with period
      const baseWithoutPeriod = base.replace(/\.$/, '');
      const withHint = `${baseWithoutPeriod} — ${hint}.`;
      
      // Only append if within 120 chars
      if (withHint.length <= 120) {
        return withHint;
      }
    }
  }
  
  return base;
};

/**
 * Generate a subtle personal resonance line based on user profile.
 * Phase 4: Multiple variants, deterministic selection, optional domain hints.
 * Priority: Enneagram > Human Design > null
 * Returns null if no profile data available.
 */
const generatePersonalResonance = (
  userProfile: UserProfile | null, 
  userId: string,
  themes: string[]
): string | null => {
  if (!userProfile) return null;
  
  let resonance: string | null = null;
  
  // Priority 1: Enneagram core type
  if (userProfile.enneagram?.core_type) {
    const coreType = userProfile.enneagram.core_type;
    const variants = ENNEAGRAM_RESONANCE[coreType];
    if (variants && variants.length > 0) {
      resonance = selectVariant(variants, userId, `enneagram_${coreType}`);
    }
  }
  
  // Priority 2: Human Design type (only if enneagram not found)
  if (!resonance && userProfile.human_design?.type) {
    const hdType = userProfile.human_design.type;
    const variants = HD_RESONANCE[hdType];
    if (variants && variants.length > 0) {
      resonance = selectVariant(variants, userId, `hd_${hdType}`);
    }
  }
  
  // No profile data available
  if (!resonance) return null;
  
  // Try to append domain hint if themes available
  resonance = appendDomainHint(resonance, themes);
  
  // Final guardrail: ensure ≤120 chars and single sentence
  if (resonance.length > 120) {
    resonance = resonance.substring(0, 117).trim() + '...';
  }
  
  return resonance;
};

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
  
  // If the raw text has heavy astrological jargon, use a more meaningful extraction
  const hasHeavyJargon = /transiting\s+(mercury|venus|mars|jupiter|saturn|sun|moon)/i.test(raw) ||
    /natal\s+(mercury|venus|mars|jupiter|saturn|pluto)/i.test(raw) ||
    /polarity\s+between/i.test(raw) ||
    /opportunity\s+between/i.test(raw);
  
  if (hasHeavyJargon) {
    // Try to extract the meaningful observation
    const meaningfulPatterns = [
      /you may notice\s+(.+)/i,
      /this invites\s+(.+)/i,
      /notice\s+(.+)/i,
      /there's\s+(.+)/i,
    ];
    
    for (const pattern of meaningfulPatterns) {
      const match = raw.match(pattern);
      if (match && match[1] && match[1].length > 20) {
        let extracted = match[1]
          .replace(/\(.*?\)/g, '')
          .replace(/\s+/g, ' ')
          .trim();
        
        if (extracted.length > 180) {
          extracted = extracted.substring(0, 177).trim() + '...';
        }
        
        if (extracted.length > 20) {
          return extracted.charAt(0).toUpperCase() + extracted.slice(1);
        }
      }
    }
    
    return 'Take your time with what\'s emerging.';
  }
  
  // Clean without heavy stripping
  let cleaned = raw
    .replace(/\(.*?\)/g, '')
    .replace(/\s+/g, ' ')
    .trim();
  
  // Truncate for 3 lines (~180 chars)
  if (cleaned.length > 180) {
    cleaned = cleaned.substring(0, 177).trim() + '...';
  }
  
  if (cleaned.length < 15) {
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

// Interface for enneagram results from API
interface EnneagramResult {
  core_type?: number;
  wing?: number;
  confidence?: number;
}

export default function HomeV2({ 
  userId, 
  keystone, 
  isLoading,
  onFocusStateChange,
}: HomeV2Props) {
  const router = useRouter();
  const isStaging = BUILD_ENV === 'staging' || BUILD_ENV === 'preview';
  
  // Get chart and journal entries from store
  const chart = useAppStore((state) => state.chart);
  const journalEntries = useAppStore((state) => state.journalEntries);
  
  // Transit insight state
  const [transitInsight, setTransitInsight] = useState<TransitInterpretation | null>(null);
  const [transitLoading, setTransitLoading] = useState(true);
  const [transitError, setTransitError] = useState<string | null>(null);
  
  // Daily focus state (for context)
  const [dailyFocus, setDailyFocus] = useState<DailyFocusResponse | null>(null);
  const [focusDismissed, setFocusDismissed] = useState(false);
  
  // Enneagram state (for personal resonance)
  const [enneagramResult, setEnneagramResult] = useState<EnneagramResult | null>(null);
  
  // Journal entries state (for memory anchor)
  const [localJournalEntries, setLocalJournalEntries] = useState<any[]>([]);
  
  // Phase 5: Progressive disclosure state
  const [showMoreContent, setShowMoreContent] = useState(false);
  
  // Phase 5: Animation values
  const headlineOpacity = useRef(new Animated.Value(0)).current;
  const questionOpacity = useRef(new Animated.Value(0)).current;
  const moreContentOpacity = useRef(new Animated.Value(0)).current;
  const hasAnimated = useRef(false);
  
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
  
  // Fetch enneagram results for personal resonance
  useEffect(() => {
    const fetchEnneagram = async () => {
      if (!userId) return;
      
      try {
        const data = await getEnneagramResult(userId);
        // API returns { has_result, result: { inferred_core, inferred_wing, confidence, ... } }
        if (data?.has_result && data?.result) {
          const result = data.result;
          setEnneagramResult({
            core_type: result.inferred_core,
            wing: result.inferred_wing,
            confidence: result.confidence,
          });
        }
      } catch (err) {
        // Silent fail - resonance is optional
        console.debug('[HomeV2] Enneagram fetch skipped:', err);
      }
    };
    
    fetchEnneagram();
  }, [userId]);
  
  // Fetch journal entries for memory anchor
  useEffect(() => {
    const fetchJournal = async () => {
      if (!userId) return;
      
      try {
        const entries = await getJournalEntries(userId);
        setLocalJournalEntries(entries || []);
      } catch (err) {
        console.debug('[HomeV2] Journal fetch skipped:', err);
        setLocalJournalEntries([]);
      }
    };
    
    fetchJournal();
  }, [userId]);
  
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
  
  // Phase 5: Handle "Continue reading" tap
  const handleContinueReading = useCallback(() => {
    setShowMoreContent(true);
    Animated.timing(moreContentOpacity, {
      toValue: 1,
      duration: 250,
      useNativeDriver: true,
    }).start();
  }, [moreContentOpacity]);
  
  // Phase 5: Trigger entrance animations when content loads
  useEffect(() => {
    if (!isLoading && !transitLoading && !hasAnimated.current) {
      hasAnimated.current = true;
      
      // Headline fades in first (250ms)
      Animated.timing(headlineOpacity, {
        toValue: 1,
        duration: 250,
        useNativeDriver: true,
      }).start();
      
      // Reflection question appears 150ms after headline starts
      setTimeout(() => {
        Animated.timing(questionOpacity, {
          toValue: 1,
          duration: 250,
          useNativeDriver: true,
        }).start();
      }, 150);
    }
  }, [isLoading, transitLoading, headlineOpacity, questionOpacity]);
  
  // Phase 5: Calculate "Last reflected" for memory anchor
  const lastReflectedText = React.useMemo(() => {
    if (!journalEntries || journalEntries.length === 0) {
      return 'Start your first reflection.';
    }
    
    // Find most recent journal entry
    const sortedEntries = [...journalEntries].sort((a, b) => {
      const dateA = new Date(a.created_at || a.date || 0).getTime();
      const dateB = new Date(b.created_at || b.date || 0).getTime();
      return dateB - dateA;
    });
    
    const lastEntry = sortedEntries[0];
    if (!lastEntry) {
      return 'Start your first reflection.';
    }
    
    const lastDate = new Date(lastEntry.created_at || lastEntry.date || 0);
    const now = new Date();
    const diffMs = now.getTime() - lastDate.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
      return 'Last reflected: today';
    } else if (diffDays === 1) {
      return 'Last reflected: yesterday';
    } else if (diffDays < 7) {
      return `Last reflected: ${diffDays} days ago`;
    } else if (diffDays < 30) {
      const weeks = Math.floor(diffDays / 7);
      return `Last reflected: ${weeks} week${weeks > 1 ? 's' : ''} ago`;
    } else {
      return 'Last reflected: a while ago';
    }
  }, [journalEntries]);
  
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
  
  // Personal resonance: derived from enneagram or human design
  // Phase 4: Uses userId and themes for deterministic variant selection + domain hints
  const userProfile: UserProfile = {
    enneagram: enneagramResult ? { core_type: enneagramResult.core_type } : undefined,
    human_design: chart?.human_design ? { type: chart.human_design.type } : undefined,
  };
  const personalResonance = generatePersonalResonance(userProfile, userId, themes);
  
  // Phase 5: Additional content for progressive disclosure
  // Uses the third key point or micro_affirmation as extra interpretive nuance
  const additionalContent = transitInsight?.key_points?.[2] 
    || keystone?.micro_affirmation 
    || 'Sometimes the quietest moments carry the most meaning.';
  
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
        
        {/* Primary Headline - with fade-in animation */}
        <Animated.Text style={[styles.primaryHeadline, { opacity: headlineOpacity }]}>
          {primaryHeadline}
        </Animated.Text>
        
        {/* Personal Resonance - subtle, secondary, shown only if available */}
        {personalResonance && (
          <Text style={styles.personalResonance} numberOfLines={1}>
            {personalResonance}
          </Text>
        )}
        
        {/* Micro anchor - simplified two lines */}
        <View style={styles.microAnchor}>
          <Text style={styles.anchorTime}>As of {timestamp}</Text>
          <Text style={styles.anchorThemes}>
            Active: {themes.join(' • ')}
          </Text>
        </View>
        
        {/* Single reflection question - with delayed fade-in */}
        <Animated.Text style={[styles.reflectionQuestion, { opacity: questionOpacity }]}>
          {reflectionQuestion}
        </Animated.Text>
        
        {/* Progressive Disclosure: Continue reading link */}
        {!showMoreContent && additionalContent && (
          <TouchableOpacity 
            style={styles.continueReadingLink}
            onPress={handleContinueReading}
            activeOpacity={0.6}
          >
            <Text style={styles.continueReadingText}>Continue reading →</Text>
          </TouchableOpacity>
        )}
        
        {/* Progressive Disclosure: Additional content (revealed on tap) */}
        {showMoreContent && (
          <Animated.View style={[styles.additionalContentContainer, { opacity: moreContentOpacity }]}>
            <Text style={styles.additionalContent} numberOfLines={2}>
              {additionalContent}
            </Text>
          </Animated.View>
        )}
        
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
        
        {/* Memory Anchor: Last reflected */}
        <Text style={styles.memoryAnchor}>
          {lastReflectedText}
        </Text>
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
  personalResonance: {
    fontSize: 14,
    fontWeight: '400',
    color: Colors.textSecondary,
    opacity: 0.75,
    marginTop: Spacing.xs,
    marginBottom: Spacing.md,
    lineHeight: 20,
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
    marginTop: Spacing.md,
  },
  reflectButtonText: {
    fontSize: 15,
    fontWeight: '500',
    color: Colors.background,
    letterSpacing: 0.3,
  },
  
  // Phase 5: Progressive Disclosure
  continueReadingLink: {
    paddingVertical: Spacing.sm,
    marginBottom: Spacing.sm,
  },
  continueReadingText: {
    fontSize: 13,
    color: Colors.accent,
    fontWeight: '400',
    opacity: 0.8,
  },
  additionalContentContainer: {
    marginBottom: Spacing.md,
  },
  additionalContent: {
    fontSize: 14,
    fontWeight: '400',
    color: Colors.textSecondary,
    lineHeight: 22,
    opacity: 0.7,
  },
  
  // ============================================
  // YOUR CURRENT CHAPTER - Secondary, calmer, dimmer
  // ============================================
  chapterSection: {
    paddingTop: Spacing.xxl,
    paddingBottom: Spacing.xl,
    marginTop: Spacing.lg,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.03)',
    opacity: 0.9,
  },
  chapterHeadline: {
    fontSize: 15,
    fontWeight: '400',
    color: Colors.text,
    lineHeight: 23,
    marginBottom: Spacing.sm,
    opacity: 0.85,
  },
  chapterBody: {
    fontSize: 14,
    fontWeight: '400',
    color: Colors.textSecondary,
    lineHeight: 22,
    marginBottom: Spacing.md,
    opacity: 0.7,
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
    opacity: 0.85,
  },
  
  // Phase 5: Memory Anchor
  memoryAnchor: {
    fontSize: 11,
    color: Colors.textTertiary,
    opacity: 0.4,
    marginTop: Spacing.lg,
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
