/**
 * HomeInsightCard.tsx
 * 
 * Mirror-style daily insight for Home Screen.
 * Single-shape card: label → title → body → bridge → Reflect
 * NO legacy section headers.
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
} from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import { InlineResonanceReflect } from './ResonanceReflectButtons';

// Types - Mirror format
export interface DailyInsight {
  success: boolean;
  date: string;
  pattern_id: string;
  title: string;
  // New Mirror fields
  body?: string;
  bridge?: string;
  // Legacy fields (ignored in render, kept for compatibility)
  what_happening?: string;
  why_feels?: string;
  watch_for?: string;
  better_move?: string;
  interrupt?: string;
  phase?: string;
  phase_description?: string;
  confidence?: string;
}

interface Props {
  insight: DailyInsight | null;
  isLoading: boolean;
}

/**
 * Transform legacy insight into Mirror format
 */
function toMirrorFormat(insight: DailyInsight): { title: string; body: string; bridge: string | null } {
  // If already in new format, use directly
  if (insight.body) {
    return {
      title: insight.title,
      body: insight.body,
      bridge: insight.bridge || null,
    };
  }
  
  // Transform legacy format into Mirror voice
  // Take what_happening as the main body, make it personal
  const rawBody = insight.what_happening || '';
  
  // Clean up any system language
  let body = rawBody
    .replace(/Looking at your timeline[,.]?\s*/gi, '')
    .replace(/a certain rhythm appears[,.]?\s*/gi, '')
    .replace(/deeper arc/gi, 'pattern')
    .replace(/This pattern suggests/gi, 'You may notice')
    .replace(/Current life phase/gi, 'Right now')
    .replace(/Active influences/gi, 'What\'s present');
  
  // If body is empty or too short, create a Mirror-style fallback
  if (!body || body.length < 20) {
    body = 'Something in this moment may feel familiar. Not the details—the texture underneath. You\'ve been somewhere like this before.';
  }
  
  // Use why_feels as bridge if available and not system-sounding
  let bridge: string | null = null;
  if (insight.why_feels && !insight.why_feels.includes('timeline') && !insight.why_feels.includes('rhythm')) {
    bridge = insight.why_feels;
  }
  
  return {
    title: insight.title || 'Something Familiar',
    body,
    bridge,
  };
}

export default function HomeInsightCard({ insight, isLoading }: Props) {
  const { theme } = useTheme();

  // Loading state
  if (isLoading) {
    return (
      <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.loadingText, { color: theme.textTertiary }]}>
          Reading patterns...
        </Text>
      </View>
    );
  }

  // No data state
  if (!insight) {
    return null;
  }

  // Transform to Mirror format
  const mirror = toMirrorFormat(insight);

  return (
    <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
      {/* Eyebrow Label */}
      <Text style={[styles.eyebrow, { color: theme.textTertiary }]}>
        TODAY'S INSIGHT
      </Text>

      {/* Title */}
      <Text style={[styles.title, { color: theme.text }]}>
        {mirror.title}
      </Text>

      {/* Body */}
      <Text style={[styles.body, { color: theme.textSecondary }]}>
        {mirror.body}
      </Text>

      {/* Bridge (optional) */}
      {mirror.bridge && (
        <Text style={[styles.bridge, { color: theme.textTertiary }]}>
          {mirror.bridge}
        </Text>
      )}

      {/* Resonance + Reflect CTA */}
      <View style={[styles.ctaContainer, { borderTopColor: theme.border }]}>
        <InlineResonanceReflect
          source={{
            lens: 'patterns',
            type: 'daily_insight',
            name: mirror.title,
            value: mirror.body,
            id: `insight_${insight.date}`,
          }}
          patternSignature={`daily_insight_${insight.pattern_id}`}
          context="home"
          prompt={`What feels familiar about this moment?`}
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    borderRadius: 16,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 20,
    marginBottom: 16,
  },
  loadingText: {
    fontSize: 14,
    textAlign: 'center',
    paddingVertical: 20,
  },
  eyebrow: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 8,
    textTransform: 'uppercase',
  },
  title: {
    fontSize: 24,
    fontWeight: '600',
    lineHeight: 30,
    marginBottom: 12,
  },
  body: {
    fontSize: 15,
    lineHeight: 24,
    marginBottom: 8,
  },
  bridge: {
    fontSize: 14,
    lineHeight: 21,
    fontStyle: 'italic',
    marginBottom: 12,
  },
  ctaContainer: {
    marginTop: 12,
    paddingTop: 14,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
});
