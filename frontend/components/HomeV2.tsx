/**
 * HomeV2 - Restructured Home Tab Layout
 * 
 * Phase 1: Structural Reset
 * Phase 2: Resonance Calibration - Copy tightening, visual hierarchy
 * Phase 3: Deterministic Personal Resonance Layer
 * Phase 4: Resonance Precision - Multiple variants, deterministic selection
 * Phase 5: Interaction Psychology Layer - Progressive disclosure, micro motion, memory anchor
 * Phase 6: First 7-Day Guided Arc - Subtle progression for new users
 * Phase 10: Resonance Engine v1 - Transit-aware headlines and questions
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
import { getDailyFocus, DailyFocusResponse, getEnneagramResult, getJournalEntries, getChapter, ChapterResponse } from '../services/api';
import { 
  getTransitInsightNow, 
  TransitInterpretation,
  getTransitCompute,
} from '../services/transitService';
import { BUILD_ENV } from '../utils/buildInfo';
import AsyncStorage from '@react-native-async-storage/async-storage';
import SectionLabel from './SectionLabel';

// Chapter cache key
const CHAPTER_CACHE_KEY = 'chapter_cache';

// ============================================
// PHASE 10: Resonance Engine v1
// PHASE 10A: Polish - Domain hints + Journal echo texture
// ============================================

// Part D: Safety Layer - Forbidden words that imply fate/prediction
const FORBIDDEN_WORDS = [
  'will',
  'destined',
  'guaranteed',
  'fated',
  'meant to',
  'the universe',
  'cosmic forces',
  'stars say',
  'planets say',
  'horoscope',
  'house',      // No astrology terms
  'transit',    // No astrology terms
  'natal',      // No astrology terms
  'planet',     // No astrology terms
];

/**
 * Validate resonance text - reject if contains forbidden words
 */
const validateResonanceText = (text: string): boolean => {
  const lowerText = text.toLowerCase();
  for (const forbidden of FORBIDDEN_WORDS) {
    if (lowerText.includes(forbidden)) {
      console.debug(`[ResonanceEngine] Rejected text containing: "${forbidden}"`);
      return false;
    }
  }
  return true;
};

// Phase 10A: House to plain domain mapping (no astrology words)
const HOUSE_DOMAIN_MAP: Record<number, string> = {
  1: 'your sense of self',  // Phase 10B: Softened from "identity"
  2: 'security',
  3: 'communication',
  4: 'home',
  5: 'creativity',
  6: 'routine',
  7: 'relationships',
  8: 'shared resources',
  9: 'meaning',
  10: 'direction',
  11: 'community',
  12: 'inner life',
};

// Phase 10A: Journal echo phrases (for when overlap detected)
// Phase 10B: Fixed punctuation - use " — " (space em dash space) for clean reading
const ECHO_PHRASES = [
  ', and it may echo something familiar',
  ', and it may resemble a recent pattern',
  ', something you may have noticed before',
];

/**
 * Phase 10A: Get domain hint from top houses
 * Returns a plain language domain string (no astrology)
 */
const getDomainHint = (topHouses: number[] | undefined): string | null => {
  if (!topHouses || topHouses.length === 0) return null;
  
  // Use the first (strongest) house
  const primaryHouse = topHouses[0];
  const domain = HOUSE_DOMAIN_MAP[primaryHouse];
  
  return domain || null;
};

/**
 * Phase 10A: Select echo phrase deterministically
 */
const selectEchoPhrase = (userId: string): string => {
  const dateKey = getLocalDateKey();
  const hashKey = `${userId}|${dateKey}|echo`;
  const hash = stableHash(hashKey);
  const index = hash % ECHO_PHRASES.length;
  return ECHO_PHRASES[index];
};

// Aspect type to archetypal tension mapping
interface TensionArchetype {
  type: 'friction' | 'polarity' | 'intensity' | 'shift' | 'emphasis';
  description: string;
  headlineTemplates: string[];
  questionModifiers: Record<string, string[]>;
}

