import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useRouter } from 'expo-router';
import { Colors } from '../../constants/colors';
import { useAppStore } from '../../store';
import { Ionicons } from '@expo/vector-icons';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

// ============================================
// SECTION DEFINITIONS
// ============================================

interface SectionConfig {
  id: string;
  title: string;
  introCopy: string;
  questionFormat: 'likert' | 'forced_choice';
}

const SECTIONS: SectionConfig[] = [
  {
    id: 'core_motivation',
    title: 'Core Motivation',
    introCopy: 'These questions focus on your core motivation — the patterns that repeat across your life.\n\nAnswer based on what feels most fundamental to you, not just how you\'ve been feeling recently.',
    questionFormat: 'likert',
  },
  {
    id: 'disambiguation',
    title: 'Disambiguation',
    introCopy: 'These questions help distinguish between patterns that often look similar on the surface.\n\nChoose the option that feels closer underneath, even if neither feels perfect.',
    questionFormat: 'forced_choice',
  },
  {
    id: 'wing_resolution',
    title: 'Wing Resolution',
    introCopy: 'These final questions refine how your core type expresses itself.\n\nThey help determine which adjacent pattern you tend to draw from more.',
    questionFormat: 'likert', // Can be mixed, but we'll use likert as base
  },
];

// ============================================
// PLACEHOLDER QUESTIONS (to be replaced)
// ============================================

interface LikertQuestion {
  id: string;
  text: string;
  type: 'likert';
}

interface ForcedChoiceQuestion {
  id: string;
  optionA: string;
  optionB: string;
  type: 'forced_choice';
}

type Question = LikertQuestion | ForcedChoiceQuestion;

// Placeholder questions - to be replaced with actual assessment questions
const SECTION_QUESTIONS: { [key: string]: Question[] } = {
  core_motivation: [
    // Placeholder - will be replaced with actual Likert questions
  ],
  disambiguation: [
    // Placeholder - will be replaced with actual forced-choice questions
  ],
  wing_resolution: [
    // Placeholder - will be replaced with actual questions
  ],
};

// ============================================
// LIKERT SCALE OPTIONS
// ============================================

const LIKERT_OPTIONS = [
  { value: 1, label: 'Strongly Disagree' },
  { value: 2, label: 'Disagree' },
  { value: 3, label: 'Neutral' },
  { value: 4, label: 'Agree' },
  { value: 5, label: 'Strongly Agree' },
];

// ============================================
// TYPES FOR RESPONSES
// ============================================

export interface LikertResponse {
  questionId: string;
  value: number; // 1-5
}

export interface ForcedChoiceResponse {
  questionId: string;
  choice: 'A' | 'B';
}

export interface AssessmentResponses {
  core_motivation: LikertResponse[];
  disambiguation: ForcedChoiceResponse[];
  wing_resolution: (LikertResponse | ForcedChoiceResponse)[];
}

// ============================================
// COMPONENT
// ============================================

