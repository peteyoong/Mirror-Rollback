/**
 * Cycle Completion Modal - Task 51 (Fixed in Task 54)
 * 
 * Shows when a lunar cycle is completing (near New Moon).
 * Allows Reflector to either close the consideration or continue to next cycle.
 * 
 * Task 54 fixes:
 * - Added proper error display
 * - Added success confirmation message
 * - Added loading state to both buttons
 * - Fixed silent failure issue
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Modal,
  ActivityIndicator,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useTheme } from '../../contexts/ThemeContext';
import api from '../../services/api';

// =============================================================================
// TYPES
// =============================================================================

interface CycleCompletionModalProps {
  visible: boolean;
  userId: string;
  considerationId: string;
  considerationTopic: string;
  cycleCompletionPrompts: string[];
  onClose: () => void;
  onComplete: (message?: string) => void;
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

export default function CycleCompletionModal({
  visible,
  userId,
  considerationId,
  considerationTopic,
  cycleCompletionPrompts,
  onClose,
  onComplete,
}: CycleCompletionModalProps) {
  const { theme } = useTheme();
  const [reflection, setReflection] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [continueToNextCycle, setContinueToNextCycle] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Reset state when modal opens/closes
  React.useEffect(() => {
    if (visible) {
      setError(null);
      setIsSubmitting(false);
    }
  }, [visible]);

  const handleSubmit = async () => {
    if (!considerationId || isSubmitting) {
      console.log('[CycleCompletion] Submit blocked: no considerationId or already submitting');
      return;
    }
    
    console.log('[CycleCompletion] Submit clicked:', {
      considerationId,
      continueToNextCycle,
      hasReflection: !!reflection.trim(),
    });
    
    setIsSubmitting(true);
    setError(null);
    
    try {
      const payload = {
        final_reflection: reflection.trim() || null,
        continue_to_next_cycle: continueToNextCycle,
      };
      
      console.log('[CycleCompletion] Sending payload:', payload);
      
      const response = await api.post(
        `/lunar-journal/${userId}/consideration/${considerationId}/close`,
        payload
      );
      
      console.log('[CycleCompletion] Response received:', response.data);
      
      if (response.data?.success) {
        // Success - determine message based on action
        const successMessage = continueToNextCycle
          ? 'Observation continued into the next lunar cycle.'
          : 'Cycle completed and archived.';
        
        console.log('[CycleCompletion] Success, calling onComplete with:', successMessage);
        
        // Clear form state
        setReflection('');
        setContinueToNextCycle(false);
        
        // Call onComplete with success message
        onComplete(successMessage);
      } else {
        // Response doesn't have success flag
        throw new Error(response.data?.detail || 'Unknown error occurred');
      }
      
    } catch (err: any) {
      console.error('[CycleCompletion] Error:', err);
      
      // Extract error message
      const errorMessage = err.response?.data?.detail 
        || err.message 
        || 'Failed to complete cycle. Please try again.';
      
      setError(errorMessage);
      // Don't close modal on error - let user retry
    } finally {
      setIsSubmitting(false);
      console.log('[CycleCompletion] Submit finished, isSubmitting set to false');
    }
  };

  const handleDismiss = () => {
    if (isSubmitting) return; // Don't allow dismiss while submitting
    setError(null);
    setReflection('');
    setContinueToNextCycle(false);
    onClose();
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      transparent={true}
      onRequestClose={handleDismiss}
    >
      <KeyboardAvoidingView 
        style={styles.overlay}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <View style={[styles.modalContent, { backgroundColor: theme.background }]}>
          <ScrollView 
            style={styles.scroll}
            contentContainerStyle={styles.scrollContent}
            showsVerticalScrollIndicator={false}
            keyboardShouldPersistTaps="handled"
          >
            {/* Header */}
            <View style={styles.header}>
              <Text style={styles.moonIcon}>🌑</Text>
              <Text style={[styles.title, { color: LUNAR_COLORS.moonlight }]}>
                LUNAR CYCLE COMPLETING
              </Text>
            </View>

            {/* Error Message */}
            {error && (
              <View style={[styles.errorBox, { backgroundColor: 'rgba(229, 115, 115, 0.15)' }]}>
                <Text style={styles.errorText}>{error}</Text>
              </View>
            )}

            {/* Message */}
            <Text style={[styles.message, { color: theme.text }]}>
              This lunar cycle appears to be completing. A new cycle may soon begin.
            </Text>

            {/* Consideration Topic */}
            <View style={[styles.topicSection, { backgroundColor: LUNAR_COLORS.glow }]}>
              <Text style={[styles.topicLabel, { color: LUNAR_COLORS.silver }]}>
                YOU'VE BEEN OBSERVING
              </Text>
              <Text style={[styles.topicText, { color: theme.text }]}>
                "{considerationTopic}"
              </Text>
            </View>

            {/* Reflection Prompts */}
            <View style={styles.promptsSection}>
              <Text style={[styles.promptsLabel, { color: LUNAR_COLORS.silver }]}>
                REFLECTION QUESTIONS
              </Text>
              {cycleCompletionPrompts.map((prompt, index) => (
                <Text key={index} style={[styles.promptItem, { color: theme.textSecondary }]}>
                  • {prompt}
                </Text>
              ))}
            </View>

            {/* Final Reflection Input */}
            <View style={styles.inputSection}>
              <Text style={[styles.inputLabel, { color: LUNAR_COLORS.silver }]}>
                FINAL REFLECTION (OPTIONAL)
              </Text>
              <TextInput
                style={[
                  styles.input,
                  { 
                    backgroundColor: theme.surface, 
                    color: theme.text,
                    borderColor: theme.border,
                  }
                ]}
                placeholder="What clarity emerged over this cycle?"
                placeholderTextColor={theme.textTertiary}
                value={reflection}
                onChangeText={setReflection}
                multiline
                numberOfLines={4}
                textAlignVertical="top"
                editable={!isSubmitting}
              />
            </View>

            {/* Continue Option */}
            <TouchableOpacity
              style={[
                styles.optionButton,
                { 
                  backgroundColor: continueToNextCycle ? LUNAR_COLORS.glow : 'transparent',
                  borderColor: continueToNextCycle ? LUNAR_COLORS.moonlight : theme.border,
                  opacity: isSubmitting ? 0.6 : 1,
                }
              ]}
              onPress={() => !isSubmitting && setContinueToNextCycle(!continueToNextCycle)}
              activeOpacity={0.7}
              disabled={isSubmitting}
            >
              <View style={[
                styles.checkbox,
                { 
                  borderColor: continueToNextCycle ? LUNAR_COLORS.moonlight : theme.textTertiary,
                  backgroundColor: continueToNextCycle ? LUNAR_COLORS.moonlight : 'transparent',
                }
              ]}>
                {continueToNextCycle && (
                  <Text style={styles.checkmark}>✓</Text>
                )}
              </View>
              <View style={styles.optionText}>
                <Text style={[styles.optionTitle, { color: theme.text }]}>
                  Continue observing into next cycle
                </Text>
                <Text style={[styles.optionDescription, { color: theme.textSecondary }]}>
                  Keep the same consideration active for another lunar cycle
                </Text>
              </View>
            </TouchableOpacity>

            {/* Actions */}
            <View style={styles.actions}>
              <TouchableOpacity
                style={[styles.dismissButton, isSubmitting && { opacity: 0.5 }]}
                onPress={handleDismiss}
                disabled={isSubmitting}
              >
                <Text style={[styles.dismissButtonText, { color: theme.textSecondary }]}>
                  Not now
                </Text>
              </TouchableOpacity>
              
              <TouchableOpacity
                style={[
                  styles.completeButton, 
                  { backgroundColor: LUNAR_COLORS.moonlight },
                  isSubmitting && { opacity: 0.8 },
                ]}
                onPress={handleSubmit}
                disabled={isSubmitting}
                activeOpacity={0.7}
              >
                {isSubmitting ? (
                  <View style={styles.loadingContainer}>
                    <ActivityIndicator size="small" color="#1A1D24" />
                    <Text style={styles.loadingText}>
                      {continueToNextCycle ? 'Continuing...' : 'Completing...'}
                    </Text>
                  </View>
                ) : (
                  <Text style={styles.completeButtonText}>
                    {continueToNextCycle ? 'Continue to Next Cycle' : 'Complete Cycle'}
                  </Text>
                )}
              </TouchableOpacity>
            </View>
          </ScrollView>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
}

