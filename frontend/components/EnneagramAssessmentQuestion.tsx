/**
 * EnneagramAssessmentQuestion
 * ===========================
 * Displays one question at a time with appropriate input controls.
 * Supports likert (1-5) and forced choice (A/B + both/neither) formats.
 */

import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '../constants/colors';
import { P2AssessmentQuestion, P2AssessmentAnswer } from '../services/api';

interface Props {
  question: P2AssessmentQuestion;
  selectedAnswer: P2AssessmentAnswer | null;
  onSelectAnswer: (answer: P2AssessmentAnswer) => void;
  onContinue: () => void;
  isSubmitting: boolean;
}

// Likert scale labels (frequency-based - for most questions)
const LIKERT_LABELS_FREQUENCY = [
  { value: 1, label: 'Rarely' },
  { value: 2, label: 'Sometimes' },
  { value: 3, label: 'Often' },
  { value: 4, label: 'Usually' },
  { value: 5, label: 'Almost Always' },
];

// Agreement-based labels (for consistency/validation questions)
const LIKERT_LABELS_AGREEMENT = [
  { value: 1, label: 'Strongly Disagree' },
  { value: 2, label: 'Disagree' },
  { value: 3, label: 'Neutral' },
  { value: 4, label: 'Agree' },
  { value: 5, label: 'Strongly Agree' },
];

// Helper text that rotates (based on question index hint from id)
const HELPER_TEXTS = [
  "Answer based on what usually happens.",
  "Think about how this shows up under pressure.",
  "Go with your first, most familiar response.",
];

// Helper text for agreement questions
const AGREEMENT_HELPER_TEXT = "Select the option that best reflects how you feel.";

// Check if question is a consistency/validation question (needs agreement labels)
const isConsistencyQuestion = (questionId: string): boolean => {
  // Consistency questions start with "CON_" or contain validation-related keywords
  return questionId.startsWith('CON_');
};