const ASPECT_ARCHETYPES: Record<string, TensionArchetype> = {
  square: {
    type: 'friction',
    description: 'friction between two needs',
    headlineTemplates: [
      'There may be tension between holding structure and wanting change.',
      'A subtle pressure between what you want and what feels practical could be present.',
      'You might feel friction between moving forward and staying grounded.',
      'There could be an inner negotiation between security and growth.',
    ],
    questionModifiers: {
      pattern: ['Where is this pressure starting to repeat itself?', 'What friction keeps showing up?'],
      choice: ['Which side of this tension are you leaning toward?', 'What would ease this friction?'],
      tension: ['Where does this pressure feel strongest?', 'What needs your attention most?'],
    },
  },
  opposition: {
    type: 'polarity',
    description: 'polarity pulling in two directions',
    headlineTemplates: [
      'You might feel pulled between expansion and responsibility.',
      'There could be a sense of being stretched between different priorities.',
      'A polarity between giving and receiving may be present.',
      'You might notice a pull between what you want and what others need.',
    ],
    questionModifiers: {
      pattern: ['What kind of either-or keeps resurfacing?', 'Where do you feel most divided?'],
      choice: ['Which side of this pull are you leaning toward?', 'What would bring more balance?'],
      tension: ['Where do you feel most stretched?', 'What needs to be held together?'],
    },
  },
  conjunction: {
    type: 'intensity',
    description: 'intensified focus',
    headlineTemplates: [
      'A particular area of life may feel more concentrated right now.',
      'There could be an intensified focus on something that matters.',
      'You might notice a heightened sense of clarity about a direction.',
      'Something may be asking for your full attention.',
    ],
    questionModifiers: {
      pattern: ['What keeps demanding your focus?', 'Where is your attention being pulled?'],
      choice: ['What deserves your full attention today?', 'Where could focus make a difference?'],
      awareness: ['What feels most alive right now?', 'What has your attention?'],
    },
  },
  trine: {
    type: 'shift',
    description: 'natural flow or ease',
    headlineTemplates: [
      'There may be a sense of things aligning more easily.',
      'A gentle momentum could be available if you lean into it.',
      'You might notice that certain things feel less effortful.',
      'There could be an opening where things flow with less resistance.',
    ],
    questionModifiers: {
      pattern: ['What feels easier than expected?', 'Where is there unexpected flow?'],
      choice: ['What could you lean into right now?', 'Where might less effort serve you?'],
      awareness: ['What feels naturally supported?', 'Where do you feel momentum?'],
    },
  },
  sextile: {
    type: 'shift',
    description: 'subtle opportunity or opening',
    headlineTemplates: [
      'A subtle opening for something new may be present.',
      'There could be a quiet opportunity to try a different approach.',
      'You might notice a small window for something you\'ve been considering.',
      'A gentle invitation to explore something could be available.',
    ],
    questionModifiers: {
      pattern: ['What small openings are you noticing?', 'Where might there be room to try?'],
      choice: ['What small step could you take?', 'What invitation feels worth exploring?'],
      awareness: ['What possibility feels alive?', 'What would you try if it were easy?'],
    },
  },
};

// Default fallback for unknown aspects
const DEFAULT_ARCHETYPE: TensionArchetype = {
  type: 'shift',
  description: 'subtle shift in tone',
  headlineTemplates: [
    'There may be a subtle shift in how things feel today.',
    'You might notice something different about your inner state.',
    'A quiet change in tone could be present.',
  ],
  questionModifiers: {
    pattern: ['What feels different lately?'],
    choice: ['What small adjustment might help?'],
    awareness: ['What are you noticing?'],
  },
};

// Transit aspect data structure
interface TransitAspect {
  transit_planet: string;
  aspect: string;
  natal_body: string;
  orb: number;
}

// Journal signature structure (simplified)
interface JournalSignature {
  events?: string[];
  top_houses?: number[];
}

