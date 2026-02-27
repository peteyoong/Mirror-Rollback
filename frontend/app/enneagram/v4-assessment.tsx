/**
 * Enneagram Assessment V4
 * =======================
 * 108-question behavioral assessment with weighted scoring
 * 
 * Features:
 * - 3 sections: Body, Heart, Head triads
 * - 5-point Likert scale responses
 * - Real-time progress persistence
 * - Gaming detection (response time tracking)
 * - Top 2 types with wing suggestions
 * 
 * Target: ~15 minute completion, 90%+ accuracy
 */

import React, { useState, useCallback, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Alert,
  BackHandler,
  Platform,
  Pressable,
  ActivityIndicator,
  ScrollView,
  TouchableOpacity,
  Animated,
  Dimensions,
} from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Colors } from '../../constants/colors';
import { useAppStore } from '../../store';
import { navigateToLenses } from '../../utils/navigation';
import { apiWithRetry } from '../../services/api';

// Constants
const V4_SESSION_STORAGE_KEY = 'enneagram_v4_assessment_session';
const SESSION_TTL_MS = 24 * 60 * 60 * 1000; // 24 hours
const MIN_RESPONSE_TIME_MS = 2000; // 2 seconds minimum
const { width: SCREEN_WIDTH } = Dimensions.get('window');

// Types
interface V4Question {
  id: string;
  text: string;
  primary_type: number;
  secondary_influence?: number;
  triad: 'body' | 'heart' | 'head';
  difficulty_weight: number;
  reverse_coded: boolean;
  options: Array<{
    value: number;
    text: string;
  }>;
  index: number;
}

interface V4TypeScore {
  type: number;
  name: string;
  percentage: number;
}

interface V4Result {
  primary_type: {
    number: number;
    name: string;
    percentage: number;
    core_desire: string;
    core_fear: string;
    brief: string;
  };
  secondary_type: {
    number: number;
    name: string;
    percentage: number;
  };
  suggested_wing: number;
  full_type_string: string;
  all_scores: V4TypeScore[];
  confidence_level: 'high' | 'medium' | 'low';
  is_unclear: boolean;
  flags: string[];
}

interface StoredSession {
  session_id: string;
  user_id: string;
  current_index: number;
  created_at_iso: string;
  updated_at_iso: string;
}

// View states
type ViewState = 'loading' | 'welcome' | 'section_intro' | 'questions' | 'computing' | 'results' | 'error';

// Section info
const SECTION_INFO = {
  body: {
    name: 'Body Center',
    subtitle: 'The Gut Triad',
    types: [8, 9, 1],
    description: 'These questions explore how you respond to life through action, instinct, and boundaries.',
    icon: 'body-outline' as const,
    color: '#E57373',
  },
  heart: {
    name: 'Heart Center',
    subtitle: 'The Feeling Triad',
    types: [2, 3, 4],
    description: 'These questions explore how you connect with others and process emotions.',
    icon: 'heart-outline' as const,
    color: '#81C784',
  },
  head: {
    name: 'Head Center',
    subtitle: 'The Thinking Triad',
    types: [5, 6, 7],
    description: 'These questions explore how you analyze, plan, and seek security.',
    icon: 'bulb-outline' as const,
    color: '#64B5F6',
  },
};

// API Functions
const startV4Assessment = async (userId: string) => {
  const response = await apiWithRetry.post('/enneagram/v4/start', { user_id: userId });
  return response.data;
};

const submitV4Answer = async (
  sessionId: string,
  questionId: string,
  answerValue: number,
  responseTimeMs: number
) => {
  const response = await apiWithRetry.post('/enneagram/v4/answer', {
    session_id: sessionId,
    question_id: questionId,
    answer_value: answerValue,
    response_time_ms: responseTimeMs,
  });
  return response.data;
};

const resumeV4Assessment = async (userId: string) => {
  const response = await apiWithRetry.post('/enneagram/v4/resume', { user_id: userId });
  return response.data;
};

const getV4Results = async (sessionId: string) => {
  const response = await apiWithRetry.get(`/enneagram/v4/results/${sessionId}`);
  return response.data;
};

