/**
 * Lunar Reflection Signal Card - Task 49
 * 
 * Special card for Human Design Reflectors showing lunar cycle phase
 * and aligned reflective content.
 * 
 * Replaces DailyPatternSignalCard for Reflector users.
 */

import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../contexts/ThemeContext';
import api from '../services/api';
import { InlineReflectButton } from './UniversalReflectButton';

// =============================================================================
// TYPES
// =============================================================================

interface LunarCycleData {
  is_reflector: boolean;
  human_design_type: string | null;
  lunar_day: number;
  moon_phase: string;
  moon_icon: string;
  phase_energy: string;
  days_since_new_moon: number;
  days_until_new_moon: number;
  days_until_full_moon: number;
  cycle_progress: number;
  signal_title?: string;
  reflection_message?: string;
  reflective_question?: string;
  guidance?: string;
  pattern_lens_message?: string;
  strategy?: string;
  // Task 50: Lunar Gate data
  current_moon_gate?: number;
  gate_line?: number;
  gate_formatted?: string;
  gate_title?: string;
  gate_theme?: string;
  center?: string;
  gate_reflection_message?: string;
  gate_reflective_question?: string;
}

interface LunarReflectionSignalCardProps {
  userId: string;
  onReflectorStatus?: (isReflector: boolean) => void;
}

// =============================================================================
// CONSTANTS
// =============================================================================

const DISMISS_KEY_PREFIX = 'lunar_signal_dismissed_';

// Moonlight silver color palette
const LUNAR_COLORS = {
  moonlight: '#C0C8D4',
  silver: '#A8B2C0',
  midnight: '#1A1D24',
  glow: 'rgba(192, 200, 212, 0.15)',
};

// =============================================================================
// COMPONENT
// =============================================================================

