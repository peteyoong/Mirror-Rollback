import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Animated,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useRouter } from 'expo-router';
import { Colors } from '../../constants/colors';
import { useAppStore } from '../../store';
import { updateUserEmail } from '../../services/api';

const QUESTIONS = [
  {
    grounding: "Let's begin gently.",
    question: "How would you describe your relationship with yourself right now?",
    options: [
      "Steady and grounded",
      "Curious and reflective",
      "Uncertain or searching",
      "Overwhelmed or stuck",
      "Hard to say right now"
    ]
  },
  {
    grounding: "There's no right answer here.",
    question: "When you pause to reflect, what usually helps most?",
    options: [
      "Gentle questions",
      "Clear perspectives",
      "Emotional reassurance",
      "Practical grounding",
      "I don't reflect much"
    ]
  },
  {
    grounding: "You can always adjust this later.",
    question: "How deep do you want this experience to go right now?",
    options: [
      "Light and grounding",
      "Thoughtful but simple",
      "Deep and exploratory",
      "Slowly, step by step",
      "I'm not sure"
    ]
  },
  {
    grounding: "Just notice what feels true.",
    question: "How do you usually relate to uncertainty?",
    options: [
      "I look for meaning",
      "I look for stability",
      "I explore perspectives",
      "I feel uncomfortable with it",
      "It depends"
    ]
  },
  {
    grounding: "Whatever you choose is enough.",
    question: "What are you hoping this space supports you with?",
    options: [
      "Self-understanding",
      "Emotional clarity",
      "Perspective during change",
      "Quiet reflection",
      "I'm not sure yet"
    ]
  }
];

type ScreenState = 'questions' | 'email' | 'transition';

