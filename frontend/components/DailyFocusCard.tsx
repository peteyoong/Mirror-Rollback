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
import { Colors } from '../constants/colors';
import { getDailyFocus, DailyFocusResponse } from '../services/api';

interface DailyFocusCardProps {
  userId: string;
  onStateChange?: (state: DailyFocusState) => void;
}

export interface DailyFocusState {
  isLoading: boolean;
  isDismissed: boolean;
  hasContext: boolean;
  context: string | null;
  ambientLine: string | null;
}

const DISMISS_KEY_PREFIX = 'daily_focus_dismissed_';

/**
 * Daily Focus Card - Context Selector Layer UI
 * 
 * Surfaces daily context with the Mirror philosophy:
 * - Non-prescriptive
 * - Dismissible (until next day)
 * - Optional
 * - No guilt copy
 */
export default function DailyFocusCard({ userId, onStateChange }: DailyFocusCardProps) {
  const [dailyFocus, setDailyFocus] = useState<DailyFocusResponse | null>(null);
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
    focus: DailyFocusResponse | null
  ) => {
    if (onStateChange) {
      onStateChange({
        isLoading,
        isDismissed,
        hasContext: !!focus?.context,
        context: focus?.context || null,
        ambientLine: focus?.ambient_line || null,
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
        
        // Fetch daily focus
        const focus = await getDailyFocus(userId);
        setDailyFocus(focus);
        notifyStateChange(false, false, focus);
      } catch (err) {
        console.error('Failed to fetch daily focus:', err);
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
      notifyStateChange(false, true, dailyFocus);
    } catch (err) {
      console.error('Failed to dismiss daily focus:', err);
    }
  };

  // Don't render if dismissed
  if (dismissed) {
    return null;
  }

  if (loading) {
    return (
      <View style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="small" color={Colors.textTertiary} />
        </View>
      </View>
    );
  }

  // If error, show ambient line only with fallback
  if (error || !dailyFocus) {
    return (
      <View style={styles.container}>
        <View style={styles.card}>
          <View style={styles.header}>
            <Text style={styles.cardTitle}>Today's Mirror</Text>
            <TouchableOpacity 
              style={styles.dismissButton}
              onPress={handleDismiss}
              hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
            >
              <Ionicons name="close" size={18} color={Colors.textTertiary} />
            </TouchableOpacity>
          </View>
          <Text style={styles.ambientLine}>
            Something to notice today: where your attention naturally rests.
          </Text>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.card}>
        {/* Header with dismiss */}
        <View style={styles.header}>
          <Text style={styles.cardTitle}>Today's Mirror</Text>
          <TouchableOpacity 
            style={styles.dismissButton}
            onPress={handleDismiss}
            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
          >
            <Ionicons name="close" size={18} color={Colors.textTertiary} />
          </TouchableOpacity>
        </View>
        
        {/* Ambient Line - Always shown */}
        <Text style={styles.ambientLine}>
          {dailyFocus.ambient_line}
        </Text>
        
        {/* Context Block - Only if context exists */}
        {dailyFocus.context && (
          <View style={styles.contextBlock}>
            <Text style={styles.contextLine}>
              Today's mirror may relate more to {dailyFocus.context}.
            </Text>
            <Text style={styles.contextDismiss}>
              Or it may not — see if this fits.
            </Text>
          </View>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 16,
    paddingTop: 8,
    paddingBottom: 8,
  },
  loadingContainer: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 24,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  card: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  cardTitle: {
    fontSize: 13,
    fontWeight: '500',
    color: Colors.textTertiary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  dismissButton: {
    padding: 2,
  },
  ambientLine: {
    fontSize: 16,
    color: Colors.textSecondary,
    lineHeight: 24,
    fontWeight: '400',
  },
  contextBlock: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  contextLine: {
    fontSize: 15,
    color: Colors.text,
    lineHeight: 22,
    fontWeight: '400',
  },
  contextDismiss: {
    fontSize: 14,
    color: Colors.textTertiary,
    marginTop: 6,
    fontStyle: 'italic',
  },
});
