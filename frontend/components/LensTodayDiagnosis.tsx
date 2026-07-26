/**
 * LensTodayDiagnosis - Diagnosis-first Today component for HD and Astrology
 * 
 * Follows Home diagnosis standard:
 * 1. Diagnosis (primary, always visible)
 * 2. Signals (collapsible, secondary)
 * 
 * V1: Initial implementation with collapsible signals
 */

import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../services/api';
import { InsightCardFooter } from './InsightCardFooter';

interface LensDiagnosisData {
  success: boolean;
  lens: 'human_design' | 'astrology';
  date: string;
  title: string;
  body: string;
  bridge: string;
  misstep: string;
  better_move: string;
  signals: HDSignals | AstroSignals;
  debug?: any;
}

interface HDSignals {
  active_gates: Array<{
    gate: number;
    shadow: string;
    gift: string;
    center: string;
    activation: string;
  }>;
  defined_centers: string[];
  undefined_centers: string[];
  type: string;
  authority: string;
}

interface AstroSignals {
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
  }>;
}

interface LensTodayDiagnosisProps {
  userId: string;
  lens: 'human_design' | 'astrology';
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
  onReflect?: (context: string, prompt: string) => void;
}

export const LensTodayDiagnosis: React.FC<LensTodayDiagnosisProps> = ({
  userId,
  lens,
  theme,
  onReflect,
}) => {
  const [diagnosis, setDiagnosis] = useState<LensDiagnosisData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [signalsExpanded, setSignalsExpanded] = useState(false);

  useEffect(() => {
    loadDiagnosis();
  }, [userId, lens]);

  const loadDiagnosis = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const endpoint = lens === 'human_design' 
        ? `/human-design/today-diagnosis/${userId}`
        : `/astrology/today-diagnosis/${userId}`;
      
      const response = await api.get(endpoint);
      setDiagnosis(response.data);
    } catch (err: any) {
      console.error(`[LensTodayDiagnosis] Error loading ${lens} diagnosis:`, err);
      setError(err.message || 'Failed to load diagnosis');
    } finally {
      setLoading(false);
    }
  };

  const handleReflect = () => {
    if (diagnosis && onReflect) {
      const prompt = `Reflecting on: "${diagnosis.title}"\n\n${diagnosis.body}`;
      onReflect(diagnosis.title, prompt);
    }
  };

  if (loading) {
    return (
      <View style={[styles.container, { backgroundColor: theme.background }]}>
        <ActivityIndicator size="large" color={theme.accent} />
        <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
          Loading diagnosis...
        </Text>
      </View>
    );
  }

  if (error || !diagnosis) {
    return (
      <View style={[styles.container, { backgroundColor: theme.background }]}>
        <Text style={[styles.errorText, { color: theme.textSecondary }]}>
          {error || 'Could not load diagnosis'}
        </Text>
        <TouchableOpacity style={[styles.retryButton, { borderColor: theme.accent }]} onPress={loadDiagnosis}>
          <Text style={[styles.retryText, { color: theme.accent }]}>Try Again</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const isHD = lens === 'human_design';
  const hdSignals = isHD ? diagnosis.signals as HDSignals : null;
  const astroSignals = !isHD ? diagnosis.signals as AstroSignals : null;

  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}>
      {/* ============================================ */}
      {/* DIAGNOSIS SECTION - Primary, always visible */}
      {/* ============================================ */}
      
      {/* Title - tension-based */}
      <View style={styles.diagnosisSection}>
        <Text style={[styles.diagnosisTitle, { color: theme.text }]}>
          {diagnosis.title}
        </Text>
        
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
        
        {/* Likely Misstep */}
        <View style={styles.misstepSection}>
          <Text style={[styles.misstepLabel, { color: theme.textTertiary }]}>
            LIKELY MISSTEP
          </Text>
          <Text style={[styles.misstepText, { color: theme.textSecondary }]}>
            {diagnosis.misstep}
          </Text>
        </View>
        
        {/* Better Move */}
        <View style={styles.betterMoveSection}>
          <Text style={[styles.betterMoveLabel, { color: theme.accent }]}>
            BETTER MOVE
          </Text>
          <Text style={[styles.betterMoveText, { color: theme.text }]}>
            {diagnosis.better_move}
          </Text>
        </View>
        
        {/* Unified Insight Card Footer (Resonate + Reflect) - replaces old Reflect CTA */}
        <InsightCardFooter
          source={{
            lens: lens,
            type: `${lens}_today_diagnosis`,
            name: diagnosis.title,
            value: diagnosis.body,
            id: `${lens}_diagnosis_${diagnosis.date}`,
          }}
          patternSignature={`${lens}_diagnosis_${diagnosis.date}`}
          context={`${lens}_today`}
          prompt={`Reflecting on: "${diagnosis.title}"\n\n${diagnosis.body}`}
          showBorder={true}
          borderColor={theme.border}
        />
      </View>
      
      {/* ============================================ */}
      {/* SIGNALS SECTION - Collapsible */}
      {/* ============================================ */}
      
      <TouchableOpacity 
        style={[styles.signalsHeader, { borderTopColor: theme.border }]}
        onPress={() => setSignalsExpanded(!signalsExpanded)}
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
      
      {signalsExpanded && (
        <View style={[styles.signalsContent, { backgroundColor: theme.surface }]}>
          
          {/* HD SIGNALS */}
          {isHD && hdSignals && (
            <>
              {/* Active Gates with Gene Keys */}
              <View style={styles.signalGroup}>
                <Text style={[styles.signalGroupLabel, { color: theme.textTertiary }]}>
                  ACTIVE GATES (Gene Keys)
                </Text>
                {hdSignals.active_gates.slice(0, 5).map((gate, idx) => (
                  <View key={idx} style={[styles.gateRow, { borderBottomColor: theme.border }]}>
                    <View style={styles.gateInfo}>
                      <Text style={[styles.gateNumber, { color: theme.text }]}>
                        Gate {gate.gate}
                      </Text>
                      <Text style={[styles.gateCenter, { color: theme.textTertiary }]}>
                        {gate.center} Center
                      </Text>
                    </View>
                    <View style={styles.geneKeyInfo}>
                      <Text style={[styles.shadowText, { color: theme.textSecondary }]}>
                        Shadow: {gate.shadow}
                      </Text>
                      <Text style={[styles.giftText, { color: theme.accent }]}>
                        Gift: {gate.gift}
                      </Text>
                    </View>
                  </View>
                ))}
              </View>
              
              {/* Type & Authority */}
              <View style={styles.signalGroup}>
                <Text style={[styles.signalGroupLabel, { color: theme.textTertiary }]}>
                  YOUR DESIGN
                </Text>
                <Text style={[styles.signalText, { color: theme.textSecondary }]}>
                  Type: {hdSignals.type}
                </Text>
                <Text style={[styles.signalText, { color: theme.textSecondary }]}>
                  Authority: {hdSignals.authority}
                </Text>
              </View>
              
              {/* Centers */}
              {hdSignals.defined_centers.length > 0 && (
                <View style={styles.signalGroup}>
                  <Text style={[styles.signalGroupLabel, { color: theme.textTertiary }]}>
                    CENTERS ACTIVATED
                  </Text>
                  <Text style={[styles.signalText, { color: theme.textSecondary }]}>
                    Defined: {hdSignals.defined_centers.join(', ')}
                  </Text>
                </View>
              )}
            </>
          )}
          
          {/* ASTRO SIGNALS */}
          {!isHD && astroSignals && (
            <>
              {/* Active Houses */}
              <View style={styles.signalGroup}>
                <Text style={[styles.signalGroupLabel, { color: theme.textTertiary }]}>
                  HOUSES ACTIVATED
                </Text>
                {astroSignals.house_meanings?.map((h, idx) => (
                  <View key={idx} style={styles.houseRow}>
                    <Text style={[styles.houseNumber, { color: theme.text }]}>
                      House {h.house}
                    </Text>
                    <Text style={[styles.houseArea, { color: theme.textSecondary }]}>
                      {h.area}
                    </Text>
                  </View>
                ))}
              </View>
              
              {/* Transits */}
              {astroSignals.transits?.length > 0 && (
                <View style={styles.signalGroup}>
                  <Text style={[styles.signalGroupLabel, { color: theme.textTertiary }]}>
                    CURRENT TRANSITS
                  </Text>
                  {astroSignals.transits.slice(0, 3).map((t, idx) => (
                    <Text key={idx} style={[styles.signalText, { color: theme.textSecondary }]}>
                      {t.planet} {t.aspect} {t.natal_planet}
                    </Text>
                  ))}
                </View>
              )}
            </>
          )}
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    textAlign: 'center',
  },
  errorText: {
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 16,
  },
  retryButton: {
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderWidth: 1,
    borderRadius: 8,
    alignSelf: 'center',
  },
  retryText: {
    fontSize: 16,
    fontWeight: '500',
  },
  
  // Diagnosis Section
  diagnosisSection: {
    marginBottom: 24,
  },
  diagnosisTitle: {
    fontSize: 22,
    fontWeight: '500',
    marginBottom: 16,
    lineHeight: 28,
  },
  diagnosisBody: {
    fontSize: 16,
    lineHeight: 28,
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
    fontSize: 16,
    lineHeight: 26,
    fontStyle: 'italic',
  },
  
  // Misstep
  misstepSection: {
    marginBottom: 16,
  },
  misstepLabel: {
    fontSize: 14,
    fontWeight: '500',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  misstepText: {
    fontSize: 17,
    lineHeight: 26,
  },
  
  // Better Move
  betterMoveSection: {
    marginBottom: 20,
  },
  betterMoveLabel: {
    fontSize: 14,
    fontWeight: '500',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  betterMoveText: {
    fontSize: 17,
    lineHeight: 26,
    fontWeight: '500',
  },
  
  // Reflect Button
  reflectButton: {
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderWidth: 1,
    borderRadius: 8,
    alignSelf: 'flex-start',
  },
  reflectButtonText: {
    fontSize: 16,
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
    fontSize: 16,
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
    fontSize: 14,
    fontWeight: '500',
    letterSpacing: 0.5,
    marginBottom: 14,
  },
  signalText: {
    fontSize: 16,
    lineHeight: 28,
    marginBottom: 4,
  },
  
  // Gate Row (HD)
  gateRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 10,
    borderBottomWidth: 1,
  },
  gateInfo: {
    flex: 1,
  },
  gateNumber: {
    fontSize: 17,
    fontWeight: '500',
  },
  gateCenter: {
    fontSize: 14,
    marginTop: 2,
  },
  geneKeyInfo: {
    flex: 1,
    alignItems: 'flex-end',
  },
  shadowText: {
    fontSize: 16,
  },
  giftText: {
    fontSize: 16,
    fontWeight: '500',
    marginTop: 2,
  },
  
  // House Row (Astro)
  houseRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 6,
  },
  houseNumber: {
    fontSize: 16,
    fontWeight: '500',
  },
  houseArea: {
    fontSize: 16,
  },
});

export default LensTodayDiagnosis;