/**
 * Part A: Generate a resonant headline based on transit data
 * Phase 10A: Now includes domain hints and journal-echo texture
 * Returns a grounded, non-mystical headline that reflects current tensions
 */
const generateResonantHeadline = (
  aspects: TransitAspect[],
  userId: string,
  journalSignatures?: JournalSignature[],
  topHouses?: number[],
  hasJournalOverlap?: boolean
): string | null => {
  if (!aspects || aspects.length === 0) return null;
  
  // Find the strongest aspect (lowest orb = tightest aspect)
  const sortedAspects = [...aspects].sort((a, b) => a.orb - b.orb);
  const primaryAspect = sortedAspects[0];
  
  if (!primaryAspect) return null;
  
  // Get archetype for this aspect type
  const archetype = ASPECT_ARCHETYPES[primaryAspect.aspect] || DEFAULT_ARCHETYPE;
  const templates = archetype.headlineTemplates;
  
  if (!templates || templates.length === 0) return null;
  
  // Select template deterministically using hash
  const dateKey = getLocalDateKey();
  const hashKey = `${userId}|${dateKey}|headline|${primaryAspect.aspect}`;
  const hash = stableHash(hashKey);
  const index = hash % templates.length;
  
  let headline = templates[index];
  
  // Validate safety
  if (!validateResonanceText(headline)) {
    // Fall back to first safe template
    headline = templates.find(t => validateResonanceText(t)) || 'A moment for quiet attention.';
  }
  
  // Phase 10A: Remove trailing period for appending
  let baseHeadline = headline.replace(/\.$/, '');
  
  // Phase 10A: Add domain hint if top_houses available
  const domainHint = getDomainHint(topHouses);
  if (domainHint) {
    const withDomain = `${baseHeadline}, especially around ${domainHint}.`;
    // Only add if stays under 28 words and passes validation
    const wordCount = withDomain.split(' ').length;
    if (wordCount <= 28 && validateResonanceText(withDomain)) {
      baseHeadline = withDomain.replace(/\.$/, '');
    }
  }
  
  // Phase 10A: Add echo phrase if journal overlap detected
  if (hasJournalOverlap) {
    const echoPhrase = selectEchoPhrase(userId);
    const withEcho = `${baseHeadline}${echoPhrase}.`;
    // Only add if stays under 28 words and passes validation
    const wordCount = withEcho.split(' ').length;
    if (wordCount <= 28 && validateResonanceText(withEcho)) {
      return withEcho;
    }
  }
  
  // Ensure ends with period
  return baseHeadline.endsWith('.') ? baseHeadline : `${baseHeadline}.`;
};

/**
 * Detect primary tension type from aspects
 */
const detectPrimaryTension = (aspects: TransitAspect[]): TensionArchetype | null => {
  if (!aspects || aspects.length === 0) return null;
  
  // Find tightest aspect (lowest orb)
  const sortedAspects = [...aspects].sort((a, b) => a.orb - b.orb);
  const primaryAspect = sortedAspects[0];
  
  if (!primaryAspect) return null;
  
  return ASPECT_ARCHETYPES[primaryAspect.aspect] || DEFAULT_ARCHETYPE;
};

/**
 * Part B: Generate context-aware 7-day arc question
 * Blends day theme with active tension
 */
const generateContextAwareQuestion = (
  daysSinceSignup: number,
  aspects: TransitAspect[],
  userId: string
): string | null => {
  // Only for first 7 days
  if (daysSinceSignup < 0 || daysSinceSignup > 7) return null;
  
  const dayFocus = SEVEN_DAY_ARC[daysSinceSignup];
  if (!dayFocus) return null;
  
  // Get the day's theme key (lowercase)
  const themeKey = dayFocus.theme.toLowerCase();
  
  // Get primary tension archetype
  const tension = detectPrimaryTension(aspects);
  
  // If we have tension data, try to get a tension-aware question
  if (tension && tension.questionModifiers) {
    const modifiers = tension.questionModifiers[themeKey];
    
    if (modifiers && modifiers.length > 0) {
      // Select deterministically
      const dateKey = getLocalDateKey();
      const hashKey = `${userId}|${dateKey}|question|${themeKey}|${tension.type}`;
      const hash = stableHash(hashKey);
      const index = hash % modifiers.length;
      
      const question = modifiers[index];
      
      // Validate safety and length (under 16 words)
      if (validateResonanceText(question) && question.split(' ').length <= 16) {
        return question;
      }
    }
  }
  
  // Fall back to static day question
  return dayFocus.questionModifier || null;
};