export default function EnneagramAssessment() {
  const router = useRouter();
  const { user } = useAppStore();
  
  // Navigation state
  const [currentSectionIndex, setCurrentSectionIndex] = useState(0);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [showSectionIntro, setShowSectionIntro] = useState(true);
  const [showInterpretingScreen, setShowInterpretingScreen] = useState(false);
  
  // Response storage
  const [responses, setResponses] = useState<AssessmentResponses>({
    core_motivation: [],
    disambiguation: [],
    wing_resolution: [],
  });
  
  // Get current section and questions
  const currentSection = SECTIONS[currentSectionIndex];
  const currentSectionQuestions = SECTION_QUESTIONS[currentSection.id] || [];
  const currentQuestion = currentSectionQuestions[currentQuestionIndex];
  
  // Calculate overall progress
  const totalQuestions = Object.values(SECTION_QUESTIONS).reduce(
    (sum, questions) => sum + questions.length,
    0
  );
  const completedQuestions = 
    responses.core_motivation.length + 
    responses.disambiguation.length + 
    responses.wing_resolution.length;
  const overallProgress = totalQuestions > 0 
    ? (completedQuestions / totalQuestions) * 100 
    : 0;
  
  // Handle Likert response
  const handleLikertResponse = useCallback((value: number) => {
    if (!currentQuestion || currentQuestion.type !== 'likert') return;
    
    const newResponse: LikertResponse = {
      questionId: currentQuestion.id,
      value,
    };
    
    setResponses(prev => ({
      ...prev,
      [currentSection.id]: [...prev[currentSection.id as keyof AssessmentResponses], newResponse],
    }));
    
    advanceToNext();
  }, [currentQuestion, currentSection]);
  
  // Handle Forced Choice response
  const handleForcedChoiceResponse = useCallback((choice: 'A' | 'B') => {
    if (!currentQuestion || currentQuestion.type !== 'forced_choice') return;
    
    const newResponse: ForcedChoiceResponse = {
      questionId: currentQuestion.id,
      choice,
    };
    
    setResponses(prev => ({
      ...prev,
      [currentSection.id]: [...prev[currentSection.id as keyof AssessmentResponses], newResponse],
    }));
    
    advanceToNext();
  }, [currentQuestion, currentSection]);
  
  // Advance to next question or section
  const advanceToNext = useCallback(() => {
    const nextQuestionIndex = currentQuestionIndex + 1;
    
    if (nextQuestionIndex < currentSectionQuestions.length) {
      // More questions in current section
      setCurrentQuestionIndex(nextQuestionIndex);
    } else {
      // Section complete
      const nextSectionIndex = currentSectionIndex + 1;
      
      if (nextSectionIndex < SECTIONS.length) {
        // Move to next section
        setCurrentSectionIndex(nextSectionIndex);
        setCurrentQuestionIndex(0);
        setShowSectionIntro(true);
      } else {
        // Assessment complete - show interpreting screen
        setShowInterpretingScreen(true);
        
        // Navigate to results after delay
        setTimeout(() => {
          // Store responses in async storage for results screen
          // For now, navigate to results
          router.replace('/enneagram/results');
        }, 3000);
      }
    }
  }, [currentQuestionIndex, currentSectionQuestions.length, currentSectionIndex, router]);
  
  // Start section (from intro)
  const handleStartSection = useCallback(() => {
    setShowSectionIntro(false);
  }, []);
  
  // Go back
  const handleBack = useCallback(() => {
    if (showSectionIntro) {
      // If on section intro, go to previous section's last question
      if (currentSectionIndex > 0) {
        const prevSectionId = SECTIONS[currentSectionIndex - 1].id;
        const prevSectionQuestions = SECTION_QUESTIONS[prevSectionId] || [];
        setCurrentSectionIndex(currentSectionIndex - 1);
        setCurrentQuestionIndex(prevSectionQuestions.length - 1);
        setShowSectionIntro(false);
      } else {
        // Exit assessment
        router.back();
      }
    } else if (currentQuestionIndex > 0) {
      // Go to previous question in current section
      setCurrentQuestionIndex(currentQuestionIndex - 1);
      // Remove last response
      setResponses(prev => {
        const sectionResponses = [...prev[currentSection.id as keyof AssessmentResponses]];
        sectionResponses.pop();
        return {
          ...prev,
          [currentSection.id]: sectionResponses,
        };
      });
    } else {
      // First question of section, show section intro
      setShowSectionIntro(true);
    }
  }, [showSectionIntro, currentSectionIndex, currentQuestionIndex, currentSection, router]);
  
  // Redirect if no user
  if (!user) {
    router.replace('/onboarding');
    return null;
  }
  
  // ============================================
  // RENDER: Interpreting Screen
  // ============================================
  if (showInterpretingScreen) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar style="dark" />
        <View style={styles.interpretingContainer}>
          <View style={styles.interpretingIconContainer}>
            <Ionicons name="analytics-outline" size={48} color={Colors.textSecondary} />
          </View>
          <Text style={styles.interpretingTitle}>Interpreting your responses…</Text>
          <Text style={styles.interpretingSubtext}>
            We're analyzing your patterns to identify your Enneagram type.
          </Text>
        </View>
      </SafeAreaView>
    );
  }
  
  // ============================================
  // RENDER: Section Intro
  // ============================================
  if (showSectionIntro) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar style="dark" />
        
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={handleBack} style={styles.backButton}>
            <Ionicons name="chevron-back" size={24} color={Colors.text} />
          </TouchableOpacity>
          <Text style={styles.sectionIndicator}>
            Section {currentSectionIndex + 1} of {SECTIONS.length}
          </Text>
          <View style={styles.headerSpacer} />
        </View>
        
        {/* Progress bar */}
        <View style={styles.progressContainer}>
          <View style={[styles.progressBar, { width: `${overallProgress}%` }]} />
        </View>
        
        <ScrollView contentContainerStyle={styles.introScrollContent}>
          <View style={styles.introContent}>
            <Text style={styles.sectionTitle}>{currentSection.title}</Text>
            <Text style={styles.introCopy}>{currentSection.introCopy}</Text>
            
            <TouchableOpacity 
              style={styles.continueButton}
              onPress={handleStartSection}
            >
              <Text style={styles.continueButtonText}>Continue</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </SafeAreaView>
    );
  }
  
  // ============================================
  // RENDER: No Questions (placeholder state)
  // ============================================
  if (!currentQuestion) {
    // No questions defined yet - auto-advance or show placeholder
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar style="dark" />
        
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={handleBack} style={styles.backButton}>
            <Ionicons name="chevron-back" size={24} color={Colors.text} />
          </TouchableOpacity>
          <Text style={styles.sectionIndicator}>
            Section {currentSectionIndex + 1} of {SECTIONS.length}
          </Text>
          <View style={styles.headerSpacer} />
        </View>
        
        {/* Progress bar */}
        <View style={styles.progressContainer}>
          <View style={[styles.progressBar, { width: `${overallProgress}%` }]} />
        </View>
        
        <View style={styles.placeholderContent}>
          <Ionicons name="construct-outline" size={48} color={Colors.textTertiary} />
          <Text style={styles.placeholderTitle}>Questions Coming Soon</Text>
          <Text style={styles.placeholderText}>
            Questions for the {currentSection.title} section will be added here.
          </Text>
          
          <TouchableOpacity 
            style={styles.continueButton}
            onPress={advanceToNext}
          >
            <Text style={styles.continueButtonText}>
              {currentSectionIndex < SECTIONS.length - 1 ? 'Skip to Next Section' : 'Complete Assessment'}
            </Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }
  
  // ============================================
  // RENDER: Likert Question
  // ============================================
  if (currentQuestion.type === 'likert') {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar style="dark" />
        
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={handleBack} style={styles.backButton}>
            <Ionicons name="chevron-back" size={24} color={Colors.text} />
          </TouchableOpacity>
          <Text style={styles.sectionIndicator}>
            Section {currentSectionIndex + 1} of {SECTIONS.length}
          </Text>
          <View style={styles.headerSpacer} />
        </View>
        
        {/* Progress bar */}
        <View style={styles.progressContainer}>
          <View style={[styles.progressBar, { width: `${overallProgress}%` }]} />
        </View>
        
        <ScrollView contentContainerStyle={styles.questionScrollContent}>
          {/* Question number */}
          <Text style={styles.questionNumber}>
            Question {currentQuestionIndex + 1} of {currentSectionQuestions.length}
          </Text>
          
          {/* Question text */}
          <Text style={styles.questionText}>
            {(currentQuestion as LikertQuestion).text}
          </Text>
          
          {/* Likert options */}
          <View style={styles.likertContainer}>
            {LIKERT_OPTIONS.map((option) => (
              <TouchableOpacity
                key={option.value}
                style={styles.likertOption}
                onPress={() => handleLikertResponse(option.value)}
                activeOpacity={0.7}
              >
                <View style={styles.likertCircle}>
                  <Text style={styles.likertValue}>{option.value}</Text>
                </View>
                <Text style={styles.likertLabel}>{option.label}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </ScrollView>
      </SafeAreaView>
    );
  }
  
  // ============================================
  // RENDER: Forced Choice Question
  // ============================================
  if (currentQuestion.type === 'forced_choice') {
    const fcQuestion = currentQuestion as ForcedChoiceQuestion;
    
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar style="dark" />
        
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={handleBack} style={styles.backButton}>
            <Ionicons name="chevron-back" size={24} color={Colors.text} />
          </TouchableOpacity>
          <Text style={styles.sectionIndicator}>
            Section {currentSectionIndex + 1} of {SECTIONS.length}
          </Text>
          <View style={styles.headerSpacer} />
        </View>
        
        {/* Progress bar */}
        <View style={styles.progressContainer}>
          <View style={[styles.progressBar, { width: `${overallProgress}%` }]} />
        </View>
        
        <ScrollView contentContainerStyle={styles.questionScrollContent}>
          {/* Question number */}
          <Text style={styles.questionNumber}>
            Question {currentQuestionIndex + 1} of {currentSectionQuestions.length}
          </Text>
          
          {/* Instruction */}
          <Text style={styles.forcedChoiceInstruction}>
            Choose the option that feels closer to you
          </Text>
          
          {/* Options */}
          <View style={styles.forcedChoiceContainer}>
            <TouchableOpacity
              style={styles.forcedChoiceOption}
              onPress={() => handleForcedChoiceResponse('A')}
              activeOpacity={0.7}
            >
              <View style={styles.forcedChoiceLabel}>
                <Text style={styles.forcedChoiceLetter}>A</Text>
              </View>
              <Text style={styles.forcedChoiceText}>{fcQuestion.optionA}</Text>
            </TouchableOpacity>
            
            <View style={styles.forcedChoiceDivider}>
              <View style={styles.dividerLine} />
              <Text style={styles.dividerText}>or</Text>
              <View style={styles.dividerLine} />
            </View>
            
            <TouchableOpacity
              style={styles.forcedChoiceOption}
              onPress={() => handleForcedChoiceResponse('B')}
              activeOpacity={0.7}
            >
              <View style={styles.forcedChoiceLabel}>
                <Text style={styles.forcedChoiceLetter}>B</Text>
              </View>
              <Text style={styles.forcedChoiceText}>{fcQuestion.optionB}</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </SafeAreaView>
    );
  }
  
  // Fallback
  return null;
}

