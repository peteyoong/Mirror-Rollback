/**
 * Lunar Decision Journal Card - Task 51
 * 
 * Shows lunar journal info at the top of the Journal screen for Reflectors.
 * Displays current lunar day, phase, gate, and active consideration.
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  LayoutAnimation,
  Platform,
  UIManager,
} from 'react-native';
import { useTheme } from '../../contexts/ThemeContext';
import api from '../../services/api';

// Enable LayoutAnimation on Android
if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

// =============================================================================
// TYPES
// =============================================================================

interface LunarJournalStatus {
  success: boolean;
  is_reflector: boolean;
  lunar_day: number;
  moon_phase: string;
  moon_icon: string;
  cycle_progress: number;
  days_until_new_moon: number;
  current_gate: number | null;
  gate_formatted: string | null;
  gate_title: string | null;
  gate_theme: string | null;
  center: string | null;
  gate_reflection: string | null;
  active_consideration: {
    id: string;
    topic: string;
    created_at: string;
    cycle_start: string;
  } | null;
  has_active_consideration: boolean;
  recent_entries: any[];
  entry_count: number;
  daily_prompt: string;
  cycle_completion_prompts: string[] | null;
  show_cycle_completion: boolean;
  cycle_start: string;
  cycle_end: string;
  is_near_new_moon: boolean;
}

interface LunarDecisionJournalCardProps {
  userId: string;
  onStatusLoaded?: (status: LunarJournalStatus | null) => void;
  onConsiderationCreated?: () => void;
}

// =============================================================================
// CONSTANTS
// =============================================================================

const LUNAR_COLORS = {
  moonlight: '#C0C8D4',
  silver: '#A8B2C0',
  glow: 'rgba(192, 200, 212, 0.12)',
};

// =============================================================================
// COMPONENT
// =============================================================================

export default function LunarDecisionJournalCard({
  userId,
  onStatusLoaded,
  onConsiderationCreated,
}: LunarDecisionJournalCardProps) {
  const { theme } = useTheme();
  const [status, setStatus] = useState<LunarJournalStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Consideration input state
  const [showInput, setShowInput] = useState(false);
  const [considerationInput, setConsiderationInput] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Fetch lunar journal status
  // Task 60: Use ref for onStatusLoaded to prevent dependency loop
  const onStatusLoadedRef = useRef(onStatusLoaded);
  onStatusLoadedRef.current = onStatusLoaded;
  
  const fetchStatus = useCallback(async () => {
    if (!userId) return;
    
    try {
      setLoading(true);
      const response = await api.get(`/lunar-journal/${userId}/status`);
      
      if (response.data?.success) {
        setStatus(response.data);
        // Use ref to avoid re-triggering effect when callback changes
        onStatusLoadedRef.current?.(response.data);
      } else if (response.data?.is_reflector === false) {
        setStatus(null);
        onStatusLoadedRef.current?.(null);
      }
      
      setError(null);
    } catch (err) {
      console.error('[LunarJournalCard] Error:', err);
      setError('Unable to load lunar journal');
      setStatus(null);
      onStatusLoadedRef.current?.(null);
    } finally {
      setLoading(false);
    }
  }, [userId]); // Task 60: Removed onStatusLoaded from dependencies

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  // Create consideration
  const handleCreateConsideration = async () => {
    if (!considerationInput.trim() || isSubmitting) return;
    
    try {
      setIsSubmitting(true);
      await api.post(`/lunar-journal/${userId}/consideration`, {
        topic: considerationInput.trim(),
      });
      
      // Refresh status
      await fetchStatus();
      
      // Reset input
      setConsiderationInput('');
      setShowInput(false);
      onConsiderationCreated?.();
      
      if (Platform.OS !== 'web') {
        LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
      }
    } catch (err: any) {
      console.error('[LunarJournalCard] Create error:', err);
      setError(err.response?.data?.detail || 'Unable to create consideration');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Toggle input visibility
  const toggleInput = () => {
    if (Platform.OS !== 'web') {
      LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    }
    setShowInput(!showInput);
  };

  // Render nothing for non-Reflectors or when loading
  if (loading) {
    return (
      <View style={[styles.container, { backgroundColor: LUNAR_COLORS.glow }]}>
        <ActivityIndicator size="small" color={LUNAR_COLORS.moonlight} />
      </View>
    );
  }

  if (!status || !status.is_reflector) {
    return null;
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.moonIcon}>{status.moon_icon}</Text>
        <Text style={[styles.title, { color: LUNAR_COLORS.moonlight }]}>
          LUNAR DECISION JOURNAL
        </Text>
      </View>

      {/* Lunar Day & Phase */}
      <View style={styles.lunarInfo}>
        <Text style={[styles.lunarDay, { color: theme.text }]}>
          Day {Math.round(status.lunar_day)} of 29.5
        </Text>
        <View style={[styles.phaseBadge, { backgroundColor: LUNAR_COLORS.glow }]}>
          <Text style={[styles.phaseBadgeText, { color: LUNAR_COLORS.moonlight }]}>
            {status.moon_phase}
          </Text>
        </View>
      </View>

      {/* Current Gate */}
      {status.current_gate && (
        <View style={[styles.gateSection, { borderTopColor: theme.border }]}>
          <View style={styles.gateHeader}>
            <Text style={[styles.gateNumber, { color: LUNAR_COLORS.moonlight }]}>
              Gate {status.gate_formatted}
            </Text>
            <Text style={[styles.gateTitle, { color: theme.text }]}>
              {status.gate_title}
            </Text>
          </View>
          {status.gate_theme && (
            <Text style={[styles.gateTheme, { color: theme.textTertiary }]}>
              {status.gate_theme}
            </Text>
          )}
          {status.center && (
            <Text style={[styles.gateCenter, { color: LUNAR_COLORS.silver }]}>
              {status.center}
            </Text>
          )}
        </View>
      )}

      {/* Active Consideration */}
      {status.has_active_consideration && status.active_consideration ? (
        <View style={[styles.considerationSection, { borderTopColor: theme.border }]}>
          <Text style={[styles.considerationLabel, { color: LUNAR_COLORS.silver }]}>
            CURRENT CONSIDERATION
          </Text>
          <Text style={[styles.considerationTopic, { color: theme.text }]}>
            "{status.active_consideration.topic}"
          </Text>
          {status.entry_count > 0 && (
            <Text style={[styles.entryCount, { color: theme.textTertiary }]}>
              {status.entry_count} {status.entry_count === 1 ? 'entry' : 'entries'} this cycle
            </Text>
          )}
        </View>
      ) : (
        <View style={[styles.considerationSection, { borderTopColor: theme.border }]}>
          {!showInput ? (
            <>
              <Text style={[styles.noConsiderationText, { color: theme.textSecondary }]}>
                What important decision are you currently thinking about?
              </Text>
              <TouchableOpacity
                style={[styles.addButton, { borderColor: LUNAR_COLORS.moonlight }]}
                onPress={toggleInput}
                activeOpacity={0.7}
              >
                <Text style={[styles.addButtonText, { color: LUNAR_COLORS.moonlight }]}>
                  + Add Consideration
                </Text>
              </TouchableOpacity>
            </>
          ) : (
            <View style={styles.inputSection}>
              <Text style={[styles.inputLabel, { color: LUNAR_COLORS.silver }]}>
                WHAT ARE YOU CURRENTLY CONSIDERING?
              </Text>
              <TextInput
                style={[
                  styles.input,
                  { 
                    backgroundColor: theme.background, 
                    color: theme.text,
                    borderColor: theme.border,
                  }
                ]}
                placeholder="e.g., Should I move to Singapore?"
                placeholderTextColor={theme.textTertiary}
                value={considerationInput}
                onChangeText={setConsiderationInput}
                multiline
                numberOfLines={2}
                autoFocus
              />
              <View style={styles.inputActions}>
                <TouchableOpacity
                  style={styles.cancelButton}
                  onPress={toggleInput}
                >
                  <Text style={[styles.cancelButtonText, { color: theme.textSecondary }]}>
                    Cancel
                  </Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[
                    styles.saveButton,
                    { backgroundColor: LUNAR_COLORS.moonlight },
                    !considerationInput.trim() && styles.saveButtonDisabled,
                  ]}
                  onPress={handleCreateConsideration}
                  disabled={!considerationInput.trim() || isSubmitting}
                >
                  {isSubmitting ? (
                    <ActivityIndicator size="small" color="#1A1D24" />
                  ) : (
                    <Text style={styles.saveButtonText}>
                      Begin Observing
                    </Text>
                  )}
                </TouchableOpacity>
              </View>
            </View>
          )}
        </View>
      )}

      {/* Near New Moon Warning */}
      {status.is_near_new_moon && status.has_active_consideration && (
        <View style={[styles.newMoonWarning, { backgroundColor: 'rgba(192, 200, 212, 0.08)' }]}>
          <Text style={[styles.newMoonText, { color: LUNAR_COLORS.silver }]}>
            {status.days_until_new_moon < 1 
              ? "This lunar cycle appears to be completing."
              : `${Math.round(status.days_until_new_moon)} days until new cycle`
            }
          </Text>
        </View>
      )}

      {/* Error display */}
      {error && (
        <Text style={[styles.errorText, { color: theme.error }]}>
          {error}
        </Text>
      )}
    </View>
  );
}