/**
 * Part C: Check for micro validation (journal signature overlap)
 * Returns "This may feel familiar." if overlap detected
 */
const checkMicroValidation = (
  currentEvents: string[],
  journalSignatures?: JournalSignature[]
): string | null => {
  if (!currentEvents || currentEvents.length === 0) return null;
  if (!journalSignatures || journalSignatures.length === 0) return null;
  
  // Get recent signatures (last 3)
  const recentSignatures = journalSignatures.slice(0, 3);
  
  // Check for overlap
  for (const sig of recentSignatures) {
    if (sig.events && sig.events.length > 0) {
      // Check if any current event matches a recent journal event
      for (const currentEvent of currentEvents) {
        if (sig.events.includes(currentEvent)) {
          return 'This may feel familiar.';
        }
      }
    }
  }
  
  return null;
};

/**
 * Convert aspects to canonical event strings for comparison
 */
const aspectsToEvents = (aspects: TransitAspect[]): string[] => {
  return aspects.map(a => `${a.transit_planet}_${a.aspect}_${a.natal_body}`);
};

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
// PHASE 6: First 7-Day Guided Arc
// ============================================

// Day-based focus themes for first week (quiet guidance)
interface DayFocus {
  theme: string;
  focus: string;
  questionModifier?: string;
}

const SEVEN_DAY_ARC: Record<number, DayFocus> = {
  0: { theme: 'Orientation', focus: 'noticing', questionModifier: 'What do you notice about how you feel right now?' },
  1: { theme: 'Orientation', focus: 'noticing', questionModifier: 'What catches your attention today?' },
  2: { theme: 'Awareness', focus: 'emotional patterns', questionModifier: 'What emotions have been present lately?' },
  3: { theme: 'Pattern', focus: 'recurring themes', questionModifier: 'What patterns are you starting to see?' },
  4: { theme: 'Choice', focus: 'agency', questionModifier: 'What feels like it\'s in your control today?' },
  5: { theme: 'Tension', focus: 'friction points', questionModifier: 'Where do you feel friction or resistance?' },
  6: { theme: 'Integration', focus: 'alignment', questionModifier: 'What feels aligned? What doesn\'t?' },
  7: { theme: 'Review', focus: 'looking back', questionModifier: 'What have you started to notice about yourself this week?' },
};

/**
 * Calculate days since user signup
 */
const getDaysSinceSignup = (createdAt: string | undefined): number => {
  if (!createdAt) return -1;
  
  try {
    const signupDate = new Date(createdAt);
    const now = new Date();
    const diffMs = now.getTime() - signupDate.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    return diffDays;
  } catch {
    return -1;
  }
};

/**
 * Get the day-appropriate reflection question for first 7 days.
 * Returns null if user is past day 7 or if no modification needed.
 */
const getGuidedArcQuestion = (daysSinceSignup: number): string | null => {
  // Only apply for days 0-7
  if (daysSinceSignup < 0 || daysSinceSignup > 7) return null;
  
  const dayFocus = SEVEN_DAY_ARC[daysSinceSignup];
  return dayFocus?.questionModifier || null;
};

/**
 * Get the progress indicator text for first week.
 * Returns null if past day 7.
 */
