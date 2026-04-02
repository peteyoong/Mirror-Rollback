/**
 * HomeSynthesisCard V5.0 - Decisive Pattern Synthesis
 * 
 * Home answers ONLY: "Out of everything happening — what matters most right now?"
 * 
 * 4-BLOCK STRUCTURE:
 * 1. THE CALL (1 sentence — sharp, decisive)
 * 2. THE REALITY (1–2 sentences — grounded, felt experience)
 * 3. THE SOURCE HINT (1 sentence — subtle synthesis cue)
 * 4. THE EDGE (1 sentence — tension / choice)
 * + CTA: "See what's driving this today →"
 * 
 * NO:
 * - explaining transits
 * - mentioning astrology explicitly
 * - long advice
 * - horoscope tone
 */

import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator, Platform } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import api from '../services/api';

interface HomeSynthesisData {
  success: boolean;
  date: string;
  pattern_key: string;
  the_call: string;
  the_reality: string;
  the_source_hint: string;
  the_edge: string;
  cta_text: string;
  cta_target: string;
  pattern_memory_state: string;
  evolution_state: string;
  angle_id: string;
  version: string;
  debug?: any;
}

interface HomeSynthesisCardProps {
  userId: string;
  theme: {
    background: string;
    surface: string;
    text: string;
    textSecondary: string;
    textTertiary: string;
    accent: string;
    border: string;
    cardBackground?: string;
    textInverse?: string;
  };
  onNavigateToAstro?: () => void;
}

const HomeSynthesisCard: React.FC<HomeSynthesisCardProps> = ({
  userId,
  theme,
  onNavigateToAstro,
}) => {
  const router = useRouter();
  const [synthesis, setSynthesis] = useState<HomeSynthesisData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSynthesis();
  }, [userId]);

  const loadSynthesis = async () => {
    if (!userId) {
      setLoading(false);
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      
      const response = await api.get(`/home-synthesis/${userId}`);
      setSynthesis(response.data);
    } catch (err: any) {
      console.error('[HomeSynthesisCard] Error:', err);
      setError(err.message || 'Failed to load');
    } finally {
      setLoading(false);
    }
  };

  const handleCTAPress = () => {
    if (onNavigateToAstro) {
      onNavigateToAstro();
    } else {
      // Navigate to Astrology tab
      router.push('/(tabs)/astrology');
    }
  };

  // Pattern state indicator
  const getPatternStateIndicator = () => {
    if (!synthesis) return null;
    
    const state = synthesis.pattern_memory_state;
    const evolution = synthesis.evolution_state;
    
    if (evolution === 'escalating') {
      return { label: 'Intensifying', color: '#E53935' };
    } else if (evolution === 'looping') {
      return { label: 'Looping', color: '#FF9800' };
    } else if (evolution === 'integrating') {
      return { label: 'Shifting', color: '#4CAF50' };
    } else if (state === 'recurring_pattern') {
      return { label: 'Recurring', color: '#9E9E9E' };
    } else if (state === 'returning_pattern') {
      return { label: 'Returning', color: '#9E9E9E' };
    }
    
    return null;
  };

  if (loading) {
    return (
      <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="small" color={theme.accent} />
          <Text style={[styles.loadingText, { color: theme.textTertiary }]}>
            Synthesizing patterns...
          </Text>
        </View>
      </View>
    );
  }

  if (error || !synthesis) {
    return (
      <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.errorText, { color: theme.textSecondary }]}>
          {error || 'Unable to load synthesis'}
        </Text>
        <TouchableOpacity onPress={loadSynthesis}>
          <Text style={[styles.retryText, { color: theme.accent }]}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const stateIndicator = getPatternStateIndicator();

  return (
    <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.accent + '30' }]}>
      
      {/* Pattern State Indicator (if applicable) */}
      {stateIndicator && (
        <View style={[styles.stateIndicator, { backgroundColor: stateIndicator.color + '15' }]}>
          <View style={[styles.stateDot, { backgroundColor: stateIndicator.color }]} />
          <Text style={[styles.stateText, { color: stateIndicator.color }]}>
            {stateIndicator.label}
          </Text>
        </View>
      )}

      {/* 1. THE CALL - Sharp, decisive */}
      <Text style={[styles.theCall, { color: theme.text }]}>
        {synthesis.the_call}
      </Text>

      {/* 2. THE REALITY - Grounded, felt experience */}
      <View style={[styles.realityContainer, { borderLeftColor: theme.accent + '40' }]}>
        <Text style={[styles.theReality, { color: theme.textSecondary }]}>
          {synthesis.the_reality}
        </Text>
      </View>

      {/* 3. THE SOURCE HINT - Subtle synthesis cue */}
      <Text style={[styles.sourceHint, { color: theme.textTertiary }]}>
        {synthesis.the_source_hint}
      </Text>

      {/* 4. THE EDGE - Tension / choice */}
      <View style={[styles.edgeContainer, { backgroundColor: theme.cardBackground || theme.background }]}>
        <Text style={[styles.theEdge, { color: theme.text }]}>
          {synthesis.the_edge}
        </Text>
      </View>

      {/* CTA - Deep link to Astrology Today */}
      <TouchableOpacity
        style={[styles.ctaButton, { backgroundColor: theme.accent }]}
        onPress={handleCTAPress}
        activeOpacity={0.8}
      >
        <Text style={[styles.ctaText, { color: theme.textInverse || '#FFFFFF' }]}>
          {synthesis.cta_text}
        </Text>
        <Ionicons name="arrow-forward" size={18} color={theme.textInverse || '#FFFFFF'} />
      </TouchableOpacity>

    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    borderRadius: 16,
    padding: 20,
    marginVertical: 8,
    borderWidth: 1,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.08,
        shadowRadius: 8,
      },
      android: {
        elevation: 3,
      },
    }),
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 24,
  },
  loadingText: {
    marginLeft: 12,
    fontSize: 14,
  },
  errorText: {
    fontSize: 14,
    textAlign: 'center',
    paddingVertical: 16,
  },
  retryText: {
    fontSize: 14,
    textAlign: 'center',
    fontWeight: '600',
  },
  stateIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    marginBottom: 12,
  },
  stateDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginRight: 6,
  },
  stateText: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },
  theCall: {
    fontSize: 22,
    fontWeight: '700',
    lineHeight: 28,
    marginBottom: 16,
    letterSpacing: -0.3,
  },
  realityContainer: {
    borderLeftWidth: 3,
    paddingLeft: 14,
    marginBottom: 16,
  },
  theReality: {
    fontSize: 16,
    lineHeight: 24,
  },
  sourceHint: {
    fontSize: 13,
    fontStyle: 'italic',
    marginBottom: 16,
    paddingHorizontal: 4,
  },
  edgeContainer: {
    borderRadius: 10,
    padding: 14,
    marginBottom: 20,
  },
  theEdge: {
    fontSize: 15,
    lineHeight: 22,
    fontWeight: '500',
  },
  ctaButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 12,
    gap: 8,
  },
  ctaText: {
    fontSize: 16,
    fontWeight: '600',
    letterSpacing: 0.2,
  },
});

export default HomeSynthesisCard;
