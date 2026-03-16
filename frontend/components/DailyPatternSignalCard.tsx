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
import { getDailyPatternSignal, DailyPatternSignalResponse } from '../services/api';
import { InlineReflectButton } from './UniversalReflectButton';

interface DailyPatternSignalCardProps {
  userId: string;
  onStateChange?: (state: DailyPatternSignalState) => void;
}

export interface DailyPatternSignalState {
  isLoading: boolean;
  isDismissed: boolean;
  hasSignal: boolean;
  patternType: string | null;
  patternName: string | null;
}

const DISMISS_KEY_PREFIX = 'daily_pattern_signal_dismissed_';

/**
 * Daily Pattern Signal Card - Task 43
 * 
 * Shows users a daily insight about where they might be
 * within one of their recurring life patterns.
 * 
 * Uses observational, non-deterministic language:
 * - "may", "appears", "seems"
 * - Never predicts or prescribes
 * - Always ends with a reflective question
 */
export default function DailyPatternSignalCard({ userId, onStateChange }: DailyPatternSignalCardProps) {
  const { theme } = useTheme();
  const [signal, setSignal] = useState<DailyPatternSignalResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [dismissed, setDismissed] = useState(false);
  const [error, setError] = useState(false);

  // Get today's date string for dismiss key
  const getTodayKey = useCallback(() => {
    const today = new Date().toISOString().split('T')[0];
    return `${DISMISS_KEY_PREFIX}${userId}_${today}`;
  }, [userId]);

  // Notify parent of state changes
  const notifyStateChange = useCallback((
    isLoading: boolean,
    isDismissed: boolean,
    signalData: DailyPatternSignalResponse | null
  ) => {
    if (onStateChange) {
      onStateChange({
        isLoading,
        isDismissed,
        hasSignal: !!signalData?.insight_text,
        patternType: signalData?.pattern_type || null,
        patternName: signalData?.pattern_name || null,
      });
    }
  }, [onStateChange]);

  useEffect(() => {
    const checkDismissedAndFetch = async () => {
      try {
        // Check if dismissed for today
        const dismissedValue = await AsyncStorage.getItem(getTodayKey());
        if (dismissedValue === 'true') {
          setDismissed(true);
          setLoading(false);
          notifyStateChange(false, true, null);
          return;
        }
        
        // Fetch daily pattern signal
        const signalResponse = await getDailyPatternSignal(userId);
        setSignal(signalResponse);
        notifyStateChange(false, false, signalResponse);
      } catch (err) {
        console.error('Failed to fetch daily pattern signal:', err);
        setError(true);
        notifyStateChange(false, false, null);
      } finally {
        setLoading(false);
      }
    };
    
    if (userId) {
      checkDismissedAndFetch();
    }
  }, [userId, getTodayKey, notifyStateChange]);

  const handleDismiss = async () => {
    try {
      await AsyncStorage.setItem(getTodayKey(), 'true');
      setDismissed(true);
      notifyStateChange(false, true, signal);
    } catch (err) {
      console.error('Failed to dismiss daily pattern signal:', err);
    }
  };

  // Don't render if dismissed
  if (dismissed) {
    return null;
  }

  if (loading) {
    return (
      <View style={[styles.container]}>
        <View style={[styles.loadingContainer, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <ActivityIndicator size="small" color={theme.textTertiary} />
        </View>
      </View>
    );
  }

  // If error or no signal, show minimal fallback
  if (error || !signal) {
    return null;
  }

  // Get pattern type icon
  const getPatternIcon = (type: string | null): string => {
    switch (type) {
      case 'arc': return '◯';
      case 'cycle': return '↻';
      case 'phase': return '◐';
      case 'tension': return '⟷';
      default: return '◈';
    }
  };

  return (
    <View style={[styles.container]}>
      <View style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        {/* Header with pattern indicator */}
        <View style={styles.header}>
          <View style={styles.titleRow}>
            <Text style={[styles.patternIcon, { color: theme.accent }]}>
              {getPatternIcon(signal.pattern_type)}
            </Text>
            <Text style={[styles.cardTitle, { color: theme.textTertiary }]}>
              {signal.signal_title}
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
        
        {/* Pattern Name Badge (if available) */}
        {signal.pattern_name && (
          <View style={[styles.patternBadge, { backgroundColor: `${theme.accent}15`, borderColor: `${theme.accent}30` }]}>
            <Text style={[styles.patternBadgeText, { color: theme.accent }]}>
              {signal.pattern_name}
            </Text>
          </View>
        )}
        
        {/* Main Insight Text */}
        <Text style={[styles.insightText, { color: theme.text }]}>
          {signal.insight_text}
        </Text>
        
        {/* Past Reflection (if available) */}
        {signal.past_reflection && (
          <View style={[styles.pastReflectionBlock, { borderLeftColor: theme.accent }]}>
            <Text style={[styles.pastReflectionText, { color: theme.textSecondary }]}>
              {signal.past_reflection}
            </Text>
          </View>
        )}
        
        {/* Reflective Question */}
        <View style={[styles.questionBlock, { borderTopColor: theme.border }]}>
          <Text style={[styles.questionLabel, { color: theme.textTertiary }]}>
            TO NOTICE
          </Text>
          <Text style={[styles.questionText, { color: theme.textSecondary }]}>
            {signal.reflective_question}
          </Text>
        </View>

        {/* Reflect Button */}
        <View style={[styles.reflectButtonContainer, { borderTopColor: theme.border }]}>
          <InlineReflectButton
            source={{
              lens: 'patterns',
              type: 'daily_pattern_signal',
              name: signal.pattern_name || 'Daily Pattern Signal',
              value: signal.insight_text,
              id: `pattern_signal_${new Date().toISOString().split('T')[0]}`,
            }}
            prompt={signal.reflective_question}
          />
        </View>
      </View>
    </View>
  );
}

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
  patternIcon: {
    fontSize: 16,
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
  patternBadge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    borderWidth: 1,
    marginBottom: 12,
  },
  patternBadgeText: {
    fontSize: 12,
    fontWeight: '500',
  },
  insightText: {
    fontSize: 15,
    lineHeight: 24,
    fontWeight: '400',
    marginBottom: 12,
  },
  pastReflectionBlock: {
    paddingLeft: 12,
    borderLeftWidth: 2,
    marginBottom: 14,
    marginTop: 2,
  },
  pastReflectionText: {
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
  reflectButtonContainer: {
    marginTop: 14,
    paddingTop: 14,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
});
