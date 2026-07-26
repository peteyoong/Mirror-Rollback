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
import { getPatternDiagnosis, PatternDiagnosisResponse } from '../services/api';
import { useExperienceControls } from '../hooks/useExperienceControls';

/**
 * Signals Screen - DIAGNOSIS-FIRST approach
 * 
 * Instead of separate lens summaries, we show:
 * 1. Core diagnosis (what's happening, why, what to do)
 * 2. Lens evidence as SUPPORT for the diagnosis
 * 
 * Mode controls depth, not structure.
 */
export default function SignalsScreen() {
  const router = useRouter();
  const { theme } = useTheme();
  const { user } = useAppStore();
  const { mode, modeConfig } = useExperienceControls();
  const [data, setData] = useState<PatternDiagnosisResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showEvidence, setShowEvidence] = useState(mode === 'exploratory');

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (user?.id) {
      fetchDiagnosis();
    }
  }, [user?.id]);

  const fetchDiagnosis = async () => {
    if (!user?.id) return;
    
    try {
      setLoading(true);
      const result = await getPatternDiagnosis(user.id);
      setData(result);
    } catch (err) {
      console.error('[Signals] Error:', err);
      setError('Unable to load diagnosis');
    } finally {
      setLoading(false);
    }
  };

  // Render the CORE DIAGNOSIS - the main interpretive output
  const renderCoreDiagnosis = () => {
    if (!data) return null;

    return (
      <View style={styles.diagnosisContainer}>
        {/* What is happening */}
        <View style={[styles.diagnosisSection, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.diagnosisLabel, { color: theme.textTertiary }]}>WHAT IS HAPPENING</Text>
          <Text style={[styles.diagnosisText, { color: theme.text }]}>
            {data.what_is_happening}
          </Text>
        </View>

        {/* What kind of moment - always show */}
        <View style={[styles.momentCard, { backgroundColor: theme.accent + '10', borderColor: theme.accent + '30' }]}>
          <Text style={[styles.momentText, { color: theme.text }]}>
            {data.what_kind_of_moment}
          </Text>
        </View>

        {/* Why it is happening - mode controls whether to show */}
        {(mode === 'exploratory' || mode === 'directive') && (
          <View style={[styles.diagnosisSection, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Text style={[styles.diagnosisLabel, { color: theme.textTertiary }]}>WHY THIS IS SHOWING UP</Text>
            <Text style={[styles.diagnosisText, { color: theme.textSecondary }]}>
              {data.why_it_is_happening}
            </Text>
          </View>
        )}

        {/* What would be wise - always show */}
        <View style={[styles.wisdomCard, { backgroundColor: theme.surface, borderColor: theme.accent + '40' }]}>
          <Text style={[styles.diagnosisLabel, { color: theme.textTertiary }]}>WHAT WOULD BE WISE</Text>
          <Text style={[styles.wisdomText, { color: theme.text }]}>
            {data.what_would_be_wise}
          </Text>
        </View>
      </View>
    );
  };

  // Render CONSTITUTION - stable patterns (exploratory only)
  const renderConstitution = () => {
    if (!data?.constitution || mode !== 'exploratory') return null;

    const { constitution } = data;

    return (
      <View style={[styles.constitutionCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>YOUR STABLE PATTERNS</Text>
        
        <View style={styles.constitutionGrid}>
          <View style={styles.constitutionItem}>
            <Text style={[styles.constitutionLabel, { color: theme.textTertiary }]}>How you move</Text>
            <Text style={[styles.constitutionValue, { color: theme.text }]}>{constitution.action_style}</Text>
          </View>
          <View style={styles.constitutionItem}>
            <Text style={[styles.constitutionLabel, { color: theme.textTertiary }]}>How clarity comes</Text>
            <Text style={[styles.constitutionValue, { color: theme.text }]}>{constitution.clarity_style}</Text>
          </View>
          <View style={styles.constitutionItem}>
            <Text style={[styles.constitutionLabel, { color: theme.textTertiary }]}>Your recurring gift</Text>
            <Text style={[styles.constitutionValue, { color: theme.text }]}>{constitution.recurring_gift}</Text>
          </View>
          <View style={styles.constitutionItem}>
            <Text style={[styles.constitutionLabel, { color: theme.textTertiary }]}>Your recurring risk</Text>
            <Text style={[styles.constitutionValue, { color: theme.text }]}>{constitution.recurring_failure_mode}</Text>
          </View>
        </View>
      </View>
    );
  };

  // Render LENS EVIDENCE as support for the diagnosis
  const renderLensEvidence = () => {
    if (!data?.evidence) return null;
    
    const hasEvidence = data.evidence.timing || data.evidence.design || data.evidence.history;
    if (!hasEvidence) return null;

    return (
      <View style={styles.evidenceContainer}>
        <TouchableOpacity 
          onPress={() => setShowEvidence(!showEvidence)}
          style={styles.evidenceToggle}
        >
          <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
            SUPPORTING EVIDENCE {showEvidence ? '▼' : '▶'}
          </Text>
        </TouchableOpacity>

        {showEvidence && (
          <View style={styles.evidenceList}>
            {data.evidence.timing && (
              <View style={[styles.evidenceItem, { borderLeftColor: theme.accent + '50' }]}>
                <Text style={[styles.evidenceSource, { color: theme.textTertiary }]}>TIMING</Text>
                <Text style={[styles.evidenceSummary, { color: theme.text }]}>{data.evidence.timing.summary}</Text>
                <Text style={[styles.evidenceImplication, { color: theme.textSecondary }]}>{data.evidence.timing.implication}</Text>
              </View>
            )}
            
            {data.evidence.design && (
              <View style={[styles.evidenceItem, { borderLeftColor: theme.accent + '50' }]}>
                <Text style={[styles.evidenceSource, { color: theme.textTertiary }]}>YOUR DESIGN</Text>
                <Text style={[styles.evidenceSummary, { color: theme.text }]}>{data.evidence.design.summary}</Text>
                <Text style={[styles.evidenceImplication, { color: theme.textSecondary }]}>{data.evidence.design.implication}</Text>
              </View>
            )}
            
            {data.evidence.history && (
              <View style={[styles.evidenceItem, { borderLeftColor: theme.accent + '50' }]}>
                <Text style={[styles.evidenceSource, { color: theme.textTertiary }]}>YOUR HISTORY</Text>
                <Text style={[styles.evidenceSummary, { color: theme.text }]}>{data.evidence.history.summary}</Text>
                <Text style={[styles.evidenceImplication, { color: theme.textSecondary }]}>{data.evidence.history.implication}</Text>
              </View>
            )}
          </View>
        )}
      </View>
    );
  };

  // Render HISTORY DETAILS - pattern recurrence (exploratory only)
  const renderHistoryDetails = () => {
    if (!data?.history || mode !== 'exploratory') return null;
    
    const { history } = data;
    if (!history.pattern_shape && !history.examples?.length) return null;

    return (
      <View style={[styles.historyCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>PATTERN RECURRENCE</Text>
        
        {history.pattern_shape && (
          <Text style={[styles.patternShape, { color: theme.text }]}>
            The shape: {history.pattern_shape}
          </Text>
        )}
        
        {history.examples && history.examples.length > 0 && (
          <View style={styles.examplesContainer}>
            <Text style={[styles.examplesLabel, { color: theme.textTertiary }]}>From your reflections:</Text>
            {history.examples.map((example, index) => (
              <Text key={index} style={[styles.exampleText, { color: theme.textSecondary }]}>
                &quot;{example}&quot;
              </Text>
            ))}
          </View>
        )}
        
        {history.cycle_observation && (
          <Text style={[styles.cycleText, { color: theme.textSecondary }]}>
            {history.cycle_observation}
          </Text>
        )}
        
        {history.deeper_roots && (
          <Text style={[styles.rootsText, { color: theme.textTertiary }]}>
            {history.deeper_roots}
          </Text>
        )}
      </View>
    );
  };

  if (loading) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.textTertiary} />
          <Text style={[styles.loadingText, { color: theme.textTertiary }]}>
            Building diagnosis...
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
            onPress={fetchDiagnosis} 
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
        {data?.pattern_title && (
          <Text style={[styles.patternTitle, { color: theme.textTertiary }]}>
            {data.pattern_title}
          </Text>
        )}
      </View>

      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        {/* Core Diagnosis - Always first */}
        {renderCoreDiagnosis()}

        {/* Constitution - Exploratory only */}
        {renderConstitution()}

        {/* History Details - Exploratory only */}
        {renderHistoryDetails()}

        {/* Lens Evidence - Collapsible support */}
        {renderLensEvidence()}

        {/* Confidence indicator */}
        {data?.confidence && mode === 'exploratory' && (
          <View style={styles.confidenceContainer}>
            <Text style={[styles.confidenceText, { color: theme.textTertiary }]}>
              Diagnosis confidence: {Math.round(data.confidence * 100)}%
            </Text>
          </View>
        )}
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
    fontWeight: '500',
    marginBottom: 4,
  },
  patternTitle: {
    fontSize: 14,
    fontStyle: 'italic',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 20,
    paddingBottom: 40,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  errorText: {
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 16,
  },
  retryButton: {
    borderWidth: 1,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  retryText: {
    fontSize: 14,
    fontWeight: '500',
  },
  
  // Diagnosis sections
  diagnosisContainer: {
    gap: 16,
    marginBottom: 24,
  },
  diagnosisSection: {
    borderRadius: 12,
    padding: 18,
    borderWidth: 1,
  },
  diagnosisLabel: {
    fontSize: 10,
    fontWeight: '500',
    letterSpacing: 0.8,
    marginBottom: 10,
  },
  diagnosisText: {
    fontSize: 16,
    lineHeight: 24,
  },
  momentCard: {
    borderRadius: 12,
    padding: 18,
    borderWidth: 1,
  },
  momentText: {
    fontSize: 15,
    lineHeight: 23,
    fontWeight: '500',
  },
  wisdomCard: {
    borderRadius: 12,
    padding: 18,
    borderWidth: 2,
  },
  wisdomText: {
    fontSize: 16,
    lineHeight: 24,
    fontWeight: '500',
  },
  
  // Constitution section
  constitutionCard: {
    borderRadius: 12,
    padding: 18,
    borderWidth: 1,
    marginBottom: 24,
  },
  sectionLabel: {
    fontSize: 10,
    fontWeight: '500',
    letterSpacing: 0.8,
    marginBottom: 16,
  },
  constitutionGrid: {
    gap: 16,
  },
  constitutionItem: {
    gap: 4,
  },
  constitutionLabel: {
    fontSize: 11,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  constitutionValue: {
    fontSize: 14,
    lineHeight: 20,
  },
  
  // Evidence section
  evidenceContainer: {
    marginBottom: 24,
  },
  evidenceToggle: {
    paddingVertical: 8,
  },
  evidenceList: {
    marginTop: 12,
    gap: 16,
  },
  evidenceItem: {
    borderLeftWidth: 2,
    paddingLeft: 14,
  },
  evidenceSource: {
    fontSize: 10,
    fontWeight: '500',
    letterSpacing: 0.8,
    marginBottom: 6,
  },
  evidenceSummary: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 6,
  },
  evidenceImplication: {
    fontSize: 13,
    lineHeight: 19,
    fontStyle: 'italic',
  },
  
  // History section
  historyCard: {
    borderRadius: 12,
    padding: 18,
    borderWidth: 1,
    marginBottom: 24,
  },
  patternShape: {
    fontSize: 15,
    lineHeight: 22,
    marginBottom: 12,
    fontWeight: '500',
  },
  examplesContainer: {
    marginTop: 12,
    gap: 8,
  },
  examplesLabel: {
    fontSize: 11,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  exampleText: {
    fontSize: 13,
    lineHeight: 20,
    fontStyle: 'italic',
    paddingLeft: 12,
    borderLeftWidth: 1,
    borderLeftColor: 'rgba(255,255,255,0.1)',
  },
  cycleText: {
    fontSize: 14,
    lineHeight: 21,
    marginTop: 12,
  },
  rootsText: {
    fontSize: 13,
    lineHeight: 20,
    marginTop: 8,
    fontStyle: 'italic',
  },
  
  // Confidence
  confidenceContainer: {
    alignItems: 'center',
    paddingVertical: 16,
  },
  confidenceText: {
    fontSize: 12,
  },
});