const getProgressIndicator = (daysSinceSignup: number): string | null => {
  if (daysSinceSignup < 0 || daysSinceSignup > 7) return null;
  
  // Day 0 counts as Day 1 for user display
  const displayDay = daysSinceSignup + 1;
  return `Day ${displayDay} of your first week`;
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
  
  // Get chart and user from store
  const chart = useAppStore((state) => state.chart);
  const user = useAppStore((state) => state.user);
  
  // Phase 6: Calculate days since signup
  // DEBUG_DAY_OVERRIDE: Set to a number (0-7) to test different days of the arc
  // Set to null for production behavior
  const DEBUG_DAY_OVERRIDE: number | null = null;  // Production mode
  
  const daysSinceSignup = React.useMemo(() => {
    // In staging/debug mode with override set, use the override value
    if (DEBUG_DAY_OVERRIDE !== null && (BUILD_ENV === 'staging' || BUILD_ENV === 'preview')) {
      return DEBUG_DAY_OVERRIDE;
    }
    
    return getDaysSinceSignup(user?.created_at);
  }, [user?.created_at]);
  
  // Phase 6: Get guided arc values
  const progressIndicator = React.useMemo(() => {
    return getProgressIndicator(daysSinceSignup);
  }, [daysSinceSignup]);
  
  const guidedQuestion = React.useMemo(() => {
    return getGuidedArcQuestion(daysSinceSignup);
  }, [daysSinceSignup]);
  
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
  
  // Phase 10: Raw transit aspects for Resonance Engine
  const [rawTransitAspects, setRawTransitAspects] = useState<TransitAspect[]>([]);
  
  // Phase 13: Chapter data state
  const [chapterData, setChapterData] = useState<ChapterResponse | null>(null);
  const [chapterLoading, setChapterLoading] = useState(false);
  
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
  
  // Phase 10: Fetch raw transit aspects for Resonance Engine
  useEffect(() => {
    const fetchRawAspects = async () => {
      if (!userId) return;
      
      try {
        const compute = await getTransitCompute(userId);
        if (compute?.aspects_to_natal_now) {
          setRawTransitAspects(compute.aspects_to_natal_now);
        }
      } catch (err) {
        console.debug('[HomeV2] Raw aspects fetch skipped:', err);
      }
    };
    
    fetchRawAspects();
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
  
  // Phase 13: Fetch chapter data with 24-hour client-side caching
  useEffect(() => {
    const fetchChapter = async () => {
      if (!userId) return;
      
      try {
        // Check cache first
        const cachedData = await AsyncStorage.getItem(CHAPTER_CACHE_KEY);
        if (cachedData) {
          const { data, userId: cachedUserId, timestamp } = JSON.parse(cachedData);
          const now = Date.now();
          const hoursSinceCache = (now - timestamp) / (1000 * 60 * 60);
          
          // Use cache if < 24 hours old and same user
          if (hoursSinceCache < 24 && cachedUserId === userId) {
            console.debug('[HomeV2] Using cached chapter data');
            setChapterData(data);
            return;
          }
        }
        
        // Fetch fresh data
        setChapterLoading(true);
        const data = await getChapter(userId, 180);
        setChapterData(data);
        
        // Cache the result
        await AsyncStorage.setItem(CHAPTER_CACHE_KEY, JSON.stringify({
          data,
          userId,
          timestamp: Date.now(),
        }));
        console.debug('[HomeV2] Chapter data fetched and cached');
      } catch (err) {
        console.debug('[HomeV2] Chapter fetch skipped:', err);
      } finally {
        setChapterLoading(false);
      }
    };
    
    fetchChapter();
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
  
  // Phase 11: Lens discovery configuration
  const LENS_ITEMS = [
    { key: 'astrology', label: 'Astrology', route: '/(tabs)/lenses?tab=astrology&mode=today' },
    { key: 'human_design', label: 'Human Design', route: '/(tabs)/lenses?tab=human_design&mode=today' },
    { key: 'numerology', label: 'Numerology', route: '/(tabs)/lenses?tab=numerology&mode=today' },
    { key: 'enneagram', label: 'Enneagram', route: '/(tabs)/lenses?tab=enneagram&mode=today' },
  ];
  
  // Phase 11: Handle lens tap - navigate to lens with "today" context
  const handleLensTap = useCallback((route: string) => {
    router.push(route as any);
  }, [router]);
  
  // Phase 11: Handle "Explore all lenses" tap
  const handleExploreLenses = useCallback(() => {
    router.push('/(tabs)/lenses');
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
    if (!localJournalEntries || localJournalEntries.length === 0) {
      return 'Start your first reflection.';
    }
    
    // Find most recent journal entry
    const sortedEntries = [...localJournalEntries].sort((a, b) => {
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
  }, [localJournalEntries]);
  
  // ============================================
  // DERIVED CONTENT (with cleaning)
  // Phase 10: Resonance Engine integration
  // Phase 10A: Domain hints + Journal echo texture
  // ============================================
  
  // Phase 10A: Extract top_houses from raw transit aspects
  // We derive dominant houses from which natal bodies are being aspected
  const topHouses = React.useMemo(() => {
    if (rawTransitAspects.length === 0) return [];
    
    // Map natal bodies to their natural house rulership for domain hints
    // This is a simplified mapping (not astrological - just for domain derivation)
    const bodyToHouse: Record<string, number> = {
      'sun': 5,        // creativity, identity
      'moon': 4,       // home, foundations  
      'mercury': 3,    // communication
      'venus': 7,      // relationships
      'mars': 1,       // identity, action
      'jupiter': 9,    // meaning, learning
      'saturn': 10,    // career, direction
      'uranus': 11,    // community
      'neptune': 12,   // inner life
      'pluto': 8,      // shared resources
      'asc': 1,        // identity
      'mc': 10,        // direction
    };
    
    // Count house hits from aspects
    const houseCounts: Record<number, number> = {};
    
    for (const aspect of rawTransitAspects) {
      const house = bodyToHouse[aspect.natal_body.toLowerCase()];
      if (house) {
        houseCounts[house] = (houseCounts[house] || 0) + 1;
      }
    }
    
    // Sort by count and return top houses
    return Object.entries(houseCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([house]) => parseInt(house));
  }, [rawTransitAspects]);
  
  // Phase 10: Micro validation check (needed before headline for echo)
  const { microValidation, hasJournalOverlap } = React.useMemo(() => {
    if (rawTransitAspects.length === 0) {
      return { microValidation: null, hasJournalOverlap: false };
    }
    
    const currentEvents = aspectsToEvents(rawTransitAspects);
    const journalSigs: JournalSignature[] = localJournalEntries
      .slice(0, 3)
      .map(entry => ({
        events: entry.transit_signature?.events || [],
        top_houses: entry.transit_signature?.top_houses || [],
      }));
    
    const validation = checkMicroValidation(currentEvents, journalSigs);
    return { 
      microValidation: validation, 
      hasJournalOverlap: validation !== null 
    };
  }, [rawTransitAspects, localJournalEntries]);
  
  // Phase 10 + 10A: Generate resonant headline from raw transit aspects
  // Now includes domain hints and echo phrases
  const resonantHeadline = React.useMemo(() => {
    if (rawTransitAspects.length === 0) return null;
    
    // Extract journal signatures
    const journalSigs: JournalSignature[] = localJournalEntries
      .slice(0, 3)
      .map(entry => ({
        events: entry.transit_signature?.events || [],
        top_houses: entry.transit_signature?.top_houses || [],
      }))
      .filter(sig => sig.events && sig.events.length > 0);
    
    return generateResonantHeadline(
      rawTransitAspects, 
      userId, 
      journalSigs,
      topHouses,          // Phase 10A: domain hints
      hasJournalOverlap   // Phase 10A: echo texture
    );
  }, [rawTransitAspects, userId, localJournalEntries, topHouses, hasJournalOverlap]);
  
  // Headline: Use resonant headline if available, otherwise fall back to cleaned transit headline
  const rawHeadline = transitInsight?.headline || keystone?.keystone || '';
  const cleanedHeadline = cleanHeadline(rawHeadline);
  const primaryHeadline = resonantHeadline || cleanedHeadline;
  
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
  // Phase 6 + 10: Use context-aware question for first 7 days
  const rawQuestion = transitInsight?.reflect?.[0] || keystone?.reflect_question || '';
  const baseReflectionQuestion = cleanReflectionQuestion(rawQuestion);
  
  // Phase 10: Try context-aware question first, then fall back to static guided question
  const contextAwareQuestion = React.useMemo(() => {
    if (daysSinceSignup < 0 || daysSinceSignup > 7) return null;
    return generateContextAwareQuestion(daysSinceSignup, rawTransitAspects, userId);
  }, [daysSinceSignup, rawTransitAspects, userId]);
  
  const reflectionQuestion = contextAwareQuestion || guidedQuestion || baseReflectionQuestion;
  
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
        
        {/* Phase 6: Progress indicator for first 7 days */}
        {progressIndicator && (
          <Text style={styles.progressIndicator}>
            {progressIndicator}
          </Text>
        )}
        
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
        
        {/* Phase 10: Micro Validation - shown if journal events overlap */}
        {microValidation && (
          <Text style={styles.microValidation}>
            {microValidation}
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
        
        {/* Phase 11: Lens Discovery Row */}
        <View style={styles.lensDiscoveryContainer}>
          <Text style={styles.lensDiscoveryLabel}>See this through:</Text>
          <View style={styles.lensLinksRow}>
            {LENS_ITEMS.map((lens, index) => (
              <React.Fragment key={lens.key}>
                <TouchableOpacity
                  onPress={() => handleLensTap(lens.route)}
                  activeOpacity={0.6}
                  style={styles.lensLinkTouch}
                >
                  <Text style={styles.lensLinkText}>{lens.label}</Text>
                </TouchableOpacity>
                {index < LENS_ITEMS.length - 1 && (
                  <Text style={styles.lensLinkSeparator}>·</Text>
                )}
              </React.Fragment>
            ))}
          </View>
          <TouchableOpacity
            onPress={handleExploreLenses}
            activeOpacity={0.6}
            style={styles.exploreLensesLink}
          >
            <Text style={styles.exploreLensesText}>Explore all lenses →</Text>
          </TouchableOpacity>
        </View>
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
  // Phase 6: Progress indicator for first 7 days
  progressIndicator: {
    fontSize: 11,
    color: Colors.textTertiary,
    opacity: 0.3,
    letterSpacing: 0.3,
    marginBottom: Spacing.xs,
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
  // Phase 10: Micro validation line
  microValidation: {
    fontSize: 12,
    fontWeight: '400',
    fontStyle: 'italic',
    color: Colors.textTertiary,
    opacity: 0.5,
    marginBottom: Spacing.sm,
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
  
  // Phase 11: Lens Discovery Row
  lensDiscoveryContainer: {
    marginTop: Spacing.xl,
    paddingTop: Spacing.lg,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.04)',
  },
  lensDiscoveryLabel: {
    fontSize: 11,
    color: Colors.textTertiary,
    opacity: 0.5,
    letterSpacing: 0.3,
    marginBottom: Spacing.sm,
  },
  lensLinksRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    alignItems: 'center',
    marginBottom: Spacing.sm,
  },
  lensLinkTouch: {
    paddingVertical: 4,
    paddingHorizontal: 2,
  },
  lensLinkText: {
    fontSize: 13,
    color: Colors.accent,
    fontWeight: '400',
    opacity: 0.85,
  },
  lensLinkSeparator: {
    fontSize: 13,
    color: Colors.textTertiary,
    opacity: 0.3,
    marginHorizontal: 6,
  },
  exploreLensesLink: {
    paddingVertical: 4,
    marginTop: Spacing.xs,
  },
  exploreLensesText: {
    fontSize: 12,
    color: Colors.textTertiary,
    opacity: 0.5,
    fontWeight: '400',
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
