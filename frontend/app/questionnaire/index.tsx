import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Animated,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useRouter } from 'expo-router';
import { Colors } from '../../constants/colors';
import { useAppStore } from '../../store';

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

export default function Questionnaire() {
  const router = useRouter();
  const { user } = useAppStore();
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<string[]>([]);
  const [showTransition, setShowTransition] = useState(false);
  const [fadeAnim] = useState(new Animated.Value(1));

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
        // Show transition screen
        setShowTransition(true);
        Animated.timing(fadeAnim, {
          toValue: 1,
          duration: 300,
          useNativeDriver: true,
        }).start();

        // Navigate to main app after 3 seconds
        setTimeout(() => {
          router.replace('/(tabs)');
        }, 3000);
      }
    });
  };

  if (!user) {
    router.replace('/onboarding');
    return null;
  }

  if (showTransition) {
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

          {/* Skip option */}
          <TouchableOpacity
            style={styles.skipButton}
            onPress={() => router.replace('/(tabs)')}
          >
            <Text style={styles.skipText}>Skip for now</Text>
          </TouchableOpacity>
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
  skipButton: {
    marginTop: 40,
    alignItems: 'center',
    padding: 16,
  },
  skipText: {
    fontSize: 14,
    color: Colors.textTertiary,
    textDecorationLine: 'underline',
  },
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
