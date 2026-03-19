/**
 * MirrorHeroCard.tsx
 * 
 * THE primary homepage card. One card. One truth. One action.
 * Built from scratch - not patched from legacy components.
 * 
 * Structure:
 * - Eyebrow label
 * - Strong title
 * - Body (2-4 sentences, Mirror voice)
 * - Optional bridge line
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
import { InlineReflectButton } from './UniversalReflectButton';

export interface MirrorHeroData {
  title: string;
  body: string;
  bridge?: string | null;
  reflectPrompt?: string;
  date?: string;
}

interface Props {
  data: MirrorHeroData | null;
  isLoading: boolean;
}

export default function MirrorHeroCard({ data, isLoading }: Props) {
  const { theme } = useTheme();

  // Loading state
  if (isLoading) {
    return (
      <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <View style={styles.loadingContent}>
          <ActivityIndicator size="small" color={theme.textTertiary} />
          <Text style={[styles.loadingText, { color: theme.textTertiary }]}>
            Reading today...
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
          TODAY
        </Text>
        <Text style={[styles.title, { color: theme.text }]}>
          Something Present
        </Text>
        <Text style={[styles.body, { color: theme.textSecondary }]}>
          There's something here today asking for your attention. You might not have words for it yet—and that's okay. Sometimes the naming comes after the noticing.
        </Text>
        <View style={[styles.ctaContainer, { borderTopColor: theme.border }]}>
          <InlineReflectButton
            source={{
              lens: 'mirror',
              type: 'daily_hero',
              name: 'Something Present',
              value: 'Today feels like it has something in it.',
              id: `hero_${new Date().toISOString().split('T')[0]}`,
            }}
            prompt="What feels most present right now?"
          />
        </View>
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
      {/* Eyebrow */}
      <Text style={[styles.eyebrow, { color: theme.textTertiary }]}>
        TODAY
      </Text>

      {/* Title */}
      <Text style={[styles.title, { color: theme.text }]}>
        {data.title}
      </Text>

      {/* Body */}
      <Text style={[styles.body, { color: theme.textSecondary }]}>
        {data.body}
      </Text>

      {/* Bridge (optional) */}
      {data.bridge && (
        <Text style={[styles.bridge, { color: theme.textTertiary }]}>
          {data.bridge}
        </Text>
      )}

      {/* Single CTA */}
      <View style={[styles.ctaContainer, { borderTopColor: theme.border }]}>
        <InlineReflectButton
          source={{
            lens: 'mirror',
            type: 'daily_hero',
            name: data.title,
            value: data.body,
            id: `hero_${data.date || new Date().toISOString().split('T')[0]}`,
          }}
          prompt={data.reflectPrompt || "What feels true about this?"}
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
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 1.5,
    marginBottom: 12,
    textTransform: 'uppercase',
  },
  title: {
    fontSize: 24,
    fontWeight: '600',
    lineHeight: 30,
    marginBottom: 16,
    letterSpacing: -0.3,
  },
  body: {
    fontSize: 16,
    lineHeight: 26,
    marginBottom: 8,
  },
  bridge: {
    fontSize: 15,
    lineHeight: 23,
    fontStyle: 'italic',
    marginTop: 8,
    marginBottom: 8,
  },
  ctaContainer: {
    marginTop: 20,
    paddingTop: 20,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
});
