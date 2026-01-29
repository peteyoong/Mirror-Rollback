import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Alert,
  Dimensions,
  TextInput,
  Platform,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../src/context/AuthContext';
import { api } from '../../src/services/api';
import { COLORS, SPACING, BORDER_RADIUS } from '../../src/constants/theme';
import DateTimePicker from '@react-native-community/datetimepicker';

const { width } = Dimensions.get('window');

interface Question {
  id: string;
  question: string;
  type: 'options' | 'birthdata';
  options?: { value: string; label: string }[];
}

const QUESTIONS: Question[] = [
  {
    id: 'relationship_with_self',
    question: 'How would you describe your current relationship with yourself?',
    type: 'options',
    options: [
      { value: 'curious', label: 'Curious and exploring' },
      { value: 'gentle', label: 'Learning to be gentle' },
      { value: 'complex', label: 'Complex and evolving' },
      { value: 'rebuilding', label: 'Rebuilding foundations' },
    ],
  },
  {
    id: 'reflection_style',
    question: 'When you reflect, what feels most natural to you?',
    type: 'options',
    options: [
      { value: 'writing', label: 'Writing my thoughts down' },
      { value: 'contemplating', label: 'Sitting with a question' },
      { value: 'patterns', label: 'Looking for patterns' },
      { value: 'feeling', label: 'Feeling into my body' },
    ],
  },
  {
    id: 'desired_depth',
    question: 'How deep do you want to go in your reflections?',
    type: 'options',
    options: [
      { value: 'surface', label: 'Light and present-focused' },
      { value: 'moderate', label: 'Thoughtful but not heavy' },
      { value: 'deep', label: 'Deep and meaningful' },
      { value: 'varies', label: 'It varies day by day' },
    ],
  },
  {
    id: 'uncertainty_relationship',
    question: 'How do you relate to not knowing?',
    type: 'options',
    options: [
      { value: 'comfortable', label: 'I find comfort in mystery' },
      { value: 'learning', label: 'Learning to sit with it' },
      { value: 'challenging', label: 'It\'s challenging for me' },
      { value: 'mixed', label: 'Depends on the situation' },
    ],
  },
  {
    id: 'intention',
    question: 'What brings you here today?',
    type: 'options',
    options: [
      { value: 'self_understanding', label: 'To understand myself better' },
      { value: 'daily_practice', label: 'To build a daily practice' },
      { value: 'clarity', label: 'To find more clarity' },
      { value: 'presence', label: 'To be more present' },
    ],
  },
  {
    id: 'birthdata',
    question: 'To personalize your reflections, we can use your birth details (optional)',
    type: 'birthdata',
  },
];

export default function OnboardingQuestions() {
  const router = useRouter();
  const { user, updateUser } = useAuth();
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);

  const currentQuestion = QUESTIONS[currentIndex];
  const isLastQuestion = currentIndex === QUESTIONS.length - 1;
  const progress = (currentIndex + 1) / QUESTIONS.length;

  const handleSelect = (value: string) => {
    setAnswers({ ...answers, [currentQuestion.id]: value });
  };

  const handleNext = async () => {
    if (!answers[currentQuestion.id]) {
      return;
    }

    if (isLastQuestion) {
      await submitOnboarding();
    } else {
      setCurrentIndex(currentIndex + 1);
    }
  };

  const handleBack = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  };

  const submitOnboarding = async () => {
    setLoading(true);
    try {
      await api.post('/onboarding/complete', answers);
      if (user) {
        updateUser({ ...user, onboarding_completed: true, onboarding_answers: answers as any });
      }
      router.replace('/(main)/mirror');
    } catch (error: any) {
      Alert.alert('Error', 'Failed to save your responses. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        {currentIndex > 0 && (
          <TouchableOpacity onPress={handleBack} style={styles.backButton}>
            <Ionicons name="arrow-back" size={24} color={COLORS.primary} />
          </TouchableOpacity>
        )}
        <View style={styles.progressContainer}>
          <View style={styles.progressBar}>
            <View style={[styles.progressFill, { width: `${progress * 100}%` }]} />
          </View>
          <Text style={styles.progressText}>{currentIndex + 1} of {QUESTIONS.length}</Text>
        </View>
      </View>

      <ScrollView
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        <Text style={styles.question}>{currentQuestion.question}</Text>

        <View style={styles.options}>
          {currentQuestion.options.map((option) => (
            <TouchableOpacity
              key={option.value}
              style={[
                styles.option,
                answers[currentQuestion.id] === option.value && styles.optionSelected,
              ]}
              onPress={() => handleSelect(option.value)}
            >
              <Text
                style={[
                  styles.optionText,
                  answers[currentQuestion.id] === option.value && styles.optionTextSelected,
                ]}
              >
                {option.label}
              </Text>
              {answers[currentQuestion.id] === option.value && (
                <Ionicons name="checkmark" size={20} color={COLORS.accent} />
              )}
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>

      <View style={styles.footer}>
        <TouchableOpacity
          style={[
            styles.continueButton,
            !answers[currentQuestion.id] && styles.continueButtonDisabled,
          ]}
          onPress={handleNext}
          disabled={!answers[currentQuestion.id] || loading}
        >
          {loading ? (
            <ActivityIndicator color={COLORS.white} />
          ) : (
            <Text style={styles.continueButtonText}>
              {isLastQuestion ? 'Begin' : 'Continue'}
            </Text>
          )}
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: SPACING.lg,
    paddingTop: SPACING.md,
    minHeight: 60,
  },
  backButton: {
    width: 44,
    height: 44,
    justifyContent: 'center',
    marginRight: SPACING.sm,
  },
  progressContainer: {
    flex: 1,
    alignItems: 'flex-end',
  },
  progressBar: {
    width: 120,
    height: 4,
    backgroundColor: COLORS.border,
    borderRadius: 2,
    marginBottom: SPACING.xs,
  },
  progressFill: {
    height: '100%',
    backgroundColor: COLORS.accent,
    borderRadius: 2,
  },
  progressText: {
    fontSize: 12,
    color: COLORS.secondary,
  },
  content: {
    flexGrow: 1,
    paddingHorizontal: SPACING.lg,
    paddingTop: SPACING.xxl,
  },
  question: {
    fontSize: 26,
    fontWeight: '300',
    color: COLORS.primary,
    lineHeight: 36,
    marginBottom: SPACING.xxl,
  },
  options: {
    gap: SPACING.md,
  },
  option: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: COLORS.white,
    paddingVertical: SPACING.md,
    paddingHorizontal: SPACING.lg,
    borderRadius: BORDER_RADIUS.md,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  optionSelected: {
    borderColor: COLORS.accent,
    backgroundColor: '#F5F8F3',
  },
  optionText: {
    fontSize: 16,
    color: COLORS.primary,
    flex: 1,
  },
  optionTextSelected: {
    color: COLORS.accent,
  },
  footer: {
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.lg,
  },
  continueButton: {
    backgroundColor: COLORS.accent,
    paddingVertical: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    alignItems: 'center',
  },
  continueButtonDisabled: {
    opacity: 0.5,
  },
  continueButtonText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: '600',
  },
});
