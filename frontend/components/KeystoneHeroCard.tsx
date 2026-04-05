/**
 * KeystoneHeroCard.tsx
 * 
 * THE SINGLE SOURCE OF TRUTH for the homepage.
 * One Keystone Pattern. Everything else explains it.
 * 
 * Structure:
 * - Title (behavioral label - what you're doing)
 * - Body (3-line behavior sequence - the loop)
 * - Single CTA: Reflect →
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
} from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import { InlineResonanceReflect } from './ResonanceReflectButtons';

export interface KeystonePatternData {
  pattern_id: string;
  pattern_label: string;
  behavior_sequence: string[];
  confidence: number;
  sources: string[];
  date: string;
  cached?: boolean;
}

interface Props {
  data: KeystonePatternData | null;
  isLoading: boolean;
}

export default function KeystoneHeroCard({ data, isLoading }: Props) {
  const { theme } = useTheme();

  // Loading state
  if (isLoading) {
    return (
      <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <View style={styles.loadingContent}>
          <ActivityIndicator size="small" color={theme.textTertiary} />
          <Text style={[styles.loadingText, { color: theme.textTertiary }]}>
            Reading your pattern...
          </Text>
        </View>
      </View>
    );
  }

  // No data fallback
  if (!data) {
    return (
      <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.eyebrow, { color: theme.textTertiary }]}>
          TODAY'S PATTERN
        </Text>
        <Text style={[styles.title, { color: theme.text }]}>
          Something's Here
        </Text>
        <View style={styles.sequenceContainer}>
          <Text style={[styles.sequenceLine, { color: theme.textSecondary }]}>
            There's a pattern present today.
          </Text>
          <Text style={[styles.sequenceLine, { color: theme.textSecondary }]}>
            You might not have words for it yet.
          </Text>
          <Text style={[styles.sequenceLine, { color: theme.textSecondary }]}>
            That's okay. Start noticing.
          </Text>
        </View>
        <View style={[styles.ctaContainer, { borderTopColor: theme.border }]}>
          <InlineResonanceReflect
            source={{
              lens: 'keystone',
              type: 'daily_pattern',
              name: "Something's Here",
              value: "There's a pattern present today.",
              id: `keystone_${new Date().toISOString().split('T')[0]}`,
            }}
            prompt="What feels true about this?"
          />
        </View>
      </View>
    );
  }

  // Build the reflection value from the sequence
  const sequenceText = data.behavior_sequence.join(' ');

  return (
    <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
      {/* Eyebrow */}
      <Text style={[styles.eyebrow, { color: theme.textTertiary }]}>
        TODAY'S PATTERN
      </Text>

      {/* Title - The behavioral label */}
      <Text style={[styles.title, { color: theme.text }]}>
        {data.pattern_label}
      </Text>

      {/* Body - The 3-line behavior sequence */}
      <View style={styles.sequenceContainer}>
        {data.behavior_sequence.map((line, index) => (
          <Text 
            key={index} 
            style={[styles.sequenceLine, { color: theme.textSecondary }]}
          >
            {line}
          </Text>
        ))}
      </View>

      {/* Single CTA */}
      <View style={[styles.ctaContainer, { borderTopColor: theme.border }]}>
        <InlineResonanceReflect
          source={{
            lens: 'keystone',
            type: 'daily_pattern',
            name: data.pattern_label,
            value: sequenceText,
            id: `keystone_${data.date}_${data.pattern_id}`,
          }}
          prompt="Does this feel true?"
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginHorizontal: 20,
    marginTop: 8,
    marginBottom: 20,
    borderRadius: 16,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 24,
  },
  loadingContent: {
    alignItems: 'center',
    paddingVertical: 32,
    gap: 12,
  },
  loadingText: {
    fontSize: 14,
  },
  eyebrow: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1.5,
    marginBottom: 16,
    textTransform: 'uppercase',
  },
  title: {
    fontSize: 26,
    fontWeight: '600',
    lineHeight: 32,
    marginBottom: 20,
    letterSpacing: -0.3,
  },
  sequenceContainer: {
    gap: 12,
  },
  sequenceLine: {
    fontSize: 17,
    lineHeight: 26,
    letterSpacing: 0.1,
  },
  ctaContainer: {
    marginTop: 24,
    paddingTop: 20,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
});
