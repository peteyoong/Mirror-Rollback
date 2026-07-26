/**
 * InlineSignalsCard - Expanded signals view for Exploratory mode
 * 
 * Shows full grouped signals with interpretations.
 * Only rendered in exploratory mode where users want depth and exploration.
 */

import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { getPatternSignals, PatternSignalDetail, PatternSignalsResponse } from '../services/api';

interface InlineSignalsCardProps {
  userId: string;
  theme: any;
  showSynthesis?: boolean;
}

export default function InlineSignalsCard({ userId, theme, showSynthesis = true }: InlineSignalsCardProps) {
  const router = useRouter();
  const [data, setData] = useState<PatternSignalsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchSignals();
  }, [userId]);

  const fetchSignals = async () => {
    try {
      setIsLoading(true);
      const result = await getPatternSignals(userId);
      setData(result);
    } catch (err) {
      console.error('[InlineSignalsCard] Error:', err);
      setError('Unable to load signals');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSeeAll = () => {
    router.push('/signals');
  };

  const renderSignalGroup = (title: string, signals: PatternSignalDetail[] | undefined, icon: string) => {
    if (!signals || signals.length === 0) return null;
    
    return (
      <View style={styles.signalGroup}>
        <View style={styles.groupHeader}>
          <Text style={[styles.groupIcon, { color: theme.textTertiary }]}>{icon}</Text>
          <Text style={[styles.groupTitle, { color: theme.textSecondary }]}>{title}</Text>
        </View>
        {signals.slice(0, 3).map((signal, index) => (
          <View key={index} style={[styles.signalItem, { borderLeftColor: theme.accent + '40' }]}>
            <Text style={[styles.signalLabel, { color: theme.text }]}>{signal.label}</Text>
            <Text style={[styles.signalMeaning, { color: theme.textSecondary }]}>{signal.meaning}</Text>
          </View>
        ))}
      </View>
    );
  };

  if (isLoading) {
    return (
      <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.accent + '30' }]}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="small" color={theme.textTertiary} />
          <Text style={[styles.loadingText, { color: theme.textTertiary }]}>Loading signals...</Text>
        </View>
      </View>
    );
  }

  if (error || !data) {
    return null; // Silent fail - don't show error on home
  }

  const hasSignals = data.signals?.astrology?.length || data.signals?.human_design?.length || data.signals?.pattern_history?.length;
  
  if (!hasSignals) return null;

  return (
    <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.accent + '30' }]}>
      {/* Label */}
      <Text style={[styles.label, { color: theme.textTertiary }]}>ACTIVE SIGNALS</Text>
      
      {/* Summary */}
      {data.summary && (
        <Text style={[styles.summary, { color: theme.text }]}>
          {data.summary}
        </Text>
      )}
      
      {/* Signal Groups */}
      <View style={styles.signalGroups}>
        {renderSignalGroup('Astrology', data.signals?.astrology, '◐')}
        {renderSignalGroup('Human Design', data.signals?.human_design, '⬡')}
        {renderSignalGroup('Pattern History', data.signals?.pattern_history, '↻')}
      </View>
      
      {/* Synthesis - only if enabled */}
      {showSynthesis && data.synthesis && (
        <View style={[styles.synthesisBox, { backgroundColor: theme.accent + '10' }]}>
          <Text style={[styles.synthesisLabel, { color: theme.textTertiary }]}>CROSS-LENS SYNTHESIS</Text>
          <Text style={[styles.synthesisText, { color: theme.textSecondary }]}>
            {data.synthesis}
          </Text>
        </View>
      )}
      
      {/* See All Link */}
      <TouchableOpacity
        style={styles.seeAllLink}
        onPress={handleSeeAll}
        activeOpacity={0.7}
      >
        <Text style={[styles.seeAllText, { color: theme.accent }]}>
          Explore all signals →
        </Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    marginBottom: 16,
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 20,
    gap: 8,
  },
  loadingText: {
    fontSize: 16,
    fontStyle: 'italic',
  },
  label: {
    fontSize: 14,
    fontWeight: '500',
    letterSpacing: 0.8,
    marginBottom: 14,
  },
  summary: {
    fontSize: 17,
    lineHeight: 26,
    marginBottom: 16,
  },
  signalGroups: {
    gap: 16,
  },
  signalGroup: {
    gap: 8,
  },
  groupHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 4,
  },
  groupIcon: {
    fontSize: 16,
  },
  groupTitle: {
    fontSize: 14,
    fontWeight: '500',
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },
  signalItem: {
    borderLeftWidth: 2,
    paddingLeft: 12,
    marginLeft: 4,
  },
  signalLabel: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 2,
  },
  signalMeaning: {
    fontSize: 16,
    lineHeight: 27,
  },
  synthesisBox: {
    marginTop: 16,
    padding: 14,
    borderRadius: 10,
  },
  synthesisLabel: {
    fontSize: 9,
    fontWeight: '500',
    letterSpacing: 0.6,
    marginBottom: 6,
  },
  synthesisText: {
    fontSize: 16,
    lineHeight: 28,
    fontStyle: 'italic',
  },
  seeAllLink: {
    marginTop: 16,
    alignItems: 'flex-end',
  },
  seeAllText: {
    fontSize: 16,
    fontWeight: '500',
  },
});