// =============================================================================
// STYLES
// =============================================================================

const styles = StyleSheet.create({
  container: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 16,
    padding: 16,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  moonIcon: {
    fontSize: 22,
  },
  title: {
    fontSize: 11,
    fontWeight: '500',
    letterSpacing: 1,
    textTransform: 'uppercase',
  },
  lunarInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  lunarDay: {
    fontSize: 22,
    fontWeight: '500',
  },
  phaseBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  phaseBadgeText: {
    fontSize: 12,
    fontWeight: '500',
  },
  gateSection: {
    paddingTop: 12,
    marginTop: 4,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  gateHeader: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: 10,
    marginBottom: 4,
  },
  gateNumber: {
    fontSize: 14,
    fontWeight: '500',
  },
  gateTitle: {
    fontSize: 16,
    fontWeight: '500',
  },
  gateTheme: {
    fontSize: 13,
    fontStyle: 'italic',
    marginBottom: 2,
  },
  gateCenter: {
    fontSize: 11,
    fontWeight: '500',
  },
  considerationSection: {
    paddingTop: 14,
    marginTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  considerationLabel: {
    fontSize: 10,
    fontWeight: '500',
    letterSpacing: 1,
    marginBottom: 6,
  },
  considerationTopic: {
    fontSize: 16,
    fontWeight: '500',
    fontStyle: 'italic',
    lineHeight: 24,
  },
  entryCount: {
    fontSize: 12,
    marginTop: 6,
  },
  noConsiderationText: {
    fontSize: 14,
    lineHeight: 21,
    marginBottom: 12,
  },
  addButton: {
    borderWidth: 1,
    borderRadius: 8,
    paddingVertical: 10,
    paddingHorizontal: 16,
    alignItems: 'center',
  },
  addButtonText: {
    fontSize: 14,
    fontWeight: '500',
  },
  inputSection: {
    gap: 10,
  },
  inputLabel: {
    fontSize: 10,
    fontWeight: '500',
    letterSpacing: 1,
  },
  input: {
    borderWidth: 1,
    borderRadius: 8,
    padding: 12,
    fontSize: 15,
    minHeight: 60,
    textAlignVertical: 'top',
  },
  inputActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 12,
  },
  cancelButton: {
    paddingVertical: 10,
    paddingHorizontal: 16,
  },
  cancelButtonText: {
    fontSize: 14,
  },
  saveButton: {
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 8,
    minWidth: 120,
    alignItems: 'center',
  },
  saveButtonDisabled: {
    opacity: 0.5,
  },
  saveButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#1A1D24',
  },
  newMoonWarning: {
    marginTop: 12,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
  },
  newMoonText: {
    fontSize: 12,
    textAlign: 'center',
  },
  errorText: {
    fontSize: 12,
    marginTop: 8,
    textAlign: 'center',
  },
});

export type { LunarJournalStatus };