export default function Questionnaire() {
  const router = useRouter();
  const { user, setUser } = useAppStore();
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<string[]>([]);
  const [screenState, setScreenState] = useState<ScreenState>('questions');
  const [fadeAnim] = useState(new Animated.Value(1));
  
  // Email capture state
  const [email, setEmail] = useState('');
  const [emailError, setEmailError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSelectOption = (option: string) => {
    const newAnswers = [...answers, option];
    setAnswers(newAnswers);

    // Fade out
    Animated.timing(fadeAnim, {
      toValue: 0,
      duration: 200,
      useNativeDriver: true,
    }).start(() => {
      if (currentQuestion < QUESTIONS.length - 1) {
        // Move to next question
        setCurrentQuestion(currentQuestion + 1);
        // Fade in
        Animated.timing(fadeAnim, {
          toValue: 1,
          duration: 300,
          useNativeDriver: true,
        }).start();
      } else {
        // Show email capture screen
        setScreenState('email');
        Animated.timing(fadeAnim, {
          toValue: 1,
          duration: 300,
          useNativeDriver: true,
        }).start();
      }
    });
  };

  const validateEmail = (emailStr: string): boolean => {
    const trimmed = emailStr.trim();
    if (!trimmed) return false;
    if (!trimmed.includes('@')) return false;
    const parts = trimmed.split('@');
    if (parts.length !== 2) return false;
    if (!parts[1].includes('.')) return false;
    return true;
  };

  const handleSaveEmail = async () => {
    setEmailError('');
    
    if (!validateEmail(email)) {
      setEmailError('Please enter a valid email address');
      return;
    }

    if (!user?.id) {
      setEmailError('Session error. Please try again.');
      return;
    }

    setIsSubmitting(true);
    try {
      await updateUserEmail(user.id, email.trim().toLowerCase());
      
      // Update local user state with email
      setUser({ ...user, email: email.trim().toLowerCase() });
      
      // Fade to transition
      Animated.timing(fadeAnim, {
        toValue: 0,
        duration: 200,
        useNativeDriver: true,
      }).start(() => {
        setScreenState('transition');
        Animated.timing(fadeAnim, {
          toValue: 1,
          duration: 300,
          useNativeDriver: true,
        }).start();

        // Navigate to main app after 3 seconds
        setTimeout(() => {
          router.replace('/(tabs)');
        }, 3000);
      });
    } catch (err: any) {
      console.error('Save email error:', err);
      const errorMsg = err.response?.data?.detail || 'Could not save email. Please try again.';
      setEmailError(typeof errorMsg === 'string' ? errorMsg : 'Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!user) {
    router.replace('/onboarding');
    return null;
  }

  // Email capture screen
  if (screenState === 'email') {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar style="light" />
        <KeyboardAvoidingView 
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.keyboardView}
        >
          <ScrollView 
            contentContainerStyle={styles.emailScrollContent}
            keyboardShouldPersistTaps="handled"
          >
            <Animated.View style={[styles.emailContainer, { opacity: fadeAnim }]}>
              <Text style={styles.emailTitle}>Save your space</Text>
              <Text style={styles.emailDescription}>
                We use your email only to save your reflections and help you return to them.
              </Text>

              <View style={styles.emailInputContainer}>
                <TextInput
                  style={[styles.emailInput, emailError ? styles.emailInputError : null]}
                  value={email}
                  onChangeText={(text) => {
                    setEmail(text);
                    if (emailError) setEmailError('');
                  }}
                  placeholder="your@email.com"
                  placeholderTextColor={Colors.textTertiary}
                  keyboardType="email-address"
                  autoCapitalize="none"
                  autoCorrect={false}
                  autoComplete="email"
                  selectionColor={Colors.accent}
                  editable={!isSubmitting}
                />
                {emailError ? (
                  <Text style={styles.emailErrorText}>{emailError}</Text>
                ) : null}
              </View>

              <TouchableOpacity
                style={[styles.saveButton, isSubmitting && styles.saveButtonDisabled]}
                onPress={handleSaveEmail}
                disabled={isSubmitting}
                activeOpacity={0.8}
              >
                {isSubmitting ? (
                  <ActivityIndicator color={Colors.background} size="small" />
                ) : (
                  <Text style={styles.saveButtonText}>Continue</Text>
                )}
              </TouchableOpacity>
            </Animated.View>
          </ScrollView>
        </KeyboardAvoidingView>
      </SafeAreaView>
    );
  }

  // Transition screen
  if (screenState === 'transition') {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar style="light" />
        <Animated.View style={[styles.transitionContainer, { opacity: fadeAnim }]}>
          <Text style={styles.transitionText}>Thank you.</Text>
          <Text style={styles.transitionSubtext}>
            This isn't about defining you — it's about meeting you where you are.
          </Text>
        </Animated.View>
      </SafeAreaView>
    );
  }

  // Questions screen
  const question = QUESTIONS[currentQuestion];
  const progress = ((currentQuestion + 1) / QUESTIONS.length) * 100;

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="light" />
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Progress bar */}
        <View style={styles.progressContainer}>
          <View style={[styles.progressBar, { width: `${progress}%` }]} />
        </View>

        <Animated.View style={[styles.content, { opacity: fadeAnim }]}>
          {/* Grounding line */}
          <Text style={styles.grounding}>{question.grounding}</Text>

          {/* Question */}
          <Text style={styles.question}>{question.question}</Text>

          {/* Options */}
          <View style={styles.optionsContainer}>
            {question.options.map((option, index) => (
              <TouchableOpacity
                key={index}
                style={styles.option}
                onPress={() => handleSelectOption(option)}
                activeOpacity={0.7}
              >
                <Text style={styles.optionText}>{option}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </Animated.View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  keyboardView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    padding: 24,
    justifyContent: 'center',
  },
  progressContainer: {
    height: 2,
    backgroundColor: Colors.surfaceLight,
    marginBottom: 48,
    borderRadius: 1,
    overflow: 'hidden',
  },
  progressBar: {
    height: '100%',
    backgroundColor: Colors.textTertiary,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
  },
  grounding: {
    fontSize: 14,
    color: Colors.textTertiary,
    marginBottom: 24,
    fontStyle: 'italic',
  },
  question: {
    fontSize: 24,
    lineHeight: 32,
    color: Colors.text,
    marginBottom: 40,
    fontWeight: '400',
  },
  optionsContainer: {
    gap: 12,
  },
  option: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 20,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  optionText: {
    fontSize: 16,
    color: Colors.text,
    textAlign: 'center',
  },
  // Email capture styles
  emailScrollContent: {
    flexGrow: 1,
    padding: 24,
    justifyContent: 'center',
  },
  emailContainer: {
    alignItems: 'center',
    paddingHorizontal: 16,
  },
  emailTitle: {
    fontSize: 28,
    fontWeight: '500',
    color: Colors.text,
    marginBottom: 16,
    textAlign: 'center',
  },
  emailDescription: {
    fontSize: 16,
    lineHeight: 24,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginBottom: 40,
    maxWidth: 300,
  },
  emailInputContainer: {
    width: '100%',
    marginBottom: 24,
  },
  emailInput: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 18,
    fontSize: 16,
    color: Colors.text,
    borderWidth: 1,
    borderColor: Colors.border,
    textAlign: 'center',
  },
  emailInputError: {
    borderColor: Colors.error,
  },
  emailErrorText: {
    color: Colors.error,
    fontSize: 14,
    marginTop: 8,
    textAlign: 'center',
  },
  saveButton: {
    backgroundColor: Colors.text,
    borderRadius: 12,
    paddingVertical: 18,
    paddingHorizontal: 48,
    minWidth: 200,
    alignItems: 'center',
  },
  saveButtonDisabled: {
    opacity: 0.6,
  },
  saveButtonText: {
    color: Colors.background,
    fontSize: 16,
    fontWeight: '600',
  },
  // Transition styles
  transitionContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  transitionText: {
    fontSize: 28,
    fontWeight: '500',
    color: Colors.text,
    marginBottom: 24,
    textAlign: 'center',
  },
  transitionSubtext: {
    fontSize: 16,
    lineHeight: 24,
    color: Colors.textSecondary,
    textAlign: 'center',
  },
});