export default function LunarReflectionSignalCard({ 
  userId, 
  onReflectorStatus 
}: LunarReflectionSignalCardProps) {
  const { theme } = useTheme();
  const [data, setData] = useState<LunarCycleData | null>(null);
  const [loading, setLoading] = useState(true);
  const [dismissed, setDismissed] = useState(false);
  const [error, setError] = useState(false);

  // Get today's date string for dismiss key
  const getTodayKey = useCallback(() => {
    const today = new Date().toISOString().split('T')[0];
    return `${DISMISS_KEY_PREFIX}${userId}_${today}`;
  }, [userId]);

  // Fetch lunar cycle data
  useEffect(() => {
    const fetchLunarCycle = async () => {
      if (!userId) {
        setLoading(false);
        return;
      }

      try {
        // Check if dismissed for today
        const dismissedValue = await AsyncStorage.getItem(getTodayKey());
        if (dismissedValue === 'true') {
          setDismissed(true);
          setLoading(false);
          return;
        }

        // Fetch lunar cycle data
        const response = await api.get(`/lunar-cycle/${userId}`);
        const lunarData = response.data;
        
        setData(lunarData);
        
        // Notify parent about Reflector status
        if (onReflectorStatus) {
          onReflectorStatus(lunarData.is_reflector);
        }

        console.log('[LunarReflectionSignal] Fetched:', {
          isReflector: lunarData.is_reflector,
          phase: lunarData.moon_phase,
          day: lunarData.lunar_day,
        });

      } catch (err) {
        console.error('[LunarReflectionSignal] Error:', err);
        setError(true);
        if (onReflectorStatus) {
          onReflectorStatus(false);
        }
      } finally {
        setLoading(false);
      }
    };

    fetchLunarCycle();
  }, [userId, getTodayKey, onReflectorStatus]);

  // Handle dismiss
  const handleDismiss = async () => {
    try {
      await AsyncStorage.setItem(getTodayKey(), 'true');
      setDismissed(true);
    } catch (err) {
      console.error('[LunarReflectionSignal] Failed to dismiss:', err);
    }
  };

  // Don't render if:
  // - Not a Reflector
  // - Dismissed
  // - Error
  // - No data
  if (loading) {
    return (
      <View style={[styles.container]}>
        <View style={[styles.loadingContainer, { backgroundColor: LUNAR_COLORS.glow, borderColor: theme.border }]}>
          <ActivityIndicator size="small" color={LUNAR_COLORS.moonlight} />
        </View>
      </View>
    );
  }

  if (dismissed || error || !data || !data.is_reflector) {
    return null;
  }

  // Render cycle progress bar
  const renderCycleProgress = () => {
    const progress = data.cycle_progress * 100;
    return (
      <View style={styles.progressContainer}>
        <View style={[styles.progressTrack, { backgroundColor: `${LUNAR_COLORS.moonlight}20` }]}>
          <View 
            style={[
              styles.progressFill, 
              { 
                width: `${progress}%`,
                backgroundColor: LUNAR_COLORS.moonlight,
              }
            ]} 
          />
          {/* Full moon marker at ~50% */}
          <View style={[styles.fullMoonMarker, { backgroundColor: LUNAR_COLORS.silver }]} />
        </View>
        <View style={styles.progressLabels}>
          <Text style={[styles.progressLabel, { color: theme.textTertiary }]}>New</Text>
          <Text style={[styles.progressLabel, { color: theme.textTertiary }]}>Full</Text>
          <Text style={[styles.progressLabel, { color: theme.textTertiary }]}>New</Text>
        </View>
      </View>
    );
  };

  return (
    <View style={[styles.container]}>
      <View style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        {/* Header - Updated for Task 50 */}
        <View style={styles.header}>
          <View style={styles.titleRow}>
            <Text style={styles.moonIcon}>{data.moon_icon}</Text>
            <Text style={[styles.cardTitle, { color: LUNAR_COLORS.moonlight }]}>
              {data.current_moon_gate ? 'LUNAR GATE OF POSSIBILITY' : 'LUNAR REFLECTION SIGNAL'}
            </Text>
          </View>
          <TouchableOpacity 
            style={styles.dismissButton}
            onPress={handleDismiss}
            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
          >
            <Ionicons name="close" size={18} color={theme.textTertiary} />
          </TouchableOpacity>
        </View>

        {/* Phase Badge */}
        <View style={[styles.phaseBadge, { backgroundColor: LUNAR_COLORS.glow, borderColor: `${LUNAR_COLORS.moonlight}40` }]}>
          <Text style={[styles.phaseBadgeText, { color: LUNAR_COLORS.moonlight }]}>
            {data.moon_phase} • Day {Math.round(data.lunar_day)}
          </Text>
        </View>

        {/* Task 50: Current Lunar Gate Display */}
        {data.current_moon_gate && (
          <View style={styles.gateSection}>
            <View style={styles.gateHeader}>
              <Text style={[styles.gateNumber, { color: LUNAR_COLORS.moonlight }]}>
                Gate {data.gate_formatted}
              </Text>
              <Text style={[styles.gateTitle, { color: theme.text }]}>
                {data.gate_title}
              </Text>
            </View>
            {data.gate_theme && (
              <Text style={[styles.gateTheme, { color: theme.textTertiary }]}>
                {data.gate_theme}
              </Text>
            )}
            {data.center && (
              <Text style={[styles.gateCenter, { color: LUNAR_COLORS.silver }]}>
                {data.center}
              </Text>
            )}
          </View>
        )}

        {/* Cycle Progress */}
        {renderCycleProgress()}

        {/* Main Reflection Message - now gate-based when available */}
        {data.reflection_message && (
          <Text style={[styles.reflectionMessage, { color: theme.text }]}>
            {data.reflection_message}
          </Text>
        )}

        {/* Guidance */}
        {data.guidance && (
          <View style={[styles.guidanceBlock, { borderLeftColor: LUNAR_COLORS.moonlight }]}>
            <Text style={[styles.guidanceText, { color: theme.textSecondary }]}>
              {data.guidance}
            </Text>
          </View>
        )}

        {/* Reflective Question - now gate-based when available */}
        {data.reflective_question && (
          <View style={[styles.questionBlock, { borderTopColor: theme.border }]}>
            <Text style={[styles.questionLabel, { color: LUNAR_COLORS.silver }]}>
              TO NOTICE
            </Text>
            <Text style={[styles.questionText, { color: theme.textSecondary }]}>
              {data.reflective_question}
            </Text>
          </View>
        )}

        {/* Timing Info */}
        <View style={[styles.timingRow, { borderTopColor: theme.border }]}>
          <View style={styles.timingItem}>
            <Text style={[styles.timingValue, { color: LUNAR_COLORS.moonlight }]}>
              {Math.round(data.days_until_new_moon)}d
            </Text>
            <Text style={[styles.timingLabel, { color: theme.textTertiary }]}>to New Moon</Text>
          </View>
          <View style={styles.timingDivider} />
          <View style={styles.timingItem}>
            <Text style={[styles.timingValue, { color: LUNAR_COLORS.moonlight }]}>
              {Math.round(data.days_until_full_moon)}d
            </Text>
            <Text style={[styles.timingLabel, { color: theme.textTertiary }]}>to Full Moon</Text>
          </View>
        </View>

        {/* Reflect Button */}
        {data.reflective_question && (
          <View style={[styles.reflectButtonContainer, { borderTopColor: theme.border }]}>
            <InlineReflectButton
              source={{
                lens: 'human_design',
                type: data.current_moon_gate ? 'lunar_gate' : 'lunar_cycle',
                name: data.current_moon_gate 
                  ? `Gate ${data.gate_formatted} - ${data.gate_title}` 
                  : `${data.moon_phase} Reflection`,
                value: data.reflection_message || '',
                id: `lunar_${new Date().toISOString().split('T')[0]}`,
              }}
              prompt={data.reflective_question}
            />
          </View>
        )}
      </View>
    </View>
  );
}