export const EnneagramAssessmentQuestion: React.FC<Props> = ({
  question,
  selectedAnswer,
  onSelectAnswer,
  onContinue,
  isSubmitting,
}) => {
  const isLikert = question.format === 'likert';
  const canContinue = selectedAnswer !== null && !isSubmitting;
  
  // Determine which labels to use based on question type
  const useAgreementLabels = isConsistencyQuestion(question.id);
  const likertLabels = useAgreementLabels ? LIKERT_LABELS_AGREEMENT : LIKERT_LABELS_FREQUENCY;
  
  // Pick helper text based on question type
  const helperIndex = question.id.charCodeAt(question.id.length - 1) % HELPER_TEXTS.length;
  const helperText = useAgreementLabels ? AGREEMENT_HELPER_TEXT : HELPER_TEXTS[helperIndex];

  // Render Likert scale (1-5)
  const renderLikertScale = () => (
    <View style={styles.likertContainer}>
      {LIKERT_LABELS.map((item) => {
        const isSelected = selectedAnswer?.value === item.value;
        return (
          <TouchableOpacity
            key={item.value}
            style={[
              styles.likertOption,
              isSelected && styles.likertOptionSelected,
            ]}
            onPress={() => onSelectAnswer({ type: 'likert', value: item.value })}
            activeOpacity={0.7}
          >
            <View
              style={[
                styles.likertCircle,
                isSelected && styles.likertCircleSelected,
              ]}
            >
              {isSelected && (
                <Ionicons name="checkmark" size={14} color={Colors.surface} />
              )}
            </View>
            <Text
              style={[
                styles.likertLabel,
                isSelected && styles.likertLabelSelected,
              ]}
            >
              {item.label}
            </Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );

  // Render forced choice options
  const renderForcedChoice = () => {
    const options = question.options || {};
    const hasC = !!options.C;
    const allowBoth = options.allow_both !== false;
    const allowNeither = options.allow_neither !== false;

    const choices: { key: string; label: string; text?: string }[] = [];

    if (options.A) choices.push({ key: 'A', label: 'A', text: options.A });
    if (options.B) choices.push({ key: 'B', label: 'B', text: options.B });
    if (hasC && options.C) choices.push({ key: 'C', label: 'C', text: options.C });

    return (
      <View style={styles.forcedContainer}>
        {/* Main Options */}
        {choices.map((choice) => {
          const isSelected = selectedAnswer?.value === choice.key;
          return (
            <TouchableOpacity
              key={choice.key}
              style={[
                styles.forcedOption,
                isSelected && styles.forcedOptionSelected,
              ]}
              onPress={() => onSelectAnswer({ type: 'forced', value: choice.key })}
              activeOpacity={0.7}
            >
              <View style={styles.forcedHeader}>
                <View
                  style={[
                    styles.forcedBadge,
                    isSelected && styles.forcedBadgeSelected,
                  ]}
                >
                  <Text
                    style={[
                      styles.forcedBadgeText,
                      isSelected && styles.forcedBadgeTextSelected,
                    ]}
                  >
                    {choice.label}
                  </Text>
                </View>
                {isSelected && (
                  <Ionicons name="checkmark-circle" size={20} color={Colors.text} />
                )}
              </View>
              <Text style={styles.forcedText}>{choice.text}</Text>
            </TouchableOpacity>
          );
        })}

        {/* Both / Neither Options */}
        {(allowBoth || allowNeither) && !hasC && (
          <View style={styles.metaOptionsRow}>
            {allowBoth && (
              <TouchableOpacity
                style={[
                  styles.metaOption,
                  selectedAnswer?.value === 'both' && styles.metaOptionSelected,
                ]}
                onPress={() => onSelectAnswer({ type: 'forced', value: 'both' })}
                activeOpacity={0.7}
              >
                <Text
                  style={[
                    styles.metaOptionText,
                    selectedAnswer?.value === 'both' && styles.metaOptionTextSelected,
                  ]}
                >
                  Both apply
                </Text>
              </TouchableOpacity>
            )}
            {allowNeither && (
              <TouchableOpacity
                style={[
                  styles.metaOption,
                  selectedAnswer?.value === 'neither' && styles.metaOptionSelected,
                ]}
                onPress={() => onSelectAnswer({ type: 'forced', value: 'neither' })}
                activeOpacity={0.7}
              >
                <Text
                  style={[
                    styles.metaOptionText,
                    selectedAnswer?.value === 'neither' && styles.metaOptionTextSelected,
                  ]}
                >
                  Neither applies
                </Text>
              </TouchableOpacity>
            )}
          </View>
        )}
      </View>
    );
  };

  return (
    <View style={styles.container}>
      {/* Question Text */}
      <View style={styles.questionContainer}>
        <Text style={styles.questionText}>{question.prompt}</Text>
        <Text style={styles.helperText}>{helperText}</Text>
      </View>

      {/* Answer Options */}
      {isLikert ? renderLikertScale() : renderForcedChoice()}

      {/* Continue Button */}
      <TouchableOpacity
        style={[
          styles.continueButton,
          !canContinue && styles.continueButtonDisabled,
        ]}
        onPress={onContinue}
        disabled={!canContinue}
        activeOpacity={0.8}
      >
        {isSubmitting ? (
          <ActivityIndicator color={Colors.surface} size="small" />
        ) : (
          <>
            <Text style={styles.continueButtonText}>Continue</Text>
            <Ionicons name="arrow-forward" size={18} color={Colors.surface} />
          </>
        )}
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingHorizontal: 24,
    paddingVertical: 24,
  },
  questionContainer: {
    marginBottom: 32,
    paddingHorizontal: 8,
  },
  questionText: {
    fontSize: 19,
    fontWeight: '500',
    color: Colors.text,
    lineHeight: 28,
    textAlign: 'center',
  },
  helperText: {
    fontSize: 13,
    color: Colors.textTertiary,
    textAlign: 'center',
    marginTop: 12,
    fontStyle: 'italic',
  },
  // Likert Styles
  likertContainer: {
    flex: 1,
    justifyContent: 'center',
    gap: 12,
  },
  likertOption: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 16,
    paddingHorizontal: 20,
    backgroundColor: Colors.surface,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  likertOptionSelected: {
    borderColor: Colors.accent,
    backgroundColor: Colors.surfaceLight,
  },
  likertCircle: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: Colors.border,
    marginRight: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  likertCircleSelected: {
    borderColor: Colors.accent,
    backgroundColor: Colors.accent,
  },
  likertLabel: {
    fontSize: 16,
    color: Colors.text,
  },
  likertLabelSelected: {
    fontWeight: '500',
  },
  // Forced Choice Styles
  forcedContainer: {
    flex: 1,
    justifyContent: 'center',
    gap: 12,
  },
  forcedOption: {
    paddingVertical: 16,
    paddingHorizontal: 16,
    backgroundColor: Colors.surface,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  forcedOptionSelected: {
    borderColor: Colors.accent,
    backgroundColor: Colors.surfaceLight,
  },
  forcedHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  forcedBadge: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: Colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  forcedBadgeSelected: {
    backgroundColor: Colors.accent,
  },
  forcedBadgeText: {
    fontSize: 13,
    fontWeight: '600',
    color: Colors.textSecondary,
  },
  forcedBadgeTextSelected: {
    color: Colors.surface,
  },
  forcedText: {
    fontSize: 15,
    color: Colors.text,
    lineHeight: 22,
  },
  metaOptionsRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 16,
    marginTop: 8,
  },
  metaOption: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 20,
    backgroundColor: Colors.surfaceLight,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  metaOptionSelected: {
    backgroundColor: Colors.accent,
    borderColor: Colors.accent,
  },
  metaOptionText: {
    fontSize: 14,
    color: Colors.textSecondary,
  },
  metaOptionTextSelected: {
    color: Colors.surface,
    fontWeight: '500',
  },
  // Continue Button
  continueButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: Colors.accent,
    paddingVertical: 16,
    borderRadius: 12,
    marginTop: 24,
  },
  continueButtonDisabled: {
    opacity: 0.4,
  },
  continueButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.surface,
  },
});

export default EnneagramAssessmentQuestion;
