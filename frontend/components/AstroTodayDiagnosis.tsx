/**
 * AstroTodayDiagnosis - Astrology Today Diagnosis Component V3.2
 * 
 * Matches Mirror-level diagnosis quality:
 * 1. Diagnosis Title (tension-based)
 * 2. Diagnosis Body (internal conflict, real behavior)
 * 3. Bridge (normalize experience)
 * 4. Misstep (consequence-based)
 * 5. Better Move (shows consequence, not command)
 * 6. Signals (collapsible: transits, houses)
 * 
 * V3.2: Mirror-level quality - sharper, more direct, tension-driven
 */

import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import api from '../services/api';
import { InsightCardFooter } from './InsightCardFooter';

interface AstroDiagnosisData {
  success: boolean;
  lens: string;
  date: string;
  title: string;
  body: string;
  bridge: string;
  misstep: string;
  better_move: string;
  signals: {
    transits: Array<{
      planet: string;
      aspect: string;
      natal_planet: string;
      house: number;
    }>;
    active_houses: number[];
    house_meanings: Array<{
      house: number;
      area: string;
      surface: string;
    }>;
  };
  debug?: any;
}

interface AstroTodayDiagnosisProps {
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
  };
  onReflect?: (title: string, context: string, prompt: string) => void;
}