// =============================================================================
// STYLES
// =============================================================================

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 20,
    paddingTop: 8,
    paddingBottom: 4,
  },
  loadingContainer: {
    borderRadius: 12,
    padding: 24,
    alignItems: 'center',
    borderWidth: 1,
  },
  card: {
    borderRadius: 12,
    paddingVertical: 16,
    paddingHorizontal: 16,
    borderWidth: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  moonIcon: {
    fontSize: 18,
  },
  cardTitle: {
    fontSize: 11,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  dismissButton: {
    padding: 4,
    marginTop: -4,
    marginRight: -4,
    opacity: 0.5,
  },
  phaseBadge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    borderWidth: 1,
    marginBottom: 14,
  },
  phaseBadgeText: {
    fontSize: 13,
    fontWeight: '600',
  },
  // Task 50: Gate Section Styles
  gateSection: {
    marginBottom: 14,
    paddingBottom: 14,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: 'rgba(192, 200, 212, 0.2)',
  },
  gateHeader: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: 10,
    marginBottom: 6,
  },
  gateNumber: {
    fontSize: 14,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  gateTitle: {
    fontSize: 18,
    fontWeight: '600',
    flex: 1,
  },
  gateTheme: {
    fontSize: 13,
    fontStyle: 'italic',
    marginBottom: 4,
  },
  gateCenter: {
    fontSize: 11,
    fontWeight: '500',
    letterSpacing: 0.5,
  },
  progressContainer: {
    marginBottom: 16,
  },
  progressTrack: {
    height: 6,
    borderRadius: 3,
    marginBottom: 6,
    position: 'relative',
  },
  progressFill: {
    height: '100%',
    borderRadius: 3,
  },
  fullMoonMarker: {
    position: 'absolute',
    left: '50%',
    top: -2,
    width: 10,
    height: 10,
    borderRadius: 5,
    marginLeft: -5,
  },
  progressLabels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  progressLabel: {
    fontSize: 10,
    fontWeight: '500',
  },
  reflectionMessage: {
    fontSize: 15,
    lineHeight: 24,
    fontWeight: '400',
    marginBottom: 12,
  },
  guidanceBlock: {
    paddingLeft: 12,
    borderLeftWidth: 2,
    marginBottom: 14,
    marginTop: 2,
  },
  guidanceText: {
    fontSize: 14,
    lineHeight: 21,
    fontStyle: 'italic',
  },
  questionBlock: {
    paddingTop: 14,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  questionLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 6,
  },
  questionText: {
    fontSize: 14,
    lineHeight: 21,
    fontWeight: '400',
  },
  timingRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 14,
    marginTop: 14,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  timingItem: {
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  timingValue: {
    fontSize: 18,
    fontWeight: '600',
  },
  timingLabel: {
    fontSize: 11,
    marginTop: 2,
  },
  timingDivider: {
    width: 1,
    height: 30,
    backgroundColor: 'rgba(192, 200, 212, 0.2)',
  },
  reflectButtonContainer: {
    marginTop: 14,
    paddingTop: 14,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
});

// =============================================================================
// EXPORT API TYPE
// =============================================================================

export type { LunarCycleData };