export default function V4Assessment() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { user, setEnneagramResult } = useAppStore();

  // State
  const [viewState, setViewState] = useState<ViewState>('loading');
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Session state
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [currentQuestions, setCurrentQuestions] = useState<V4Question[]>([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [totalQuestions, setTotalQuestions] = useState(42);
  const [currentSection, setCurrentSection] = useState<'body' | 'heart' | 'head'>('body');
  const [selectedValue, setSelectedValue] = useState<number | null>(null);
  const [hasExistingSession, setHasExistingSession] = useState(false);

  // Result state
  const [result, setResult] = useState<V4Result | null>(null);
  const [showFullBreakdown, setShowFullBreakdown] = useState(false);

  // Timing
  const questionStartTime = useRef<number>(Date.now());
  const fadeAnim = useRef(new Animated.Value(1)).current;

  // Refs
  const hasInitialized = useRef(false);

  // ============================================
  // SESSION PERSISTENCE
  // ============================================

  const saveSession = useCallback(async (session: StoredSession) => {
    try {
      await AsyncStorage.setItem(V4_SESSION_STORAGE_KEY, JSON.stringify(session));
    } catch (err) {
      console.error('[V4] Error saving session:', err);
    }
  }, []);

  const loadSession = useCallback(async (): Promise<StoredSession | null> => {
    try {
      const stored = await AsyncStorage.getItem(V4_SESSION_STORAGE_KEY);
      if (!stored) return null;

      const session: StoredSession = JSON.parse(stored);
      const createdAt = new Date(session.created_at_iso).getTime();
      
      if (Date.now() - createdAt > SESSION_TTL_MS) {
        await AsyncStorage.removeItem(V4_SESSION_STORAGE_KEY);
        return null;
      }

      return session;
    } catch (err) {
      console.error('[V4] Error loading session:', err);
      return null;
    }
  }, []);

  const clearSession = useCallback(async () => {
    try {
      await AsyncStorage.removeItem(V4_SESSION_STORAGE_KEY);
    } catch (err) {
      console.error('[V4] Error clearing session:', err);
    }
  }, []);

  // ============================================
  // INITIALIZATION
  // ============================================

  useEffect(() => {
    const initialize = async () => {
      if (hasInitialized.current) return;
      hasInitialized.current = true;

      if (!user?.id) {
        setError('Please log in to take the assessment');
        setViewState('error');
        return;
      }

      try {
        // Check for existing session
        const storedSession = await loadSession();
        if (storedSession && storedSession.user_id === user.id) {
          setHasExistingSession(true);
        }
        setViewState('welcome');
      } catch (err) {
        console.error('[V4] Initialization error:', err);
        setViewState('welcome');
      }
    };

    initialize();
  }, [user, loadSession]);

  // ============================================
  // BACK HANDLER
  // ============================================

  useEffect(() => {
    const handleBack = () => {
      if (viewState === 'questions') {
        Alert.alert(
          'Exit Assessment?',
          'Your progress is saved. You can resume later.',
          [
            { text: 'Continue Assessment', style: 'cancel' },
            {
              text: 'Exit',
              onPress: () => navigateToLenses(router),
            },
          ]
        );
        return true;
      }
      return false;
    };

    const subscription = BackHandler.addEventListener('hardwareBackPress', handleBack);
    return () => subscription.remove();
  }, [viewState, router]);

  // ============================================
  // ASSESSMENT ACTIONS
  // ============================================

  const startAssessment = async (resume: boolean = false) => {
    if (!user?.id) return;

    setIsLoading(true);
    setError(null);

    try {
      let data;
      
      if (resume) {
        data = await resumeV4Assessment(user.id);
      } else {
        await clearSession();
        data = await startV4Assessment(user.id);
      }

      setSessionId(data.session_id);
      setCurrentQuestions(data.next_batch || []);
      setCurrentQuestionIndex(data.current_index || 0);
      setTotalQuestions(data.total_questions || 42);

      // Determine section
      const section = getSectionForIndex(data.current_index || 0);
      setCurrentSection(section);

      // Save session
      await saveSession({
        session_id: data.session_id,
        user_id: user.id,
        current_index: data.current_index || 0,
        created_at_iso: new Date().toISOString(),
        updated_at_iso: new Date().toISOString(),
      });

      // Show section intro or questions
      setViewState('section_intro');
      questionStartTime.current = Date.now();

    } catch (err: any) {
      console.error('[V4] Start error:', err);
      if (err.response?.status === 404) {
        // No session found, start fresh
        setHasExistingSession(false);
        setError('No session found. Starting fresh assessment.');
      } else {
        setError(err.message || 'Failed to start assessment');
        setViewState('error');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const getSectionForIndex = (index: number): 'body' | 'heart' | 'head' => {
    if (index < 12) return 'body';
    if (index < 24) return 'heart';
    return 'head';
  };

  const getCurrentQuestion = (): V4Question | null => {
    const localIndex = currentQuestionIndex % 12;
    return currentQuestions[localIndex] || null;
  };

  const handleSelectAnswer = (value: number) => {
    setSelectedValue(value);
  };

  const handleContinue = async () => {
    if (selectedValue === null || !sessionId) return;

    const question = getCurrentQuestion();
    if (!question) return;

    const responseTime = Date.now() - questionStartTime.current;
    
    // Check for fast response
    if (responseTime < MIN_RESPONSE_TIME_MS) {
      // Show subtle warning but allow submission
      console.log('[V4] Fast response detected:', responseTime);
    }

    setIsSubmitting(true);

    try {
      // Fade out animation
      Animated.timing(fadeAnim, {
        toValue: 0,
        duration: 150,
        useNativeDriver: true,
      }).start();

      const response = await submitV4Answer(
        sessionId,
        question.id,
        selectedValue,
        responseTime
      );

      // Check if completed
      if (response.status === 'completed') {
        setResult(response.result);
        setViewState('results');
        await clearSession();
        
        // Update store with result
        if (response.result?.primary_type && setEnneagramResult) {
          setEnneagramResult({
            type: response.result.primary_type.number,
            wing: response.result.suggested_wing,
            confidence: response.result.confidence_level === 'high' ? 90 : 
                       response.result.confidence_level === 'medium' ? 70 : 50,
          });
        }
        return;
      }

      // Update state for next question
      const newIndex = response.current_index;
      setCurrentQuestionIndex(newIndex);
      setSelectedValue(null);

      // Check for new batch
      if (response.next_batch && response.next_batch.length > 0) {
        setCurrentQuestions(response.next_batch);
      }

      // Check section change
      const newSection = getSectionForIndex(newIndex);
      if (newSection !== currentSection) {
        setCurrentSection(newSection);
        setViewState('section_intro');
      }

      // Update saved session
      await saveSession({
        session_id: sessionId,
        user_id: user!.id,
        current_index: newIndex,
        created_at_iso: new Date().toISOString(),
        updated_at_iso: new Date().toISOString(),
      });

      // Fade in animation
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 150,
        useNativeDriver: true,
      }).start();

      // Reset timer
      questionStartTime.current = Date.now();

    } catch (err: any) {
      console.error('[V4] Submit error:', err);
      setError(err.message || 'Failed to submit answer');
      
      // Restore fade
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 150,
        useNativeDriver: true,
      }).start();
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRetake = () => {
    Alert.alert(
      'Retake Assessment',
      'This will clear your current results and start fresh. Are you sure?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Retake',
          style: 'destructive',
          onPress: async () => {
            await clearSession();
            setResult(null);
            setSessionId(null);
            setCurrentQuestionIndex(0);
            setSelectedValue(null);
            setHasExistingSession(false);
            setViewState('welcome');
          },
        },
      ]
    );
  };

  const handleExit = () => {
    navigateToLenses(router);
  };

  // ============================================
  // RENDER: WELCOME SCREEN
  // ============================================

  const renderWelcome = () => (
    <ScrollView 
      contentContainerStyle={styles.welcomeContainer}
      showsVerticalScrollIndicator={false}
    >
      <View style={styles.welcomeContent}>
        {/* Header Icon */}
        <View style={styles.welcomeIconContainer}>
          <Ionicons name="finger-print-outline" size={64} color={Colors.accent} />
        </View>

        <Text style={styles.welcomeTitle}>Discover Your Type</Text>
        <Text style={styles.welcomeSubtitle}>Enneagram Assessment V4</Text>

        <View style={styles.welcomeInfoCard}>
          <View style={styles.welcomeInfoRow}>
            <Ionicons name="time-outline" size={20} color={Colors.textSecondary} />
            <Text style={styles.welcomeInfoText}>~15 minutes to complete</Text>
          </View>
          <View style={styles.welcomeInfoRow}>
            <Ionicons name="help-circle-outline" size={20} color={Colors.textSecondary} />
            <Text style={styles.welcomeInfoText}>42 behavioral questions</Text>
          </View>
          <View style={styles.welcomeInfoRow}>
            <Ionicons name="analytics-outline" size={20} color={Colors.textSecondary} />
            <Text style={styles.welcomeInfoText}>Get your top 2 types + wing</Text>
          </View>
        </View>

        <Text style={styles.welcomeDescription}>
          Answer honestly based on your natural tendencies, not who you think you should be. 
          There are no right or wrong answers.
        </Text>

        {/* Action Buttons */}
        <View style={styles.welcomeActions}>
          {hasExistingSession && (
            <TouchableOpacity
              style={styles.resumeButton}
              onPress={() => startAssessment(true)}
              disabled={isLoading}
            >
              {isLoading ? (
                <ActivityIndicator color={Colors.accent} />
              ) : (
                <>
                  <Ionicons name="play" size={20} color={Colors.accent} />
                  <Text style={styles.resumeButtonText}>Resume Assessment</Text>
                </>
              )}
            </TouchableOpacity>
          )}

          <TouchableOpacity
            style={styles.startButton}
            onPress={() => startAssessment(false)}
            disabled={isLoading}
          >
            {isLoading && !hasExistingSession ? (
              <ActivityIndicator color={Colors.surface} />
            ) : (
              <>
                <Text style={styles.startButtonText}>
                  {hasExistingSession ? 'Start Fresh' : 'Begin Assessment'}
                </Text>
                <Ionicons name="arrow-forward" size={20} color={Colors.surface} />
              </>
            )}
          </TouchableOpacity>
        </View>

        {/* Back Button */}
        <TouchableOpacity style={styles.backLink} onPress={handleExit}>
          <Text style={styles.backLinkText}>← Back to Lenses</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );

  // ============================================
  // RENDER: SECTION INTRO
  // ============================================

  const renderSectionIntro = () => {
    const section = SECTION_INFO[currentSection];
    const sectionNumber = currentSection === 'body' ? 1 : currentSection === 'heart' ? 2 : 3;

    return (
      <View style={styles.sectionIntroContainer}>
        <View style={styles.sectionIntroContent}>
          {/* Section Badge */}
          <View style={[styles.sectionBadge, { backgroundColor: section.color + '20' }]}>
            <Text style={[styles.sectionBadgeText, { color: section.color }]}>
              Section {sectionNumber} of 3
            </Text>
          </View>

          {/* Icon */}
          <View style={[styles.sectionIconContainer, { backgroundColor: section.color + '15' }]}>
            <Ionicons name={section.icon} size={48} color={section.color} />
          </View>

          <Text style={styles.sectionTitle}>{section.name}</Text>
          <Text style={styles.sectionSubtitle}>{section.subtitle}</Text>

          <Text style={styles.sectionDescription}>{section.description}</Text>

          {/* Types in this section */}
          <View style={styles.sectionTypesRow}>
            {section.types.map((type) => (
              <View key={type} style={styles.sectionTypeChip}>
                <Text style={styles.sectionTypeText}>Type {type}</Text>
              </View>
            ))}
          </View>

          {/* Progress */}
          <View style={styles.sectionProgressInfo}>
            <Text style={styles.sectionProgressText}>
              {currentQuestionIndex} of {totalQuestions} questions completed
            </Text>
            <View style={styles.progressBarContainer}>
              <View 
                style={[
                  styles.progressBarFill, 
                  { width: `${(currentQuestionIndex / totalQuestions) * 100}%` }
                ]} 
              />
            </View>
          </View>

          {/* Continue Button */}
          <TouchableOpacity
            style={styles.sectionContinueButton}
            onPress={() => setViewState('questions')}
          >
            <Text style={styles.sectionContinueText}>Continue</Text>
            <Ionicons name="arrow-forward" size={20} color={Colors.surface} />
          </TouchableOpacity>
        </View>
      </View>
    );
  };

  // ============================================
  // RENDER: QUESTION SCREEN
  // ============================================

  const renderQuestions = () => {
    const question = getCurrentQuestion();
    if (!question) {
      return (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={Colors.accent} />
          <Text style={styles.loadingText}>Loading question...</Text>
        </View>
      );
    }

    const section = SECTION_INFO[currentSection];

    return (
      <View style={styles.questionContainer}>
        {/* Header */}
        <View style={styles.questionHeader}>
          <TouchableOpacity onPress={handleExit} style={styles.exitButton}>
            <Ionicons name="close" size={24} color={Colors.textSecondary} />
          </TouchableOpacity>

          <View style={styles.progressInfo}>
            <Text style={styles.progressSection}>{section.name}</Text>
            <View style={styles.progressCountBadge}>
              <Text style={styles.progressCount}>
                {currentQuestionIndex + 1} / {totalQuestions}
              </Text>
            </View>
          </View>
        </View>

        {/* Progress Bar */}
        <View style={styles.progressBarContainerSmall}>
          <View 
            style={[
              styles.progressBarFillSmall, 
              { 
                width: `${((currentQuestionIndex + 1) / totalQuestions) * 100}%`,
                backgroundColor: section.color,
              }
            ]} 
          />
        </View>

        {/* Question Content */}
        <ScrollView 
          contentContainerStyle={styles.questionScrollContent}
          showsVerticalScrollIndicator={false}
        >
          <Animated.View style={[styles.questionContent, { opacity: fadeAnim }]}>
            <Text style={styles.questionText}>{question.text}</Text>

            {/* Options */}
            <View style={styles.optionsContainer}>
              {question.options.map((option) => {
                const isSelected = selectedValue === option.value;
                return (
                  <TouchableOpacity
                    key={option.value}
                    style={[
                      styles.optionButton,
                      isSelected && styles.optionButtonSelected,
                    ]}
                    onPress={() => handleSelectAnswer(option.value)}
                    activeOpacity={0.7}
                  >
                    <View style={[
                      styles.optionRadio,
                      isSelected && styles.optionRadioSelected,
                    ]}>
                      {isSelected && <View style={styles.optionRadioInner} />}
                    </View>
                    <Text style={[
                      styles.optionText,
                      isSelected && styles.optionTextSelected,
                    ]}>
                      {option.text}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </View>
          </Animated.View>
        </ScrollView>

        {/* Continue Button */}
        <View style={[styles.buttonContainer, { paddingBottom: Math.max(insets.bottom, 16) }]}>
          <TouchableOpacity
            style={[
              styles.continueButton,
              selectedValue !== null && styles.continueButtonActive,
              selectedValue === null && styles.continueButtonDisabled,
            ]}
            onPress={handleContinue}
            disabled={selectedValue === null || isSubmitting}
          >
            {isSubmitting ? (
              <ActivityIndicator color={Colors.surface} />
            ) : (
              <>
                <Text style={[
                  styles.continueButtonText,
                  selectedValue !== null && styles.continueButtonTextActive,
                ]}>
                  Continue
                </Text>
                <Ionicons 
                  name="arrow-forward" 
                  size={18} 
                  color={selectedValue !== null ? Colors.surface : Colors.textTertiary} 
                />
              </>
            )}
          </TouchableOpacity>
        </View>
      </View>
    );
  };

  // ============================================
  // RENDER: COMPUTING SCREEN
  // ============================================

  const renderComputing = () => (
    <View style={styles.computingContainer}>
      <ActivityIndicator size="large" color={Colors.accent} />
      <Text style={styles.computingTitle}>Analyzing Your Responses</Text>
      <Text style={styles.computingSubtitle}>
        Calculating your type profile...
      </Text>
    </View>
  );

  // ============================================
  // RENDER: RESULTS SCREEN
  // ============================================

  const renderResults = () => {
    if (!result) return null;

    const { primary_type, secondary_type, suggested_wing, all_scores, confidence_level, is_unclear } = result;

    return (
      <ScrollView 
        contentContainerStyle={styles.resultsContainer}
        showsVerticalScrollIndicator={false}
      >
        {/* Header */}
        <View style={styles.resultsHeader}>
          <Text style={styles.resultsTitle}>Your Enneagram Profile</Text>
          {is_unclear && (
            <View style={styles.unclearBadge}>
              <Ionicons name="information-circle" size={16} color={Colors.warning} />
              <Text style={styles.unclearText}>Close call - consider retaking</Text>
            </View>
          )}
        </View>

        {/* Primary Type Card */}
        <View style={styles.primaryTypeCard}>
          <View style={styles.typeNumberContainer}>
            <Text style={styles.typeNumber}>{primary_type.number}</Text>
            <Text style={styles.wingIndicator}>w{suggested_wing}</Text>
          </View>
          
          <Text style={styles.typeName}>{primary_type.name}</Text>
          <Text style={styles.typePercentage}>{primary_type.percentage.toFixed(1)}% match</Text>
          
          <Text style={styles.typeBrief}>{primary_type.brief}</Text>

          <View style={styles.typeDetailsContainer}>
            <View style={styles.typeDetailRow}>
              <Text style={styles.typeDetailLabel}>Core Desire:</Text>
              <Text style={styles.typeDetailValue}>{primary_type.core_desire}</Text>
            </View>
            <View style={styles.typeDetailRow}>
              <Text style={styles.typeDetailLabel}>Core Fear:</Text>
              <Text style={styles.typeDetailValue}>{primary_type.core_fear}</Text>
            </View>
          </View>
        </View>

        {/* Secondary Type */}
        <View style={styles.secondaryTypeCard}>
          <Text style={styles.secondaryLabel}>Also Strong</Text>
          <View style={styles.secondaryContent}>
            <Text style={styles.secondaryNumber}>{secondary_type.number}</Text>
            <View style={styles.secondaryInfo}>
              <Text style={styles.secondaryName}>{secondary_type.name}</Text>
              <Text style={styles.secondaryPercentage}>
                {secondary_type.percentage.toFixed(1)}% match
              </Text>
            </View>
          </View>
          <Text style={styles.secondaryHint}>
            This could indicate your wing, stress point, or growth direction.
          </Text>
        </View>

        {/* Confidence Level */}
        <View style={styles.confidenceCard}>
          <Text style={styles.confidenceLabel}>Confidence Level</Text>
          <View style={styles.confidenceBadge}>
            <Ionicons 
              name={confidence_level === 'high' ? 'checkmark-circle' : 
                    confidence_level === 'medium' ? 'alert-circle' : 'help-circle'} 
              size={20} 
              color={confidence_level === 'high' ? Colors.success : 
                     confidence_level === 'medium' ? Colors.warning : Colors.error} 
            />
            <Text style={[
              styles.confidenceText,
              { color: confidence_level === 'high' ? Colors.success : 
                       confidence_level === 'medium' ? Colors.warning : Colors.error }
            ]}>
              {confidence_level.charAt(0).toUpperCase() + confidence_level.slice(1)}
            </Text>
          </View>
        </View>

        {/* Full Breakdown Toggle */}
        <TouchableOpacity
          style={styles.breakdownToggle}
          onPress={() => setShowFullBreakdown(!showFullBreakdown)}
        >
          <Text style={styles.breakdownToggleText}>
            {showFullBreakdown ? 'Hide' : 'Show'} Full Breakdown
          </Text>
          <Ionicons 
            name={showFullBreakdown ? 'chevron-up' : 'chevron-down'} 
            size={20} 
            color={Colors.accent} 
          />
        </TouchableOpacity>

        {/* Full Breakdown */}
        {showFullBreakdown && (
          <View style={styles.breakdownContainer}>
            {all_scores.map((score, index) => (
              <View key={score.type} style={styles.breakdownRow}>
                <View style={styles.breakdownTypeInfo}>
                  <Text style={styles.breakdownTypeNumber}>{score.type}</Text>
                  <Text style={styles.breakdownTypeName}>{score.name}</Text>
                </View>
                <View style={styles.breakdownBarContainer}>
                  <View 
                    style={[
                      styles.breakdownBar,
                      { width: `${Math.min(score.percentage * 5, 100)}%` },
                      index === 0 && styles.breakdownBarPrimary,
                    ]}
                  />
                </View>
                <Text style={styles.breakdownPercentage}>
                  {score.percentage.toFixed(1)}%
                </Text>
              </View>
            ))}
          </View>
        )}

        {/* Action Buttons */}
        <View style={styles.resultsActions}>
          <TouchableOpacity
            style={styles.doneButton}
            onPress={handleExit}
          >
            <Text style={styles.doneButtonText}>Done</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.retakeButton}
            onPress={handleRetake}
          >
            <Ionicons name="refresh" size={18} color={Colors.textSecondary} />
            <Text style={styles.retakeButtonText}>Retake Assessment</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    );
  };

  // ============================================
  // RENDER: ERROR SCREEN
  // ============================================

  const renderError = () => (
    <View style={styles.errorContainer}>
      <Ionicons name="alert-circle" size={64} color={Colors.error} />
      <Text style={styles.errorTitle}>Something went wrong</Text>
      <Text style={styles.errorMessage}>{error}</Text>
      <TouchableOpacity style={styles.retryButton} onPress={() => setViewState('welcome')}>
        <Text style={styles.retryButtonText}>Try Again</Text>
      </TouchableOpacity>
    </View>
  );

  // ============================================
  // MAIN RENDER
  // ============================================

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <StatusBar style="light" />
      
      {viewState === 'loading' && (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={Colors.accent} />
        </View>
      )}

      {viewState === 'welcome' && renderWelcome()}
      {viewState === 'section_intro' && renderSectionIntro()}
      {viewState === 'questions' && renderQuestions()}
      {viewState === 'computing' && renderComputing()}
      {viewState === 'results' && renderResults()}
      {viewState === 'error' && renderError()}
    </SafeAreaView>
  );
}

// ============================================
// STYLES
// ============================================

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },

  // Loading
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: Colors.textSecondary,
  },

  // Welcome Screen
  welcomeContainer: {
    flexGrow: 1,
    paddingHorizontal: 24,
    paddingVertical: 32,
  },
  welcomeContent: {
    flex: 1,
    alignItems: 'center',
  },
  welcomeIconContainer: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: Colors.surfaceLight,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 24,
  },
  welcomeTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: Colors.text,
    marginBottom: 8,
  },
  welcomeSubtitle: {
    fontSize: 16,
    color: Colors.accent,
    marginBottom: 24,
  },
  welcomeInfoCard: {
    width: '100%',
    backgroundColor: Colors.surface,
    borderRadius: 16,
    padding: 20,
    marginBottom: 24,
    gap: 16,
  },
  welcomeInfoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  welcomeInfoText: {
    fontSize: 15,
    color: Colors.textSecondary,
  },
  welcomeDescription: {
    fontSize: 15,
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 32,
  },
  welcomeActions: {
    width: '100%',
    gap: 12,
  },
  resumeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderColor: Colors.accent,
    paddingVertical: 16,
    borderRadius: 12,
  },
  resumeButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.accent,
  },
  startButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: Colors.accent,
    paddingVertical: 16,
    borderRadius: 12,
  },
  startButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.surface,
  },
  backLink: {
    marginTop: 24,
    padding: 12,
  },
  backLinkText: {
    fontSize: 14,
    color: Colors.textTertiary,
  },

  // Section Intro
  sectionIntroContainer: {
    flex: 1,
    paddingHorizontal: 24,
    paddingVertical: 32,
    justifyContent: 'center',
  },
  sectionIntroContent: {
    alignItems: 'center',
  },
  sectionBadge: {
    paddingHorizontal: 16,
    paddingVertical: 6,
    borderRadius: 20,
    marginBottom: 24,
  },
  sectionBadgeText: {
    fontSize: 14,
    fontWeight: '600',
  },
  sectionIconContainer: {
    width: 100,
    height: 100,
    borderRadius: 50,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: Colors.text,
    marginBottom: 8,
  },
  sectionSubtitle: {
    fontSize: 16,
    color: Colors.textSecondary,
    marginBottom: 24,
  },
  sectionDescription: {
    fontSize: 15,
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 24,
  },
  sectionTypesRow: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 32,
  },
  sectionTypeChip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: Colors.surfaceLight,
    borderRadius: 20,
  },
  sectionTypeText: {
    fontSize: 14,
    color: Colors.textSecondary,
  },
  sectionProgressInfo: {
    width: '100%',
    marginBottom: 32,
  },
  sectionProgressText: {
    fontSize: 14,
    color: Colors.textTertiary,
    textAlign: 'center',
    marginBottom: 12,
  },
  progressBarContainer: {
    width: '100%',
    height: 6,
    backgroundColor: Colors.surfaceLight,
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    backgroundColor: Colors.accent,
    borderRadius: 3,
  },
  sectionContinueButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: Colors.accent,
    paddingVertical: 16,
    paddingHorizontal: 48,
    borderRadius: 12,
  },
  sectionContinueText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.surface,
  },

  // Question Screen
  questionContainer: {
    flex: 1,
  },
  questionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  exitButton: {
    padding: 8,
  },
  progressInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  progressSection: {
    fontSize: 14,
    color: Colors.textSecondary,
  },
  progressCountBadge: {
    backgroundColor: Colors.surfaceLight,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  progressCount: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.text,
  },
  progressBarContainerSmall: {
    height: 3,
    backgroundColor: Colors.surfaceLight,
  },
  progressBarFillSmall: {
    height: '100%',
  },
  questionScrollContent: {
    flexGrow: 1,
    paddingHorizontal: 24,
    paddingTop: 32,
    paddingBottom: 16,
  },
  questionContent: {
    flex: 1,
  },
  questionText: {
    fontSize: 20,
    fontWeight: '600',
    color: Colors.text,
    lineHeight: 28,
    marginBottom: 32,
  },
  optionsContainer: {
    gap: 12,
  },
  optionButton: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 16,
    padding: 16,
    backgroundColor: Colors.surface,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: Colors.border,
  },
  optionButtonSelected: {
    borderColor: Colors.accent,
    backgroundColor: Colors.accent + '10',
  },
  optionRadio: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: Colors.border,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 2,
  },
  optionRadioSelected: {
    borderColor: Colors.accent,
  },
  optionRadioInner: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: Colors.accent,
  },
  optionText: {
    flex: 1,
    fontSize: 16,
    color: Colors.text,
    lineHeight: 24,
  },
  optionTextSelected: {
    color: Colors.text,
  },
  buttonContainer: {
    paddingHorizontal: 24,
    paddingTop: 16,
  },
  continueButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: Colors.surfaceLight,
    paddingVertical: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  continueButtonActive: {
    backgroundColor: Colors.accent,
    borderColor: Colors.accent,
  },
  continueButtonDisabled: {
    opacity: 0.5,
  },
  continueButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.textTertiary,
  },
  continueButtonTextActive: {
    color: Colors.surface,
  },

  // Computing
  computingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  computingTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: Colors.text,
    marginTop: 24,
    marginBottom: 8,
  },
  computingSubtitle: {
    fontSize: 16,
    color: Colors.textSecondary,
  },

  // Results
  resultsContainer: {
    flexGrow: 1,
    paddingHorizontal: 24,
    paddingVertical: 32,
  },
  resultsHeader: {
    alignItems: 'center',
    marginBottom: 24,
  },
  resultsTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: Colors.text,
    marginBottom: 12,
  },
  unclearBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: Colors.warning + '20',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
  },
  unclearText: {
    fontSize: 13,
    color: Colors.warning,
  },
  primaryTypeCard: {
    backgroundColor: Colors.surface,
    borderRadius: 20,
    padding: 24,
    alignItems: 'center',
    marginBottom: 16,
    borderWidth: 1,
    borderColor: Colors.accent + '30',
  },
  typeNumberContainer: {
    flexDirection: 'row',
    alignItems: 'baseline',
    marginBottom: 8,
  },
  typeNumber: {
    fontSize: 72,
    fontWeight: '700',
    color: Colors.accent,
  },
  wingIndicator: {
    fontSize: 32,
    fontWeight: '600',
    color: Colors.textSecondary,
    marginLeft: 4,
  },
  typeName: {
    fontSize: 24,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 4,
  },
  typePercentage: {
    fontSize: 16,
    color: Colors.accent,
    marginBottom: 16,
  },
  typeBrief: {
    fontSize: 15,
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 20,
  },
  typeDetailsContainer: {
    width: '100%',
    gap: 12,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  typeDetailRow: {
    gap: 4,
  },
  typeDetailLabel: {
    fontSize: 12,
    color: Colors.textTertiary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  typeDetailValue: {
    fontSize: 14,
    color: Colors.text,
    lineHeight: 20,
  },
  secondaryTypeCard: {
    backgroundColor: Colors.surface,
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
  },
  secondaryLabel: {
    fontSize: 12,
    color: Colors.textTertiary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 12,
  },
  secondaryContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
    marginBottom: 12,
  },
  secondaryNumber: {
    fontSize: 36,
    fontWeight: '700',
    color: Colors.textSecondary,
  },
  secondaryInfo: {
    flex: 1,
  },
  secondaryName: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.text,
  },
  secondaryPercentage: {
    fontSize: 14,
    color: Colors.textSecondary,
  },
  secondaryHint: {
    fontSize: 13,
    color: Colors.textTertiary,
    fontStyle: 'italic',
  },
  confidenceCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  confidenceLabel: {
    fontSize: 14,
    color: Colors.textSecondary,
  },
  confidenceBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  confidenceText: {
    fontSize: 14,
    fontWeight: '600',
  },
  breakdownToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 16,
  },
  breakdownToggleText: {
    fontSize: 14,
    color: Colors.accent,
    fontWeight: '500',
  },
  breakdownContainer: {
    backgroundColor: Colors.surface,
    borderRadius: 16,
    padding: 16,
    marginBottom: 24,
    gap: 12,
  },
  breakdownRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  breakdownTypeInfo: {
    width: 100,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  breakdownTypeNumber: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.textSecondary,
    width: 24,
  },
  breakdownTypeName: {
    fontSize: 12,
    color: Colors.textTertiary,
    flex: 1,
  },
  breakdownBarContainer: {
    flex: 1,
    height: 8,
    backgroundColor: Colors.surfaceLight,
    borderRadius: 4,
    overflow: 'hidden',
  },
  breakdownBar: {
    height: '100%',
    backgroundColor: Colors.textSecondary,
    borderRadius: 4,
  },
  breakdownBarPrimary: {
    backgroundColor: Colors.accent,
  },
  breakdownPercentage: {
    width: 50,
    fontSize: 13,
    color: Colors.textSecondary,
    textAlign: 'right',
  },
  resultsActions: {
    gap: 12,
    marginTop: 16,
  },
  doneButton: {
    backgroundColor: Colors.accent,
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  doneButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.surface,
  },
  retakeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 16,
  },
  retakeButtonText: {
    fontSize: 14,
    color: Colors.textSecondary,
  },

  // Error
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  errorTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: Colors.text,
    marginTop: 24,
    marginBottom: 8,
  },
  errorMessage: {
    fontSize: 16,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginBottom: 24,
  },
  retryButton: {
    backgroundColor: Colors.accent,
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
  },
  retryButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.surface,
  },
});
