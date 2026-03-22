/**
 * TodayPatternCard
 * Home screen integration for Dominant Truth
 * Shows headline only - skimmable in <3 seconds
 */

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { useDominantTruthForHome } from '../hooks/useDominantTruth';

interface TodayPatternCardProps {
  userId: string;
  theme: any;
  onReflect?: () => void;
}

export default function TodayPatternCard({ userId, theme, onReflect }: TodayPatternCardProps) {
  const router = useRouter();
  const { data, isLoading, hasPattern } = useDominantTruthForHome(userId);

  // Don't render if no pattern detected
  if (!isLoading && !hasPattern) {
    return null;
  }

  const handleReflect = () => {
    if (onReflect) {
      onReflect();
    } else {
      // Navigate to Today tab in Astrology lens
      router.push({
        pathname: '/lenses/astrology',
        params: { tab: 'today' }
      });
    }
  };

  const handleExplore = () => {
    // Navigate to Today tab in Astrology lens
    router.push({
      pathname: '/lenses/astrology',
      params: { tab: 'today' }
    });
  };

  if (isLoading) {
    return (
      <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <ActivityIndicator size="small" color={theme.textTertiary} />
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.accent + '30' }]}>
      {/* Label */}
      <Text style={[styles.label, { color: theme.accent }]}>TODAY'S PATTERN</Text>
      
      {/* Headline - the hook */}
      <Text style={[styles.headline, { color: theme.text }]}>
        "{data?.headline}"
      </Text>
      
      {/* Supporting line (optional - only for high confidence) */}
      {data?.supportingLine && (
        <Text style={[styles.supportingLine, { color: theme.textTertiary }]}>
          {data.supportingLine}
        </Text>
      )}
      
      {/* CTAs */}
      <View style={styles.ctaRow}>
        <TouchableOpacity
          style={[styles.ctaButton, { backgroundColor: theme.accent }]}
          onPress={handleReflect}
          activeOpacity={0.7}
        >
          <Text style={[styles.ctaText, { color: theme.background }]}>Reflect</Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={[styles.ctaButtonSecondary, { borderColor: theme.border }]}
          onPress={handleExplore}
          activeOpacity={0.7}
        >
          <Text style={[styles.ctaTextSecondary, { color: theme.textSecondary }]}>Explore</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    marginBottom: 12,
  },
  label: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.8,
    marginBottom: 8,
  },
  headline: {
    fontSize: 17,
    fontWeight: '600',
    lineHeight: 24,
    fontStyle: 'italic',
    marginBottom: 8,
  },
  supportingLine: {
    fontSize: 13,
    lineHeight: 18,
    marginBottom: 12,
  },
  ctaRow: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 4,
  },
  ctaButton: {
    paddingVertical: 10,
    paddingHorizontal: 18,
    borderRadius: 20,
  },
  ctaButtonSecondary: {
    paddingVertical: 10,
    paddingHorizontal: 18,
    borderRadius: 20,
    borderWidth: 1,
  },
  ctaText: {
    fontSize: 14,
    fontWeight: '600',
  },
  ctaTextSecondary: {
    fontSize: 14,
    fontWeight: '500',
  },
});