// ============================================
// STYLES
// ============================================

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  
  // Header
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  backButton: {
    padding: 4,
    marginLeft: -4,
  },
  sectionIndicator: {
    fontSize: 14,
    fontWeight: '500',
    color: Colors.textSecondary,
  },
  headerSpacer: {
    width: 32,
  },
  
  // Progress
  progressContainer: {
    height: 3,
    backgroundColor: Colors.border,
    marginHorizontal: 24,
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressBar: {
    height: '100%',
    backgroundColor: Colors.text,
    borderRadius: 2,
  },
  
  // Section Intro
  introScrollContent: {
    flexGrow: 1,
    padding: 24,
    justifyContent: 'center',
  },
  introContent: {
    alignItems: 'center',
  },
  sectionTitle: {
    fontSize: 28,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 24,
    textAlign: 'center',
  },
  introCopy: {
    fontSize: 16,
    lineHeight: 26,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginBottom: 40,
    paddingHorizontal: 8,
  },
  continueButton: {
    backgroundColor: Colors.text,
    borderRadius: 12,
    paddingVertical: 16,
    paddingHorizontal: 48,
  },
  continueButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.background,
  },
  
  // Question Common
  questionScrollContent: {
    flexGrow: 1,
    padding: 24,
  },
  questionNumber: {
    fontSize: 13,
    fontWeight: '500',
    color: Colors.textTertiary,
    textAlign: 'center',
    marginBottom: 24,
    marginTop: 16,
  },
  questionText: {
    fontSize: 20,
    lineHeight: 30,
    color: Colors.text,
    textAlign: 'center',
    marginBottom: 40,
    paddingHorizontal: 8,
  },
  
  // Likert Scale
  likertContainer: {
    gap: 12,
  },
  likertOption: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  likertCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: Colors.background,
    borderWidth: 1,
    borderColor: Colors.border,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 16,
  },
  likertValue: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.text,
  },
  likertLabel: {
    fontSize: 15,
    color: Colors.text,
    flex: 1,
  },
  
  // Forced Choice
  forcedChoiceInstruction: {
    fontSize: 14,
    color: Colors.textTertiary,
    textAlign: 'center',
    marginBottom: 32,
  },
  forcedChoiceContainer: {
    gap: 16,
  },
  forcedChoiceOption: {
    backgroundColor: Colors.surface,
    borderRadius: 16,
    padding: 24,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  forcedChoiceLabel: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: Colors.background,
    borderWidth: 1,
    borderColor: Colors.text,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  forcedChoiceLetter: {
    fontSize: 14,
    fontWeight: '700',
    color: Colors.text,
  },
  forcedChoiceText: {
    fontSize: 16,
    lineHeight: 24,
    color: Colors.text,
  },
  forcedChoiceDivider: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
    paddingVertical: 8,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: Colors.border,
  },
  dividerText: {
    fontSize: 13,
    color: Colors.textTertiary,
    fontWeight: '500',
  },
  
  // Placeholder State
  placeholderContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  placeholderTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: Colors.text,
    marginTop: 16,
    marginBottom: 8,
  },
  placeholderText: {
    fontSize: 15,
    lineHeight: 22,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginBottom: 32,
  },
  
  // Interpreting Screen
  interpretingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  interpretingIconContainer: {
    marginBottom: 24,
  },
  interpretingTitle: {
    fontSize: 24,
    fontWeight: '500',
    color: Colors.text,
    marginBottom: 16,
    textAlign: 'center',
  },
  interpretingSubtext: {
    fontSize: 15,
    lineHeight: 22,
    color: Colors.textSecondary,
    textAlign: 'center',
  },
});