// =============================================================================
// STYLES
// =============================================================================

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    maxHeight: '90%',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
  },
  scroll: {
    flex: 1,
  },
  scrollContent: {
    padding: 24,
    paddingBottom: 40,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 16,
  },
  moonIcon: {
    fontSize: 24,
  },
  title: {
    fontSize: 12,
    fontWeight: '600',
    letterSpacing: 1,
  },
  errorBox: {
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
  },
  errorText: {
    fontSize: 14,
    color: '#E57373',
    textAlign: 'center',
  },
  message: {
    fontSize: 16,
    lineHeight: 24,
    marginBottom: 20,
  },
  topicSection: {
    borderRadius: 10,
    padding: 16,
    marginBottom: 24,
  },
  topicLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 8,
  },
  topicText: {
    fontSize: 17,
    fontStyle: 'italic',
    fontWeight: '500',
    lineHeight: 24,
  },
  promptsSection: {
    marginBottom: 24,
  },
  promptsLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 12,
  },
  promptItem: {
    fontSize: 14,
    lineHeight: 22,
    marginBottom: 8,
    paddingLeft: 4,
  },
  inputSection: {
    marginBottom: 20,
  },
  inputLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 10,
  },
  input: {
    borderWidth: 1,
    borderRadius: 10,
    padding: 14,
    fontSize: 15,
    minHeight: 100,
    lineHeight: 22,
  },
  optionButton: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    borderWidth: 1,
    borderRadius: 10,
    padding: 16,
    marginBottom: 24,
    gap: 12,
  },
  checkbox: {
    width: 22,
    height: 22,
    borderRadius: 4,
    borderWidth: 2,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 2,
  },
  checkmark: {
    color: '#1A1D24',
    fontSize: 14,
    fontWeight: '700',
  },
  optionText: {
    flex: 1,
  },
  optionTitle: {
    fontSize: 15,
    fontWeight: '500',
    marginBottom: 4,
  },
  optionDescription: {
    fontSize: 13,
    lineHeight: 19,
  },
  actions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: 16,
  },
  dismissButton: {
    paddingVertical: 14,
    paddingHorizontal: 20,
  },
  dismissButtonText: {
    fontSize: 15,
  },
  completeButton: {
    flex: 1,
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 48,
  },
  completeButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1A1D24',
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  loadingText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1A1D24',
  },
});
