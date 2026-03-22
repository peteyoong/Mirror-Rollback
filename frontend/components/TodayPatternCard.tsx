/**
 * TodayPatternCard
 * Home screen integration for Dominant Truth
 * Shows headline only - skimmable in <3 seconds
 * 
 * Now uses Mirror Response Engine for unified "light" intensity
 */

import React, { useMemo } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { useDominantTruthForHome } from '../hooks/useDominantTruth';
import { buildMirrorResponse, getHomeResponse } from '../services/mirrorResponseEngine';

interface TodayPatternCardProps {
  userId: string;
  theme: any;
  onReflect?: () => void;
}

export default function TodayPatternCard({ userId, theme, onReflect }: TodayPatternCardProps) {
  const router = useRouter();
  const { data, isLoading, hasPattern } = useDominantTruthForHome(userId);

  // Build unified Mirror response using the engine (light intensity for Home)
  const mirrorHomeData = useMemo(() => {
    if (!data || !hasPattern) return null;
    
    // Use the engine to build a response with "light" intensity
    const response = buildMirrorResponse({
      dominantTruth: data.dominantTruth ? {
        dominantTheme: data.dominantTruth,
        confidenceScore: data.confidence || 60,
      } : undefined,
      variationSeed: new Date().getDate(), // Changes daily
    });
    
    // Format for Home surface (light hook only)
    return getHomeResponse(response);
  }, [data, hasPattern]);

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
      
      {/* Headline - use engine response when available, fallback to original */}
      <Text style={[styles.headline, { color: theme.text }]}>
        "{mirrorHomeData?.headline || data?.headline}"
      </Text>
      
      {/* Supporting line - use engine response when available */}
      {(mirrorHomeData?.supporting || data?.supportingLine) && (
        <Text style={[styles.supportingLine, { color: theme.textTertiary }]}>
          {mirrorHomeData?.supporting || data?.supportingLine}
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
