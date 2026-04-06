/**
 * HDTodayDiagnosis - Human Design Today Diagnosis Component
 * 
 * Follows Home diagnosis standard:
 * 1. Diagnosis Title (tension-based, using Gene Key shadow/gift)
 * 2. Diagnosis Body (what's happening, where tension is, why now)
 * 3. Bridge (normalize experience)
 * 4. Misstep (what user will do wrong)
 * 5. Better Move (grounded action)
 * 6. Signals (collapsible: gates, Gene Keys, centers)
 * 
 * V1: Initial implementation with Gene Key integration
 */

import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import api from '../services/api';
import { InsightCardFooter } from './InsightCardFooter';

interface HDDiagnosisData {
  success: boolean;
  lens: string;
  date: string;
  title: string;
  body: string;
  bridge: string;
  misstep: string;
  better_move: string;
  signals: {
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
  };
  debug?: any;
}

interface HDTodayDiagnosisProps {
  userId: string;
  hdType: string;
  authority: string;
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
  onReflect?: (title: string, context: string, prompt: string, tab: string, source: string, hdType: string) => void;
}

const HDTodayDiagnosis: React.FC<HDTodayDiagnosisProps> = ({
  userId,
  hdType,
  authority,
  theme,
  onReflect,
}) => {
  const [diagnosis, setDiagnosis] = useState<HDDiagnosisData | null>(null);
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
      
      const response = await api.get(`/human-design/today-diagnosis/${userId}`);
      setDiagnosis(response.data);
    } catch (err: any) {
      console.error('[HDTodayDiagnosis] Error loading diagnosis:', err);
      setError(err.message || 'Failed to load diagnosis');
    } finally {
      setLoading(false);
    }
  };

  const handleReflect = () => {
    if (diagnosis && onReflect) {
      const prompt = `Reflecting on: "${diagnosis.title}"\n\n${diagnosis.body}`;
      onReflect(diagnosis.title, 'hd_diagnosis', prompt, 'today', 'diagnosis', hdType);
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="small" color={theme.accent} />
        <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
          Loading your design today...
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
          lens: 'human_design',
          type: 'hd_today_diagnosis',
          name: diagnosis.title,
          value: diagnosis.body,
          id: `hd_diagnosis_${diagnosis.date}`,
        }}
        patternSignature={`hd_diagnosis_${diagnosis.date}_${hdType}`}
        context="human_design_today"
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
          size={18} 
          color={theme.textTertiary} 
        />
      </TouchableOpacity>
      
      {signalsExpanded && signals && (
        <View style={[styles.signalsContent, { backgroundColor: theme.surface }]}>
          
          {/* Active Gates with Gene Keys */}
          <View style={styles.signalGroup}>
            <Text style={[styles.signalGroupLabel, { color: theme.textTertiary }]}>
              ACTIVE GATES (Gene Keys)
            </Text>
            {signals.active_gates?.slice(0, 5).map((gate, idx) => (
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
            <View style={styles.designRow}>
              <Text style={[styles.designLabel, { color: theme.textTertiary }]}>Type:</Text>
              <Text style={[styles.designValue, { color: theme.text }]}>{signals.type}</Text>
            </View>
            <View style={styles.designRow}>
              <Text style={[styles.designLabel, { color: theme.textTertiary }]}>Authority:</Text>
              <Text style={[styles.designValue, { color: theme.text }]}>{signals.authority}</Text>
            </View>
          </View>
          
          {/* Centers */}
          {signals.defined_centers?.length > 0 && (
            <View style={styles.signalGroup}>
              <Text style={[styles.signalGroupLabel, { color: theme.textTertiary }]}>
                DEFINED CENTERS
              </Text>
              <Text style={[styles.centersText, { color: theme.textSecondary }]}>
                {signals.defined_centers.join(' • ')}
              </Text>
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
  
  // Gate Row
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
    fontSize: 15,
    fontWeight: '500',
  },
  gateCenter: {
    fontSize: 12,
    marginTop: 2,
  },
  geneKeyInfo: {
    flex: 1,
    alignItems: 'flex-end',
  },
  shadowText: {
    fontSize: 13,
  },
  giftText: {
    fontSize: 13,
    fontWeight: '500',
    marginTop: 2,
  },
  
  // Design Row
  designRow: {
    flexDirection: 'row',
    marginBottom: 6,
  },
  designLabel: {
    fontSize: 13,
    width: 70,
  },
  designValue: {
    fontSize: 13,
    fontWeight: '500',
  },
  
  // Centers
  centersText: {
    fontSize: 13,
    lineHeight: 20,
  },
});

export default HDTodayDiagnosis;
