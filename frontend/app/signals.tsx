import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { useTheme } from '../contexts/ThemeContext';
import { useAppStore } from '../store';
import { getPatternSignals, PatternSignalDetail, PatternSignalsResponse } from '../services/api';

export default function SignalsScreen() {
  const router = useRouter();
  const { theme } = useTheme();
  const { user } = useAppStore();
  const [data, setData] = useState<PatternSignalsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (user?.id) {
      fetchSignals();
    }
  }, [user?.id]);

  const fetchSignals = async () => {
    if (!user?.id) return;
    
    try {
      setLoading(true);
      const result = await getPatternSignals(user.id);
      setData(result);
    } catch (err) {
      console.error('[Signals] Error:', err);
      setError('Unable to load signals');
    } finally {
      setLoading(false);
    }
  };

  const renderSignalSection = (title: string, signals: PatternSignalDetail[] | undefined, icon: string) => {
    if (!signals || signals.length === 0) return null;

    return (
      <View style={styles.signalSection}>
        <View style={styles.sectionHeader}>
          <Text style={[styles.sectionIcon, { color: theme.textTertiary }]}>{icon}</Text>
          <Text style={[styles.sectionTitle, { color: theme.textSecondary }]}>{title}</Text>
        </View>
        {signals.map((signal, index) => (
          <View key={index} style={[styles.signalItem, { borderLeftColor: theme.accent + '40' }]}>
            <Text style={[styles.signalLabel, { color: theme.text }]}>{signal.label}</Text>
            <Text style={[styles.signalMeaning, { color: theme.textSecondary }]}>{signal.meaning}</Text>
            {signal.strength && signal.strength > 0.6 && (
              <Text style={[styles.signalStrength, { color: theme.accent }]}>Strong signal</Text>
            )}
          </View>
        ))}
      </View>
    );
  };

  if (loading) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.textTertiary} />
          <Text style={[styles.loadingText, { color: theme.textTertiary }]}>
            Tracing signals...
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  if (error) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
            <Text style={[styles.backText, { color: theme.textSecondary }]}>← Back</Text>
          </TouchableOpacity>
        </View>
        <View style={styles.errorContainer}>
          <Text style={[styles.errorText, { color: theme.textSecondary }]}>
            {error}
          </Text>
          <TouchableOpacity 
            onPress={fetchSignals} 
            style={[styles.retryButton, { borderColor: theme.border }]}
          >
            <Text style={[styles.retryText, { color: theme.text }]}>Try again</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Text style={[styles.backText, { color: theme.textSecondary }]}>← Back</Text>
        </TouchableOpacity>
        <Text style={[styles.headerTitle, { color: theme.text }]}>Why this is showing up</Text>
      </View>

      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        {/* Summary */}
        <View style={[styles.summaryCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.summaryLabel, { color: theme.textTertiary }]}>SUMMARY</Text>
          <Text style={[styles.summaryText, { color: theme.text }]}>
            {data?.summary || 'Something is surfacing, but the signals are still forming.'}
          </Text>
        </View>

        {/* Signal Sections */}
        <View style={styles.signalsContainer}>
          <Text style={[styles.signalsHeading, { color: theme.textTertiary }]}>SIGNALS</Text>
          
          {renderSignalSection('Astrology', data?.signals?.astrology, '◐')}
          {renderSignalSection('Human Design', data?.signals?.human_design, '⬡')}
          {renderSignalSection('Pattern History', data?.signals?.pattern_history, '↻')}

          {(!data?.signals?.astrology && !data?.signals?.human_design && !data?.signals?.pattern_history) && (
            <View style={styles.noSignals}>
              <Text style={[styles.noSignalsText, { color: theme.textTertiary }]}>
                No specific signals traced yet. Complete your profile to see deeper connections.
              </Text>
            </View>
          )}
        </View>

        {/* Synthesis */}
        <View style={[styles.synthesisCard, { backgroundColor: theme.surface, borderColor: theme.accent + '30' }]}>
          <Text style={[styles.synthesisLabel, { color: theme.textTertiary }]}>SYNTHESIS</Text>
          <Text style={[styles.synthesisText, { color: theme.text }]}>
            {data?.synthesis || "Trust what you're noticing. Patterns surface when they're ready to be seen."}
          </Text>
        </View>

        {/* Footer note */}
        <View style={styles.footerNote}>
          <Text style={[styles.footerText, { color: theme.textTertiary }]}>
            This is not random. Multiple signals are pointing to the same pattern.
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 16,
  },
  loadingText: {
    fontSize: 14,
    fontStyle: 'italic',
  },
  header: {
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.08)',
  },
  backButton: {
    marginBottom: 12,
  },
  backText: {
    fontSize: 14,
  },
  headerTitle: {
    fontSize: 22,
    fontWeight: '600',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 20,
    paddingBottom: 40,
  },
  summaryCard: {
    borderRadius: 12,
    padding: 18,
    borderWidth: 1,
    marginBottom: 24,
  },
  summaryLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.8,
    marginBottom: 10,
  },
  summaryText: {
    fontSize: 16,
    lineHeight: 24,
  },
  signalsContainer: {
    marginBottom: 24,
  },
  signalsHeading: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.8,
    marginBottom: 16,
  },
  signalSection: {
    marginBottom: 20,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  sectionIcon: {
    fontSize: 16,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '500',
  },
  signalItem: {
    borderLeftWidth: 2,
    paddingLeft: 14,
    marginBottom: 12,
  },
  signalLabel: {
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 4,
  },
  signalMeaning: {
    fontSize: 13,
    lineHeight: 20,
  },
  signalStrength: {
    fontSize: 11,
    fontWeight: '500',
    marginTop: 4,
  },
  noSignals: {
    paddingVertical: 20,
  },
  noSignalsText: {
    fontSize: 14,
    fontStyle: 'italic',
    textAlign: 'center',
  },
  synthesisCard: {
    borderRadius: 12,
    padding: 18,
    borderWidth: 1,
    marginBottom: 24,
  },
  synthesisLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.8,
    marginBottom: 10,
  },
  synthesisText: {
    fontSize: 15,
    lineHeight: 24,
    fontStyle: 'italic',
  },
  footerNote: {
    alignItems: 'center',
    paddingVertical: 16,
  },
  footerText: {
    fontSize: 12,
    textAlign: 'center',
    fontStyle: 'italic',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  errorText: {
    fontSize: 15,
    textAlign: 'center',
    marginBottom: 20,
  },
  retryButton: {
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
    borderWidth: 1,
  },
  retryText: {
    fontSize: 14,
    fontWeight: '500',
  },
});