const AstroTodayDiagnosis: React.FC<AstroTodayDiagnosisProps> = ({
  userId,
  theme,
  onReflect,
}) => {
  const [diagnosis, setDiagnosis] = useState<AstroDiagnosisData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [signalsExpanded, setSignalsExpanded] = useState(false);

  useEffect(() => {
    loadDiagnosis();
  }, [userId]);

  const loadDiagnosis = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await api.get(`/astrology/today-diagnosis/${userId}`);
      setDiagnosis(response.data);
    } catch (err: any) {
      console.error('[AstroTodayDiagnosis] Error loading diagnosis:', err);
      setError(err.message || 'Failed to load diagnosis');
    } finally {
      setLoading(false);
    }
  };

  const handleReflect = () => {
    if (diagnosis && onReflect) {
      const prompt = `Reflecting on: "${diagnosis.title}"\n\n${diagnosis.body}`;
      onReflect(diagnosis.title, 'astro_diagnosis', prompt);
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="small" color={theme.accent} />
        <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
          Loading your sky today...
        </Text>
      </View>
    );
  }

  if (error || !diagnosis) {
    return (
      <View style={styles.errorContainer}>
        <Text style={[styles.errorText, { color: theme.textSecondary }]}>
          {error || 'Could not load diagnosis'}
        </Text>
      </View>
    );
  }

  const signals = diagnosis.signals;

  return (
    <View style={styles.container}>
      {/* ============================================ */}
      {/* DIAGNOSIS SECTION - Primary, always visible */}
      {/* ============================================ */}
      
      {/* Header */}
      <View style={styles.headerSection}>
        <Text style={[styles.headerLabel, { color: theme.textTertiary }]}>TODAY</Text>
        <Text style={[styles.diagnosisTitle, { color: theme.text }]}>
          {diagnosis.title}
        </Text>
      </View>
      
      {/* Body - what's happening internally */}
      <Text style={[styles.diagnosisBody, { color: theme.textSecondary }]}>
        {diagnosis.body}
      </Text>
      
      {/* Bridge - gray callout */}
      <View style={[styles.bridgeContainer, { backgroundColor: theme.surface, borderLeftColor: theme.accent + '40' }]}>
        <Text style={[styles.bridgeText, { color: theme.textTertiary }]}>
          {diagnosis.bridge}
        </Text>
      </View>
      
      {/* Misstep & Better Move Row */}
      <View style={styles.guidanceRow}>
        <View style={styles.guidanceColumn}>
          <Text style={[styles.guidanceLabel, { color: theme.textTertiary }]}>
            LIKELY MISSTEP
          </Text>
          <Text style={[styles.guidanceText, { color: theme.textSecondary }]}>
            {diagnosis.misstep}
          </Text>
        </View>
        <View style={[styles.guidanceColumn, styles.betterMoveColumn]}>
          <Text style={[styles.guidanceLabel, { color: theme.accent }]}>
            BETTER MOVE
          </Text>
          <Text style={[styles.guidanceText, { color: theme.text }]}>
            {diagnosis.better_move}
          </Text>
        </View>
      </View>
      
      {/* Unified Insight Card Footer (Resonate + Reflect) - replaces old Reflect CTA */}
      <InsightCardFooter
        source={{
          lens: 'astrology',
          type: 'astro_today_diagnosis',
          name: diagnosis.title,
          value: diagnosis.body,
          id: `astro_diagnosis_${diagnosis.date}`,
        }}
        patternSignature={`astro_diagnosis_${diagnosis.date}`}
        context="astrology_today"
        prompt={`Reflecting on: "${diagnosis.title}"\n\n${diagnosis.body}`}
        showBorder={true}
        borderColor={theme.border}
      />
      
      {/* ============================================ */}
      {/* SIGNALS SECTION - Collapsible */}
      {/* ============================================ */}
      
      <TouchableOpacity 
        style={[styles.signalsHeader, { borderTopColor: theme.border }]}
        onPress={() => setSignalsExpanded(!signalsExpanded)}
        activeOpacity={0.7}
      >
        <Text style={[styles.signalsHeaderText, { color: theme.textSecondary }]}>
          {signalsExpanded ? '▼' : '▶'} What this is based on
        </Text>
        <Ionicons 
          name={signalsExpanded ? 'chevron-up' : 'chevron-down'} 
          size={20} 
          color={theme.textTertiary} 
        />
      </TouchableOpacity>
      
      {signalsExpanded && signals && (
        <View style={[styles.signalsContent, { backgroundColor: theme.surface }]}>
          
          {/* Active Houses */}
          <View style={styles.signalGroup}>
            <Text style={[styles.signalGroupLabel, { color: theme.textTertiary }]}>
              HOUSES ACTIVATED
            </Text>
            {signals.house_meanings?.map((h, idx) => (
              <View key={idx} style={[styles.houseRow, { borderBottomColor: theme.border }]}>
                <Text style={[styles.houseNumber, { color: theme.text }]}>
                  House {h.house}
                </Text>
                <View style={styles.houseMeaning}>
                  <Text style={[styles.houseArea, { color: theme.accent }]}>
                    {h.area}
                  </Text>
                  <Text style={[styles.houseSurface, { color: theme.textSecondary }]}>
                    {h.surface}
                  </Text>
                </View>
              </View>
            ))}
          </View>
          
          {/* Transits */}
          {signals.transits?.length > 0 && (
            <View style={styles.signalGroup}>
              <Text style={[styles.signalGroupLabel, { color: theme.textTertiary }]}>
                CURRENT TRANSITS
              </Text>
              {signals.transits.slice(0, 3).map((t, idx) => (
                <View key={idx} style={styles.transitRow}>
                  <Text style={[styles.transitText, { color: theme.textSecondary }]}>
                    {t.planet} {t.aspect} {t.natal_planet}
                  </Text>
                  {t.house && (
                    <Text style={[styles.transitHouse, { color: theme.textTertiary }]}>
                      House {t.house}
                    </Text>
                  )}
                </View>
              ))}
            </View>
          )}
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingBottom: 8,
  },
  loadingContainer: {
    padding: 24,
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 8,
    fontSize: 14,
  },
  errorContainer: {
    padding: 16,
  },
  errorText: {
    fontSize: 14,
    textAlign: 'center',
  },
  
  // Header
  headerSection: {
    marginBottom: 16,
  },
  headerLabel: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 6,
  },
  diagnosisTitle: {
    fontSize: 22,
    fontWeight: '600',
    lineHeight: 28,
  },
  
  // Body
  diagnosisBody: {
    fontSize: 16,
    lineHeight: 24,
    marginBottom: 16,
  },
  
  // Bridge
  bridgeContainer: {
    paddingVertical: 12,
    paddingHorizontal: 14,
    borderLeftWidth: 3,
    borderRadius: 4,
    marginBottom: 20,
  },
  bridgeText: {
    fontSize: 14,
    lineHeight: 21,
    fontStyle: 'italic',
  },
  
  // Guidance
  guidanceRow: {
    flexDirection: 'row',
    marginBottom: 20,
    gap: 16,
  },
  guidanceColumn: {
    flex: 1,
  },
  betterMoveColumn: {
    flex: 1,
  },
  guidanceLabel: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  guidanceText: {
    fontSize: 14,
    lineHeight: 20,
  },
  
  // Reflect Button
  reflectButton: {
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderWidth: 1,
    borderRadius: 8,
    alignSelf: 'flex-start',
    marginBottom: 16,
  },
  reflectButtonText: {
    fontSize: 14,
    fontWeight: '500',
  },
  
  // Signals Section
  signalsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 16,
    borderTopWidth: 1,
    marginTop: 8,
  },
  signalsHeaderText: {
    fontSize: 14,
    fontWeight: '500',
  },
  signalsContent: {
    padding: 16,
    borderRadius: 8,
    marginTop: 8,
  },
  
  // Signal Groups
  signalGroup: {
    marginBottom: 20,
  },
  signalGroupLabel: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 10,
  },
  
  // House Row
  houseRow: {
    paddingVertical: 10,
    borderBottomWidth: 1,
  },
  houseNumber: {
    fontSize: 15,
    fontWeight: '500',
    marginBottom: 4,
  },
  houseMeaning: {
    marginLeft: 4,
  },
  houseArea: {
    fontSize: 13,
    fontWeight: '500',
    textTransform: 'capitalize',
  },
  houseSurface: {
    fontSize: 12,
    marginTop: 2,
  },
  
  // Transit Row
  transitRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 6,
  },
  transitText: {
    fontSize: 14,
  },
  transitHouse: {
    fontSize: 12,
  },
});

export default AstroTodayDiagnosis;
